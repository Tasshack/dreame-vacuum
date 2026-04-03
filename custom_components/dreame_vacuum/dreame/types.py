from __future__ import annotations

import math
import json
import time
from typing import Any, Dict, Final, List, Optional
from enum import IntEnum, Enum
from dataclasses import dataclass, field, asdict
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

FURNITURE_TYPE_TO_DIMENSIONS: Final = {
    1: [1500, 2000],
    2: [1800, 2000],
    3: [800, 700],
    4: [1260, 800],
    5: [2340, 750],
    6: [1500, 800],
    7: [500, 400],
    8: [800, 400],
    9: [450, 690],
    10: [735, 990],
    11: [566, 865],
    12: [210, 378],
    13: [628, 936],
}

FURNITURE_V2_TYPE_TO_DIMENSIONS: Final = {
    1: [1000, 2000],
    2: [1500, 2000],
    3: [800, 700],
    4: [1400, 600],
    5: [2300, 700],
    6: [1200, 800],
    7: [500, 400],
    8: [800, 800],
    9: [400, 600],
    10: [300, 500],
    11: [500, 400],
    12: [400, 200],
    13: [400, 600],
    14: [600, 600],
    15: [600, 600],
    16: [300, 500],
    17: [400, 400],
    18: [1600, 300],
    19: [800, 300],
    20: [800, 400],
    21: [2000, 600],
    22: [300, 300],
    23: [1000, 400],
    24: [2800, 1700],
    25: [1000, 1000],
}

FURNITURE_V2_TYPE_MIJIA_TO_DIMENSIONS: Final = {
    1: [1000, 2000],
    2: [1500, 2000],
    3: [800, 700],
    4: [1400, 600],
    5: [2300, 700],
    6: [1200, 800],
    7: [500, 400],
    8: [1000, 1000],
    9: [400, 600],
    10: [300, 500],
    11: [500, 400],
    12: [400, 200],
    13: [400, 600],
    14: [600, 600],
    15: [600, 600],
    16: [300, 500],
    17: [400, 400],
    18: [1600, 300],
    19: [800, 300],
    20: [800, 400],
    21: [2000, 600],
    22: [300, 300],
    23: [1000, 400],
    24: [2800, 1700],
    25: [800, 800],
    26: [600, 1400],
    29: [800, 700],
    30: [2300, 700],
    31: [2800, 1700],
}

piid: Final = "piid"
siid: Final = "siid"
aiid: Final = "aiid"

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
ATTR_CHARGER: Final = "charger_position"
ATTR_IS_EMPTY: Final = "is_empty"
ATTR_NO_GO_AREAS: Final = "no_go_areas"
ATTR_NO_MOPPING_AREAS: Final = "no_mopping_areas"
ATTR_CARPETS: Final = "carpets"
ATTR_DELETED_CARPETS: Final = "deleted_carpets"
ATTR_DETECTED_CARPETS: Final = "detected_carpets"
ATTR_PREDEFINED_POINTS: Final = "predefined_points"
ATTR_VIRTUAL_WALLS: Final = "virtual_walls"
ATTR_VIRTUAL_THRESHOLDS: Final = "virtual_thresholds"
ATTR_PASSABLE_THRESHOLDS: Final = "passable_thresholds"
ATTR_IMPASSABLE_THRESHOLDS: Final = "impassable_thresholds"
ATTR_RAMPS: Final = "ramps"
ATTR_CURTAINS: Final = "curtains"
ATTR_LOW_LYING_AREAS: Final = "low_lying_areas"
ATTR_ROOMS: Final = "rooms"
ATTR_ROBOT_POSITION: Final = "vacuum_position"
ATTR_MAP_ID: Final = "map_id"
ATTR_SAVED_MAP_ID: Final = "saved_map_id"
ATTR_MAP_NAME: Final = "map_name"
ATTR_ROTATION: Final = "rotation"
ATTR_TIMESTAMP: Final = "timestamp"
ATTR_UPDATED: Final = "updated_at"
ATTR_ACTIVE_AREAS: Final = "active_areas"
ATTR_ACTIVE_POINTS: Final = "active_points"
ATTR_ACTIVE_CRUISE_POINTS: Final = "active_cruise_points"
ATTR_ACTIVE_SEGMENTS: Final = "active_segments"
ATTR_FRAME_ID: Final = "frame_id"
ATTR_MAP_INDEX: Final = "map_index"
ATTR_ROOM_ID: Final = "room_id"
ATTR_FURNITURE_ID: Final = "furniture_id"
ATTR_ROOM_ICON: Final = "room_icon"
ATTR_UNIQUE_ID: Final = "unique_id"
ATTR_FLOOR_MATERIAL: Final = "floor_material"
ATTR_FLOOR_MATERIAL_DIRECTION: Final = "floor_material_direction"
ATTR_VISIBILITY: Final = "visibility"
ATTR_MOP_TEMPERATURE: Final = "mop_temperature"
ATTR_MOP_PRESSURE: Final = "mop_pressure"
ATTR_MOP_TYPE: Final = "mop_type"
ATTR_NAME: Final = "name"
ATTR_CUSTOM_NAME: Final = "custom_name"
ATTR_OUTLINE: Final = "outline"
ATTR_CENTER: Final = "center"
ATTR_ORDER: Final = "order"
ATTR_CLEANING_TIMES: Final = "cleaning_times"
ATTR_SUCTION_LEVEL: Final = "suction_level"
ATTR_WATER_VOLUME: Final = "water_volume"
ATTR_WETNESS_LEVEL: Final = "wetness_level"
ATTR_CLEANING_MODE: Final = "cleaning_mode"
ATTR_CLEANING_ROUTE: Final = "cleaning_route"
ATTR_CUSTOM_MOPPING_ROUTE: Final = "custom_mopping_route"
ATTR_TYPE: Final = "type"
ATTR_INDEX: Final = "index"
ATTR_ICON: Final = "icon"
ATTR_COLOR_INDEX: Final = "color_index"
ATTR_OBSTACLES: Final = "obstacles"
ATTR_POSSIBILTY: Final = "possibility"
ATTR_PICTURE_STATUS: Final = "picture_status"
ATTR_IGNORE_STATUS: Final = "ignore_status"
ATTR_ROOM: Final = "room"
ATTR_REASON: Final = "reason"
ATTR_ROUTER_POSITION: Final = "router_position"
ATTR_FURNITURES: Final = "furnitures"
ATTR_STARTUP_METHOD: Final = "startup_method"
ATTR_DUST_COLLECTION_COUNT: Final = "dust_collection_count"
ATTR_MOP_WASH_COUNT: Final = "mop_wash_count"
ATTR_RECOVERY_MAP_LIST: Final = "recovery_map_list"
ATTR_WIDTH: Final = "width"
ATTR_HEIGHT: Final = "height"
ATTR_SIZE_TYPE: Final = "size_type"
ATTR_ANGLE: Final = "angle"
ATTR_SCALE: Final = "scale"
ATTR_COMPLETED: Final = "completed"


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
    MOP_PAD_STOP_ROTATE = 71
    MOP_PAD_STOP_ROTATE_2 = 72
    MOP_INSTALL_FAILED = 74
    LOW_BATTERY_TURN_OFF = 75
    DIRTY_TANK_NOT_INSTALLED = 76
    ROBOT_IN_HIDDEN_ROOM = 78
    LDS_FAILED_TO_LIFT = 79
    ROBOT_STUCK = 80
    ROBOT_STUCK_REPEAT = 81
    SLIPPERY_FLOOR = 82
    UNKNOWN_ERROR = 84
    CHECK_MOP_INSTALL = 85
    DIRTY_WATER_TANK_FULL = 86
    RETRACTABLE_LEG_STUCK = 88
    INTERNAL_ERROR = 89
    ROBOT_STUCK_2 = 90
    ROBOT_STUCK_ON_TABLES = 91
    ROBOT_STUCK_ON_PASSAGE = 92
    ROBOT_STUCK_ON_THRESHOLD = 93
    ROBOT_STUCK_ON_LOW_LYING_AREA = 94
    ROBOT_STUCK_ON_RAMP = 95
    ROBOT_STUCK_ON_OBSTACLE = 96
    ROBOT_STUCK_ON_PET = 97
    ROBOT_STUCK_ON_SLIPPERY_SURFACE = 98
    ROBOT_STUCK_ON_CARPET = 99
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
    CLEAN_TANK_LEVEL = 116
    STATION_DISCONNECTED = 117
    DIRTY_TANK_LEVEL = 118
    WASHBOARD_LEVEL = 119
    NO_MOP_IN_STATION = 120
    DUST_BAG_FULL = 121
    UNKNOWN_WARNING = 122
    SELF_TEST_FAILED = 123
    WASHBOARD_NOT_WORKING = 124
    DRAINAGE_FAILED = 125
    MOP_NOT_DETECTED = 126
    MOP_HOLDER_ERROR = 127
    DOCK_ERROR = 128
    WASH_FAILED = 129
    ROBOT_STUCK_ON_CURTAIN = 200
    EDGE_MOP_STOP_ROTATE = 201
    EDGE_MOP_DETACHED = 202
    CHASSIS_LIFT_MALFUNCTION = 203
    INTERNAL_ERROR_2 = 207
    MOP_COVER_ERROR = 209
    ROLLER_MOP_ERROR = 210
    ONBOARD_WATER_TANK_EMPTY = 213
    ONBOARD_DIRTY_WATER_TANK_FULL = 214
    MOP_NOT_INSTALLED = 215
    ROLLER_MOP_ERROR_2 = 218
    FLUFFING_ROLLER_ERROR = 222
    MOP_COVER_ERROR_2 = 223
    BLOCKED_BY_OBSTACLE = 226
    RETURN_TO_CHARGE_FAILED = 1000


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
    RETURNING_TO_WASH = 10
    BUILDING = 11
    SWEEPING_AND_MOPPING = 12
    CHARGING_COMPLETED = 13
    UPGRADING = 14
    CLEAN_SUMMON = 15
    STATION_RESET = 16
    RETURNING_INSTALL_MOP = 17
    RETURNING_REMOVE_MOP = 18
    WATER_CHECK = 19
    CLEAN_ADD_WATER = 20
    WASHING_PAUSED = 21
    AUTO_EMPTYING = 22
    REMOTE_CONTROL = 23
    SMART_CHARGING = 24
    SECOND_CLEANING = 25
    HUMAN_FOLLOWING = 26
    SPOT_CLEANING = 27
    RETURNING_AUTO_EMPTY = 28
    WAITING_FOR_TASK = 29
    STATION_CLEANING = 30
    RETURNING_TO_DRAIN = 31
    DRAINING = 32
    AUTO_WATER_DRAINING = 33
    EMPTYING = 34
    DUST_BAG_DRYING = 35
    DUST_BAG_DRYING_PAUSED = 36
    HEADING_TO_EXTRA_CLEANING = 37
    EXTRA_CLEANING = 38
    FINDING_PET_PAUSED = 95
    FINDING_PET = 96
    SHORTCUT = 97
    MONITORING = 98
    MONITORING_PAUSED = 99
    INITIAL_DEEP_CLEANING = 101
    INITIAL_DEEP_CLEANING_PAUSED = 102
    SANITIZING = 103
    SANITIZING_WITH_DRY = 104
    CHANGING_MOP = 105
    CHANGING_MOP_PAUSED = 106
    FLOOR_MAINTAINING = 107
    FLOOR_MAINTAINING_PAUSED = 108


class DreameVacuumStateOld(IntEnum):
    """Dreame Vacuum old state"""

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
    RETURNING_TO_WASH = 10
    BUILDING = 11
    SWEEPING_AND_MOPPING = 12
    CHARGING_COMPLETED = 13
    UPGRADING = 14
    CLEAN_SUMMON = 15
    STATION_RESET = 16
    RETURNING_INSTALL_MOP = 17
    RETURNING_REMOVE_MOP = 18
    REMOTE_CONTROL = 19
    CLEAN_ADD_WATER = 20
    MONITORING = 21
    MONITORING_PAUSED = 21
    WASHING_PAUSED = 23
    AUTO_EMPTYING = 24
    WATER_CHECK = 25
    SMART_CHARGING = 26


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
    SWEEPING_AND_MOPPING = 2
    MOPPING_AFTER_SWEEPING = 3


class DreameVacuumWaterTank(IntEnum):
    """Dreame Vacuum water tank status"""

    UNKNOWN = -1
    NOT_INSTALLED = 0
    INSTALLED = 1
    MOP_INSTALLED = 10
    MOP_IN_STATION = 99


class DreameVacuumWaterVolume(IntEnum):
    """Dreame Vacuum water volume"""

    UNKNOWN = -1
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class DreameVacuumMopPadHumidity(IntEnum):
    """Dreame Vacuum mop pad humidity"""

    UNKNOWN = -1
    SLIGHTLY_DRY = 1
    MOIST = 2
    WET = 3


class DreameVacuumCarpetSensitivity(IntEnum):
    """Dreame Vacuum carpet sensitivity"""

    UNKNOWN = -1
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class DreameVacuumCarpetCleaning(IntEnum):
    """Dreame Vacuum carpet cleaning"""

    UNKNOWN = -1
    NOT_SET = 0
    AVOIDANCE = 1
    ADAPTATION = 2
    REMOVE_MOP = 3
    ADAPTATION_WITHOUT_ROUTE = 4
    VACUUM_AND_MOP = 5
    IGNORE = 6
    CROSS = 7


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
    CRUISING_PATH = 20
    CRUISING_PATH_PAUSED = 21
    CRUISING_POINT = 22
    CRUISING_POINT_PAUSED = 23
    SUMMON_CLEAN_PAUSED = 24
    RETURNING_INSTALL_MOP = 25
    RETURNING_REMOVE_MOP = 26
    STATION_CLEANING = 27
    PET_FINDING = 30
    AUTO_CLEANING_WASHING_PAUSED = 31
    AREA_CLEANING_WASHING_PAUSED = 32
    CUSTOM_CLEANING_WASHING_PAUSED = 33


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
    SELF_REPAIR = 15
    FACTORY_FUNCION_TEST = 16
    STANDBY = 17
    SEGMENT_CLEANING = 18
    ZONE_CLEANING = 19
    SPOT_CLEANING = 20
    FAST_MAPPING = 21
    CRUISING_PATH = 22
    CRUISING_POINT = 23
    SUMMON_CLEAN = 24
    SHORTCUT = 25
    PERSON_FOLLOW = 26
    WATER_CHECK = 1501


class DreameVacuumDustCollection(IntEnum):
    """Dreame Vacuum dust collection availability"""

    UNKNOWN = -1
    NOT_AVAILABLE = 0
    AVAILABLE = 1
    OVER_USE = 2
    NEVER = 3


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
    RETURNING = 3
    PAUSED = 4
    CLEAN_ADD_WATER = 5
    ADDING_WATER = 6
    RETURNING_FOR_DRY_MOP = 7


class DreameVacuumMopCleanFrequency(IntEnum):
    """Dreame Vacuum mop clean frequency"""

    UNKNOWN = -1
    BY_ROOM = 0
    EIGHT_SQUARE_METERS = 8
    TEN_SQUARE_METERS = 10
    FIVE_SQUARE_METERS = 5
    FIFTEEN_SQUARE_METERS = 15
    TWENTY_SQUARE_METERS = 20
    TWENTYFIVE_SQUARE_METERS = 25


class DreameVacuumMopWashLevel(IntEnum):
    """Dreame Vacuum mop wash level"""

    UNKNOWN = -1
    WATER_SAVING = 0
    DAILY = 1
    DEEP = 2


class DreameVacuumMoppingType(IntEnum):
    """Dreame Vacuum mopping type"""

    UNKNOWN = -1
    DAILY = 0
    ACCURATE = 1
    DEEP = 2


class DreameVacuumCleaningRoute(IntEnum):
    """Dreame Vacuum Cleaning route"""

    UNKNOWN = -1
    NOT_SET = 0
    STANDARD = 1
    INTENSIVE = 2
    DEEP = 3
    QUICK = 4


class DreameVacuumCustomMoppingRoute(IntEnum):
    """Dreame Vacuum Mopping route"""

    UNKNOWN = -2
    OFF = -1
    STANDARD = 0
    INTENSIVE = 1
    DEEP = 2


class DreameVacuumWiderCornerCoverage(IntEnum):
    """Dreame Vacuum wider corner coverage"""

    UNKNOWN = -1
    OFF = 0
    HIGH_FREQUENCY = 1
    LOW_FREQUENCY = 7


class DreameVacuumMopPadSwing(IntEnum):
    """Dreame Vacuum mop pad swing"""

    UNKNOWN = -1
    OFF = 0
    AUTO = 1
    DAILY = 2
    WEEKLY = 7


class DreameVacuumMopExtendFrequency(IntEnum):
    """Dreame Vacuum mop extend frequency"""

    UNKNOWN = -1
    STANDARD = 7
    INTELLIGENT = 1
    HIGH = 2


class DreameVacuumSelfCleanFrequency(IntEnum):
    """Dreame Vacuum self clean frequency"""

    UNKNOWN = -1
    BY_AREA = 1
    BY_TIME = 2
    BY_ROOM = 3
    INTELLIGENT = 4


class DreameVacuumAutoEmptyMode(IntEnum):
    """Dreame Vacuum auto empty mode"""

    UNKNOWN = -1
    OFF = 0
    STANDARD = 1
    HIGH_FREQUENCY = 2
    LOW_FREQUENCY = 3


class DreameVacuumAutoEmptyModeV2(IntEnum):
    """Dreame Vacuum auto empty mode"""

    UNKNOWN = -1
    OFF = 0
    STANDARD = 1
    INTELLIGENT = 2
    LOW_FREQUENCY = 3
    CUSTOM_FREQUENCY = 4
    HIGH_FREQUENCY = 5


class DreameVacuumCleanGenius(IntEnum):
    """Dreame Vacuum CleanGenius"""

    UNKNOWN = -1
    OFF = 0
    ROUTINE_CLEANING = 1
    DEEP_CLEANING = 2


class DreameVacuumCleanGeniusMode(IntEnum):
    """Dreame Vacuum CleanGenius mode"""

    UNKNOWN = -1
    VACUUM_AND_MOP = 2
    MOP_AFTER_VACUUM = 3


class DreameVacuumSecondCleaning(IntEnum):
    """Dreame Vacuum Second Cleaning mode"""

    UNKNOWN = -1
    OFF = 0
    IN_DEEP_MODE = 1
    IN_ALL_MODES = 2


class DreameVacuumFloorMaterial(IntEnum):
    """Dreame Vacuum floor material"""

    UNKNOWN = -1
    NONE = 0
    WOOD = 1
    TILE = 2
    MEDIUM_PILE_CARPET = 5
    LOW_PILE_CARPET = 6
    CARPET = 7


class DreameVacuumFloorMaterialDirection(IntEnum):
    """Dreame Vacuum floor direction"""

    UNKNOWN = -1
    HORIZONTAL = 0
    VERTICAL = 90


class DreameVacuumSegmentVisibility(IntEnum):
    """Dreame Vacuum segment visibility"""

    HIDDEN = 0
    VISIBLE = 1


class DreameVacuumVoiceAssistantLanguage(str, Enum):
    """Dreame Vacuum assistant language"""

    DEFAULT = ""
    ENGLISH = "EN"
    GERMAN = "DE"
    RUSSIAN = "RU"
    ITALIAN = "IT"
    FRENCH = "FR"
    KOREAN = "KO"
    CHINESE = "ZH"


class DreameVacuumMopPressure(IntEnum):
    """Dreame Vacuum mop pressure"""

    UNKNOWN = -1
    LIGHT = 0
    NORMAL = 2


class DreameVacuumMopTemperature(IntEnum):
    """Dreame Vacuum mop temperature"""

    UNKNOWN = -1
    NORMAL = 0
    WARM = 1


class DreameVacuumLowLyingAreaFrequency(IntEnum):
    """Dreame Vacuum low lying area frequency"""

    UNKNOWN = -1
    WEEKLY = 0
    DAILY = 1


class DreameVacuumScraperFrequency(IntEnum):
    """Dreame Vacuum scraper frequency"""

    UNKNOWN = -1
    OFF = 0
    WEEKLY = 1
    DAILY = 2


class DreameVacuumStreamStatus(IntEnum):
    """Dreame Vacuum stream status"""

    UNKNOWN = -1
    IDLE = 0
    VIDEO = 1
    AUDIO = 2
    RECORDING = 3


class DreameVacuumLowWaterWarning(IntEnum):
    """Dreame Vacuum low water warning"""

    UNKNOWN = -1
    NO_WARNING = 0
    NO_WATER_LEFT_DISMISS = 1
    NO_WATER_LEFT = 2
    NO_WATER_LEFT_AFTER_CLEAN = 3
    NO_WATER_FOR_CLEAN = 4
    LOW_WATER = 5
    TANK_NOT_INSTALLED = 6


class DreameVacuumDrainageStatus(IntEnum):
    """Dreame Vacuum drainage status"""

    UNKNOWN = -1
    IDLE = 0
    DRAINING = 1
    DRAINING_SUCCESS = 2
    DRAINING_FAILED = 3


class DreameVacuumTaskType(IntEnum):
    """Dreame Vacuum task type status"""

    UNKNOWN = -1
    IDLE = 0
    STANDARD = 1
    STANDARD_PAUSED = 2
    CUSTOM = 3
    CUSTOM_PAUSED = 4
    SHORTCUT = 5
    SHORTCUT_PAUSED = 6
    SCHEDULED = 7
    SCHEDULED_PAUSED = 8
    SMART = 9
    SMART_PAUSED = 10
    PARTIAL = 11
    PARTIAL_PAUSED = 12
    SUMMON = 13
    SUMMON_PAUSED = 14
    WATER_STAIN = 15
    WATER_STAIN_PAUSED = 16
    BOOSTED_EDGE_CLEANING = 17
    HAIR_COMPRESSING = 18
    LARGE_PARTICLE_CLEANING = 19
    INTENSIVE_STAIN_CLEANING = 20
    STAIN_CLEANING = 21
    INITIAL_DEEP_CLEANING = 22
    INITIAL_DEEP_CLEANING_PAUSED = 23
    MOP_PAD_HEATING = 24
    CLEANING_AFTER_MAPPING = 25
    SMALL_PARTICLE_CLEANING = 26
    CHANGING_MOP = 30
    CHANGING_MOP_PAUSED = 31
    FLOOR_MAINTAINING = 32
    FLOOR_MAINTAINING_PAUSED = 33
    WOOD_FLOOR_MAINTAINING = 36


class DreameVacuumMapRecoveryStatus(IntEnum):
    """Dreame Vacuum map recovery status"""

    UNKNOWN = -1
    IDLE = 0
    RUNNING = 2
    SUCCESS = 3
    FAIL = 4
    FAIL_2 = 5


class DreameVacuumMapBackupStatus(IntEnum):
    """Dreame Vacuum map backup status"""

    UNKNOWN = -1
    IDLE = 0
    RUNNING = 2
    SUCCESS = 3
    FAIL = 4


class DreameVacuumCleanWaterTankStatus(IntEnum):
    """Dreame Vacuum clean water tank status"""

    UNKNOWN = -1
    INSTALLED = 0
    NOT_INSTALLED = 1
    LOW_WATER = 2
    CHECKING = 3


class DreameVacuumDirtyWaterTankStatus(IntEnum):
    """Dreame Vacuum dirty water tank status"""

    UNKNOWN = -1
    INSTALLED = 0
    NOT_INSTALLED_OR_FULL = 1


class DreameVacuumDustBagStatus(IntEnum):
    """Dreame Vacuum dust bag status"""

    UNKNOWN = -1
    INSTALLED = 0
    NOT_INSTALLED = 1
    CHECK = 2


class DreameVacuumDetergentStatus(IntEnum):
    """Dreame Vacuum detergent status"""

    UNKNOWN = -1
    INSTALLED = 0
    DISABLED = 1
    LOW_DETERGENT = 2


class DreameVacuumHotWaterStatus(IntEnum):
    """Dreame Vacuum hot water status"""

    UNKNOWN = -1
    DISABLED = 0
    ENABLED = 1


class DreameVacuumStationDrainageStatus(IntEnum):
    """Dreame Vacuum station drainage status"""

    UNKNOWN = -1
    IDLE = 0
    DRAINING = 1


class DreameVacuumWashingMode(IntEnum):
    """Dreame Vacuum washing mode"""

    UNKNOWN = -1
    LIGHT = 0
    STANDARD = 1
    DEEP = 2
    ULTRA_WASHING = 3


class DreameVacuumWaterTemperature(IntEnum):
    """Dreame Vacuum water temperature"""

    UNKNOWN = -1
    NORMAL = 0
    MILD = 1
    WARM = 2
    HOT = 3
    MAX = 4


class DreameVacuumDustBagDryingStatus(IntEnum):
    """Dreame Vacuum dust bag drying status"""

    UNKNOWN = -1
    IDLE = 0
    DRYING = 1
    PAUSED = 2


class DreameVacuumAutoLDSCoverage(IntEnum):
    """Dreame Vacuum auto lds coverage"""

    UNKNOWN = -1
    OFF = 0
    SECURITY = 1
    EXTREME = 2


class DreameVacuumShortcutTaskType(IntEnum):
    UNKNOWN = -1
    ALL = 0
    SEGMENT = 1
    ZONE = 2
    CUSTOMIZED_CLEANING = 3


class DreameVacuumProperty(IntEnum):
    """Dreame Vacuum properties"""

    STATE = 0
    ERROR = 1
    BATTERY_LEVEL = 2
    CHARGING_STATUS = 3
    OFF_PEAK_CHARGING = 4
    STATUS = 5
    CLEANING_TIME = 6
    CLEANED_AREA = 7
    SUCTION_LEVEL = 8
    WATER_VOLUME = 9
    WATER_TANK = 10
    TASK_STATUS = 11
    CLEANING_START_TIME = 12
    CLEAN_LOG_FILE_NAME = 13
    CLEANING_PROPERTIES = 14
    RESUME_CLEANING = 15
    CARPET_BOOST = 16
    CLEAN_LOG_STATUS = 17
    SERIAL_NUMBER = 18
    REMOTE_CONTROL = 19
    MOP_CLEANING_REMAINDER = 20
    CLEANING_PAUSED = 21
    FAULTS = 22
    NATION_MATCHED = 23
    RELOCATION_STATUS = 24
    OBSTACLE_AVOIDANCE = 25
    AI_DETECTION = 26
    CLEANING_MODE = 27
    UPLOAD_MAP = 28
    SELF_WASH_BASE_STATUS = 29
    CUSTOMIZED_CLEANING = 30
    CHILD_LOCK = 31
    CARPET_SENSITIVITY = 32
    TIGHT_MOPPING = 33
    CLEANING_CANCEL = 34
    Y_CLEAN = 35
    WATER_ELECTROLYSIS = 36
    CARPET_RECOGNITION = 37
    SELF_CLEAN = 38
    WARN_STATUS = 39
    CARPET_CLEANING = 40
    AUTO_ADD_DETERGENT = 41
    CAPABILITY = 42
    SAVE_WATER_TIPS = 43
    DRYING_TIME = 44
    LOW_WATER_WARNING = 45
    MAP_INDEX = 46
    MAP_NAME = 47
    CRUISE_TYPE = 48
    MOP_WASH_LEVEL = 49
    AUTO_MOUNT_MOP = 50
    SCHEDULED_CLEAN = 51
    SHORTCUTS = 52
    INTELLIGENT_RECOGNITION = 53
    AUTO_SWITCH_SETTINGS = 54
    AUTO_WATER_REFILLING = 55
    MOP_IN_STATION = 56
    MOP_PAD_INSTALLED = 57
    WATER_CHECK = 58
    DRY_STOP_REMAINDER = 59
    NUMERIC_MESSAGE_PROMPT = 60
    MESSAGE_PROMPT = 61
    TASK_TYPE = 62
    PET_DETECTIVE = 63
    DRAINAGE_STATUS = 64
    DOCK_CLEANING_STATUS = 65
    BACK_CLEAN_MODE = 66
    CLEANING_PROGRESS = 67
    DRYING_PROGRESS = 68
    DEVICE_CAPABILITY = 69
    DND = 70
    DND_START = 71
    DND_END = 72
    DND_TASK = 73
    MAP_DATA = 74
    FRAME_INFO = 75
    OBJECT_NAME = 76
    MAP_EXTEND_DATA = 77
    ROBOT_TIME = 78
    RESULT_CODE = 79
    MULTI_FLOOR_MAP = 80
    MAP_LIST = 81
    RECOVERY_MAP_LIST = 82
    MAP_RECOVERY = 83
    MAP_RECOVERY_STATUS = 84
    OLD_MAP_DATA = 85
    MAP_BACKUP_STATUS = 86
    WIFI_MAP = 87
    RESTORE_MAP_BY_AREA = 88
    VOLUME = 89
    VOICE_PACKET_ID = 90
    VOICE_CHANGE_STATUS = 91
    VOICE_CHANGE = 92
    VOICE_ASSISTANT = 93
    VOICE_ASSISTANT_LANGUAGE = 94
    EMPTY_STAMP = 95
    CURRENT_CITY = 96
    VOICE_TEST = 97
    LISTEN_LANGUAGE_TYPE = 98
    BAIDU_LOG = 99
    RESPONSE_WORD = 100
    DREAME_GPT = 101
    LISTEN_LANGUAGE = 102
    LISTEN_LANGUAGE_STATUS = 103
    TIMEZONE = 104
    SCHEDULE = 105
    SCHEDULE_ID = 106
    SCHEDULE_CANCEL_REASON = 107
    CRUISE_SCHEDULE = 108
    MAIN_BRUSH_TIME_LEFT = 109
    MAIN_BRUSH_LEFT = 110
    SIDE_BRUSH_TIME_LEFT = 111
    SIDE_BRUSH_LEFT = 112
    FILTER_LEFT = 113
    FILTER_TIME_LEFT = 114
    FIRST_CLEANING_DATE = 115
    TOTAL_CLEANING_TIME = 116
    CLEANING_COUNT = 117
    TOTAL_CLEANED_AREA = 118
    TOTAL_RUNTIME = 119
    TOTAL_CRUISE_TIME = 120
    MAP_SAVING = 121
    KEEP_ALIVE = 122
    AUTO_DUST_COLLECTING = 123
    AUTO_EMPTY_FREQUENCY = 124
    DUST_COLLECTION = 125
    AUTO_EMPTY_STATUS = 126
    SENSOR_DIRTY_LEFT = 127
    SENSOR_DIRTY_TIME_LEFT = 128
    MOP_PAD_LEFT = 129
    MOP_PAD_TIME_LEFT = 130
    TANK_FILTER_LEFT = 131
    TANK_FILTER_TIME_LEFT = 132
    SILVER_ION_TIME_LEFT = 133
    SILVER_ION_LEFT = 134
    SILVER_ION_ADD = 135
    DETERGENT_LEFT = 136
    DETERGENT_TIME_LEFT = 137
    SQUEEGEE_LEFT = 138
    SQUEEGEE_TIME_LEFT = 139
    DIRTY_WATER_CHANNEL_DIRTY_TIME_LEFT = 140
    DIRTY_WATER_CHANNEL_DIRTY_LEFT = 141
    ONBOARD_DIRTY_WATER_TANK_TIME_LEFT = 142
    ONBOARD_DIRTY_WATER_TANK_LEFT = 143
    CLEAN_WATER_TANK_STATUS = 144
    DIRTY_WATER_TANK_STATUS = 145
    DUST_BAG_STATUS = 146
    DETERGENT_STATUS = 147
    STATION_DRAINAGE_STATUS = 148
    AI_MAP_OPTIMIZATION_STATUS = 149
    SECOND_CLEANING_STATUS = 150
    WATER_TANK_STATUS = 151
    ADD_CLEANING_AREA_STATUS = 152
    ADD_CLEANING_AREA_RESULT = 153
    FIRST_CONNECT_WIFI = 154
    HAND_DUST_STATUS = 155
    HAND_DUST_CONNECT_STATUS = 156
    HOT_WATER_STATUS = 157
    THRESHOLD_CONFIRMATION_STATUS = 158
    DUST_BAG_DRYING_LEFT = 159
    DUST_BAG_DRYING_STATUS = 160
    DUST_BOX_STATUS = 161
    ROLLER_COVER = 162
    CABIN_DOOR_DRYING_LEFT_TIME = 163
    MOP_TRANSPORT_CARRIER_RESET = 164
    MOP_TRANSPORT_CARRIER_STATUS = 165
    ROLLER_COVER_STATUS = 166
    WASHBOARD_CLEANING_STATUS = 167
    MECHANICAL_FOOT_STATUS = 168
    STATION_OTA_STATUS = 169
    WETNESS_LEVEL = 170
    CLEAN_CARPETS_FIRST = 171
    AUTO_LDS_COVERAGE = 172
    LDS_STATE = 173
    CLEANGENIUS_MODE = 174
    QUICK_WASH_MODE = 175
    WATER_TEMPERATURE = 176
    CLEAN_EFFICIENCY = 177
    IMPACT_INJECTION_PUMP = 178
    OBSTACLE_VIDEOS = 179
    DND_DISABLE_RESUME_CLEANING = 180
    DND_DISABLE_AUTO_EMPTY = 181
    DND_REDUCE_VOLUME = 182
    HAND_VACUUM_AUTO_DUSTING = 183
    DYNAMIC_OBSTACLE_CLEANING = 185
    HUMAN_NOISE_REDUCTION = 186
    PET_CARE = 187
    LOWER_HATCH_CONTROL = 188
    SMART_MOP_WASHING = 189
    BLOCK_HEALTH_CHECKS = 190
    MOP_AFTER_VACUUM = 191
    SMALL_AREA_FAST_CLEAN = 192
    SHIELD_ULTRASONIC_SIGNALS = 193
    SILENT_DRYING = 194
    HAIR_COMPRESSION = 195
    SIDE_BRUSH_CARPET_ROTATE = 196
    ERP_LOW_POWER = 197
    SHIELD_WASHBOARD_IN_PLACE = 198
    SELF_CLEANING_PROBLEM = 199
    WASHING_TEST = 200
    FEEDBACK_SWITCH = 201
    CARPET_AI_SEGMENT = 202
    OBSTACLE_CROSSING = 203
    VISUAL_RESUME = 204
    FAN_ABNORMAL_NOISE = 205
    LARGE_MEMORY_RESET = 206
    BOW_BEFORE_EDGE = 207
    VOLTAGE = 208
    DETERGENT_A = 209
    DETERGENT_B = 210
    MOP_TEMPERATURE = 211
    BATTERY_CHARGE_LEVEL = 212
    DUST_BAG_DRYING = 213
    SWEEP_DISTANCE = 214
    LOW_LYING_AREA_FREQUENCY = 215
    MOPPING_WITH_DETERGENT = 216
    PRESSURIZED_CLEANING = 217
    SCRAPER_FREQUENCY = 218
    REALTIME_PARTICLE_DETECT = 219
    IGNORE_STAIRS = 220
    LIFT_CHASSIS_ON_CARPET = 221
    RING_LIGHT_ALWAYS_ON = 222
    AUTO_CHANGE_MOP = 223
    POWER_SAVING = 224
    WHEEL_LIFT_BOOST_MOPPING = 225
    CABIN_DOOR_DRYING_TIME = 226
    CABIN_DOOR_SILENT_DRYING = 227
    CABIN_DOOR_DRYING = 228
    CLOSE_ROLLER_COVER_ON_CARPET = 229
    FLOOR_MAINTAINING = 230
    DETERGENT_C = 231
    STORE_MODE = 232
    INTEGRATED_POWER = 233
    INTELLIGENT_STAIN_CLEANING = 234
    ACTIVE_SUSPENSION_CROSSING = 235
    SHIELD_ROLLER_ACTIVE = 236
    MOP_PRESSURE = 237
    PET_AI_MODEL = 238
    LOWER_LDS_WHILE_DOCKING = 239
    RL_NAVIGATION_MESSAGE = 240
    DUST_LIGHT = 241
    QUICK_MOP_SWITCHING = 242
    BLOCK_AGENCY_ALARM = 243
    EXHIBITION_MODE = 244
    AUTO_EMPTY_AREA = 245
    DEODORIZER_TIME_LEFT = 246
    DEODORIZER_LEFT = 247
    WHEEL_DIRTY_TIME_LEFT = 248
    WHEEL_DIRTY_LEFT = 249
    SCALE_INHIBITOR_TIME_LEFT = 250
    SCALE_INHIBITOR_LEFT = 251
    FLUFFING_ROLLER_DIRTY_LEFT = 252
    FLUFFING_ROLLER_DIRTY_TIME_LEFT = 253
    ROLLER_MOP_FILTER_DIRTY_TIME_LEFT = 254
    ROLLER_MOP_FILTER_DIRTY_LEFT = 255
    WATER_OUTLET_FILTER_DIRTY_TIME_LEFT = 256
    WATER_OUTLET_FILTER_DIRTY_LEFT = 257
    FACTORY_TEST_STATUS = 258
    FACTORY_TEST_RESULT = 259
    SELF_TEST_STATUS = 260
    LSD_TEST_STATUS = 261
    DEBUG_SWITCH = 262
    SERIAL = 263
    CALIBRATION_STATUS = 264
    VERSION = 265
    PERFORMANCE_SWITCH = 266
    AI_TEST_STATUS = 267
    PUBLIC_KEY = 268
    AUTO_PAIR = 269
    MCU_VERSION = 270
    MOP_TEST_STATUS = 271
    PLATFORM_NETWORK = 272
    STREAM_STATUS = 273
    STREAM_AUDIO = 274
    STREAM_RECORD = 275
    TAKE_PHOTO = 276
    STREAM_KEEP_ALIVE = 277
    STREAM_FAULT = 278
    CAMERA_LIGHT_BRIGHTNESS = 279
    CAMERA_LIGHT = 280
    STREAM_VENDOR = 281
    STREAM_PROPERTY = 282
    STREAM_CRUISE_POINT = 283
    STREAM_TASK = 284
    STEAM_HUMAN_FOLLOW = 285
    OBSTACLE_VIDEO_STATUS = 286
    OBSTACLE_VIDEO_DATA = 287
    STREAM_UPLOAD = 288
    STREAM_CODE = 289
    STREAM_SET_CODE = 290
    STREAM_VERIFY_CODE = 291
    STREAM_RESET_CODE = 292
    STREAM_SPACE = 293


class DreameVacuumAutoSwitchProperty(str, Enum):
    """Dreame Vacuum Auto Switch properties"""

    COLLISION_AVOIDANCE = "LessColl"
    FILL_LIGHT = "FillinLight"
    AUTO_DRYING = "AutoDry"
    STAIN_AVOIDANCE = "StainIdentify"
    MOPPING_TYPE = "CleanType"
    CLEANGENIUS = "SmartHost"
    WIDER_CORNER_COVERAGE = "MeticulousTwist"
    FLOOR_DIRECTION_CLEANING = "MaterialDirectionClean"
    PET_FOCUSED_CLEANING = "PetPartClean"
    AUTO_RECLEANING = "SmartAutoMop"
    AUTO_REWASHING = "SmartAutoWash"
    MOP_PAD_SWING = "MopScalable"
    AUTO_CHARGING = "SmartCharge"
    HUMAN_FOLLOW = "MonitorHumanFollow"
    MAX_SUCTION_POWER = "SuctionMax"
    SMART_DRYING = "SmartDrying"
    DRAINAGE_CONFIRM_RESULT = "FluctuationConfirmResult"
    DRAINAGE_TEST_RESULT = "FluctuationTestResult"
    HOT_WASHING = "HotWash"
    UV_STERILIZATION = "UVLight"
    CLEANING_ROUTE = "CleanRoute"
    CUSTOM_MOPPING_MODE = "MopEffectSwitch"
    MOPPING_MODE = "MopEffectState"
    SELF_CLEAN_FREQUENCY = "BackWashType"
    INTENSIVE_CARPET_CLEANING = "CarpetFineClean"
    GAP_CLEANING_EXTENSION = "LacuneMopScalable"
    MOPPING_UNDER_FURNITURES = "MopScalable2"
    # CLEAN_CARPETS_FIRST = "CarpetFirstClean"
    ULTRA_CLEAN_MODE = "SuperWash"
    STREAMING_VOICE_PROMPT = "MonitorPromptLevel"
    MOP_EXTEND = "MopExtrSwitch"
    MOP_EXTEND_FREQUENCY = "ExtrFreq"
    SIDE_REACH = "SbrushExtrSwitch"
    INTELLIGENT_STAIN_CLEANING = "HeavyStainSmart"


class DreameVacuumStrAIProperty(str, Enum):
    """Dreame Vacuum json AI obstacle detection properties"""

    AI_OBSTACLE_DETECTION = "obstacle_detect_switch"
    AI_OBSTACLE_IMAGE_UPLOAD = "obstacle_app_display_switch"
    AI_PET_DETECTION = "whether_have_pet"
    AI_HUMAN_DETECTION = "human_detect_switch"
    AI_FURNITURE_DETECTION = "furniture_detect_switch"
    AI_FLUID_DETECTION = "fluid_detect_switch"


class DreameVacuumAIProperty(IntEnum):
    """Dreame Vacuum bitwise AI obstacle detection properties"""

    AI_FURNITURE_DETECTION = 1
    AI_OBSTACLE_DETECTION = 2
    AI_OBSTACLE_PICTURE = 4
    AI_FLUID_DETECTION = 8
    AI_PET_DETECTION = 16
    AI_OBSTACLE_IMAGE_UPLOAD = 32
    AI_IMAGE = 64
    AI_PET_AVOIDANCE = 128
    FUZZY_OBSTACLE_DETECTION = 256
    PET_PICTURE = 512
    PET_FOCUSED_DETECTION = 1024
    LARGE_PARTICLES_BOOST = 2048


class DreameVacuumAction(IntEnum):
    """Dreame Vacuum actions"""

    START = 1
    PAUSE = 2
    CHARGE = 3
    START_CUSTOM = 4
    STOP = 5
    CLEAR_WARNING = 6
    START_WASHING = 7
    GET_PHOTO_INFO = 8
    SHORTCUTS = 9
    DELETE_DND_TASK = 10
    REQUEST_MAP = 11
    UPDATE_MAP_DATA = 12
    BACKUP_MAP = 13
    WIFI_MAP = 14
    LOCATE = 15
    TEST_SOUND = 16
    DELETE_SCHEDULED_TASK = 17
    DELETE_CRUISE_SCHEDULE = 18
    RESET_MAIN_BRUSH = 19
    RESET_SIDE_BRUSH = 20
    RESET_FILTER = 21
    RESET_SENSOR = 22
    START_AUTO_EMPTY = 23
    RESET_TANK_FILTER = 24
    RESET_MOP_PAD = 25
    RESET_SILVER_ION = 26
    RESET_DETERGENT = 27
    RESET_SQUEEGEE = 28
    RESET_DIRTY_WATER_CHANNEL = 29
    RESET_ONBOARD_DIRTY_WATER_TANK = 30
    RESET_DEODORIZER = 31
    RESET_WHEEL = 32
    RESET_SCALE_INHIBITOR = 33
    RESET_FLUFFING_ROLLER = 34
    RESET_ROLLER_MOP_FILTER = 35
    RESET_WATER_OUTLET_FILTER = 36
    STREAM_VIDEO = 37
    STREAM_AUDIO = 38
    STREAM_PROPERTY = 39
    STREAM_CODE = 40


# Dreame Vacuum property mapping
DreameVacuumPropertyMapping = {
    DreameVacuumProperty.STATE: {siid: 2, piid: 1},
    DreameVacuumProperty.ERROR: {siid: 2, piid: 2},
    DreameVacuumProperty.BATTERY_LEVEL: {siid: 3, piid: 1},
    DreameVacuumProperty.CHARGING_STATUS: {siid: 3, piid: 2},
    DreameVacuumProperty.OFF_PEAK_CHARGING: {siid: 3, piid: 3},
    DreameVacuumProperty.STATUS: {siid: 4, piid: 1},
    DreameVacuumProperty.CLEANING_TIME: {siid: 4, piid: 2},
    DreameVacuumProperty.CLEANED_AREA: {siid: 4, piid: 3},
    DreameVacuumProperty.SUCTION_LEVEL: {siid: 4, piid: 4},
    DreameVacuumProperty.WATER_VOLUME: {siid: 4, piid: 5},
    DreameVacuumProperty.WATER_TANK: {siid: 4, piid: 6},
    DreameVacuumProperty.TASK_STATUS: {siid: 4, piid: 7},
    DreameVacuumProperty.CLEANING_START_TIME: {siid: 4, piid: 8},
    DreameVacuumProperty.CLEAN_LOG_FILE_NAME: {siid: 4, piid: 9},
    DreameVacuumProperty.CLEANING_PROPERTIES: {siid: 4, piid: 10},
    DreameVacuumProperty.RESUME_CLEANING: {siid: 4, piid: 11},
    DreameVacuumProperty.CARPET_BOOST: {siid: 4, piid: 12},
    DreameVacuumProperty.CLEAN_LOG_STATUS: {siid: 4, piid: 13},
    DreameVacuumProperty.SERIAL_NUMBER: {siid: 4, piid: 14},
    DreameVacuumProperty.REMOTE_CONTROL: {siid: 4, piid: 15},
    DreameVacuumProperty.MOP_CLEANING_REMAINDER: {siid: 4, piid: 16},
    DreameVacuumProperty.CLEANING_PAUSED: {siid: 4, piid: 17},
    DreameVacuumProperty.FAULTS: {siid: 4, piid: 18},
    DreameVacuumProperty.NATION_MATCHED: {siid: 4, piid: 19},
    DreameVacuumProperty.RELOCATION_STATUS: {siid: 4, piid: 20},
    DreameVacuumProperty.OBSTACLE_AVOIDANCE: {siid: 4, piid: 21},
    DreameVacuumProperty.AI_DETECTION: {siid: 4, piid: 22},
    DreameVacuumProperty.CLEANING_MODE: {siid: 4, piid: 23},
    DreameVacuumProperty.UPLOAD_MAP: {siid: 4, piid: 24},
    DreameVacuumProperty.SELF_WASH_BASE_STATUS: {siid: 4, piid: 25},
    DreameVacuumProperty.CUSTOMIZED_CLEANING: {siid: 4, piid: 26},
    DreameVacuumProperty.CHILD_LOCK: {siid: 4, piid: 27},
    DreameVacuumProperty.CARPET_SENSITIVITY: {siid: 4, piid: 28},
    DreameVacuumProperty.TIGHT_MOPPING: {siid: 4, piid: 29},
    DreameVacuumProperty.CLEANING_CANCEL: {siid: 4, piid: 30},
    DreameVacuumProperty.Y_CLEAN: {siid: 4, piid: 31},
    DreameVacuumProperty.WATER_ELECTROLYSIS: {siid: 4, piid: 32},
    DreameVacuumProperty.CARPET_RECOGNITION: {siid: 4, piid: 33},
    DreameVacuumProperty.SELF_CLEAN: {siid: 4, piid: 34},
    DreameVacuumProperty.WARN_STATUS: {siid: 4, piid: 35},
    DreameVacuumProperty.CARPET_CLEANING: {siid: 4, piid: 36},
    DreameVacuumProperty.AUTO_ADD_DETERGENT: {siid: 4, piid: 37},
    DreameVacuumProperty.CAPABILITY: {siid: 4, piid: 38},
    DreameVacuumProperty.SAVE_WATER_TIPS: {siid: 4, piid: 39},
    DreameVacuumProperty.DRYING_TIME: {siid: 4, piid: 40},
    DreameVacuumProperty.LOW_WATER_WARNING: {siid: 4, piid: 41},
    DreameVacuumProperty.MAP_INDEX: {siid: 4, piid: 42},
    DreameVacuumProperty.MAP_NAME: {siid: 4, piid: 43},
    DreameVacuumProperty.CRUISE_TYPE: {siid: 4, piid: 44},
    DreameVacuumProperty.AUTO_MOUNT_MOP: {siid: 4, piid: 45},
    DreameVacuumProperty.MOP_WASH_LEVEL: {siid: 4, piid: 46},
    DreameVacuumProperty.SCHEDULED_CLEAN: {siid: 4, piid: 47},
    DreameVacuumProperty.SHORTCUTS: {siid: 4, piid: 48},
    DreameVacuumProperty.INTELLIGENT_RECOGNITION: {siid: 4, piid: 49},
    DreameVacuumProperty.AUTO_SWITCH_SETTINGS: {siid: 4, piid: 50},
    DreameVacuumProperty.AUTO_WATER_REFILLING: {siid: 4, piid: 51},
    DreameVacuumProperty.MOP_IN_STATION: {siid: 4, piid: 52},
    DreameVacuumProperty.MOP_PAD_INSTALLED: {siid: 4, piid: 53},
    DreameVacuumProperty.WATER_CHECK: {siid: 4, piid: 54},
    DreameVacuumProperty.DRY_STOP_REMAINDER: {siid: 4, piid: 55},
    DreameVacuumProperty.NUMERIC_MESSAGE_PROMPT: {siid: 4, piid: 56},
    DreameVacuumProperty.MESSAGE_PROMPT: {siid: 4, piid: 57},
    DreameVacuumProperty.TASK_TYPE: {siid: 4, piid: 58},
    DreameVacuumProperty.PET_DETECTIVE: {siid: 4, piid: 59},
    DreameVacuumProperty.DRAINAGE_STATUS: {siid: 4, piid: 60},
    DreameVacuumProperty.DOCK_CLEANING_STATUS: {siid: 4, piid: 61},
    DreameVacuumProperty.BACK_CLEAN_MODE: {siid: 4, piid: 62},
    DreameVacuumProperty.CLEANING_PROGRESS: {siid: 4, piid: 63},
    DreameVacuumProperty.DRYING_PROGRESS: {siid: 4, piid: 64},
    DreameVacuumProperty.DEVICE_CAPABILITY: {siid: 4, piid: 83},
    # DreameVacuumProperty.COMBINED_DATA: {siid: 4, piid: 99},
    DreameVacuumProperty.DND: {siid: 5, piid: 1},
    DreameVacuumProperty.DND_START: {siid: 5, piid: 2},
    DreameVacuumProperty.DND_END: {siid: 5, piid: 3},
    DreameVacuumProperty.DND_TASK: {siid: 5, piid: 4},
    DreameVacuumProperty.MAP_DATA: {siid: 6, piid: 1},
    DreameVacuumProperty.FRAME_INFO: {siid: 6, piid: 2},
    DreameVacuumProperty.OBJECT_NAME: {siid: 6, piid: 3},
    DreameVacuumProperty.MAP_EXTEND_DATA: {siid: 6, piid: 4},
    DreameVacuumProperty.ROBOT_TIME: {siid: 6, piid: 5},
    DreameVacuumProperty.RESULT_CODE: {siid: 6, piid: 6},
    DreameVacuumProperty.MULTI_FLOOR_MAP: {siid: 6, piid: 7},
    DreameVacuumProperty.MAP_LIST: {siid: 6, piid: 8},
    DreameVacuumProperty.RECOVERY_MAP_LIST: {siid: 6, piid: 9},
    DreameVacuumProperty.MAP_RECOVERY: {siid: 6, piid: 10},
    DreameVacuumProperty.MAP_RECOVERY_STATUS: {siid: 6, piid: 11},
    DreameVacuumProperty.OLD_MAP_DATA: {siid: 6, piid: 13},
    DreameVacuumProperty.MAP_BACKUP_STATUS: {siid: 6, piid: 14},
    DreameVacuumProperty.WIFI_MAP: {siid: 6, piid: 15},
    DreameVacuumProperty.RESTORE_MAP_BY_AREA: {siid: 6, piid: 16},
    DreameVacuumProperty.VOLUME: {siid: 7, piid: 1},
    DreameVacuumProperty.VOICE_PACKET_ID: {siid: 7, piid: 2},
    DreameVacuumProperty.VOICE_CHANGE_STATUS: {siid: 7, piid: 3},
    DreameVacuumProperty.VOICE_CHANGE: {siid: 7, piid: 4},
    DreameVacuumProperty.VOICE_ASSISTANT: {siid: 7, piid: 5},
    DreameVacuumProperty.EMPTY_STAMP: {siid: 7, piid: 6},
    DreameVacuumProperty.CURRENT_CITY: {siid: 7, piid: 7},
    DreameVacuumProperty.VOICE_TEST: {siid: 7, piid: 9},
    DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE: {siid: 7, piid: 10},
    DreameVacuumProperty.LISTEN_LANGUAGE_TYPE: {siid: 7, piid: 10},
    DreameVacuumProperty.BAIDU_LOG: {siid: 7, piid: 11},
    DreameVacuumProperty.RESPONSE_WORD: {siid: 7, piid: 12},
    DreameVacuumProperty.DREAME_GPT: {siid: 7, piid: 14},
    DreameVacuumProperty.LISTEN_LANGUAGE: {siid: 7, piid: 15},
    DreameVacuumProperty.LISTEN_LANGUAGE_STATUS: {siid: 7, piid: 16},
    DreameVacuumProperty.TIMEZONE: {siid: 8, piid: 1},
    DreameVacuumProperty.SCHEDULE: {siid: 8, piid: 2},
    DreameVacuumProperty.SCHEDULE_ID: {siid: 8, piid: 3},
    DreameVacuumProperty.SCHEDULE_CANCEL_REASON: {siid: 8, piid: 4},
    DreameVacuumProperty.CRUISE_SCHEDULE: {siid: 8, piid: 5},
    DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT: {siid: 9, piid: 1},
    DreameVacuumProperty.MAIN_BRUSH_LEFT: {siid: 9, piid: 2},
    DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT: {siid: 10, piid: 1},
    DreameVacuumProperty.SIDE_BRUSH_LEFT: {siid: 10, piid: 2},
    DreameVacuumProperty.FILTER_LEFT: {siid: 11, piid: 1},
    DreameVacuumProperty.FILTER_TIME_LEFT: {siid: 11, piid: 2},
    DreameVacuumProperty.FIRST_CLEANING_DATE: {siid: 12, piid: 1},
    DreameVacuumProperty.TOTAL_CLEANING_TIME: {siid: 12, piid: 2},
    DreameVacuumProperty.CLEANING_COUNT: {siid: 12, piid: 3},
    DreameVacuumProperty.TOTAL_CLEANED_AREA: {siid: 12, piid: 4},
    DreameVacuumProperty.TOTAL_RUNTIME: {siid: 12, piid: 5},
    DreameVacuumProperty.TOTAL_CRUISE_TIME: {siid: 12, piid: 6},
    DreameVacuumProperty.MAP_SAVING: {siid: 13, piid: 1},
    DreameVacuumProperty.KEEP_ALIVE: {siid: 14, piid: 4},
    DreameVacuumProperty.AUTO_DUST_COLLECTING: {siid: 15, piid: 1},
    DreameVacuumProperty.AUTO_EMPTY_FREQUENCY: {siid: 15, piid: 2},
    DreameVacuumProperty.DUST_COLLECTION: {siid: 15, piid: 3},
    DreameVacuumProperty.AUTO_EMPTY_STATUS: {siid: 15, piid: 5},
    DreameVacuumProperty.SENSOR_DIRTY_LEFT: {siid: 16, piid: 1},
    DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT: {siid: 16, piid: 2},
    DreameVacuumProperty.TANK_FILTER_LEFT: {siid: 17, piid: 1},
    DreameVacuumProperty.TANK_FILTER_TIME_LEFT: {siid: 17, piid: 2},
    DreameVacuumProperty.MOP_PAD_LEFT: {siid: 18, piid: 1},
    DreameVacuumProperty.MOP_PAD_TIME_LEFT: {siid: 18, piid: 2},
    DreameVacuumProperty.SILVER_ION_TIME_LEFT: {siid: 19, piid: 1},
    DreameVacuumProperty.SILVER_ION_LEFT: {siid: 19, piid: 2},
    DreameVacuumProperty.SILVER_ION_ADD: {siid: 19, piid: 3},
    DreameVacuumProperty.DETERGENT_LEFT: {siid: 20, piid: 1},
    DreameVacuumProperty.DETERGENT_TIME_LEFT: {siid: 20, piid: 2},
    DreameVacuumProperty.SQUEEGEE_LEFT: {siid: 24, piid: 1},
    DreameVacuumProperty.SQUEEGEE_TIME_LEFT: {siid: 24, piid: 2},
    DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_TIME_LEFT: {siid: 25, piid: 1},
    DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_LEFT: {siid: 25, piid: 2},
    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT: {siid: 26, piid: 1},
    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT: {siid: 26, piid: 2},
    DreameVacuumProperty.CLEAN_WATER_TANK_STATUS: {siid: 27, piid: 1},
    DreameVacuumProperty.DIRTY_WATER_TANK_STATUS: {siid: 27, piid: 2},
    DreameVacuumProperty.DUST_BAG_STATUS: {siid: 27, piid: 3},
    DreameVacuumProperty.DETERGENT_STATUS: {siid: 27, piid: 4},
    DreameVacuumProperty.STATION_DRAINAGE_STATUS: {siid: 27, piid: 5},
    DreameVacuumProperty.AI_MAP_OPTIMIZATION_STATUS: {siid: 27, piid: 7},
    DreameVacuumProperty.SECOND_CLEANING_STATUS: {siid: 27, piid: 8},
    DreameVacuumProperty.WATER_TANK_STATUS: {siid: 27, piid: 9},
    DreameVacuumProperty.ADD_CLEANING_AREA_STATUS: {siid: 27, piid: 10},
    DreameVacuumProperty.ADD_CLEANING_AREA_RESULT: {siid: 27, piid: 11},
    DreameVacuumProperty.FIRST_CONNECT_WIFI: {siid: 27, piid: 12},
    DreameVacuumProperty.HAND_DUST_STATUS: {siid: 27, piid: 13},
    DreameVacuumProperty.HAND_DUST_CONNECT_STATUS: {siid: 27, piid: 14},
    DreameVacuumProperty.HOT_WATER_STATUS: {siid: 27, piid: 15},
    DreameVacuumProperty.THRESHOLD_CONFIRMATION_STATUS: {siid: 27, piid: 16},
    DreameVacuumProperty.DUST_BAG_DRYING_LEFT: {siid: 27, piid: 17},
    DreameVacuumProperty.DUST_BAG_DRYING_STATUS: {siid: 27, piid: 18},
    DreameVacuumProperty.DUST_BOX_STATUS: {siid: 27, piid: 19},
    DreameVacuumProperty.ROLLER_COVER: {siid: 27, piid: 20},
    DreameVacuumProperty.CABIN_DOOR_DRYING_LEFT_TIME: {siid: 27, piid: 21},
    DreameVacuumProperty.MOP_TRANSPORT_CARRIER_RESET: {siid: 27, piid: 24},
    DreameVacuumProperty.MOP_TRANSPORT_CARRIER_STATUS: {siid: 27, piid: 25},
    DreameVacuumProperty.ROLLER_COVER_STATUS: {siid: 27, piid: 26},
    DreameVacuumProperty.WASHBOARD_CLEANING_STATUS: {siid: 27, piid: 27},
    DreameVacuumProperty.MECHANICAL_FOOT_STATUS: {siid: 27, piid: 28},
    DreameVacuumProperty.STATION_OTA_STATUS: {siid: 27, piid: 30},
    DreameVacuumProperty.WETNESS_LEVEL: {siid: 28, piid: 1},
    DreameVacuumProperty.CLEAN_CARPETS_FIRST: {siid: 28, piid: 2},
    DreameVacuumProperty.AUTO_LDS_COVERAGE: {siid: 28, piid: 3},
    DreameVacuumProperty.LDS_STATE: {siid: 28, piid: 4},
    DreameVacuumProperty.CLEANGENIUS_MODE: {siid: 28, piid: 5},
    DreameVacuumProperty.QUICK_WASH_MODE: {siid: 28, piid: 6},
    DreameVacuumProperty.WATER_TEMPERATURE: {siid: 28, piid: 8},
    DreameVacuumProperty.CLEAN_EFFICIENCY: {siid: 28, piid: 9},
    DreameVacuumProperty.IMPACT_INJECTION_PUMP: {siid: 28, piid: 12},
    DreameVacuumProperty.OBSTACLE_VIDEOS: {siid: 28, piid: 13},
    DreameVacuumProperty.DND_DISABLE_RESUME_CLEANING: {siid: 28, piid: 14},
    DreameVacuumProperty.DND_DISABLE_AUTO_EMPTY: {siid: 28, piid: 15},
    DreameVacuumProperty.DND_REDUCE_VOLUME: {siid: 28, piid: 16},
    DreameVacuumProperty.HAND_VACUUM_AUTO_DUSTING: {siid: 28, piid: 17},
    DreameVacuumProperty.DYNAMIC_OBSTACLE_CLEANING: {siid: 28, piid: 18},
    DreameVacuumProperty.HUMAN_NOISE_REDUCTION: {siid: 28, piid: 19},
    DreameVacuumProperty.PET_CARE: {siid: 28, piid: 20},
    DreameVacuumProperty.LOWER_HATCH_CONTROL: {siid: 28, piid: 21},
    DreameVacuumProperty.SMART_MOP_WASHING: {siid: 28, piid: 22},
    DreameVacuumProperty.BLOCK_HEALTH_CHECKS: {siid: 28, piid: 23},
    DreameVacuumProperty.MOP_AFTER_VACUUM: {siid: 28, piid: 24},
    DreameVacuumProperty.SMALL_AREA_FAST_CLEAN: {siid: 28, piid: 25},
    DreameVacuumProperty.SHIELD_ULTRASONIC_SIGNALS: {siid: 28, piid: 26},
    DreameVacuumProperty.SILENT_DRYING: {siid: 28, piid: 27},
    DreameVacuumProperty.HAIR_COMPRESSION: {siid: 28, piid: 28},
    DreameVacuumProperty.SIDE_BRUSH_CARPET_ROTATE: {siid: 28, piid: 29},
    DreameVacuumProperty.ERP_LOW_POWER: {siid: 28, piid: 30},
    DreameVacuumProperty.SHIELD_WASHBOARD_IN_PLACE: {siid: 28, piid: 31},
    DreameVacuumProperty.SELF_CLEANING_PROBLEM: {siid: 28, piid: 32},
    DreameVacuumProperty.WASHING_TEST: {siid: 28, piid: 33},
    DreameVacuumProperty.FEEDBACK_SWITCH: {siid: 28, piid: 36},
    DreameVacuumProperty.CARPET_AI_SEGMENT: {siid: 28, piid: 37},
    DreameVacuumProperty.OBSTACLE_CROSSING: {siid: 28, piid: 38},
    DreameVacuumProperty.VISUAL_RESUME: {siid: 28, piid: 39},
    DreameVacuumProperty.FAN_ABNORMAL_NOISE: {siid: 28, piid: 40},
    DreameVacuumProperty.LARGE_MEMORY_RESET: {siid: 28, piid: 41},
    DreameVacuumProperty.BOW_BEFORE_EDGE: {siid: 28, piid: 42},
    DreameVacuumProperty.VOLTAGE: {siid: 28, piid: 43},
    DreameVacuumProperty.DETERGENT_A: {siid: 28, piid: 44},
    DreameVacuumProperty.DETERGENT_B: {siid: 28, piid: 45},
    DreameVacuumProperty.MOP_TEMPERATURE: {siid: 28, piid: 46},
    DreameVacuumProperty.BATTERY_CHARGE_LEVEL: {siid: 28, piid: 47},
    DreameVacuumProperty.DUST_BAG_DRYING: {siid: 28, piid: 48},
    DreameVacuumProperty.SWEEP_DISTANCE: {siid: 28, piid: 49},
    DreameVacuumProperty.LOW_LYING_AREA_FREQUENCY: {siid: 28, piid: 51},
    DreameVacuumProperty.MOPPING_WITH_DETERGENT: {siid: 28, piid: 52},
    DreameVacuumProperty.PRESSURIZED_CLEANING: {siid: 28, piid: 53},
    DreameVacuumProperty.SCRAPER_FREQUENCY: {siid: 28, piid: 54},
    DreameVacuumProperty.REALTIME_PARTICLE_DETECT: {siid: 28, piid: 58},
    DreameVacuumProperty.IGNORE_STAIRS: {siid: 28, piid: 59},
    DreameVacuumProperty.LIFT_CHASSIS_ON_CARPET: {siid: 28, piid: 60},
    DreameVacuumProperty.RING_LIGHT_ALWAYS_ON: {siid: 28, piid: 61},
    DreameVacuumProperty.AUTO_CHANGE_MOP: {siid: 28, piid: 62},
    DreameVacuumProperty.POWER_SAVING: {siid: 28, piid: 63},
    DreameVacuumProperty.WHEEL_LIFT_BOOST_MOPPING: {siid: 28, piid: 64},
    DreameVacuumProperty.CABIN_DOOR_DRYING_TIME: {siid: 28, piid: 66},
    DreameVacuumProperty.CABIN_DOOR_SILENT_DRYING: {siid: 28, piid: 67},
    DreameVacuumProperty.CABIN_DOOR_DRYING: {siid: 28, piid: 68},
    DreameVacuumProperty.CLOSE_ROLLER_COVER_ON_CARPET: {siid: 28, piid: 69},
    DreameVacuumProperty.FLOOR_MAINTAINING: {siid: 28, piid: 75},
    DreameVacuumProperty.DETERGENT_C: {siid: 28, piid: 76},
    DreameVacuumProperty.STORE_MODE: {siid: 28, piid: 79},
    DreameVacuumProperty.INTEGRATED_POWER: {siid: 28, piid: 81},
    DreameVacuumProperty.INTELLIGENT_STAIN_CLEANING: {siid: 28, piid: 83},
    DreameVacuumProperty.ACTIVE_SUSPENSION_CROSSING: {siid: 28, piid: 84},
    DreameVacuumProperty.SHIELD_ROLLER_ACTIVE: {siid: 28, piid: 85},
    DreameVacuumProperty.MOP_PRESSURE: {siid: 28, piid: 86},
    DreameVacuumProperty.PET_AI_MODEL: {siid: 28, piid: 87},
    DreameVacuumProperty.LOWER_LDS_WHILE_DOCKING: {siid: 28, piid: 88},
    DreameVacuumProperty.RL_NAVIGATION_MESSAGE: {siid: 28, piid: 89},
    DreameVacuumProperty.DUST_LIGHT: {siid: 28, piid: 90},
    DreameVacuumProperty.QUICK_MOP_SWITCHING: {siid: 28, piid: 92},
    DreameVacuumProperty.BLOCK_AGENCY_ALARM: {siid: 28, piid: 93},
    DreameVacuumProperty.EXHIBITION_MODE: {siid: 28, piid: 94},
    DreameVacuumProperty.AUTO_EMPTY_AREA: {siid: 28, piid: 95},
    DreameVacuumProperty.DEODORIZER_TIME_LEFT: {siid: 29, piid: 1},
    DreameVacuumProperty.DEODORIZER_LEFT: {siid: 29, piid: 2},
    DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT: {siid: 30, piid: 1},
    DreameVacuumProperty.WHEEL_DIRTY_LEFT: {siid: 30, piid: 2},
    DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT: {siid: 31, piid: 1},
    DreameVacuumProperty.SCALE_INHIBITOR_LEFT: {siid: 31, piid: 2},
    DreameVacuumProperty.FLUFFING_ROLLER_DIRTY_LEFT: {siid: 32, piid: 1},
    DreameVacuumProperty.FLUFFING_ROLLER_DIRTY_TIME_LEFT: {siid: 32, piid: 2},
    DreameVacuumProperty.ROLLER_MOP_FILTER_DIRTY_TIME_LEFT: {siid: 33, piid: 1},
    DreameVacuumProperty.ROLLER_MOP_FILTER_DIRTY_LEFT: {siid: 33, piid: 2},
    DreameVacuumProperty.WATER_OUTLET_FILTER_DIRTY_TIME_LEFT: {siid: 35, piid: 1},
    DreameVacuumProperty.WATER_OUTLET_FILTER_DIRTY_LEFT: {siid: 35, piid: 2},
    DreameVacuumProperty.FACTORY_TEST_STATUS: {siid: 99, piid: 1},
    DreameVacuumProperty.FACTORY_TEST_RESULT: {siid: 99, piid: 3},
    DreameVacuumProperty.SELF_TEST_STATUS: {siid: 99, piid: 8},
    DreameVacuumProperty.LSD_TEST_STATUS: {siid: 99, piid: 9},
    DreameVacuumProperty.DEBUG_SWITCH: {siid: 99, piid: 11},
    DreameVacuumProperty.SERIAL: {siid: 99, piid: 14},
    DreameVacuumProperty.CALIBRATION_STATUS: {siid: 99, piid: 15},
    DreameVacuumProperty.VERSION: {siid: 99, piid: 17},
    DreameVacuumProperty.PERFORMANCE_SWITCH: {siid: 99, piid: 24},
    DreameVacuumProperty.AI_TEST_STATUS: {siid: 99, piid: 25},
    DreameVacuumProperty.PUBLIC_KEY: {siid: 99, piid: 27},
    DreameVacuumProperty.AUTO_PAIR: {siid: 99, piid: 28},
    DreameVacuumProperty.MCU_VERSION: {siid: 99, piid: 31},
    DreameVacuumProperty.MOP_TEST_STATUS: {siid: 99, piid: 35},
    DreameVacuumProperty.PLATFORM_NETWORK: {siid: 99, piid: 95},
    DreameVacuumProperty.STREAM_STATUS: {siid: 10001, piid: 1},
    DreameVacuumProperty.STREAM_AUDIO: {siid: 10001, piid: 2},
    DreameVacuumProperty.STREAM_RECORD: {siid: 10001, piid: 4},
    DreameVacuumProperty.TAKE_PHOTO: {siid: 10001, piid: 5},
    DreameVacuumProperty.STREAM_KEEP_ALIVE: {siid: 10001, piid: 6},
    DreameVacuumProperty.STREAM_FAULT: {siid: 10001, piid: 7},
    DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS: {siid: 10001, piid: 9},
    DreameVacuumProperty.CAMERA_LIGHT: {siid: 10001, piid: 10},
    DreameVacuumProperty.STREAM_VENDOR: {siid: 10001, piid: 11},
    DreameVacuumProperty.STREAM_PROPERTY: {siid: 10001, piid: 99},
    DreameVacuumProperty.STREAM_CRUISE_POINT: {siid: 10001, piid: 101},
    DreameVacuumProperty.STREAM_TASK: {siid: 10001, piid: 103},
    DreameVacuumProperty.STEAM_HUMAN_FOLLOW: {siid: 10001, piid: 110},
    DreameVacuumProperty.OBSTACLE_VIDEO_STATUS: {siid: 10001, piid: 111},
    DreameVacuumProperty.OBSTACLE_VIDEO_DATA: {siid: 10001, piid: 112},
    DreameVacuumProperty.STREAM_UPLOAD: {siid: 10001, piid: 1003},
    DreameVacuumProperty.STREAM_CODE: {siid: 10001, piid: 1100},
    DreameVacuumProperty.STREAM_SET_CODE: {siid: 10001, piid: 1101},
    DreameVacuumProperty.STREAM_VERIFY_CODE: {siid: 10001, piid: 1102},
    DreameVacuumProperty.STREAM_RESET_CODE: {siid: 10001, piid: 1103},
    DreameVacuumProperty.STREAM_SPACE: {siid: 10001, piid: 2003},
}


# Dreame Vacuum action mapping
DreameVacuumActionMapping = {
    DreameVacuumAction.START: {siid: 2, aiid: 1},
    DreameVacuumAction.PAUSE: {siid: 2, aiid: 2},
    DreameVacuumAction.CHARGE: {siid: 3, aiid: 1},
    DreameVacuumAction.START_CUSTOM: {siid: 4, aiid: 1},
    DreameVacuumAction.STOP: {siid: 4, aiid: 2},
    DreameVacuumAction.CLEAR_WARNING: {siid: 4, aiid: 3},
    DreameVacuumAction.START_WASHING: {siid: 4, aiid: 4},
    DreameVacuumAction.GET_PHOTO_INFO: {siid: 4, aiid: 6},
    DreameVacuumAction.SHORTCUTS: {siid: 4, aiid: 8},
    DreameVacuumAction.DELETE_DND_TASK: {siid: 5, aiid: 1},
    DreameVacuumAction.REQUEST_MAP: {siid: 6, aiid: 1},
    DreameVacuumAction.UPDATE_MAP_DATA: {siid: 6, aiid: 2},
    DreameVacuumAction.BACKUP_MAP: {siid: 6, aiid: 3},
    DreameVacuumAction.WIFI_MAP: {siid: 6, aiid: 4},
    DreameVacuumAction.LOCATE: {siid: 7, aiid: 1},
    DreameVacuumAction.TEST_SOUND: {siid: 7, aiid: 2},
    DreameVacuumAction.DELETE_SCHEDULED_TASK: {siid: 8, aiid: 1},
    DreameVacuumAction.DELETE_CRUISE_SCHEDULE: {siid: 8, aiid: 2},
    DreameVacuumAction.RESET_MAIN_BRUSH: {siid: 9, aiid: 1},
    DreameVacuumAction.RESET_SIDE_BRUSH: {siid: 10, aiid: 1},
    DreameVacuumAction.RESET_FILTER: {siid: 11, aiid: 1},
    DreameVacuumAction.RESET_SENSOR: {siid: 16, aiid: 1},
    DreameVacuumAction.START_AUTO_EMPTY: {siid: 15, aiid: 1},
    DreameVacuumAction.RESET_TANK_FILTER: {siid: 17, aiid: 1},
    DreameVacuumAction.RESET_MOP_PAD: {siid: 18, aiid: 1},
    DreameVacuumAction.RESET_SILVER_ION: {siid: 19, aiid: 1},
    DreameVacuumAction.RESET_DETERGENT: {siid: 20, aiid: 1},
    DreameVacuumAction.RESET_SQUEEGEE: {siid: 24, aiid: 1},
    DreameVacuumAction.RESET_DIRTY_WATER_CHANNEL: {siid: 25, aiid: 1},
    DreameVacuumAction.RESET_ONBOARD_DIRTY_WATER_TANK: {siid: 26, aiid: 1},
    DreameVacuumAction.RESET_DEODORIZER: {siid: 29, aiid: 1},
    DreameVacuumAction.RESET_WHEEL: {siid: 30, aiid: 1},
    DreameVacuumAction.RESET_SCALE_INHIBITOR: {siid: 31, aiid: 1},
    DreameVacuumAction.RESET_FLUFFING_ROLLER: {siid: 32, aiid: 1},
    DreameVacuumAction.RESET_ROLLER_MOP_FILTER: {siid: 33, aiid: 1},
    DreameVacuumAction.RESET_WATER_OUTLET_FILTER: {siid: 35, aiid: 1},
    DreameVacuumAction.STREAM_VIDEO: {siid: 10001, aiid: 1},
    DreameVacuumAction.STREAM_AUDIO: {siid: 10001, aiid: 2},
    DreameVacuumAction.STREAM_PROPERTY: {siid: 10001, aiid: 3},
    DreameVacuumAction.STREAM_CODE: {siid: 10001, aiid: 4},
}


PROPERTY_AVAILABILITY: Final = {
    DreameVacuumProperty.CUSTOMIZED_CLEANING.name: lambda device: not device.status.started
    and (device.status.has_saved_map or device.status.current_map is None)
    and not device.status.cleangenius_cleaning,
    DreameVacuumProperty.TIGHT_MOPPING.name: lambda device: (device.status.water_tank_or_mop_installed)
    and not device.status.cleangenius_cleaning,
    DreameVacuumProperty.MULTI_FLOOR_MAP.name: lambda device: not device.status.has_temporary_map
    and not device.status.started,
    DreameVacuumProperty.SUCTION_LEVEL.name: lambda device: not device.status.mopping
    and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning))
    and not device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and not device.status.scheduled_clean
    and not device.status.cruising
    and not device.status.max_suction_power,
    DreameVacuumAutoSwitchProperty.MAX_SUCTION_POWER.name: lambda device: (
        (device.capability.max_suction_power_extended and device.status.mopping_after_sweeping)
        or device.status.sweeping
    )
    and not device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and not device.status.scheduled_clean
    and not device.status.cruising
    and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning)),
    DreameVacuumProperty.WATER_VOLUME.name: lambda device: (device.status.water_tank_or_mop_installed)
    and not device.status.sweeping
    and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning))
    and not device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and not device.status.scheduled_clean
    and not device.status.cruising,
    DreameVacuumProperty.WETNESS_LEVEL.name: lambda device: (device.status.water_tank_or_mop_installed)
    and not device.status.sweeping
    and not device.status.fast_mapping
    and not device.status.scheduled_clean
    and not device.status.cruising
    and not device.status.cleangenius_cleaning
    and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning)),
    DreameVacuumProperty.CLEANING_MODE.name: lambda device: (
        not device.status.started or not device.status.mopping_after_sweeping
    )
    and not device.status.fast_mapping
    and not device.status.scheduled_clean
    and not device.status.cruising
    and (not device.status.customized_cleaning or not device.capability.custom_cleaning_mode)
    and not device.status.cleangenius_cleaning
    and not device.status.returning_to_wash
    and not device.status.shortcut_task,
    DreameVacuumProperty.CARPET_SENSITIVITY.name: lambda device: bool(
        device.get_property(DreameVacuumProperty.CARPET_BOOST)
    ),
    DreameVacuumProperty.CARPET_BOOST.name: lambda device: not device.capability.carpet_recognition
    or (device.status.carpet_recognition and not device.status.carpet_avoidance),
    DreameVacuumProperty.CARPET_CLEANING.name: lambda device: device.status.carpet_recognition
    or device.capability.mop_pad_lifting_plus
    or device.capability.auto_carpet_cleaning,
    DreameVacuumProperty.AUTO_EMPTY_FREQUENCY.name: lambda device: bool(
        device.get_property(DreameVacuumProperty.AUTO_DUST_COLLECTING)
    ),
    DreameVacuumProperty.CLEANING_TIME.name: lambda device: not device.status.fast_mapping
    and not device.status.cruising,
    DreameVacuumProperty.CLEANED_AREA.name: lambda device: not device.status.fast_mapping
    and not device.status.cruising,
    DreameVacuumProperty.RELOCATION_STATUS.name: lambda device: not device.status.fast_mapping,
    DreameVacuumProperty.AUTO_ADD_DETERGENT.name: lambda device: bool(
        device.get_property(DreameVacuumProperty.AUTO_ADD_DETERGENT) != 2
    ),
    DreameVacuumProperty.INTELLIGENT_RECOGNITION.name: lambda device: device.status.multi_map,
    DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE.name: lambda device: bool(
        device.get_property(DreameVacuumProperty.VOICE_ASSISTANT) == 1
    ),
    DreameVacuumProperty.STREAM_STATUS.name: lambda device: bool(
        device.get_property(DreameVacuumProperty.STREAM_STATUS) is not None
    ),
    DreameVacuumProperty.LOW_WATER_WARNING.name: lambda device: not device.status.auto_water_refilling_enabled,
    DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS.name: lambda device: bool(
        device.status.camera_light_brightness
        and device.status.camera_light_brightness != 101
        and device.status.stream_session is not None
    ),
    DreameVacuumProperty.DRYING_TIME.name: lambda device: not device.status.smart_drying and device.status.auto_drying,
    DreameVacuumProperty.MOP_WASH_LEVEL.name: lambda device: device.status.self_clean,
    DreameVacuumProperty.TASK_TYPE.name: lambda device: device.status.task_type.value > 0,
    DreameVacuumProperty.CLEANING_PROGRESS.name: lambda device: bool(
        device.status.started and not device.status.cruising
    ),
    DreameVacuumProperty.DRYING_PROGRESS.name: lambda device: device.status.drying,
    DreameVacuumProperty.DUST_BAG_DRYING_LEFT.name: lambda device: device.status.dust_bag_drying,
    DreameVacuumProperty.CLEAN_CARPETS_FIRST.name: lambda device: not (
        not device.status.carpet_recognition or device.status.carpet_avoidance
    ),
    DreameVacuumProperty.MOP_PRESSURE.name: lambda device: (device.status.water_tank_or_mop_installed)
    and not device.status.sweeping
    and not device.status.fast_mapping
    and not device.status.scheduled_clean
    and not device.status.cruising
    and not device.status.cleangenius_cleaning
    and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning)),
    DreameVacuumProperty.MOP_TEMPERATURE.name: lambda device: (device.status.water_tank_or_mop_installed)
    and not device.status.sweeping
    and not device.status.fast_mapping
    and not device.status.scheduled_clean
    and not device.status.cruising
    and not device.status.cleangenius_cleaning
    and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning)),
    DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE.name: lambda device: not device.status.started
    and not device.status.fast_mapping
    and not device.status.washing
    and not device.status.washing_paused,
    DreameVacuumAutoSwitchProperty.MOP_PAD_SWING.name: lambda device: not device.status.started
    and not device.status.fast_mapping
    and not device.status.washing
    and not device.status.washing_paused,
    DreameVacuumAutoSwitchProperty.MOP_EXTEND_FREQUENCY.name: lambda device: not device.status.started
    and not device.status.fast_mapping
    and not device.status.washing
    and not device.status.washing_paused,
    DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY.name: lambda device: device.status.self_clean
    and not device.status.started
    and not device.status.fast_mapping
    and not device.status.cleangenius_cleaning,
    DreameVacuumAutoSwitchProperty.STAIN_AVOIDANCE.name: lambda device: device.status.ai_fluid_detection,
    DreameVacuumAutoSwitchProperty.CLEANGENIUS.name: lambda device: not device.status.started
    and not device.status.fast_mapping
    and not device.status.cruising
    and not device.status.spot_cleaning
    and not device.status.zone_cleaning
    and device.status.mop_pad_installed,
    DreameVacuumProperty.CLEANGENIUS_MODE.name: lambda device: not device.status.started
    and device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and not device.status.cruising
    and not device.status.spot_cleaning
    and not device.status.zone_cleaning
    and device.status.mop_pad_installed,
    DreameVacuumAutoSwitchProperty.FLOOR_DIRECTION_CLEANING.name: lambda device: device.status.floor_direction_cleaning_available,
    DreameVacuumAutoSwitchProperty.MOPPING_TYPE.name: lambda device: not device.status.started
    and not device.status.fast_mapping,
    DreameVacuumStrAIProperty.AI_HUMAN_DETECTION.name: lambda device: device.status.ai_obstacle_detection,
    DreameVacuumAIProperty.AI_OBSTACLE_IMAGE_UPLOAD.name: lambda device: device.status.ai_obstacle_detection,
    DreameVacuumAIProperty.AI_OBSTACLE_PICTURE.name: lambda device: device.status.ai_obstacle_detection,
    DreameVacuumAIProperty.AI_PET_DETECTION.name: lambda device: device.status.ai_obstacle_detection,
    DreameVacuumAIProperty.AI_FURNITURE_DETECTION.name: lambda device: device.status.ai_obstacle_detection,
    DreameVacuumAIProperty.AI_FLUID_DETECTION.name: lambda device: device.status.ai_obstacle_detection,
    DreameVacuumAIProperty.FUZZY_OBSTACLE_DETECTION.name: lambda device: device.status.ai_obstacle_detection,
    DreameVacuumAIProperty.AI_PET_AVOIDANCE.name: lambda device: device.status.ai_obstacle_detection
    and device.status.ai_pet_detection,
    DreameVacuumAIProperty.PET_PICTURE.name: lambda device: device.status.ai_obstacle_detection
    and device.status.ai_pet_detection,
    DreameVacuumAIProperty.PET_FOCUSED_DETECTION.name: lambda device: device.status.ai_obstacle_detection
    and device.status.ai_pet_detection,
    DreameVacuumAutoSwitchProperty.GAP_CLEANING_EXTENSION.name: lambda device: (
        device.status.mop_extend if device.capability.mop_extend else device.status.mop_pad_swing.value > 0
    ),
    DreameVacuumAutoSwitchProperty.MOPPING_UNDER_FURNITURES.name: lambda device: (
        device.status.mop_extend if device.capability.mop_extend else device.status.mop_pad_swing.value > 0
    ),
    DreameVacuumAutoSwitchProperty.AUTO_RECLEANING.name: lambda device: not device.status.has_temporary_map
    and device.status.has_saved_map
    and not device.status.fast_mapping
    and not device.status.started,
    DreameVacuumAutoSwitchProperty.AUTO_REWASHING.name: lambda device: not device.status.has_temporary_map
    and device.status.has_saved_map
    and not device.status.fast_mapping
    and not device.status.started,
    DreameVacuumAutoSwitchProperty.CLEANING_ROUTE.name: lambda device: not device.status.has_temporary_map
    and device.status.has_saved_map
    and device.status.cleaning_route.value > 0
    and not device.status.fast_mapping
    and not device.status.started
    and (not device.status.customized_cleaning or not device.capability.custom_cleaning_mode)
    and not device.status.cleangenius_cleaning,
    DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE.name: lambda device: device.status.self_clean
    and device.status.auto_water_refilling_enabled,
    DreameVacuumAutoSwitchProperty.INTENSIVE_CARPET_CLEANING.name: lambda device: not device.status.started
    and device.status.carpet_recognition
    and not device.status.carpet_avoidance,
    DreameVacuumProperty.FIRST_CLEANING_DATE.name: lambda device: device.get_property(
        DreameVacuumProperty.FIRST_CLEANING_DATE
    ),
    DreameVacuumProperty.WATER_TEMPERATURE.name: lambda device: not device.status.smart_mop_washing
    and device.status.self_clean,
    DreameVacuumProperty.SILENT_DRYING.name: lambda device: not device.status.drying,
    DreameVacuumProperty.SIDE_BRUSH_CARPET_ROTATE.name: lambda device: not device.status.started
    and device.status.carpet_recognition
    and not device.status.carpet_avoidance,
    DreameVacuumProperty.CLEAN_CARPETS_FIRST.name: lambda device: not device.status.started
    and device.status.carpet_recognition
    and not device.status.carpet_avoidance,
    DreameVacuumProperty.LIFT_CHASSIS_ON_CARPET.name: lambda device: not device.status.started
    and device.status.carpet_recognition
    and not device.status.carpet_avoidance,
    DreameVacuumProperty.CLOSE_ROLLER_COVER_ON_CARPET.name: lambda device: not device.status.started
    and device.status.carpet_recognition
    and not device.status.carpet_avoidance,
    DreameVacuumProperty.AUTO_CHANGE_MOP.name: lambda device: device.status.has_saved_map,
    DreameVacuumProperty.DND_DISABLE_RESUME_CLEANING.name: lambda device: device.status.dnd,
    DreameVacuumProperty.DND_DISABLE_AUTO_EMPTY.name: lambda device: device.status.dnd,
    DreameVacuumProperty.DND_REDUCE_VOLUME.name: lambda device: device.status.dnd,
    DreameVacuumProperty.SMART_MOP_WASHING.name: lambda device: device.status.self_clean,
    DreameVacuumProperty.AUTO_EMPTY_AREA.name: lambda device: device.get_property(
        DreameVacuumProperty.AUTO_DUST_COLLECTING
    )
    == 4,
    DreameVacuumProperty.AUTO_LDS_COVERAGE.name: lambda device: not device.status.started
    and not device.status.washing
    and not device.status.washing_paused
    and not device.status.returning,
    DreameVacuumProperty.LDS_STATE.name: lambda device: not device.status.started
    and not device.status.washing_paused
    and not device.status.returning,
    DreameVacuumProperty.MOPPING_WITH_DETERGENT: lambda device: device.status.detergent_status
    is not DreameVacuumDetergentStatus.DISABLED
    and not device.status.washing,
    "self_clean_area": lambda device: device.status.self_clean
    and not device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and not device.status.self_clean_by_time
    and not device.status.self_clean_intelligent
    and (device.status.self_clean_value or (device.status.current_map and not device.status.has_saved_map)),
    "self_clean_time": lambda device: device.status.self_clean
    and not device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and device.status.self_clean_by_time
    and (device.status.self_clean_value or (device.status.current_map and not device.status.has_saved_map)),
    "self_clean_by_zone": lambda device: device.status.self_clean
    and not device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and device.status.self_clean_value is not None
    and (not device.status.current_map or device.status.has_saved_map),
    "mop_clean_frequency": lambda device: device.status.self_clean
    and not device.status.cleangenius_cleaning
    and not device.status.fast_mapping
    and device.status.self_clean_value is not None,
    "mop_pad_humidity": lambda device: (device.status.water_tank_or_mop_installed)
    and not device.status.cleangenius_cleaning
    and not device.status.sweeping
    and not (device.status.customized_cleaning and not (device.status.zone_cleaning or device.status.spot_cleaning))
    and not device.status.fast_mapping
    and not device.status.started
    and not device.status.scheduled_clean
    and not device.status.cruising,
    "washing_mode": lambda device: device.status.self_clean,
    "map_rotation": lambda device: bool(
        device.status.selected_map is not None
        and device.status.selected_map.rotation is not None
        and not device.status.fast_mapping
        and device.status.has_saved_map
    ),
    "selected_map": lambda device: bool(
        device.status.multi_map
        and not device.status.fast_mapping
        and device.status.map_list
        and device.status.map_data_list
        and device.status.selected_map
        and device.status.selected_map.map_name
        and device.status.selected_map.map_id in device.status.map_list
    ),
    "current_room": lambda device: device.status.current_room is not None and not device.status.fast_mapping,
    "cleaning_history": lambda device: bool(device.status.last_cleaning_time is not None),
    "cruising_history": lambda device: bool(device.status.last_cruising_time is not None),
    "cleaning_sequence": lambda device: not device.status.started
    and device.status.has_saved_map
    and device.status.current_segments
    and next(iter(device.status.current_segments.values())).order is not None,
    "camera_light_brightness_auto": lambda device: device.status.camera_light_brightness
    and device.status.stream_session is not None,
    "dnd_start": lambda device: device.status.dnd,
    "dnd_end": lambda device: device.status.dnd,
    "off_peak_charging_start": lambda device: device.status.off_peak_charging,
    "off_peak_charging_end": lambda device: device.status.off_peak_charging,
    "custom_mopping_route": lambda device: not device.status.started
    and not device.status.cleangenius_cleaning
    and not device.status.customized_cleaning,
    "self_clean": lambda device: (
        device.status.washing_available
        or device.status.washing
        or device.status.returning_to_wash_paused
        or device.status.washing_paused
    )
    and not device.status.draining
    and not device.status.self_repairing,
    "mapping_time": lambda device: device.status.fast_mapping,
}


ACTION_AVAILABILITY: Final = {
    DreameVacuumAction.RESET_MAIN_BRUSH.name: lambda device: bool(device.status.main_brush_life < 100),
    DreameVacuumAction.RESET_SIDE_BRUSH.name: lambda device: bool(device.status.side_brush_life < 100),
    DreameVacuumAction.RESET_FILTER.name: lambda device: bool(device.status.filter_life < 100),
    DreameVacuumAction.RESET_SENSOR.name: lambda device: bool(device.status.sensor_dirty_life < 100),
    DreameVacuumAction.RESET_TANK_FILTER.name: lambda device: bool(device.status.tank_filter_life < 100),
    DreameVacuumAction.RESET_MOP_PAD.name: lambda device: bool(device.status.mop_life < 100),
    DreameVacuumAction.RESET_SILVER_ION.name: lambda device: bool(device.status.silver_ion_life < 100),
    DreameVacuumAction.RESET_DETERGENT.name: lambda device: bool(device.status.detergent_life < 100),
    DreameVacuumAction.RESET_SQUEEGEE.name: lambda device: bool(device.status.squeegee_life < 100),
    DreameVacuumAction.RESET_ONBOARD_DIRTY_WATER_TANK.name: lambda device: bool(
        device.status.onboard_dirty_water_tank_life is not None and device.status.onboard_dirty_water_tank_life < 100
    ),
    DreameVacuumAction.RESET_DIRTY_WATER_CHANNEL.name: lambda device: bool(
        device.status.dirty_water_channel_dirty_life is not None and device.status.dirty_water_channel_dirty_life < 100
    ),
    DreameVacuumAction.RESET_DEODORIZER.name: lambda device: device.status.deodorizer_life is not None
    and bool(device.status.deodorizer_life < 100),
    DreameVacuumAction.RESET_WHEEL.name: lambda device: device.status.wheel_dirty_life is not None
    and bool(device.status.wheel_dirty_life < 100),
    DreameVacuumAction.RESET_SCALE_INHIBITOR.name: lambda device: device.status.scale_inhibitor_life is not None
    and bool(device.status.scale_inhibitor_life < 100),
    DreameVacuumAction.RESET_FLUFFING_ROLLER.name: lambda device: device.status.fluffing_roller_dirty_life is not None
    and bool(device.status.fluffing_roller_dirty_life < 100),
    DreameVacuumAction.RESET_ROLLER_MOP_FILTER.name: lambda device: device.status.roller_mop_filter_dirty_life
    is not None
    and bool(device.status.roller_mop_filter_dirty_life < 100),
    DreameVacuumAction.RESET_WATER_OUTLET_FILTER.name: lambda device: device.status.water_outlet_filter_dirty_life
    is not None
    and bool(device.status.water_outlet_filter_dirty_life < 100),
    DreameVacuumAction.START_AUTO_EMPTY.name: lambda device: device.status.dust_collection_available,
    DreameVacuumAction.START.name: lambda device: not (
        device.status.started or device.status.draining or device.status.self_repairing
    )
    or device.status.paused
    or device.status.returning
    or device.status.returning_paused,
    DreameVacuumAction.START_CUSTOM.name: lambda device: not (device.status.draining or device.status.self_repairing),
    DreameVacuumAction.CHARGE.name: lambda device: not device.status.docked and not device.status.returning,
    DreameVacuumAction.PAUSE.name: lambda device: device.status.started
    and not (
        device.status.returning_paused
        or device.status.paused
        or device.status.draining
        or device.status.self_repairing
    ),
    DreameVacuumAction.STOP.name: lambda device: (
        device.status.started
        or device.status.returning
        or device.status.washing
        or device.status.washing_paused
        or device.status.drying
        or device.status.returning_to_wash_paused
        or device.status.paused
    )
    and not device.status.draining
    and not device.status.self_repairing,
    "start_fast_mapping": lambda device: device.status.mapping_available
    and not device.status.draining
    and not device.status.self_repairing,
    "start_mapping": lambda device: device.status.mapping_available
    and not device.status.draining
    and not device.status.self_repairing,
    "manual_drying": lambda device: device.status.drying_available,
    "manual_dust_bag_drying": lambda device: device.status.dust_bag_drying_available,
    "water_tank_draining": lambda device: device.status.water_tank_draining_available,
    "base_station_self_repair": lambda device: not device.status.draining
    and not device.status.self_repairing
    and not device.status.started
    and not device.status.paused
    and not device.status.returning
    and not device.status.returning_paused
    and not device.status.returning_to_wash_paused
    and not device.status.washing
    and not device.status.washing_paused
    and not device.status.drying,
    "base_station_cleaning": lambda device: device.status.docked
    and (not device.status.station_cleaning or device.capability.washboard_cleaning_status)
    and device.status.water_tank_or_mop_installed
    and not device.status.draining
    and not device.status.self_repairing
    and not device.status.started
    and not device.status.paused
    and not device.status.washing
    and not device.status.washing_paused
    and not device.status.drying
    and not device.status.auto_emptying,
    "start_recleaning": lambda device: device.status.second_cleaning_available,
    "empty_water_tank": lambda device: device.status.water_tank_emptying_available,
}


CONSUMABLE_PROPERTIES: Final = [
    DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT,
    DreameVacuumProperty.MAIN_BRUSH_LEFT,
    DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT,
    DreameVacuumProperty.SIDE_BRUSH_LEFT,
    DreameVacuumProperty.FILTER_LEFT,
    DreameVacuumProperty.FILTER_TIME_LEFT,
    DreameVacuumProperty.TANK_FILTER_LEFT,
    DreameVacuumProperty.TANK_FILTER_TIME_LEFT,
    DreameVacuumProperty.SILVER_ION_TIME_LEFT,
    DreameVacuumProperty.SILVER_ION_LEFT,
    DreameVacuumProperty.DETERGENT_TIME_LEFT,
    DreameVacuumProperty.DETERGENT_LEFT,
    DreameVacuumProperty.SQUEEGEE_TIME_LEFT,
    DreameVacuumProperty.SQUEEGEE_LEFT,
    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT,
    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT,
    DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_TIME_LEFT,
    DreameVacuumProperty.DIRTY_WATER_CHANNEL_DIRTY_LEFT,
    DreameVacuumProperty.DEODORIZER_TIME_LEFT,
    DreameVacuumProperty.DEODORIZER_LEFT,
    DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT,
    DreameVacuumProperty.WHEEL_DIRTY_LEFT,
    DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT,
    DreameVacuumProperty.SCALE_INHIBITOR_LEFT,
    DreameVacuumProperty.FLUFFING_ROLLER_DIRTY_TIME_LEFT,
    DreameVacuumProperty.FLUFFING_ROLLER_DIRTY_LEFT,
    DreameVacuumProperty.ROLLER_MOP_FILTER_DIRTY_TIME_LEFT,
    DreameVacuumProperty.ROLLER_MOP_FILTER_DIRTY_LEFT,
    DreameVacuumProperty.WATER_OUTLET_FILTER_DIRTY_TIME_LEFT,
    DreameVacuumProperty.WATER_OUTLET_FILTER_DIRTY_LEFT,
]


DISCARDED_PROPERTIES: Final = [
    DreameVacuumProperty.ERROR,
    DreameVacuumProperty.STATE,
    DreameVacuumProperty.STATUS,
    DreameVacuumProperty.TASK_STATUS,
    DreameVacuumProperty.AUTO_EMPTY_STATUS,
    DreameVacuumProperty.FAULTS,
    DreameVacuumProperty.SELF_WASH_BASE_STATUS,
    DreameVacuumProperty.AUTO_SWITCH_SETTINGS,
    DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS,
    DreameVacuumProperty.AI_DETECTION,
    DreameVacuumProperty.SHORTCUTS,
    DreameVacuumProperty.MAP_BACKUP_STATUS,
    DreameVacuumProperty.MAP_RECOVERY_STATUS,
    DreameVacuumProperty.OFF_PEAK_CHARGING,
    DreameVacuumProperty.SCHEDULE,
    DreameVacuumProperty.DND_TASK,
    DreameVacuumProperty.KEEP_ALIVE,
]


READ_ONLY_PROPERTIES: Final = [
    DreameVacuumProperty.STATE,
    DreameVacuumProperty.ERROR,
    DreameVacuumProperty.FAULTS,
    DreameVacuumProperty.BATTERY_LEVEL,
    DreameVacuumProperty.CHARGING_STATUS,
    DreameVacuumProperty.STATUS,
    DreameVacuumProperty.WATER_TANK,
    DreameVacuumProperty.TASK_STATUS,
    DreameVacuumProperty.WARN_STATUS,
    DreameVacuumProperty.RELOCATION_STATUS,
    DreameVacuumProperty.SELF_WASH_BASE_STATUS,
    DreameVacuumProperty.DUST_COLLECTION,
    DreameVacuumProperty.AUTO_EMPTY_STATUS,
    DreameVacuumProperty.CLEANING_PAUSED,
    DreameVacuumProperty.CLEANING_CANCEL,
    DreameVacuumProperty.SCHEDULED_CLEAN,
    DreameVacuumProperty.MOP_IN_STATION,
    DreameVacuumProperty.MOP_PAD_INSTALLED,
    DreameVacuumProperty.LOW_WATER_WARNING,
    DreameVacuumProperty.DRAINAGE_STATUS,
    DreameVacuumProperty.TASK_TYPE,
    DreameVacuumProperty.WATER_CHECK,
    DreameVacuumProperty.MAP_RECOVERY_STATUS,
    DreameVacuumProperty.CLEAN_WATER_TANK_STATUS,
    DreameVacuumProperty.DIRTY_WATER_TANK_STATUS,
    DreameVacuumProperty.DUST_BAG_STATUS,
    DreameVacuumProperty.DETERGENT_STATUS,
    DreameVacuumProperty.STATION_DRAINAGE_STATUS,
    DreameVacuumProperty.HOT_WATER_STATUS,
    DreameVacuumProperty.ROLLER_COVER_STATUS,
    DreameVacuumProperty.DUST_BAG_DRYING_STATUS,
    DreameVacuumProperty.DUST_BAG_DRYING_LEFT,
]


READ_WRITE_PROPERTIES: Final = [
    DreameVacuumProperty.WATER_VOLUME,
    DreameVacuumProperty.SUCTION_LEVEL,
    DreameVacuumProperty.RESUME_CLEANING,
    DreameVacuumProperty.CARPET_BOOST,
    DreameVacuumProperty.MOP_CLEANING_REMAINDER,
    DreameVacuumProperty.OBSTACLE_AVOIDANCE,
    DreameVacuumProperty.AI_DETECTION,
    DreameVacuumProperty.DRYING_TIME,
    DreameVacuumProperty.AUTO_ADD_DETERGENT,
    DreameVacuumProperty.CARPET_CLEANING,
    DreameVacuumProperty.CLEANING_MODE,
    DreameVacuumProperty.WATER_ELECTROLYSIS,
    DreameVacuumProperty.INTELLIGENT_RECOGNITION,
    DreameVacuumProperty.AUTO_WATER_REFILLING,
    DreameVacuumProperty.AUTO_MOUNT_MOP,
    DreameVacuumProperty.MOP_WASH_LEVEL,
    DreameVacuumProperty.CUSTOMIZED_CLEANING,
    DreameVacuumProperty.CHILD_LOCK,
    DreameVacuumProperty.CARPET_SENSITIVITY,
    DreameVacuumProperty.TIGHT_MOPPING,
    DreameVacuumProperty.CARPET_RECOGNITION,
    DreameVacuumProperty.SELF_CLEAN,
    DreameVacuumProperty.DND_TASK,
    DreameVacuumProperty.SCHEDULE,
    DreameVacuumProperty.MULTI_FLOOR_MAP,
    DreameVacuumProperty.VOLUME,
    DreameVacuumProperty.AUTO_DUST_COLLECTING,
    DreameVacuumProperty.AUTO_EMPTY_FREQUENCY,
    DreameVacuumProperty.VOICE_PACKET_ID,
    DreameVacuumProperty.TIMEZONE,
    DreameVacuumProperty.MAP_SAVING,
    DreameVacuumProperty.AUTO_SWITCH_SETTINGS,
    DreameVacuumProperty.SHORTCUTS,
    DreameVacuumProperty.VOICE_ASSISTANT,
    DreameVacuumProperty.CRUISE_SCHEDULE,
    DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS,
    DreameVacuumProperty.STREAM_PROPERTY,
    DreameVacuumProperty.STREAM_SPACE,
    DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE,
    DreameVacuumProperty.OFF_PEAK_CHARGING,
    DreameVacuumProperty.WETNESS_LEVEL,
    DreameVacuumProperty.CLEAN_CARPETS_FIRST,
    DreameVacuumProperty.QUICK_WASH_MODE,
    DreameVacuumProperty.DND,
    DreameVacuumProperty.DND_START,
    DreameVacuumProperty.DND_END,
    DreameVacuumProperty.CLEANGENIUS_MODE,
    DreameVacuumProperty.SMART_MOP_WASHING,
    DreameVacuumProperty.WATER_TEMPERATURE,
    DreameVacuumProperty.DND_DISABLE_RESUME_CLEANING,
    DreameVacuumProperty.DND_DISABLE_AUTO_EMPTY,
    DreameVacuumProperty.DND_REDUCE_VOLUME,
    DreameVacuumProperty.SILENT_DRYING,
    DreameVacuumProperty.HAIR_COMPRESSION,
    DreameVacuumProperty.SIDE_BRUSH_CARPET_ROTATE,
    DreameVacuumProperty.AUTO_LDS_COVERAGE,
    DreameVacuumProperty.MOPPING_WITH_DETERGENT,
    DreameVacuumProperty.LIFT_CHASSIS_ON_CARPET,
    DreameVacuumProperty.CLOSE_ROLLER_COVER_ON_CARPET,
    DreameVacuumProperty.MOP_PRESSURE,
    DreameVacuumProperty.MOP_TEMPERATURE,
    DreameVacuumProperty.LOW_LYING_AREA_FREQUENCY,
    DreameVacuumProperty.SCRAPER_FREQUENCY,
    DreameVacuumProperty.AUTO_CHANGE_MOP,
    DreameVacuumProperty.DUST_BAG_DRYING,
    DreameVacuumProperty.RING_LIGHT_ALWAYS_ON,
    DreameVacuumProperty.OBSTACLE_CROSSING,
    DreameVacuumProperty.ACTIVE_SUSPENSION_CROSSING,
    DreameVacuumProperty.DYNAMIC_OBSTACLE_CLEANING,
    DreameVacuumProperty.PRESSURIZED_CLEANING,
    DreameVacuumProperty.BATTERY_CHARGE_LEVEL,
    DreameVacuumProperty.AUTO_EMPTY_AREA,
    DreameVacuumProperty.LDS_STATE,
    DreameVacuumProperty.ROLLER_COVER,
]


WARNING_ERROR_CODE: Final = [
    DreameVacuumErrorCode.REMOVE_MOP,
    DreameVacuumErrorCode.MOP_REMOVED_2,
    DreameVacuumErrorCode.CLEAN_MOP_PAD,
    DreameVacuumErrorCode.BLOCKED,
    DreameVacuumErrorCode.WATER_TANK_DRY,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE,
    DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE_2,
    DreameVacuumErrorCode.STATION_DISCONNECTED,
    DreameVacuumErrorCode.DUST_BAG_FULL,
    DreameVacuumErrorCode.SELF_TEST_FAILED,
    DreameVacuumErrorCode.LOW_BATTERY_TURN_OFF,
    DreameVacuumErrorCode.TANKBOX,
    DreameVacuumErrorCode.WATERBOX_EMPTY,
    DreameVacuumErrorCode.FILTER_BLOCKED,
    DreameVacuumErrorCode.CHECK_MOP_INSTALL,
    DreameVacuumErrorCode.WASH_FAILED,
    DreameVacuumErrorCode.LASER,
    DreameVacuumErrorCode.BATTERY_LOW,
    DreameVacuumErrorCode.SLIPPERY_FLOOR,
    DreameVacuumErrorCode.ONBOARD_WATER_TANK_EMPTY,
    DreameVacuumErrorCode.ONBOARD_DIRTY_WATER_TANK_FULL,
]


def PIID(property: DreameVacuumProperty, mapping=DreameVacuumPropertyMapping) -> int | None:
    if property in mapping:
        return mapping[property][piid]


def DIID(property: DreameVacuumProperty, mapping=DreameVacuumPropertyMapping) -> str | None:
    if property in mapping:
        return f"{mapping[property][siid]}.{mapping[property][piid]}"


def DID(siid, piid) -> DreameVacuumProperty | None:
    for prop in [prop for prop in DreameVacuumProperty]:
        mapping = DreameVacuumPropertyMapping.get(prop)
        if mapping is not None and siid == mapping["siid"] and piid == mapping["piid"]:
            return prop
    return None


class RobotType(IntEnum):
    LIDAR = 0
    VSLAM = 1
    MOPPING = 2
    SWEEPING_AND_MOPPING = 3


class PathType(str, Enum):
    LINE = "L"
    SWEEP = "S"
    SWEEP_AND_MOP = "W"
    MOP = "M"


class ObstacleType(IntEnum):
    UNKNOWN = 0
    BASE = 128
    SCALE = 129
    THREAD = 130
    WIRE = 131
    TOY = 132
    SHOES = 133
    SOCK = 134
    FECE = 135
    TRASH_CAN = 136
    FABRIC = 137
    POWER_STRIP = 138
    LIQUID_STAIN = 139
    OBSTACLE = 142
    PET = 158
    # ??? = 160
    # ??? = 166
    CLEANING_TOOLS = 163
    DETECTED_STAIN = 169
    BLOCKED_ROOM = 200
    EASY_TO_STUCK_FURNITURE = 201
    UNCLEANABLE_STAIN = 202
    LEG = 204
    LARGE_PARTICLES = 205
    DRIED_STAIN = 206
    FOOD_BOWL = 209
    PET_BED = 210
    CLEANED_STAIN = 214
    SKIPPED_UNCLEANABLE_STAIN = 215
    CLEANED_DRIED_STAIN = 216
    CLEANED_LARGE_PARTICLES = 217
    PEN = 228


class ObstacleIgnoreStatus(IntEnum):
    UNKNOWN = -1
    NOT_IGNORED = 0
    MANUALLY_IGNORED = 1
    AUTOMATICALLY_IGNORED = 2
    ERROR = 3
    HIDDEN = 4


class ObstaclePictureStatus(IntEnum):
    UNKNOWN = -1
    DISABLED = 0
    UPLOADING = 1
    UPLOADED = 2
    UPLOAD_FAILED = 3


class SegmentSkipReason(IntEnum):
    BLOCKED_BY_VIRTUAL_WALL = 2
    BLOCKED_BY_DOOR = 3
    BLOCKED_BY_THRESHOLD = 4
    BLOCKED_BY_OBSTACLE = 5
    BLOCKED_BY_CARPET = 6
    BLOCKED_BY_DETECTED_CARPET = 7
    BLOCKED_BY_HIDDEN_OBSTACLE = 8
    BLOCKED_BY_DYNAMIC_OBSTACLE = 9
    PASSAGE_TOO_LOW = 10
    STEP_TOO_LOW = 27
    FAILED_TO_CROSS_THRESHOLD = 33


class TaskInterruptReason(IntEnum):
    TASK_COMPLETED = 0
    ROBOT_LIFTED = 11
    ROBOT_FALLEN = 12
    CLIFF_SENSOR_ERROR = 13
    MOP_PAD_REMOVED = 14
    MOP_PAD_FALLEN_OFF = 15
    MOP_PAD_STUCK = 16
    MOP_PAD_FALLEN_OFF_BY_TABLE = 17
    MOP_PAD_FALLEN_OFF_BY_OBSTACLE = 18
    MOP_PAD_ABNORMALLY_REMOVED = 19
    MOP_PAD_FALLEN_OFF_CROSSING_OBSTACLE = 20
    BRUSH_ENTANGLED_BY_OBSTACLE = 21
    BRUSH_ENTANGLED_BY_CARPET = 22
    BRUSH_ENTANGLED_BY_OBJECT = 23
    LASER_DISTANCE_SENSOR_ERROR = 24
    ROBOT_IS_STUCK_ON_STEP = 25
    ROBOT_IS_STUCK_ON_OBSTACLE = 26
    BASE_STATION_POWERED_OFF = 27
    ABNORMAL_DOCKING = 101
    CANNOT_FIND_BASE_STATION = 102


class FurnitureType(IntEnum):
    SINGLE_BED = 1
    DOUBLE_BED = 2
    ARM_CHAIR = 3
    TWO_SEAT_SOFA = 4
    THREE_SEAT_SOFA = 5
    DINING_TABLE = 6
    NIGHTSTANT = 7
    COFFEE_TABLE = 8
    TOILET = 9
    LITTER_BOX = 10
    PET_BED = 11
    FOOD_BOWL = 12
    PET_TOILET = 13
    REFRIGERATOR = 14
    WASHING_MACHINE = 15
    ENCLOSED_LITTER_BOX = 16
    AIR_CONDITIONER = 17
    TV_CABINET = 18
    BOOKSHELF = 19
    SHOE_CABINET = 20
    WARDROBE = 21
    GREENERY = 22
    FLOOR_MIRROR = 23
    L_SHAPED_SOFA = 24
    ROUND_COFFEE_TABLE = 25
    TABLE = 26
    # ??? = 27
    # ??? = 28
    ARM_CHAIR_NARROW = 29
    THREE_SEAT_SOFA_NARROW = 30
    L_SHAPED_SOFA_RIGHT = 31


class CleansetType(IntEnum):
    NONE = 0
    DEFAULT = 1
    CLEANING_MODE = 2
    CUSTOM_MOPPING_ROUTE = 3
    CLEANING_ROUTE = 4
    WETNESS_LEVEL = 5
    WETNESS_LEVEL_MAX_15 = 6


class DeviceCapability(IntEnum):
    MOP_PAD_UNMOUNTING = 1
    DRAINAGE = 2
    MOPPING_AFTER_SWEEPING = 3
    MAX_SUCTION_POWER = 4
    OBSTACLE_IMAGE_CROP = 5
    UV_STERILIZATION = 6
    MOP_PAD_SWING = 7
    HOT_WASHING = 8
    AUTO_EMPTY_MODE = 9
    FLOOR_DIRECTION_CLEANING = 10
    LARGE_PARTICLES_BOOST = 11
    SEGMENT_VISIBILITY = 12
    MOP_PAD_SWING_PLUS = 13
    AUTO_REWASHING = 14
    MOP_PAD_LIFTING_PLUS = 15
    PET_FURNITURE = 16
    CLEANING_ROUTE = 17
    MOPPING_SETTINGS = 18
    SEGMENT_SLOW_CLEAN_ROUTE = 19
    TASK_TYPE = 21
    ULTRA_CLEAN_MODE = 22
    EXTENDED_FURNITURES = 23
    SELF_CLEAN_FREQUENCY = 24
    CLEANGENIUS = 25
    CLEANGENIUS_AUTO = 26
    FLUID_DETECTION = 27
    INTENSIVE_CARPET_CLEANING = 28
    CLEAN_CARPETS_FIRST = 29
    WETNESS_LEVEL = 30
    AUTO_RENAME_SEGMENT = 31
    DISABLE_SENSOR_CLEANING = 32
    FLOOR_MATERIAL = 33
    GEN5 = 34
    FURNITURES_V2 = 35
    SAVED_FURNITURES = 36
    OBSTACLES = 37
    WATER_CHECK = 38
    AUTO_CARPET_CLEANING = 39
    SEGMENT_MOPPING_SETTINGS = 40
    SEGMENT_MOPPING_TYPE = 41
    MOPPING_TYPE = 42
    MAX_SUCTION_POWER_EXTENDED = 43
    AUTO_RECLEANING = 44
    NEW_STATE = 45
    CAMERA_STREAMING = 46
    DETERGENT = 47
    CLEANGENIUS_MODE = 48
    SIDE_REACH = 49
    WATER_TEMPERATURE = 50
    WASHING_MODE = 51
    SMART_MOP_WASHING = 52
    DND_FUNCTIONS = 53
    RAMPS = 54
    VIRTUAL_TRACKS = 55
    DEODORIZER = 56
    WHEEL = 57
    SCALE_INHIBITOR = 58
    SILENT_DRYING = 59
    HAIR_COMPRESSION = 60
    SIDE_BRUSH_CARPET_ROTATE = 61
    AUTO_LDS_LIFTING = 62
    AREA_ROTATION = 63
    MOP_PAD_LIFTING = 64
    MOPPING_WITH_DETERGENT = 65
    CARPET_CROSSING = 66
    DYNAMIC_OBSTACLE_CLEANING = 67
    OBSTACLE_CROSSING = 68
    DOUBLE_DETERGENT = 69
    MOP_TEMPERATURE = 70
    DUST_BAG_DRYING = 71
    LOW_LYING_AREA_FREQUENCY = 72
    PRESSURIZED_CLEANING = 73
    SCRAPER_FREQUENCY = 74
    CARPET_MATERIAL = 75
    CARPET_TYPE = 76
    CARPET_CLEANSET_V2 = 77
    CARPET_CLEANSET_V3 = 78
    LOW_LYING_AREAS = 79
    LOW_LYING_AREA_DELETE = 80
    CARPET_SHAPE = 81
    CARPET_ID = 82
    AUTO_EMPTYING = 83
    WASHLESS_BASE = 84
    WATER_TANK_DRAINING = 85
    AUTO_ADD_DETERGENT = 86
    FILL_LIGHT = 87
    LOCAL_STORAGE = 88
    LASER_OBSTACLE = 89
    LIFT_CHASSIS_ON_CARPET = 90
    ROLLER_COVER = 91
    MOP_PRESSURE = 92
    FLOOR_MAINTAINING = 93
    INTELLIGENT_AUTO_EMPTY = 95
    AUTO_EMPTY_AREA = 96
    HOT_WATER_WASHING = 97
    PET_AI_MODEL = 98
    MECHANICAL_FOOT = 99
    WASHBOARD_CLEANING_STATUS = 100
    ACTIVE_SUSPENSION = 101
    DISABLE_MOP_CONSUMABLE = 102
    DETERGENT_STATUS = 103
    FLUFFING_ROLLER = 104
    ROLLER_MOP_FILTER = 105
    ROLLER_MOP = 106
    WATER_OUTLET_FILTER = 107
    SQUEEGEE = 108
    ONBOARD_DIRTY_WATER_TANK = 109
    CARPET_TASSEL = 110
    FLOOR_MATS = 111
    MANUAL_DUST_BAG_DRYING = 112
    INTELLIGENT_SELF_CLEAN_FREQUENCY = 113
    DUST_COLLECTION_DURING_DRYING = 114
    POWER_SAVING = 115
    AUTO_CHANGE_MOP = 116
    BATTERY_CHARGE_LEVEL = 117
    DEODORIZER_MODULE = 118
    MAP_V2 = 119
    QUICK_DRY = 120
    DRYING_TIME_V3 = 121
    DRYING_TIME_V2 = 122
    RESOURCES_AES_IV = 123
    CLEANING_SEQUENCE_V2 = 124
    CLEANING_ROUTE_V2 = 125
    LOWER_LDS_WHILE_DOCKING = 126
    CUSTOM_DRYING_TIME = 127
    DRYING_TIME_LIST = 128
    DIRTY_WATER_CHANNEL = 129
    DISABLE_SILENT_DRYING = 130
    SILENT_DRYING_TIME = 131
    SELF_CLEAN_TIME_MIN = 132
    SELF_CLEAN_TIME_MAX = 133
    SELF_CLEAN_TIME_DEFAULT = 134
    SELF_CLEAN_TIME_FIXED_DEFAULT = 135
    SELF_CLEAN_AREA_MIN = 136
    SELF_CLEAN_AREA_MAX = 137
    SELF_CLEAN_AREA_DEFAULT = 138
    SELF_CLEAN_AREA_FIXED_DEFAULT = 139
    SMALL_WATER_TANK = 140


class DreameVacuumDeviceCapability:
    def __init__(self, device) -> None:
        self.key = None
        self.list = None
        self.lidar_navigation = True
        self.multi_floor_map = True
        self.ai_detection = False
        self.self_wash_base = False
        self.auto_empty_base = False
        self.mop_pad_lifting = False
        self.mop_pad_lifting_plus = False
        self.customized_cleaning = False
        self.auto_switch_settings = False
        self.mop_pad_unmounting = False
        self.mopping_after_sweeping = False
        self.wifi_map = False
        self.backup_map = False
        self.dnd = False
        self.dnd_task = False
        self.shortcuts = False
        self.drainage = False
        self.carpet_recognition = False
        self.fill_light = False
        self.voice_assistant = False
        self.pet_detective = False
        self.hot_washing = False
        self.mop_pad_swing = False
        self.mop_pad_swing_plus = False
        self.smart_drying = False
        self.off_peak_charging = False
        self.max_suction_power = False
        self.obstacle_image_crop = False
        self.uv_sterilization = False
        self.self_clean_frequency = False
        self.auto_empty_mode = False
        self.object_shift = False
        self.robot_type = RobotType.LIDAR
        self.tight_mopping = False
        self.floor_material = False
        self.floor_direction_cleaning = False
        self.segment_visibility = False
        self.cleangenius = False
        self.cleangenius_auto = False
        self.large_particles_boost = False
        self.fluid_detection = False
        self.intensive_carpet_cleaning = False
        self.mopping_settings = False
        self.custom_mopping_route = False
        self.cleaning_route = False
        self.segment_slow_clean_route = True
        self.pet_furniture = False
        self.task_type = False
        self.water_tank_draining = False
        self.disable_sensor_cleaning = False
        self.auto_rename_segment = False
        self.ultra_clean_mode = False
        self.clean_carpets_first = False
        self.mop_clean_frequency = False
        self.saved_furnitures = False
        self.extended_furnitures = False
        self.furnitures_v2 = False
        self.wetness = False
        self.wetness_level = False
        self.obstacles = False
        self.water_check = False
        self.auto_carpet_cleaning = False
        self.segment_mopping_settings = False
        self.segment_mopping_type = False
        self.mopping_type = False
        self.mopping_mode = False
        self.auto_charging = False
        self.max_suction_power_extended = False
        self.auto_recleaning = False
        self.auto_rewashing = False
        self.new_state = False
        self.camera_streaming = False
        self.gen5 = False
        self.detergent = False
        self.embedded_tank = False
        self.cleangenius_mode = False
        self.side_reach = False
        self.water_temperature = False
        self.washing_mode = False
        self.smart_mop_washing = False
        self.dnd_functions = False
        self.ramps = False
        self.virtual_tracks = False
        self.wheel = False
        self.scale_inhibitor = False
        self.deodorizer = False
        self.silent_drying = False
        self.hair_compression = False
        self.side_brush_carpet_rotate = False
        self.lift_chassis_on_carpet = False
        self.auto_lds_lifting = False
        self.station_cleaning = False
        self.mijia = False
        self.area_rotation = False
        self.mopping_with_detergent = False
        self.carpet_crossing = False
        self.dynamic_obstacle_cleaning = False
        self.obstacle_crossing = False
        self.double_detergent = False
        self.mop_temperature = False
        self.dust_bag_drying = False
        self.low_lying_area_frequency = False
        self.pressurized_cleaning = False
        self.scraper_frequency = False
        self.auto_add_detergent = False
        self.local_storage = False
        self.laser_obstacle = False
        self.battery_charge_level = False
        self.carpet_material = False
        self.carpet_type = False
        self.carpet_cleanset_v2 = False
        self.carpet_cleanset_v3 = False
        self.low_lying_areas = False
        self.low_lying_area_delete = False
        self.carpet_shape = False
        self.carpet_id = False
        self.auto_emptying = False
        self.washless_base = False
        self.roller_cover = False
        self.mop_pressure = False
        self.floor_maintaining = False
        self.intelligent_auto_empty = False
        self.auto_empty_area = False
        self.hot_water_washing = False
        self.pet_ai_model = False
        self.mechanical_foot = False
        self.washboard_cleaning_status = False
        self.active_suspension = False
        self.disable_mop_consumable = False
        self.detergent_status = False
        self.fluffing_roller = False
        self.roller_mop_filter = False
        self.roller_mop = False
        self.water_outlet_filter = False
        self.squeegee = False
        self.onboard_dirty_water_tank = False
        self.carpet_tassel = False
        self.floor_mats = False
        self.manual_dust_bag_drying = False
        self.intelligent_self_clean_frequency = False
        self.dust_collection_during_drying = False
        self.power_saving = False
        self.auto_change_mop = False
        self.battery_charge_level = False
        self.deodorizer_module = False
        self.map_v2 = False
        self.quick_dry = False
        self.drying_time_v3 = False
        self.drying_time_v2 = False
        self.resources_aes_iv = "YWViZjhjNTJlMjZhNDc2Nw=="
        self.cleaning_sequence_v2 = False
        self.cleaning_route_v2 = False
        self.lower_lds_while_docking = False
        self.custom_drying_time = False
        self.drying_time_list = None
        self.disable_silent_drying = False
        self.silent_drying_time = 5
        self.self_clean_time_min = 10
        self.self_clean_time_max = 50
        self.self_clean_time_default = 25
        self.self_clean_time_fixed_default = 0
        self.self_clean_area_min = 10
        self.self_clean_area_max = 35
        self.self_clean_area_default = 20
        self.self_clean_area_fixed_default = 0
        self.small_water_tank = False
        self.furnitures_v3 = False
        self._custom_cleaning_mode = False
        self._capability = None
        self._device = device

    def load(self, device_info):
        model = self._device.info.model[(self._device.info.model.rfind(".") + 1) :]
        if model not in device_info[3]:
            raise Exception("Unsupported Device!")
        device = device_info[0][device_info[3][model]]
        if not device or not (len(device) == 3 or len(device) == 4) or device[2] < 0:
            raise Exception("Unsupported Device!")
        self._capability = device_info[1][device[2]]
        if self._capability is None:
            raise Exception("Device capability missing!")
        if len(device) == 4:
            if device[3] < 0 or device[3] >= len(device_info[1] or device[3] < 0):
                raise Exception("Device key missing!")
            self.key = device_info[2][device[3]]
            if not self.key or len(self.key) < 1:
                raise Exception("Device Key missing!")

        self.lidar_navigation = bool(self._device.get_property(DreameVacuumProperty.MAP_SAVING) is None)
        self.multi_floor_map = bool(
            self._device.get_property(DreameVacuumProperty.MULTI_FLOOR_MAP) is not None and self.lidar_navigation
        )
        self.ai_detection = bool(self._device.get_property(DreameVacuumProperty.AI_DETECTION) is not None)
        self.self_wash_base = bool(self._device.get_property(DreameVacuumProperty.SELF_WASH_BASE_STATUS) is not None)
        self.auto_empty_base = bool(self._device.get_property(DreameVacuumProperty.DUST_COLLECTION) is not None)
        self.customized_cleaning = bool(
            self._device.get_property(DreameVacuumProperty.CUSTOMIZED_CLEANING) is not None
        )
        self.tight_mopping = bool(self._device.get_property(DreameVacuumProperty.TIGHT_MOPPING) is not None)
        self.auto_switch_settings = bool(
            self._device.get_property(DreameVacuumProperty.AUTO_SWITCH_SETTINGS) is not None
        )
        self.carpet_recognition = bool(
            self._device.get_property(DreameVacuumProperty.CARPET_RECOGNITION) is not None
            or self._device.get_property(DreameVacuumProperty.CARPET_CLEANING) is not None
        )
        self.wifi_map = bool(self._device.get_property(DreameVacuumProperty.WIFI_MAP) is not None)
        self.backup_map = bool(self._device.get_property(DreameVacuumProperty.MAP_BACKUP_STATUS) is not None)
        self.dnd_task = bool(self._device.get_property(DreameVacuumProperty.DND_TASK) is not None)
        self.dnd = bool(self.dnd_task or self._device.get_property(DreameVacuumProperty.DND) is not None)
        self.shortcuts = bool(self._device.get_property(DreameVacuumProperty.SHORTCUTS) is not None)
        self.off_peak_charging = bool(self._device.get_property(DreameVacuumProperty.OFF_PEAK_CHARGING) is not None)
        self.voice_assistant = bool(self._device.get_property(DreameVacuumProperty.VOICE_ASSISTANT) is not None)

        if self._capability:
            version = self._device.info.version if self._device.info.version else 1
            for v in self._capability:
                capability = v[0]
                if capability in DeviceCapability._value2member_map_:
                    capability = DeviceCapability(capability)
                    param = capability.name.lower()
                    if param and hasattr(self, param):
                        setattr(
                            self,
                            param,
                            (
                                bool(version >= v[1])
                                if not isinstance(v[1], str)
                                else int(v[1]) if v[1].isnumeric() else v[1]
                            ),
                        )

        if not self.gen5 and (
            "mova.vacuum." in self._device.info.model or "trouver.vacuum." in self._device.info.model
        ):
            self.gen5 = True

        if self.gen5:
            if self.self_wash_base and self.washless_base:
                self.self_wash_base = False
            if self.auto_empty_base and (
                not self.auto_emptying
                or self._device.get_property(DreameVacuumProperty.DUST_COLLECTION)
                == DreameVacuumDustCollection.NEVER.value
            ):
                self.auto_empty_base = False

        self.detergent = bool(
            self.self_wash_base
            and (self.detergent or self._device.get_property(DreameVacuumProperty.DETERGENT_LEFT) != None)
        )

        if not self.self_wash_base:
            self.cleangenius = False
            self.station_cleaning = False
            self.washing_mode = False
            self.scale_inhibitor = False
            self.deodorizer = False
            self.detergent = False
            self.drainage = False
            self.water_tank_draining = False

        self.mop_pad_swing = bool(self.mop_pad_swing or self.mop_pad_swing_plus)
        self.mop_pad_unmounting = bool(
            self.self_wash_base
            and self.mop_pad_unmounting
            and self._device.get_property(DreameVacuumProperty.AUTO_MOUNT_MOP) is not None
        )
        self.drainage = bool(
            self.drainage and self._device.get_property(DreameVacuumProperty.DRAINAGE_STATUS) is not None
        )
        self.pet_detective = bool(
            self.pet_detective and self._device.get_property(DreameVacuumProperty.PET_DETECTIVE) is not None
        )
        self.mopping_settings = self.mopping_settings or self.mopping_type
        self.segment_mopping_settings = self.segment_mopping_settings or self.segment_mopping_type
        self.task_type = bool(self.task_type and self._device.get_property(DreameVacuumProperty.TASK_TYPE) is not None)
        self.wetness = bool(
            self.wetness_level
            or (self.mopping_settings and self._device.get_property(DreameVacuumProperty.WETNESS_LEVEL))
        )
        if not self.cleaning_route:
            self.segment_slow_clean_route = False
        self.custom_mopping_route = self.mopping_settings and not self.cleaning_route
        self.disable_sensor_cleaning = (
            self.disable_sensor_cleaning
            or not self.lidar_navigation
            or self._device.get_property(DreameVacuumProperty.SENSOR_DIRTY_LEFT) is None
            or (
                not self.camera_streaming
                and self._device.get_property(DreameVacuumProperty.OBSTACLE_AVOIDANCE) is None
            )
        )
        self.mop_pad_lifting = bool(
            self.mop_pad_lifting
            or self.mop_pad_lifting_plus
            or self.mop_pad_unmounting
            or (self.self_wash_base and self.auto_empty_base)
        )

        if self.drying_time_v3:
            self.drying_time_v2 = True
            self.silent_drying = False

        if self.drying_time_v2:
            self.custom_drying_time = True

        if self.disable_silent_drying:
            self.silent_drying = False

        self.object_shift = bool(self.lidar_navigation and "p20" in self._device.info.model)
        self.floor_material = bool(self.mop_pad_lifting and self.carpet_recognition and not self.mop_clean_frequency)
        self.robot_type = (
            RobotType.SWEEPING_AND_MOPPING
            if self.self_wash_base and self.mop_pad_lifting
            else (
                RobotType.MOPPING
                if self.self_wash_base
                else RobotType.LIDAR if self.lidar_navigation else RobotType.VSLAM
            )
        )
        if "xiaomi.vacuum." in self._device.info.model:
            self.mijia = True
            self.wifi_map = False
            self.mop_clean_frequency = True
            self.self_clean_frequency = False
            self.floor_material = "d110" in self._device.info.model
            self.off_peak_charging = False
            self.camera_streaming = False
            self.furnitures_v2 = False
            self.fill_light = False
            self.station_cleaning = self.self_wash_base
        else:
            self.station_cleaning = bool(self.self_wash_base and self.gen5)
            if (
                self.extended_furnitures
                and "mova.vacuum." not in self._device.info.model
                and "trouver.vacuum." not in self._device.info.model
                and (
                    self.roller_mop
                    or self.roller_mop_filter
                    or self.mop_pressure
                    or self.mop_temperature
                    or self.carpet_tassel
                    or self.auto_change_mop
                    or self.intelligent_auto_empty
                    or self.auto_empty_area
                    or self.pet_ai_model
                    or self.low_lying_area_frequency
                    or self.dust_bag_drying
                )
            ):
                self.furnitures_v3 = True

        self.list = [
            key
            for key, value in self.__dict__.items()
            if not callable(value) and not key.startswith("_") and value == True
        ]
        if self.custom_cleaning_mode:
            self.list.append("custom_cleaning_mode")
        if self.cruising:
            self.list.append("cruising")
        if self.map:
            self.list.append("map")

    @property
    def map(self) -> bool:
        """Returns true when mapping feature is available."""
        return bool(self._device._map_manager is not None)

    @property
    def custom_cleaning_mode(self) -> bool:
        """Returns true if customized cleaning mode can be set to segments."""
        if self.auto_switch_settings and self.mop_pad_lifting:
            return True
        segments = self._device.status.current_segments
        if not self._custom_cleaning_mode:
            if segments:
                if next(iter(segments.values())).cleaning_mode is not None:
                    self._custom_cleaning_mode = True
                    return True
            else:
                self._custom_cleaning_mode = self.mop_pad_lifting
                return self.mop_pad_lifting
        return self._custom_cleaning_mode and (not segments or next(iter(segments.values())).cleaning_mode is not None)

    @property
    def cruising(self) -> bool:
        if not self.lidar_navigation or not self.camera_streaming:
            return False
        return bool(
            (self._device.status.current_map and self._device.status.current_map.predefined_points is not None)
            or self._device.get_property(DreameVacuumProperty.CRUISE_SCHEDULE) is not None
            or self._device.status.fill_light is not None
        )

    def mop_extend(self) -> bool:
        return (
            self.auto_switch_settings
            and self.mop_pad_swing
            and self._device.mop_extend_frequency is not None
            and self._device.mop_extend_frequency.value >= 0
        )


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
        return other is not None and self.x == other.x and self.y == other.y and self.a == other.a

    def as_dict(self) -> Dict[str, Any]:
        if self.a is None:
            return {ATTR_X: self.x, ATTR_Y: self.y}
        return {ATTR_X: self.x, ATTR_Y: self.y, ATTR_A: self.a}

    def to_img(self, image_dimensions, original=False) -> Point:
        return image_dimensions.to_img(self, original)

    def to_coord(self, image_dimensions) -> Point:
        return image_dimensions.to_coord(self)

    def rotated(self, image_dimensions, degree) -> Point:
        w = int(
            (image_dimensions.width * image_dimensions.scale)
            + image_dimensions.padding[0]
            + image_dimensions.padding[2]
            - image_dimensions.crop[0]
            - image_dimensions.crop[2]
        )
        h = int(
            (image_dimensions.height * image_dimensions.scale)
            + image_dimensions.padding[1]
            + image_dimensions.padding[3]
            - image_dimensions.crop[1]
            - image_dimensions.crop[3]
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
    def __init__(self, x: float, y: float, path_type: PathType) -> None:
        super().__init__(x, y)
        self.path_type = path_type

    def as_dict(self) -> Dict[str, Any]:
        attributes = {**super().as_dict()}
        if self.path_type:
            attributes[ATTR_TYPE] = self.path_type.value
        return attributes


class Obstacle(Point):
    def __init__(
        self,
        x: float,
        y: float,
        type: int,
        possibility: int,
        object_id: str = None,
        file_name: str = None,
        key: int = None,
        pos_x: float = None,
        pos_y: float = None,
        width: float = None,
        height: float = None,
        picture_status: int = 0,
        ignore_status: int = None,
    ) -> None:
        super().__init__(x, y)
        self.type = ObstacleType(type) if type in ObstacleType._value2member_map_ else ObstacleType.UNKNOWN
        self.possibility = possibility
        self.object_id = object_id
        self.key = key
        self.file_name = file_name
        self.object_name = file_name
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.height = height
        self.width = width
        self.picture_status = (
            ObstaclePictureStatus(picture_status)
            if picture_status in ObstaclePictureStatus._value2member_map_
            else ObstaclePictureStatus.UNKNOWN
        )
        if self.type == ObstacleType.BLOCKED_ROOM:
            self.ignore_status = ObstacleIgnoreStatus.NOT_IGNORED
        else:
            self.ignore_status = (
                ObstacleIgnoreStatus(ignore_status)
                if ignore_status in ObstacleIgnoreStatus._value2member_map_
                else ObstacleIgnoreStatus.UNKNOWN
            )
        self.id = self.object_id if self.object_id else f"0{int(self.x)}0{int(self.y)}"

        if self.type == ObstacleType.BLOCKED_ROOM:
            self.segment_id = int(self.x)
            self.x = 0
            self.y = 0
            self.possibility = None
        else:
            self.segment_id = None

        if file_name and "/" in file_name:
            self.object_name = file_name.split("/")[-1]
            if "-" in self.object_name:
                self.object_name = self.object_name.split("-")[0]

            if self.object_id:
                self.object_name = f"{self.id}-{self.object_name}"
            else:
                self.id = self.object_name

        self.segment = None
        self.color_index = None
        self.reason = None

    def as_dict(self) -> Dict[str, Any]:
        attributes = super().as_dict()
        attributes[ATTR_TYPE] = self.type.name.replace("_", " ").title()
        if self.possibility is not None:
            attributes[ATTR_POSSIBILTY] = self.possibility
        if self.picture_status is not None:
            attributes[ATTR_PICTURE_STATUS] = self.picture_status.name.replace("_", " ").title()
        if self.ignore_status is not None:
            attributes[ATTR_IGNORE_STATUS] = self.ignore_status.name.replace("_", " ").title()
        if self.segment is not None:
            attributes[ATTR_ROOM] = self.segment
        if self.reason is not None:
            attributes[ATTR_REASON] = self.reason.name.replace("_", " ").capitalize()
        return attributes

    def __eq__(self: Obstacle, other: Obstacle) -> bool:
        return not (
            other is None
            or self.x != other.x
            or self.y != other.y
            or self.possibility != other.possibility
            or self.type != other.type
            or self.object_id != other.object_id
            or self.key != other.key
            or self.file_name != other.file_name
            or self.pos_x != other.pos_x
            or self.pos_y != other.pos_y
            or self.height != other.height
            or self.width != other.width
            or self.picture_status != other.picture_status
            or self.ignore_status != other.ignore_status
        )


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
        return Area(self.x0, self.y0, self.x0, self.y1, self.x1, self.y1, self.x1, self.y0)

    def to_img(self, image_dimensions, original=False) -> Zone:
        p0 = Point(self.x0, self.y0).to_img(image_dimensions, original)
        p1 = Point(self.x1, self.y1).to_img(image_dimensions, original)
        return Zone(p0.x, p0.y, p1.x, p1.y)

    def to_coord(self, image_dimensions) -> Zone:
        p0 = Point(self.x0, self.y0).to_coord(image_dimensions)
        p1 = Point(self.x1, self.y1).to_coord(image_dimensions)
        return Zone(p0.x, p0.y, p1.x, p1.y)

    def check_point(self, x, y, size) -> bool:
        return self.as_area().check_point(x, y, size)


class Segment(Zone):
    def __init__(
        self,
        id: int,
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
        cleaning_mode: int = None,
        mopping_settings: int = None,
        order: int = None,
    ) -> None:
        super().__init__(x0, y0, x1, y1)
        self.coords = [x0, y0, x1, y1]
        self.id = id
        self.unique_id = None
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
        self.cleaning_mode = cleaning_mode
        self.mopping_settings = mopping_settings
        self.wetness_level = None
        self.cleaning_route = None
        self.custom_mopping_route = None
        self.color_index = 0
        self.floor_material = None
        self.floor_material_direction = None
        self.floor_material_rotated_direction = None
        self.visibility = None
        self.mop_temperature = None
        self.mop_pressure = None
        self.mop_type = None
        self.cleanset_type = CleansetType.NONE
        self.carpet_cleaning = None
        self.carpet_preferences = None
        self.set_name()

    @property
    def mop_pad_humidity(self) -> int:
        return self.water_volume

    @property
    def outline(self) -> List[List[int]]:
        return [
            [self.x0, self.y0],
            [self.x0, self.y1],
            [self.x1, self.y1],
            [self.x1, self.y0],
        ]

    @property
    def center(self) -> List[int]:
        return [self.x, self.y]

    @property
    def letter(self) -> str:
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return f"{letters[((self.id % 26) - 1)]}{math.floor(self.id / 26)}" if self.id > 26 else letters[self.id - 1]

    def calculate_coords(self, dimensions) -> None:
        grid_size = dimensions.grid_size
        top = dimensions.top
        left = dimensions.left

        self.x0 = math.floor(left + (self.coords[0] * grid_size))
        self.y0 = math.floor(top + (self.coords[1] * grid_size))
        self.x1 = math.floor(left + (self.coords[2] * grid_size) + grid_size)
        self.y1 = math.floor(top + (self.coords[3] * grid_size) + grid_size)

    def set_name(self) -> None:
        if self.type != 0 and SEGMENT_TYPE_CODE_TO_NAME.get(self.type):
            self.name = SEGMENT_TYPE_CODE_TO_NAME[self.type]
            if self.index > 0:
                self.name = f"{self.name} {self.index + 1}"
        elif self.custom_name is not None:
            self.name = self.custom_name
        else:
            self.name = f"Room {self.id}"
        self.icon = SEGMENT_TYPE_CODE_TO_HA_ICON.get(self.type, "mdi:home-outline")

    def set_custom_carpet_settings(self, carpet_cleaning, carpet_preferences=None):
        self.carpet_cleaning = carpet_cleaning
        self.carpet_preferences = carpet_preferences

    def next_type_index(self, type, segments) -> int:
        index = 0
        if type > 0:
            for segment_id in sorted(segments, key=lambda segment_id: segments[segment_id].index):
                if segment_id != self.id and segments[segment_id].type == type and segments[segment_id].index == index:
                    index = index + 1
        return index

    def name_list(self, segments) -> dict[int, str]:
        list = {}
        for k, v in SEGMENT_TYPE_CODE_TO_NAME.items():
            index = self.next_type_index(k, segments)
            name = f"{v}"
            if index > 0:
                name = f"{name} {index + 1}"

            list[k] = name

        name = f"Room {self.id}"
        if self.type == 0:
            name = f"{self.name}"
        list[0] = name
        if self.type != 0:  # and self.index > 0:
            list[self.type] = self.name

        return {v: k for k, v in list.items()}

    def as_dict(self) -> Dict[str, Any]:
        attributes = {**super(Segment, self).as_dict()}
        if self.id:
            attributes[ATTR_ROOM_ID] = self.id
        if self.name is not None:
            attributes[ATTR_NAME] = self.name
        if self.custom_name is not None:
            attributes[ATTR_CUSTOM_NAME] = self.custom_name
        if self.order is not None:
            attributes[ATTR_ORDER] = self.order
        if self.cleaning_times is not None:
            attributes[ATTR_CLEANING_TIMES] = self.cleaning_times
        if self.suction_level is not None:
            attributes[ATTR_SUCTION_LEVEL] = self.suction_level
        if self.water_volume is not None:
            attributes[ATTR_WATER_VOLUME] = self.water_volume
        if self.wetness_level is not None and (
            self.cleanset_type == CleansetType.WETNESS_LEVEL or self.cleanset_type == CleansetType.WETNESS_LEVEL_MAX_15
        ):
            attributes[ATTR_WETNESS_LEVEL] = self.wetness_level
        if self.cleaning_mode is not None and self.cleanset_type != CleansetType.DEFAULT:
            attributes[ATTR_CLEANING_MODE] = self.cleaning_mode
        if self.custom_mopping_route is not None and self.cleanset_type == CleansetType.CUSTOM_MOPPING_ROUTE:
            attributes[ATTR_CUSTOM_MOPPING_ROUTE] = self.custom_mopping_route
        if self.cleaning_route is not None and self.cleanset_type != CleansetType.CUSTOM_MOPPING_ROUTE:
            attributes[ATTR_CLEANING_ROUTE] = self.cleaning_route
        if self.type is not None:
            attributes[ATTR_TYPE] = self.type
        if self.index is not None:
            attributes[ATTR_INDEX] = self.index
        if self.icon is not None:
            attributes[ATTR_ICON] = self.icon
        if self.color_index is not None:
            attributes[ATTR_COLOR_INDEX] = self.color_index
        if self.unique_id is not None:
            attributes[ATTR_UNIQUE_ID] = self.unique_id
        if self.floor_material is not None:
            attributes[ATTR_FLOOR_MATERIAL] = DreameVacuumFloorMaterial(self.floor_material).name.title()
        if self.floor_material_rotated_direction is not None:
            attributes[ATTR_FLOOR_MATERIAL_DIRECTION] = DreameVacuumFloorMaterialDirection(
                self.floor_material_rotated_direction
            ).name.title()
        if self.visibility is not None:
            attributes[ATTR_VISIBILITY] = DreameVacuumSegmentVisibility(int(self.visibility)).name.title()
        if self.mop_temperature is not None:
            attributes[ATTR_MOP_TEMPERATURE] = DreameVacuumMopTemperature(int(self.mop_temperature)).name.title()
        if self.mop_pressure is not None:
            attributes[ATTR_MOP_PRESSURE] = DreameVacuumMopPressure(int(self.mop_pressure)).name.title()
        if self.mop_type is not None:
            attributes[ATTR_MOP_TYPE] = self.mop_type

        if self.x is not None and self.y is not None:
            attributes[ATTR_X] = self.x
            attributes[ATTR_Y] = self.y

        return attributes

    def __eq__(self: Segment, other: Segment) -> bool:
        return not (
            other is None
            or self.x0 != other.x0
            or self.y0 != other.y0
            or self.x1 != other.x1
            or self.y1 != other.y1
            or self.x != other.x
            or self.y != other.y
            or self.name != other.name
            or self.index != other.index
            or self.type != other.type
            or self.color_index != other.color_index
            or self.icon != other.icon
            or self.neighbors != other.neighbors
            or self.order != other.order
            or self.cleaning_times != other.cleaning_times
            or self.suction_level != other.suction_level
            or self.water_volume != other.water_volume
            or self.wetness_level != other.wetness_level
            or self.cleaning_mode != other.cleaning_mode
            or self.floor_material != other.floor_material
            or self.floor_material_direction != other.floor_material_direction
            or self.floor_material_rotated_direction != other.floor_material_rotated_direction
            or self.mopping_settings != other.mopping_settings
            or self.visibility != other.visibility
            or self.carpet_cleaning != other.carpet_cleaning
            or self.carpet_preferences != other.carpet_preferences
            or self.mop_type != other.mop_type
            or self.mop_temperature != other.mop_temperature
            or self.mop_pressure != other.mop_pressure
        )

    def __str__(self) -> str:
        return f"{{room_id: {self.id}, outline: {self.outline}}}"

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

    def to_img(self, image_dimensions, original=False) -> Wall:
        p0 = Point(self.x0, self.y0).to_img(image_dimensions, original)
        p1 = Point(self.x1, self.y1).to_img(image_dimensions, original)
        return Wall(p0.x, p0.y, p1.x, p1.y)

    def to_coord(self, image_dimensions) -> Wall:
        p0 = Point(self.x0, self.y0).to_coord(image_dimensions)
        p1 = Point(self.x1, self.y1).to_coord(image_dimensions)
        return Wall(p0.x, p0.y, p1.x, p1.y)

    def as_list(self) -> List[float]:
        return [self.x0, self.y0, self.x1, self.y1]


class Area:
    def __init__(
        self, x0: float, y0: float, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, angle: int = None
    ) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3
        self.angle = angle
        self.hidden = False

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
            and self.angle == other.angle
            and self.hidden == other.hidden
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
            ATTR_ANGLE: self.angle,
        }

    def as_list(self) -> List[float]:
        return [self.x0, self.y0, self.x1, self.y1, self.x2, self.y2, self.x3, self.y3]

    def to_img(self, image_dimensions, original=False) -> Area:
        if self.angle:
            theta = -self.angle * math.pi / 180
            cosang = math.cos(theta)
            sinang = math.sin(theta)
            cx = (self.x0 + self.x1 + self.x2 + self.x3) / 4
            cy = (self.y0 + self.y1 + self.y2 + self.y3) / 4

            coords = self.as_list()
            for i in range(0, 8, 2):
                tx = coords[i] - cx
                ty = coords[i + 1] - cy
                coords[i] = (tx * cosang + ty * sinang) + cx
                coords[i + 1] = (-tx * sinang + ty * cosang) + cy

            p0 = Point(coords[0], coords[1]).to_img(image_dimensions, original)
            p1 = Point(coords[2], coords[3]).to_img(image_dimensions, original)
            p2 = Point(coords[4], coords[5]).to_img(image_dimensions, original)
            p3 = Point(coords[6], coords[7]).to_img(image_dimensions, original)
        else:
            p0 = Point(self.x0, self.y0).to_img(image_dimensions, original)
            p1 = Point(self.x1, self.y1).to_img(image_dimensions, original)
            p2 = Point(self.x2, self.y2).to_img(image_dimensions, original)
            p3 = Point(self.x3, self.y3).to_img(image_dimensions, original)
        return Area(p0.x, p0.y, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)

    def to_coord(self, image_dimensions) -> Area:
        p0 = Point(self.x0, self.y0).to_coord(image_dimensions)
        p1 = Point(self.x1, self.y1).to_coord(image_dimensions)
        p2 = Point(self.x2, self.y2).to_coord(image_dimensions)
        p3 = Point(self.x3, self.y3).to_coord(image_dimensions)
        return Area(p0.x, p0.y, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)

    def check_size(self, size) -> bool:
        return self.x2 - self.x0 == size and self.y2 - self.y1 == size

    def check_point(self, x, y, size) -> bool:
        x_coords = [self.x0, self.x1, self.x2, self.x3]
        y_coords = [self.y0, self.y1, self.y2, self.y3]

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        return x >= min_x - size and x <= max_x + size and y >= min_y - size and y <= max_y + size


class Furniture(Point):
    def __init__(
        self,
        x: float,
        y: float,
        x0: float,
        y0: float,
        width: float,
        height: float,
        type: FurnitureType,
        edit_type: int,
        angle: float = 0,
        scale: float = 1.0,
        furniture_id: int = None,
        segment_id: int = None,
        modified: bool = False,
    ) -> None:
        super().__init__(x, y)
        self.x0 = x0
        self.y0 = y0
        self.width = width
        self.height = height
        self.type = type
        self.edit_type = edit_type
        self.angle = angle
        self.scale = scale
        self.furniture_id = furniture_id
        self.segment_id = segment_id
        self.modified = modified

    def as_dict(self) -> Dict[str, Any]:
        attributes = super().as_dict()
        attributes[ATTR_TYPE] = self.type.name.replace("_", " ").title()
        if self.x0 is not None and self.y0 is not None:
            attributes[ATTR_X0] = self.x0
            attributes[ATTR_Y0] = self.y0
        if self.width and self.height:
            attributes[ATTR_WIDTH] = self.width
            attributes[ATTR_HEIGHT] = self.height
        if self.segment_id:
            attributes[ATTR_ROOM_ID] = self.segment_id
        if self.furniture_id is not None:
            attributes[ATTR_FURNITURE_ID] = self.furniture_id
        attributes[ATTR_ANGLE] = self.angle
        attributes[ATTR_SCALE] = self.scale
        return attributes

    def __eq__(self: Furniture, other: Furniture) -> bool:
        return not (
            other is None
            or self.x != other.x
            or self.y != other.y
            or self.x0 != other.x0
            or self.y0 != other.y0
            or self.width != other.width
            or self.height != other.height
            or self.type != other.type
            or self.edit_type != other.edit_type
            or self.furniture_id != other.furniture_id
            or self.segment_id != other.segment_id
            or self.angle != other.angle
            or self.scale != other.scale
        )


class Coordinate(Point):
    def __init__(self, x: float, y: float, completed: bool, type: int) -> None:
        super().__init__(x, y)
        self.type = type
        self.completed = completed

    def as_dict(self) -> Dict[str, Any]:
        attributes = {**super().as_dict()}
        if self.type is not None:
            attributes[ATTR_TYPE] = self.type
        if self.completed is not None:
            attributes[ATTR_COMPLETED] = self.completed
        return attributes

    def __eq__(self: Coordinate, other: Coordinate) -> bool:
        return not (
            other is None
            or self.x != other.x
            or self.y != other.y
            or self.type != other.type
            or self.completed != other.completed
        )


class Carpet(Area):
    def __init__(
        self,
        id: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
        ellipse: bool = None,
        carpet_type: int = None,
        ignored_areas: List[int] = None,
        segments: List[int] = None,
        polygon: List[float] = None,
        hidden: bool = None,
        tassel: List[int] = None,
    ) -> None:
        super().__init__(x0, y0, x1, y1, x2, y2, x3, y3)
        self.id = id
        self.segments = segments
        self.ignored_areas = ignored_areas
        self.ellipse = ellipse
        self.polygon = polygon
        self.carpet_cleaning = None
        self.carpet_preferences = None
        self.carpet_type = carpet_type
        self.tassel = tassel
        if ellipse is not None:
            ## Detected carpets returns string but added and ignored carpets are using int
            self.ellipse = ellipse == "1" or ellipse == 1
        if hidden is not None:
            self.hidden = hidden == "1" or hidden == 1

    def set_custom_carpet_settings(self, carpet_cleaning, carpet_preferences=None):
        self.carpet_cleaning = carpet_cleaning
        self.carpet_preferences = carpet_preferences

    def __eq__(self: Carpet, other: Carpet) -> bool:
        return not (
            other is None
            or self.x0 != other.x0
            or self.y0 != other.y0
            or self.x2 != other.x2
            or self.y2 != other.y2
            or self.id != other.id
            or self.ellipse != other.ellipse
            or self.carpet_cleaning != other.carpet_cleaning
            or self.carpet_preferences != other.carpet_preferences
            or self.carpet_type != other.carpet_type
            or self.segments != other.segments
            or self.ignored_areas != other.ignored_areas
            or self.polygon != other.polygon
            or self.hidden != other.hidden
            or self.tassel != other.tassel
        )


class Polygon(Area):
    def __init__(
        self,
        id: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
        polygon: List[float],
        type: int = None,
        hidden: int = None,
        ms: int = None,
        area: int = None,
    ) -> None:
        super().__init__(x0, y0, x1, y1, x2, y2, x3, y3)
        self.id = id
        self.polygon = polygon
        self.type = type  # 0 = Automatically Detected, 1 = Manually Added
        self.hidden = hidden  # 1 = Automatically Hidden, 2 = Manually Hidden
        self.ms = ms
        self.area = area

    def __eq__(self: Polygon, other: Polygon) -> bool:
        return not (
            other is None
            or self.x0 != other.x0
            or self.y0 != other.y0
            or self.x2 != other.x2
            or self.y2 != other.y2
            or self.id != other.id
            or self.polygon != other.polygon
            or self.type != other.type
            or self.hidden != other.hidden
            or self.ms != other.ms
            or self.area != other.area
        )


class MapImageDimensions:
    def __init__(self, top: int, left: int, height: int, width: int, grid_size: int) -> None:
        self.top = top
        self.left = left
        self.original_top = top
        self.original_left = left
        self.height = height
        self.width = width
        self.grid_size = grid_size
        self.offset = int(self.grid_size / 2)
        self.scale = 1
        self.padding = [0, 0, 0, 0]
        self.crop = [0, 0, 0, 0]
        self.bounds = None

    def to_img(self, point: Point, original: bool = False) -> Point:
        if original:
            left = self.original_left - self.offset
            top = self.original_top - self.offset
        else:
            left = self.left
            top = self.top

        return Point(
            ((point.x - left) / self.grid_size) * self.scale + self.padding[0] - self.crop[0],
            ((((self.height) * self.grid_size - 1) - (point.y - top)) / self.grid_size) * self.scale
            + self.padding[1]
            - self.crop[1],
        )

    def to_coord(self, point: Point) -> Point:
        return Point(
            ((point.x - self.left) / self.grid_size),
            ((((self.height) * self.grid_size - 1) - (point.y - self.top)) / self.grid_size),
        )

    def __eq__(self: MapImageDimensions, other: MapImageDimensions) -> bool:
        return (
            other is not None
            and self.top == other.top
            and self.left == other.left
            and self.original_top == other.original_top
            and self.original_left == other.original_left
            and self.height == other.height
            and self.width == other.width
            and self.grid_size == other.grid_size
        )


class CleaningHistory:
    def __init__(self, history_data, property_mapping) -> None:
        self.date: datetime = None
        self.status: DreameVacuumStatus = None
        self.cleaning_time: int = 0
        self.cleaned_area: int = 0
        self.suction_level: DreameVacuumSuctionLevel = None
        self.file_name: str = None
        self.key = None
        self.object_name = None
        self.completed: bool = None
        self.cleaning_status: CleaningStatus = None
        self.water_tank_or_mop: DreameVacuumWaterTank = None
        self.map_index: int = None
        self.map_name: str = None
        self.cruise_type: int = None
        self.cleanup_method: CleanupMethod = None
        self.second_cleaning: int = None
        self.second_mopping: int = None
        self.mopping_mode: int = None
        self.multiple_cleaning_time: str = None
        self.pet: int = None
        self.task_interrupt_reason: TaskInterruptReason = None
        self.blocked_segments: Dict[int, list] = None
        self.clean_again: int = None
        self.mop_after_sweep: int = None
        self.customized_cleaning: bool = False

        for history_data_item in history_data:
            pid = history_data_item[piid]
            value = history_data_item["value"] if "value" in history_data_item else history_data_item["val"]

            if pid == PIID(DreameVacuumProperty.STATUS, property_mapping):
                if value in DreameVacuumStatus._value2member_map_:
                    self.status = DreameVacuumStatus(value)
                else:
                    self.status = DreameVacuumStatus.UNKNOWN
            elif pid == PIID(DreameVacuumProperty.CLEANING_TIME, property_mapping):
                self.cleaning_time = value
            elif pid == PIID(DreameVacuumProperty.CLEANED_AREA, property_mapping):
                self.cleaned_area = value
            elif pid == PIID(DreameVacuumProperty.SUCTION_LEVEL, property_mapping):
                if value in DreameVacuumSuctionLevel._value2member_map_:
                    self.suction_level = DreameVacuumSuctionLevel(value)
                else:
                    self.suction_level = DreameVacuumSuctionLevel.UNKNOWN
            elif pid == PIID(DreameVacuumProperty.CLEANING_START_TIME, property_mapping):
                self.date = datetime.fromtimestamp(value)
            elif pid == PIID(DreameVacuumProperty.CLEAN_LOG_FILE_NAME, property_mapping):
                self.file_name = value
                if len(self.file_name) > 1:
                    if "," in self.file_name:
                        values = self.file_name.split(",")
                        self.object_name = values[0]
                        self.key = values[1]
                    else:
                        self.object_name = self.file_name
            elif pid == PIID(DreameVacuumProperty.CLEAN_LOG_STATUS, property_mapping):
                self.completed = bool(value == 1 or value == True)
                self.cleaning_status = CleaningStatus(value) if value in CleaningStatus._value2member_map_ else None
            elif pid == PIID(DreameVacuumProperty.WATER_TANK, property_mapping):
                if value in DreameVacuumWaterTank._value2member_map_:
                    self.water_tank_or_mop = DreameVacuumWaterTank(value)
                else:
                    self.water_tank_or_mop = DreameVacuumWaterTank.UNKNOWN
            elif pid == PIID(DreameVacuumProperty.MAP_INDEX, property_mapping):
                self.map_index = value
            elif pid == PIID(DreameVacuumProperty.MAP_NAME, property_mapping):
                self.map_name = value
            elif pid == PIID(DreameVacuumProperty.CRUISE_TYPE, property_mapping):
                self.cruise_type = value
            elif pid == PIID(DreameVacuumProperty.CLEANING_PROPERTIES, property_mapping):
                props = json.loads(value)
                if "cmc" in props:
                    value = props["cmc"]
                    self.cleanup_method = (
                        CleanupMethod(value) if value in CleanupMethod._value2member_map_ else CleanupMethod.OTHER
                    )
                if "clt" in props:
                    self.mop_after_sweep = props.get("clt")
                if "abnormal_end" in props:
                    values = json.loads(props["abnormal_end"])
                    self.task_interrupt_reason = (
                        TaskInterruptReason(values[0]) if values[0] in TaskInterruptReason._value2member_map_ else None
                    )
                self.customized_cleaning = bool(props.get("customeClean", 0) == 1)
                self.second_cleaning = props.get("ismultiple")
                self.second_mopping = props.get("ctyo")
                self.mopping_mode = props.get("mooClean")
                self.multiple_cleaning_time = props.get("multime")
                self.pet = props.get("pet")
                self.clean_again = props.get("cleanagain")
                if "area_clean_detail" in props:
                    values = props["area_clean_detail"]
                    if len(values) > 1:
                        values = json.loads(values)
                        if values:
                            self.blocked_segments = {
                                v[0]: (
                                    [SegmentSkipReason(v[1]), v[2], v[3]] if len(v) > 3 else [SegmentSkipReason(v[1])]
                                )
                                for v in values
                                if v[1] in SegmentSkipReason._value2member_map_
                            }


class RecoveryMapInfo:
    date = None

    def __init__(self, map_id, date, raw_map, map_object_name, object_name, map_type) -> None:
        self.date = date
        self.raw_map: str = raw_map
        self.map_object_name: str = map_object_name
        self.object_name: str = object_name
        self.map_data: MapData = None
        self.map_id: int = map_id

        self.map_type = (
            RecoveryMapType(map_type) if map_type in RecoveryMapType._value2member_map_ else RecoveryMapType.UNKNOWN
        )

        if self.date:
            self.date = datetime.fromtimestamp(self.date)

    def as_dict(self):
        if self.date:
            return {
                "date": time.strftime("%Y-%m-%d %H:%M", time.localtime(self.date.timestamp())),
                "map_type": self.map_type.name.replace("_", " ").title(),
                "object_name": self.object_name,
            }

    def __eq__(self: RecoveryMapInfo, other: RecoveryMapInfo) -> bool:
        return self.date != other.date or self.map_id != other.map_id or self.object_name != other.object_name

    @property
    def __dict__(self: RecoveryMapInfo):
        if self.date:
            return {
                "date": self.date,
                "map_id": self.map_id,
                "object_name": self.object_name,
                "map_object_name": self.map_object_name,
            }
        return {}


class MapFrameType(IntEnum):
    I = 73
    P = 80
    # T = ??
    W = 87


class MapPixelType(IntEnum):
    OUTSIDE = 0
    WIFI_WALL = 2
    WIFI_UNREACHED = 10
    WIFI_POOR = 11
    WIFI_LOW = 12
    WIFI_HIGH = 13
    WIFI_EXCELLENT = 14
    WALL = 255
    FLOOR = 254
    NEW_SEGMENT = 253
    UNKNOWN = 252
    OBSTACLE_WALL = 251
    DIRTY_AREA = 250
    CLEAN_AREA = 249


class RecoveryMapType(IntEnum):
    UNKNOWN = -1
    EDITED = 0
    ORIGINAL = 1
    BACKUP = 2


class StartupMethod(IntEnum):
    OTHER = -1
    BY_BUTTON = 0
    THROUGH_APP = 1
    SCHEDULED_ACTIVATION = 2
    THROUGH_VOICE = 3


class CleanupMethod(IntEnum):
    OTHER = -1
    DEFAULT_MODE = 0
    CUSTOMIZED_CLEANING = 1
    CLEANGENIUS = 2
    WATER_STAIN_CLEANING = 3


class TaskEndType(IntEnum):
    OTHER = 0
    MANUAL_DOCKING = 1
    NORMAL_RECHARGING = 2
    ABNORMAL_DOCKING = 3
    STOP = 4


class CleaningStatus(IntEnum):
    INTERRUPTED = 0
    COMPLETED = 1
    MANUALLY_ENDED = 2
    FAILED = 3


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
        self.optimized_charger_position: Optional[Point] = None
        self.router_position: Optional[Point] = None  # Data json: whmp
        # Map header: top, left, height, width, grid_size
        self.dimensions: Optional[MapImageDimensions] = None
        self.optimized_dimensions: Optional[MapImageDimensions] = None
        self.combined_dimensions: Optional[MapImageDimensions] = None
        self.data: Optional[Any] = None  # Raw image data for handling P frames
        # Data json
        self.timestamp_ms: Optional[int] = None  # Data json: timestamp_ms
        self.rotation: Optional[int] = None  # Data json: mra
        self.no_go_areas: Optional[List[Area]] = None  # Data json: vw.rect
        self.no_mopping_areas: Optional[List[Area]] = None  # Data json: vw.mop
        self.virtual_walls: Optional[List[Wall]] = None  # Data json: vw.line
        self.virtual_thresholds: Optional[List[Wall]] = None  # Data json: vws.vwsl
        self.passable_thresholds: Optional[List[Wall]] = None  # Data json: vws.vwsl
        self.impassable_thresholds: Optional[List[Wall]] = None  # Data json: vws.npthrsd
        self.ramps: Optional[List[Area]] = None  # Data json: vws.ramp
        self.cliffs: Optional[List[Line]] = None  # Data json: vws.cliff
        self.curtains: Optional[List[Wall]] = None  # Data json: ct.line
        self.path: Optional[Path] = None  # Data json: tr
        self.active_segments: Optional[int] = None  # Data json: sa
        self.active_areas: Optional[List[Area]] = None  # Data json: da2
        self.active_points: Optional[List[Point]] = None  # Data json: sp
        # Data json: rism.map_header.map_id
        self.saved_map_id: Optional[int] = None
        self.saved_map_status: Optional[int] = None  # Data json: ris
        self.restored_map: Optional[bool] = None  # Data json: rpur
        self.frame_map: Optional[bool] = None  # Data json: fsm
        self.docked: Optional[bool] = None  # Data json: oc
        self.clean_log: Optional[bool] = None  # Data json: iscleanlog
        self.cleanset: Optional[Dict[str, List[int]]] = None  # Data json: cleanset
        self.carpet_cleanset: Optional[Dict[str, List[int]]] = None  # Data json: carpetcleanset
        self.line_to_robot: Optional[bool] = None  # Data json: l2r
        self.temporary_map: Optional[int] = None  # Data json: suw
        self.cleaned_area: Optional[int] = None  # Data json: cs
        self.cleaning_time: Optional[int] = None  # Data json: ct
        self.completed: Optional[bool] = None  # Data json: cf
        self.blocked_segments: Optional[Dict[int, List]] = None  #
        self.second_cleaning: Optional[bool] = None  # History list data json: ismultiple
        self.second_mopping: Optional[bool] = None  # History list data json: ctyo
        self.task_interrupt_reason: Optional[TaskInterruptReason] = None  #  History list data json: abnormal_end
        self.cleaning_status: Optional[CleaningStatus] = None  #  History list data: piid: 13
        self.remaining_battery: Optional[int] = None  # Data json: clean_finish_remain_electricity
        self.work_status: Optional[int] = None  # Data json: wm
        self.recovery_map: Optional[bool] = None  # Data json: us
        self.recovery_map_type: Optional[RecoveryMapType] = None  # Generated from recovery map list json
        self.obstacles: Optional[Dict[int, Obstacle]] = None  # Data json: ai_obstacle
        self.furnitures: Optional[Dict[int, Furniture]] = None  # Data json: ai_furniture
        self.saved_furnitures: Optional[Dict[int, Furniture]] = None  # Data json: furniture_info
        self.carpets: Optional[List[Carpet]] = None  # Data json: vw.addcpt
        self.deleted_carpets: Optional[List[Carpet]] = None  # Data json: vw.nocpt
        self.detected_carpets: Optional[List[Carpet]] = None  # Data json: carpet_info
        self.low_lying_areas: Optional[List[Polygon]] = None  # Data json: sneak_areas or sneak_areas_end
        self.cleaning_sequence: Optional[Dict[int, int]] = None  # Data json: cleanareaorder
        self.mop_type: Optional[Dict[int, str]] = None  # Data json: mop_type_with_order
        self.carpet_pixels: Optional[Any] = None  # Generated from map data
        self.new_map: Optional[bool] = None  # Data json: risp
        self.startup_method: Optional[StartupMethod] = None  # Data json: smd
        self.task_end_type: Optional[TaskEndType] = None  # Data json: ctyi
        self.cleanup_method: Optional[CleanupMethod] = None  # Data json: cmc
        self.customized_cleaning: Optional[int] = None  # Data json: customeclean
        self.dust_collection_count: Optional[int] = None  # Data json: ds
        self.mop_wash_count: Optional[int] = None  # Data json: wt
        self.cleaned_segments: Optional[List[Any]] = None  # Data json: CleanArea (from cleaning map data)
        self.multiple_cleaning_time: Optional[int] = None  # Data json: multime
        self.dos: Optional[int] = None  # Data json: dos
        self.mopping_mode: Optional[int] = None  # Data json: mooClean
        self.notified: Optional[bool] = None  # Data json: nopush
        self.sequence: bool = False
        self.change_mop: bool = False
        self.recommended_area_type: Optional[int] = None  # Data json: rec_vw.type
        self.recommended_threshold_type: Optional[int] = None  # Data json: rec_vws.type
        self.recommended_carpets: Optional[List[Carpet]] = None  # Data json: rec_vw.addcpt
        self.recommended_ramps: Optional[List[Area]] = None  # Data json: rec_vws.ramp
        self.recommended_cliffs: Optional[List[Line]] = None  # Data json: rec_vws.cliff
        self.recommended_virtual_thresholds: Optional[List[Wall]] = None  # Data json: rec_vws.vwsl
        self.recommended_passable_thresholds: Optional[List[Wall]] = None  # Data json: rec_vws.vwsl
        self.recommended_impassible_thresholds: Optional[List[Wall]] = None  # Data json: rec_vws.npthrsd
        self.recommended_virtual_walls: Optional[List[Wall]] = None  # Data json: rec_vw.line
        self.recommended_no_go_areas: Optional[List[Area]] = None  # Data json: rec_vw.rect
        self.recommended_no_mopping_areas: Optional[List[Area]] = None  # Data json: rec_vw.mop
        # Generated
        self.custom_name: Optional[str] = None  # Map list json: name
        self.object_name: Optional[str] = None  # Map list json: mapobj
        self.map_index: Optional[int] = None  # Generated from saved map list
        self.map_name: Optional[str] = None  # Generated map name for map list
        # Generated pixel map for rendering colors
        self.pixel_type: Optional[Any] = None
        self.optimized_pixel_type: Optional[Any] = None
        self.combined_pixel_type: Optional[Any] = None
        # Generated segments from pixel_type
        self.segments: Optional[Dict[int, Segment]] = None
        self.floor_material: Optional[Dict[int, int]] = None  # Generated from seg_inf.material
        self.saved_map: Optional[bool] = None  # Generated for rism map
        self.empty_map: Optional[bool] = None  # Generated from pixel_type
        self.wifi_map_data: Optional[MapData] = None  # Generated from whm
        self.wifi_map: Optional[bool] = None  #
        self.cleaning_map_data: Optional[MapData] = None  # Generated from decmap
        self.cleaning_map: Optional[bool] = None  #
        self.has_cleaned_area: Optional[bool] = None  #
        self.has_dirty_area: Optional[bool] = None  #
        self.history_map: Optional[bool] = None  #
        self.furniture_version: Optional[bool] = None  #
        self.recovery_map_list: Optional[List[RecoveryMapInfo]] = None  # Generated from recovery map list
        self.active_cruise_points: Optional[List[Coordinate]] = None  # Data json: pointinfo.tpoint
        self.predefined_points: Optional[Dict[int, Coordinate]] = None  # Data json: pointinfo.spoint
        self.task_cruise_points: Optional[List[Coordinate]] = None  # Data json: tpointinfo
        # Generated from pixel_type and robot poisiton
        self.hidden_segments: Optional[int] = None  # Data json: delsr
        self.robot_segment: Optional[int] = None
        self.station_segment: Optional[int] = None
        # For renderer to detect changes
        self.last_updated: Optional[float] = None
        # For vslam map rendering optimization
        self.need_optimization: Optional[bool] = None
        # 3D Map Properties
        self.ai_outborders_user: Optional[Any] = None
        self.ai_outborders: Optional[Any] = None
        self.ai_outborders_new: Optional[Any] = None
        self.ai_outborders_2d: Optional[Any] = None
        self.ai_furniture_warning: Optional[Any] = None
        self.walls_info: Optional[Any] = None
        self.walls_info_new: Optional[Any] = None
        self.zone_cleaning: Optional[bool] = False

    def __eq__(self: MapData, other: MapData) -> bool:
        if other is None:
            return False

        if self.map_id != other.map_id:
            return False

        if self.custom_name != other.custom_name:
            return False

        if self.rotation != other.rotation:
            return False

        if self.work_status != other.work_status:
            return False

        if self.robot_position != other.robot_position:
            return False

        if self.charger_position != other.charger_position:
            return False

        if self.no_go_areas != other.no_go_areas:
            return False

        if self.no_mopping_areas != other.no_mopping_areas:
            return False

        if self.carpets != other.carpets:
            return False

        if self.deleted_carpets != other.deleted_carpets:
            return False

        if self.detected_carpets != other.detected_carpets:
            return False

        if self.virtual_walls != other.virtual_walls:
            return False

        if self.virtual_thresholds != other.virtual_thresholds:
            return False

        if self.passable_thresholds != other.passable_thresholds:
            return False

        if self.impassable_thresholds != other.impassable_thresholds:
            return False

        if self.ramps != other.ramps:
            return False

        if self.low_lying_areas != other.low_lying_areas:
            return False

        if self.curtains != other.curtains:
            return False

        if self.docked != other.docked:
            return False

        if self.active_segments != other.active_segments:
            return False

        if self.active_areas != other.active_areas:
            return False

        if self.active_points != other.active_points:
            return False

        if self.active_cruise_points != other.active_cruise_points:
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

        if not self.saved_map and not other.saved_map and self.cleanset != other.cleanset:
            return False

        if self.sequence != other.sequence:
            return False

        if self.cleaning_sequence != other.cleaning_sequence:
            return False

        if self.mop_type != other.mop_type:
            return False

        if self.carpet_cleanset != other.carpet_cleanset:
            return False

        if not self.saved_map and not other.saved_map and self.furnitures != other.furnitures:
            return False

        if self.saved_furnitures != other.saved_furnitures:
            return False

        if self.obstacles != other.obstacles:
            return False

        if self.predefined_points != other.predefined_points:
            return False

        if self.router_position != other.router_position:
            return False

        if self.hidden_segments != other.hidden_segments:
            return False

        if self.zone_cleaning != other.zone_cleaning:
            return False

        return True

    def as_dict(self) -> Dict[str, Any]:
        attributes_list = {}
        if self.charger_position is not None:
            attributes_list[ATTR_CHARGER] = (
                self.optimized_charger_position
                if self.optimized_charger_position is not None
                else self.charger_position
            )
        if self.custom_name is not None:
            attributes_list[ATTR_CUSTOM_NAME] = self.custom_name
        if self.segments is not None and (self.saved_map or self.saved_map_status == 2 or self.restored_map):
            attributes_list[ATTR_ROOMS] = {k: v.as_dict() for k, v in sorted(self.segments.items())}
        if not self.saved_map and self.robot_position is not None:
            attributes_list[ATTR_ROBOT_POSITION] = self.robot_position
        if self.map_id:
            attributes_list[ATTR_MAP_ID] = self.map_id
        if self.saved_map_id:
            attributes_list[ATTR_SAVED_MAP_ID] = self.saved_map_id
        if self.map_name is not None:
            attributes_list[ATTR_MAP_NAME] = self.map_name
        if self.rotation is not None:
            attributes_list[ATTR_ROTATION] = self.rotation
        if self.last_updated is not None:
            attributes_list[ATTR_UPDATED] = datetime.fromtimestamp(self.last_updated)
        if not self.saved_map and self.active_areas is not None:
            attributes_list[ATTR_ACTIVE_AREAS] = self.active_areas
        if not self.saved_map and self.active_segments is not None:
            attributes_list[ATTR_ACTIVE_SEGMENTS] = self.active_segments
        if not self.saved_map and self.active_points is not None:
            attributes_list[ATTR_ACTIVE_POINTS] = self.active_points
        if not self.saved_map and self.active_cruise_points is not None:
            attributes_list[ATTR_ACTIVE_CRUISE_POINTS] = self.active_cruise_points
        if self.predefined_points:
            attributes_list[ATTR_PREDEFINED_POINTS] = self.predefined_points
        if self.virtual_walls is not None:
            attributes_list[ATTR_VIRTUAL_WALLS] = self.virtual_walls
        if self.virtual_thresholds is not None:
            attributes_list[ATTR_VIRTUAL_THRESHOLDS] = self.virtual_thresholds
        if self.passable_thresholds is not None:
            attributes_list[ATTR_PASSABLE_THRESHOLDS] = self.passable_thresholds
        if self.impassable_thresholds is not None:
            attributes_list[ATTR_IMPASSABLE_THRESHOLDS] = self.impassable_thresholds
        if self.ramps is not None:
            attributes_list[ATTR_RAMPS] = self.ramps
        if self.low_lying_areas is not None:
            attributes_list[ATTR_LOW_LYING_AREAS] = self.low_lying_areas
        if self.no_go_areas is not None:
            attributes_list[ATTR_NO_GO_AREAS] = self.no_go_areas
        if self.no_mopping_areas is not None:
            attributes_list[ATTR_NO_MOPPING_AREAS] = self.no_mopping_areas
        if self.carpets is not None:
            attributes_list[ATTR_CARPETS] = self.carpets
        if self.deleted_carpets is not None:
            attributes_list[ATTR_DELETED_CARPETS] = self.deleted_carpets
        if self.detected_carpets is not None:
            attributes_list[ATTR_DETECTED_CARPETS] = self.detected_carpets
        if self.curtains is not None:
            attributes_list[ATTR_CURTAINS] = self.curtains
        if self.empty_map is not None:
            attributes_list[ATTR_IS_EMPTY] = self.empty_map
        if self.frame_id:
            attributes_list[ATTR_FRAME_ID] = self.frame_id
        if self.map_index:
            attributes_list[ATTR_MAP_INDEX] = self.map_index
        if self.obstacles:
            attributes_list[ATTR_OBSTACLES] = self.obstacles
        if self.saved_furnitures and self.saved_map:
            attributes_list[ATTR_FURNITURES] = list(self.saved_furnitures.values())
        elif self.furnitures:
            attributes_list[ATTR_FURNITURES] = list(self.furnitures.values())
        if self.router_position:
            attributes_list[ATTR_ROUTER_POSITION] = self.router_position
        if self.startup_method is not None:
            attributes_list[ATTR_STARTUP_METHOD] = self.startup_method.name.replace("_", " ").title()
        if self.dust_collection_count is not None:
            attributes_list[ATTR_DUST_COLLECTION_COUNT] = self.dust_collection_count
        if self.mop_wash_count is not None:
            attributes_list[ATTR_MOP_WASH_COUNT] = self.mop_wash_count
        if self.recovery_map_list:
            attributes_list[ATTR_RECOVERY_MAP_LIST] = [v.as_dict() for v in reversed(self.recovery_map_list)]
        return attributes_list

    def check_point(self, x, y, absolute=False) -> bool:
        pixel_type = self.pixel_type
        dimensions = self.dimensions
        if self.combined_pixel_type is not None:
            pixel_type = self.combined_pixel_type
            dimensions = self.combined_dimensions

        if not absolute:
            x = int((x - dimensions.left) / dimensions.grid_size)
            y = int((y - dimensions.top) / dimensions.grid_size)
        if x < 0 or x >= dimensions.width or y < 0 or y >= dimensions.height:
            return False
        value = int(pixel_type[x, y])
        return value > 0 and value != 255


@dataclass
class DirtyData:
    value: Any = None
    previous_value: Any = None
    update_time: float = None


@dataclass
class Shortcut:
    id: int = -1
    index: int = -1
    name: str = None
    map_id: int = None
    running: bool = False
    tasks: list[list[ShortcutTask]] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})


@dataclass
class ShortcutTask:
    order: int = None
    segment_id: int = None
    suction_level: int = None
    water_volume: int = None
    cleaning_times: int = None
    cleaning_mode: int = None
    wetness_level: int = None
    mopping_settings: int = None
    cleaning_route: int = None
    custom_mopping_route: int = None
    mop_temperature: int = None
    mop_pressure: int = None
    coords: list[int] = None
    task_type: DreameVacuumShortcutTaskType = None


@dataclass
class DNDTask:
    id: int = -1
    enabled: bool = False
    start: str = None
    end: str = None
    repeats: int = None
    ss: int = False

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
    

@dataclass
class ScheduledTask:
    id: int = -1
    enabled: bool = False
    invalid: bool = False
    time: str = None
    repeats: str = None
    once: bool = False
    map_id: str = None
    suction_level: int = None
    water_volume: int = None
    options: str = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GoToZoneSettings:
    x: int = None
    y: int = None
    stop: bool = False
    start: bool = False
    suction_level: int = None
    water_level: int = None
    cleaning_mode: int = None
    size: int = 50


@dataclass
class MapRendererConfig:
    color: bool = True
    icon: bool = True
    name: bool = True
    name_background: bool = True
    order: bool = True
    suction_level: bool = True
    water_volume: bool = True
    cleaning_times: bool = True
    cleaning_mode: bool = True
    mopping_mode: bool = True
    path: bool = True
    no_go: bool = True
    no_mop: bool = True
    virtual_wall: bool = True
    pathway: bool = True
    low_lying_area: bool = True
    active_area: bool = True
    active_point: bool = True
    charger: bool = True
    robot: bool = True
    cleaning_direction: bool = True
    obstacle: bool = True
    stain: bool = True
    pet: bool = True
    carpet: bool = True
    material: bool = True
    furniture: bool = True
    curtain: bool = True
    ramp: bool = True
    cruise_point: bool = True


@dataclass
class MapRendererColorScheme:
    floor: tuple[int] = (221, 221, 221, 255)
    outside: tuple[int] = (0, 0, 0, 0)
    wall: tuple[int] = (159, 159, 159, 255)
    passive_segment: tuple[int] = (200, 200, 200, 255)
    hidden_segment: tuple[int] = (226, 226, 226, 255)
    new_segment: tuple[int] = (153, 191, 255, 255)
    dirty_area: tuple[int] = (123, 148, 172, 255)
    clean_area: tuple[int] = (156, 202, 250, 255)
    second_clean_area: tuple[int] = (64, 149, 241, 255)
    blocked_segment: tuple[int] = (255, 159, 10, 110)
    no_go: tuple[int] = (177, 0, 0, 50)
    no_go_outline: tuple[int] = (199, 0, 0, 200)
    no_mop: tuple[int] = (170, 47, 255, 50)
    no_mop_outline: tuple[int] = (153, 0, 210, 200)
    virtual_wall: tuple[int] = (199, 0, 0, 200)
    virtual_threshold: tuple[int] = (50, 215, 75, 255)
    passable_threshold_outline: tuple[int] = (50, 215, 75, 255)
    passable_threshold: tuple[int] = (50, 215, 75, 50)
    impassable_threshold_outline: tuple[int] = (199, 0, 0, 255)
    impassable_threshold: tuple[int] = (199, 0, 0, 50)
    curtain: tuple[int] = (247, 123, 46, 255)
    ramp: tuple[int] = (255, 255, 255, 50)
    ramp_outline: tuple[int] = (10, 132, 255, 255)
    low_lying_area: tuple[int] = (157, 211, 246, 40)
    auto_low_lying_area_outline: tuple[int] = (121, 203, 255, 255)
    manual_low_lying_area_outline: tuple[int] = (100, 181, 232, 255)
    active_area: tuple[int] = (255, 255, 255, 80)
    active_area_outline: tuple[int] = (34, 109, 242, 255)  # (103, 156, 244, 200)
    active_point: tuple[int] = (255, 255, 255, 80)
    active_point_outline: tuple[int] = (34, 109, 242, 255)  # (103, 156, 244, 200)
    path: tuple[int] = (255, 255, 255, 255)
    mop_path: tuple[int] = (255, 255, 255, 100)
    segment: tuple[list[tuple[int]]] = (
        [(171, 199, 248, 255), (121, 170, 255, 255)],
        [(249, 224, 125, 255), (255, 211, 38, 255)],
        [(184, 227, 255, 255), (141, 210, 255, 255)],
        [(184, 217, 141, 255), (150, 217, 141, 255)],
    )
    obstacle_bg: tuple[int] = (34, 109, 242, 255)
    icon_background: tuple[int] = (0, 0, 0, 100)
    settings_background: tuple[int] = (255, 255, 255, 175)
    settings_icon_background: tuple[int] = (255, 255, 255, 205)
    material_color: tuple[int] = (0, 0, 0, 20)
    carpet_color_detected: tuple[int] = (0, 0, 0, 35)
    carpet_color: tuple[int] = (0, 0, 0, 80)
    text: tuple[int] = (255, 255, 255, 255)
    order: tuple[int] = (255, 255, 255, 255)
    text_stroke: tuple[int] = (240, 240, 240, 200)
    invert: bool = False
    dark: bool = False


MAP_COLOR_SCHEME_LIST: Final = {
    "Dreame Light": MapRendererColorScheme(),
    "Dreame Dark": MapRendererColorScheme(
        floor=(110, 110, 110, 255),
        wall=(64, 64, 64, 255),
        passive_segment=(100, 100, 100, 255),
        hidden_segment=(116, 116, 116, 255),
        new_segment=(0, 91, 244, 255),
        no_go=(133, 0, 0, 128),
        no_go_outline=(149, 0, 0, 200),
        no_mop=(134, 0, 226, 128),
        no_mop_outline=(115, 0, 157, 200),
        virtual_wall=(133, 0, 0, 200),
        virtual_threshold=(36, 163, 55, 255),
        passable_threshold_outline=(36, 163, 55, 255),
        passable_threshold=(36, 163, 55, 50),
        impassable_threshold_outline=(133, 0, 0, 200),
        impassable_threshold=(133, 0, 0, 200),
        curtain=(173, 85, 29, 255),
        ramp_outline=(16, 95, 186, 255),
        active_area=(200, 200, 200, 70),
        active_area_outline=(28, 81, 176, 255),  # (9, 54, 129, 200),
        active_point=(200, 200, 200, 80),
        active_point_outline=(28, 81, 176, 255),  # (9, 54, 129, 200),
        path=(200, 200, 200, 255),
        mop_path=(200, 200, 200, 100),
        segment=(
            [(13, 64, 155, 255), (0, 55, 150, 255)],
            [(143, 75, 7, 255), (117, 53, 0, 255)],
            [(0, 106, 176, 255), (0, 96, 158, 255)],
            [(76, 107, 36, 255), (44, 107, 36, 255)],
        ),
        obstacle_bg=(28, 81, 176, 255),
        material_color=(255, 255, 255, 20),
        carpet_color_detected=(255, 255, 255, 35),
        carpet_color=(255, 255, 255, 80),
        settings_icon_background=(255, 255, 255, 195),
        dark=True,
    ),
    "Mijia Light": MapRendererColorScheme(
        new_segment=(131, 178, 255, 255),
        virtual_wall=(255, 45, 45, 200),
        no_go=(230, 30, 30, 128),
        no_go_outline=(255, 45, 45, 200),
        segment=(
            [(131, 178, 255, 255), (105, 142, 204, 255)],
            [(245, 201, 66, 255), (196, 161, 53, 255)],
            [(103, 207, 229, 255), (82, 165, 182, 255)],
            [(255, 155, 101, 255), (204, 124, 81, 255)],
        ),
        obstacle_bg=(131, 178, 255, 255),
    ),
    "Mijia Dark": MapRendererColorScheme(
        floor=(150, 150, 150, 255),
        wall=(119, 133, 153, 255),
        new_segment=(99, 148, 230, 255),
        passive_segment=(100, 100, 100, 255),
        hidden_segment=(116, 116, 116, 255),
        no_go=(133, 0, 0, 128),
        no_go_outline=(149, 0, 0, 200),
        no_mop=(134, 0, 226, 128),
        no_mop_outline=(115, 0, 157, 200),
        virtual_wall=(133, 0, 0, 200),
        active_area=(200, 200, 200, 70),
        active_area_outline=(9, 54, 129, 200),
        active_point=(200, 200, 200, 80),
        active_point_outline=(9, 54, 129, 200),
        path=(200, 200, 200, 255),
        mop_path=(200, 200, 200, 100),
        segment=(
            [(108, 141, 195, 255), (76, 99, 137, 255)],
            [(188, 157, 62, 255), (133, 111, 44, 255)],
            [(88, 161, 176, 255), (62, 113, 123, 255)],
            [(195, 125, 87, 255), (138, 89, 62, 255)],
        ),
        obstacle_bg=(108, 141, 195, 255),
        material_color=(255, 255, 255, 35),
        carpet_color_detected=(255, 255, 255, 50),
        carpet_color=(255, 255, 255, 90),
        settings_icon_background=(255, 255, 255, 195),
        dark=True,
    ),
    "Grayscale": MapRendererColorScheme(
        floor=(100, 100, 100, 255),
        wall=(40, 40, 40, 255),
        passive_segment=(50, 50, 50, 255),
        hidden_segment=(55, 55, 55, 255),
        new_segment=(80, 80, 80, 255),
        no_go=(133, 0, 0, 128),
        no_go_outline=(149, 0, 0, 200),
        no_mop=(134, 0, 226, 128),
        no_mop_outline=(115, 0, 157, 200),
        virtual_wall=(133, 0, 0, 200),
        virtual_threshold=(36, 163, 55, 255),
        passable_threshold_outline=(36, 163, 55, 255),
        passable_threshold=(36, 163, 55, 50),
        impassable_threshold_outline=(133, 0, 0, 200),
        impassable_threshold=(133, 0, 0, 200),
        curtain=(173, 85, 29, 255),
        ramp_outline=(16, 95, 186, 255),
        active_area=(221, 221, 221, 60),
        active_area_outline=(22, 103, 238, 200),
        active_point=(221, 221, 221, 80),
        active_point_outline=(22, 103, 238, 200),
        path=(200, 200, 200, 255),
        mop_path=(200, 200, 200, 100),
        segment=(
            [(90, 90, 90, 255), (95, 95, 95, 255)],
            [(80, 80, 80, 255), (85, 85, 85, 255)],
            [(70, 70, 70, 255), (75, 75, 75, 255)],
            [(60, 60, 60, 255), (65, 65, 65, 255)],
        ),
        obstacle_bg=(90, 90, 90, 255),
        material_color=(255, 255, 255, 20),
        carpet_color_detected=(255, 255, 255, 35),
        carpet_color=(255, 255, 255, 80),
        icon_background=(200, 200, 200, 200),
        settings_icon_background=(255, 255, 255, 205),
        text=(0, 0, 0, 255),
        text_stroke=(0, 0, 0, 100),
        invert=True,
        dark=True,
    ),
    "Transparent": MapRendererColorScheme(
        floor=(0, 0, 0, 0),
        wall=(0, 0, 0, 0),
        passive_segment=(0, 0, 0, 0),
        hidden_segment=(0, 0, 0, 0),
        new_segment=(0, 0, 0, 0),
        path=(255, 255, 255, 200),
        mop_path=(255, 255, 255, 50),
        segment=(
            [(0, 0, 0, 0), (121, 170, 255, 255)],
            [(0, 0, 0, 0), (255, 211, 38, 255)],
            [(0, 0, 0, 0), (141, 210, 255, 255)],
            [(0, 0, 0, 0), (150, 217, 141, 255)],
        ),
    ),
}

MAP_ICON_SET_LIST: Final = {"Dreame": 0, "Dreame Old": 1, "Mijia": 2, "Material": 3}


class MapRendererLayer(IntEnum):
    IMAGE = 0
    OBJECTS = 1
    PATH = 2
    PATH_MASK = 3
    NO_MOP = 4
    NO_GO = 5
    WALL = 6
    VIRTUAL_THRESHOLD = 7
    PASSABLE_THRESHOLD = 8
    IMPASSABLE_THRESHOLD = 9
    RAMP = 10
    CURTAIN = 11
    LOW_LYING_AREA = 12
    FURNITURES = 13
    FURNITURE = 14
    ACTIVE_AREA = 15
    ACTIVE_POINT = 16
    SEGMENTS = 17
    SEGMENT = 18
    CHARGER = 19
    ROBOT = 20
    ROUTER = 21
    OBSTACLES = 22
    OBSTACLE = 23
    CRUISE_POINTS = 24
    CRUISE_POINT = 25


@dataclass
class Line:
    x: int | List[int] = None
    y: int | List[int] = None
    ishorizontal: bool = False
    direction: int = 0


@dataclass
class CLine(Line):
    length: int = 0
    findEnd: bool = False


@dataclass
class ALine:
    p0: Line = field(default_factory=lambda: Line(0, 0, False, 0))
    p1: Line = field(default_factory=lambda: Line(0, 0, False, 0))
    length: int = 0


@dataclass
class Paths:
    clines: List[CLine] = field(default_factory=lambda: [])
    alines: List[ALine] = field(default_factory=lambda: [])
    length: int = 0


@dataclass
class Angle:
    lines: List[ALine] = field(default_factory=lambda: [])
    horizontalDir: int = 0
    verticalDir: int = 0


@dataclass
class MapRendererResources:
    renderer: str = ""
    icon_set: int = 0
    robot_type: int = 0
    robot: str = None
    charger: str = None
    charging: str = None
    cleaning: str = None
    warning: str = None
    sleeping: str = None
    cleaning_direction: str = None
    selected_segment: str = None
    cruise_point_background: str = None
    segment: Dict[int, Dict[str, str]] = None
    default_map_image: str = None
    font: str = None
    repeats: list[str] = None
    suction_level: list[str] = None
    water_volume: list[str] = None
    mop_pad_humidity: list[str] = None
    cleaning_mode: list[str] = None
    cleaning_route: list[str] = None
    custom_mopping_route: list[str] = None
    mop_temperature: list[str] = None
    mop_pressure: list[str] = None
    washing: str = None
    hot_washing: str = None
    drying: str = None
    hot_drying: str = None
    emptying: str = None
    cruise_path_point_background: str = None
    obstacle_background: str = None
    obstacle_hidden_background: str = None
    obstacle: Dict[int, Dict[str, str]] = None
    furniture: Dict[int, Dict[str, str]] = None
    rotate: str = None
    delete: str = None
    resize: str = None
    move: str = None
    problem: str = None
    clean: str = None
    settings: str = None
    edit: str = None
    wifi: str = None
    version: int = 1


@dataclass
class MapRendererData:
    data: Dict[int, list[int]]
    size: list[int] = None
    map_id: int = 0
    saved_map_id: int = None
    map_index: int = None
    saved_map_status: int = None
    empty_map: bool = None
    frame_id: int = 0
    saved_map: bool = False
    wifi_map: bool = False
    history_map: bool = False
    recovery_map: bool = False
    temporary_map: bool = False
    need_optimization: bool = None
    segments: Dict[int, list[int | str]] | None = None
    active_segments: list[int] = field(default_factory=lambda: [])
    active_areas: list[list[int]] = field(default_factory=lambda: [])
    active_points: list[list[int]] = field(default_factory=lambda: [])
    active_cruise_points: list[list[int]] = field(default_factory=lambda: [])
    task_cruise_points: bool = False
    predefined_points: list[list[int]] | None = None
    no_mop: list[list[int]] = field(default_factory=lambda: [])
    no_go: list[list[int]] = field(default_factory=lambda: [])
    carpets: list[list[int]] | None = None
    deleted_carpets: list[list[int]] | None = None
    detected_carpets: list[list[int]] | None = None
    virtual_walls: list[list[int]] = field(default_factory=lambda: [])
    virtual_thresholds: list[list[int]] | None = None
    passable_thresholds: list[list[int]] | None = None
    impassable_thresholds: list[list[int]] | None = None
    ramps: list[list[int]] | None = None
    curtains: list[list[int]] | None = None
    low_lying_areas: list[list[int]] | None = None
    obstacles: list[list[int | float]] = field(default_factory=lambda: [])
    furnitures: list[list[int | float]] | None = None
    path: list[list[int]] = field(default_factory=lambda: [])
    floor_material: Dict[int, list[int]] | None = None
    hidden_segments: Dict[int, list[int]] | None = None
    blocked_segments: Dict[int, list[int]] | None = None
    robot_position: list[int] | None = None
    charger_position: list[int] | None = None
    router_position: list[int] | None = None
    station_segment: int | None = None
    ai_outborders_user: list[list[int]] | None = None
    ai_outborders: list[list[int]] | None = None
    ai_outborders_new: list[list[int]] | None = None
    ai_outborders_2d: list[list[int]] | None = None
    second_cleaning: int | None = None
    second_mopping: int | None = None
    mop_wash_count: int | None = None
    dust_collection_count: int | None = None
    multiple_cleaning_time: int | None = None
    dos: int | None = None
    cleaning_map: bool = None
    cleaning_map_data: MapRendererData = None
    has_cleaned_area: bool = None
    has_dirty_area: bool = None
    mopping_mode: int | None = None
    wifi_map_data: MapRendererData = None
    task_end_type: int | None = None
    task_interrupt_reason: int | None = None
    cleaning_status: int | None = None
    recommended_area_type: int | None = (None,)
    recommended_threshold_type: int | None = (None,)
    recommended_carpets: list[list[int]] | None = (None,)
    recommended_ramps: list[list[int]] | None = (None,)
    recommended_cliffs: list[list[int]] | None = (None,)
    recommended_virtual_thresholds: list[list[int]] | None = (None,)
    recommended_passable_thresholds: list[list[int]] | None = (None,)
    recommended_impassible_thresholds: list[list[int]] | None = (None,)
    recommended_virtual_walls: list[list[int]] | None = (None,)
    recommended_no_go_areas: list[list[int]] | None = (None,)
    recommended_no_mopping_areas: list[list[int]] | None = (None,)
    ai_furniture_warning: int | None = None
    walls_info: Any | None = None
    walls_info_new: Any | None = None
    furniture_version: int | None = None
    startup_method: int | None = None
    cleanup_method: int | None = None
    cleaned_segments: list[int] | None = None
    cleaned_area: int | None = None
    cleaning_time: int | None = None
    robot_status: int | None = None
    station_status: int | None = None
    completed: bool | None = None
    remaining_battery: int | None = None
    zone_cleaning: bool | None = False
    cleanset: bool = False
    sequence: bool = False
    change_mop: bool = False
    docked: bool = True
    work_status: int = 0
    resources: MapRendererResources = None
    version: int = 1
