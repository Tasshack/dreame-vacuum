"""Support for Dreame Vacuum buttons."""
from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from collections.abc import Callable
from functools import partial
import copy

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame import DreameVacuumAction


@dataclass
class DreameVacuumButtonEntityDescription(
    DreameVacuumEntityDescription, ButtonEntityDescription
):
    """Describes Dreame Vacuum Button entity."""

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
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.status.filter_life is not None
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
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.status.mop_life is not None
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
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.status.detergent_life is not None
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.START_AUTO_EMPTY,
        icon_fn=lambda value, device: "mdi:delete-off"
        if not device.status.dust_collection_available
        else "mdi:delete-restore"
        if device.status.auto_emptying
        else "mdi:delete-empty",
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.capability.auto_empty_base
        ),
    ),
    DreameVacuumButtonEntityDescription(
        action_key=DreameVacuumAction.CLEAR_WARNING,
        icon="mdi:clipboard-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        action_fn=lambda device: device.clear_warning(),
    ),
    DreameVacuumButtonEntityDescription(
        key="start_fast_mapping",
        icon="mdi:map-plus",
        entity_category=EntityCategory.CONFIG,
        action_fn=lambda device: device.start_fast_mapping(),
        exists_fn=lambda description, device: device.capability.lidar_navigation,
    ),
    DreameVacuumButtonEntityDescription(
        key="start_mapping",
        icon="mdi:broom",
        entity_category=EntityCategory.CONFIG,
        action_fn=lambda device: device.start_mapping(),
        entity_registry_enabled_default=False,
        exists_fn=lambda description, device: device.capability.lidar_navigation,
    ),
    DreameVacuumButtonEntityDescription(
        name_fn=lambda value, device: "Self-Clean Pause"
        if device.status.washing
        else "Self-Clean",
        key="self_clean",
        icon_fn=lambda value, device: "mdi:washing-machine-off"
        if device.status.washing or not device.status.washing_available
        else "mdi:washing-machine",
        action_fn=lambda device: device.toggle_washing(),
        exists_fn=lambda description, device: device.capability.self_wash_base,
    ),
    DreameVacuumButtonEntityDescription(
        name_fn=lambda value, device: "Stop Drying"
        if device.status.drying
        else "Start Drying",
        key="manual_drying",
        icon_fn=lambda value, device: "mdi:weather-sunny-off"
        if device.status.drying or not device.status.drying_available
        else "mdi:weather-sunny",
        action_fn=lambda device: device.toggle_drying(),
        exists_fn=lambda description, device: device.capability.self_wash_base,
    ),
    DreameVacuumButtonEntityDescription(
        key="water_tank_draining",
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        action_fn=lambda device: device.start_draining(),
        exists_fn=lambda description, device: device.capability.self_wash_base
        and device.capability.drainage,
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

    if coordinator.device.capability.shortcuts:
        update_shortcut_buttons = partial(
            async_update_shortcut_buttons, coordinator, {}, async_add_entities
        )
        coordinator.async_add_listener(update_shortcut_buttons)
        update_shortcut_buttons()


@callback
def async_update_shortcut_buttons(
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, list[DreameVacuumButtonEntity]],
    async_add_entities,
) -> None:
    if coordinator.device.status.shortcuts:
        new_ids = set([k for k, v in coordinator.device.status.shortcuts.items()])
    else:
        new_ids = set([])

    current_ids = set(current)
    new_entities = []

    for shortcut_id in current_ids - new_ids:
        async_remove_shortcut_buttons(shortcut_id, coordinator, current)

    for shortcut_id in new_ids - current_ids:
        current[shortcut_id] = [
            DreameVacuumShortcutButtonEntity(
                coordinator,
                DreameVacuumButtonEntityDescription(
                    icon="mdi:play-speed",
                    available_fn=lambda device: not device.status.started
                    and not device.status.shortcut_task
                    and not device.status.draining,
                ),
                shortcut_id,
            )
        ]
        new_entities = new_entities + current[shortcut_id]

    if new_entities:
        async_add_entities(new_entities)


def async_remove_shortcut_buttons(
    shortcut_id: str,
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, DreameVacuumButtonEntity],
) -> None:
    registry = entity_registry.async_get(coordinator.hass)
    entities = current[shortcut_id]
    for entity in entities:
        if entity.entity_id in registry.entities:
            registry.async_remove(entity.entity_id)
    del current[shortcut_id]


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

        if self.entity_description.action_fn is not None:
            await self._try_command(
                "Unable to call %s",
                self.entity_description.action_fn,
                self.device,
            )
        elif self.entity_description.action_key is not None:
            await self._try_command(
                "Unable to call %s",
                self.device.call_action,
                self.entity_description.action_key,
            )


class DreameVacuumShortcutButtonEntity(DreameVacuumEntity, ButtonEntity):
    """Defines a Dreame Vacuum Button entity."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumButtonEntityDescription,
        shortcut_id: int,
    ) -> None:
        """Initialize a Dreame Vacuum Shortcut Button entity."""
        self.shortcut_id = shortcut_id
        self.shortcut = None
        self.shortcuts = None
        if coordinator.device and coordinator.device.status.shortcuts:
            self.shortcuts = copy.deepcopy(coordinator.device.status.shortcuts)
            for k, v in self.shortcuts.items():
                if k == self.shortcut_id:
                    self.shortcut = v
                    break

        super().__init__(coordinator, description)
        self._attr_translation_key = None
        self.id = shortcut_id
        if self.id >= 32:
            self.id = self.id - 31
        self._attr_unique_id = f"{self.device.mac}_shortcut_{self.id}"
        self.entity_id = f"button.{self.device.name.lower()}_shortcut_{self.id}"

    def _set_id(self) -> None:
        """Set name of the entity"""
        key = "shortcut"
        if self.shortcut:
            name = self.shortcut.name
            if name.lower().startswith(key):
                name = name[8:]
            name = f"{key}_{name}"
        else:
            name = f"{key}_{self.id}"

        self._attr_name = f"{self.device.name} {name.replace('_', ' ').title()}"

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.shortcuts != self.device.status.shortcuts:
            self.shortcuts = copy.deepcopy(self.device.status.shortcuts)
            if self.shortcuts and self.shortcut_id in self.shortcuts:
                if self.shortcut != self.shortcuts[self.shortcut_id]:
                    self.shortcut = self.shortcuts[self.shortcut_id]
                    self._set_id()
            elif self.shortcut:
                self.shortcut = None
                self._set_id()

        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes of the entity."""
        return self.shortcut.__dict__

    async def async_press(self, **kwargs: Any) -> None:
        """Press the button."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        await self._try_command(
            "Unable to call %s",
            self.device.start_shortcut,
            self.shortcut_id,
        )
