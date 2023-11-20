from __future__ import annotations

import voluptuous as vol
from typing import Final

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature
)

from .dreame import DreameVacuumState, DreameVacuumSuctionLevel, DreameVacuumAction, InvalidActionException, SUCTION_LEVEL_QUIET
from .const import (
    DOMAIN,
    FAN_SPEED_SILENT,
    FAN_SPEED_STANDARD,
    FAN_SPEED_STRONG,
    FAN_SPEED_TURBO,
    INPUT_CLEANING_SEQUENCE,
    INPUT_DND_ENABLED,
    INPUT_DND_END,
    INPUT_DND_START,
    INPUT_SUCTION_LEVEL,
    INPUT_LANGUAGE_ID,
    INPUT_LINE,
    INPUT_MAP_ID,
    INPUT_MAP_NAME,
    INPUT_MAP_URL,
    INPUT_MD5,
    INPUT_MOP_ARRAY,
    INPUT_REPEATS,
    INPUT_ROTATION,
    INPUT_SEGMENT,
    INPUT_SEGMENT_ID,
    INPUT_SEGMENT_NAME,
    INPUT_SEGMENTS_ARRAY,
    INPUT_SIZE,
    INPUT_URL,
    INPUT_VELOCITY,
    INPUT_WALL_ARRAY,
    INPUT_WATER_VOLUME,
    INPUT_ZONE,
    INPUT_ZONE_ARRAY,
    INPUT_CONSUMABLE,
    INPUT_POINTS,
    SERVICE_CLEAN_ZONE,
    SERVICE_CLEAN_SEGMENT,
    SERVICE_CLEAN_SPOT,
    SERVICE_INSTALL_VOICE_PACK,
    SERVICE_MERGE_SEGMENTS,
    SERVICE_MOVE_REMOTE_CONTROL_STEP,
    SERVICE_RENAME_MAP,
    SERVICE_RENAME_SEGMENT,
    SERVICE_REQUEST_MAP,
    SERVICE_SELECT_MAP,
    SERVICE_DELETE_MAP,
    SERVICE_SET_CLEANING_SEQUENCE,
    SERVICE_SET_CUSTOM_CLEANING,
    SERVICE_SET_DND,
    SERVICE_SET_RESTRICTED_ZONE,
    SERVICE_SPLIT_SEGMENTS,
    SERVICE_SAVE_TEMPORARY_MAP,
    SERVICE_DISCARD_TEMPORARY_MAP,
    SERVICE_REPLACE_TEMPORARY_MAP,
    SERVICE_RESET_CONSUMABLE,
    CONSUMABLE_MAIN_BRUSH,
    CONSUMABLE_SIDE_BRUSH,
    CONSUMABLE_FILTER,
    CONSUMABLE_SECONDARY_FILTER,
    CONSUMABLE_SENSOR,
    CONSUMABLE_MOP_PAD,
    CONSUMABLE_SILVER_ION,
    CONSUMABLE_DETERGENT,
)

SUPPORT_DREAME = (
    VacuumEntityFeature.START
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.FAN_SPEED
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.MAP
)


STATE_CODE_TO_STATE: Final = {
    DreameVacuumState.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumState.SWEEPING: STATE_CLEANING,
    DreameVacuumState.IDLE: STATE_IDLE,
    DreameVacuumState.PAUSED: STATE_PAUSED,
    DreameVacuumState.ERROR: STATE_ERROR,
    DreameVacuumState.RETURNING: STATE_RETURNING,
    DreameVacuumState.CHARGING: STATE_DOCKED,
    DreameVacuumState.MOPPING: STATE_CLEANING,
    DreameVacuumState.DRYING: STATE_DOCKED,
    DreameVacuumState.WASHING: STATE_CLEANING,
    DreameVacuumState.RETURNING_WASHING: STATE_RETURNING,
    DreameVacuumState.BUILDING: STATE_DOCKED,
    DreameVacuumState.SWEEPING_AND_MOPPING: STATE_CLEANING,
    DreameVacuumState.CHARGING_COMPLETED: STATE_DOCKED,
    DreameVacuumState.UPGRADING: STATE_IDLE,
}

SUCTION_LEVEL_TO_FAN_SPEED: Final = {
    DreameVacuumSuctionLevel.QUIET: FAN_SPEED_SILENT,
    DreameVacuumSuctionLevel.STANDARD: FAN_SPEED_STANDARD,
    DreameVacuumSuctionLevel.STRONG: FAN_SPEED_STRONG,
    DreameVacuumSuctionLevel.TURBO: FAN_SPEED_TURBO,
}

CONSUMABLE_RESET_ACTION = {
    CONSUMABLE_MAIN_BRUSH: DreameVacuumAction.RESET_MAIN_BRUSH,
    CONSUMABLE_SIDE_BRUSH: DreameVacuumAction.RESET_SIDE_BRUSH,
    CONSUMABLE_FILTER: DreameVacuumAction.RESET_FILTER,
    CONSUMABLE_SECONDARY_FILTER: DreameVacuumAction.RESET_SECONDARY_FILTER,
    CONSUMABLE_SENSOR: DreameVacuumAction.RESET_SENSOR,
    CONSUMABLE_MOP_PAD: DreameVacuumAction.RESET_MOP_PAD,
    CONSUMABLE_SILVER_ION: DreameVacuumAction.RESET_SILVER_ION,
    CONSUMABLE_DETERGENT: DreameVacuumAction.RESET_DETERGENT,
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Dreame Vacuum based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_REQUEST_MAP,
        {},
        DreameVacuum.async_request_map.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SELECT_MAP,
        {
            vol.Required(INPUT_MAP_ID): cv.positive_int,
        },
        DreameVacuum.async_select_map.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_DELETE_MAP,
        {
            vol.Optional(INPUT_MAP_ID): cv.positive_int,
        },
        DreameVacuum.async_delete_map.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SAVE_TEMPORARY_MAP,
        {},
        DreameVacuum.async_save_temporary_map.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_DISCARD_TEMPORARY_MAP,
        {},
        DreameVacuum.async_discard_temporary_map.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_REPLACE_TEMPORARY_MAP,
        {
            vol.Optional(INPUT_MAP_ID): cv.positive_int,
        },
        DreameVacuum.async_replace_temporary_map.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_CLEAN_ZONE,
        {
            vol.Required(INPUT_ZONE): vol.Any(
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
                vol.ExactSequence(
                    [
                        vol.Coerce(int),
                        vol.Coerce(int),
                        vol.Coerce(int),
                        vol.Coerce(int),
                    ]
                )
            ),
            vol.Optional(INPUT_REPEATS): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
        },
        DreameVacuum.async_clean_zone.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_CLEAN_SEGMENT,
        {
            vol.Required(INPUT_SEGMENTS_ARRAY): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
            vol.Optional(INPUT_REPEATS): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
            vol.Optional(INPUT_SUCTION_LEVEL): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
            vol.Optional(INPUT_WATER_VOLUME): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
        },
        DreameVacuum.async_clean_segment.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_CLEAN_SPOT,
        {
            vol.Required(INPUT_POINTS): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
            vol.Optional(INPUT_REPEATS): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
            vol.Optional(INPUT_SUCTION_LEVEL): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
            vol.Optional(INPUT_WATER_VOLUME): vol.Any(
                vol.Coerce(int), [vol.Coerce(int)]
            ),
        },
        DreameVacuum.async_clean_spot.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_RESTRICTED_ZONE,
        {
            vol.Optional(INPUT_WALL_ARRAY): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
            vol.Optional(INPUT_ZONE_ARRAY): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
            vol.Optional(INPUT_MOP_ARRAY): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
        },
        DreameVacuum.async_set_restricted_zone.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_MOVE_REMOTE_CONTROL_STEP,
        {
            vol.Required(INPUT_VELOCITY): vol.All(
                vol.Coerce(int), vol.Clamp(min=-600, max=600)
            ),
            vol.Required(INPUT_ROTATION): vol.All(
                vol.Coerce(int), vol.Clamp(min=-360, max=360)
            ),
        },
        DreameVacuum.async_remote_control_move_step.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_INSTALL_VOICE_PACK,
        {
            vol.Required(INPUT_LANGUAGE_ID): cv.string,
            vol.Required(INPUT_URL): cv.string,
            vol.Required(INPUT_MD5): cv.string,
            vol.Required(INPUT_SIZE): cv.positive_int,
        },
        DreameVacuum.async_install_voice_pack.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_RENAME_MAP,
        {
            vol.Required(INPUT_MAP_ID): cv.positive_int,
            vol.Required(INPUT_MAP_NAME): cv.string,
        },
        DreameVacuum.async_rename_map.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_MERGE_SEGMENTS,
        {
            vol.Optional(INPUT_MAP_ID): cv.positive_int,
            vol.Required(INPUT_SEGMENTS_ARRAY): vol.All(
                [vol.Coerce(int)]
            ),
        },
        DreameVacuum.async_merge_segments.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SPLIT_SEGMENTS,
        {
            vol.Optional(INPUT_MAP_ID): cv.positive_int,
            vol.Required(INPUT_SEGMENT): vol.All(vol.Coerce(int)),
            vol.Required(INPUT_LINE): vol.All(
                list,
                vol.ExactSequence(
                    [
                        vol.Coerce(int),
                        vol.Coerce(int),
                        vol.Coerce(int),
                        vol.Coerce(int),
                    ]
                ),
            ),
        },
        DreameVacuum.async_split_segments.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_RENAME_SEGMENT,
        {
            vol.Required(INPUT_SEGMENT_ID): cv.positive_int,
            vol.Required(INPUT_SEGMENT_NAME): cv.string,
        },
        DreameVacuum.async_rename_segment.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_CLEANING_SEQUENCE,
        {
            vol.Required(INPUT_CLEANING_SEQUENCE): cv.ensure_list,
        },
        DreameVacuum.async_set_cleaning_sequence.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_CUSTOM_CLEANING,
        {
            vol.Required(INPUT_SEGMENT_ID): cv.ensure_list,
            vol.Required(INPUT_SUCTION_LEVEL): cv.ensure_list,
            vol.Required(INPUT_WATER_VOLUME): cv.ensure_list,
            vol.Required(INPUT_REPEATS): cv.ensure_list,
        },
        DreameVacuum.async_set_custom_cleaning.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_DND,
        {
            vol.Required(INPUT_DND_ENABLED): cv.boolean,
            vol.Optional(INPUT_DND_START): cv.string,
            vol.Optional(INPUT_DND_END): cv.string,
        },
        DreameVacuum.async_set_dnd.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_RESET_CONSUMABLE,
        {
            vol.Required(INPUT_CONSUMABLE): vol.In(
                [
                    CONSUMABLE_MAIN_BRUSH,
                    CONSUMABLE_SIDE_BRUSH,
                    CONSUMABLE_FILTER,
                    CONSUMABLE_SECONDARY_FILTER,
                    CONSUMABLE_SENSOR,
                    CONSUMABLE_MOP_PAD,
                    CONSUMABLE_SILVER_ION,
                    CONSUMABLE_DETERGENT,
                ]
            ),
        },
        DreameVacuum.async_reset_consumable.__name__,
    )

    async_add_entities([DreameVacuum(coordinator)])


class DreameVacuum(DreameVacuumEntity, StateVacuumEntity):
    """Representation of a Dreame Vacuum cleaner robot."""

    def __init__(self, coordinator: DreameVacuumDataUpdateCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)

        self._attr_supported_features = SUPPORT_DREAME
        self._attr_device_class = DOMAIN
        self._attr_name = coordinator.device.name
        self._attr_unique_id = f"{coordinator.device.mac}_" + DOMAIN
        self._set_attrs()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._set_attrs()
        self.async_write_ha_state()

    def _set_attrs(self):
        if self.device.status.has_error:
            self._attr_icon = "mdi:alert-octagon"
        elif self.device.status.has_warning:
            self._attr_icon = "mdi:robot-vacuum-alert"
        elif self.device.status.returning_to_wash:
            self._attr_icon = "mdi:water-circle"
        elif self.device.status.washing:
            self._attr_icon = "mdi:water-sync"
        elif self.device.status.paused or self.device.status.washing_paused or self.device.status.returning_to_wash_paused:
            self._attr_icon = "mdi:pause-circle"
        elif self.device.status.drying:
            self._attr_icon = "mdi:hair-dryer"
        elif self.device.status.sleeping:
            self._attr_icon = "mdi:sleep"
        elif self.device.status.charging:
            self._attr_icon = "mdi:lightning-bolt-circle"
        elif self.device.status.docked:
            self._attr_icon = "mdi:ev-station"
        elif self.device.status.paused:
            self._attr_icon = "mdi:pause-circle"
        else:
            self._attr_icon = "mdi:robot-vacuum"

        if self.device.status.started and (self.device.status.customized_cleaning and not (self.device.status.zone_cleaning or self.device.status.spot_cleaning)):
            self._attr_fan_speed_list = []
            self._attr_fan_speed = STATE_UNAVAILABLE.capitalize()
        else:
            self._attr_fan_speed_list = list(SUCTION_LEVEL_TO_FAN_SPEED.values())
            self._attr_fan_speed = SUCTION_LEVEL_TO_FAN_SPEED.get(self.device.status.suction_level, STATE_UNKNOWN)
            
        self._attr_battery_level = self.device.status.battery_level
        self._attr_extra_state_attributes = self.device.status.attributes
        self._attr_state = STATE_CODE_TO_STATE.get(self.device.status.state, STATE_UNKNOWN)
        self._attr_status = self.device.status.status_name.replace("_", " ").capitalize()
        
    @property
    def state(self) -> str | None:
        """Return the state of the vacuum cleaner."""
        return self._attr_state

    @property
    def status(self) -> str | None:
        """Return the status of the vacuum cleaner."""
        return self._attr_status

    @property
    def supported_features(self) -> int:
        """Flag vacuum cleaner features that are supported."""
        return self._attr_supported_features
    
    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes of the entity."""
        return self._attr_extra_state_attributes

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available and self.device.device_connected

    async def async_locate(self, **kwargs) -> None:
        """Locate the vacuum cleaner."""
        await self._try_command("Unable to call locate: %s", self.device.locate)

    async def async_start(self) -> None:
        """Start or resume the cleaning task."""
        await self._try_command("Unable to call start: %s", self.device.start)

    async def async_start_pause(self) -> None:
        """Start or resume the cleaning task."""
        await self._try_command(
            "Unable to call start_pause: %s", self.device.start_pause
        )

    async def async_stop(self, **kwargs) -> None:
        """Stop the vacuum cleaner."""
        await self._try_command("Unable to call stop: %s", self.device.stop)

    async def async_pause(self) -> None:
        """Pause the cleaning task."""
        await self._try_command("Unable to call pause: %s", self.device.pause)

    async def async_return_to_base(self, **kwargs) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self._try_command(
            "Unable to call return_to_base: %s", self.device.return_to_base
        )

    async def async_clean_zone(self, zone, repeats=1) -> None:
        await self._try_command(
            "Unable to call clean_zone: %s", self.device.clean_zone, zone, repeats
        )

    async def async_clean_segment(
        self, segments, repeats=1, suction_level="", water_volume=""
    ) -> None:
        """Clean selected segments."""
        await self._try_command(
            "Unable to call clean_segment: %s",
            self.device.clean_segment,
            segments,
            repeats,
            suction_level,
            water_volume,
        )

    async def async_clean_spot(
        self, points, repeats=1, suction_level="", water_volume=""
    ) -> None:
        await self._try_command(
            "Unable to call clean_spot: %s", self.device.clean_spot, points, repeats, suction_level, water_volume)

    async def async_set_restricted_zone(self, walls="", zones="", no_mops="") -> None:
        """Create restricted zone."""
        await self._try_command(
            "Unable to call set_restricted_zone: %s",
            self.device.set_restricted_zone,
            walls,
            zones,
            no_mops,
        )

    async def async_remote_control_move_step(
        self, rotation: int = 0, velocity: int = 0
    ) -> None:
        """Remote control the robot."""
        await self._try_command(
            "Unable to call remote_control_move_step: %s",
            self.device.remote_control_move_step,
            rotation,
            velocity,
        )

    async def async_set_fan_speed(self, fan_speed, **kwargs) -> None:
        """Set fan speed."""
        if self.device.status.started and (self.device.status.customized_cleaning and not (self.device.status.zone_cleaning or self.device.status.spot_cleaning)):
            raise InvalidActionException(
                "Cannot set fan speed when customized cleaning is enabled"
            )

        if isinstance(fan_speed, str) and fan_speed.isnumeric():
            fan_speed = int(fan_speed)

        if isinstance(fan_speed, int):
            if fan_speed not in DreameVacuumSuctionLevel._value2member_map_:
                raise HomeAssistantError("Invalid fan speed")
        else:
            fan_speed = fan_speed.lower()
            fan_speed_list = ({v.lower(): k for k, v in SUCTION_LEVEL_TO_FAN_SPEED.items()})
            if fan_speed in fan_speed_list:
                fan_speed = fan_speed_list[fan_speed]
            else:
                raise HomeAssistantError(
                    "Fan speed not recognized. Valid options: %s",
                    self.fan_speed_list,
                ) from None

        await self._try_command(
            "Unable to set fan speed: %s", self.device.set_suction_level, fan_speed
        )

    async def async_select_map(self, map_id) -> None:
        """Switch selected map."""
        await self._try_command(
            "Unable to switch to selected map: %s", self.device.select_map, map_id
        )

    async def async_delete_map(self, map_id=None) -> None:
        """Delete a map."""
        await self._try_command(
            "Unable to delete map: %s", self.device.delete_map, map_id
        )

    async def async_save_temporary_map(self) -> None:
        """Save the temporary map."""
        await self._try_command(
            "Unable to save map: %s", self.device.save_temporary_map
        )

    async def async_discard_temporary_map(self) -> None:
        """Discard the temporary map."""
        await self._try_command(
            "Unable to discard temporary map: %s", self.device.discard_temporary_map
        )

    async def async_replace_temporary_map(self, map_id=None) -> None:
        """Replace the temporary map with another saved map."""
        await self._try_command(
            "Unable to replace temporary map: %s",
            self.device.replace_temporary_map,
            map_id,
        )

    async def async_request_map(self) -> None:
        """Request new map."""
        await self._try_command(
            "Unable to call request_map: %s", self.device.request_map
        )

    async def async_rename_map(self, map_id, map_name="") -> None:
        """Rename a map"""
        if map_name != "":
            await self._try_command(
                "Unable to call rename_map: %s",
                self.device.rename_map,
                map_id,
                map_name,
            )

    async def async_rename_segment(self, segment_id, segment_name="") -> None:
        """Rename a segment"""
        if segment_name != "":
            await self._try_command(
                "Unable to call set_segment_name: %s",
                self.device.set_segment_name,
                segment_id,
                0,
                segment_name,
            )

    async def async_merge_segments(self, map_id=None, segments=None) -> None:
        """Merge segments"""
        if segments is not None:
            await self._try_command(
                "Unable to call merge_segments: %s",
                self.device.merge_segments,
                map_id,
                segments,
            )

    async def async_split_segments(self, map_id=None, segment=None, line=None) -> None:
        """Split segments"""
        if segment is not None and line is not None:
            await self._try_command(
                "Unable to call split_segments: %s",
                self.device.split_segments,
                map_id,
                segment,
                line,
            )

    async def async_set_cleaning_sequence(self, cleaning_sequence) -> None:
        """Set cleaning sequence"""
        if cleaning_sequence != "" and cleaning_sequence is not None:
            await self._try_command(
                "Unable to call cleaning_sequence: %s",
                self.device.set_cleaning_sequence,
                cleaning_sequence,
            )

    async def async_set_custom_cleaning(self, segment_id, suction_level, water_volume, repeats) -> None:
        """Set custom cleaning"""
        if (
            segment_id != ""
            and segment_id is not None
            and suction_level != ""
            and suction_level is not None
            and water_volume != ""
            and water_volume is not None
            and repeats != ""
            and repeats is not None
        ):
            await self._try_command(
                "Unable to call set_custom_cleaning: %s",
                self.device.set_custom_cleaning,
                segment_id,
                suction_level,
                water_volume,
                repeats,
            )

    async def async_install_voice_pack(self, lang_id, url, md5, size, **kwargs) -> None:
        """install a custom language pack"""
        await self._try_command(
            "Unable to call install_voice_pack: %s",
            self.device.install_voice_pack,
            lang_id,
            url,
            md5,
            size,
        )

    async def async_send_command(self, command: str, params, **kwargs) -> None:
        """Send a command to a vacuum cleaner."""
        await self._try_command(
            "Unable to call send_command: %s", self.device.send_command, command, params
        )

    async def async_set_dnd(self, dnd_enabled, dnd_start="", dnd_end="") -> None:
        """Set do not disturb function"""
        await self._try_command(
            "Unable to call set_dnd_enabled: %s",
            self.device.set_dnd_enabled,
            dnd_enabled,
        )
        if dnd_start != "" and dnd_start is not None:
            await self._try_command(
                "Unable to call set_dnd_start: %s", self.device.set_dnd_start, dnd_start
            )
        if dnd_end != "" and dnd_end is not None:
            await self._try_command(
                "Unable to call set_dnd_end: %s", self.device.set_dnd_end, dnd_end
            )

    async def async_reset_consumable(self, consumable: str) -> None:
        """Reset consumable"""
        action = CONSUMABLE_RESET_ACTION.get(consumable)
        if action:
            await self._try_command(
                "Unable to call reset_consumable: %s",
                self.device.call_action,
                action,
            )
