"""Support for Dreame Vacuum buttons."""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame import DreameVacuumAction


@dataclass
class DreameVacuumButtonEntityDescription(DreameVacuumEntityDescription, ButtonEntityDescription):
    """Describes Dreame Vacuum Button entity."""

    parameters_fn: Callable[[object], Any] = None
    action_fn: Callable[[object]] = None


BUTTONS: tuple[ButtonEntityDescription, ...] = (
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.RESET_MAIN_BRUSH,
        icon="mdi:car-turbocharger",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.status.main_brush_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.RESET_SIDE_BRUSH,
        icon="mdi:pinwheel-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.status.side_brush_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.RESET_FILTER,
        icon="mdi:air-filter",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.status.filter_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.RESET_SENSOR,
        icon="mdi:radar",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.status.sensor_dirty_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.RESET_MOP_PAD,
        icon="mdi:hydro-power",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.status.mop_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.RESET_SILVER_ION,
        icon="mdi:shimmer",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.status.silver_ion_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.RESET_DETERGENT,
        icon="mdi:chart-bubble",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.status.detergent_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.START_AUTO_EMPTY,
        icon_fn=lambda value, device: (
            "mdi:delete-off"
            if not device.status.dust_collection_available
            else "mdi:delete-restore" if device.status.auto_emptying else "mdi:delete-empty"
        ),
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.status.auto_empty_base_available
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.CLEAR_WARNING,
        icon="mdi:clipboard-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        parameters_fn=lambda device: [device.status.error.value],
    ),
    DreameVacuumButtonEntityDescription(
        key="start_fast_mapping",
        icon="mdi:map-plus",
        entity_category=EntityCategory.CONFIG,
        available_fn=lambda device: device.status.mapping_available,
        action_fn=lambda device: device.start_fast_mapping(),
        exists_fn=lambda description, device: device.status.lidar_navigation,
    ),
    DreameVacuumButtonEntityDescription(
        key="start_mapping",
        icon="mdi:broom",
        entity_category=EntityCategory.CONFIG,
        available_fn=lambda device: device.status.mapping_available,
        action_fn=lambda device: device.start_mapping(),
        entity_registry_enabled_default=False,
        exists_fn=lambda description, device: device.status.lidar_navigation,
    ),
    DreameVacuumButtonEntityDescription(
        name="Self-Clean",
        key="self_clean",
        icon="mdi:washing-machine",
        available_fn=lambda device: bool(
            device.status.washing_available or device.status.returning_to_wash_paused or device.status.washing_paused
        ),
        action_fn=lambda device: device.start_washing(),
        exists_fn=lambda description, device: device.status.self_wash_base_available,
    ),
    DreameVacuumButtonEntityDescription(
        name="Self-Clean Pause",
        key="self_clean_pause",
        icon="mdi:washing-machine-off",
        available_fn=lambda device: device.status.washing,
        action_fn=lambda device: device.pause_washing(),
        exists_fn=lambda description, device: device.status.self_wash_base_available,
    ),
    DreameVacuumButtonEntityDescription(
        key="start_drying",
        icon="mdi:weather-sunny",
        available_fn=lambda device: bool(device.status.drying_available and not device.status.drying),
        action_fn=lambda device: device.start_drying(),
        exists_fn=lambda description, device: device.status.self_wash_base_available,
    ),
    DreameVacuumButtonEntityDescription(
        key="stop_drying",
        icon="mdi:weather-sunny-off",
        available_fn=lambda device: bool(device.status.drying_available and device.status.drying),
        action_fn=lambda device: device.stop_drying(),
        exists_fn=lambda description, device: device.status.self_wash_base_available,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum Button based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DreameVacuumButtonEntity(coordinator, description)
        for description in BUTTONS
        if description.exists_fn(description, coordinator.device)
    )


class DreameVacuumButtonEntity(DreameVacuumEntity, ButtonEntity):
    """Defines a Dreame Vacuum Button entity."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumButtonEntityDescription,
    ) -> None:
        """Initialize a Dreame Vacuum Button entity."""
        super().__init__(coordinator, description)

    async def async_press(self, **kwargs: Any) -> None:
        """Press the button."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        parameters = None
        if self.entity_description.parameters_fn is not None:
            parameters = self.entity_description.parameters_fn(self.device)

        if self.entity_description.action_key is not None:
            await self._try_command(
                "Unable to call %s",
                self.device.call_action,
                self.entity_description.action_key,
                parameters,
            )
        elif self.entity_description.action_fn is not None:
            await self._try_command(
                "Unable to call %s",
                self.entity_description.action_fn,
                self.device,
            )
