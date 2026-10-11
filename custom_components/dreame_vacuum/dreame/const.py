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
WATER_TANK_IN_STATION: Final = "in_station"

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

PROBLEM_TYPE_ERROR: Final = "error"
PROBLEM_TYPE_WARNING: Final = "warning"
PROBLEM_TYPE_LOW_WATER: Final = "low_water"
PROBLEM_TYPE_DOCK: Final = "dock"

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
ATTR_ROOM_ICON: Final = "room_icon"
ATTR_ROOM_NAME: Final = "room_name"
ATTR_RECOVERY_MAP: Final = "recovery_map"
ATTR_ICON: Final = "icon"
ATTR_TYPE: Final = "type"
ATTR_CODE: Final = "code"
ATTR_ITEMS: Final = "items"
ATTR_ORDER: Final = "order"
ATTR_DID: Final = "did"
ATTR_STATUS: Final = "status"
ATTR_CLEANING_MODE: Final = "cleaning_mode"
ATTR_SUCTION_LEVEL: Final = "suction_level"
ATTR_WASHING_MODE: Final = "washing_mode"
ATTR_WATER_TANK: Final = "water_tank"
ATTR_TIMING_CLEAN: Final = "timing_clean"
ATTR_CURRENT_MOP_TYPE: Final = "current_mop_type"
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
    DreameVacuumWaterTank.IN_STATION: WATER_TANK_IN_STATION,
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
    DreameVacuumErrorCode.BIN_FULL_2: ERROR_BIN_FULL,
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
