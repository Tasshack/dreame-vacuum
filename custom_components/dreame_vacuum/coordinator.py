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
    ATTR_ENTITY_ID
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .dreame import DreameVacuumDevice, DreameVacuumProperty
from .dreame.resources import CONSUMABLE_IMAGE
from .const import (
    DOMAIN,
    LOGGER,
    CONF_NOTIFY,
    CONF_COUNTRY,
    CONF_MAC,
    CONF_PREFER_CLOUD,
    CONTENT_TYPE,
    NOTIFICATION_CLEANUP_COMPLETED,
    NOTIFICATION_MAIN_BRUSH_NO_LIFE_LEFT,
    NOTIFICATION_SIDE_BRUSH_NO_LIFE_LEFT,
    NOTIFICATION_FILTER_NO_LIFE_LEFT,
    NOTIFICATION_SENSOR_NO_LIFE_LEFT,
    NOTIFICATION_MOP_NO_LIFE_LEFT,
    NOTIFICATION_SILVER_ION_LIFE_LEFT,
    NOTIFICATION_DETERGENT_NO_LIFE_LEFT,
    NOTIFICATION_DUST_COLLECTION_NOT_PERFORMED,
    NOTIFICATION_RESUME_CLEANING,
    NOTIFICATION_RESUME_CLEANING_NOT_PERFORMED,
    NOTIFICATION_REPLACE_MULTI_MAP,
    NOTIFICATION_REPLACE_MAP,
    NOTIFICATION_2FA_LOGIN,
    NOTIFICATION_ID_DUST_COLLECTION,
    NOTIFICATION_ID_CLEANING_PAUSED,
    NOTIFICATION_ID_REPLACE_MAIN_BRUSH,
    NOTIFICATION_ID_REPLACE_SIDE_BRUSH,
    NOTIFICATION_ID_REPLACE_FILTER,
    NOTIFICATION_ID_CLEAN_SENSOR,
    NOTIFICATION_ID_REPLACE_MOP,
    NOTIFICATION_ID_SILVER_ION,
    NOTIFICATION_ID_REPLACE_DETERGENT,
    NOTIFICATION_ID_CLEANUP_COMPLETED,
    NOTIFICATION_ID_WARNING,
    NOTIFICATION_ID_ERROR,
    NOTIFICATION_ID_REPLACE_TEMPORARY_MAP,
    NOTIFICATION_ID_2FA_LOGIN,
    EVENT_TASK_STATUS,
    EVENT_CONSUMABLE,
    EVENT_WARNING,
    EVENT_ERROR,
    EVENT_INFORMATION,
    EVENT_2FA_LOGIN,
    CONSUMABLE_MAIN_BRUSH,
    CONSUMABLE_SIDE_BRUSH,
    CONSUMABLE_FILTER,
    CONSUMABLE_SENSOR,
    CONSUMABLE_MOP_PAD,
    CONSUMABLE_SILVER_ION,
    CONSUMABLE_DETERGENT,
)


class DreameVacuumDataUpdateCoordinator(DataUpdateCoordinator[DreameVacuumDevice]):
    """Class to manage fetching Dreame Vacuum data from single endpoint."""

    config_entry: ConfigEntry

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
        self._available = False
        self._has_warning = False
        self._has_temporary_map = None
        self._two_factor_url = None

        self.device = DreameVacuumDevice(
            entry.data[CONF_NAME],
            self._host,
            self._token,
            entry.data.get(CONF_MAC),
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            entry.data.get(CONF_COUNTRY),
            entry.options.get(CONF_PREFER_CLOUD, False),
        )
        
        self.device.listen(
            self._dust_collection_changed, DreameVacuumProperty.DUST_COLLECTION
        )
        self.device.listen(self._error_changed, DreameVacuumProperty.ERROR)
        self.device.listen(
            self._task_status_changed, DreameVacuumProperty.TASK_STATUS
        )
        self.device.listen(
            self._cleaning_paused_changed, DreameVacuumProperty.CLEANING_PAUSED
        )
        self.device.listen(self.async_set_updated_data)
        self.device.listen_error(self.async_set_update_error)

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
        )
        
        hass.bus.async_listen(
            persistent_notification.EVENT_PERSISTENT_NOTIFICATIONS_UPDATED,
            self._notification_dismiss_listener,
        )

    def _dust_collection_changed(self, previous_value=None) -> None:
        if previous_value is not None:
            if self.device.status.auto_emptying_not_performed:
                self._fire_event(EVENT_INFORMATION, {EVENT_INFORMATION: NOTIFICATION_ID_DUST_COLLECTION})

                self._create_persistent_notification(
                    NOTIFICATION_DUST_COLLECTION_NOT_PERFORMED,
                    NOTIFICATION_ID_DUST_COLLECTION,
                )
            else:
                self._remove_persistent_notification(
                    NOTIFICATION_ID_DUST_COLLECTION)

    def _cleaning_paused_changed(self, previous_value=None) -> None:
        if previous_value is not None and self.device.status.cleaning_paused:
            notification = NOTIFICATION_RESUME_CLEANING
            if self.device.status.battery_level >= 80:
                dnd_remaining = self.device.status.dnd_remaining
                if dnd_remaining:
                    hour = math.floor(dnd_remaining / 3600)
                    minute = math.floor((dnd_remaining - hour * 3600) / 60)
                    notification = f"{NOTIFICATION_RESUME_CLEANING_NOT_PERFORMED}\n## Cleaning will start in {hour} hour(s) and {minute} minutes(s)"
                self._fire_event(EVENT_INFORMATION, {EVENT_INFORMATION: NOTIFICATION_ID_CLEANING_PAUSED})
            else:
                self._fire_event(EVENT_INFORMATION, {EVENT_INFORMATION: NOTIFICATION_ID_CLEANING_PAUSED})

            self._create_persistent_notification(
                notification, NOTIFICATION_ID_CLEANING_PAUSED
            )
        else:
            self._remove_persistent_notification(
                NOTIFICATION_ID_CLEANING_PAUSED)

    def _task_status_changed(self, previous_value=None) -> None:
        if previous_value is not None:
            if self.device.cleanup_completed:
                self._fire_event(EVENT_TASK_STATUS, self.device.status.job)
                self._create_persistent_notification(
                    NOTIFICATION_CLEANUP_COMPLETED, NOTIFICATION_ID_CLEANUP_COMPLETED
                )

                if self.device.status.main_brush_life == 0:
                    self._create_persistent_notification(
                        f'{NOTIFICATION_MAIN_BRUSH_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get(CONSUMABLE_MAIN_BRUSH)})',
                        NOTIFICATION_ID_REPLACE_MAIN_BRUSH,
                    )
                    self._fire_event(EVENT_CONSUMABLE, {EVENT_CONSUMABLE: CONSUMABLE_MAIN_BRUSH})
                if self.device.status.side_brush_life == 0:
                    self._create_persistent_notification(
                        f'{NOTIFICATION_SIDE_BRUSH_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get(CONSUMABLE_SIDE_BRUSH)})',
                        NOTIFICATION_ID_REPLACE_SIDE_BRUSH,
                    )
                    self._fire_event(EVENT_CONSUMABLE, {EVENT_CONSUMABLE: CONSUMABLE_SIDE_BRUSH})
                if self.device.status.filter_life == 0:
                    self._create_persistent_notification(
                        f'{NOTIFICATION_FILTER_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get(CONSUMABLE_FILTER)})',
                        NOTIFICATION_ID_REPLACE_FILTER,
                    )
                    self._fire_event(EVENT_CONSUMABLE, {EVENT_CONSUMABLE: CONSUMABLE_FILTER})
                if self.device.status.sensor_dirty_life == 0:
                    self._create_persistent_notification(
                        f'{NOTIFICATION_SENSOR_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get(CONSUMABLE_SENSOR)})',
                        NOTIFICATION_ID_CLEAN_SENSOR,
                    )
                    self._fire_event(EVENT_CONSUMABLE, {EVENT_CONSUMABLE: CONSUMABLE_SENSOR})
                if self.device.status.mop_life == 0:
                    self._create_persistent_notification(
                        f'{NOTIFICATION_MOP_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get(CONSUMABLE_MOP_PAD)})',
                        NOTIFICATION_ID_REPLACE_MOP
                    )
                    self._fire_event(EVENT_CONSUMABLE, {EVENT_CONSUMABLE: CONSUMABLE_MOP_PAD})
                if self.device.status.silver_ion_life == 0:
                    self._create_persistent_notification(
                        f'{NOTIFICATION_SILVER_ION_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get(CONSUMABLE_SILVER_ION)})',
                        NOTIFICATION_ID_SILVER_ION
                    )
                    self._fire_event(EVENT_CONSUMABLE, {EVENT_CONSUMABLE: CONSUMABLE_SILVER_ION})
                if self.device.status.detergent_life == 0:
                    self._create_persistent_notification(
                        NOTIFICATION_DETERGENT_NO_LIFE_LEFT, NOTIFICATION_ID_REPLACE_DETERGENT
                    )
                    self._fire_event(EVENT_CONSUMABLE, {EVENT_CONSUMABLE: CONSUMABLE_DETERGENT})

            elif previous_value == 0 and not self.device.status.fast_mapping:
                self._fire_event(EVENT_TASK_STATUS, self.device.status.job)

    def _error_changed(self, previous_value=None) -> None:
        has_warning = self.device.status.has_warning
        if has_warning:
            self._fire_event(EVENT_WARNING, {EVENT_WARNING: self.device.status.error_description[0], "code": self.device.status.error.value})

            self._create_persistent_notification(
                self.device.status.error_description[0], NOTIFICATION_ID_WARNING
            )
        elif self._has_warning:
            self._has_warning = False
            self._remove_persistent_notification(NOTIFICATION_ID_WARNING)

        if self.device.status.has_error:
            description = self.device.status.error_description
            self._fire_event(EVENT_ERROR, {EVENT_ERROR: description[0], "code": self.device.status.error.value})

            description = f"### {description[0]}\n{description[1]}"
            image = self.device.status.error_image
            if image:
                description = f"{description}![image](data:{CONTENT_TYPE};base64,{image})"
            self._create_persistent_notification(
                description, f"{NOTIFICATION_ID_ERROR}_{self.device.status.error.value}"
            )

        self._has_warning = has_warning

    def _has_temporary_map_changed(self, previous_value=None) -> None:
        if self.device.status.has_temporary_map:
            self._fire_event(EVENT_WARNING, {EVENT_WARNING: NOTIFICATION_REPLACE_MULTI_MAP})

            self._create_persistent_notification(
                NOTIFICATION_REPLACE_MULTI_MAP
                if self.device.status.multi_map
                else NOTIFICATION_REPLACE_MAP,
                NOTIFICATION_ID_REPLACE_TEMPORARY_MAP,
            )
        else:
            self._fire_event(EVENT_WARNING, {EVENT_WARNING: NOTIFICATION_ID_REPLACE_TEMPORARY_MAP})

            self._remove_persistent_notification(
                NOTIFICATION_ID_REPLACE_TEMPORARY_MAP)

    def _create_persistent_notification(self, content, notification_id) -> None:
        if self._notify:
            if isinstance(self._notify, list):
                if notification_id == NOTIFICATION_ID_CLEANUP_COMPLETED:
                    if NOTIFICATION_ID_CLEANUP_COMPLETED not in self._notify:
                        return
                elif NOTIFICATION_ID_WARNING in notification_id:
                    if NOTIFICATION_ID_WARNING not in self._notify:
                        return
                elif NOTIFICATION_ID_ERROR in notification_id:
                    if NOTIFICATION_ID_ERROR not in self._notify:
                        return
                elif notification_id == NOTIFICATION_ID_DUST_COLLECTION or notification_id == NOTIFICATION_ID_CLEANING_PAUSED:
                    if "information" not in self._notify:
                        return
                elif notification_id != NOTIFICATION_ID_REPLACE_TEMPORARY_MAP: 
                    if "consumable" not in self._notify:
                        return

            persistent_notification.async_create(
                self.hass,
                content,
                title=self.device.name,
                notification_id=f"{DOMAIN}_{notification_id}",
            )

    def _remove_persistent_notification(self, notification_id) -> None:
        persistent_notification.async_dismiss(
            self.hass, f"{DOMAIN}_{notification_id}")

    def _notification_dismiss_listener(self, event) -> None:
        notifications = self.hass.data.get(persistent_notification.DOMAIN)

        if self._has_warning:
            if (
                f"{persistent_notification.DOMAIN}.{DOMAIN}_{NOTIFICATION_ID_WARNING}"
                not in notifications
            ):
                self._has_warning = False
                self.device.clear_warning()

        if self._two_factor_url:
            if (
                f"{persistent_notification.DOMAIN}.{DOMAIN}_{NOTIFICATION_ID_2FA_LOGIN}"
                not in notifications
            ):
                self._two_factor_url = None

    def _fire_event(self, event_id, data) -> None:
        event_data =  {ATTR_ENTITY_ID: generate_entity_id("vacuum.{}", self.device.name, hass=self.hass)}
        if data:
            event_data.update(data)
        self.hass.bus.fire(f"{DOMAIN}_{event_id}", event_data)

    async def _async_update_data(self) -> DreameVacuumDevice:
        """Handle device update. This function is only called once when the integration is added to Home Assistant."""
        try:
            await self.hass.async_add_executor_job(self.device.update)
            self.device.schedule_update()
            self.async_set_updated_data()
            return self.device
        except Exception as ex:
            LOGGER.error("Update failed: %s", traceback.format_exc())
            raise UpdateFailed(ex) from ex

    @callback
    def async_set_updated_data(self, device=None) -> None:
        if self._has_temporary_map != self.device.status.has_temporary_map:
            self._has_temporary_map_changed(self._has_temporary_map)
            self._has_temporary_map = self.device.status.has_temporary_map

        if self.device.token != self._token or self.device.host != self._host:
            data = self._entry.data.copy()
            self._host = self.device.host
            self._token = self.device.token
            data[CONF_HOST] = self._host
            data[CONF_TOKEN] = self._token
            self.hass.config_entries.async_update_entry(self._entry, data=data)
            
        if self._two_factor_url != self.device.two_factor_url:
            if self.device.two_factor_url:
                self._create_persistent_notification(
                    f"{NOTIFICATION_2FA_LOGIN}[{self.device.two_factor_url}]({self.device.two_factor_url})", NOTIFICATION_ID_2FA_LOGIN
                )
                self._fire_event(EVENT_2FA_LOGIN, {"url": self.device.two_factor_url})
            else:
                self._remove_persistent_notification(NOTIFICATION_ID_2FA_LOGIN)

            self._two_factor_url = self.device.two_factor_url

        self._available = self.device.available

        super().async_set_updated_data(self.device)

    @callback
    def async_set_update_error(self, ex) -> None:
        if self._available:
            self._available = self.device.available
            super().async_set_update_error(ex)
