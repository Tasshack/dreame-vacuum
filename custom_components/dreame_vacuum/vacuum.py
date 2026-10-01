from __future__ import annotations

import time
import voluptuous as vol
from typing import Final

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity

from dataclasses import dataclass
from homeassistant.helpers.importlib import async_import_module
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
    ENTITY_ID_FORMAT,
)
from .recorder import VACUUM_UNRECORDED_ATTRIBUTES

from .dreame.const import (
    STATE_UNKNOWN,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    ATTR_SELECTED_MAP,
    ATTR_ROOMS,
    ATTR_MAPS,
    ATTR_ID,
    ATTR_NAME,
    ATTR_RECOVERY_MAP,
)
from .dreame import DreameVacuumState, DreameVacuumSuctionLevel, DreameVacuumAction, InvalidActionException
from .const import (
    DOMAIN,
    CONSUMABLE_MAIN_BRUSH,
    CONSUMABLE_SIDE_BRUSH,
    CONSUMABLE_FILTER,
    CONSUMABLE_TANK_FILTER,
    CONSUMABLE_SENSOR,
    CONSUMABLE_MOP_PAD,
    CONSUMABLE_SILVER_ION,
    CONSUMABLE_DETERGENT,
    CONSUMABLE_SQUEEGEE,
    CONSUMABLE_ONBOARD_DIRTY_WATER_TANK,
    CONSUMABLE_DIRTY_WATER_CHANNEL,
    CONSUMABLE_DEODORIZER,
    CONSUMABLE_WHEEL,
    CONSUMABLE_SCALE_INHIBITOR,
    CONSUMABLE_FLUFFING_ROLLER,
    CONSUMABLE_ROLLER_MOP_FILTER,
    CONSUMABLE_WATER_OUTLET_FILTER,
)

try:
    from homeassistant.components.vacuum import Segment
except ImportError:
    from dataclasses import dataclass

    @dataclass
    class Segment:
        id: str
        name: str
        group: str | None = None


CLEAN_AREA_ENTITY_FEATURE = getattr(VacuumEntityFeature, "CLEAN_AREA", 0)

STATE_CODE_TO_STATE: Final = {
    DreameVacuumState.UNKNOWN: STATE_IDLE,
    DreameVacuumState.SWEEPING: STATE_CLEANING,
    DreameVacuumState.IDLE: STATE_IDLE,
    DreameVacuumState.PAUSED: STATE_PAUSED,
    DreameVacuumState.ERROR: STATE_ERROR,
    DreameVacuumState.RETURNING: STATE_RETURNING,
    DreameVacuumState.CHARGING: STATE_DOCKED,
    DreameVacuumState.MOPPING: STATE_CLEANING,
    DreameVacuumState.DRYING: STATE_DOCKED,
    DreameVacuumState.WASHING: STATE_CLEANING,
    DreameVacuumState.RETURNING_TO_WASH: STATE_RETURNING,
    DreameVacuumState.BUILDING: STATE_DOCKED,
    DreameVacuumState.SWEEPING_AND_MOPPING: STATE_CLEANING,
    DreameVacuumState.CHARGING_COMPLETED: STATE_DOCKED,
    DreameVacuumState.UPGRADING: STATE_IDLE,
    DreameVacuumState.CLEAN_SUMMON: STATE_CLEANING,
    DreameVacuumState.STATION_RESET: STATE_IDLE,
    DreameVacuumState.RETURNING_INSTALL_MOP: STATE_RETURNING,
    DreameVacuumState.RETURNING_REMOVE_MOP: STATE_RETURNING,
    DreameVacuumState.WATER_CHECK: STATE_DOCKED,
    DreameVacuumState.CLEAN_ADD_WATER: STATE_CLEANING,
    DreameVacuumState.WASHING_PAUSED: STATE_PAUSED,
    DreameVacuumState.AUTO_EMPTYING: STATE_DOCKED,
    DreameVacuumState.REMOTE_CONTROL: STATE_CLEANING,
    DreameVacuumState.SMART_CHARGING: STATE_DOCKED,
    DreameVacuumState.SECOND_CLEANING: STATE_CLEANING,
    DreameVacuumState.HUMAN_FOLLOWING: STATE_CLEANING,
    DreameVacuumState.SPOT_CLEANING: STATE_CLEANING,
    DreameVacuumState.RETURNING_AUTO_EMPTY: STATE_RETURNING,
    DreameVacuumState.SHORTCUT: STATE_CLEANING,
    DreameVacuumState.WAITING_FOR_TASK: STATE_IDLE,
    DreameVacuumState.STATION_CLEANING: STATE_CLEANING,
    DreameVacuumState.RETURNING_TO_DRAIN: STATE_RETURNING,
    DreameVacuumState.DRAINING: STATE_CLEANING,
    DreameVacuumState.AUTO_WATER_DRAINING: STATE_CLEANING,
    DreameVacuumState.MONITORING: STATE_CLEANING,
    DreameVacuumState.MONITORING_PAUSED: STATE_PAUSED,
    DreameVacuumState.EMPTYING: STATE_DOCKED,
    DreameVacuumState.DUST_BAG_DRYING: STATE_DOCKED,
    DreameVacuumState.DUST_BAG_DRYING_PAUSED: STATE_PAUSED,
    DreameVacuumState.HEADING_TO_EXTRA_CLEANING: STATE_CLEANING,
    DreameVacuumState.EXTRA_CLEANING: STATE_CLEANING,
    DreameVacuumState.FINDING_PET_PAUSED: STATE_PAUSED,
    DreameVacuumState.FINDING_PET: STATE_CLEANING,
    DreameVacuumState.INITIAL_DEEP_CLEANING: STATE_CLEANING,
    DreameVacuumState.INITIAL_DEEP_CLEANING_PAUSED: STATE_PAUSED,
    DreameVacuumState.SANITIZING: STATE_DOCKED,
    DreameVacuumState.SANITIZING_WITH_DRY: STATE_DOCKED,
}



CONSUMABLE_RESET_ACTION = {
    CONSUMABLE_MAIN_BRUSH: DreameVacuumAction.RESET_MAIN_BRUSH,
    CONSUMABLE_SIDE_BRUSH: DreameVacuumAction.RESET_SIDE_BRUSH,
    CONSUMABLE_FILTER: DreameVacuumAction.RESET_FILTER,
    CONSUMABLE_TANK_FILTER: DreameVacuumAction.RESET_TANK_FILTER,
    CONSUMABLE_SENSOR: DreameVacuumAction.RESET_SENSOR,
    CONSUMABLE_MOP_PAD: DreameVacuumAction.RESET_MOP_PAD,
    CONSUMABLE_SILVER_ION: DreameVacuumAction.RESET_SILVER_ION,
    CONSUMABLE_DETERGENT: DreameVacuumAction.RESET_DETERGENT,
    CONSUMABLE_SQUEEGEE: DreameVacuumAction.RESET_SQUEEGEE,
    CONSUMABLE_ONBOARD_DIRTY_WATER_TANK: DreameVacuumAction.RESET_ONBOARD_DIRTY_WATER_TANK,
    CONSUMABLE_DIRTY_WATER_CHANNEL: DreameVacuumAction.RESET_DIRTY_WATER_CHANNEL,
    CONSUMABLE_DEODORIZER: DreameVacuumAction.RESET_DEODORIZER,
    CONSUMABLE_WHEEL: DreameVacuumAction.RESET_WHEEL,
    CONSUMABLE_SCALE_INHIBITOR: DreameVacuumAction.RESET_SCALE_INHIBITOR,
    CONSUMABLE_FLUFFING_ROLLER: DreameVacuumAction.RESET_FLUFFING_ROLLER,
    CONSUMABLE_ROLLER_MOP_FILTER: DreameVacuumAction.RESET_ROLLER_MOP_FILTER,
    CONSUMABLE_WATER_OUTLET_FILTER: DreameVacuumAction.RESET_WATER_OUTLET_FILTER,
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
        "vacuum_request_map",
        {},
        DreameVacuum.async_request_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_select_map",
        {
            vol.Required("map_id"): cv.positive_int,
        },
        DreameVacuum.async_select_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_delete_map",
        {
            vol.Optional("map_id"): cv.positive_int,
        },
        DreameVacuum.async_delete_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_save_temporary_map",
        {},
        DreameVacuum.async_save_temporary_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_discard_temporary_map",
        {},
        DreameVacuum.async_discard_temporary_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_replace_temporary_map",
        {
            vol.Optional("map_id"): cv.positive_int,
        },
        DreameVacuum.async_replace_temporary_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_clean_zone",
        {
            vol.Required("zone"): vol.Any(
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
                ),
            ),
            vol.Optional("repeats"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("suction_level"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("water_volume"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
        },
        DreameVacuum.async_clean_zone.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_clean_segment",
        {
            vol.Required("segments"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("repeats"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("suction_level"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("water_volume"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
        },
        DreameVacuum.async_clean_segment.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_clean_spot",
        {
            vol.Required("points"): vol.Any(
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
                vol.ExactSequence(
                    [
                        vol.Coerce(int),
                        vol.Coerce(int),
                    ]
                ),
            ),
            vol.Optional("repeats"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("suction_level"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("water_volume"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
        },
        DreameVacuum.async_clean_spot.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_goto",
        {
            vol.Required("x"): vol.All(vol.Coerce(int)),
            vol.Required("y"): vol.All(vol.Coerce(int)),
        },
        DreameVacuum.async_goto.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_follow_path",
        {
            vol.Optional("points"): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
        },
        DreameVacuum.async_follow_path.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_start_shortcut",
        {
            vol.Required("shortcut_id"): vol.All(vol.Coerce(int)),
        },
        DreameVacuum.async_start_shortcut.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_restricted_zone",
        {
            vol.Optional("walls"): vol.All(
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
            vol.Optional("zones"): vol.Any(
                vol.All(
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
                vol.All(
                    list,
                    [
                        vol.ExactSequence(
                            [
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                            ]
                        )
                    ],
                ),
            ),
            vol.Optional("no_mops"): vol.Any(
                vol.All(
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
                vol.All(
                    list,
                    [
                        vol.ExactSequence(
                            [
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                            ]
                        )
                    ],
                ),
            ),
        },
        DreameVacuum.async_set_restricted_zone.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_carpet_area",
        {
            vol.Optional("carpets"): vol.Any(
                vol.All(
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
                vol.All(
                    list,
                    [
                        vol.ExactSequence(
                            [
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Any(vol.Coerce(int), None),
                            ]
                        )
                    ],
                ),
                vol.All(
                    list,
                    [
                        vol.ExactSequence(
                            [
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Any(vol.Coerce(int), None),
                                vol.Any(vol.Coerce(int), None),
                            ]
                        )
                    ],
                ),
                vol.All(
                    list,
                    [
                        vol.ExactSequence(
                            [
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Any(vol.Coerce(int), None),
                                vol.Any(vol.Coerce(int), None),
                                vol.Any(vol.Coerce(int), None),
                            ]
                        )
                    ],
                ),
            ),
            vol.Optional("deleted_carpets"): vol.Any(
                vol.All(
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
                vol.All(
                    list,
                    [
                        vol.ExactSequence(
                            [
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                                vol.Coerce(int),
                            ]
                        )
                    ],
                ),
            ),
        },
        DreameVacuum.async_set_carpet_area.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_carpet_type",
        {
            vol.Required("id"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Required("object_type"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("carpet_type"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
        },
        DreameVacuum.async_set_carpet_type.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_virtual_threshold",
        {
            vol.Optional("virtual_thresholds"): vol.All(
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
        DreameVacuum.async_set_virtual_threshold.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_threshold",
        {
            vol.Optional("passable_thresholds"): vol.All(
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
            vol.Optional("impassable_thresholds"): vol.All(
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
            vol.Optional("ramps"): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
        },
        DreameVacuum.async_set_threshold.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_predefined_points",
        {
            vol.Optional("points"): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
        },
        DreameVacuum.async_set_predefined_points.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_remote_control_move_step",
        {
            vol.Required("velocity"): vol.All(vol.Coerce(int), vol.Clamp(min=-600, max=600)),
            vol.Required("rotation"): vol.All(vol.Coerce(int), vol.Clamp(min=-360, max=360)),
            vol.Optional("prompt"): cv.boolean,
        },
        DreameVacuum.async_remote_control_move_step.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_install_voice_pack",
        {
            vol.Required("lang_id"): cv.string,
            vol.Required("url"): cv.url,
            vol.Required("md5"): cv.string,
            vol.Required("size"): cv.positive_int,
        },
        DreameVacuum.async_install_voice_pack.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_rename_map",
        {
            vol.Required("map_id"): cv.positive_int,
            vol.Required("map_name"): cv.string,
        },
        DreameVacuum.async_rename_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_restore_map",
        {
            vol.Required("recovery_map_index"): cv.positive_int,
            vol.Optional("map_id"): cv.positive_int,
        },
        DreameVacuum.async_restore_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_restore_map_from_file",
        {
            vol.Required("file_url"): cv.url,
            vol.Optional("map_id"): cv.positive_int,
        },
        DreameVacuum.async_restore_map_from_file.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_backup_map",
        {
            vol.Optional("map_id"): cv.positive_int,
        },
        DreameVacuum.async_backup_map.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_merge_segments",
        {
            vol.Optional("map_id"): cv.positive_int,
            vol.Required("segments"): vol.All([vol.Coerce(int)]),
        },
        DreameVacuum.async_merge_segments.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_split_segments",
        {
            vol.Optional("map_id"): cv.positive_int,
            vol.Required("segment"): vol.All(vol.Coerce(int)),
            vol.Required("line"): vol.All(
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
        "vacuum_rename_segment",
        {
            vol.Required("segment_id"): cv.positive_int,
            vol.Required("segment_name"): cv.string,
        },
        DreameVacuum.async_rename_segment.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_cleaning_sequence",
        {
            vol.Required("cleaning_sequence"): cv.ensure_list,
        },
        DreameVacuum.async_set_cleaning_sequence.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_custom_cleaning",
        {
            vol.Required("segment_id"): cv.ensure_list,
            vol.Required("suction_level"): cv.ensure_list,
            vol.Required("water_volume"): cv.ensure_list,
            vol.Required("repeats"): cv.ensure_list,
            vol.Optional("cleaning_mode"): cv.ensure_list,
            vol.Optional("custom_mopping_route"): cv.ensure_list,
            vol.Optional("cleaning_route"): cv.ensure_list,
            vol.Optional("wetness_level"): cv.ensure_list,
            vol.Optional("mop_temperature"): cv.ensure_list,
            vol.Optional("mop_pressure"): cv.ensure_list,
        },
        DreameVacuum.async_set_custom_cleaning.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_custom_carpet_cleaning",
        {
            vol.Required("id"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Required("object_type"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("carpet_cleaning"): vol.Any(vol.Coerce(int), [vol.Coerce(int)]),
            vol.Optional("carpet_preferences"): vol.Any(
                [vol.Coerce(str)], [[vol.Coerce(str)]], [vol.Coerce(int)], [[vol.Coerce(int)]]
            ),
        },
        DreameVacuum.async_set_custom_carpet_cleaning.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_segment_type",
        {
            vol.Required("type"): vol.Any(dict[str, list[int]]),
            vol.Optional("map_id"): vol.Coerce(int),
        },
        DreameVacuum.async_set_segment_type.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_hidden_segments",
        {
            vol.Optional("segments"): vol.All(list, [vol.Coerce(int)]),
            vol.Optional("map_id"): vol.Coerce(int),
        },
        DreameVacuum.async_set_hidden_segments.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_floor_material",
        {
            vol.Required("material"): vol.Any(dict[str, list[int]]),
            vol.Optional("map_id"): vol.Coerce(int),
        },
        DreameVacuum.async_set_floor_material.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_low_lying_area",
        {
            vol.Optional("area"): vol.All(
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
        DreameVacuum.async_set_low_lying_area.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_furniture",
        {
            vol.Optional("furnitures"): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(float),
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
        },
        DreameVacuum.async_set_furniture.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_curtain",
        {
            vol.Optional("curtains"): vol.All(
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
        DreameVacuum.async_set_curtain.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_mop_type",
        {
            vol.Required("mop_type"): vol.Any(dict[str, str]),
            vol.Optional("map_id"): vol.Coerce(int),
        },
        DreameVacuum.async_set_mop_type.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_reset_consumable",
        {
            vol.Required("consumable"): vol.In(
                [
                    CONSUMABLE_MAIN_BRUSH,
                    CONSUMABLE_SIDE_BRUSH,
                    CONSUMABLE_FILTER,
                    CONSUMABLE_TANK_FILTER,
                    CONSUMABLE_SENSOR,
                    CONSUMABLE_MOP_PAD,
                    CONSUMABLE_SILVER_ION,
                    CONSUMABLE_DETERGENT,
                    CONSUMABLE_SQUEEGEE,
                    CONSUMABLE_ONBOARD_DIRTY_WATER_TANK,
                    CONSUMABLE_DIRTY_WATER_CHANNEL,
                    CONSUMABLE_DEODORIZER,
                    CONSUMABLE_WHEEL,
                    CONSUMABLE_SCALE_INHIBITOR,
                    CONSUMABLE_FLUFFING_ROLLER,
                    CONSUMABLE_ROLLER_MOP_FILTER,
                    CONSUMABLE_WATER_OUTLET_FILTER,
                ]
            ),
        },
        DreameVacuum.async_reset_consumable.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_rename_shortcut",
        {
            vol.Required("shortcut_id"): cv.positive_int,
            vol.Required("shortcut_name"): cv.string,
        },
        DreameVacuum.async_rename_shortcut.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_delete_shortcut",
        {vol.Required("shortcut_id"): cv.positive_int},
        DreameVacuum.async_delete_shortcut.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_obstacle_ignore",
        {
            vol.Required("x"): vol.All(vol.Coerce(float)),
            vol.Required("y"): vol.All(vol.Coerce(float)),
            vol.Required("obstacle_ignored"): vol.All(vol.Coerce(bool)),
        },
        DreameVacuum.async_set_obstacle_ignore.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_router_position",
        {
            vol.Required("x"): vol.All(vol.Coerce(int)),
            vol.Required("y"): vol.All(vol.Coerce(int)),
        },
        DreameVacuum.async_set_router_position.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_walls",
        {
            vol.Optional("walls"): vol.Any(dict[str, list[int]]),
            vol.Optional("doors"): vol.All(
                list,
                [
                    vol.ExactSequence(
                        [
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                            vol.Coerce(int),
                        ]
                    )
                ],
            ),
            vol.Optional("map_id"): vol.Coerce(int),
        },
        DreameVacuum.async_set_walls.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_set_property",
        {
            vol.Required("key"): cv.string,
            vol.Optional("value"): vol.Any(vol.Coerce(int), vol.Coerce(str), vol.Coerce(bool)),
            vol.Optional("params"): vol.Any([vol.Coerce(int)], [vol.Coerce(str)], [vol.Coerce(bool)]),
        },
        DreameVacuum.async_set_property.__name__,
    )

    platform.async_register_entity_service(
        "vacuum_call_action",
        {vol.Required("key"): cv.string, vol.Optional("value"): cv.string},
        DreameVacuum.async_call_action.__name__,
    )

    activity_class = None
    ## For backwards compatibility
    try:
        module = await async_import_module(hass, f"homeassistant.components.vacuum")
        activity_class = module.VacuumActivity
    except:
        pass

    async_add_entities([DreameVacuum(coordinator, activity_class)])


class DreameVacuum(DreameVacuumEntity, StateVacuumEntity):
    """Representation of a Dreame Vacuum cleaner robot."""

    _unrecorded_attributes = frozenset(VACUUM_UNRECORDED_ATTRIBUTES)

    def __init__(self, coordinator: DreameVacuumDataUpdateCoordinator, activity_class) -> None:
        """Initialize the vacuum entity."""
        super().__init__(coordinator)

        self._attr_device_class = DOMAIN
        self._attr_name = (
            f" {coordinator.device.name}"  ## Add whitespace to display entity on top at the device configuration page
        )
        self._attr_has_entity_name = False
        self._attr_translation_key = DOMAIN
        self._attr_unique_id = f"{coordinator.device.mac}_" + DOMAIN
        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, f"{self.device.name}", hass=self.coordinator.hass)
        self._attr_supported_features = (
            VacuumEntityFeature.SEND_COMMAND
            | VacuumEntityFeature.LOCATE
            | VacuumEntityFeature.STATE
            | VacuumEntityFeature.STATUS
            | VacuumEntityFeature.START
            | VacuumEntityFeature.PAUSE
            | VacuumEntityFeature.STOP
            | VacuumEntityFeature.RETURN_HOME
        )
        if coordinator.device._map_manager:
            self._attr_supported_features |= VacuumEntityFeature.MAP
            if CLEAN_AREA_ENTITY_FEATURE:
                self._attr_supported_features |= CLEAN_AREA_ENTITY_FEATURE
        self._activity_class = activity_class

        self._set_attrs()

    def _on_locale_changed(self) -> None:
        self._set_attrs()
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._set_attrs()
        if CLEAN_AREA_ENTITY_FEATURE:
            self._check_segments_changed()
        self.async_write_ha_state()

    @callback
    def _check_segments_changed(self) -> None:
        """Check if segments have changed and create repair issue."""
        last_seen = self.last_seen_segments
        if last_seen is None:
            return

        current_ids = {seg.id for seg in self._get_segments()}
        last_seen_ids = {seg.id for seg in last_seen}

        if current_ids != last_seen_ids:
            self.async_create_segments_issue()

    def _set_attrs(self):
        if self.device.status.has_error:
            self._attr_icon = "mdi:alert-octagon"
        elif self.device.status.has_warning or self.device.status.low_water or self.device.status.draining_complete:
            self._attr_icon = "mdi:robot-vacuum-alert"
        elif self.device.status.returning_to_wash:
            self._attr_icon = "mdi:water-circle"
        elif self.device.status.washing:
            self._attr_icon = "mdi:water-sync"
        elif (
            self.device.status.paused
            or self.device.status.washing_paused
            or self.device.status.returning_to_wash_paused
        ):
            self._attr_icon = "mdi:pause-circle"
        elif self.device.status.drying:
            self._attr_icon = "mdi:hair-dryer"
        elif self.device.status.sleeping:
            self._attr_icon = "mdi:sleep"
        elif self.device.status.charging:
            self._attr_icon = "mdi:lightning-bolt-circle"
        elif self.device.status.docked:
            self._attr_icon = "mdi:ev-station"
        elif self.device.status.cruising:
            self._attr_icon = "mdi:map-marker-path"
        else:
            self._attr_icon = "mdi:robot-vacuum"

        if (
            not (
                self.device.status
                and self.device.status.started
                and (
                    self.device.status.customized_cleaning
                    and not (self.device.status.zone_cleaning or self.device.status.spot_cleaning)
                )
            )
            and not self.device.status.scheduled_clean
        ):
            self._attr_supported_features = self._attr_supported_features | VacuumEntityFeature.FAN_SPEED
            self._attr_fan_speed = self.device.status.suction_level.name.lower().replace("quiet", "silent")
            self._attr_fan_speed_list = [level.name.lower().replace("quiet", "silent") for level in DreameVacuumSuctionLevel if level != DreameVacuumSuctionLevel.UNKNOWN]
        else:
            self._attr_fan_speed = None
            self._attr_fan_speed_list = []

        self._vacuum_state = STATE_CODE_TO_STATE.get(self.device.status.state, STATE_IDLE)
        if self._activity_class is None:
            self._attr_state = self._vacuum_state
        attributes = self.device.status.attributes

        if attributes.get(ATTR_SELECTED_MAP) is not None:
            attributes[ATTR_SELECTED_MAP] = self._localize_map_name(self.device.status.selected_map)

        if attributes.get(ATTR_ROOMS):
            rooms = {}
            for v in self.device.status.map_data_list.values():
                map_rooms = attributes[ATTR_ROOMS].get(v.map_name)
                if map_rooms is None:
                    continue
                rooms[self._localize_map_name(v)] = [
                    {**room, ATTR_NAME: self._localize_segment_name(v.segments.get(room[ATTR_ID]), room[ATTR_ID])}
                    for room in map_rooms
                ]
            attributes[ATTR_ROOMS] = rooms

        if attributes.get(ATTR_MAPS):
            map_data_by_id = {v.map_id: v for v in self.device.status.map_data_list.values()}
            for map_attributes in attributes[ATTR_MAPS]:
                v = map_data_by_id.get(map_attributes.get(ATTR_ID))
                if v is None:
                    continue
                map_attributes[ATTR_NAME] = self._localize_map_name(v)

        self._attr_extra_state_attributes = attributes

    @property
    def supported_features(self) -> int:
        """Flag vacuum cleaner features that are supported."""
        return self._attr_supported_features

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes of the entity."""
        return self._attr_extra_state_attributes

    @property
    def activity(self):
        if self._activity_class is not None:
            return self._activity_class(self._vacuum_state)
        return self._vacuum_state

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
        await self._try_command("Unable to call start_pause: %s", self.device.start_pause)

    async def async_stop(self, **kwargs) -> None:
        """Stop the vacuum cleaner."""
        await self._try_command("Unable to call stop: %s", self.device.stop)

    async def async_pause(self) -> None:
        """Pause the cleaning task."""
        await self._try_command("Unable to call pause: %s", self.device.pause)

    async def async_return_to_base(self, **kwargs) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self._try_command("Unable to call return_to_base: %s", self.device.return_to_base)

    async def async_clean_zone(self, zone, repeats=1, suction_level="", water_volume="") -> None:
        await self._try_command(
            "Unable to call clean_zone: %s",
            self.device.clean_zone,
            zone,
            repeats,
            suction_level,
            water_volume,
        )

    async def async_clean_segment(self, segments, repeats=1, suction_level="", water_volume="") -> None:
        """Clean selected segments."""
        await self._try_command(
            "Unable to call clean_segment: %s",
            self.device.clean_segment,
            segments,
            repeats,
            suction_level,
            water_volume,
        )

    async def async_clean_spot(self, points, repeats=1, suction_level="", water_volume="") -> None:
        """Clean 1.5 square meters area of selected points."""
        await self._try_command(
            "Unable to call clean_spot: %s",
            self.device.clean_spot,
            points,
            repeats,
            suction_level,
            water_volume,
        )

    def _get_segments(self) -> list[Segment]:
        """Get the segments that can be cleaned."""
        segments: list[Segment] = []
        map_data_list = self.device.status.map_data_list
        if map_data_list is None:
            return segments

        for map_data in map_data_list.values():
            if map_data.segments is None or map_data.map_index is None:
                continue

            for segment_id, segment in map_data.segments.items():
                if segment.visibility is False:
                    continue

                segments.append(
                    Segment(
                        id=f"{map_data.map_index}_{segment_id}",
                        name=self._localize_segment_name(segment, segment_id),
                        group=map_data.map_name,
                    )
                )

        return segments

    async def async_get_segments(self) -> list[Segment]:
        """Get the segments that can be cleaned."""
        return self._get_segments()

    async def async_clean_segments(self, segment_ids: list[str], **kwargs) -> None:
        """Perform an area clean.

        Only cleans segments from the currently selected map.
        """
        selected_map = self.device.status.selected_map
        if selected_map is None or selected_map.map_index is None:
            return

        selected_map_index = selected_map.map_index

        # Parse composite IDs and filter to only segments from the selected map
        int_segment_ids: list[int] = []
        for composite_id in segment_ids:
            map_index_str, segment_id_str = composite_id.split("_", 1)
            if int(map_index_str) == selected_map_index:
                int_segment_ids.append(int(segment_id_str))

        if not int_segment_ids:
            return

        await self._try_command(
            "Unable to call clean_segment: %s",
            self.device.clean_segment,
            int_segment_ids,
        )

    async def async_goto(self, x, y) -> None:
        """Go to a point and take pictures around."""
        if x is not None and y is not None and x != "" and y != "":
            await self._try_command("Unable to call go_to: %s", self.device.go_to, x, y)

    async def async_follow_path(self, points="") -> None:
        """Start a survaliance job."""
        await self._try_command("Unable to call follow_path: %s", self.device.follow_path, points)

    async def async_start_shortcut(self, shortcut_id="") -> None:
        """Start a shortct job."""
        await self._try_command("Unable to call start_shortcut: %s", self.device.start_shortcut, shortcut_id)

    async def async_set_restricted_zone(self, walls="", zones="", no_mops="") -> None:
        """Create restricted zone."""
        await self._try_command(
            "Unable to call set_restricted_zone: %s",
            self.device.set_restricted_zone,
            walls,
            zones,
            no_mops,
        )

    async def async_set_carpet_area(self, carpets="", deleted_carpets="") -> None:
        """Create or update carpet areas."""
        await self._try_command(
            "Unable to call set_carpet_area: %s",
            self.device.set_carpet_area,
            carpets,
            deleted_carpets,
        )

    async def async_set_carpet_type(
        self,
        id,
        object_type,
        carpet_type=None,
    ) -> None:
        """Set carpet type"""
        if id != "" and id is not None and object_type != "" and object_type is not None:
            await self._try_command(
                "Unable to call set_carpet_type: %s",
                self.device.set_carpet_type,
                id,
                object_type,
                carpet_type,
            )

    async def async_set_virtual_threshold(self, virtual_thresholds="") -> None:
        """Create or update virtual thresholds."""
        await self._try_command(
            "Unable to call set_virtual_threshold: %s",
            self.device.set_virtual_threshold,
            virtual_thresholds,
        )

    async def async_set_threshold(self, passable_thresholds="", impassable_thresholds="", ramps="") -> None:
        """Create or update thresholds."""
        await self._try_command(
            "Unable to call set_threshold: %s",
            self.device.set_threshold,
            passable_thresholds,
            impassable_thresholds,
            ramps,
        )

    async def async_set_predefined_points(self, points="") -> None:
        """Create or update predefined coordinates on the map."""
        await self._try_command(
            "Unable to call set_predefined_points: %s",
            self.device.set_predefined_points,
            points,
        )

    async def async_remote_control_move_step(
        self, rotation: int = 0, velocity: int = 0, prompt: bool | None = None
    ) -> None:
        """Remote control the robot."""
        await self._try_command(
            "Unable to call remote_control_move_step: %s",
            self.device.remote_control_move_step,
            rotation,
            velocity,
            prompt,
        )

    async def async_set_fan_speed(self, fan_speed, **kwargs) -> None:
        """Set fan speed."""
        if self.device.status.cruising:
            raise InvalidActionException("Cannot set fan speed when cruising")

        if self.device.status.started and (
            self.device.status.customized_cleaning
            and not (self.device.status.zone_cleaning or self.device.status.spot_cleaning)
        ):
            raise InvalidActionException("Cannot set fan speed when customized cleaning is enabled")

        if isinstance(fan_speed, str) and fan_speed.isnumeric():
            fan_speed = int(fan_speed)

        if isinstance(fan_speed, int):
            if fan_speed not in DreameVacuumSuctionLevel._value2member_map_:
                raise HomeAssistantError("Invalid fan speed")
        else:
            fan_speed = fan_speed.lower()
            fan_speeds = {
                "silent": DreameVacuumSuctionLevel.QUIET,
                "standard": DreameVacuumSuctionLevel.STANDARD,
                "strong": DreameVacuumSuctionLevel.STRONG,
                "turbo": DreameVacuumSuctionLevel.TURBO,
            }
            if fan_speed in fan_speeds:
                fan_speed = fan_speeds[fan_speed]
            else:
                raise HomeAssistantError(
                    "Fan speed not recognized. Valid options: %s",
                    self.fan_speed_list,
                ) from None

        await self._try_command("Unable to set fan speed: %s", self.device.set_suction_level, fan_speed)

    async def async_select_map(self, map_id) -> None:
        """Switch selected map."""
        await self._try_command("Unable to switch to selected map: %s", self.device.set_selected_map, map_id)

    async def async_delete_map(self, map_id=None) -> None:
        """Delete a map."""
        await self._try_command("Unable to delete map: %s", self.device.delete_map, map_id)

    async def async_save_temporary_map(self) -> None:
        """Save the temporary map."""
        await self._try_command("Unable to save map: %s", self.device.save_temporary_map)

    async def async_discard_temporary_map(self) -> None:
        """Discard the temporary map."""
        await self._try_command("Unable to discard temporary map: %s", self.device.discard_temporary_map)

    async def async_replace_temporary_map(self, map_id=None) -> None:
        """Replace the temporary map with another saved map."""
        await self._try_command(
            "Unable to replace temporary map: %s",
            self.device.replace_temporary_map,
            map_id,
        )

    async def async_request_map(self) -> None:
        """Request new map."""
        await self._try_command("Unable to call request_map: %s", self.device.request_map)

    async def async_set_property(self, key, value=None, params=None) -> None:
        """Set property."""
        if key is not None and value is not None and key != "" and value != "":
            await self._try_command("set_property failed: %s", self.device.set_property_value, key, value, params)

    async def async_call_action(self, key, value=None) -> None:
        """Call action."""
        if key is not None and key != "":
            await self._try_command("call_action failed: %s", self.device.call_action_value, key, value)

    async def async_rename_map(self, map_id, map_name="") -> None:
        """Rename a map"""
        await self._try_command(
            "Unable to call rename_map: %s",
            self.device.rename_map,
            map_id,
            map_name,
        )

    async def async_restore_map(self, recovery_map_index, map_id=None) -> None:
        """Restore a map"""
        if recovery_map_index and recovery_map_index != "":
            await self._try_command(
                "Unable to call restore_map: %s",
                self.device.restore_map,
                recovery_map_index,
                map_id,
            )

    async def async_restore_map_from_file(self, file_url, map_id=None) -> None:
        """Restore a map from file"""
        if file_url and file_url != "":
            await self._try_command(
                "Unable to call restore_map_from_file: %s",
                self.device.restore_map_from_file,
                file_url,
                map_id,
            )

    async def async_backup_map(self, map_id=None) -> None:
        """Backup a map"""
        await self._try_command(
            "Unable to call backup_map: %s",
            self.device.backup_map,
            map_id,
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

    async def async_set_custom_cleaning(
        self,
        segment_id,
        suction_level,
        water_volume,
        repeats,
        cleaning_mode=None,
        custom_mopping_route=None,
        cleaning_route=None,
        wetness_level=None,
        mop_temperature=None,
        mop_pressure=None,
    ) -> None:
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
                cleaning_mode,
                custom_mopping_route,
                cleaning_route,
                wetness_level,
                mop_temperature,
                mop_pressure,
            )

    async def async_set_custom_carpet_cleaning(
        self,
        id,
        object_type,
        carpet_cleaning=None,
        carpet_preferences=None,
    ) -> None:
        """Set custom carpet cleaning"""
        if id != "" and id is not None and object_type != "" and object_type is not None:
            await self._try_command(
                "Unable to call set_custom_carpet_cleaning: %s",
                self.device.set_custom_carpet_cleaning,
                id,
                object_type,
                carpet_cleaning,
                carpet_preferences,
            )

    async def async_set_segment_type(
        self,
        type,
        map_id=None,
    ) -> None:
        """Set segment type"""
        if type != "" and type is not None:
            await self._try_command("Unable to call set_segment_type: %s", self.device.set_segment_type, type, map_id)

    async def async_set_hidden_segments(
        self,
        segments=None,
        map_id=None,
    ) -> None:
        """Set hidden segments"""
        if segments is None:
            segments = []
        if segments != "" and segments is not None:
            await self._try_command(
                "Unable to call set_hidden_segments: %s",
                self.device.set_hidden_segments,
                segments,
                map_id,
            )

    async def async_set_floor_material(
        self,
        material,
        map_id=None,
    ) -> None:
        """Set floor material"""
        if material != "" and material is not None:
            await self._try_command(
                "Unable to call set_floor_material: %s", self.device.set_floor_material, material, map_id
            )

    async def async_set_low_lying_area(
        self,
        area=None,
    ) -> None:
        """Set low lying area"""
        if area != "" and area is not None:
            await self._try_command("Unable to call set_low_lying_area: %s", self.device.set_low_lying_area, area)

    async def async_set_furniture(
        self,
        furnitures=None,
    ) -> None:
        """Set furnitures"""
        if furnitures != "" and furnitures is not None:
            await self._try_command("Unable to call set_furniture: %s", self.device.set_furniture, furnitures)

    async def async_set_curtain(
        self,
        curtains=None,
    ) -> None:
        """Set curtains"""
        if curtains != "" and curtains is not None:
            await self._try_command("Unable to call set_curtain: %s", self.device.set_curtain, curtains)

    async def async_set_mop_type(
        self,
        mop_type,
        map_id=None,
    ) -> None:
        """Set mop type"""
        if mop_type != "" and mop_type is not None:
            await self._try_command("Unable to call set_mop_type: %s", self.device.set_mop_type, mop_type, map_id)

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

    async def async_send_command(self, command: str, params=None, **kwargs) -> None:
        """Send a command to a vacuum cleaner."""
        await self._try_command("Unable to call send_command: %s", self.device.send_command, command, params)

    async def async_reset_consumable(self, consumable: str) -> None:
        """Reset consumable"""
        action = CONSUMABLE_RESET_ACTION.get(consumable)
        if action:
            await self._try_command(
                "Unable to call reset_consumable: %s",
                self.device.call_action,
                action,
            )

    async def async_rename_shortcut(self, shortcut_id, shortcut_name) -> None:
        """Rename a shortcut"""
        if shortcut_name and shortcut_name != "":
            await self._try_command(
                "Unable to call rename_shortcut: %s",
                self.device.rename_shortcut,
                shortcut_id,
                shortcut_name,
            )

    async def async_delete_shortcut(self, shortcut_id) -> None:
        """Delete a shortcut"""
        if shortcut_id and shortcut_id != "":
            await self._try_command(
                "Unable to call delete_shortcut: %s",
                self.device.delete_shortcut,
                shortcut_id,
            )

    async def async_set_obstacle_ignore(self, x, y, obstacle_ignored) -> None:
        """Set obstacle ignore status"""
        if x is not None and x != "" and y is not None and y != "":
            await self._try_command(
                "Unable to call set_obstacle_ignore: %s",
                self.device.set_obstacle_ignore,
                x,
                y,
                obstacle_ignored,
            )

    async def async_set_router_position(self, x, y) -> None:
        """Set router position on current map"""
        if x is not None and x != "" and y is not None and y != "":
            await self._try_command(
                "Unable to call set_router_position: %s",
                self.device.set_router_position,
                x,
                y,
            )

    async def async_set_walls(self, walls=None, doors=None, map_id=None) -> None:
        """Set walls and doors"""
        if (walls is not None and walls != "") or (doors is not None and doors != ""):
            await self._try_command("Unable to call set_walls: %s", self.device.set_walls, walls, doors, map_id)
