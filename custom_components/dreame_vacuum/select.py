"""Support for Dreame Vacuum selects."""
from __future__ import annotations

import copy
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
    UNIT_HOURS,
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
    DreameVacuumSuctionLevel,
    DreameVacuumCleaningMode,
    DreameVacuumWaterVolume,
    DreameVacuumSelfCleanArea,
    DreameVacuumMopPadHumidity,
    DreameVacuumCarpetSensitivity,
    DreameVacuumMopWashLevel,
    DreameVacuumMoppingType,
    SUCTION_LEVEL_CODE_TO_NAME,
    WATER_VOLUME_CODE_TO_NAME,
    MOP_PAD_HUMIDITY_CODE_TO_NAME,
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


@dataclass
class DreameVacuumSelectEntityDescription(
    DreameVacuumEntityDescription, SelectEntityDescription
):
    """Describes Dreame Vacuum Select entity."""

    set_fn: Callable[[object, int, int]] = None
    options: Callable[[object, object], list[str]] = None
    value_int_fn: Callable[[object, str], int] = None


SELECTS: tuple[DreameVacuumSelectEntityDescription, ...] = (
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.SUCTION_LEVEL,
        device_class=f"{DOMAIN}__suction_level",
        icon_fn=lambda value, device: "mdi:fan-off"
        if device.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING
        else SUCTION_LEVEL_TO_ICON.get(device.status.suction_level, "mdi:fan"),
        options=lambda device, segment: list(device.status.suction_level_list),
        value_int_fn=lambda value, device: DreameVacuumSuctionLevel[value.upper()],
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.WATER_VOLUME,
        device_class=f"{DOMAIN}__water_volume",
        icon_fn=lambda value, device: "mdi:water-off"
        if (
            not device.status.water_tank_or_mop_installed
            or device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING
        )
        else WATER_VOLUME_TO_ICON.get(device.status.water_volume, "mdi:water"),
        options=lambda device, segment: list(device.status.water_volume_list),
        value_int_fn=lambda value, device: DreameVacuumWaterVolume[value.upper()],
        exists_fn=lambda description, device: bool(
            not device.status.self_wash_base_available and 
            DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_MODE,
        device_class=f"{DOMAIN}__cleaning_mode",
        icon_fn=lambda value, device: "mdi:hydro-power"
        if device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
        else "mdi:cup-water"
        if device.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING
        else "mdi:broom",
        options=lambda device, segment: list(device.status.cleaning_mode_list),
        value_fn=lambda value, device: device.status.cleaning_mode_name,
        value_int_fn=lambda value, device: DreameVacuumCleaningMode[value.upper()],
        set_fn=lambda device, map_id, value: device.set_cleaning_mode(value),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.CARPET_SENSITIVITY,
        device_class=f"{DOMAIN}__carpet_sensitivity",
        icon="mdi:rug",
        options=lambda device, segment: list(device.status.carpet_sensitivity_list),
        value_int_fn=lambda value, device: DreameVacuumCarpetSensitivity[value.upper()],
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.AUTO_EMPTY_FREQUENCY,
        icon_fn=lambda value, device: f"mdi:numeric-{value[0]}-box-multiple-outline",
        options=lambda device, segment: [f"{i}{UNIT_TIMES}" for i in range(1, 4)],
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: f"{value}{UNIT_TIMES}",
        value_int_fn=lambda value, device: int(value[0]),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.DRYING_TIME, 
        icon="mdi:hair-dryer",
        options=lambda device, segment: [f"{i}h" for i in range(2, 5)],
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: f"{value}h",
        value_int_fn=lambda value, device: int(value[0]),
    ),
    DreameVacuumSelectEntityDescription(
        property_key=DreameVacuumProperty.MOP_WASH_LEVEL,
        device_class=f"{DOMAIN}__mop_wash_level",
        icon="mdi:water-opacity",
        options=lambda device, segment: list(device.status.mop_wash_level_list),
        value_int_fn=lambda value, device: DreameVacuumMopWashLevel[value.upper()],
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_pad_humidity",
        device_class=f"{DOMAIN}__mop_pad_humidity",
        icon_fn=lambda value, device: "mdi:water-off"
        if (
            not device.status.water_tank_or_mop_installed
            or device.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING
        )
        else MOP_PAD_HUMIDITY_TO_ICON.get(device.status.mop_pad_humidity, "mdi:water-percent"),
        options=lambda device, segment: list(device.status.mop_pad_humidity_list),
        value_fn=lambda value, device: device.status.mop_pad_humidity_name,
        value_int_fn=lambda value, device: DreameVacuumMopPadHumidity[value.upper()],
        exists_fn=lambda description, device: device.status.self_wash_base_available,
        available_fn=lambda device: device.status.water_tank_or_mop_installed and not device.status.sweeping and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning)) and not device.status.fast_mapping and not device.status.started,
        set_fn=lambda device, map_id, value: device.set_mop_pad_humidity(value),
    ),
    DreameVacuumSelectEntityDescription(
        key="self_clean_area",
        device_class=f"{DOMAIN}__self_clean_area",
        icon="mdi:texture-box",
        options=lambda device, segment: list(device.status.self_clean_area_list),
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: device.status.self_clean_area_name,
        value_int_fn=lambda value, device: DreameVacuumSelfCleanArea[value.upper()],
        exists_fn=lambda description, device: device.status.self_wash_base_available,
        available_fn=lambda device: device.status.self_clean and not device.status.started and not device.status.fast_mapping and not device.status.cleaning_paused,
        set_fn=lambda device, map_id, value: device.set_self_clean_area(value),
    ),
    DreameVacuumSelectEntityDescription(
        key="mopping_type",
        device_class=f"{DOMAIN}__mopping_type",
        icon="mdi:spray-bottle",
        options=lambda device, segment: list(device.status.mopping_type_list),
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: device.status.mopping_type_name,
        value_int_fn=lambda value, device: DreameVacuumMoppingType[value.upper()],
        exists_fn=lambda description, device: device.status.auto_switch_settings_available and device.status.mopping_type is not None,
        available_fn=lambda device: not device.status.started and not device.status.fast_mapping and not device.status.cleaning_paused,
        set_fn=lambda device, map_id, value: device.set_mopping_type(value),
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
        exists_fn=lambda description, device: device.status.map_available,
        available_fn=lambda device: bool(
            device.status.selected_map is not None
            and device.status.selected_map.rotation is not None
            and not device.status.fast_mapping
            and device.status.has_saved_map
        ),
        set_fn=lambda device, map_id, value: device.set_map_rotation(
            device.status.selected_map.map_id, value
        ),
    ),
    DreameVacuumSelectEntityDescription(
        key="selected_map",
        icon="mdi:map-check",
        options=lambda device, segment: [
            v.map_name for k, v in device.status.map_data_list.items()
        ],
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda value, device: device.status.selected_map.map_name
        if device.status.selected_map and device.status.selected_map.map_name
        else "",
        exists_fn=lambda description, device: device.status.map_available,# and device.status.lidar_navigation,
        available_fn=lambda device: bool(
            device.status.multi_map
            and not device.status.fast_mapping
            and device.status.map_list
            and device.status.selected_map
            and device.status.selected_map.map_name
            and device.status.selected_map.map_id in device.status.map_list
        ),
        value_int_fn=lambda value, device: next(
            (k for k, v in device.status.map_data_list.items() if v.map_name == value),
            None,
        ),
        set_fn=lambda device, map_id, value: device.select_map(value),
        attrs_fn=lambda device: {"map_id": device.status.selected_map.map_id, "map_index": device.status.selected_map.map_index}
        if device.status.selected_map
        else None,
    ),
)

SEGMENT_SELECTS: tuple[DreameVacuumSelectEntityDescription, ...] = (
    DreameVacuumSelectEntityDescription(
        key="suction_level",
        device_class=f"{DOMAIN}__suction_level",
        icon_fn=lambda value, segment: SUCTION_LEVEL_TO_ICON.get(
            segment.suction_level, "mdi:fan"
        )
        if segment
        else "mdi:fan-off",
        options=lambda device, segment: list(device.status.suction_level_list),
        available_fn=lambda device: bool(
            device.status.segments
            and next(iter(device.status.segments.values())).suction_level is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
        ),
        value_fn=lambda device, segment: SUCTION_LEVEL_CODE_TO_NAME.get(
            segment.suction_level, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumSuctionLevel[value.upper()],
        set_fn=lambda device, segment_id, value: device.set_segment_suction_level(
            segment_id, value
        ),
        exists_fn=lambda description, device: device.status.customized_cleaning_available,
    ),
    DreameVacuumSelectEntityDescription(
        key="water_volume",
        device_class=f"{DOMAIN}__water_volume",
        icon_fn=lambda value, segment: WATER_VOLUME_TO_ICON.get(
            segment.water_volume, "mdi:water"
        )
        if segment
        else "mdi:water-off",
        options=lambda device, segment: list(device.status.water_volume_list),
        available_fn=lambda device: bool(
            device.status.segments
            and next(iter(device.status.segments.values())).water_volume is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
        ),
        value_fn=lambda device, segment: WATER_VOLUME_CODE_TO_NAME.get(
            segment.water_volume, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumWaterVolume[value.upper()],
        set_fn=lambda device, segment_id, value: device.set_segment_water_volume(
            segment_id, value
        ),
        exists_fn=lambda description, device: device.status.customized_cleaning_available and not device.status.self_wash_base_available,
    ),
    DreameVacuumSelectEntityDescription(
        key="mop_pad_humidity",
        device_class=f"{DOMAIN}__mop_pad_humidity",
        icon_fn=lambda value, segment: MOP_PAD_HUMIDITY_TO_ICON.get(
            segment.water_volume, "mdi:water-percent"
        )
        if segment
        else "mdi:water-off",
        options=lambda device, segment: list(device.status.mop_pad_humidity_list),
        available_fn=lambda device: bool(
            device.status.segments
            and next(iter(device.status.segments.values())).mop_pad_humidity is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.fast_mapping
        ),
        value_fn=lambda device, segment: MOP_PAD_HUMIDITY_CODE_TO_NAME.get(
            segment.mop_pad_humidity, STATE_UNKNOWN
        ),
        value_int_fn=lambda value, self: DreameVacuumMopPadHumidity[value.upper()],
        set_fn=lambda device, segment_id, value: device.set_segment_mop_pad_humidity(
            segment_id, value
        ),
        exists_fn=lambda description, device: device.status.customized_cleaning_available and device.status.self_wash_base_available,
    ),
    DreameVacuumSelectEntityDescription(
        key="cleaning_times",
        icon_fn=lambda value, segment: "mdi:home-floor-" + str(segment.cleaning_times)
        if segment and segment.cleaning_times and segment.cleaning_times < 4
        else "mdi:home-floor-0",
        options=lambda device, segment: [f"{i}{UNIT_TIMES}" for i in range(1, 4)],
        available_fn=lambda device: bool(
            device.status.segments
            and next(iter(device.status.segments.values())).cleaning_times is not None
            and device.status.customized_cleaning
            and not (device.status.zone_cleaning or device.status.spot_cleaning)
            and not device.status.started
            and not device.status.fast_mapping
        ),
        value_fn=lambda device, segment: f"{segment.cleaning_times}{UNIT_TIMES}",
        value_int_fn=lambda value, self: int(value[0]),
        set_fn=lambda device, segment_id, value: device.set_segment_cleaning_times(
            segment_id, value
        ),
        exists_fn=lambda description, device: device.status.customized_cleaning_available,
    ),
    DreameVacuumSelectEntityDescription(
        key="order",
        options=lambda device, segment: [
            str(i) for i in range(1, len(device.status.segments.values()) + 1)
        ]
        if device.status.segments
        else [STATE_UNAVAILABLE],
        entity_category=EntityCategory.CONFIG,
        available_fn=lambda device: bool(
            device.status.segments
            and next(iter(device.status.segments.values())).order is not None
            and not device.status.started
            and device.status.custom_order
            and device.status.has_saved_map
            and not device.status.fast_mapping
        ),
        value_fn=lambda device, segment: str(segment.order) if segment.order else STATE_UNAVAILABLE,
        set_fn=lambda device, segment_id, value: device.set_segment_order(
            segment_id, value
        )
        if value > 0
        else None,
        exists_fn=lambda description, device: device.status.customized_cleaning_available,
    ),
    DreameVacuumSelectEntityDescription(
        name="",
        key="name",
        options=lambda device, segment: list(segment.name_list(device.status.segments)),
        entity_category=EntityCategory.CONFIG,
        available_fn=lambda device: bool(
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
        set_fn=lambda device, segment_id, value: device.set_segment_name(
            segment_id, value
        ),
        attrs_fn=lambda segment: {
            "room_id": segment.segment_id,
            "index": segment.index,
            "type": segment.type,
        },
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
        for (k, v) in coordinator.device.status.map_data_list.items():
            for (j, s) in v.segments.items():
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
        super().__init__(coordinator, description)            
        if description.property_key is not None and description.value_fn is None:
            prop = f'{description.property_key.name.lower()}_name'
            if hasattr(coordinator.device.status, prop):
                description.value_fn = lambda value, device: getattr(device.status, prop)

        self._attr_options = description.options(coordinator.device, None)
        self._attr_current_option = self.native_value

    @callback
    def _handle_coordinator_update(self) -> None:
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
        current_index = (self._attr_options.index(self._attr_current_option))
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

        if self.entity_description.set_fn is not None:
            await self._try_command(
                "Unable to call %s",
                self.entity_description.set_fn,
                self.device,
                0,
                int(value),
            )
        elif self.entity_description.property_key is not None:
            await self._try_command(
                "Unable to call %s",
                self.device.set_property,
                self.entity_description.property_key,
                int(value),
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
            self.segments = copy.deepcopy(coordinator.device.status.segments)
            if segment_id in self.segments:
                self.segment = self.segments[segment_id]

        super().__init__(coordinator, description)
        self._attr_unique_id = f"{self.device.mac}_room_{segment_id}_{description.key.lower()}"
        self.entity_id = f"select.{self.device.name.lower()}_room_{segment_id}_{description.key.lower()}"
        self._attr_options = []
        self._attr_current_option = "unavailable"
        if self.segment:
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

        self._attr_name = f"{self.device.name} {name.replace('_', ' ').title()}"

        if self.entity_description.icon_fn is not None:
            self._attr_icon = self.entity_description.icon_fn(
                self.native_value, self.segment
            )
        elif self.segment:
            self._attr_icon = self.segment.icon
        else:
            self._attr_icon = "mdi:home-off-outline"

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.segments != self.device.status.segments:
            self.segments = copy.deepcopy(self.device.status.segments)
            if self.segments and self.segment_id in self.segments:
                if self.segment != self.segments[self.segment_id]:
                    self.segment = self.segments[self.segment_id]
                    self._attr_current_option = self.native_value
                    self._set_id()
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
        current_index = (self._attr_options.index(self._attr_current_option))
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
        if super().available:
            return bool(self.segment is not None)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the extra state attributes of the entity."""
        if self.entity_description.attrs_fn is not None and self.segment:
            return self.entity_description.attrs_fn(self.segment)
        return None

    @property
    def native_value(self) -> str | None:
        """Return the current Dreame Vacuum number value."""
        if self.segment:
            return self.entity_description.value_fn(self.device, self.segment)