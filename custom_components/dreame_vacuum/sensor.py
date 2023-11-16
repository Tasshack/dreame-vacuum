"""Support for Dreame Vacuum sensors."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry

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

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription


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
class DreameVacuumSensorEntityDescription(
    DreameVacuumEntityDescription, SensorEntityDescription
):
    """Describes DreameVacuum sensor entity."""


SENSORS: tuple[DreameVacuumSensorEntityDescription, ...] = (
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_TIME,
        icon="mdi:timer-sand",
        native_unit_of_measurement=UNIT_MINUTES,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_TIME,
        name="Mapping Time",
        key="mapping_time",
        icon="mdi:map-clock",
        native_unit_of_measurement=UNIT_MINUTES,
        available_fn=lambda device: device.status.fast_mapping,
        exists_fn=lambda description, device: device.capability.lidar_navigation,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANED_AREA,
        icon="mdi:ruler-square",
        native_unit_of_measurement=UNIT_AREA,
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
        icon_fn=lambda value, device: "mdi:water-pump-off"
        if not device.status.water_tank_or_mop_installed
        else "mdi:water-pump",
        exists_fn=lambda description, device: not device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        key="mop_pad",
        icon="mdi:google-circles-communities",
        exists_fn=lambda description, device: device.capability.self_wash_base,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DUST_COLLECTION,
        icon_fn=lambda value, device: "mdi:delete-off"
        if not device.status.dust_collection
        else "mdi:delete-sweep",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.AUTO_EMPTY_STATUS,
        icon_fn=lambda value, device: "mdi:delete-clock"
        if device.status.auto_emptying_not_performed
        else "mdi:delete-restore"
        if device.status.auto_emptying
        else "mdi:delete",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SELF_WASH_BASE_STATUS,
        icon="mdi:dishwasher",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.LOW_WATER_WARNING,
        icon_fn=lambda value, device: "mdi:water-alert"
        if device.status.low_water_warning.value > 1
        else "mdi:water-check",
        exists_fn=lambda description, device: device.capability.self_wash_base
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DRAINAGE_STATUS,
        icon_fn=lambda value, device: "mdi:pump"
        if device.status.draining
        else "mdi:pump-off",
        exists_fn=lambda description, device: device.capability.drainage,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TASK_TYPE,
        icon="mdi:sitemap",
        exists_fn=lambda description, device: device.status.task_type.value > 0,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.STREAM_STATUS,
        icon_fn=lambda value, device: STREAM_STATUS_TO_ICON.get(
            device.status.stream_status, "mdi:webcam-off"
        ),
        exists_fn=lambda description, device: device.capability.stream_status
        or DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ERROR,
        icon_fn=lambda value, device: "mdi:alert-circle-outline"
        if device.status.has_error
        else "mdi:alert-outline"
        if device.status.has_warning
        else "mdi:check-circle-outline",
        attrs_fn=lambda device: {
            "value": device.status.error,
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
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MAIN_BRUSH_LEFT,
        icon="mdi:car-turbocharger",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT,
        icon="mdi:car-turbocharger",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SIDE_BRUSH_LEFT,
        icon="mdi:pinwheel-outline",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT,
        icon="mdi:pinwheel-outline",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FILTER_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FILTER_TIME_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SENSOR_DIRTY_LEFT,
        icon="mdi:radar",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
        icon="mdi:radar",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SECONDARY_FILTER_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SECONDARY_FILTER_TIME_LEFT,
        icon="mdi:air-filter",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MOP_PAD_LEFT,
        icon="mdi:hydro-power",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MOP_PAD_TIME_LEFT,
        icon="mdi:hydro-power",
        native_unit_of_measurement=UNIT_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SILVER_ION_LEFT,
        icon="mdi:shimmer",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SILVER_ION_TIME_LEFT,
        icon="mdi:shimmer",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DETERGENT_LEFT,
        icon="mdi:water-opacity",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DETERGENT_TIME_LEFT,
        icon="mdi:water-opacity",
        native_unit_of_measurement=UNIT_DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FIRST_CLEANING_DATE,
        icon="mdi:calendar-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value, device: datetime.fromtimestamp(value).replace(
            tzinfo=datetime.now().astimezone().tzinfo
        ),
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TOTAL_CLEANING_TIME,
        icon="mdi:timer-outline",
        native_unit_of_measurement=UNIT_MINUTES,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_COUNT,
        icon="mdi:counter",
        native_unit_of_measurement=UNIT_TIMES,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TOTAL_CLEANED_AREA,
        icon="mdi:set-square",
        native_unit_of_measurement=UNIT_AREA,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DreameVacuumSensorEntityDescription(
        key="current_room",
        icon="mdi:home-map-marker",
        value_fn=lambda value, device: device.status.current_room.name,
        exists_fn=lambda description, device: device.capability.map
        and device.capability.lidar_navigation,
        attrs_fn=lambda device: {
            "room_id": device.status.current_room.segment_id,
            "room_icon": device.status.current_room.icon,
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
        exists_fn=lambda description, device: device.capability.map
        and device.capability.cruising,
        attrs_fn=lambda device: device.status.cruising_history,
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

        super().__init__(coordinator, description)
