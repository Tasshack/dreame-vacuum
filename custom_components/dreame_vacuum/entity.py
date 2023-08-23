from __future__ import annotations

from typing import Any, Dict
from dataclasses import dataclass
from collections.abc import Callable
from functools import partial

from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError

from .coordinator import DreameVacuumDataUpdateCoordinator
from .const import DOMAIN, LOGGER, ATTR_VALUE
from .dreame import (
    DreameVacuumDevice,
    DreameVacuumProperty,
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
        (
            description.action_key is not None
            and description.action_key in device.action_mapping
        )
        or description.property_key is None
        or description.property_key.value in device.data
    )
    value_fn: Callable[[object, object], Any] = None
    format_fn: Callable[[str, object], Any] = None
    available_fn: Callable[[object], bool] = None
    icon_fn: Callable[[str, object], str] = None
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
                    name = PROPERTY_TO_NAME.get(description.property_key)
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

            if description.available_fn is None:
                if description.property_key is not None:
                    description.available_fn = PROPERTY_AVAILABILITY.get(
                        description.property_key)
                elif description.action_key is not None:
                    description.available_fn = ACTION_AVAILABILITY.get(
                        description.action_key)

        super().__init__(coordinator=coordinator)
        if description:
            if description.key is not None:
                self._attr_translation_key = description.key
            self.entity_description = description
            self._set_id()

    def _set_id(self) -> None:
        if self.entity_description:
            if self.entity_description.icon_fn is not None:
                self._attr_icon = self.entity_description.icon_fn(
                    self.native_value, self.device
                )

            self._attr_name = f"{self.device.name} {self.entity_description.name}"
            self._attr_unique_id = f"{self.device.mac}_{self.entity_description.key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.entity_description.icon_fn is not None:
            self._attr_icon = self.entity_description.icon_fn(
                self.native_value, self.device
            )
        super()._handle_coordinator_update()

    async def _try_command(self, mask_error, func, *args, **kwargs) -> bool:
        """Call a vacuum command handling error messages."""
        try:
            await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
            return True
        except (InvalidActionException, InvalidValueException) as exc:
            LOGGER.error(mask_error, exc)
            raise ValueError(str(exc)) from None
        except (DeviceUpdateFailedException, DeviceException) as exc:
            if self.coordinator._available:
                raise HomeAssistantError(str(exc)) from None
            return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Dreame Vacuum device."""
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, self.device.mac)},
            identifiers={(DOMAIN, self.device.mac)},
            name=self.device.name,
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
            value = self.device.get_property(
                self.entity_description.property_key)
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(value, self.device)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes of the entity."""
        attrs = None
        if self.entity_description.value_fn is not None:
            if self.entity_description.property_key is not None:
                attrs = {
                    ATTR_VALUE: self.device.get_property(
                        self.entity_description.property_key
                    )
                }
            elif self.entity_description.attrs_fn is not None:
                attrs = self.entity_description.attrs_fn(self.device)
        return attrs

    @property
    def device(self) -> DreameVacuumDevice:
        return self.coordinator.device
