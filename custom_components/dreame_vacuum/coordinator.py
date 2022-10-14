"""DataUpdateCoordinator for Dreame Vacuum."""
from __future__ import annotations

import traceback
import math
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_TOKEN,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .dreame import DreameVacuumDevice, DreameVacuumProperty
from .dreame.resources import CONSUMABLE_IMAGE
from .const import (
    DOMAIN,
    LOGGER,
    CONF_NOTIFY,
    CONF_COUNTRY,
    CONF_MAC,
    CONTENT_TYPE,
    NOTIFICATION_CLEANUP_COMPLETED,
    NOTIFICATION_MAIN_BRUSH_NO_LIFE_LEFT,
    NOTIFICATION_SIDE_BRUSH_NO_LIFE_LEFT,
    NOTIFICATION_FILTER_NO_LIFE_LEFT,
    NOTIFICATION_SENSOR_NO_LIFE_LEFT,
    NOTIFICATION_MOP_NO_LIFE_LEFT,
    NOTIFICATION_DUST_COLLECTION_NOT_PERFORMED,
    NOTIFICATION_RESUME_CLEANING,
    NOTIFICATION_RESUME_CLEANING_NOT_PERFORMED,
    NOTIFICATION_REPLACE_MULTI_MAP,
    NOTIFICATION_REPLACE_MAP,
    NOTIFICATION_ID_DUST_COLLECTION,
    NOTIFICATION_ID_CLEANING_PAUSED,
    NOTIFICATION_ID_REPLACE_MAIN_BRUSH,
    NOTIFICATION_ID_REPLACE_SIDE_BRUSH,
    NOTIFICATION_ID_REPLACE_FILTER,
    NOTIFICATION_ID_CLEAN_SENSOR,
    NOTIFICATION_ID_REPLACE_MOP,
    NOTIFICATION_ID_CLEANUP_COMPLETED,
    NOTIFICATION_ID_WARNING,
    NOTIFICATION_ID_ERROR,
    NOTIFICATION_ID_REPLACE_TEMPORARY_MAP,
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

        self.device = DreameVacuumDevice(
            entry.data[CONF_NAME],
            self._host,
            self._token,
            entry.data.get(CONF_MAC),
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            entry.data.get(CONF_COUNTRY),
        )

        if self._notify:
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

        if self._notify:
            hass.bus.async_listen(
                persistent_notification.EVENT_PERSISTENT_NOTIFICATIONS_UPDATED,
                self._notification_dismiss_listener,
            )

    def _dust_collection_changed(self, previous_value=None) -> None:
        if previous_value is not None:
            if self.device.status.auto_emptying_not_performed:
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

            self._create_persistent_notification(
                notification, NOTIFICATION_ID_CLEANING_PAUSED
            )
        else:
            self._remove_persistent_notification(
                NOTIFICATION_ID_CLEANING_PAUSED)

    def _task_status_changed(self, previous_value=None) -> None:
        if previous_value is not None and self.device.cleanup_completed:
            self._create_persistent_notification(
                NOTIFICATION_CLEANUP_COMPLETED, NOTIFICATION_ID_CLEANUP_COMPLETED
            )

            if self.device.status.main_brush_life == 0:
                self._create_persistent_notification(
                    f'{NOTIFICATION_MAIN_BRUSH_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get("main_brush")})',
                    NOTIFICATION_ID_REPLACE_MAIN_BRUSH,
                )
            if self.device.status.side_brush_life == 0:
                self._create_persistent_notification(
                    f'{NOTIFICATION_SIDE_BRUSH_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get("side_brush")})',
                    NOTIFICATION_ID_REPLACE_SIDE_BRUSH,
                )
            if self.device.status.filter_life == 0:
                self._create_persistent_notification(
                    f'{NOTIFICATION_FILTER_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get("filter")})',
                    NOTIFICATION_ID_REPLACE_FILTER,
                )
            if self.device.status.sensor_dirty_life == 0:
                self._create_persistent_notification(
                    f'{NOTIFICATION_SENSOR_NO_LIFE_LEFT}\n![image](data:{CONTENT_TYPE};base64,{CONSUMABLE_IMAGE.get("sensor")})',
                    NOTIFICATION_ID_CLEAN_SENSOR,
                )
            if self.device.status.mop_life == 0:
                self._create_persistent_notification(
                    NOTIFICATION_MOP_NO_LIFE_LEFT, NOTIFICATION_ID_REPLACE_MOP
                )

    def _error_changed(self, previous_value=None) -> None:
        has_warning = self.device.status.has_warning
        if has_warning:
            self._create_persistent_notification(
                self.device.status.error_description, NOTIFICATION_ID_WARNING
            )
        elif self._has_warning:
            self._has_warning = False
            self._remove_persistent_notification(NOTIFICATION_ID_WARNING)

        if self.device.status.has_error:
            description = self.device.status.error_description
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
            self._create_persistent_notification(
                NOTIFICATION_REPLACE_MULTI_MAP
                if self.device.status.multi_map
                else NOTIFICATION_REPLACE_MAP,
                NOTIFICATION_ID_REPLACE_TEMPORARY_MAP,
            )
        else:
            self._remove_persistent_notification(
                NOTIFICATION_ID_REPLACE_TEMPORARY_MAP)

    def _create_persistent_notification(self, content, notification_id) -> None:
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
        if self._has_warning:
            notifications = self.hass.data.get(persistent_notification.DOMAIN)
            if (
                f"{persistent_notification.DOMAIN}.{DOMAIN}_{NOTIFICATION_ID_WARNING}"
                not in notifications
            ):
                self._has_warning = False
                self.device.clear_warning()

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

        self._available = self.device.available

        super().async_set_updated_data(self.device)

    @callback
    def async_set_update_error(self, ex) -> None:
        if self._available:
            self._available = self.device.available
            super().async_set_update_error(ex)
