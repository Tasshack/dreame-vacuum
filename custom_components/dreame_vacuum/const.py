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
CONF_ICON_SET: Final = "icon_set"
CONF_COUNTRY: Final = "country"
CONF_TYPE: Final = "configuration_type"
CONF_MAC: Final = "mac"
CONF_DID: Final = "did"
CONF_AUTH_KEY: Final = "auth_key"
CONF_MAP_OBJECTS: Final = "map_objects"
CONF_HIDDEN_MAP_OBJECTS: Final = "hidden_map_objects"
CONF_PREFER_CLOUD: Final = "prefer_cloud"
CONF_LOW_RESOLUTION: Final = "low_resolution"
CONF_SQUARE: Final = "square"
CONF_ACCOUNT_TYPE: Final = "account_type"
CONF_DONATED: Final = "donated"
CONF_VERSION: Final = "version"

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
    "pathway": "Virtual Thresholds",
    "active_area": "Active Areas",
    "active_point": "Active Points",
    "charger": "Charger Icon",
    "robot": "Robot Icon",
    "cleaning_direction": "Cleaning Direction",
    "obstacle": "AI Obstacle",
    "pet": "Pet",
    "carpet": "Carpet Area",
    "material": "Floor Material",
    "low_lying_area": "Low-Lying Areas",
    "furniture": "Furniture",
    "ramp": "Ramp",
    "curtain": "Curtain",
    "cruise_point": "Cruise Points",
}
NOTIFICATION: Final = {
    "cleanup_completed": "Cleanup Completed",
    "consumable": "Consumable",
    "information": "Information",
    "warning": "Warning",
    "error": "Error",
}

SPONSOR: Final = (
    '\n<p><a href="https://ko-fi.com/tasshack"><img src="data:image/png;base64,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"/></a></p><p><a href="https://paypal.me/tasshackK"><img src="data:image/png;base64,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"></a></p><p><a href="https://github.com/sponsors/Tasshack"><img src="data:image/png;base64,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"></a></p>'
)

FAN_SPEED_SILENT: Final = "Silent"
FAN_SPEED_STANDARD: Final = "Standard"
FAN_SPEED_STRONG: Final = "Strong"
FAN_SPEED_TURBO: Final = "Turbo"

SERVICE_CLEAN_ZONE: Final = "vacuum_clean_zone"
SERVICE_CLEAN_SEGMENT: Final = "vacuum_clean_segment"
SERVICE_CLEAN_SPOT: Final = "vacuum_clean_spot"
SERVICE_GOTO: Final = "vacuum_goto"
SERVICE_FOLLOW_PATH: Final = "vacuum_follow_path"
SERVICE_START_SHORTCUT: Final = "vacuum_start_shortcut"
SERVICE_REQUEST_MAP: Final = "vacuum_request_map"
SERVICE_SELECT_MAP: Final = "vacuum_select_map"
SERVICE_DELETE_MAP: Final = "vacuum_delete_map"
SERVICE_SET_RESTRICTED_ZONE: Final = "vacuum_set_restricted_zone"
SERVICE_SET_CARPET_AREA: Final = "vacuum_set_carpet_area"
SERVICE_SET_CARPET_TYPE: Final = "vacuum_set_carpet_type"
SERVICE_SET_SEGMENT_TYPE: Final = "vacuum_set_segment_type"
SERVICE_SET_HIDDEN_SEGMENTS: Final = "vacuum_set_hidden_segments"
SERVICE_SET_FLOOR_MATERIAL: Final = "vacuum_set_floor_material"
SERVICE_SET_LOW_LYING_AREA: Final = "vacuum_set_low_lying_area"
SERVICE_SET_FURNITURE: Final = "vacuum_set_furniture"
SERVICE_SET_CURTAIN: Final = "vacuum_set_curtain"
SERVICE_SET_MOP_TYPE: Final = "vacuum_set_mop_type"
SERVICE_SET_VIRTUAL_THRESHOLD: Final = "vacuum_set_virtual_threshold"
SERVICE_SET_THRESHOLD: Final = "vacuum_set_threshold"
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
SERVICE_SET_CUSTOM_CARPET_CLEANING: Final = "vacuum_set_custom_carpet_cleaning"
SERVICE_INSTALL_VOICE_PACK: Final = "vacuum_install_voice_pack"
SERVICE_RESET_CONSUMABLE: Final = "vacuum_reset_consumable"
SERVICE_RENAME_SHORTCUT: Final = "vacuum_rename_shortcut"
SERVICE_DELETE_SHORTCUT: Final = "vacuum_delete_shortcut"
SERVICE_SET_OBSTACLE_IGNORE: Final = "vacuum_set_obstacle_ignore"
SERVICE_SET_ROUTER_POSITION: Final = "vacuum_set_router_position"
SERVICE_SET_PROPERTY: Final = "vacuum_set_property"
SERVICE_CALL_ACTION: Final = "vacuum_call_action"

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
INPUT_DELETED_CARPET_ARRAY: Final = "deleted_carpets"
INPUT_VIRTUAL_THRESHOLD_ARRAY: Final = "virtual_thresholds"
INPUT_PASSABLE_THRESHOLD_ARRAY: Final = "passable_thresholds"
INPUT_IMPASSABLE_THRESHOLD_ARRAY: Final = "impassable_thresholds"
INPUT_RAMP_ARRAY: Final = "ramps"
INPUT_REPEATS: Final = "repeats"
INPUT_CLEANING_MODE: Final = "cleaning_mode"
INPUT_CUSTOM_MOPPING_ROUTE: Final = "custom_mopping_route"
INPUT_CLEANING_ROUTE: Final = "cleaning_route"
INPUT_WETNESS_LEVEL: Final = "wetness_level"
INPUT_MOP_TEMPERATURE: Final = "mop_temperature"
INPUT_MOP_PRESSURE: Final = "mop_pressure"
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
INPUT_KEY: Final = "key"
INPUT_VALUE: Final = "value"
INPUT_PARAMS: Final = "params"
INPUT_ID: Final = "id"
INPUT_TYPE: Final = "type"
INPUT_OBJECT_TYPE: Final = "object_type"
INPUT_CARPET_TYPE: Final = "carpet_type"
INPUT_MATERIAL: Final = "material"
INPUT_CARPET_CLEANING: Final = "carpet_cleaning"
INPUT_CARPET_PREFERENCES: Final = "carpet_preferences"
INPUT_AREA: Final = "area"
INPUT_FURNITURE_ARRAY: Final = "furnitures"
INPUT_CURTAIN_ARRAY: Final = "curtains"
INPUT_MOP_TYPE: Final = "mop_type"

CONSUMABLE_MAIN_BRUSH = "main_brush"
CONSUMABLE_SIDE_BRUSH = "side_brush"
CONSUMABLE_FILTER = "filter"
CONSUMABLE_TANK_FILTER = "tank_filter"
CONSUMABLE_SENSOR = "sensor"
CONSUMABLE_MOP_PAD = "mop_pad"
CONSUMABLE_SILVER_ION = "silver_ion"
CONSUMABLE_DETERGENT = "detergent"
CONSUMABLE_SQUEEGEE = "squeegee"
CONSUMABLE_ONBOARD_DIRTY_WATER_TANK = "onboard_dirty_water_tank"
CONSUMABLE_DIRTY_WATER_CHANNEL = "dirty_water_channel"
CONSUMABLE_DEODORIZER = "deodorizer"
CONSUMABLE_WHEEL = "wheel"
CONSUMABLE_SCALE_INHIBITOR = "scale_inhibitor"
CONSUMABLE_FLUFFING_ROLLER = "fluffing_roller"
CONSUMABLE_ROLLER_MOP_FILTER = "roller_mop_filter"
CONSUMABLE_WATER_OUTLET_FILTER = "water_outlet_filter"

NOTIFICATION_ID_DUST_COLLECTION: Final = "dust_collection"
NOTIFICATION_ID_CLEANING_PAUSED: Final = "cleaning_paused"
NOTIFICATION_ID_REPLACE_MAIN_BRUSH: Final = "replace_main_brush"
NOTIFICATION_ID_REPLACE_SIDE_BRUSH: Final = "replace_side_brush"
NOTIFICATION_ID_REPLACE_FILTER: Final = "replace_filter"
NOTIFICATION_ID_REPLACE_TANK_FILTER: Final = "replace_tank_filter"
NOTIFICATION_ID_CLEAN_SENSOR: Final = "clean_sensor"
NOTIFICATION_ID_REPLACE_MOP: Final = "replace_mop"
NOTIFICATION_ID_SILVER_ION: Final = "silver_ion"
NOTIFICATION_ID_REPLACE_DETERGENT: Final = "replace_detergent"
NOTIFICATION_ID_REPLACE_SQUEEGEE: Final = "replace_squeegee"
NOTIFICATION_ID_CLEAN_ONBOARD_DIRTY_WATER_TANK: Final = "clean_onboard_dirty_water_tank"
NOTIFICATION_ID_CLEAN_DIRTY_WATER_CHANNEL: Final = "clean_dirty_water_channel"
NOTIFICATION_ID_REPLACE_DEODORIZER = "replace_deodorizer"
NOTIFICATION_ID_CLEAN_WHEEL = "clean_wheel"
NOTIFICATION_ID_REPLACE_SCALE_INHIBITOR = "replace_scale_inhibitor"
NOTIFICATION_ID_CLEAN_FLUFFING_ROLLER = "clean_fluffing_roller"
NOTIFICATION_ID_CLEAN_ROLLER_MOP_FILTER = "clean_roller_mop_filter"
NOTIFICATION_ID_CLEAN_WATER_OUTLET_FILTER = "clean_water_outlet_filter"
NOTIFICATION_ID_CLEANUP_COMPLETED: Final = "cleanup_completed"
NOTIFICATION_ID_WARNING: Final = "warning"
NOTIFICATION_ID_ERROR: Final = "error"
NOTIFICATION_ID_INFORMATION: Final = "information"
NOTIFICATION_ID_CONSUMABLE: Final = "consumable"
NOTIFICATION_ID_REPLACE_TEMPORARY_MAP: Final = "replace_temporary_map"
NOTIFICATION_ID_LOW_WATER: Final = "low_water"
NOTIFICATION_ID_DRAINAGE_STATUS: Final = "drainage_status"

NOTIFICATION_CLEANUP_COMPLETED: Final = "### Cleanup completed"
NOTIFICATION_DUST_COLLECTION_NOT_PERFORMED: Final = (
    "### Dust collecting (Auto-empty) task not performed\nThe robot will not perform auto-empty tasks during the DND period."
)
NOTIFICATION_RESUME_CLEANING: Final = (
    "### Resume Cleaning Mode\nThe robot will automatically resume unfinished cleaning tasks after charging its battery to 80%."
)
NOTIFICATION_RESUME_CLEANING_NOT_PERFORMED: Final = (
    "### The robot is in the DND period\nRobot will resume cleaning after the DND period ends."
)
NOTIFICATION_REPLACE_MAP: Final = "### A new map has been generated\nYou need to save or discard map before using it."
NOTIFICATION_REPLACE_MULTI_MAP: Final = (
    "### A new map has been generated\nMulti-floor maps that can be saved have reached the upper limit. You need to replace or discard map before using it."
)
NOTIFICATION_DRAINAGE_COMPLETED: Final = "### Drainage completed"
NOTIFICATION_DRAINAGE_FAILED: Final = "### Drainage failed"
NOTIFICATION_SPONSOR: Final = f"## Do not forget to support the project.{SPONSOR}"

EVENT_TASK_STATUS: Final = "task_status"
EVENT_CONSUMABLE: Final = "consumable"
EVENT_WARNING: Final = "warning"
EVENT_ERROR: Final = "error"
EVENT_LOW_WATER: Final = "low_water"
EVENT_INFORMATION: Final = "information"
EVENT_DRAINAGE_STATUS: Final = "drainage_status"
