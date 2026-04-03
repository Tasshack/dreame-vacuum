"""Support for Dreame Vacuum sensors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    UNIT_MINUTES,
    UNIT_HOURS,
    UNIT_PERCENT,
    UNIT_AREA,
    UNIT_TIMES,
    UNIT_DAYS,
)
from .dreame import (
    DreameVacuumProperty,
    DreameVacuumRelocationStatus,
    DreameVacuumStreamStatus,
)
from .dreame.const import ATTR_VALUE
from .dreame.types import ATTR_ROOM_ID, ATTR_ROOM_ICON

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription, remove_entities


STREAM_STATUS_TO_ICON = {
    DreameVacuumStreamStatus.IDLE: "mdi:webcam",
    DreameVacuumStreamStatus.VIDEO: "mdi:cctv",
    DreameVacuumStreamStatus.AUDIO: "mdi:microphone",
    DreameVacuumStreamStatus.RECORDING: "mdi:record-rec",
}

RELOCATION_STATUS_TO_ICON = {
    DreameVacuumRelocationStatus.LOCATED: "mdi:map-marker-radius",
    DreameVacuumRelocationStatus.SUCCESS: "mdi:map-marker-check",
    DreameVacuumRelocationStatus.FAILED: "mdi:map-marker-alert",
    DreameVacuumRelocationStatus.LOCATING: "mdi:map-marker-distance",
}


@dataclass
class DreameVacuumSensorEntityDescription(DreameVacuumEntityDescription, SensorEntityDescription):
    """Describes DreameVacuum sensor entity."""


SENSORS: tuple[DreameVacuumSensorEntityDescription, ...] = (
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_TIME,
        icon="mdi:timer-sand",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UNIT_MINUTES,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_TIME,
        name="Mapping Time",
        key="mapping_time",
        icon="mdi:map-clock",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UNIT_MINUTES,
        available_fn=lambda device: device.status.fast_mapping,
        exists_fn=lambda description, device: device.capability.lidar_navigation,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANED_AREA,
        icon="mdi:ruler-square",
        device_class=SensorDeviceClass.AREA,
        native_unit_of_measurement=UNIT_AREA,
        suggested_display_precision=0,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.STATE,
        icon="mdi:robot-vacuum",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.STATUS,
        icon="mdi:vacuum",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.RELOCATION_STATUS,
        icon_fn=lambda value, device: RELOCATION_STATUS_TO_ICON.get(
            device.status.relocation_status, "mdi:map-marker-radius"
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TASK_STATUS,
        icon="mdi:file-tree",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WATER_TANK,
        icon_fn=lambda value, device: (
            "mdi:water-pump-off" if not device.status.water_tank_or_mop_installed else "mdi:water-pump"
        ),
        exists_fn=lambda description, device: not device.capability.self_wash_base
        and not device.capability.embedded_tank
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        key="mop_pad",
        icon="mdi:google-circles-communities",
        exists_fn=lambda description, device: device.capability.self_wash_base,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DUST_COLLECTION,
        icon_fn=lambda value, device: "mdi:delete-off" if not device.status.dust_collection else "mdi:delete-sweep",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.AUTO_EMPTY_STATUS,
        icon_fn=lambda value, device: (
            "mdi:delete-clock"
            if device.status.auto_emptying_not_performed
            else "mdi:delete-restore" if device.status.auto_emptying else "mdi:delete"
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SELF_WASH_BASE_STATUS,
        icon="mdi:dishwasher",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.LOW_WATER_WARNING,
        icon_fn=lambda value, device: (
            "mdi:water-alert" if device.status.low_water_warning.value > 1 else "mdi:water-check"
        ),
        exists_fn=lambda description, device: device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DRAINAGE_STATUS,
        icon_fn=lambda value, device: "mdi:pump" if device.status.draining else "mdi:pump-off",
        exists_fn=lambda description, device: device.capability.water_check,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TASK_TYPE,
        icon="mdi:sitemap",
        exists_fn=lambda description, device: device.capability.task_type,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.STREAM_STATUS,
        icon_fn=lambda value, device: STREAM_STATUS_TO_ICON.get(device.status.stream_status, "mdi:webcam-off"),
        exists_fn=lambda description, device: device.capability.camera_streaming
        or DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ERROR,
        icon_fn=lambda value, device: (
            "mdi:alert-circle-outline"
            if device.status.has_error
            else "mdi:alert-outline" if device.status.has_warning else "mdi:check-circle-outline"
        ),
        attrs_fn=lambda device: {
            ATTR_VALUE: device.status.error,
            "faults": device.status.faults,
            "description": device.status.error_description[0],
        },
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CHARGING_STATUS,
        icon="mdi:home-lightning-bolt",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.BATTERY_LEVEL,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=UNIT_PERCENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon_fn=lambda value, device: (
            "mdi:battery-heart-variant"
            if device.status.battery_charge_level != 100
            and not device.status.charging
            and device.status.battery_level == device.status.battery_charge_level
            else icon_for_battery_level(device.status.battery_level, device.status.charging)
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MAIN_BRUSH_LEFT,
        icon="mdi:car-turbocharger",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT,
        icon="mdi:car-turbocharger",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SIDE_BRUSH_LEFT,
        icon="mdi:pinwheel-outline",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT,
        icon="mdi:pinwheel-outline",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FILTER_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FILTER_TIME_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SENSOR_DIRTY_LEFT,
        icon="mdi:radar",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: not device.capability.disable_sensor_cleaning,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
        icon="mdi:radar",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: not device.capability.disable_sensor_cleaning,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TANK_FILTER_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TANK_FILTER_TIME_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MOP_PAD_LEFT,
        icon="mdi:hydro-power",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and not device.capability.disable_mop_consumable
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MOP_PAD_TIME_LEFT,
        icon="mdi:hydro-power",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and not device.capability.disable_mop_consumable
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SILVER_ION_LEFT,
        icon="mdi:shimmer",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SILVER_ION_TIME_LEFT,
        icon="mdi:shimmer",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DETERGENT_LEFT,
        icon="mdi:water-opacity",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.detergent
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DETERGENT_TIME_LEFT,
        icon="mdi:water-opacity",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.detergent
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SQUEEGEE_LEFT,
        icon="mdi:squeegee",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.squeegee
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SQUEEGEE_TIME_LEFT,
        icon="mdi:squeegee",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.squeegee
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT,
        icon="mdi:train-car-tank",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.capability.onboard_dirty_water_tank
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT,
        icon="mdi:train-car-tank",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.capability.onboard_dirty_water_tank
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_LEFT,
        icon="mdi:cup",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_TIME_LEFT,
        icon="mdi:cup",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DEODORIZER_LEFT,
        icon="mdi:scent",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.capability.deodorizer
            and device.capability.self_wash_base
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DEODORIZER_TIME_LEFT,
        icon="mdi:scent",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.capability.deodorizer
            and device.capability.self_wash_base
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WHEEL_DIRTY_LEFT,
        icon="mdi:tire",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.wheel
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT,
        icon="mdi:tire",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.wheel
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SCALE_INHIBITOR_LEFT,
        icon="mdi:pipe",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.scale_inhibitor
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT,
        icon="mdi:pipe",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.scale_inhibitor
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FLUFFING_ROLLER_DIRTY_LEFT,
        icon="mdi:blinds-open",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.fluffing_roller
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FLUFFING_ROLLER_DIRTY_TIME_LEFT,
        icon="mdi:blinds-open",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.fluffing_roller
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ROLLER_MOP_FILTER_DIRTY_LEFT,
        icon="mdi:blinds-open",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.roller_mop_filter
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ROLLER_MOP_FILTER_DIRTY_TIME_LEFT,
        icon="mdi:filter-settings",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.roller_mop_filter
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WATER_OUTLET_FILTER_DIRTY_LEFT,
        icon="mdi:filter-settings",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.water_outlet_filter
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WATER_OUTLET_FILTER_DIRTY_TIME_LEFT,
        icon="mdi:filter-settings",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.water_outlet_filter
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FIRST_CLEANING_DATE,
        icon="mdi:calendar-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value, device: datetime.fromtimestamp(value).replace(
            tzinfo=datetime.now().astimezone().tzinfo
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TOTAL_CLEANING_TIME,
        icon="mdi:timer-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UNIT_MINUTES,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_COUNT,
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UNIT_TIMES,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TOTAL_CLEANED_AREA,
        icon="mdi:set-square",
        device_class=SensorDeviceClass.AREA,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UNIT_AREA,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEAN_WATER_TANK_STATUS,
        icon="mdi:beer",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda description, device: device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DIRTY_WATER_TANK_STATUS,
        icon="mdi:glass-mug",
        exists_fn=lambda description, device: device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DUST_BAG_STATUS,
        icon="mdi:delete-circle-outline",
        exists_fn=lambda description, device: device.capability.auto_empty_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DETERGENT_STATUS,
        icon="mdi:chart-bubble",
        exists_fn=lambda description, device: device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.STATION_DRAINAGE_STATUS,
        icon="mdi:water-pump",
        exists_fn=lambda description, device: device.capability.drainage
        and DreameVacuumEntityDescription().exists_fn(description, device),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.HOT_WATER_STATUS,
        icon="mdi:water-thermometer",
        exists_fn=lambda description, device: device.capability.hot_washing
        and DreameVacuumEntityDescription().exists_fn(description, device),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DUST_BAG_DRYING_STATUS,
        icon="mdi:fire-circle",
        exists_fn=lambda description, device: device.capability.dust_bag_drying
        or device.capability.manual_dust_bag_drying
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        key="current_room",
        icon="mdi:home-map-marker",
        value_fn=lambda value, device: device.status.current_room.name,
        exists_fn=lambda description, device: device.capability.map and device.capability.lidar_navigation,
        attrs_fn=lambda device: {
            ATTR_ROOM_ID: device.status.current_room.id,
            ATTR_ROOM_ICON: device.status.current_room.icon,
        },
    ),
    DreameVacuumSensorEntityDescription(
        key="cleaning_history",
        icon="mdi:clipboard-text-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda value, device: device.status.last_cleaning_time,
        exists_fn=lambda description, device: device.capability.map,
        attrs_fn=lambda device: device.status.cleaning_history,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        key="cruising_history",
        icon="mdi:map-marker-path",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda value, device: device.status.last_cruising_time,
        exists_fn=lambda description, device: device.capability.map and device.capability.cruising,
        attrs_fn=lambda device: device.status.cruising_history,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_PROGRESS,
        icon="mdi:home-percent",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=None,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DRYING_PROGRESS,
        icon="mdi:water-percent",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=None,
        exists_fn=lambda description, device: device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        key="drying_left",
        property_key=DreameVacuumProperty.DRYING_PROGRESS,
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UNIT_MINUTES,
        value_fn=lambda value, device: device.status.drying_left_time,
        entity_category=None,
        exists_fn=lambda description, device: device.capability.self_wash_base
        and (device.capability.dust_bag_drying or device.capability.manual_dust_bag_drying)
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DUST_BAG_DRYING_LEFT,
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UNIT_MINUTES,
        value_fn=lambda value, device: int(value / 60) if value > 60 else 1,
        entity_category=None,
        exists_fn=lambda description, device: device.capability.dust_bag_drying
        or device.capability.manual_dust_bag_drying,
    ),
    DreameVacuumSensorEntityDescription(
        key="firmware_version",
        icon="mdi:chip",
        value_fn=lambda value, device: device.info.version,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum sensor based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    remove_entities(hass, entry, coordinator, "sensor", SENSORS)
    async_add_entities(
        DreameVacuumSensorEntity(coordinator, description)
        for description in SENSORS
        if description.exists_fn(description, coordinator.device)
    )


class DreameVacuumSensorEntity(DreameVacuumEntity, SensorEntity):
    """Defines a Dreame Vacuum sensor entity."""

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumSensorEntityDescription,
    ) -> None:
        """Initialize a Dreame Vacuum sensor entity."""
        if description.value_fn is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                prop = f"{description.property_key.name.lower()}_name"
            else:
                prop = f"{description.key.lower()}_name"
            if hasattr(coordinator.device.status, prop):
                description.value_fn = lambda value, device: getattr(device.status, prop)
        super().__init__(coordinator, description)
        self._generate_entity_id(ENTITY_ID_FORMAT)
