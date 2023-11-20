"""Support for Dreame Vacuum numbers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import (
    ENTITY_ID_FORMAT,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, UNIT_MINUTES, UNIT_AREA, UNIT_PERCENT

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame import DreameVacuumAction, DreameVacuumProperty


@dataclass
class DreameVacuumNumberEntityDescription(
    DreameVacuumEntityDescription, NumberEntityDescription
):
    """Describes Dreame Vacuum Number entity."""

    mode: NumberMode = NumberMode.AUTO
    post_action: DreameVacuumAction = None
    set_fn: Callable[[object, int]] = None


NUMBERS: tuple[DreameVacuumNumberEntityDescription, ...] = (
    DreameVacuumNumberEntityDescription(
        property_key=DreameVacuumProperty.VOLUME,
        icon_fn=lambda value, device: "mdi:volume-off"
        if value == 0
        else "mdi:volume-high",
        mode=NumberMode.SLIDER,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.CONFIG,
        post_action=DreameVacuumAction.TEST_SOUND,
    ),
    DreameVacuumNumberEntityDescription(
        property_key=DreameVacuumProperty.MOP_CLEANING_REMAINDER,
        icon="mdi:alarm-check",
        mode=NumberMode.BOX,
        native_unit_of_measurement=UNIT_MINUTES,
        native_min_value=0,
        native_max_value=180,
        native_step=15,
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: not device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumNumberEntityDescription(
        key="self_clean_area",
        icon_fn=lambda value, device: "mdi:texture-box"
        if device.status.self_clean_value
        or (device.status.current_map and not device.status.has_saved_map)
        else "mdi:checkbox-blank-off-outline",
        mode=NumberMode.SLIDER,
        native_unit_of_measurement=UNIT_AREA,
        exists_fn=lambda description, device: device.capability.self_wash_base,
        native_min_value=10,
        native_max_value=35,
        native_step=1,
        entity_category=None,
        value_fn=lambda value, device: (
            10
            if device.status.self_clean_value < 10
            else 35
            if device.status.self_clean_value > 35
            else device.status.self_clean_value
        )
        if device.status.self_clean_value and device.status.self_clean_value > 0
        else 20,
    ),
    DreameVacuumNumberEntityDescription(
        key="self_clean_time",
        icon="mdi:table-clock",
        mode=NumberMode.SLIDER,
        native_unit_of_measurement=UNIT_MINUTES,
        exists_fn=lambda description, device: device.capability.self_clean_frequency,
        native_min_value=10,
        native_max_value=50,
        native_step=1,
        entity_category=None,
        value_fn=lambda value, device: (
            10
            if device.status.self_clean_value < 10
            else 50
            if device.status.self_clean_value > 50
            else device.status.self_clean_value
        )
        if device.status.self_clean_value and device.status.self_clean_value > 0
        else 25,
    ),
    DreameVacuumNumberEntityDescription(
        property_key=DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS,
        icon="mdi:brightness-percent",
        mode=NumberMode.SLIDER,
        native_min_value=40,
        native_max_value=100,
        native_step=1,
        exists_fn=lambda description, device: device.capability.stream_status and device.capability.fill_light,  # and DreameVacuumEntityDescription().exists_fn(description, device),
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum number based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DreameVacuumNumberEntity(coordinator, description)
        for description in NUMBERS
        if description.exists_fn(description, coordinator.device)
    )


class DreameVacuumNumberEntity(DreameVacuumEntity, NumberEntity):
    """Defines a Dreame Vacuum number."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumNumberEntityDescription,
    ) -> None:
        """Initialize Dreame Vacuum number."""
        if description.set_fn is None and (
            description.property_key is not None or description.key is not None
        ):
            if description.property_key is not None:
                prop = f"set_{description.property_key.name.lower()}"
            else:
                prop = f"set_{description.key.lower()}"
            if hasattr(coordinator.device, prop):
                description.set_fn = lambda device, value: getattr(device, prop)(value)

        super().__init__(coordinator, description)
        self._generate_entity_id(ENTITY_ID_FORMAT)
        self._attr_mode = description.mode
        self._attr_native_value = super().native_value

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = super().native_value
        super()._handle_coordinator_update()

    async def async_set_native_value(self, value: float) -> None:
        """Set the Dreame Vacuum number value."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        value = int(value)
        if self.entity_description.format_fn is not None:
            value = self.entity_description.format_fn(value, self.device)

        if value is None:
            raise HomeAssistantError("Invalid value")

        result = False

        if self.entity_description.set_fn is not None:
            result = await self._try_command(
                "Unable to call: %s", self.entity_description.set_fn, self.device, value
            )
        elif self.entity_description.property_key is not None:
            result = await self._try_command(
                "Unable to call: %s",
                self.device.set_property,
                self.entity_description.property_key,
                value,
            )

        if result and self.entity_description.post_action is not None:
            await self._try_command(
                "Unable to call %s",
                self.device.call_action,
                self.entity_description.post_action,
            )

    @property
    def native_value(self) -> int | None:
        """Return the current Dreame Vacuum number value."""
        return self._attr_native_value
