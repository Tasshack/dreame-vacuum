"""Support for Dreame Vacuum sensors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UNIT_MINUTES, UNIT_HOURS, UNIT_PERCENT, UNIT_AREA, UNIT_TIMES, UNIT_DAYS
from .dreame import (
    DreameVacuumProperty,
    DreameVacuumRelocationStatus,
)

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription


@dataclass
class DreameVacuumSensorEntityDescription(DreameVacuumEntityDescription, SensorEntityDescription):
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
        exists_fn=lambda description, device: device.status.lidar_navigation,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANED_AREA,
        icon="mdi:ruler-square",
        native_unit_of_measurement=UNIT_AREA,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.STATE,
        device_class=f"{DOMAIN}__state",
        icon="mdi:robot-vacuum",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.STATUS,
        device_class=f"{DOMAIN}__status",
        icon="mdi:vacuum",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.RELOCATION_STATUS,
        device_class=f"{DOMAIN}__relocation_status",
        icon_fn=lambda value, device: (
            "mdi:map-marker-distance"
            if device.status.relocation_status is DreameVacuumRelocationStatus.LOCATING
            else (
                "mdi:map-marker-alert"
                if device.status.relocation_status is DreameVacuumRelocationStatus.FAILED
                else (
                    "mdi:map-marker-check"
                    if device.status.relocation_status is DreameVacuumRelocationStatus.SUCCESS
                    else "mdi:map-marker-radius"
                )
            )
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TASK_STATUS,
        device_class=f"{DOMAIN}__task_status",
        icon="mdi:file-tree",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WATER_TANK,
        device_class=f"{DOMAIN}__water_tank_and_mop",
        icon_fn=lambda value, device: (
            "mdi:water-pump-off" if not device.status.water_tank_or_mop_installed else "mdi:water-pump"
        ),
        exists_fn=lambda description, device: not device.status.self_wash_base_available
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSensorEntityDescription(
        key="mop_pad",
        device_class=f"{DOMAIN}__water_tank_and_mop",
        icon="mdi:google-circles-communities",
        value_fn=lambda value, device: device.status.water_tank_name,
        exists_fn=lambda description, device: device.status.self_wash_base_available,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DUST_COLLECTION,
        device_class=f"{DOMAIN}__dust_collection",
        icon_fn=lambda value, device: "mdi:delete-off" if not device.status.dust_collection else "mdi:delete-sweep",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.AUTO_EMPTY_STATUS,
        device_class=f"{DOMAIN}__auto_empty_status",
        icon_fn=lambda value, device: (
            "mdi:delete-clock"
            if device.status.auto_emptying_not_performed
            else "mdi:delete-restore" if device.status.auto_emptying else "mdi:delete"
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.SELF_WASH_BASE_STATUS,
        device_class=f"{DOMAIN}__self_wash_base_status",
        icon="mdi:dishwasher",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ERROR,
        device_class=f"{DOMAIN}__error",
        icon_fn=lambda value, device: (
            "mdi:alert-circle-outline"
            if device.status.has_error
            else "mdi:alert-outline" if device.status.has_warning else "mdi:check-circle-outline"
        ),
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CHARGING_STATUS,
        device_class=f"{DOMAIN}__charging_status",
        icon="mdi:home-lightning-bolt",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.BATTERY_LEVEL,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=UNIT_PERCENT,
        icon_fn=lambda value, device: icon_for_battery_level(device.status.battery_level, device.status.charging),
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
        # device_class=SensorDeviceClass.DURATION,
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
        # device_class=SensorDeviceClass.DURATION,
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
        # device_class=SensorDeviceClass.DURATION,
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
        # device_class=SensorDeviceClass.DURATION,
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
        # device_class=SensorDeviceClass.DURATION,
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
        # device_class=SensorDeviceClass.DURATION,
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
        # device_class=SensorDeviceClass.DURATION,
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
        # device_class=SensorDeviceClass.DURATION,
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
        name="Current Room",
        key="current_room",
        icon="mdi:home-map-marker",
        value_fn=lambda value, device: device.status.current_room.name,
        exists_fn=lambda description, device: device.status.map_available and device.status.lidar_navigation,
        available_fn=lambda device: bool(device.status.current_room is not None and not device.status.fast_mapping),
        attrs_fn=lambda device: {
            "room_id": device.status.current_room.segment_id,
            "room_icon": device.status.current_room.icon,
        },
    ),
    DreameVacuumSensorEntityDescription(
        name="Cleaning History",
        key="cleaning_history",
        icon="mdi:clipboard-text-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda value, device: device.status.last_cleaning_time,
        exists_fn=lambda description, device: device.status.map_available,
        available_fn=lambda device: bool(device.status.last_cleaning_time is not None),
        attrs_fn=lambda device: device.status.cleaning_history,
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
        super().__init__(coordinator, description)

        if description.property_key is not None and description.value_fn is None:
            prop = f"{description.property_key.name.lower()}_name"
            if hasattr(coordinator.device.status, prop):
                description.value_fn = lambda value, device: getattr(device.status, prop)
