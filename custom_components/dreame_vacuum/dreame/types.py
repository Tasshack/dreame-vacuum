from __future__ import annotations

from typing import Any, Dict, Final, List, Optional, Union
from enum import IntEnum
from dataclasses import dataclass
from datetime import datetime


SEGMENT_TYPE_CODE_TO_NAME: Final = {
    0: "Room",
    1: "Living Room",
    2: "Primary Bedroom",
    3: "Study",
    4: "Kitchen",
    5: "Dining Hall",
    6: "Bathroom",
    7: "Balcony",
    8: "Corridor",
    9: "Utility Room",
    10: "Closet",
    11: "Meeting Room",
    12: "Office",
    13: "Fitness Area",
    14: "Recreation Area",
    15: "Secondary Bedroom",
}

SEGMENT_TYPE_CODE_TO_HA_ICON: Final = {
    0: "mdi:home-outline",
    1: "mdi:sofa-outline",
    2: "mdi:bed-king-outline",
    3: "mdi:bookshelf",
    4: "mdi:chef-hat",
    5: "mdi:room-service-outline",
    6: "mdi:toilet",
    7: "mdi:flower-outline",
    8: "mdi:foot-print",
    9: "mdi:archive-outline",
    10: "mdi:hanger",
    11: "mdi:presentation",
    12: "mdi:monitor-shimmer",
    13: "mdi:dumbbell",
    14: "mdi:gamepad-variant-outline",
    15: "mdi:bed-single-outline",
}

ATTR_A: Final = "a"
ATTR_X: Final = "x"
ATTR_X0: Final = "x0"
ATTR_X1: Final = "x1"
ATTR_X2: Final = "x2"
ATTR_X3: Final = "x3"
ATTR_Y: Final = "y"
ATTR_Y0: Final = "y0"
ATTR_Y1: Final = "y1"
ATTR_Y2: Final = "y2"
ATTR_Y3: Final = "y3"
ATTR_CALIBRATION: Final = "calibration_points"
ATTR_CHARGER: Final = "charger_position"
ATTR_IS_EMPTY: Final = "is_empty"
ATTR_NO_GO_AREAS: Final = "no_go_areas"
ATTR_NO_MOPPING_AREAS: Final = "no_mopping_areas"
ATTR_WALLS: Final = "walls"
ATTR_ROOMS: Final = "rooms"
ATTR_ROBOT_POSITION: Final = "vacuum_position"
ATTR_MAP_ID: Final = "map_id"
ATTR_MAP_NAME: Final = "map_name"
ATTR_ROTATION: Final = "rotation"
ATTR_TIMESTAMP: Final = "timestamp"
ATTR_UPDATED: Final = "updated_at"
ATTR_USED_TIMES: Final = "used_times"
ATTR_ACTIVE_AREAS: Final = "active_areas"
ATTR_ACTIVE_SEGMENTS: Final = "active_segments"
ATTR_FRAME_ID: Final = "frame_id"
ATTR_MAP_INDEX: Final = "map_index"
ATTR_ROOM_ID: Final = "room_id"
ATTR_NAME: Final = "name"
ATTR_OUTLINE: Final = "outline"
ATTR_CENTER: Final = "center"
ATTR_ORDER: Final = "order"
ATTR_CLEANING_TIMES: Final = "cleaning_times"
ATTR_SUCTION_LEVEL: Final = "suction_level"
ATTR_WATER_VOLUME: Final = "water_volume"
ATTR_TYPE: Final = "type"
ATTR_INDEX: Final = "index"
ATTR_ICON: Final = "icon"
ATTR_COLOR_INDEX: Final = "color_index"


class DreameVacuumChargingStatus(IntEnum):
    """Dreame Vacuum charging status"""

    UNKNOWN = -1
    CHARGING = 1
    NOT_CHARGING = 2
    CHARGING_COMPLETED = 3
    RETURN_TO_CHARGE = 5


class DreameVacuumErrorCode(IntEnum):
    """Dreame Vacuum error code"""

    UNKNOWN = -1
    NO_ERROR = 0
    DROP = 1
    CLIFF = 2
    BUMPER = 3
    GESTURE = 4
    BUMPER_REPEAT = 5
    DROP_REPEAT = 6
    OPTICAL_FLOW = 7
    BOX = 8
    TANKBOX = 9
    WATERBOX_EMPTY = 10
    BOX_FULL = 11
    BRUSH = 12
    SIDE_BRUSH = 13
    FAN = 14
    LEFT_WHEEL_MOTOR = 15
    RIGHT_WHEEL_MOTOR = 16
    TURN_SUFFOCATE = 17
    FORWARD_SUFFOCATE = 18
    CHARGER_GET = 19
    BATTERY_LOW = 20
    CHARGE_FAULT = 21
    BATTERY_PERCENTAGE = 22
    HEART = 23
    CAMERA_OCCLUSION = 24
    MOVE = 25
    FLOW_SHIELDING = 26
    INFRARED_SHIELDING = 27
    CHARGE_NO_ELECTRIC = 28
    BATTERY_FAULT = 29
    FAN_SPEED_ERROR = 30
    LEFTWHELL_SPEED = 31
    RIGHTWHELL_SPEED = 32
    BMI055_ACCE = 33
    BMI055_GYRO = 34
    XV7001 = 35
    LEFT_MAGNET = 36
    RIGHT_MAGNET = 37
    FLOW_ERROR = 38
    INFRARED_FAULT = 39
    CAMERA_FAULT = 40
    STRONG_MAGNET = 41
    WATER_PUMP = 42
    RTC = 43
    AUTO_KEY_TRIG = 44
    P3V3 = 45
    CAMERA_IDLE = 46
    BLOCKED = 47
    LDS_ERROR = 48
    LDS_BUMPER = 49
    WATER_PUMP_2 = 50
    FILTER_BLOCKED = 51
    EDGE = 54
    CARPET = 55
    LASER = 56
    EDGE_2 = 57
    ULTRASONIC = 58
    NO_GO_ZONE = 59
    ROUTE = 61
    ROUTE_2 = 62
    BLOCKED_2 = 63
    BLOCKED_3 = 64
    RESTRICTED = 65
    RESTRICTED_2 = 66
    RESTRICTED_3 = 67
    REMOVE_MOP = 68
    MOP_REMOVED = 69
    MOP_REMOVED_2 = 70
    BIN_FULL = 101
    BIN_OPEN = 102
    BIN_OPEN_2 = 103
    BIN_FULL_2 = 104
    WATER_TANK = 105
    DIRTY_WATER_TANK = 106
    WATER_TANK_DRY = 107
    DIRTY_WATER_TANK_2 = 108
    DIRTY_WATER_TANK_BLOCKED = 109
    DIRTY_WATER_TANK_PUMP = 110
    MOP_PAD = 111
    WET_MOP_PAD = 112
    CLEAN_MOP_PAD = 114


class DreameVacuumState(IntEnum):
    """Dreame Vacuum state"""

    UNKNOWN = -1
    SWEEPING = 1
    IDLE = 2
    PAUSED = 3
    ERROR = 4
    RETURNING = 5
    CHARGING = 6
    MOPPING = 7
    DRYING = 8
    WASHING = 9
    RETURNING_WASHING = 10
    BUILDING = 11
    MOPPING_AND_SWEEPING = 12
    CHARGING_COMPLETED = 13
    UPGRADING = 14


class DreameVacuumSuctionLevel(IntEnum):
    """Dreame Vacuum suction level"""

    UNKNOWN = -1
    QUIET = 0
    STANDARD = 1
    STRONG = 2
    TURBO = 3


class DreameVacuumCleaningMode(IntEnum):
    """Dreame Vacuum cleaning mode"""

    UNKNOWN = -1
    SWEEPING = 0
    MOPPING = 1
    MOPPING_AND_SWEEPING = 2


class DreameVacuumWaterTank(IntEnum):
    """Dreame Vacuum water tank status"""

    UNKNOWN = -1
    NOT_INSTALLED = 0
    INSTALLED = 1
    MOP_INSTALLED = 10


class DreameVacuumWaterVolume(IntEnum):
    """Dreame Vacuum water volume"""

    UNKNOWN = -1
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class DreameVacuumCarpetSensitivity(IntEnum):
    """Dreame Vacuum carpet boost sensitivity"""

    UNKNOWN = -1
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class DreameVacuumRelocationStatus(IntEnum):
    """Dreame Vacuum relocation status"""

    UNKNOWN = -1
    LOCATED = 0
    LOCATING = 1
    FAILED = 10
    SUCCESS = 11


class DreameVacuumTaskStatus(IntEnum):
    """Dreame Vacuum task status"""

    UNKNOWN = -1
    COMPLETED = 0
    AUTO_CLEANING = 1
    ZONE_CLEANING = 2
    SEGMENT_CLEANING = 3
    SPOT_CLEANING = 4
    FAST_MAPPING = 5
    AUTO_CLEANING_PAUSED = 6
    ZONE_CLEANING_PAUSED = 7
    SEGMENT_CLEANING_PAUSED = 8
    SPOT_CLEANING_PAUSED = 9
    MAP_CLEANING_PAUSED = 10
    DOCKING_PAUSED = 11
    MOPPING_PAUSED = 12
    SEGMENT_MOPPING_PAUSED = 13
    ZONE_MOPPING_PAUSED = 14
    AUTO_MOPPING_PAUSED = 15
    AUTO_DOCKING_PAUSED = 16
    SEGMENT_DOCKING_PAUSED = 17
    ZONE_DOCKING_PAUSED = 18


class DreameVacuumStatus(IntEnum):
    """Dreame Vacuum status"""

    UNKNOWN = -1
    IDLE = 0
    PAUSED = 1
    CLEANING = 2
    BACK_HOME = 3
    PART_CLEANING = 4
    FOLLOW_WALL = 5
    CHARGING = 6
    OTA = 7
    FCT = 8
    WIFI_SET = 9
    POWER_OFF = 10
    FACTORY = 11
    ERROR = 12
    REMOTE_CONTROL = 13
    SLEEPING = 14
    SELF_TEST = 15
    FACTORY_FUNCION_TEST = 16
    STANDBY = 17
    SEGMENT_CLEANING = 18
    ZONE_CLEANING = 19
    SPOT_CLEANING = 20
    FAST_MAPPING = 21


class DreameVacuumDustCollection(IntEnum):
    """Dreame Vacuum dust collection availability"""

    UNKNOWN = -1
    NOT_AVAILABLE = 0
    AVAILABLE = 1


class DreameVacuumAutoEmptyStatus(IntEnum):
    """Dreame Vacuum dust collection status"""

    UNKNOWN = -1
    IDLE = 0
    ACTIVE = 1
    NOT_PERFORMED = 2


class DreameVacuumSelfWashBaseStatus(IntEnum):
    """Dreame Vacuum self-wash base status"""

    UNKNOWN = -1
    IDLE = 0
    WASHING = 1
    DRYING = 2
    PAUSED = 2
    RETURNING = 3


class DreameVacuumProperty(IntEnum):
    """Dreame Vacuum properties"""

    STATE = 0,
    ERROR = 1,
    BATTERY_LEVEL = 2,
    CHARGING_STATUS = 3,
    STATUS = 4,
    CLEANING_TIME = 5,
    CLEANED_AREA = 6,
    SUCTION_LEVEL = 7,
    WATER_VOLUME = 8,
    WATER_TANK = 9,
    TASK_STATUS = 10,
    CLEANING_START_TIME = 11,
    CLEAN_LOG_FILE_NAME = 12,
    CLEANING_PROPERTIES = 13,
    RESUME_CLEANING = 14,
    CARPET_BOOST = 15,
    CLEAN_LOG_STATUS = 16,
    SERIAL_NUMBER = 17,
    REMOTE_CONTROL = 18,
    MOP_CLEANING_REMAINDER = 19,
    CLEANING_PAUSED = 20,
    FAULTS = 21,
    RELOCATION_STATUS = 22,
    OBSTACLE_AVOIDANCE = 23,
    AI_DETECTION = 24,
    CLEANING_MODE = 25,
    SELF_WASH_BASE_STATUS = 26,
    CUSTOMIZED_CLEANING = 27,
    CHILD_LOCK = 28,
    CARPET_SENSITIVITY = 29,
    TIGHT_MOPPING = 30,
    CLEANING_CANCEL = 31,
    CARPET_DISTINGUISH = 32,
    AUTO_WASH = 33,
    WARN_STATUS = 34,
    CARPET_CLEAN = 35,
    AUTO_ADD_DETERGENT = 36,
    DRYING_TIME = 37,
    DND = 38,
    DND_START = 39,
    DND_END = 40,
    MAP_DATA = 41,
    FRAME_INFO = 42,
    OBJECT_NAME = 43,
    MAP_EXTEND_DATA = 44,
    ROBOT_TIME = 45,
    RESULT_CODE = 46,
    MULTI_FLOOR_MAP = 47,
    MAP_LIST = 48,
    RECOVERY_MAP_LIST = 49,
    MAP_RECOVERY = 50,
    MAP_RECOVERY_STATUS = 51,
    OLD_MAP_DATA = 52,
    VOLUME = 53,
    VOICE_PACKET_ID = 54,
    VOICE_CHANGE_STATUS = 55,
    VOICE_CHANGE = 56,
    TIMEZONE = 57,
    SCHEDULE = 58,
    SCHEDULE_ID = 59,
    SCHEDULE_CANCLE_REASON = 60,
    MAIN_BRUSH_TIME_LEFT = 61,
    MAIN_BRUSH_LEFT = 62,
    SIDE_BRUSH_TIME_LEFT = 63,
    SIDE_BRUSH_LEFT = 64,
    FILTER_LEFT = 65,
    FILTER_TIME_LEFT = 66,
    FIRST_CLEANING_DATE = 67,
    TOTAL_CLEANING_TIME = 68,
    CLEANING_COUNT = 69,
    TOTAL_CLEANED_AREA = 70,
    AUTO_DUST_COLLECTING = 71,
    AUTO_EMPTY_FREQUENCY = 72,
    DUST_COLLECTION = 73,
    AUTO_EMPTY_STATUS = 74,
    SENSOR_DIRTY_LEFT = 75,
    SENSOR_DIRTY_TIME_LEFT = 76,
    MOP_LEFT = 77,
    MOP_TIME_LEFT = 78,
    SILVER_ION_TIME_LEFT = 79,
    SILVER_ION_LEFT = 80


class DreameVacuumAction(IntEnum):
    """Dreame Vacuum actions"""

    START = 1
    PAUSE = 2
    CHARGE = 3
    START_CUSTOM = 4
    STOP = 5
    CLEAR_WARNING = 6
    START_WASHING = 7
    REQUEST_MAP = 8
    UPDATE_MAP_DATA = 9
    LOCATE = 10
    TEST_SOUND = 11
    RESET_MAIN_BRUSH = 12
    RESET_SIDE_BRUSH = 13
    RESET_FILTER = 14
    RESET_SENSOR = 15
    START_AUTO_EMPTY = 16
    RESET_MOP = 17
    RESET_SILVER_ION = 10


# Dreame Vacuum property mapping
DreameVacuumPropertyMapping = {
    DreameVacuumProperty.STATE: {"siid": 2, "piid": 1},
    DreameVacuumProperty.ERROR: {"siid": 2, "piid": 2},
    DreameVacuumProperty.BATTERY_LEVEL: {"siid": 3, "piid": 1},
    DreameVacuumProperty.CHARGING_STATUS: {"siid": 3, "piid": 2},
    DreameVacuumProperty.STATUS: {"siid": 4, "piid": 1},
    DreameVacuumProperty.CLEANING_TIME: {"siid": 4, "piid": 2},
    DreameVacuumProperty.CLEANED_AREA: {"siid": 4, "piid": 3},
    DreameVacuumProperty.SUCTION_LEVEL: {"siid": 4, "piid": 4},
    DreameVacuumProperty.WATER_VOLUME: {"siid": 4, "piid": 5},
    DreameVacuumProperty.WATER_TANK: {"siid": 4, "piid": 6},
    DreameVacuumProperty.TASK_STATUS: {"siid": 4, "piid": 7},
    DreameVacuumProperty.CLEANING_START_TIME: {"siid": 4, "piid": 8},
    DreameVacuumProperty.CLEAN_LOG_FILE_NAME: {"siid": 4, "piid": 9},
    DreameVacuumProperty.CLEANING_PROPERTIES: {"siid": 4, "piid": 10},
    DreameVacuumProperty.RESUME_CLEANING: {"siid": 4, "piid": 11},
    DreameVacuumProperty.CARPET_BOOST: {"siid": 4, "piid": 12},
    DreameVacuumProperty.CLEAN_LOG_STATUS: {"siid": 4, "piid": 13},
    DreameVacuumProperty.SERIAL_NUMBER: {"siid": 4, "piid": 14},
    DreameVacuumProperty.REMOTE_CONTROL: {"siid": 4, "piid": 15},
    DreameVacuumProperty.MOP_CLEANING_REMAINDER: {"siid": 4, "piid": 16},
    DreameVacuumProperty.CLEANING_PAUSED: {"siid": 4, "piid": 17},
    DreameVacuumProperty.FAULTS: {"siid": 4, "piid": 18},
    # DreameVacuumProperty.NATION_MATCHED: {"siid": 4, "piid": 19},
    DreameVacuumProperty.RELOCATION_STATUS: {"siid": 4, "piid": 20},
    DreameVacuumProperty.OBSTACLE_AVOIDANCE: {"siid": 4, "piid": 21},
    DreameVacuumProperty.AI_DETECTION: {"siid": 4, "piid": 22},
    DreameVacuumProperty.CLEANING_MODE: {"siid": 4, "piid": 23},
    # DreameVacuumProperty.UPLOAD_MAP: {"siid": 4, "piid": 24},
    DreameVacuumProperty.SELF_WASH_BASE_STATUS: {"siid": 4, "piid": 25},
    DreameVacuumProperty.CUSTOMIZED_CLEANING: {"siid": 4, "piid": 26},
    DreameVacuumProperty.CHILD_LOCK: {"siid": 4, "piid": 27},
    DreameVacuumProperty.CARPET_SENSITIVITY: {"siid": 4, "piid": 28},
    DreameVacuumProperty.TIGHT_MOPPING: {"siid": 4, "piid": 29},
    DreameVacuumProperty.CLEANING_CANCEL: {"siid": 4, "piid": 30},
    DreameVacuumProperty.CARPET_DISTINGUISH: {"siid": 4, "piid": 33},
    DreameVacuumProperty.AUTO_WASH: {"siid": 4, "piid": 34},
    DreameVacuumProperty.WARN_STATUS: {"siid": 4, "piid": 35},
    DreameVacuumProperty.CARPET_CLEAN: {"siid": 4, "piid": 36},
    DreameVacuumProperty.AUTO_ADD_DETERGENT: {"siid": 4, "piid": 37},
    DreameVacuumProperty.DRYING_TIME: {"siid": 4, "piid": 40},
    # DreameVacuumProperty.COMBINED_DATA: {"siid": 4, "piid": 99},
    DreameVacuumProperty.DND: {"siid": 5, "piid": 1},
    DreameVacuumProperty.DND_START: {"siid": 5, "piid": 2},
    DreameVacuumProperty.DND_END: {"siid": 5, "piid": 3},
    DreameVacuumProperty.MAP_DATA: {"siid": 6, "piid": 1},
    DreameVacuumProperty.FRAME_INFO: {"siid": 6, "piid": 2},
    DreameVacuumProperty.OBJECT_NAME: {"siid": 6, "piid": 3},
    DreameVacuumProperty.MAP_EXTEND_DATA: {"siid": 6, "piid": 4},
    DreameVacuumProperty.ROBOT_TIME: {"siid": 6, "piid": 5},
    DreameVacuumProperty.RESULT_CODE: {"siid": 6, "piid": 6},
    DreameVacuumProperty.MULTI_FLOOR_MAP: {"siid": 6, "piid": 7},
    DreameVacuumProperty.MAP_LIST: {"siid": 6, "piid": 8},
    DreameVacuumProperty.RECOVERY_MAP_LIST: {"siid": 6, "piid": 9},
    DreameVacuumProperty.MAP_RECOVERY: {"siid": 6, "piid": 10},
    DreameVacuumProperty.MAP_RECOVERY_STATUS: {"siid": 6, "piid": 11},
    DreameVacuumProperty.OLD_MAP_DATA: {"siid": 6, "piid": 13},
    DreameVacuumProperty.VOLUME: {"siid": 7, "piid": 1},
    DreameVacuumProperty.VOICE_PACKET_ID: {"siid": 7, "piid": 2},
    DreameVacuumProperty.VOICE_CHANGE_STATUS: {"siid": 7, "piid": 3},
    DreameVacuumProperty.VOICE_CHANGE: {"siid": 7, "piid": 4},
    DreameVacuumProperty.TIMEZONE: {"siid": 8, "piid": 1},
    DreameVacuumProperty.SCHEDULE: {"siid": 8, "piid": 2},
    DreameVacuumProperty.SCHEDULE_ID: {"siid": 8, "piid": 3},
    DreameVacuumProperty.SCHEDULE_CANCLE_REASON: {"siid": 8, "piid": 4},
    DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT: {"siid": 9, "piid": 1},
    DreameVacuumProperty.MAIN_BRUSH_LEFT: {"siid": 9, "piid": 2},
    DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT: {"siid": 10, "piid": 1},
    DreameVacuumProperty.SIDE_BRUSH_LEFT: {"siid": 10, "piid": 2},
    DreameVacuumProperty.FILTER_LEFT: {"siid": 11, "piid": 1},
    DreameVacuumProperty.FILTER_TIME_LEFT: {"siid": 11, "piid": 2},
    DreameVacuumProperty.FIRST_CLEANING_DATE: {"siid": 12, "piid": 1},
    DreameVacuumProperty.TOTAL_CLEANING_TIME: {"siid": 12, "piid": 2},
    DreameVacuumProperty.CLEANING_COUNT: {"siid": 12, "piid": 3},
    DreameVacuumProperty.TOTAL_CLEANED_AREA: {"siid": 12, "piid": 4},
    DreameVacuumProperty.AUTO_DUST_COLLECTING: {"siid": 15, "piid": 1},
    DreameVacuumProperty.AUTO_EMPTY_FREQUENCY: {"siid": 15, "piid": 2},
    DreameVacuumProperty.DUST_COLLECTION: {"siid": 15, "piid": 3},
    DreameVacuumProperty.AUTO_EMPTY_STATUS: {"siid": 15, "piid": 5},
    DreameVacuumProperty.SENSOR_DIRTY_LEFT: {"siid": 16, "piid": 1},
    DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT: {"siid": 16, "piid": 2},
    DreameVacuumProperty.MOP_LEFT: {"siid": 18, "piid": 1},
    DreameVacuumProperty.MOP_TIME_LEFT: {"siid": 18, "piid": 2},
    DreameVacuumProperty.SILVER_ION_TIME_LEFT: {"siid": 18, "piid": 1},
    DreameVacuumProperty.SILVER_ION_LEFT: {"siid": 18, "piid": 2},

}

# Dreame Vacuum action mapping
DreameVacuumActionMapping = {
    DreameVacuumAction.START: {"siid": 2, "aiid": 1},
    DreameVacuumAction.PAUSE: {"siid": 2, "aiid": 2},
    DreameVacuumAction.CHARGE: {"siid": 3, "aiid": 1},
    DreameVacuumAction.START_CUSTOM: {"siid": 4, "aiid": 1},
    DreameVacuumAction.STOP: {"siid": 4, "aiid": 2},
    DreameVacuumAction.CLEAR_WARNING: {"siid": 4, "aiid": 3},
    DreameVacuumAction.START_WASHING: {"siid": 4, "aiid": 4},
    DreameVacuumAction.REQUEST_MAP: {"siid": 6, "aiid": 1},
    DreameVacuumAction.UPDATE_MAP_DATA: {"siid": 6, "aiid": 2},
    DreameVacuumAction.LOCATE: {"siid": 7, "aiid": 1},
    DreameVacuumAction.TEST_SOUND: {"siid": 7, "aiid": 2},
    DreameVacuumAction.RESET_MAIN_BRUSH: {"siid": 9, "aiid": 1},
    DreameVacuumAction.RESET_SIDE_BRUSH: {"siid": 10, "aiid": 1},
    DreameVacuumAction.RESET_FILTER: {"siid": 11, "aiid": 1},
    DreameVacuumAction.RESET_SENSOR: {"siid": 16, "aiid": 1},
    DreameVacuumAction.START_AUTO_EMPTY: {"siid": 15, "aiid": 1},
    DreameVacuumAction.RESET_MOP: {"siid": 18, "aiid": 1},
    DreameVacuumAction.RESET_SILVER_ION: {"siid": 19, "aiid": 1},
}

PROPERTY_AVAILABILITY: Final = {
    DreameVacuumProperty.CUSTOMIZED_CLEANING: lambda device: not device.status.started and (device.status.has_saved_map or device.status.current_map is None),
    DreameVacuumProperty.TIGHT_MOPPING: lambda device: device.status.water_tank_installed and not device.status.started,
    DreameVacuumProperty.MULTI_FLOOR_MAP: lambda device: not device.status.has_temporary_map,
    DreameVacuumProperty.MOP_CLEANING_REMAINDER: lambda device: device.status.water_tank_installed,
    DreameVacuumProperty.DND_START: lambda device: device.status.dnd_enabled,
    DreameVacuumProperty.DND_END: lambda device: device.status.dnd_enabled,
    DreameVacuumProperty.SUCTION_LEVEL: lambda device: not device.status.mopping and not (device.status.customized_cleaning and not device.status.zone_cleaning) and not device.status.fast_mapping,
    DreameVacuumProperty.WATER_VOLUME: lambda device: device.status.water_tank_installed and not device.status.sweeping and not (device.status.customized_cleaning and not device.status.zone_cleaning) and not device.status.fast_mapping,
    DreameVacuumProperty.CLEANING_MODE: lambda device: not device.status.started and not device.status.fast_mapping and not device.status.cleaning_paused,
    DreameVacuumProperty.CARPET_SENSITIVITY: lambda device: bool(device.get_property(DreameVacuumProperty.CARPET_BOOST)),
    DreameVacuumProperty.AUTO_EMPTY_FREQUENCY: lambda device: bool(device.get_property(DreameVacuumProperty.AUTO_DUST_COLLECTING)),
    DreameVacuumProperty.CLEANING_TIME: lambda device: not device.status.fast_mapping,
    DreameVacuumProperty.CLEANED_AREA: lambda device: not device.status.fast_mapping,
    DreameVacuumProperty.RELOCATION_STATUS: lambda device: not device.status.fast_mapping,
}

ACTION_AVAILABILITY: Final = {
    DreameVacuumAction.RESET_MAIN_BRUSH: lambda device: bool(device.status.main_brush_life < 100),
    DreameVacuumAction.RESET_SIDE_BRUSH: lambda device: bool(device.status.side_brush_life < 100),
    DreameVacuumAction.RESET_FILTER: lambda device: bool(device.status.filter_life < 100),
    DreameVacuumAction.RESET_SENSOR: lambda device: bool(device.status.sensor_dirty_life < 100),
    DreameVacuumAction.RESET_MOP: lambda device: bool(device.status.mop_life < 100),
    DreameVacuumAction.RESET_SILVER_ION: lambda device: bool(device.status.silver_ion < 100),
    DreameVacuumAction.START_AUTO_EMPTY: lambda device: device.status.dust_collection_available,
    DreameVacuumAction.CLEAR_WARNING: lambda device: device.status.has_warning,
    DreameVacuumAction.START: lambda device: not device.status.started or device.status.returning or device.status.returning_paused,
    DreameVacuumAction.START_CUSTOM: lambda device: not device.status.started or device.status.returning or device.status.returning_paused,
    DreameVacuumAction.PAUSE: lambda device: device.status.started and not device.status.returning_paused and not device.status.paused,
    DreameVacuumAction.CHARGE: lambda device: not device.status.docked and not device.status.returning,
    DreameVacuumAction.STOP: lambda device: not device.status.fast_mapping and device.status.started,
}


def PIID(property: DreameVacuumProperty, mapping=DreameVacuumPropertyMapping) -> int | None:
    if property in mapping:
        return mapping[property]["piid"]


def DIID(property: DreameVacuumProperty, mapping=DreameVacuumPropertyMapping) -> str | None:
    if property in mapping:
        return f'{mapping[property]["siid"]}.{mapping[property]["piid"]}'


class Point:
    def __init__(self, x: float, y: float, a=None) -> None:
        self.x = x
        self.y = y
        self.a = a

    def __str__(self) -> str:
        if self.a is None:
            return f"({self.x}, {self.y})"
        return f"({self.x}, {self.y}, a = {self.a})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self: Point, other: Point) -> bool:
        return (
            other is not None
            and self.x == other.x
            and self.y == other.y
            and self.a == other.a
        )

    def as_dict(self) -> Dict[str, Any]:
        if self.a is None:
            return {ATTR_X: self.x, ATTR_Y: self.y}
        return {ATTR_X: self.x, ATTR_Y: self.y, ATTR_A: self.a}

    def to_img(self, image_dimensions) -> Point:
        return image_dimensions.to_img(self)
    
    def rotated(self, image_dimensions, degree) -> Point:
        w = int(
            (
                image_dimensions.width
                + (image_dimensions.padding[0] + image_dimensions.padding[1])
            )
            * image_dimensions.scale
        )
        h = int(
            (
                image_dimensions.height
                + (image_dimensions.padding[2] + image_dimensions.padding[3])
            )
            * image_dimensions.scale
        )
        x = self.x
        y = self.y
        while degree > 0:
            tmp = y
            y = w - x
            x = tmp
            tmp = h
            h = w
            w = tmp
            degree = degree - 90
        return Point(x, y)

    def __mul__(self, other) -> Point:
        return Point(self.x * other, self.y * other, self.a)

    def __truediv__(self, other) -> Point:
        return Point(self.x / other, self.y / other, self.a)


class Path(Point):
    def __init__(self, x: float, y: float, line: bool, absolute: bool = False) -> None:
        super().__init__(x, y)
        self.line = line
        self.absolute = absolute


class Zone:
    def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def __str__(self) -> str:
        return f"[{self.x0}, {self.y0}, {self.x1}, {self.y1}]"

    def __eq__(self: Zone, other: Zone) -> bool:
        return (
            other is not None
            and self.x0 == other.x0
            and self.y0 == other.y0
            and self.x1 == other.x1
            and self.y1 == other.y1
        )

    def __repr__(self) -> str:
        return self.__str__()

    def as_dict(self) -> Dict[str, Any]:
        return {ATTR_X0: self.x0, ATTR_Y0: self.y0, ATTR_X1: self.x1, ATTR_Y1: self.y1}

    def as_area(self) -> Area:
        return Area(
            self.x0, self.y0, self.x0, self.y1, self.x1, self.y1, self.x1, self.y0
        )


class Segment(Zone):
    def __init__(
        self,
        room_id: int,
        x0: Optional[float] = None,
        y0: Optional[float] = None,
        x1: Optional[float] = None,
        y1: Optional[float] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        name: str = None,
        custom_name: str = None,
        index: int = 0,
        type: int = 0,
        icon: str = None,
        neighbors: List[int] = [],
        cleaning_times: int = None,
        suction_level: int = None,
        water_volume: int = None,
        order: int = None,
    ) -> None:
        super().__init__(x0, y0, x1, y1)
        self.room_id = room_id
        self.x = x
        self.y = y
        self.name = name
        self.custom_name = custom_name
        self.type = type
        self.index = index
        self.icon = icon
        self.neighbors = neighbors
        self.order = order
        self.cleaning_times = cleaning_times
        self.suction_level = suction_level
        self.water_volume = water_volume
        self.color_index = None
        self.set_name()

    @property
    def outline(self) -> List[List[int]]:
        return [[self.x0, self.y0], [self.x0, self.y1], [self.x1, self.y1], [self.x1, self.y0]]

    @property
    def center(self) -> List[int]:
        return [self.x, self.y]

    def set_name(self) -> None:
        if self.custom_name is not None:
            self.name = self.custom_name
        elif self.type is not 0 and SEGMENT_TYPE_CODE_TO_NAME.get(self.type):
            self.name = SEGMENT_TYPE_CODE_TO_NAME[self.type]
            if self.index > 0:
                self.name = f"{self.name} {self.index + 1}"
        else:
            self.name = f"Room {self.room_id}"
        self.icon = SEGMENT_TYPE_CODE_TO_HA_ICON[self.type]

    def next_type_index(self, type, segments) -> int:
        index = 0
        if type > 0:
            for room_id in sorted(segments, key=lambda room_id: segments[room_id].index):
                if (
                    room_id != self.room_id
                    and segments[room_id].type == type
                    and segments[room_id].index == index
                ):
                    index = index + 1
        return index

    def name_list(self, segments) -> dict[int, str]:
        list = {k: v for k, v in SEGMENT_TYPE_CODE_TO_NAME.items()}
        for k, v in list.items():
            index = self.next_type_index(k, segments)
            if index > 0:
                list[k] = f"{v} {index + 1}"

        name = f"Room {self.room_id}"
        if self.type == 0:
            name = f"{self.name}"
        list[0] = name
        if self.type != 0 and self.index > 0:
            list[self.type] = self.name

        return {v: k for k, v in list.items()}

    def as_dict(self) -> Dict[str, Any]:
        attributes = {**super(Segment, self).as_dict()}
        #attributes[ATTR_OUTLINE] = self.outline
        if self.room_id:
            attributes[ATTR_ROOM_ID] = self.room_id
        if self.name is not None:
            attributes[ATTR_NAME] = self.name
        if self.order is not None:
            attributes[ATTR_ORDER] = self.order
        if self.cleaning_times is not None:
            attributes[ATTR_CLEANING_TIMES] = self.cleaning_times
        if self.suction_level is not None:
            attributes[ATTR_SUCTION_LEVEL] = self.suction_level
        if self.water_volume is not None:
            attributes[ATTR_WATER_VOLUME] = self.water_volume
        if self.type is not None:
            attributes[ATTR_TYPE] = self.type
        if self.index is not None:
            attributes[ATTR_INDEX] = self.index
        #if self.icon is not None:
            #attributes[ATTR_ICON] = self.icon
        if self.color_index is not None:
            attributes[ATTR_COLOR_INDEX] = self.color_index
        if self.x is not None and self.y is not None:
            #attributes[ATTR_CENTER] = self.center
            attributes[ATTR_X] = self.x
            attributes[ATTR_Y] = self.y


        return attributes

    def __eq__(self: Segment, other: Segment) -> bool:
        return (
            other is not None
            and self.x0 == other.x0
            and self.y0 == other.y0
            and self.x1 == other.x1
            and self.y1 == other.y1
            and self.x == other.x
            and self.y == other.y
            and self.name == other.name
            and self.index == other.index
            and self.type == other.type
            and self.color_index == other.color_index
            and self.icon == other.icon
            and self.neighbors == other.neighbors
            and self.order == other.order
            and self.cleaning_times == other.cleaning_times
            and self.suction_level == other.suction_level
            and self.water_volume == other.water_volume
        )

    def __str__(self) -> str:
        return f"{{room_id: {self.room_id}, outline: {self.outline}}}"

    def __repr__(self) -> str:
        return self.__str__()


class Wall:
    def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def __eq__(self: Wall, other: Wall) -> bool:
        return (
            other is not None
            and self.x0 == other.x0
            and self.y0 == other.y0
            and self.x1 == other.x1
            and self.y1 == other.y1
        )

    def __str__(self) -> str:
        return f"[{self.x0}, {self.y0}, {self.x1}, {self.y1}]"

    def __repr__(self) -> str:
        return self.__str__()

    def as_dict(self) -> Dict[str, Any]:
        return {ATTR_X0: self.x0, ATTR_Y0: self.y0, ATTR_X1: self.x1, ATTR_Y1: self.y1}

    def to_img(self, image_dimensions) -> Wall:
        p0 = Point(self.x0, self.y0).to_img(image_dimensions)
        p1 = Point(self.x1, self.y1).to_img(image_dimensions)
        return Wall(p0.x, p0.y, p1.x, p1.y)

    def as_list(self) -> List[float]:
        return [self.x0, self.y0, self.x1, self.y1]


class Area:
    def __init__(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
    ) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3

    def __eq__(self: Area, other: Area) -> bool:
        return (
            other is not None
            and self.x0 == other.x0
            and self.y0 == other.y0
            and self.x1 == other.x1
            and self.y1 == other.y1
            and self.x2 == other.x2
            and self.y2 == other.y2
            and self.x3 == other.x3
            and self.y3 == other.y3
        )

    def __str__(self) -> str:
        return f"[{self.x0}, {self.y0}, {self.x1}, {self.y1}, {self.x2}, {self.y2}, {self.x3}, {self.y3}]"

    def __repr__(self) -> str:
        return self.__str__()

    def as_dict(self) -> Dict[str, Any]:
        return {
            ATTR_X0: self.x0,
            ATTR_Y0: self.y0,
            ATTR_X1: self.x1,
            ATTR_Y1: self.y1,
            ATTR_X2: self.x2,
            ATTR_Y2: self.y2,
            ATTR_X3: self.x3,
            ATTR_Y3: self.y3,
        }

    def as_list(self) -> List[float]:
        return [self.x0, self.y0, self.x1, self.y1, self.x2, self.y2, self.x3, self.y3]

    def to_img(self, image_dimensions) -> Area:
        p0 = Point(self.x0, self.y0).to_img(image_dimensions)
        p1 = Point(self.x1, self.y1).to_img(image_dimensions)
        p2 = Point(self.x2, self.y2).to_img(image_dimensions)
        p3 = Point(self.x3, self.y3).to_img(image_dimensions)
        return Area(p0.x, p0.y, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)


class MapImageDimensions:
    def __init__(self, top: int, left: int, height: int, width: int, grid_size: int) -> None:
        self.top = top
        self.left = left
        self.height = height
        self.width = width
        self.grid_size = grid_size
        self.scale = 1
        self.padding = [0, 0, 0, 0]

    def to_img(self, point: Point) -> Point:
        return Point(
            ((point.x - self.left) / self.grid_size) * self.scale
            + (self.padding[0] * self.scale),
            (
                (
                    (self.height - 1) * self.grid_size
                    - (point.y - self.top)
                )
                / self.grid_size
            )
            * self.scale
            + (self.padding[2] * self.scale),
        )
    
    def __eq__(self: MapImageDimensions, other: MapImageDimensions) -> bool:
        return (
            other is not None
            and self.top == other.top
            and self.left == other.left
            and self.height == other.height
            and self.width == other.width
            and self.grid_size == other.grid_size
        )


class MapFrameType(IntEnum):
    I = 73
    P = 80
    # T = ??


class MapPixelType(IntEnum):
    OUTSIDE = 255
    WALL = 254
    FLOOR = 253
    NEW_SEGMENT = 252


class MapDataPartial:
    def __init__(self) -> None:
        self.map_id: Optional[int] = None  # Map header: map_id
        self.frame_id: Optional[int] = None  # Map header: frame_id
        self.frame_type: Optional[int] = None  # Map header: frame_type
        self.timestamp_ms: Optional[int] = None  # Data json: timestamp_ms
        self.raw: Optional[bytes] = None  # Unzipped raw map
        self.data_json: Optional[object] = {}  # Data json


class MapData:
    def __init__(self) -> None:
        # Header
        self.map_id: Optional[int] = None  # Map header: map_id
        self.frame_id: Optional[int] = None  # Map header: frame_id
        self.frame_type: Optional[int] = None  # Map header: frame_type
        # Map header: robot x, robot y, robot angle
        self.robot_position: Optional[Point] = None
        # Map header: charger x, charger y, charger angle
        self.charger_position: Optional[Point] = None
        # Map header: top, left, height, width, grid_size
        self.dimensions: Optional[MapImageDimensions] = None
        self.data: Optional[Any] = None  # Raw image data for handling P frames
        # Data json
        self.timestamp_ms: Optional[int] = None  # Data json: timestamp_ms
        self.rotation: Optional[int] = None  # Data json: mra
        self.robot_mode: Optional[int] = None  # Data json: robot_mode
        self.no_go_areas: Optional[List[Area]] = None  # Data json: vw.rect
        self.no_mopping_areas: Optional[List[Area]] = None  # Data json: vw.mop
        self.walls: Optional[List[Wall]] = None  # Data json: vw.line
        self.path: Optional[Path] = None  # Data json: tr
        self.active_segments: Optional[int] = None  # Data json: sa
        self.active_areas: Optional[List[Area]] = None  # Data json: da2
        self.used_times: Optional[int] = None  # Data json: map_used_times
        # Data json: rism.map_header.map_id
        self.saved_map_id: Optional[int] = None
        self.saved_map_status: Optional[int] = None  # Data json: ris
        self.restored_map: Optional[bool] = None  # Data json: rpur
        self.frame_map: Optional[bool] = None  # Data json: fsm
        self.docked: Optional[bool] = None  # Data json: oc
        self.clean_log: Optional[bool] = None  # Data json: iscleanlog
        self.cleanset: Optional[Dict[str, List[int]]
                                ] = None  # Data json: cleanset
        self.l2r: Optional[bool] = None  # Data json: l2r
        self.temporary_map: Optional[int] = None  # Data json: suw
        self.cleaned_area: Optional[int] = None  # Data json: cs
        self.recovery_map: Optional[bool] = None  # Data json: us
        self.ai_obstacle: Optional[List[Point]
                                   ] = None  # Data json: ai_obstacle
        self.new_map: Optional[bool] = None  # Data json: risp
        # Generated
        self.custom_name: Optional[str] = None  # Map list json: name
        self.map_index: Optional[int] = None  # Generated from saved map list
        self.map_name: Optional[str] = None  # Generated map name for map list
        # Generated pixel map for rendering colors
        self.pixel_type: Optional[Any] = None
        # Generated segments from pixel_type
        self.segments: Optional[Dict[int, Segment]] = None
        self.saved_map: Optional[bool] = None  # Generated for rism map
        self.empty_map: Optional[bool] = None  # Generated from pixel_type
        # Generated from pixel_type and robot poisiton
        self.robot_segment: Optional[int] = None
        # For renderer to detect changes
        self.last_updated: Optional[float] = None

    def __eq__(self: MapData, other: MapData) -> bool:
        if other is None:
            return False

        if self.map_id != other.map_id:
            return False

        if self.custom_name != other.custom_name:
            return False

        if self.rotation != other.rotation:
            return False

        if self.robot_mode != other.robot_mode:
            return False

        if self.robot_position != other.robot_position:
            return False

        if self.charger_position != other.charger_position:
            return False

        if self.no_go_areas != other.no_go_areas:
            return False

        if self.no_mopping_areas != other.no_mopping_areas:
            return False

        if self.walls != other.walls:
            return False

        if self.docked != other.docked:
            return False

        if self.active_segments != other.active_segments:
            return False

        if self.active_areas != other.active_areas:
            return False

        if self.clean_log != other.clean_log:
            return False

        if self.saved_map_status != other.saved_map_status:
            return False

        if self.restored_map != other.restored_map:
            return False

        if self.frame_map != other.frame_map:
            return False

        if self.temporary_map != other.temporary_map:
            return False

        if self.saved_map != other.saved_map:
            return False

        if self.new_map != other.new_map:
            return False

        if self.cleanset != other.cleanset:
            return False

        return True

    def as_dict(self) -> Dict[str, Any]:
        attributes_list = {}
        if self.charger_position is not None:
            attributes_list[ATTR_CHARGER] = self.charger_position
        if self.segments is not None and (self.saved_map or self.saved_map_status == 2):
            attributes_list[ATTR_ROOMS] = {k: v.as_dict() for k, v in sorted(self.segments.items())}
        if not self.saved_map and self.robot_position is not None:
            attributes_list[ATTR_ROBOT_POSITION] = self.robot_position
        if self.map_id:
            attributes_list[ATTR_MAP_ID] = self.map_id
        if self.map_name is not None:
            attributes_list[ATTR_MAP_NAME] = self.map_name
        if self.rotation is not None:
            attributes_list[ATTR_ROTATION] = self.rotation
        if self.last_updated is not None:
            attributes_list[ATTR_UPDATED] = datetime.fromtimestamp(
                self.last_updated)
        if self.used_times is not None:
            attributes_list[ATTR_USED_TIMES] = self.used_times
        if not self.saved_map and self.active_areas is not None:
            attributes_list[ATTR_ACTIVE_AREAS] = self.active_areas
        if not self.saved_map and self.active_segments is not None:
            attributes_list[ATTR_ACTIVE_SEGMENTS] = self.active_segments
        if self.walls is not None:
            attributes_list[ATTR_WALLS] = self.walls
        if self.no_go_areas is not None:
            attributes_list[ATTR_NO_GO_AREAS] = self.no_go_areas
        if self.no_mopping_areas is not None:
            attributes_list[ATTR_NO_MOPPING_AREAS] = self.no_mopping_areas
        if self.empty_map is not None:
            attributes_list[ATTR_IS_EMPTY] = self.empty_map
        if self.frame_id:
            attributes_list[ATTR_FRAME_ID] = self.frame_id
        if self.map_index:
            attributes_list[ATTR_MAP_INDEX] = self.map_index
        return attributes_list


class MapRendererLayer(IntEnum):
    IMAGE = 0
    OBJECTS = 1
    PATH = 2
    NO_MOP = 3
    NO_GO = 4
    WALL = 5
    ACTIVE_AREA = 6
    SEGMENTS = 7
    CHARGER = 8
    ROBOT = 9


@dataclass
class CleaningHistory:
    date: datetime = None
    status: DreameVacuumStatus = None
    cleaning_time: int = 0
    cleaned_area: int = 0
    suction_level: DreameVacuumSuctionLevel = None
    file_name: str = None
    completed: bool = None
    water_tank: DreameVacuumWaterTank = None
