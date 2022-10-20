"""Support for Dreame Vacuum switches."""
from __future__ import annotations

from typing import Any
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame import DreameVacuumProperty


@dataclass
class DreameVacuumSwitchEntityDescription(
    DreameVacuumEntityDescription, SwitchEntityDescription
):
    """Describes Dreame Vacuum Switch entity."""

    set_fn: Callable[[object, int]] = None


SWITCHES: tuple[DreameVacuumSwitchEntityDescription, ...] = (
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.RESUME_CLEANING,
        icon="mdi:play-pause",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CARPET_BOOST,
        icon_fn=lambda value, device: "mdi:upload-off" if value is 0 else "mdi:upload",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.OBSTACLE_AVOIDANCE,
        icon_fn=lambda value, device: "mdi:video-3d-off"
        if value is 0
        else "mdi:video-3d",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CUSTOMIZED_CLEANING,
        icon="mdi:home-search",
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CHILD_LOCK,
        icon_fn=lambda value, device: "mdi:lock-off" if value is 0 else "mdi:lock",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.TIGHT_MOPPING,
        icon="mdi:heating-coil",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.DND,
        name="DND",
        icon_fn=lambda value, device: "mdi:minus-circle-off-outline"
        if not value
        else "mdi:minus-circle-outline",
        format_fn=lambda value, device: bool(value),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.MULTI_FLOOR_MAP,
        icon_fn=lambda value, device: "mdi:layers-off" if value is 0 else "mdi:layers",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_DUST_COLLECTING,
        icon_fn=lambda value, device: "mdi:autorenew-off"
        if value is 0
        else "mdi:autorenew",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CARPET_RECOGNITION,
        icon="mdi:rug",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.SELF_CLEAN,
        icon="mdi:water-sync",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.WATER_ELECTROLYSIS,
        icon="mdi:lightning-bolt",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_WATER_REFILLING,
        icon="mdi:water-boiler-auto",
        entity_category=EntityCategory.CONFIG,
    ),    
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CARPET_AVOIDANCE,
        icon="mdi:close-box-outline",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: device.status.carpet_avoidance,
        format_fn=lambda value, device: 1 if value else 2,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_ADD_DETERGENT,
        icon="mdi:chart-bubble",
        value_fn=lambda value, device: device.status.auto_add_detergent,
        entity_category=EntityCategory.CONFIG,
        format_fn=lambda value, device: int(value),
    ),
    DreameVacuumSwitchEntityDescription(
        key="cleaning_sequence",
        icon="mdi:order-numeric-ascending",
        value_fn=lambda value, device: device.status.custom_order,
        exists_fn=lambda description, device: device.status.map_available,
        available_fn=lambda device: bool(
            not device.status.started
            and device.status.has_saved_map
            and device.status.segments
            and next(iter(device.status.segments.values())).order is not None
        ),
        set_fn=lambda device, value: device.set_segment_order(1, value),
        format_fn=lambda value, device: int(value),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        name="AI Obstacle Detection",
        key="ai_obstacle_detection",
        icon_fn=lambda value, device: "mdi:robot-off" if not value else "mdi:robot",
        value_fn=lambda value, device: device.status.ai_obstacle_detection,
        exists_fn=lambda description, device: device.status.ai_detection_available,
        set_fn=lambda device, value: device.set_ai_obstacle_detection(value),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        key="obstacle_picture",
        icon_fn=lambda value, device: "mdi:camera-off" if not value else "mdi:camera",
        value_fn=lambda value, device: device.status.obstacle_picture,
        exists_fn=lambda description, device: device.status.ai_detection_available,
        available_fn=lambda device: bool(
            device.status.ai_obstacle_detection and device.status.obstacle_picture is not None),
        set_fn=lambda device, value: device.set_obstacle_picture(value),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        key="pet_detection",
        icon_fn=lambda value, device: "mdi:dog-side-off" if not value else "mdi:dog-side",
        value_fn=lambda value, device: device.status.pet_detection,
        exists_fn=lambda description, device: device.status.ai_detection_available,
        available_fn=lambda device: bool(
            device.status.ai_obstacle_detection and device.status.pet_detection is not None),
        set_fn=lambda device, value: device.set_pet_detection(value),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        key="human_detection",
        icon_fn=lambda value, device: "mdi:account-off" if not value else "mdi:account",
        value_fn=lambda value, device: device.status.human_detection,
        exists_fn=lambda description, device: device.status.ai_detection_available,
        available_fn=lambda device: bool(
            device.status.ai_obstacle_detection and device.status.human_detection is not None),
        set_fn=lambda device, value: device.set_human_detection(value),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        key="furniture_detection",
        icon="mdi:table-furniture",
        value_fn=lambda value, device: device.status.furniture_detection,
        exists_fn=lambda description, device: device.status.ai_detection_available,
        available_fn=lambda device: bool(
            device.status.ai_obstacle_detection and device.status.furniture_detection is not None),
        set_fn=lambda device, value: device.set_furniture_detection(value),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        key="fluid_detection",
        icon_fn=lambda value, device: "mdi:water-off-outline" if not value else "mdi:water-outline",
        value_fn=lambda value, device: device.status.fluid_detection,
        exists_fn=lambda description, device: device.status.ai_detection_available,
        available_fn=lambda device: bool(
            device.status.ai_obstacle_detection and device.status.fluid_detection is not None),
        set_fn=lambda device, value: device.set_fluid_detection(value),
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum switch based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DreameVacuumSwitchEntity(coordinator, description)
        for description in SWITCHES
        if description.exists_fn(description, coordinator.device)
    )


class DreameVacuumSwitchEntity(DreameVacuumEntity, SwitchEntity):
    """Defines a Dreame Vacuum Switch entity."""

    entity_description: DreameVacuumSwitchEntityDescription

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumSwitchEntityDescription,
    ) -> None:
        """Initialize a Dreame Vacuum switch entity."""
        super().__init__(coordinator, description)
        self._attr_is_on = bool(self.native_value)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_is_on = bool(self.native_value)
        super()._handle_coordinator_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the Dreame Vacuum sync receive switch."""
        await self.async_set_state(0)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the Dreame Vacuum sync receive switch."""
        await self.async_set_state(1)

    async def async_set_state(self, state) -> None:
        """Turn on or off the Dreame Vacuum sync receive switch."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        value = int(state)
        if self.entity_description.format_fn is not None:
            value = self.entity_description.format_fn(state, self.device)

        if self.entity_description.property_key is not None:
            await self._try_command(
                "Unable to call: %s",
                self.device.set_property,
                self.entity_description.property_key,
                value,
            )
        elif self.entity_description.set_fn is not None:
            await self._try_command(
                "Unable to call: %s", self.entity_description.set_fn, self.device, value
            )
