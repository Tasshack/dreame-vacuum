"""Support for Dreame Vacuum selects."""
from __future__ import annotations

import copy
from enum import IntEnum
import voluptuous as vol
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform, entity_registry

from .const import (
    DOMAIN,
    ATTR_VALUE,
    UNIT_TIMES,
    INPUT_CYCLE,
    SERVICE_SELECT_NEXT,
    SERVICE_SELECT_PREVIOUS,
    SERVICE_SELECT_FIRST,
    SERVICE_SELECT_LAST,
)

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import (
    DreameVacuumEntity,
    DreameVacuumEntityDescription,
)

from .dreame import (
    DreameVacuumProperty,
    DreameVacuumAutoSwitchProperty,
    DreameVacuumSuctionLevel,
    DreameVacuumCleaningMode,
    DreameVacuumWaterVolume,
    DreameVacuumMopPadHumidity,
    DreameVacuumCarpetSensitivity,
    DreameVacuumCarpetCleaning,
    DreameVacuumMopWashLevel,
    DreameVacuumMoppingType,
    DreameVacuumWiderCornerCoverage,
    DreameVacuumFloorMaterial,
    SUCTION_LEVEL_CODE_TO_NAME,
    WATER_VOLUME_CODE_TO_NAME,
    MOP_PAD_HUMIDITY_CODE_TO_NAME,
    CLEANING_MODE_CODE_TO_NAME,
    FLOOR_MATERIAL_CODE_TO_NAME,
)

SUCTION_LEVEL_TO_ICON = {
    DreameVacuumSuctionLevel.QUIET: "mdi:fan-speed-1",
    DreameVacuumSuctionLevel.STANDARD: "mdi:fan-speed-2",
    DreameVacuumSuctionLevel.STRONG: "mdi:fan-speed-3",
    DreameVacuumSuctionLevel.TURBO: "mdi:weather-windy",
}

WATER_VOLUME_TO_ICON = {
    DreameVacuumWaterVolume.LOW: "mdi:water-minus",
    DreameVacuumWaterVolume.MEDIUM: "mdi:water",
    DreameVacuumWaterVolume.HIGH: "mdi:water-plus",
}

MOP_PAD_HUMIDITY_TO_ICON = {
    DreameVacuumMopPadHumidity.SLIGHTLY_DRY: "mdi:water-minus",
    DreameVacuumMopPadHumidity.MOIST: "mdi:water",
    DreameVacuumMopPadHumidity.WET: "mdi:water-plus",
}

CLEANING_MODE_TO_ICON = {
    DreameVacuumCleaningMode.SWEEPING: "mdi:broom",
    DreameVacuumCleaningMode.MOPPING: "mdi:cup-water",
    DreameVacuumCleaningMode.SWEEPING_AND_MOPPING: "mdi:hydro-power",
    DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING: "mdi:hydro-power",
}

FLOOR_MATERIAL_TO_ICON = {
    DreameVacuumFloorMaterial.NONE: "mdi:checkbox-blank",
    DreameVacuumFloorMaterial.TILE: "mdi:apps",
    DreameVacuumFloorMaterial.WOOD: "mdi:pine-tree-box",
}


@dataclass
class DreameVacuumSelectEntityDescription(
    DreameVacuumEntityDescription, SelectEntityDescription
):
    """Describes Dreame Vacuum Select entity."""

    set_fn: Callable[[object, int, int]] = None
    options: Callable[[object, object], list[str]] = None
    segment_available_fn: Callable[[object, object], bool] = None
    segment_list_fn: Callable[[object], bool] = None


SELECTS: tuple[DreameVacuumSelectEntityDescription, ...] = (
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.SUCTION_LEVEL,
        icon_fn=lambda value, device: "mdi:fan-off"
        if device.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING
        else SUCTION_LEVEL_TO_ICON.get(device.status.suction_level, "mdi:fan"),
        value_int_fn=lambda value, device: DreameVacuumSuctionLevel[value.upper()],
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.WATER_VOLUME,
        icon_fn=lambda value, device: "mdi:water-off"
        if (
            not (
                device.status.water_tank_or_mop_installed
                or device.status.auto_mount_mop
            )
            or device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING
        )
        else WATER_VOLUME_TO_ICON.get(device.status.water_volume, "mdi:water"),
        value_int_fn=lambda value, device: DreameVacuumWaterVolume[value.upper()],
        exists_fn=lambda description, device: bool(
            not device.capability.self_wash_base
            and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_MODE,
        icon_fn=lambda value, device: CLEANING_MODE_TO_ICON.get(
            device.status.cleaning_mode, "mdi:broom"
        ),
        value_int_fn=lambda value, device: DreameVacuumCleaningMode[value.upper()],
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CARPET_SENSITIVITY,
        icon="mdi:rug",
        value_int_fn=lambda value, device: DreameVacuumCarpetSensitivity[value.upper()],
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CARPET_CLEANING,
        icon="mdi:close-box-outline",
        value_int_fn=lambda value, device: DreameVacuumCarpetCleaning[value.upper()],
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.mop_pad_unmounting
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.AUTO_EMPTY_FREQUENCY,
        icon_fn=lambda value, device: f"mdi:numeric-{value[0]}-box-multiple-outline",
        options=lambda device, segment: [f"{i}{UNIT_TIMES}" for i in range(1, 4)],
        entity_category=None,
        value_fn=lambda value, device: f"{value}{UNIT_TIMES}",
        value_int_fn=lambda value, device: int(value[0]),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.DRYING_TIME,
        icon="mdi:sun-clock",
        options=lambda device, segment: [f"{i}h" for i in range(2, 5)],
        entity_category=None,
        value_fn=lambda value, device: f"{value}h",
        value_int_fn=lambda value, device: int(value[0]),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.MOP_WASH_LEVEL,
        icon="mdi:water-opacity",
        value_int_fn=lambda value, device: DreameVacuumMopWashLevel[value.upper()],
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE,
        icon="mdi:translate-variant",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.voice_assistant,
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_pad_humidity",
        icon_fn=lambda value, device: "mdi:water-off"
        if (
            not (
                device.status.water_tank_or_mop_installed
                or device.status.auto_mount_mop
            )
            or device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING
        )
        else MOP_PAD_HUMIDITY_TO_ICON.get(
            device.status.mop_pad_humidity, "mdi:water-percent"
        ),
        value_int_fn=lambda value, device: DreameVacuumMopPadHumidity[value.upper()],
        exists_fn=lambda description, device: device.capability.self_wash_base,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.MOPPING_TYPE,
        icon="mdi:spray-bottle",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, device: DreameVacuumMoppingType[value.upper()],
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE,
        icon="mdi:rounded-corner",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, device: DreameVacuumWiderCornerCoverage[
            value.upper()
        ],
        exists_fn=lambda description, device: bool(
            not device.capability.mop_pad_swing
            and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSelectEntityDescription(
        key="map_rotation",
        icon="mdi:crop-rotate",
        options=lambda device, segment: ["0", "90", "180", "270"],
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: str(device.status.selected_map.rotation)
        if device.status.selected_map
        and device.status.selected_map.rotation is not None
        else "",
        exists_fn=lambda description, device: device.capability.map,
    ),
    DreameVacuumSelectEntityDescription(
        key="selected_map",
        icon="mdi:map-check",
        options=lambda device, segment: [
            v.map_name for k, v in device.status.map_data_list.items()
        ],
        entity_category=None,
        value_fn=lambda value, device: device.status.selected_map.map_name
        if device.status.selected_map and device.status.selected_map.map_name
        else "",
        exists_fn=lambda description, device: device.capability.map
        and device.capability.multi_floor_map,
        value_int_fn=lambda value, device: next(
            (k for k, v in device.status.map_data_list.items() if v.map_name == value),
            None,
        ),
        attrs_fn=lambda device: {
            "map_id": device.status.selected_map.map_id,
            "map_index": device.status.selected_map.map_index,
        }
        if device.status.selected_map
        else None,
    ),
)

SEGMENT_SELECTS: tuple[DreameVacuumSelectEntityDescription, ...] = (
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.SUCTION_LEVEL.name.lower(),
        icon_fn=lambda value, segment: SUCTION_LEVEL_TO_ICON.get(
            segment.suction_level, "mdi:fan"
        )
        if segment
        else "mdi:fan-off",
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.suction_level is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.MOPPING.value
        ),
        value_fn=lambda device, segment: SUCTION_LEVEL_CODE_TO_NAME.get(
            segment.suction_level, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumSuctionLevel[value.upper()],
        exists_fn=lambda description, device: device.capability.customized_cleaning,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.WATER_VOLUME.name.lower(),
        icon_fn=lambda value, segment: WATER_VOLUME_TO_ICON.get(
            segment.water_volume, "mdi:water"
        )
        if segment
        else "mdi:water-off",
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.water_volume is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.SWEEPING.value
        ),
        value_fn=lambda device, segment: WATER_VOLUME_CODE_TO_NAME.get(
            segment.water_volume, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumWaterVolume[value.upper()],
        exists_fn=lambda description, device: device.capability.customized_cleaning
        and not device.capability.self_wash_base,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_pad_humidity",
        icon_fn=lambda value, segment: MOP_PAD_HUMIDITY_TO_ICON.get(
            segment.water_volume, "mdi:water-percent"
        )
        if segment
        else "mdi:water-off",
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.mop_pad_humidity is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.SWEEPING.value
        ),
        value_fn=lambda device, segment: MOP_PAD_HUMIDITY_CODE_TO_NAME.get(
            segment.mop_pad_humidity, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumMopPadHumidity[value.upper()],
        exists_fn=lambda description, device: device.capability.customized_cleaning
        and device.capability.self_wash_base,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.CLEANING_MODE.name.lower(),
        icon_fn=lambda value, segment: CLEANING_MODE_TO_ICON.get(
            segment.cleaning_mode, "mdi:broom"
        )
        if segment
        else "mdi:broom",
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.cleaning_mode is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.scheduled_clean
            and not device.status.fast_mapping
            and not device.status.cruising
            and not device.status.started  # TODO: Check
        ),
        value_fn=lambda device, segment: CLEANING_MODE_CODE_TO_NAME.get(
            segment.cleaning_mode, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumCleaningMode[value.upper()],
        exists_fn=lambda description, device: device.capability.customized_cleaning
        and device.capability.custom_cleaning_mode,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="cleaning_times",
        icon_fn=lambda value, segment: "mdi:home-floor-" + str(segment.cleaning_times)
        if segment and segment.cleaning_times and segment.cleaning_times < 4
        else "mdi:home-floor-0",
        options=lambda device, segment: [f"{i}{UNIT_TIMES}" for i in range(1, 4)],
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.cleaning_times is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.scheduled_clean
            and not device.status.cruising
            and not device.status.started
            and not device.status.fast_mapping
        ),
        value_fn=lambda device, segment: f"{segment.cleaning_times}{UNIT_TIMES}",
        value_int_fn=lambda value, self: int(value[0]),
        exists_fn=lambda description, device: device.capability.customized_cleaning,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="order",
        options=lambda device, segment: [
            str(i) for i in range(1, len(device.status.current_segments.values()) + 1)
        ]
        if device.status.current_segments
        else [STATE_UNAVAILABLE],
        entity_category=None,
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.order is not None
            and not device.status.started
            and device.status.custom_order
            and not device.status.scheduled_clean
            and not device.status.cruising
            and device.status.has_saved_map
            and not device.status.fast_mapping
        ),
        value_fn=lambda device, segment: str(segment.order)
        if segment.order
        else STATE_UNAVAILABLE,
        exists_fn=lambda description, device: device.capability.customized_cleaning,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="floor_material",
        icon_fn=lambda value, segment: FLOOR_MATERIAL_TO_ICON.get(
            segment.floor_material, "mdi:checkbox-blank"
        )
        if segment
        else "mdi:checkbox-blank-off",
        entity_category=EntityCategory.CONFIG,
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.floor_material is not None
            and not device.status.fast_mapping
            and not device.status.has_temporary_map
        ),
        value_fn=lambda device, segment: FLOOR_MATERIAL_CODE_TO_NAME.get(
            segment.floor_material, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumFloorMaterial[value.upper()],
        exists_fn=lambda description, device: device.capability.floor_material,
        segment_list_fn=lambda device: device.status.segments,
    ),
    DreameVacuumSelectEntityDescription(
        name="",
        key="name",
        options=lambda device, segment: list(segment.name_list(device.status.segments)),
        entity_category=EntityCategory.CONFIG,
        segment_available_fn=lambda device, segment: bool(
            device.status.segments
            and not device.status.fast_mapping
            and not device.status.has_temporary_map
        ),
        value_fn=lambda device, segment: device.status.segments[segment.segment_id].name
        if segment.segment_id in device.status.segments
        else None,
        value_int_fn=lambda value, self: next(
            (
                type
                for name, type in self.segment.name_list(
                    self.device.status.segments
                ).items()
                if name == value
            ),
            None,
        ),
        attrs_fn=lambda segment: {
            "room_id": segment.segment_id,
            "index": segment.index,
            "type": segment.type,
        },
        segment_list_fn=lambda device: device.status.segments,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum select based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DreameVacuumSelectEntity(coordinator, description)
        for description in SELECTS
        if description.exists_fn(description, coordinator.device)
    )
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SELECT_NEXT,
        {vol.Optional(INPUT_CYCLE, default=True): bool},
        DreameVacuumSelectEntity.async_next.__name__,
    )
    platform.async_register_entity_service(
        SERVICE_SELECT_PREVIOUS,
        {vol.Optional(INPUT_CYCLE, default=True): bool},
        DreameVacuumSelectEntity.async_previous.__name__,
    )
    platform.async_register_entity_service(
        SERVICE_SELECT_FIRST, {}, DreameVacuumSelectEntity.async_first.__name__
    )
    platform.async_register_entity_service(
        SERVICE_SELECT_LAST, {}, DreameVacuumSelectEntity.async_last.__name__
    )

    update_segment_selects = partial(
        async_update_segment_selects, coordinator, {}, async_add_entities
    )
    coordinator.async_add_listener(update_segment_selects)
    update_segment_selects()


@callback
def async_update_segment_selects(
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, list[DreameVacuumSegmentSelectEntity]],
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
        async_remove_segment_selects(segment_id, coordinator, current)

    new_entities = []
    for segment_id in new_ids - current_ids:
        current[segment_id] = [
            DreameVacuumSegmentSelectEntity(coordinator, description, segment_id)
            for description in SEGMENT_SELECTS
            if description.exists_fn(description, coordinator.device)
        ]
        new_entities = new_entities + current[segment_id]

    if new_entities:
        async_add_entities(new_entities)


def async_remove_segment_selects(
    segment_id: str,
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, DreameVacuumSegmentSelectEntity],
) -> None:
    registry = entity_registry.async_get(coordinator.hass)
    entities = current[segment_id]
    for entity in entities:
        if entity.entity_id in registry.entities:
            registry.async_remove(entity.entity_id)
    del current[segment_id]


class DreameVacuumSelectEntity(DreameVacuumEntity, SelectEntity):
    """Defines a Dreame Vacuum select."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: SelectEntityDescription,
    ) -> None:
        """Initialize Dreame Vacuum select."""
        if description.value_fn is None and (
            description.property_key is not None or description.key is not None
        ):
            if description.property_key is not None:
                prop = f"{description.property_key.name.lower()}_name"
            else:
                prop = f"{description.key.lower()}_name"
            if hasattr(coordinator.device.status, prop):
                description.value_fn = lambda value, device: getattr(
                    device.status, prop
                )

        if description.set_fn is None and (
            description.property_key is not None or description.key is not None
        ):
            if description.property_key is not None:
                set_prop = f"set_{description.property_key.name.lower()}"
            else:
                set_prop = f"set_{description.key.lower()}"
            if hasattr(coordinator.device, set_prop):
                description.set_fn = lambda device, segment_id, value: getattr(
                    device, set_prop
                )(value)

        if description.options is None and (
            description.property_key is not None or description.key is not None
        ):
            if description.property_key is not None:
                options_prop = f"{description.property_key.name.lower()}_list"
            else:
                options_prop = f"{description.key.lower()}_list"
            if hasattr(coordinator.device.status, options_prop):
                description.options = lambda device, segment: list(
                    getattr(device.status, options_prop)
                )

        super().__init__(coordinator, description)
        if description.options is not None:
            self._attr_options = description.options(coordinator.device, None)
        self._attr_current_option = self.native_value

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.entity_description.options is not None:
            self._attr_options = self.entity_description.options(self.device, None)
        self._attr_current_option = self.native_value
        super()._handle_coordinator_update()

    @callback
    async def async_select_index(self, idx: int) -> None:
        """Select new option by index."""
        new_index = idx % len(self._attr_options)
        await self.async_select_option(self._attr_options[new_index])

    @callback
    async def async_offset_index(self, offset: int, cycle: bool) -> None:
        """Offset current index."""
        current_index = self._attr_options.index(self._attr_current_option)
        new_index = current_index + offset
        if cycle:
            new_index = new_index % len(self._attr_options)
        elif new_index < 0:
            new_index = 0
        elif new_index >= len(self._attr_options):
            new_index = len(self._attr_options) - 1

        if cycle or current_index != new_index:
            await self.async_select_option(self._attr_options[new_index])

    @callback
    async def async_first(self) -> None:
        """Select first option."""
        await self.async_select_index(0)

    @callback
    async def async_last(self) -> None:
        """Select last option."""
        await self.async_select_index(-1)

    @callback
    async def async_next(self, cycle: bool) -> None:
        """Select next option."""
        await self.async_offset_index(1, cycle)

    @callback
    async def async_previous(self, cycle: bool) -> None:
        """Select previous option."""
        await self.async_offset_index(-1, cycle)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        if option not in self._attr_options:
            raise HomeAssistantError(
                f"Invalid option for {self.entity_description.name} {option}. Valid options: {self._attr_options}"
            )

        value = option
        if self.entity_description.value_int_fn is not None:
            value = self.entity_description.value_int_fn(option, self.device)

        if value is None:
            raise HomeAssistantError(
                f"Invalid option for {self.entity_description.name} {option}. Valid options: {self._attr_options}"
            )

        if not isinstance(value, int) and (
            isinstance(value, IntEnum) or (isinstance(value, str) and value.isnumeric())
        ):
            value = int(value)

        if self.entity_description.set_fn is not None:
            await self._try_command(
                "Unable to call %s",
                self.entity_description.set_fn,
                self.device,
                0,
                value,
            )
        elif self.entity_description.property_key is not None:
            await self._try_command(
                "Unable to call %s",
                self.device.set_property,
                self.entity_description.property_key,
                value,
            )


class DreameVacuumSegmentSelectEntity(DreameVacuumEntity, SelectEntity):
    """Defines a Dreame Vacuum Segment select."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumSelectEntityDescription,
        segment_id: int,
    ) -> None:
        """Initialize Dreame Vacuum Segment Select."""
        self.segment_id = segment_id
        self.segment = None
        self.segments = None
        if coordinator.device:
            self.segments = copy.deepcopy(
                description.segment_list_fn(coordinator.device)
            )
            if segment_id in self.segments:
                self.segment = self.segments[segment_id]

        if description.set_fn is None and (
            description.property_key is not None or description.key is not None
        ):
            if description.property_key is not None:
                segment_set_prop = (
                    f"set_segment_{description.property_key.name.lower()}"
                )
            else:
                segment_set_prop = f"set_segment_{description.key.lower()}"
            if hasattr(coordinator.device, segment_set_prop):
                description.set_fn = lambda device, segment_id, value: getattr(
                    device, segment_set_prop
                )(segment_id, value)

        if description.options is None and (
            description.property_key is not None or description.key is not None
        ):
            if description.property_key is not None:
                segment_options_prop = f"{description.property_key.name.lower()}_list"
            else:
                segment_options_prop = f"{description.key.lower()}_list"
            if hasattr(coordinator.device.status, segment_options_prop):
                description.options = lambda device, segment: list(
                    getattr(device.status, segment_options_prop)
                )

        super().__init__(coordinator, description)
        self._attr_unique_id = (
            f"{self.device.mac}_room_{segment_id}_{description.key.lower()}"
        )
        self.entity_id = f"select.{self.device.name.lower()}_room_{segment_id}_{description.key.lower()}"
        self._attr_options = []
        self._attr_current_option = "unavailable"
        if self.segment:
            if description.options is not None:
                self._attr_options = description.options(
                    coordinator.device, self.segment
                )
            self._attr_current_option = self.native_value

    def _set_id(self) -> None:
        """Set name, unique id and icon of the entity"""
        if self.entity_description.name == "":
            name = f"room_{self.segment_id}_{self.entity_description.key}"
        elif self.segment:
            name = f"{self.entity_description.key}_{self.segment.name}"
        else:
            name = f"{self.entity_description.key}_room_unavailable"

        self._attr_name = f"{self.device.name} {name.replace('_', ' ').title()}"

        if self.entity_description.icon_fn is not None:
            self._attr_icon = self.entity_description.icon_fn(
                self.native_value, self.segment
            )
        elif self.segment:
            self._attr_icon = self.segment.icon
        else:
            self._attr_icon = "mdi:home-off-outline"

    @property
    def _device_segments(self):
        return self.entity_description.segment_list_fn(self.device)

    @callback
    def _handle_coordinator_update(self) -> None:
        device_segments = self._device_segments
        if self.segments != device_segments:
            self.segments = copy.deepcopy(device_segments)
            if self.segments and self.segment_id in self.segments:
                if self.segment != self.segments[self.segment_id]:
                    self.segment = self.segments[self.segment_id]
                    self._attr_current_option = self.native_value
                    self._set_id()
                if self.entity_description.options is not None:
                    self._attr_options = self.entity_description.options(
                        self.device, self.segment
                    )
            elif self.segment:
                self._attr_options = []
                self.segment = None
                self._set_id()

        self.async_write_ha_state()

    @callback
    async def async_select_index(self, idx: int) -> None:
        """Select new option by index."""
        new_index = idx % len(self._attr_options)
        await self.async_select_option(self._attr_options[new_index])

    @callback
    async def async_offset_index(self, offset: int, cycle: bool) -> None:
        """Offset current index."""
        current_index = self._attr_options.index(self._attr_current_option)
        new_index = current_index + offset
        if cycle:
            new_index = new_index % len(self._attr_options)
        elif new_index < 0:
            new_index = 0
        elif new_index >= len(self._attr_options):
            new_index = len(self._attr_options) - 1

        if cycle or current_index != new_index:
            await self.async_select_option(self._attr_options[new_index])

    @callback
    async def async_first(self) -> None:
        """Select first option."""
        await self.async_select_index(0)

    @callback
    async def async_last(self) -> None:
        """Select last option."""
        await self.async_select_index(-1)

    @callback
    async def async_next(self, cycle: bool) -> None:
        """Select next option."""
        await self.async_offset_index(1, cycle)

    @callback
    async def async_previous(self, cycle: bool) -> None:
        """Select previous option."""
        await self.async_offset_index(-1, cycle)

    async def async_select_option(self, option: str) -> None:
        """Set the Dreame Vacuum Segment Select value."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        value = option
        if self.entity_description.value_int_fn is not None:
            value = self.entity_description.value_int_fn(value, self)

        if value is None:
            raise HomeAssistantError(
                "(%s) Invalid option (%s). Valid options: %s",
                self.entity_description.name,
                option,
                self._attr_options,
            )

        await self._try_command(
            "Unable to call %s",
            self.entity_description.set_fn,
            self.device,
            self.segment_id,
            int(value),
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.device.device_connected or (
            self._attr_available and self.segment is None
        ):
            return False
        if self.entity_description.segment_available_fn is not None:
            return self.entity_description.segment_available_fn(
                self.device, self.segment
            )
        return self._attr_available

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes of the entity."""
        attrs = None
        if self.entity_description.attrs_fn is not None:
            attrs = self.entity_description.attrs_fn(self.segment)
        elif (
            self.entity_description.value_fn is not None
            or self.entity_description.value_int_fn is not None
        ):
            if self.entity_description.property_key is not None:
                attrs = {
                    ATTR_VALUE: self.device.get_property(
                        self.entity_description.property_key
                    )
                }
            elif self.entity_description.value_int_fn is not None:
                attrs = {
                    ATTR_VALUE: self.entity_description.value_int_fn(
                        self.native_value, self
                    )
                }

        return attrs

    @property
    def native_value(self) -> str | None:
        """Return the current Dreame Vacuum select value."""
        if self.segment:
            return self.entity_description.value_fn(self.device, self.segment)
