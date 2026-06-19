from typing import Final
from .types import (
    DreameVacuumChargingStatus,
    DreameVacuumTaskStatus,
    DreameVacuumState,
    DreameVacuumWaterTank,
    DreameVacuumCarpetSensitivity,
    DreameVacuumCarpetCleaning,
    DreameVacuumStatus,
    DreameVacuumErrorCode,
    DreameVacuumRelocationStatus,
    DreameVacuumDustCollection,
    DreameVacuumAutoEmptyStatus,
    DreameVacuumMapRecoveryStatus,
    DreameVacuumMapBackupStatus,
    DreameVacuumSelfWashBaseStatus,
    DreameVacuumSuctionLevel,
    DreameVacuumWaterVolume,
    DreameVacuumMopPadHumidity,
    DreameVacuumCleaningMode,
    DreameVacuumMopWashLevel,
    DreameVacuumMopCleanFrequency,
    DreameVacuumMoppingType,
    DreameVacuumStreamStatus,
    DreameVacuumVoiceAssistantLanguage,
    DreameVacuumMopPressure,
    DreameVacuumMopTemperature,
    DreameVacuumLowLyingAreaFrequency,
    DreameVacuumScraperFrequency,
    DreameVacuumWiderCornerCoverage,
    DreameVacuumMopPadSwing,
    DreameVacuumMopExtendFrequency,
    DreameVacuumSecondCleaning,
    DreameVacuumCleaningRoute,
    DreameVacuumCustomMoppingRoute,
    DreameVacuumSelfCleanFrequency,
    DreameVacuumAutoEmptyMode,
    DreameVacuumAutoEmptyModeV2,
    DreameVacuumCleanGenius,
    DreameVacuumCleanGeniusMode,
    DreameVacuumWashingMode,
    DreameVacuumWaterTemperature,
    DreameVacuumAutoLDSCoverage,
    DreameVacuumFloorMaterial,
    DreameVacuumFloorMaterialDirection,
    DreameVacuumSegmentVisibility,
    DreameVacuumDrainageStatus,
    DreameVacuumLowWaterWarning,
    DreameVacuumTaskType,
    DreameVacuumCleanWaterTankStatus,
    DreameVacuumDirtyWaterTankStatus,
    DreameVacuumDustBagStatus,
    DreameVacuumDetergentStatus,
    DreameVacuumHotWaterStatus,
    DreameVacuumStationDrainageStatus,
    DreameVacuumDustBagDryingStatus,
    DreameVacuumProperty,
    DreameVacuumAIProperty,
    DreameVacuumStrAIProperty,
    DreameVacuumAutoSwitchProperty,
    DreameVacuumAction,
)

SUCTION_LEVEL_QUIET: Final = "quiet"
SUCTION_LEVEL_STANDARD: Final = "standard"
SUCTION_LEVEL_STRONG: Final = "strong"
SUCTION_LEVEL_TURBO: Final = "turbo"

WATER_VOLUME_LOW: Final = "low"
WATER_VOLUME_MEDIUM: Final = "medium"
WATER_VOLUME_HIGH: Final = "high"

MOP_PAD_HUMIDITY_SLIGHTLY_DRY: Final = "slightly_dry"
MOP_PAD_HUMIDITY_MOIST: Final = "moist"
MOP_PAD_HUMIDITY_WET: Final = "wet"

CLEANING_MODE_SWEEPING: Final = "sweeping"
CLEANING_MODE_MOPPING: Final = "mopping"
CLEANING_MODE_SWEEPING_AND_MOPPING: Final = "sweeping_and_mopping"
CLEANING_MODE_MOPPING_AFTER_SWEEPING: Final = "mopping_after_sweeping"

STATE_NOT_SET: Final = "not_set"
STATE_UNKNOWN: Final = "unknown"
STATE_SWEEPING: Final = "sweeping"
STATE_IDLE: Final = "idle"
STATE_PAUSED: Final = "paused"
STATE_RETURNING: Final = "returning"
STATE_CHARGING: Final = "charging"
STATE_ERROR: Final = "error"
STATE_MOPPING: Final = "mopping"
STATE_DRYING: Final = "drying"
STATE_WASHING: Final = "washing"
STATE_RETURNING_WASH: Final = "returning_to_wash"
STATE_BUILDING: Final = "building"
STATE_SWEEPING_AND_MOPPING: Final = "sweeping_and_mopping"
STATE_CHARGING_COMPLETED: Final = "charging_completed"
STATE_UPGRADING: Final = "upgrading"
STATE_CLEAN_SUMMON: Final = "clean_summon"
STATE_STATION_RESET: Final = "station_reset"
STATE_RETURNING_INSTALL_MOP: Final = "returning_install_mop"
STATE_RETURNING_REMOVE_MOP: Final = "returning_remove_mop"
STATE_WATER_CHECK: Final = "water_check"
STATE_CLEAN_ADD_WATER: Final = "clean_add_water"
STATE_WASHING_PAUSED: Final = "washing_paused"
STATE_AUTO_EMPTYING: Final = "auto_emptying"
STATE_REMOTE_CONTROL: Final = "remote_control"
STATE_SMART_CHARGING: Final = "smart_charging"
STATE_SECOND_CLEANING: Final = "second_cleaning"
STATE_HUMAN_FOLLOWING: Final = "human_following"
STATE_SPOT_CLEANING: Final = "spot_cleaning"
STATE_RETURNING_AUTO_EMPTY: Final = "returning_auto_empty"
STATE_WAITING_FOR_TASK: Final = "waiting_for_task"
STATE_STATION_CLEANING: Final = "station_cleaning"
STATE_RETURNING_TO_DRAIN: Final = "returning_to_drain"
STATE_DRAINING: Final = "draining"
STATE_AUTO_WATER_DRAINING: Final = "auto_water_draining"
STATE_EMPTYING: Final = "emptying"
STATE_DUST_BAG_DRYING: Final = "dust_bag_drying"
STATE_DUST_BAG_DRYING_PAUSED: Final = "dust_bag_drying_paused"
STATE_HEADING_TO_EXTRA_CLEANING: Final = "heading_to_extra_cleaning"
STATE_EXTRA_CLEANING: Final = "extra_cleaning"
STATE_FINDING_PET_PAUSED: Final = "finding_pet_paused"
STATE_FINDING_PET: Final = "finding_pet"
STATE_SHORTCUT: Final = "shortcut"
STATE_MONITORING: Final = "monitoring"
STATE_MONITORING_PAUSED: Final = "monitoring_paused"
STATE_INITIAL_DEEP_CLEANING: Final = "initial_deep_cleaning"
STATE_INITIAL_DEEP_CLEANING_PAUSED: Final = "initial_deep_cleaning_paused"
STATE_SANITIZING: Final = "sanitizing"
STATE_SANITIZING_WITH_DRY: Final = "sanitizing_with_dry"
STATE_CHANGING_MOP: Final = "changing_mop"
STATE_CHANGING_MOP_PAUSED: Final = "changing_mop_paused"
STATE_FLOOR_MAINTAINING: Final = "floor_maintaining"
STATE_FLOOR_MAINTAINING_PAUSED: Final = "floor_maintaining_paused"
STATE_UNAVAILABLE: Final = "unavailable"
STATE_OFF: Final = "off"
STATE_CLEANING: Final = "cleaning"
STATE_DOCKED: Final = "docked"
STATE_REMOTE_PICKUP: Final = "remote_pickup"
STATE_ARRANGING_ITEMS: Final = "arranging_items"
STATE_PET_GUARDING: Final = "pet_guarding"
STATE_PET_GUARDING_PAUSED: Final = "pet_guarding_paused"
STATE_INSTALLING_MOP: Final = "installing_mop"
STATE_UNINSTALLING_MOP: Final = "uninstalling_mop"
STATE_INTELLIGENT_RECHARGING: Final = "intelligent_recharging"
STATE_ASSISTED_CLEANING: Final = "assisted_cleaning"
STATE_ENTERING_DOCK: Final = "entering_dock"
STATE_LEAVING_DOCK: Final = "leaving_dock"
STATE_NAVIGATING_TO_CLIMBER: Final = "navigating_to_climber"
STATE_DOCKING_TO_CLIMBER: Final = "docking_to_climber"
STATE_CLIMBER_DOCKED: Final = "climber_docked"
STATE_CLIMBER_NAVIGATING: Final = "climber_navigating"
STATE_CLIMBING_STAIRS: Final = "climbing_stairs"
STATE_CLIMBING_STAIRS_COMPLETED: Final = "climbing_stairs_completed"
STATE_CLIMBER_AT_DOCK: Final = "climber_at_dock"
STATE_CLIMBER_LEAVING_DOCK: Final = "climber_leaving_dock"

TASK_STATUS_COMPLETED: Final = "completed"
TASK_STATUS_AUTO_CLEANING: Final = "cleaning"
TASK_STATUS_ZONE_CLEANING: Final = "zone_cleaning"
TASK_STATUS_SEGMENT_CLEANING: Final = "room_cleaning"
TASK_STATUS_SPOT_CLEANING: Final = "spot_cleaning"
TASK_STATUS_FAST_MAPPING: Final = "fast_mapping"
TASK_STATUS_AUTO_CLEANING_PAUSE: Final = "cleaning_paused"
TASK_STATUS_SEGMENT_CLEANING_PAUSE: Final = "room_cleaning_paused"
TASK_STATUS_ZONE_CLEANING_PAUSE: Final = "zone_cleaning_paused"
TASK_STATUS_SPOT_CLEANING_PAUSE: Final = "spot_cleaning_paused"
TASK_STATUS_MAP_CLEANING_PAUSE: Final = "map_cleaning_paused"
TASK_STATUS_DOCKING_PAUSE: Final = "docking_paused"
TASK_STATUS_MOPPING_PAUSE: Final = "mopping_paused"
TASK_STATUS_ZONE_MOPPING_PAUSE: Final = "zone_mopping_paused"
TASK_STATUS_SEGMENT_MOPPING_PAUSE: Final = "room_mopping_paused"
TASK_STATUS_AUTO_MOPPING_PAUSE: Final = "mopping_paused"
TASK_STATUS_CRUISING_PATH: Final = "cruising_path"
TASK_STATUS_CRUISING_PATH_PAUSED: Final = "cruising_path_paused"
TASK_STATUS_CRUISING_POINT: Final = "cruising_point"
TASK_STATUS_CRUISING_POINT_PAUSED: Final = "cruising_point_paused"
TASK_STATUS_SUMMON_CLEAN_PAUSED: Final = "summon_clean_paused"
TASK_STATUS_RETURNING_INSTALL_MOP: Final = "returning_to_install_mop"
TASK_STATUS_RETURNING_REMOVE_MOP: Final = "returning_to_remove_mop"
TASK_STATUS_STATION_CLEANING: Final = "station_cleaning"
TASK_STATUS_PET_FINDING: Final = "pet_finding"
TASK_STATUS_AUTO_CLEANING_WASHING_PAUSED: Final = "auto_cleaning_washing_paused"
TASK_STATUS_AREA_CLEANING_WASHING_PAUSED: Final = "area_cleaning_washing_paused"
TASK_STATUS_CUSTOM_CLEANING_WASHING_PAUSED: Final = "custom_cleaning_washing_paused"
TASK_STATUS_PICKING_UP_ITEM: Final = "picking_up_item"
TASK_STATUS_PICKING_UP_ITEM_PAUSED: Final = "picking_up_item_paused"
TASK_STATUS_PICKING_UP_ITEM_SUCCESS: Final = "picking_up_item_success"
TASK_STATUS_REMOTE_PICKUP_INITIALIZING: Final = "remote_pickup_initializing"
TASK_STATUS_REMOTE_PICKUP_IDENTIFING: Final = "remote_pickup_identifing"
TASK_STATUS_MANUAL_REMOTE_PICKUP: Final = "manual_remote_pickup"
TASK_STATUS_AUTOMATIC_REMOTE_PICKUP: Final = "automatic_remote_pickup"
TASK_STATUS_REMOTE_PICKUP_IN_PROGRESS: Final = "remote_pickup_in_progress"
TASK_STATUS_REMOTE_PICKUP_PAUSED: Final = "remote_pickup_paused"
TASK_STATUS_PLACING_ITEM: Final = "placing_item"
TASK_STATUS_PLACING_ITEM_PAUSED: Final = "placing_item_paused"

STATUS_CLEANING: Final = "cleaning"
STATUS_FOLLOW_WALL: Final = "follow_wall_cleaning"
STATUS_CHARGING: Final = "charging"
STATUS_OTA: Final = "ota"
STATUS_FCT: Final = "fct"
STATUS_WIFI_SET: Final = "wifi_set"
STATUS_POWER_OFF: Final = "power_off"
STATUS_FACTORY: Final = "factory"
STATUS_ERROR: Final = "error"
STATUS_REMOTE_CONTROL: Final = "remote_control"
STATUS_SLEEP: Final = "sleeping"
STATUS_SELF_REPAIR: Final = "self_repair"
STATUS_FACTORY_FUNC_TEST: Final = "factory_test"
STATUS_STANDBY: Final = "standby"
STATUS_SEGMENT_CLEANING: Final = "room_cleaning"
STATUS_ZONE_CLEANING: Final = "zone_cleaning"
STATUS_SPOT_CLEANING: Final = "spot_cleaning"
STATUS_FAST_MAPPING: Final = "fast_mapping"
STATUS_CRUISING_PATH: Final = "cruising_path"
STATUS_CRUISING_POINT: Final = "cruising_point"
STATUS_SUMMON_CLEAN: Final = "summon_clean"
STATUS_SHORTCUT: Final = "shortcut"
STATUS_PERSON_FOLLOW: Final = "person_follow"
STATUS_WATER_CHECK: Final = "water_check"
STATUS_PET_GUARDING: Final = "pet_guarding"
STATUS_AUTO_ARRANGEMENT: Final = "auto_arrangement"
STATUS_SMART_ARRANGEMENT: Final = "smart_arrangement"
STATUS_ZONED_ARRANGEMENT: Final = "zoned_arrangement"

RELOCATION_STATUS_LOCATED: Final = "located"
RELOCATION_STATUS_LOCATING: Final = "locating"
RELOCATION_STATUS_FAILED: Final = "failed"
RELOCATION_STATUS_SUCESS: Final = "success"

CHARGING_STATUS_CHARGING: Final = "charging"
CHARGING_STATUS_NOT_CHARGING: Final = "not_charging"
CHARGING_STATUS_RETURN_TO_CHARGE: Final = "return_to_charge"
CHARGING_STATUS_CHARGING_COMPLETED: Final = "charging_completed"

DUST_COLLECTION_NOT_AVAILABLE: Final = "not_available"
DUST_COLLECTION_AVAILABLE: Final = "available"

AUTO_EMPTY_STATUS_ACTIVE: Final = "active"
AUTO_EMPTY_STATUS_NOT_PERFORMED: Final = "not_performed"

MAP_RECOVERY_STATUS_RUNNING: Final = "running"
MAP_RECOVERY_STATUS_SUCCESS: Final = "success"
MAP_RECOVERY_STATUS_FAIL: Final = "fail"

MAP_BACKUP_STATUS_RUNNING: Final = "running"
MAP_BACKUP_STATUS_SUCCESS: Final = "success"
MAP_BACKUP_STATUS_FAIL: Final = "fail"

SELF_WASH_BASE_STATUS_WASHING: Final = "washing"
SELF_WASH_BASE_STATUS_DRYING: Final = "drying"
SELF_WASH_BASE_STATUS_PAUSED: Final = "paused"
SELF_WASH_BASE_STATUS_RETURNING: Final = "returning"
SELF_WASH_BASE_STATUS_CLEAN_ADD_WATER: Final = "clean_add_water"
SELF_WASH_BASE_STATUS_ADDING_WATER: Final = "adding_water"

MOP_WASH_LEVEL_DEEP: Final = "deep"
MOP_WASH_LEVEL_DAILY: Final = "daily"
MOP_WASH_LEVEL_WATER_SAVING: Final = "water_saving"

MOP_CLEAN_FREQUENCY_BY_ROOM: Final = "by_room"
MOP_CLEAN_FREQUENCY_FIVE_SQUARE_METERS: Final = "5m²"
MOP_CLEAN_FREQUENCY_EIGHT_SQUARE_METERS: Final = "8m²"
MOP_CLEAN_FREQUENCY_TEN_SQUARE_METERS: Final = "10m²"
MOP_CLEAN_FREQUENCY_FIFTEEN_SQUARE_METERS: Final = "15m²"
MOP_CLEAN_FREQUENCY_TWENTY_SQUARE_METERS: Final = "20m²"
MOP_CLEAN_FREQUENCY_TWENTYFIVE_SQUARE_METERS: Final = "25m²"

MOPPING_TYPE_DEEP: Final = "deep"
MOPPING_TYPE_DAILY: Final = "daily"
MOPPING_TYPE_ACCURATE: Final = "accurate"

STREAM_STATUS_VIDEO: Final = "video"
STREAM_STATUS_AUDIO: Final = "audio"
STREAM_STATUS_RECORDING: Final = "recording"

VOICE_ASSISTANT_LANGUAGE_DEFAULT: Final = "default"
VOICE_ASSISTANT_LANGUAGE_ENGLISH: Final = "english"
VOICE_ASSISTANT_LANGUAGE_GERMAN: Final = "german"
VOICE_ASSISTANT_LANGUAGE_RUSSIAN: Final = "russian"
VOICE_ASSISTANT_LANGUAGE_ITALIAN: Final = "italian"
VOICE_ASSISTANT_LANGUAGE_FRENCH: Final = "french"
VOICE_ASSISTANT_LANGUAGE_KOREAN: Final = "korean"
VOICE_ASSISTANT_LANGUAGE_CHINESE: Final = "chinese"

WATER_TANK_INSTALLED: Final = "installed"
WATER_TANK_NOT_INSTALLED: Final = "not_installed"
WATER_TANK_MOP_INSTALLED: Final = "mop_installed"
WATER_TANK_MOP_IN_STATION: Final = "mop_in_station"

CARPET_SENSITIVITY_LOW: Final = "low"
CARPET_SENSITIVITY_MEDIUM: Final = "medium"
CARPET_SENSITIVITY_HIGH: Final = "high"

CARPET_CLEANING_AVOIDANCE: Final = "avoidance"
CARPET_CLEANING_ADAPTATION: Final = "adaptation"
CARPET_CLEANING_REMOVE_MOP: Final = "remove_mop"
CARPET_CLEANING_ADAPTATION_WITHOUT_ROUTE: Final = "adaptation_without_route"
CARPET_CLEANING_VACUUM_AND_MOP: Final = "vacuum_and_mop"
CARPET_CLEANING_IGNORE: Final = "ignore"
CARPET_CLEANING_CROSS: Final = "cross"

WIDER_CORNER_COVERAGE_LOW_FREQUENCY: Final = "low_frequency"
WIDER_CORNER_COVERAGE_HIGH_FREQUENCY: Final = "high_frequency"

MOP_PAD_SWING_AUTO: Final = "auto"
MOP_PAD_SWING_DAILY: Final = "daily"
MOP_PAD_SWING_WEEKLY: Final = "weekly"

MOP_EXTEND_FREQUENCY_STANDARD: Final = "standard"
MOP_EXTEND_FREQUENCY_INTELLIGENT: Final = "intelligent"
MOP_EXTEND_FREQUENCY_HIGH: Final = "high"

SECOND_CLEANING_IN_DEEP_MODE: Final = "in_deep_mode"
SECOND_CLEANING_IN_ALL_MODES: Final = "in_all_modes"

ROUTE_QUICK: Final = "quick"
ROUTE_STANDARD: Final = "standard"
ROUTE_INTENSIVE: Final = "intensive"
ROUTE_DEEP: Final = "deep"
ROUTE_OFF: Final = "off"

CLEANGENIUS_ROUTINE_CLEANING: Final = "routine_cleaning"
CLEANGENIUS_DEEP_CLEANING: Final = "deep_cleaning"

CLEANGENIUS_MODE_VACUUM_AND_MOP: Final = "vacuum_and_mop"
CLEANGENIUS_MODE_MOP_AFTER_VACUUM: Final = "mop_after_vacuum"

WASHING_MODE_LIGHT: Final = "light"
WASHING_MODE_STANDARD: Final = "standard"
WASHING_MODE_DEEP: Final = "deep"
WASHING_MODE_ULTRA_WASHING: Final = "ultra_washing"

WATER_TEMPERATURE_NORMAL: Final = "normal"
WATER_TEMPERATURE_MILD: Final = "mild"
WATER_TEMPERATURE_WARM: Final = "warm"
WATER_TEMPERATURE_HOT: Final = "hot"
WATER_TEMPERATURE_MAX: Final = "max"

SELF_CLEAN_FREQUENCY_BY_AREA: Final = "by_area"
SELF_CLEAN_FREQUENCY_BY_TIME: Final = "by_time"
SELF_CLEAN_FREQUENCY_BY_ROOM: Final = "by_room"
SELF_CLEAN_FREQUENCY_INTELLIGENT: Final = "intelligent"

AUTO_EMPTY_MODE_STANDARD: Final = "standard"
AUTO_EMPTY_MODE_HIGH_FREQUENCY: Final = "high_frequency"
AUTO_EMPTY_MODE_LOW_FREQUENCY: Final = "low_frequency"
AUTO_EMPTY_MODE_CUSTOM_FREQUENCY: Final = "custom_frequency"
AUTO_EMPTY_MODE_INTELLIGENT: Final = "intelligent"

FLOOR_MATERIAL_NONE: Final = "none"
FLOOR_MATERIAL_TILE: Final = "tile"
FLOOR_MATERIAL_WOOD: Final = "wood"
FLOOR_MATERIAL_MEDIUM_PILE_CARPET: Final = "medium_pile_carpet"
FLOOR_MATERIAL_LOW_PILE_CARPET: Final = "low_pile_carpet"
FLOOR_MATERIAL_CARPET: Final = "carpet"

FLOOR_MATERIAL_DIRECTION_VERTICAL: Final = "vertical"
FLOOR_MATERIAL_DIRECTION_HORIZONTAL: Final = "horizontal"

SEGMENT_VISIBILITY_VISIBLE: Final = "visible"
SEGMENT_VISIBILITY_HIDDEN: Final = "hidden"

DRAINAGE_STATUS_DRAINING: Final = "draining"
DRAINAGE_STATUS_DRAINING_SUCCESS: Final = "draining_successful"
DRAINAGE_STATUS_DRAINING_FAILED: Final = "draining_failed"

LOW_WATER_WARNING_NO_WARNING: Final = "no_warning"
LOW_WATER_WARNING_NO_WATER_LEFT: Final = "no_water_left"
LOW_WATER_WARNING_NO_WATER_LEFT_AFTER_CLEAN: Final = "no_water_left_after_clean"
LOW_WATER_WARNING_NO_WATER_FOR_CLEAN: Final = "no_water_for_clean"
LOW_WATER_WARNING_LOW_WATER: Final = "low_water"
LOW_WATER_WARNING_TANK_NOT_INSTALLED: Final = "tank_not_installed"

TASK_TYPE_STANDARD: Final = "standard"
TASK_TYPE_STANDARD_PAUSED: Final = "standard_paused"
TASK_TYPE_CUSTOM: Final = "custom"
TASK_TYPE_CUSTOM_PAUSED: Final = "custom_paused"
TASK_TYPE_SHORTCUT: Final = "shortcut"
TASK_TYPE_SHORTCUT_PAUSED: Final = "shortcut_paused"
TASK_TYPE_SCHEDULED: Final = "scheduled"
TASK_TYPE_SCHEDULED_PAUSED: Final = "scheduled_paused"
TASK_TYPE_SMART: Final = "smart"
TASK_TYPE_SMART_PAUSED: Final = "smart_paused"
TASK_TYPE_PARTIAL: Final = "partial"
TASK_TYPE_PARTIAL_PAUSED: Final = "partial_paused"
TASK_TYPE_SUMMON: Final = "summon"
TASK_TYPE_SUMMON_PAUSED: Final = "summon_paused"
TASK_TYPE_WATER_STAIN: Final = "water_stain"
TASK_TYPE_WATER_STAIN_PAUSED: Final = "water_stain_paused"
TASK_TYPE_BOOSTED_EDGE_CLEANING: Final = "boosted_edge_cleaning"
TASK_TYPE_HAIR_COMPRESSING: Final = "hair_compressing"
TASK_TYPE_LARGE_PARTICLE_CLEANING: Final = "large_particle_cleaning"
TASK_TYPE_INTENSIVE_STAIN_CLEANING: Final = "intensive_stain_cleaning"
TASK_TYPE_STAIN_CLEANING: Final = "stain_cleaning"
TASK_TYPE_INITIAL_DEEP_CLEANING: Final = "initial_deep_cleaning"
TASK_TYPE_INITIAL_DEEP_CLEANING_PAUSED: Final = "initial_deep_cleaning_paused"
TASK_TYPE_MOP_PAD_HEATING: Final = "mop_pad_heating"
TASK_TYPE_CLEANING_AFTER_MAPPING: Final = "cleaning_after_mapping"
TASK_TYPE_SMALL_PARTICLE_CLEANING: Final = "small_particle_cleaning"
TASK_TYPE_CHANGING_MOP: Final = "changing_mop"
TASK_TYPE_CHANGING_MOP_PAUSED: Final = "changing_mop_paused"
TASK_TYPE_FLOOR_MAINTAINING: Final = "floor_maintaining"
TASK_TYPE_FLOOR_MAINTAINING_PAUSED: Final = "floor_maintaining_paused"
TASK_TYPE_ARRANGING_ITEMS: Final = "arranging_items"
TASK_TYPE_ARRANGING_ITEMS_PAUSED: Final = "arranging_items_paused"
TASK_TYPE_INTENSIVE_HAIR_CLEANING: Final = "intensive_hair_cleaning"
TASK_TYPE_ACCESSORY_HANDLING: Final = "accessory_handling"
TASK_TYPE_INCREASED_DRUM_SPEED_CLEANING: Final = "increased_drum_speed_cleaning"
TASK_TYPE_PRESSURIZED_CLEANING: Final = "pressurized_cleaning"
TASK_TYPE_STEAM_CLEANING: Final = "steam_cleaning"
TASK_TYPE_STEAM_CLEANING_PAUSED: Final = "steam_cleaning_paused"

CLEAN_WATER_TANK_STATUS_INSTALLED: Final = "installed"
CLEAN_WATER_TANK_STATUS_NOT_INSTALLED: Final = "not_installed"
CLEAN_WATER_TANK_STATUS_LOW_WATER: Final = "low_water"

DIRTY_WATER_TANK_STATUS_INSTALLED: Final = "installed"
DIRTY_WATER_TANK_STATUS_NOT_INSTALLED_OR_FULL: Final = "not_installed_or_full"

DUST_BAG_STATUS_INSTALLED: Final = "installed"
DUST_BAG_STATUS_NOT_INSTALLED: Final = "not_installed"
DUST_BAG_STATUS_CHECK: Final = "check"

AUTO_LDS_COVERAGE_SECURITY: Final = "security"
AUTO_LDS_COVERAGE_EXTREME: Final = "extreme"

DETERGENT_STATUS_INSTALLED: Final = "installed"
DETERGENT_STATUS_DISABLED: Final = "disabled"
DETERGENT_STATUS_LOW_DETERGENT: Final = "low_detergent"

HOT_WATER_STATUS_DISABLED: Final = "disabled"
HOT_WATER_STATUS_ENABLED: Final = "enabled"

STATION_DRAINAGE_STATUS_DRAINING: Final = "draining"

ERROR_NO_ERROR: Final = "no_error"
ERROR_DROP: Final = "drop"
ERROR_CLIFF: Final = "cliff"
ERROR_BUMPER: Final = "bumper"
ERROR_GESTURE: Final = "gesture"
ERROR_BUMPER_REPEAT: Final = "bumper_repeat"
ERROR_DROP_REPEAT: Final = "drop_repeat"
ERROR_OPTICAL_FLOW: Final = "optical_flow"
ERROR_NO_BOX: Final = "no_box"
ERROR_NO_TANKBOX: Final = "no_tank_box"
ERROR_WATERBOX_EMPTY: Final = "water_box_empty"
ERROR_BOX_FULL: Final = "box_full"
ERROR_BRUSH: Final = "brush"
ERROR_SIDE_BRUSH: Final = "side_brush"
ERROR_FAN: Final = "fan"
ERROR_LEFT_WHEEL_MOTOR: Final = "left_wheel_motor"
ERROR_RIGHT_WHEEL_MOTOR: Final = "right_wheel_motor"
ERROR_TURN_SUFFOCATE: Final = "turn_suffocate"
ERROR_FORWARD_SUFFOCATE: Final = "forward_suffocate"
ERROR_CHARGER_GET: Final = "charger_get"
ERROR_BATTERY_LOW: Final = "battery_low"
ERROR_CHARGE_FAULT: Final = "charge_fault"
ERROR_BATTERY_PERCENTAGE: Final = "battery_percentage"
ERROR_HEART: Final = "heart"
ERROR_CAMERA_OCCLUSION: Final = "camera_occlusion"
ERROR_MOVE: Final = "move"
ERROR_FLOW_SHIELDING: Final = "flow_shielding"
ERROR_INFRARED_SHIELDING: Final = "infrared_shielding"
ERROR_CHARGE_NO_ELECTRIC: Final = "charge_no_electric"
ERROR_BATTERY_FAULT: Final = "battery_fault"
ERROR_FAN_SPEED_ERROR: Final = "fan_speed_error"
ERROR_LEFTWHELL_SPEED: Final = "left_wheell_speed"
ERROR_RIGHTWHELL_SPEED: Final = "right_wheell_speed"
ERROR_BMI055_ACCE: Final = "bmi055_acce"
ERROR_BMI055_GYRO: Final = "bmi055_gyro"
ERROR_XV7001: Final = "xv7001"
ERROR_LEFT_MAGNET: Final = "left_magnet"
ERROR_RIGHT_MAGNET: Final = "right_magnet"
ERROR_FLOW_ERROR: Final = "flow_error"
ERROR_INFRARED_FAULT: Final = "infrared_fault"
ERROR_CAMERA_FAULT: Final = "camera_fault"
ERROR_STRONG_MAGNET: Final = "strong_magnet"
ERROR_WATER_PUMP: Final = "water_pump"
ERROR_RTC: Final = "rtc"
ERROR_AUTO_KEY_TRIG: Final = "auto_key_trig"
ERROR_P3V3: Final = "p3v3"
ERROR_CAMERA_IDLE: Final = "camera_idle"
ERROR_BLOCKED: Final = "blocked"
ERROR_LDS_ERROR: Final = "lds_error"
ERROR_LDS_BUMPER: Final = "lds_bumper"
ERROR_FILTER_BLOCKED: Final = "filter_blocked"
ERROR_EDGE: Final = "edge"
ERROR_CARPET: Final = "carpet"
ERROR_LASER: Final = "laser"
ERROR_ULTRASONIC: Final = "ultrasonic"
ERROR_NO_GO_ZONE: Final = "no_go_zone"
ERROR_ROUTE: Final = "route"
ERROR_RESTRICTED: Final = "restricted"
ERROR_REMOVE_MOP: Final = "remove_mop"
ERROR_MOP_REMOVED: Final = "mop_removed"
ERROR_MOP_PAD_STOP_ROTATE: Final = "mop_pad_stop_rotate"
ERROR_MOP_INSTALL_FAILED: Final = "mop_install_failed"
ERROR_LOW_BATTERY_TURN_OFF: Final = "low_battery_turn_off"
ERROR_DIRTY_TANK_NOT_INSTALLED: Final = "dirty_tank_not_installed"
ERROR_ROBOT_IN_HIDDEN_ROOM: Final = "robot_in_hidden_room"
ERROR_LDS_FAILED_TO_LIFT: Final = "lds_failed_to_lift"
ERROR_ROBOT_STUCK: Final = "robot_stuck"
ERROR_SLIPPERY_FLOOR: Final = "slippery_floor"
ERROR_CHECK_MOP_INSTALL: Final = "check_mop_install"
ERROR_DIRTY_WATER_TANK_FULL: Final = "dirty_water_tank_full"
ERROR_RETRACTABLE_LEG_STUCK: Final = "retractable_leg_stuck"
ERROR_INTERNAL_ERROR: Final = "internal_error"
ERROR_ROBOT_STUCK_ON_TABLES: Final = "robot_stuck_on_tables"
ERROR_ROBOT_STUCK_ON_PASSAGE: Final = "robot_stuck_on_passage"
ERROR_ROBOT_STUCK_ON_THRESHOLD: Final = "robot_stuck_on_threshold"
ERROR_ROBOT_STUCK_ON_LOW_LYING_AREA: Final = "robot_stuck_on_low_lying_area"
ERROR_ROBOT_STUCK_ON_RAMP: Final = "robot_stuck_on_ramp"
ERROR_ROBOT_STUCK_ON_OBSTACLE: Final = "robot_stuck_on_obstacle"
ERROR_ROBOT_STUCK_ON_PET: Final = "robot_stuck_on_pet"
ERROR_ROBOT_STUCK_ON_SLIPPERY_SURFACE: Final = "robot_stuck_on_slippery_surface"
ERROR_ROBOT_STUCK_ON_CARPET: Final = "robot_stuck_on_carpet"
ERROR_BIN_FULL: Final = "bin_full"
ERROR_BIN_OPEN: Final = "bin_open"
ERROR_WATER_TANK: Final = "water_tank"
ERROR_DIRTY_WATER_TANK: Final = "dirty_water_tank"
ERROR_WATER_TANK_DRY: Final = "water_tank_dry"
ERROR_DIRTY_WATER_TANK_BLOCKED: Final = "dirty_water_tank_blocked"
ERROR_DIRTY_WATER_TANK_PUMP: Final = "dirty_water_tank_pump"
ERROR_MOP_PAD: Final = "mop_pad"
ERROR_WET_MOP_PAD: Final = "wet_mop_pad"
ERROR_CLEAN_MOP_PAD: Final = "clean_mop_pad"
ERROR_CLEAN_TANK_LEVEL: Final = "clean_tank_level"
ERROR_STATION_DISCONNECTED: Final = "station_disconnected"
ERROR_DIRTY_TANK_LEVEL: Final = "dirty_tank_level"
ERROR_WASHBOARD_LEVEL: Final = "washboard_level"
ERROR_NO_MOP_IN_STATION: Final = "no_mop_in_station"
ERROR_DUST_BAG_FULL: Final = "dust_bag_full"
ERROR_SELF_TEST_FAILED: Final = "self_test_failed"
ERROR_WASHBOARD_NOT_WORKING: Final = "washboard_not_working"
ERROR_DRAINAGE_FAILED: Final = "drainage_failed"
ERROR_MOP_NOT_DETECTED: Final = "mop_not_detected"
ERROR_MOP_HOLDER_ERROR: Final = "mop_holder_error"
ERROR_DOCK_ERROR: Final = "dock_error"
ERROR_WASH_FAILED: Final = "wash_failed"
ERROR_ROBOT_STUCK_ON_CURTAIN: Final = "robot_stuck_on_curtain"
ERROR_EDGE_MOP_STOP_ROTATE: Final = "edge_mop_stop_rotate"
ERROR_EDGE_MOP_DETACHED: Final = "edge_mop_detached"
ERROR_CHASSIS_LIFT_MALFUNCTION: Final = "chassis_lift_malfunction"
ERROR_MOP_COVER_ERROR: Final = "mop_cover_error"
ERROR_ROLLER_MOP_ERROR: Final = "roller_mop_error"
ERROR_ONBOARD_WATER_TANK_EMPTY: Final = "onboard_water_tank_empty"
ERROR_ONBOARD_DIRTY_WATER_TANK_FULL: Final = "onboard_dirty_water_tank_full"
ERROR_MOP_NOT_INSTALLED: Final = "mop_not_installed"
ERROR_FLUFFING_ROLLER_ERROR: Final = "fluffing_roller_error"
ERROR_BLOCKED_BY_OBSTACLE: Final = "blocked_by_obstacle"
ERROR_RETURN_TO_CHARGE_FAILED: Final = "return_to_charge_failed"
ERROR_ROBOTIC_ARM_STOPPED: Final = "robotic_arm_stopped"
ERROR_DRAINAGE_OUTLET_FILTER: Final = "drainage_outlet_filter"
ERROR_MAIN_WHEELS_ERROR: Final = "main_wheels_error"

ATTR_VALUE: Final = "value"
ATTR_CHARGING: Final = "charging"
ATTR_DOCKED: Final = "docked"
ATTR_LOCATED: Final = "located"
ATTR_STARTED: Final = "started"
ATTR_FAULTS: Final = "faults"
ATTR_HAS_ERROR: Final = "has_error"
ATTR_PAUSED: Final = "paused"
ATTR_RUNNING: Final = "running"
ATTR_RETURNING_PAUSED: Final = "returning_paused"
ATTR_RETURNING: Final = "returning"
ATTR_MAPPING: Final = "mapping"
ATTR_MAPPING_AVAILABLE: Final = "mapping_available"
ATTR_WASHING_AVAILABLE: Final = "washing_available"
ATTR_RETURNING_TO_WASH: Final = "returning_to_wash"
ATTR_RETURNING_TO_WASH_PAUSED: Final = "returning_to_wash_paused"
ATTR_DRYING_AVAILABLE: Final = "drying_available"
ATTR_DUST_BAG_DRYING_AVAILABLE: Final = "dust_bag_drying_available"
ATTR_DRAINING_AVAILABLE: Final = "draining_available"
ATTR_DRYING_LEFT: Final = "drying_left"
ATTR_DUST_COLLECTION_AVAILABLE: Final = "dust_collection_available"
ATTR_ROOMS: Final = "rooms"
ATTR_MAPS: Final = "maps"
ATTR_MAP_COUNT: Final = "map_count"
ATTR_CURRENT_SEGMENT: Final = "current_segment"
ATTR_SELECTED_MAP: Final = "selected_map"
ATTR_SELECTED_MAP_ID: Final = "selected_map_id"
ATTR_SELECTED_MAP_INDEX: Final = "selected_map_index"
ATTR_ID: Final = "id"
ATTR_DATE: Final = "date"
ATTR_INDEX: Final = "index"
ATTR_NAME: Final = "name"
ATTR_CUSTOM_NAME: Final = "custom_name"
ATTR_RECOVERY_MAP: Final = "recovery_map"
ATTR_ICON: Final = "icon"
ATTR_TYPE: Final = "type"
ATTR_ORDER: Final = "order"
ATTR_DID: Final = "did"
ATTR_STATUS: Final = "status"
ATTR_CLEANING_MODE: Final = "cleaning_mode"
ATTR_SUCTION_LEVEL: Final = "suction_level"
ATTR_WASHING_MODE: Final = "washing_mode"
ATTR_WATER_TANK: Final = "water_tank"
ATTR_COMPLETED: Final = "completed"
ATTR_TIMESTAMP: Final = "timestamp"
ATTR_CLEANING_TIME: Final = "cleaning_time"
ATTR_CLEANED_AREA: Final = "cleaned_area"
ATTR_MOP_PAD_HUMIDITY: Final = "mop_pad_humidity"
ATTR_SELF_CLEAN_AREA: Final = "self_clean_area"
ATTR_SELF_CLEAN_AREA_MIN: Final = "self_clean_area_min"
ATTR_SELF_CLEAN_AREA_MAX: Final = "self_clean_area_max"
ATTR_SELF_CLEAN_AREA_DEFAULT: Final = "self_clean_area_default"
ATTR_PREVIOUS_SELF_CLEAN_AREA: Final = "previous_self_clean_area"
ATTR_SELF_CLEAN_TIME: Final = "self_clean_time"
ATTR_PREVIOUS_SELF_CLEAN_TIME: Final = "previous_self_clean_time"
ATTR_SELF_CLEAN_TIME_MIN: Final = "self_clean_time_min"
ATTR_SELF_CLEAN_TIME_MAX: Final = "self_clean_time_max"
ATTR_SELF_CLEAN_TIME_DEFAULT: Final = "self_clean_time_default"
ATTR_MOP_CLEAN_FREQUENCY: Final = "mop_clean_frequency"
ATTR_MOP_PAD: Final = "mop_pad"
ATTR_BATTERY: Final = "battery"
ATTR_CLEANING_SEQUENCE: Final = "cleaning_sequence"
ATTR_WASHING: Final = "washing"
ATTR_WASHING_PAUSED: Final = "washing_paused"
ATTR_DRYING: Final = "drying"
ATTR_DRAINING: Final = "draining"
ATTR_CLEANGENIUS: Final = "cleangenius_cleaning"
ATTR_WETNESS_LEVEL: Final = "wetness_level"
ATTR_OFF_PEAK_CHARGING: Final = "off_peak_charging"
ATTR_OFF_PEAK_CHARGING_START: Final = "off_peak_charging_start"
ATTR_OFF_PEAK_CHARGING_END: Final = "off_peak_charging_end"
ATTR_LOW_WATER: Final = "low_water"
ATTR_VACUUM_STATE: Final = "vacuum_state"
ATTR_DND: Final = "dnd"
ATTR_SHORTCUTS: Final = "shortcuts"
ATTR_CRUISING_TIME: Final = "cruising_time"
ATTR_CRUISING_TYPE: Final = "cruising_type"
ATTR_MAP_INDEX: Final = "map_index"
ATTR_MAP_NAME: Final = "map_name"
ATTR_CALIBRATION: Final = "calibration_points"
ATTR_SELECTED: Final = "selected"
ATTR_CLEANING_HISTORY_PICTURE: Final = "cleaning_history_picture"
ATTR_CRUISING_HISTORY_PICTURE: Final = "cruising_history_picture"
ATTR_OBSTACLE_PICTURE: Final = "obstacle_picture"
ATTR_RECOVERY_MAP_PICTURE: Final = "recovery_map_picture"
ATTR_RECOVERY_MAP_FILE: Final = "recovery_map_file"
ATTR_WIFI_MAP_PICTURE: Final = "wifi_map_picture"
ATTR_BLOCKED_SEGMENTS: Final = "blocked_rooms"
ATTR_INTERRUPT_REASON: Final = "interrupt_reason"
ATTR_MULTIPLE_CLEANING_TIME: Final = "multiple_cleaning_time"
ATTR_PET: Final = "pet"
ATTR_CLEANUP_METHOD: Final = "cleanup_method"
ATTR_SEGMENT_CLEANING: Final = "segment_cleaning"
ATTR_ZONE_CLEANING: Final = "zone_cleaning"
ATTR_SPOT_CLEANING: Final = "spot_cleaning"
ATTR_CRUSING: Final = "cruising"
ATTR_HAS_SAVED_MAP: Final = "has_saved_map"
ATTR_HAS_TEMPORARY_MAP: Final = "has_temporary_map"
ATTR_AUTO_EMPTY_MODE: Final = "auto_empty_mode"
ATTR_CARPET_AVOIDANCE: Final = "carpet_avoidance"
ATTR_FLOOR_DIRECTION_CLEANING_AVAILABLE: Final = "floor_direction_cleaning_available"
ATTR_SHORTCUT_TASK: Final = "shortcut_task"
ATTR_FIRMWARE_VERSION: Final = "firmware_version"
ATTR_AP: Final = "ap"
ATTR_MAP_ID: Final = "map_id"
ATTR_SAVED_MAP_ID: Final = "saved_map_id"
ATTR_COLOR_SCHEME: Final = "color_scheme"
ATTR_CAPABILITIES: Final = "capabilities"
ATTR_LAST_UPDATED_TIME: Final = "last_updated_time"

MAP_PARAMETER_NAME: Final = "name"
MAP_PARAMETER_VALUE: Final = "value"
MAP_PARAMETER_TIME: Final = "time"
MAP_PARAMETER_CODE: Final = "code"
MAP_PARAMETER_OUT: Final = "out"
MAP_PARAMETER_MAP: Final = "map"
MAP_PARAMETER_ANGLE: Final = "angle"
MAP_PARAMETER_MAPSTR: Final = "mapstr"
MAP_PARAMETER_CURR_ID: Final = "curr_id"
MAP_PARAMETER_VACUUM: Final = "vacuum"
MAP_PARAMETER_URL: Final = "url"
MAP_PARAMETER_EXPIRES_TIME: Final = "expires_time"

MAP_REQUEST_PARAMETER_MAP_ID: Final = "map_id"
MAP_REQUEST_PARAMETER_FRAME_ID: Final = "frame_id"
MAP_REQUEST_PARAMETER_FRAME_TYPE: Final = "frame_type"
MAP_REQUEST_PARAMETER_REQ_TYPE: Final = "req_type"
MAP_REQUEST_PARAMETER_FORCE_TYPE: Final = "force_type"
MAP_REQUEST_PARAMETER_TYPE: Final = "type"
MAP_REQUEST_PARAMETER_INDEX: Final = "index"
MAP_REQUEST_PARAMETER_ROOM_ID: Final = "roomID"

MAP_DATA_JSON_CLASS: Final = "ValetudoMap"
MAP_DATA_JSON_PARAMETER_CLASS: Final = "__class"
MAP_DATA_JSON_PARAMETER_SIZE: Final = "size"
MAP_DATA_JSON_PARAMETER_X: Final = "x"
MAP_DATA_JSON_PARAMETER_Y: Final = "y"
MAP_DATA_JSON_PARAMETER_PIXEL_SIZE: Final = "pixelSize"
MAP_DATA_JSON_PARAMETER_LAYERS: Final = "layers"
MAP_DATA_JSON_PARAMETER_ENTITIES: Final = "entities"
MAP_DATA_JSON_PARAMETER_META_DATA: Final = "metaData"
MAP_DATA_JSON_PARAMETER_VERSION: Final = "version"
MAP_DATA_JSON_PARAMETER_ROTATION: Final = "rotation"
MAP_DATA_JSON_PARAMETER_TYPE: Final = "type"
MAP_DATA_JSON_PARAMETER_POINTS: Final = "points"
MAP_DATA_JSON_PARAMETER_PIXELS: Final = "pixels"
MAP_DATA_JSON_PARAMETER_SEGMENT_ID: Final = "segmentId"
MAP_DATA_JSON_PARAMETER_ACTIVE: Final = "active"
MAP_DATA_JSON_PARAMETER_NAME: Final = "name"
MAP_DATA_JSON_PARAMETER_DIMENSIONS: Final = "dimensions"
MAP_DATA_JSON_PARAMETER_MIN: Final = "min"
MAP_DATA_JSON_PARAMETER_MAX: Final = "max"
MAP_DATA_JSON_PARAMETER_MID: Final = "mid"
MAP_DATA_JSON_PARAMETER_AVG: Final = "avg"
MAP_DATA_JSON_PARAMETER_PIXEL_COUNT: Final = "pixelCount"
MAP_DATA_JSON_PARAMETER_COMPRESSED_PIXELS: Final = "compressedPixels"
MAP_DATA_JSON_PARAMETER_ROBOT_POSITION: Final = "robot_position"
MAP_DATA_JSON_PARAMETER_CHARGER_POSITION: Final = "charger_location"
MAP_DATA_JSON_PARAMETER_NO_MOP_AREA: Final = "no_mop_area"
MAP_DATA_JSON_PARAMETER_NO_GO_AREA: Final = "no_go_area"
MAP_DATA_JSON_PARAMETER_ACTIVE_ZONE: Final = "active_zone"
MAP_DATA_JSON_PARAMETER_VIRTUAL_WALL: Final = "virtual_wall"
MAP_DATA_JSON_PARAMETER_PATH: Final = "path"
MAP_DATA_JSON_PARAMETER_FLOOR: Final = "floor"
MAP_DATA_JSON_PARAMETER_WALL: Final = "wall"
MAP_DATA_JSON_PARAMETER_SEGMENT: Final = "segment"

DEVICE_INFO: Final = (
    "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"
)

PROPERTY_TO_NAME: Final = {
    DreameVacuumProperty.STATE.name: ["state", "State"],
    DreameVacuumProperty.ERROR.name: ["error", "Error"],
    DreameVacuumProperty.BATTERY_LEVEL.name: ["battery_level", "Battery Level"],
    DreameVacuumProperty.CHARGING_STATUS.name: ["charging_status", "Charging Status"],
    DreameVacuumProperty.OFF_PEAK_CHARGING.name: [
        "off_peak_charging",
        "Off-Peak Charging",
    ],
    DreameVacuumProperty.STATUS.name: ["status", "Status"],
    DreameVacuumProperty.CLEANING_TIME.name: ["cleaning_time", "Cleaning Time"],
    DreameVacuumProperty.CLEANED_AREA.name: ["cleaned_area", "Cleaned Area"],
    DreameVacuumProperty.SUCTION_LEVEL.name: ["suction_level", "Suction Level"],
    DreameVacuumProperty.WATER_VOLUME.name: ["water_volume", "Water Volume"],
    DreameVacuumProperty.WATER_TANK.name: ["water_tank", "Water Tank"],
    DreameVacuumProperty.TASK_STATUS.name: ["task_status", "Task Status"],
    DreameVacuumProperty.RESUME_CLEANING.name: ["resume_cleaning", "Resume Cleaning"],
    DreameVacuumProperty.CARPET_BOOST.name: ["carpet_boost", "Carpet Boost"],
    DreameVacuumProperty.REMOTE_CONTROL.name: ["remote_control", "Remote Control"],
    DreameVacuumProperty.MOP_CLEANING_REMAINDER.name: [
        "mop_cleaning_remainder",
        "Mop Cleaning Remainder",
    ],
    DreameVacuumProperty.CLEANING_PAUSED.name: ["cleaning_paused", "Cleaning Paused"],
    DreameVacuumProperty.FAULTS.name: ["faults", "Faults"],
    DreameVacuumProperty.RELOCATION_STATUS.name: [
        "relocation_status",
        "Relocation Status",
    ],
    DreameVacuumProperty.OBSTACLE_AVOIDANCE.name: [
        "obstacle_avoidance",
        "Obstacle Avoidance",
    ],
    DreameVacuumProperty.AI_DETECTION.name: [
        "ai_obstacle_detection",
        "AI Obstacle Detection",
    ],
    DreameVacuumProperty.CLEANING_MODE.name: ["cleaning_mode", "Cleaning Mode"],
    DreameVacuumProperty.SELF_WASH_BASE_STATUS.name: [
        "self_wash_base_status",
        "Self-Wash Base Status",
    ],
    DreameVacuumProperty.CUSTOMIZED_CLEANING.name: [
        "customized_cleaning",
        "Customized Cleaning",
    ],
    DreameVacuumProperty.CHILD_LOCK.name: ["child_lock", "Child Lock"],
    DreameVacuumProperty.CARPET_SENSITIVITY.name: [
        "carpet_sensitivity",
        "Carpet Sensitivity",
    ],
    DreameVacuumProperty.TIGHT_MOPPING.name: ["tight_mopping", "Tight Mopping"],
    DreameVacuumProperty.CLEANING_CANCEL.name: ["cleaning_cancel", "Cleaning Cancel"],
    DreameVacuumProperty.CARPET_RECOGNITION.name: [
        "carpet_recognition",
        "Carpet Recognition",
    ],
    DreameVacuumProperty.SELF_CLEAN.name: ["self_clean", "Self-Clean"],
    DreameVacuumProperty.WARN_STATUS.name: ["warn_status", "Warn Status"],
    DreameVacuumProperty.CARPET_CLEANING.name: ["carpet_cleaning", "Carpet Cleaning"],
    DreameVacuumProperty.AUTO_ADD_DETERGENT.name: [
        "auto_add_detergent",
        "Auto-Add Detergent",
    ],
    DreameVacuumProperty.DRYING_TIME.name: ["drying_time", "Drying Time"],
    DreameVacuumProperty.MULTI_FLOOR_MAP.name: ["multi_floor_map", "Multi Floor Map"],
    DreameVacuumProperty.MAP_LIST.name: ["map_list", "Map List"],
    DreameVacuumProperty.RECOVERY_MAP_LIST.name: [
        "recovery_map_list",
        "Recovery Map List",
    ],
    DreameVacuumProperty.MAP_RECOVERY.name: ["map_recovery", "Map Recovery"],
    DreameVacuumProperty.MAP_RECOVERY_STATUS.name: [
        "map_recovery_status",
        "Map Recovery Status",
    ],
    DreameVacuumProperty.VOLUME.name: ["volume", "Volume"],
    DreameVacuumProperty.VOICE_ASSISTANT.name: ["voice_assistant", "Voice Assistant"],
    DreameVacuumProperty.SCHEDULE.name: ["schedule", "Schedule"],
    DreameVacuumProperty.AUTO_DUST_COLLECTING.name: [
        "auto_dust_collecting",
        "Auto Dust Collecting",
    ],
    DreameVacuumProperty.AUTO_EMPTY_FREQUENCY.name: [
        "auto_empty_frequency",
        "Auto Empty Frequency",
    ],
    DreameVacuumProperty.MAP_SAVING.name: [
        "map_saving",
        "Map Saving",
    ],
    DreameVacuumProperty.DUST_COLLECTION.name: ["dust_collection", "Dust Collection"],
    DreameVacuumProperty.AUTO_EMPTY_STATUS.name: [
        "auto_empty_status",
        "Auto Empty Status",
    ],
    DreameVacuumProperty.SERIAL_NUMBER.name: ["serial_number", "Serial Number"],
    DreameVacuumProperty.VOICE_PACKET_ID.name: ["voice_packet_id", "Voice Packet Id"],
    DreameVacuumProperty.TIMEZONE.name: ["timezone", "Timezone"],
    DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT.name: [
        "main_brush_time_left",
        "Main Brush  Time Left",
    ],
    DreameVacuumProperty.MAIN_BRUSH_LEFT.name: ["main_brush_left", "Main Brush Left"],
    DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT.name: [
        "side_brush_time_left",
        "Side Brush Time Left",
    ],
    DreameVacuumProperty.SIDE_BRUSH_LEFT.name: ["side_brush_left", "Side Brush Left"],
    DreameVacuumProperty.FILTER_LEFT.name: ["filter_left", "Filter Left"],
    DreameVacuumProperty.FILTER_TIME_LEFT.name: [
        "filter_time_left",
        "Filter Time Left",
    ],
    DreameVacuumProperty.FIRST_CLEANING_DATE.name: [
        "first_cleaning_date",
        "First Cleaning Date",
    ],
    DreameVacuumProperty.TOTAL_CLEANING_TIME.name: [
        "total_cleaning_time",
        "Total Cleaning Time",
    ],
    DreameVacuumProperty.CLEANING_COUNT.name: ["cleaning_count", "Cleaning Count"],
    DreameVacuumProperty.TOTAL_CLEANED_AREA.name: [
        "total_cleaned_area",
        "Total Cleaned Area",
    ],
    DreameVacuumProperty.TOTAL_RUNTIME.name: [
        "total_runtime",
        "Total Runtime",
    ],
    DreameVacuumProperty.TOTAL_CRUISE_TIME.name: [
        "total_cruise_time",
        "Total Cruise Time",
    ],
    DreameVacuumProperty.SENSOR_DIRTY_LEFT.name: [
        "sensor_dirty_left",
        "Sensor Dirty Left",
    ],
    DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT.name: [
        "sensor_dirty_time_left",
        "Sensor Dirty Time Left",
    ],
    DreameVacuumProperty.TANK_FILTER_LEFT.name: [
        "tank_filter_left",
        "Tank Filter Left",
    ],
    DreameVacuumProperty.TANK_FILTER_TIME_LEFT.name: [
        "tank_filter_time_left",
        "Tank Filter Time Left",
    ],
    DreameVacuumProperty.MOP_PAD_LEFT.name: ["mop_pad_left", "Mop Pad Left"],
    DreameVacuumProperty.MOP_PAD_TIME_LEFT.name: [
        "mop_pad_time_left",
        "Mop Pad Time Left",
    ],
    DreameVacuumProperty.SILVER_ION_LEFT.name: ["silver_ion_left", "Silver-ion Left"],
    DreameVacuumProperty.SILVER_ION_TIME_LEFT.name: [
        "silver_ion_time_left",
        "Silver-ion Time Left",
    ],
    DreameVacuumProperty.DETERGENT_LEFT.name: ["detergent_left", "Detergent Left"],
    DreameVacuumProperty.DETERGENT_TIME_LEFT.name: [
        "detergent_time_left",
        "Detergent Time Left",
    ],
    DreameVacuumProperty.SQUEEGEE_LEFT.name: ["squeegee_left", "Squeegee Left"],
    DreameVacuumProperty.SQUEEGEE_TIME_LEFT.name: [
        "squeegee_time_left",
        "Squeegee Time Left",
    ],
    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT.name: [
        "onboard_dirty_water_tank_left",
        "Onboard Dirty Water Tank Left",
    ],
    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT.name: [
        "onboard_dirty_water_tank_time_left",
        "Onboard Dirty Water Tank Time Left",
    ],
    DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_LEFT.name: [
        "DIRTY_WATER_CHANNEL_DIRTY_left",
        "Dirty Water Channel Left",
    ],
    DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_TIME_LEFT.name: [
        "DIRTY_WATER_CHANNEL_DIRTY_time_left",
        "Dirty Water Channel Time Left",
    ],
    DreameVacuumProperty.DEODORIZER_LEFT.name: [
        "deodorizer_left",
        "Deodorizer Left",
    ],
    DreameVacuumProperty.DEODORIZER_TIME_LEFT.name: [
        "deodorizer_time_left",
        "Deodorizer Time Left",
    ],
    DreameVacuumProperty.WHEEL_DIRTY_LEFT.name: [
        "wheel_dirty_left",
        "Wheel Dirty Left",
    ],
    DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT.name: [
        "wheel_dirty_time_left",
        "Wheel Dirty Time Left",
    ],
    DreameVacuumProperty.SCALE_INHIBITOR_LEFT.name: [
        "scale_inhibitor_left",
        "Scale Inhibitor Left",
    ],
    DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT.name: [
        "scale_inhibitor_time_left",
        "Scale Inhibitor Time Left",
    ],
    DreameVacuumProperty.CLEANGENIUS_MODE.name: [
        "cleangenius_mode",
        "CleanGenius Mode",
    ],
    DreameVacuumProperty.DND_DISABLE_RESUME_CLEANING.name: [
        "dnd_disable_resume_cleaning",
        "DnD Disable Resume Cleaning",
    ],
    DreameVacuumProperty.DND_DISABLE_AUTO_EMPTY.name: [
        "dnd_disable_auto_empty",
        "DnD Disable Auto Empty",
    ],
    DreameVacuumProperty.DND_REDUCE_VOLUME.name: [
        "dnd_reduce_volume",
        "DnD Reduce Volume",
    ],
    DreameVacuumAIProperty.AI_FURNITURE_DETECTION.name: [
        "ai_furniture_detection",
        "AI Furniture Detection",
    ],
    DreameVacuumAIProperty.AI_OBSTACLE_DETECTION.name: [
        "ai_obstacle_detection",
        "AI Obstacle Detection",
    ],
    DreameVacuumAIProperty.AI_OBSTACLE_PICTURE.name: [
        "ai_obstacle_picture",
        "AI Obstacle Picture",
    ],
    DreameVacuumAIProperty.AI_FLUID_DETECTION.name: [
        "ai_fluid_detection",
        "AI Fluid Detection",
    ],
    DreameVacuumAIProperty.AI_PET_DETECTION.name: [
        "ai_pet_detection",
        "AI Pet Detection",
    ],
    DreameVacuumAIProperty.AI_OBSTACLE_IMAGE_UPLOAD.name: [
        "ai_obstacle_image_upload",
        "AI Obstacle Image Upload",
    ],
    DreameVacuumAIProperty.AI_IMAGE.name: ["ai_image", "AI Image"],
    DreameVacuumAIProperty.AI_PET_AVOIDANCE.name: [
        "ai_pet_avoidance",
        "AI Pet Avoidance",
    ],
    DreameVacuumAIProperty.FUZZY_OBSTACLE_DETECTION.name: [
        "fuzzy_obstacle_detection",
        "Fuzzy Obstacle Detection",
    ],
    DreameVacuumAIProperty.PET_PICTURE.name: ["pet_picture", "Pet Picture"],
    DreameVacuumAIProperty.PET_FOCUSED_DETECTION.name: [
        "pet_focused_detection",
        "Pet Focused Detection",
    ],
    DreameVacuumAIProperty.LARGE_PARTICLES_BOOST.name: [
        "large_particles_boost",
        "Large Particles Boost",
    ],
    DreameVacuumStrAIProperty.AI_HUMAN_DETECTION.name: [
        "ai_human_detection",
        "AI Human Detection",
    ],
    DreameVacuumAutoSwitchProperty.COLLISION_AVOIDANCE.name: [
        "collision_avoidance",
        "Collision Avoidance",
    ],
    DreameVacuumAutoSwitchProperty.FILL_LIGHT.name: ["fill_light", "Fill Light"],
    DreameVacuumAutoSwitchProperty.AUTO_DRYING.name: ["auto_drying", "Auto Drying"],
    DreameVacuumAutoSwitchProperty.STAIN_AVOIDANCE.name: [
        "stain_avoidance",
        "Stain Avoidance",
    ],
    DreameVacuumAutoSwitchProperty.MOPPING_TYPE.name: ["mopping_type", "Mopping Type"],
    DreameVacuumAutoSwitchProperty.CLEANGENIUS.name: [
        "cleangenius",
        "CleanGenius",
    ],
    DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE.name: [
        "wider_corner_coverage",
        "Wider Corner Coverage",
    ],
    DreameVacuumAutoSwitchProperty.FLOOR_DIRECTION_CLEANING.name: [
        "floor_direction_cleaning",
        "Floor Direction Cleaning",
    ],
    DreameVacuumAutoSwitchProperty.PET_FOCUSED_CLEANING.name: [
        "pet_focused_cleaning",
        "Pet Focused Cleaning",
    ],
    DreameVacuumAutoSwitchProperty.AUTO_RECLEANING.name: [
        "auto_recleaning",
        "Auto Re-Cleaning",
    ],
    DreameVacuumAutoSwitchProperty.AUTO_REWASHING.name: [
        "auto_rewashing",
        "Auto Re-Washing",
    ],
    DreameVacuumAutoSwitchProperty.MOP_PAD_SWING.name: [
        "mop_pad_swing",
        "Mop Pad Swing",
    ],
    DreameVacuumAutoSwitchProperty.MOP_EXTEND.name: [
        "mop_extend",
        "Mop Extend",
    ],
    DreameVacuumAutoSwitchProperty.MOP_EXTEND_FREQUENCY.name: [
        "mop_extend_frequency",
        "Mop Extend Frequency",
    ],
    DreameVacuumAutoSwitchProperty.HUMAN_FOLLOW.name: ["human_follow", "Human Follow"],
    DreameVacuumAutoSwitchProperty.MAX_SUCTION_POWER.name: [
        "max_suction_power",
        "Max Suction Power",
    ],
    DreameVacuumAutoSwitchProperty.SMART_DRYING.name: ["smart_drying", "Smart Drying"],
    DreameVacuumAutoSwitchProperty.DRAINAGE_CONFIRM_RESULT.name: [
        "drainage_confirm_result",
        "Drainage Confirm Result",
    ],
    DreameVacuumAutoSwitchProperty.DRAINAGE_TEST_RESULT.name: [
        "drainage_test_result",
        "Drainage Test Result",
    ],
    DreameVacuumAutoSwitchProperty.HOT_WASHING.name: ["hot_washing", "Hot Washing"],
    DreameVacuumAutoSwitchProperty.UV_STERILIZATION.name: [
        "uv_sterilization",
        "UV Sterilization",
    ],
}

ACTION_TO_NAME: Final = {
    DreameVacuumAction.START: ["start", "Start"],
    DreameVacuumAction.PAUSE: ["pause", "Pause"],
    DreameVacuumAction.CHARGE: ["charge", "Charge"],
    DreameVacuumAction.START_CUSTOM: ["start_custom", "Start Custom"],
    DreameVacuumAction.STOP: ["stop", "Stop"],
    DreameVacuumAction.CLEAR_WARNING: ["clear_warning", "Clear Warning"],
    DreameVacuumAction.REQUEST_MAP: ["request_map", "Request Map"],
    DreameVacuumAction.UPDATE_MAP_DATA: ["update_map_data", "Update Map Data"],
    DreameVacuumAction.LOCATE: ["locate", "Locate"],
    DreameVacuumAction.PLAY_SOUND: ["play_sound", "Play Sound"],
    DreameVacuumAction.RESET_MAIN_BRUSH: ["reset_main_brush", "Reset Main Brush"],
    DreameVacuumAction.RESET_SIDE_BRUSH: ["reset_side_brush", "Reset Side Brush"],
    DreameVacuumAction.RESET_FILTER: ["reset_filter", "Reset Filter"],
    DreameVacuumAction.RESET_SENSOR: ["reset_sensor", "Reset Sensor"],
    DreameVacuumAction.START_AUTO_EMPTY: ["start_auto_empty", "Start Auto Empty"],
    DreameVacuumAction.RESET_MOP_PAD: ["reset_mop_pad", "Reset Mop Pad"],
    DreameVacuumAction.RESET_SILVER_ION: ["reset_silver_ion", "Reset Silver-ion"],
    DreameVacuumAction.RESET_DETERGENT: ["reset_detergent", "Reset Detergent"],
}

STATE_CODE_TO_STATE: Final = {
    DreameVacuumState.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumState.SWEEPING: STATE_SWEEPING,
    DreameVacuumState.IDLE: STATE_IDLE,
    DreameVacuumState.PAUSED: STATE_PAUSED,
    DreameVacuumState.ERROR: STATE_ERROR,
    DreameVacuumState.RETURNING: STATE_RETURNING,
    DreameVacuumState.CHARGING: STATE_CHARGING,
    DreameVacuumState.MOPPING: STATE_MOPPING,
    DreameVacuumState.DRYING: STATE_DRYING,
    DreameVacuumState.WASHING: STATE_WASHING,
    DreameVacuumState.RETURNING_TO_WASH: STATE_RETURNING_WASH,
    DreameVacuumState.BUILDING: STATE_BUILDING,
    DreameVacuumState.SWEEPING_AND_MOPPING: STATE_SWEEPING_AND_MOPPING,
    DreameVacuumState.CHARGING_COMPLETED: STATE_CHARGING_COMPLETED,
    DreameVacuumState.UPGRADING: STATE_UPGRADING,
    DreameVacuumState.CLEAN_SUMMON: STATE_CLEAN_SUMMON,
    DreameVacuumState.STATION_RESET: STATE_STATION_RESET,
    DreameVacuumState.RETURNING_INSTALL_MOP: STATE_RETURNING_INSTALL_MOP,
    DreameVacuumState.RETURNING_REMOVE_MOP: STATE_RETURNING_REMOVE_MOP,
    DreameVacuumState.WATER_CHECK: STATE_WATER_CHECK,
    DreameVacuumState.CLEAN_ADD_WATER: STATE_CLEAN_ADD_WATER,
    DreameVacuumState.WASHING_PAUSED: STATE_WASHING_PAUSED,
    DreameVacuumState.AUTO_EMPTYING: STATE_AUTO_EMPTYING,
    DreameVacuumState.REMOTE_CONTROL: STATE_REMOTE_CONTROL,
    DreameVacuumState.SMART_CHARGING: STATE_SMART_CHARGING,
    DreameVacuumState.SECOND_CLEANING: STATE_SECOND_CLEANING,
    DreameVacuumState.HUMAN_FOLLOWING: STATE_HUMAN_FOLLOWING,
    DreameVacuumState.SPOT_CLEANING: STATE_SPOT_CLEANING,
    DreameVacuumState.RETURNING_AUTO_EMPTY: STATE_RETURNING_AUTO_EMPTY,
    DreameVacuumState.WAITING_FOR_TASK: STATE_WAITING_FOR_TASK,
    DreameVacuumState.STATION_CLEANING: STATE_STATION_CLEANING,
    DreameVacuumState.RETURNING_TO_DRAIN: STATE_RETURNING_TO_DRAIN,
    DreameVacuumState.DRAINING: STATE_DRAINING,
    DreameVacuumState.AUTO_WATER_DRAINING: STATE_AUTO_WATER_DRAINING,
    DreameVacuumState.EMPTYING: STATE_EMPTYING,
    DreameVacuumState.DUST_BAG_DRYING: STATE_DUST_BAG_DRYING,
    DreameVacuumState.DUST_BAG_DRYING_PAUSED: STATE_DUST_BAG_DRYING_PAUSED,
    DreameVacuumState.HEADING_TO_EXTRA_CLEANING: STATE_HEADING_TO_EXTRA_CLEANING,
    DreameVacuumState.EXTRA_CLEANING: STATE_EXTRA_CLEANING,
    DreameVacuumState.FINDING_PET_PAUSED: STATE_FINDING_PET_PAUSED,
    DreameVacuumState.FINDING_PET: STATE_FINDING_PET,
    DreameVacuumState.SHORTCUT: STATE_SHORTCUT,
    DreameVacuumState.MONITORING: STATE_MONITORING,
    DreameVacuumState.MONITORING_PAUSED: STATE_MONITORING_PAUSED,
    DreameVacuumState.INITIAL_DEEP_CLEANING: STATE_INITIAL_DEEP_CLEANING,
    DreameVacuumState.INITIAL_DEEP_CLEANING_PAUSED: STATE_INITIAL_DEEP_CLEANING_PAUSED,
    DreameVacuumState.SANITIZING: STATE_SANITIZING,
    DreameVacuumState.SANITIZING_WITH_DRY: STATE_SANITIZING_WITH_DRY,
    DreameVacuumState.CHANGING_MOP: STATE_CHANGING_MOP,
    DreameVacuumState.CHANGING_MOP_PAUSED: STATE_CHANGING_MOP_PAUSED,
    DreameVacuumState.FLOOR_MAINTAINING: STATE_FLOOR_MAINTAINING,
    DreameVacuumState.FLOOR_MAINTAINING_PAUSED: STATE_FLOOR_MAINTAINING_PAUSED,
    DreameVacuumState.REMOTE_PICKUP: STATE_REMOTE_PICKUP,
    DreameVacuumState.ARRANGING_ITEMS: STATE_ARRANGING_ITEMS,
    DreameVacuumState.PET_GUARDING: STATE_PET_GUARDING,
    DreameVacuumState.PET_GUARDING_PAUSED: STATE_PET_GUARDING_PAUSED,
    DreameVacuumState.INSTALLING_MOP: STATE_INSTALLING_MOP,
    DreameVacuumState.UNINSTALLING_MOP: STATE_UNINSTALLING_MOP,
    DreameVacuumState.INTELLIGENT_RECHARGING: STATE_INTELLIGENT_RECHARGING,
    DreameVacuumState.ASSISTED_CLEANING: STATE_ASSISTED_CLEANING,
    DreameVacuumState.ENTERING_DOCK: STATE_ENTERING_DOCK,
    DreameVacuumState.LEAVING_DOCK: STATE_LEAVING_DOCK,
    DreameVacuumState.NAVIGATING_TO_CLIMBER: STATE_NAVIGATING_TO_CLIMBER,
    DreameVacuumState.DOCKING_TO_CLIMBER: STATE_DOCKING_TO_CLIMBER,
    DreameVacuumState.CLIMBER_DOCKED: STATE_CLIMBER_DOCKED,
    DreameVacuumState.CLIMBER_NAVIGATING: STATE_CLIMBER_NAVIGATING,
    DreameVacuumState.CLIMBING_STAIRS: STATE_CLIMBING_STAIRS,
    DreameVacuumState.CLIMBING_STAIRS_COMPLETED: STATE_CLIMBING_STAIRS_COMPLETED,
    DreameVacuumState.CLIMBER_AT_DOCK: STATE_CLIMBER_AT_DOCK,
    DreameVacuumState.CLIMBER_LEAVING_DOCK: STATE_CLIMBER_LEAVING_DOCK,
}

# Dreame Vacuum suction level names
SUCTION_LEVEL_CODE_TO_NAME: Final = {
    DreameVacuumSuctionLevel.QUIET: SUCTION_LEVEL_QUIET,
    DreameVacuumSuctionLevel.STANDARD: SUCTION_LEVEL_STANDARD,
    DreameVacuumSuctionLevel.STRONG: SUCTION_LEVEL_STRONG,
    DreameVacuumSuctionLevel.TURBO: SUCTION_LEVEL_TURBO,
}

# Dreame Vacuum water volume names
WATER_VOLUME_CODE_TO_NAME: Final = {
    DreameVacuumWaterVolume.LOW: WATER_VOLUME_LOW,
    DreameVacuumWaterVolume.MEDIUM: WATER_VOLUME_MEDIUM,
    DreameVacuumWaterVolume.HIGH: WATER_VOLUME_HIGH,
}

# Dreame Vacuum mop pad humidity names
MOP_PAD_HUMIDITY_CODE_TO_NAME: Final = {
    DreameVacuumMopPadHumidity.SLIGHTLY_DRY: MOP_PAD_HUMIDITY_SLIGHTLY_DRY,
    DreameVacuumMopPadHumidity.MOIST: MOP_PAD_HUMIDITY_MOIST,
    DreameVacuumMopPadHumidity.WET: MOP_PAD_HUMIDITY_WET,
}

# Dreame Vacuum cleaning mode names
CLEANING_MODE_CODE_TO_NAME: Final = {
    DreameVacuumCleaningMode.SWEEPING: CLEANING_MODE_SWEEPING,
    DreameVacuumCleaningMode.MOPPING: CLEANING_MODE_MOPPING,
    DreameVacuumCleaningMode.SWEEPING_AND_MOPPING: CLEANING_MODE_SWEEPING_AND_MOPPING,
    DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING: CLEANING_MODE_MOPPING_AFTER_SWEEPING,
}

WATER_TANK_CODE_TO_NAME: Final = {
    DreameVacuumWaterTank.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumWaterTank.INSTALLED: WATER_TANK_INSTALLED,
    DreameVacuumWaterTank.NOT_INSTALLED: WATER_TANK_NOT_INSTALLED,
    DreameVacuumWaterTank.MOP_INSTALLED: WATER_TANK_MOP_INSTALLED,
    DreameVacuumWaterTank.MOP_IN_STATION: WATER_TANK_MOP_IN_STATION,
}

CARPET_SENSITIVITY_CODE_TO_NAME: Final = {
    DreameVacuumCarpetSensitivity.LOW: CARPET_SENSITIVITY_LOW,
    DreameVacuumCarpetSensitivity.MEDIUM: CARPET_SENSITIVITY_MEDIUM,
    DreameVacuumCarpetSensitivity.HIGH: CARPET_SENSITIVITY_HIGH,
}

CARPET_CLEANING_CODE_TO_NAME: Final = {
    DreameVacuumCarpetCleaning.AVOIDANCE: CARPET_CLEANING_AVOIDANCE,
    DreameVacuumCarpetCleaning.ADAPTATION: CARPET_CLEANING_ADAPTATION,
    DreameVacuumCarpetCleaning.REMOVE_MOP: CARPET_CLEANING_REMOVE_MOP,
    DreameVacuumCarpetCleaning.ADAPTATION_WITHOUT_ROUTE: CARPET_CLEANING_ADAPTATION_WITHOUT_ROUTE,
    DreameVacuumCarpetCleaning.VACUUM_AND_MOP: CARPET_CLEANING_VACUUM_AND_MOP,
    DreameVacuumCarpetCleaning.IGNORE: CARPET_CLEANING_IGNORE,
    DreameVacuumCarpetCleaning.CROSS: CARPET_CLEANING_CROSS,
}

FLOOR_MATERIAL_CODE_TO_NAME: Final = {
    DreameVacuumFloorMaterial.NONE: FLOOR_MATERIAL_NONE,
    DreameVacuumFloorMaterial.TILE: FLOOR_MATERIAL_TILE,
    DreameVacuumFloorMaterial.WOOD: FLOOR_MATERIAL_WOOD,
    DreameVacuumFloorMaterial.MEDIUM_PILE_CARPET: FLOOR_MATERIAL_MEDIUM_PILE_CARPET,
    DreameVacuumFloorMaterial.LOW_PILE_CARPET: FLOOR_MATERIAL_LOW_PILE_CARPET,
    DreameVacuumFloorMaterial.CARPET: FLOOR_MATERIAL_CARPET,
}

FLOOR_MATERIAL_DIRECTION_CODE_TO_NAME: Final = {
    DreameVacuumFloorMaterialDirection.VERTICAL: FLOOR_MATERIAL_DIRECTION_VERTICAL,
    DreameVacuumFloorMaterialDirection.HORIZONTAL: FLOOR_MATERIAL_DIRECTION_HORIZONTAL,
}

SEGMENT_VISIBILITY_CODE_TO_NAME: Final = {
    DreameVacuumSegmentVisibility.VISIBLE: SEGMENT_VISIBILITY_VISIBLE,
    DreameVacuumSegmentVisibility.HIDDEN: SEGMENT_VISIBILITY_HIDDEN,
}

TASK_STATUS_CODE_TO_NAME: Final = {
    DreameVacuumTaskStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumTaskStatus.COMPLETED: TASK_STATUS_COMPLETED,
    DreameVacuumTaskStatus.AUTO_CLEANING: TASK_STATUS_AUTO_CLEANING,
    DreameVacuumTaskStatus.ZONE_CLEANING: TASK_STATUS_ZONE_CLEANING,
    DreameVacuumTaskStatus.SEGMENT_CLEANING: TASK_STATUS_SEGMENT_CLEANING,
    DreameVacuumTaskStatus.SPOT_CLEANING: TASK_STATUS_SPOT_CLEANING,
    DreameVacuumTaskStatus.FAST_MAPPING: TASK_STATUS_FAST_MAPPING,
    DreameVacuumTaskStatus.AUTO_CLEANING_PAUSED: TASK_STATUS_AUTO_CLEANING_PAUSE,
    DreameVacuumTaskStatus.SEGMENT_CLEANING_PAUSED: TASK_STATUS_SEGMENT_CLEANING_PAUSE,
    DreameVacuumTaskStatus.ZONE_CLEANING_PAUSED: TASK_STATUS_ZONE_CLEANING_PAUSE,
    DreameVacuumTaskStatus.SPOT_CLEANING_PAUSED: TASK_STATUS_SPOT_CLEANING_PAUSE,
    DreameVacuumTaskStatus.MAP_CLEANING_PAUSED: TASK_STATUS_MAP_CLEANING_PAUSE,
    DreameVacuumTaskStatus.DOCKING_PAUSED: TASK_STATUS_DOCKING_PAUSE,
    DreameVacuumTaskStatus.MOPPING_PAUSED: TASK_STATUS_MOPPING_PAUSE,
    DreameVacuumTaskStatus.ZONE_MOPPING_PAUSED: TASK_STATUS_ZONE_MOPPING_PAUSE,
    DreameVacuumTaskStatus.SEGMENT_MOPPING_PAUSED: TASK_STATUS_SEGMENT_MOPPING_PAUSE,
    DreameVacuumTaskStatus.AUTO_MOPPING_PAUSED: TASK_STATUS_AUTO_MOPPING_PAUSE,
    DreameVacuumTaskStatus.AUTO_DOCKING_PAUSED: TASK_STATUS_DOCKING_PAUSE,
    DreameVacuumTaskStatus.ZONE_DOCKING_PAUSED: TASK_STATUS_DOCKING_PAUSE,
    DreameVacuumTaskStatus.SEGMENT_DOCKING_PAUSED: TASK_STATUS_DOCKING_PAUSE,
    DreameVacuumTaskStatus.CRUISING_PATH: TASK_STATUS_CRUISING_PATH,
    DreameVacuumTaskStatus.CRUISING_PATH_PAUSED: TASK_STATUS_CRUISING_PATH_PAUSED,
    DreameVacuumTaskStatus.CRUISING_POINT: TASK_STATUS_CRUISING_POINT,
    DreameVacuumTaskStatus.CRUISING_POINT_PAUSED: TASK_STATUS_CRUISING_POINT_PAUSED,
    DreameVacuumTaskStatus.SUMMON_CLEAN_PAUSED: TASK_STATUS_SUMMON_CLEAN_PAUSED,
    DreameVacuumTaskStatus.RETURNING_INSTALL_MOP: TASK_STATUS_RETURNING_INSTALL_MOP,
    DreameVacuumTaskStatus.RETURNING_REMOVE_MOP: TASK_STATUS_RETURNING_REMOVE_MOP,
    DreameVacuumTaskStatus.STATION_CLEANING: TASK_STATUS_STATION_CLEANING,
    DreameVacuumTaskStatus.PET_FINDING: TASK_STATUS_PET_FINDING,
    DreameVacuumTaskStatus.AUTO_CLEANING_WASHING_PAUSED: TASK_STATUS_AUTO_CLEANING_WASHING_PAUSED,
    DreameVacuumTaskStatus.AREA_CLEANING_WASHING_PAUSED: TASK_STATUS_AREA_CLEANING_WASHING_PAUSED,
    DreameVacuumTaskStatus.CUSTOM_CLEANING_WASHING_PAUSED: TASK_STATUS_CUSTOM_CLEANING_WASHING_PAUSED,
    DreameVacuumTaskStatus.PICKING_UP_ITEM: TASK_STATUS_PICKING_UP_ITEM,
    DreameVacuumTaskStatus.PICKING_UP_ITEM_PAUSED: TASK_STATUS_PICKING_UP_ITEM_PAUSED,
    DreameVacuumTaskStatus.PICKING_UP_ITEM_SUCCESS: TASK_STATUS_PICKING_UP_ITEM_SUCCESS,
    DreameVacuumTaskStatus.REMOTE_PICKUP_INITIALIZING: TASK_STATUS_REMOTE_PICKUP_INITIALIZING,
    DreameVacuumTaskStatus.REMOTE_PICKUP_IDENTIFING: TASK_STATUS_REMOTE_PICKUP_IDENTIFING,
    DreameVacuumTaskStatus.MANUAL_REMOTE_PICKUP: TASK_STATUS_MANUAL_REMOTE_PICKUP,
    DreameVacuumTaskStatus.AUTOMATIC_REMOTE_PICKUP: TASK_STATUS_AUTOMATIC_REMOTE_PICKUP,
    DreameVacuumTaskStatus.REMOTE_PICKUP_IN_PROGRESS: TASK_STATUS_REMOTE_PICKUP_IN_PROGRESS,
    DreameVacuumTaskStatus.REMOTE_PICKUP_PAUSED: TASK_STATUS_REMOTE_PICKUP_PAUSED,
    DreameVacuumTaskStatus.PLACING_ITEM: TASK_STATUS_PLACING_ITEM,
    DreameVacuumTaskStatus.PLACING_ITEM_PAUSED: TASK_STATUS_PLACING_ITEM_PAUSED,
}

STATUS_CODE_TO_NAME: Final = {
    DreameVacuumStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumStatus.IDLE: STATE_IDLE,
    DreameVacuumStatus.PAUSED: STATE_PAUSED,
    DreameVacuumStatus.CLEANING: STATUS_CLEANING,
    DreameVacuumStatus.BACK_HOME: STATE_RETURNING,
    DreameVacuumStatus.PARTIAL_CLEANING: STATUS_SPOT_CLEANING,
    DreameVacuumStatus.FOLLOW_WALL: STATUS_FOLLOW_WALL,
    DreameVacuumStatus.CHARGING: STATUS_CHARGING,
    DreameVacuumStatus.OTA: STATUS_OTA,
    DreameVacuumStatus.FCT: STATUS_FCT,
    DreameVacuumStatus.WIFI_SET: STATUS_WIFI_SET,
    DreameVacuumStatus.POWER_OFF: STATUS_POWER_OFF,
    DreameVacuumStatus.FACTORY: STATUS_FACTORY,
    DreameVacuumStatus.ERROR: STATUS_ERROR,
    DreameVacuumStatus.REMOTE_CONTROL: STATUS_REMOTE_CONTROL,
    DreameVacuumStatus.SLEEPING: STATUS_SLEEP,
    DreameVacuumStatus.SELF_REPAIR: STATUS_SELF_REPAIR,
    DreameVacuumStatus.FACTORY_FUNCION_TEST: STATUS_FACTORY_FUNC_TEST,
    DreameVacuumStatus.STANDBY: STATUS_STANDBY,
    DreameVacuumStatus.SEGMENT_CLEANING: STATUS_SEGMENT_CLEANING,
    DreameVacuumStatus.ZONE_CLEANING: STATUS_ZONE_CLEANING,
    DreameVacuumStatus.SPOT_CLEANING: STATUS_SPOT_CLEANING,
    DreameVacuumStatus.FAST_MAPPING: STATUS_FAST_MAPPING,
    DreameVacuumStatus.CRUISING_PATH: STATUS_CRUISING_PATH,
    DreameVacuumStatus.CRUISING_POINT: STATUS_CRUISING_POINT,
    DreameVacuumStatus.SUMMON_CLEAN: STATUS_SUMMON_CLEAN,
    DreameVacuumStatus.SHORTCUT: STATUS_SHORTCUT,
    DreameVacuumStatus.PERSON_FOLLOW: STATUS_PERSON_FOLLOW,
    DreameVacuumStatus.WATER_CHECK: STATUS_WATER_CHECK,
    DreameVacuumStatus.PET_GUARDING: STATUS_PET_GUARDING,
    DreameVacuumStatus.AUTO_ARRANGEMENT: STATUS_AUTO_ARRANGEMENT,
    DreameVacuumStatus.SMART_ARRANGEMENT: STATUS_SMART_ARRANGEMENT,
    DreameVacuumStatus.ZONED_ARRANGEMENT: STATUS_ZONED_ARRANGEMENT,
}

RELOCATION_STATUS_CODE_TO_NAME: Final = {
    DreameVacuumRelocationStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumRelocationStatus.LOCATED: RELOCATION_STATUS_LOCATED,
    DreameVacuumRelocationStatus.LOCATING: RELOCATION_STATUS_LOCATING,
    DreameVacuumRelocationStatus.FAILED: RELOCATION_STATUS_FAILED,
    DreameVacuumRelocationStatus.SUCCESS: RELOCATION_STATUS_SUCESS,
}

CHARGING_STATUS_CODE_TO_NAME: Final = {
    DreameVacuumChargingStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumChargingStatus.CHARGING: CHARGING_STATUS_CHARGING,
    DreameVacuumChargingStatus.NOT_CHARGING: CHARGING_STATUS_NOT_CHARGING,
    DreameVacuumChargingStatus.CHARGING_COMPLETED: CHARGING_STATUS_CHARGING_COMPLETED,
    DreameVacuumChargingStatus.RETURN_TO_CHARGE: CHARGING_STATUS_RETURN_TO_CHARGE,
}

ERROR_CODE_TO_ERROR_NAME: Final = {
    DreameVacuumErrorCode.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumErrorCode.NO_ERROR: ERROR_NO_ERROR,
    DreameVacuumErrorCode.DROP: ERROR_DROP,
    DreameVacuumErrorCode.CLIFF: ERROR_CLIFF,
    DreameVacuumErrorCode.BUMPER: ERROR_BUMPER,
    DreameVacuumErrorCode.GESTURE: ERROR_GESTURE,
    DreameVacuumErrorCode.BUMPER_REPEAT: ERROR_BUMPER_REPEAT,
    DreameVacuumErrorCode.DROP_REPEAT: ERROR_DROP_REPEAT,
    DreameVacuumErrorCode.OPTICAL_FLOW: ERROR_OPTICAL_FLOW,
    DreameVacuumErrorCode.BOX: ERROR_NO_BOX,
    DreameVacuumErrorCode.TANKBOX: ERROR_NO_TANKBOX,
    DreameVacuumErrorCode.WATERBOX_EMPTY: ERROR_WATERBOX_EMPTY,
    DreameVacuumErrorCode.BOX_FULL: ERROR_BOX_FULL,
    DreameVacuumErrorCode.BRUSH: ERROR_BRUSH,
    DreameVacuumErrorCode.SIDE_BRUSH: ERROR_SIDE_BRUSH,
    DreameVacuumErrorCode.FAN: ERROR_FAN,
    DreameVacuumErrorCode.LEFT_WHEEL_MOTOR: ERROR_LEFT_WHEEL_MOTOR,
    DreameVacuumErrorCode.RIGHT_WHEEL_MOTOR: ERROR_RIGHT_WHEEL_MOTOR,
    DreameVacuumErrorCode.TURN_SUFFOCATE: ERROR_TURN_SUFFOCATE,
    DreameVacuumErrorCode.FORWARD_SUFFOCATE: ERROR_FORWARD_SUFFOCATE,
    DreameVacuumErrorCode.CHARGER_GET: ERROR_CHARGER_GET,
    DreameVacuumErrorCode.BATTERY_LOW: ERROR_BATTERY_LOW,
    DreameVacuumErrorCode.CHARGE_FAULT: ERROR_CHARGE_FAULT,
    DreameVacuumErrorCode.BATTERY_PERCENTAGE: ERROR_BATTERY_PERCENTAGE,
    DreameVacuumErrorCode.HEART: ERROR_HEART,
    DreameVacuumErrorCode.CAMERA_OCCLUSION: ERROR_CAMERA_OCCLUSION,
    DreameVacuumErrorCode.MOVE: ERROR_MOVE,
    DreameVacuumErrorCode.FLOW_SHIELDING: ERROR_FLOW_SHIELDING,
    DreameVacuumErrorCode.INFRARED_SHIELDING: ERROR_INFRARED_SHIELDING,
    DreameVacuumErrorCode.CHARGE_NO_ELECTRIC: ERROR_CHARGE_NO_ELECTRIC,
    DreameVacuumErrorCode.BATTERY_FAULT: ERROR_BATTERY_FAULT,
    DreameVacuumErrorCode.FAN_SPEED_ERROR: ERROR_FAN_SPEED_ERROR,
    DreameVacuumErrorCode.LEFTWHELL_SPEED: ERROR_LEFTWHELL_SPEED,
    DreameVacuumErrorCode.RIGHTWHELL_SPEED: ERROR_RIGHTWHELL_SPEED,
    DreameVacuumErrorCode.BMI055_ACCE: ERROR_BMI055_ACCE,
    DreameVacuumErrorCode.BMI055_GYRO: ERROR_BMI055_GYRO,
    DreameVacuumErrorCode.XV7001: ERROR_XV7001,
    DreameVacuumErrorCode.LEFT_MAGNET: ERROR_LEFT_MAGNET,
    DreameVacuumErrorCode.RIGHT_MAGNET: ERROR_RIGHT_MAGNET,
    DreameVacuumErrorCode.FLOW_ERROR: ERROR_FLOW_ERROR,
    DreameVacuumErrorCode.INFRARED_FAULT: ERROR_INFRARED_FAULT,
    DreameVacuumErrorCode.CAMERA_FAULT: ERROR_CAMERA_FAULT,
    DreameVacuumErrorCode.STRONG_MAGNET: ERROR_STRONG_MAGNET,
    DreameVacuumErrorCode.WATER_PUMP: ERROR_WATER_PUMP,
    DreameVacuumErrorCode.RTC: ERROR_RTC,
    DreameVacuumErrorCode.AUTO_KEY_TRIG: ERROR_AUTO_KEY_TRIG,
    DreameVacuumErrorCode.P3V3: ERROR_P3V3,
    DreameVacuumErrorCode.CAMERA_IDLE: ERROR_CAMERA_IDLE,
    DreameVacuumErrorCode.BLOCKED: ERROR_BLOCKED,
    DreameVacuumErrorCode.LDS_ERROR: ERROR_LDS_ERROR,
    DreameVacuumErrorCode.LDS_BUMPER: ERROR_LDS_BUMPER,
    DreameVacuumErrorCode.WATER_PUMP_2: ERROR_WATER_PUMP,
    DreameVacuumErrorCode.FILTER_BLOCKED: ERROR_FILTER_BLOCKED,
    DreameVacuumErrorCode.EDGE: ERROR_EDGE,
    DreameVacuumErrorCode.CARPET: ERROR_CARPET,
    DreameVacuumErrorCode.LASER: ERROR_LASER,
    DreameVacuumErrorCode.EDGE_2: ERROR_EDGE,
    DreameVacuumErrorCode.ULTRASONIC: ERROR_ULTRASONIC,
    DreameVacuumErrorCode.NO_GO_ZONE: ERROR_NO_GO_ZONE,
    DreameVacuumErrorCode.ROUTE: ERROR_ROUTE,
    DreameVacuumErrorCode.ROUTE_2: ERROR_ROUTE,
    DreameVacuumErrorCode.BLOCKED_2: ERROR_BLOCKED,
    DreameVacuumErrorCode.BLOCKED_3: ERROR_BLOCKED,
    DreameVacuumErrorCode.RESTRICTED: ERROR_RESTRICTED,
    DreameVacuumErrorCode.RESTRICTED_2: ERROR_RESTRICTED,
    DreameVacuumErrorCode.RESTRICTED_3: ERROR_RESTRICTED,
    DreameVacuumErrorCode.REMOVE_MOP: ERROR_REMOVE_MOP,
    DreameVacuumErrorCode.MOP_REMOVED: ERROR_MOP_REMOVED,
    DreameVacuumErrorCode.MOP_REMOVED_2: ERROR_MOP_REMOVED,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE: ERROR_MOP_PAD_STOP_ROTATE,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE_2: ERROR_MOP_PAD_STOP_ROTATE,
    DreameVacuumErrorCode.MOP_INSTALL_FAILED: ERROR_MOP_INSTALL_FAILED,
    DreameVacuumErrorCode.LOW_BATTERY_TURN_OFF: ERROR_LOW_BATTERY_TURN_OFF,
    DreameVacuumErrorCode.DIRTY_TANK_NOT_INSTALLED: ERROR_DIRTY_TANK_NOT_INSTALLED,
    DreameVacuumErrorCode.ROBOT_IN_HIDDEN_ROOM: ERROR_ROBOT_IN_HIDDEN_ROOM,
    DreameVacuumErrorCode.LDS_FAILED_TO_LIFT: ERROR_LDS_FAILED_TO_LIFT,
    DreameVacuumErrorCode.ROBOT_STUCK: ERROR_ROBOT_STUCK,
    DreameVacuumErrorCode.ROBOT_STUCK_REPEAT: ERROR_ROBOT_STUCK,
    DreameVacuumErrorCode.SLIPPERY_FLOOR: ERROR_SLIPPERY_FLOOR,
    DreameVacuumErrorCode.UNKNOWN_ERROR: STATE_UNKNOWN,
    DreameVacuumErrorCode.CHECK_MOP_INSTALL: ERROR_CHECK_MOP_INSTALL,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_FULL: ERROR_DIRTY_WATER_TANK_FULL,
    DreameVacuumErrorCode.RETRACTABLE_LEG_STUCK: ERROR_RETRACTABLE_LEG_STUCK,
    DreameVacuumErrorCode.INTERNAL_ERROR: ERROR_INTERNAL_ERROR,
    DreameVacuumErrorCode.ROBOT_STUCK_2: ERROR_ROBOT_STUCK,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_TABLES: ERROR_ROBOT_STUCK_ON_TABLES,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_PASSAGE: ERROR_ROBOT_STUCK_ON_PASSAGE,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_THRESHOLD: ERROR_ROBOT_STUCK_ON_THRESHOLD,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_LOW_LYING_AREA: ERROR_ROBOT_STUCK_ON_LOW_LYING_AREA,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_RAMP: ERROR_ROBOT_STUCK_ON_RAMP,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_OBSTACLE: ERROR_ROBOT_STUCK_ON_OBSTACLE,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_PET: ERROR_ROBOT_STUCK_ON_PET,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_SLIPPERY_SURFACE: ERROR_ROBOT_STUCK_ON_SLIPPERY_SURFACE,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_CARPET: ERROR_ROBOT_STUCK_ON_CARPET,
    DreameVacuumErrorCode.BIN_FULL: ERROR_BIN_FULL,
    DreameVacuumErrorCode.BIN_OPEN: ERROR_BIN_OPEN,
    DreameVacuumErrorCode.BIN_OPEN_2: ERROR_BIN_OPEN,
    DreameVacuumErrorCode.WATER_TANK: ERROR_WATER_TANK,
    DreameVacuumErrorCode.DIRTY_WATER_TANK: ERROR_DIRTY_WATER_TANK,
    DreameVacuumErrorCode.WATER_TANK_DRY: ERROR_WATER_TANK_DRY,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_2: ERROR_DIRTY_WATER_TANK,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_BLOCKED: ERROR_DIRTY_WATER_TANK_BLOCKED,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_PUMP: ERROR_DIRTY_WATER_TANK_PUMP,
    DreameVacuumErrorCode.MOP_PAD: ERROR_MOP_PAD,
    DreameVacuumErrorCode.WET_MOP_PAD: ERROR_WET_MOP_PAD,
    DreameVacuumErrorCode.CLEAN_MOP_PAD: ERROR_CLEAN_MOP_PAD,
    DreameVacuumErrorCode.CLEAN_TANK_LEVEL: ERROR_CLEAN_TANK_LEVEL,
    DreameVacuumErrorCode.STATION_DISCONNECTED: ERROR_STATION_DISCONNECTED,
    DreameVacuumErrorCode.DIRTY_TANK_LEVEL: ERROR_DIRTY_TANK_LEVEL,
    DreameVacuumErrorCode.WASHBOARD_LEVEL: ERROR_WASHBOARD_LEVEL,
    DreameVacuumErrorCode.NO_MOP_IN_STATION: ERROR_NO_MOP_IN_STATION,
    DreameVacuumErrorCode.DUST_BAG_FULL: ERROR_DUST_BAG_FULL,
    DreameVacuumErrorCode.SELF_TEST_FAILED: ERROR_SELF_TEST_FAILED,
    DreameVacuumErrorCode.UNKNOWN_WARNING: STATE_UNKNOWN,
    DreameVacuumErrorCode.WASHBOARD_NOT_WORKING: ERROR_WASHBOARD_NOT_WORKING,
    DreameVacuumErrorCode.DRAINAGE_FAILED: ERROR_DRAINAGE_FAILED,
    DreameVacuumErrorCode.MOP_NOT_DETECTED: ERROR_MOP_NOT_DETECTED,
    DreameVacuumErrorCode.MOP_HOLDER_ERROR: ERROR_MOP_HOLDER_ERROR,
    DreameVacuumErrorCode.DOCK_ERROR: ERROR_DOCK_ERROR,
    DreameVacuumErrorCode.WASH_FAILED: ERROR_WASH_FAILED,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_CURTAIN: ERROR_ROBOT_STUCK_ON_CURTAIN,
    DreameVacuumErrorCode.EDGE_MOP_STOP_ROTATE: ERROR_EDGE_MOP_STOP_ROTATE,
    DreameVacuumErrorCode.EDGE_MOP_DETACHED: ERROR_EDGE_MOP_DETACHED,
    DreameVacuumErrorCode.CHASSIS_LIFT_MALFUNCTION: ERROR_CHASSIS_LIFT_MALFUNCTION,
    DreameVacuumErrorCode.INTERNAL_ERROR_2: ERROR_INTERNAL_ERROR,
    DreameVacuumErrorCode.MOP_COVER_ERROR: ERROR_MOP_COVER_ERROR,
    DreameVacuumErrorCode.ROLLER_MOP_ERROR: ERROR_ROLLER_MOP_ERROR,
    DreameVacuumErrorCode.ONBOARD_WATER_TANK_EMPTY: ERROR_ONBOARD_WATER_TANK_EMPTY,
    DreameVacuumErrorCode.ONBOARD_DIRTY_WATER_TANK_FULL: ERROR_ONBOARD_DIRTY_WATER_TANK_FULL,
    DreameVacuumErrorCode.MOP_NOT_INSTALLED: ERROR_MOP_NOT_INSTALLED,
    DreameVacuumErrorCode.ROLLER_MOP_ERROR_2: ERROR_ROLLER_MOP_ERROR,
    DreameVacuumErrorCode.FLUFFING_ROLLER_ERROR: ERROR_FLUFFING_ROLLER_ERROR,
    DreameVacuumErrorCode.MOP_COVER_ERROR_2: ERROR_MOP_COVER_ERROR,
    DreameVacuumErrorCode.BLOCKED_BY_OBSTACLE: ERROR_BLOCKED_BY_OBSTACLE,
    DreameVacuumErrorCode.RETURN_TO_CHARGE_FAILED: ERROR_RETURN_TO_CHARGE_FAILED,
    DreameVacuumErrorCode.ROBOTIC_ARM_STOPPED: ERROR_ROBOTIC_ARM_STOPPED,
    DreameVacuumErrorCode.LDS_ERROR_2: ERROR_LDS_ERROR,
    DreameVacuumErrorCode.MOP_COVER_ERROR_3: ERROR_MOP_COVER_ERROR,
    DreameVacuumErrorCode.ROLLER_MOP_ERROR_3: ERROR_ROLLER_MOP_ERROR,
    DreameVacuumErrorCode.DRAINAGE_OUTLET_FILTER: ERROR_DRAINAGE_OUTLET_FILTER,
    DreameVacuumErrorCode.MAIN_WHEELS_ERROR: ERROR_MAIN_WHEELS_ERROR,
    DreameVacuumErrorCode.INTERNAL_ERROR_3: ERROR_INTERNAL_ERROR,
    DreameVacuumErrorCode.INTERNAL_ERROR_4: ERROR_INTERNAL_ERROR,
}

DUST_COLLECTION_TO_NAME: Final = {
    DreameVacuumDustCollection.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumDustCollection.NOT_AVAILABLE: DUST_COLLECTION_NOT_AVAILABLE,
    DreameVacuumDustCollection.AVAILABLE: DUST_COLLECTION_AVAILABLE,
}

AUTO_EMPTY_STATUS_TO_NAME: Final = {
    DreameVacuumAutoEmptyStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumAutoEmptyStatus.IDLE: STATE_IDLE,
    DreameVacuumAutoEmptyStatus.ACTIVE: AUTO_EMPTY_STATUS_ACTIVE,
    DreameVacuumAutoEmptyStatus.NOT_PERFORMED: AUTO_EMPTY_STATUS_NOT_PERFORMED,
}

MAP_RECOVERY_STATUS_TO_NAME: Final = {
    DreameVacuumMapRecoveryStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumMapRecoveryStatus.IDLE: STATE_IDLE,
    DreameVacuumMapRecoveryStatus.RUNNING: MAP_RECOVERY_STATUS_RUNNING,
    DreameVacuumMapRecoveryStatus.SUCCESS: MAP_RECOVERY_STATUS_SUCCESS,
    DreameVacuumMapRecoveryStatus.FAIL: MAP_RECOVERY_STATUS_FAIL,
    DreameVacuumMapRecoveryStatus.FAIL_2: MAP_RECOVERY_STATUS_FAIL,
}

MAP_BACKUP_STATUS_TO_NAME: Final = {
    DreameVacuumMapBackupStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumMapBackupStatus.IDLE: STATE_IDLE,
    DreameVacuumMapBackupStatus.RUNNING: MAP_BACKUP_STATUS_RUNNING,
    DreameVacuumMapBackupStatus.SUCCESS: MAP_BACKUP_STATUS_SUCCESS,
    DreameVacuumMapBackupStatus.FAIL: MAP_BACKUP_STATUS_FAIL,
}

SELF_WASH_BASE_STATUS_TO_NAME: Final = {
    DreameVacuumSelfWashBaseStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumSelfWashBaseStatus.IDLE: STATE_IDLE,
    DreameVacuumSelfWashBaseStatus.WASHING: SELF_WASH_BASE_STATUS_WASHING,
    DreameVacuumSelfWashBaseStatus.DRYING: SELF_WASH_BASE_STATUS_DRYING,
    DreameVacuumSelfWashBaseStatus.PAUSED: SELF_WASH_BASE_STATUS_PAUSED,
    DreameVacuumSelfWashBaseStatus.RETURNING: SELF_WASH_BASE_STATUS_RETURNING,
    DreameVacuumSelfWashBaseStatus.CLEAN_ADD_WATER: SELF_WASH_BASE_STATUS_CLEAN_ADD_WATER,
    DreameVacuumSelfWashBaseStatus.ADDING_WATER: SELF_WASH_BASE_STATUS_ADDING_WATER,
}

MOP_WASH_LEVEL_TO_NAME: Final = {
    DreameVacuumMopWashLevel.DEEP: MOP_WASH_LEVEL_DEEP,
    DreameVacuumMopWashLevel.DAILY: MOP_WASH_LEVEL_DAILY,
    DreameVacuumMopWashLevel.WATER_SAVING: MOP_WASH_LEVEL_WATER_SAVING,
}

MOP_CLEAN_FREQUENCY_TO_NAME: Final = {
    DreameVacuumMopCleanFrequency.BY_ROOM: MOP_CLEAN_FREQUENCY_BY_ROOM,
    DreameVacuumMopCleanFrequency.FIVE_SQUARE_METERS: MOP_CLEAN_FREQUENCY_FIVE_SQUARE_METERS,
    DreameVacuumMopCleanFrequency.EIGHT_SQUARE_METERS: MOP_CLEAN_FREQUENCY_EIGHT_SQUARE_METERS,
    DreameVacuumMopCleanFrequency.TEN_SQUARE_METERS: MOP_CLEAN_FREQUENCY_TEN_SQUARE_METERS,
    DreameVacuumMopCleanFrequency.FIFTEEN_SQUARE_METERS: MOP_CLEAN_FREQUENCY_FIFTEEN_SQUARE_METERS,
    DreameVacuumMopCleanFrequency.TWENTY_SQUARE_METERS: MOP_CLEAN_FREQUENCY_TWENTY_SQUARE_METERS,
    DreameVacuumMopCleanFrequency.TWENTYFIVE_SQUARE_METERS: MOP_CLEAN_FREQUENCY_TWENTYFIVE_SQUARE_METERS,
}

MOPPING_TYPE_TO_NAME: Final = {
    DreameVacuumMoppingType.DEEP: MOPPING_TYPE_DEEP,
    DreameVacuumMoppingType.DAILY: MOPPING_TYPE_DAILY,
    DreameVacuumMoppingType.ACCURATE: MOPPING_TYPE_ACCURATE,
}

STREAM_STATUS_TO_NAME: Final = {
    DreameVacuumStreamStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumStreamStatus.IDLE: STATE_IDLE,
    DreameVacuumStreamStatus.VIDEO: STREAM_STATUS_VIDEO,
    DreameVacuumStreamStatus.AUDIO: STREAM_STATUS_AUDIO,
    DreameVacuumStreamStatus.RECORDING: STREAM_STATUS_RECORDING,
}

VOICE_ASSISTANT_LANGUAGE_TO_NAME: Final = {
    DreameVacuumVoiceAssistantLanguage.DEFAULT: VOICE_ASSISTANT_LANGUAGE_DEFAULT,
    DreameVacuumVoiceAssistantLanguage.ENGLISH: VOICE_ASSISTANT_LANGUAGE_ENGLISH,
    DreameVacuumVoiceAssistantLanguage.GERMAN: VOICE_ASSISTANT_LANGUAGE_GERMAN,
    DreameVacuumVoiceAssistantLanguage.RUSSIAN: VOICE_ASSISTANT_LANGUAGE_RUSSIAN,
    DreameVacuumVoiceAssistantLanguage.ITALIAN: VOICE_ASSISTANT_LANGUAGE_ITALIAN,
    DreameVacuumVoiceAssistantLanguage.FRENCH: VOICE_ASSISTANT_LANGUAGE_FRENCH,
    DreameVacuumVoiceAssistantLanguage.KOREAN: VOICE_ASSISTANT_LANGUAGE_KOREAN,
    DreameVacuumVoiceAssistantLanguage.CHINESE: VOICE_ASSISTANT_LANGUAGE_CHINESE,
}

MOP_PRESSURE_TO_NAME: Final = {
    DreameVacuumMopPressure.LIGHT: WASHING_MODE_LIGHT,
    DreameVacuumMopPressure.NORMAL: WATER_TEMPERATURE_NORMAL,
}

MOP_TEMPERATURE_TO_NAME: Final = {
    DreameVacuumMopTemperature.NORMAL: WATER_TEMPERATURE_NORMAL,
    DreameVacuumMopTemperature.WARM: WATER_TEMPERATURE_WARM,
}

LOW_LYING_AREA_FREQUENCY_TO_NAME: Final = {
    DreameVacuumLowLyingAreaFrequency.WEEKLY: MOP_PAD_SWING_WEEKLY,
    DreameVacuumLowLyingAreaFrequency.DAILY: MOP_PAD_SWING_DAILY,
}

SCRAPER_FREQUENCY_TO_NAME: Final = {
    DreameVacuumScraperFrequency.OFF: STATE_OFF,
    DreameVacuumScraperFrequency.WEEKLY: MOP_PAD_SWING_WEEKLY,
    DreameVacuumScraperFrequency.DAILY: MOP_PAD_SWING_DAILY,
}

WIDER_CORNER_COVERAGE_TO_NAME: Final = {
    DreameVacuumWiderCornerCoverage.OFF: STATE_OFF,
    DreameVacuumWiderCornerCoverage.LOW_FREQUENCY: WIDER_CORNER_COVERAGE_LOW_FREQUENCY,
    DreameVacuumWiderCornerCoverage.HIGH_FREQUENCY: WIDER_CORNER_COVERAGE_HIGH_FREQUENCY,
}

MOP_PAD_SWING_TO_NAME: Final = {
    DreameVacuumMopPadSwing.OFF: STATE_OFF,
    DreameVacuumMopPadSwing.AUTO: MOP_PAD_SWING_AUTO,
    DreameVacuumMopPadSwing.DAILY: MOP_PAD_SWING_DAILY,
    DreameVacuumMopPadSwing.WEEKLY: MOP_PAD_SWING_WEEKLY,
}

MOP_EXTEND_FREQUENCY_TO_NAME: Final = {
    DreameVacuumMopExtendFrequency.STANDARD: MOP_EXTEND_FREQUENCY_STANDARD,
    DreameVacuumMopExtendFrequency.INTELLIGENT: MOP_EXTEND_FREQUENCY_INTELLIGENT,
    DreameVacuumMopExtendFrequency.HIGH: MOP_EXTEND_FREQUENCY_HIGH,
}

SECOND_CLEANING_TO_NAME: Final = {
    DreameVacuumSecondCleaning.OFF: STATE_OFF,
    DreameVacuumSecondCleaning.IN_DEEP_MODE: SECOND_CLEANING_IN_DEEP_MODE,
    DreameVacuumSecondCleaning.IN_ALL_MODES: SECOND_CLEANING_IN_ALL_MODES,
}

CLEANING_ROUTE_TO_NAME: Final = {
    DreameVacuumCleaningRoute.QUICK: ROUTE_QUICK,
    DreameVacuumCleaningRoute.STANDARD: ROUTE_STANDARD,
    DreameVacuumCleaningRoute.INTENSIVE: ROUTE_INTENSIVE,
    DreameVacuumCleaningRoute.DEEP: ROUTE_DEEP,
}

CUSTOM_MOPPING_ROUTE_TO_NAME: Final = {
    DreameVacuumCustomMoppingRoute.OFF: ROUTE_OFF,
    DreameVacuumCustomMoppingRoute.STANDARD: ROUTE_STANDARD,
    DreameVacuumCustomMoppingRoute.INTENSIVE: ROUTE_INTENSIVE,
    DreameVacuumCustomMoppingRoute.DEEP: ROUTE_DEEP,
}

CLEANGENIUS_TO_NAME = {
    DreameVacuumCleanGenius.OFF: STATE_OFF,
    DreameVacuumCleanGenius.ROUTINE_CLEANING: CLEANGENIUS_ROUTINE_CLEANING,
    DreameVacuumCleanGenius.DEEP_CLEANING: CLEANGENIUS_DEEP_CLEANING,
}

CLEANGENIUS_MODE_TO_NAME = {
    DreameVacuumCleanGeniusMode.VACUUM_AND_MOP: CLEANGENIUS_MODE_VACUUM_AND_MOP,
    DreameVacuumCleanGeniusMode.MOP_AFTER_VACUUM: CLEANGENIUS_MODE_MOP_AFTER_VACUUM,
}

WASHING_MODE_TO_NAME = {
    DreameVacuumWashingMode.LIGHT: WASHING_MODE_LIGHT,
    DreameVacuumWashingMode.STANDARD: WASHING_MODE_STANDARD,
    DreameVacuumWashingMode.DEEP: WASHING_MODE_DEEP,
    DreameVacuumWashingMode.ULTRA_WASHING: WASHING_MODE_ULTRA_WASHING,
}

WATER_TEMPERATURE_TO_NAME = {
    DreameVacuumWaterTemperature.NORMAL: WATER_TEMPERATURE_NORMAL,
    DreameVacuumWaterTemperature.MILD: WATER_TEMPERATURE_MILD,
    DreameVacuumWaterTemperature.WARM: WATER_TEMPERATURE_WARM,
    DreameVacuumWaterTemperature.HOT: WATER_TEMPERATURE_HOT,
    DreameVacuumWaterTemperature.MAX: WATER_TEMPERATURE_MAX,
}

SELF_CLEAN_FREQUENCY_TO_NAME: Final = {
    DreameVacuumSelfCleanFrequency.BY_AREA: SELF_CLEAN_FREQUENCY_BY_AREA,
    DreameVacuumSelfCleanFrequency.BY_TIME: SELF_CLEAN_FREQUENCY_BY_TIME,
    DreameVacuumSelfCleanFrequency.BY_ROOM: SELF_CLEAN_FREQUENCY_BY_ROOM,
    DreameVacuumSelfCleanFrequency.INTELLIGENT: SELF_CLEAN_FREQUENCY_INTELLIGENT,
}

AUTO_EMPTY_MODE_TO_NAME = {
    DreameVacuumAutoEmptyMode.OFF: STATE_OFF,
    DreameVacuumAutoEmptyMode.STANDARD: AUTO_EMPTY_MODE_STANDARD,
    DreameVacuumAutoEmptyMode.HIGH_FREQUENCY: AUTO_EMPTY_MODE_HIGH_FREQUENCY,
    DreameVacuumAutoEmptyMode.LOW_FREQUENCY: AUTO_EMPTY_MODE_LOW_FREQUENCY,
}

AUTO_EMPTY_MODE_V2_TO_NAME = {
    DreameVacuumAutoEmptyModeV2.OFF: STATE_OFF,
    DreameVacuumAutoEmptyModeV2.STANDARD: AUTO_EMPTY_MODE_STANDARD,
    DreameVacuumAutoEmptyModeV2.CUSTOM_FREQUENCY: AUTO_EMPTY_MODE_CUSTOM_FREQUENCY,
    DreameVacuumAutoEmptyModeV2.HIGH_FREQUENCY: AUTO_EMPTY_MODE_HIGH_FREQUENCY,
    DreameVacuumAutoEmptyModeV2.LOW_FREQUENCY: AUTO_EMPTY_MODE_LOW_FREQUENCY,
    DreameVacuumAutoEmptyModeV2.INTELLIGENT: AUTO_EMPTY_MODE_INTELLIGENT,
}

DRAINAGE_STATUS_TO_NAME: Final = {
    DreameVacuumDrainageStatus.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumDrainageStatus.IDLE: STATE_IDLE,
    DreameVacuumDrainageStatus.DRAINING: DRAINAGE_STATUS_DRAINING,
    DreameVacuumDrainageStatus.DRAINING_SUCCESS: DRAINAGE_STATUS_DRAINING_SUCCESS,
    DreameVacuumDrainageStatus.DRAINING_FAILED: DRAINAGE_STATUS_DRAINING_FAILED,
}

LOW_WATER_WARNING_TO_NAME: Final = {
    DreameVacuumLowWaterWarning.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumLowWaterWarning.NO_WARNING: LOW_WATER_WARNING_NO_WARNING,
    DreameVacuumLowWaterWarning.NO_WATER_LEFT_DISMISS: LOW_WATER_WARNING_NO_WARNING,
    DreameVacuumLowWaterWarning.NO_WATER_LEFT: LOW_WATER_WARNING_NO_WATER_LEFT,
    DreameVacuumLowWaterWarning.NO_WATER_LEFT_AFTER_CLEAN: LOW_WATER_WARNING_NO_WATER_LEFT_AFTER_CLEAN,
    DreameVacuumLowWaterWarning.NO_WATER_FOR_CLEAN: LOW_WATER_WARNING_NO_WATER_FOR_CLEAN,
    DreameVacuumLowWaterWarning.LOW_WATER: LOW_WATER_WARNING_LOW_WATER,
    DreameVacuumLowWaterWarning.TANK_NOT_INSTALLED: LOW_WATER_WARNING_TANK_NOT_INSTALLED,
}

TASK_TYPE_TO_NAME: Final = {
    DreameVacuumTaskType.UNKNOWN: STATE_UNKNOWN,
    DreameVacuumTaskType.IDLE: STATE_IDLE,
    DreameVacuumTaskType.STANDARD: TASK_TYPE_STANDARD,
    DreameVacuumTaskType.STANDARD_PAUSED: TASK_TYPE_STANDARD_PAUSED,
    DreameVacuumTaskType.CUSTOM: TASK_TYPE_CUSTOM,
    DreameVacuumTaskType.CUSTOM_PAUSED: TASK_TYPE_CUSTOM_PAUSED,
    DreameVacuumTaskType.SHORTCUT: TASK_TYPE_SHORTCUT,
    DreameVacuumTaskType.SHORTCUT_PAUSED: TASK_TYPE_SHORTCUT_PAUSED,
    DreameVacuumTaskType.SCHEDULED: TASK_TYPE_SCHEDULED,
    DreameVacuumTaskType.SCHEDULED_PAUSED: TASK_TYPE_SCHEDULED_PAUSED,
    DreameVacuumTaskType.SMART: TASK_TYPE_SMART,
    DreameVacuumTaskType.SMART_PAUSED: TASK_TYPE_SMART_PAUSED,
    DreameVacuumTaskType.PARTIAL: TASK_TYPE_PARTIAL,
    DreameVacuumTaskType.PARTIAL_PAUSED: TASK_TYPE_PARTIAL_PAUSED,
    DreameVacuumTaskType.SUMMON: TASK_TYPE_SUMMON,
    DreameVacuumTaskType.SUMMON_PAUSED: TASK_TYPE_SUMMON_PAUSED,
    DreameVacuumTaskType.WATER_STAIN: TASK_TYPE_WATER_STAIN,
    DreameVacuumTaskType.WATER_STAIN_PAUSED: TASK_TYPE_WATER_STAIN_PAUSED,
    DreameVacuumTaskType.BOOSTED_EDGE_CLEANING: TASK_TYPE_BOOSTED_EDGE_CLEANING,
    DreameVacuumTaskType.HAIR_COMPRESSING: TASK_TYPE_HAIR_COMPRESSING,
    DreameVacuumTaskType.LARGE_PARTICLE_CLEANING: TASK_TYPE_LARGE_PARTICLE_CLEANING,
    DreameVacuumTaskType.INTENSIVE_STAIN_CLEANING: TASK_TYPE_INTENSIVE_STAIN_CLEANING,
    DreameVacuumTaskType.STAIN_CLEANING: TASK_TYPE_STAIN_CLEANING,
    DreameVacuumTaskType.INITIAL_DEEP_CLEANING: TASK_TYPE_INITIAL_DEEP_CLEANING,
    DreameVacuumTaskType.INITIAL_DEEP_CLEANING_PAUSED: TASK_TYPE_INITIAL_DEEP_CLEANING_PAUSED,
    DreameVacuumTaskType.MOP_PAD_HEATING: TASK_TYPE_MOP_PAD_HEATING,
    DreameVacuumTaskType.CLEANING_AFTER_MAPPING: TASK_TYPE_CLEANING_AFTER_MAPPING,
    DreameVacuumTaskType.SMALL_PARTICLE_CLEANING: TASK_TYPE_SMALL_PARTICLE_CLEANING,
    DreameVacuumTaskType.CHANGING_MOP: TASK_TYPE_CHANGING_MOP,
    DreameVacuumTaskType.CHANGING_MOP_PAUSED: TASK_TYPE_CHANGING_MOP_PAUSED,
    DreameVacuumTaskType.FLOOR_MAINTAINING: TASK_TYPE_FLOOR_MAINTAINING,
    DreameVacuumTaskType.FLOOR_MAINTAINING_PAUSED: TASK_TYPE_FLOOR_MAINTAINING_PAUSED,
    DreameVacuumTaskType.ARRANGING_ITEMS: TASK_TYPE_ARRANGING_ITEMS,
    DreameVacuumTaskType.ARRANGING_ITEMS_PAUSED: TASK_TYPE_ARRANGING_ITEMS_PAUSED,
    DreameVacuumTaskType.INTENSIVE_HAIR_CLEANING: TASK_TYPE_INTENSIVE_HAIR_CLEANING,
    DreameVacuumTaskType.ACCESSORY_HANDLING: TASK_TYPE_ACCESSORY_HANDLING,
    DreameVacuumTaskType.INCREASED_DRUM_SPEED_CLEANING: TASK_TYPE_INCREASED_DRUM_SPEED_CLEANING,
    DreameVacuumTaskType.PRESSURIZED_CLEANING: TASK_TYPE_PRESSURIZED_CLEANING,
    DreameVacuumTaskType.STEAM_CLEANING: TASK_TYPE_STEAM_CLEANING,
    DreameVacuumTaskType.STEAM_CLEANING_PAUSED: TASK_TYPE_STEAM_CLEANING_PAUSED,
}

CLEAN_WATER_TANK_STATUS_TO_NAME: Final = {
    DreameVacuumCleanWaterTankStatus.INSTALLED: CLEAN_WATER_TANK_STATUS_INSTALLED,
    DreameVacuumCleanWaterTankStatus.NOT_INSTALLED: CLEAN_WATER_TANK_STATUS_NOT_INSTALLED,
    DreameVacuumCleanWaterTankStatus.LOW_WATER: CLEAN_WATER_TANK_STATUS_LOW_WATER,
    DreameVacuumCleanWaterTankStatus.CHECKING: CLEAN_WATER_TANK_STATUS_INSTALLED,
}

DIRTY_WATER_TANK_STATUS_TO_NAME: Final = {
    DreameVacuumDirtyWaterTankStatus.INSTALLED: DIRTY_WATER_TANK_STATUS_INSTALLED,
    DreameVacuumDirtyWaterTankStatus.NOT_INSTALLED_OR_FULL: DIRTY_WATER_TANK_STATUS_NOT_INSTALLED_OR_FULL,
}

DUST_BAG_STATUS_TO_NAME: Final = {
    DreameVacuumDustBagStatus.INSTALLED: DUST_BAG_STATUS_INSTALLED,
    DreameVacuumDustBagStatus.NOT_INSTALLED: DUST_BAG_STATUS_NOT_INSTALLED,
    DreameVacuumDustBagStatus.CHECK: DUST_BAG_STATUS_CHECK,
}

AUTO_LDS_COVERAGE_TO_NAME = {
    DreameVacuumAutoLDSCoverage.OFF: STATE_OFF,
    DreameVacuumAutoLDSCoverage.SECURITY: AUTO_LDS_COVERAGE_SECURITY,
    DreameVacuumAutoLDSCoverage.EXTREME: AUTO_LDS_COVERAGE_EXTREME,
}

DETERGENT_STATUS_TO_NAME: Final = {
    DreameVacuumDetergentStatus.INSTALLED: DETERGENT_STATUS_INSTALLED,
    DreameVacuumDetergentStatus.DISABLED: DETERGENT_STATUS_DISABLED,
    DreameVacuumDetergentStatus.LOW_DETERGENT: DETERGENT_STATUS_LOW_DETERGENT,
}

HOT_WATER_STATUS_TO_NAME: Final = {
    DreameVacuumHotWaterStatus.DISABLED: HOT_WATER_STATUS_DISABLED,
    DreameVacuumHotWaterStatus.ENABLED: HOT_WATER_STATUS_ENABLED,
}

STATION_DRAINAGE_STATUS_TO_NAME: Final = {
    DreameVacuumStationDrainageStatus.IDLE: STATE_IDLE,
    DreameVacuumStationDrainageStatus.DRAINING: STATION_DRAINAGE_STATUS_DRAINING,
}

DUST_BAG_DRYING_STATUS_TO_NAME: Final = {
    DreameVacuumDustBagDryingStatus.IDLE: STATE_IDLE,
    DreameVacuumDustBagDryingStatus.DRYING: SELF_WASH_BASE_STATUS_DRYING,
    DreameVacuumDustBagDryingStatus.PAUSED: SELF_WASH_BASE_STATUS_PAUSED,
}

ERROR_CODE_TO_IMAGE_INDEX: Final = {
    DreameVacuumErrorCode.BUMPER: 1,
    DreameVacuumErrorCode.BUMPER_REPEAT: 1,
    DreameVacuumErrorCode.DROP: 2,
    DreameVacuumErrorCode.DROP_REPEAT: 2,
    DreameVacuumErrorCode.CLIFF: 3,
    DreameVacuumErrorCode.GESTURE: 15,
    DreameVacuumErrorCode.BRUSH: 4,
    DreameVacuumErrorCode.SIDE_BRUSH: 5,
    DreameVacuumErrorCode.LEFT_WHEEL_MOTOR: 6,
    DreameVacuumErrorCode.RIGHT_WHEEL_MOTOR: 6,
    DreameVacuumErrorCode.LEFTWHELL_SPEED: 6,
    DreameVacuumErrorCode.RIGHTWHELL_SPEED: 6,
    DreameVacuumErrorCode.TURN_SUFFOCATE: 7,
    DreameVacuumErrorCode.FORWARD_SUFFOCATE: 7,
    DreameVacuumErrorCode.BOX: 8,
    DreameVacuumErrorCode.BOX_FULL: 9,
    DreameVacuumErrorCode.FAN: 9,
    DreameVacuumErrorCode.FILTER_BLOCKED: 9,
    DreameVacuumErrorCode.CHARGE_FAULT: 12,
    DreameVacuumErrorCode.CHARGE_NO_ELECTRIC: 16,
    DreameVacuumErrorCode.BATTERY_LOW: 20,
    DreameVacuumErrorCode.BATTERY_FAULT: 29,
    DreameVacuumErrorCode.INFRARED_FAULT: 39,
    DreameVacuumErrorCode.LDS_ERROR: 48,
    DreameVacuumErrorCode.LDS_BUMPER: 49,
    DreameVacuumErrorCode.EDGE: 54,
    DreameVacuumErrorCode.EDGE_2: 54,
    DreameVacuumErrorCode.CARPET: 55,
    DreameVacuumErrorCode.ULTRASONIC: 58,
    DreameVacuumErrorCode.ROUTE: 61,
    DreameVacuumErrorCode.ROUTE_2: 62,
    DreameVacuumErrorCode.BLOCKED: 63,
    DreameVacuumErrorCode.BLOCKED_2: 63,
    DreameVacuumErrorCode.BLOCKED_3: 64,
    DreameVacuumErrorCode.RESTRICTED: 65,
    DreameVacuumErrorCode.ROBOT_IN_HIDDEN_ROOM: 65,
    DreameVacuumErrorCode.RESTRICTED_2: 65,
    DreameVacuumErrorCode.RESTRICTED_3: 65,
    DreameVacuumErrorCode.MOP_REMOVED: 69,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE: 69,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE_2: 69,
    DreameVacuumErrorCode.BIN_FULL: 101,
    DreameVacuumErrorCode.BIN_FULL_2: 101,
    DreameVacuumErrorCode.BIN_OPEN: 102,
    DreameVacuumErrorCode.BIN_OPEN_2: 102,
    DreameVacuumErrorCode.WATER_TANK: 105,
    DreameVacuumErrorCode.CLEAN_TANK_LEVEL: 105,
    DreameVacuumErrorCode.DIRTY_WATER_TANK: 106,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_2: 106,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_BLOCKED: 106,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_PUMP: 106,
    DreameVacuumErrorCode.DIRTY_TANK_LEVEL: 118,
    DreameVacuumErrorCode.WATER_TANK_DRY: 107,
    DreameVacuumErrorCode.MOP_PAD: 111,
    DreameVacuumErrorCode.WET_MOP_PAD: 111,
    DreameVacuumErrorCode.WASHBOARD_LEVEL: 114,
    DreameVacuumErrorCode.CLEAN_MOP_PAD: 114,
    DreameVacuumErrorCode.NO_MOP_IN_STATION: 69,
    DreameVacuumErrorCode.DUST_BAG_FULL: 102,
    DreameVacuumErrorCode.DIRTY_TANK_NOT_INSTALLED: 76,
    DreameVacuumErrorCode.CLEAN_TANK_LEVEL: 105,
    DreameVacuumErrorCode.STATION_DISCONNECTED: 117,
    DreameVacuumErrorCode.SELF_TEST_FAILED: 999,
    DreameVacuumErrorCode.WASHBOARD_NOT_WORKING: 111,
    DreameVacuumErrorCode.RETURN_TO_CHARGE_FAILED: 1000,
}

ERROR_CODE_GEN5_TO_IMAGE_INDEX: Final = {
    DreameVacuumErrorCode.BUMPER: 1,
    DreameVacuumErrorCode.BUMPER_REPEAT: 1,
    DreameVacuumErrorCode.DROP: 2,
    DreameVacuumErrorCode.DROP_REPEAT: 2,
    DreameVacuumErrorCode.CLIFF: 3,
    DreameVacuumErrorCode.BRUSH: 4,
    DreameVacuumErrorCode.SIDE_BRUSH: 5,
    DreameVacuumErrorCode.LEFT_WHEEL_MOTOR: 6,
    DreameVacuumErrorCode.RIGHT_WHEEL_MOTOR: 6,
    DreameVacuumErrorCode.LEFTWHELL_SPEED: 6,
    DreameVacuumErrorCode.RIGHTWHELL_SPEED: 6,
    DreameVacuumErrorCode.TURN_SUFFOCATE: 7,
    DreameVacuumErrorCode.FORWARD_SUFFOCATE: 7,
    DreameVacuumErrorCode.ROBOT_STUCK_2: 7,
    DreameVacuumErrorCode.BOX: 8,
    DreameVacuumErrorCode.BOX_FULL: 9,
    DreameVacuumErrorCode.FAN: 9,
    DreameVacuumErrorCode.FILTER_BLOCKED: 9,
    DreameVacuumErrorCode.CHARGE_FAULT: 12,
    DreameVacuumErrorCode.GESTURE: 15,
    DreameVacuumErrorCode.CHARGE_NO_ELECTRIC: 16,
    DreameVacuumErrorCode.OPTICAL_FLOW: 19,
    DreameVacuumErrorCode.INTERNAL_ERROR: 19,
    DreameVacuumErrorCode.INTERNAL_ERROR_2: 19,
    DreameVacuumErrorCode.UNKNOWN: 19,
    DreameVacuumErrorCode.BATTERY_LOW: 20,
    DreameVacuumErrorCode.LOW_BATTERY_TURN_OFF: 20,
    DreameVacuumErrorCode.BATTERY_FAULT: 29,
    DreameVacuumErrorCode.INFRARED_FAULT: 19,
    DreameVacuumErrorCode.BLOCKED: 47,
    DreameVacuumErrorCode.LDS_ERROR: 48,
    DreameVacuumErrorCode.LDS_BUMPER: 49,
    DreameVacuumErrorCode.EDGE: 54,
    DreameVacuumErrorCode.EDGE_2: 54,
    DreameVacuumErrorCode.CARPET: 55,
    DreameVacuumErrorCode.ULTRASONIC: 58,
    DreameVacuumErrorCode.ROUTE: 61,
    DreameVacuumErrorCode.ROUTE_2: 62,
    DreameVacuumErrorCode.BLOCKED_2: 63,
    DreameVacuumErrorCode.BLOCKED_3: 64,
    DreameVacuumErrorCode.RESTRICTED: 65,
    DreameVacuumErrorCode.ROBOT_IN_HIDDEN_ROOM: 65,
    DreameVacuumErrorCode.RESTRICTED_2: 65,
    DreameVacuumErrorCode.RESTRICTED_3: 65,
    DreameVacuumErrorCode.NO_GO_ZONE: 65,
    DreameVacuumErrorCode.MOP_REMOVED: 69,
    DreameVacuumErrorCode.MOP_REMOVED_2: 69,
    DreameVacuumErrorCode.NO_MOP_IN_STATION: 69,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE: 69,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE_2: 69,
    DreameVacuumErrorCode.MOP_INSTALL_FAILED: 74,
    DreameVacuumErrorCode.DIRTY_TANK_NOT_INSTALLED: 76,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_FULL: 76,
    DreameVacuumErrorCode.LDS_FAILED_TO_LIFT: 79,
    DreameVacuumErrorCode.ROBOT_STUCK: 80,
    DreameVacuumErrorCode.ROBOT_STUCK_REPEAT: 80,
    DreameVacuumErrorCode.SLIPPERY_FLOOR: 82,
    DreameVacuumErrorCode.RETRACTABLE_LEG_STUCK: 88,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_TABLES: 91,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_PASSAGE: 92,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_THRESHOLD: 93,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_LOW_LYING_AREA: 94,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_RAMP: 95,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_OBSTACLE: 96,
    DreameVacuumErrorCode.BLOCKED_BY_OBSTACLE: 96,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_PET: 97,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_SLIPPERY_SURFACE: 98,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_CARPET: 99,
    DreameVacuumErrorCode.BIN_FULL: 101,
    DreameVacuumErrorCode.BIN_FULL_2: 101,
    DreameVacuumErrorCode.BIN_OPEN: 102,
    DreameVacuumErrorCode.BIN_OPEN_2: 102,
    DreameVacuumErrorCode.DUST_BAG_FULL: 102,
    DreameVacuumErrorCode.WATERBOX_EMPTY: 105,
    DreameVacuumErrorCode.WATER_TANK: 105,
    DreameVacuumErrorCode.CLEAN_TANK_LEVEL: 105,
    DreameVacuumErrorCode.DIRTY_WATER_TANK: 106,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_2: 106,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_BLOCKED: 106,
    DreameVacuumErrorCode.DIRTY_WATER_TANK_PUMP: 106,
    DreameVacuumErrorCode.WATER_TANK_DRY: 107,
    DreameVacuumErrorCode.MOP_PAD: 111,
    DreameVacuumErrorCode.WET_MOP_PAD: 111,
    DreameVacuumErrorCode.WASHBOARD_NOT_WORKING: 111,
    DreameVacuumErrorCode.CLEAN_MOP_PAD: 114,
    DreameVacuumErrorCode.WASHBOARD_LEVEL: 114,
    DreameVacuumErrorCode.STATION_DISCONNECTED: 117,
    DreameVacuumErrorCode.DIRTY_TANK_LEVEL: 118,
    DreameVacuumErrorCode.MOP_NOT_DETECTED: 126,
    DreameVacuumErrorCode.MOP_HOLDER_ERROR: 126,
    DreameVacuumErrorCode.DOCK_ERROR: 128,
    DreameVacuumErrorCode.ROBOT_STUCK_ON_CURTAIN: 130,
    DreameVacuumErrorCode.EDGE_MOP_STOP_ROTATE: 201,
    DreameVacuumErrorCode.EDGE_MOP_DETACHED: 201,
    DreameVacuumErrorCode.MOP_COVER_ERROR: 209,
    DreameVacuumErrorCode.MOP_COVER_ERROR_2: 209,
    DreameVacuumErrorCode.ROLLER_MOP_ERROR: 210,
    DreameVacuumErrorCode.ROLLER_MOP_ERROR_2: 210,
    DreameVacuumErrorCode.ONBOARD_WATER_TANK_EMPTY: 213,
    DreameVacuumErrorCode.ONBOARD_DIRTY_WATER_TANK_FULL: 214,
    DreameVacuumErrorCode.MOP_NOT_INSTALLED: 215,
    DreameVacuumErrorCode.FLUFFING_ROLLER_ERROR: 222,
    DreameVacuumErrorCode.SELF_TEST_FAILED: 999,
    DreameVacuumErrorCode.DRAINAGE_FAILED: 999,
    DreameVacuumErrorCode.RETURN_TO_CHARGE_FAILED: 1000,
    DreameVacuumErrorCode.LDS_ERROR_2: 48,
    DreameVacuumErrorCode.MOP_COVER_ERROR_3: 209,
    DreameVacuumErrorCode.ROLLER_MOP_ERROR_3: 210,
    DreameVacuumErrorCode.INTERNAL_ERROR_3: 19,
    DreameVacuumErrorCode.INTERNAL_ERROR_4: 19,
    DreameVacuumErrorCode.ROBOTIC_ARM_STOPPED: 212,
    DreameVacuumErrorCode.DRAINAGE_OUTLET_FILTER: 998,
}


# Dreame Vacuum error descriptions
ERROR_CODE_TO_ERROR_DESCRIPTION: Final = {
    DreameVacuumErrorCode.NO_ERROR: ["No error", ""],
    DreameVacuumErrorCode.DROP: [
        "Wheels are suspended",
        "Please reposition the robot and restart.",
    ],
    DreameVacuumErrorCode.CLIFF: [
        "Cliff sensor error",
        "Please wipe the cliff sensor and start the cleanup away from the stairs.",
    ],
    DreameVacuumErrorCode.BUMPER: [
        "Collision sensor is stuck",
        "Please clean and gently tap the collision sensor.",
    ],
    DreameVacuumErrorCode.GESTURE: [
        "Robot is tilted",
        "Please move the robot to a level surface and start again.",
    ],
    DreameVacuumErrorCode.BUMPER_REPEAT: [
        "Collision sensor is stuck",
        "Please clean and gently tap the collision sensor.",
    ],
    DreameVacuumErrorCode.DROP_REPEAT: [
        "Wheels are suspended",
        "Please reposition the robot and restart.",
    ],
    DreameVacuumErrorCode.OPTICAL_FLOW: [
        "Optical flow sensor error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.BOX: [
        "Dust bin not installed",
        "Please install the dust bin and filter.",
    ],
    DreameVacuumErrorCode.TANKBOX: [
        "Water tank not installed",
        "Please install the water tank.",
    ],
    DreameVacuumErrorCode.WATERBOX_EMPTY: [
        "Water tank is empty",
        "Please will up the water tank",
    ],
    DreameVacuumErrorCode.BOX_FULL: [
        "The filter not dry or blocked",
        "Please check whether the filter has dried or needs to be cleaned.",
    ],
    DreameVacuumErrorCode.BRUSH: [
        "The main brush wrapped",
        "Please remove the main brush and clean its bristles and bearings.",
    ],
    DreameVacuumErrorCode.SIDE_BRUSH: [
        "The side brush wrapped",
        "Please remove and clean the side brush.",
    ],
    DreameVacuumErrorCode.FAN: [
        "The filter not dry or blocked",
        "Please check whether the filter has dried or needs to be cleaned.",
    ],
    DreameVacuumErrorCode.LEFT_WHEEL_MOTOR: [
        "The robot is stuck, or its left wheel may be blocked by foreign objects",
        "Check whether there is any object stuck in the main wheels and start the robot in a new position.",
    ],
    DreameVacuumErrorCode.RIGHT_WHEEL_MOTOR: [
        "The robot is stuck, or its right wheel may be blocked by foreign objects",
        "Check whether there is any object stuck in the main wheels and start the robot in a new position.",
    ],
    DreameVacuumErrorCode.TURN_SUFFOCATE: [
        "The robot is stuck, or cannot turn",
        "The robot may be blocked or stuck.",
    ],
    DreameVacuumErrorCode.FORWARD_SUFFOCATE: [
        "The robot is stuck, or cannot go forward",
        "The robot may be blocked or stuck.",
    ],
    DreameVacuumErrorCode.CHARGER_GET: [
        "Cannot find base",
        "Please check whether the power cord is plugged in correctly.",
    ],
    DreameVacuumErrorCode.BATTERY_LOW: [
        "Low battery",
        "Battery level is too low. Please charge.",
    ],
    DreameVacuumErrorCode.CHARGE_FAULT: [
        "Charging error",
        "Please use a dry cloth to wipe charging contacts of the robot and auto-empty base.",
    ],
    DreameVacuumErrorCode.BATTERY_PERCENTAGE: ["Battery level error", ""],
    DreameVacuumErrorCode.HEART: [
        "Internal error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.CAMERA_OCCLUSION: [
        "Visual positioning sensor error",
        "Please clean the visual positioning sensor.",
    ],
    DreameVacuumErrorCode.MOVE: [
        "Move sensor error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.FLOW_SHIELDING: [
        "Optical sensor error",
        "Please wipe the optical sensor clean and restart.",
    ],
    DreameVacuumErrorCode.INFRARED_SHIELDING: [
        "Infrared shielding error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.CHARGE_NO_ELECTRIC: [
        "The charging dock is not powered on",
        "The charging dock is not powered on. Please check whether the power cord is plugged in correctly.",
    ],
    DreameVacuumErrorCode.BATTERY_FAULT: [
        "Battery temperature error",
        "Please wait until the battery temperature returns to normal.",
    ],
    DreameVacuumErrorCode.FAN_SPEED_ERROR: [
        "Fan speed sensor error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.LEFTWHELL_SPEED: [
        "Left wheel may be blocked by foreign objects",
        "Check whether there is any object stuck in the main wheels and start the robot in a new position.",
    ],
    DreameVacuumErrorCode.RIGHTWHELL_SPEED: [
        "Right wheel may be blocked by foreign objects",
        "Check whether there is any object stuck in the main wheels and start the robot in a new position.",
    ],
    DreameVacuumErrorCode.BMI055_ACCE: [
        "Accelerometer error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.BMI055_GYRO: [
        "Gyro error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.XV7001: [
        "Gyro error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.LEFT_MAGNET: [
        "Left magnet sensor error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.RIGHT_MAGNET: [
        "Right magnet sensor error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.FLOW_ERROR: [
        "Flow sensor error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.INFRARED_FAULT: [
        "Infrared error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.CAMERA_FAULT: [
        "Camera error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.STRONG_MAGNET: [
        "Strong magnetic field detected",
        "Strong magnetic field detected. Please start away from the virtual wall.",
    ],
    DreameVacuumErrorCode.WATER_PUMP: [
        "Water pump error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.RTC: ["RTC error", "Please try to restart the vacuum-mop."],
    DreameVacuumErrorCode.AUTO_KEY_TRIG: [
        "Internal error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.P3V3: [
        "Internal error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.CAMERA_IDLE: [
        "Internal error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.BLOCKED: [
        "The robot may be blocked or stuck.",
        "Cleanup route is blocked, returning to the dock.",
    ],
    DreameVacuumErrorCode.LDS_ERROR: [
        "Laser distance sensor error",
        "Please check whether the laser distance sensor has any jammed items",
    ],
    DreameVacuumErrorCode.LDS_BUMPER: [
        "Laser distance sensor bumper error",
        "Please check whether the laser distance sensor bumper is jammed",
    ],
    DreameVacuumErrorCode.WATER_PUMP_2: [
        "Water pump error",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.FILTER_BLOCKED: [
        "The filter not dry or blocked",
        "Please check whether the filter has dried or needs to be cleaned",
    ],
    DreameVacuumErrorCode.EDGE: [
        "Edge sensor error",
        "Edge sensor error. Please check and clean it.",
    ],
    DreameVacuumErrorCode.CARPET: [
        "Please start the robot in non-carpet area.",
        "A carpet is detected under the robot when it is mopping. Please move the robot to another place and restart it.",
    ],
    DreameVacuumErrorCode.LASER: [
        "The 3D obstacle avoidance sensor is malfunctioning.",
        "Please try to clean the 3D obstacle avoidance sensor.",
    ],
    DreameVacuumErrorCode.EDGE_2: [
        "Edge sensor error",
        "Edge sensor error. Please check and clean it.",
    ],
    DreameVacuumErrorCode.ULTRASONIC: [
        "The ultrasonic sensor is malfunctioning.",
        "Please restart the robot and try it again.",
    ],
    DreameVacuumErrorCode.NO_GO_ZONE: [
        "No-Go zone or virtual wall detected.",
        "Please move the robot away from the area and restart.",
    ],
    DreameVacuumErrorCode.ROUTE: [
        "Unable to reach the specified area.",
        "Please ensure that all doors in the home are open and clear any obstacles along the path.",
    ],
    DreameVacuumErrorCode.ROUTE_2: [
        "Unable to reach the specified area.",
        "Please try to delete the restricted area in the path.",
    ],
    DreameVacuumErrorCode.BLOCKED_2: [
        "Cleanup route is blocked.",
        "Please ensure that all doors in the home are open and clear any obstacles around the vacuum-mop.",
    ],
    DreameVacuumErrorCode.BLOCKED_3: [
        "Cleanup route is blocked.",
        "Please try to delete the restricted area or move the vacuum-mop out of this area.",
    ],
    DreameVacuumErrorCode.RESTRICTED: [
        "Detected that the vacuum-mop is in a restricted area.",
        "Please move the vacuum-mop out of this area.",
    ],
    DreameVacuumErrorCode.RESTRICTED_2: [
        "Detected that the vacuum-mop is in a restricted area.",
        "Please move the vacuum-mop out of this area.",
    ],
    DreameVacuumErrorCode.RESTRICTED_3: [
        "Detected that the vacuum-mop is in a restricted area.",
        "Please move the vacuum-mop out of this area.",
    ],
    DreameVacuumErrorCode.REMOVE_MOP: [
        "Mopping completed. Please remove and clean the mop in time.",
        "",
    ],
    DreameVacuumErrorCode.MOP_REMOVED: [
        "The mop pad comes off during the cleaning task.",
        "The mop pads come off, install them before resuming working.",
    ],
    DreameVacuumErrorCode.MOP_REMOVED_2: [
        "The mop pad comes off during the cleaning task.",
        "The mop pads come off, install them before resuming working.",
    ],
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE: [
        "Mop Pad Stops Rotating.",
        "The mop pad has stopped rotating, please check.",
    ],
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE_2: [
        "Mop Pad Stops Rotating.",
        "The mop pad has stopped rotating, please check.",
    ],
    DreameVacuumErrorCode.MOP_INSTALL_FAILED: [
        "Mop pad installation failed.",
        "Failed to install mop pads. Please install manually.",
    ],
    DreameVacuumErrorCode.LOW_BATTERY_TURN_OFF: [
        "Low battery. Robot will shut down soon.",
        "",
    ],
    DreameVacuumErrorCode.DIRTY_TANK_NOT_INSTALLED: [
        "The used water tank of robot is not installed.",
        "Please make sure that the used water tank of robot is installed properly, and then start the task.",
    ],
    DreameVacuumErrorCode.ROBOT_IN_HIDDEN_ROOM: [
        "Hidden area. Please move the robot to the appropriate area and retry.",
        "The area has been hidden. To reuse it, please go to the specific map and click the gray area to manually recover the hidden area.",
    ],
    DreameVacuumErrorCode.LDS_FAILED_TO_LIFT: [
        "Failed to lift LDS module.",
        "Please clear any debris around the LDS and move robot to an open area to resume the task.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK: [
        "Move robot to an open area and resume the task.",
        "LDS cannot be raised here for positioning.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_REPEAT: [
        "Move robot to an open area and resume the task.",
        "1. Robot failed to position because the area under the furniture is uneven or has changed.\n2. Start the task or control the LDS to rise in an open area",
    ],
    DreameVacuumErrorCode.SLIPPERY_FLOOR: [
        "Slippery floor. Please try again later.",
        "Slippery floor. Robot failed to get through obstacles. You can wait for robot to retry, or clear the water around it and resume the task.",
    ],
    DreameVacuumErrorCode.CHECK_MOP_INSTALL: [
        "Check mop Installation Instructions",
        "Please check if the mop is installed properly.",
    ],
    DreameVacuumErrorCode.DIRTY_WATER_TANK_FULL: [
        "Abnormal water level in the robot's used water tank",
        "The robot's used water tank is too dirty. Please remove and clean it in time.",
    ],
    DreameVacuumErrorCode.RETRACTABLE_LEG_STUCK: [
        "Retractable legs may be tangled.",
        "Please check if the retractable legs are tangled.",
    ],
    DreameVacuumErrorCode.INTERNAL_ERROR: [
        "Internal Error",
        "Malfunction due to an internal error. Try to restart the robot.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_2: [
        "The robot is stuck",
        "The robot may be blocked or stuck. Please clear surrounding.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_TABLES: [
        "The robot is stuck",
        "Robot stuck among the tables and chairs\n1. Please move robot to an open area and restart the task.\n2. It is recommended to arrange the tables and chairs neatly to prevent robot from getting stuck.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_PASSAGE: [
        "The robot is stuck",
        "Robot stuck in the narrow passage\n1. Please move robot to an open area and restart the task.\n2. It is recommended to set the narrow passage as a no-go zone to prevent the robot from getting stuck.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_THRESHOLD: [
        "The robot is stuck",
        "Robot stuck at the step/threshold\n1. Please move robot to an open area and restart the task.\n2. It is recommended to set the step/threshold as an impassable threshold to prevent robot from getting stuck.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_LOW_LYING_AREA: [
        "The robot is stuck",
        "Robot stuck in a low-clearance area\n1. Please move robot to an open area and restart the task.\n2. It is recommended to set the low area as a no-go zone to prevent robot from getting stuck.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_RAMP: [
        "Robot has detected Easy-to-Fall ramps on the path",
        "It is recommended to set passable thresholds if there are no Easy-to-Fall ramps on the path.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_OBSTACLE: [
        "Robot has detected obstacles on the path",
        "Please remove obstacles from the path and restart the task.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_PET: [
        "Robot has detected people or pets on the path",
        "Please ensure that no people or pets are on the path when restarting the task.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_SLIPPERY_SURFACE: [
        "Robot is stuck due to slipping",
        "Robot is stuck due to slipping. Please clean the main wheels.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_CARPET: [
        "The robot is stuck",
        "Robot slips on the carpet\n1. Please move robot away from the carpet and restart the task\n2. It is recommended to set the carpet as a no-go zone to prevent robot from getting stuck.",
    ],
    DreameVacuumErrorCode.BIN_FULL: [
        "The dust collection bag is full, or the air duct is blocked.",
        "The system detects that the dust collection bag is full, or the air duct is blocked.",
    ],
    DreameVacuumErrorCode.BIN_OPEN: [
        "The upper cover of auto-empty base is not closed, or the dust collection bag is not installed.",
        "The system detects that the upper cover of auto-empty base is not closed, or the dust collection bag is not installed.",
    ],
    DreameVacuumErrorCode.BIN_OPEN_2: [
        "The upper cover of auto-empty base is not closed, or the dust collection bag is not installed.",
        "The system detects that the upper cover of auto-empty base is not closed, or the dust collection bag is not installed.",
    ],
    DreameVacuumErrorCode.BIN_FULL_2: [
        "The dust collection bag is full, or the air duct is blocked.",
        "The system detects that the dust collection bag is full, or the air duct is blocked.",
    ],
    DreameVacuumErrorCode.WATER_TANK: [
        "The clean water tank is not installed.",
        "The clean water tank is not installed, please install it.",
    ],
    DreameVacuumErrorCode.DIRTY_WATER_TANK: [
        "The dirty water tank is full or not installed.",
        "Check whether the dirty water tank is full and the dirty water tank is installed.",
    ],
    DreameVacuumErrorCode.WATER_TANK_DRY: [
        "Low water level in the clean water tank.",
        "Insufficient water in the fresh tank, please add water. Otherwise, the robot will not return to the base to have the mop pad cleaned during the cleaning task.",
    ],
    DreameVacuumErrorCode.DIRTY_WATER_TANK_BLOCKED: [
        "Dirty water tank blocked.",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.DIRTY_WATER_TANK_PUMP: [
        "Dirty water tank pump error.",
        "Please try to restart the vacuum-mop.",
    ],
    DreameVacuumErrorCode.MOP_PAD: [
        "The washboard is not installed properly.",
        "The washboard is not installed and the robot cannot return to the self-wash base. Please ensure that the washboard is installed and the clasps on both sides are tightly fastened.",
    ],
    DreameVacuumErrorCode.WET_MOP_PAD: [
        "The water level of the washboard is abnormal, please clean the washboard timely.",
        "The water level of the washboard is abnormal. Please clean it timely to avoid blockage. If the problem still cannot be solved, please contact customer service.",
    ],
    DreameVacuumErrorCode.CLEAN_MOP_PAD: [
        "The cleaning task is complete, please clean the mop pad washboard.",
        "Please clean the mop pad washboard in time to avoid stains or odor.",
    ],
    DreameVacuumErrorCode.CLEAN_TANK_LEVEL: [
        "Please fill the clean water tank.",
        "The water in the clean water tank is about to be used up. Check and fill the clean water tank promptly.",
    ],
    DreameVacuumErrorCode.STATION_DISCONNECTED: [
        "Base station not powered on.",
        "Please check whether the power is off or the power switch is on in your home, and re-plug both ends of the base station power supply.",
    ],
    DreameVacuumErrorCode.DIRTY_TANK_LEVEL: [
        "The water level in the used water tank is too high.",
        "Please check if the used water tank is full.",
    ],
    DreameVacuumErrorCode.WASHBOARD_LEVEL: [
        "Water level in the washboard is too high.",
        "Please clean the used water tank and washboard in time.",
    ],
    DreameVacuumErrorCode.NO_MOP_IN_STATION: [
        "Check if the mop pad is in the base station, or install the mop pad onto the robot manually.",
        "The mop pad is out of place. Retry after putting it into the base station or install it onto the robot manually.",
    ],
    DreameVacuumErrorCode.DUST_BAG_FULL: [
        "Check whether the dust collection bag is full.",
        "If so, replace the bag. Please clean the auto-empty vents of the dust bin and the base station regularly.",
    ],
    DreameVacuumErrorCode.SELF_TEST_FAILED: [
        "Self test failed.",
        "There is no water in the clean water tank of the upper and lower water modules.",
    ],
    DreameVacuumErrorCode.WASHBOARD_NOT_WORKING: [
        "Washboard stops working. Please check.",
        "Washboard stops working. Please follow troubleshooting steps as below:\n1. Check if the washboard is tangled. Clean up before use\n2. Check if the washboard is installed properly\n3.如仍未解决请联系客服",
    ],
    DreameVacuumErrorCode.DRAINAGE_FAILED: [
        "Abnormal water drainage from used water tank",
        "Sewage pump error. Please contact customer service.",
    ],
    DreameVacuumErrorCode.MOP_NOT_DETECTED: [
        "Mop not detected.",
        "Mop not detected. Please install and continue the task.",
    ],
    DreameVacuumErrorCode.MOP_HOLDER_ERROR: [
        "Mop holder error in the dock.",
        "Mop holder quantity/placement error in the dock. Please install the mop holder or adjust its placement to ensure proper cleaning.",
    ],
    DreameVacuumErrorCode.DOCK_ERROR: [
        "Dock Error",
        "Please check the dock and try the following steps:\n1. Make sure the hatch is fully closed.\n2. Make sure the three groups of mops are placed on the hatch in red-yellow-blue order. If the mops are currently on the transport carrier or washboard, put them back on the hatch in this order and try again.\n3. Check for any debris inside the dock. Do not place your hand, robot, or other items in the washboard when switching mops.",
    ],
    DreameVacuumErrorCode.WASH_FAILED: [
        "Failed to wash dirty mop.",
        "Please check the dock and try the following steps:\n1. Please manually attach the mop that needs washing to robot.\n2. Please install other dirty mops onto the hatch.\n3. Go to the app → Dock Functions → Wash to restart the mop-washing task.",
    ],
    DreameVacuumErrorCode.ROBOT_STUCK_ON_CURTAIN: [
        "The robot is stuck",
        "Robot slips in the curtain area\n1. Please move robot away from the curtain area and restart the task.\n2. Robot cannot clean this curtain area. It is recommended to remove it.",
    ],
    DreameVacuumErrorCode.EDGE_MOP_STOP_ROTATE: [
        "Edge mop stopped rotating.",
        "Edge mop stopped rotating. Please follow these steps:\n1. Check if robot is on a carpet. Friction between the edge mop and carpet may stop it from rotating. Move robot to a non-carpet area and resume cleaning.\n2. Check if the edge mop is tangled. If so, remove them and resume cleaning.",
    ],
    DreameVacuumErrorCode.EDGE_MOP_DETACHED: [
        "Edge mop detached.",
        "Edge mop not detected. Please install it before resuming cleaning.",
    ],
    DreameVacuumErrorCode.CHASSIS_LIFT_MALFUNCTION: [
        "Chassis lift malfunction.",
        "Chassis lift malfunction. Please restart the task. If the issue persists, contact customer service.",
    ],
    DreameVacuumErrorCode.INTERNAL_ERROR_2: [
        "Internal Error",
        "Malfunction due to an internal error. Try to restart the robot.",
    ],
    DreameVacuumErrorCode.MOP_COVER_ERROR: [
        "Mop cover error.",
        "Check for any debris near the roller mop and mop cover. Clean the roller mop to prevent the cover from getting stuck. After that, place the robot flat and resume the task. If the issue persists, please contact customer service.",
    ],
    DreameVacuumErrorCode.ROLLER_MOP_ERROR: [
        "Roller mop error.",
        "Check for any debris near the roller mop and mop cover. Clean the roller mop to prevent it from getting stuck. After that, place the robot flat and resume the task. If the issue persists, please contact customer service.",
    ],
    DreameVacuumErrorCode.ONBOARD_WATER_TANK_EMPTY: [
        "Low water level in robot’s clean water box.",
        "Low water level in robot’s clean water box. Please refill promptly.",
    ],
    DreameVacuumErrorCode.ONBOARD_DIRTY_WATER_TANK_FULL: [
        "Robot's used water box is full. Please empty it promptly.",
        "Please take out the box and empty it. Alternatively, you can move robot to the dock for mop-washing (this will also drain the used water).",
    ],
    DreameVacuumErrorCode.MOP_NOT_INSTALLED: [
        "Mop Not Installed",
        "Please confirm the roller mop is properly installed before starting or resuming the task.",
    ],
    DreameVacuumErrorCode.ROLLER_MOP_ERROR_2: [
        "Roller mop error.",
        "Check for any debris near the roller mop and mop cover. Clean the roller mop to prevent it from getting stuck. After that, place the robot flat and resume the task. If the issue persists, please contact customer service.",
    ],
    DreameVacuumErrorCode.FLUFFING_ROLLER_ERROR: [
        "Fluffing Roller Error.",
        "1. Turn robot over with the bottom facing up. Press the release button on one side of the roller mop to take it out, then clean any debris around it.\n2. Press the orange clip and take out the fluffing roller. Clean any hair or debris on it.\n3. After cleaning, install the fluffing roller and press the clip firmly. Then install the roller mop, place the robot flat, and resume the task.\nIf the issue persists, please check more details or contact customer service.",
    ],
    DreameVacuumErrorCode.MOP_COVER_ERROR_2: [
        "Mop cover error.",
        "Check for any debris near the roller mop and mop cover. Clean the roller mop to prevent the cover from getting stuck. After that, place the robot flat and resume the task. If the issue persists, please contact customer service.",
    ],
    DreameVacuumErrorCode.BLOCKED_BY_OBSTACLE: [
        "Robot blocked by obstacle",
        "Please check for any obstacles in front of the robot and remove them.",
    ],
    DreameVacuumErrorCode.RETURN_TO_CHARGE_FAILED: [
        "Failed to return to charge.",
        "Please check the base station.\n1. Check if the ramp extension plate is installed down to the base station;\n2. Check if the base station is powered on;\n3. Make sure there is no obstacle in front of the base station.",
    ],
    DreameVacuumErrorCode.ROBOTIC_ARM_STOPPED: [
        "Robotic arm stopped", 
        "Please press and hold the Dock button and the Robotic Arm On/Off button to reset before using again."
    ],
    DreameVacuumErrorCode.DRAINAGE_OUTLET_FILTER: [
        "The wastewater outlet filter of robot is clogged", 
        "Please clean the wastewater outlet filter of the robot promptly to ensure smooth water flow."
    ],
    DreameVacuumErrorCode.MAIN_WHEELS_ERROR: [
        "Main wheels error", 
        "Wheel anomaly detected. The cleaning task has been paused. You can try to resume cleaning using the button on robot or via the app. If the issue persists, please contact us for assistance."],
    DreameVacuumErrorCode.LDS_ERROR_2: [
        "Laser distance sensor error",
        "Please check whether the laser distance sensor has any jammed items",
    ],
    DreameVacuumErrorCode.MOP_COVER_ERROR_3: [
        "Mop cover error.",
        "Check for any debris near the roller mop and mop cover. Clean the roller mop to prevent the cover from getting stuck. After that, place the robot flat and resume the task. If the issue persists, please contact customer service.",
    ],
    DreameVacuumErrorCode.ROLLER_MOP_ERROR_3: [
        "Roller mop error.",
        "Check for any debris near the roller mop and mop cover. Clean the roller mop to prevent it from getting stuck. After that, place the robot flat and resume the task. If the issue persists, please contact customer service.",
    ],
    DreameVacuumErrorCode.INTERNAL_ERROR_3: [
        "Internal Error",
        "Malfunction due to an internal error. Try to restart the robot.",
    ],
    DreameVacuumErrorCode.INTERNAL_ERROR_4: [
        "Internal Error",
        "Malfunction due to an internal error. Try to restart the robot.",
    ],
}

# Dreame Vacuum low water warning descriptions
LOW_WATER_WARNING_CODE_TO_DESCRIPTION: Final = {
    DreameVacuumLowWaterWarning.NO_WARNING: ["No warning", ""],
    DreameVacuumLowWaterWarning.NO_WATER_LEFT_DISMISS: ["No warning", ""],
    DreameVacuumLowWaterWarning.NO_WATER_LEFT: [
        "Please fill the clean water tank.",
        "The water in the clean water tank is about to be used up. Check and fill the clean water tank promptly.",
    ],
    DreameVacuumLowWaterWarning.NO_WATER_LEFT_AFTER_CLEAN: [
        "Please fill the clean water tank.",
        "Mop pad has been cleaned. Detected that the water in the clean water tank is insufficient, please fill the clean water tank and empty the used water tank.",
    ],
    DreameVacuumLowWaterWarning.NO_WATER_FOR_CLEAN: [
        "Low water level in the clean water tank.",
        "Robot has switched to Vacuuming Mode.",
    ],
    DreameVacuumLowWaterWarning.LOW_WATER: [
        "About to run out of water",
        "Please fill the clean water tank.",
    ],
    DreameVacuumLowWaterWarning.TANK_NOT_INSTALLED: [
        "The clean water tank is not installed.",
        "Please check the clean water tank",
    ],
}

CONSUMABLE_TO_LIFE_WARNING_DESCRIPTION: Final = {
    DreameVacuumProperty.MAIN_BRUSH_LEFT: [
        [
            "Main brush must be replaced",
            "The main brush is worn out. Please replace it in time and reset the counter.",
        ],
        [
            "Main brush needs to be replaced soon",
            "The main brush is nearly worn out. Please replace it in time.",
        ],
    ],
    DreameVacuumProperty.SIDE_BRUSH_LEFT: [
        [
            "Side brush must be replaced",
            "The side brush is worn out. Please replace it and reset the counter.",
        ],
        [
            "Side brush needs to be replaced soon",
            "The side brush is nearly worn out. Please replace it as soon as possible.",
        ],
    ],
    DreameVacuumProperty.FILTER_LEFT: [
        [
            "Filter must be replaced",
            "The filter is worn out. Please replace it in time and reset the counter.",
        ],
        [
            "Filter needs to be replaced soon",
            "The filter is nearly worn out. Please replace it in time.",
        ],
    ],
    DreameVacuumProperty.SENSOR_DIRTY_LEFT: [
        ["Sensors must be cleaned", "Please clean the sensors and reset the counter"]
    ],
    DreameVacuumProperty.TANK_FILTER_LEFT: [
        [
            "Tank filter must be replaced",
            "The tank filter is worn out. Please replace it in time and reset the counter.",
        ],
        [
            "Tank filter needs to be replaced soon",
            "The tank filter is nearly worn out. Please replace it in time.",
        ],
    ],
    DreameVacuumProperty.MOP_PAD_LEFT: [
        ["Mop Pad Worn Out", "Please replace the mop pad and reset the counter."],
        ["Mop Pad Nearly Worn Out", "Please replace the mop pad timely."],
    ],
    DreameVacuumProperty.SILVER_ION_LEFT: [
        [
            "Silver Ion Sterilizer Deteriorated",
            "Please replace the silver ion sterilizer and reset the counter.",
        ],
        [
            "Silver Ion Sterilizer Near to Deterioration",
            "Please replace the silver ion sterilizer timely.",
        ],
    ],
    DreameVacuumProperty.DETERGENT_LEFT: [
        [
            "The detergent is used up",
            "Please replace the detergent cartridge it and reset the counter.",
        ],
        [
            "The detergent is about to be used up",
            "The detergent is about to be used up, please replace it in time.",
        ],
    ],
    DreameVacuumProperty.SQUEEGEE_LEFT: [
        ["Squeegee Worn Out", "Please replace the squeegee and reset the counter."],
        ["Squeegee Nearly Worn Out", "Please replace the squeegee timely."],
    ],
    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT: [
        [
            "Onboard dirty water tank needs to be cleaned",
            "Please clean the onboard dirty water tank and reset the counter.",
        ]
    ],
    DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_LEFT: [
        [
            "Dirty water channel needs to be cleaned",
            "Please clean the dirty water channel and reset the counter.",
        ]
    ],
    DreameVacuumProperty.DEODORIZER_LEFT: [
        [
            "Used water tank deodorizer has been exhausted.",
            "Used water tank deodorizer has been exhausted. Please replace it.",
        ],
        [
            "Used water tank deodorizer is running out.",
            "Used water tank deodorizer is running out. Please replace it.",
        ],
    ],
    DreameVacuumProperty.WHEEL_DIRTY_LEFT: [
        ["Omnidirectional wheel needs to be cleaned", "Please clean omnidirectional wheel and reset the counter."]
    ],
    DreameVacuumProperty.SCALE_INHIBITOR_LEFT: [
        ["Scale inhibitor has been exhausted", "Please replace the scale inhibitor and reset the counter."],
        ["Scale inhibitor is running out", "Please replace the scale inhibitor timely."],
    ],
    DreameVacuumProperty.FLUFFING_ROLLER_DIRTY_LEFT: [
        ["Fluffing roller needs to be cleaned", "Please clean fluffing roller and reset the counter."]
    ],
    DreameVacuumProperty.ROLLER_MOP_FILTER_DIRTY_LEFT: [
        ["Roller mop filter needs to be cleaned", "Please clean roller mop filter and reset the counter."]
    ],
    DreameVacuumProperty.WATER_OUTLET_FILTER_DIRTY_LEFT: [
        ["Water outlet filter needs to be cleaned", "Please clean water outlet filter and reset the counter."]
    ],
}
