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
    ENTITY_ID_FORMAT,
    SelectEntity,
    SelectEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory, async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform, entity_registry

from .const import (
    DOMAIN,
    UNIT_TIMES,
    UNIT_AREA,
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
    remove_entities,
)

from .dreame.const import ATTR_VALUE, STATE_NOT_SET
from .dreame.types import ATTR_MAP_INDEX, ATTR_MAP_ID
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
    DreameVacuumMopCleanFrequency,
    DreameVacuumMoppingType,
    DreameVacuumWiderCornerCoverage,
    DreameVacuumMopPadSwing,
    DreameVacuumMopExtendFrequency,
    DreameVacuumWashingMode,
    DreameVacuumWaterTemperature,
    DreameVacuumAutoLDSCoverage,
    DreameVacuumSecondCleaning,
    DreameVacuumCleaningRoute,
    DreameVacuumCustomMoppingRoute,
    DreameVacuumSelfCleanFrequency,
    DreameVacuumMopPressure,
    DreameVacuumMopTemperature,
    DreameVacuumLowLyingAreaFrequency,
    DreameVacuumScraperFrequency,
    DreameVacuumAutoEmptyMode,
    DreameVacuumAutoEmptyModeV2,
    DreameVacuumCleanGenius,
    DreameVacuumCleanGeniusMode,
    DreameVacuumFloorMaterial,
    DreameVacuumFloorMaterialDirection,
    DreameVacuumSegmentVisibility,
    SUCTION_LEVEL_CODE_TO_NAME,
    WATER_VOLUME_CODE_TO_NAME,
    MOP_PAD_HUMIDITY_CODE_TO_NAME,
    CLEANING_MODE_CODE_TO_NAME,
    FLOOR_MATERIAL_CODE_TO_NAME,
    FLOOR_MATERIAL_DIRECTION_CODE_TO_NAME,
    SEGMENT_VISIBILITY_CODE_TO_NAME,
    CUSTOM_MOPPING_ROUTE_TO_NAME,
    CLEANING_ROUTE_TO_NAME,
    MOP_PRESSURE_TO_NAME,
    MOP_TEMPERATURE_TO_NAME,
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
    DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING: "mdi:water-polo",
}

FLOOR_MATERIAL_TO_ICON = {
    DreameVacuumFloorMaterial.NONE: "mdi:checkbox-blank",
    DreameVacuumFloorMaterial.TILE: "mdi:apps",
    DreameVacuumFloorMaterial.WOOD: "mdi:pine-tree-box",
    DreameVacuumFloorMaterial.MEDIUM_PILE_CARPET: "mdi:rug",
    DreameVacuumFloorMaterial.LOW_PILE_CARPET: "mdi:rug",
    DreameVacuumFloorMaterial.CARPET: "mdi:rug",
}

FLOOR_MATERIAL_DIRECTION_TO_ICON = {
    DreameVacuumFloorMaterialDirection.VERTICAL: "mdi:swap-vertical-bold",
    DreameVacuumFloorMaterialDirection.HORIZONTAL: "mdi:swap-horizontal-bold",
}

SEGMENT_VISIBILITY_TO_ICON = {
    DreameVacuumSegmentVisibility.VISIBLE: "mdi:eye-check",
    DreameVacuumSegmentVisibility.HIDDEN: "mdi:eye-remove",
}

SELF_CLEAN_FREQUENCY_TO_ICON = {
    DreameVacuumSelfCleanFrequency.BY_AREA: "mdi:texture-box",
    DreameVacuumSelfCleanFrequency.BY_ROOM: "mdi:home-switch",
    DreameVacuumSelfCleanFrequency.BY_TIME: "mdi:table-clock",
    DreameVacuumSelfCleanFrequency.INTELLIGENT: "mdi:atom-variant",
}

AUTO_EMPTY_MODE_TO_ICON = {
    DreameVacuumAutoEmptyMode.OFF: "mdi:autorenew-off",
    DreameVacuumAutoEmptyMode.STANDARD: "mdi:autorenew",
    DreameVacuumAutoEmptyMode.HIGH_FREQUENCY: "mdi:auto-upload",
    DreameVacuumAutoEmptyMode.LOW_FREQUENCY: "mdi:auto-download",
}

AUTO_EMPTY_MODE_V2_TO_ICON = {
    DreameVacuumAutoEmptyModeV2.OFF: "mdi:autorenew-off",
    DreameVacuumAutoEmptyModeV2.STANDARD: "mdi:autorenew",
    DreameVacuumAutoEmptyModeV2.INTELLIGENT: "mdi:atom-variant",
    DreameVacuumAutoEmptyModeV2.HIGH_FREQUENCY: "mdi:auto-upload",
    DreameVacuumAutoEmptyModeV2.LOW_FREQUENCY: "mdi:auto-download",
    DreameVacuumAutoEmptyModeV2.CUSTOM_FREQUENCY: "mdi:ruler-square",
}

CUSTOM_MOPPING_ROUTE_TO_ICON = {
    DreameVacuumCustomMoppingRoute.OFF: "mdi:map-marker-remove",
    DreameVacuumCustomMoppingRoute.STANDARD: "mdi:sine-wave",
    DreameVacuumCustomMoppingRoute.INTENSIVE: "mdi:swap-vertical-variant",
    DreameVacuumCustomMoppingRoute.DEEP: "mdi:heating-coil",
}

CLEANING_ROUTE_TO_ICON = {
    DreameVacuumCleaningRoute.STANDARD: "mdi:sine-wave",
    DreameVacuumCleaningRoute.INTENSIVE: "mdi:swap-vertical-variant",
    DreameVacuumCleaningRoute.DEEP: "mdi:heating-coil",
    DreameVacuumCleaningRoute.QUICK: "mdi:truck-fast-outline",
}


@dataclass
class DreameVacuumSelectEntityDescription(DreameVacuumEntityDescription, SelectEntityDescription):
    """Describes Dreame Vacuum Select entity."""

    set_fn: Callable[[object, int, int]] = None
    options: Callable[[object, object], list[str]] = None
    segment_available_fn: Callable[[object, object], bool] = None
    segment_list_fn: Callable[[object], bool] = None


SELECTS: tuple[DreameVacuumSelectEntityDescription, ...] = (
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.SUCTION_LEVEL,
        icon_fn=lambda value, device: (
            "mdi:fan-off"
            if device.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING
            else SUCTION_LEVEL_TO_ICON.get(device.status.suction_level, "mdi:fan")
        ),
        value_int_fn=lambda value, self: DreameVacuumSuctionLevel[value.upper()].value,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.WATER_VOLUME,
        icon_fn=lambda value, device: (
            "mdi:water-off"
            if (
                not (device.status.water_tank_or_mop_installed)
                or device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING
            )
            else WATER_VOLUME_TO_ICON.get(device.status.water_volume, "mdi:water")
        ),
        value_int_fn=lambda value, self: DreameVacuumWaterVolume[value.upper()].value,
        exists_fn=lambda description, device: not device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_MODE,
        icon_fn=lambda value, device: CLEANING_MODE_TO_ICON.get(device.status.cleaning_mode, "mdi:broom"),
        value_int_fn=lambda value, self: DreameVacuumCleaningMode[value.upper()].value,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CARPET_SENSITIVITY,
        icon="mdi:rug",
        value_int_fn=lambda value, self: DreameVacuumCarpetSensitivity[value.upper()].value,
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: not device.capability.carpet_recognition
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CARPET_CLEANING,
        icon="mdi:close-box-outline",
        value_int_fn=lambda value, self: DreameVacuumCarpetCleaning[value.upper()].value,
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.mop_pad_unmounting
        or device.capability.auto_carpet_cleaning
        or device.capability.mop_pad_lifting_plus
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.AUTO_EMPTY_FREQUENCY,
        icon_fn=lambda value, device: f"mdi:numeric-{value[0]}-box-multiple-outline",
        options=lambda device, segment: [f"{i}{UNIT_TIMES}" for i in range(1, 4)],
        entity_category=None,
        value_fn=lambda value, device: f"{value}{UNIT_TIMES}",
        value_int_fn=lambda value, self: int(value[0]),
        exists_fn=lambda description, device: DreameVacuumEntityDescription().exists_fn(description, device)
        and not device.capability.auto_empty_mode,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.DRYING_TIME,
        icon="mdi:sun-clock",
        entity_category=None,
        value_fn=lambda value, device: f"{value}h",
        value_int_fn=lambda value, self: int(value[0]),
        exists_fn=lambda description, device: not device.capability.mop_clean_frequency
        and device.capability.self_wash_base,
        available_fn=lambda device: not device.status.smart_drying
        and not device.status.silent_drying
        and device.status.auto_drying,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.MOP_WASH_LEVEL,
        icon="mdi:water-opacity",
        value_int_fn=lambda value, self: DreameVacuumMopWashLevel[value.upper()].value,
        entity_category=None,
        exists_fn=lambda description, device: DreameVacuumEntityDescription().exists_fn(description, device)
        and device.capability.self_wash_base
        and not device.capability.smart_mop_washing,
        available_fn=lambda device: not device.status.ultra_clean_mode and device.status.self_clean,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE,
        icon="mdi:translate-variant",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.voice_assistant,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.MOP_PRESSURE,
        icon="mdi:car-brake-low-pressure",
        entity_category=None,
        value_int_fn=lambda value, self: DreameVacuumMopPressure[value.upper()].value,
        exists_fn=lambda description, device: device.capability.mop_pressure,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.MOP_TEMPERATURE,
        icon="mdi:thermometer-water",
        entity_category=None,
        value_int_fn=lambda value, self: DreameVacuumMopTemperature[value.upper()].value,
        exists_fn=lambda description, device: device.capability.mop_temperature,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.LOW_LYING_AREA_FREQUENCY,
        icon="mdi:priority-high",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumLowLyingAreaFrequency[value.upper()].value,
        exists_fn=lambda description, device: device.capability.low_lying_area_frequency,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.SCRAPER_FREQUENCY,
        icon="mdi:squeegee",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumScraperFrequency[value.upper()].value,
        exists_fn=lambda description, device: device.capability.scraper_frequency,
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_pad_humidity",
        icon_fn=lambda value, device: (
            "mdi:water-off"
            if (
                not (device.status.water_tank_or_mop_installed)
                or device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING
            )
            else MOP_PAD_HUMIDITY_TO_ICON.get(device.status.mop_pad_humidity, "mdi:water-percent")
        ),
        value_int_fn=lambda value, self: DreameVacuumMopPadHumidity[value.upper()].value,
        exists_fn=lambda description, device: device.capability.self_wash_base,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.MOPPING_TYPE,
        icon="mdi:spray-bottle",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumMoppingType[value.upper()].value,
        exists_fn=lambda description, device: device.capability.self_wash_base
        and not device.capability.custom_mopping_route
        and not device.capability.cleaning_route
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSelectEntityDescription(
        key="custom_mopping_route",
        entity_category=None,
        icon_fn=lambda value, device: CUSTOM_MOPPING_ROUTE_TO_ICON.get(
            device.status.custom_mopping_route, "mdi:routes"
        ),
        value_int_fn=lambda value, self: DreameVacuumCustomMoppingRoute[value.upper()].value,
        exists_fn=lambda description, device: device.capability.custom_mopping_route
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE,
        icon="mdi:rounded-corner",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumWiderCornerCoverage[value.upper()].value,
        exists_fn=lambda description, device: DreameVacuumEntityDescription().exists_fn(description, device)
        and not device.capability.mop_pad_swing
        and not device.capability.mop_clean_frequency,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.MOP_PAD_SWING,
        icon="mdi:arrow-split-vertical",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumMopPadSwing[value.upper()].value,
        exists_fn=lambda description, device: DreameVacuumEntityDescription().exists_fn(description, device)
        and device.capability.mop_pad_swing
        and not device.capability.mop_extend,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.MOP_EXTEND_FREQUENCY,
        icon="mdi:waves-arrow-right",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumMopExtendFrequency[value.upper()].value,
        exists_fn=lambda description, device: DreameVacuumEntityDescription().exists_fn(description, device)
        and device.capability.mop_extend,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY,
        icon_fn=lambda value, device: SELF_CLEAN_FREQUENCY_TO_ICON.get(
            device.status.self_clean_frequency, "mdi:home-switch"
        ),
        entity_category=None,
        options=lambda device, segment: (
            [
                i
                for i in device.status.self_clean_frequency_list
                if i != DreameVacuumSelfCleanFrequency.BY_ROOM.name.lower()
            ]
            if (device.status.current_map and not device.status.has_saved_map)
            else (list(device.status.self_clean_frequency_list))
        ),
        value_int_fn=lambda value, self: DreameVacuumSelfCleanFrequency[value.upper()].value,
        exists_fn=lambda description, device: device.capability.self_clean_frequency,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.AUTO_RECLEANING,
        icon="mdi:repeat-variant",
        options=lambda device, segment: list(device.status.second_cleaning_list),
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumSecondCleaning[value.upper()].value,
        exists_fn=lambda description, device: device.capability.auto_recleaning,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.AUTO_REWASHING,
        options=lambda device, segment: list(device.status.second_cleaning_list),
        entity_category=EntityCategory.CONFIG,
        icon="mdi:archive-refresh",
        value_int_fn=lambda value, self: DreameVacuumSecondCleaning[value.upper()].value,
        exists_fn=lambda description, device: device.capability.auto_rewashing,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.CLEANING_ROUTE,
        entity_category=None,
        icon_fn=lambda value, device: CLEANING_ROUTE_TO_ICON.get(device.status.cleaning_route, "mdi:routes"),
        value_int_fn=lambda value, self: DreameVacuumCleaningRoute[value.upper()].value,
        exists_fn=lambda description, device: device.capability.cleaning_route,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.BATTERY_CHARGE_LEVEL,
        icon="mdi:battery-heart-variant",
        options=lambda device, segment: ["80%", "90%", "100%"],
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: f"{value}%",
        value_int_fn=lambda value, self: int(value[:-1]),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.CLEANGENIUS,
        icon="mdi:atom",
        entity_category=None,
        value_int_fn=lambda value, self: DreameVacuumCleanGenius[value.upper()].value,
        exists_fn=lambda description, device: device.capability.cleangenius,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CLEANGENIUS_MODE,
        icon="mdi:atom",
        entity_category=None,
        value_int_fn=lambda value, self: DreameVacuumCleanGeniusMode[value.upper()].value,
        exists_fn=lambda description, device: device.capability.cleangenius_mode,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.WATER_TEMPERATURE,
        icon="mdi:water-thermometer",
        entity_category=None,
        value_int_fn=lambda value, self: DreameVacuumWaterTemperature[value.upper()].value,
        exists_fn=lambda description, device: device.capability.water_temperature,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.AUTO_LDS_COVERAGE,
        icon="mdi:elevator",
        entity_category=EntityCategory.CONFIG,
        value_int_fn=lambda value, self: DreameVacuumAutoLDSCoverage[value.upper()].value,
        exists_fn=lambda description, device: device.capability.auto_lds_lifting,
    ),
    DreameVacuumSelectEntityDescription(
        key="auto_empty_mode",
        icon_fn=lambda value, device: (
            AUTO_EMPTY_MODE_V2_TO_ICON.get(device.status.auto_empty_mode, "mdi:autorenew")
            if device.capability.intelligent_auto_empty
            else AUTO_EMPTY_MODE_TO_ICON.get(device.status.auto_empty_mode, "mdi:autorenew")
        ),
        entity_category=None,
        value_int_fn=lambda value, self: (
            DreameVacuumAutoEmptyModeV2[value.upper()].value
            if self.device.capability.intelligent_auto_empty
            else DreameVacuumAutoEmptyMode[value.upper()].value
        ),
        exists_fn=lambda description, device: device.capability.auto_empty_mode,
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_clean_frequency",
        icon_fn=lambda value, device: "mdi:home-switch" if device.status.self_clean_value == 0 else "mdi:texture-box",
        entity_category=None,
        value_int_fn=lambda value, self: 0 if value == "by_room" else int(value.replace(UNIT_AREA, "")),
        exists_fn=lambda description, device: device.capability.self_wash_base
        and device.capability.mop_clean_frequency,
    ),
    DreameVacuumSelectEntityDescription(
        key="washing_mode",
        icon="mdi:water-opacity",
        entity_category=None,
        value_int_fn=lambda value, self: DreameVacuumWashingMode[value.upper()].value,
        exists_fn=lambda description, device: device.capability.smart_mop_washing
        and DreameVacuumEntityDescription().exists_fn(description, device),
        available_fn=lambda device: not device.status.smart_mop_washing and device.status.self_clean,
    ),
    DreameVacuumSelectEntityDescription(
        key="map_rotation",
        icon="mdi:crop-rotate",
        options=lambda device, segment: ["0", "90", "180", "270"],
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: (
            str(device.status.selected_map.rotation)
            if device.status.selected_map and device.status.selected_map.rotation is not None
            else ""
        ),
        exists_fn=lambda description, device: device.capability.map,
    ),
    DreameVacuumSelectEntityDescription(
        key="selected_map",
        icon="mdi:map-check",
        options=lambda device, segment: (
            [v.map_name for k, v in device.status.map_data_list.items()] if device.status.map_data_list else []
        ),
        entity_category=None,
        value_fn=lambda value, device: (
            device.status.selected_map.map_name
            if device.status.selected_map and device.status.selected_map.map_name
            else ""
        ),
        exists_fn=lambda description, device: device.capability.map
        and device.capability.multi_floor_map
        and device.capability.lidar_navigation,
        value_int_fn=lambda value, self: next(
            (k for k, v in self.device.status.map_data_list.items() if v.map_name == value),
            None,
        ),
        attrs_fn=lambda device: (
            {
                ATTR_MAP_ID: device.status.selected_map.map_id,
                ATTR_MAP_INDEX: device.status.selected_map.map_index,
            }
            if device.status.selected_map
            else None
        ),
    ),
)

SEGMENT_SELECTS: tuple[DreameVacuumSelectEntityDescription, ...] = (
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.SUCTION_LEVEL.name.lower(),
        icon_fn=lambda value, segment: (
            SUCTION_LEVEL_TO_ICON.get(segment.suction_level, "mdi:fan") if segment else "mdi:fan-off"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.suction_level is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.MOPPING.value
            and not device.status.cleangenius_cleaning
        ),
        value_fn=lambda device, segment: SUCTION_LEVEL_CODE_TO_NAME.get(segment.suction_level, STATE_UNKNOWN),
        value_int_fn=lambda value, self: DreameVacuumSuctionLevel[value.upper()].value,
        exists_fn=lambda description, device: device.capability.customized_cleaning,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.WATER_VOLUME.name.lower(),
        icon_fn=lambda value, segment: (
            WATER_VOLUME_TO_ICON.get(segment.water_volume, "mdi:water") if segment else "mdi:water-off"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.water_volume is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.SWEEPING.value
            and not device.status.cleangenius_cleaning
        ),
        value_fn=lambda device, segment: WATER_VOLUME_CODE_TO_NAME.get(segment.water_volume, STATE_UNKNOWN),
        value_int_fn=lambda value, self: DreameVacuumWaterVolume[value.upper()].value,
        exists_fn=lambda description, device: device.capability.customized_cleaning
        and not device.capability.self_wash_base,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_pad_humidity",
        icon_fn=lambda value, segment: (
            MOP_PAD_HUMIDITY_TO_ICON.get(segment.water_volume, "mdi:water-percent") if segment else "mdi:water-off"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.mop_pad_humidity is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.SWEEPING.value
            and not device.status.cleangenius_cleaning
        ),
        value_fn=lambda device, segment: MOP_PAD_HUMIDITY_CODE_TO_NAME.get(segment.mop_pad_humidity, STATE_UNKNOWN),
        value_int_fn=lambda value, self: DreameVacuumMopPadHumidity[value.upper()].value,
        exists_fn=lambda description, device: device.capability.customized_cleaning
        and device.capability.self_wash_base,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.CLEANING_MODE.name.lower(),
        icon_fn=lambda value, segment: (
            CLEANING_MODE_TO_ICON.get(segment.cleaning_mode, "mdi:broom") if segment else "mdi:broom"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.scheduled_clean
            and not device.status.fast_mapping
            and not device.status.cruising
            and not device.status.cleangenius_cleaning
            and not device.status.started  # TODO: Check
        ),
        value_fn=lambda device, segment: CLEANING_MODE_CODE_TO_NAME.get(
            segment.cleaning_mode if segment.cleaning_mode is not None else 2, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumCleaningMode[value.upper()].value,
        exists_fn=lambda description, device: device.capability.customized_cleaning
        and device.capability.custom_cleaning_mode,
        segment_list_fn=lambda device: device.status.current_segments,
        options=lambda device, segment: list(device.status.segment_cleaning_mode_list),
    ),
    DreameVacuumSelectEntityDescription(
        key="cleaning_times",
        icon_fn=lambda value, segment: (
            "mdi:home-floor-" + str(segment.cleaning_times)
            if segment and segment.cleaning_times and segment.cleaning_times < 4
            else "mdi:home-floor-0"
        ),
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
            and not device.status.cleangenius_cleaning
        ),
        value_fn=lambda device, segment: f"{segment.cleaning_times}{UNIT_TIMES}",
        value_int_fn=lambda value, self: int(value[0]),
        exists_fn=lambda description, device: device.capability.customized_cleaning,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="custom_mopping_route",
        entity_category=None,
        icon_fn=lambda value, segment: (
            CUSTOM_MOPPING_ROUTE_TO_ICON.get(segment.custom_mopping_route, "mdi:routes") if segment else "mdi:routes"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and segment.cleaning_mode is not DreameVacuumCleaningMode.SWEEPING.value
            and not device.status.cleangenius_cleaning
        ),
        value_fn=lambda device, segment: CUSTOM_MOPPING_ROUTE_TO_NAME.get(
            segment.custom_mopping_route if segment.custom_mopping_route is not None else -1, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumCustomMoppingRoute[value.upper()].value,
        exists_fn=lambda description, device: device.capability.segment_mopping_settings
        and not device.capability.cleaning_route,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumAutoSwitchProperty.CLEANING_ROUTE.name.lower(),
        entity_category=None,
        icon_fn=lambda value, segment: (
            CLEANING_ROUTE_TO_ICON.get(segment.cleaning_route, "mdi:routes") if segment else "mdi:map-marker-remove"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
            and not device.status.scheduled_clean
            and not device.status.cruising
            and (
                segment.cleaning_mode is DreameVacuumCleaningMode.MOPPING.value
                and not device.capability.cleaning_route_v2
            )
            and not device.status.cleangenius_cleaning
        ),
        value_fn=lambda device, segment: CLEANING_ROUTE_TO_NAME.get(
            segment.cleaning_route if segment.cleaning_route else 1, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumCleaningRoute[value.upper()].value,
        exists_fn=lambda description, device: device.capability.cleaning_route,
        segment_list_fn=lambda device: device.status.current_segments,
        options=lambda device, segment: list(device.status.segment_cleaning_route_list),
    ),
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.MOP_PRESSURE.name.lower(),
        entity_category=None,
        icon_fn=lambda value, segment: "mdi:car-brake-low-pressure",
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
        value_fn=lambda device, segment: MOP_PRESSURE_TO_NAME.get(segment.mop_pressure, STATE_UNKNOWN),
        value_int_fn=lambda value, self: DreameVacuumMopPressure[value.upper()].value,
        exists_fn=lambda description, device: device.capability.mop_pressure,
        segment_list_fn=lambda device: device.status.current_segments,
        options=lambda device, segment: list(device.status.mop_pressure_list),
    ),
    DreameVacuumSelectEntityDescription(
        key=DreameVacuumProperty.MOP_TEMPERATURE.name.lower(),
        entity_category=None,
        icon_fn=lambda value, segment: "mdi:thermometer-water",
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
        value_fn=lambda device, segment: MOP_TEMPERATURE_TO_NAME.get(segment.mop_temperature, STATE_UNKNOWN),
        value_int_fn=lambda value, self: DreameVacuumMopTemperature[value.upper()].value,
        exists_fn=lambda description, device: device.capability.mop_temperature,
        segment_list_fn=lambda device: device.status.current_segments,
        options=lambda device, segment: list(device.status.mop_temperature_list),
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_type",
        entity_category=EntityCategory.CONFIG,
        icon_fn=lambda value, segment: (
            f"mdi:alpha-{segment.mop_type.lower()}-circle" if segment and segment.mop_type else "mdi:record-circle"
        ),
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and not device.status.started
            and not device.status.cruising
            and device.status.has_saved_map
            and not device.status.fast_mapping
            and segment.id in device.status.current_segments
            and device.status.auto_change_mop
        ),
        value_fn=lambda device, segment: segment.mop_type,
        exists_fn=lambda description, device: device.capability.auto_change_mop,
        segment_list_fn=lambda device: device.status.current_segments,
        options=lambda device, segment: ["A", "B", "C"],
    ),
    DreameVacuumSelectEntityDescription(
        key="order",
        options=lambda device, segment: (
            (
                device.status.segment_order_list(segment)
                if device.capability.cleaning_sequence_v2
                else ([STATE_NOT_SET] + device.status.segment_order_list(segment))
            )
            if segment and device.status.current_segments
            else [STATE_UNAVAILABLE]
        ),
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
            and segment.id in device.status.current_segments
        ),
        value_fn=lambda device, segment: str(segment.order) if segment.order else STATE_NOT_SET,
        exists_fn=lambda description, device: device.capability.customized_cleaning,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="floor_material",
        icon_fn=lambda value, segment: (
            FLOOR_MATERIAL_TO_ICON.get(segment.floor_material, "mdi:checkbox-blank")
            if segment
            else "mdi:checkbox-blank-off"
        ),
        entity_category=EntityCategory.CONFIG,
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.floor_material is not None
            and segment.visibility != False
            and not device.status.started
            and not device.status.fast_mapping
            and not device.status.has_temporary_map
            and not device.status.scheduled_clean
            and device.status.has_saved_map
        ),
        value_fn=lambda device, segment: FLOOR_MATERIAL_CODE_TO_NAME.get(segment.floor_material, STATE_UNKNOWN),
        value_int_fn=lambda value, self: DreameVacuumFloorMaterial[value.upper()].value,
        exists_fn=lambda description, device: device.capability.floor_material,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="floor_material_direction",
        icon_fn=lambda value, segment: (
            FLOOR_MATERIAL_DIRECTION_TO_ICON.get(
                segment.floor_material_rotated_direction,
                "mdi:arrow-top-left-bottom-right-bold",
            )
            if segment and segment.floor_material == 1
            else "mdi:arrow-top-left-bottom-right-bold"
        ),
        entity_category=EntityCategory.CONFIG,
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.floor_material == 1
            and segment.visibility != False
            and not device.status.started
            and not device.status.fast_mapping
            and not device.status.has_temporary_map
            and not device.status.scheduled_clean
            and device.status.has_saved_map
        ),
        value_fn=lambda device, segment: FLOOR_MATERIAL_DIRECTION_CODE_TO_NAME.get(
            (
                segment.floor_material_rotated_direction
                if segment.floor_material_rotated_direction is not None
                else (
                    DreameVacuumFloorMaterialDirection.VERTICAL
                    if device.status.current_map.rotation == 0 or device.status.current_map.rotation == 180
                    else DreameVacuumFloorMaterialDirection.HORIZONTAL
                )
            ),
            STATE_UNKNOWN,
        ),
        value_int_fn=lambda value, self: DreameVacuumFloorMaterialDirection[value.upper()].value,
        exists_fn=lambda description, device: device.capability.floor_direction_cleaning,
        segment_list_fn=lambda device: device.status.current_segments,
    ),
    DreameVacuumSelectEntityDescription(
        key="visibility",
        icon_fn=lambda value, segment: (
            SEGMENT_VISIBILITY_TO_ICON.get(segment.visibility, "mdi:eye") if segment else "mdi:home-remove"
        ),
        entity_category=EntityCategory.CONFIG,
        segment_available_fn=lambda device, segment: bool(
            device.status.current_segments
            and segment.visibility is not None
            and not device.status.started
            and not device.status.fast_mapping
            and not device.status.has_temporary_map
            and not device.status.scheduled_clean
            and device.status.has_saved_map
        ),
        value_fn=lambda device, segment: SEGMENT_VISIBILITY_CODE_TO_NAME.get(segment.visibility, STATE_UNKNOWN),
        value_int_fn=lambda value, self: DreameVacuumSegmentVisibility[value.upper()].value,
        exists_fn=lambda description, device: device.capability.segment_visibility,
        segment_list_fn=lambda device: device.status.segments,
    ),
    DreameVacuumSelectEntityDescription(
        name="",
        key="name",
        options=lambda device, segment: list(segment.name_list(device.status.segments)),
        entity_category=EntityCategory.CONFIG,
        segment_available_fn=lambda device, segment: bool(
            device.status.segments and not device.status.fast_mapping and not device.status.has_temporary_map
        ),
        value_fn=lambda device, segment: (
            device.status.segments[segment.id].name if segment.id in device.status.segments else None
        ),
        value_int_fn=lambda value, self: next(
            (type for name, type in self.segment.name_list(self.device.status.segments).items() if name == value),
            None,
        ),
        attrs_fn=lambda segment: {
            "room_id": segment.id,
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

    remove_entities(hass, entry, coordinator, "select", SELECTS)
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
    platform.async_register_entity_service(SERVICE_SELECT_FIRST, {}, DreameVacuumSelectEntity.async_first.__name__)
    platform.async_register_entity_service(SERVICE_SELECT_LAST, {}, DreameVacuumSelectEntity.async_last.__name__)

    update_segment_selects = partial(async_update_segment_selects, coordinator, {}, async_add_entities)
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
        if description.value_fn is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                prop = f"{description.property_key.name.lower()}_name"
            else:
                prop = f"{description.key.lower()}_name"
            if hasattr(coordinator.device.status, prop):
                description.value_fn = lambda value, device: getattr(device.status, prop)

        if description.set_fn is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                set_prop = f"set_{description.property_key.name.lower()}"
            else:
                set_prop = f"set_{description.key.lower()}"
            if hasattr(coordinator.device, set_prop):
                description.set_fn = lambda device, segment_id, value: getattr(device, set_prop)(value)

        if description.options is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                options_prop = f"{description.property_key.name.lower()}_list"
            else:
                options_prop = f"{description.key.lower()}_list"
            if hasattr(coordinator.device.status, options_prop):
                description.options = lambda device, segment: list(getattr(device.status, options_prop))

        super().__init__(coordinator, description)
        self._generate_entity_id(ENTITY_ID_FORMAT)
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
            value = self.entity_description.value_int_fn(option, self)

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

        if description.options is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                segment_options_prop = f"{description.property_key.name.lower()}_list"
            else:
                segment_options_prop = f"{description.key.lower()}_list"
            if hasattr(coordinator.device.status, segment_options_prop):
                description.options = lambda device, segment: list(getattr(device.status, segment_options_prop))

        super().__init__(coordinator, description)
        self._attr_unique_id = f"{self.device.mac}_room_{segment_id}_{description.key.lower()}"
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT,
            f"{self.device.name}_room_{segment_id}_{description.key.lower()}",
            hass=self.coordinator.hass,
        )
        self._attr_options = []
        self._attr_current_option = "unavailable"
        if self.segment:
            if description.options is not None:
                self._attr_options = description.options(coordinator.device, self.segment)
            self._attr_current_option = self.native_value

    def _set_id(self) -> None:
        """Set name, unique id and icon of the entity"""
        if self.entity_description.name == "":
            name = f"room_{self.segment_id}_{self.entity_description.key}"
        elif self.segment:
            name = f"{self.entity_description.key}_{self.segment.name}"
        else:
            name = f"{self.entity_description.key}_room_unavailable"

        self._attr_name = name.replace("_", " ").title()

        if self.entity_description.icon_fn is not None:
            self._attr_icon = self.entity_description.icon_fn(self.native_value, self.segment)
        elif self.segment:
            self._attr_icon = self.segment.icon
        else:
            self._attr_icon = "mdi:home-off-outline"

    @property
    def _device_segments(self):
        return self.entity_description.segment_list_fn(self.device)

    @property
    def enabled(self) -> bool:
        if (
            not self.device.status.multi_map
            and self._attr_available
            and self.segments
            and self.segment_id not in self.segments
        ):
            return False
        return self.registry_entry is None or not self.registry_entry.disabled

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
                    self._attr_options = self.entity_description.options(self.device, self.segment)
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

        if not isinstance(value, int) and (
            isinstance(value, IntEnum) or (isinstance(value, str) and value.isnumeric())
        ):
            value = int(value)

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
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes of the entity."""
        attrs = None
        if self.entity_description.attrs_fn is not None:
            attrs = self.entity_description.attrs_fn(self.segment)
        elif self.entity_description.value_fn is not None or self.entity_description.value_int_fn is not None:
            if self.entity_description.property_key is not None:
                attrs = {ATTR_VALUE: self.device.get_property(self.entity_description.property_key)}
            elif self.entity_description.value_int_fn is not None:
                attrs = {ATTR_VALUE: self.entity_description.value_int_fn(self.native_value, self)}

        return attrs

    @property
    def native_value(self) -> str | None:
        """Return the current Dreame Vacuum select value."""
        if self.segment:
            return self.entity_description.value_fn(self.device, self.segment)
