"""Support for Dreame Vacuum numbers."""

from __future__ import annotations
import copy

from dataclasses import dataclass
from functools import partial
from typing import Callable
from .dreame import DreameVacuumCleaningMode

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
from homeassistant.helpers import entity_registry

from .const import DOMAIN, UNIT_MINUTES, UNIT_HOURS, UNIT_AREA, UNIT_PERCENT

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame import DreameVacuumAction, DreameVacuumProperty


def WETNESS_LEVEL_TO_ICON(wetness, max):
    if wetness:
        if wetness > max:
            return "mdi:water-plus"
        if wetness < 6:
            return "mdi:water-minus"
        return "mdi:water"
    return "mdi:water-off"


@dataclass
class DreameVacuumNumberEntityDescription(DreameVacuumEntityDescription, NumberEntityDescription):
    """Describes Dreame Vacuum Number entity."""

    mode: NumberMode = NumberMode.AUTO
    set_fn: Callable[[object, int]] = None
    max_value_fn: Callable[[object], int] = None
    min_value_fn: Callable[[object], int] = None
    segment_icon_fn: Callable[[str, object, object], str] = None
    segment_available_fn: Callable[[object, object], bool] = None
    segment_list_fn: Callable[[object], bool] = None


NUMBERS: tuple[DreameVacuumNumberEntityDescription, ...] = (
    DreameVacuumNumberEntityDescription(
        property_key=DreameVacuumProperty.VOLUME,
        icon_fn=lambda value, device: (
            "mdi:volume-off"
            if not value
            else "mdi:volume-low" if value <= 35 else "mdi:volume-medium" if value <= 65 else "mdi:volume-high"
        ),
        mode=NumberMode.SLIDER,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.CONFIG,
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
        icon_fn=lambda value, device: (
            "mdi:texture-box"
            if device.status.self_clean_value or (device.status.current_map and not device.status.has_saved_map)
            else "mdi:checkbox-blank-off-outline"
        ),
        mode=NumberMode.SLIDER,
        native_unit_of_measurement=UNIT_AREA,
        exists_fn=lambda description, device: device.capability.self_wash_base
        and not device.capability.mop_clean_frequency,
        min_value_fn=lambda device: device.status.self_clean_area_min,
        max_value_fn=lambda device: device.status.self_clean_area_max,
        native_step=1,
        entity_category=None,
        value_fn=lambda value, device: (
            (
                device.status.self_clean_area_min
                if device.status.self_clean_value < device.status.self_clean_area_min
                else (
                    device.status.self_clean_area_max
                    if device.status.self_clean_value > device.status.self_clean_area_max
                    else device.status.self_clean_value
                )
            )
            if device.status.self_clean_value and device.status.self_clean_value > 0
            else device.status.self_clean_area_default
        ),
    ),
    DreameVacuumNumberEntityDescription(
        key="self_clean_time",
        icon="mdi:table-clock",
        mode=NumberMode.SLIDER,
        native_unit_of_measurement=UNIT_MINUTES,
        exists_fn=lambda description, device: device.capability.self_clean_frequency
        and not device.capability.mop_clean_frequency,
        min_value_fn=lambda device: device.status.self_clean_time_min,
        max_value_fn=lambda device: device.status.self_clean_time_max,
        native_step=1,
        entity_category=None,
        value_fn=lambda value, device: (
            (
                device.status.self_clean_time_min
                if device.status.self_clean_value < device.status.self_clean_time_min
                else (
                    device.status.self_clean_time_max
                    if device.status.self_clean_value > device.status.self_clean_time_max
                    else device.status.self_clean_value
                )
            )
            if device.status.self_clean_value and device.status.self_clean_value > 0
            else device.status.self_clean_time_default
        ),
    ),
    DreameVacuumNumberEntityDescription(
        property_key=DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS,
        icon="mdi:brightness-percent",
        mode=NumberMode.SLIDER,
        native_min_value=40,
        native_max_value=100,
        native_step=1,
        exists_fn=lambda description, device: device.capability.camera_streaming
        and device.capability.fill_light,  # and DreameVacuumEntityDescription().exists_fn(description, device),
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumNumberEntityDescription(
        property_key=DreameVacuumProperty.WETNESS_LEVEL,
        icon_fn=lambda value, device: (
            "mdi:water-off"
            if (
                not (device.status.water_tank_or_mop_installed)
                or device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING
            )
            else WETNESS_LEVEL_TO_ICON(
                device.status.wetness_level, 14 if device.capability.mop_clean_frequency else 26
            )
        ),
        mode=NumberMode.SLIDER,
        native_min_value=1,
        max_value_fn=lambda device: 15 if device.capability.mop_clean_frequency else 32,
        native_step=1,
        exists_fn=lambda description, device: device.capability.wetness_level        
    ),
    DreameVacuumNumberEntityDescription(
        property_key=DreameVacuumProperty.DRYING_TIME,
        icon="mdi:sun-clock",
        native_unit_of_measurement=UNIT_HOURS,
        mode=NumberMode.SLIDER,
        native_min_value=2,
        native_max_value=12,
        native_step=1,
        entity_category=None,
        exists_fn=lambda description, device: device.capability.mop_clean_frequency
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
)


SEGMENT_NUMBERS: tuple[DreameVacuumNumberEntityDescription, ...] = (
    DreameVacuumNumberEntityDescription(
        key=DreameVacuumProperty.WETNESS_LEVEL.name.lower(),
        segment_icon_fn=lambda value, device, segment: (
            WETNESS_LEVEL_TO_ICON(segment.wetness_level, 14 if device.capability.mop_clean_frequency else 26)
            if segment
            else "mdi:water-off"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.wetness_level is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.SWEEPING.value
            and not device.status.cleangenius_cleaning
        ),
        mode=NumberMode.SLIDER,
        native_min_value=1,
        native_max_value=32,
        native_step=1,
        value_fn=lambda device, segment: segment.wetness_level,
        exists_fn=lambda description, device: device.capability.wetness_level,
        segment_list_fn=lambda device: device.status.current_segments,
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

    update_segment_numbers = partial(async_update_segment_numbers, coordinator, {}, async_add_entities)
    coordinator.async_add_listener(update_segment_numbers)
    update_segment_numbers()


@callback
def async_update_segment_numbers(
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, list[DreameVacuumSegmentNumberEntity]],
    async_add_entities,
) -> None:
    new_ids = []
    if coordinator.device and coordinator.device.status.map_list:
        for k, v in coordinator.device.status.map_data_list.items():
            for j, s in v.segments.items():
                if j not in new_ids:
                    new_ids.append(j)

    new_ids = set(new_ids)
    current_ids = set(current)

    for segment_id in current_ids - new_ids:
        async_remove_segment_numbers(segment_id, coordinator, current)

    new_entities = []
    for segment_id in new_ids - current_ids:
        current[segment_id] = [
            DreameVacuumSegmentNumberEntity(coordinator, description, segment_id)
            for description in SEGMENT_NUMBERS
            if description.exists_fn(description, coordinator.device)
        ]
        new_entities = new_entities + current[segment_id]

    if new_entities:
        async_add_entities(new_entities)


def async_remove_segment_numbers(
    segment_id: str,
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, DreameVacuumSegmentNumberEntity],
) -> None:
    registry = entity_registry.async_get(coordinator.hass)
    entities = current[segment_id]
    for entity in entities:
        if entity.entity_id in registry.entities:
            registry.async_remove(entity.entity_id)
    del current[segment_id]


class DreameVacuumNumberEntity(DreameVacuumEntity, NumberEntity):
    """Defines a Dreame Vacuum number."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumNumberEntityDescription,
    ) -> None:
        """Initialize Dreame Vacuum number."""
        if description.set_fn is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                prop = f"set_{description.property_key.name.lower()}"
            else:
                prop = f"set_{description.key.lower()}"
            if hasattr(coordinator.device, prop):
                description.set_fn = lambda device, value: getattr(device, prop)(value)

        if description.min_value_fn:
            description.native_min_value = description.min_value_fn(coordinator.device)
        if description.max_value_fn:
            description.native_max_value = description.max_value_fn(coordinator.device)

        super().__init__(coordinator, description)
        self._generate_entity_id(ENTITY_ID_FORMAT)
        self._attr_mode = description.mode
        self._attr_native_value = super().native_value

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = super().native_value
        if self.entity_description.min_value_fn:
            self.entity_description.native_min_value = self.entity_description.min_value_fn(self.device)
        if self.entity_description.max_value_fn:
            self.entity_description.native_max_value = self.entity_description.max_value_fn(self.device)
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
            result = await self._try_command("Unable to call: %s", self.entity_description.set_fn, self.device, value)
        elif self.entity_description.property_key is not None:
            result = await self._try_command(
                "Unable to call: %s",
                self.device.set_property,
                self.entity_description.property_key,
                value,
            )

    @property
    def native_value(self) -> int | None:
        """Return the current Dreame Vacuum number value."""
        return self._attr_native_value


class DreameVacuumSegmentNumberEntity(DreameVacuumEntity, NumberEntity):
    """Defines a Dreame Vacuum Segment number."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumNumberEntityDescription,
        segment_id: int,
    ) -> None:
        """Initialize Dreame Vacuum Segment Number."""
        self.segment_id = segment_id
        self.segment = None
        self.segments = None
        if coordinator.device:
            self.segments = copy.deepcopy(description.segment_list_fn(coordinator.device))
            if segment_id in self.segments:
                self.segment = self.segments[segment_id]

        if description.set_fn is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                segment_set_prop = f"set_segment_{description.property_key.name.lower()}"
            else:
                segment_set_prop = f"set_segment_{description.key.lower()}"
            if hasattr(coordinator.device, segment_set_prop):
                description.set_fn = lambda device, segment_id, value: getattr(device, segment_set_prop)(
                    segment_id, value
                )

        super().__init__(coordinator, description)
        self._attr_unique_id = f"{self.device.mac}_room_{segment_id}_{description.key.lower()}"
        self.entity_id = f"number.{self.device.name.lower()}_room_{segment_id}_{description.key.lower()}"
        self._attr_native_value = None
        if self.segment:
            self._attr_native_value = description.value_fn(coordinator.device, self.segment)

    def _set_id(self) -> None:
        """Set name, unique id and icon of the entity"""
        if self.entity_description.name == "":
            name = f"room_{self.segment_id}_{self.entity_description.key}"
        elif self.segment:
            name = f"{self.entity_description.key}_{self.segment.name}"
        else:
            name = f"{self.entity_description.key}_room_unavailable"

        self._attr_name = name.replace('_', ' ').title()

        if self.entity_description.segment_icon_fn is not None:
            self._attr_icon = self.entity_description.segment_icon_fn(
                self._attr_native_value, self.device, self.segment
            )
        elif self.segment:
            self._attr_icon = self.segment.icon
        else:
            self._attr_icon = "mdi:home-off-outline"

    @callback
    def _handle_coordinator_update(self) -> None:
        device_segments = self._device_segments
        if self.segments != device_segments:
            self.segments = copy.deepcopy(device_segments)
            if self.segments and self.segment_id in self.segments:
                if self.segment != self.segments[self.segment_id]:
                    self.segment = self.segments[self.segment_id]
                    if self.entity_description.min_value_fn:
                        self.entity_description.native_min_value = self.entity_description.min_value_fn(self.device)
                    if self.entity_description.max_value_fn:
                        self.entity_description.native_max_value = self.entity_description.max_value_fn(self.device)
                    self._attr_native_value = self.entity_description.value_fn(self.device, self.segment)
                    self._set_id()
            elif self.segment:
                self.segment = None
                self._set_id()

        self.async_write_ha_state()

    @property
    def _device_segments(self):
        return self.entity_description.segment_list_fn(self.device)

    async def async_set_native_value(self, value: int) -> None:
        """Set the Dreame Vacuum number value."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        await self._try_command(
            "Unable to call %s",
            self.entity_description.set_fn,
            self.device,
            self.segment_id,
            value,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.device.device_connected or (self._attr_available and self.segment is None):
            return False
        if self.entity_description.segment_available_fn is not None:
            return self.entity_description.segment_available_fn(self.device, self.segment)
        return self._attr_available

    @property
    def native_value(self) -> str | None:
        """Return the current Dreame Vacuum number value."""
        if self.segment:
            return self._attr_native_value
