from __future__ import annotations

from typing import Any, Dict
from dataclasses import dataclass
from collections.abc import Callable
from functools import partial

from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers import entity_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import async_generate_entity_id

from .coordinator import DreameVacuumDataUpdateCoordinator
from .const import DOMAIN, LOGGER
from .dreame.const import ATTR_VALUE
from .dreame import (
    DreameVacuumDevice,
    DreameVacuumProperty,
    DreameVacuumAutoSwitchProperty,
    DreameVacuumStrAIProperty,
    DreameVacuumAIProperty,
    DreameVacuumAction,
    DeviceException,
    DeviceUpdateFailedException,
    InvalidActionException,
    InvalidValueException,
    PROPERTY_TO_NAME,
    ACTION_TO_NAME,
    PROPERTY_AVAILABILITY,
    ACTION_AVAILABILITY,
)


@dataclass
class DreameVacuumEntityDescription:
    key: str = None
    name: str = None
    entity_category: str = None
    property_key: DreameVacuumProperty = None
    action_key: DreameVacuumAction = None
    exists_fn: Callable[[object, object], bool] = lambda description, device: bool(
        (description.action_key is not None and description.action_key in device.action_mapping)
        or description.property_key is None
        or (
            isinstance(description.property_key, DreameVacuumProperty)
            and description.property_key.value in device.data
        )
        or (
            isinstance(description.property_key, DreameVacuumAutoSwitchProperty)
            and device.auto_switch_data
            and description.property_key.name in device.auto_switch_data
        )
        or (
            (
                isinstance(description.property_key, DreameVacuumStrAIProperty)
                or isinstance(description.property_key, DreameVacuumAIProperty)
            )
            and device.ai_data
            and description.property_key.name in device.ai_data
        )
    )
    value_fn: Callable[[object, object], Any] = None
    value_int_fn: Callable[[object, str], int] = None
    format_fn: Callable[[str, object], Any] = None
    available_fn: Callable[[object], bool] = None
    icon_fn: Callable[[str, object], str] = None
    name_fn: Callable[[str, object], str] = None
    attrs_fn: Callable[[object, Dict]] = None


class DreameVacuumEntity(CoordinatorEntity[DreameVacuumDataUpdateCoordinator]):
    """Defines a base Dreame Vacuum entity."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumEntityDescription = None,
    ) -> None:
        if description is not None:
            if description.key is None:
                if description.property_key is not None:
                    name = PROPERTY_TO_NAME.get(description.property_key.name)
                    if name:
                        description.key = name[0]
                        description.name = name[1]
                    else:
                        description.key = description.property_key.name.lower()
                elif description.action_key is not None:
                    name = ACTION_TO_NAME.get(description.action_key)
                    if name:
                        description.key = name[0]
                        description.name = name[1]
                    else:
                        description.key = description.action_key.name.lower()

            if description.name is None and description.key is not None:
                description.name = description.key.replace("_", " ").title()
            elif description.key is None and description.name is not None:
                description.key = description.name.lower().replace(" ", "_").replace("-", "_")

            if description.value_fn is None and (description.property_key is not None or description.key is not None):
                if description.property_key is not None:
                    prop = description.property_key.name.lower()
                else:
                    prop = description.key.lower()
                if hasattr(coordinator.device.status, prop):
                    description.value_fn = lambda value, device: getattr(device.status, prop)

            if description.available_fn is None:
                if description.property_key is not None:
                    description.available_fn = PROPERTY_AVAILABILITY.get(description.property_key.name)
                elif description.action_key is not None:
                    description.available_fn = ACTION_AVAILABILITY.get(description.action_key.name)
                elif description.key is not None:
                    if description.key in PROPERTY_AVAILABILITY:
                        description.available_fn = PROPERTY_AVAILABILITY[description.key]
                    elif description.key in ACTION_AVAILABILITY:
                        description.available_fn = ACTION_AVAILABILITY[description.key]

        super().__init__(coordinator=coordinator)
        if description:
            if description.key is not None:
                self._attr_translation_key = description.key
            self.entity_description = description
            self._set_id()
            self._attr_unique_id = f"{self.device.mac}_{self.entity_description.key}"

    def _set_id(self) -> None:
        if self.entity_description:
            if self.entity_description.icon_fn is not None:
                self._attr_icon = self.entity_description.icon_fn(self.native_value, self.device)

            name = self.entity_description.name
            if self.entity_description.name_fn is not None:
                name = self.entity_description.name_fn(self.native_value, self.device)

            self._attr_name = f"{self.device.name} {name}"

    def _generate_entity_id(self, format) -> None:
        if self.entity_description.key:
            self.entity_id = async_generate_entity_id(
                format, f"{self.device.name} {self.entity_description.key}", hass=self.coordinator.hass
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        self._set_id()
        self.async_write_ha_state()

    async def _try_command(self, mask_error, func, *args, **kwargs) -> bool:
        """Call a vacuum command handling error messages."""
        if not self.device.device_connected:
            raise HomeAssistantError("Device is not available") from None

        try:
            await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
            return True
        except (InvalidActionException, InvalidValueException) as exc:
            LOGGER.error(mask_error, exc)
            raise HomeAssistantError(str(exc)) from None
        except (DeviceUpdateFailedException, DeviceException) as exc:
            if self.device.available:
                raise HomeAssistantError(str(exc)) from None
            return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Dreame Vacuum device."""
        if self.device.info:
            return DeviceInfo(
                connections={
                    (CONNECTION_NETWORK_MAC, self.device.mac)
                },
                identifiers={(DOMAIN, self.device.mac)},
                name=self.device.name,
                serial_number=self.device.status.serial_number if self.device.status else None,
                manufacturer=self.device.info.manufacturer,
                model=self.device.info.model,
                sw_version=self.device.info.firmware_version,
                hw_version=self.device.info.hardware_version,
            )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.device.device_connected:
            return False

        if self.entity_description.available_fn is not None:
            return self.entity_description.available_fn(self.device)
        return self._attr_available

    @property
    def native_value(self) -> Any:
        """Return the native value of the entity."""
        value = None
        if self.entity_description.property_key is not None:
            value = self.device.get_property(self.entity_description.property_key)
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(value, self.device)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes of the entity."""
        attrs = None
        if self.entity_description.attrs_fn is not None:
            attrs = self.entity_description.attrs_fn(self.device)
        elif self.entity_description.value_fn is not None or self.entity_description.value_int_fn is not None:
            if self.entity_description.property_key is not None:
                attrs = {ATTR_VALUE: self.device.get_property(self.entity_description.property_key)}
            elif self.entity_description.value_int_fn is not None:
                attrs = {ATTR_VALUE: self.entity_description.value_int_fn(self.native_value, self)}
        return attrs

    @property
    def device(self) -> DreameVacuumDevice:
        return self.coordinator.device
