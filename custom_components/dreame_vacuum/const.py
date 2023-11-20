import logging
from typing import Final

DOMAIN = "dreame_vacuum"
LOGGER = logging.getLogger(__package__)

UNIT_MINUTES: Final = "min"
UNIT_HOURS: Final = "hr"
UNIT_PERCENT: Final = "%"
UNIT_DAYS: Final = "dy"
UNIT_AREA: Final = "m²"
UNIT_TIMES: Final = "x"

CONF_NOTIFY: Final = "notify"
CONF_COLOR_SCHEME: Final = "color_scheme"
CONF_COLOR_SCHEME_BACKGROUND: Final = "color_scheme_background"
CONF_ICON_SET: Final = "icon_set"
CONF_COUNTRY: Final = "country"
CONF_TYPE: Final = "configuration_type"
CONF_MAC: Final = "mac"
CONF_DID: Final = "did"
CONF_MAP_OBJECTS: Final = "map_objects"
CONF_MAP_OBJECTS_OVERLAY: Final = "map_objects_overlay"
CONF_MAP_OBJECTS_BACKGROUND: Final = "map_objects_background"
CONF_PREFER_CLOUD: Final = "prefer_cloud"
CONF_LOW_RESOLUTION: Final = "low_resolution"
CONF_SQUARE: Final = "square"
CONF_ACCOUNT_TYPE: Final = "account_type"

CONTENT_TYPE: Final = "image/png"

MAP_OBJECTS: Final = {
    "color": "Room Colors",
    "icon": "Room Icons",
    "name": "Room Names",
    "name_background": "Room Name Background",
    "order": "Room Order",
    "suction_level": "Room Suction Level",
    "water_volume": "Room Water Volume",
    "cleaning_times": "Room Cleaning Times",
    "cleaning_mode": "Room Cleaning Mode",
    "mopping_mode": "Room Mopping Mode",
    "path": "Path",
    "no_go": "No Go Zones",
    "no_mop": "No Mop Zones",
    "virtual_wall": "Virtual Walls",
    "pathway": "Pathways",
    "active_area": "Active Areas",
    "active_point": "Active Points",
    "charger": "Charger Icon",
    "robot": "Robot Icon",
    "cleaning_direction": "Cleaning Direction",
    "obstacle": "AI Obstacle",
    "pet": "Pet",
    "carpet": "Carpet Area",
    "material": "Floor Material",
    "furniture": "Furniture",
    "cruise_point": "Cruise Points",
}
NOTIFICATION: Final = {
    "cleanup_completed": "Cleanup Completed",
    "consumable": "Consumable",
    "information": "Information",
    "warning": "Warning",
    "error": "Error",
}

FAN_SPEED_SILENT: Final = "Silent"
FAN_SPEED_STANDARD: Final = "Standard"
FAN_SPEED_STRONG: Final = "Strong"
FAN_SPEED_TURBO: Final = "Turbo"

SERVICE_CLEAN_ZONE: Final = "vacuum_clean_zone"
SERVICE_CLEAN_SEGMENT: Final = "vacuum_clean_segment"
SERVICE_CLEAN_SPOT: Final = "vacuum_clean_spot"
SERVICE_GOTO: Final = "vacuum_goto"
SERVICE_FOLLOW_PATH: Final = "vacuum_follow_path"
SERVICE_REQUEST_MAP: Final = "vacuum_request_map"
SERVICE_SELECT_MAP: Final = "vacuum_select_map"
SERVICE_DELETE_MAP: Final = "vacuum_delete_map"
SERVICE_SET_RESTRICTED_ZONE: Final = "vacuum_set_restricted_zone"
SERVICE_SET_CARPET_AREA: Final = "vacuum_set_carpet_area"
SERVICE_SET_PATHWAY: Final = "vacuum_set_pathway"
SERVICE_SET_PREDEFINED_POINTS: Final = "vacuum_set_predefined_points"
SERVICE_MOVE_REMOTE_CONTROL_STEP: Final = "vacuum_remote_control_move_step"
SERVICE_RENAME_MAP: Final = "vacuum_rename_map"
SERVICE_RESTORE_MAP: Final = "vacuum_restore_map"
SERVICE_RESTORE_MAP_FROM_FILE: Final = "vacuum_restore_map_from_file"
SERVICE_BACKUP_MAP: Final = "vacuum_backup_map"
SERVICE_SAVE_TEMPORARY_MAP: Final = "vacuum_save_temporary_map"
SERVICE_DISCARD_TEMPORARY_MAP: Final = "vacuum_discard_temporary_map"
SERVICE_REPLACE_TEMPORARY_MAP: Final = "vacuum_replace_temporary_map"
SERVICE_MERGE_SEGMENTS: Final = "vacuum_merge_segments"
SERVICE_SPLIT_SEGMENTS: Final = "vacuum_split_segments"
SERVICE_RENAME_SEGMENT: Final = "vacuum_rename_segment"
SERVICE_SET_CLEANING_SEQUENCE: Final = "vacuum_set_cleaning_sequence"
SERVICE_SET_CUSTOM_CLEANING: Final = "vacuum_set_custom_cleaning"
SERVICE_INSTALL_VOICE_PACK: Final = "vacuum_install_voice_pack"
SERVICE_RESET_CONSUMABLE: Final = "vacuum_reset_consumable"
SERVICE_RENAME_SHORTCUT: Final = "vacuum_rename_shortcut"
SERVICE_SET_OBSTACLE_IGNORE: Final = "vacuum_set_obstacle_ignore"
SERVICE_SET_ROUTER_POSITION: Final = "vacuum_set_router_position"

SERVICE_SELECT_NEXT = "select_select_next"
SERVICE_SELECT_PREVIOUS = "select_select_previous"
SERVICE_SELECT_FIRST = "select_select_first"
SERVICE_SELECT_LAST = "select_select_last"

INPUT_ROTATION: Final = "rotation"
INPUT_VELOCITY: Final = "velocity"
INPUT_MAP_ID: Final = "map_id"
INPUT_MAP_NAME: Final = "map_name"
INPUT_FILE_URL: Final = "file_url"
INPUT_RECOVERY_MAP_INDEX: Final = "recovery_map_index"
INPUT_WALL_ARRAY: Final = "walls"
INPUT_ZONE: Final = "zone"
INPUT_ZONE_ARRAY: Final = "zones"
INPUT_CARPET_ARRAY: Final = "carpets"
INPUT_IGNORED_CARPET_ARRAY: Final = "ignored_carpets"
INPUT_PATHWAY_ARRAY: Final = "pathways"
INPUT_REPEATS: Final = "repeats"
INPUT_CLEANING_MODE: Final = "cleaning_mode"
INPUT_SEGMENTS_ARRAY: Final = "segments"
INPUT_SEGMENT: Final = "segment"
INPUT_SEGMENT_ID: Final = "segment_id"
INPUT_SEGMENT_NAME: Final = "segment_name"
INPUT_LINE: Final = "line"
INPUT_SUCTION_LEVEL: Final = "suction_level"
INPUT_MOP_MODE: Final = "mop_mode"
INPUT_MOP_ARRAY: Final = "no_mops"
INPUT_LANGUAGE_ID: Final = "lang_id"
INPUT_DELAY: Final = "delay"
INPUT_URL: Final = "url"
INPUT_MD5: Final = "md5"
INPUT_SIZE: Final = "size"
INPUT_CLEANING_SEQUENCE: Final = "cleaning_sequence"
INPUT_WATER_VOLUME: Final = "water_volume"
INPUT_CONSUMABLE: Final = "consumable"
INPUT_CYCLE: Final = "cycle"
INPUT_POINTS: Final = "points"
INPUT_SHORTCUT_ID: Final = "shortcut_id"
INPUT_SHORTCUT_NAME: Final = "shortcut_name"
INPUT_X: Final = "x"
INPUT_Y: Final = "y"
INPUT_OBSTACLE_IGNORED: Final = "obstacle_ignored"

CONSUMABLE_MAIN_BRUSH = "main_brush"
CONSUMABLE_SIDE_BRUSH = "side_brush"
CONSUMABLE_FILTER = "filter"
CONSUMABLE_SECONDARY_FILTER = "secondary_filter"
CONSUMABLE_SENSOR = "sensor"
CONSUMABLE_MOP_PAD = "mop_pad"
CONSUMABLE_SILVER_ION = "silver_ion"
CONSUMABLE_DETERGENT = "detergent"
CONSUMABLE_SQUEEGEE = "squeegee"
CONSUMABLE_ONBOARD_DIRTY_WATER_TANK = "onboard_dirty_water_tank"
CONSUMABLE_DIRTY_WATER_TANK = "dirty_water_tank"

NOTIFICATION_ID_DUST_COLLECTION: Final = "dust_collection"
NOTIFICATION_ID_CLEANING_PAUSED: Final = "cleaning_paused"
NOTIFICATION_ID_REPLACE_MAIN_BRUSH: Final = "replace_main_brush"
NOTIFICATION_ID_REPLACE_SIDE_BRUSH: Final = "replace_side_brush"
NOTIFICATION_ID_REPLACE_FILTER: Final = "replace_filter"
NOTIFICATION_ID_REPLACE_SECONDARY_FILTER: Final = "replace_secondary_filter"
NOTIFICATION_ID_CLEAN_SENSOR: Final = "clean_sensor"
NOTIFICATION_ID_REPLACE_MOP: Final = "replace_mop"
NOTIFICATION_ID_SILVER_ION: Final = "silver_ion"
NOTIFICATION_ID_REPLACE_DETERGENT: Final = "replace_detergent"
NOTIFICATION_ID_REPLACE_SQUEEGEE: Final = "replace_squeegee"
NOTIFICATION_ID_CLEAN_ONBOARD_DIRTY_WATER_TANK: Final = "clean_onboard_dirty_water_tank"
NOTIFICATION_ID_CLEAN_DIRTY_WATER_TANK: Final = "clean_dirty_water_tank"
NOTIFICATION_ID_CLEANUP_COMPLETED: Final = "cleanup_completed"
NOTIFICATION_ID_WARNING: Final = "warning"
NOTIFICATION_ID_ERROR: Final = "error"
NOTIFICATION_ID_INFORMATION: Final = "information"
NOTIFICATION_ID_CONSUMABLE: Final = "consumable"
NOTIFICATION_ID_REPLACE_TEMPORARY_MAP: Final = "replace_temporary_map"
NOTIFICATION_ID_2FA_LOGIN: Final = "2fa_login"
NOTIFICATION_ID_LOW_WATER: Final = "low_water"
NOTIFICATION_ID_DRAINAGE_STATUS: Final = "drainage_status"

NOTIFICATION_CLEANUP_COMPLETED: Final = "### Cleanup completed"
NOTIFICATION_DUST_COLLECTION_NOT_PERFORMED: Final = "### Dust collecting (Auto-empty) task not performed\nThe robot will not perform auto-empty tasks during the DND period."
NOTIFICATION_RESUME_CLEANING: Final = "### Resume Cleaning Mode\nThe robot will automatically resume unfinished cleaning tasks after charging its battery to 80%."
NOTIFICATION_RESUME_CLEANING_NOT_PERFORMED: Final = "### The robot is in the DND period\nRobot will resume cleaning after the DND period ends."
NOTIFICATION_REPLACE_MAP: Final = (
    "### A new map has been generated\nYou need to save or discard map before using it."
)
NOTIFICATION_REPLACE_MULTI_MAP: Final = "### A new map has been generated\nMulti-floor maps that can be saved have reached the upper limit. You need to replace or discard map before using it."
NOTIFICATION_2FA_LOGIN: Final = "### Additional authentication required.\nOpen following URL using device that has the same public IP, as your Home Assistant instance:\n"
NOTIFICATION_DRAINAGE_COMPLETED: Final = "### Drainage completed"
NOTIFICATION_DRAINAGE_FAILED: Final = "### Drainage failed"

EVENT_TASK_STATUS: Final = "task_status"
EVENT_CONSUMABLE: Final = "consumable"
EVENT_WARNING: Final = "warning"
EVENT_ERROR: Final = "error"
EVENT_LOW_WATER: Final = "low_water"
EVENT_INFORMATION: Final = "information"
EVENT_DRAINAGE_STATUS: Final = "drainage_status"
EVENT_2FA_LOGIN: Final = "2fa_login"
