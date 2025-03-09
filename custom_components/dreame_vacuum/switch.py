"""Support for Dreame Vacuum switches."""

from __future__ import annotations

from typing import Any
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame import (
    DreameVacuumProperty,
    DreameVacuumAutoSwitchProperty,
    DreameVacuumStrAIProperty,
    DreameVacuumAIProperty,
)


@dataclass
class DreameVacuumSwitchEntityDescription(DreameVacuumEntityDescription, SwitchEntityDescription):
    """Describes Dreame Vacuum Switch entity."""

    set_fn: Callable[[object, int]] = None


SWITCHES: tuple[DreameVacuumSwitchEntityDescription, ...] = (
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.RESUME_CLEANING,
        value_fn=lambda value, device: bool(value),
        icon="mdi:play-pause",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CARPET_BOOST,
        icon_fn=lambda value, device: "mdi:upload-off" if value == 0 else "mdi:upload",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.OBSTACLE_AVOIDANCE,
        icon_fn=lambda value, device: "mdi:video-3d-off" if value == 0 else "mdi:video-3d",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CUSTOMIZED_CLEANING,
        icon="mdi:home-search",
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CHILD_LOCK,
        icon_fn=lambda value, device: "mdi:lock-off" if value == 0 else "mdi:lock",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.TIGHT_MOPPING,
        icon="mdi:heating-coil",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.status.mopping_type is None
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        key="dnd",
        name="DnD",
        icon_fn=lambda value, device: "mdi:minus-circle-off-outline" if not value else "mdi:minus-circle-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.DND_DISABLE_RESUME_CLEANING,
        icon="mdi:pause-box",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: bool(
            device.capability.dnd_functions and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.DND_DISABLE_AUTO_EMPTY,
        icon="mdi:delete-off",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: bool(
            device.capability.dnd_functions and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.DND_REDUCE_VOLUME,
        icon="mdi:volume-minus",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: bool(
            device.capability.dnd_functions and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.MULTI_FLOOR_MAP,
        icon_fn=lambda value, device: "mdi:layers-off" if value == 0 else "mdi:layers",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.lidar_navigation
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_DUST_COLLECTING,
        icon_fn=lambda value, device: "mdi:autorenew-off" if value == 0 else "mdi:autorenew",
        entity_category=None,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and not device.capability.auto_empty_mode
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CARPET_RECOGNITION,
        icon="mdi:rug",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and not device.capability.auto_carpet_cleaning
            and not device.capability.mop_pad_lifting_plus
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.SELF_CLEAN,
        icon_fn=lambda value, device: "mdi:water-off-outline" if value == 0 else "mdi:water-sync",
        entity_category=None,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.WATER_ELECTROLYSIS,
        icon_fn=lambda value, device: "mdi:lightning-bolt-outline" if value == 0 else "mdi:lightning-bolt",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device)
            and device.capability.self_wash_base
            and not device.capability.mop_clean_frequency
            and not device.capability.small_self_clean_area
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_WATER_REFILLING,
        icon_fn=lambda value, device: "mdi:water-boiler-off" if value == 0 else "mdi:water-boiler-auto",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.water_check
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.INTELLIGENT_RECOGNITION,
        icon_fn=lambda value, device: "mdi:wifi-remove" if value == 0 else "mdi:wifi-marker",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.wifi_map
        and DreameVacuumEntityDescription().exists_fn(description, device),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.AUTO_DRYING,
        icon_fn=lambda value, device: "mdi:weather-sunny-off" if not value else "mdi:weather-sunny",
        entity_category=None,
        exists_fn=lambda description, device: device.capability.self_wash_base,
    ),
    DreameVacuumSwitchEntityDescription(
        key="carpet_avoidance",
        icon="mdi:close-box-outline",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: not device.capability.mop_pad_unmounting
        and device.capability.carpet_recognition,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_ADD_DETERGENT,
        icon="mdi:chart-bubble",
        entity_category=EntityCategory.CONFIG,
        format_fn=lambda value, device: int(value),
        exists_fn=lambda description, device: bool(
            DreameVacuumEntityDescription().exists_fn(description, device) and device.capability.detergent
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.MAP_SAVING,
        icon="mdi:map-legend",
        entity_category=EntityCategory.CONFIG,
        format_fn=lambda value, device: int(value),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_MOUNT_MOP,
        icon="mdi:google-circles-group",
        entity_category=EntityCategory.CONFIG,
        format_fn=lambda value, device: int(value),
        exists_fn=lambda description, device: bool(
            device.capability.mop_pad_unmounting and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.VOICE_ASSISTANT,
        icon_fn=lambda value, device: "mdi:microphone-message-off" if not value else "mdi:microphone-message",
        entity_category=EntityCategory.CONFIG,
        format_fn=lambda value, device: int(value),
    ),
    DreameVacuumSwitchEntityDescription(
        key="cleaning_sequence",
        icon="mdi:order-numeric-ascending",
        value_fn=lambda value, device: device.status.custom_order,
        exists_fn=lambda description, device: device.capability.customized_cleaning and device.capability.map,
        set_fn=lambda device, value: device.set_cleaning_sequence(
            []
            if not value
            else (
                device.status.previous_cleaning_sequence
                if device.status.previous_cleaning_sequence
                else list(sorted(device.status.current_segments.keys()))
            )
        ),
        format_fn=lambda value, device: int(value),
        entity_category=None,
    ),
    DreameVacuumSwitchEntityDescription(
        key="self_clean_by_zone",
        icon_fn=lambda value, device: "mdi:texture-box" if not value else "mdi:home-switch",
        value_fn=lambda value, device: bool(not device.status.self_clean_value),
        exists_fn=lambda description, device: device.capability.self_wash_base
        and not device.capability.self_clean_frequency
        and device.status.self_clean_value is not None
        and not device.capability.mop_clean_frequency,
        set_fn=lambda device, value: device.set_self_clean_value(value),
        format_fn=lambda value, device: (
            0 if value else device.status.previous_self_clean_area if device.status.previous_self_clean_area else 20
        ),
        entity_category=None,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.AI_OBSTACLE_DETECTION,
        icon_fn=lambda value, device: "mdi:robot-off" if not value else "mdi:robot",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.AI_OBSTACLE_IMAGE_UPLOAD,
        icon="mdi:cloud-upload",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.AI_OBSTACLE_PICTURE,
        icon_fn=lambda value, device: "mdi:camera-off" if not value else "mdi:camera",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.AI_PET_DETECTION,
        icon_fn=lambda value, device: "mdi:dog-side-off" if not value else "mdi:dog-side",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumStrAIProperty.AI_HUMAN_DETECTION,
        icon_fn=lambda value, device: "mdi:account-off" if not value else "mdi:account",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.AI_FURNITURE_DETECTION,
        icon="mdi:table-furniture",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.AI_FLUID_DETECTION,
        icon_fn=lambda value, device: "mdi:water-off-outline" if not value else "mdi:water-outline",
        exists_fn=lambda description, device: device.capability.fluid_detection,
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.FUZZY_OBSTACLE_DETECTION,
        icon="mdi:blur-linear",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.AI_PET_AVOIDANCE,
        icon="mdi:dog-service",
        exists_fn=lambda description, device: device.capability.pet_detective,
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.PET_PICTURE,
        icon="mdi:cat",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.PET_FOCUSED_DETECTION,
        icon="mdi:dog",
        exists_fn=lambda description, device: device.capability.pet_furniture,
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAIProperty.LARGE_PARTICLES_BOOST,
        icon="mdi:weather-dust",
        exists_fn=lambda description, device: bool(device.capability.large_particles_boost),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.FILL_LIGHT,
        icon_fn=lambda value, device: "mdi:lightbulb-off" if not value else "mdi:lightbulb-on",
        exists_fn=lambda description, device: bool(
            device.capability.fill_light and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.COLLISION_AVOIDANCE,
        icon_fn=lambda value, device: "mdi:sign-direction-remove" if not value else "mdi:sign-direction",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.STAIN_AVOIDANCE,
        icon="mdi:liquid-spot",
        format_fn=lambda value, device: 2 if value else 1,
        exists_fn=lambda description, device: bool(
            device.capability.fluid_detection and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.FLOOR_DIRECTION_CLEANING,
        exists_fn=lambda description, device: bool(
            device.capability.floor_direction_cleaning
            and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        icon="mdi:arrow-decision-auto",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.PET_FOCUSED_CLEANING,
        exists_fn=lambda description, device: bool(
            device.capability.pet_detective and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        icon="mdi:paw",
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.INTENSIVE_CARPET_CLEANING,
        icon="mdi:creation",
        exists_fn=lambda description, device: bool(
            device.capability.intensive_carpet_cleaning
            and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.SIDE_REACH,
        icon="mdi:selection-ellipse-arrow-inside",
        exists_fn=lambda description, device: bool(
            device.capability.side_reach and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.MOP_EXTEND,
        icon="mdi:waves-arrow-right",
        exists_fn=lambda description, device: bool(
            device.capability.mop_extend and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.GAP_CLEANING_EXTENSION,
        icon="mdi:plus-circle-multiple",
        exists_fn=lambda description, device: bool(
            device.capability.mop_pad_swing_plus and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.MOPPING_UNDER_FURNITURES,
        icon="mdi:table-picnic",
        exists_fn=lambda description, device: bool(
            device.capability.mop_pad_swing_plus and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.OFF_PEAK_CHARGING,
        icon="mdi:battery-clock",
        entity_category=EntityCategory.CONFIG,
        exists_fn=lambda description, device: device.capability.off_peak_charging,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.AUTO_CHARGING,
        icon="mdi:battery-sync",
        exists_fn=lambda description, device: bool(
            device.capability.auto_charging and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.HUMAN_FOLLOW,
        icon_fn=lambda value, device: "mdi:account-off" if not value else "mdi:account-arrow-left",
        exists_fn=lambda description, device: bool(
            device.capability.mop_pad_swing
            and device.capability.camera_streaming
            and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.MAX_SUCTION_POWER,
        icon="mdi:speedometer",
        exists_fn=lambda description, device: bool(
            device.capability.max_suction_power and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=None,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.SMART_DRYING,
        icon="mdi:clock-fast",
        exists_fn=lambda description, device: bool(
            device.capability.smart_drying and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.HOT_WASHING,
        icon="mdi:sun-thermometer",
        exists_fn=lambda description, device: bool(
            device.capability.hot_washing and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=None,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.UV_STERILIZATION,
        icon="mdi:sun-wireless",
        exists_fn=lambda description, device: bool(
            device.capability.uv_sterilization and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=None,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE,
        icon="mdi:silverware-clean",
        exists_fn=lambda description, device: bool(
            device.capability.ultra_clean_mode and not device.capability.smart_mop_washing and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumAutoSwitchProperty.STREAMING_VOICE_PROMPT,
        icon_fn=lambda value, device: "mdi:account-tie-voice-off" if not value else "mdi:account-tie-voice",
        exists_fn=lambda description, device: bool(
            device.capability.camera_streaming and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.CLEAN_CARPETS_FIRST,
        icon="mdi:order-bool-descending-variant",
        exists_fn=lambda description, device: bool(
            device.capability.clean_carpets_first and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.SMART_MOP_WASHING,
        icon="mdi:hand-water",
        exists_fn=lambda description, device: bool(
            device.capability.smart_mop_washing and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.SILENT_DRYING,
        icon="mdi:volume-mute",
        exists_fn=lambda description, device: bool(
            device.capability.silent_drying and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.HAIR_COMPRESSION,
        icon="mdi:arrow-collapse-vertical",
        exists_fn=lambda description, device: bool(
            device.capability.hair_compression and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.SIDE_BRUSH_CARPET_ROTATE,
        icon="mdi:format-rotate-90",
        exists_fn=lambda description, device: bool(
            device.capability.side_brush_carpet_rotate and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        property_key=DreameVacuumProperty.AUTO_LDS_LIFTING,
        icon="mdi:elevator",
        exists_fn=lambda description, device: bool(
            device.capability.auto_lds_lifting and DreameVacuumEntityDescription().exists_fn(description, device)
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    DreameVacuumSwitchEntityDescription(
        key="camera_light_brightness_auto",
        icon_fn=lambda value, device: "mdi:brightness-percent" if not value else "mdi:brightness-auto",
        value_fn=lambda value, device: bool(device.status.camera_light_brightness == 101),
        exists_fn=lambda description, device: device.capability.camera_streaming
        and device.capability.fill_light,  # and DreameVacuumEntityDescription().exists_fn(description, device),
        format_fn=lambda value, device: 101 if value else 40,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum switch based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DreameVacuumSwitchEntity(coordinator, description)
        for description in SWITCHES
        if description.exists_fn(description, coordinator.device)
    )


class DreameVacuumSwitchEntity(DreameVacuumEntity, SwitchEntity):
    """Defines a Dreame Vacuum Switch entity."""

    entity_description: DreameVacuumSwitchEntityDescription

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumSwitchEntityDescription,
    ) -> None:
        """Initialize a Dreame Vacuum switch entity."""
        if description.set_fn is None and (description.property_key is not None or description.key is not None):
            if description.property_key is not None:
                prop = f"set_{description.property_key.name.lower()}"
            else:
                prop = f"set_{description.key.lower()}"
            if hasattr(coordinator.device, prop):
                description.set_fn = lambda device, value: getattr(device, prop)(value)

        super().__init__(coordinator, description)
        self._generate_entity_id(ENTITY_ID_FORMAT)
        self._attr_is_on = bool(self.native_value)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_is_on = bool(self.native_value)
        super()._handle_coordinator_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the Dreame Vacuum sync receive switch."""
        await self.async_set_state(0)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the Dreame Vacuum sync receive switch."""
        await self.async_set_state(1)

    async def async_set_state(self, state) -> None:
        """Turn on or off the Dreame Vacuum sync receive switch."""
        if not self.available:
            raise HomeAssistantError("Entity unavailable")

        value = int(state)
        if self.entity_description.format_fn is not None:
            value = self.entity_description.format_fn(state, self.device)

        if self.entity_description.set_fn is not None:
            await self._try_command("Unable to call: %s", self.entity_description.set_fn, self.device, value)
        elif self.entity_description.property_key is not None:
            await self._try_command(
                "Unable to call: %s",
                self.device.set_property,
                self.entity_description.property_key,
                value,
            )
