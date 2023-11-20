from __future__ import annotations
import logging
import time
import json
import re
import copy
import zlib
import base64
from datetime import datetime
from random import randrange
from threading import Timer
from typing import Any, Optional

from .types import (
    PIID,
    DIID,
    DreameVacuumProperty,
    DreameVacuumPropertyMapping,
    DreameVacuumAction,
    DreameVacuumActionMapping,
    DreameVacuumChargingStatus,
    DreameVacuumTaskStatus,
    DreameVacuumState,
    DreameVacuumWaterTank,
    DreameVacuumCarpetSensitivity,
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
    DreameVacuumSelfCleanArea,
    DreameVacuumMopWashLevel,
    DreameVacuumMoppingType,
    CleaningHistory,
    MapData,
    Segment,
    ATTR_ACTIVE_AREAS,
    ATTR_ACTIVE_POINTS,
    ATTR_ACTIVE_SEGMENTS
)
from .const import (
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    SUCTION_LEVEL_CODE_TO_NAME,
    WATER_VOLUME_CODE_TO_NAME,
    MOP_PAD_HUMIDITY_CODE_TO_NAME,
    CLEANING_MODE_CODE_TO_NAME,
    CARPET_SENSITIVITY_CODE_TO_NAME,
    CHARGING_STATUS_CODE_TO_NAME,
    RELOCATION_STATUS_CODE_TO_NAME,
    SELF_WASH_BASE_STATUS_TO_NAME,
    AUTO_EMPTY_STATUS_TO_NAME,
    TASK_STATUS_CODE_TO_NAME,
    STATE_CODE_TO_STATE,
    ERROR_CODE_TO_ERROR_NAME,
    ERROR_CODE_TO_ERROR_DESCRIPTION,
    STATUS_CODE_TO_NAME,
    WATER_TANK_CODE_TO_NAME,
    DUST_COLLECTION_TO_NAME,
    SELF_AREA_CLEAN_TO_NAME,
    MOP_WASH_LEVEL_TO_NAME,
    MOPPING_TYPE_TO_NAME,
    ERROR_CODE_TO_IMAGE_INDEX,
    PROPERTY_TO_NAME,
    DEVICE_MAP_KEY,
    AI_SETTING_SWITCH,
    AI_SETTING_UPLOAD,
    AI_SETTING_PET,
    AI_SETTING_HUMAN,
    AI_SETTING_FURNITURE,
    AI_SETTING_FLUID,
    ATTR_CHARGING,
    ATTR_CLEANING_SEQUENCE,
    ATTR_STARTED,
    ATTR_PAUSED,
    ATTR_RUNNING,
    ATTR_RETURNING_PAUSED,
    ATTR_RETURNING,
    ATTR_MAPPING,
    ATTR_ROOMS,
    ATTR_CURRENT_SEGMENT,
    ATTR_SELECTED_MAP,
    ATTR_ID,
    ATTR_NAME,
    ATTR_ICON,
    ATTR_STATUS,
    ATTR_CLEANING_MODE,
    ATTR_SUCTION_LEVEL,
    ATTR_WATER_TANK,
    ATTR_COMPLETED,
    ATTR_CLEANING_TIME,
    ATTR_CLEANED_AREA,
    ATTR_MOP_PAD_HUMIDITY,
    ATTR_MOP_PAD,
)
from .resources import ERROR_IMAGE
from .exceptions import (
    DeviceUpdateFailedException,
    InvalidActionException,
    InvalidValueException,
)
from .protocol import DreameVacuumProtocol
from .map import DreameMapVacuumMapManager

_LOGGER = logging.getLogger(__name__)


class DreameVacuumDevice:
    """Support for Dreame Vacuum"""

    property_mapping: dict[DreameVacuumProperty,
                           dict[str, int]] = DreameVacuumPropertyMapping
    action_mapping: dict[DreameVacuumAction,
                         dict[str, int]] = DreameVacuumActionMapping

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
    ) -> None:
        # Used for tracking the task status is changed from cleaning to completed
        self.cleanup_completed: bool = False
        # Used for easy filtering the device from cloud device list and generating unique ids
        self.mac: str = None
        self.token: str = None  # Local api token
        self.host: str = None  # IP address or host name of the device
        # Dictionary for storing the current property values
        self.data: dict[DreameVacuumProperty, Any] = {}
        self.available: bool = False  # Last update is successful or not

        self._update_running: bool = False  # Update is running
        # Previous cleaning mode for restoring it after water tank is installed or removed
        self._previous_cleaning_mode: DreameVacuumCleaningMode = None
        # Device do not request properties that returned -1 as result. This property used for overriding that behavior at first connection
        self._ready: bool = False
        # Last settings properties requested time
        self._last_settings_request: float = 0
        self._last_map_list_request: float = 0  # Last map list property requested time
        self._last_map_request: float = 0  # Last map request trigger time
        self._last_change: float = 0  # Last property change time
        self._last_update_failed: float = 0  # Last update failed time      
        self._cleaning_history_update: float = 0  # Cleaning history update time
        self._update_fail_count: int = 0 # Update failed counter
        # Map Manager object. Only available when cloud connection is present
        self._map_manager: DreameMapVacuumMapManager = None
        self._update_callback = None  # External update callback for device
        self._error_callback = None  # External update failed callback
        # External update callbacks for specific device property
        self._property_update_callback = {}
        self._update_timer: Timer = None  # Update schedule timer
        # Used for requesting consumable properties after reset action otherwise they will only requested when cleaning completed
        self._consumable_reset: bool = False
        self._remote_control: bool = False
        self._dirty_data: dict[DreameVacuumProperty, Any] = {}

        self._name = name
        self.mac = mac
        self.token = token
        self.host = host
        self.two_factor_url = None
        self.status = DreameVacuumDeviceStatus(self)

        self.listen(self._task_status_changed,
                    DreameVacuumProperty.TASK_STATUS)
        self.listen(self._status_changed,
                    DreameVacuumProperty.STATUS)
        self.listen(
            self._charging_status_changed, DreameVacuumProperty.CHARGING_STATUS
        )
        self.listen(self._water_tank_changed, DreameVacuumProperty.WATER_TANK)
        self.listen(self._water_tank_changed, DreameVacuumProperty.AUTO_MOUNT_MOP)
        self.listen(self._ai_obstacle_detection_changed,
                    DreameVacuumProperty.AI_DETECTION)
        self.listen(self._auto_switch_settings_changed,
                    DreameVacuumProperty.AUTO_SWITCH_SETTINGS)
        self.listen(self._intelligent_recognition_changed, DreameVacuumProperty.INTELLIGENT_RECOGNITION)

        self._protocol = DreameVacuumProtocol(self.host, self.token, username, password, country, prefer_cloud)
        if self._protocol.cloud:
            self._map_manager = DreameMapVacuumMapManager(self._protocol)

            self.listen(self._map_list_changed, DreameVacuumProperty.MAP_LIST)
            self.listen(self._recovery_map_list_changed,
                        DreameVacuumProperty.RECOVERY_MAP_LIST)
            self.listen(self._map_property_changed, DreameVacuumProperty.ERROR)
            self.listen(
                self._map_property_changed, DreameVacuumProperty.SELF_WASH_BASE_STATUS
            )
            self.listen(
                self._map_property_changed, DreameVacuumProperty.CUSTOMIZED_CLEANING
            )

            self._map_manager.listen(self._property_changed)
            self._map_manager.listen_error(self._update_failed)

    def _request_properties(self, properties: list[DreameVacuumProperty] = None) -> bool:
        """Request properties from the device."""
        if not properties:
            properties = [prop for prop in DreameVacuumProperty]

            # Remove write only and response only properties from default list
            properties.remove(DreameVacuumProperty.SCHEDULE_ID)
            properties.remove(DreameVacuumProperty.REMOTE_CONTROL)
            properties.remove(DreameVacuumProperty.VOICE_CHANGE)
            properties.remove(DreameVacuumProperty.VOICE_CHANGE_STATUS)
            properties.remove(DreameVacuumProperty.MAP_RECOVERY)
            properties.remove(DreameVacuumProperty.MAP_RECOVERY_STATUS)
            properties.remove(DreameVacuumProperty.CLEANING_START_TIME)
            properties.remove(DreameVacuumProperty.CLEAN_LOG_FILE_NAME)
            properties.remove(DreameVacuumProperty.CLEANING_PROPERTIES)
            properties.remove(DreameVacuumProperty.CLEAN_LOG_STATUS)
            properties.remove(DreameVacuumProperty.MAP_DATA)
            properties.remove(DreameVacuumProperty.FRAME_INFO)
            properties.remove(DreameVacuumProperty.OBJECT_NAME)
            properties.remove(DreameVacuumProperty.MAP_EXTEND_DATA)
            properties.remove(DreameVacuumProperty.ROBOT_TIME)
            properties.remove(DreameVacuumProperty.RESULT_CODE)
            properties.remove(DreameVacuumProperty.OLD_MAP_DATA)
            properties.remove(DreameVacuumProperty.WIFI_MAP)
            properties.remove(DreameVacuumProperty.TAKE_PHOTO)
            properties.remove(DreameVacuumProperty.CAMERA_LIGHT)
            properties.remove(DreameVacuumProperty.CAMERA_BRIGHTNESS)
            properties.remove(DreameVacuumProperty.STREAM_KEEP_ALIVE)
            properties.remove(DreameVacuumProperty.STREAM_UPLOAD)
            properties.remove(DreameVacuumProperty.STREAM_STATUS)
            properties.remove(DreameVacuumProperty.STREAM_AUDIO)
            properties.remove(DreameVacuumProperty.STREAM_RECORD)
            properties.remove(DreameVacuumProperty.STREAM_CODE)
            properties.remove(DreameVacuumProperty.STREAM_SET_CODE)
            properties.remove(DreameVacuumProperty.STREAM_VERIFY_CODE)
            properties.remove(DreameVacuumProperty.STREAM_RESET_CODE)
            properties.remove(DreameVacuumProperty.STREAM_CRUISE_POINT)
            properties.remove(DreameVacuumProperty.STREAM_PROPERTY)
            properties.remove(DreameVacuumProperty.STREAM_FAULT)
            properties.remove(DreameVacuumProperty.STREAM_TASK)
            properties.remove(DreameVacuumProperty.STREAM_SPACE)

        property_list = []
        for prop in properties:
            if prop in self.property_mapping:
                mapping = self.property_mapping[prop]
                # Do not include properties that are not exists on the device
                if "aiid" not in mapping and (
                    not self._ready or prop.value in self.data
                ):
                    property_list.append({"did": str(prop.value), **mapping})

        props = property_list.copy()
        results = []
        while props:
            result = self._protocol.get_properties(props[:15])
            if result is not None:
                results.extend(result)
                props[:] = props[15:]

        changed = False
        callbacks = []
        for prop in results:
            if prop["code"] == 0 and "value" in prop:
                did = int(prop["did"])
                value = prop["value"]
                
                if did in self._dirty_data:
                    if self._dirty_data[did] != value:
                        _LOGGER.info("Property %s Value Discarded: %s <- %s", DreameVacuumProperty(did).name, self._dirty_data[did], value)
                    del self._dirty_data[did]
                    continue

                if self.data.get(did, None) != value:
                    # Do not call external listener when map list and recovery map list properties changed
                    if did != DreameVacuumProperty.MAP_LIST.value and did != DreameVacuumProperty.RECOVERY_MAP_LIST.value:
                        changed = True
                    current_value = self.data.get(did)
                    if current_value is not None:
                        _LOGGER.info(
                            "Property %s Changed: %s -> %s", DreameVacuumProperty(did).name, current_value, value)
                    else:
                        _LOGGER.info(
                            "Property %s Added: %s", DreameVacuumProperty(did).name, value)
                    self.data[did] = value
                    if did in self._property_update_callback:
                        for callback in self._property_update_callback[did]:
                            callbacks.append([callback, current_value])
                            
        if not self._ready:
            self.status.update_static_properties()

        for callback in callbacks:
            callback[0](callback[1])

        if changed:
            self._last_change = time.time()
            if self._ready:
                self._property_changed()
        return changed

    def _update_status(self, task_status: DreameVacuumTaskStatus, status: DreameVacuumStatus) -> None:
        """Update status properties on memory for map renderer to update the image before action is sent to the device."""
        if task_status is not DreameVacuumTaskStatus.COMPLETED:
            new_state = DreameVacuumState.SWEEPING
            if self.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING:
                new_state = DreameVacuumState.MOPPING
            elif self.status.cleaning_mode is DreameVacuumCleaningMode.SWEEPING_AND_MOPPING:
                new_state = DreameVacuumState.SWEEPING_AND_MOPPING
            self._update_property(
                DreameVacuumProperty.STATE, new_state.value
            )

        if status is DreameVacuumStatus.STANDBY:
            self._update_property(
                DreameVacuumProperty.STATE, DreameVacuumState.IDLE.value
            )

        self._update_property(
            DreameVacuumProperty.STATUS, status.value
        )
        self._update_property(
            DreameVacuumProperty.TASK_STATUS, task_status.value
        )

    def _update_property(self, prop: DreameVacuumProperty, value: Any) -> Any:
        """Update device property on memory and notify listeners."""
        if prop in self.property_mapping:
            current_value = self.get_property(prop)
            if current_value != value:                
                self._dirty_data[prop.value] = value
                did = prop.value
                self.data[did] = value

                if did in self._property_update_callback:
                    for callback in self._property_update_callback[did]:
                        callback(current_value)

                self._property_changed()

                return current_value if current_value is not None else value
        return None

    def _map_property_changed(self, previous_property: Any = None) -> None:
        """Update last update time of the map when a property associated with rendering map changed."""
        if self._map_manager:
            self._map_manager.editor.refresh_map()

    def _map_list_changed(self, previous_map_list: Any = None) -> None:
        """Update map list object name on map manager map list property when changed"""
        if self._map_manager:
            map_list = self.get_property(DreameVacuumProperty.MAP_LIST)
            if map_list and map_list != "":
                try:
                    map_list = json.loads(map_list)
                    object_name = map_list.get("object_name")
                    if object_name and object_name != "":
                        self._map_manager.set_map_list_object_name(map_list)
                    else:
                        self._last_map_list_request = 0
                except:
                    pass

    def _recovery_map_list_changed(self, previous_recovery_map_list: Any = None) -> None:
        """Update recovery list object name on map manager recovery list property when changed"""
        if self._map_manager:
            map_list = self.get_property(
                DreameVacuumProperty.RECOVERY_MAP_LIST)
            if map_list and map_list != "":
                try:
                    map_list = json.loads(map_list)
                    object_name = map_list.get("object_name")
                    if object_name and object_name != "":
                        self._map_manager.set_recovery_map_list_object_name(
                            map_list)
                    else:
                        self._last_map_list_request = 0
                except:
                    pass

    def _water_tank_changed(self, previous_water_tank: Any = None) -> None:
        """Update cleaning mode on device when water tank status is changed."""
        # App does not allow you to update cleaning mode when water tank or mop pad is not installed.
        if self.get_property(DreameVacuumProperty.CLEANING_MODE) is not None:
            new_list = CLEANING_MODE_CODE_TO_NAME.copy()
            if not self.status.auto_mount:
                if not self.status.water_tank_or_mop_installed:
                    new_list.pop(DreameVacuumCleaningMode.MOPPING)
                    new_list.pop(DreameVacuumCleaningMode.SWEEPING_AND_MOPPING)
                    if self.status.cleaning_mode != DreameVacuumCleaningMode.SWEEPING:
                        # Store current cleaning mode for future use when water tank is reinstalled                
                        if not self.status.started:
                            self._previous_cleaning_mode = self.status.cleaning_mode
                            self.set_cleaning_mode(DreameVacuumCleaningMode.SWEEPING.value)
                else:
                    if not self.status.mop_pad_lifting_available:
                        new_list.pop(DreameVacuumCleaningMode.SWEEPING)

                        if not self.status.started and self.status.sweeping:
                            if (
                                self._previous_cleaning_mode is not None
                                and self._previous_cleaning_mode
                                != DreameVacuumCleaningMode.SWEEPING
                            ):
                                self.set_cleaning_mode(self._previous_cleaning_mode.value)
                            else:
                                self.set_cleaning_mode(DreameVacuumCleaningMode.SWEEPING_AND_MOPPING.value)
                            # Store current cleaning mode for future use when water tank is removed
                            self._previous_cleaning_mode = self.status.cleaning_mode

            self.status.cleaning_mode_list = {
                v: k for k, v in new_list.items()}

    def _task_status_changed(self, previous_task_status: Any = None) -> None:
        """Task status is a very important property and must be listened to trigger necessary actions when a task started or ended"""
        if previous_task_status is not None:
            if previous_task_status in DreameVacuumTaskStatus._value2member_map_:
                previous_task_status = DreameVacuumTaskStatus(previous_task_status)

            task_status = self.status.task_status
            if previous_task_status is DreameVacuumTaskStatus.COMPLETED:
                # as implemented on the app
                self._update_property(DreameVacuumProperty.CLEANING_TIME, 0)
                self._update_property(DreameVacuumProperty.CLEANED_AREA, 0)

            if self._map_manager is not None:
                # Update map data for renderer to update the map image according to the new task status
                if previous_task_status is DreameVacuumTaskStatus.COMPLETED:
                    if (
                        task_status is DreameVacuumTaskStatus.AUTO_CLEANING
                        or task_status is DreameVacuumTaskStatus.ZONE_CLEANING
                        or task_status is DreameVacuumTaskStatus.SEGMENT_CLEANING
                        or task_status is DreameVacuumTaskStatus.SPOT_CLEANING
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
                if previous_task_status is DreameVacuumTaskStatus.FAST_MAPPING:
                    # as implemented on the app
                    self._update_property(
                        DreameVacuumProperty.CLEANING_TIME, 0)
                    self.cleanup_completed = False
                    if self._map_manager is not None:
                        # Mapping is completed, get the new map list from cloud
                        self._map_manager.request_next_map_list()
                elif self.cleanup_completed is not None:
                    self.cleanup_completed = True     
                    self._cleaning_history_update = time.time()
            else:
                self.cleanup_completed = None if self.status.fast_mapping else False

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
                    DreameVacuumProperty.SENSOR_DIRTY_LEFT,
                    DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
                    DreameVacuumProperty.SECONDARY_FILTER_LEFT,
                    DreameVacuumProperty.SECONDARY_FILTER_TIME_LEFT,
                    DreameVacuumProperty.MOP_PAD_LEFT,
                    DreameVacuumProperty.MOP_PAD_TIME_LEFT,
                    DreameVacuumProperty.SILVER_ION_TIME_LEFT,
                    DreameVacuumProperty.SILVER_ION_LEFT,
                    DreameVacuumProperty.DETERGENT_TIME_LEFT,
                    DreameVacuumProperty.DETERGENT_LEFT,
                    DreameVacuumProperty.TOTAL_CLEANING_TIME,
                    DreameVacuumProperty.CLEANING_COUNT,
                    DreameVacuumProperty.TOTAL_CLEANED_AREA,
                    DreameVacuumProperty.FIRST_CLEANING_DATE,
                    DreameVacuumProperty.SCHEDULE,
                    DreameVacuumProperty.SCHEDULE_CANCEL_REASON,
                    DreameVacuumProperty.CRUISE_SCHEDULE,
                ]

                if self._map_manager is not None:
                    properties.extend(
                        [DreameVacuumProperty.MAP_LIST, DreameVacuumProperty.RECOVERY_MAP_LIST])
                    self._last_map_list_request = time.time()

                try:
                    self._request_properties(properties)
                except Exception as ex:
                    pass

    def _status_changed(self, previous_status: Any = None) -> None:
        if previous_status is not None:
            if previous_status in DreameVacuumStatus._value2member_map_:
                previous_status = DreameVacuumStatus(previous_status)

            status = self.status.status
            if self._remote_control and status is not DreameVacuumStatus.REMOTE_CONTROL and previous_status is not DreameVacuumStatus.REMOTE_CONTROL:
                self._remote_control = False

            if status is DreameVacuumStatus.CHARGING and previous_status is DreameVacuumStatus.BACK_HOME:
                self._cleaning_history_update = time.time()

        self._map_property_changed()

    def _charging_status_changed(self, previous_charging_status: Any = None) -> None:
        self._remote_control = False
        self._map_property_changed()

    def _ai_obstacle_detection_changed(self, previous_ai_obstacle_detection: Any = None) -> None:
        """AI Detection property returns multiple values as json or int this function parses and sets the sub properties to memory"""
        value = self.get_property(DreameVacuumProperty.AI_DETECTION)
        if isinstance(value, str):
            settings = json.loads(value)

            if AI_SETTING_SWITCH in settings:
                self.status.ai_obstacle_detection = settings[AI_SETTING_SWITCH]
            if AI_SETTING_UPLOAD in settings:
                self.status.obstacle_image_upload = settings[AI_SETTING_UPLOAD]
            if AI_SETTING_PET in settings:
                self.status.pet_detection = settings[AI_SETTING_PET]
            if AI_SETTING_HUMAN in settings:
                self.status.human_detection = settings[AI_SETTING_HUMAN]
            if AI_SETTING_FURNITURE in settings:
                self.status.furniture_detection = settings[AI_SETTING_FURNITURE]
            if AI_SETTING_FLUID in settings:
                self.status.fluid_detection = settings[AI_SETTING_FLUID]
        elif isinstance(value, int):
            self.status.furniture_detection = (value & 1) == 1
            self.status.ai_obstacle_detection = (value & 2) == 2
            self.status.obstacle_picture = (value & 4) == 4
            self.status.fluid_detection = (value & 8) == 8
            self.status.pet_detection = (value & 16) == 16
            self.status.obstacle_image_upload = (value & 32) == 32
            self.status.ai_picture = (value & 64) == 64

        self.status.ai_policy_accepted = bool(self.status.ai_policy_accepted or self.status.ai_obstacle_detection or self.status.obstacle_picture)

    def _auto_switch_settings_changed(self, previous_auto_switch_settings: Any = None) -> None:
        value = self.get_property(DreameVacuumProperty.AUTO_SWITCH_SETTINGS)
        if isinstance(value, str) and len(value) > 2:
            try:
                settings = json.loads(value)
                self.status.collision_avoidance = 0
                self.status.fill_light = 0
                self.status.auto_drying = 0
                self.status.stain_avoidance = 0
                self.status.mopping_type = 0

                if len(settings):
                    for setting in settings:
                        key = setting["k"]
                        value = setting["v"]

                        if key == "LessColl":
                            self.status.collision_avoidance = value
                        elif key == "FillinLight":
                            self.status.fill_light = value
                        elif key == "AutoDry":
                            self.status.auto_drying = value
                        elif key == "StainIdentify":
                            self.status.stain_avoidance = value
                        elif key == "CleanType":
                            self.status.mopping_type = value
            except:
                pass

    def _intelligent_recognition_changed(self, previous_intelligent_recognition: Any = None) -> None:
        if not self.status.auto_switch_settings_available:
            self.status.auto_drying = self.get_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION)        

    def _request_cleaning_history(self) -> None:
        """Get and parse the cleaning history from cloud event data and set it to memory"""
        if self.cloud_connected and self._cleaning_history_update != 0 and (self._cleaning_history_update == -1 or self.status._cleaning_history is None or (time.time() - self._cleaning_history_update >= 5 and self.status.task_status is DreameVacuumTaskStatus.COMPLETED)):
            self._cleaning_history_update = 0

            _LOGGER.debug("Get Cleaning History")
            try:
                # Limit the results
                start = None
                total = self.get_property(DreameVacuumProperty.CLEANING_COUNT)
                if total > 0:
                    start = self.get_property(
                        DreameVacuumProperty.FIRST_CLEANING_DATE)

                if start is None:
                    start = int(time.time())
                if total is None:
                    total = 5
                limit = 40
                if total < 20:
                    limit = total + 20

                # Cleaning history is generated from events of status property that has been sent to cloud by the device when it changed
                result = self._protocol.cloud.get_device_event(
                    DIID(DreameVacuumProperty.STATUS,
                         self.property_mapping), limit, start
                )
                if result:
                    cleaning_history = []
                    history_size = 0
                    for data in result:
                        history_data = json.loads(data["value"])

                        history = CleaningHistory()

                        for history_data_item in history_data:
                            piid = history_data_item["piid"]
                            value = history_data_item["value"]
                            if piid == PIID(DreameVacuumProperty.STATUS, self.property_mapping):
                                if value in DreameVacuumStatus._value2member_map_:
                                    history.status = DreameVacuumStatus(value)
                                else:
                                    history.status = DreameVacuumStatus.UNKNOWN
                            elif piid == PIID(DreameVacuumProperty.CLEANING_TIME, self.property_mapping):
                                history.cleaning_time = value
                            elif piid == PIID(DreameVacuumProperty.CLEANED_AREA, self.property_mapping):
                                history.cleaned_area = value
                            elif piid == PIID(DreameVacuumProperty.SUCTION_LEVEL, self.property_mapping):
                                if value in DreameVacuumSuctionLevel._value2member_map_:
                                    history.suction_level = DreameVacuumSuctionLevel(value)
                                else:
                                    history.suction_level = DreameVacuumSuctionLevel.UNKNOWN
                            elif piid == PIID(DreameVacuumProperty.CLEANING_START_TIME, self.property_mapping):
                                history.date = datetime.fromtimestamp(value)
                            elif piid == PIID(DreameVacuumProperty.CLEAN_LOG_FILE_NAME, self.property_mapping):
                                history.file_name = value
                            elif piid == PIID(DreameVacuumProperty.CLEAN_LOG_STATUS, self.property_mapping):
                                history.completed = bool(value)
                            elif piid == PIID(DreameVacuumProperty.WATER_TANK, self.property_mapping):
                                if value in DreameVacuumWaterTank._value2member_map_:
                                    history.water_tank = DreameVacuumWaterTank(
                                        value)
                                else:
                                    history.water_tank = DreameVacuumWaterTank.UNKNOWN

                        if history_size > 0 and cleaning_history[-1].date == history.date:
                            continue

                        cleaning_history.append(history)
                        history_size = history_size + 1
                        if history_size >= 20 or history_size >= total:
                            break

                    if self.status._cleaning_history != cleaning_history:                        
                        _LOGGER.debug("Cleaning History Changed")
                        self.status._cleaning_history = cleaning_history
                        if cleaning_history:
                            self.status._last_cleaning_time = cleaning_history[0].date.replace(tzinfo=datetime.now().astimezone().tzinfo)

                        if self._ready:
                            self._property_changed()
            except:
                _LOGGER.warning("Get Cleaning History failed!")

    def _property_changed(self) -> None:
        """Call external listener when a property changed"""
        if self._update_callback:
            _LOGGER.debug("Update Callback")
            self._update_callback()

    def _update_failed(self, ex) -> None:
        """Call external listener when update failed"""
        if self._error_callback:
            self._error_callback(ex)

    def _update_task(self) -> None:
        """Timer task for updating properties periodically"""
        self._update_timer = None
        
        try:
            self.update()
            self._update_fail_count = 0
        except Exception as ex:
            self._update_fail_count = self._update_fail_count + 1
            if self.available:
                self._last_update_failed = time.time()
                if self._update_fail_count <= 3:
                    _LOGGER.warning("Update failed, retrying %s: %s", self._update_fail_count, ex)
                else:
                    _LOGGER.debug("Update Failed: %s", ex)
                    self.available = False
                    self._update_failed(ex)
              
        self.schedule_update(self._update_interval)

    @staticmethod
    def split_group_value(value: int, mop_pad_lifting_available: bool = False) -> list[int]:
        if value is not None:
            value_list = []
            value_list.append((value & 3) if mop_pad_lifting_available else (value & 1))
            byte1 = value >> 8
            byte1 = byte1 & -769
            value_list.append(byte1)
            value_list.append(value >> 16)
            return value_list

    @staticmethod
    def combine_group_value(values: list[int]) -> int:
        if values and len(values) == 3:
            num = 0
            high = (num ^ values[2]) << 8
            mid = (high ^ values[1]) << 8
            low = mid ^ values[0]
            return low

    def connect_device(self) -> None:
        """Connect to the device api."""
        _LOGGER.info("Connecting to device")
        self.info = DreameVacuumDeviceInfo(self._protocol.connect())
        if self.mac is None:
            self.mac = self.info.mac_address
        _LOGGER.info("Connected to device: %s %s", self.info.model, self.info.firmware_version)
            
        self._last_settings_request = time.time()
        self._last_map_list_request = self._last_settings_request
        self._dirty_data = {}
        self._request_properties()
        self._last_update_failed = None

        if self.device_connected and self._protocol.cloud is not None and (not self._ready or not self.available):
            if self._map_manager:
                model = self.info.model.split('.')
                if len(model) == 3:
                    key = json.loads(zlib.decompress(base64.b64decode(DEVICE_MAP_KEY), zlib.MAX_WBITS | 32)).get(model[2])
                    if key:
                        self._map_manager.set_aes_iv(key)

                if not self.status.lidar_navigation:
                    self._map_manager.set_vslam_map()
                self._map_manager.set_update_interval(
                    self._map_update_interval)
                self._map_manager.set_device_running(self.status.running, self.status.docked and not self.status.started)

                if self.status.current_map is None:
                    self._map_manager.schedule_update(15)
                    self._map_manager.update()
                    self._last_map_request = self._last_settings_request
                    self._map_manager.schedule_update()
                else:
                    self.update_map()

            if self.cloud_connected:
                self._cleaning_history_update = -1
                self._request_cleaning_history()

                if self.status.ai_detection_available and not self.status.ai_policy_accepted:
                    prop = "prop.s_ai_config"
                    response = self._protocol.cloud.get_batch_device_datas([prop])
                    if response and prop in response and response[prop]:
                        try:
                            self.status.ai_policy_accepted = json.loads(
                                response[prop]).get("privacyAuthed")
                        except:
                            pass

        if not self.available:
            self.available = True
            if self._ready:
                self._property_changed()

        self._ready = True

    def connect_cloud(self) -> None:
        """Connect to the cloud api."""
        if self._protocol.cloud and not self._protocol.cloud.logged_in:
            self._protocol.cloud.login()            
            if self._protocol.cloud.logged_in is False:
                if self._protocol.cloud.two_factor_url:
                    self.two_factor_url = self._protocol.cloud.two_factor_url                    
                    self._property_changed()
                self._map_manager.schedule_update(-1)
                return
            elif self._protocol.cloud.logged_in:
                if self.two_factor_url:
                    self.two_factor_url = None
                    self._property_changed()

                if self._protocol.connected:
                    self._map_manager.schedule_update(5)
                self.token, self.host = self._protocol.cloud.get_info(
                    self.mac)
                self._protocol.set_credentials(
                    self.host, self.token, self.mac)

    def disconnect(self) -> None:
        """Disconnect from device and cancel timers"""
        _LOGGER.info("Disconnect")
        self.schedule_update(-1)
        self._protocol.disconnect()
        if self._map_manager:
            self._map_manager.schedule_update(-1)

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

    def schedule_update(self, wait: float = None) -> None:
        """Schedule a device update for future"""
        if not wait:
            wait = self._update_interval

        if self._update_timer is not None:
            self._update_timer.cancel()
            del self._update_timer
            self._update_timer = None

        if wait >= 0:
            self._update_timer = Timer(wait, self._update_task)
            self._update_timer.start()

    def get_property(self, prop: DreameVacuumProperty) -> Any:
        """Get a device property from memory"""
        if prop is not None and prop.value in self.data:
            return self.data[prop.value]
        return None

    def set_property(self, prop: DreameVacuumProperty, value: Any) -> bool:
        """Sets property value using the existing property mapping and notify listeners
        Property must be set on memory first and notify its listeners because device does not return new value immediately."""
        
        self.schedule_update(10)
        current_value = self._update_property(prop, value)
        if current_value is not None:
            self._last_change = time.time()
            self._last_settings_request = 0

            try:
                mapping = self.property_mapping[prop]
                result = self._protocol.set_property(mapping["siid"], mapping["piid"], value)

                if result and result[0]["code"] != 0:
                    _LOGGER.error(
                        "Property not updated: %s: %s -> %s", prop, current_value, value
                    )
                    self._update_property(prop, current_value)
                    if prop.value in self._dirty_data:
                        del self._dirty_data[prop.value]

                # Schedule the update for getting the updated property value from the device
                # If property is actually updated nothing will happen otherwise it will return to previous value and notify its listeners. (Post optimistic approach)
                self.schedule_update(2)
                return True
            except Exception as ex:
                self._update_property(prop, current_value)
                if prop.value in self._dirty_data:
                    del self._dirty_data[prop.value]
                self.schedule_update(1)
                raise DeviceUpdateFailedException(
                    "Set property failed %s: %s", prop.name, ex) from None

        self.schedule_update(1)
        return False

    def get_map_for_render(self, map_index: int) -> MapData | None:
        """Makes changes on map data for device related properties for renderer.
        Map manager does not need any device property for parsing and storing map data but map renderer does. 
        For example if device is running but not mopping renderer does not show no mopping areas and this function handles that so renderer does not need device data too."""

        map_data = self.get_map(map_index)
        if map_data:
            if map_data.need_optimization:
                map_data = self._map_manager.optimizer.optimize(map_data, self._map_manager.selected_map if map_data.saved_map_status == 2 else None)
                map_data.need_optimization = False
            
            map_data = copy.deepcopy(map_data)
            
            if map_data.optimized_pixel_type is not None:
                map_data.pixel_type = map_data.optimized_pixel_type
                map_data.dimensions = map_data.optimized_dimensions
                if map_data.optimized_charger_position is not None:
                    map_data.charger_position = map_data.optimized_charger_position

            if (
                self.status.started and not self.status.zone_cleaning
            ) or map_data.saved_map:
                # Map data always contains last active areas
                map_data.active_areas = None

            if (
                self.status.started and not self.status.spot_cleaning
            ) or map_data.saved_map:
                # Map data always contains last active areas
                map_data.active_points = None

            if not self.status.segment_cleaning or map_data.saved_map:
                # Map data always contains last active segments
                map_data.active_segments = None

            if not map_data.saved_map:
                if self.status.started and self.status.sweeping:
                    # App does not render no mopping areas when cleaning mode is sweeping
                    map_data.no_mopping_areas = None

                if (self.status.zone_cleaning and map_data.active_areas) or (self.status.spot_cleaning and map_data.active_points):
                    # App does not render segments when zone or spot cleaning
                    map_data.segments = None
            else:
                map_data.path = None

            if not self.status.customized_cleaning or map_data.saved_map:
                # App does not render customized cleaning settings on saved map list
                map_data.cleanset = None

            # Device currently may not be docked but map data can be old and still showing when robot is docked
            map_data.docked = bool(map_data.docked or self.status.docked)

            if not map_data.saved_map and not self.status.lidar_navigation and map_data.saved_map_status == 1 and map_data.docked:
                # For correct scaling of vslam saved map
                map_data.saved_map_status = 2

            if map_data.charger_position == None and map_data.docked and map_data.robot_position:
                map_data.charger_position = copy.deepcopy(map_data.robot_position)
                if self.status.robot_shape != 2:
                    map_data.charger_position.a = map_data.robot_position.a + 180

            if map_data.saved_map:
                # App does not render robot position on saved map list
                map_data.robot_position = None

                # App does not render restricted zones on saved map list
                map_data.walls = None
                map_data.no_go_areas = None
                map_data.no_mopping_areas = None                
                map_data.obstacles = None

            elif map_data.charger_position and map_data.docked:
                if not map_data.robot_position:
                    map_data.robot_position = copy.deepcopy(
                        map_data.charger_position)

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
        This function is used for requesting map data when a image request has been made to renderer"""

        if self._map_manager:
            now = time.time()
            if now - self._last_map_request > 120:
                self._last_map_request = now
                self._map_manager.set_update_interval(
                    self._map_update_interval)
                self._map_manager.schedule_update(0.01)

    def update(self) -> None:
        """Get properties from the device."""
        _LOGGER.debug("Device update: %s", self._update_interval)

        if self._update_running:
            return

        if not self.cloud_connected:
            self.connect_cloud()

        if not self.device_connected:
            self.connect_device()

        if not self.device_connected:
            raise DeviceUpdateFailedException("Device cannot be reached")

        self._update_running = True

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
            DreameVacuumProperty.NO_WATER_WARNING,
            #DreameVacuumProperty.SAVE_WATER_TIPS,
        ]

        now = time.time()
        if self.status.active:
            # Only changed when robot is active
            properties.extend(
                [DreameVacuumProperty.CLEANED_AREA,
                    DreameVacuumProperty.CLEANING_TIME]
            )

        if self._consumable_reset:
            # Consumable properties
            properties.extend(
                [
                    DreameVacuumProperty.MAIN_BRUSH_TIME_LEFT,
                    DreameVacuumProperty.MAIN_BRUSH_LEFT,
                    DreameVacuumProperty.SIDE_BRUSH_TIME_LEFT,
                    DreameVacuumProperty.SIDE_BRUSH_LEFT,
                    DreameVacuumProperty.FILTER_LEFT,
                    DreameVacuumProperty.FILTER_TIME_LEFT,
                    DreameVacuumProperty.SENSOR_DIRTY_LEFT,
                    DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
                    DreameVacuumProperty.MOP_PAD_LEFT,
                    DreameVacuumProperty.MOP_PAD_TIME_LEFT,
                ]
            )

        if now - self._last_settings_request > 9.5:
            self._last_settings_request = now

            # Read/Write properties
            properties.extend(
                [
                    DreameVacuumProperty.SUCTION_LEVEL,
                    DreameVacuumProperty.RESUME_CLEANING,
                    DreameVacuumProperty.CARPET_BOOST,
                    DreameVacuumProperty.MOP_CLEANING_REMAINDER,
                    DreameVacuumProperty.OBSTACLE_AVOIDANCE,
                    DreameVacuumProperty.AI_DETECTION,
                    DreameVacuumProperty.DRYING_TIME,
                    DreameVacuumProperty.AUTO_ADD_DETERGENT,
                    DreameVacuumProperty.CARPET_AVOIDANCE,
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
                    DreameVacuumProperty.DND,
                    DreameVacuumProperty.DND_START,
                    DreameVacuumProperty.DND_END,
                    DreameVacuumProperty.DND_TASK,
                    DreameVacuumProperty.MULTI_FLOOR_MAP,
                    DreameVacuumProperty.VOLUME,
                    DreameVacuumProperty.AUTO_DUST_COLLECTING,
                    DreameVacuumProperty.AUTO_EMPTY_FREQUENCY,
                    DreameVacuumProperty.VOICE_PACKET_ID,
                    DreameVacuumProperty.TIMEZONE,
                    DreameVacuumProperty.MAP_SAVING,
                    DreameVacuumProperty.AUTO_SWITCH_SETTINGS,
                    DreameVacuumProperty.QUICK_COMMAND,
                ]
            )

            if not self.status.self_wash_base_available:
                properties.append(DreameVacuumProperty.WATER_VOLUME)

        if self._map_manager and not self.status.running and now - self._last_map_list_request > 60:
            properties.extend([DreameVacuumProperty.MAP_LIST,
                              DreameVacuumProperty.RECOVERY_MAP_LIST])
            self._last_map_list_request = time.time()
            
        try:
            self._request_properties(properties)
        except Exception as ex:
            self._update_running = False
            raise DeviceUpdateFailedException(ex) from None

        if self._consumable_reset:
            self._consumable_reset = False

        if self._map_manager:
            self._map_manager.set_update_interval(self._map_update_interval)
            self._map_manager.set_device_running(self.status.running, self.status.docked and not self.status.started)

        if self.cloud_connected:            
            self._request_cleaning_history()

        self._update_running = False

    def call_action(self, action: DreameVacuumAction, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        """Call an action."""
        if action not in self.action_mapping:
            raise InvalidActionException(
                f"Unable to find {action} in the action mapping"
            )

        mapping = self.action_mapping[action]
        if "siid" not in mapping or "aiid" not in mapping:
            raise InvalidActionException(
                f"{action} is not an action (missing siid or aiid)"
            )

        if (
            action is not DreameVacuumAction.REQUEST_MAP
            and action is not DreameVacuumAction.UPDATE_MAP_DATA
        ):
            self.schedule_update(10)

        # Reset consumable on memory
        if action is DreameVacuumAction.RESET_MAIN_BRUSH:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.MAIN_BRUSH_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SIDE_BRUSH:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.SIDE_BRUSH_LEFT, 100)
        elif action is DreameVacuumAction.RESET_FILTER:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.FILTER_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SENSOR:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.SENSOR_DIRTY_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SECONDARY_FILTER:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.SECONDARY_FILTER_LEFT, 100)
        elif action is DreameVacuumAction.RESET_MOP_PAD:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.MOP_PAD_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SILVER_ION:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.SILVER_ION_LEFT, 100)
        elif action is DreameVacuumAction.RESET_DETERGENT:
            self._consumable_reset = True
            self._update_property(DreameVacuumProperty.DETERGENT_LEFT, 100)

        # Update listeners
        if (
            action is DreameVacuumAction.START or
            action is DreameVacuumAction.START_CUSTOM or
            action is DreameVacuumAction.STOP or
            action is DreameVacuumAction.CHARGE or
            action is DreameVacuumAction.UPDATE_MAP_DATA or
            self._consumable_reset
        ):
            self._property_changed()
            
        try:
            result = self._protocol.action(
                mapping["siid"], mapping["aiid"], parameters)
            if result and result.get("code") != 0:
                result = None
        except Exception as ex:
            _LOGGER.error("Send action failed %s: %s", action.name, ex)
            self.schedule_update(1)
            return

        if result:
            _LOGGER.info("Send action %s", action.name)
            self._last_change = time.time()
            if (
                action is not DreameVacuumAction.REQUEST_MAP
                and action is not DreameVacuumAction.UPDATE_MAP_DATA
            ):
                self._last_settings_request = 0

        # Schedule update for retrieving new properties after action sent
        self.schedule_update(3)
        return result

    def send_command(self, command: str, parameters: dict[str, Any]) -> dict[str, Any] | None:
        """Send a raw command to the device. This is mostly useful when trying out
        commands which are not implemented by a given device instance. (Not likely)"""

        if command == "" or parameters is None:
            raise InvalidActionException("Invalid Command: (%s).", command)

        self.schedule_update(10)
        self._protocol.send(command, parameters, 1)
        self.schedule_update(2)

    def set_suction_level(self, suction_level: int) -> bool:
        """Set suction level."""
        if self.status.started and (self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning)):
            raise InvalidActionException(
                "Cannot set suction level when customized cleaning is enabled"
            )
        return self.set_property(DreameVacuumProperty.SUCTION_LEVEL, int(suction_level))

    def set_cleaning_mode(self, cleaning_mode: int) -> bool:
        """Set cleaning mode."""
        if self.status.started:
            raise InvalidActionException(
                "Cannot set cleaning mode while vacuum is running"
            )

        if not self.status.auto_mount:
            if cleaning_mode is DreameVacuumCleaningMode.SWEEPING.value:
                if self.status.water_tank_or_mop_installed and not self.status.mop_pad_lifting_available:
                    if self.status.self_wash_base_available:
                        raise InvalidActionException(
                            "Cannot set sweeping while mop pads are installed"
                        )
                    else:
                        raise InvalidActionException(
                            "Cannot set sweeping while water tank is installed"
                        )
            elif not self.status.water_tank_or_mop_installed:
                if self.status.self_wash_base_available:
                    raise InvalidActionException(
                        "Cannot set mopping while mop pads are not installed"
                    )
                else:
                    raise InvalidActionException(
                        "Cannot set mopping while water tank is not installed"
                    )

        if self.status.self_wash_base_available:
            values = DreameVacuumDevice.split_group_value(self.get_property(DreameVacuumProperty.CLEANING_MODE), self.status.mop_pad_lifting_available)
            if values and len(values) == 3:
                if self.status.mop_pad_lifting_available:
                    if cleaning_mode == 2:
                        values[0] = 0
                    elif cleaning_mode == 0:
                        values[0] = 2
                    else:
                        values[0] = cleaning_mode
                elif cleaning_mode == 2:
                    values[0] = 0
                    
                cleaning_mode = DreameVacuumDevice.combine_group_value(values)
        elif self.status.mop_pad_lifting_available:
            if cleaning_mode == 2:
                cleaning_mode = 0
            elif cleaning_mode == 0:
                cleaning_mode = 2

        return self.set_property(DreameVacuumProperty.CLEANING_MODE, int(cleaning_mode))

    def set_mop_pad_humidity(self, mop_pad_humidity: int) -> bool:
        """Set mop pad humidity."""
        if self.status.self_wash_base_available:
            if self.status.started and (self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning)):
                raise InvalidActionException(
                    "Cannot set mop pad humidity when customized cleaning is enabled"
                )

            values = DreameVacuumDevice.split_group_value(self.get_property(DreameVacuumProperty.CLEANING_MODE), self.status.mop_pad_lifting_available)
            if values and len(values) == 3:
                values[2] = mop_pad_humidity
                return self.set_property(DreameVacuumProperty.CLEANING_MODE, DreameVacuumDevice.combine_group_value(values))

    def set_water_volume(self, water_volume: int) -> bool:
        """Set water volume."""
        if not self.status.self_wash_base_available:
            if self.status.started and (self.status.customized_cleaning and not (self.status.zone_cleaning or self.status.spot_cleaning)):
                raise InvalidActionException(
                    "Cannot set water volume when customized cleaning is enabled"
                )

            return self.set_property(DreameVacuumProperty.WATER_VOLUME, int(water_volume))

    def set_dnd_enabled(self, dnd_enabled: bool) -> bool:
        """Set do not disturb function"""
        return self.set_property(DreameVacuumProperty.DND, bool(dnd_enabled))

    def set_dnd_start(self, dnd_start: str) -> bool:
        """Set do not disturb function"""
        time_pattern = re.compile("([0-1][0-9]|2[0-3]):[0-5][0-9]$")
        if not re.match(time_pattern, dnd_start):
            raise InvalidValueException(
                "DND start time is not valid: (%s).", dnd_start)
        return self.set_property(DreameVacuumProperty.DND_START, dnd_start)

    def set_dnd_end(self, dnd_end: str) -> bool:
        """Set do not disturb function"""
        time_pattern = re.compile("([0-1][0-9]|2[0-3]):[0-5][0-9]$")
        if not re.match(time_pattern, dnd_end):
            raise InvalidValueException(
                "DND end time is not valid: (%s).", dnd_end)
        return self.set_property(DreameVacuumProperty.DND_END, dnd_end)

    def set_self_clean_area(self, self_clean_area: int) -> bool:
        """Set self clean area."""
        if self.status.self_wash_base_available:
            values = DreameVacuumDevice.split_group_value(self.get_property(DreameVacuumProperty.CLEANING_MODE), self.status.mop_pad_lifting_available)
            if values and len(values) == 3:
                values[1] = self_clean_area
                return self.set_property(DreameVacuumProperty.CLEANING_MODE, DreameVacuumDevice.combine_group_value(values))

    def locate(self) -> dict[str, Any] | None:
        """Locate the vacuum cleaner."""
        return self.call_action(DreameVacuumAction.LOCATE)

    def start(self) -> dict[str, Any] | None:
        """Start or resume the cleaning task."""            
        self.schedule_update(10)

        if self.status.fast_mapping_paused:
            return self.start_custom(DreameVacuumStatus.FAST_MAPPING.value)

        if not self.status.started:
            self._update_status(DreameVacuumTaskStatus.AUTO_CLEANING, DreameVacuumStatus.CLEANING)

        if self._map_manager:
            self._map_manager.editor.refresh_map()
        return self.call_action(DreameVacuumAction.START)

    def start_custom(self, status, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        """Start custom cleaning task."""
        if status != DreameVacuumStatus.FAST_MAPPING.value and self.status.fast_mapping:
            raise InvalidActionException(
                "Cannot start cleaning while fast mapping")

        payload = [{"piid": PIID(
            DreameVacuumProperty.STATUS, self.property_mapping), "value": status}]
        
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
        self.schedule_update(10)

        if self.status.fast_mapping:
            return self.return_to_base()
                
        if self.status.started:
            # Clear active segments on current map data
            if self._map_manager:
                self._map_manager.editor.set_active_segments([])

            self._update_status(DreameVacuumTaskStatus.COMPLETED, DreameVacuumStatus.STANDBY)
        return self.call_action(DreameVacuumAction.STOP)

    def pause(self) -> dict[str, Any] | None:
        """Pause the cleaning task."""
        if not self.status.paused and self.status.started:
            self._update_property(
                DreameVacuumProperty.STATE, DreameVacuumState.PAUSED.value
            )

        return self.call_action(DreameVacuumAction.PAUSE)

    def return_to_base(self) -> dict[str, Any] | None:
        """Set the vacuum cleaner to return to the dock."""
        if self.status.started:
            self._update_property(
                DreameVacuumProperty.STATE, DreameVacuumState.RETURNING.value
            )

            # Clear active segments on current map data
            #if self._map_manager:
            #    self._map_manager.editor.set_active_segments([])
        if self._map_manager:
            self._map_manager.editor.refresh_map()
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

    def clean_zone(self, zones: list[int] | list[list[int]], cleaning_times: int) -> dict[str, Any] | None:
        """Clean selected area."""
        self.schedule_update(10)
        if zones and not isinstance(zones[0], list):
            zones = [zones]

        suction_level = self.status.suction_level.value
        if self.status.self_wash_base_available:
            water_volume = self.status.mop_pad_humidity.value
        else:
            water_volume = self.status.water_volume.value

        cleanlist = []
        for zone in zones:
            cleanlist.append(
                [
                    int(round(zone[0])),
                    int(round(zone[1])),
                    int(round(zone[2])),
                    int(round(zone[3])),
                    cleaning_times,
                    suction_level,
                    water_volume,
                ]
            )

        if not self.status.started or self.status.paused:
            if self._map_manager:
                # Set active areas on current map data is implemented on the app
                self._map_manager.editor.set_active_areas(zones)

            self._update_status(DreameVacuumTaskStatus.ZONE_CLEANING, DreameVacuumStatus.ZONE_CLEANING)

        return self.start_custom(
            DreameVacuumStatus.ZONE_CLEANING.value,
            str(json.dumps({"areas": cleanlist}, separators=(",", ":"))).replace(
                " ", ""
            ),
        )

    def clean_segment(self, selected_segments: int | list[int], cleaning_times: int | list[int], suction_level: int | list[int], water_volume: int | list[int]) -> dict[str, Any] | None:
        """Clean selected segment using id."""
        self.schedule_update(10)
        if not isinstance(selected_segments, list):
            selected_segments = [selected_segments]

        if not suction_level or suction_level == "":
            suction_level = self.status.suction_level.value

        if not water_volume or water_volume == "":
            if self.status.self_wash_base_available:
                water_volume = self.status.mop_pad_humidity.value
            else:
                water_volume = self.status.water_volume.value

        cleanlist = []
        index = 0
        segments = self.status.segments
        custom_order = self.get_property(DreameVacuumProperty.CLEANING_MODE) is not None and self.status.custom_order

        for segment_id in selected_segments:
            if not cleaning_times:
                if (
                    segments and segment_id in segments and self.status.customized_cleaning
                ):
                    repeat = segments[segment_id].cleaning_times
                else:
                    repeat = 1
            elif isinstance(cleaning_times, list):
                repeat = cleaning_times[index]
            else:
                repeat = cleaning_times

            if not suction_level:
                if (
                    segments and segment_id in segments and self.status.customized_cleaning
                ):
                    fan = segments[segment_id].suction_level
                else:
                    fan = 1
            elif isinstance(suction_level, list):
                fan = suction_level[index]
            else:
                fan = suction_level

            if not water_volume:
                if (
                    segments and segment_id in segments and self.status.customized_cleaning
                ):
                    water = segments[segment_id].water_volume
                else:
                    water = 1
            elif isinstance(water_volume, list):
                water = water_volume[index]
            else:
                water = water_volume
                
            cleanlist.append(
                [segment_id, repeat, fan, water,
                    1 if custom_order else (index + 1)]
            )
            index = index + 1

        if not self.status.started or self.status.paused:
            if self._map_manager:
                # Set active segments on current map data is implemented on the app
                self._map_manager.editor.set_active_segments(selected_segments)
                
            self._update_status(DreameVacuumTaskStatus.SEGMENT_CLEANING, DreameVacuumStatus.SEGMENT_CLEANING)
                
        return self.start_custom(
            DreameVacuumStatus.SEGMENT_CLEANING.value,
            str(json.dumps({"selects": cleanlist}, separators=(",", ":"))).replace(
                " ", ""
            ),
        )

    def clean_spot(self, points: list[int] | list[list[int]], cleaning_times: int | list[int], suction_level: int | list[int], water_volume: int | list[int]) -> dict[str, Any] | None:
        self.schedule_update(10)
        if points and not isinstance(points[0], list):
            points = [points]
            
        suction_level = self.status.suction_level.value
        if self.status.self_wash_base_available:
            water_volume = self.status.mop_pad_humidity.value
        else:
            water_volume = self.status.water_volume.value

        cleanlist = []
        for point in points:
            cleanlist.append(
                [
                    int(round(point[0])),
                    int(round(point[1])),
                    cleaning_times,
                    suction_level,
                    water_volume,
                ]
            )

        if not self.status.started or self.status.paused:
            if self._map_manager:
                # Set active points on current map data is implemented on the app
                self._map_manager.editor.set_active_points(points)

            self._update_status(DreameVacuumTaskStatus.SPOT_CLEANING, DreameVacuumStatus.SPOT_CLEANING)

        return self.start_custom(
            DreameVacuumStatus.SPOT_CLEANING.value,
            str(json.dumps({"points": cleanlist}, separators=(",", ":"))).replace(
                " ", ""
            ),
        )

    def start_fast_mapping(self) -> dict[str, Any] | None:
        """Fast map."""
        self.schedule_update(10)
        if self.status.fast_mapping:
            return

        if self.status.battery_level < 15:
            raise InvalidActionException(
                "Low battery capacity. Please start the robot for working after it being fully charged."
            )

        if not self.status.self_wash_base_available and self.status.water_tank_or_mop_installed and not self.status.mop_pad_lifting_available:
            raise InvalidActionException(
                "Please make sure the mop pad is not installed before fast mapping."
            )

        self._update_status(DreameVacuumTaskStatus.FAST_MAPPING, DreameVacuumStatus.FAST_MAPPING)

        if self._map_manager:
            self._map_manager.editor.refresh_map()

        return self.start_custom(DreameVacuumStatus.FAST_MAPPING.value)

    def start_mapping(self) -> dict[str, Any] | None:
        """Create a new map by cleaning whole floor."""
        self.schedule_update(10)
        if self._map_manager:
            self._map_manager.editor.reset_map()
            self._update_status(DreameVacuumTaskStatus.AUTO_CLEANING, DreameVacuumStatus.CLEANING)

        return self.start_custom(DreameVacuumStatus.CLEANING.value, "3")

    def start_self_wash_base(self, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        """Start self-wash base for cleaning or drying the mop."""
        if not self.status.self_wash_base_available:
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

    def start_washing(self) -> dict[str, Any] | None:
        """Start washing the mop if self-wash base is present."""
        if self.status.washing_paused:
            if self.info and self.info.version <= 1037:
                return self.start()
            return self.start_self_wash_base("1,1")
        if self.status.washing_available or self.status.returning_to_wash_paused:
            return self.start_self_wash_base("2,1")

    def pause_washing(self) -> dict[str, Any] | None:
        """Pause washing the mop if self-wash base is present."""
        if self.status.washing:
            if self.info and self.info.version <= 1037:
                return self.pause()
            return self.start_self_wash_base("1,0")

    def start_drying(self) -> dict[str, Any] | None:
        """Start drying the mop if self-wash base is present."""
        if self.status.drying_available and not self.status.drying:
            return self.start_self_wash_base("3,1")

    def stop_drying(self) -> dict[str, Any] | None:
        """Stop drying the mop if self-wash base is present."""
        if self.status.drying_available and self.status.drying:
            return self.start_self_wash_base("3,0")

    def clear_warning(self) -> dict[str, Any] | None:
        """Clear warning error code from the vacuum cleaner."""
        if self.status.has_warning:
            return self.call_action(
                DreameVacuumAction.CLEAR_WARNING,
                [{"piid": PIID(DreameVacuumProperty.CLEANING_PROPERTIES,
                               self.property_mapping), "value": f"[{self.status.error.value}]"}],
            )

    def remote_control_move_step(
        self, rotation: int = 0, velocity: int = 0
    ) -> dict[str, Any] | None:
        """Send remote control command to device."""
        if self.status.fast_mapping:
            raise InvalidActionException(
                "Cannot remote control vacuum while fast mapping"
            )

        if self.status.washing:
            raise InvalidActionException(
                "Cannot remote control vacuum while self-wash base is running"
            )

        payload = (
            '{"spdv":%(velocity)d,"spdw":%(rotation)d,"audio":"%(audio)s","random":%(random)d}'
            % {
                "velocity": velocity,
                "rotation": rotation,
                "audio": "false" if self._remote_control or self.status.status is DreameVacuumStatus.SLEEPING else "true",
                "random": randrange(65535),
            }
        )
        self._remote_control = True
        mapping = self.property_mapping[DreameVacuumProperty.REMOTE_CONTROL]
        return self._protocol.set_property(mapping["siid"], mapping["piid"], payload, 0)

    def install_voice_pack(self, lang_id: int, url: str, md5: str, size: int) -> dict[str, Any] | None:
        """install a custom language pack"""
        payload = (
            '{"id":"%(lang_id)s","url":"%(url)s","md5":"%(md5)s","size":%(size)d}'
            % {"lang_id": lang_id, "url": url, "md5": md5, "size": size}
        )
        mapping = self.property_mapping[DreameVacuumProperty.VOICE_CHANGE]
        return self._protocol.set_property(mapping["siid"], mapping["piid"], payload, 1)

    def set_ai_detection(self, settings: dict[str, bool] | int) -> dict[str, Any] | None:
        """Send ai detection parameters to the device."""
        if self.status.ai_detection_available:
            self._property_changed()

            if (
                (self.status.ai_obstacle_detection or self.status.obstacle_image_upload) 
                and (self._protocol.cloud and not self.status.ai_policy_accepted)
            ):
                prop = "prop.s_ai_config"
                response = self._protocol.cloud.get_batch_device_datas([prop])
                if response and prop in response and response[prop]:
                    try:
                        self.status.ai_policy_accepted = json.loads(
                            response[prop]).get("privacyAuthed")
                    except:
                        pass

                if not self.status.ai_policy_accepted:
                    if self.status.ai_obstacle_detection:
                        self.status.ai_obstacle_detection = False

                    if self.status.obstacle_image_upload:
                        self.status.obstacle_image_upload = False

                    self._property_changed()

                    raise InvalidActionException(
                        "You need to accept privacy policy from the App before enabling AI obstacle detection feature"
                    )

            mapping = self.property_mapping[DreameVacuumProperty.AI_DETECTION]
            if isinstance(settings, int):
                return self._protocol.set_property(mapping["siid"], mapping["piid"], settings, 1)
            return self._protocol.set_property(mapping["siid"], mapping["piid"], str(json.dumps(settings, separators=(",", ":"))).replace(" ", ""), 1)

    def set_ai_obstacle_detection(self, enabled: bool) -> dict[str, Any] | None:
        """Enable or disable AI detection feature."""
        if self.status.ai_detection_available:
            current_value = self.status.ai_obstacle_detection
            self.status.ai_obstacle_detection = bool(enabled)
            value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(value, int):
                value = (value | 2) if self.status.ai_obstacle_detection else (value & -3)
                result = self.set_ai_detection(value)
            else:
                result = self.set_ai_detection(
                    {AI_SETTING_SWITCH: self.status.ai_obstacle_detection})
            if result and result[0]["code"] != 0:
                self.status.ai_obstacle_detection = current_value
                self._property_changed()
            return result

    def set_obstacle_image_upload(self, enabled: bool) -> dict[str, Any] | None:
        """Enable or disable obstacle picture uploading to the cloud."""
        if self.status.ai_detection_available:
            current_value = self.status.obstacle_image_upload
            self.status.obstacle_image_upload = bool(enabled)
            value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(value, int):
                value = (value | 32) if self.status.obstacle_image_upload else (value & -33)
                result = self.set_ai_detection(value)
            else:
                result = self.set_ai_detection(
                    {AI_SETTING_UPLOAD: self.status.obstacle_image_upload})
            if result and result[0]["code"] != 0:
                self.status.obstacle_image_upload = current_value
                self._property_changed()
            return result

    def set_pet_detection(self, enabled: bool) -> dict[str, Any] | None:
        """Enable or disable AI pet detection feature."""
        if self.status.ai_detection_available:
            current_value = self.status.pet_detection
            self.status.pet_detection = bool(enabled)
            value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(value, int):
                value = (value | 16) if self.status.pet_detection else (value & -17)
                result = self.set_ai_detection(value)
            else:
                result = self.set_ai_detection(
                    {AI_SETTING_PET: self.status.pet_detection})
            if result and result[0]["code"] != 0:
                self.status.pet_detection = current_value
                self._property_changed()
            return result

    def set_human_detection(self, enabled: bool) -> dict[str, Any] | None:
        """Enable or disable AI human detection feature."""
        if self.status.ai_detection_available:
            current_value = self.status.human_detection
            self.status.human_detection = bool(enabled)
            value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(value, int):
                return None
            else:
                result = self.set_ai_detection(
                    {AI_SETTING_HUMAN: self.status.human_detection})
            if result and result[0]["code"] != 0:
                self.status.human_detection = current_value
                self._property_changed()
            return result

    def set_furniture_detection(self, enabled: bool) -> dict[str, Any] | None:
        """Enable or disable AI furnitue detection feature."""
        if self.status.ai_detection_available:
            current_value = self.status.furniture_detection
            self.status.furniture_detection = bool(enabled)
            value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(value, int):
                value = (value | 1) if self.status.furniture_detection else (value & -2)
                result = self.set_ai_detection(value)
            else:
                result = self.set_ai_detection(
                    {AI_SETTING_FURNITURE: self.status.furniture_detection})
            if result and result[0]["code"] != 0:
                self.status.furniture_detection = current_value
                self._property_changed()
            return result

    def set_fluid_detection(self, enabled: bool) -> dict[str, Any] | None:
        """Enable or disable AI fluid detection feature."""
        if self.status.ai_detection_available:
            current_value = self.status.fluid_detection
            self.status.fluid_detection = bool(enabled)
            value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(value, int):
                value = (value | 8) if self.status.fluid_detection else (value & -9)
                result = self.set_ai_detection(value)
            else:
                result = self.set_ai_detection(
                    {AI_SETTING_FLUID: self.status.fluid_detection})
            if result and result[0]["code"] != 0:
                self.status.fluid_detection = current_value
                self._property_changed()
            return result

    def set_obstacle_picture(self, enabled: bool) -> dict[str, Any] | None:
        """Enable or disable AI obstacle picture display feature."""
        if self.status.ai_detection_available:
            current_value = self.status.obstacle_picture
            self.status.obstacle_picture = bool(enabled)
            value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(value, int):
                value = (value | 4) if self.status.obstacle_picture else (value & -5)
                result = self.set_ai_detection(value)
            else:
                result = self.set_ai_detection(
                    {AI_SETTING_FLUID: self.status.obstacle_picture})
            if result and result[0]["code"] != 0:
                self.status.obstacle_picture = current_value
                self._property_changed()
            return result

    def set_auto_switch_settings(self, settings) -> dict[str, Any] | None:
        if self.status.ai_detection_available:
            self._property_changed()

            mapping = self.property_mapping[DreameVacuumProperty.AUTO_SWITCH_SETTINGS]
            return self._protocol.set_property(mapping["siid"], mapping["piid"], str(json.dumps(settings, separators=(",", ":"))).replace(" ", ""), 1)

    def set_fill_light(self, enabled: bool) -> dict[str, Any] | None:
        if self.status.auto_switch_settings_available:
            current_value = self.status.fill_light
            self.status.fill_light = 1 if enabled else 0
            result = self.set_auto_switch_settings({"k": "FillinLight", "v": self.status.fill_light})
            if result and result[0]["code"] != 0:
                self.status.fill_light = current_value
                self._property_changed()
            return result

    def set_collision_avoidance(self, enabled: bool) -> dict[str, Any] | None:
        if self.status.auto_switch_settings_available:
            current_value = self.status.collision_avoidance
            self.status.collision_avoidance = 1 if enabled else 0
            result = self.set_auto_switch_settings({"k": "LessColl", "v": self.status.collision_avoidance})
            if result and result[0]["code"] != 0:
                self.status.collision_avoidance = current_value
                self._property_changed()
            return result

    def set_auto_drying(self, enabled: bool) -> dict[str, Any] | None:
        if self.status.auto_switch_settings_available:
            current_value = self.status.auto_drying
            self.status.auto_drying = 1 if enabled else 0
            result = self.set_auto_switch_settings({"k": "AutoDry", "v": self.status.auto_drying})
            if result and result[0]["code"] != 0:
                self.status.auto_drying = current_value
                self._property_changed()
            return result
        else:
            current_value = self.status.auto_drying
            self.status.auto_drying = 1 if enabled else 0
            if not self.set_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION, self.status.auto_drying):
                self.status.auto_drying = current_value
                self._property_changed()
                return False
            return True

    def set_stain_avoidance(self, stain_avoidance: int) -> dict[str, Any] | None:
        if self.status.auto_switch_settings_available:
            current_value = self.status.stain_avoidance
            self.status.stain_avoidance = stain_avoidance
            result = self.set_auto_switch_settings({"k": "StainIdentify", "v": self.status.stain_avoidance})
            if result and result[0]["code"] != 0:
                self.status.stain_avoidance = current_value
                self._property_changed()
            return result
        
    def set_mopping_type(self, mopping_type: int) -> dict[str, Any] | None:
        if self.status.auto_switch_settings_available:
            current_value = self.status.mopping_type
            self.status.mopping_type = mopping_type
            result = self.set_auto_switch_settings({"k": "CleanType", "v": self.status.mopping_type})
            if result and result[0]["code"] != 0:
                self.status.mopping_type = current_value
                self._property_changed()
            return result

    def set_multi_map(self, enabled: bool) -> bool:
        if self.set_property(DreameVacuumProperty.MULTI_FLOOR_MAP, int(enabled)):
            if self.status.auto_switch_settings_available and not enabled and self.get_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION) == 1:
                self.set_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION, 0)
            return True
        return False

    def request_map(self) -> dict[str, Any] | None:
        """Send map request action to the device. 
        Device will upload a new map on cloud after this command if it has a saved map on memory. 
        Otherwise this action will timeout when device is spot cleaning or a restored map exists on memory."""

        if self._map_manager:
            return self._map_manager.request_new_map()
        return self.call_action(
            DreameVacuumAction.REQUEST_MAP, [{"piid": PIID(
                DreameVacuumProperty.FRAME_INFO, self.property_mapping), "value": '{"frame_type":"I"}'}]
        )

    def update_map_data(self, parameters: dict[str, Any]) -> dict[str, Any] | None:
        """Send update map action to the device."""
        if self._map_manager:
            self._map_manager.schedule_update(10)
            self._property_changed()
            self._last_map_request = time.time()
            
        response = self.call_action(
            DreameVacuumAction.UPDATE_MAP_DATA,
            [
                {
                    "piid": PIID(DreameVacuumProperty.MAP_EXTEND_DATA, self.property_mapping),
                    "value": str(json.dumps(parameters, separators=(",", ":"))).replace(
                        " ", ""
                    ),
                }
            ],
        )

        self.schedule_update(5)

        if self._map_manager:
            self._map_manager.request_next_map()
            self._last_map_list_request = 0            

        return response

    def rename_map(self, map_id: int, map_name: str = "") -> dict[str, Any] | None:
        """Set custom name for a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot rename a map when temporary map is present"
            )

        if map_name != "":
            map_name = map_name.replace(" ", "-")
            if self._map_manager:
                self._map_manager.editor.set_map_name(map_id, map_name)
            return self.update_map_data({"nrism": {map_id: {"name": map_name}}})

    def set_map_rotation(self, map_id: int, rotation: int) -> dict[str, Any] | None:
        """Set rotation of a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot rotate a map when temporary map is present"
            )

        if rotation is not None:
            rotation = int(rotation)
            if rotation > 270 or rotation < 0:
                rotation = 0

            if self._map_manager:
                self._map_manager.editor.set_rotation(map_id, rotation)
            return self.update_map_data({"smra": {map_id: {"ra": rotation}}})

    def set_restricted_zone(self, walls=[], zones=[], no_mops=[]) -> dict[str, Any] | None:
        """Set restricted zones on current map."""
        if self._map_manager:
            self._map_manager.editor.set_zones(walls, zones, no_mops)
        return self.update_map_data({"vw": {"line": walls, "rect": zones, "mop": no_mops}})

    def select_map(self, map_id: int) -> dict[str, Any] | None:
        """Change currently selected map when multi floor map is enabled."""
        if self.status.multi_map:
            if self._map_manager:
                self._map_manager.editor.select_map(map_id)
            return self.update_map_data({"sm": {}, "mapid": map_id})

    def delete_map(self, map_id: int = None) -> dict[str, Any] | None:
        """Delete a map."""
        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot delete a map when temporary map is present"
            )

        if self.status.started:
            raise InvalidActionException(
                "Cannot delete a map while vacuum is running")

        if self._map_manager:
            if map_id == 0:
                map_id = None

            # Device do not deletes saved maps when you disable multi floor map feature
            # but it deletes all maps if you delete any map when multi floor map is disabled.
            if self.status.multi_map:
                if not map_id and self._map_manager.selected_map:
                    map_id = self._map_manager.selected_map.map_id
            else:
                if (
                    (self._map_manager.selected_map and map_id == self._map_manager.selected_map.map_id)
                ):
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
                raise InvalidActionException(
                    "Cannot replace a map when multi floor map is disabled"
                )

            if self._map_manager:
                self._map_manager.editor.replace_temporary_map(map_id)
            parameters = {"cw": 1}
            if map_id:
                parameters["mapid"] = map_id
            return self.update_map_data(parameters)

    def restore_map(self, map_id: int, map_url: str) -> dict[str, Any] | None:
        """Replace a map with previously saved version by device."""

        if not self.status.has_temporary_map:
            if self._map_manager:
                self._map_manager.editor.restore_map(map_id, map_url)
                self._last_map_request = time.time()
                self._map_manager.schedule_update(10)

            mapping = self.property_mapping[DreameVacuumProperty.MAP_RECOVERY]
            response = self._protocol.set_property(mapping["siid"], mapping["piid"], str(
                json.dumps({"map_id": map_id, "map_url": map_url}, separators=(",", ":"))).replace(" ", ""), 1)

            if self._map_manager:
                self._map_manager.request_next_map()
            return response

    def merge_segments(self, map_id: int, segments: list[int]) -> dict[str, Any] | None:
        """Merge segments on a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot edit segments when temporary map is present"
            )
                
        if segments:
            if map_id == "":
                map_id = None

            if self._map_manager:
                if not map_id:
                    if self.status.lidar_navigation and self._map_manager.selected_map:
                        map_id = self._map_manager.selected_map.map_id
                    else:
                        map_id = 0
                self._map_manager.editor.merge_segments(map_id, segments)

            if not map_id and self.status.lidar_navigation:
                raise InvalidActionException(
                    "Map ID is required"
                )

            data = { "msr": [segments[0], segments[1]] }
            if map_id:
                data["mapid"] = map_id
            return self.update_map_data(data)

    def split_segments(self, map_id: int, segment: int, line: list[int]) -> dict[str, Any] | None:
        """Split segments on a map"""
        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot edit segments when temporary map is present"
            )

        if segment and line is not None:
            if map_id == "":
                map_id = None

            if self._map_manager:
                if not map_id:
                    if self.status.lidar_navigation and self._map_manager.selected_map:
                        map_id = self._map_manager.selected_map.map_id
                    else:
                        map_id = 0
                self._map_manager.editor.split_segments(map_id, segment, line)

            if not map_id and self.status.lidar_navigation:
                raise InvalidActionException(
                    "Map ID is required"
                )

            line.append(segment)
            data = { "dsrid": line }
            if map_id:
                data["mapid"] = map_id
            return self.update_map_data(data)

    def set_cleaning_sequence(self, cleaning_sequence: list[int]) -> dict[str, Any] | None:
        """Set cleaning sequence on current map. 
        Device will use this order even you specify order in segment cleaning."""

        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot edit segments when temporary map is present"
            )

        if self.status.started:
            raise InvalidActionException(
                "Cannot set cleaning sequence while vacuum is running"
            )
        
        if cleaning_sequence == "" or not cleaning_sequence:
            cleaning_sequence = []
            
        if self._map_manager:
            if cleaning_sequence and self.status.segments and len(cleaning_sequence) != len(self.status.segments.items()):
                raise InvalidValueException("Invalid size for cleaning sequence")
                
            cleaning_sequence = self._map_manager.editor.set_cleaning_sequence(cleaning_sequence)

        return self.update_map_data({"cleanOrder": cleaning_sequence})

    def set_cleanset(self, cleanset: dict[str, list[int]]) -> dict[str, Any] | None:
        """Set customized cleaning settings on current map. 
        Device will use these settings even you pass another setting for custom segment cleaning."""

        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot edit segments when temporary map is present"
            )

        if cleanset is not None:
            return self.update_map_data({"customeClean": cleanset})

    def set_custom_cleaning(self, segment_id: list[int], suction_level: list[int], water_volume: list[int], cleaning_times: list[int]) -> dict[str, Any] | None:
        """Set customized cleaning settings on current map. 
        Device will use these settings even you pass another setting for custom segment cleaning."""

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
            segments = self.status.segments
            if segments:
                count = len(segments.items())
                if (
                    len(segment_id) != count
                    or len(suction_level) != count
                    or len(water_volume) != count
                    or len(cleaning_times) != cleaning_times
                ):
                    return

            custom_cleaning = []
            index = 0
            for segment in segment_id:
                custom_cleaning.append(
                    # for some reason cleanset uses different int values for water volume
                    [segment, suction_level[index], water_volume[index] + 1, cleaning_times[index]]
                )
                index = index + 1

            return self.set_cleanset(custom_cleaning)

    def set_segment_name(self, segment_id: int, segment_type: int, custom_name: str = None) -> dict[str, Any] | None:
        """Update name of a segment on current map"""
        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot edit segment when temporary map is present"
            )

        if self._map_manager:
            segment_info = self._map_manager.editor.set_segment_name(
                segment_id, segment_type, custom_name
            )
            if segment_info:
                return self.update_map_data({"nsr": segment_info})

    def set_segment_order(self, segment_id: int, order: int) -> dict[str, Any] | None:
        """Update cleaning order of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            return self.update_map_data({"cleanOrder": self._map_manager.editor.set_segment_order(segment_id, order)})

    def set_segment_suction_level(self, segment_id: int, suction_level: int) -> dict[str, Any] | None:
        """Update suction level of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_suction_level(
                    segment_id, suction_level)
            )

    def set_segment_water_volume(self, segment_id: int, water_volume: int) -> dict[str, Any] | None:
        """Update water volume of a segment on current map"""
        if not self.status.self_wash_base_available and self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_water_volume(
                    segment_id, water_volume)
            )

    def set_segment_mop_pad_humidity(self, segment_id: int, mop_pad_humidity: int) -> dict[str, Any] | None:
        """Update mop pad humidity of a segment on current map"""
        if self.status.self_wash_base_available and self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_water_volume(
                    segment_id, mop_pad_humidity)
            )

    def set_segment_cleaning_times(self, segment_id: int, cleaning_times: int) -> dict[str, Any] | None:
        """Update cleaning times of a segment on current map."""
        if self.status.started:
            raise InvalidActionException(
                "Cannot set room cleaning times while vacuum is running"
            )

        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_cleaning_times(
                    segment_id, cleaning_times)
            )

    @property
    def _update_interval(self) -> float:
        """Dynamic update interval of the device for the timer."""
        now = time.time()
        if self._last_update_failed:
            return 5 if now - self._last_update_failed <= 60 else 10 if now - self._last_update_failed <= 300 else 30
        if not - self._last_change <= 60:
            return 3 if self.status.active else 5
        if self.status.active or self.status.started:
            return 3 if self.status.running else 5
        if self._map_manager:
            return min(self._map_update_interval, 10)
        return 10

    @property
    def _map_update_interval(self) -> float:
        """Dynamic map update interval for the map manager."""
        if self._map_manager:
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
            and self._protocol.cloud.logged_in
            and self._protocol.cloud.connected
        )


class DreameVacuumDeviceStatus:
    """Helper class for device status and int enum type properties.
    This class is used for determining various states of the device by its properties. 
    Determined states are used by multiple validation and rendering condition checks.
    Almost of the rules are extracted from mobile app that has a similar class with same purpose."""

    _cleaning_history = None
    _last_cleaning_time = None

    suction_level_list = {v: k for k, v in SUCTION_LEVEL_CODE_TO_NAME.items()}
    water_volume_list = {v: k for k, v in WATER_VOLUME_CODE_TO_NAME.items()}
    mop_pad_humidity_list = {v: k for k, v in MOP_PAD_HUMIDITY_CODE_TO_NAME.items()}
    cleaning_mode_list = {v: k for k, v in CLEANING_MODE_CODE_TO_NAME.items()}
    carpet_sensitivity_list = {v: k for k, v in CARPET_SENSITIVITY_CODE_TO_NAME.items()}
    self_clean_area_list = {v: k for k, v in SELF_AREA_CLEAN_TO_NAME.items()}
    mop_wash_level_list = {v: k for k, v in MOP_WASH_LEVEL_TO_NAME.items()}
    mopping_type_list = {v: k for k, v in MOPPING_TYPE_TO_NAME.items()}

    ai_policy_accepted = False
    ai_obstacle_detection = None
    obstacle_image_upload = None
    pet_detection = None
    human_detection = None
    furniture_detection = None
    fluid_detection = None
    obstacle_picture = None
    ai_picture = None
    collision_avoidance = None
    fill_light = None
    auto_drying = None
    stain_avoidance = None
    mopping_type = None
        
    lidar_navigation = None
    ai_detection_available = None
    self_wash_base_available = None
    auto_empty_base_available = None
    mop_pad_lifting_available = None
    customized_cleaning_available = None
    auto_switch_settings_available = None
    robot_shape = None

    def __init__(self, device):
        self._device = device

    def update_static_properties(self):
        self.lidar_navigation = bool(self._get_property(DreameVacuumProperty.MAP_SAVING) is None)
        self.ai_detection_available = bool(self._get_property(DreameVacuumProperty.AI_DETECTION) is not None)
        self.self_wash_base_available = bool(self._get_property(DreameVacuumProperty.SELF_WASH_BASE_STATUS) is not None)
        self.auto_empty_base_available = bool(self._get_property(DreameVacuumProperty.DUST_COLLECTION) is not None)
        self.customized_cleaning_available = bool(self._get_property(DreameVacuumProperty.CUSTOMIZED_CLEANING) is not None)
        self.auto_switch_settings_available = bool(self._get_property(DreameVacuumProperty.AUTO_SWITCH_SETTINGS) is not None)
        self.mop_pad_lifting_available = bool((self.self_wash_base_available and self.auto_empty_base_available) or (self._device.info and "r2216" in self._device.info.model))
        self.robot_shape = 2 if self.self_wash_base_available and not self.mop_pad_lifting_available else 0 if self.lidar_navigation else 1

    def _get_property(self, prop: DreameVacuumProperty) -> Any:
        """Helper function for accessing a property from device"""
        return self._device.get_property(prop)

    @property
    def _map_manager(self) -> DreameMapVacuumMapManager | None:
        """Helper property for accessing map manager from device"""
        return self._device._map_manager

    @property
    def _device_connected(self) -> bool:
        """Helper property for accessing device connection status"""
        return self._device.device_connected

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
        _LOGGER.debug("SUCTION_LEVEL not supported: %s", value)
        return DreameVacuumSuctionLevel.UNKNOWN

    @property
    def suction_level_name(self) -> str:
        """Return suction level as string for translation."""
        return SUCTION_LEVEL_CODE_TO_NAME.get(self.suction_level, STATE_UNKNOWN)

    @property
    def water_volume(self) -> DreameVacuumWaterVolume:
        """Return water volume of the device."""
        value = self._get_property(DreameVacuumProperty.WATER_VOLUME)
        if value is not None and value in DreameVacuumWaterVolume._value2member_map_:
            return DreameVacuumWaterVolume(value)
        _LOGGER.debug("WATER_VOLUME not supported: %s", value)
        return DreameVacuumWaterVolume.UNKNOWN

    @property
    def water_volume_name(self) -> str:
        """Return water volume as string for translation."""
        return WATER_VOLUME_CODE_TO_NAME.get(self.water_volume, STATE_UNKNOWN)

    @property
    def mop_pad_humidity(self) -> DreameVacuumMopPadHumidity:
        """Return mop pad humidity of the device."""
        if self.self_wash_base_available:
            values = DreameVacuumDevice.split_group_value(self._get_property(DreameVacuumProperty.CLEANING_MODE))
            if values and len(values) == 3:
                value = values[2]
                if value is not None and value in DreameVacuumMopPadHumidity._value2member_map_:
                    return DreameVacuumMopPadHumidity(value)
                _LOGGER.debug("MOP_PAD_HUMIDITY not supported: %s", value)
                return DreameVacuumMopPadHumidity.UNKNOWN

    @property
    def mop_pad_humidity_name(self) -> str:
        """Return mop pad humidity as string for translation."""
        return MOP_PAD_HUMIDITY_CODE_TO_NAME.get(self.mop_pad_humidity, STATE_UNKNOWN)

    @property
    def cleaning_mode(self) -> DreameVacuumCleaningMode:
        """Return cleaning mode of the device."""
        value = self._get_property(DreameVacuumProperty.CLEANING_MODE)
        if self.self_wash_base_available:
            values = DreameVacuumDevice.split_group_value(value, self.mop_pad_lifting_available)
            if values and len(values) == 3:
                if not self.mop_pad_lifting_available:
                    if not self.water_tank_or_mop_installed:
                        return DreameVacuumCleaningMode.SWEEPING
                    if values[0] == 1:
                        return DreameVacuumCleaningMode.MOPPING
                    return DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                else:
                    if values[0] == 2:
                        return DreameVacuumCleaningMode.SWEEPING
                    if values[0] == 0:
                        return DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                    value = values[0]
        elif self.mop_pad_lifting_available:
            if value == 2:
                return DreameVacuumCleaningMode.SWEEPING
            if value == 0:
                return DreameVacuumCleaningMode.SWEEPING_AND_MOPPING

        if value is None:
            return DreameVacuumCleaningMode.SWEEPING_AND_MOPPING if self.water_tank_or_mop_installed else DreameVacuumCleaningMode.SWEEPING

        if value in DreameVacuumCleaningMode._value2member_map_:
            return DreameVacuumCleaningMode(value)
        _LOGGER.debug("CLEANING_MODE not supported: %s", value)
        return DreameVacuumCleaningMode.UNKNOWN

    @property
    def cleaning_mode_name(self) -> str:
        """Return cleaning mode as string for translation."""
        return CLEANING_MODE_CODE_TO_NAME.get(self.cleaning_mode, STATE_UNKNOWN)

    @property
    def status(self) -> DreameVacuumStatus:
        """Return status of the device."""
        value = self._get_property(DreameVacuumProperty.STATUS)
        if value is not None and value in DreameVacuumStatus._value2member_map_:
            return DreameVacuumStatus(value)
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
            return DreameVacuumTaskStatus(value)
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
            if value == 2:
                return DreameVacuumWaterTank.MOP_INSTALLED

            if value in DreameVacuumWaterTank._value2member_map_:
                return DreameVacuumWaterTank(value)
        _LOGGER.debug("WATER_TANK not supported: %s", value)
        return DreameVacuumWaterTank.UNKNOWN

    @property
    def water_tank_name(self) -> str:
        """Return water tank as string for translation."""
        return WATER_TANK_CODE_TO_NAME.get(self.water_tank, STATE_UNKNOWN)

    @property
    def charging_status(self) -> DreameVacuumChargingStatus:
        """Return charging status of the device."""
        value = self._get_property(DreameVacuumProperty.CHARGING_STATUS)
        if value is not None and value in DreameVacuumChargingStatus._value2member_map_:
            value = DreameVacuumChargingStatus(value)
            # Charging status complete is not present on older firmwares
            if (
                value is DreameVacuumChargingStatus.CHARGING
                and self.battery_level == 100
            ):
                return DreameVacuumChargingStatus.CHARGING_COMPLETED
            return value
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
        if (
            value is not None
            and value in DreameVacuumAutoEmptyStatus._value2member_map_
        ):
            return DreameVacuumAutoEmptyStatus(value)
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
        if (
            value is not None
            and value in DreameVacuumRelocationStatus._value2member_map_
        ):
            return DreameVacuumRelocationStatus(value)
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
        if (
            value is not None
            and value in DreameVacuumSelfWashBaseStatus._value2member_map_
        ):
            return DreameVacuumSelfWashBaseStatus(value)
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
        if (
            value is not None
            and value in DreameVacuumCarpetSensitivity._value2member_map_
        ):
            return DreameVacuumCarpetSensitivity(value)
        _LOGGER.debug("CARPET_SENSITIVITY not supported: %s", value)
        return DreameVacuumCarpetSensitivity.UNKNOWN

    @property
    def carpet_sensitivity_name(self) -> str:
        """Return carpet sensitivity as string for translation."""
        return CARPET_SENSITIVITY_CODE_TO_NAME.get(
            self.carpet_sensitivity, STATE_UNKNOWN
        )

    @property
    def state(self) -> DreameVacuumState:
        """Return state of the device."""
        value = self._get_property(DreameVacuumProperty.STATE)
        if value is not None and value in DreameVacuumState._value2member_map_:
            vacuum_state = DreameVacuumState(value)

            ## Determine state as implemented on the app
            if vacuum_state is DreameVacuumState.IDLE:
                if (
                    self.started
                    or self.cleaning_paused
                    or self.fast_mapping_paused
                ):
                    return DreameVacuumState.PAUSED
                elif self.docked:
                    ## This is for compatibility with various lovelace vacuum cards 
                    ## Device will report idle when charging is completed and vacuum card will display return to dock icon even when robot is docked
                    if self.washing:
                        return DreameVacuumState.WASHING
                    if self.drying:                        
                        return DreameVacuumState.DRYING                    
                    if self.charging:
                        return DreameVacuumState.CHARGING
                    if self.charging_status is DreameVacuumChargingStatus.CHARGING_COMPLETED:
                        return DreameVacuumState.CHARGING_COMPLETED
            return vacuum_state
        _LOGGER.debug("STATE not supported: %s", value)
        return DreameVacuumState.UNKNOWN

    @property
    def state_name(self) -> str:
        """Return state as string for translation."""
        return STATE_CODE_TO_STATE.get(self.state, STATE_UNKNOWN)

    @property
    def self_clean_area(self) -> DreameVacuumSelfCleanArea:
        """Return self-clean area of the device."""
        if self.self_wash_base_available:
            values = DreameVacuumDevice.split_group_value(self._get_property(DreameVacuumProperty.CLEANING_MODE))
            if values and len(values) == 3:
                value = values[1]
                if (
                    value is not None
                    and value in DreameVacuumSelfCleanArea._value2member_map_
                ):
                    return DreameVacuumSelfCleanArea(value)
                _LOGGER.debug("SELF_CLEAN_AREA not supported: %s", value)
                return DreameVacuumSelfCleanArea.UNKNOWN

    @property
    def self_clean_area_name(self) -> str:
        """Return self-clean area as string for translation."""
        return SELF_AREA_CLEAN_TO_NAME.get(self.self_clean_area, STATE_UNKNOWN)

    @property
    def mop_wash_level(self) -> DreameVacuumSelfCleanArea:
        """Return mop wash level of the device."""
        if self.self_wash_base_available:
            value = self._get_property(DreameVacuumProperty.MOP_WASH_LEVEL)
            if (
                value is not None
                and value in DreameVacuumMopWashLevel._value2member_map_
            ):
                return DreameVacuumMopWashLevel(value)
            _LOGGER.debug("MOP_WASH_LEVEL not supported: %s", value)
            return DreameVacuumMopWashLevel.UNKNOWN

    @property
    def mop_wash_level_name(self) -> str:
        """Return mop wash level as string for translation."""
        return MOP_WASH_LEVEL_TO_NAME.get(self.mop_wash_level, STATE_UNKNOWN)

    @property
    def mopping_type_name(self) -> str:
        """Return moping type as string for translation."""
        if (
            self.mopping_type is not None
            and self.mopping_type in DreameVacuumMoppingType._value2member_map_
        ):
            return MOPPING_TYPE_TO_NAME.get(DreameVacuumMoppingType(self.mopping_type), STATE_UNKNOWN)
        return STATE_UNKNOWN

    @property
    def error(self) -> DreameVacuumErrorCode:
        """Return error of the device."""
        value = self._get_property(DreameVacuumProperty.ERROR)
        if value is not None and value in DreameVacuumErrorCode._value2member_map_:
            return DreameVacuumErrorCode(value)
        _LOGGER.debug("ERROR_CODE not supported: %s", value)
        return DreameVacuumErrorCode.UNKNOWN

    @property
    def error_name(self) -> str:
        """Return error as string for translation."""
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
    def robot_status(self) -> int:  # TODO: Convert to enum
        """Device status for robot icon rendering."""
        if self.running and not self.returning and not self.fast_mapping:
            return 1
        elif self.self_wash_base_available and (self.washing or self.drying or self.washing_paused):
            if self.has_error or self.has_warning:
                return 6
            return 7
        elif self.charging:
            return 2
        elif self.has_error or self.has_warning:
            if self.sleeping:
                return 5
            else:
                return 3
        elif self.sleeping:
            return 4
        return 0

    @property
    def has_error(self) -> bool:
        """Returns true when an error is present."""
        error = self.error
        return bool(
            error.value > 0
            and not self.has_warning
            and error != DreameVacuumErrorCode.BATTERY_LOW
        )

    @property
    def has_warning(self) -> bool:
        """Returns true when a warning is present and available for dismiss."""
        error = self.error
        return bool(
            error.value > 0
            and (
                error == DreameVacuumErrorCode.REMOVE_MOP
                or error == DreameVacuumErrorCode.MOP_REMOVED_2
                or error == DreameVacuumErrorCode.CLEAN_MOP_PAD
                or error == DreameVacuumErrorCode.BLOCKED
                or error == DreameVacuumErrorCode.WATER_TANK_DRY
                or error == DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE
                or error == DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE_2
            )
        )

    @property
    def dust_collection_available(self) -> bool:        
        """Returns true when robot is docked and can start auto emptying."""
        return bool(self._get_property(DreameVacuumProperty.DUST_COLLECTION))

    @property
    def self_clean(self) -> bool:
        return bool(self._get_property(DreameVacuumProperty.SELF_CLEAN) == 1)

    @property
    def scheduled_clean(self) -> bool:
        return bool(self._get_property(DreameVacuumProperty.SCHEDULED_CLEAN) == 1)

    @property
    def auto_mount(self) -> bool:
        return bool(self._get_property(DreameVacuumProperty.AUTO_MOUNT_MOP) == 1)

    @property
    def dnd_remaining(self) -> bool:
        """Returns remaining seconds to DND period to end."""
        if self.dnd_enabled:
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
                    end_seconds = int(end_time[0]) * \
                        3600 + int(end_time[1]) * 60

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
        water_tank = self.water_tank
        return bool(water_tank is DreameVacuumWaterTank.INSTALLED or water_tank is DreameVacuumWaterTank.MOP_INSTALLED)

    @property
    def located(self) -> bool:
        """Returns true when robot knows its position on current map."""
        relocation_status = self.relocation_status
        return bool(
            relocation_status is DreameVacuumRelocationStatus.LOCATED
            or relocation_status is DreameVacuumRelocationStatus.UNKNOWN
        )

    @property
    def sweeping(self) -> bool:
        """Returns true when cleaning mode is sweeping therefore cannot set its water volume."""
        cleaning_mode = self.cleaning_mode
        return bool(cleaning_mode is not DreameVacuumCleaningMode.MOPPING and cleaning_mode is not DreameVacuumCleaningMode.SWEEPING_AND_MOPPING)

    @property
    def mopping(self) -> bool:
        """Returns true when cleaning mode is mopping therefore cannot set its suction level."""
        return bool(self.cleaning_mode is DreameVacuumCleaningMode.MOPPING)

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
        Used for resuming fast cleaning on start because standard start action can not be used for resuming fast mapping."""

        state = self._get_property(DreameVacuumProperty.STATE)
        task_status = self.task_status
        return bool(
            (
                task_status == DreameVacuumTaskStatus.FAST_MAPPING
                or task_status == DreameVacuumTaskStatus.MAP_CLEANING_PAUSED
            )
            and (
                state == DreameVacuumState.PAUSED
                or state == DreameVacuumState.ERROR
                or state == DreameVacuumState.IDLE
            )
        )

    @property
    def carpet_avoidance(self) -> bool:        
        """Returns true when carpet avoidance feature is enabled."""
        value = self._get_property(DreameVacuumProperty.CARPET_AVOIDANCE)
        return bool(value == 1)

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
        return bool(self.charging_status is DreameVacuumChargingStatus.CHARGING)

    @property
    def docked(self) -> bool:
        """Returns true when device is docked."""
        return bool(
            self.charging
            or self.charging_status is DreameVacuumChargingStatus.CHARGING_COMPLETED
            or self.washing
            or self.drying
            or self.washing_paused
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
            and task_status is DreameVacuumTaskStatus.DOCKING_PAUSED
            or task_status is DreameVacuumTaskStatus.AUTO_DOCKING_PAUSED
            or task_status is DreameVacuumTaskStatus.SEGMENT_DOCKING_PAUSED
            or task_status is DreameVacuumTaskStatus.ZONE_DOCKING_PAUSED
        )

    @property
    def returning(self) -> bool:
        """Returns true when returning to dock for charging or washing."""
        return bool(
            self._device_connected
            and (
                self.status is DreameVacuumStatus.BACK_HOME
                or self.returning_to_wash
            )
        )

    @property
    def started(self) -> bool:
        """Returns true when device has an active task.
        Used for preventing updates on settings that relates to currently performing task."""
        return bool(
            self.task_status != DreameVacuumTaskStatus.COMPLETED or self.cleaning_paused
        )

    @property
    def paused(self) -> bool:
        """Returns true when device has an active paused task."""
        status = self.status
        return bool(
            self.started
            and (
                status is DreameVacuumStatus.PAUSED
                or status is DreameVacuumStatus.SLEEPING
                or status is DreameVacuumStatus.IDLE
                or status is DreameVacuumStatus.STANDBY
            )
            or self.cleaning_paused
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
            not self.docked
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
                or status is DreameVacuumStatus.MONITOR_CRUISE
                or status is DreameVacuumStatus.MONITOR_SPOT
                or status is DreameVacuumStatus.SUMMON_CLEAN
            )
        )

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
    def cleaning_history(self) -> dict[str, Any] | None:
        """Returns the cleaning history list as dict."""
        if self._cleaning_history:
            list = {}
            for history in self._cleaning_history:
                date = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(
                        history.date.timestamp())
                )                
                list[date] = {
                    ATTR_CLEANING_TIME: f"{history.cleaning_time} min",
                    ATTR_CLEANED_AREA: f"{history.cleaned_area} m²",
                }
                if history.status is not None:
                    list[date][ATTR_STATUS] = (
                        STATUS_CODE_TO_NAME.get(history.status, STATE_UNKNOWN)
                        .replace("_", " ")
                        .capitalize()
                    )
                if history.suction_level is not None:
                    list[date][ATTR_SUCTION_LEVEL] = (
                        SUCTION_LEVEL_CODE_TO_NAME.get(
                            history.suction_level, STATE_UNKNOWN)
                        .replace("_", " ")
                        .capitalize()
                    )
                if history.completed is not None:
                    list[date][ATTR_COMPLETED] = history.completed
                if history.water_tank is not None:
                    list[date][ATTR_WATER_TANK] = (
                        WATER_TANK_CODE_TO_NAME.get(
                            history.water_tank, STATE_UNKNOWN)
                        .replace("_", " ")
                        .capitalize()
                    )
            return list

    @property
    def washing(self) -> bool:
        """Returns true the when device is currently performing mop washing."""
        return bool(self.self_wash_base_available and (self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.WASHING or self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.CLEAN_ADD_WATER))

    @property
    def drying(self) -> bool:
        """Returns true the when device is currently performing mop drying."""
        return bool(self.self_wash_base_available and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.DRYING)

    @property
    def washing_paused(self) -> bool:
        """Returns true when mop washing paused."""
        return bool(self.self_wash_base_available and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.PAUSED)

    @property
    def returning_to_wash(self) -> bool:
        """Returns true when the device returning to self-wash base to wash or dry its mop."""
        return bool(self.self_wash_base_available and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.RETURNING and (self.state == DreameVacuumState.RETURNING or self.state == DreameVacuumState.RETURNING_WASHING))

    @property
    def returning_to_wash_paused(self) -> bool:
        """Returns true when the device returning to self-wash base to wash or dry its mop."""
        return bool(self.self_wash_base_available and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.RETURNING and self.state == DreameVacuumState.PAUSED)

    @property
    def washing_available(self) -> bool:
        """Returns true when device has a self-wash base and washing mop can be performed."""
        return bool(
            self.self_wash_base_available and
            self.water_tank_or_mop_installed and
            not
            (
                self.washing or
                self.washing_paused or
                self.returning_to_wash_paused or
                self.returning_to_wash or
                self.returning or
                self.returning_paused or
                self.cleaning_paused
            )
        )

    @property
    def drying_available(self) -> bool:
        """Returns true when device has a self-wash base and drying mop can be performed."""
        return bool(
            self.self_wash_base_available and
            self.water_tank_or_mop_installed and
            self.docked and
            not (self.washing or self.washing_paused)
        )

    @property
    def mapping_available(self) -> bool:
        """Returns true when creating a new map is possible."""
        return bool(
            not self.started
            and not self.fast_mapping
            and (
                not self.map_available
                or ((3 if self.multi_map else 1) > len(self.map_list))
            )
        )

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
        """Returns sensor clean remaining life in percent."""
        return self._get_property(DreameVacuumProperty.SENSOR_DIRTY_LEFT)
    
    @property
    def secondary_filter_life(self) -> int:
        """Returns secondary filter remaining life in percent."""
        return self._get_property(DreameVacuumProperty.SECONDARY_FILTER_LEFT)

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
    def dnd_enabled(self) -> bool:
        """Returns DND is enabled."""
        return bool(self._get_property(DreameVacuumProperty.DND))

    @property
    def dnd_start(self) -> str:
        """Returns DND start time."""
        return self._get_property(DreameVacuumProperty.DND_START)

    @property
    def dnd_end(self) -> str:
        """Returns DND end time."""
        return self._get_property(DreameVacuumProperty.DND_END)

    @property
    def custom_order(self) -> bool:
        """Returns true when custom cleaning sequence is set."""
        segments = self.segments
        if segments:
            for v in segments.values():
                if v.order:
                    return True
        return False

    @property
    def cleaning_sequence(self) -> list[int] | None:
        """Returns custom cleaning sequence list."""
        segments = self.segments 
        if segments:
            return list(sorted(segments, key=lambda segment_id: segments[segment_id].order if segments[segment_id].order else 99)) if self.custom_order else None
        return [] if self.custom_order else None
    
    @property
    def map_available(self) -> bool:
        """Returns true when mapping feature is available."""
        return bool(self._map_manager is not None)

    @property
    def has_saved_map(self) -> bool:
        """Returns true when device has saved map and knowns its location on saved map."""
        if not self.map_available:
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
        if not self.map_available:
            return False

        current_map = self.current_map
        return bool(
            current_map is not None
            and current_map.temporary_map
            and not current_map.empty_map
        )

    @property
    def has_new_map(self) -> bool:
        """Returns true when fast mapping from empty map."""
        if not self.map_available:
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
        if self.map_available and not self.has_temporary_map and not self.has_new_map:
            return self._map_manager.selected_map

    @property
    def current_map(self) -> MapData | None:
        """Return the current map data"""
        if self.map_available:
            return self._map_manager.get_map()

    @property
    def map_list(self) -> list[int] | None:
        """Return the saved map id list if multi floor map is enabled"""
        if self.map_available:
            if self.multi_map:
                return self._map_manager.map_list

            selected_map = self._map_manager.selected_map
            if selected_map:
                return [selected_map.map_id]
        return []

    @property
    def map_data_list(self) -> dict[int, MapData] | None:
        """Return the saved map data list if multi floor map is enabled"""
        if self.map_available:
            if self.multi_map:
                return self._map_manager.map_data_list
            selected_map = self.selected_map
            if selected_map:
                return {selected_map.map_id: selected_map}
        return {}

    @property
    def segments(self) -> dict[int, Segment] | None:
        """Return the segments of current map"""
        current_map = self.current_map
        if current_map and current_map.segments and not current_map.empty_map:
            return current_map.segments
        return {}

    @property
    def current_room(self) -> Segment | None:
        """Return the segment that device is currently on"""
        if self.lidar_navigation:
            current_map = self.current_map
            if (
                current_map
                and current_map.segments
                and current_map.robot_segment
                and not current_map.empty_map
            ):
                return current_map.segments[current_map.robot_segment]

    @property
    def active_segments(self) -> list[int] | None:        
        map_data = self.current_map
        if map_data and self.started and not self.fast_mapping:
            if self.segment_cleaning:
                if map_data.active_segments:
                    return map_data.active_segments
            elif not self.zone_cleaning and not self.spot_cleaning and map_data.segments and not self.docked and not self.returning and not self.returning_paused:
                return list(map_data.segments.keys())
            return []

    @property
    def job(self) -> dict[str, Any] | None:
        attributes = {
            ATTR_CLEANING_MODE: self.cleaning_mode.name,
            ATTR_STATUS: self.status.name
        }        
        attributes[ATTR_WATER_TANK if not self.self_wash_base_available else ATTR_MOP_PAD] = self.water_tank_or_mop_installed

        if self._device.cleanup_completed:
            attributes.update({
                ATTR_CLEANED_AREA: self._get_property(DreameVacuumProperty.CLEANED_AREA),
                ATTR_CLEANING_TIME: self._get_property(DreameVacuumProperty.CLEANING_TIME),
                ATTR_COMPLETED: True,
            })
        else:
            attributes[ATTR_COMPLETED] = False

        map_data = self.current_map
        if map_data:
            if map_data.active_segments is not None:
                attributes[ATTR_ACTIVE_SEGMENTS] = map_data.active_segments
            elif map_data.active_areas is not None:
                attributes[ATTR_ACTIVE_AREAS] = map_data.active_areas
            elif map_data.active_points is not None:
                attributes[ATTR_ACTIVE_POINTS] = map_data.active_points
        return attributes

    @property
    def attributes(self) -> dict[str, Any] | None:
        """Return the attributes of the device."""
        properties = [
            DreameVacuumProperty.CLEANING_MODE,
            DreameVacuumProperty.TIGHT_MOPPING,
            DreameVacuumProperty.ERROR,
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
            DreameVacuumProperty.SENSOR_DIRTY_LEFT,
            DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
            DreameVacuumProperty.SECONDARY_FILTER_LEFT,
            DreameVacuumProperty.SECONDARY_FILTER_TIME_LEFT,
            DreameVacuumProperty.MOP_PAD_LEFT,
            DreameVacuumProperty.MOP_PAD_TIME_LEFT,
            DreameVacuumProperty.SILVER_ION_LEFT,
            DreameVacuumProperty.SILVER_ION_TIME_LEFT,
            DreameVacuumProperty.DETERGENT_LEFT,
            DreameVacuumProperty.DETERGENT_TIME_LEFT,
            DreameVacuumProperty.TOTAL_CLEANED_AREA,
            DreameVacuumProperty.TOTAL_CLEANING_TIME,
            DreameVacuumProperty.CLEANING_COUNT,
            DreameVacuumProperty.DND_START,
            DreameVacuumProperty.DND_END,
            DreameVacuumProperty.CUSTOMIZED_CLEANING,
            DreameVacuumProperty.SERIAL_NUMBER,
        ]

        attributes = {}
        if not self.self_wash_base_available:
            attributes[ATTR_WATER_TANK] = self.water_tank_or_mop_installed
            properties.append(DreameVacuumProperty.WATER_VOLUME)
        else:
            attributes[ATTR_MOP_PAD] = self.water_tank_or_mop_installed
            if self.started and (self.customized_cleaning and not (self.zone_cleaning or self.spot_cleaning)):
                attributes[ATTR_MOP_PAD_HUMIDITY] = STATE_UNAVAILABLE.capitalize()
                attributes[f"{ATTR_MOP_PAD_HUMIDITY}_list"] = []
            else:
                attributes[ATTR_MOP_PAD_HUMIDITY] = self.mop_pad_humidity_name.replace("_", " ").capitalize()
                attributes[f"{ATTR_MOP_PAD_HUMIDITY}_list"] = [v.replace("_", " ").capitalize() for v in self.mop_pad_humidity_list.keys()]

        for prop in properties:
            value = self._get_property(prop)
            if value is not None:
                prop_name = PROPERTY_TO_NAME.get(prop)
                if prop_name:
                    prop_name = prop_name[0]
                else:
                    prop_name = prop.name.lower()

                if prop is DreameVacuumProperty.ERROR:
                    value = self.error_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.WATER_VOLUME:
                    if self.started and (self.customized_cleaning and not (self.zone_cleaning or self.spot_cleaning)):
                        value = STATE_UNAVAILABLE.capitalize()
                        attributes[f"{prop_name}_list"] = []
                    else:
                        value = self.water_volume_name.capitalize()
                        attributes[f"{prop_name}_list"] = [v.capitalize() for v in self.water_volume_list.keys()]
                elif prop is DreameVacuumProperty.CLEANING_MODE:
                    value = self.cleaning_mode_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.CUSTOMIZED_CLEANING:
                    value = self.customized_cleaning and not self.zone_cleaning and not self.spot_cleaning 
                elif prop is DreameVacuumProperty.TIGHT_MOPPING:
                    value = "on" if value == 1 else "off"
                attributes[prop_name] = value
                
        attributes[ATTR_CLEANING_SEQUENCE] = self.cleaning_sequence
        attributes[ATTR_CHARGING] = self.docked
        attributes[ATTR_STARTED] = self.started
        attributes[ATTR_PAUSED] = self.paused
        attributes[ATTR_RUNNING] = self.running
        attributes[ATTR_RETURNING_PAUSED] = self.returning_paused
        attributes[ATTR_RETURNING] = self.returning
        attributes[ATTR_MAPPING] = self.fast_mapping
        
        if self.map_list:
            attributes[ATTR_ACTIVE_SEGMENTS] = self.active_segments
            if self.lidar_navigation:
                attributes[ATTR_CURRENT_SEGMENT] = self.current_room.segment_id if self.current_room else 0
            attributes[ATTR_SELECTED_MAP] = self.selected_map.map_name if self.selected_map else None
            attributes[ATTR_ROOMS] = {}
            for (k, v) in self.map_data_list.items():
                attributes[ATTR_ROOMS][v.map_name] = [
                    {ATTR_ID: j, ATTR_NAME: s.name, ATTR_ICON: s.icon}
                    for (j, s) in sorted(v.segments.items())
                ]

        return attributes


class DreameVacuumDeviceInfo:
    """Container of device information."""

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "%s v%s (%s) @ %s - token: %s" % (
            self.data["model"],
            self.data["fw_ver"],
            self.data["mac"],
            self.network_interface["localIp"],
            self.data["token"],
        )

    @property
    def network_interface(self) -> str:
        """Information about network configuration."""
        return self.data["netif"]

    @property
    def accesspoint(self) -> str:
        """Information about connected WLAN access point."""
        return self.data["ap"]

    @property
    def model(self) -> Optional[str]:
        """Model string if available."""
        if self.data["model"] is not None:
            return self.data["model"]
        return None

    @property
    def firmware_version(self) -> Optional[str]:
        """Firmware version if available."""
        if self.data["fw_ver"] is not None:
            return self.data["fw_ver"]
        return None

    @property
    def version(self) -> Optional[int]:
        """Firmware version number if firmware version available."""
        firmware_version = self.firmware_version
        if firmware_version is not None:
            firmware_version = firmware_version.split("_")
            if len(firmware_version) == 2:
                return int(firmware_version[1])
        return None

    @property
    def hardware_version(self) -> Optional[str]:
        """Hardware version if available."""
        if self.data["hw_ver"] is not None:
            return self.data["hw_ver"]
        return None

    @property
    def mac_address(self) -> Optional[str]:
        """MAC address if available."""
        if self.data["mac"] is not None:
            return self.data["mac"]
        return None

    @property
    def manufacturer(self) -> str:
        """Manufacturer name."""
        return "Dreametech™"

    @property
    def raw(self) -> dict[str, Any]:
        """Raw data as returned by the device."""
        return self.data
