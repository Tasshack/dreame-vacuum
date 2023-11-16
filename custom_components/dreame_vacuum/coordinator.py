"""DataUpdateCoordinator for Dreame Vacuum."""
from __future__ import annotations

import math
import traceback
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_TOKEN,
    CONF_PASSWORD,
    CONF_USERNAME,
    ATTR_ENTITY_ID,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .dreame import DreameVacuumDevice, DreameVacuumProperty
from .dreame.resources import (
    CONSUMABLE_IMAGE,
    DRAINAGE_STATUS_SUCCESS,
    DRAINAGE_STATUS_FAIL,
)
from .const import (
    DOMAIN,
    LOGGER,
    CONF_NOTIFY,
    CONF_COUNTRY,
    CONF_MAC,
    CONF_DID,
    CONF_ACCOUNT_TYPE,
    CONF_PREFER_CLOUD,
    CONTENT_TYPE,
    NOTIFICATION_CLEANUP_COMPLETED,
    NOTIFICATION_DUST_COLLECTION_NOT_PERFORMED,
    NOTIFICATION_RESUME_CLEANING,
    NOTIFICATION_RESUME_CLEANING_NOT_PERFORMED,
    NOTIFICATION_REPLACE_MULTI_MAP,
    NOTIFICATION_REPLACE_MAP,
    NOTIFICATION_2FA_LOGIN,
    NOTIFICATION_DRAINAGE_COMPLETED,
    NOTIFICATION_DRAINAGE_FAILED,
    NOTIFICATION_ID_DUST_COLLECTION,
    NOTIFICATION_ID_CLEANING_PAUSED,
    NOTIFICATION_ID_REPLACE_MAIN_BRUSH,
    NOTIFICATION_ID_REPLACE_SIDE_BRUSH,
    NOTIFICATION_ID_REPLACE_FILTER,
    NOTIFICATION_ID_REPLACE_SECONDARY_FILTER,
    NOTIFICATION_ID_CLEAN_SENSOR,
    NOTIFICATION_ID_REPLACE_MOP,
    NOTIFICATION_ID_SILVER_ION,
    NOTIFICATION_ID_REPLACE_DETERGENT,
    NOTIFICATION_ID_CLEANUP_COMPLETED,
    NOTIFICATION_ID_WARNING,
    NOTIFICATION_ID_ERROR,
    NOTIFICATION_ID_INFORMATION,
    NOTIFICATION_ID_CONSUMABLE,
    NOTIFICATION_ID_REPLACE_TEMPORARY_MAP,
    NOTIFICATION_ID_2FA_LOGIN,
    NOTIFICATION_ID_LOW_WATER,
    NOTIFICATION_ID_DRAINAGE_STATUS,
    EVENT_TASK_STATUS,
    EVENT_CONSUMABLE,
    EVENT_WARNING,
    EVENT_ERROR,
    EVENT_INFORMATION,
    EVENT_2FA_LOGIN,
    EVENT_LOW_WATER,
    EVENT_DRAINAGE_STATUS,
    CONSUMABLE_MAIN_BRUSH,
    CONSUMABLE_SIDE_BRUSH,
    CONSUMABLE_FILTER,
    CONSUMABLE_SECONDARY_FILTER,
    CONSUMABLE_SENSOR,
    CONSUMABLE_MOP_PAD,
    CONSUMABLE_SILVER_ION,
    CONSUMABLE_DETERGENT,
)


class DreameVacuumDataUpdateCoordinator(DataUpdateCoordinator[DreameVacuumDevice]):
    """Class to manage fetching Dreame Vacuum data from single endpoint."""

    _device: DreameVacuumDevice = None

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry: ConfigEntry,
    ) -> None:
        """Initialize global Dreame Vacuum data updater."""
        self._token = entry.data[CONF_TOKEN]
        self._host = entry.data[CONF_HOST]
        self._notify = entry.options.get(CONF_NOTIFY, True)
        self._entry = entry
        self._ready = False
        self._available = False
        self._has_warning = False
        self._has_temporary_map = None
        self._low_water = False
        self._drainage_status = None
        self._washing = None
        self._two_factor_url = None

        LOGGER.info("Integration loading: %s", entry.data[CONF_NAME])
        self._device = DreameVacuumDevice(
            entry.data[CONF_NAME],
            self._host,
            self._token,
            entry.data.get(CONF_MAC),
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            entry.data.get(CONF_COUNTRY),
            entry.options.get(CONF_PREFER_CLOUD, False),
            entry.data.get(CONF_ACCOUNT_TYPE, "mi"),
            entry.data.get(CONF_DID),
        )

        self._device.listen(
            self._dust_collection_changed, DreameVacuumProperty.DUST_COLLECTION
        )
        self._device.listen(self._error_changed, DreameVacuumProperty.ERROR)
        self._device.listen(self._task_status_changed, DreameVacuumProperty.TASK_STATUS)
        self._device.listen(
            self._cleaning_paused_changed, DreameVacuumProperty.CLEANING_PAUSED
        )
        self._device.listen(
            self._low_water_warning_changed, DreameVacuumProperty.LOW_WATER_WARNING
        )
        self._device.listen(
            self._drainage_status_changed, DreameVacuumProperty.DRAINAGE_STATUS
        )
        self._device.listen(
            self._self_wash_base_status_changed,
            DreameVacuumProperty.SELF_WASH_BASE_STATUS,
        )
        self._device.listen(self.async_set_updated_data)
        self._device.listen_error(self.async_set_update_error)

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
        )

        async_dispatcher_connect(
            hass,
            persistent_notification.SIGNAL_PERSISTENT_NOTIFICATIONS_UPDATED,
            self._notification_dismiss_listener,
        )

    def __del__(self):
        if self._device is not None:
            self._device.listen(None)
            self._device.disconnect()
            del self._device
            self._device = None
        super().__del__()

    def _dust_collection_changed(self, previous_value=None) -> None:
        if self._device.status.auto_emptying_not_performed:
            self._fire_event(
                EVENT_INFORMATION, {EVENT_INFORMATION: NOTIFICATION_ID_DUST_COLLECTION}
            )

            self._create_persistent_notification(
                NOTIFICATION_DUST_COLLECTION_NOT_PERFORMED,
                NOTIFICATION_ID_DUST_COLLECTION,
            )
        else:
            self._remove_persistent_notification(NOTIFICATION_ID_DUST_COLLECTION)

    def _cleaning_paused_changed(self, previous_value=None) -> None:
        if self._device.status.cleaning_paused:
            notification = NOTIFICATION_RESUME_CLEANING
            if self._device.status.battery_level >= 80:
                dnd_remaining = self._device.status.dnd_remaining
                if dnd_remaining:
                    hour = math.floor(dnd_remaining / 3600)
                    minute = math.floor((dnd_remaining - hour * 3600) / 60)
                    notification = f"{NOTIFICATION_RESUME_CLEANING_NOT_PERFORMED}\n## Cleaning will start in {hour} hour(s) and {minute} minutes(s)"
                self._fire_event(
                    EVENT_INFORMATION,
                    {EVENT_INFORMATION: NOTIFICATION_ID_CLEANING_PAUSED},
                )
            else:
                self._fire_event(
                    EVENT_INFORMATION,
                    {EVENT_INFORMATION: NOTIFICATION_ID_CLEANING_PAUSED},
                )

            self._create_persistent_notification(
                notification, NOTIFICATION_ID_CLEANING_PAUSED
            )
        else:
            self._remove_persistent_notification(NOTIFICATION_ID_CLEANING_PAUSED)

    def _task_status_changed(self, previous_value=None) -> None:
        if previous_value is not None:
            if self._device.cleanup_completed:
                self._fire_event(EVENT_TASK_STATUS, self._device.status.job)
                self._create_persistent_notification(
                    NOTIFICATION_CLEANUP_COMPLETED, NOTIFICATION_ID_CLEANUP_COMPLETED
                )
                self._check_consumables()

            elif (
                previous_value == 0
                and not self._device.status.fast_mapping
                and not self._device.status.cruising
            ):
                self._fire_event(EVENT_TASK_STATUS, self._device.status.job)
        else:
            self._check_consumables()

    def _error_changed(self, previous_value=None) -> None:
        has_warning = self._device.status.has_warning
        description = self._device.status.error_description
        if has_warning:
            content = description[0]
            self._fire_event(
                EVENT_WARNING,
                {EVENT_WARNING: content, "code": self._device.status.error.value},
            )

            if len(description[1]) > 2:
                content = f"### {content}\n{description[1]}"

            image = self._device.status.error_image
            if image:
                content = f"{content}![image](data:{CONTENT_TYPE};base64,{image})"
            self._create_persistent_notification(content, NOTIFICATION_ID_WARNING)
        elif self._has_warning:
            self._remove_persistent_notification(NOTIFICATION_ID_WARNING)

        if self._device.status.has_error:
            self._fire_event(
                EVENT_ERROR,
                {EVENT_ERROR: description[0], "code": self._device.status.error.value},
            )

            content = f"### {description[0]}\n{description[1]}"
            image = self._device.status.error_image
            if image:
                content = f"{content}![image](data:{CONTENT_TYPE};base64,{image})"
            self._create_persistent_notification(
                content, f"{NOTIFICATION_ID_ERROR}_{self._device.status.error.value}"
            )

        self._has_warning = has_warning

    def _has_temporary_map_changed(self, previous_value=None) -> None:
        if self._device.status.has_temporary_map:
            self._fire_event(
                EVENT_WARNING, {EVENT_WARNING: NOTIFICATION_REPLACE_MULTI_MAP}
            )

            self._create_persistent_notification(
                NOTIFICATION_REPLACE_MULTI_MAP
                if self._device.status.multi_map
                else NOTIFICATION_REPLACE_MAP,
                NOTIFICATION_ID_REPLACE_TEMPORARY_MAP,
            )
        else:
            self._fire_event(
                EVENT_WARNING, {EVENT_WARNING: NOTIFICATION_ID_REPLACE_TEMPORARY_MAP}
            )

            self._remove_persistent_notification(NOTIFICATION_ID_REPLACE_TEMPORARY_MAP)

    def _low_water_warning_changed(self, previous_value=None) -> None:
        low_water_warning = self._device.status.low_water_warning
        if low_water_warning.value > 0 and (
            not previous_value or low_water_warning.value > 1
        ):
            low_water_warning = self._device.status.low_water_warning_name_description
            self._fire_event(
                EVENT_LOW_WATER,
                {EVENT_LOW_WATER: description[0], "code": low_water_warning.value},
            )

            description = f"### {low_water_warning[0]}"
            if len(low_water_warning[1]) > 2:
                description = f"{description}\n{low_water_warning[1]}"
            self._create_persistent_notification(description, NOTIFICATION_ID_LOW_WATER)
        elif self._low_water:
            self._remove_persistent_notification(NOTIFICATION_ID_LOW_WATER)

        self._low_water = self._device.status.low_water

    def _drainage_status_changed(self, previous_value=None) -> None:
        if self._device.status.draining_complete:
            success = bool(self._device.status.drainage_status.value == 2)
            if success:
                description = f"{NOTIFICATION_DRAINAGE_COMPLETED}\n![image](data:{CONTENT_TYPE};base64,{DRAINAGE_STATUS_SUCCESS})"
            else:
                description = f"{NOTIFICATION_DRAINAGE_FAILED}\n![image](data:{CONTENT_TYPE};base64,{DRAINAGE_STATUS_FAIL})"

            self._fire_event(EVENT_DRAINAGE_STATUS, {EVENT_DRAINAGE_STATUS: success})
            self._create_persistent_notification(
                description, NOTIFICATION_ID_DRAINAGE_STATUS
            )
        elif self._drainage_status:
            self._remove_persistent_notification(NOTIFICATION_ID_DRAINAGE_STATUS)

        self._drainage_status = self._device.status.draining_complete

    def _self_wash_base_status_changed(
        self, previous_self_wash_base_status=None
    ) -> None:
        if (
            self._washing is not None
            and self._device.status.washing != self._washing
            and self._device.status.started
        ):
            self._check_consumables()
        self._washing = self._device.status.washing

    def _check_consumable(self, consumable, notification_id, property):
        description = self._device.status.consumable_life_warning_description(property)
        if description:
            self._create_persistent_notification(
                f"### {description[0]}\n{description[1]}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get(consumable)})",
                notification_id,
            )
            self._fire_event(
                EVENT_CONSUMABLE,
                {
                    EVENT_CONSUMABLE: consumable,
                    "life_left": self._device.get_property(property),
                },
            )

    def _check_consumables(self):
        self._check_consumable(
            CONSUMABLE_MAIN_BRUSH,
            NOTIFICATION_ID_REPLACE_MAIN_BRUSH,
            DreameVacuumProperty.MAIN_BRUSH_LEFT,
        )
        self._check_consumable(
            CONSUMABLE_SIDE_BRUSH,
            NOTIFICATION_ID_REPLACE_SIDE_BRUSH,
            DreameVacuumProperty.SIDE_BRUSH_LEFT,
        )
        self._check_consumable(
            CONSUMABLE_FILTER,
            NOTIFICATION_ID_REPLACE_FILTER,
            DreameVacuumProperty.FILTER_LEFT,
        )
        self._check_consumable(
            CONSUMABLE_SECONDARY_FILTER,
            NOTIFICATION_ID_REPLACE_SECONDARY_FILTER,
            DreameVacuumProperty.SECONDARY_FILTER_LEFT,
        )
        self._check_consumable(
            CONSUMABLE_SENSOR,
            NOTIFICATION_ID_CLEAN_SENSOR,
            DreameVacuumProperty.SENSOR_DIRTY_LEFT,
        )
        self._check_consumable(
            CONSUMABLE_MOP_PAD,
            NOTIFICATION_ID_REPLACE_MOP,
            DreameVacuumProperty.MOP_PAD_LEFT,
        )
        if self._device.capability.self_wash_base:
            self._check_consumable(
                CONSUMABLE_SILVER_ION,
                NOTIFICATION_ID_SILVER_ION,
                DreameVacuumProperty.SILVER_ION_LEFT,
            )
            self._check_consumable(
                CONSUMABLE_DETERGENT,
                NOTIFICATION_ID_REPLACE_DETERGENT,
                DreameVacuumProperty.DETERGENT_LEFT,
            )

    def _create_persistent_notification(self, content, notification_id) -> None:
        if self._notify or notification_id == NOTIFICATION_ID_2FA_LOGIN:
            if isinstance(self._notify, list) and notification_id != NOTIFICATION_ID_2FA_LOGIN:
                if notification_id == NOTIFICATION_ID_CLEANUP_COMPLETED:
                    if NOTIFICATION_ID_CLEANUP_COMPLETED not in self._notify:
                        return
                elif (
                    NOTIFICATION_ID_WARNING in notification_id
                    or NOTIFICATION_ID_LOW_WATER in notification_id
                ):
                    if NOTIFICATION_ID_WARNING not in self._notify:
                        return
                elif NOTIFICATION_ID_ERROR in notification_id:
                    if NOTIFICATION_ID_ERROR not in self._notify:
                        return
                elif (
                    notification_id == NOTIFICATION_ID_DUST_COLLECTION
                    or notification_id == NOTIFICATION_ID_CLEANING_PAUSED
                ):
                    if NOTIFICATION_ID_INFORMATION not in self._notify:
                        return
                elif (
                    notification_id != NOTIFICATION_ID_REPLACE_TEMPORARY_MAP
                    and notification_id != NOTIFICATION_ID_DRAINAGE_STATUS
                ):
                    if NOTIFICATION_ID_CONSUMABLE not in self._notify:
                       return

            persistent_notification.async_create(
                hass=self.hass,
                message=content,
                title=self._device.name,
                notification_id=f"{DOMAIN}_{self._device.mac}_{notification_id}",
            )

    def _remove_persistent_notification(self, notification_id) -> None:
        persistent_notification.async_dismiss(
            self.hass, f"{DOMAIN}_{self._device.mac}_{notification_id}"
        )

    def _notification_dismiss_listener(self, type, data) -> None:
        if type == persistent_notification.UpdateType.REMOVED:
            notifications = self.hass.data.get(persistent_notification.DOMAIN)
            if self._has_warning:
                if (
                    f"{DOMAIN}_{self._device.mac}_{NOTIFICATION_ID_WARNING}"
                    not in notifications
                ):
                    if NOTIFICATION_ID_WARNING in self._notify:
                        self._device.clear_warning()
                    self._has_warning = self._device.status.has_warning

            if self._two_factor_url:
                if (
                    f"{DOMAIN}_{self._device.mac}_{NOTIFICATION_ID_2FA_LOGIN}"
                    not in notifications
                ):
                    self._two_factor_url = None

            if self._low_water:
                if (
                    f"{DOMAIN}_{self._device.mac}_{NOTIFICATION_ID_LOW_WATER}"
                    not in notifications
                ):
                    if NOTIFICATION_ID_WARNING in self._notify:
                        self._device.clear_warning()
                    self._low_water = self._device.status.low_water

            if self._drainage_status:
                if (
                    f"{DOMAIN}_{self._device.mac}_{NOTIFICATION_ID_DRAINAGE_STATUS}"
                    not in notifications
                ):
                    if NOTIFICATION_ID_WARNING in self._notify:
                        self._device.clear_warning()
                    self._drainage_status = self._device.status.draining_complete

    def _fire_event(self, event_id, data) -> None:
        event_data = {
            ATTR_ENTITY_ID: generate_entity_id(
                "vacuum.{}", self._device.name, hass=self.hass
            )
        }
        if data:
            event_data.update(data)
        self.hass.bus.fire(f"{DOMAIN}_{event_id}", event_data)

    async def _async_update_data(self) -> DreameVacuumDevice:
        """Handle device update. This function is only called once when the integration is added to Home Assistant."""
        try:
            LOGGER.info("Integration starting...")
            await self.hass.async_add_executor_job(self._device.update)
            self._device.schedule_update()
            self.async_set_updated_data()
            return self._device
        except Exception as ex:
            LOGGER.warning("Integration start failed: %s", traceback.format_exc())
            if self._device is not None:
                self._device.listen(None)
                self._device.disconnect()
                del self._device
                self._device = None
            raise UpdateFailed(ex) from ex

    @property
    def device(self) -> DreameVacuumDevice:
        return self._device

    @callback
    def async_set_updated_data(self, device=None) -> None:
        if self._has_temporary_map != self._device.status.has_temporary_map:
            self._has_temporary_map_changed(self._has_temporary_map)
            self._has_temporary_map = self._device.status.has_temporary_map

        if not self._ready:
            self._ready = True
            if (self._device.token and self._device.token != self._token) or (self._device.host and self._device.host != self._host):
                data = self._entry.data.copy()
                self._host = self._device.host
                self._token = self._device.token
                data[CONF_HOST] = self._host
                data[CONF_TOKEN] = self._token
                LOGGER.info("Update Host Config: %s", self._host)
                self.hass.config_entries.async_update_entry(self._entry, data=data)

        if self._two_factor_url != self._device.two_factor_url:
            if self._device.two_factor_url:
                self._create_persistent_notification(
                    f"{NOTIFICATION_2FA_LOGIN}[{self._device.two_factor_url}]({self._device.two_factor_url})",
                    NOTIFICATION_ID_2FA_LOGIN,
                )
                self._fire_event(EVENT_2FA_LOGIN, {"url": self._device.two_factor_url})
            else:
                self._remove_persistent_notification(NOTIFICATION_ID_2FA_LOGIN)

            self._two_factor_url = self._device.two_factor_url

        self._available = self._device and self._device.available
        super().async_set_updated_data(self._device)

    @callback
    def async_set_update_error(self, ex) -> None:
        if self._available:
            self._available = self._device and self._device.available
            super().async_set_update_error(ex)
