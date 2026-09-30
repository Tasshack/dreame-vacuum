"""Support for Dreame Vacuum times."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Callable

from homeassistant.components.time import (
    ENTITY_ID_FORMAT,
    TimeEntity,
    TimeEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription, remove_entities


@dataclass
class DreameVacuumTimeEntityDescription(DreameVacuumEntityDescription, TimeEntityDescription):
    """Describes Dreame Vacuum Time entity."""

    set_fn: Callable[[object, int]] = None


TIMES: tuple[DreameVacuumTimeEntityDescription, ...] = (
    DreameVacuumTimeEntityDescription(
        key="dnd_start",
        name="DnD Start",
        icon="mdi:clock-start",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.dnd,
    ),
    DreameVacuumTimeEntityDescription(
        key="dnd_end",
        name="DnD End",
        icon="mdi:clock-end",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.dnd,
    ),
    DreameVacuumTimeEntityDescription(
        key="off_peak_charging_start",
        name="Off-Peak Charging Start",
        icon="mdi:battery-lock-open",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.off_peak_charging,
    ),
    DreameVacuumTimeEntityDescription(
        key="off_peak_charging_end",
        name="Off-Peak Charging End",
        icon="mdi:battery-lock",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.off_peak_charging,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum time based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    remove_entities(hass, entry, coordinator, "time", TIMES)
    async_add_entities(
        DreameVacuumTimeEntity(coordinator, description)
        for description in TIMES
        if description.exists_fn(description, coordinator.device)
    )


class DreameVacuumTimeEntity(DreameVacuumEntity, TimeEntity):
    """Defines a Dreame Vacuum time."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumTimeEntityDescription,
    ) -> None:
        """Initialize Dreame Vacuum time."""
        if description.set_fn is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                prop = f"set_{description.property_key.name.lower()}"
            else:
                prop = f"set_{description.key.lower()}"
            if hasattr(coordinator.device, prop):
                description.set_fn = lambda device, value: getattr(device, prop)(value)

        super().__init__(coordinator, description)
        self._generate_entity_id(ENTITY_ID_FORMAT)
        value = super().native_value
        if value:
            values = value.split(":")
            self._attr_native_value = time(int(values[0]), int(values[1]), 0)
        else:
            self._attr_native_value = None

    @callback
    def _handle_coordinator_update(self) -> None:
        value = super().native_value
        if value:
            values = value.split(":")
            self._attr_native_value = time(int(values[0]), int(values[1]), 0)
        else:
            self._attr_native_value = None
        super()._handle_coordinator_update()

    async def async_set_value(self, value: time) -> None:
        """Set the Dreame Vacuum time value."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        if value is None:
            raise HomeAssistantError("Invalid value")

        value = str(value)[0:-3]
        if self.entity_description.set_fn is not None:
            await self._try_command("Unable to call: %s", self.entity_description.set_fn, self.device, value)
        elif self.entity_description.property_key is not None:
            await self._try_command(
                "Unable to call: %s",
                self.device.set_property,
                self.entity_description.property_key,
                value,
            )
        else:
            raise HomeAssistantError("Not implemented")

    @property
    def native_value(self):
        """Return the current Dreame Vacuum time value."""
        return self._attr_native_value
