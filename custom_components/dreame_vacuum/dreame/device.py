from __future__ import annotations
import logging
import time
import json
import re
import copy
import zlib
import base64
import traceback
from functools import cmp_to_key
from datetime import datetime
from random import randrange
from threading import Timer
from typing import Any, Optional

from .types import (
    PIID,
    DIID,
    DID,
    ACTION_AVAILABILITY,
    PROPERTY_AVAILABILITY,
    DreameVacuumProperty,
    DreameVacuumAutoSwitchProperty,
    DreameVacuumStrAIProperty,
    DreameVacuumAIProperty,
    DreameVacuumPropertyMapping,
    DreameVacuumAction,
    DreameVacuumActionMapping,
    DreameVacuumChargingStatus,
    DreameVacuumTaskStatus,
    DreameVacuumState,
    DreameVacuumStateOld,
    DreameVacuumWaterTank,
    DreameVacuumCarpetSensitivity,
    DreameVacuumCarpetCleaning,
    DreameVacuumStatus,
    DreameVacuumErrorCode,
    DreameVacuumRelocationStatus,
    DreameVacuumDustCollection,
    DreameVacuumAutoEmptyStatus,
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
    DreameVacuumWiderCornerCoverage,
    DreameVacuumMopPadSwing,
    DreameVacuumMopExtendFrequency,
    DreameVacuumSecondCleaning,
    DreameVacuumCleaningRoute,
    DreameVacuumCustomMoppingRoute,
    DreameVacuumSelfCleanFrequency,
    DreameVacuumAutoEmptyMode,
    DreameVacuumCleanGenius,
    DreameVacuumCleanGeniusMode,
    DreameVacuumWashingMode,
    DreameVacuumWaterTemperature,
    DreameVacuumDrainageStatus,
    DreameVacuumLowWaterWarning,
    DreameVacuumTaskType,
    DreameVacuumMapRecoveryStatus,
    DreameVacuumMapBackupStatus,
    DreameVacuumCleanWaterTankStatus,
    DreameVacuumDirtyWaterTankStatus,
    DreameVacuumDustBagStatus,
    DreameVacuumDetergentStatus,
    DreameVacuumHotWaterStatus,
    DreameVacuumStationDrainageStatus,
    CleaningHistory,
    DreameVacuumDeviceCapability,
    DirtyData,
    RobotType,
    MapData,
    Segment,
    Shortcut,
    ShortcutTask,
    ObstacleType,
    CleanupMethod,
    GoToZoneSettings,
    Path,
    PathType,
    Coordinate,
    ScheduleTask,
    ATTR_ACTIVE_AREAS,
    ATTR_ACTIVE_POINTS,
    ATTR_ACTIVE_SEGMENTS,
    ATTR_PREDEFINED_POINTS,
    ATTR_ACTIVE_CRUISE_POINTS,
)
from .const import (
    DEVICE_INFO,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    SUCTION_LEVEL_CODE_TO_NAME,
    WATER_VOLUME_CODE_TO_NAME,
    MOP_PAD_HUMIDITY_CODE_TO_NAME,
    CLEANING_MODE_CODE_TO_NAME,
    CARPET_SENSITIVITY_CODE_TO_NAME,
    CARPET_CLEANING_CODE_TO_NAME,
    CHARGING_STATUS_CODE_TO_NAME,
    RELOCATION_STATUS_CODE_TO_NAME,
    SELF_WASH_BASE_STATUS_TO_NAME,
    AUTO_EMPTY_STATUS_TO_NAME,
    MAP_RECOVERY_STATUS_TO_NAME,
    MAP_BACKUP_STATUS_TO_NAME,
    TASK_STATUS_CODE_TO_NAME,
    STATE_CODE_TO_STATE,
    ERROR_CODE_TO_ERROR_NAME,
    ERROR_CODE_TO_ERROR_DESCRIPTION,
    STATUS_CODE_TO_NAME,
    WATER_TANK_CODE_TO_NAME,
    DUST_COLLECTION_TO_NAME,
    MOP_WASH_LEVEL_TO_NAME,
    MOP_CLEAN_FREQUENCY_TO_NAME,
    MOPPING_TYPE_TO_NAME,
    STREAM_STATUS_TO_NAME,
    WIDER_CORNER_COVERAGE_TO_NAME,
    MOP_PAD_SWING_TO_NAME,
    MOP_EXTEND_FREQUENCY_TO_NAME,
    SECOND_CLEANING_TO_NAME,
    CLEANING_ROUTE_TO_NAME,
    CUSTOM_MOPPING_ROUTE_TO_NAME,
    CLEANGENIUS_TO_NAME,
    CLEANGENIUS_MODE_TO_NAME,
    WASHING_MODE_TO_NAME,
    WASHING_MODE_ULTRA_WASHING,
    WATER_TEMPERATURE_TO_NAME,
    SELF_CLEAN_FREQUENCY_TO_NAME,
    AUTO_EMPTY_MODE_TO_NAME,
    FLOOR_MATERIAL_CODE_TO_NAME,
    FLOOR_MATERIAL_DIRECTION_CODE_TO_NAME,
    SEGMENT_VISIBILITY_CODE_TO_NAME,
    LOW_WATER_WARNING_TO_NAME,
    LOW_WATER_WARNING_CODE_TO_DESCRIPTION,
    DRAINAGE_STATUS_TO_NAME,
    VOICE_ASSISTANT_LANGUAGE_TO_NAME,
    TASK_TYPE_TO_NAME,
    CLEAN_WATER_TANK_STATUS_TO_NAME,
    DIRTY_WATER_TANK_STATUS_TO_NAME,
    DUST_BAG_STATUS_TO_NAME,
    DETERGENT_STATUS_TO_NAME,
    HOT_WATER_STATUS_TO_NAME,
    STATION_DRAINAGE_STATUS_TO_NAME,
    ERROR_CODE_TO_IMAGE_INDEX,
    CONSUMABLE_TO_LIFE_WARNING_DESCRIPTION,
    PROPERTY_TO_NAME,
    CLEANING_MODE_MOPPING_AFTER_SWEEPING,
    MOP_WASH_LEVEL_WATER_SAVING,
    MOP_CLEAN_FREQUENCY_BY_ROOM,
    MOP_CLEAN_FREQUENCY_FIVE_SQUARE_METERS,
    MOP_CLEAN_FREQUENCY_EIGHT_SQUARE_METERS,
    MOP_CLEAN_FREQUENCY_FIFTEEN_SQUARE_METERS,
    MOP_CLEAN_FREQUENCY_TWENTY_SQUARE_METERS,
    MOP_CLEAN_FREQUENCY_TWENTYFIVE_SQUARE_METERS,
    CARPET_CLEANING_ADAPTATION_WITHOUT_ROUTE,
    CARPET_CLEANING_CROSS,
    CARPET_CLEANING_VACUUM_AND_MOP,
    CARPET_CLEANING_REMOVE_MOP,
    CARPET_CLEANING_IGNORE,
    FLOOR_MATERIAL_MEDIUM_PILE_CARPET,
    FLOOR_MATERIAL_LOW_PILE_CARPET,
    FLOOR_MATERIAL_CARPET,
    ATTR_CHARGING,
    ATTR_DOCKED,
    ATTR_VACUUM_STATE,
    ATTR_DND,
    ATTR_SHORTCUTS,
    ATTR_BATTERY,
    ATTR_CLEANING_SEQUENCE,
    ATTR_STARTED,
    ATTR_PAUSED,
    ATTR_RUNNING,
    ATTR_RETURNING_PAUSED,
    ATTR_RETURNING,
    ATTR_MAPPING,
    ATTR_MAPPING_AVAILABLE,
    ATTR_WASHING_AVAILABLE,
    ATTR_DRYING_AVAILABLE,
    ATTR_DRAINING_AVAILABLE,
    ATTR_DUST_COLLECTION_AVAILABLE,
    ATTR_ROOMS,
    ATTR_CURRENT_SEGMENT,
    ATTR_SELECTED_MAP,
    ATTR_SELECTED_MAP_ID,
    ATTR_SELECTED_MAP_INDEX,
    ATTR_ID,
    ATTR_NAME,
    ATTR_ICON,
    ATTR_ORDER,
    ATTR_STATUS,
    ATTR_DID,
    ATTR_CLEANING_MODE,
    ATTR_SUCTION_LEVEL,
    ATTR_WATER_TANK,
    ATTR_COMPLETED,
    ATTR_CLEANING_TIME,
    ATTR_TIMESTAMP,
    ATTR_CLEANED_AREA,
    ATTR_MOP_PAD_HUMIDITY,
    ATTR_WASHING_MODE,
    ATTR_SELF_CLEAN_AREA,
    ATTR_PREVIOUS_SELF_CLEAN_AREA,
    ATTR_SELF_CLEAN_AREA_MIN,
    ATTR_SELF_CLEAN_AREA_MAX,
    ATTR_SELF_CLEAN_TIME,
    ATTR_PREVIOUS_SELF_CLEAN_TIME,
    ATTR_SELF_CLEAN_TIME_MIN,
    ATTR_SELF_CLEAN_TIME_MAX,
    ATTR_MOP_CLEAN_FREQUENCY,
    ATTR_MOP_PAD,
    ATTR_WASHING,
    ATTR_WASHING_PAUSED,
    ATTR_DRYING,
    ATTR_DRAINING,
    ATTR_OFF_PEAK_CHARGING,
    ATTR_OFF_PEAK_CHARGING_START,
    ATTR_OFF_PEAK_CHARGING_END,
    ATTR_CLEANGENIUS,
    ATTR_LOW_WATER,
    ATTR_CRUISING_TIME,
    ATTR_CRUISING_TYPE,
    ATTR_MAP_INDEX,
    ATTR_MAP_NAME,
    ATTR_NEGLECTED_SEGMENTS,
    ATTR_INTERRUPT_REASON,
    ATTR_MULTIPLE_CLEANING_TIME,
    ATTR_CLEANUP_METHOD,
    ATTR_SEGMENT_CLEANING,
    ATTR_ZONE_CLEANING,
    ATTR_SPOT_CLEANING,
    ATTR_CRUSING,
    ATTR_HAS_SAVED_MAP,
    ATTR_HAS_TEMPORARY_MAP,
    ATTR_AUTO_EMPTY_MODE,
    ATTR_CARPET_AVOIDANCE,
    ATTR_FLOOR_DIRECTION_CLEANING_AVAILABLE,
    ATTR_SHORTCUT_TASK,
    ATTR_FIRMWARE_VERSION,
    ATTR_AP,
    ATTR_CAPABILITIES,
)
from .resources import ERROR_IMAGE
from .exceptions import (
    DeviceUpdateFailedException,
    InvalidActionException,
    InvalidValueException,
)
from .protocol import DreameVacuumProtocol
from .map import DreameMapVacuumMapManager, DreameVacuumMapDecoder

_LOGGER = logging.getLogger(__name__)


class DreameVacuumDevice:
    """Support for Dreame Vacuum"""

    property_mapping: dict[DreameVacuumProperty, dict[str, int]] = DreameVacuumPropertyMapping
    action_mapping: dict[DreameVacuumAction, dict[str, int]] = DreameVacuumActionMapping

    def __init__(
        self,
        name: str,
        host: str,
        token: str,
        mac: str = None,
        username: str = None,
        password: str = None,
        country: str = None,
        prefer_cloud: bool = False,
        account_type: str = "mi",
        device_id: str = None,
        auth_key: str = None,
    ) -> None:
        # Used for easy filtering the device from cloud device list and generating unique ids
        self.info = None
        self.mac: str = None
        self.token: str = None  # Local api token
        self.host: str = None  # IP address or host name of the device
        # Dictionary for storing the current property values
        self.data: dict[DreameVacuumProperty, Any] = {}
        self.auto_switch_data: dict[DreameVacuumAutoSwitchProperty, Any] = None
        self.ai_data: dict[DreameVacuumStrAIProperty | DreameVacuumAIProperty, Any] = None
        self.available: bool = False  # Last update is successful or not
        self.disconnected: bool = False

        self._update_running: bool = False  # Update is running
        # Previous cleaning mode for restoring it after water tank is installed or removed
        self._previous_cleaning_mode: DreameVacuumCleaningMode = None
        self._previous_cleangenius: int = None
        # Device do not request properties that returned -1 as result. This property used for overriding that behavior at first connection
        self._ready: bool = False
        # Last settings properties requested time
        self._last_settings_request: float = 0
        self._last_map_list_request: float = 0  # Last map list property requested time
        self._last_map_request: float = 0  # Last map request trigger time
        self._last_change: float = 0  # Last property change time
        self._last_update_failed: float = 0  # Last update failed time
        self._cleaning_history_update: float = 0  # Cleaning history update time
        self._update_fail_count: int = 0  # Update failed counter
        self._draining_complete_time: int = None
        self._map_select_time: float = None
        self._last_map_change_time: float = None
        # Map Manager object. Only available when cloud connection is present
        self._map_manager: DreameMapVacuumMapManager = None
        self._update_callback = None  # External update callback for device
        self._error_callback = None  # External update failed callback
        # External update callbacks for specific device property
        self._property_update_callback = {}
        self._update_timer: Timer = None  # Update schedule timer
        self._callback_timer: Timer = None  # Update listener debouncing timer
        # Used for requesting consumable properties after reset action otherwise they will only requested when cleaning completed
        self._consumable_change: bool = False
        self._remote_control: bool = False
        self._dirty_data: dict[DreameVacuumProperty, DirtyData] = {}
        self._dirty_auto_switch_data: dict[DreameVacuumAutoSwitchProperty, DirtyData] = {}
        self._dirty_ai_data: dict[DreameVacuumStrAIProperty | DreameVacuumAIProperty, Any] = None
        self._discard_timeout = 5
        self._restore_timeout = 15

        self._name = name
        self.mac = mac
        self.token = token
        self.host = host
        self.auth_failed = False
        self.account_type = account_type
        self.status = DreameVacuumDeviceStatus(self)
        self.capability = DreameVacuumDeviceCapability(self)

        # Remove write only and response only properties from default list
        self._default_properties = list(
            set([prop for prop in DreameVacuumProperty])
            - set(
                [
                    DreameVacuumProperty.SCHEDULE_ID,
                    DreameVacuumProperty.REMOTE_CONTROL,
                    DreameVacuumProperty.VOICE_CHANGE,
                    DreameVacuumProperty.VOICE_CHANGE_STATUS,
                    DreameVacuumProperty.MAP_RECOVERY,
                    DreameVacuumProperty.CLEANING_START_TIME,
                    DreameVacuumProperty.CLEAN_LOG_FILE_NAME,
                    DreameVacuumProperty.CLEANING_PROPERTIES,
                    DreameVacuumProperty.CLEAN_LOG_STATUS,
                    DreameVacuumProperty.MAP_INDEX,
                    DreameVacuumProperty.MAP_NAME,
                    DreameVacuumProperty.CRUISE_TYPE,
                    DreameVacuumProperty.MAP_DATA,
                    DreameVacuumProperty.FRAME_INFO,
                    DreameVacuumProperty.OBJECT_NAME,
                    DreameVacuumProperty.MAP_EXTEND_DATA,
                    DreameVacuumProperty.ROBOT_TIME,
                    DreameVacuumProperty.RESULT_CODE,
                    DreameVacuumProperty.OLD_MAP_DATA,
                    DreameVacuumProperty.FACTORY_TEST_STATUS,
                    DreameVacuumProperty.FACTORY_TEST_RESULT,
                    DreameVacuumProperty.SELF_TEST_STATUS,
                    DreameVacuumProperty.LSD_TEST_STATUS,
                    DreameVacuumProperty.DEBUG_SWITCH,
                    DreameVacuumProperty.SERIAL,
                    DreameVacuumProperty.CALIBRATION_STATUS,
                    DreameVacuumProperty.VERSION,
                    DreameVacuumProperty.PERFORMANCE_SWITCH,
                    DreameVacuumProperty.AI_TEST_STATUS,
                    DreameVacuumProperty.PUBLIC_KEY,
                    DreameVacuumProperty.AUTO_PAIR,
                    DreameVacuumProperty.MCU_VERSION,
                    DreameVacuumProperty.MOP_TEST_STATUS,
                    DreameVacuumProperty.PLATFORM_NETWORK,
                    DreameVacuumProperty.TAKE_PHOTO,
                    DreameVacuumProperty.STEAM_HUMAN_FOLLOW,
                    DreameVacuumProperty.STREAM_KEEP_ALIVE,
                    DreameVacuumProperty.STREAM_UPLOAD,
                    DreameVacuumProperty.STREAM_AUDIO,
                    DreameVacuumProperty.STREAM_RECORD,
                    DreameVacuumProperty.STREAM_CODE,
                    DreameVacuumProperty.STREAM_SET_CODE,
                    DreameVacuumProperty.STREAM_VERIFY_CODE,
                    DreameVacuumProperty.STREAM_RESET_CODE,
                    DreameVacuumProperty.STREAM_CRUISE_POINT,
                    DreameVacuumProperty.STREAM_FAULT,
                    DreameVacuumProperty.STREAM_TASK,
                ]
            )
        )
        self._discarded_properties = [
            DreameVacuumProperty.ERROR,
            DreameVacuumProperty.STATE,
            DreameVacuumProperty.STATUS,
            DreameVacuumProperty.TASK_STATUS,
            DreameVacuumProperty.AUTO_EMPTY_STATUS,
            DreameVacuumProperty.ERROR,
            DreameVacuumProperty.SELF_WASH_BASE_STATUS,
            DreameVacuumProperty.AUTO_SWITCH_SETTINGS,
            DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS,
            DreameVacuumProperty.AI_DETECTION,
            DreameVacuumProperty.SHORTCUTS,
            DreameVacuumProperty.MAP_BACKUP_STATUS,
            DreameVacuumProperty.MAP_RECOVERY_STATUS,
            DreameVacuumProperty.OFF_PEAK_CHARGING,
            DreameVacuumProperty.SCHEDULE,
        ]
        self._read_write_properties = [
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
            DreameVacuumProperty.AUTO_LDS_LIFTING,
            DreameVacuumProperty.MOP_WASHING_WITH_DETERGENT,
        ]

        self.listen(self._task_status_changed, DreameVacuumProperty.TASK_STATUS)
        self.listen(self._status_changed, DreameVacuumProperty.STATUS)
        self.listen(self._charging_status_changed, DreameVacuumProperty.CHARGING_STATUS)
        self.listen(self._cleaning_mode_changed, DreameVacuumProperty.CLEANING_MODE)
        self.listen(self._water_tank_changed, DreameVacuumProperty.WATER_TANK)
        self.listen(self._water_tank_changed, DreameVacuumProperty.MOP_PAD_INSTALLED)
        self.listen(self._water_tank_changed, DreameVacuumProperty.MOP_IN_STATION)
        self.listen(self._auto_mount_mop_changed, DreameVacuumProperty.AUTO_MOUNT_MOP)
        self.listen(self._ai_obstacle_detection_changed, DreameVacuumProperty.AI_DETECTION)
        self.listen(
            self._auto_switch_settings_changed,
            DreameVacuumProperty.AUTO_SWITCH_SETTINGS,
        )
        self.listen(self._dnd_task_changed, DreameVacuumProperty.DND_TASK)
        self.listen(self._schedule_changed, DreameVacuumProperty.SCHEDULE)
        self.listen(self._stream_status_changed, DreameVacuumProperty.STREAM_STATUS)
        self.listen(self._shortcuts_changed, DreameVacuumProperty.SHORTCUTS)
        self.listen(
            self._voice_assistant_language_changed,
            DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE,
        )
        self.listen(self._drainage_status_changed, DreameVacuumProperty.DRAINAGE_STATUS)
        self.listen(
            self._self_wash_base_status_changed,
            DreameVacuumProperty.SELF_WASH_BASE_STATUS,
        )
        self.listen(self._off_peak_charging_changed, DreameVacuumProperty.OFF_PEAK_CHARGING)
        self.listen(self._suction_level_changed, DreameVacuumProperty.SUCTION_LEVEL)
        self.listen(self._water_volume_changed, DreameVacuumProperty.WATER_VOLUME)
        self.listen(self._wetness_level_changed, DreameVacuumProperty.WETNESS_LEVEL)
        self.listen(self._error_changed, DreameVacuumProperty.ERROR)
        self.listen(
            self._map_recovery_status_changed,
            DreameVacuumProperty.MAP_RECOVERY_STATUS,
        )

        self._protocol = DreameVacuumProtocol(
            self.host,
            self.token,
            username,
            password,
            country,
            prefer_cloud,
            account_type,
            device_id,
            auth_key,
        )
        if self._protocol.cloud:
            self._map_manager = DreameMapVacuumMapManager(self._protocol)

            self.listen(self._map_list_changed, DreameVacuumProperty.MAP_LIST)
            self.listen(self._recovery_map_list_changed, DreameVacuumProperty.RECOVERY_MAP_LIST)
            self.listen(self._battery_level_changed, DreameVacuumProperty.BATTERY_LEVEL)
            self.listen(self._map_property_changed, DreameVacuumProperty.CUSTOMIZED_CLEANING)
            self.listen(self._map_property_changed, DreameVacuumProperty.STATE)
            self.listen(self._map_property_changed, DreameVacuumProperty.AUTO_EMPTY_STATUS)
            self.listen(
                self._map_backup_status_changed,
                DreameVacuumProperty.MAP_BACKUP_STATUS,
            )
            self._map_manager.listen(self._map_changed, self._map_updated)
            self._map_manager.listen_error(self._update_failed)

    def _connected_callback(self):
        if not self._ready:
            return
        _LOGGER.info("Requesting properties after connect")
        self.available = True
        self.schedule_update(2, True)
        self._property_changed()

    def _message_callback(self, message):
        if not self._ready:
            return

        _LOGGER.debug("Message Callback: %s", message)

        if "method" in message and "params" in message:
            self.available = True
            method = message["method"]
            params = message["params"]
            if method == "properties_changed":
                properties = []
                map_properties = []
                for param in params:
                    prop = DID(param["siid"], param["piid"])
                    if prop is not None:
                        if prop in self._default_properties:
                            param["did"] = str(prop.value)
                            param["code"] = 0
                            properties.append(param)
                            continue

                        if (
                            prop is DreameVacuumProperty.OBJECT_NAME
                            or prop is DreameVacuumProperty.MAP_DATA
                            or prop is DreameVacuumProperty.ROBOT_TIME
                            or prop is DreameVacuumProperty.OLD_MAP_DATA
                        ):
                            map_properties.append(param)

                if len(map_properties) and self._map_manager:
                    self._map_manager.handle_properties(map_properties)

                self._handle_properties(properties)
            elif method == "_otc.info":
                info = DreameVacuumDeviceInfo(params)
                if info != self.info:
                    self.info = info
                    self._last_change = time.time()
                    if self._ready:
                        self._property_changed()

    def _handle_properties(self, properties) -> bool:
        changed = False
        callbacks = []
        for prop in properties:
            if not isinstance(prop, dict):
                continue
            did = int(prop["did"])
            if did not in DreameVacuumProperty._value2member_map_:
                did = DID(prop["siid"], prop["piid"])
                if did is None:
                    continue
                did = int(did.value)
            if prop["code"] == 0 and "value" in prop:
                value = prop["value"]
                if did in self._dirty_data:
                    if (
                        self._dirty_data[did].value != value
                        and time.time() - self._dirty_data[did].update_time < self._discard_timeout
                    ):
                        _LOGGER.info(
                            "Property %s Value Discarded: %s <- %s",
                            DreameVacuumProperty(did).name,
                            self._dirty_data[did].value,
                            value,
                        )
                        del self._dirty_data[did]
                        continue
                    del self._dirty_data[did]

                current_value = self.data.get(did)
                if current_value != value:
                    # Do not call external listener when map and json properties changed
                    if not (
                        did == DreameVacuumProperty.MAP_LIST.value
                        or did == DreameVacuumProperty.RECOVERY_MAP_LIST.value
                        or did == DreameVacuumProperty.MAP_DATA.value
                        or did == DreameVacuumProperty.OBJECT_NAME.value
                        or did == DreameVacuumProperty.AUTO_SWITCH_SETTINGS.value
                        or did == DreameVacuumProperty.AI_DETECTION.value
                        # or did == DreameVacuumProperty.SELF_TEST_STATUS.value
                    ):
                        changed = True
                    custom_property = (
                        did == DreameVacuumProperty.AUTO_SWITCH_SETTINGS.value
                        or did == DreameVacuumProperty.AI_DETECTION.value
                        or did == DreameVacuumProperty.MAP_LIST.value
                        or did == DreameVacuumProperty.SERIAL_NUMBER.value
                    )
                    if not custom_property:
                        if current_value is not None:
                            _LOGGER.info(
                                "Property %s Changed: %s -> %s",
                                DreameVacuumProperty(did).name,
                                current_value,
                                value,
                            )
                        else:
                            _LOGGER.info(
                                "Property %s Added: %s",
                                DreameVacuumProperty(did).name,
                                value,
                            )
                    self.data[did] = value
                    if did in self._property_update_callback:
                        for callback in self._property_update_callback[did]:
                            if not self._ready and custom_property:
                                callback(current_value)
                            else:
                                callbacks.append([callback, current_value])
            else:
                _LOGGER.debug("Property %s Not Available", DreameVacuumProperty(did).name)

        if not self._ready:
            self.capability.load(json.loads(zlib.decompress(base64.b64decode(DEVICE_INFO), zlib.MAX_WBITS | 32)))

        for callback in callbacks:
            callback[0](callback[1])

        if changed:
            self._last_change = time.time()
            if self._ready:
                self._property_changed()

        if not self._ready:
            if self._protocol.dreame_cloud:
                self._discard_timeout = 5

            if self.capability.self_wash_base:
                if self.capability.mop_clean_frequency:
                    self.status.self_clean_area_min = 5
                    self.status.self_clean_area_max = 10
                    self.status.self_clean_area_default = 8
                elif self.capability.small_self_clean_area:
                    self.status.self_clean_area_min = 5
                    self.status.self_clean_area_max = 15
                    self.status.self_clean_area_default = 15
                else:
                    self.status.self_clean_area_max = 35 if self.capability.cleaning_route else 30

            self.status.previous_self_clean_area = (
                self.status.self_clean_value if self.status.self_clean_value else self.status.self_clean_area_default
            )
            self.status.previous_self_clean_time = (
                self.status.self_clean_value
                if self.status.self_clean_value and self.status.self_clean_by_time
                else self.status.self_clean_time_default
            )

            if self.capability.mop_clean_frequency:
                if MOP_WASH_LEVEL_WATER_SAVING in self.status.mop_wash_level_list:
                    self.status.mop_wash_level_list.pop(MOP_WASH_LEVEL_WATER_SAVING)

                if self.capability.mop_pad_swing:
                    if MOP_CLEAN_FREQUENCY_EIGHT_SQUARE_METERS in self.status.mop_clean_frequency_list:
                        self.status.mop_clean_frequency_list.pop(MOP_CLEAN_FREQUENCY_EIGHT_SQUARE_METERS)
                    if MOP_CLEAN_FREQUENCY_FIVE_SQUARE_METERS in self.status.mop_clean_frequency_list:
                        self.status.mop_clean_frequency_list.pop(MOP_CLEAN_FREQUENCY_FIVE_SQUARE_METERS)
                else:
                    if MOP_CLEAN_FREQUENCY_BY_ROOM in self.status.mop_clean_frequency_list:
                        self.status.mop_clean_frequency_list.pop(MOP_CLEAN_FREQUENCY_BY_ROOM)
                    if MOP_CLEAN_FREQUENCY_FIFTEEN_SQUARE_METERS in self.status.mop_clean_frequency_list:
                        self.status.mop_clean_frequency_list.pop(MOP_CLEAN_FREQUENCY_FIFTEEN_SQUARE_METERS)
                    if MOP_CLEAN_FREQUENCY_TWENTY_SQUARE_METERS in self.status.mop_clean_frequency_list:
                        self.status.mop_clean_frequency_list.pop(MOP_CLEAN_FREQUENCY_TWENTY_SQUARE_METERS)
                    if MOP_CLEAN_FREQUENCY_TWENTYFIVE_SQUARE_METERS in self.status.mop_clean_frequency_list:
                        self.status.mop_clean_frequency_list.pop(MOP_CLEAN_FREQUENCY_TWENTYFIVE_SQUARE_METERS)

            if (
                self.capability.smart_mop_washing
                and not self.capability.ultra_clean_mode
                and WASHING_MODE_ULTRA_WASHING in self.status.washing_mode_list
            ):
                self.status.washing_mode_list.pop(WASHING_MODE_ULTRA_WASHING)

            if (
                not self.capability.mopping_after_sweeping
                and CLEANING_MODE_MOPPING_AFTER_SWEEPING in self.status.cleaning_mode_list
            ):
                self.status.cleaning_mode_list.pop(CLEANING_MODE_MOPPING_AFTER_SWEEPING)

            if (
                not self.capability.mop_pad_lifting_plus
                or self.capability.auto_carpet_cleaning
                or self.capability.carpet_crossing
            ) and CARPET_CLEANING_ADAPTATION_WITHOUT_ROUTE in self.status.carpet_cleaning_list:
                self.status.carpet_cleaning_list.pop(CARPET_CLEANING_ADAPTATION_WITHOUT_ROUTE)

            if (
                not self.capability.auto_carpet_cleaning or self.capability.carpet_crossing
            ) and CARPET_CLEANING_VACUUM_AND_MOP in self.status.carpet_cleaning_list:
                self.status.carpet_cleaning_list.pop(CARPET_CLEANING_VACUUM_AND_MOP)

            if (
                not self.capability.mop_pad_unmounting
            ) and CARPET_CLEANING_REMOVE_MOP in self.status.carpet_cleaning_list:
                self.status.carpet_cleaning_list.pop(CARPET_CLEANING_REMOVE_MOP)

            if (
                not self.capability.mop_pad_lifting_plus and not self.capability.auto_carpet_cleaning
            ) and CARPET_CLEANING_IGNORE in self.status.carpet_cleaning_list:
                self.status.carpet_cleaning_list.pop(CARPET_CLEANING_IGNORE)

            if not self.capability.carpet_crossing and CARPET_CLEANING_CROSS in self.status.carpet_cleaning_list:
                self.status.carpet_cleaning_list.pop(CARPET_CLEANING_CROSS)

            if (
                not (self.capability.carpet_material and self.capability.carpet_type)
                and FLOOR_MATERIAL_CARPET in self.status.floor_material_list
            ):
                self.status.floor_material_list.pop(FLOOR_MATERIAL_MEDIUM_PILE_CARPET)
                self.status.floor_material_list.pop(FLOOR_MATERIAL_LOW_PILE_CARPET)
                self.status.floor_material_list.pop(FLOOR_MATERIAL_CARPET)

            self.status.segment_cleaning_mode_list = self.status.cleaning_mode_list.copy()
            if CLEANING_MODE_MOPPING_AFTER_SWEEPING in self.status.segment_cleaning_mode_list:
                self.status.segment_cleaning_mode_list.pop(CLEANING_MODE_MOPPING_AFTER_SWEEPING)

            if self.capability.cleaning_route:
                if (
                    self.status.cleaning_mode == DreameVacuumCleaningMode.SWEEPING
                    or self.status.cleaning_mode == DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                ):
                    new_list = CLEANING_ROUTE_TO_NAME.copy()
                    new_list.pop(DreameVacuumCleaningRoute.DEEP)
                    new_list.pop(DreameVacuumCleaningRoute.INTENSIVE)
                    self.status.cleaning_route_list = {v: k for k, v in new_list.items()}
                    new_list = CLEANING_ROUTE_TO_NAME.copy()
                    if self.capability.segment_slow_clean_route:
                        new_list.pop(DreameVacuumCleaningRoute.QUICK)
                    self.status.segment_cleaning_route_list = {v: k for k, v in new_list.items()}

            for p in dir(self.capability):
                if not p.startswith("__") and not callable(getattr(self.capability, p)):
                    val = getattr(self.capability, p)
                    if isinstance(val, bool) and val:
                        _LOGGER.info("Capability %s", p.upper())

        return changed

    def _request_properties(self, properties: list[DreameVacuumProperty] = None) -> bool:
        """Request properties from the device."""
        if not properties:
            properties = self._default_properties

        property_list = []
        for prop in properties:
            if prop in self.property_mapping:
                mapping = self.property_mapping[prop]
                # Do not include properties that are not exists on the device
                if "aiid" not in mapping and (not self._ready or prop.value in self.data):
                    property_list.append({"did": str(prop.value), **mapping})

        props = property_list.copy()
        results = []
        while props:
            result = self._protocol.get_properties(props[:15])
            if result is not None:
                results.extend(result)
                props[:] = props[15:]

        return self._handle_properties(results)

    def _update_status(self, task_status: DreameVacuumTaskStatus, status: DreameVacuumStatus) -> None:
        """Update status properties on memory for map renderer to update the image before action is sent to the device."""
        if task_status is not DreameVacuumTaskStatus.COMPLETED:
            new_state = DreameVacuumState.SWEEPING
            if self.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING:
                new_state = DreameVacuumState.MOPPING
            elif self.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING_AND_MOPPING:
                new_state = DreameVacuumState.SWEEPING_AND_MOPPING
            self._update_property(DreameVacuumProperty.STATE, new_state.value)

        self._update_property(DreameVacuumProperty.STATUS, status.value)
        self._update_property(DreameVacuumProperty.TASK_STATUS, task_status.value)

    def _update_property(self, prop: DreameVacuumProperty, value: Any, delay=True) -> Any:
        """Update device property on memory and notify listeners."""
        if prop in self.property_mapping:
            if (
                not self.capability.new_state
                and prop == DreameVacuumProperty.STATE
                and int(value) > 18
                and value in DreameVacuumState._value2member_map_
            ):
                old_state = DreameVacuumStateOld[DreameVacuumState(value).name]
                if old_state:
                    value = int(old_state)

            current_value = self.get_property(prop)
            if current_value != value:
                did = prop.value
                self.data[did] = value
                if did in self._property_update_callback:
                    for callback in self._property_update_callback[did]:
                        callback(current_value)

                if (
                    prop != DreameVacuumProperty.CUSTOMIZED_CLEANING
                    and prop != DreameVacuumProperty.STATE
                    and prop != DreameVacuumProperty.AUTO_EMPTY_STATUS
                ):
                    self._property_changed(delay)
                return current_value if current_value is not None else value
        return None

    def _map_property_changed(self, previous_property: Any = None) -> None:
        """Update last update time of the map when a property associated with rendering map changed."""
        if self._map_manager and previous_property is not None:
            self._map_manager.editor.refresh_map()

    def _map_list_changed(self, previous_map_list: Any = None) -> None:
        """Update map list object name on map manager map list property when changed"""
        if self._map_manager:
            map_list = self.get_property(DreameVacuumProperty.MAP_LIST)
            if map_list and map_list != "":
                try:
                    map_list = json.loads(map_list)
                    object_name = map_list.get("object_name")
                    if object_name is None:
                        object_name = map_list.get("obj_name")
                    if object_name and object_name != "":
                        _LOGGER.info("Property MAP_LIST Changed: %s", object_name)
                        self._map_manager.set_map_list_object_name(object_name, map_list.get("md5"))
                    else:
                        self._last_map_list_request = 0
                except:
                    pass

    def _recovery_map_list_changed(self, previous_recovery_map_list: Any = None) -> None:
        """Update recovery list object name on map manager recovery list property when changed"""
        if self._map_manager:
            map_list = self.get_property(DreameVacuumProperty.RECOVERY_MAP_LIST)
            if map_list and map_list != "":
                try:
                    map_list = json.loads(map_list)
                    object_name = map_list.get("object_name")
                    if object_name is None:
                        object_name = map_list.get("obj_name")
                    if object_name and object_name != "":
                        self._map_manager.set_recovery_map_list_object_name(object_name)
                    else:
                        self._last_map_list_request = 0
                except:
                    pass

    def _map_recovery_status_changed(self, previous_map_recovery_status: Any = None) -> None:
        if previous_map_recovery_status and self.status.map_recovery_status:
            if self.status.map_recovery_status == DreameVacuumMapRecoveryStatus.SUCCESS.value:
                if not self._protocol.dreame_cloud:
                    self._last_map_list_request = 0
                self._last_map_change_time = time.time()
                self._map_manager.request_next_map()
                self._map_manager.request_next_recovery_map_list()

            if self.status.map_recovery_status != DreameVacuumMapRecoveryStatus.RUNNING.value:
                self._request_properties([DreameVacuumProperty.MAP_RECOVERY_STATUS])

    def _map_backup_status_changed(self, previous_map_backup_status: Any = None) -> None:
        if previous_map_backup_status and self.status.map_backup_status:
            if self.status.map_backup_status == DreameVacuumMapBackupStatus.SUCCESS.value:
                if not self._protocol.dreame_cloud:
                    self._last_map_list_request = 0
                self._last_map_change_time = time.time()
                self._map_manager.request_next_recovery_map_list()
            if self.status.map_backup_status != DreameVacuumMapBackupStatus.RUNNING.value:
                self._request_properties([DreameVacuumProperty.MAP_BACKUP_STATUS])

    def _cleaning_mode_changed(self, previous_cleaning_mode: Any = None) -> None:
        value = self.get_property(DreameVacuumProperty.CLEANING_MODE)
        new_cleaning_mode = None
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(value, self.capability.mop_pad_lifting)
            if values and len(values) == 3:
                if (
                    self.status.self_clean_value != values[1]
                    and values[1] > 0
                    and (self.status.wetness_level is None or self.status.wetness_level < 27)
                ):
                    if self.status.self_clean_by_time:
                        self.status.previous_self_clean_time = values[1]
                    else:
                        self.status.previous_self_clean_area = values[1]
                self.status.self_clean_value = values[1]
                if not self.capability.wetness or values[2] != 0:
                    if values[2] <= 0:
                        if self.capability.custom_mopping_route:
                            if not self.status.custom_mopping_mode:
                                values[2] = self.get_auto_switch_property(DreameVacuumAutoSwitchProperty.MOPPING_MODE)
                        elif self.status.water_volume:
                            values[2] = self.status.water_volume.value

                    if (
                        values[2] > 0
                        and values[2] is not None
                        and values[2] in DreameVacuumMopPadHumidity._value2member_map_
                    ):
                        self.status.mop_pad_humidity = values[2]
                if values[0] == 3:
                    new_cleaning_mode = DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
                elif not self.capability.mop_pad_lifting:
                    if not self.status.water_tank_or_mop_installed:
                        new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING
                    elif values[0] == 1:
                        new_cleaning_mode = DreameVacuumCleaningMode.MOPPING
                    else:
                        new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                else:
                    if values[0] == 2:
                        new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING
                    elif values[0] == 0:
                        new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                    elif values[0] in DreameVacuumCleaningMode._value2member_map_:
                        new_cleaning_mode = DreameVacuumCleaningMode(values[0])
        elif self.capability.mop_pad_lifting:
            if value == 3:
                new_cleaning_mode = DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
            elif value == 2:
                new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING
            elif value == 0:
                new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING_AND_MOPPING

        if new_cleaning_mode is None:
            if value in DreameVacuumCleaningMode._value2member_map_:
                new_cleaning_mode = DreameVacuumCleaningMode(value)
            else:
                new_cleaning_mode = DreameVacuumCleaningMode.UNKNOWN

        if previous_cleaning_mode is not None and self.status.go_to_zone:
            self.status.go_to_zone.cleaning_mode = None
            self.status.go_to_zone.water_level = None

        if self.status.cleaning_mode != new_cleaning_mode:
            self.status.cleaning_mode = new_cleaning_mode

            if self._ready and self.capability.cleaning_route:
                new_list = CLEANING_ROUTE_TO_NAME.copy()
                if (
                    self.status.cleaning_mode == DreameVacuumCleaningMode.SWEEPING
                    or self.status.cleaning_mode == DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                ):
                    new_list.pop(DreameVacuumCleaningRoute.DEEP)
                    new_list.pop(DreameVacuumCleaningRoute.INTENSIVE)
                self.status.cleaning_route_list = {v: k for k, v in new_list.items()}

                if self.status.cleaning_route and self.status.cleaning_route not in self.status.cleaning_route_list:
                    self.set_auto_switch_property(
                        DreameVacuumAutoSwitchProperty.CLEANING_ROUTE,
                        DreameVacuumCleaningRoute.STANDARD.value,
                    )

    def _water_tank_changed(self, previous_water_tank: Any = None) -> None:
        """Update cleaning mode on device when water tank status is changed."""
        # App does not allow you to update cleaning mode when water tank or mop pad is not installed.
        if self.get_property(DreameVacuumProperty.CLEANING_MODE) is not None:
            new_list = CLEANING_MODE_CODE_TO_NAME.copy()
            if not self.capability.mopping_after_sweeping or (
                self.status.started
                and self.status.cleaning_mode is not DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
            ):
                new_list.pop(DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING)

            if not self.capability.embedded_tank and (
                not self.status.auto_mount_mop or not self.status.mop_in_station
            ):
                try:
                    if not self.status.water_tank_or_mop_installed:
                        new_list.pop(DreameVacuumCleaningMode.MOPPING)
                        new_list.pop(DreameVacuumCleaningMode.SWEEPING_AND_MOPPING)
                        if DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING in new_list:
                            new_list.pop(DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING)
                        if self.status.cleaning_mode is not DreameVacuumCleaningMode.SWEEPING:
                            # Store current cleaning mode for future use when water tank is reinstalled
                            self._previous_cleaning_mode = self.status.cleaning_mode
                            if self._ready and not self.status.scheduled_clean and not self.status.shortcut_task:
                                try:
                                    self._update_cleaning_mode(DreameVacuumCleaningMode.SWEEPING.value)
                                except:
                                    pass
                    elif not self.capability.mop_pad_lifting:
                        new_list.pop(DreameVacuumCleaningMode.SWEEPING)
                        if DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING in new_list:
                            new_list.pop(DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING)
                        if self.status.sweeping:
                            if self._ready and not self.status.scheduled_clean and not self.status.shortcut_task:
                                if (
                                    self._previous_cleaning_mode is not None
                                    and self._previous_cleaning_mode is not DreameVacuumCleaningMode.SWEEPING
                                ):
                                    self._update_cleaning_mode(self._previous_cleaning_mode.value)
                                else:
                                    self._update_cleaning_mode(DreameVacuumCleaningMode.SWEEPING_AND_MOPPING.value)
                            # Store current cleaning mode for future use when water tank is removed
                            self._previous_cleaning_mode = self.status.cleaning_mode
                except:
                    pass

            self.status.cleaning_mode_list = {v: k for k, v in new_list.items()}

    def _auto_mount_mop_changed(self, previous_auto_mount_mop: Any = None) -> None:
        if previous_auto_mount_mop is not None:
            carpet_cleaning_list = CARPET_CLEANING_CODE_TO_NAME.copy()
            if not self.status.auto_mount_mop:
                carpet_cleaning_list.pop(DreameVacuumCarpetCleaning.REMOVE_MOP)
            self.status.carpet_cleaning_list = {v: k for k, v in carpet_cleaning_list.items()}

    def _task_status_changed(self, previous_task_status: Any = None) -> None:
        """Task status is a very important property and must be listened to trigger necessary actions when a task started or ended"""
        if previous_task_status is not None:
            if previous_task_status in DreameVacuumTaskStatus._value2member_map_:
                previous_task_status = DreameVacuumTaskStatus(previous_task_status)

            task_status = self.get_property(DreameVacuumProperty.TASK_STATUS)
            if task_status in DreameVacuumTaskStatus._value2member_map_:
                task_status = DreameVacuumTaskStatus(task_status)

            if self._map_manager is not None:
                # Update map data for renderer to update the map image according to the new task status
                if previous_task_status is DreameVacuumTaskStatus.COMPLETED:
                    if (
                        task_status is DreameVacuumTaskStatus.AUTO_CLEANING
                        or task_status is DreameVacuumTaskStatus.ZONE_CLEANING
                        or task_status is DreameVacuumTaskStatus.SEGMENT_CLEANING
                        or task_status is DreameVacuumTaskStatus.SPOT_CLEANING
                        or task_status is DreameVacuumTaskStatus.CRUISING_PATH
                        or task_status is DreameVacuumTaskStatus.CRUISING_POINT
                    ):
                        # Clear path on current map on cleaning start as implemented on the app
                        self._map_manager.editor.clear_path()
                    elif task_status is DreameVacuumTaskStatus.FAST_MAPPING:
                        # Clear current map on mapping start as implemented on the app
                        self._map_manager.editor.reset_map()
                    else:
                        self._map_manager.editor.refresh_map()
                else:
                    self._map_manager.editor.refresh_map()

            if task_status is DreameVacuumTaskStatus.COMPLETED:
                if (
                    previous_task_status is DreameVacuumTaskStatus.CRUISING_PATH
                    or previous_task_status is DreameVacuumTaskStatus.CRUISING_POINT
                    or self.status.go_to_zone
                ):
                    if self._map_manager is not None:
                        # Get the new map list from cloud
                        self._map_manager.editor.set_cruise_points([])
                        self._map_manager.request_next_map_list()
                    self._cleaning_history_update = time.time()
                elif previous_task_status is DreameVacuumTaskStatus.FAST_MAPPING:
                    # as implemented on the app
                    self._update_property(DreameVacuumProperty.CLEANING_TIME, 0)
                    if self._map_manager is not None:
                        # Mapping is completed, get the new map list from cloud
                        self._map_manager.request_next_map_list()
                elif (
                    self.status.cleanup_started
                    and not self.status.cleanup_completed
                    and (self.status.status is DreameVacuumStatus.BACK_HOME or not self.status.running)
                ):
                    self.status.cleanup_started = False
                    self.status.cleanup_completed = True
                    self._cleaning_history_update = time.time()

                    if self._previous_cleangenius is not None:
                        self.set_auto_switch_property(
                            DreameVacuumAutoSwitchProperty.CLEANGENIUS, self._previous_cleangenius
                        )
                        self._previous_cleangenius = None
            else:
                self.status.cleanup_started = not (
                    self.status.fast_mapping
                    or self.status.cruising
                    or (
                        task_status is DreameVacuumTaskStatus.DOCKING_PAUSED
                        and previous_task_status is DreameVacuumTaskStatus.COMPLETED
                    )
                )
                self.status.cleanup_completed = False
                if self.status.cleanup_started:
                    if previous_task_status is DreameVacuumTaskStatus.COMPLETED:
                        # as implemented on the app
                        self._update_property(DreameVacuumProperty.CLEANING_TIME, 0)
                        self._update_property(DreameVacuumProperty.CLEANED_AREA, 0)

                    if (
                        task_status is not DreameVacuumTaskStatus.ZONE_CLEANING
                        and self._previous_cleangenius is not None
                    ):
                        self._previous_cleangenius = None

            if self.status.go_to_zone is not None and not (
                task_status is DreameVacuumTaskStatus.ZONE_CLEANING
                or task_status is DreameVacuumTaskStatus.ZONE_CLEANING_PAUSED
                or task_status is DreameVacuumTaskStatus.ZONE_MOPPING_PAUSED
                or task_status is DreameVacuumTaskStatus.ZONE_DOCKING_PAUSED
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT_PAUSED
            ):
                self._restore_go_to_zone()

            if self._map_manager:
                self._map_manager.editor.refresh_map()

            if (
                task_status is DreameVacuumTaskStatus.COMPLETED
                or previous_task_status is DreameVacuumTaskStatus.COMPLETED
            ):
                # Get properties that only changes when task status is changed
                properties = [
                    DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT,
                    DreameVacuumProperty.MAIN_BRUSH_LEFT,
                    DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT,
                    DreameVacuumProperty.SIDE_BRUSH_LEFT,
                    DreameVacuumProperty.FILTER_LEFT,
                    DreameVacuumProperty.FILTER_TIME_LEFT,
                    DreameVacuumProperty.TANK_FILTER_LEFT,
                    DreameVacuumProperty.TANK_FILTER_TIME_LEFT,
                    DreameVacuumProperty.MOP_PAD_LEFT,
                    DreameVacuumProperty.MOP_PAD_TIME_LEFT,
                    DreameVacuumProperty.SILVER_ION_TIME_LEFT,
                    DreameVacuumProperty.SILVER_ION_LEFT,
                    DreameVacuumProperty.DETERGENT_TIME_LEFT,
                    DreameVacuumProperty.DETERGENT_LEFT,
                    DreameVacuumProperty.SQUEEGEE_TIME_LEFT,
                    DreameVacuumProperty.SQUEEGEE_LEFT,
                    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT,
                    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT,
                    DreameVacuumProperty.DIRTY_WATER_TANK_TIME_LEFT,
                    DreameVacuumProperty.DIRTY_WATER_TANK_LEFT,
                    DreameVacuumProperty.DEODORIZER_TIME_LEFT,
                    DreameVacuumProperty.DEODORIZER_LEFT,
                    DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT,
                    DreameVacuumProperty.WHEEL_DIRTY_LEFT,
                    DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT,
                    DreameVacuumProperty.SCALE_INHIBITOR_LEFT,
                    DreameVacuumProperty.TOTAL_CLEANING_TIME,
                    DreameVacuumProperty.CLEANING_COUNT,
                    DreameVacuumProperty.TOTAL_CLEANED_AREA,
                    DreameVacuumProperty.TOTAL_RUNTIME,
                    DreameVacuumProperty.TOTAL_CRUISE_TIME,
                    DreameVacuumProperty.FIRST_CLEANING_DATE,
                    DreameVacuumProperty.SCHEDULE,
                    DreameVacuumProperty.SCHEDULE_CANCEL_REASON,
                    DreameVacuumProperty.CRUISE_SCHEDULE,
                ]

                if not self.capability.disable_sensor_cleaning:
                    properties.extend(
                        [
                            DreameVacuumProperty.SENSOR_DIRTY_LEFT,
                            DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
                        ]
                    )

                if self._map_manager is not None:
                    properties.extend(
                        [
                            DreameVacuumProperty.MAP_LIST,
                            DreameVacuumProperty.RECOVERY_MAP_LIST,
                        ]
                    )
                    self._last_map_list_request = time.time()

                try:
                    self._request_properties(properties)
                except Exception as ex:
                    pass

                if self._protocol.prefer_cloud and self._protocol.dreame_cloud:
                    self.schedule_update(1, True)

        if self.capability.mopping_after_sweeping:
            if self.status.started:
                if (
                    self.status.cleaning_mode is not DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
                    and CLEANING_MODE_MOPPING_AFTER_SWEEPING in self.status.cleaning_mode_list
                ):
                    self.status.cleaning_mode_list.pop(CLEANING_MODE_MOPPING_AFTER_SWEEPING)
                    self._property_changed(False)
            elif CLEANING_MODE_MOPPING_AFTER_SWEEPING not in self.status.cleaning_mode_list and (
                self.status.water_tank_or_mop_installed
            ):
                self.status.cleaning_mode_list[CLEANING_MODE_MOPPING_AFTER_SWEEPING] = (
                    DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
                )
                self._property_changed(False)

    def _status_changed(self, previous_status: Any = None) -> None:
        if previous_status is not None:
            if previous_status in DreameVacuumStatus._value2member_map_:
                previous_status = DreameVacuumStatus(previous_status)

            status = self.get_property(DreameVacuumProperty.STATUS)
            if (
                self._remote_control
                and status != DreameVacuumStatus.REMOTE_CONTROL.value
                and previous_status != DreameVacuumStatus.REMOTE_CONTROL.value
            ):
                self._remote_control = False

            if (
                not self.capability.cruising
                and status == DreameVacuumStatus.BACK_HOME
                and previous_status == DreameVacuumStatus.ZONE_CLEANING
                and self.status.started
            ):
                self.status.cleanup_started = False
                self.status.cleanup_completed = False
                self.status.go_to_zone.stop = True
                self._restore_go_to_zone(True)
            elif (
                not self.status.started
                and self.status.cleanup_started
                and not self.status.cleanup_completed
                and (self.status.status is DreameVacuumStatus.BACK_HOME or not self.status.running)
            ):
                self.status.cleanup_started = False
                self.status.cleanup_completed = True
                self._cleaning_history_update = time.time()

                if self._previous_cleangenius is not None:
                    self.set_auto_switch_property(
                        DreameVacuumAutoSwitchProperty.CLEANGENIUS, self._previous_cleangenius
                    )
                    self._previous_cleangenius = None

                did = DreameVacuumProperty.TASK_STATUS.value
                if did in self._property_update_callback:
                    for callback in self._property_update_callback[did]:
                        callback(self.status.task_status.value)
                self._property_changed(False)
            elif status == DreameVacuumStatus.CHARGING.value and previous_status == DreameVacuumStatus.BACK_HOME.value:
                self._cleaning_history_update = time.time()

            if previous_status == DreameVacuumStatus.OTA.value:
                self._ready = False
                self.connect_device()

            if self._map_manager:
                self._map_manager.editor.refresh_map()

    def _charging_status_changed(self, previous_charging_status: Any = None) -> None:
        self._remote_control = False
        if previous_charging_status is not None:
            if self._map_manager:
                self._map_manager.editor.refresh_map()

            if self._ready and self.capability.mop_pad_lifting:
                self._water_tank_changed()

            if (
                self._protocol.dreame_cloud
                and self.status.charging_status != DreameVacuumChargingStatus.CHARGING_COMPLETED
            ):
                self.schedule_update(2, True)

    def _ai_obstacle_detection_changed(self, previous_ai_obstacle_detection: Any = None) -> None:
        """AI Detection property returns multiple values as json or int this function parses and sets the sub properties to memory"""
        ai_value = self.get_property(DreameVacuumProperty.AI_DETECTION)
        changed = False
        if isinstance(ai_value, str):
            settings = json.loads(ai_value)
            if settings and self.ai_data is None:
                self.ai_data = {}

            for prop in DreameVacuumStrAIProperty:
                if prop.value in settings:
                    value = settings[prop.value]
                    if prop.value in self._dirty_ai_data:
                        if (
                            self._dirty_ai_data[prop.name].value != value
                            and time.time() - self._dirty_ai_data[prop.name].update_time < self._discard_timeout
                        ):
                            _LOGGER.info(
                                "AI Property %s Value Discarded: %s <- %s",
                                prop.name,
                                self._dirty_ai_data[prop.name].value,
                                value,
                            )
                            del self._dirty_ai_data[prop.name]
                            continue
                        del self._dirty_ai_data[prop.name]

                    current_value = self.ai_data.get(prop.name)
                    if current_value != value:
                        if current_value is not None:
                            _LOGGER.info(
                                "AI Property %s Changed: %s -> %s",
                                prop.name,
                                current_value,
                                value,
                            )
                            if (
                                prop == DreameVacuumStrAIProperty.AI_PET_DETECTION
                                or prop == DreameVacuumStrAIProperty.AI_FLUID_DETECTION
                            ):
                                self._map_property_changed(current_value)
                        else:
                            _LOGGER.info("AI Property %s Added: %s", prop.name, value)
                        changed = True
                        self.ai_data[prop.name] = value
        elif isinstance(ai_value, int):
            if self.ai_data is None:
                self.ai_data = {}

            for prop in DreameVacuumAIProperty:
                bit = int(prop.value)
                value = (ai_value & bit) == bit
                if prop.name in self._dirty_ai_data:
                    if (
                        self._dirty_ai_data[prop.name].value != value
                        and time.time() - self._dirty_ai_data[prop.name].update_time < self._discard_timeout
                    ):
                        _LOGGER.info(
                            "AI Property %s Value Discarded: %s <- %s",
                            prop.name,
                            self._dirty_ai_data[prop.name].value,
                            value,
                        )
                        del self._dirty_ai_data[prop.name]
                        continue
                    del self._dirty_ai_data[prop.name]

                current_value = self.ai_data.get(prop.name)
                if current_value != value:
                    if current_value is not None:
                        _LOGGER.info(
                            "AI Property %s Changed: %s -> %s",
                            prop.name,
                            current_value,
                            value,
                        )
                        if (
                            prop == DreameVacuumAIProperty.AI_PET_DETECTION
                            or prop == DreameVacuumAIProperty.AI_FLUID_DETECTION
                        ):
                            self._map_property_changed(current_value)
                    else:
                        _LOGGER.info("AI Property %s Added: %s", prop.name, value)
                    changed = True
                    self.ai_data[prop.name] = value

        if changed:
            self._last_change = time.time()
            if self._ready:
                self._property_changed()

        self.status.ai_policy_accepted = bool(
            self.status.ai_policy_accepted or self.status.ai_obstacle_detection or self.status.ai_obstacle_picture
        )

    def _auto_switch_settings_changed(self, previous_auto_switch_settings: Any = None) -> None:
        value = self.get_property(DreameVacuumProperty.AUTO_SWITCH_SETTINGS)
        if isinstance(value, str) and len(value) > 2:
            mopping_setting_changed = False
            cleangenius_changed = False
            try:
                settings = json.loads(value)
                settings_dict = {}

                if isinstance(settings, list):
                    for setting in settings:
                        settings_dict[setting["k"]] = setting["v"]
                elif "k" in settings:
                    settings_dict[settings["k"]] = settings["v"]

                if settings_dict and self.auto_switch_data is None:
                    self.auto_switch_data = {}

                changed = False
                for prop in DreameVacuumAutoSwitchProperty:
                    if prop.value in settings_dict:
                        value = settings_dict[prop.value]

                        if prop.name in self._dirty_auto_switch_data:
                            if (
                                self._dirty_auto_switch_data[prop.name].value != value
                                and time.time() - self._dirty_auto_switch_data[prop.name].update_time
                                < self._discard_timeout
                            ):
                                _LOGGER.info(
                                    "Property %s Value Discarded: %s <- %s",
                                    prop.name,
                                    self._dirty_auto_switch_data[prop.name].value,
                                    value,
                                )
                                del self._dirty_auto_switch_data[prop.name]
                                continue
                            del self._dirty_auto_switch_data[prop.name]

                        current_value = self.auto_switch_data.get(prop.name)
                        if current_value != value:
                            if (
                                prop == DreameVacuumAutoSwitchProperty.MOPPING_MODE
                                or prop == DreameVacuumAutoSwitchProperty.CUSTOM_MOPPING_MODE
                            ):
                                mopping_setting_changed = True
                            if prop == DreameVacuumAutoSwitchProperty.CLEANGENIUS:
                                cleangenius_changed = True
                                if self._previous_cleangenius is not None:
                                    self._previous_cleangenius = value

                            if current_value is not None:
                                _LOGGER.info(
                                    "Property %s Changed: %s -> %s",
                                    prop.name,
                                    current_value,
                                    value,
                                )
                            else:
                                _LOGGER.info("Property %s Added: %s", prop.name, value)
                            changed = True
                            self.auto_switch_data[prop.name] = value

                if changed:
                    self._last_change = time.time()
                    if self._ready and previous_auto_switch_settings is not None:
                        self._property_changed()
            except Exception as ex:
                _LOGGER.error("Failed to parse auto switch settings: %s", ex)

            if (
                mopping_setting_changed
                and self.capability.self_wash_base
                and self.capability.custom_mopping_route
                and not self.capability.wetness_level
                and not self.capability.mop_clean_frequency
            ):
                if self.status.mop_pad_humidity == 3:
                    if not self.capability.small_self_clean_area:
                        self.status.self_clean_area_max = 15
                        self.status.self_clean_area_default = 15

                    if self.capability.self_clean_frequency:
                        if self.status.mop_pad_humidity == 3:
                            self.status.self_clean_time_max = 20
                            self.status.self_clean_time_default = 20
                else:
                    if not self.capability.small_self_clean_area:
                        self.status.self_clean_area_max = 35 if self.capability.cleaning_route else 30
                        self.status.self_clean_area_default = 20

                    if self.capability.self_clean_frequency:
                        self.status.self_clean_time_max = 50
                        self.status.self_clean_time_default = 25

            if cleangenius_changed and self._map_manager and self._ready and previous_auto_switch_settings is not None:
                self._map_manager.editor.refresh_map()

    def _dnd_task_changed(self, previous_dnd_task: Any = None) -> None:
        dnd_tasks = self.get_property(DreameVacuumProperty.DND_TASK)
        if dnd_tasks and dnd_tasks != "":
            self.status.dnd_tasks = json.loads(dnd_tasks)

    def _schedule_changed(self, previous_schedule: Any = None) -> None:
        schedule = self.get_property(DreameVacuumProperty.SCHEDULE)
        schedule_list = []
        if schedule and schedule != "":
            tasks = schedule.split(";")
            for task in tasks:
                props = task.split("-")
                if len(props) >= 9:
                    schedule_list.append(
                        ScheduleTask(
                            id=int(props[0]),
                            enabled=bool(props[1] == "1" or props[1] == "2"),
                            invalid=bool(props[1] == "3"),
                            time=props[2],
                            repeats=props[3],
                            once=bool(props[4] == "0"),
                            map_id=props[5],
                            suction_level=int(props[6]),
                            water_volume=int(props[7]),
                            options=props[8].split(",") if props[8] != "0" else None,
                        )
                    )
        if schedule_list and len(schedule_list) > 1:
            schedule_list.sort(
                key=cmp_to_key(
                    lambda a, b: (
                        b.id - a.id
                        if a.time == b.time
                        else int(a.time.replace(":", "")) - int(b.time.replace(":", ""))
                    )
                )
            )
        self.status.schedule = schedule_list

    def _stream_status_changed(self, previous_stream_status: Any = None) -> None:
        stream_status = self.get_property(DreameVacuumProperty.STREAM_STATUS)
        if stream_status and stream_status != "" and stream_status != "null":
            stream_status = json.loads(stream_status)
            if stream_status and stream_status.get("result") == 0:
                self.status.stream_session = stream_status.get("session")
                operation_type = stream_status.get("operType")
                operation = stream_status.get("operation")
                if operation_type:
                    if operation_type == "end" or operation == "end":
                        self.status.stream_status = DreameVacuumStreamStatus.IDLE
                    elif operation_type == "start" or operation == "start":
                        if operation:
                            if operation == "monitor" or operation_type == "monitor":
                                self.status.stream_status = DreameVacuumStreamStatus.VIDEO
                            elif operation == "intercom" or operation_type == "intercom":
                                self.status.stream_status = DreameVacuumStreamStatus.AUDIO
                            elif operation == "recordVideo" or operation_type == "recordVideo":
                                self.status.stream_status = DreameVacuumStreamStatus.RECORDING

    def _shortcuts_changed(self, previous_shortcuts: Any = None) -> None:
        self.reload_shortcuts()

    def _voice_assistant_language_changed(self, previous_voice_assistant_language: Any = None) -> None:
        value = self.get_property(DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE)
        language_list = self.status.voice_assistant_language_list
        if value and len(value):
            language_list = VOICE_ASSISTANT_LANGUAGE_TO_NAME.copy()
            language_list.pop(DreameVacuumVoiceAssistantLanguage.DEFAULT)
            language_list = {v: k for k, v in language_list.items()}
        elif DreameVacuumVoiceAssistantLanguage.DEFAULT.value not in language_list:
            language_list = {v: k for k, v in VOICE_ASSISTANT_LANGUAGE_TO_NAME.items()}
        self.status.voice_assistant_language_list = language_list

    def _drainage_status_changed(self, previous_drainage_status: Any = None) -> None:
        if self.status.draining_complete:
            self._draining_complete_time = time.time()
        else:
            self._draining_complete_time = None

    def _self_wash_base_status_changed(self, previous_self_wash_base_status: Any = None) -> None:
        if previous_self_wash_base_status is not None:
            if (
                bool(
                    self.status.started
                    and previous_self_wash_base_status == DreameVacuumSelfWashBaseStatus.WASHING.value
                    or previous_self_wash_base_status == DreameVacuumSelfWashBaseStatus.CLEAN_ADD_WATER.value
                )
                != self.status.washing
            ):
                self._consumable_change = True

            if self._map_manager:
                self._map_manager.editor.refresh_map()

    def _off_peak_charging_changed(self, previous_off_peak_charging: Any = None) -> None:
        off_peak_charging = self.get_property(DreameVacuumProperty.OFF_PEAK_CHARGING)
        if off_peak_charging and off_peak_charging != "":
            self.status.off_peak_charging_config = json.loads(off_peak_charging)

    def _suction_level_changed(self, previous_suction_level: Any = None) -> None:
        if previous_suction_level is not None and self.status.go_to_zone:
            self.status.go_to_zone.suction_level = None

    def _water_volume_changed(self, previous_water_volume: Any = None) -> None:
        if self.capability.wetness and not self.capability.wetness_level:
            self.status.mop_pad_humidity = self.status.water_volume.value
        if previous_water_volume is not None and self.status.go_to_zone:
            self.status.go_to_zone.water_volume = None

    def _wetness_level_changed(self, previous_wetness_level: Any = None) -> None:
        wetness_level = self.status.wetness_level
        if wetness_level:
            water_level = 2
            if wetness_level > 32:
                if wetness_level > 200:
                    water_level = 3
                elif wetness_level < 200:
                    water_level = 1
            else:
                if wetness_level > (14 if self.capability.mop_clean_frequency else 26):
                    water_level = 3
                elif wetness_level < 6:
                    water_level = 1

            self.status.mop_pad_humidity = water_level

            if (
                self.capability.self_wash_base
                and self.capability.wetness_level
                and not self.capability.mop_clean_frequency
            ):
                if self.status.wetness_level > 26:
                    self.status.self_clean_time_max = 20
                    self.status.self_clean_time_default = 20

                    if not self.capability.small_self_clean_area:
                        self.status.self_clean_area_max = 20
                else:
                    self.status.self_clean_time_max = 50
                    self.status.self_clean_time_default = 25

                    if not self.capability.small_self_clean_area:
                        self.status.self_clean_area_max = 35

    def _error_changed(self, previous_error: Any = None) -> None:
        if previous_error is not None and self.status.go_to_zone and self.status.has_error:
            self._restore_go_to_zone(True)

        if self._map_manager and previous_error is not None:
            self._map_manager.editor.refresh_map()

    def _battery_level_changed(self, previous_battery_level: Any = None) -> None:
        if self._map_manager and previous_battery_level is not None and self.status.battery_level == 100:
            self._map_manager.editor.refresh_map()

    def _request_cleaning_history(self) -> None:
        """Get and parse the cleaning history from cloud event data and set it to memory"""
        if (
            self.cloud_connected
            and self._cleaning_history_update != 0
            and (
                self._cleaning_history_update == -1
                or self.status._cleaning_history is None
                or (
                    time.time() - self._cleaning_history_update >= 5
                    and self.status.task_status is DreameVacuumTaskStatus.COMPLETED
                )
            )
        ):
            self._cleaning_history_update = 0

            _LOGGER.info("Get Cleaning History")
            try:
                # Limit the results
                start = None
                max = 25
                total = self.get_property(DreameVacuumProperty.CLEANING_COUNT)
                if total > 0:
                    start = self.get_property(DreameVacuumProperty.FIRST_CLEANING_DATE)

                if start is None:
                    start = int(time.time())
                if total is None:
                    total = 5
                limit = 40
                if total < max:
                    limit = total + max

                changed = False
                # Cleaning history is generated from events of status property that has been sent to cloud by the device when it changed
                result = self._protocol.cloud.get_device_event(
                    DIID(DreameVacuumProperty.STATUS, self.property_mapping),
                    limit,
                    start,
                )
                if result:
                    cleaning_history = []
                    history_size = 0
                    for data in result:
                        history = CleaningHistory(
                            json.loads(data["history"] if "history" in data else data["value"]),
                            self.property_mapping,
                        )
                        if history_size > 0 and cleaning_history[-1].date == history.date:
                            continue

                        if history.cleanup_method == CleanupMethod.CUSTOMIZED_CLEANING and self.capability.cleangenius:
                            history.cleanup_method = CleanupMethod.DEFAULT_MODE

                        cleaning_history.append(history)
                        history_size = history_size + 1
                        if history_size >= max or history_size >= total:
                            break

                    if self.status._cleaning_history != cleaning_history:
                        _LOGGER.info("Cleaning History Changed")
                        self.status._cleaning_history = cleaning_history
                        self.status._cleaning_history_attrs = None
                        if cleaning_history:
                            self.status._last_cleaning_time = cleaning_history[0].date.replace(
                                tzinfo=datetime.now().astimezone().tzinfo
                            )
                        changed = True

                if self.capability.cruising:
                    # Cruising history is generated from events of water volume property that has been sent to cloud by the device when it changed
                    result = self._protocol.cloud.get_device_event(
                        DIID(DreameVacuumProperty.WATER_VOLUME, self.property_mapping),
                        limit,
                        start,
                    )
                    if result:
                        cruising_history = []
                        history_size = 0
                        for data in result:
                            history = CleaningHistory(
                                json.loads(data["history"] if "history" in data else data["value"]),
                                self.property_mapping,
                            )
                            if history_size > 0 and cruising_history[-1].date == history.date:
                                continue
                            cruising_history.append(history)
                            history_size = history_size + 1
                            if history_size >= max or history_size >= total:
                                break

                        if self.status._cruising_history != cruising_history:
                            _LOGGER.debug("Cruising History Changed")
                            self.status._cruising_history = cruising_history
                            self.status._cruising_history_attrs = None
                            if cruising_history:
                                self.status._last_cruising_time = cruising_history[0].date.replace(
                                    tzinfo=datetime.now().astimezone().tzinfo
                                )
                            changed = True

                if changed:
                    if self.capability.auto_recleaning:
                        self.history_map(1)

                    if self._ready:
                        for k, v in copy.deepcopy(self.status._history_map_data).items():
                            found = False
                            if self.status._cleaning_history:
                                for item in self.status._cleaning_history:
                                    if k in item.file_name:
                                        found = True
                                        break

                            if found:
                                continue

                            if self.status._cruising_history:
                                for item in self.status._cruising_history:
                                    if k in item.file_name:
                                        found = True
                                        break

                            if found:
                                continue

                            del self.status._history_map_data[k]

                        if self._map_manager:
                            self._map_manager.editor.refresh_map()
                        self._property_changed()

            except Exception as ex:
                _LOGGER.warning("Get Cleaning History failed!: %s", ex)

    def _property_changed(self, delay=True) -> None:
        """Call external listener when a property changed"""
        if self._update_callback:
            if self._callback_timer is not None:
                self._callback_timer.cancel()

            if delay:
                self._callback_timer = Timer(0.1, self._update_callback)
                self._callback_timer.start()
            else:
                self._update_callback()

    def _map_updated(self) -> None:
        """Call external listener when a map updated from local"""
        self._last_map_change_time = time.time()
        self._property_changed()

    def _map_changed(self, saved_map) -> None:
        """Call external listener when a map changed"""
        map_data = self.status.current_map
        if self._map_select_time:
            self._map_select_time = None
        if not saved_map:
            self._last_map_change_time = time.time()
        if map_data and self.status.started:
            if self.status.go_to_zone is None and not self.status._capability.cruising and self.status.zone_cleaning:
                if map_data.active_areas and len(map_data.active_areas) == 1:
                    area = map_data.active_areas[0]
                    size = map_data.dimensions.grid_size * 2
                    if area.check_size(size):
                        new_cleaning_mode = None
                        if not (self.capability.self_wash_base or self.capability.mop_pad_lifting):
                            if (
                                self.status.cleaning_mode == DreameVacuumCleaningMode.MOPPING
                                and not self.status.water_tank_or_mop_installed
                            ):
                                new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING.value
                            elif (
                                self.status.cleaning_mode == DreameVacuumCleaningMode.SWEEPING
                                and self.status.water_tank_or_mop_installed
                            ):
                                new_cleaning_mode = DreameVacuumCleaningMode.MOPPING_AND_SWEEPING.value

                        self.status.go_to_zone = GoToZoneSettings(
                            x=area.x0 + map_data.dimensions.grid_size,
                            y=area.y0 + map_data.dimensions.grid_size,
                            stop=bool(not self._map_manager.ready),
                            size=size,
                            cleaning_mode=new_cleaning_mode,
                        )
                        self._map_manager.editor.set_active_areas([])
                    else:
                        self.status.go_to_zone = False
                else:
                    self.status.go_to_zone = False

            if self.status.go_to_zone:
                position = map_data.robot_position
                if position:
                    size = self.status.go_to_zone.size
                    x = self.status.go_to_zone.x
                    y = self.status.go_to_zone.y
                    if (
                        position.x >= x - size
                        and position.x <= x + size
                        and position.y >= y - size
                        and position.y <= y + size
                    ):
                        self._restore_go_to_zone(True)

            if self.status.docked != map_data.docked and self._protocol.prefer_cloud:
                self.schedule_update(self._update_interval, True)

        if self._map_manager.ready:
            self._property_changed()

    def _update_failed(self, ex) -> None:
        """Call external listener when update failed"""
        if self._error_callback:
            self._error_callback(ex)

    def _action_update_task(self) -> None:
        self._update_task(True)

    def _update_task(self, force_request_properties=False) -> None:
        """Timer task for updating properties periodically"""
        self._update_timer = None
        try:
            self.update(force_request_properties)
            if self._ready:
                self.available = True
            self._update_fail_count = 0
        except Exception as ex:
            self._update_fail_count = self._update_fail_count + 1
            if self.available:
                self._last_update_failed = time.time()
                if self._update_fail_count <= 3:
                    _LOGGER.debug(
                        "Update failed, retrying %s: %s",
                        self._update_fail_count,
                        str(ex),
                    )
                elif self._ready:
                    _LOGGER.warning("Update Failed: %s", str(ex))
                    self.available = False
                    self._update_failed(ex)

        if not self.disconnected:
            self.schedule_update(self._update_interval)

    def _update_cleaning_mode(self, cleaning_mode) -> int:
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(
                self.get_property(DreameVacuumProperty.CLEANING_MODE),
                self.capability.mop_pad_lifting,
            )
            if not (values and len(values) == 3):
                return False

            if self.capability.mop_pad_lifting:
                if cleaning_mode == 2:
                    values[0] = 0
                elif cleaning_mode == 0:
                    values[0] = 2
                else:
                    values[0] = cleaning_mode
            elif cleaning_mode == 2:
                values[0] = 0
            cleaning_mode = DreameVacuumDevice.combine_group_value(values)
        elif self.capability.mop_pad_lifting:
            if cleaning_mode == 2:
                cleaning_mode = 0
            elif cleaning_mode == 0:
                cleaning_mode = 2
        return self.set_property(DreameVacuumProperty.CLEANING_MODE, cleaning_mode)

    def _update_self_clean_value(self, self_clean_value) -> int:
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(
                self.get_property(DreameVacuumProperty.CLEANING_MODE),
                self.capability.mop_pad_lifting,
            )
            if values and len(values) == 3:
                values[1] = self_clean_value
                return self.set_property(
                    DreameVacuumProperty.CLEANING_MODE,
                    DreameVacuumDevice.combine_group_value(values),
                )
        return False

    def _update_self_clean_time(self, self_clean_time) -> int:
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(
                self.get_property(DreameVacuumProperty.CLEANING_MODE),
                self.capability.mop_pad_lifting,
            )
            if values and len(values) == 3:
                values[1] = self_clean_time
                return self.set_property(
                    DreameVacuumProperty.CLEANING_MODE,
                    DreameVacuumDevice.combine_group_value(values),
                )
        return False

    def _update_water_level(self, water_level) -> int:
        if (
            self.capability.mopping_settings
            and self.capability.self_wash_base
            and not self.capability.wetness_level
            and water_level == 3
            and self.status.self_clean_value > 15
            and not self.status.self_clean_by_time
        ):
            self.set_self_clean_value(15)

        if self.capability.custom_mopping_route and not self.status.custom_mopping_mode:
            self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.MOPPING_MODE, water_level)

        if self.capability.wetness:
            wetness_level = 0
            if self.capability.custom_mopping_route and not self.status.custom_mopping_mode:
                if water_level == 1:
                    wetness_level = 100
                elif water_level == 3:
                    wetness_level = 400
                else:
                    wetness_level = 200
            elif self.capability.mop_clean_frequency:
                if water_level == 1:
                    wetness_level = 2
                elif water_level == 3:
                    wetness_level = 14
                else:
                    wetness_level = 8
            else:
                if water_level == 1:
                    wetness_level = 5
                elif water_level == 3:
                    wetness_level = 27
                else:
                    wetness_level = 16
            result = self.set_wetness_level(wetness_level)
            if self.capability.wetness_level:
                return result

        if not self.capability.self_wash_base:
            result = self.set_property(DreameVacuumProperty.WATER_VOLUME, int(water_level))
        else:
            values = DreameVacuumDevice.split_group_value(
                self.get_property(DreameVacuumProperty.CLEANING_MODE),
                self.capability.mop_pad_lifting,
            )
            if values and len(values) == 3:
                if self.capability.wetness and not self.capability.wetness_level and values[2] == 0:
                    return result
                values[2] = water_level
                return self.set_property(
                    DreameVacuumProperty.CLEANING_MODE,
                    DreameVacuumDevice.combine_group_value(values),
                )
            return False
        return result

    def _update_suction_level(self, suction_level) -> int:
        return self.set_property(DreameVacuumProperty.SUCTION_LEVEL, int(suction_level))

    def _set_go_to_zone(self, x, y, size):
        current_cleaning_mode = int(self.status.cleaning_mode.value)
        current_suction_level = int(self.status.suction_level.value)
        current_water_level = int(
            self.status.mop_pad_humidity if self.capability.self_wash_base else self.status.water_volume.value
        )

        new_cleaning_mode = None
        new_suction_level = None
        new_water_level = None

        if self.capability.self_wash_base or self.capability.mop_pad_lifting:
            if current_cleaning_mode != DreameVacuumCleaningMode.SWEEPING.value:
                new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING.value
            else:
                current_cleaning_mode = None

            if current_suction_level != DreameVacuumSuctionLevel.QUIET.value:
                new_suction_level = DreameVacuumSuctionLevel.QUIET.value
            else:
                current_suction_level = None

            current_water_level = None
        else:
            cleaning_mode = DreameVacuumCleaningMode.MOPPING.value
            if self.status.water_tank_or_mop_installed:
                if self.status.current_map and self.status.current_map.no_mopping_areas:
                    for area in self.status.current_map.no_mopping_areas:
                        if area.check_point(x, y, size):
                            cleaning_mode = DreameVacuumCleaningMode.SWEEPING.value
                            break

            if current_cleaning_mode != cleaning_mode:
                new_cleaning_mode = cleaning_mode
            else:
                if (
                    current_cleaning_mode == DreameVacuumCleaningMode.MOPPING.value
                    and not self.status.water_tank_or_mop_installed
                ):
                    current_cleaning_mode = DreameVacuumCleaningMode.SWEEPING.value
                elif (
                    current_cleaning_mode == DreameVacuumCleaningMode.SWEEPING.value
                    and self.status.water_tank_or_mop_installed
                ):
                    current_cleaning_mode = DreameVacuumCleaningMode.SWEEPING_AND_MOPPING.value
                else:
                    current_cleaning_mode = None

            if current_water_level != DreameVacuumWaterVolume.LOW.value:
                new_water_level = DreameVacuumWaterVolume.LOW.value
            else:
                current_water_level = None

            current_suction_level = None

        try:
            if new_suction_level is not None:
                self._update_suction_level(new_suction_level)

            if new_water_level is not None:
                self._update_water_level(new_water_level)

            if new_cleaning_mode is not None:
                self._update_cleaning_mode(new_cleaning_mode)
        except:
            pass

        self.status.go_to_zone = GoToZoneSettings(
            x=x,
            y=y,
            stop=True,
            suction_level=current_suction_level,
            water_level=current_water_level,
            cleaning_mode=current_cleaning_mode,
            size=size,
        )

    def _restore_go_to_zone(self, stop=False):
        if self.status.go_to_zone is not None:
            if self.status.go_to_zone:
                stop = stop and self.status.go_to_zone.stop
                suction_level = self.status.go_to_zone.suction_level
                water_level = self.status.go_to_zone.water_level
                cleaning_mode = self.status.go_to_zone.cleaning_mode
                self.status.go_to_zone = None
                if stop:
                    self.schedule_update(10, True)
                    try:
                        mapping = self.action_mapping[DreameVacuumAction.STOP]
                        self._protocol.action(mapping["siid"], mapping["aiid"])
                    except:
                        pass

                try:
                    self._cleaning_history_update = time.time()
                    if cleaning_mode is not None and self.status.cleaning_mode.value != cleaning_mode:
                        self._update_cleaning_mode(cleaning_mode)
                    if suction_level is not None and self.status.suction_level.value != suction_level:
                        self._update_suction_level(suction_level)
                    if water_level is not None and self.status.water_volume.value != water_level:
                        self._update_water_level(water_level)

                    if stop and self.status.started:
                        self._update_status(DreameVacuumTaskStatus.COMPLETED, DreameVacuumStatus.STANDBY)
                except:
                    pass

                if self._protocol.dreame_cloud:
                    self.schedule_update(3, True)
            else:
                self.status.go_to_zone = None

    @staticmethod
    def split_group_value(value: int, mop_pad_lifting: bool = False) -> list[int]:
        if value is not None:
            value_list = []
            value_list.append((value & 0x03) if mop_pad_lifting else (value & 1))
            byte1 = value >> 8
            byte1 = byte1 & -769
            value_list.append(byte1)
            value_list.append(value >> 16)
            return value_list

    @staticmethod
    def combine_group_value(values: list[int]) -> int:
        if values and len(values) == 3:
            return ((((0 ^ values[2]) << 8) ^ values[1]) << 8) ^ values[0]

    def connect_device(self) -> None:
        """Connect to the device api."""
        _LOGGER.info("Connecting to device")
        info = self._protocol.connect(self._message_callback, self._connected_callback)
        if info:
            self.info = DreameVacuumDeviceInfo(info)
            if self.mac is None:
                self.mac = self.info.mac_address
            _LOGGER.info(
                "Connected to device: %s %s",
                self.info.model,
                self.info.firmware_version,
            )

            self._last_settings_request = time.time()
            self._last_map_list_request = self._last_settings_request
            self._dirty_data = {}
            self._dirty_auto_switch_data = {}
            self._dirty_ai_data = {}
            self._request_properties()
            self._last_update_failed = None

            if self.device_connected and self._protocol.cloud is not None and (not self._ready or not self.available):
                if self._map_manager:
                    self._map_manager.set_capability(self.capability)
                    self._map_manager.set_update_interval(self._map_update_interval)
                    self._map_manager.set_device_running(
                        self.status.running,
                        self.status.docked and not self.status.started,
                    )

                    if self.status.current_map is None:
                        self._map_manager.schedule_update(15)
                        try:
                            self._map_manager.update()
                            self._last_map_request = self._last_settings_request
                        except Exception as ex:
                            _LOGGER.error("Initial map update failed! %s", str(ex))
                        self._map_manager.schedule_update()
                    else:
                        self.update_map()

                if self.cloud_connected:
                    self._cleaning_history_update = -1
                    self._request_cleaning_history()
                    if (self.capability.ai_detection and not self.status.ai_policy_accepted) or True:
                        try:
                            prop = "prop.s_ai_config"
                            response = self._protocol.cloud.get_batch_device_datas([prop])
                            if response and prop in response and response[prop]:
                                value = json.loads(response[prop])
                                self.status.ai_policy_acepted = (
                                    value.get("privacyAuthed")
                                    if "privacyAuthed" in value
                                    else value.get("aiPrivacyAuthed")
                                )
                        except:
                            pass

            if not self.available:
                self.available = True

            if not self._ready:
                self._ready = True
            else:
                self._property_changed(False)

    def connect_cloud(self) -> None:
        """Connect to the cloud api."""
        if self._protocol.cloud and not self._protocol.cloud.logged_in:
            self._protocol.cloud.login()
            self.auth_failed = False
            if self._protocol.cloud.logged_in is False:
                if self._protocol.cloud.auth_failed:
                    self.auth_failed = True
                    self._property_changed(False)
                self._map_manager.schedule_update(-1)
            elif self._protocol.cloud.logged_in:
                if self._protocol.connected:
                    self._map_manager.schedule_update(5)

                self.token, self.host = self._protocol.cloud.get_info(self.mac)
                if not self._protocol.dreame_cloud:
                    self._protocol.set_credentials(self.host, self.token, self.mac, self.account_type)

    def disconnect(self) -> None:
        """Disconnect from device and cancel timers"""
        _LOGGER.info("Disconnect")
        self.disconnected = True
        self.schedule_update(-1)
        self._protocol.disconnect()
        if self._map_manager:
            self._map_manager.disconnect()
        self._property_changed(False)

    def listen(self, callback, property: DreameVacuumProperty = None) -> None:
        """Set callback functions for external listeners"""
        if callback is None:
            self._update_callback = None
            self._property_update_callback = {}
            return

        if property is None:
            self._update_callback = callback
        else:
            if property.value not in self._property_update_callback:
                self._property_update_callback[property.value] = []
            self._property_update_callback[property.value].append(callback)

    def listen_error(self, callback) -> None:
        """Set error callback function for external listeners"""
        self._error_callback = callback

    def schedule_update(self, wait: float = None, force_request_properties=False) -> None:
        """Schedule a device update for future"""
        if wait == None:
            wait = self._update_interval

        if self._update_timer is not None:
            self._update_timer.cancel()
            del self._update_timer
            self._update_timer = None

        if wait >= 0:
            self._update_timer = Timer(
                wait, self._action_update_task if force_request_properties else self._update_task
            )
            self._update_timer.start()

    def get_property(
        self,
        prop: (
            DreameVacuumProperty | DreameVacuumAutoSwitchProperty | DreameVacuumStrAIProperty | DreameVacuumAIProperty
        ),
    ) -> Any:
        """Get a device property from memory"""
        if isinstance(prop, DreameVacuumAutoSwitchProperty):
            return self.get_auto_switch_property(prop)
        if isinstance(prop, DreameVacuumStrAIProperty) or isinstance(prop, DreameVacuumAIProperty):
            return self.get_ai_property(prop)
        if prop is not None and prop.value in self.data:
            return self.data[prop.value]
        return None

    def get_auto_switch_property(self, prop: DreameVacuumAutoSwitchProperty) -> int:
        """Get a device auto switch property from memory"""
        if self.capability.auto_switch_settings and self.auto_switch_data:
            if prop is not None and prop.name in self.auto_switch_data:
                return int(self.auto_switch_data[prop.name])
        return None

    def get_ai_property(self, prop: DreameVacuumStrAIProperty | DreameVacuumAIProperty) -> bool:
        """Get a device AI property from memory"""
        if self.capability.ai_detection and self.ai_data:
            if prop is not None and prop.name in self.ai_data:
                return bool(self.ai_data[prop.name])
        return None

    def set_property_value(self, prop: str, value: Any):
        if prop is not None and value is not None:
            set_fn = "set_" + prop.lower()
            if hasattr(self, set_fn):
                set_fn = getattr(self, set_fn)
            else:
                set_fn = None

            prop = prop.upper()
            if prop in DreameVacuumProperty.__members__:
                prop = DreameVacuumProperty(DreameVacuumProperty[prop])
                if prop not in self._read_write_properties:
                    raise InvalidActionException("Invalid property: %s", prop)
            elif prop in DreameVacuumAutoSwitchProperty.__members__:
                prop = DreameVacuumAutoSwitchProperty(DreameVacuumAutoSwitchProperty[prop])
            elif prop in DreameVacuumAIProperty.__members__:
                prop = DreameVacuumAIProperty(DreameVacuumAIProperty[prop])
            elif prop in DreameVacuumStrAIProperty.__members__:
                prop = DreameVacuumStrAIProperty(DreameVacuumStrAIProperty[prop])
            elif set_fn is None:
                raise InvalidActionException("Invalid property: %s", prop)

            if set_fn is None and self.get_property(prop) is None:
                raise InvalidActionException("Invalid property: %s", prop)

            prop_name = prop.lower() if isinstance(prop, str) else prop.name

            if (
                (
                    self.status.started
                    or not (
                        prop is DreameVacuumProperty.SUCTION_LEVEL
                        or prop is DreameVacuumProperty.WATER_VOLUME
                        or prop is DreameVacuumProperty.CLEANING_MODE
                        or prop is DreameVacuumProperty.WETNESS_LEVEL
                        or prop is DreameVacuumAutoSwitchProperty.CLEANING_ROUTE
                        or prop == "CUSTOM_MOPPING_ROUTE"
                        or prop == "MOP_PAD_HUMIDITY"
                    )
                )
                and prop_name in PROPERTY_AVAILABILITY
                and not PROPERTY_AVAILABILITY[prop_name](self)
            ):
                raise InvalidActionException("Property unavailable: %s", prop)

            def get_int_value(enum, value, enum_list=None):
                if isinstance(value, str):
                    value = value.upper()
                    if value.isnumeric():
                        value = int(value)
                    elif value in enum.__members__:
                        value = enum[value].value
                        if enum_list is None:
                            return value

                if isinstance(value, int):
                    if enum_list is None:
                        if value in enum._value2member_map_:
                            return value
                    elif value in enum_list.values():
                        return value

            string_value = False
            if prop is DreameVacuumProperty.SUCTION_LEVEL:
                value = get_int_value(DreameVacuumSuctionLevel, value)
            elif prop is DreameVacuumProperty.WATER_VOLUME:
                value = get_int_value(DreameVacuumWaterVolume, value)
            elif prop is DreameVacuumProperty.CLEANING_MODE:
                value = get_int_value(DreameVacuumCleaningMode, value)
            elif prop is DreameVacuumProperty.CARPET_SENSITIVITY:
                value = get_int_value(DreameVacuumCarpetSensitivity, value)
            elif prop is DreameVacuumProperty.CARPET_CLEANING:
                value = get_int_value(
                    DreameVacuumCarpetCleaning, value, {v: k for k, v in CARPET_CLEANING_CODE_TO_NAME.items()}
                )
            elif prop is DreameVacuumProperty.MOP_WASH_LEVEL:
                value = get_int_value(DreameVacuumMopWashLevel, value)
            elif prop is DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE:
                value = get_int_value(
                    DreameVacuumVoiceAssistantLanguage, value, self.status.voice_assistant_language_list
                )
            elif prop is DreameVacuumProperty.SCHEDULE:  ## TODO: Convert this to service
                valid = True
                if value and value != "":
                    tasks = value.split(";")
                    for task in tasks:
                        props = task.split("-")
                        if len(props) < 9:
                            valid = False
                            break
                        id = int(props[0])
                        if not id:
                            valid = False
                            break
                        time = props[2]
                        if ":" not in time:
                            valid = False
                            break
                if valid:
                    string_value = value
            elif prop is DreameVacuumProperty.CLEANGENIUS_MODE:
                value = get_int_value(DreameVacuumCleanGeniusMode, value)
            elif prop is DreameVacuumProperty.WATER_TEMPERATURE:
                value = get_int_value(DreameVacuumWaterTemperature, value)
            elif prop is DreameVacuumAutoSwitchProperty.MOPPING_TYPE:
                value = get_int_value(DreameVacuumMoppingType, value)
            elif prop is DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE:
                value = get_int_value(DreameVacuumWiderCornerCoverage, value)
            elif prop is DreameVacuumAutoSwitchProperty.MOP_PAD_SWING:
                value = get_int_value(DreameVacuumMopPadSwing, value)
            elif prop is DreameVacuumAutoSwitchProperty.MOP_EXTEND_FREQUENCY:
                value = get_int_value(DreameVacuumMopExtendFrequency, value)
            elif prop is DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY:
                value = get_int_value(DreameVacuumSelfCleanFrequency, value)
            elif (
                prop is DreameVacuumAutoSwitchProperty.AUTO_RECLEANING
                or prop is DreameVacuumAutoSwitchProperty.AUTO_REWASHING
            ):
                value = get_int_value(DreameVacuumSecondCleaning, value)
            elif prop is DreameVacuumAutoSwitchProperty.CLEANING_ROUTE:
                value = get_int_value(DreameVacuumCleaningRoute, value, self.status.cleaning_route_list)
            elif prop is DreameVacuumAutoSwitchProperty.CLEANGENIUS:
                value = get_int_value(DreameVacuumCleanGenius, value)
            elif prop == "MOP_PAD_HUMIDITY":
                value = get_int_value(DreameVacuumMopPadHumidity, value)
            elif prop == "CUSTOM_MOPPING_ROUTE":
                value = get_int_value(DreameVacuumCustomMoppingRoute, value)
            elif prop == "AUTO_EMPTY_MODE":
                value = get_int_value(DreameVacuumAutoEmptyMode, value)
            elif prop == "WASHING_MODE":
                value = get_int_value(DreameVacuumWashingMode, value)
            elif prop == "SELECTED_MAP":
                if not self.status.map_data_list or value not in self.status.map_data_list:
                    value = None
            elif (
                prop == DreameVacuumProperty.DND_START
                or prop == DreameVacuumProperty.DND_END
                or prop == "OFF_PEAK_CHARGING_START"
                or prop == "OFF_PEAK_CHARGING_END"
            ):
                string_value = re.match(r"([0-1][0-9]|2[0-3]):[0-5][0-9]$", value)
            elif isinstance(value, bool):
                value = int(value)
            elif isinstance(value, str):
                value = value.upper()
                if value == "TRUE" or value == "1":
                    value = 1
                elif value == "FALSE" or value == "0":
                    value = 0
                elif value.isnumeric():
                    value = int(value)
                else:
                    value = None

            if value is None or not (isinstance(value, int) or string_value):
                if value is not None:
                    raise InvalidActionException("Invalid value: %s", value)
                else:
                    raise InvalidActionException("Invalid value")

            if prop == DreameVacuumProperty.VOLUME:
                if value < 0 or value > 100:
                    value = None
            elif prop == DreameVacuumProperty.MOP_CLEANING_REMAINDER:
                if value < 0 or value > 180:
                    value = None
            elif prop == DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS:
                if value < 40 or value > 100:
                    value = None
            elif prop == DreameVacuumProperty.WETNESS_LEVEL:
                if value < 1 or value > 32:
                    value = None
            elif prop == "SELF_CLEAN_AREA":
                if value < self.status.self_clean_area_min or value > self.status.self_clean_area_max:
                    value = None
            elif prop == "SELF_CLEAN_TIME":
                if value < self.status.self_clean_time_min or value > self.status.self_clean_time_max:
                    value = None

            if value is None:
                raise InvalidActionException("Invalid value")

            if not self.device_connected:
                raise InvalidActionException("Device unavailable")

            if set_fn:
                return set_fn(value)

            if self.get_property(prop) == value or self.set_property(prop, value):
                return
            raise InvalidActionException("Property %s not updated: %s", prop, value)
        raise InvalidActionException("Invalid property or value")

    def call_action_value(self, action: str, params: None):
        if action is not None:
            if hasattr(self, action) and not action.startswith("_"):
                action_fn = getattr(self, action)
            else:
                action_fn = None

            action = action.upper()
            if action in DreameVacuumAction.__members__:
                action = DreameVacuumAction(DreameVacuumAction[action])
            elif action_fn is None:
                raise InvalidActionException("Invalid action")

            action_name = action.lower() if isinstance(action, str) else action.name

            if action_name in ACTION_AVAILABILITY and not ACTION_AVAILABILITY[action_name](self):
                raise InvalidActionException("Action unavailable")

            if not self.device_connected:
                raise InvalidActionException("Device unavailable")

            if action_fn:
                if params is not None:
                    return action_fn(params)
                return action_fn()

            result = self.call_action(action, params)
            if result and result.get("code") == 0:
                return
            raise InvalidActionException("Unable to call action")
        raise InvalidActionException("Invalid action")

    def set_property(
        self,
        prop: (
            DreameVacuumProperty | DreameVacuumAutoSwitchProperty | DreameVacuumStrAIProperty | DreameVacuumAIProperty
        ),
        value: Any,
    ) -> bool:
        """Sets property value using the existing property mapping and notify listeners
        Property must be set on memory first and notify its listeners because device does not return new value immediately.
        """
        if value is None:
            return False

        if isinstance(prop, DreameVacuumAutoSwitchProperty):
            return self.set_auto_switch_property(prop, value)
        if isinstance(prop, DreameVacuumStrAIProperty) or isinstance(prop, DreameVacuumAIProperty):
            return self.set_ai_property(prop, value)

        self.schedule_update(10)
        current_value = self._update_property(prop, value, False)
        if current_value is not None:
            if prop not in self._discarded_properties:
                self._dirty_data[prop.value] = DirtyData(value, current_value, time.time())

            self._last_change = time.time()
            self._last_settings_request = 0

            try:
                mapping = self.property_mapping[prop]
                result = self._protocol.set_property(mapping["siid"], mapping["piid"], value)

                if result is None or result[0]["code"] != 0:
                    _LOGGER.error(
                        "Property not updated: %s: %s -> %s",
                        prop.name,
                        current_value,
                        value,
                    )
                    self._update_property(prop, current_value)
                    if prop.value in self._dirty_data:
                        del self._dirty_data[prop.value]
                    self._property_changed(False)

                    self.schedule_update(2)
                    return False
                else:
                    _LOGGER.info("Update Property: %s: %s -> %s", prop.name, current_value, value)
                    if prop.value in self._dirty_data:
                        self._dirty_data[prop.value].update_time = time.time()

                    self.schedule_update(3)
                    return True
            except Exception as ex:
                self._update_property(prop, current_value)
                if prop.value in self._dirty_data:
                    del self._dirty_data[prop.value]
                self.schedule_update(1)
                raise DeviceUpdateFailedException("Set property failed %s: %s", prop.name, ex) from None

        self.schedule_update(1)
        return False

    def get_map_for_render(self, map_data: MapData) -> MapData | None:
        """Makes changes on map data for device related properties for renderer.
        Map manager does not need any device property for parsing and storing map data but map renderer does.
        For example if device is running but not mopping renderer does not show no mopping areas and this function handles that so renderer does not need device data too.
        """
        if map_data:
            if map_data.need_optimization:
                map_data = self._map_manager.optimizer.optimize(
                    map_data,
                    self._map_manager.selected_map if map_data.saved_map_status == 2 else None,
                )
                map_data.need_optimization = False

            render_map_data = copy.deepcopy(map_data)
            if (
                not self.capability.lidar_navigation
                and self.status.docked
                and not self.status.started
                and map_data.saved_map_status == 1
            ):
                saved_map_data = self._map_manager.selected_map
                render_map_data.segments = copy.deepcopy(saved_map_data.segments)
                render_map_data.data = copy.deepcopy(saved_map_data.data)
                render_map_data.pixel_type = copy.deepcopy(saved_map_data.pixel_type)
                render_map_data.dimensions = copy.deepcopy(saved_map_data.dimensions)
                render_map_data.charger_position = copy.deepcopy(saved_map_data.charger_position)
                render_map_data.no_go_areas = saved_map_data.no_go_areas
                render_map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                render_map_data.virtual_walls = saved_map_data.virtual_walls
                render_map_data.robot_position = render_map_data.charger_position
                render_map_data.docked = True
                render_map_data.path = None
                render_map_data.need_optimization = False
                render_map_data.saved_map_status = 2
                render_map_data.optimized_pixel_type = None
                render_map_data.optimized_charger_position = None

            if render_map_data.optimized_pixel_type is not None:
                render_map_data.pixel_type = render_map_data.optimized_pixel_type
                render_map_data.dimensions = render_map_data.optimized_dimensions
                if render_map_data.optimized_charger_position is not None:
                    render_map_data.charger_position = render_map_data.optimized_charger_position

                # if not self.status.started and render_map_data.docked and render_map_data.robot_position and render_map_data.charger_position:
                #    render_map_data.charger_position = copy.deepcopy(render_map_data.robot_position)

            if render_map_data.combined_pixel_type is not None:
                render_map_data.pixel_type = render_map_data.combined_pixel_type
                render_map_data.dimensions = render_map_data.combined_dimensions

            if self.capability.map_object_offset:
                offset = render_map_data.dimensions.grid_size / 2
                render_map_data.dimensions.left = render_map_data.dimensions.left - offset
                render_map_data.dimensions.top = render_map_data.dimensions.top - offset
            else:
                render_map_data.dimensions.top = render_map_data.dimensions.top - render_map_data.dimensions.grid_size

            if render_map_data.wifi_map:
                return render_map_data

            if render_map_data.furniture_version == 1 and self.capability.new_furnitures:
                render_map_data.furniture_version = 3 if self.capability.mijia else 2

            if not render_map_data.history_map:
                if self.status.started and not (
                    self.status.zone_cleaning
                    or self.status.go_to_zone
                    or (
                        render_map_data.active_areas
                        and self.status.task_status is DreameVacuumTaskStatus.DOCKING_PAUSED
                    )
                ):
                    # Map data always contains last active areas
                    render_map_data.active_areas = None

                if self.status.started and not self.status.spot_cleaning:
                    # Map data always contains last active points
                    render_map_data.active_points = None

                if not self.status.segment_cleaning:
                    # Map data always contains last active segments
                    render_map_data.active_segments = None

                if not self.status.cruising:
                    # Map data always contains last active path points
                    render_map_data.active_cruise_points = None

                if self.capability.camera_streaming and render_map_data.predefined_points is None:
                    render_map_data.predefined_points = []
            else:
                if not self.capability.camera_streaming:
                    if render_map_data.active_areas and len(render_map_data.active_areas) == 1:
                        area = render_map_data.active_areas[0]
                        size = render_map_data.dimensions.grid_size * 2
                        if area.check_size(size):
                            x = area.x0 + render_map_data.dimensions.grid_size
                            y = area.y0 + render_map_data.dimensions.grid_size
                            render_map_data.task_cruise_points = {
                                1: Coordinate(
                                    x,
                                    y,
                                    False,
                                    0,
                                )
                            }

                            if render_map_data.completed == False:
                                if render_map_data.robot_position:
                                    render_map_data.completed = bool(
                                        render_map_data.robot_position.x >= x - size
                                        and render_map_data.robot_position.x <= x + size
                                        and render_map_data.robot_position.y >= y - size
                                        and render_map_data.robot_position.y <= y + size
                                    )
                                else:
                                    render_map_data.completed = True

                            render_map_data.active_areas = None

                if render_map_data.active_areas or render_map_data.active_points:
                    render_map_data.segments = None

                if render_map_data.customized_cleaning != 1:
                    render_map_data.cleanset = None

                if (
                    render_map_data.cleanup_method is None
                    or render_map_data.cleanup_method != CleanupMethod.CUSTOMIZED_CLEANING
                ):
                    render_map_data.cleanset = None

                if render_map_data.task_cruise_points:
                    render_map_data.active_cruise_points = render_map_data.task_cruise_points.copy()
                    render_map_data.task_cruise_points = True
                    render_map_data.active_areas = None
                    render_map_data.path = None
                    render_map_data.no_mopping_areas = None
                    render_map_data.cleanset = None
                    if render_map_data.furnitures is not None:
                        render_map_data.furnitures = {}

                if render_map_data.segments:
                    if render_map_data.task_cruise_points or (
                        render_map_data.cleanup_method is not None
                        and (
                            render_map_data.cleanup_method == CleanupMethod.CLEANGENIUS
                            and not self.capability.cleangenius_mode
                        )
                    ):
                        render_map_data.sequence = False
                    elif render_map_data.active_segments:
                        order = 1
                        render_map_data.sequence = True
                        for segment_id in list(
                            sorted(
                                render_map_data.segments,
                                key=lambda segment_id: (
                                    render_map_data.segments[segment_id].order
                                    if render_map_data.segments[segment_id].order
                                    else 99
                                ),
                            )
                        ):
                            if (
                                len(render_map_data.active_segments) > 1
                                and render_map_data.segments[segment_id].order
                                and segment_id in render_map_data.active_segments
                            ):
                                render_map_data.segments[segment_id].order = order
                                order = order + 1
                            else:
                                render_map_data.segments[segment_id].order = None

                    if self.capability.cleaning_route:
                        for k, v in render_map_data.segments.items():
                            render_map_data.segments[k].custom_mopping_route = None

                return render_map_data

            if not render_map_data.saved_map and not render_map_data.recovery_map:
                # if self.status.started and (self.status.sweeping or self.status.cruising):
                #    # App does not render no mopping areas when cleaning mode is sweeping
                #    render_map_data.no_mopping_areas = None

                if not self.status._capability.cruising:
                    if self.status.go_to_zone:
                        render_map_data.active_cruise_points = {
                            1: Coordinate(
                                self.status.go_to_zone.x,
                                self.status.go_to_zone.y,
                                False,
                                0,
                            )
                        }
                        render_map_data.active_areas = None
                        render_map_data.path = None

                    if render_map_data.active_areas and len(render_map_data.active_areas) == 1:
                        area = render_map_data.active_areas[0]
                        size = render_map_data.dimensions.grid_size * 2
                        if area.check_size(size):
                            if self.status.started and not self.status.go_to_zone and self.status.zone_cleaning:
                                render_map_data.active_cruise_points = {
                                    1: Coordinate(
                                        area.x0 + render_map_data.dimensions.grid_size,
                                        area.y0 + render_map_data.dimensions.grid_size,
                                        False,
                                        0,
                                    )
                                }
                            render_map_data.active_areas = None
                            render_map_data.path = None

                if not self.status.go_to_zone and (
                    (self.status.zone_cleaning and render_map_data.active_areas)
                    or (self.status.spot_cleaning and render_map_data.active_points)
                ):
                    # App does not render segments when zone or spot cleaning
                    render_map_data.segments = None

                # App does not render pet obstacles when pet detection turned off
                # App does not render stain obstacles when stain avoidance turned off
                if render_map_data.obstacles:
                    obstacles = copy.deepcopy(render_map_data.obstacles)
                    for k, v in obstacles.items():
                        if (
                            (v.type == ObstacleType.PET and self.status.ai_pet_detection == 0)
                            or (
                                self.capability.fluid_detection
                                and (
                                    v.type == ObstacleType.LIQUID_STAIN
                                    or v.type == ObstacleType.DRIED_STAIN
                                    or v.type == ObstacleType.DETECTED_STAIN
                                    or v.type == ObstacleType.MIXED_STAIN
                                )
                                and not self.status.ai_fluid_detection
                            )
                            or (v.picture_status is not None and v.picture_status.value == 0)
                        ):
                            del render_map_data.obstacles[k]

                if render_map_data.furnitures and self.status.ai_furniture_detection == 0:
                    render_map_data.furnitures = {}

                # App adds robot position to paths as last line when map data is line to robot
                if render_map_data.line_to_robot and render_map_data.path and render_map_data.robot_position:
                    render_map_data.path.append(
                        Path(
                            render_map_data.robot_position.x,
                            render_map_data.robot_position.y,
                            PathType.LINE,
                        )
                    )

            if not self.status.customized_cleaning or self.status.cruising or self.status.cleangenius_cleaning:
                # App does not render customized cleaning settings on saved map list
                render_map_data.cleanset = None
            elif (
                not render_map_data.saved_map
                and not render_map_data.recovery_map
                and render_map_data.cleanset is None
                and self.status.customized_cleaning
                and not self.status.cleangenius_cleaning
            ):
                DreameVacuumMapDecoder.set_segment_cleanset(render_map_data, {}, self.capability)
                render_map_data.cleanset = True

            if render_map_data.segments:
                if not self.status.custom_order or render_map_data.saved_map or render_map_data.recovery_map:
                    render_map_data.sequence = False

                if self.capability.cleaning_route:
                    for k, v in render_map_data.segments.items():
                        render_map_data.segments[k].custom_mopping_route = None

            if render_map_data.robot_position:
                # Device currently may not be docked but map data can be old and still showing when robot is docked
                render_map_data.docked = bool(render_map_data.docked or self.status.docked)

            if (
                not self.capability.lidar_navigation
                and not render_map_data.saved_map
                and not render_map_data.recovery_map
                and render_map_data.saved_map_status == 1
                and render_map_data.docked
            ):
                # For correct scaling of vslam saved map
                render_map_data.saved_map_status = 2

            if (
                render_map_data.docked
                and render_map_data.robot_position
                and not render_map_data.saved_map
                and not render_map_data.recovery_map
            ):
                if render_map_data.charger_position == None:
                    if not self.status.multi_map:
                        render_map_data.charger_position = copy.deepcopy(render_map_data.robot_position)
                        if (
                            self.capability.robot_type != RobotType.MOPPING
                            and self.capability.robot_type != RobotType.SWEEPING_AND_MOPPING
                        ):
                            render_map_data.charger_position.a = render_map_data.robot_position.a + 180
                elif (
                    not self.status.docked
                    and not self.status.started
                    and render_map_data.robot_position.x == render_map_data.charger_position.x
                    and render_map_data.robot_position.y == render_map_data.charger_position.y
                ):
                    render_map_data.docked = False
                    render_map_data.robot_position = None

            if render_map_data.saved_map or render_map_data.recovery_map:
                render_map_data.active_areas = None
                render_map_data.active_points = None
                render_map_data.active_segments = None
                render_map_data.active_cruise_points = None
                render_map_data.path = None
                render_map_data.cleanset = None
            elif render_map_data.charger_position and render_map_data.docked and not self.status.fast_mapping:
                if not render_map_data.robot_position:
                    render_map_data.robot_position = copy.deepcopy(render_map_data.charger_position)
            return render_map_data
        return map_data

    def get_map(self, map_index: int) -> MapData | None:
        """Get stored map data by index from map manager."""
        if self._map_manager:
            if self.status.multi_map:
                return self._map_manager.get_map(map_index)
            if map_index == 1:
                return self._map_manager.selected_map
            if map_index == 0:
                return self.status.current_map

    def update_map(self) -> None:
        """Trigger a map update.
        This function is used for requesting map data when a image request has been made to renderer
        """

        self._last_change = time.time()
        if self._map_manager:
            now = time.time()
            if now - self._last_map_request > 120:
                self._last_map_request = now
                self._map_manager.set_update_interval(self._map_update_interval)
                self._map_manager.schedule_update(0.01)

    def update(self, force_request_properties=False) -> None:
        """Get properties from the device."""
        _LOGGER.debug("Device update: %s", self._update_interval)

        if self._update_running:
            return

        if not self.cloud_connected:
            self.connect_cloud()

        if not self.device_connected:
            self.connect_device()

        if not self.device_connected:
            raise DeviceUpdateFailedException("Device cannot be reached") from None

        # self._update_running = True

        # Read-only properties
        properties = [
            DreameVacuumProperty.STATE,
            DreameVacuumProperty.ERROR,
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
        ]

        if self.capability.backup_map:
            properties.append(DreameVacuumProperty.MAP_BACKUP_STATUS)

        now = time.time()
        if self.status.active:
            # Only changed when robot is active
            properties.extend([DreameVacuumProperty.CLEANED_AREA, DreameVacuumProperty.CLEANING_TIME])

        if self._consumable_change:
            # Consumable properties
            properties.extend(
                [
                    DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT,
                    DreameVacuumProperty.MAIN_BRUSH_LEFT,
                    DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT,
                    DreameVacuumProperty.SIDE_BRUSH_LEFT,
                    DreameVacuumProperty.FILTER_LEFT,
                    DreameVacuumProperty.FILTER_TIME_LEFT,
                    DreameVacuumProperty.MOP_PAD_LEFT,
                    DreameVacuumProperty.MOP_PAD_TIME_LEFT,
                    DreameVacuumProperty.DETERGENT_LEFT,
                    DreameVacuumProperty.DETERGENT_TIME_LEFT,
                    DreameVacuumProperty.SQUEEGEE_LEFT,
                    DreameVacuumProperty.SQUEEGEE_TIME_LEFT,
                    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT,
                    DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT,
                    DreameVacuumProperty.DIRTY_WATER_TANK_LEFT,
                    DreameVacuumProperty.DIRTY_WATER_TANK_TIME_LEFT,
                    DreameVacuumProperty.SILVER_ION_LEFT,
                    DreameVacuumProperty.SILVER_ION_TIME_LEFT,
                    DreameVacuumProperty.TANK_FILTER_LEFT,
                    DreameVacuumProperty.TANK_FILTER_TIME_LEFT,
                    DreameVacuumProperty.DEODORIZER_LEFT,
                    DreameVacuumProperty.DEODORIZER_TIME_LEFT,
                    DreameVacuumProperty.WHEEL_DIRTY_LEFT,
                    DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT,
                    DreameVacuumProperty.SCALE_INHIBITOR_LEFT,
                    DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT,
                ]
            )

            if not self.capability.disable_sensor_cleaning:
                properties.extend(
                    [
                        DreameVacuumProperty.SENSOR_DIRTY_LEFT,
                        DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
                    ]
                )

        if now - self._last_settings_request > 9.5:
            self._last_settings_request = now

            if not self._consumable_change and self.status.washing:
                properties.extend(
                    [
                        DreameVacuumProperty.DETERGENT_LEFT,
                        DreameVacuumProperty.DETERGENT_TIME_LEFT,
                        DreameVacuumProperty.SQUEEGEE_LEFT,
                        DreameVacuumProperty.SQUEEGEE_TIME_LEFT,
                        DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT,
                        DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT,
                        DreameVacuumProperty.DIRTY_WATER_TANK_LEFT,
                        DreameVacuumProperty.DIRTY_WATER_TANK_TIME_LEFT,
                        DreameVacuumProperty.SCALE_INHIBITOR_LEFT,
                        DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT,
                        DreameVacuumProperty.DEODORIZER_LEFT,
                        DreameVacuumProperty.DEODORIZER_TIME_LEFT,
                    ]
                )

            properties.extend(self._read_write_properties)

            if not self.capability.dnd_task:
                properties.extend(
                    [
                        DreameVacuumProperty.DND,
                        DreameVacuumProperty.DND_START,
                        DreameVacuumProperty.DND_END,
                    ]
                )

        if self._map_manager and not self.status.running and now - self._last_map_list_request > 60:
            properties.extend([DreameVacuumProperty.MAP_LIST, DreameVacuumProperty.RECOVERY_MAP_LIST])
            self._last_map_list_request = time.time()

        try:
            if self._protocol.dreame_cloud and (not self.device_connected or not self.cloud_connected):
                force_request_properties = True

            if not self._protocol.dreame_cloud or force_request_properties:
                self._request_properties(properties)
            elif self.status.map_backup_status:
                self._request_properties([DreameVacuumProperty.MAP_BACKUP_STATUS])
            elif self.status.map_recovery_status:
                self._request_properties([DreameVacuumProperty.MAP_RECOVERY_STATUS])
        except Exception as ex:
            self._update_running = False
            raise DeviceUpdateFailedException(ex) from None

        if self._dirty_data:
            for k, v in copy.deepcopy(self._dirty_data).items():
                if time.time() - v.update_time >= self._restore_timeout:
                    if v.previous_value is not None:
                        value = self.data.get(k)
                        if value is None or v.value == value:
                            _LOGGER.info(
                                "Property %s Value Restored: %s <- %s",
                                DreameVacuumProperty(k).name,
                                v.previous_value,
                                value,
                            )
                            self.data[k] = v.previous_value
                            if k in self._property_update_callback:
                                for callback in self._property_update_callback[k]:
                                    callback(v.previous_value)

                            self._property_changed(False)
                            self.schedule_update(1, True)
                    del self._dirty_data[k]

        if self._dirty_auto_switch_data:
            for k, v in copy.deepcopy(self._dirty_auto_switch_data).items():
                if time.time() - v.update_time >= self._restore_timeout:
                    if v.previous_value is not None:
                        value = self.auto_switch_data.get(k)
                        ## TODO
                        # if value is None or v.value == value:
                        #    _LOGGER.info(
                        #        "Property %s Value Restored: %s <- %s",
                        #        k,
                        #        v.previous_value,
                        #        value,
                        #    )
                        #    self.auto_switch_data[k] = v.previous_value
                        #    self._property_changed(False)
                        #    self.schedule_update(1, True)
                    del self._dirty_auto_switch_data[k]

        if self._dirty_ai_data:
            for k, v in copy.deepcopy(self._dirty_ai_data).items():
                if time.time() - v.update_time >= self._restore_timeout:
                    if v.previous_value is not None:
                        value = self.ai_data.get(k)
                        ## TODO
                        # if value is None or v.value == value:
                        #    _LOGGER.info(
                        #        "AI Property %s Value Restored: %s <- %s",
                        #        k,
                        #        v.previous_value,
                        #        value,
                        #    )
                        #    self.ai_data[k] = v.previous_value
                        #    self._property_changed(False)
                        #    self.schedule_update(1, True)
                    del self._dirty_ai_data[k]

        if self._consumable_change:
            self._consumable_change = False

        if self._map_manager:
            if (
                not self.status.started
                and not self.status.running
                and self._last_map_change_time is not None
                and now - self._last_map_change_time > 120
            ):
                self._last_map_change_time = None
                self._map_manager.request_next_map_list()
                self._map_manager.request_next_recovery_map_list()
            self._map_manager.set_update_interval(self._map_update_interval)
            self._map_manager.set_device_running(self.status.running, self.status.docked and not self.status.started)

        # Reset drainage status after 10 minutes
        if self._draining_complete_time is not None and now - self._draining_complete_time > 600:
            self._draining_complete_time = None
            if self.status.draining_complete:
                self.set_property(DreameVacuumProperty.DRAINAGE_STATUS, 0)

        if self.cloud_connected:
            self._request_cleaning_history()

        self._update_running = False

    def call_stream_audio_action(self, property: DreameVacuumProperty, parameters=None):
        return self.call_stream_action(DreameVacuumAction.STREAM_AUDIO, property, parameters)

    def call_stream_video_action(self, property: DreameVacuumProperty, parameters=None):
        return self.call_stream_action(DreameVacuumAction.STREAM_VIDEO, property, parameters)

    def call_stream_property_action(self, property: DreameVacuumProperty, parameters=None):
        return self.call_stream_action(DreameVacuumAction.STREAM_PROPERTY, property, parameters)

    def call_stream_action(
        self,
        action: DreameVacuumAction,
        property: DreameVacuumProperty,
        parameters=None,
    ):
        params = {"session": self.status.stream_session}
        if parameters:
            params.update(parameters)
        return self.call_action(
            action,
            [
                {
                    "piid": PIID(property),
                    "value": str(json.dumps(params, separators=(",", ":"))).replace(" ", ""),
                }
            ],
        )

    def call_shortcut_action(self, command: str, parameters={}):
        return self.call_action(
            DreameVacuumAction.SHORTCUTS,
            [
                {
                    "piid": PIID(DreameVacuumProperty.CLEANING_PROPERTIES),
                    "value": str(
                        json.dumps(
                            {"cmd": command, "params": parameters},
                            separators=(",", ":"),
                        )
                    ).replace(" ", ""),
                }
            ],
        )

    def call_shortcut_action_async(self, callback, command: str, parameters={}):
        mapping = self.action_mapping[DreameVacuumAction.SHORTCUTS]
        return self._protocol.action_async(
            callback,
            mapping["siid"],
            mapping["aiid"],
            [
                {
                    "piid": PIID(DreameVacuumProperty.CLEANING_PROPERTIES),
                    "value": str(
                        json.dumps(
                            {"cmd": command, "params": parameters},
                            separators=(",", ":"),
                        )
                    ).replace(" ", ""),
                }
            ],
        )

    def call_action(self, action: DreameVacuumAction, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        """Call an action."""
        if action not in self.action_mapping:
            raise InvalidActionException(f"Unable to find {action} in the action mapping")

        mapping = self.action_mapping[action]
        if "siid" not in mapping or "aiid" not in mapping:
            raise InvalidActionException(f"{action} is not an action (missing siid or aiid)")

        if self.status.draining_complete:
            self.set_property(DreameVacuumProperty.DRAINAGE_STATUS, 0)

        map_action = bool(action is DreameVacuumAction.REQUEST_MAP or action is DreameVacuumAction.UPDATE_MAP_DATA)

        if not map_action:
            self.schedule_update(10, True)

        cleaning_action = bool(
            action
            in [
                DreameVacuumAction.START,
                DreameVacuumAction.START_CUSTOM,
                DreameVacuumAction.PAUSE,
                DreameVacuumAction.STOP,
                DreameVacuumAction.CHARGE,
            ]
        )

        if not cleaning_action:
            available_fn = ACTION_AVAILABILITY.get(action.name)
            if available_fn and not available_fn(self):
                raise InvalidActionException("Action unavailable")
        elif self._map_select_time:
            elapsed = time.time() - self._map_select_time
            self._map_select_time = None
            if elapsed < 5:
                time.sleep(5 - elapsed)

        # Reset consumable on memory
        if action is DreameVacuumAction.RESET_MAIN_BRUSH:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.MAIN_BRUSH_LEFT, 100)
            self._update_property(DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT, 300)
        elif action is DreameVacuumAction.RESET_SIDE_BRUSH:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SIDE_BRUSH_LEFT, 100)
            self._update_property(DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT, 200)
        elif action is DreameVacuumAction.RESET_FILTER:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.FILTER_LEFT, 100)
            self._update_property(DreameVacuumProperty.FILTER_TIME_LEFT, 150)
        elif action is DreameVacuumAction.RESET_SENSOR:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SENSOR_DIRTY_LEFT, 100)
            self._update_property(DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT, 30)
        elif action is DreameVacuumAction.RESET_TANK_FILTER:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.TANK_FILTER_LEFT, 100)
            self._update_property(DreameVacuumProperty.TANK_FILTER_TIME_LEFT, 30)
        elif action is DreameVacuumAction.RESET_MOP_PAD:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.MOP_PAD_LEFT, 100)
            self._update_property(DreameVacuumProperty.MOP_PAD_TIME_LEFT, 80)
        elif action is DreameVacuumAction.RESET_SILVER_ION:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SILVER_ION_LEFT, 100)
            self._update_property(DreameVacuumProperty.SILVER_ION_TIME_LEFT, 365)
        elif action is DreameVacuumAction.RESET_DETERGENT:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.DETERGENT_LEFT, 100)
            self._update_property(DreameVacuumProperty.DETERGENT_TIME_LEFT, 18)
        elif action is DreameVacuumAction.RESET_SQUEEGEE:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SQUEEGEE_LEFT, 100)
            self._update_property(DreameVacuumProperty.SQUEEGEE_TIME_LEFT, 100)
        elif action is DreameVacuumAction.RESET_ONBOARD_DIRTY_WATER_TANK:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT, 100)
            self._update_property(DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT, 100)
        elif action is DreameVacuumAction.RESET_DIRTY_WATER_TANK:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.DIRTY_WATER_TANK_LEFT, 100)
            self._update_property(DreameVacuumProperty.DIRTY_WATER_TANK_TIME_LEFT, 100)
        elif action is DreameVacuumAction.RESET_DEODORIZER:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.DEODORIZER_LEFT, 100)
            self._update_property(DreameVacuumProperty.DEODORIZER_TIME_LEFT, 180)
        elif action is DreameVacuumAction.RESET_WHEEL:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.WHEEL_DIRTY_LEFT, 100)
            self._update_property(DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT, 30)
        elif action is DreameVacuumAction.RESET_SCALE_INHIBITOR:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SCALE_INHIBITOR_LEFT, 100)
            self._update_property(DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT, 1095)

        elif action is DreameVacuumAction.START_AUTO_EMPTY:
            self._update_property(
                DreameVacuumProperty.AUTO_EMPTY_STATUS,
                DreameVacuumAutoEmptyStatus.ACTIVE.value,
            )
        elif action is DreameVacuumAction.CLEAR_WARNING:
            self._update_property(DreameVacuumProperty.ERROR, DreameVacuumErrorCode.NO_ERROR.value)

        # Update listeners
        if cleaning_action or self._consumable_change:
            self._property_changed(False)

        try:
            result = self._protocol.action(mapping["siid"], mapping["aiid"], parameters)
        except Exception as ex:
            _LOGGER.error("Send action failed %s: %s", action.name, ex)
            self.schedule_update(1, True)
            return

        # Schedule update for retrieving new properties after action sent
        self.schedule_update(6, bool(not map_action and self._protocol.dreame_cloud))
        if result and result.get("code") == 0:
            _LOGGER.info("Send action %s %s", action.name, parameters)
            self._last_change = time.time()
            if not map_action:
                self._last_settings_request = 0
        else:
            _LOGGER.error("Send action failed %s (%s): %s", action.name, parameters, result)

        return result

    def send_command(self, command: str, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        """Send a raw command to the device. This is mostly useful when trying out
        commands which are not implemented by a given device instance. (Not likely)"""

        if command == "":
            raise InvalidActionException(f"Invalid Command: ({command}).")

        self.schedule_update(10, True)
        response = self._protocol.send(command, parameters, 3)
        if response:
            _LOGGER.info("Send command response: %s", response)
        self.schedule_update(2, True)

    def set_volume(self, volume: int) -> bool:
        """Set volume."""
        result = self.set_property(DreameVacuumProperty.VOLUME, volume)
        if result:
            self.call_action(DreameVacuumAction.TEST_SOUND)
        return result

    def set_suction_level(self, suction_level: int) -> bool:
        """Set suction level."""
        if self.status.cruising:
            raise InvalidActionException("Cannot set suction level when cruising")

        if self.status.started and (
            self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning)
        ):
            raise InvalidActionException("Cannot set suction level when customized cleaning is enabled")
        return self._update_suction_level(suction_level)

    def set_cleaning_mode(self, cleaning_mode: int) -> bool:
        """Set cleaning mode."""
        if self.status.cleaning_mode is None:
            raise InvalidActionException("Cleaning mode is not supported on this device")

        if self.status.cruising:
            raise InvalidActionException("Cannot set cleaning mode when cruising")

        if self.status.draining:
            raise InvalidActionException("Cannot set cleaning mode when draining")

        if self.status.scheduled_clean or self.status.shortcut_task:
            raise InvalidActionException("Cannot set cleaning mode when scheduled cleaning or shortcut task")

        if (
            self.status.started
            and self.capability.custom_cleaning_mode
            and (self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning))
        ):
            raise InvalidActionException("Cannot set cleaning mode when customized cleaning is enabled")

        cleaning_mode = int(cleaning_mode)
        if cleaning_mode == DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING.value and (
            not self.capability.mopping_after_sweeping
            or (
                self.status.started
                and self.status.cleaning_mode is not DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
            )
        ):
            raise InvalidActionException("Cannot set mopping after sweeping")

        if not self.status.auto_mount_mop or not self.status.mop_in_station:
            if cleaning_mode == DreameVacuumCleaningMode.SWEEPING.value:
                if self.status.water_tank_or_mop_installed and not self.capability.mop_pad_lifting:
                    if self.capability.self_wash_base:
                        raise InvalidActionException("Cannot set sweeping while mop pads are installed")
                    else:
                        raise InvalidActionException("Cannot set sweeping while water tank is installed")
            elif not self.status.water_tank_or_mop_installed:
                if self.capability.self_wash_base:
                    raise InvalidActionException("Cannot set mopping while mop pads are not installed")
                else:
                    raise InvalidActionException("Cannot set mopping while water tank is not installed")

        if self.status.started and not PROPERTY_AVAILABILITY[DreameVacuumProperty.CLEANING_MODE.name](self):
            raise InvalidActionException("Cleaning mode unavailable")

        return self._update_cleaning_mode(cleaning_mode)

    def set_self_clean_area(self, self_clean_area: int) -> bool:
        """Set self clean area."""
        if self.capability.self_wash_base and (
            not self.capability.self_clean_frequency or not self.status.self_clean_by_time
        ):
            return self.set_self_clean_value(self_clean_area)

    def set_self_clean_time(self, self_clean_time: int) -> bool:
        """Set self clean time."""
        if self.capability.self_wash_base and self.capability.self_clean_frequency and self.status.self_clean_by_time:
            return self.set_self_clean_value(self_clean_time)

    def set_self_clean_value(self, self_clean_value: int) -> bool:
        """Set self clean value."""
        if self.capability.self_wash_base:
            current_self_clean_value = self.status.self_clean_value
            if self._update_self_clean_value(self_clean_value):
                if self_clean_value and self_clean_value != current_self_clean_value:
                    if self.status.self_clean_by_time:
                        self.status.previous_self_clean_time = self_clean_value
                    else:
                        self.status.previous_self_clean_area = self_clean_value
                return True
        return False

    def set_mop_clean_frequency(self, mop_clean_frequency: int) -> bool:
        """Set mop clean frequency."""
        if self.capability.self_wash_base and self.capability.mop_clean_frequency:
            return self.set_self_clean_value(mop_clean_frequency)

    def set_mop_pad_humidity(self, mop_pad_humidity: int) -> bool:
        """Set mop pad humidity."""
        if self.capability.self_wash_base:
            if self.status.cruising:
                raise InvalidActionException("Cannot set mop pad humidity when cruising")

            if self.status.started and (
                self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning)
            ):
                raise InvalidActionException("Cannot set mop pad humidity when customized cleaning is enabled")
            return self._update_water_level(mop_pad_humidity)
        return False

    def set_water_volume(self, water_volume: int) -> bool:
        """Set water volume."""
        if not self.capability.self_wash_base:
            if self.status.cruising:
                raise InvalidActionException("Cannot set water level when cruising")

            if self.status.started and (
                self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning)
            ):
                raise InvalidActionException("Cannot set water volume when customized cleaning is enabled")

            return self._update_water_level(water_volume)
        return False

    def set_wetness_level(self, wetness_level: int) -> bool:
        """Set wetness level."""
        if self.capability.wetness:
            if self.status.started and (
                self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning)
            ):
                raise InvalidActionException("Cannot set wetness level when customized cleaning is enabled")

            if self.capability.self_wash_base and self.capability.wetness_level:
                if (
                    wetness_level > 26
                    and self.status.self_clean_value > 20
                    and (
                        not self.capability.self_clean_frequency
                        or (
                            self.status.self_clean_frequency == DreameVacuumSelfCleanFrequency.BY_TIME
                            or self.status.self_clean_frequency == DreameVacuumSelfCleanFrequency.BY_ROOM
                        )
                    )
                ):
                    self.set_self_clean_value(20)

            return self.set_property(DreameVacuumProperty.WETNESS_LEVEL, int(wetness_level))
        return False

    def set_dnd_task(self, enabled: bool, dnd_start: str, dnd_end: str) -> bool:
        """Set do not disturb task"""
        if dnd_start is None or dnd_start == "":
            dnd_start = "22:00"

        if dnd_end is None or dnd_end == "":
            dnd_end = "08:00"

        time_pattern = re.compile("([0-1][0-9]|2[0-3]):[0-5][0-9]$")
        if not re.match(time_pattern, dnd_start):
            raise InvalidValueException("DnD start time is not valid: (%s).", dnd_start)
        if not re.match(time_pattern, dnd_end):
            raise InvalidValueException("DnD end time is not valid: (%s).", dnd_end)
        if dnd_start == dnd_end:
            raise InvalidValueException(
                "DnD Start time must be different from DnD end time: (%s == %s).",
                dnd_start,
                dnd_end,
            )

        if self.status.dnd_tasks is None:
            self.status.dnd_tasks = []

        if len(self.status.dnd_tasks) == 0:
            self.status.dnd_tasks.append(
                {
                    "id": 1,
                    "en": enabled,
                    "st": dnd_start,
                    "et": dnd_end,
                    "wk": 127,
                    "ss": 0,
                }
            )
        else:
            self.status.dnd_tasks[0]["en"] = enabled
            self.status.dnd_tasks[0]["st"] = dnd_start
            self.status.dnd_tasks[0]["et"] = dnd_end
        return self.set_property(
            DreameVacuumProperty.DND_TASK,
            str(json.dumps(self.status.dnd_tasks, separators=(",", ":"))).replace(" ", ""),
        )

    def set_dnd(self, enabled: bool) -> bool:
        """Set do not disturb function"""
        return (
            self.set_property(DreameVacuumProperty.DND, bool(enabled))
            if not self.capability.dnd_task
            else self.set_dnd_task(bool(enabled), self.status.dnd_start, self.status.dnd_end)
        )

    def set_dnd_start(self, dnd_start: str) -> bool:
        """Set do not disturb function"""
        return (
            self.set_property(DreameVacuumProperty.DND_START, dnd_start)
            if not self.capability.dnd_task
            else self.set_dnd_task(self.status.dnd, str(dnd_start), self.status.dnd_end)
        )

    def set_dnd_end(self, dnd_end: str) -> bool:
        """Set do not disturb function"""
        if not self.capability.dnd_task:
            return self.set_property(DreameVacuumProperty.DND_END, dnd_end)
        return self.set_dnd_task(self.status.dnd, self.status.dnd_start, str(dnd_end))

    def set_off_peak_charging_config(self, enabled: bool, start: str, end: str) -> bool:
        """Set of peak charging config"""
        if start is None or start == "":
            start = "22:00"

        if end is None or end == "":
            end = "08:00"

        time_pattern = re.compile("([0-1][0-9]|2[0-3]):[0-5][0-9]$")
        if not re.match(time_pattern, start):
            raise InvalidValueException("Start time is not valid: (%s).", start)
        if not re.match(time_pattern, end):
            raise InvalidValueException("End time is not valid: (%s).", end)
        if start == end:
            raise InvalidValueException("Start time must be different from end time: (%s == %s).", start, end)

        self.status.off_peak_charging_config = {
            "enable": enabled,
            "startTime": start,
            "endTime": end,
        }
        return self.set_property(
            DreameVacuumProperty.OFF_PEAK_CHARGING,
            str(json.dumps(self.status.off_peak_charging_config, separators=(",", ":"))).replace(" ", ""),
        )

    def set_off_peak_charging(self, enabled: bool) -> bool:
        """Set off peak charging function"""
        return self.set_off_peak_charging_config(
            bool(enabled),
            self.status.off_peak_charging_start,
            self.status.off_peak_charging_end,
        )

    def set_off_peak_charging_start(self, off_peak_charging_start: str) -> bool:
        """Set off peak charging function"""
        return self.set_off_peak_charging_config(
            self.status.off_peak_charging,
            str(off_peak_charging_start),
            self.status.off_peak_charging_end,
        )

    def set_off_peak_charging_end(self, off_peak_charging_end: str) -> bool:
        """Set off peak charging function"""
        return self.set_off_peak_charging_config(
            self.status.off_peak_charging,
            self.status.off_peak_charging_start,
            str(off_peak_charging_end),
        )

    def set_voice_assistant_language(self, voice_assistant_language: str) -> bool:
        if (
            self.get_property(DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE) is None
            or voice_assistant_language is None
            or len(voice_assistant_language) < 2
            or voice_assistant_language.upper() not in DreameVacuumVoiceAssistantLanguage.__members__
        ):
            raise InvalidActionException(f"Voice assistant language ({voice_assistant_language}) is not supported")
        return self.set_property(
            DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE,
            DreameVacuumVoiceAssistantLanguage[voice_assistant_language.upper()],
        )

    def set_washing_mode(self, washing_mode: int) -> bool:
        if self.capability.smart_mop_washing:
            result = False
            if washing_mode < 3:
                if washing_mode != self.status.mop_wash_level.value:
                    result = self.set_property(DreameVacuumProperty.MOP_WASH_LEVEL, washing_mode)
                if result and self.status.ultra_clean_mode:
                    result = self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE, 0)
            elif self.capability.ultra_clean_mode:
                result = self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE, 1)

            if result and self.status.smart_mop_washing:
                self.set_property(DreameVacuumProperty.SMART_MOP_WASHING, 0)

    def set_mop_wash_level(self, mop_wash_level: int) -> bool:
        if not self.capability.smart_mop_washing:
            result = self.set_property(DreameVacuumProperty.MOP_WASH_LEVEL, mop_wash_level)
            if result and self.capability.ultra_clean_mode and self.status.ultra_clean_mode:
                return self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE, 0)

    def set_drying_time(self, drying_time: int) -> bool:
        result = self.set_property(DreameVacuumProperty.DRYING_TIME, drying_time)
        if result and self.capability.silent_drying and self.status.silent_drying:
            return self.set_property(DreameVacuumProperty.SILENT_DRYING, 0)

    def delete_schedule(self, schedule_id) -> dict[str, Any] | None:
        """Delete a scheduled task."""
        found = False
        for schedule in self.status.schedule:
            if str(schedule.id) == str(schedule_id):
                found = True
                break

        if not found:
            raise InvalidActionException(f"Schedule not found! (%s)", schedule_id)

        schedule_list = self.get_property(DreameVacuumProperty.SCHEDULE)
        if schedule_list and schedule_list != "":
            tasks = schedule_list.split(";")
            schedule = ""
            for task in tasks:
                props = task.split("-")
                if props[0] != str(schedule_id):
                    if len(schedule) > 1:
                        schedule = f"{schedule};"
                    schedule = f"{schedule}{task}"
            self.set_property(DreameVacuumProperty.SCHEDULE, schedule)

        response = self.call_action(
            DreameVacuumAction.DELETE_SCHEDULE,
            [
                {
                    "piid": PIID(DreameVacuumProperty.SCHEDULE_ID, self.property_mapping),
                    "value": schedule_id,
                }
            ],
        )
        self.schedule_update(3, True)
        if not response or response.get("code") != 0:
            self.set_property(DreameVacuumProperty.SCHEDULE, schedule_list)
        return response

    def locate(self) -> dict[str, Any] | None:
        """Locate the vacuum cleaner."""
        return self.call_action(DreameVacuumAction.LOCATE)

    def start(self) -> dict[str, Any] | None:
        """Start or resume the cleaning task."""
        if self.status.fast_mapping_paused:
            self._update_status(DreameVacuumTaskStatus.FAST_MAPPING, DreameVacuumStatus.FAST_MAPPING)
            return self.start_custom(DreameVacuumStatus.FAST_MAPPING.value)

        if self.status.returning_paused:
            return self.return_to_base()

        if self.status.returning_to_wash_paused:
            return self.start_washing()

        if self.capability.cruising:
            if self.status.cruising_paused:
                return self.start_custom(self.status.status.value)
        elif not self.status.paused:
            self._restore_go_to_zone()

        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException("Cannot start cleaning while draining or self repairing/testing")

        self.schedule_update(10, True)

        if not self.status.started:
            self._update_status(DreameVacuumTaskStatus.AUTO_CLEANING, DreameVacuumStatus.CLEANING)
        elif (
            self.status.paused
            and not self.status.cleaning_paused
            and not self.status.cruising
            and not self.status.scheduled_clean
        ):
            self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.CLEANING.value)
            if self.status.task_status is not DreameVacuumTaskStatus.COMPLETED:
                new_state = DreameVacuumState.SWEEPING
                if self.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING:
                    new_state = DreameVacuumState.MOPPING
                elif self.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING_AND_MOPPING:
                    new_state = DreameVacuumState.SWEEPING_AND_MOPPING
                self._update_property(DreameVacuumProperty.STATE, new_state.value)

        if self._map_manager:
            if not self.status.started:
                self._map_manager.editor.clear_path()
            self._map_manager.editor.refresh_map()

        return self.call_action(DreameVacuumAction.START)

    def start_custom(self, status, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        """Start custom cleaning task."""
        if not self.capability.cruising and status != DreameVacuumStatus.ZONE_CLEANING.value:
            self._restore_go_to_zone()

        if status is not DreameVacuumStatus.FAST_MAPPING.value and self.status.fast_mapping:
            raise InvalidActionException("Cannot start cleaning while fast mapping")

        payload = [
            {
                "piid": PIID(DreameVacuumProperty.STATUS, self.property_mapping),
                "value": status,
            }
        ]

        if parameters is not None:
            payload.append(
                {
                    "piid": PIID(DreameVacuumProperty.CLEANING_PROPERTIES, self.property_mapping),
                    "value": parameters,
                }
            )

        return self.call_action(DreameVacuumAction.START_CUSTOM, payload)

    def stop(self) -> dict[str, Any] | None:
        """Stop the vacuum cleaner."""
        if self.status.fast_mapping:
            return self.return_to_base()

        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot stop while draining or self repairing/testing")

        self.schedule_update(10, True)

        response = None
        if self.status.go_to_zone:
            response = self.call_action(DreameVacuumAction.STOP)

        if self.status.started:
            self._update_status(DreameVacuumTaskStatus.COMPLETED, DreameVacuumStatus.STANDBY)

            # Clear active segments on current map data
            if self._map_manager:
                if self.status.go_to_zone:
                    self._map_manager.editor.set_active_areas([])
                self._map_manager.editor.set_cruise_points([])
                self._map_manager.editor.set_active_segments([])
        elif self.status.drying:
            return self.stop_drying()

        if response:
            return response

        return self.call_action(DreameVacuumAction.STOP)

    def pause(self) -> dict[str, Any] | None:
        """Pause the cleaning task."""
        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot pause while draining or self repairing/testing")

        self.schedule_update(10, True)

        if not self.status.started and self.status.washing:
            return self.pause_washing()

        if not self.status.paused and self.status.started:
            if self.status.cruising and not self.capability.cruising:
                self._update_property(
                    DreameVacuumProperty.STATE,
                    DreameVacuumState.MONITORING_PAUSED.value,
                )
            else:
                self._update_property(DreameVacuumProperty.STATE, DreameVacuumState.PAUSED.value)
            self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.PAUSED.value)
            if self.status.go_to_zone:
                self._update_property(
                    DreameVacuumProperty.TASK_STATUS,
                    DreameVacuumTaskStatus.CRUISING_POINT_PAUSED.value,
                )

        return self.call_action(DreameVacuumAction.PAUSE)

    def return_to_base(self) -> dict[str, Any] | None:
        """Set the vacuum cleaner to return to the dock."""
        if self._map_manager:
            self._map_manager.editor.set_cruise_points([])

        # if self.status.started:
        if not self.status.docked:
            self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.BACK_HOME.value)
            self._update_property(DreameVacuumProperty.STATE, DreameVacuumState.RETURNING.value)

        # Clear active segments on current map data
        # if self._map_manager:
        #    self._map_manager.editor.set_active_segments([])

        if not self.capability.cruising:
            self._restore_go_to_zone()
        return self.call_action(DreameVacuumAction.CHARGE)

    def start_pause(self) -> dict[str, Any] | None:
        """Start or resume the cleaning task."""
        if (
            not self.status.started
            or self.status.state is DreameVacuumState.PAUSED
            or self.status.status is DreameVacuumStatus.BACK_HOME
        ):
            return self.start()
        return self.pause()

    def clean_zone(
        self,
        zones: list[int] | list[list[int]],
        cleaning_times: int | list[int],
        suction_level: int | list[int],
        water_volume: int | list[int],
    ) -> dict[str, Any] | None:
        """Clean selected area."""
        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot start cleaning while draining or self repairing/testing")

        if not isinstance(zones, list) or not zones:
            raise InvalidActionException(f"Invalid zone coordinates: %s", zones)

        if not isinstance(zones[0], list):
            zones = [zones]

        if suction_level is None or suction_level == "":
            suction_level = self.status.suction_level.value
        else:
            self._update_suction_level(suction_level[0] if isinstance(suction_level, list) else suction_level)

        if water_volume is None or water_volume == "":
            water_volume = self.status.water_volume.value
        else:
            self._update_water_level(int(water_volume[0] if isinstance(water_volume, list) else water_volume))

        if cleaning_times is None or cleaning_times == "":
            cleaning_times = 1

        cleanlist = []
        index = 0
        for zone in zones:
            if not isinstance(zone, list) or len(zone) != 4:
                raise InvalidActionException(f"Invalid zone coordinates: %s", zone)

            if isinstance(cleaning_times, list):
                if index < len(cleaning_times):
                    repeat = cleaning_times[index]
                else:
                    repeat = 1
            else:
                repeat = cleaning_times

            if isinstance(suction_level, list):
                if index < len(suction_level):
                    fan = suction_level[index]
                else:
                    fan = self.status.suction_level.value
            else:
                fan = suction_level

            if isinstance(water_volume, list):
                if index < len(water_volume):
                    water = water_volume[index]
                else:
                    if self.capability.self_wash_base:
                        water = self.status.mop_pad_humidity
                    else:
                        water = self.status.water_volume.value
            else:
                water = water_volume

            index = index + 1

            x_coords = sorted([zone[0], zone[2]])
            y_coords = sorted([zone[1], zone[3]])

            size = (self.status.current_map.dimensions.grid_size * 2) if self.status.current_map else 100
            w = (x_coords[1] - x_coords[0]) / size
            h = (y_coords[1] - y_coords[0]) / size

            if h <= 1.0 or w <= 1.0:
                raise InvalidActionException(f"Zone {index} is smaller than minimum zone size ({h}, {w})")

            cleanlist.append(
                [
                    int(round(zone[0])),
                    int(round(zone[1])),
                    int(round(zone[2])),
                    int(round(zone[3])),
                    max(1, repeat),
                    fan,
                    water,
                ]
            )

        self.schedule_update(10, True)
        if not self.capability.cruising:
            self._restore_go_to_zone()

        if self.status.cleangenius_cleaning:
            self._previous_cleangenius = self.get_property(DreameVacuumAutoSwitchProperty.CLEANGENIUS)
            self.set_auto_switch_property(
                DreameVacuumAutoSwitchProperty.CLEANGENIUS, DreameVacuumCleanGenius.OFF.value
            )
        else:
            self._previous_cleangenius = None

        if not self.status.started or self.status.paused:
            self._update_status(DreameVacuumTaskStatus.ZONE_CLEANING, DreameVacuumStatus.ZONE_CLEANING)

            if self._map_manager:
                # Set active areas on current map data is implemented on the app
                if not self.status.started:
                    self._map_manager.editor.clear_path()
                self._map_manager.editor.set_active_areas(zones)

        return self.start_custom(
            DreameVacuumStatus.ZONE_CLEANING.value,
            str(json.dumps({"areas": cleanlist}, separators=(",", ":"))).replace(" ", ""),
        )

    def clean_segment(
        self,
        selected_segments: int | list[int],
        cleaning_times: int | list[int] | None = None,
        suction_level: int | list[int] | None = None,
        water_volume: int | list[int] | None = None,
        timestamp: int | None = None,
    ) -> dict[str, Any] | None:
        """Clean selected segment using id."""
        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot start cleaning while draining or self repairing/testing")

        if self.status.current_map and not self.status.has_saved_map:
            raise InvalidActionException("Cannot clean segments on current map")

        if not isinstance(selected_segments, list):
            selected_segments = [selected_segments]

        if suction_level is None or suction_level == "":
            suction_level = self.status.suction_level.value

        if water_volume is None or water_volume == "":
            water_volume = self.status.water_volume.value

        if cleaning_times is None or cleaning_times == "":
            cleaning_times = 1

        cleanlist = []
        index = 0
        segments = self.status.current_segments

        for segment_id in selected_segments:
            if isinstance(cleaning_times, list):
                if index < len(cleaning_times):
                    repeat = cleaning_times[index]
                else:
                    if segments and segment_id in segments and self.status.customized_cleaning:
                        repeat = segments[segment_id].cleaning_times
                    else:
                        repeat = 1
            else:
                repeat = cleaning_times

            if isinstance(suction_level, list):
                if index < len(suction_level):
                    fan = suction_level[index]
                elif segments and segment_id in segments and self.status.customized_cleaning:
                    fan = segments[segment_id].suction_level
                else:
                    fan = self.status.suction_level.value
            else:
                fan = suction_level

            if isinstance(water_volume, list):
                if index < len(water_volume):
                    water = water_volume[index]
                elif segments and segment_id in segments and self.status.customized_cleaning:
                    water = segments[segment_id].water_volume
                else:
                    if self.capability.self_wash_base:
                        water = self.status.mop_pad_humidity
                    else:
                        water = self.status.water_volume.value
            else:
                water = water_volume

            index = index + 1
            cleanlist.append(
                [segment_id, max(1, repeat), fan, water, 1 if self.capability.customized_cleaning else index]
            )  ## Sending index other than 1 breaks the operation of 5th gen devices

        self.schedule_update(10, True)
        if not self.status.started or self.status.paused:
            self._update_status(
                DreameVacuumTaskStatus.SEGMENT_CLEANING,
                DreameVacuumStatus.SEGMENT_CLEANING,
            )

            if self._map_manager:
                if not self.status.started:
                    self._map_manager.editor.clear_path()

                # Set active segments on current map data is implemented on the app
                self._map_manager.editor.set_active_segments(selected_segments)

        data = {"selects": cleanlist}
        if timestamp is not None:
            data["timestamp"] = timestamp

        return self.start_custom(
            DreameVacuumStatus.SEGMENT_CLEANING.value,
            str(json.dumps(data, separators=(",", ":"))).replace(" ", ""),
        )

    def clean_spot(
        self,
        points: list[int] | list[list[int]],
        cleaning_times: int | list[int] | None,
        suction_level: int | list[int] | None,
        water_volume: int | list[int] | None,
    ) -> dict[str, Any] | None:
        """Clean 1.5 square meters area of selected points."""
        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot start cleaning while draining or self repairing/testing")

        if not isinstance(points, list) or not points:
            raise InvalidActionException(f"Invalid point coordinates: %s", points)

        if not isinstance(points[0], list):
            points = [points]

        if suction_level is None or suction_level == "":
            suction_level = self.status.suction_level.value
        else:
            self._update_suction_level(suction_level[0] if isinstance(suction_level, list) else suction_level)

        if water_volume is None or water_volume == "":
            water_volume = self.status.water_volume.value
        else:
            self._update_water_level(int(water_volume[0] if isinstance(water_volume, list) else water_volume))

        if cleaning_times is None or cleaning_times == "":
            cleaning_times = 1

        cleanlist = []
        index = 0
        for point in points:
            if isinstance(cleaning_times, list):
                if index < len(cleaning_times):
                    repeat = cleaning_times[index]
                else:
                    repeat = 1
            else:
                repeat = cleaning_times

            if isinstance(suction_level, list):
                if index < len(suction_level):
                    fan = suction_level[index]
                else:
                    fan = self.status.suction_level.value
            else:
                fan = suction_level

            if isinstance(water_volume, list):
                if index < len(water_volume):
                    water = water_volume[index]
                else:
                    if self.capability.self_wash_base:
                        water = self.status.mop_pad_humidity
                    else:
                        water = self.status.water_volume.value
            else:
                water = water_volume

            index = index + 1

            if self.status.current_map and not self.status.current_map.check_point(point[0], point[1]):
                raise InvalidActionException(f"Coordinate ({point[0]}, {point[1]}) is not inside the map")

            cleanlist.append(
                [
                    int(round(point[0])),
                    int(round(point[1])),
                    repeat,
                    fan,
                    water,
                ]
            )

        self.schedule_update(10, True)

        if self.status.cleangenius_cleaning:
            self._previous_cleangenius = self.get_property(DreameVacuumAutoSwitchProperty.CLEANGENIUS)
            self.set_auto_switch_property(
                DreameVacuumAutoSwitchProperty.CLEANGENIUS, DreameVacuumCleanGenius.OFF.value
            )
        else:
            self._previous_cleangenius = None

        if not self.status.started or self.status.paused:
            self._update_status(DreameVacuumTaskStatus.SPOT_CLEANING, DreameVacuumStatus.SPOT_CLEANING)

            if self._map_manager:
                if not self.status.started:
                    self._map_manager.editor.clear_path()

                # Set active points on current map data is implemented on the app
                self._map_manager.editor.set_active_points(points)

        return self.start_custom(
            DreameVacuumStatus.SPOT_CLEANING.value,
            str(json.dumps({"points": cleanlist}, separators=(",", ":"))).replace(" ", ""),
        )

    def go_to(self, x, y) -> dict[str, Any] | None:
        """Go to a point and take pictures around."""
        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot go to point while draining or self repairing/testing")

        if self.status.current_map and not self.status.current_map.check_point(x, y):
            raise InvalidActionException("Coordinate is not inside the map")

        if self.status.battery_level < 15:
            raise InvalidActionException(
                "Low battery capacity. Please start the robot for working after it being fully charged."
            )

        if not self.capability.cruising:
            size = (self.status.current_map.dimensions.grid_size * 2) if self.status.current_map else 100
            if self.status.current_map and self.status.current_map.robot_position:
                position = self.status.current_map.robot_position
                if abs(x - position.x) <= size and abs(y - position.y) <= size:
                    raise InvalidActionException(f"Robot is already on selected coordinate")
            self._set_go_to_zone(x, y, size)
            size = int(size / 2)
            zone = [
                x - size,
                y - size,
                x + size,
                y + size,
            ]

        if not (self.status.started or self.status.paused):
            if not self.capability.cruising and self.status.cleangenius_cleaning:
                self._previous_cleangenius = self.get_property(DreameVacuumAutoSwitchProperty.CLEANGENIUS)
                self.set_auto_switch_property(
                    DreameVacuumAutoSwitchProperty.CLEANGENIUS, DreameVacuumCleanGenius.OFF.value
                )
            else:
                self._previous_cleangenius = None

            self._update_property(DreameVacuumProperty.STATE, DreameVacuumState.MONITORING.value)
            self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.CRUISING_POINT.value)
            self._update_property(
                DreameVacuumProperty.TASK_STATUS,
                DreameVacuumTaskStatus.CRUISING_POINT.value,
            )

            if self._map_manager:
                # Set active cruise points on current map data is implemented on the app
                self._map_manager.editor.set_cruise_points([[x, y, 0, 0]])

        if self.capability.cruising:
            return self.start_custom(
                DreameVacuumStatus.CRUISING_POINT.value,
                str(
                    json.dumps(
                        {"tpoint": [[x, y, 0, 0]]},
                        separators=(",", ":"),
                    )
                ).replace(" ", ""),
            )
        else:
            cleanlist = [
                int(round(zone[0])),
                int(round(zone[1])),
                int(round(zone[2])),
                int(round(zone[3])),
                1,
                0,
                1,
            ]

            response = self.start_custom(
                DreameVacuumStatus.ZONE_CLEANING.value,
                str(json.dumps({"areas": [cleanlist]}, separators=(",", ":"))).replace(" ", ""),
            )
            if not response:
                self._restore_go_to_zone()

            return response

    def follow_path(self, points: list[int] | list[list[int]]) -> dict[str, Any] | None:
        """Start a survaliance job."""
        if not self.capability.cruising:
            raise InvalidActionException("Follow path is supported on this device")

        if self.status.stream_status != DreameVacuumStreamStatus.IDLE:
            raise InvalidActionException(f"Follow path only works with live camera streaming")

        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot follow path while draining or self repairing/testing")

        if self.status.battery_level < 15:
            raise InvalidActionException(
                "Low battery capacity. Please start the robot for working after it being fully charged."
            )

        if not points:
            points = []

        if points and not isinstance(points[0], list):
            points = [points]

        if self.status.current_map:
            for point in points:
                if not self.status.current_map.check_point(point[0], point[1]):
                    raise InvalidActionException(f"Coordinate ({point[0]}, {point[1]}) is not inside the map")

        path = []
        for point in points:
            path.append([int(round(point[0])), int(round(point[1])), 0, 1])

        predefined_points = []
        if self.status.current_map and self.status.current_map.predefined_points:
            for point in self.status.current_map.predefined_points.values():
                predefined_points.append([int(round(point.x)), int(round(point.y)), 0, 1])

        if len(path) == 0:
            path.extend(predefined_points)

        if len(path) == 0:
            raise InvalidActionException("At least one valid or saved coordinate is required")

        if not self.status.started or self.status.paused:
            self._update_property(DreameVacuumProperty.STATE, DreameVacuumState.MONITORING.value)
            self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.CRUISING_PATH.value)
            self._update_property(
                DreameVacuumProperty.TASK_STATUS,
                DreameVacuumTaskStatus.CRUISING_PATH.value,
            )

            if self._map_manager:
                # Set active cruise points on current map data is implemented on the app
                self._map_manager.editor.set_cruise_points(path[:20])

        return self.start_custom(
            DreameVacuumStatus.CRUISING_PATH.value,
            str(
                json.dumps(
                    {"tpoint": path[:20]},
                    separators=(",", ":"),
                )
            ).replace(" ", ""),
        )

    def start_shortcut(self, shortcut_id: int) -> dict[str, Any] | None:
        """Start shortcut job."""
        if not self.capability.shortcuts and not self.status.shortcuts:
            raise InvalidActionException(f"Shortcuts are not supported on this device")

        if shortcut_id < 32 or shortcut_id > 128:
            raise InvalidActionException(f"Invalid shortcut ID: {shortcut_id}")

        if self.status.draining or self.status.self_repairing:
            raise InvalidActionException(f"Cannot start cleaning while draining or self repairing/testing")

        if not self.status.started:
            if self.status.status is DreameVacuumStatus.STANDBY:
                self._update_property(DreameVacuumProperty.STATE, DreameVacuumState.IDLE.value)

            self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.SEGMENT_CLEANING.value)
            self._update_property(
                DreameVacuumProperty.TASK_STATUS,
                DreameVacuumTaskStatus.AUTO_CLEANING.value,
            )

        if self.status.shortcuts and shortcut_id in self.status.shortcuts:
            self.status.shortcuts[shortcut_id].running = True

        return self.start_custom(
            DreameVacuumStatus.SHORTCUT.value,
            str(shortcut_id),
        )

    def start_fast_mapping(self) -> dict[str, Any] | None:
        """Fast map."""
        if self.status.fast_mapping:
            return

        if self.status.battery_level < 15:
            raise InvalidActionException(
                "Low battery capacity. Please start the robot for working after it being fully charged."
            )

        if self.status.water_tank_or_mop_installed and not self.capability.mop_pad_lifting:
            raise InvalidActionException("Please make sure the mop pad is not installed before fast mapping.")

        self.schedule_update(10, True)
        self._update_status(DreameVacuumTaskStatus.FAST_MAPPING, DreameVacuumStatus.FAST_MAPPING)

        if self._map_manager:
            self._map_manager.editor.reset_map()

        return self.start_custom(DreameVacuumStatus.FAST_MAPPING.value)

    def start_mapping(self) -> dict[str, Any] | None:
        """Create a new map by cleaning whole floor."""
        self.schedule_update(10, True)
        self._update_status(DreameVacuumTaskStatus.AUTO_CLEANING, DreameVacuumStatus.CLEANING)

        if self._map_manager:
            self._map_manager.editor.reset_map()

        return self.start_custom(DreameVacuumStatus.CLEANING.value, "3")

    def start_self_wash_base(self, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        """Start self-wash base for cleaning or drying the mop."""
        if not self.capability.self_wash_base:
            return

        if self.info and self.info.version <= 1037:
            parameters = None

        payload = None
        if parameters is not None:
            payload = [
                {
                    "piid": PIID(DreameVacuumProperty.CLEANING_PROPERTIES, self.property_mapping),
                    "value": parameters,
                }
            ]
        return self.call_action(DreameVacuumAction.START_WASHING, payload)

    def toggle_washing(self) -> dict[str, Any] | None:
        """Toggle washing the mop if self-wash base is present."""
        if self.status.washing:
            return self.pause_washing()
        return self.start_washing()

    def start_washing(self) -> dict[str, Any] | None:
        """Start washing the mop if self-wash base is present."""
        if self.status.washing_paused:
            self._update_property(
                DreameVacuumProperty.SELF_WASH_BASE_STATUS,
                DreameVacuumSelfWashBaseStatus.WASHING.value,
            )
            if self.info and self.info.version <= 1037:
                return self.start()
            return self.start_self_wash_base("1,1")
        if self.status.washing_available or self.status.returning_to_wash_paused:
            self._update_property(
                DreameVacuumProperty.SELF_WASH_BASE_STATUS,
                DreameVacuumSelfWashBaseStatus.WASHING.value,
            )
            return self.start_self_wash_base("2,1")

    def pause_washing(self) -> dict[str, Any] | None:
        """Pause washing the mop if self-wash base is present."""
        if self.status.washing:
            self._update_property(
                DreameVacuumProperty.SELF_WASH_BASE_STATUS,
                DreameVacuumSelfWashBaseStatus.PAUSED.value,
            )
            if self.info and self.info.version <= 1037:
                return self.pause()
            return self.start_self_wash_base("1,0")

    def toggle_drying(self) -> dict[str, Any] | None:
        """Toggle drying the mop if self-wash base is present."""
        if self.status.drying_available and self.status.drying:
            return self.stop_drying()
        return self.start_drying()

    def start_drying(self) -> dict[str, Any] | None:
        """Start drying the mop if self-wash base is present."""
        if self.status.drying_available and not self.status.drying:
            self._update_property(
                DreameVacuumProperty.SELF_WASH_BASE_STATUS,
                DreameVacuumSelfWashBaseStatus.DRYING.value,
            )
            return self.start_self_wash_base("3,1")

    def stop_drying(self) -> dict[str, Any] | None:
        """Stop drying the mop if self-wash base is present."""
        if self.status.drying_available and self.status.drying:
            self._update_property(
                DreameVacuumProperty.SELF_WASH_BASE_STATUS,
                DreameVacuumSelfWashBaseStatus.IDLE.value,
            )
            return self.start_self_wash_base("3,0")

    def start_draining(self, clean_water_tank=False) -> dict[str, Any] | None:
        """Start draining water if self-wash base is present."""
        if clean_water_tank:
            if self.capability.empty_water_tank:
                return self.start_self_wash_base("9,1")
        if self.status.washing_available and self.status.drying_available:
            return self.start_self_wash_base("7,1")

    def start_self_repairing(self) -> dict[str, Any] | None:
        """Start self repairing if self-wash base is present."""
        if not self.status.draining and not self.status.self_repairing:
            current_status = self.status.status
            self.schedule_update(10)
            self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.SELF_REPAIR.value)
            mapping = self.property_mapping[DreameVacuumProperty.SELF_TEST_STATUS]
            result = self._protocol.set_property(mapping["siid"], mapping["piid"], '{"bittest":[17,0]}')

            self.schedule_update(3)
            if result is None or result[0]["code"] != 0:
                _LOGGER.error("Start self repairing failed")
                self._update_property(DreameVacuumProperty.STATUS, current_status)
                raise InvalidActionException(f"Start self repairing failed")
            return result

    def start_station_cleaning(self) -> dict[str, Any] | None:
        """Start base station cleaning if self-wash base is present."""
        if (
            self.capability.station_cleaning
            and not self.status.draining
            and not self.status.self_repairing
            and not self.status.station_cleaning
        ):
            current_status = self.status.task_status
            self.schedule_update(10)
            self._update_property(DreameVacuumProperty.TASK_STATUS, DreameVacuumTaskStatus.STATION_CLEANING.value)
            result = self.start_self_wash_base("5,1")
            self.schedule_update(3)
            if result is None or result[0]["code"] != 0:
                _LOGGER.error("Start base station cleaning failed")
                self._update_property(DreameVacuumProperty.TASK_STATUS, current_status)
                raise InvalidActionException(f"Start base station cleaning failed")
            return result

    def start_recleaning(self) -> dict[str, Any] | None:
        """Start self repairing if dirty areas or neglected rooms are present."""
        if self.capability.auto_recleaning and self.status._cleaning_history and self.status.current_map:
            history = self.status._cleaning_history[0]
            map_data = self.status._history_map_data.get(history.object_name) if history.object_name else None
            if map_data and self.status.current_map.map_id == map_data.map_id:
                timestamp = history.multiple_cleaning_time if history.multiple_cleaning_time else ""
                if (
                    history.cleanup_method != CleanupMethod.CLEANGENIUS
                    and not map_data.cleaned_segments
                    and map_data.neglected_segments
                ):
                    return self.clean_segment(map_data.neglected_segments.keys(), timestamp=timestamp)
                else:
                    data = {
                        "MopAgain": map_data.dos if map_data.dos is not None else 1,
                        "timestamp": timestamp,
                        "CleanArea": map_data.cleaned_segments if map_data.cleaned_segments else [],
                        "BigArea": map_data.neglected_segments.keys() if map_data.neglected_segments else [],
                    }
                    self.schedule_update(10, True)
                    self._update_property(
                        DreameVacuumProperty.STATE,
                        DreameVacuumState.SECOND_CLEANING.value,
                    )
                    self._update_property(DreameVacuumProperty.STATUS, DreameVacuumStatus.CLEANING.value)
                    self._update_property(
                        DreameVacuumProperty.TASK_STATUS,
                        DreameVacuumStatus.CLEANING.value,
                    )
                    return self.start_custom(
                        DreameVacuumStatus.CLEANING.value,
                        str(json.dumps(data, separators=(",", ":"))).replace(" ", ""),
                    )

    def reload_shortcuts(self) -> None:
        shortcuts = self.get_property(DreameVacuumProperty.SHORTCUTS)
        if shortcuts and shortcuts != "":
            shortcuts = json.loads(shortcuts)
            if shortcuts:
                new_shortcuts = {}
                for shortcut in shortcuts:
                    id = shortcut["id"]
                    running = (
                        False
                        if "state" not in shortcut
                        else bool(shortcut["state"] == "0" or shortcut["state"] == "1")
                    )
                    name = base64.decodebytes(shortcut["name"].encode("utf8")).decode("utf-8")
                    new_shortcuts[id] = Shortcut(id=id, name=name, running=running)
                self.status.shortcuts = new_shortcuts
                self._property_changed()

                def callback(response):
                    detail = {}
                    if response and "out" in response:
                        data = response["out"]
                        if data and len(data):
                            if "value" in data[0] and data[0]["value"] != "":
                                for task in json.loads(data[0]["value"]):
                                    detail[task["id"]] = task["mapId"]

                    new_shortcuts = {}
                    for shortcut in shortcuts:
                        id = shortcut["id"]
                        running = (
                            False
                            if "state" not in shortcut
                            else bool(shortcut["state"] == "0" or shortcut["state"] == "1")
                        )
                        name = base64.decodebytes(shortcut["name"].encode("utf8")).decode("utf-8")
                        map_id = detail[id] if id in detail else None
                        tasks = None
                        response = self.call_shortcut_action("GET_COMMAND_BY_ID", {"id": id})
                        if response and "out" in response:
                            data = response["out"]
                            if data and len(data):
                                if "value" in data[0] and data[0]["value"] != "":
                                    tasks = []
                                    for task in json.loads(data[0]["value"]):
                                        segments = []
                                        for segment in task:
                                            segments.append(
                                                ShortcutTask(
                                                    segment_id=segment[0],
                                                    suction_level=segment[1],
                                                    water_volume=segment[2],
                                                    cleaning_times=segment[3],
                                                    cleaning_mode=segment[4],
                                                )
                                            )
                                        tasks.append(segments)
                        new_shortcuts[id] = Shortcut(id=id, name=name, map_id=map_id, running=running, tasks=tasks)
                    self.status.shortcuts = new_shortcuts
                    self._property_changed()

                self.call_shortcut_action_async(callback, "GET_COMMANDS")

    def clear_warning(self) -> dict[str, Any] | None:
        """Clear warning error code from the vacuum cleaner."""
        if self.status.draining_complete:
            return self.set_property(DreameVacuumProperty.DRAINAGE_STATUS, 0)
        if self.status.has_warning:
            return self.call_action(
                DreameVacuumAction.CLEAR_WARNING,
                [
                    {
                        "piid": PIID(
                            DreameVacuumProperty.CLEANING_PROPERTIES,
                            self.property_mapping,
                        ),
                        "value": f"[{self.status.error.value}]",
                    }
                ],
            )
        else:
            return self.clear_low_water_warning()

    def clear_low_water_warning(self) -> dict[str, Any] | None:
        """Clear low water warning error code from the vacuum cleaner."""
        if self.status.low_water:
            return self.set_property(DreameVacuumProperty.LOW_WATER_WARNING, 1)

    def remote_control_move_step(
        self, rotation: int = 0, velocity: int = 0, prompt: bool | None = None
    ) -> dict[str, Any] | None:
        """Send remote control command to device."""
        if self.status.fast_mapping:
            raise InvalidActionException("Cannot remote control vacuum while fast mapping")

        if self.status.washing:
            raise InvalidActionException("Cannot remote control vacuum while self-wash base is running")

        payload = '{"spdv":%(velocity)d,"spdw":%(rotation)d,"audio":"%(audio)s","random":%(random)d}' % {
            "velocity": velocity,
            "rotation": rotation,
            "audio": (
                "true"
                if prompt == True
                else (
                    "false"
                    if prompt == False or self._remote_control or self.status.status is DreameVacuumStatus.SLEEPING
                    else "true"
                )
            ),
            "random": randrange(65535),
        }
        self._remote_control = True
        mapping = self.property_mapping[DreameVacuumProperty.REMOTE_CONTROL]
        return self._protocol.set_property(mapping["siid"], mapping["piid"], payload, 1)

    def install_voice_pack(self, lang_id: int, url: str, md5: str, size: int) -> dict[str, Any] | None:
        """install a custom language pack"""
        payload = '{"id":"%(lang_id)s","url":"%(url)s","md5":"%(md5)s","size":%(size)d}' % {
            "lang_id": lang_id,
            "url": url,
            "md5": md5,
            "size": size,
        }
        mapping = self.property_mapping[DreameVacuumProperty.VOICE_CHANGE]
        return self._protocol.set_property(mapping["siid"], mapping["piid"], payload, 3)

    def obstacle_image(self, index):
        if self.capability.map and self.status.current_map:
            map_data = self.status.current_map
            if map_data:
                return self._map_manager.get_obstacle_image(map_data, index)
        return (None, None)

    def obstacle_history_image(self, index, history_index, cruising=False):
        if self.capability.map:
            map_data = self.history_map(history_index, cruising)
            if map_data:
                return self._map_manager.get_obstacle_image(map_data, index)
        return (None, None)

    def history_map(self, index, cruising=False):
        if self.capability.map and index and str(index).isnumeric():
            item = None
            if cruising:
                if self.status._cruising_history and len(self.status._cruising_history) > int(index) - 1:
                    item = self.status._cruising_history[int(index) - 1]
            else:
                if self.status._cleaning_history and len(self.status._cleaning_history) > int(index) - 1:
                    item = self.status._cleaning_history[int(index) - 1]
            if item and item.object_name:
                if item.object_name not in self.status._history_map_data:
                    map_data = self._map_manager.get_history_map(item.object_name, item.key)
                    if map_data is None:
                        return None
                    map_data.last_updated = item.date.timestamp()
                    map_data.completed = item.completed
                    map_data.neglected_segments = item.neglected_segments
                    map_data.second_cleaning = item.second_cleaning
                    map_data.cleaned_area = item.cleaned_area
                    map_data.cleaning_time = item.cleaning_time
                    if item.cleanup_method is not None:
                        map_data.cleanup_method = item.cleanup_method
                    if map_data.cleaning_map_data:
                        map_data.cleaning_map_data.last_updated = item.date.timestamp()
                        map_data.cleaning_map_data.completed = item.completed
                        map_data.cleaning_map_data.neglected_segments = item.neglected_segments
                        map_data.cleaning_map_data.second_cleaning = item.second_cleaning
                        map_data.cleaning_map_data.cleaned_area = item.cleaned_area
                        map_data.cleaning_map_data.cleaning_time = item.cleaning_time
                        map_data.cleaning_map_data.cleanup_method = map_data.cleanup_method
                    self.status._history_map_data[item.object_name] = map_data
                return self.status._history_map_data[item.object_name]

    def recovery_map(self, map_id, index):
        if self.capability.map and map_id and index and str(index).isnumeric():
            if (map_id is None or map_id == "") and self.status.selected_map:
                map_id = self.status.selected_map.map_id

            return self._map_manager.get_recovery_map(map_id, index)

    def recovery_map_file(self, map_id, index):
        if self.capability.map and map_id and index and str(index).isnumeric():
            if (map_id is None or map_id == "") and self.status.selected_map:
                map_id = self.status.selected_map.map_id

            return self._map_manager.get_recovery_map_file(map_id, index)

    def set_ai_detection(self, settings: dict[str, bool] | int) -> dict[str, Any] | None:
        """Send ai detection parameters to the device."""
        if self.capability.ai_detection:
            # if (self.status.ai_obstacle_detection or self.status.ai_obstacle_image_upload) and (
            #    self._protocol.cloud and not self.status.ai_policy_accepted
            # ):
            #    prop = "prop.s_ai_config"
            #    response = self._protocol.cloud.get_batch_device_datas([prop])
            #    if response and prop in response and response[prop]:
            #        try:
            #            self.status.ai_policy_accepted = json.loads(response[prop]).get("privacyAuthed")
            #        except:
            #            pass
            #    if not self.status.ai_policy_accepted:
            #        if self.status.ai_obstacle_detection:
            #            self.set_ai_property(DreameVacuumAIProperty.AI_OBSTACLE_DETECTION, False)
            #        if self.status.ai_obstacle_image_upload:
            #            self.set_ai_property(DreameVacuumAIProperty.AI_OBSTACLE_IMAGE_UPLOAD, False)
            #        self._property_changed(False)
            #        raise InvalidActionException(
            #            "You need to accept privacy policy from the App before enabling AI obstacle detection feature"
            #        )
            mapping = self.property_mapping[DreameVacuumProperty.AI_DETECTION]
            if isinstance(settings, int):
                return self._protocol.set_property(mapping["siid"], mapping["piid"], settings, 3)
            return self._protocol.set_property(
                mapping["siid"],
                mapping["piid"],
                str(json.dumps(settings, separators=(",", ":"))).replace(" ", ""),
                3,
            )

    def set_ai_property(
        self, prop: DreameVacuumStrAIProperty | DreameVacuumAIProperty, value: bool
    ) -> dict[str, Any] | None:
        if self.capability.ai_detection:
            if prop.name not in self.ai_data:
                raise InvalidActionException("Not supported")
            current_value = self.get_ai_property(prop)

            self._dirty_ai_data[prop.name] = DirtyData(value, current_value, time.time())
            self.ai_data[prop.name] = value
            ai_value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            self._property_changed(False)
            result = None
            try:
                if isinstance(ai_value, int):
                    bit = DreameVacuumAIProperty[prop.name].value
                    result = self.set_ai_detection((ai_value | bit) if value else (ai_value & -(bit + 1)))
                else:
                    result = self.set_ai_detection({DreameVacuumStrAIProperty[prop.name].value: bool(value)})

                if result is None or result[0]["code"] != 0:
                    _LOGGER.error(
                        "AI Property not updated: %s: %s -> %s",
                        prop.name,
                        current_value,
                        value,
                    )
                    if prop.name in self._dirty_ai_data:
                        del self._dirty_ai_data[prop.name]
                    self.ai_data[prop.name] = current_value
                    self._property_changed(False)
            except Exception as ex:
                if prop.name in self._dirty_ai_data:
                    del self._dirty_ai_data[prop.name]
                self.ai_data[prop.name] = current_value
                self._property_changed(False)
            return result

    def set_auto_switch_settings(self, settings) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            mapping = self.property_mapping[DreameVacuumProperty.AUTO_SWITCH_SETTINGS]
            return self._protocol.set_property(
                mapping["siid"],
                mapping["piid"],
                str(json.dumps(settings, separators=(",", ":"))).replace(" ", ""),
                1,
            )

    def set_auto_switch_property(self, prop: DreameVacuumAutoSwitchProperty, value: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            if prop.name not in self.auto_switch_data:
                raise InvalidActionException("Not supported")
            current_value = self.get_auto_switch_property(prop)
            if current_value != value:
                self._dirty_auto_switch_data[prop.name] = DirtyData(value, current_value, time.time())
                self.auto_switch_data[prop.name] = value
                self._property_changed(False)
                result = None
                if prop is DreameVacuumAutoSwitchProperty.CLEANGENIUS and self._map_manager:
                    self._map_manager.editor.refresh_map()
                try:
                    result = self.set_auto_switch_settings({"k": prop.value, "v": int(value)})
                    if result is None or result[0]["code"] != 0:
                        _LOGGER.error(
                            "Auto Switch Property not updated: %s: %s -> %s",
                            prop.name,
                            current_value,
                            value,
                        )
                        if prop.name in self._dirty_auto_switch_data:
                            del self._dirty_auto_switch_data[prop.name]
                        self.auto_switch_data[prop.name] = current_value
                        self._property_changed(False)
                    else:
                        _LOGGER.info("Update Property: %s: %s -> %s", prop.name, current_value, value)
                        if prop.name in self._dirty_auto_switch_data:
                            self._dirty_auto_switch_data[prop.name].update_time = time.time()
                except:
                    if prop.name in self._dirty_auto_switch_data:
                        del self._dirty_auto_switch_data[prop.name]
                    self.auto_switch_data[prop.name] = current_value
                    self._property_changed(False)
                return result
        elif self.capability.self_wash_base and prop == DreameVacuumAutoSwitchProperty.AUTO_DRYING:
            return self.set_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION, int(value))

    def set_camera_light_brightness(self, brightness: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            if brightness < 40:
                brightness = 40
            current_value = self.status.camera_light_brightness
            self._update_property(DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS, str(brightness))
            result = self.call_stream_property_action(
                DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS, {"value": str(brightness)}
            )
            if result is None or result.get("code") != 0:
                self._update_property(DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS, str(current_value))
            return result

    def set_wider_corner_coverage(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            current_value = self.get_auto_switch_property(DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE)
            if current_value is not None and current_value > 0 and value <= 0:
                value = -current_value
            return self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE, value)

    def set_mop_pad_swing(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            current_value = self.get_auto_switch_property(DreameVacuumAutoSwitchProperty.MOP_PAD_SWING)
            if current_value is not None and current_value > 0 and value <= 0:
                value = -current_value
            return self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.MOP_PAD_SWING, value)

    def set_auto_recleaning(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings and self.capability.auto_recleaning:
            current_value = self.get_auto_switch_property(DreameVacuumAutoSwitchProperty.AUTO_RECLEANING)
            if current_value is not None and current_value > 0 and value <= 0:
                value = -current_value
            return self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.AUTO_RECLEANING, value)

    def set_auto_rewashing(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings and self.capability.auto_rewashing:
            current_value = self.get_auto_switch_property(DreameVacuumAutoSwitchProperty.AUTO_REWASHING)
            if current_value is not None and current_value > 0 and value <= 0:
                value = -current_value
            return self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.AUTO_REWASHING, value)

    def set_self_clean_frequency(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            current_value = self.get_auto_switch_property(DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY)
            if current_value is not None and current_value > 0 and value <= 0:  # OFF
                if current_value == DreameVacuumSelfCleanFrequency.BY_TIME.value:
                    self.status.previous_self_clean_time = self.status.self_clean_value
                elif current_value == DreameVacuumSelfCleanFrequency.BY_AREA.value:
                    self.status.previous_self_clean_area = self.status.self_clean_value

            if not value:
                result = self.set_self_clean_value(0)
                if not self.capability.self_clean_frequency:
                    return result

            result = not self.capability.self_clean_frequency or self.set_auto_switch_property(
                DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY, value
            )
            if result and value:
                if self.capability.self_clean_frequency and value == DreameVacuumSelfCleanFrequency.BY_TIME.value:
                    self.set_self_clean_value(
                        self.status.previous_self_clean_time
                        if self.status.previous_self_clean_time
                        else self.status.self_clean_time_default
                    )
                else:
                    self.set_self_clean_value(
                        self.status.previous_self_clean_area
                        if self.status.previous_self_clean_area
                        else self.status.self_clean_area_default
                    )

    def set_auto_empty_mode(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_empty_mode:
            return self.set_property(DreameVacuumProperty.AUTO_DUST_COLLECTING, value)

    def set_custom_mopping_route(self, value: int) -> dict[str, Any] | None:
        if self.capability.custom_mopping_route:
            if value < 0:
                result = self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.CUSTOM_MOPPING_MODE, 0)
                if result:
                    return self._update_water_level(
                        self.get_auto_switch_property(DreameVacuumAutoSwitchProperty.MOPPING_MODE)
                    )
            if not self.status.custom_mopping_mode:
                result = self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.CUSTOM_MOPPING_MODE, 1)
                if result:
                    self._update_water_level(
                        self.status.mop_pad_humidity
                        if self.capability.self_wash_base
                        else self.status.water_volume.value
                    )
            return self.set_auto_switch_property(DreameVacuumAutoSwitchProperty.MOPPING_TYPE, value)

    def set_resume_cleaning(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_charging and bool(value):
            value = 2
        return self.set_property(DreameVacuumProperty.RESUME_CLEANING, value)

    def set_carpet_avoidance(self, value: bool) -> dict[str, Any] | None:
        return self.set_property(DreameVacuumProperty.CARPET_CLEANING, 1 if value else 2)

    def set_carpet_cleaning(self, value: int) -> dict[str, Any] | None:
        if self.get_property(DreameVacuumProperty.CARPET_CLEANING) is not None:
            if (
                value == 4
                and (
                    not self.capability.mop_pad_lifting_plus
                    or self.capability.auto_carpet_cleaning
                    or self.capability.carpet_crossing
                )
            ) or (
                value == 6 and (not self.capability.mop_pad_lifting_plus and not self.capability.auto_carpet_cleaning)
            ):
                raise InvalidActionException("Selected cleaning setting is not supported on this device: %s", value)

            if value == 6:
                return self.set_carpet_recognition(0)
            elif not self.status.carpet_recognition:
                self.set_carpet_recognition(1)
            result = self.set_property(DreameVacuumProperty.CARPET_CLEANING, value)
            if result and self.capability.mop_pad_unmounting and value == 3 and not self.status.auto_mount_mop:
                self.set_property(DreameVacuumProperty.AUTO_MOUNT_MOP, 1)

    def set_carpet_recognition(self, value: int) -> dict[str, Any] | None:
        if self.capability.carpet_recognition:
            current_value = self.get_property(DreameVacuumProperty.CARPET_RECOGNITION)
            if current_value is not None:
                if bool(value):
                    value = 1
                else:
                    value = 3 if self.get_property(DreameVacuumProperty.CARPET_BOOST) == 1 else 0
                if self.set_property(DreameVacuumProperty.CARPET_RECOGNITION, value):
                    self.set_property(
                        DreameVacuumProperty.CARPET_BOOST,
                        1 if value == 1 and current_value == 3 else 0,
                    )

    def set_multi_floor_map(self, enabled: bool) -> bool:
        if self.set_property(DreameVacuumProperty.MULTI_FLOOR_MAP, int(enabled)):
            if (
                self.capability.auto_switch_settings
                and not enabled
                and self.get_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION) == 1
            ):
                self.set_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION, 0)
            return True
        return False

    def rename_shortcut(self, shortcut_id: int, shortcut_name: str = "") -> dict[str, Any] | None:
        """Rename a shortcut"""
        if self.status.started:
            raise InvalidActionException("Cannot rename a shortcut while vacuum is running")

        if not self.capability.shortcuts or not self.status.shortcuts:
            raise InvalidActionException("Shortcuts are not supported on this device")

        if shortcut_id not in self.status.shortcuts:
            raise InvalidActionException(f"Shortcut {shortcut_id} not found")

        if shortcut_name and len(shortcut_name) > 0:
            current_name = self.status.shortcuts[shortcut_id]
            if current_name != shortcut_name:
                counter = 1
                for id, shortcut in self.status.shortcuts.items():
                    if shortcut.name == shortcut_name and shortcut.id != shortcut_id:
                        counter = counter + 1

                if counter > 1:
                    shortcut_name = f"{shortcut_name}{counter}"

                self.status.shortcuts[shortcut_id].name = shortcut_name
                shortcut_name = base64.b64encode(shortcut_name.encode("utf-8")).decode("utf-8")
                shortcuts = self.get_property(DreameVacuumProperty.SHORTCUTS)
                if shortcuts and shortcuts != "":
                    shortcuts = json.loads(shortcuts)
                    if shortcuts:
                        for shortcut in shortcuts:
                            if shortcut["id"] == shortcut_id:
                                shortcut["name"] = shortcut_name
                                break
                self._update_property(
                    DreameVacuumProperty.SHORTCUTS,
                    str(json.dumps(shortcuts, separators=(",", ":"))).replace(" ", ""),
                )
                self._property_changed(False)

                success = False
                response = self.call_shortcut_action(
                    "EDIT_COMMAND",
                    {"id": shortcut_id, "name": shortcut_name, "type": 3},
                )
                if response and "out" in response:
                    data = response["out"]
                    if data and len(data):
                        if "value" in data[0] and data[0]["value"] != "":
                            success = data[0]["value"] == "0"
                if not success:
                    self.status.shortcuts[shortcut_id].name = current_name
                    self._property_changed(False)
                return response

    def set_obstacle_ignore(self, x, y, obstacle_ignored) -> dict[str, Any] | None:
        if not self.capability.ai_detection:
            raise InvalidActionException("Obstacle detection is not available on this device")

        if not self._map_manager:
            raise InvalidActionException("Obstacle ignore requires cloud connection")

        if self.status.started:
            raise InvalidActionException("Cannot set obstacle ignore status while vacuum is running")

        if not self.status.current_map and not self.status.current_map.obstacles:
            raise InvalidActionException("Obstacle not found")

        if self.status.current_map.obstacles is None or (
            len(self.status.current_map.obstacles)
            and next(iter(self.status.current_map.obstacles.values())).ignore_status is None
        ):
            raise InvalidActionException("Obstacle ignore is not supported on this device")

        found = False
        obstacle_type = 142
        for k, v in self.status.current_map.obstacles.items():
            if int(v.x) == int(x) and int(v.y) == int(y):
                if v.ignore_status.value == 2:
                    raise InvalidActionException("Cannot ignore a dynamically ignored obstacle")
                obstacle_type = v.type.value
                found = True
                break

        if not found:
            raise InvalidActionException("Obstacle not found")

        self._map_manager.editor.set_obstacle_ignore(x, y, obstacle_ignored)
        return self.update_map_data_async(
            {
                "obstacleignore": [
                    int(x),
                    int(y),
                    obstacle_type,
                    1 if bool(obstacle_ignored) else 0,
                ]
            }
        )

    def set_router_position(self, x, y):
        if not self.capability.wifi_map:
            raise InvalidActionException("WiFi map is not available on this device")

        if self.status.started:
            raise InvalidActionException("Cannot set router position while vacuum is running")

        if self._map_manager:
            self._map_manager.editor.set_router_position(x, y)
        return self.update_map_data_async({"wrp": [int(x), int(y)]})

    def request_map(self) -> dict[str, Any] | None:
        """Send map request action to the device.
        Device will upload a new map on cloud after this command if it has a saved map on memory.
        Otherwise this action will timeout when device is spot cleaning or a restored map exists on memory.
        """

        if self._map_manager:
            return self._map_manager.request_new_map()
        return self.call_action(
            DreameVacuumAction.REQUEST_MAP,
            [
                {
                    "piid": PIID(DreameVacuumProperty.FRAME_INFO, self.property_mapping),
                    "value": '{"frame_type":"I"}',
                }
            ],
        )

    def update_map_data_async(self, parameters: dict[str, Any]):
        """Send update map action to the device."""
        if self._map_manager:
            self._map_manager.schedule_update(10)
            self._property_changed(False)
            self._last_map_request = time.time()

        parameters = [
            {
                "piid": PIID(DreameVacuumProperty.MAP_EXTEND_DATA, self.property_mapping),
                "value": str(json.dumps(parameters, separators=(",", ":"))),
            }
        ]

        def callback(result):
            if result and result.get("code") == 0:
                _LOGGER.info("Send action UPDATE_MAP_DATA async %s", parameters)
                self._last_change = time.time()
            else:
                _LOGGER.error(
                    "Send action failed UPDATE_MAP_DATA async (%s): %s",
                    parameters,
                    result,
                )

            self.schedule_update(5)

            if self._map_manager:
                if self._protocol.dreame_cloud:
                    self._map_manager.schedule_update(3)
                    self._map_manager.request_next_map_list()
                else:
                    self._last_map_change_time = self._last_change
                    self._map_manager.request_next_map(True)
                    self._map_manager.request_next_map_list()
                    self._last_map_list_request = 0

        mapping = self.action_mapping[DreameVacuumAction.UPDATE_MAP_DATA]
        self._protocol.action_async(callback, mapping["siid"], mapping["aiid"], parameters)

    def update_map_data(self, parameters: dict[str, Any]) -> dict[str, Any] | None:
        """Send update map action to the device."""
        if self._map_manager:
            self._map_manager.schedule_update(10)
            self._property_changed(False)
            self._last_map_request = time.time()

        response = self.call_action(
            DreameVacuumAction.UPDATE_MAP_DATA,
            [
                {
                    "piid": PIID(DreameVacuumProperty.MAP_EXTEND_DATA, self.property_mapping),
                    "value": str(json.dumps(parameters, separators=(",", ":"))),
                }
            ],
        )

        self.schedule_update(5, True)

        if self._map_manager:
            if self._protocol.dreame_cloud:
                self._map_manager.schedule_update(3)
                self._map_manager.request_next_map_list()
            else:
                self._last_map_change_time = self._last_change
                self._map_manager.request_next_map(True)
                self._map_manager.request_next_map_list()
                self._last_map_list_request = 0

        return response

    def rename_map(self, map_id: int, map_name: str = "") -> dict[str, Any] | None:
        """Set custom name for a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot rename a map when temporary map is present")

        if map_name is None:
            map_name = ""

        if self._map_manager:
            map_data_list = self.status.map_data_list
            if not map_data_list or map_id not in map_data_list:
                raise InvalidActionException(f"Map not found! (%s)", map_id)
            self._map_manager.editor.set_map_name(map_id, map_name)
        return self.update_map_data_async({"nrism": {map_id: {"name": map_name if len(map_name) else None}}})

    def set_map_rotation(self, rotation: int, map_id: int = None) -> dict[str, Any] | None:
        """Set rotation of a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot rotate a map when temporary map is present")

        if rotation is not None:
            rotation = int(rotation)
            if rotation > 270 or rotation < 0:
                rotation = 0

            if self._map_manager:
                if map_id is None:
                    map_id = self.status.selected_map.map_id
                self._map_manager.editor.set_rotation(map_id, rotation)

            if map_id is not None:
                return self.update_map_data_async({"smra": {map_id: {"ra": rotation}}})

    def set_restricted_zone(self, walls=[], zones=[], no_mops=[]) -> dict[str, Any] | None:
        """Set restricted zones on current saved map."""
        if walls == "":
            walls = []
        if zones == "":
            zones = []
        if no_mops == "":
            no_mops = []

        if self._map_manager:
            self._map_manager.editor.set_zones(walls, zones, no_mops)

        payload = {"line": walls, "rect": zones, "mop": no_mops}
        current_map = self.status.current_map
        if current_map and current_map.saved_map_status != 2:  # and self.capability.lidar_navigation:
            payload["temp"] = {}

        return self.update_map_data_async({"vw": payload})

    def set_carpet_area(self, carpets=[], ignored_carpets=[]) -> dict[str, Any] | None:
        """Set carpet areas on current saved map."""
        if carpets == "":
            carpets = []
        if ignored_carpets == "":
            ignored_carpets = []

        for index in range(len(carpets)):
            carpets[index].append(index + 1)

        if self._map_manager:
            if self.status.current_map and not (
                self.status.current_map.carpets is not None
                or self.status.current_map.detected_carpets is not None
                or self.status.current_map.ignored_carpets is not None
            ):
                raise InvalidActionException("Carpets are not supported on this device")
            if self.status.current_map and not self.status.has_saved_map:
                raise InvalidActionException("Cannot edit carpets on current map")

            self._map_manager.editor.set_carpets(carpets, ignored_carpets)
        else:
            if not self.capability.carpet_recognition:
                raise InvalidActionException("Carpets are not supported on this device")
        return self.update_map_data_async({"cpt": {"addcpt": carpets, "nocpt": ignored_carpets}})

    def set_virtual_threshold(self, virtual_thresholds=[]) -> dict[str, Any] | None:
        """Set virtual thresholds on current saved map."""
        if virtual_thresholds == "":
            virtual_thresholds = []

        if self._map_manager:
            if self.status.current_map and not (
                self.status.current_map.virtual_thresholds is not None
                or self.status.current_map.passable_thresholds is not None
                or self.capability.floor_material
            ):
                raise InvalidActionException("Virtual thresholds are not supported on this device")

            if self.status.current_map and not self.status.has_saved_map:
                raise InvalidActionException("Cannot edit virtual thresholds on current map")
            self._map_manager.editor.set_virtual_thresholds(virtual_thresholds)
        else:
            if not (
                self.get_property(DreameVacuumProperty.CARPET_RECOGNITION) is not None
                or self.get_property(DreameVacuumProperty.CARPET_CLEANING) is not None
            ):
                raise InvalidActionException("Virtual thresholds are not supported on this device")
        return self.update_map_data_async({"vws": {"vwsl": virtual_thresholds}})

    def set_predefined_points(self, points=[]) -> dict[str, Any] | None:
        """Set predefined points on current saved map."""
        if points == "":
            points = []

        if not self.capability.cruising:
            raise InvalidActionException("Predefined points are not supported on this device")

        if self.status.started:
            raise InvalidActionException("Cannot set predefined points while vacuum is running")

        if self.status.current_map:
            for point in points:
                if not self.status.current_map.check_point(point[0], point[1]):
                    raise InvalidActionException(f"Coordinate ({point[0]}, {point[1]}) is not inside the map")

        predefined_points = []
        for point in points:
            predefined_points.append([point[0], point[1], 0, 1])

        if self._map_manager:
            if self.status.current_map and not self.status.has_saved_map:
                raise InvalidActionException("Cannot edit predefined points on current map")
            self._map_manager.editor.set_predefined_points(predefined_points[:20])

        return self.update_map_data_async({"spoint": predefined_points[:20], "tpoint": []})

    def set_selected_map(self, map_id: int) -> dict[str, Any] | None:
        """Change currently selected map when multi floor map is enabled."""
        if self._map_manager:
            map_data_list = self.status.map_data_list
            if not map_data_list or map_id not in map_data_list:
                raise InvalidActionException(f"Map not found! (%s)", map_id)
            self._map_manager.editor.set_selected_map(map_id)
        self._map_select_time = time.time()
        return self.update_map_data({"sm": {}, "mapid": map_id})

    def delete_map(self, map_id: int = None) -> dict[str, Any] | None:
        """Delete a map."""
        map_id = int(map_id)

        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot delete a map when temporary map is present")

        if self.status.started:
            raise InvalidActionException("Cannot delete a map while vacuum is running")

        if self._map_manager:
            if map_id is not None and map_id != 0:
                map_data_list = self.status.map_data_list
                if not map_data_list or map_id not in map_data_list:
                    raise InvalidActionException(f"Map not found! (%s)", map_id)

            if map_id == 0:
                map_id = None

            # Device do not deletes saved maps when you disable multi floor map feature
            # but it deletes all maps if you delete any map when multi floor map is disabled.
            if self.status.multi_map:
                if not map_id and self._map_manager.selected_map:
                    map_id = self._map_manager.selected_map.map_id
                self._map_manager.editor.delete_map(map_id)
            else:
                if self._map_manager.selected_map and map_id == self._map_manager.selected_map.map_id:
                    self._map_manager.editor.delete_map()
                else:
                    self._map_manager.editor.delete_map(map_id)
        parameters = {"cm": {}}
        if map_id:
            parameters["mapid"] = map_id
        return self.update_map_data(parameters)

    def save_temporary_map(self) -> dict[str, Any] | None:
        """Replace new map with an old one when multi floor map is disabled."""
        if self.status.has_temporary_map:
            if self._map_manager:
                self._map_manager.editor.save_temporary_map()
            return self.update_map_data({"cw": 5})

    def discard_temporary_map(self) -> dict[str, Any] | None:
        """Discard new map when device have reached maximum number of maps it can store."""
        if self.status.has_temporary_map:
            if self._map_manager:
                self._map_manager.editor.discard_temporary_map()
            return self.update_map_data({"cw": 0})

    def replace_temporary_map(self, map_id: int = None) -> dict[str, Any] | None:
        """Replace new map with an old one when device have reached maximum number of maps it can store."""
        if self.status.has_temporary_map:
            if self.status.multi_map:
                raise InvalidActionException("Cannot replace a map when multi floor map is disabled")

            if self._map_manager:
                self._map_manager.editor.replace_temporary_map(map_id)
            parameters = {"cw": 1}
            if map_id:
                parameters["mapid"] = map_id
            return self.update_map_data(parameters)

    def restore_map_from_file(self, map_url: int, map_id: int = None) -> dict[str, Any] | None:
        map_recovery_status = self.status.map_recovery_status
        if map_recovery_status is None:
            raise InvalidActionException("Map recovery is not supported on this device")

        if map_recovery_status == DreameVacuumMapRecoveryStatus.RUNNING.value:
            raise InvalidActionException("Map recovery in progress")

        if map_id is None or map_id == "":
            if self.status.selected_map is None:
                raise InvalidActionException("Map ID is required")

            map_id = self.status.selected_map.map_id

        if self.status.map_data_list and not (map_id in self.status.map_data_list):
            raise InvalidActionException("Map not found")

        if self.status.started:
            raise InvalidActionException("Cannot set restore a map while vacuum is running")

        self.schedule_update(15)
        if self._map_manager:
            self._last_map_request = time.time()
            self._map_manager.schedule_update(15)

        self._update_property(
            DreameVacuumProperty.MAP_RECOVERY_STATUS,
            DreameVacuumMapRecoveryStatus.RUNNING.value,
        )
        mapping = self.property_mapping[DreameVacuumProperty.MAP_RECOVERY]
        response = self._protocol.set_property(
            mapping["siid"],
            mapping["piid"],
            str(json.dumps({"map_id": map_id, "map_url": map_url}, separators=(",", ":"))).replace(" ", ""),
        )
        if not response or response[0]["code"] != 0:
            self._update_property(DreameVacuumProperty.MAP_RECOVERY_STATUS, map_recovery_status)
            raise InvalidActionException("Map recovery failed with error code %s", response[0]["code"])
        self._map_manager.schedule_update(5)
        self.schedule_update(1)
        return response

    def restore_map(self, recovery_map_index: int, map_id: int = None) -> dict[str, Any] | None:
        """Replace a map with previously saved version by device."""
        map_recovery_status = self.status.map_recovery_status
        if map_recovery_status is None:
            raise InvalidActionException("Map recovery is not supported on this device")

        if not self._map_manager:
            raise InvalidActionException("Map recovery requires cloud connection")

        if map_recovery_status == DreameVacuumMapRecoveryStatus.RUNNING.value:
            raise InvalidActionException("Map recovery in progress")

        if self.status.started:
            raise InvalidActionException("Cannot set restore a map while vacuum is running")

        if self.status.has_temporary_map:
            raise InvalidActionException("Restore a map when temporary map is present")

        if (map_id is None or map_id == "") and self.status.selected_map:
            map_id = self.status.selected_map.map_id

        if not map_id or map_id not in self.status.map_data_list:
            raise InvalidActionException("Map not found")

        if len(self.status.map_data_list[map_id].recovery_map_list) <= int(recovery_map_index) - 1:
            raise InvalidActionException("Invalid recovery map index")

        recovery_map_info = self.status.map_data_list[map_id].recovery_map_list[int(recovery_map_index) - 1]
        object_name = recovery_map_info.object_name
        if object_name and object_name != "":
            file, map_url, object_name = self.recovery_map_file(map_id, recovery_map_index)
            if map_url == None:
                raise InvalidActionException("Failed get recovery map file url: %s", object_name)

            if file == None:
                raise InvalidActionException("Failed to download recovery map file: %s", map_url)

            response = self.restore_map_from_file(map_url, map_id)
            if response and response[0]["code"] == 0:
                self._map_manager.editor.restore_map(recovery_map_info)
            return response
        raise InvalidActionException("Invalid recovery map object name")

    def backup_map(self, map_id: int = None) -> dict[str, Any] | None:
        """Save a map map to cloud for later use of restoring."""
        if not self.capability.backup_map:
            raise InvalidActionException("Map backup is not supported on this device")

        if self.status.map_backup_status == DreameVacuumMapBackupStatus.RUNNING.value:
            raise InvalidActionException("Map backup in progress")

        if map_id is None or map_id == "":
            if self.status.selected_map is None:
                raise InvalidActionException("Map ID is required")

            map_id = self.status.selected_map.map_id

        if self.status.map_data_list and not (map_id in self.status.map_data_list):
            raise InvalidActionException("Map not found")

        response = self.call_action(
            DreameVacuumAction.BACKUP_MAP,
            [
                {
                    "piid": PIID(DreameVacuumProperty.MAP_EXTEND_DATA, self.property_mapping),
                    "value": str(map_id),
                }
            ],
        )
        self.schedule_update(3, True)
        if response and response.get("code") == 0:
            self._last_map_change_time = time.time()
            self._update_property(
                DreameVacuumProperty.MAP_BACKUP_STATUS,
                DreameVacuumMapBackupStatus.RUNNING.value,
            )
        return response

    def merge_segments(self, map_id: int, segments: list[int]) -> dict[str, Any] | None:
        """Merge segments on a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit segments when temporary map is present")

        if segments:
            if map_id == "":
                map_id = None

            if self._map_manager:
                if not map_id:
                    if self.capability.lidar_navigation and self._map_manager.selected_map:
                        map_id = self._map_manager.selected_map.map_id
                    else:
                        map_id = 0
                self._map_manager.editor.merge_segments(map_id, segments)

            if not map_id and self.capability.lidar_navigation:
                raise InvalidActionException("Map ID is required")

            data = {"msr": [segments[0], segments[1]]}
            if map_id:
                data["mapid"] = map_id
            return self.update_map_data(data)

    def split_segments(self, map_id: int, segment: int, line: list[int]) -> dict[str, Any] | None:
        """Split segments on a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit segments when temporary map is present")

        if segment and line is not None:
            if map_id == "":
                map_id = None

            if self._map_manager:
                if not map_id:
                    if self.capability.lidar_navigation and self._map_manager.selected_map:
                        map_id = self._map_manager.selected_map.map_id
                    else:
                        map_id = 0
                self._map_manager.editor.split_segments(map_id, segment, line)

            if not map_id and self.capability.lidar_navigation:
                raise InvalidActionException("Map ID is required")

            line.append(segment)
            data = {"dsrid": line}
            if map_id:
                data["mapid"] = map_id
            return self.update_map_data(data)

    def set_cleaning_sequence(self, cleaning_sequence: list[int]) -> dict[str, Any] | None:
        """Set cleaning sequence on current map.
        Device will use this order even you specify order in segment cleaning."""

        if not self.capability.customized_cleaning:
            raise InvalidActionException("Cleaning sequence is not supported on this device")

        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit segments when temporary map is present")

        if self.status.started:
            raise InvalidActionException("Cannot set cleaning sequence while vacuum is running")

        if cleaning_sequence == "" or not cleaning_sequence:
            cleaning_sequence = []

        if self._map_manager:
            if cleaning_sequence and self.status.segments:
                for k in cleaning_sequence:
                    if int(k) not in self.status.segments.keys():
                        raise InvalidValueException("Segment not found! (%s)", k)

            map_data = self.status.current_map
            if map_data and map_data.segments and not map_data.temporary_map:
                if not cleaning_sequence:
                    current = self._map_manager.cleaning_sequence
                    if current and len(current):
                        self.status._previous_cleaning_sequence[map_data.map_id] = current
                    elif map_data.map_id in self.status._previous_cleaning_sequence:
                        del self.status._previous_cleaning_sequence[map_data.map_id]

                cleaning_sequence = self._map_manager.editor.set_cleaning_sequence(cleaning_sequence)

        return self.update_map_data_async({"cleanOrder": cleaning_sequence})

    def set_cleanset(self, cleanset: dict[str, list[int]]) -> dict[str, Any] | None:
        """Set customized cleaning settings on current map. Device will use these settings even you pass another setting for custom segment cleaning."""
        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit customized cleaning settings when temporary map is present")

        if cleanset is not None:
            return self.update_map_data_async({"customeClean": cleanset})

    def set_custom_cleaning(
        self,
        segment_id: list[int],
        suction_level: list[int],
        water_volume: list[int],
        cleaning_times: list[int],
        cleaning_mode: list[int] = None,
        custom_mopping_route: list[int] = None,
        cleaning_route: list[int] = None,
        wetness_level: list[int] = None,
    ) -> dict[str, Any] | None:
        """Set customized cleaning settings on current map.
        Device will use these settings even you pass another setting for custom segment cleaning.
        """

        if not self.capability.customized_cleaning:
            raise InvalidActionException("Customized cleaning is not supported on this device")

        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit customized cleaning parameters when temporary map is present")

        if self.status.started:
            raise InvalidActionException("Cannot edit customized cleaning parameters while vacuum is running")

        if suction_level is not None:
            for v in suction_level:
                if int(v) < 0 or int(v) > 3:
                    raise InvalidActionException("Invalid suction level: %s", v)

        if water_volume is not None:
            for v in water_volume:
                if int(v) < 1 or int(v) > 3:
                    raise InvalidActionException("Invalid water volume: %s", v)

        if cleaning_times is not None:
            for v in cleaning_times:
                if int(v) < 1 or int(v) > 3:
                    raise InvalidActionException("Invalid cleaning times: %s", v)

        if cleaning_mode is not None:
            for v in cleaning_mode:
                if int(v) < 0 or int(v) > 2:
                    raise InvalidActionException("Invalid cleaning mode: %s", v)

        if custom_mopping_route is not None:
            if self.capability.segment_mopping_settings and not self.capability.cleaning_route and self.capability.map:
                for v in custom_mopping_route:
                    if int(v) < -1 or int(v) > 2:
                        raise InvalidActionException("Invalid custom mopping route: %s", v)
            else:
                raise InvalidActionException("Custom mopping route is not supported on this device")

        if cleaning_route is not None:
            if self.capability.cleaning_route and self.capability.map:
                for v in cleaning_route:
                    if int(v) < 1 or int(v) > (3 if self.capability.segment_slow_clean_route else 4):
                        raise InvalidActionException("Invalid cleaning route: %s", v)
            else:
                raise InvalidActionException("Cleaning route is not supported on this device")

        if wetness_level is not None:
            if self.capability.wetness_level and self.capability.map:
                for v in wetness_level:
                    if int(v) < 1 or int(v) > 32:
                        raise InvalidActionException("Invalid wetness level: %s", v)
            else:
                raise InvalidActionException("Wetness level is not supported on this device")

        if self.capability.map:
            if not self.status.has_saved_map:
                raise InvalidActionException("Cannot edit customized cleaning parameters on current map")

            current_map = self.status.current_map
            if current_map:
                segments = self.status.segments
                index = 0
                if not segment_id or segment_id == "":
                    raise InvalidActionException("Segment ID is required")

                for k in segment_id:
                    id = int(k)
                    if not segments or id not in segments:
                        raise InvalidActionException("Invalid Segment ID: %s", id)
                    self._map_manager.editor.set_segment_suction_level(id, int(suction_level[index]), False)
                    if self.capability.wetness_level and wetness_level is not None:
                        self._map_manager.editor.set_segment_wetness_level(id, int(wetness_level[index]), False)
                    else:
                        self._map_manager.editor.set_segment_water_volume(id, int(water_volume[index]), False)
                    self._map_manager.editor.set_segment_cleaning_times(id, int(cleaning_times[index]), False)
                    if self.capability.custom_cleaning_mode and cleaning_mode is not None:
                        self._map_manager.editor.set_segment_cleaning_mode(id, int(cleaning_mode[index]), False)
                    if (
                        self.capability.segment_mopping_settings
                        and not self.capability.cleaning_route
                        and custom_mopping_route is not None
                    ):
                        self._map_manager.editor.set_segment_custom_mopping_route(
                            id, int(custom_mopping_route[index]), False
                        )
                    elif self.capability.cleaning_route and cleaning_route is not None:
                        self._map_manager.editor.set_segment_cleaning_route(id, int(cleaning_route[index]), False)
                    index = index + 1
                self._map_manager.editor.refresh_map()
                return self.set_cleanset(self._map_manager.editor.cleanset(current_map))

        custom_cleaning_mode = self.capability.custom_cleaning_mode
        has_cleaning_mode = cleaning_mode != "" and cleaning_mode is not None
        if (
            segment_id != ""
            and segment_id
            and suction_level != ""
            and suction_level
            and water_volume != ""
            and water_volume
            and cleaning_times != ""
            and cleaning_times is not None
        ):
            if has_cleaning_mode and not custom_cleaning_mode:
                raise InvalidActionException(
                    "Setting custom cleaning mode for segments is not supported by the device!"
                )
            elif not has_cleaning_mode and custom_cleaning_mode:
                raise InvalidActionException("Cleaning mode is required")

            if segments:
                count = len(segments.items())
                if (
                    len(segment_id) != count
                    or len(suction_level) != count
                    or len(water_volume) != count
                    or len(cleaning_times) != count
                    or (custom_cleaning_mode and cleaning_mode is not None and len(cleaning_mode) != count)
                ):
                    raise InvalidActionException("Parameter count mismatch!")

            custom_cleaning = []
            index = 0
            water_level = water_volume[index]
            if self.capability.wetness_level:
                if water_level == 1:
                    water_level = 5
                elif water_level == 3:
                    water_level = 27
                else:
                    water_level = 16
            else:
                water_level = water_level + 1

            for id in segment_id:
                # for some reason cleanset uses different int values for water volume
                values = [
                    id,
                    suction_level[index],
                    water_level,
                    cleaning_times[index],
                ]
                if custom_cleaning_mode:
                    values.append(cleaning_mode[index])
                    if segments:
                        if id not in segments:
                            raise InvalidActionException("Invalid Segment ID: %s", id)

                        if segments[id].custom_mopping_route is not None:
                            mopping_values = DreameVacuumMapDecoder.split_mopping_settings(
                                segments[id].mopping_settings
                            )
                            if mopping_values:
                                if self.capability.wetness_level:
                                    mopping_values[1] = 0
                                    mopping_values[2] = 0
                                else:
                                    # Set mopping mode or water volume according to the mopping effect switch
                                    mopping_values[2 if segments[id].custom_mopping_route == -1 else 1] = water_volume[
                                        index
                                    ]
                                    values.append(DreameVacuumMapDecoder.combine_mopping_settings(mopping_values))
                            else:
                                values.append(segments[id].mopping_settings)
                custom_cleaning.append(values)
                index = index + 1

            return self.set_cleanset(custom_cleaning)

        raise InvalidActionException("Missing parameters!")

    def set_custom_carpet_cleaning(
        self,
        id: int | list[int],
        type: int | list[int],
        carpet_cleaning: int | list[int] = None,
        carpet_settings: list[int] | list[list[int]] = None,
    ) -> dict[str, Any] | None:
        """Set customized carpet cleaning settings on current map."""
        if not self.capability.carpet_recognition:
            raise InvalidActionException("Custom carpet cleaning is not supported on this device")

        if carpet_settings is not None and not self.capability.carpet_cleanset_v3:
            raise InvalidActionException("Custom carpet settings is not supported on this device")

        if id is None or type is None:
            raise InvalidActionException("Missing id or type")

        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit carpets when temporary map is present")

        if not isinstance(id, list):
            id = [id]

        carpet_cleanset = []
        index = 0
        for carpet_id in id:
            if isinstance(type, list):
                if index < len(type):
                    type = type[index]
                else:
                    raise InvalidActionException("Missing carpet type")
            else:
                carpet_type = type

            if isinstance(carpet_cleaning, list):
                if index < len(carpet_cleaning):
                    cleaning_setting = carpet_cleaning[index]
                else:
                    raise InvalidActionException("Missing carpet cleaning")
            else:
                cleaning_setting = carpet_cleaning

            if (
                carpet_settings is not None
                and isinstance(carpet_settings, list)
                and carpet_settings
                and isinstance(carpet_settings[0], list)
            ):
                if index < len(carpet_settings):
                    enabled_settings = carpet_settings[index]
                else:
                    enabled_settings = None
            else:
                enabled_settings = carpet_settings

            if not (carpet_type == 0 or carpet_type == 1 or carpet_type == 2):
                raise InvalidActionException(
                    "Invalid type: %s (0 = Automatically Detected Carpet, 1 = Manually Created Carpet, 2 = Room Carpet)",
                    carpet_type,
                )

            if carpet_type == 2 and not self.capability.carpet_material:
                raise InvalidActionException("Room carpets are not supported on this device: %s", cleaning_setting)

            if cleaning_setting is None or cleaning_setting == 0:
                cleaning_setting = -1

            if not (cleaning_setting >= -1 and cleaning_setting <= 7):
                raise InvalidActionException("Invalid carpet cleaning setting: %s", cleaning_setting)

            if (
                cleaning_setting == 4
                and (
                    not self.capability.mop_pad_lifting_plus
                    or self.capability.auto_carpet_cleaning
                    or self.capability.carpet_crossing
                )
            ) or (
                cleaning_setting == 6
                and (not self.capability.mop_pad_lifting_plus and not self.capability.auto_carpet_cleaning)
            ):
                raise InvalidActionException(
                    "Selected cleaning setting is not supported on this device: %s", cleaning_setting
                )

            index = index + 1
            cleanset = [carpet_type, carpet_id, cleaning_setting]

            if self.capability.carpet_cleanset_v3:
                if cleaning_setting == -1 or enabled_settings is None:
                    settings = -1
                else:
                    settings = 0
                    if self.capability.clean_carpets_first and "clean_carpets_first" in enabled_settings:
                        settings |= 1
                    if (
                        self.get_property(DreameVacuumProperty.CARPET_BOOST) is not None
                        and "carpet_boost" in enabled_settings
                    ):
                        settings |= 2
                    if self.capability.intensive_carpet_cleaning and "intensive_carpet_cleaning" in enabled_settings:
                        settings |= 4
                    if self.capability.side_brush_carpet_rotate and "side_brush_carpet_rotate" in enabled_settings:
                        settings |= 8

                cleanset.append(settings)
            carpet_cleanset.append(cleanset)

        if carpet_cleanset:
            if self.capability.map:
                current_map = self.status.current_map
                if current_map:
                    if current_map.carpet_cleanset is None:
                        raise InvalidActionException("Cannot set sustom carpet cleaning on selected map")
                    carpet_cleanset = self._map_manager.editor.set_custom_carpet_cleaning(carpet_cleanset)
                    if not carpet_cleanset:
                        raise InvalidActionException("Cannot find selected carpet(s)")

            return self.update_map_data_async({"carpetcleanset": carpet_cleanset})

    def set_hidden_segments(self, hidden_segments: list[int]):
        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit segments when temporary map is present")

        if self.status.started:
            raise InvalidActionException("Cannot set room visibility while vacuum is running")

        if hidden_segments == "" or not hidden_segments:
            hidden_segments = []

        if self._map_manager:
            if hidden_segments and self.status.segments:
                for k in hidden_segments:
                    if int(k) not in self.status.segments.keys():
                        raise InvalidValueException("Segment not found! (%s)", k)

            # hidden_segments = self._map_manager.editor.set_hidden_segments(hidden_segments)

        return self.update_map_data_async({"delsr": hidden_segments})

    def set_segment_name(self, segment_id: int, segment_type: int, custom_name: str = None) -> dict[str, Any] | None:
        """Update name of a segment on current map"""
        if self.status.has_temporary_map:
            raise InvalidActionException("Cannot edit segment when temporary map is present")

        if self._map_manager:
            segment_info = self._map_manager.editor.set_segment_name(segment_id, segment_type, custom_name)
            if segment_info:
                data = {"nsr": segment_info}
                if self.status.current_map:
                    data["mapid"] = self.status.current_map.map_id
                if self.capability.auto_rename_segment:
                    data["autonsr"] = True
                return self.update_map_data_async(data)

    def set_segment_order(self, segment_id: int, order: int) -> dict[str, Any] | None:
        """Update cleaning order of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            if order is None or (isinstance(order, str) and not order.isnumeric()):
                order = 0

            cleaning_order = self._map_manager.editor.set_segment_order(segment_id, order)

            return self.update_map_data_async({"cleanOrder": cleaning_order})

    def set_segment_suction_level(self, segment_id: int, suction_level: int) -> dict[str, Any] | None:
        """Update suction level of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(self._map_manager.editor.set_segment_suction_level(segment_id, suction_level))

    def set_segment_water_volume(self, segment_id: int, water_volume: int) -> dict[str, Any] | None:
        """Update water volume of a segment on current map"""
        if not self.capability.self_wash_base and self._map_manager and not self.status.has_temporary_map:
            if self.capability.wetness_level:
                if self.capability.mop_clean_frequency:
                    if water_volume == 1:
                        water_volume = 5
                    elif water_volume == 3:
                        water_volume = 15
                    else:
                        water_volume = 10
                else:
                    if water_volume == 1:
                        water_volume = 5
                    elif water_volume == 3:
                        water_volume = 27
                    else:
                        water_volume = 16

                return self.set_cleanset(self._map_manager.editor.set_segment_wetness_level(segment_id, water_volume))

            return self.set_cleanset(self._map_manager.editor.set_segment_water_volume(segment_id, water_volume))

    def set_segment_mop_pad_humidity(self, segment_id: int, mop_pad_humidity: int) -> dict[str, Any] | None:
        """Update mop pad humidity of a segment on current map"""
        if self.capability.self_wash_base and self._map_manager and not self.status.has_temporary_map:
            if self.capability.wetness_level:
                if self.capability.mop_clean_frequency:
                    if mop_pad_humidity == 1:
                        mop_pad_humidity = 2
                    elif mop_pad_humidity == 3:
                        mop_pad_humidity = 14
                    else:
                        mop_pad_humidity = 8
                else:
                    if mop_pad_humidity == 1:
                        mop_pad_humidity = 5
                    elif mop_pad_humidity == 3:
                        mop_pad_humidity = 27
                    else:
                        mop_pad_humidity = 16

                return self.set_cleanset(
                    self._map_manager.editor.set_segment_wetness_level(segment_id, mop_pad_humidity)
                )

            return self.set_cleanset(self._map_manager.editor.set_segment_water_volume(segment_id, mop_pad_humidity))

    def set_segment_wetness_level(self, segment_id: int, wetness_level: int) -> dict[str, Any] | None:
        """Update wetness level of a segment on current map"""
        if self.capability.wetness_level and self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_wetness_level(segment_id, int(wetness_level))
            )

    def set_segment_cleaning_mode(self, segment_id: int, cleaning_mode: int) -> dict[str, Any] | None:
        """Update mop pad humidity of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(self._map_manager.editor.set_segment_cleaning_mode(segment_id, cleaning_mode))

    def set_segment_custom_mopping_route(self, segment_id: int, custom_mopping_route: int) -> dict[str, Any] | None:
        """Update custom mopping route of a segment on current map"""
        if (
            self.capability.self_wash_base
            and self.capability.custom_mopping_route
            and self._map_manager
            and not self.status.has_temporary_map
        ):
            return self.set_cleanset(
                self._map_manager.editor.set_segment_custom_mopping_route(segment_id, custom_mopping_route)
            )

    def set_segment_cleaning_route(self, segment_id: int, cleaning_route: int) -> dict[str, Any] | None:
        """Update cleaning route of a segment on current map"""
        if (
            self.capability.self_wash_base
            and self.capability.cleaning_route
            and self._map_manager
            and not self.status.has_temporary_map
        ):
            return self.set_cleanset(self._map_manager.editor.set_segment_cleaning_route(segment_id, cleaning_route))

    def set_segment_cleaning_times(self, segment_id: int, cleaning_times: int) -> dict[str, Any] | None:
        """Update cleaning times of a segment on current map."""
        if self.status.started:
            raise InvalidActionException("Cannot set room cleaning times while vacuum is running")

        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(self._map_manager.editor.set_segment_cleaning_times(segment_id, cleaning_times))

    def set_segment_floor_material(
        self, segment_id: int, floor_material: int, direction: int = None
    ) -> dict[str, Any] | None:
        """Update floor material of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            if (
                floor_material > 4
                and floor_material < 8
                and not (self.capability.carpet_material and self.capability.carpet_type)
            ):
                raise InvalidActionException("Setting floor material as carpet is not supported on this device")

            if not self.capability.floor_direction_cleaning:
                direction = None
            else:
                if floor_material != 1:
                    direction = None
                elif direction is None:
                    segment = self.status.segments[segment_id]
                    direction = (
                        segment.floor_material_rotated_direction
                        if segment.floor_material_rotated_direction is not None
                        else (
                            0
                            if self.status.current_map.rotation == 0 or self.status.current_map.rotation == 90
                            else 90
                        )
                    )

            data = {"nsm": self._map_manager.editor.set_segment_floor_material(segment_id, floor_material, direction)}
            if self.status.selected_map:
                data["map_id"] = self.status.selected_map.map_id
            return self.update_map_data_async(data)

    def set_segment_floor_material_direction(
        self, segment_id: int, floor_material_direction: int
    ) -> dict[str, Any] | None:
        """Update floor material direction of a segment on current map"""
        if self.capability.floor_direction_cleaning and self._map_manager and not self.status.has_temporary_map:
            data = {
                "nsm": self._map_manager.editor.set_segment_floor_material(segment_id, 1, floor_material_direction)
            }
            if self.status.selected_map:
                data["map_id"] = self.status.selected_map.map_id
            return self.update_map_data_async(data)

    def set_segment_visibility(self, segment_id: int, visibility: int) -> dict[str, Any] | None:
        """Update visibility a segment on current map"""
        if self.capability.segment_visibility and self._map_manager and not self.status.has_temporary_map:
            data = {"delsr": self._map_manager.editor.set_segment_visibility(segment_id, int(visibility))}
            # if self.status.selected_map:
            #    data["map_id"] = self.status.selected_map.map_id
            return self.update_map_data_async(data)

    @property
    def _update_interval(self) -> float:
        """Dynamic update interval of the device for the timer."""
        now = time.time()
        if self.status.map_backup_status or self.status.map_recovery_status:
            return 2
        if self._last_update_failed:
            return 5 if now - self._last_update_failed <= 60 else 10 if now - self._last_update_failed <= 300 else 30
        if now - self._last_change <= 60:
            return 3 if self.status.active or not self._protocol.prefer_cloud else 5
        if self.status.active or self.status.started:
            return 3 if self.status.running or not self._protocol.prefer_cloud else 5
        if self._map_manager:
            return min(self._map_update_interval, 5 if not self._protocol.prefer_cloud else 10)
        return 5 if not self._protocol.prefer_cloud else 10

    @property
    def _map_update_interval(self) -> float:
        """Dynamic map update interval for the map manager."""
        if self._map_manager:
            if self._protocol.dreame_cloud:
                return 10 if self.status.active else 30
            now = time.time()
            if now - self._last_map_request <= 120 or now - self._last_change <= 60:
                return 2.5 if self.status.active or self.status.started else 5
            return 3 if self.status.running else 10 if self.status.active else 30
        return -1

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name

    @property
    def device_connected(self) -> bool:
        """Return connection status of the device."""
        return self._protocol.connected

    @property
    def cloud_connected(self) -> bool:
        """Return connection status of the device."""
        return (
            self._protocol.cloud
            and self._protocol.cloud.connected
            and (not self._protocol.prefer_cloud or self.device_connected)
        )


class DreameVacuumDeviceStatus:
    """Helper class for device status and int enum type properties.
    This class is used for determining various states of the device by its properties.
    Determined states are used by multiple validation and rendering condition checks.
    Almost of the rules are extracted from mobile app that has a similar class with same purpose.
    """

    def __init__(self, device):
        self._device: DreameVacuumDevice = device
        self._cleaning_history = None
        self._cleaning_history_attrs = None
        self._last_cleaning_time = None
        self._cruising_history = None
        self._cruising_history_attrs = None
        self._last_cruising_time = None
        self._history_map_data: dict[str, MapData] = {}
        self._previous_cleaning_sequence: dict[int, list[int]] = {}

        self.suction_level_list = {v: k for k, v in SUCTION_LEVEL_CODE_TO_NAME.items()}
        self.water_volume_list = {v: k for k, v in WATER_VOLUME_CODE_TO_NAME.items()}
        self.mop_pad_humidity_list = {v: k for k, v in MOP_PAD_HUMIDITY_CODE_TO_NAME.items()}
        self.cleaning_mode_list = {v: k for k, v in CLEANING_MODE_CODE_TO_NAME.items()}
        self.carpet_sensitivity_list = {v: k for k, v in CARPET_SENSITIVITY_CODE_TO_NAME.items()}
        self.carpet_cleaning_list = {v: k for k, v in CARPET_CLEANING_CODE_TO_NAME.items()}
        self.mop_wash_level_list = {v: k for k, v in MOP_WASH_LEVEL_TO_NAME.items()}
        self.mop_clean_frequency_list = {v: k for k, v in MOP_CLEAN_FREQUENCY_TO_NAME.items()}
        self.mopping_type_list = {v: k for k, v in MOPPING_TYPE_TO_NAME.items()}
        self.wider_corner_coverage_list = {v: k for k, v in WIDER_CORNER_COVERAGE_TO_NAME.items()}
        self.mop_pad_swing_list = {v: k for k, v in MOP_PAD_SWING_TO_NAME.items()}
        self.mop_extend_frequency_list = {v: k for k, v in MOP_EXTEND_FREQUENCY_TO_NAME.items()}
        self.second_cleaning_list = {v: k for k, v in SECOND_CLEANING_TO_NAME.items()}
        self.cleaning_route_list = {v: k for k, v in CLEANING_ROUTE_TO_NAME.items()}
        self.custom_mopping_route_list = {v: k for k, v in CUSTOM_MOPPING_ROUTE_TO_NAME.items()}
        self.cleangenius_list = {v: k for k, v in CLEANGENIUS_TO_NAME.items()}
        self.washing_mode_list = {v: k for k, v in WASHING_MODE_TO_NAME.items()}
        self.cleangenius_mode_list = {v: k for k, v in CLEANGENIUS_MODE_TO_NAME.items()}
        self.water_temperature_list = {v: k for k, v in WATER_TEMPERATURE_TO_NAME.items()}
        self.self_clean_frequency_list = {v: k for k, v in SELF_CLEAN_FREQUENCY_TO_NAME.items()}
        self.auto_empty_mode_list = {v: k for k, v in AUTO_EMPTY_MODE_TO_NAME.items()}
        self.floor_material_list = {v: k for k, v in FLOOR_MATERIAL_CODE_TO_NAME.items()}
        self.floor_material_direction_list = {v: k for k, v in FLOOR_MATERIAL_DIRECTION_CODE_TO_NAME.items()}
        self.visibility_list = {v: k for k, v in SEGMENT_VISIBILITY_CODE_TO_NAME.items()}
        self.voice_assistant_language_list = {v: k for k, v in VOICE_ASSISTANT_LANGUAGE_TO_NAME.items()}
        self.segment_cleaning_mode_list = {}
        self.segment_cleaning_route_list = {}
        self.warning_codes = [
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
            DreameVacuumErrorCode.UNKNOWN_WARNING_2,
        ]

        self.cleaning_mode = None
        self.mop_pad_humidity = 1
        self.previous_self_clean_area = 0
        self.previous_self_clean_time = 25
        self.self_clean_area_min = 10
        self.self_clean_area_max = 35
        self.self_clean_area_default = 20
        self.self_clean_time_min = 10
        self.self_clean_time_max = 50
        self.self_clean_time_default = 25
        self.self_clean_value = None
        self.ai_policy_accepted = False
        self.go_to_zone: GoToZoneSettings = None
        self.cleanup_completed: bool = False
        self.cleanup_started: bool = False

        self.stream_status = None
        self.stream_session = None

        self.dnd_tasks = None
        self.schedule = []
        self.off_peak_charging_config = None
        self.shortcuts = None

    def _get_property(self, prop: DreameVacuumProperty) -> Any:
        """Helper function for accessing a property from device"""
        return self._device.get_property(prop)

    @property
    def _capability(self) -> DreameVacuumDeviceCapability:
        """Helper property for accessing device capabilities"""
        return self._device.capability

    @property
    def _map_manager(self) -> DreameMapVacuumMapManager | None:
        """Helper property for accessing map manager from device"""
        return self._device._map_manager

    @property
    def _device_connected(self) -> bool:
        """Helper property for accessing device connection status"""
        return self._device.device_connected

    @property
    def serial_number(self) -> int:
        """Return serial number of the device."""
        return self._get_property(DreameVacuumProperty.SERIAL_NUMBER)

    @property
    def battery_level(self) -> int:
        """Return battery level of the device."""
        return self._get_property(DreameVacuumProperty.BATTERY_LEVEL)

    @property
    def suction_level(self) -> DreameVacuumSuctionLevel:
        """Return suction level of the device."""
        value = self._get_property(DreameVacuumProperty.SUCTION_LEVEL)
        if value is not None and value in DreameVacuumSuctionLevel._value2member_map_:
            return DreameVacuumSuctionLevel(value)
        if value is not None:
            _LOGGER.debug("SUCTION_LEVEL not supported: %s", value)
        return DreameVacuumSuctionLevel.UNKNOWN

    @property
    def suction_level_name(self) -> str:
        """Return suction level as string for translation."""
        return SUCTION_LEVEL_CODE_TO_NAME.get(self.suction_level, STATE_UNKNOWN)

    @property
    def water_volume(self) -> DreameVacuumWaterVolume:
        """Return water volume of the device."""
        if self._capability.self_wash_base:
            if self.mop_pad_humidity is None:
                if self._capability.wetness_level:
                    wetness_level = self.status.wetness_level
                    if wetness_level > 32:
                        if wetness_level > 200:
                            return DreameVacuumMopPadHumidity.WET
                        elif wetness_level < 200:
                            return DreameVacuumMopPadHumidity.SLIGHTLY_DRY
                    else:
                        if wetness_level > (14 if self._capability.mop_clean_frequency else 26):
                            return DreameVacuumMopPadHumidity.WET
                        elif wetness_level < 6:
                            return DreameVacuumMopPadHumidity.SLIGHTLY_DRY
                    return DreameVacuumMopPadHumidity.MOIST
                return DreameVacuumMopPadHumidity.UNKNOWN
            return DreameVacuumMopPadHumidity(self.mop_pad_humidity)

        value = self._get_property(DreameVacuumProperty.WATER_VOLUME)
        if value is not None and value in DreameVacuumWaterVolume._value2member_map_:
            return DreameVacuumWaterVolume(value)
        if value is not None:
            _LOGGER.debug("WATER_VOLUME not supported: %s", value)
        return DreameVacuumWaterVolume.UNKNOWN

    @property
    def water_volume_name(self) -> str:
        """Return water volume as string for translation."""
        return WATER_VOLUME_CODE_TO_NAME.get(self.water_volume, STATE_UNKNOWN)

    @property
    def mop_pad_humidity_name(self) -> str:
        """Return mop pad humidity as string for translation."""
        return MOP_PAD_HUMIDITY_CODE_TO_NAME.get(DreameVacuumMopPadHumidity(self.mop_pad_humidity), STATE_UNKNOWN)

    @property
    def cleaning_mode_name(self) -> str:
        """Return cleaning mode as string for translation."""
        return CLEANING_MODE_CODE_TO_NAME.get(self.cleaning_mode, STATE_UNKNOWN)

    @property
    def wetness_level(self) -> int:
        """Return wetness level of the device."""
        return self._get_property(DreameVacuumProperty.WETNESS_LEVEL)

    @property
    def status(self) -> DreameVacuumStatus:
        """Return status of the device."""
        value = self._get_property(DreameVacuumProperty.STATUS)
        if value is not None and value in DreameVacuumStatus._value2member_map_:
            if self.go_to_zone and value == DreameVacuumStatus.ZONE_CLEANING.value:
                return DreameVacuumStatus.CRUISING_POINT
            if value == DreameVacuumStatus.CHARGING.value and not self.charging:
                return DreameVacuumStatus.IDLE
            return DreameVacuumStatus(value)
        if value is not None:
            _LOGGER.debug("STATUS not supported: %s", value)
        return DreameVacuumStatus.UNKNOWN

    @property
    def status_name(self) -> str:
        """Return status as string for translation."""
        return STATUS_CODE_TO_NAME.get(self.status, STATE_UNKNOWN)

    @property
    def task_status(self) -> DreameVacuumTaskStatus:
        """Return task status of the device."""
        value = self._get_property(DreameVacuumProperty.TASK_STATUS)
        if value is not None and value in DreameVacuumTaskStatus._value2member_map_:
            if self.go_to_zone:
                if value == DreameVacuumTaskStatus.ZONE_CLEANING.value:
                    return DreameVacuumTaskStatus.CRUISING_POINT
                if value == DreameVacuumTaskStatus.ZONE_CLEANING_PAUSED.value:
                    return DreameVacuumTaskStatus.CRUISING_POINT_PAUSED
            return DreameVacuumTaskStatus(value)
        if value is not None:
            _LOGGER.debug("TASK_STATUS not supported: %s", value)
        return DreameVacuumTaskStatus.UNKNOWN

    @property
    def task_status_name(self) -> str:
        """Return task status as string for translation."""
        return TASK_STATUS_CODE_TO_NAME.get(self.task_status, STATE_UNKNOWN)

    @property
    def water_tank(self) -> DreameVacuumWaterTank:
        """Return water tank of the device."""
        value = self._get_property(DreameVacuumProperty.WATER_TANK)
        if value is not None:
            if value == 3:
                return DreameVacuumWaterTank.INSTALLED
            if self.mop_in_station:
                return DreameVacuumWaterTank.IN_STATION
            if value == 2:
                return DreameVacuumWaterTank.MOP_INSTALLED

            if value in DreameVacuumWaterTank._value2member_map_:
                return DreameVacuumWaterTank(value)
        if value is not None:
            _LOGGER.debug("WATER_TANK not supported: %s", value)
        return DreameVacuumWaterTank.UNKNOWN

    @property
    def water_tank_name(self) -> str:
        """Return water tank as string for translation."""
        return WATER_TANK_CODE_TO_NAME.get(self.water_tank, STATE_UNKNOWN)

    @property
    def mop_pad_name(self) -> str:
        """Return mop pad as string for translation."""
        return self.water_tank_name

    @property
    def charging_status(self) -> DreameVacuumChargingStatus:
        """Return charging status of the device."""
        value = self._get_property(DreameVacuumProperty.CHARGING_STATUS)
        if value is not None and value in DreameVacuumChargingStatus._value2member_map_:
            value = DreameVacuumChargingStatus(value)
            # Charging status complete is not present on older firmwares
            if value is DreameVacuumChargingStatus.CHARGING and self.battery_level == 100:
                return DreameVacuumChargingStatus.CHARGING_COMPLETED
            return value
        if value is not None:
            _LOGGER.debug("CHARGING_STATUS not supported: %s", value)
        return DreameVacuumChargingStatus.UNKNOWN

    @property
    def charging_status_name(self) -> str:
        """Return charging status as string for translation."""
        return CHARGING_STATUS_CODE_TO_NAME.get(self.charging_status, STATE_UNKNOWN)

    @property
    def auto_empty_status(self) -> DreameVacuumAutoEmptyStatus:
        """Return auto empty status of the device."""
        value = self._get_property(DreameVacuumProperty.AUTO_EMPTY_STATUS)
        if value is not None and value in DreameVacuumAutoEmptyStatus._value2member_map_:
            return DreameVacuumAutoEmptyStatus(value)
        if value is not None:
            _LOGGER.debug("AUTO_EMPTY_STATUS not supported: %s", value)
        return DreameVacuumAutoEmptyStatus.UNKNOWN

    @property
    def auto_empty_status_name(self) -> str:
        """Return auto empty status as string for translation."""
        return AUTO_EMPTY_STATUS_TO_NAME.get(self.auto_empty_status, STATE_UNKNOWN)

    @property
    def relocation_status(self) -> DreameVacuumRelocationStatus:
        """Return relocation status of the device."""
        value = self._get_property(DreameVacuumProperty.RELOCATION_STATUS)
        if value is not None and value in DreameVacuumRelocationStatus._value2member_map_:
            return DreameVacuumRelocationStatus(value)
        if value is not None:
            _LOGGER.debug("RELOCATION_STATUS not supported: %s", value)
        return DreameVacuumRelocationStatus.UNKNOWN

    @property
    def relocation_status_name(self) -> str:
        """Return relocation status as string for translation."""
        return RELOCATION_STATUS_CODE_TO_NAME.get(self.relocation_status, STATE_UNKNOWN)

    @property
    def self_wash_base_status(self) -> DreameVacuumSelfWashBaseStatus:
        """Return self-wash base status of the device."""
        value = self._get_property(DreameVacuumProperty.SELF_WASH_BASE_STATUS)
        if value is not None and value in DreameVacuumSelfWashBaseStatus._value2member_map_:
            return DreameVacuumSelfWashBaseStatus(value)
        if value is not None:
            _LOGGER.debug("SELF_WASH_BASE_STATUS not supported: %s", value)
        return DreameVacuumSelfWashBaseStatus.UNKNOWN

    @property
    def self_wash_base_status_name(self) -> str:
        """Return self-wash base status as string for translation."""
        return SELF_WASH_BASE_STATUS_TO_NAME.get(self.self_wash_base_status, STATE_UNKNOWN)

    @property
    def dust_collection(self) -> DreameVacuumDustCollection:
        value = self._get_property(DreameVacuumProperty.DUST_COLLECTION)
        if value is not None and value in DreameVacuumDustCollection._value2member_map_:
            return DreameVacuumDustCollection(value)
        if value is not None:
            _LOGGER.debug("DUST_COLLECTION not supported: %s", value)
        return DreameVacuumDustCollection.UNKNOWN

    @property
    def dust_collection_name(self) -> str:
        """Return dust collection as string for translation."""
        return DUST_COLLECTION_TO_NAME.get(self.dust_collection, STATE_UNKNOWN)

    @property
    def carpet_sensitivity(self) -> DreameVacuumCarpetSensitivity:
        """Return carpet sensitivity of the device."""
        value = self._get_property(DreameVacuumProperty.CARPET_SENSITIVITY)
        if value is not None and value in DreameVacuumCarpetSensitivity._value2member_map_:
            return DreameVacuumCarpetSensitivity(value)
        if value is not None:
            _LOGGER.debug("CARPET_SENSITIVITY not supported: %s", value)
        return DreameVacuumCarpetSensitivity.UNKNOWN

    @property
    def carpet_sensitivity_name(self) -> str:
        """Return carpet sensitivity as string for translation."""
        return CARPET_SENSITIVITY_CODE_TO_NAME.get(self.carpet_sensitivity, STATE_UNKNOWN)

    @property
    def carpet_cleaning(self) -> DreameVacuumCarpetCleaning:
        """Return carpet cleaning of the device."""
        value = self._get_property(DreameVacuumProperty.CARPET_CLEANING)

        if (
            not self.carpet_recognition
            and self._capability.mop_pad_lifting_plus
            and self._capability.auto_carpet_cleaning
        ):
            return DreameVacuumCarpetCleaning.IGNORE
        elif value == 6 or (value == 3 and self._capability.mop_pad_unmounting and not self.auto_mount_mop):
            return DreameVacuumCarpetCleaning.ADAPTATION

        if value is not None and value in DreameVacuumCarpetCleaning._value2member_map_:
            return DreameVacuumCarpetCleaning(value)
        if value is not None:
            _LOGGER.debug("CARPET_CLEANING not supported: %s", value)
        return DreameVacuumCarpetCleaning.UNKNOWN

    @property
    def carpet_cleaning_name(self) -> str:
        """Return carpet cleaning as string for translation."""
        return CARPET_CLEANING_CODE_TO_NAME.get(self.carpet_cleaning, STATE_UNKNOWN)

    @property
    def state(self) -> DreameVacuumState:
        """Return state of the device."""
        value = self._get_property(DreameVacuumProperty.STATE)
        if (
            value is not None
            and int(value) > 18
            and not self._capability.new_state
            and value in DreameVacuumStateOld._value2member_map_
        ):
            value = DreameVacuumState[DreameVacuumStateOld(value).name].value

        if value is not None and value in DreameVacuumState._value2member_map_:
            if self.go_to_zone and (
                value == DreameVacuumState.IDLE
                or value == DreameVacuumState.SWEEPING.value
                or value == DreameVacuumState.MOPPING.value
                or value == DreameVacuumState.SWEEPING_AND_MOPPING.value
            ):
                if self.paused:
                    return DreameVacuumState.MONITORING_PAUSED
                return DreameVacuumState.MONITORING
            vacuum_state = DreameVacuumState(value)

            ## Determine state as implemented on the app
            if vacuum_state is DreameVacuumState.IDLE:
                if self.started or self.cleaning_paused or self.fast_mapping_paused:
                    return DreameVacuumState.PAUSED
                elif self.docked:
                    if self.washing:
                        return DreameVacuumState.WASHING
                    if self.washing_paused:
                        return DreameVacuumState.WASHING_PAUSED
                    if self.drying:
                        return DreameVacuumState.DRYING
                    if self.charging:
                        return DreameVacuumState.CHARGING
                    ## This is for compatibility with various lovelace vacuum cards
                    ## Device will report idle when charging is completed and vacuum card will display return to dock icon even when robot is docked
                    if self.charging_status is DreameVacuumChargingStatus.CHARGING_COMPLETED:
                        return DreameVacuumState.CHARGING_COMPLETED
            return vacuum_state

        if value is not None:
            _LOGGER.debug("STATE not supported: %s", value)
        return DreameVacuumState.UNKNOWN

    @property
    def state_name(self) -> str:
        """Return state as string for translation."""
        return STATE_CODE_TO_STATE.get(self.state, STATE_UNKNOWN)

    @property
    def mop_wash_level(self) -> DreameVacuumMopWashLevel:
        """Return mop wash level of the device."""
        if self._capability.self_wash_base:
            value = self._get_property(DreameVacuumProperty.MOP_WASH_LEVEL)
            if value is not None and value in DreameVacuumMopWashLevel._value2member_map_:
                return DreameVacuumMopWashLevel(value)
            if value is not None:
                _LOGGER.debug("MOP_WASH_LEVEL not supported: %s", value)
            return DreameVacuumMopWashLevel.UNKNOWN

    @property
    def mop_wash_level_name(self) -> str:
        """Return mop wash level as string for translation."""
        return MOP_WASH_LEVEL_TO_NAME.get(self.mop_wash_level, STATE_UNKNOWN)

    @property
    def mop_clean_frequency(self) -> DreameVacuumMopCleanFrequency:
        """Return mop clean frequency of the device."""
        if self._capability.self_wash_base and self._capability.mop_clean_frequency:
            value = self.self_clean_value
            if value == 0:
                return DreameVacuumMopCleanFrequency.BY_ROOM
            if value is not None and value in DreameVacuumMopCleanFrequency._value2member_map_:
                return DreameVacuumMopCleanFrequency(value)
            if value is not None:
                _LOGGER.debug("MOP_CLEAN_FREQUENCY not supported: %s", value)
            return DreameVacuumMopCleanFrequency.UNKNOWN

    @property
    def mop_clean_frequency_name(self) -> str:
        """Return mop clean frequency as string for translation."""
        return MOP_CLEAN_FREQUENCY_TO_NAME.get(self.mop_clean_frequency, STATE_UNKNOWN)

    @property
    def mopping_type(self) -> DreameVacuumMoppingType:
        value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.MOPPING_TYPE)
        if value is not None:
            if value in DreameVacuumMoppingType._value2member_map_:
                return DreameVacuumMoppingType(value)
            _LOGGER.debug("MOPPING_TYPE not supported: %s", value)
            return DreameVacuumMoppingType.UNKNOWN
        return None

    @property
    def mopping_type_name(self) -> str:
        """Return moping type as string for translation."""
        if self.mopping_type is not None and self.mopping_type in DreameVacuumMoppingType._value2member_map_:
            return MOPPING_TYPE_TO_NAME.get(DreameVacuumMoppingType(self.mopping_type), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def stream_status_name(self) -> str:
        """Return camera stream status as string for translation."""
        return STREAM_STATUS_TO_NAME.get(self.stream_status, STATE_UNKNOWN)

    @property
    def wider_corner_coverage(self) -> DreameVacuumWiderCornerCoverage:
        value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE)
        if value is not None and value < 0:
            value = 0
        if value is not None and value in DreameVacuumWiderCornerCoverage._value2member_map_:
            return DreameVacuumWiderCornerCoverage(value)
        if value is not None:
            _LOGGER.debug("WIDER_CORNER_COVERAGE not supported: %s", value)
        return DreameVacuumWiderCornerCoverage.UNKNOWN

    @property
    def wider_corner_coverage_name(self) -> str:
        """Return wider corner coverage as string for translation."""
        wider_corner_coverage = 0 if self.wider_corner_coverage < 0 else self.wider_corner_coverage
        if (
            wider_corner_coverage is not None
            and wider_corner_coverage in DreameVacuumWiderCornerCoverage._value2member_map_
        ):
            return WIDER_CORNER_COVERAGE_TO_NAME.get(
                DreameVacuumWiderCornerCoverage(wider_corner_coverage), STATE_UNKNOWN
            )
        return STATE_UNKNOWN

    @property
    def mop_pad_swing(self) -> DreameVacuumMopPadSwing:
        if self._capability.mop_pad_swing:
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.MOP_PAD_SWING)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumMopPadSwing._value2member_map_:
                return DreameVacuumMopPadSwing(value)
            if value is not None:
                _LOGGER.debug("MOP_PAD_SWING not supported: %s", value)
            return DreameVacuumMopPadSwing.UNKNOWN

    @property
    def mop_pad_swing_name(self) -> str:
        """Return mop pad swing as string for translation."""
        mop_pad_swing = 0 if self.mop_pad_swing < 0 else self.mop_pad_swing
        if mop_pad_swing is not None and mop_pad_swing in DreameVacuumMopPadSwing._value2member_map_:
            return MOP_PAD_SWING_TO_NAME.get(DreameVacuumMopPadSwing(mop_pad_swing), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def mop_extend_frequency(self) -> DreameVacuumMopExtendFrequency:
        if self._capability.mop_extend:
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.MOP_EXTEND_FREQUENCY)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumMopExtendFrequency._value2member_map_:
                return DreameVacuumMopExtendFrequency(value)
            if value is not None:
                _LOGGER.debug("MOP_EXTEND_FREQUENCY not supported: %s", value)
            return DreameVacuumMopExtendFrequency.UNKNOWN

    @property
    def mop_extend_frequency_name(self) -> str:
        """Return mop pad swing as string for translation."""
        mop_extend_frequency = 0 if self.mop_extend_frequency < 0 else self.mop_extend_frequency
        if (
            mop_extend_frequency is not None
            and mop_extend_frequency in DreameVacuumMopExtendFrequency._value2member_map_
        ):
            return MOP_EXTEND_FREQUENCY_TO_NAME.get(
                DreameVacuumMopExtendFrequency(mop_extend_frequency), STATE_UNKNOWN
            )
        return STATE_UNKNOWN

    @property
    def auto_recleaning(self) -> DreameVacuumSecondCleaning:
        if self._capability.auto_recleaning:
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.AUTO_RECLEANING)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumSecondCleaning._value2member_map_:
                return DreameVacuumSecondCleaning(value)
            if value is not None:
                _LOGGER.debug("AUTO_RECLEANING not supported: %s", value)
            return DreameVacuumSecondCleaning.UNKNOWN

    @property
    def auto_recleaning_name(self) -> str:
        """Return mop pad swing as string for translation."""
        auto_recleaning = 0 if self.auto_recleaning < 0 else self.auto_recleaning
        if auto_recleaning is not None and auto_recleaning in DreameVacuumSecondCleaning._value2member_map_:
            return SECOND_CLEANING_TO_NAME.get(DreameVacuumSecondCleaning(auto_recleaning), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def auto_rewashing(self) -> DreameVacuumSecondCleaning:
        if self._capability.auto_rewashing:
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.AUTO_REWASHING)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumSecondCleaning._value2member_map_:
                return DreameVacuumSecondCleaning(value)
            if value is not None:
                _LOGGER.debug("AUTO_REWASHING not supported: %s", value)
            return DreameVacuumSecondCleaning.UNKNOWN

    @property
    def auto_rewashing_name(self) -> str:
        """Return mop pad swing as string for translation."""
        auto_rewashing = 0 if self.auto_rewashing < 0 else self.auto_rewashing
        if auto_rewashing is not None and auto_rewashing in DreameVacuumSecondCleaning._value2member_map_:
            return SECOND_CLEANING_TO_NAME.get(DreameVacuumSecondCleaning(auto_rewashing), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def cleaning_route(self) -> DreameVacuumCleaningRoute:
        if self._capability.cleaning_route:
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.CLEANING_ROUTE)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumCleaningRoute._value2member_map_:
                return DreameVacuumCleaningRoute(value)
            if value is not None:
                _LOGGER.debug("CLEANING_ROUTE not supported: %s", value)
            return DreameVacuumCleaningRoute.UNKNOWN

    @property
    def cleaning_route_name(self) -> str:
        """Return cleaning route as string for translation."""
        cleaning_route = 0 if self.cleaning_route < 0 else self.cleaning_route
        if cleaning_route is not None and cleaning_route in DreameVacuumCleaningRoute._value2member_map_:
            return CLEANING_ROUTE_TO_NAME.get(DreameVacuumCleaningRoute(cleaning_route), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def custom_mopping_route(self) -> DreameVacuumCustomMoppingRoute:
        if self._capability.custom_mopping_route:
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.MOPPING_TYPE)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumCustomMoppingRoute._value2member_map_:
                if not self.custom_mopping_mode:
                    return DreameVacuumCustomMoppingRoute.OFF
                return DreameVacuumCustomMoppingRoute(value)
            if value is not None:
                _LOGGER.debug("CUSTOM_MOPPING_ROUTE not supported: %s", value)
            return DreameVacuumCustomMoppingRoute.UNKNOWN

    @property
    def custom_mopping_route_name(self) -> str:
        """Return mopping route as string for translation."""
        mopping_route = -2 if self.custom_mopping_route < -2 else self.custom_mopping_route
        if mopping_route is not None and mopping_route in DreameVacuumCustomMoppingRoute._value2member_map_:
            return CUSTOM_MOPPING_ROUTE_TO_NAME.get(DreameVacuumCustomMoppingRoute(mopping_route), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def cleangenius(self) -> DreameVacuumCleanGenius:
        if self._capability.cleangenius:
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.CLEANGENIUS)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumCleanGenius._value2member_map_:
                return DreameVacuumCleanGenius(value)
            if value is not None:
                _LOGGER.debug("CLEANGENIUS not supported: %s", value)
        return DreameVacuumCleanGenius.UNKNOWN

    @property
    def cleangenius_name(self) -> str:
        """Return CleanGenius as string for translation."""
        cleangenius = 0 if not self.cleangenius or self.cleangenius < 0 else self.cleangenius
        if cleangenius is not None and cleangenius in DreameVacuumCleanGenius._value2member_map_:
            return CLEANGENIUS_TO_NAME.get(DreameVacuumCleanGenius(cleangenius), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def cleangenius_mode(self) -> DreameVacuumCleanGeniusMode:
        if self._capability.cleangenius_mode:
            value = self._device.get_property(DreameVacuumProperty.CLEANGENIUS_MODE)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumCleanGeniusMode._value2member_map_:
                return DreameVacuumCleanGeniusMode(value)
            if value is not None:
                _LOGGER.debug("CLEANGENIUS_MODE not supported: %s", value)
        return DreameVacuumCleanGeniusMode.UNKNOWN

    @property
    def cleangenius_mode_name(self) -> str:
        """Return Smart Clean Mode as string for translation."""
        cleangenius_mode = 2 if not self.cleangenius_mode or self.cleangenius_mode < 1 else self.cleangenius_mode
        if cleangenius_mode is not None and cleangenius_mode in DreameVacuumCleanGeniusMode._value2member_map_:
            return CLEANGENIUS_MODE_TO_NAME.get(DreameVacuumCleanGeniusMode(cleangenius_mode), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def water_temperature(self) -> DreameVacuumWaterTemperature:
        if self._capability.water_temperature:
            value = self._device.get_property(DreameVacuumProperty.WATER_TEMPERATURE)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumWaterTemperature._value2member_map_:
                return DreameVacuumWaterTemperature(value)
            if value is not None:
                _LOGGER.debug("WATER_TEMPERATURE not supported: %s", value)
        return DreameVacuumWaterTemperature.UNKNOWN

    @property
    def water_temperature_name(self) -> str:
        """Return Water Temperature as string for translation."""
        water_temperature = self.water_temperature
        if water_temperature is not None and water_temperature in DreameVacuumWaterTemperature._value2member_map_:
            return WATER_TEMPERATURE_TO_NAME.get(DreameVacuumWaterTemperature(water_temperature), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def washing_mode(self) -> DreameVacuumWashingMode:
        if self._capability.cleangenius_mode:
            if self.ultra_clean_mode:
                return DreameVacuumWashingMode.ULTRA_WASHING
            value = self.mop_wash_level.value
            if value is not None and value < 0:
                value = 1
            if value is not None and value in DreameVacuumWashingMode._value2member_map_:
                return DreameVacuumWashingMode(value)
            if value is not None:
                _LOGGER.debug("WASHING_MODE not supported: %s", value)
        return DreameVacuumWashingMode.UNKNOWN

    @property
    def washing_mode_name(self) -> str:
        """Return Washing Mode as string for translation."""
        washing_mode = self.washing_mode
        if washing_mode is not None and washing_mode in DreameVacuumWashingMode._value2member_map_:
            return WASHING_MODE_TO_NAME.get(DreameVacuumWashingMode(washing_mode), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def self_clean_frequency(self) -> DreameVacuumSelfCleanFrequency:
        if self._capability.self_clean_frequency:
            if not self.self_clean_value:
                return DreameVacuumSelfCleanFrequency.BY_ROOM
            value = self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY)
            if value is not None and value < 0:
                value = 0
            if value is not None and value in DreameVacuumSelfCleanFrequency._value2member_map_:
                if value == DreameVacuumSelfCleanFrequency.BY_ROOM.value and (
                    self.current_map and not self.has_saved_map
                ):
                    return DreameVacuumSelfCleanFrequency.BY_AREA
                return DreameVacuumSelfCleanFrequency(value)
            if value is not None:
                _LOGGER.debug("SELF_CLEAN_FREQUENCY not supported: %s", value)
            return DreameVacuumSelfCleanFrequency.UNKNOWN

    @property
    def self_clean_frequency_name(self) -> str:
        """Return self clean frequency as string for translation."""
        self_clean_frequency = 0 if self.self_clean_frequency < 0 else self.self_clean_frequency
        if (
            self_clean_frequency is not None
            and self_clean_frequency in DreameVacuumSelfCleanFrequency._value2member_map_
        ):
            return SELF_CLEAN_FREQUENCY_TO_NAME.get(
                DreameVacuumSelfCleanFrequency(self_clean_frequency), STATE_UNKNOWN
            )
        return STATE_UNKNOWN

    @property
    def auto_empty_mode(self) -> DreameVacuumAutoEmptyMode:
        if self._capability.auto_empty_mode:
            value = self._get_property(DreameVacuumProperty.AUTO_DUST_COLLECTING)
            if value is not None and value in DreameVacuumAutoEmptyMode._value2member_map_:
                return DreameVacuumAutoEmptyMode(value)
            if value is not None:
                _LOGGER.debug("AUTO_EMPTY_MODE not supported: %s", value)
            return DreameVacuumAutoEmptyMode.UNKNOWN

    @property
    def auto_empty_mode_name(self) -> str:
        """Return auto empty mode as string for translation."""
        if self._capability.auto_empty_mode:
            auto_empty_mode = self._get_property(DreameVacuumProperty.AUTO_DUST_COLLECTING)
            if auto_empty_mode is not None and auto_empty_mode in DreameVacuumAutoEmptyMode._value2member_map_:
                return AUTO_EMPTY_MODE_TO_NAME.get(DreameVacuumAutoEmptyMode(auto_empty_mode), STATE_UNKNOWN)
            return STATE_UNKNOWN

    @property
    def low_water_warning(self) -> DreameVacuumLowWaterWarning:
        """Return low water warning of the device."""
        value = self._get_property(DreameVacuumProperty.LOW_WATER_WARNING)
        if value is not None and value in DreameVacuumLowWaterWarning._value2member_map_:
            return DreameVacuumLowWaterWarning(value)
        if value is not None:
            _LOGGER.debug("LOW_WATER_WARNING not supported: %s", value)
        return DreameVacuumLowWaterWarning.UNKNOWN

    @property
    def low_water_warning_name(self) -> str:
        """Return low water warning as string for translation."""
        return LOW_WATER_WARNING_TO_NAME.get(self.low_water_warning, STATE_UNKNOWN)

    @property
    def low_water_warning_name_description(self) -> str:
        """Return low water warning description of the device."""
        return LOW_WATER_WARNING_CODE_TO_DESCRIPTION.get(self.low_water_warning, [STATE_UNKNOWN, ""])

    @property
    def voice_assistant_language(self) -> DreameVacuumVoiceAssistantLanguage:
        """Return voice assistant language of the device."""
        value = self._get_property(DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE)
        if value is not None and value in DreameVacuumVoiceAssistantLanguage._value2member_map_:
            return DreameVacuumVoiceAssistantLanguage(value)
        if value is not None:
            _LOGGER.debug("VOICE_ASSISTANT_LANGUAGE not supported: %s", value)
        return DreameVacuumVoiceAssistantLanguage.DEFAULT

    @property
    def voice_assistant_language_name(self) -> str:
        """Return voice assistant language as string for translation."""
        return VOICE_ASSISTANT_LANGUAGE_TO_NAME.get(self.voice_assistant_language, STATE_UNKNOWN)

    @property
    def drainage_status(self) -> DreameVacuumDrainageStatus:
        """Return drainage status of the device."""
        value = self._get_property(DreameVacuumProperty.DRAINAGE_STATUS)
        if value is not None and value in DreameVacuumDrainageStatus._value2member_map_:
            if self.state == DreameVacuumState.AUTO_WATER_DRAINING or self.state == DreameVacuumState.DRAINING:
                return DreameVacuumDrainageStatus.DRAINING
            return DreameVacuumDrainageStatus(value)
        if value is not None:
            _LOGGER.debug("DRAINAGE_STATUS not supported: %s", value)
        return DreameVacuumDrainageStatus.UNKNOWN

    @property
    def drainage_status_name(self) -> str:
        """Return drainage status as string for translation."""
        return DRAINAGE_STATUS_TO_NAME.get(self.drainage_status, STATE_UNKNOWN)

    @property
    def task_type(self) -> DreameVacuumTaskType:
        """Return drainage status of the device."""
        value = self._get_property(DreameVacuumProperty.TASK_TYPE)
        if value is not None and value in DreameVacuumTaskType._value2member_map_:
            return DreameVacuumTaskType(value)
        if value is not None:
            _LOGGER.debug("TASK_TYPE not supported: %s", value)
        return DreameVacuumTaskType.UNKNOWN

    @property
    def task_type_name(self) -> str:
        """Return drainage status as string for translation."""
        return TASK_TYPE_TO_NAME.get(self.task_type, STATE_UNKNOWN)

    @property
    def faults(self) -> str:
        faults = self._get_property(DreameVacuumProperty.FAULTS)
        return 0 if faults == "" or faults == " " else faults

    @property
    def error(self) -> DreameVacuumErrorCode:
        """Return error of the device."""
        value = self._get_property(DreameVacuumProperty.ERROR)
        if value is not None and value in DreameVacuumErrorCode._value2member_map_:
            if (
                (self._capability.self_wash_base and value == DreameVacuumErrorCode.REMOVE_MOP.value)
                or value == DreameVacuumErrorCode.LOW_BATTERY_TURN_OFF.value
                or value == DreameVacuumErrorCode.UNKNOWN_WARNING_2.value
            ):
                return DreameVacuumErrorCode.NO_ERROR
            return DreameVacuumErrorCode(value)
        if value is not None:
            _LOGGER.debug("ERROR_CODE not supported: %s", value)
        return DreameVacuumErrorCode.UNKNOWN

    @property
    def error_name(self) -> str:
        """Return error as string for translation."""
        if not self.has_error and not self.has_warning:
            return ERROR_CODE_TO_ERROR_NAME.get(DreameVacuumErrorCode.NO_ERROR)
        return ERROR_CODE_TO_ERROR_NAME.get(self.error, STATE_UNKNOWN)

    @property
    def error_description(self) -> str:
        """Return error description of the device."""
        return ERROR_CODE_TO_ERROR_DESCRIPTION.get(self.error, [STATE_UNKNOWN, ""])

    @property
    def error_image(self) -> str:
        """Return error image of the device as base64 string."""
        if not self.has_error:
            return None
        return ERROR_IMAGE.get(ERROR_CODE_TO_IMAGE_INDEX.get(self.error, 19))

    @property
    def low_water(self) -> bool:
        """Returns true when water level in the clean water tank is low."""
        if self._capability.self_wash_base and not self.auto_water_refilling_enabled:
            warning = self.low_water_warning
            return warning and warning.value > 1
        return False

    @property
    def robot_status(self) -> int:  # TODO: Convert to enum
        """Device status for robot icon rendering."""
        value = 0
        if self.running and not self.returning and not self.fast_mapping and not self.cruising:
            value = 1
        elif self.charging:
            value = 2
        elif self.sleeping:
            value = 3
        if self.has_error:
            value += 10
        if self.started and (self.sweeping or self.cruising):
            value += 100
        return value

    @property
    def station_status(self) -> int:  # TODO: Convert to enum
        """Station status for charger icon rendering."""
        if self._capability.auto_empty_base and self.auto_emptying:
            return 1
        if self._capability.self_wash_base:
            value = 0
            if self.washing:
                value = 2
            if self.washing_paused:
                value = 3
            if self.drying:
                value = 4
            if value and self.hot_washing:
                value = value + 10
            return value
        return 0

    @property
    def has_error(self) -> bool:
        """Returns true when an error is present."""
        error = self.error
        return bool(error.value > 0 and not self.has_warning and error is not DreameVacuumErrorCode.BATTERY_LOW)

    @property
    def has_warning(self) -> bool:
        """Returns true when a warning is present and available for dismiss."""
        error = self.error
        return bool(error.value > 0 and error in self.warning_codes)

    @property
    def dust_collection_available(self) -> bool:
        """Returns true when robot is docked and can start auto emptying."""
        return bool(
            (
                self._get_property(DreameVacuumProperty.DUST_COLLECTION) == 1
                or (
                    (self._capability.auto_empty_mode or self._capability.gen5)
                    and self.started
                    and (not self.returning or self.returning_paused)
                    and not self.returning_to_wash
                )
            )
            and (not self.washing or self.washing_paused)
            and not self.draining
            and not self.self_repairing
        )

    @property
    def self_clean(self) -> bool:
        return bool(self._get_property(DreameVacuumProperty.SELF_CLEAN) == 1)

    @property
    def scheduled_clean(self) -> bool:
        if self.started:
            value = self._get_property(DreameVacuumProperty.SCHEDULED_CLEAN)
            return bool(value == 1 or value == 2 or value == 4)
        return False

    @property
    def auto_mount_mop(self) -> bool:
        return bool(
            self._capability.mop_pad_unmounting and self._get_property(DreameVacuumProperty.AUTO_MOUNT_MOP) == 1
        )

    @property
    def camera_light_brightness(self) -> int:
        if self._capability.camera_streaming:
            brightness = self._get_property(DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS)
            if brightness and str(brightness).isnumeric():
                return int(brightness)

    @property
    def dnd_remaining(self) -> bool:
        """Returns remaining seconds to DND period to end."""
        if self.dnd:
            dnd_start = self.dnd_start
            dnd_end = self.dnd_end
            if dnd_start and dnd_end:
                end_time = dnd_end.split(":")
                if len(end_time) == 2:
                    now = datetime.now()
                    hour = now.hour
                    minute = now.minute
                    if minute < 10:
                        minute = f"0{minute}"

                    time = int(f"{hour}{minute}")
                    start = int(dnd_start.replace(":", ""))
                    end = int(dnd_end.replace(":", ""))
                    current_seconds = hour * 3600 + int(minute) * 60
                    end_seconds = int(end_time[0]) * 3600 + int(end_time[1]) * 60

                    if (
                        start < end
                        and start < time
                        and time < end
                        or end < start
                        and (2400 > time and time > start or end > time and time > 0)
                        or time == start
                        or time == end
                    ):
                        return (
                            (end_seconds + 86400 - current_seconds)
                            if current_seconds > end_seconds
                            else (end_seconds - current_seconds)
                        )
                return 0
        return None

    @property
    def water_tank_or_mop_installed(self) -> bool:
        """Returns true when water tank or additional mop is installed to the device."""
        installed = self._get_property(DreameVacuumProperty.WATER_TANK) != DreameVacuumWaterTank.NOT_INSTALLED.value
        if self._capability.mop_pad_unmounting:
            value = self._get_property(DreameVacuumProperty.MOP_PAD_INSTALLED)
            if value is not None:
                return bool(value == 0 or installed)
        return bool(installed or self._capability.embedded_tank)

    @property
    def mop_pad_installed(self) -> bool:
        """Returns true when mop is installed on vacuums with mop pad unmounting feature."""
        if self._capability.mop_pad_unmounting:
            value = self._get_property(DreameVacuumProperty.MOP_PAD_INSTALLED)
            return self.water_tank_or_mop_installed if value is None else bool(value == 0)
        return self.water_tank_or_mop_installed

    @property
    def located(self) -> bool:
        """Returns true when robot knows its position on current map."""
        relocation_status = self.relocation_status
        return bool(
            relocation_status is DreameVacuumRelocationStatus.LOCATED
            or relocation_status is DreameVacuumRelocationStatus.UNKNOWN
            or self.fast_mapping
        )

    @property
    def sweeping(self) -> bool:
        """Returns true when cleaning mode is sweeping therefore cannot set its water volume."""
        cleaning_mode = self.cleaning_mode
        if cleaning_mode is None:
            return not self.water_tank_or_mop_installed
        return bool(
            cleaning_mode is not DreameVacuumCleaningMode.MOPPING
            and cleaning_mode is not DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
            and cleaning_mode is not DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
        )

    @property
    def mopping(self) -> bool:
        """Returns true when cleaning mode is mopping therefore cannot set its suction level."""
        return bool(self.cleaning_mode is DreameVacuumCleaningMode.MOPPING)

    @property
    def mopping_after_sweeping(self) -> bool:
        """Returns true when cleaning mode is mopping after sweeping therefore cannot change the cleaning mode when active."""
        return bool(self.cleaning_mode is DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING)

    @property
    def zone_cleaning(self) -> bool:
        """Returns true when device is currently performing a zone cleaning task."""
        task_status = self.task_status
        return bool(
            self._device_connected
            and self.started
            and (
                task_status is DreameVacuumTaskStatus.ZONE_CLEANING
                or task_status is DreameVacuumTaskStatus.ZONE_CLEANING_PAUSED
                or task_status is DreameVacuumTaskStatus.ZONE_MOPPING_PAUSED
                or task_status is DreameVacuumTaskStatus.ZONE_DOCKING_PAUSED
            )
        )

    @property
    def spot_cleaning(self) -> bool:
        """Returns true when device is currently performing a spot cleaning task."""
        task_status = self.task_status
        return bool(
            self._device_connected
            and self.started
            and (
                task_status is DreameVacuumTaskStatus.SPOT_CLEANING
                or task_status is DreameVacuumTaskStatus.SPOT_CLEANING_PAUSED
                or self.status is DreameVacuumStatus.SPOT_CLEANING
            )
        )

    @property
    def segment_cleaning(self) -> bool:
        """Returns true when device is currently performing a custom segment cleaning task."""
        task_status = self.task_status
        return bool(
            self._device_connected
            and self.started
            and (
                task_status is DreameVacuumTaskStatus.SEGMENT_CLEANING
                or task_status is DreameVacuumTaskStatus.SEGMENT_CLEANING_PAUSED
                or task_status is DreameVacuumTaskStatus.SEGMENT_MOPPING_PAUSED
                or task_status is DreameVacuumTaskStatus.SEGMENT_DOCKING_PAUSED
            )
        )

    @property
    def auto_cleaning(self) -> bool:
        """Returns true when device is currently performing a complete map cleaning task."""
        task_status = self.task_status
        return bool(
            self._device_connected
            and self.started
            and (
                task_status is DreameVacuumTaskStatus.AUTO_CLEANING
                or task_status is DreameVacuumTaskStatus.AUTO_CLEANING_PAUSED
                or task_status is DreameVacuumTaskStatus.AUTO_MOPPING_PAUSED
                or task_status is DreameVacuumTaskStatus.AUTO_DOCKING_PAUSED
            )
        )

    @property
    def fast_mapping(self) -> bool:
        """Returns true when device is creating a new map."""
        return bool(
            self._device_connected
            and (
                self.task_status is DreameVacuumTaskStatus.FAST_MAPPING
                or self.status is DreameVacuumStatus.FAST_MAPPING
                or self.fast_mapping_paused
            )
        )

    @property
    def fast_mapping_paused(self) -> bool:
        """Returns true when creating a new map paused by user.
        Used for resuming fast cleaning on start because standard start action can not be used for resuming fast mapping.
        """

        state = self._get_property(DreameVacuumProperty.STATE)
        task_status = self.task_status
        return bool(
            (
                task_status is DreameVacuumTaskStatus.FAST_MAPPING
                or task_status is DreameVacuumTaskStatus.MAP_CLEANING_PAUSED
            )
            and (
                state == DreameVacuumState.PAUSED.value
                or state == DreameVacuumState.ERROR.value
                or state == DreameVacuumState.IDLE.value
            )
        )

    @property
    def draining(self) -> bool:
        """Returns true when device has a self-wash base and draining is performing."""
        return bool(self._capability.drainage and self.drainage_status is DreameVacuumDrainageStatus.DRAINING)

    @property
    def draining_complete(self) -> bool:
        """Returns true when device has a self-wash base and draining is performing."""
        return bool(
            self._capability.drainage
            and (
                self.drainage_status is DreameVacuumDrainageStatus.DRAINING_FAILED
                or self.drainage_status is DreameVacuumDrainageStatus.DRAINING_SUCCESS
            )
        )

    @property
    def self_repairing(self) -> bool:
        """Returns true when device is self repairing/testing or water checking."""
        status = self.status
        return bool(
            status is DreameVacuumStatus.SELF_REPAIR
            or status is DreameVacuumStatus.WATER_CHECK
            or self.state is DreameVacuumState.WATER_CHECK
        )

    @property
    def station_cleaning(self) -> bool:
        """Returns true when base station is cleaning."""
        task_status = self.task_status
        return bool(task_status is DreameVacuumTaskStatus.STATION_CLEANING)

    @property
    def cruising(self) -> bool:
        """Returns true when device is cruising."""
        if self._capability.cruising:
            task_status = self.task_status
            status = self.status
            return bool(
                task_status is DreameVacuumTaskStatus.CRUISING_PATH
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT
                or task_status is DreameVacuumTaskStatus.CRUISING_PATH_PAUSED
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT_PAUSED
                or status is DreameVacuumStatus.CRUISING_PATH
                or status is DreameVacuumStatus.CRUISING_POINT
            )
        return bool(self.go_to_zone)

    @property
    def cruising_paused(self) -> bool:
        """Returns true when cruising paused."""
        if self._capability.cruising:
            task_status = self.task_status
            return bool(
                task_status is DreameVacuumTaskStatus.CRUISING_PATH_PAUSED
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT_PAUSED
            )
        if self.go_to_zone:
            status = self.status
            if self.started and (
                status is DreameVacuumStatus.PAUSED
                or status is DreameVacuumStatus.SLEEPING
                or status is DreameVacuumStatus.IDLE
                or status is DreameVacuumStatus.STANDBY
            ):
                return True
        return False

    @property
    def carpet_avoidance(self) -> bool:
        """Returns true when carpet avoidance is enabled."""
        return bool(
            self._capability.carpet_recognition
            and (
                self.carpet_cleaning is DreameVacuumCarpetCleaning.AVOIDANCE
                or self.carpet_cleaning is DreameVacuumCarpetCleaning.IGNORE
            )
        )

    @property
    def resume_cleaning(self) -> bool:
        """Returns true when resume_cleaning is enabled."""
        return bool(
            self._get_property(DreameVacuumProperty.RESUME_CLEANING) == (2 if self._capability.auto_charging else 1)
        )

    @property
    def carpet_recognition(self) -> bool:
        """Returns true when carpet recognition is enabled."""
        return bool(
            self._capability.carpet_recognition and self._get_property(DreameVacuumProperty.CARPET_RECOGNITION) == 1
        )

    @property
    def mop_in_station(self) -> bool:
        """Returns true when the mop pad is in the station."""
        value = self._get_property(DreameVacuumProperty.MOP_IN_STATION)
        return bool(value == 1 or value == 4) and not self.docked

    @property
    def auto_add_detergent(self) -> bool:
        """Returns true when auto-add detergent feature is enabled."""
        value = self._get_property(DreameVacuumProperty.AUTO_ADD_DETERGENT)
        return bool(value == 1 or value == 3)

    @property
    def cleaning_paused(self) -> bool:
        """Returns true when device battery is too low for resuming its task and needs to be charged before continuing."""
        return bool(self._get_property(DreameVacuumProperty.CLEANING_PAUSED))

    @property
    def charging(self) -> bool:
        """Returns true when device is currently charging."""
        return bool(self.charging_status is DreameVacuumChargingStatus.CHARGING and self.battery_level < 100)

    @property
    def docked(self) -> bool:
        """Returns true when device is docked."""
        return bool(
            (
                self.charging
                or self.charging_status is DreameVacuumChargingStatus.CHARGING_COMPLETED
                or self.washing
                or self.drying
                or self.washing_paused
            )
            and not (self.running and not self.returning and not self.fast_mapping and not self.cruising)
        )

    @property
    def sleeping(self) -> bool:
        """Returns true when device is sleeping."""
        return bool(self.status is DreameVacuumStatus.SLEEPING)

    @property
    def returning_paused(self) -> bool:
        """Returns true when returning to dock is paused."""
        task_status = self.task_status
        return bool(
            self._device_connected
            and not self.docked
            and (
                task_status is DreameVacuumTaskStatus.DOCKING_PAUSED
                or task_status is DreameVacuumTaskStatus.AUTO_DOCKING_PAUSED
                or task_status is DreameVacuumTaskStatus.SEGMENT_DOCKING_PAUSED
                or task_status is DreameVacuumTaskStatus.ZONE_DOCKING_PAUSED
            )
        )

    @property
    def returning(self) -> bool:
        """Returns true when returning to dock for charging or washing."""
        return bool(
            self._device_connected
            and (self.status is DreameVacuumStatus.BACK_HOME or self.returning_to_wash)
            and not self.docked
        )

    @property
    def started(self) -> bool:
        """Returns true when device has an active task.
        Used for preventing updates on settings that relates to currently performing task.
        """
        status = self.status
        return bool(
            (
                self.task_status is not DreameVacuumTaskStatus.COMPLETED
                and self.task_status is not DreameVacuumTaskStatus.DOCKING_PAUSED
            )
            or self.cleaning_paused
            or status is DreameVacuumStatus.CLEANING
            or status is DreameVacuumStatus.SEGMENT_CLEANING
            or status is DreameVacuumStatus.ZONE_CLEANING
            or status is DreameVacuumStatus.SPOT_CLEANING
            or status is DreameVacuumStatus.PART_CLEANING
            or status is DreameVacuumStatus.FAST_MAPPING
            or status is DreameVacuumStatus.CRUISING_PATH
            or status is DreameVacuumStatus.CRUISING_POINT
            or status is DreameVacuumStatus.SHORTCUT
        )

    @property
    def paused(self) -> bool:
        """Returns true when device has an active paused task."""
        status = self.status
        return bool(
            self.cleaning_paused
            or self.cruising_paused
            or (
                self.started
                and (
                    status is DreameVacuumStatus.PAUSED
                    or status is DreameVacuumStatus.SLEEPING
                    or status is DreameVacuumStatus.IDLE
                    or status is DreameVacuumStatus.STANDBY
                )
            )
        )

    @property
    def active(self) -> bool:
        """Returns true when device is moving or not sleeping."""
        return self.status is DreameVacuumStatus.STANDBY or self.running

    @property
    def running(self) -> bool:
        """Returns true when device is moving."""
        status = self.status
        return bool(
            not (
                self.charging
                or self.charging_status is DreameVacuumChargingStatus.CHARGING_COMPLETED
                or self.washing
                or self.drying
                or self.washing_paused
            )
            and (
                status is DreameVacuumStatus.CLEANING
                or status is DreameVacuumStatus.BACK_HOME
                or status is DreameVacuumStatus.PART_CLEANING
                or status is DreameVacuumStatus.FOLLOW_WALL
                or status is DreameVacuumStatus.REMOTE_CONTROL
                or status is DreameVacuumStatus.SEGMENT_CLEANING
                or status is DreameVacuumStatus.ZONE_CLEANING
                or status is DreameVacuumStatus.SPOT_CLEANING
                or status is DreameVacuumStatus.PART_CLEANING
                or status is DreameVacuumStatus.FAST_MAPPING
                or status is DreameVacuumStatus.CRUISING_PATH
                or status is DreameVacuumStatus.CRUISING_POINT
                or status is DreameVacuumStatus.SUMMON_CLEAN
                or status is DreameVacuumStatus.SHORTCUT
                or status is DreameVacuumStatus.PERSON_FOLLOW
            )
        )

    @property
    def shortcut_task(self) -> bool:
        """Returns true when device has an active shortcut task."""
        if self.started and self.shortcuts:
            for k, v in self.shortcuts.items():
                if v.running:
                    return True
        return False

    @property
    def auto_emptying(self) -> bool:
        """Returns true when device is auto emptying."""
        return bool(self.auto_empty_status is DreameVacuumAutoEmptyStatus.ACTIVE)

    @property
    def auto_emptying_not_performed(self) -> bool:
        """Returns true when auto emptying is not performed due to DND settings."""
        return bool(self.auto_empty_status is DreameVacuumAutoEmptyStatus.NOT_PERFORMED)

    @property
    def customized_cleaning(self) -> bool:
        """Returns true when customized cleaning feature is enabled."""
        return bool(
            self._get_property(DreameVacuumProperty.CUSTOMIZED_CLEANING)
            and self.has_saved_map
            and not self.cleangenius_cleaning
        )

    @property
    def cleangenius_cleaning(self) -> bool:
        """Returns true when CleanGenius feature is enabled."""
        return bool(
            self._capability.cleangenius
            and self._get_property(DreameVacuumAutoSwitchProperty.CLEANGENIUS)
            and self.mop_pad_installed
            and not self.zone_cleaning
            and not self.spot_cleaning
        )

    @property
    def custom_mopping_mode(self) -> bool:
        """Returns true when custom mopping mode feature is enabled."""
        return bool(
            self._capability.mopping_settings
            and self._get_property(DreameVacuumAutoSwitchProperty.CUSTOM_MOPPING_MODE) == 1
        )

    @property
    def max_suction_power(self) -> bool:
        """Returns true when max suction power feature is enabled."""
        return bool(
            self._capability.max_suction_power
            and self._get_property(DreameVacuumAutoSwitchProperty.MAX_SUCTION_POWER) == 1
        )

    @property
    def ultra_clean_mode(self) -> bool:
        """Returns true when ultra clean mode is enabled."""
        return bool(
            self._capability.ultra_clean_mode
            and self._get_property(DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE) == 1
        )

    @property
    def mop_extend(self) -> bool:
        """Returns true when mop extend feature is enabled."""
        return bool(self._capability.mop_extend and self._get_property(DreameVacuumAutoSwitchProperty.MOP_EXTEND) == 1)

    @property
    def smart_mop_washing(self) -> bool:
        """Returns true when smart mop washing feature is enabled."""
        return bool(
            self._capability.smart_mop_washing and self._get_property(DreameVacuumProperty.SMART_MOP_WASHING) == 1
        )

    @property
    def multi_map(self) -> bool:
        """Returns true when multi floor map feature is enabled."""
        return bool(self._get_property(DreameVacuumProperty.MULTI_FLOOR_MAP))

    @property
    def last_cleaning_time(self) -> datetime | None:
        if self._cleaning_history:
            return self._last_cleaning_time

    @property
    def last_cruising_time(self) -> datetime | None:
        if self._cruising_history:
            return self._last_cruising_time

    @property
    def cleaning_history(self) -> dict[str, Any] | None:
        """Returns the cleaning history list as dict."""
        if self._cleaning_history:
            if self._cleaning_history_attrs is None:
                list = {}
                for history in self._cleaning_history:
                    date = time.strftime("%m-%d %H:%M", time.localtime(history.date.timestamp()))
                    list[date] = {
                        ATTR_TIMESTAMP: history.date.timestamp(),
                        ATTR_CLEANING_TIME: f"{history.cleaning_time} min",
                        ATTR_CLEANED_AREA: f"{history.cleaned_area} m²",
                    }
                    if history.status is not None:
                        list[date][ATTR_STATUS] = (
                            STATUS_CODE_TO_NAME.get(history.status, STATE_UNKNOWN).replace("_", " ").capitalize()
                        )
                    if history.suction_level is not None:
                        list[date][ATTR_SUCTION_LEVEL] = (
                            SUCTION_LEVEL_CODE_TO_NAME.get(history.suction_level, STATE_UNKNOWN)
                            .replace("_", " ")
                            .capitalize()
                        )
                    if history.completed is not None:
                        list[date][ATTR_COMPLETED] = history.completed
                    if history.water_tank_or_mop is not None:
                        list[date][ATTR_MOP_PAD if self._capability.self_wash_base else ATTR_WATER_TANK] = (
                            WATER_TANK_CODE_TO_NAME.get(history.water_tank_or_mop, STATE_UNKNOWN)
                            .replace("_", " ")
                            .capitalize()
                        )
                    if isinstance(history.neglected_segments, dict):
                        list[date][ATTR_NEGLECTED_SEGMENTS] = {
                            k: v.name.replace("_", " ").capitalize() for k, v in history.neglected_segments.items()
                        }
                    if history.cleanup_method is not None:
                        list[date][ATTR_CLEANUP_METHOD] = history.cleanup_method.name.replace("_", " ").capitalize()
                    if history.task_interrupt_reason is not None:
                        list[date][ATTR_INTERRUPT_REASON] = history.task_interrupt_reason.name.replace(
                            "_", " "
                        ).capitalize()
                    if history.multiple_cleaning_time is not None:
                        list[date][ATTR_MULTIPLE_CLEANING_TIME] = history.multiple_cleaning_time
                self._cleaning_history_attrs = list
            return self._cleaning_history_attrs

    @property
    def cruising_history(self) -> dict[str, Any] | None:
        """Returns the cruising history list as dict."""
        if self._cruising_history:
            if self._cruising_history_attrs is None:
                list = {}
                for history in self._cruising_history:
                    date = time.strftime("%m-%d %H:%M", time.localtime(history.date.timestamp()))
                    list[date] = {
                        ATTR_CRUISING_TIME: f"{history.cleaning_time} min",
                    }
                    if history.status is not None:
                        list[date][ATTR_STATUS] = (
                            STATUS_CODE_TO_NAME.get(history.status, STATE_UNKNOWN).replace("_", " ").capitalize()
                        )
                    if history.cruise_type is not None:
                        list[date][ATTR_CRUISING_TYPE] = history.cruise_type
                    if history.map_index is not None:
                        list[date][ATTR_MAP_INDEX] = history.map_index
                    if history.map_name is not None and len(history.map_name) > 1:
                        list[date][ATTR_MAP_NAME] = history.map_name
                    if history.completed is not None:
                        list[date][ATTR_COMPLETED] = history.completed
                self._cruising_history_attrs = list
            return self._cruising_history_attrs

    @property
    def washing(self) -> bool:
        """Returns true the when device is currently performing mop washing."""
        return bool(
            self._capability.self_wash_base
            and (
                self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.WASHING
                or self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.CLEAN_ADD_WATER
            )
        )

    @property
    def drying(self) -> bool:
        """Returns true the when device is currently performing mop drying."""
        return bool(
            self._capability.self_wash_base and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.DRYING
        )

    @property
    def washing_paused(self) -> bool:
        """Returns true when mop washing paused."""
        return bool(
            self._capability.self_wash_base and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.PAUSED
        )

    @property
    def returning_to_wash(self) -> bool:
        """Returns true when the device returning to self-wash base to wash or dry its mop."""
        return bool(
            self._capability.self_wash_base
            and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.RETURNING
            and (self.state is DreameVacuumState.RETURNING or self.state is DreameVacuumState.RETURNING_TO_WASH)
        )

    @property
    def returning_to_wash_paused(self) -> bool:
        """Returns true when the device returning to self-wash base to wash or dry its mop."""
        return bool(
            self._capability.self_wash_base
            and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.RETURNING
            and self.state is DreameVacuumState.PAUSED
        )

    @property
    def washing_available(self) -> bool:
        """Returns true when device has a self-wash base and washing mop can be performed."""
        return bool(
            self._capability.self_wash_base
            and (self.water_tank_or_mop_installed or self.mop_in_station)
            and not (
                self.washing
                or self.washing_paused
                or self.returning_to_wash_paused
                or self.returning_to_wash
                or self.returning
                or self.returning_paused
                or self.cleaning_paused
                # or self.drying
            )
        )

    @property
    def drying_available(self) -> bool:
        """Returns true when device has a self-wash base and drying mop can be performed."""
        return bool(
            self._capability.self_wash_base
            and self.water_tank_or_mop_installed
            and self.docked
            and not (self.washing or self.washing_paused)
            and not self.started
        )

    @property
    def maximum_maps(self) -> int:
        return (
            1 if not self._capability.lidar_navigation or not self.multi_map else 4 if self._capability.wifi_map else 3
        )

    @property
    def mapping_available(self) -> bool:
        """Returns true when creating a new map is possible."""
        return bool(
            not self.started
            and not self.fast_mapping
            and (not self._device.capability.map or self.maximum_maps > len(self.map_list))
        )

    @property
    def second_cleaning_available(self) -> bool:
        if self._capability.auto_recleaning and self._cleaning_history and self.current_map:
            history = self._cleaning_history[0]
            if history.object_name:
                map_data = self._history_map_data.get(history.object_name)
                return bool(
                    (map_data is not None and self.current_map.map_id == map_data.map_id)
                    and (
                        bool(history.neglected_segments)
                        or bool(
                            history.cleanup_method.value == 2
                            and not (history.mopping_mode != 2 and not self.mop_pad_installed)
                            and (history.second_mopping == 2 or map_data.cleaned_segments)
                            and map_data.cleaning_map_data is not None
                            and map_data.cleaning_map_data.has_dirty_area
                        )
                    )
                )
        return False

    @property
    def main_brush_life(self) -> int:
        """Returns main brush remaining life in percent."""
        return self._get_property(DreameVacuumProperty.MAIN_BRUSH_LEFT)

    @property
    def side_brush_life(self) -> int:
        """Returns side brush remaining life in percent."""
        return self._get_property(DreameVacuumProperty.SIDE_BRUSH_LEFT)

    @property
    def filter_life(self) -> int:
        """Returns filter remaining life in percent."""
        return self._get_property(DreameVacuumProperty.FILTER_LEFT)

    @property
    def sensor_dirty_life(self) -> int:
        """Returns sensor clean remaining time in percent."""
        return self._get_property(DreameVacuumProperty.SENSOR_DIRTY_LEFT)

    @property
    def tank_filter_life(self) -> int:
        """Returns tank filter remaining life in percent."""
        return self._get_property(DreameVacuumProperty.TANK_FILTER_LEFT)

    @property
    def mop_life(self) -> int:
        """Returns mop remaining life in percent."""
        return self._get_property(DreameVacuumProperty.MOP_PAD_LEFT)

    @property
    def silver_ion_life(self) -> int:
        """Returns silver-ion life in percent."""
        return self._get_property(DreameVacuumProperty.SILVER_ION_LEFT)

    @property
    def detergent_life(self) -> int:
        """Returns detergent life in percent."""
        return self._get_property(DreameVacuumProperty.DETERGENT_LEFT)

    @property
    def squeegee_life(self) -> int:
        """Returns squeegee life in percent."""
        return self._get_property(DreameVacuumProperty.SQUEEGEE_LEFT)

    @property
    def onboard_dirty_water_tank_life(self) -> int:
        """Returns onboard dirty water tank life in percent."""
        return self._get_property(DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT)

    @property
    def dirty_water_tank_life(self) -> int:
        """Returns dirty water tank life in percent."""
        return self._get_property(DreameVacuumProperty.DIRTY_WATER_TANK_LEFT)

    @property
    def deodorizer_life(self) -> int:
        """Returns deodorizer life in percent."""
        return self._get_property(DreameVacuumProperty.DEODORIZER_LEFT)

    @property
    def wheel_dirty_life(self) -> int:
        """Returns wheel life in percent."""
        return self._get_property(DreameVacuumProperty.WHEEL_DIRTY_LEFT)

    @property
    def scale_inhibitor_life(self) -> int:
        """Returns scale inhibitor life in percent."""
        return self._get_property(DreameVacuumProperty.SCALE_INHIBITOR_LEFT)

    @property
    def dnd(self) -> bool | None:
        """Returns DND is enabled."""
        if self._capability.dnd:
            return (
                bool(self._get_property(DreameVacuumProperty.DND))
                if not self._capability.dnd_task
                else self.dnd_tasks[0].get("en") if self.dnd_tasks and len(self.dnd_tasks) else False
            )

    @property
    def dnd_start(self) -> str | None:
        """Returns DND start time."""
        if self._capability.dnd:
            return (
                self._get_property(DreameVacuumProperty.DND_START)
                if not self._capability.dnd_task
                else self.dnd_tasks[0].get("st") if self.dnd_tasks and len(self.dnd_tasks) else "22:00"
            )

    @property
    def dnd_end(self) -> str | None:
        """Returns DND end time."""
        if self._capability.dnd:
            return (
                self._get_property(DreameVacuumProperty.DND_END)
                if not self._capability.dnd_task
                else self.dnd_tasks[0].get("et") if self.dnd_tasks and len(self.dnd_tasks) else "08:00"
            )

    @property
    def off_peak_charging(self) -> bool | None:
        """Returns Off-Peak charging is enabled."""
        if self._capability.off_peak_charging:
            return bool(
                self._capability.off_peak_charging
                and len(self.off_peak_charging_config)
                and self.off_peak_charging_config.get("enable")
            )

    @property
    def off_peak_charging_start(self) -> str | None:
        """Returns Off-Peak charging start time."""
        if self._capability.off_peak_charging:
            return (
                self.off_peak_charging_config.get("startTime")
                if self.off_peak_charging_config and len(self.off_peak_charging_config)
                else "22:00"
            )

    @property
    def off_peak_charging_end(self) -> str | None:
        """Returns Off-Peak charging end time."""
        if self._capability.off_peak_charging:
            return (
                self.off_peak_charging_config.get("endTime")
                if self.off_peak_charging_config and len(self.off_peak_charging_config)
                else "08:00"
            )

    @property
    def auto_water_refilling_enabled(self) -> bool:
        """Returns true when auto water refilling is enabled."""
        return bool(self._get_property(DreameVacuumProperty.AUTO_WATER_REFILLING) == 1)

    @property
    def water_draining_available(self) -> bool:
        """Returns true when water tank draining is possible."""
        return bool(
            self._capability.drainage
            and self.auto_water_refilling_enabled
            and not self.draining
            and self.docked
            and not self.drying
            and not self.washing
            and not self.washing_paused
            and not self.started
        )

    @property
    def floor_direction_cleaning_available(self) -> bool:
        """Returns true when water tank draining is possible."""
        return bool(
            self._capability.floor_direction_cleaning
            and not self.started
            and not self.has_temporary_map
            and not self.fast_mapping
            and self.segments
            and len([k for k, v in self.segments.items() if v.floor_material_direction is not None])
        )

    @property
    def ai_obstacle_detection(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_OBSTACLE_DETECTION)

    @property
    def ai_obstacle_image_upload(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_OBSTACLE_IMAGE_UPLOAD)

    @property
    def ai_pet_detection(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_PET_DETECTION)

    @property
    def ai_furniture_detection(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_FURNITURE_DETECTION)

    @property
    def ai_fluid_detection(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_FLUID_DETECTION)

    @property
    def ai_obstacle_picture(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_OBSTACLE_PICTURE)

    @property
    def fill_light(self) -> bool:
        return self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.FILL_LIGHT)

    @property
    def hot_washing(self) -> bool:
        if self._capability.water_temperature:
            return self.hot_water_status.value == 1
        return (
            self._capability.hot_washing
            and self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.HOT_WASHING) == 1
        )

    @property
    def auto_drying(self) -> bool:
        if self._device.capability.self_wash_base:
            if not self._device.capability.auto_switch_settings:
                return bool(self._get_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION))
            return bool(self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.AUTO_DRYING) == 1)
        return False

    @property
    def smart_drying(self) -> bool:
        return bool(
            self._device.capability.smart_drying
            and self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.SMART_DRYING) == 1
        )

    @property
    def silent_drying(self) -> bool:
        return bool(
            self._device.capability.silent_drying
            and self._device.get_property(DreameVacuumProperty.SILENT_DRYING) == 1
        )

    @property
    def stain_avoidance(self) -> bool:
        return bool(self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.STAIN_AVOIDANCE) == 2)

    @property
    def pet_focused_cleaning(self) -> bool:
        return self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.PET_FOCUSED_CLEANING)

    @property
    def uv_sterilization(self) -> bool:
        return (
            self._capability.uv_sterilization
            and self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.UV_STERILIZATION) == 1
        )

    @property
    def self_clean_by_time(self) -> bool:
        return (
            self.self_clean_value
            and self._capability.self_clean_frequency
            and self._device.get_auto_switch_property(DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY) == 2
        )

    @property
    def map_backup_status(self) -> int | None:
        value = self._get_property(DreameVacuumProperty.MAP_BACKUP_STATUS)
        if value == 1:
            return 2
        return value

    @property
    def map_backup_status_name(self) -> str:
        """Return map backup status as string for translation."""
        return MAP_BACKUP_STATUS_TO_NAME.get(self.map_backup_status, STATE_UNKNOWN)

    @property
    def map_recovery_status(self) -> int | None:
        value = self._get_property(DreameVacuumProperty.MAP_RECOVERY_STATUS)
        if value == 1:
            return 2
        return value

    @property
    def map_recovery_status_name(self) -> str:
        """Return map recovery status as string for translation."""
        return MAP_RECOVERY_STATUS_TO_NAME.get(self.map_recovery_status, STATE_UNKNOWN)

    @property
    def clean_water_tank_status(self) -> DreameVacuumCleanWaterTankStatus:
        """Return clean water tank status of the device."""
        value = self._get_property(DreameVacuumProperty.CLEAN_WATER_TANK_STATUS)
        if value is not None and value in DreameVacuumCleanWaterTankStatus._value2member_map_:
            if value == DreameVacuumCleanWaterTankStatus.ACTIVE.value:
                value = DreameVacuumCleanWaterTankStatus.INSTALLED.value
            return DreameVacuumCleanWaterTankStatus(value)
        if value is not None:
            _LOGGER.debug("CLEAN_WATER_TANK_STATUS not supported: %s", value)
        return DreameVacuumCleanWaterTankStatus.UNKNOWN

    @property
    def clean_water_tank_status_name(self) -> str:
        """Return clean water tank status as string for translation."""
        return CLEAN_WATER_TANK_STATUS_TO_NAME.get(self.clean_water_tank_status, STATE_UNKNOWN)

    @property
    def dirty_water_tank_status(self) -> DreameVacuumDirtyWaterTankStatus:
        """Return dirty water tank status of the device."""
        value = self._get_property(DreameVacuumProperty.DIRTY_WATER_TANK_STATUS)
        if value is not None and value in DreameVacuumDirtyWaterTankStatus._value2member_map_:
            return DreameVacuumDirtyWaterTankStatus(value)
        if value is not None:
            _LOGGER.debug("DIRTY_WATER_TANK_STATUS not supported: %s", value)
        return DreameVacuumDirtyWaterTankStatus.UNKNOWN

    @property
    def dirty_water_tank_status_name(self) -> str:
        """Return dirty water tank status as string for translation."""
        return DIRTY_WATER_TANK_STATUS_TO_NAME.get(self.dirty_water_tank_status, STATE_UNKNOWN)

    @property
    def dust_bag_status(self) -> DreameVacuumDustBagStatus:
        """Return dust bag status of the device."""
        value = self._get_property(DreameVacuumProperty.DUST_BAG_STATUS)
        if value is not None and value in DreameVacuumDustBagStatus._value2member_map_:
            return DreameVacuumDustBagStatus(value)
        if value is not None:
            _LOGGER.debug("DUST_BAG_STATUS not supported: %s", value)
        return DreameVacuumDustBagStatus.UNKNOWN

    @property
    def dust_bag_status_name(self) -> str:
        """Return dust bag status as string for translation."""
        return DUST_BAG_STATUS_TO_NAME.get(self.dust_bag_status, STATE_UNKNOWN)

    @property
    def detergent_status(self) -> DreameVacuumDetergentStatus:
        """Return detergent status of the device."""
        value = self._get_property(DreameVacuumProperty.DETERGENT_STATUS)
        if value is not None and value in DreameVacuumDetergentStatus._value2member_map_:
            return DreameVacuumDetergentStatus(value)
        if value is not None:
            _LOGGER.debug("DETERGENT_STATUS not supported: %s", value)
        return DreameVacuumDetergentStatus.UNKNOWN

    @property
    def detergent_status_name(self) -> str:
        """Return detergent status as string for translation."""
        return DETERGENT_STATUS_TO_NAME.get(self.detergent_status, STATE_UNKNOWN)

    @property
    def hot_water_status(self) -> DreameVacuumHotWaterStatus:
        """Return hot water status of the device."""
        value = self._get_property(DreameVacuumProperty.HOT_WATER_STATUS)
        if value is not None and value in DreameVacuumHotWaterStatus._value2member_map_:
            return DreameVacuumHotWaterStatus(value)
        if value is not None:
            _LOGGER.debug("HOT_WATER_STATUS not supported: %s", value)
        return DreameVacuumHotWaterStatus.UNKNOWN

    @property
    def hot_water_status_name(self) -> str:
        """Return hot water status as string for translation."""
        return HOT_WATER_STATUS_TO_NAME.get(self.hot_water_status, STATE_UNKNOWN)

    @property
    def station_drainage_status(self) -> DreameVacuumStationDrainageStatus:
        """Return station drainage status of the device."""
        value = self._get_property(DreameVacuumProperty.STATION_DRAINAGE_STATUS)
        if value is not None and value in DreameVacuumStationDrainageStatus._value2member_map_:
            return DreameVacuumStationDrainageStatus(value)
        if value is not None:
            _LOGGER.debug("STATION_DRAINAGE_STATUS not supported: %s", value)
        return DreameVacuumStationDrainageStatus.UNKNOWN

    @property
    def station_drainage_status_name(self) -> str:
        """Return station drainage status as string for translation."""
        return STATION_DRAINAGE_STATUS_TO_NAME.get(self.station_drainage_status, STATE_UNKNOWN)

    @property
    def custom_order(self) -> bool:
        """Returns true when custom cleaning sequence is set."""
        if self.cleangenius_cleaning and not self._capability.cleangenius_mode:
            return False
        segments = self.current_segments
        if segments:
            for v in segments.values():
                if v.order:
                    return True
        return False

    @property
    def segment_order(self) -> list[int] | None:
        """Returns cleaning order list."""
        segments = self.current_segments
        if segments:
            return (
                list(
                    sorted(
                        segments,
                        key=lambda segment_id: segments[segment_id].order if segments[segment_id].order else 99,
                    )
                )
                if self.custom_order
                else None
            )
        return [] if self.custom_order else None

    @property
    def has_saved_map(self) -> bool:
        """Returns true when device has saved map and knowns its location on saved map."""
        if self._map_manager is None:
            return True

        current_map = self.current_map
        return bool(
            current_map is not None
            and current_map.saved_map_status == 2
            and not self.has_temporary_map
            and not self.has_new_map
            and not current_map.empty_map
        )

    @property
    def has_temporary_map(self) -> bool:
        """Returns true when device cannot store the newly created map and waits prompt for restoring or discarding it."""
        if self._map_manager is None:
            return False

        current_map = self.current_map
        return bool(current_map is not None and current_map.temporary_map and not current_map.empty_map)

    @property
    def has_new_map(self) -> bool:
        """Returns true when fast mapping from empty map."""
        if self._map_manager is None:
            return False

        current_map = self.current_map
        return bool(
            current_map is not None
            and not current_map.temporary_map
            and not current_map.empty_map
            and current_map.new_map
        )

    @property
    def selected_map(self) -> MapData | None:
        """Return the selected map data"""
        if self._map_manager and not self.has_temporary_map and not self.has_new_map:
            return self._map_manager.selected_map

    @property
    def current_map(self) -> MapData | None:
        """Return the current map data"""
        if self._map_manager:
            return self._map_manager.get_map()

    @property
    def map_list(self) -> list[int] | None:
        """Return the saved map id list if multi floor map is enabled"""
        if self._map_manager:
            if self.multi_map:
                return self._map_manager.map_list

            selected_map = self._map_manager.selected_map
            if selected_map:
                return [selected_map.map_id]
        return []

    @property
    def map_data_list(self) -> dict[int, MapData] | None:
        """Return the saved map data list if multi floor map is enabled"""
        if self._map_manager:
            if self.multi_map:
                return self._map_manager.map_data_list
            selected_map = self.selected_map
            if selected_map:
                return {selected_map.map_id: selected_map}
        return {}

    @property
    def current_segments(self) -> dict[int, Segment] | None:
        """Return the segments of current map"""
        current_map = self.current_map
        if current_map and current_map.segments and not current_map.empty_map:
            return current_map.segments
        return {}

    @property
    def segments(self) -> dict[int, Segment] | None:
        """Return the segments of selected map"""
        current_map = self.selected_map
        if current_map and current_map.segments and not current_map.empty_map:
            return current_map.segments
        return {}

    @property
    def current_room(self) -> Segment | None:
        """Return the segment that device is currently on"""
        if self._capability.lidar_navigation:
            current_map = self.current_map
            if current_map and current_map.segments and current_map.robot_segment and not current_map.empty_map:
                return current_map.segments[current_map.robot_segment]

    @property
    def cleaning_sequence(self) -> list[int] | None:
        """Returns custom segment cleaning sequence list."""
        if self._map_manager:
            return self._map_manager.cleaning_sequence

    @property
    def previous_cleaning_sequence(self):
        if self.current_map and self.current_map.map_id in self._previous_cleaning_sequence:
            return self._previous_cleaning_sequence[self.current_map.map_id]

    @property
    def active_segments(self) -> list[int] | None:
        map_data = self.current_map
        if map_data and self.started and not self.fast_mapping:
            if self.segment_cleaning:
                if map_data.active_segments:
                    return map_data.active_segments
            elif (
                not self.zone_cleaning
                and not self.spot_cleaning
                and map_data.segments
                and not self.docked
                and not self.returning
                and not self.returning_paused
            ):
                return list(map_data.segments.keys())
            return []

    @property
    def job(self) -> dict[str, Any] | None:
        details = {
            ATTR_STATUS: self.status.name,
        }
        if self._device._protocol.cloud:
            details[ATTR_DID] = self._device._protocol.cloud.device_id
        if self._capability.custom_cleaning_mode:
            details[ATTR_CLEANING_MODE] = self.cleaning_mode.name
        details[ATTR_WATER_TANK if not self._capability.self_wash_base else ATTR_MOP_PAD] = (
            self.water_tank_or_mop_installed
        )

        if self.cleanup_completed:
            details.update(
                {
                    ATTR_CLEANED_AREA: self._get_property(DreameVacuumProperty.CLEANED_AREA),
                    ATTR_CLEANING_TIME: self._get_property(DreameVacuumProperty.CLEANING_TIME),
                    ATTR_COMPLETED: True,
                }
            )
        else:
            details[ATTR_COMPLETED] = False

        map_data = self.current_map
        if map_data:
            if map_data.active_segments:
                details[ATTR_ACTIVE_SEGMENTS] = map_data.active_segments
            elif map_data.active_areas is not None:
                if self.go_to_zone:
                    details[ATTR_ACTIVE_CRUISE_POINTS] = {
                        1: Coordinate(self.go_to_zone.x, self.go_to_zone.y, False, 0)
                    }
                else:
                    details[ATTR_ACTIVE_AREAS] = map_data.active_areas
            elif map_data.active_points is not None:
                details[ATTR_ACTIVE_POINTS] = map_data.active_points
            elif map_data.predefined_points is not None:
                details[ATTR_PREDEFINED_POINTS] = map_data.predefined_points
            elif map_data.active_cruise_points is not None:
                details[ATTR_ACTIVE_CRUISE_POINTS] = map_data.active_cruise_points
        return details

    @property
    def attributes(self) -> dict[str, Any] | None:
        """Return the attributes of the device."""
        properties = [
            DreameVacuumProperty.STATUS,
            DreameVacuumProperty.CLEANING_MODE,
            DreameVacuumProperty.SUCTION_LEVEL,
            DreameVacuumProperty.TIGHT_MOPPING,
            DreameVacuumProperty.ERROR,
            DreameVacuumProperty.LOW_WATER_WARNING,
            DreameVacuumProperty.CLEANING_TIME,
            DreameVacuumProperty.CLEANED_AREA,
            DreameVacuumProperty.VOICE_PACKET_ID,
            DreameVacuumProperty.TIMEZONE,
            DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT,
            DreameVacuumProperty.MAIN_BRUSH_LEFT,
            DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT,
            DreameVacuumProperty.SIDE_BRUSH_LEFT,
            DreameVacuumProperty.FILTER_LEFT,
            DreameVacuumProperty.FILTER_TIME_LEFT,
            DreameVacuumProperty.TANK_FILTER_LEFT,
            DreameVacuumProperty.TANK_FILTER_TIME_LEFT,
            DreameVacuumProperty.MOP_PAD_LEFT,
            DreameVacuumProperty.MOP_PAD_TIME_LEFT,
            DreameVacuumProperty.SILVER_ION_LEFT,
            DreameVacuumProperty.SILVER_ION_TIME_LEFT,
            DreameVacuumProperty.DETERGENT_LEFT,
            DreameVacuumProperty.DETERGENT_TIME_LEFT,
            DreameVacuumProperty.SQUEEGEE_LEFT,
            DreameVacuumProperty.SQUEEGEE_TIME_LEFT,
            DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_LEFT,
            DreameVacuumProperty.ONBOARD_DIRTY_WATER_TANK_TIME_LEFT,
            DreameVacuumProperty.DIRTY_WATER_TANK_LEFT,
            DreameVacuumProperty.DIRTY_WATER_TANK_TIME_LEFT,
            DreameVacuumProperty.TOTAL_CLEANED_AREA,
            DreameVacuumProperty.TOTAL_CLEANING_TIME,
            DreameVacuumProperty.CLEANING_COUNT,
            DreameVacuumProperty.CUSTOMIZED_CLEANING,
            DreameVacuumProperty.NATION_MATCHED,
            DreameVacuumProperty.TOTAL_RUNTIME,
            DreameVacuumProperty.TOTAL_CRUISE_TIME,
            DreameVacuumProperty.DRYING_PROGRESS,
            DreameVacuumProperty.CLEANING_PROGRESS,
            DreameVacuumProperty.INTELLIGENT_RECOGNITION,
            DreameVacuumProperty.MULTI_FLOOR_MAP,
            DreameVacuumProperty.WETNESS_LEVEL,
            DreameVacuumProperty.SCHEDULED_CLEAN,
            DreameVacuumProperty.VOICE_ASSISTANT,
            DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE,
            DreameVacuumProperty.AUTO_DUST_COLLECTING,
            DreameVacuumProperty.AUTO_EMPTY_STATUS,
            DreameVacuumProperty.SELF_CLEAN,
            DreameVacuumProperty.DRYING_TIME,
            DreameVacuumProperty.OBSTACLE_AVOIDANCE,
            DreameVacuumProperty.VOLUME,
            DreameVacuumProperty.CHILD_LOCK,
            DreameVacuumProperty.RESUME_CLEANING,
            DreameVacuumProperty.MAP_SAVING,
            DreameVacuumProperty.CARPET_BOOST,
            DreameVacuumProperty.SCHEDULE,
            DreameVacuumProperty.MAP_RECOVERY_STATUS,
            DreameVacuumProperty.DETERGENT_STATUS,
        ]

        if self._capability.deodorizer:
            properties.append(DreameVacuumProperty.DEODORIZER_LEFT)
            properties.append(DreameVacuumProperty.DEODORIZER_TIME_LEFT)

        if self._capability.wheel:
            properties.append(DreameVacuumProperty.WHEEL_DIRTY_LEFT)
            properties.append(DreameVacuumProperty.WHEEL_DIRTY_TIME_LEFT)

        if self._capability.scale_inhibitor:
            properties.append(DreameVacuumProperty.SCALE_INHIBITOR_LEFT)
            properties.append(DreameVacuumProperty.SCALE_INHIBITOR_TIME_LEFT)

        if self._capability.backup_map:
            properties.append(DreameVacuumProperty.MAP_BACKUP_STATUS)

        if not self._capability.disable_sensor_cleaning:
            properties.extend(
                [
                    DreameVacuumProperty.SENSOR_DIRTY_LEFT,
                    DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
                ]
            )

        if not self._capability.dnd_task:
            properties.extend(
                [
                    DreameVacuumProperty.DND_START,
                    DreameVacuumProperty.DND_END,
                ]
            )

        if not self._capability.carpet_recognition:
            properties.append(DreameVacuumProperty.CARPET_SENSITIVITY)
        elif not self._capability.auto_carpet_cleaning and not self._capability.mop_pad_lifting_plus:
            properties.append(DreameVacuumProperty.CARPET_RECOGNITION)

        if (
            self._capability.mop_pad_unmounting
            or self._capability.auto_carpet_cleaning
            or self._capability.mop_pad_lifting_plus
        ):
            properties.append(DreameVacuumProperty.CARPET_CLEANING)

        if not self._capability.auto_empty_mode:
            properties.append(DreameVacuumProperty.AUTO_EMPTY_FREQUENCY)

        if self._capability.mop_pad_unmounting:
            properties.append(DreameVacuumProperty.AUTO_MOUNT_MOP)

        if self._capability.detergent or self._capability.smart_mop_washing:
            properties.append(DreameVacuumProperty.AUTO_ADD_DETERGENT)

        if self._capability.clean_carpets_first:
            properties.append(DreameVacuumProperty.CLEAN_CARPETS_FIRST)

        if self._capability.auto_empty_base:
            properties.append(DreameVacuumProperty.DUST_BAG_STATUS)

        if self._capability.drainage:
            properties.append(DreameVacuumProperty.STATION_DRAINAGE_STATUS)

        if self._capability.hot_washing:
            properties.append(DreameVacuumProperty.HOT_WATER_STATUS)

        attributes = {}

        customized = (
            not self.zone_cleaning
            and not self.spot_cleaning
            and self.has_saved_map
            and (self.cleangenius_cleaning or self.customized_cleaning)
        )
        if not self._capability.self_wash_base:
            if not self._capability.embedded_tank:
                attributes[ATTR_WATER_TANK] = self.water_tank_or_mop_installed
                properties.append(DreameVacuumProperty.WATER_VOLUME)
        else:
            attributes[ATTR_MOP_PAD] = self.water_tank_or_mop_installed
            attributes[ATTR_MOP_PAD_HUMIDITY] = self.mop_pad_humidity_name.replace("_", " ").capitalize()
            attributes[f"{ATTR_MOP_PAD_HUMIDITY}_list"] = (
                [v.replace("_", " ").capitalize() for v in self.mop_pad_humidity_list.keys()]
                if PROPERTY_AVAILABILITY["mop_pad_humidity"](self._device) or customized
                else []
            )
            properties.extend(
                [
                    DreameVacuumProperty.CLEAN_WATER_TANK_STATUS,
                    DreameVacuumProperty.DIRTY_WATER_TANK_STATUS,
                ]
            )

            if self._capability.mop_clean_frequency:
                attributes[ATTR_MOP_CLEAN_FREQUENCY] = self.self_clean_value
            else:
                if self.self_clean_value is not None:
                    attributes[ATTR_SELF_CLEAN_TIME if self.self_clean_by_time else ATTR_SELF_CLEAN_AREA] = (
                        self.self_clean_value
                    )
                attributes[ATTR_SELF_CLEAN_AREA_MIN] = self.self_clean_area_min
                attributes[ATTR_SELF_CLEAN_AREA_MAX] = self.self_clean_area_max
                attributes[ATTR_PREVIOUS_SELF_CLEAN_AREA] = self.previous_self_clean_area
                if self._capability.self_clean_frequency:
                    attributes[ATTR_SELF_CLEAN_TIME_MIN] = self.self_clean_time_min
                    attributes[ATTR_SELF_CLEAN_TIME_MAX] = self.self_clean_time_max
                    attributes[ATTR_PREVIOUS_SELF_CLEAN_TIME] = self.previous_self_clean_time

            if not self._capability.smart_mop_washing:
                if self._capability.ultra_clean_mode:
                    properties.append(DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE)

                properties.append(DreameVacuumProperty.MOP_WASH_LEVEL)
            else:
                properties.append(DreameVacuumProperty.SMART_MOP_WASHING)

                attributes[ATTR_WASHING_MODE] = self.washing_mode_name.replace("_", " ").capitalize()
                attributes[f"{ATTR_WASHING_MODE}_list"] = (
                    [v.replace("_", " ").capitalize() for v in self.washing_mode_list.keys()]
                    if PROPERTY_AVAILABILITY["washing_mode"](self._device)
                    else []
                )

            if self._capability.mop_washing_with_detergent:
                properties.append(DreameVacuumProperty.MOP_WASHING_WITH_DETERGENT)

        if self._capability.auto_switch_settings:
            properties.extend(
                [
                    DreameVacuumAutoSwitchProperty.MOPPING_MODE,
                    DreameVacuumAutoSwitchProperty.AUTO_DRYING,
                    DreameVacuumAutoSwitchProperty.COLLISION_AVOIDANCE,
                    DreameVacuumAutoSwitchProperty.FILL_LIGHT,
                    DreameVacuumAutoSwitchProperty.STREAMING_VOICE_PROMPT,
                ]
            )

        if self._capability.camera_streaming:
            properties.extend(
                [
                    DreameVacuumAIProperty.AI_OBSTACLE_DETECTION,
                    DreameVacuumAIProperty.AI_PET_DETECTION,
                    DreameVacuumAIProperty.AI_OBSTACLE_PICTURE,
                    DreameVacuumAIProperty.AI_OBSTACLE_IMAGE_UPLOAD,
                    DreameVacuumAIProperty.PET_FOCUSED_DETECTION,
                ]
            )

        if self._capability.large_particles_boost:
            properties.append(DreameVacuumAIProperty.LARGE_PARTICLES_BOOST)

        if self._capability.self_wash_base and self._capability.hot_washing and not self._capability.smart_mop_washing:
            properties.append(DreameVacuumAutoSwitchProperty.HOT_WASHING)

        if self._capability.max_suction_power:
            properties.append(DreameVacuumAutoSwitchProperty.MAX_SUCTION_POWER)

        if self._capability.uv_sterilization:
            properties.append(DreameVacuumAutoSwitchProperty.UV_STERILIZATION)

        if self._capability.custom_cleaning_mode:
            properties.append(DreameVacuumAutoSwitchProperty.CUSTOM_MOPPING_MODE)

        if self._capability.cleaning_route:
            properties.append(DreameVacuumAutoSwitchProperty.CLEANING_ROUTE)

        if self._capability.cleangenius:
            properties.append(DreameVacuumAutoSwitchProperty.CLEANGENIUS)

        if self._capability.cleangenius_mode:
            properties.append(DreameVacuumProperty.CLEANGENIUS_MODE)

        if self._capability.water_temperature:
            properties.append(DreameVacuumProperty.WATER_TEMPERATURE)

        if self._capability.silent_drying:
            properties.append(DreameVacuumProperty.SILENT_DRYING)

        if self._capability.hair_compression:
            properties.append(DreameVacuumProperty.HAIR_COMPRESSION)

        if self._capability.side_brush_carpet_rotate:
            properties.append(DreameVacuumProperty.SIDE_BRUSH_CARPET_ROTATE)

        if self._capability.auto_lds_lifting:
            properties.append(DreameVacuumProperty.AUTO_LDS_LIFTING)

        if self._device.capability.dnd_functions:
            properties.extend(
                [
                    DreameVacuumProperty.DND_DISABLE_RESUME_CLEANING,
                    DreameVacuumProperty.DND_DISABLE_AUTO_EMPTY,
                    DreameVacuumProperty.DND_REDUCE_VOLUME,
                ]
            )

        if (
            self._capability.self_wash_base
            and not self._capability.custom_mopping_route
            and not self._capability.cleaning_route
        ):
            properties.append(DreameVacuumAutoSwitchProperty.MOPPING_TYPE)

        if self._capability.self_wash_base and self._capability.self_clean_frequency:
            properties.append(DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY)

        if self._capability.floor_direction_cleaning:
            properties.append(DreameVacuumAutoSwitchProperty.FLOOR_DIRECTION_CLEANING)

        if self._capability.intensive_carpet_cleaning:
            properties.append(DreameVacuumAutoSwitchProperty.INTENSIVE_CARPET_CLEANING)

        if self._capability.mop_extend:
            properties.append(DreameVacuumAutoSwitchProperty.MOP_EXTEND)
            properties.append(DreameVacuumAutoSwitchProperty.MOP_EXTEND_FREQUENCY)
        elif self._capability.mop_pad_swing:
            properties.append(DreameVacuumAutoSwitchProperty.MOP_PAD_SWING)

        if self._capability.mop_pad_swing_plus:
            properties.append(DreameVacuumAutoSwitchProperty.GAP_CLEANING_EXTENSION)
            properties.append(DreameVacuumAutoSwitchProperty.MOPPING_UNDER_FURNITURES)

        if self._capability.auto_recleaning:
            properties.append(DreameVacuumAutoSwitchProperty.AUTO_RECLEANING)

        if self._capability.auto_rewashing:
            properties.append(DreameVacuumAutoSwitchProperty.AUTO_REWASHING)

        if not self._capability.mop_pad_swing and not self._capability.mop_clean_frequency:
            properties.append(DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE)

        boolean_properties = [
            DreameVacuumProperty.TIGHT_MOPPING,
            DreameVacuumProperty.MULTI_FLOOR_MAP,
            DreameVacuumProperty.INTELLIGENT_RECOGNITION,
            DreameVacuumProperty.SELF_CLEAN,
            DreameVacuumProperty.CHILD_LOCK,
            DreameVacuumProperty.MAP_SAVING,
            DreameVacuumProperty.RESUME_CLEANING,
            DreameVacuumProperty.CARPET_RECOGNITION,
            DreameVacuumProperty.CARPET_CLEANING,
            DreameVacuumProperty.CARPET_BOOST,
            DreameVacuumProperty.CLEAN_CARPETS_FIRST,
            DreameVacuumProperty.OBSTACLE_AVOIDANCE,
            DreameVacuumProperty.AUTO_MOUNT_MOP,
            DreameVacuumProperty.VOICE_ASSISTANT,
            DreameVacuumAutoSwitchProperty.ULTRA_CLEAN_MODE,
            DreameVacuumAutoSwitchProperty.UV_STERILIZATION,
            DreameVacuumAutoSwitchProperty.HOT_WASHING,
            DreameVacuumAutoSwitchProperty.MAX_SUCTION_POWER,
            DreameVacuumAutoSwitchProperty.AUTO_DRYING,
            DreameVacuumAutoSwitchProperty.CUSTOM_MOPPING_MODE,
            DreameVacuumAutoSwitchProperty.MOP_EXTEND,
            DreameVacuumAutoSwitchProperty.INTENSIVE_CARPET_CLEANING,
            DreameVacuumAutoSwitchProperty.FLOOR_DIRECTION_CLEANING,
            DreameVacuumAutoSwitchProperty.GAP_CLEANING_EXTENSION,
            DreameVacuumAutoSwitchProperty.MOPPING_UNDER_FURNITURES,
            DreameVacuumAutoSwitchProperty.COLLISION_AVOIDANCE,
            DreameVacuumAutoSwitchProperty.FILL_LIGHT,
            DreameVacuumAutoSwitchProperty.STREAMING_VOICE_PROMPT,
        ]

        for prop in properties:
            value = self._get_property(prop)
            if value is not None:
                prop_name = PROPERTY_TO_NAME.get(prop.name)
                if prop_name:
                    prop_name = prop_name[0]
                else:
                    prop_name = prop.name.lower()

                if prop is DreameVacuumProperty.ERROR:
                    value = self.error_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.LOW_WATER_WARNING:
                    value = self.low_water_warning_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.STATUS:
                    value = self.status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.AUTO_EMPTY_STATUS:
                    value = self.auto_empty_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.MAP_RECOVERY_STATUS:
                    value = self.map_recovery_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.MAP_BACKUP_STATUS:
                    value = self.map_backup_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.CLEAN_WATER_TANK_STATUS:
                    value = self.clean_water_tank_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.DIRTY_WATER_TANK_STATUS:
                    value = self.dirty_water_tank_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.DUST_BAG_STATUS:
                    value = self.dust_bag_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.DETERGENT_STATUS:
                    value = self.detergent_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.STATION_DRAINAGE_STATUS:
                    value = self.station_drainage_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.HOT_WATER_STATUS:
                    value = self.hot_water_status_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.WATER_VOLUME:
                    value = self.water_volume_name.capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.capitalize() for v in self.water_volume_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device) or customized
                        else []
                    )
                elif prop is DreameVacuumProperty.SUCTION_LEVEL:
                    value = self.suction_level_name.capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.capitalize() for v in self.suction_level_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device) or customized
                        else []
                    )
                elif prop is DreameVacuumProperty.CLEANING_MODE:
                    value = self.cleaning_mode_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.cleaning_mode_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device) or customized
                        else []
                    )
                elif prop is DreameVacuumProperty.MOP_WASH_LEVEL:
                    value = self.mop_wash_level_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.mop_wash_level_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE:
                    if not self._capability.voice_assistant:
                        continue
                    value = self.voice_assistant_language_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = [
                        v.replace("_", " ").capitalize() for v in self.voice_assistant_language_list.keys()
                    ]
                elif prop is DreameVacuumProperty.CLEANGENIUS_MODE:
                    value = self.cleangenius_mode_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.cleangenius_mode_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumProperty.WATER_TEMPERATURE:
                    value = self.water_temperature_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.water_temperature_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.CLEANING_ROUTE:
                    value = self.cleaning_route_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.cleaning_route_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device) or customized
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.CLEANGENIUS:
                    value = self.cleangenius_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.cleangenius_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.MOPPING_TYPE:
                    value = self.mopping_type_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.mopping_type_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE:
                    value = self.wider_corner_coverage_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.wider_corner_coverage_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumProperty.CARPET_CLEANING:
                    value = self.carpet_cleaning_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.carpet_cleaning_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumProperty.CARPET_SENSITIVITY:
                    value = self.carpet_sensitivity_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.carpet_sensitivity_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.MOP_PAD_SWING:
                    value = self.mop_pad_swing_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.mop_pad_swing_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.MOP_EXTEND_FREQUENCY:
                    value = self.mop_extend_frequency_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.mop_extend_frequency_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.AUTO_REWASHING:
                    value = self.auto_rewashing_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.second_cleaning_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumAutoSwitchProperty.AUTO_RECLEANING:
                    value = self.auto_recleaning_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.second_cleaning_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumProperty.CUSTOMIZED_CLEANING:
                    value = bool(value and not self.zone_cleaning and not self.spot_cleaning and self.has_saved_map)
                elif prop is DreameVacuumProperty.SCHEDULED_CLEAN:
                    value = bool(value == 1 or value == 2 or value == 4)
                elif prop is DreameVacuumProperty.AUTO_DUST_COLLECTING:
                    if self._capability.auto_empty_mode:
                        attributes[ATTR_AUTO_EMPTY_MODE] = self.auto_empty_mode_name.replace("_", " ").capitalize()
                        attributes[f"{ATTR_AUTO_EMPTY_MODE}_list"] = [
                            v.replace("_", " ").capitalize() for v in self.auto_empty_mode_list.keys()
                        ]
                    value = bool(value > 0)
                elif prop is DreameVacuumAutoSwitchProperty.SELF_CLEAN_FREQUENCY:
                    value = self.self_clean_frequency_name.replace("_", " ").capitalize()
                    attributes[f"{prop_name}_list"] = (
                        [v.replace("_", " ").capitalize() for v in self.self_clean_frequency_list.keys()]
                        if PROPERTY_AVAILABILITY[prop.name](self._device)
                        else []
                    )
                elif prop is DreameVacuumProperty.SCHEDULE:
                    value = self.schedule
                elif prop in boolean_properties:
                    value = bool(value > 0)
                attributes[prop_name] = value

        if self._capability.dnd_task and self.dnd_tasks is not None:
            attributes[ATTR_DND] = {}
            for dnd_task in self.dnd_tasks:
                attributes[ATTR_DND][dnd_task["id"]] = {
                    "enabled": dnd_task.get("en"),
                    "start": dnd_task.get("st"),
                    "end": dnd_task.get("et"),
                }
        else:
            attributes[ATTR_DND] = self.dnd

        if self._capability.off_peak_charging:
            attributes[ATTR_OFF_PEAK_CHARGING] = self.off_peak_charging
            attributes[ATTR_OFF_PEAK_CHARGING_START] = self.off_peak_charging_start
            attributes[ATTR_OFF_PEAK_CHARGING_END] = self.off_peak_charging_end

        if self._capability.shortcuts:
            attributes[ATTR_SHORTCUTS] = {}
            if self.shortcuts is not None:
                for id, shortcut in self.shortcuts.items():
                    attributes[ATTR_SHORTCUTS][id] = {
                        "name": shortcut.name,
                        "map_id": shortcut.map_id,
                        "running": shortcut.running,
                        "tasks": shortcut.tasks,
                    }

        attributes[ATTR_BATTERY] = self.battery_level
        attributes[ATTR_CLEANING_SEQUENCE] = self.segment_order
        attributes[ATTR_CHARGING] = self.charging
        attributes[ATTR_DOCKED] = self.docked
        attributes[ATTR_STARTED] = self.started
        attributes[ATTR_PAUSED] = self.paused
        attributes[ATTR_RUNNING] = self.running
        attributes[ATTR_RETURNING_PAUSED] = self.returning_paused
        attributes[ATTR_RETURNING] = self.returning
        attributes[ATTR_SEGMENT_CLEANING] = self.segment_cleaning
        attributes[ATTR_ZONE_CLEANING] = self.zone_cleaning
        attributes[ATTR_SPOT_CLEANING] = self.spot_cleaning
        attributes[ATTR_CRUSING] = self.cruising
        attributes[ATTR_VACUUM_STATE] = self.state_name.lower()
        attributes[ATTR_HAS_SAVED_MAP] = self._map_manager is not None and self.has_saved_map
        attributes[ATTR_HAS_TEMPORARY_MAP] = self.has_temporary_map

        if self._capability.lidar_navigation:
            attributes[ATTR_MAPPING] = self.fast_mapping
            attributes[ATTR_MAPPING_AVAILABLE] = self.mapping_available
        if self._capability.auto_empty_base:
            attributes[ATTR_DUST_COLLECTION_AVAILABLE] = self.dust_collection_available

        if self._capability.self_wash_base:
            attributes[ATTR_WASHING] = self.washing
            attributes[ATTR_WASHING_PAUSED] = self.washing
            attributes[ATTR_DRYING] = self.drying
            if not self.auto_water_refilling_enabled:
                attributes[ATTR_LOW_WATER] = bool(self.low_water_warning)
            else:
                attributes[ATTR_DRAINING] = self.draining
            attributes[ATTR_WASHING_AVAILABLE] = bool(
                (self.washing_available or self.washing or self.returning_to_wash_paused or self.washing_paused)
                and not self.draining
                and not self.self_repairing
            )
            attributes[ATTR_DRYING_AVAILABLE] = self.drying_available
            attributes[ATTR_DRAINING_AVAILABLE] = self.water_draining_available

        if self._capability.cleangenius:
            attributes[ATTR_CLEANGENIUS] = bool(
                self.cleangenius_cleaning and not self.zone_cleaning and not self.spot_cleaning and self.has_saved_map
            )

        if self.map_list:
            attributes[ATTR_ACTIVE_SEGMENTS] = self.active_segments
            if self._capability.lidar_navigation:
                attributes[ATTR_CURRENT_SEGMENT] = self.current_room.segment_id if self.current_room else 0
            attributes[ATTR_SELECTED_MAP] = self.selected_map.map_name if self.selected_map else None
            attributes[ATTR_SELECTED_MAP_ID] = self.selected_map.map_id if self.selected_map else None
            attributes[ATTR_SELECTED_MAP_INDEX] = self.current_map.map_index if self.current_map else None
            attributes[ATTR_ROOMS] = {}
            for k, v in self.map_data_list.items():
                attributes[ATTR_ROOMS][v.map_name] = [
                    {ATTR_ID: j, ATTR_NAME: s.name, ATTR_ICON: s.icon} for (j, s) in sorted(v.segments.items())
                ]

        if self._capability.carpet_recognition:
            attributes[ATTR_CARPET_AVOIDANCE] = self.carpet_avoidance

        if self._capability.floor_direction_cleaning:
            attributes[ATTR_FLOOR_DIRECTION_CLEANING_AVAILABLE] = self.floor_direction_cleaning_available

        if self._capability.shortcuts:
            attributes[ATTR_SHORTCUT_TASK] = self.shortcut_task
        attributes[ATTR_FIRMWARE_VERSION] = self._device.info.version
        attributes[ATTR_AP] = self._device.info.ap
        attributes[ATTR_CAPABILITIES] = self._capability.list
        return attributes

    def consumable_life_warning_description(self, consumable_property) -> str:
        description = CONSUMABLE_TO_LIFE_WARNING_DESCRIPTION.get(consumable_property)
        if description:
            value = self._get_property(consumable_property)
            if value is not None and value >= 0 and value <= 5:
                if value != 0 and len(description) > 1:
                    return description[1]
                return description[0]

    def segment_order_list(self, segment) -> list[int] | None:
        order = []
        if self.current_segments:
            order = [
                v.order
                for k, v in sorted(
                    self.current_segments.items(),
                    key=lambda s: s[1].order if s[1].order != None else 0,
                )
                if v.order
            ]
            if not segment.order and len(order):
                order = order + [max(order) + 1]
        return list(map(str, order))


class DreameVacuumDeviceInfo:
    """Container of device information."""

    def __init__(self, data):
        self.data = data
        self.version = 0
        firmware_version = self.firmware_version
        if firmware_version is not None:
            firmware_version = firmware_version.split("_")
            if len(firmware_version) == 2:
                self.version = int(firmware_version[1])

    def __repr__(self):
        return "%s v%s (%s) @ %s - token: %s" % (
            self.model,
            self.version,
            self.mac,
            self.network_interface["localIp"] if self.network_interface else "",
        )

    @property
    def network_interface(self) -> str:
        """Information about network configuration."""
        if "netif" in self.data:
            return self.data["netif"]
        return None

    @property
    def ap(self) -> str:
        """Information about wifi configuration."""
        if "ap" in self.data:
            ap = self.data["ap"]
            return {
                "ssid": ap.get("ssid", ap.get("siid")),
                "bssid": ap.get("bssid"),
                "rssi": ap.get("rssi"),
                "ip": self.ip_address,
            }
        return None

    @property
    def model(self) -> Optional[str]:
        """Model string if available."""
        if "model" in self.data:
            return self.data["model"]
        return None

    @property
    def firmware_version(self) -> Optional[str]:
        """Firmware version if available."""
        if "fw_ver" in self.data and self.data["fw_ver"] is not None:
            return self.data["fw_ver"]
        if "ver" in self.data and self.data["ver"] is not None:
            return self.data["ver"]
        return None

    @property
    def hardware_version(self) -> Optional[str]:
        """Hardware version if available."""
        if "hw_ver" in self.data:
            return self.data["hw_ver"]
        return "Linux"

    @property
    def mac_address(self) -> Optional[str]:
        """MAC address if available."""
        if "mac" in self.data:
            return self.data["mac"]
        return None

    @property
    def ip_address(self) -> Optional[str]:
        """IP address if available."""
        if self.network_interface:
            return self.network_interface.get("localIp")
        return None

    @property
    def manufacturer(self) -> str:
        """Manufacturer name."""
        return "Dreametech™"

    @property
    def raw(self) -> dict[str, Any]:
        """Raw data as returned by the device."""
        return self.data
