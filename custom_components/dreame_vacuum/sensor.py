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

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UNIT_MINUTES, UNIT_HOURS, UNIT_PERCENT, UNIT_AREA, UNIT_TIMES
from .dreame import (
    DreameVacuumProperty,
    DreameVacuumRelocationStatus,
)

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription


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
        icon_fn=lambda value, device: "mdi:map-marker-distance"
        if device.status.relocation_status is DreameVacuumRelocationStatus.LOCATING
        else "mdi:map-marker-alert"
        if device.status.relocation_status is DreameVacuumRelocationStatus.FAILED
        else "mdi:map-marker-check"
        if device.status.relocation_status is DreameVacuumRelocationStatus.SUCCESS
        else "mdi:map-marker-radius",
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TASK_STATUS,
        device_class=f"{DOMAIN}__task_status",
        icon="mdi:file-tree",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WATER_TANK,
        device_class=f"{DOMAIN}__water_tank",
        icon_fn=lambda value, device: "mdi:water-pump-off"
        if not device.status.water_tank_installed
        else "mdi:water-pump",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.DUST_COLLECTION,
        device_class=f"{DOMAIN}__dust_collection",
        icon_fn=lambda value, device: "mdi:delete-off"
        if not device.status.dust_collection
        else "mdi:delete-sweep",
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.AUTO_EMPTY_STATUS,
        device_class=f"{DOMAIN}__auto_empty_status",
        icon_fn=lambda value, device: "mdi:delete-clock"
        if device.status.auto_emptying_not_performed
        else "mdi:delete-restore"
        if device.status.auto_emptying
        else "mdi:delete",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.WASH_STATION_STATUS,
        device_class=f"{DOMAIN}__wash_station_status",
        icon="mdi:dishwasher",
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.ERROR,
        device_class=f"{DOMAIN}__error",
        icon_fn=lambda value, device: "mdi:alert-circle-outline"
        if device.status.has_error
        else "mdi:alert-outline"
        if device.status.has_warning
        else "mdi:check-circle-outline",
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
        device_class=SensorDeviceClass.DURATION,
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
        device_class=SensorDeviceClass.DURATION,
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
        device_class=SensorDeviceClass.DURATION,
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
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MOP_LEFT,
        icon="mdi:hydro-power",
        native_unit_of_measurement=UNIT_PERCENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.MOP_TIME_LEFT,
        icon="mdi:hydro-power",
        native_unit_of_measurement=UNIT_HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.FIRST_CLEANING_DATE,
        icon="mdi:calendar-start",
        device_class=SensorDeviceClass.DATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value, device: datetime.fromtimestamp(value),
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TOTAL_CLEANING_TIME,
        icon="mdi:timer-outline",
        native_unit_of_measurement=UNIT_MINUTES,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.CLEANING_COUNT,
        icon="mdi:counter",
        native_unit_of_measurement=UNIT_TIMES,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        property_key=DreameVacuumProperty.TOTAL_CLEANED_AREA,
        icon="mdi:set-square",
        native_unit_of_measurement=UNIT_AREA,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    DreameVacuumSensorEntityDescription(
        name="Current Room",
        key="current_room",
        icon="mdi:home-map-marker",
        value_fn=lambda value, device: device.status.current_room.name,
        exists_fn=lambda description, device: device.status.map_available,
        available_fn=lambda device: bool(
            device.status.current_room is not None and not device.status.fast_mapping
        ),
        attrs_fn=lambda device: {
            "room_id": device.status.current_room.id,
            "room_icon": device.status.current_room.icon,
        },
    ),
    DreameVacuumSensorEntityDescription(
        name="Cleaning History",
        key="cleaning_history",
        icon="mdi:clipboard-text-clock",
        value_fn=lambda value, device: list(
            device.status.cleaning_history.keys())[0]
        if device.status.cleaning_history and len(device.status.cleaning_history)
        else 0,
        exists_fn=lambda description, device: device.status.map_available,
        available_fn=lambda device: bool(
            device.status.cleaning_history and len(
                device.status.cleaning_history)
        ),
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
        if description.exists_fn(description, coordinator.data)
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
            prop = f'{description.property_key.name.lower()}_name'
            if hasattr(coordinator.device.status, prop):
                description.value_fn = lambda value, device: getattr(
                    device.status, prop)
