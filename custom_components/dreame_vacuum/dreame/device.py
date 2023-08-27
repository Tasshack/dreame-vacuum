from __future__ import annotations
import logging
import time
import json
import re
import copy
import zlib
import base64
import traceback
from datetime import datetime
from random import randrange
from threading import Timer
from typing import Any, Optional

from .types import (
    PIID,
    DIID,
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
    DreameVacuumMoppingType,
    DreameVacuumStreamStatus,
    DreameVacuumVoiceAssistantLanguage,
    DreameVacuumWiderCornerCoverage,
    DreameVacuumDrainageStatus,
    DreameVacuumLowWaterWarning,
    DreameVacuumTaskType,
    CleaningHistory,
    RobotType,
    MapData,
    Segment,
    Shortcut,
    ShortcutTask,
    ObstacleType,
    GoToZoneSettings,
    Path,
    PathType,
    Coordinate,
    ATTR_ACTIVE_AREAS,
    ATTR_ACTIVE_POINTS,
    ATTR_ACTIVE_SEGMENTS,
    ATTR_PREDEFINED_POINTS,
    ATTR_ACTIVE_CRUISE_POINTS,
    DeviceCapability,
)
from .const import (
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
    TASK_STATUS_CODE_TO_NAME,
    STATE_CODE_TO_STATE,
    ERROR_CODE_TO_ERROR_NAME,
    ERROR_CODE_TO_ERROR_DESCRIPTION,
    STATUS_CODE_TO_NAME,
    WATER_TANK_CODE_TO_NAME,
    DUST_COLLECTION_TO_NAME,
    MOP_WASH_LEVEL_TO_NAME,
    MOPPING_TYPE_TO_NAME,
    STREAM_STATUS_TO_NAME,
    WIDER_CORNER_COVERAGE_TO_NAME,
    FLOOR_MATERIAL_CODE_TO_NAME,
    LOW_WATER_WARNING_TO_NAME,
    LOW_WATER_WARNING_CODE_TO_DESCRIPTION,
    DRAINAGE_STATUS_TO_NAME,
    VOICE_ASSISTANT_LANGUAGE_TO_NAME,
    TASK_TYPE_TO_NAME,
    ERROR_CODE_TO_IMAGE_INDEX,
    CONSUMABLE_TO_LIFE_WARNING_DESCRIPTION,
    PROPERTY_TO_NAME,
    DEVICE_KEY,
    CLEANING_MODE_MOPPING_AFTER_SWEEPING,
    ATTR_CHARGING,
    ATTR_DND,
    ATTR_SHORTCUTS,
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
    ATTR_SELF_CLEAN_AREA,
    ATTR_MOP_PAD,
    ATTR_WASHING,
    ATTR_WASHING_PAUSED,
    ATTR_DRYING,
    ATTR_DRAINING,
    ATTR_LOW_WATER,
    ATTR_CRUISING_TIME,
    ATTR_CRUISING_TYPE,
    ATTR_MAP_INDEX,
    ATTR_MAP_NAME,
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

    property_mapping: dict[
        DreameVacuumProperty, dict[str, int]
    ] = DreameVacuumPropertyMapping
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
    ) -> None:
        # Used for tracking the task status is changed from cleaning to completed
        self.cleanup_completed: bool = False
        # Used for easy filtering the device from cloud device list and generating unique ids
        self.mac: str = None
        self.token: str = None  # Local api token
        self.host: str = None  # IP address or host name of the device
        # Dictionary for storing the current property values
        self.data: dict[DreameVacuumProperty, Any] = {}
        self.auto_switch_data: dict[DreameVacuumAutoSwitchProperty, Any] = None
        self.ai_data: dict[
            DreameVacuumStrAIProperty | DreameVacuumAIProperty, Any
        ] = None
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
        self._update_fail_count: int = 0  # Update failed counter
        self._draining_complete_time: int = None
        # Map Manager object. Only available when cloud connection is present
        self._map_manager: DreameMapVacuumMapManager = None
        self._update_callback = None  # External update callback for device
        self._error_callback = None  # External update failed callback
        # External update callbacks for specific device property
        self._property_update_callback = {}
        self._update_timer: Timer = None  # Update schedule timer
        # Used for requesting consumable properties after reset action otherwise they will only requested when cleaning completed
        self._consumable_change: bool = False
        self._remote_control: bool = False
        self._dirty_data: dict[DreameVacuumProperty, Any] = {}

        self._name = name
        self.mac = mac
        self.token = token
        self.host = host
        self.two_factor_url = None
        self.account_type = account_type
        self.status = DreameVacuumDeviceStatus(self)
        self.capability = DeviceCapability(self)

        self._default_properties = [prop for prop in DreameVacuumProperty]
        # Remove write only and response only properties from default list
        self._default_properties.remove(DreameVacuumProperty.SCHEDULE_ID)
        self._default_properties.remove(DreameVacuumProperty.REMOTE_CONTROL)
        self._default_properties.remove(DreameVacuumProperty.VOICE_CHANGE)
        self._default_properties.remove(DreameVacuumProperty.VOICE_CHANGE_STATUS)
        self._default_properties.remove(DreameVacuumProperty.MAP_RECOVERY)
        self._default_properties.remove(DreameVacuumProperty.MAP_RECOVERY_STATUS)
        self._default_properties.remove(DreameVacuumProperty.CLEANING_START_TIME)
        self._default_properties.remove(DreameVacuumProperty.CLEAN_LOG_FILE_NAME)
        self._default_properties.remove(DreameVacuumProperty.CLEANING_PROPERTIES)
        self._default_properties.remove(DreameVacuumProperty.CLEAN_LOG_STATUS)
        self._default_properties.remove(DreameVacuumProperty.MAP_INDEX)
        self._default_properties.remove(DreameVacuumProperty.MAP_NAME)
        self._default_properties.remove(DreameVacuumProperty.CRUISE_TYPE)
        self._default_properties.remove(DreameVacuumProperty.MAP_DATA)
        self._default_properties.remove(DreameVacuumProperty.FRAME_INFO)
        self._default_properties.remove(DreameVacuumProperty.OBJECT_NAME)
        self._default_properties.remove(DreameVacuumProperty.MAP_EXTEND_DATA)
        self._default_properties.remove(DreameVacuumProperty.ROBOT_TIME)
        self._default_properties.remove(DreameVacuumProperty.RESULT_CODE)
        self._default_properties.remove(DreameVacuumProperty.OLD_MAP_DATA)
        self._default_properties.remove(DreameVacuumProperty.TAKE_PHOTO)
        self._default_properties.remove(DreameVacuumProperty.STEAM_HUMAN_FOLLOW)
        self._default_properties.remove(DreameVacuumProperty.STREAM_KEEP_ALIVE)
        self._default_properties.remove(DreameVacuumProperty.STREAM_UPLOAD)
        self._default_properties.remove(DreameVacuumProperty.STREAM_AUDIO)
        self._default_properties.remove(DreameVacuumProperty.STREAM_RECORD)
        self._default_properties.remove(DreameVacuumProperty.STREAM_CODE)
        self._default_properties.remove(DreameVacuumProperty.STREAM_SET_CODE)
        self._default_properties.remove(DreameVacuumProperty.STREAM_VERIFY_CODE)
        self._default_properties.remove(DreameVacuumProperty.STREAM_RESET_CODE)
        self._default_properties.remove(DreameVacuumProperty.STREAM_CRUISE_POINT)
        self._default_properties.remove(DreameVacuumProperty.STREAM_FAULT)
        self._default_properties.remove(DreameVacuumProperty.STREAM_TASK)

        self.listen(self._task_status_changed, DreameVacuumProperty.TASK_STATUS)
        self.listen(self._status_changed, DreameVacuumProperty.STATUS)
        self.listen(self._charging_status_changed, DreameVacuumProperty.CHARGING_STATUS)
        self.listen(self._cleaning_mode_changed, DreameVacuumProperty.CLEANING_MODE)
        self.listen(self._water_tank_changed, DreameVacuumProperty.WATER_TANK)
        self.listen(self._water_tank_changed, DreameVacuumProperty.AUTO_MOUNT_MOP)
        self.listen(
            self._ai_obstacle_detection_changed, DreameVacuumProperty.AI_DETECTION
        )
        self.listen(
            self._auto_switch_settings_changed,
            DreameVacuumProperty.AUTO_SWITCH_SETTINGS,
        )
        self.listen(self._dnd_task_changed, DreameVacuumProperty.DND_TASK)
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
        self.listen(self._suction_level_changed, DreameVacuumProperty.SUCTION_LEVEL)
        self.listen(self._water_volume_changed, DreameVacuumProperty.WATER_VOLUME)
        self.listen(self._error_changed, DreameVacuumProperty.ERROR)

        self._protocol = DreameVacuumProtocol(
            self.host,
            self.token,
            username,
            password,
            country,
            prefer_cloud,
            account_type,
            device_id,
        )
        if self._protocol.cloud:
            self._map_manager = DreameMapVacuumMapManager(self._protocol)

            self.listen(self._map_list_changed, DreameVacuumProperty.MAP_LIST)
            self.listen(
                self._recovery_map_list_changed, DreameVacuumProperty.RECOVERY_MAP_LIST
            )
            self.listen(self._map_property_changed, DreameVacuumProperty.ERROR)
            self.listen(
                self._map_property_changed, DreameVacuumProperty.CUSTOMIZED_CLEANING
            )

            self._map_manager.listen(self._map_changed)
            self._map_manager.listen_error(self._update_failed)

    def _message_callback(self, message):
        if not self._ready:
            return

        if "method" in message:
            if message["method"] == "properties_changed" and "params" in message:
                params = []
                map_params = []
                for param in message["params"]:
                    properties = [prop for prop in DreameVacuumProperty]
                    for prop in properties:
                        if prop in self.property_mapping:
                            mapping = self.property_mapping[prop]
                            if (
                                "aiid" not in mapping
                                and param["siid"] == mapping["siid"]
                                and param["piid"] == mapping["piid"]
                            ):
                                if prop in self._default_properties:
                                    param["did"] = str(prop.value)
                                    param["code"] = 0
                                    params.append(param)
                                else:
                                    if (
                                        prop is DreameVacuumProperty.OBJECT_NAME
                                        or prop is DreameVacuumProperty.MAP_DATA
                                        or prop is DreameVacuumProperty.ROBOT_TIME
                                        or prop is DreameVacuumProperty.OLD_MAP_DATA
                                    ):
                                        map_params.append(param)
                                break

                if len(map_params) and self._map_manager:
                    self._map_manager.handle_properties(map_params)

                self._handle_properties(params)

    def _handle_properties(self, properties) -> bool:
        changed = False
        callbacks = []
        for prop in properties:
            if not isinstance(prop, dict):
                continue
            did = int(prop["did"])
            if prop["code"] == 0 and "value" in prop:
                value = prop["value"]
                if did in self._dirty_data:
                    if self._dirty_data[did] != value:
                        _LOGGER.info(
                            "Property %s Value Discarded: %s <- %s",
                            DreameVacuumProperty(did).name,
                            self._dirty_data[did],
                            value,
                        )
                    del self._dirty_data[did]
                    continue

                if self.data.get(did, None) != value:
                    # Do not call external listener when map properties changed
                    if (
                        did is not DreameVacuumProperty.MAP_LIST.value
                        and did is not DreameVacuumProperty.RECOVERY_MAP_LIST.value
                        and did is not DreameVacuumProperty.MAP_DATA.value
                        and did is not DreameVacuumProperty.OBJECT_NAME.value
                    ):
                        changed = True
                    current_value = self.data.get(did)
                    if (
                        did is not DreameVacuumProperty.AUTO_SWITCH_SETTINGS.value
                        and did is not DreameVacuumProperty.AI_DETECTION.value
                        and did is not DreameVacuumProperty.MAP_LIST.value
                        and did is not DreameVacuumProperty.SERIAL_NUMBER.value
                    ):
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
                            callbacks.append([callback, current_value])
            else:
                _LOGGER.debug(
                    "Property %s Not Available", DreameVacuumProperty(did).name
                )

        if not self._ready:
            self.capability.refresh()
            if (
                not self.capability.mopping_after_sweeping
                and CLEANING_MODE_MOPPING_AFTER_SWEEPING
                in self.status.cleaning_mode_list
            ):
                self.status.cleaning_mode_list.pop(CLEANING_MODE_MOPPING_AFTER_SWEEPING)

            self.status.segment_cleaning_mode_list = (
                self.status.cleaning_mode_list.copy()
            )
            if (
                CLEANING_MODE_MOPPING_AFTER_SWEEPING
                in self.status.segment_cleaning_mode_list
            ):
                self.status.segment_cleaning_mode_list.pop(
                    CLEANING_MODE_MOPPING_AFTER_SWEEPING
                )

        for callback in callbacks:
            callback[0](callback[1])

        if changed:
            self._last_change = time.time()
            if self._ready:
                self._property_changed()
        return changed

    def _request_properties(
        self, properties: list[DreameVacuumProperty] = None
    ) -> bool:
        """Request properties from the device."""
        if not properties:
            properties = self._default_properties

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

        return self._handle_properties(results)

    def _update_status(
        self, task_status: DreameVacuumTaskStatus, status: DreameVacuumStatus
    ) -> None:
        """Update status properties on memory for map renderer to update the image before action is sent to the device."""
        if task_status is not DreameVacuumTaskStatus.COMPLETED:
            new_state = DreameVacuumState.SWEEPING
            if self.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING:
                new_state = DreameVacuumState.MOPPING
            elif (
                self.status.cleaning_mode
                is DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
            ):
                new_state = DreameVacuumState.SWEEPING_AND_MOPPING
            self._update_property(DreameVacuumProperty.STATE, new_state.value)

        self._update_property(DreameVacuumProperty.STATUS, status.value)
        self._update_property(DreameVacuumProperty.TASK_STATUS, task_status.value)

    def _update_property(self, prop: DreameVacuumProperty, value: Any) -> Any:
        """Update device property on memory and notify listeners."""
        if prop in self.property_mapping:
            current_value = self.get_property(prop)
            if current_value != value:
                if not (
                    prop is DreameVacuumProperty.STATE
                    or prop is DreameVacuumProperty.STATUS
                    or prop is DreameVacuumProperty.TASK_STATUS
                    or prop is DreameVacuumProperty.AUTO_EMPTY_STATUS
                    or prop is DreameVacuumProperty.ERROR
                    or prop is DreameVacuumProperty.SELF_WASH_BASE_STATUS
                    or prop is DreameVacuumProperty.AUTO_SWITCH_SETTINGS
                    or prop is DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS
                    or prop is DreameVacuumProperty.AI_DETECTION
                    or prop is DreameVacuumProperty.SHORTCUTS
                ):
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
                        self._map_manager.set_map_list_object_name(
                            object_name, map_list.get("md5")
                        )
                    else:
                        self._last_map_list_request = 0
                except:
                    pass

    def _recovery_map_list_changed(
        self, previous_recovery_map_list: Any = None
    ) -> None:
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

    def _cleaning_mode_changed(self, previous_cleaning_mode: Any = None) -> None:
        value = self.get_property(DreameVacuumProperty.CLEANING_MODE)
        new_cleaning_mode = None
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(
                value, self.capability.mop_pad_lifting
            )
            if values and len(values) == 3:
                if self.status.self_clean_area != values[1] and values[1]:
                    self.status.previous_self_clean_area = values[1]
                self.status.self_clean_area = values[1]
                if values[2] <= 0 and self.status.water_volume:
                    values[2] = self.status.water_volume.value
                if (
                    values[2] is not None
                    and values[2] in DreameVacuumMopPadHumidity._value2member_map_
                ):
                    self.status.mop_pad_humidity = DreameVacuumMopPadHumidity(values[2])
                else:
                    self.status.mop_pad_humidity = DreameVacuumMopPadHumidity.UNKNOWN
                if values[0] == 3:
                    new_cleaning_mode = DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
                elif not self.capability.mop_pad_lifting:
                    if not self.status.water_tank_or_mop_installed:
                        new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING
                    elif values[0] == 1:
                        new_cleaning_mode = DreameVacuumCleaningMode.MOPPING
                    else:
                        new_cleaning_mode = (
                            DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                        )
                else:
                    if values[0] == 2:
                        new_cleaning_mode = DreameVacuumCleaningMode.SWEEPING
                    elif values[0] == 0:
                        new_cleaning_mode = (
                            DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                        )
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

        self.status.cleaning_mode = new_cleaning_mode

    def _water_tank_changed(self, previous_water_tank: Any = None) -> None:
        """Update cleaning mode on device when water tank status is changed."""
        # App does not allow you to update cleaning mode when water tank or mop pad is not installed.
        if self.get_property(DreameVacuumProperty.CLEANING_MODE) is not None:
            new_list = CLEANING_MODE_CODE_TO_NAME.copy()
            if not self.capability.mopping_after_sweeping or (
                self.status.started
                and self.status.cleaning_mode
                is not DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
            ):
                new_list.pop(DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING)

            if not self.status.auto_mount_mop:  # or not self.status.mop_in_station:
                if not self.status.water_tank_or_mop_installed:
                    new_list.pop(DreameVacuumCleaningMode.MOPPING)
                    new_list.pop(DreameVacuumCleaningMode.SWEEPING_AND_MOPPING)
                    if (
                        self.status.cleaning_mode
                        is not DreameVacuumCleaningMode.SWEEPING
                    ):
                        # Store current cleaning mode for future use when water tank is reinstalled
                        self._previous_cleaning_mode = self.status.cleaning_mode
                        if self._ready and not self.status.scheduled_clean:
                            self._update_cleaning_mode(
                                DreameVacuumCleaningMode.SWEEPING.value
                            )
                else:
                    if not self.capability.mop_pad_lifting:
                        new_list.pop(DreameVacuumCleaningMode.SWEEPING)

                        if self.status.sweeping:
                            if self._ready and not self.status.scheduled_clean:
                                if (
                                    self._previous_cleaning_mode is not None
                                    and self._previous_cleaning_mode
                                    is not DreameVacuumCleaningMode.SWEEPING
                                ):
                                    self._update_cleaning_mode(
                                        self._previous_cleaning_mode.value
                                    )
                                else:
                                    self._update_cleaning_mode(
                                        DreameVacuumCleaningMode.SWEEPING_AND_MOPPING.value
                                    )
                            # Store current cleaning mode for future use when water tank is removed
                            self._previous_cleaning_mode = self.status.cleaning_mode

            self.status.cleaning_mode_list = {v: k for k, v in new_list.items()}

    def _task_status_changed(self, previous_task_status: Any = None) -> None:
        """Task status is a very important property and must be listened to trigger necessary actions when a task started or ended"""
        if self.capability.mopping_after_sweeping:
            if self.status.started:
                if (
                    self.status.cleaning_mode
                    is not DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
                    and CLEANING_MODE_MOPPING_AFTER_SWEEPING
                    in self.status.cleaning_mode_list
                ):
                    self.status.cleaning_mode_list.pop(
                        CLEANING_MODE_MOPPING_AFTER_SWEEPING
                    )
                    self._property_changed()
            elif (
                CLEANING_MODE_MOPPING_AFTER_SWEEPING
                not in self.status.cleaning_mode_list
            ):
                self.status.cleaning_mode_list[
                    CLEANING_MODE_MOPPING_AFTER_SWEEPING
                ] = DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
                self._property_changed()

        if previous_task_status is not None:
            if previous_task_status in DreameVacuumTaskStatus._value2member_map_:
                previous_task_status = DreameVacuumTaskStatus(previous_task_status)

            task_status = self.get_property(DreameVacuumProperty.TASK_STATUS)
            if task_status in DreameVacuumTaskStatus._value2member_map_:
                task_status = DreameVacuumTaskStatus(task_status)

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
                    task_status is DreameVacuumTaskStatus.CRUISING_PATH
                    or task_status is DreameVacuumTaskStatus.CRUISING_POINT
                    or self.status.go_to_zone
                ):
                    self.cleanup_completed = False
                    if self._map_manager is not None:
                        # Get the new map list from cloud
                        self._map_manager.editor.set_cruise_points([])
                        self._map_manager.request_next_map_list()
                    self._cleaning_history_update = time.time()
                else:
                    if previous_task_status is DreameVacuumTaskStatus.FAST_MAPPING:
                        # as implemented on the app
                        self._update_property(DreameVacuumProperty.CLEANING_TIME, 0)
                        self.cleanup_completed = False
                        if self._map_manager is not None:
                            # Mapping is completed, get the new map list from cloud
                            self._map_manager.request_next_map_list()
                    elif self.cleanup_completed is not None:
                        self.cleanup_completed = True
                        self._cleaning_history_update = time.time()
            else:
                self.cleanup_completed = (
                    None if self.status.fast_mapping or self.status.cruising else False
                )

            if self.status.go_to_zone is not None and not (
                task_status is DreameVacuumTaskStatus.ZONE_CLEANING
                or task_status is DreameVacuumTaskStatus.ZONE_CLEANING_PAUSED
                or task_status is DreameVacuumTaskStatus.ZONE_MOPPING_PAUSED
                or task_status is DreameVacuumTaskStatus.ZONE_DOCKING_PAUSED
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT_PAUSED
            ):
                self._restore_go_to_zone()

            self._map_property_changed(previous_task_status)

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

    def _status_changed(self, previous_status: Any = None) -> None:
        if previous_status is not None:
            if previous_status in DreameVacuumStatus._value2member_map_:
                previous_status = DreameVacuumStatus(previous_status)

            status = self.get_property(DreameVacuumProperty.STATUS)
            if (
                self._remote_control
                and status is not DreameVacuumStatus.REMOTE_CONTROL.value
                and previous_status is not DreameVacuumStatus.REMOTE_CONTROL.value
            ):
                self._remote_control = False

            if (
                not self.capability.cruising
                and status == DreameVacuumStatus.BACK_HOME
                and previous_status == DreameVacuumStatus.ZONE_CLEANING
                and self.status.started
            ):
                self.status.go_to_zone.stop = True
                self._restore_go_to_zone(True)

            if (
                status is DreameVacuumStatus.CHARGING.value
                and previous_status is DreameVacuumStatus.BACK_HOME.value
            ):
                self._cleaning_history_update = time.time()

            if previous_status is DreameVacuumStatus.OTA.value:
                self._ready = False
                self.connect_device()

        self._map_property_changed(previous_status)

    def _charging_status_changed(self, previous_charging_status: Any = None) -> None:
        self._remote_control = False
        self._map_property_changed(previous_charging_status)

    def _ai_obstacle_detection_changed(
        self, previous_ai_obstacle_detection: Any = None
    ) -> None:
        """AI Detection property returns multiple values as json or int this function parses and sets the sub properties to memory"""
        ai_value = self.get_property(DreameVacuumProperty.AI_DETECTION)
        if isinstance(ai_value, str):
            settings = json.loads(ai_value)
            if settings and self.ai_data is None:
                self.ai_data = {}

            for prop in DreameVacuumStrAIProperty:
                if prop.value in settings:
                    value = settings[prop.value]
                    current_value = self.ai_data.get(prop.name)
                    if current_value != value:
                        if current_value is not None:
                            _LOGGER.info(
                                "AI Property %s Changed: %s -> %s",
                                prop.name,
                                current_value,
                                value,
                            )
                        else:
                            _LOGGER.info("AI Property %s Added: %s", prop.name, value)
                        self.ai_data[prop.name] = value
        elif isinstance(ai_value, int):
            if self.ai_data is None:
                self.ai_data = {}

            for prop in DreameVacuumAIProperty:
                bit = int(prop.value)
                value = (ai_value & bit) == bit
                current_value = self.ai_data.get(prop.name)
                if current_value != value:
                    if current_value is not None:
                        _LOGGER.info(
                            "Property %s Changed: %s -> %s",
                            prop.name,
                            current_value,
                            value,
                        )
                    else:
                        _LOGGER.info("Property %s Added: %s", prop.name, value)
                    self.ai_data[prop.name] = value

        self.status.ai_policy_accepted = bool(
            self.status.ai_policy_accepted
            or self.status.ai_obstacle_detection
            or self.status.ai_obstacle_picture
        )

    def _auto_switch_settings_changed(
        self, previous_auto_switch_settings: Any = None
    ) -> None:
        value = self.get_property(DreameVacuumProperty.AUTO_SWITCH_SETTINGS)
        if isinstance(value, str) and len(value) > 2:
            try:
                settings = json.loads(value)
                if len(settings):
                    settings_dict = {}
                    for setting in settings:
                        settings_dict[setting["k"]] = setting["v"]

                    if settings_dict and self.auto_switch_data is None:
                        self.auto_switch_data = {}

                    for prop in DreameVacuumAutoSwitchProperty:
                        if prop.value in settings_dict:
                            value = settings_dict[prop.value]
                            current_value = self.auto_switch_data.get(prop.name)
                            if current_value != value:
                                if current_value is not None:
                                    _LOGGER.info(
                                        "Property %s Changed: %s -> %s",
                                        prop.name,
                                        current_value,
                                        value,
                                    )
                                else:
                                    _LOGGER.info(
                                        "Property %s Added: %s", prop.name, value
                                    )
                                self.auto_switch_data[prop.name] = value
            except:
                pass

    def _dnd_task_changed(self, previous_dnd_task: Any = None) -> None:
        dnd_tasks = self.get_property(DreameVacuumProperty.DND_TASK)
        if dnd_tasks and dnd_tasks != "":
            self.status.dnd_tasks = json.loads(dnd_tasks)

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
                                self.status.stream_status = (
                                    DreameVacuumStreamStatus.VIDEO
                                )
                            elif (
                                operation == "intercom" or operation_type == "intercom"
                            ):
                                self.status.stream_status = (
                                    DreameVacuumStreamStatus.AUDIO
                                )
                            elif (
                                operation == "recordVideo"
                                or operation_type == "recordVideo"
                            ):
                                self.status.stream_status = (
                                    DreameVacuumStreamStatus.RECORDING
                                )

    def _shortcuts_changed(self, previous_shortcuts: Any = None) -> None:
        shortcuts = self.get_property(DreameVacuumProperty.SHORTCUTS)
        if shortcuts and shortcuts != "":
            shortcuts = json.loads(shortcuts)
            if shortcuts:
                # response = self.call_shortcut_action("GET_COMMANDS")
                new_shortcuts = {}
                for shortcut in shortcuts:
                    id = shortcut["id"]
                    running = (
                        False
                        if "state" not in shortcut
                        else bool(shortcut["state"] == "0" or shortcut["state"] == "1")
                    )
                    name = base64.decodebytes(shortcut["name"].encode("utf8")).decode(
                        "utf-8"
                    )
                    tasks = None
                    # response = self.call_shortcut_action("GET_COMMAND_BY_ID", {"id": id})
                    # if response and "out" in response:
                    #    data = response["out"]
                    #    if data and len(data):
                    #        if "value" in data[0] and data[0]["value"] != "":
                    #            tasks = []
                    #            for task in json.loads(data[0]["value"]):
                    #                segments = []
                    #                for segment in task:
                    #                    segments.append(ShortcutTask(segment_id=segment[0], suction_level=segment[1], water_volume=segment[2], cleaning_times=segment[3], cleaning_mode=segment[4]))
                    #                tasks.append(segments)
                    new_shortcuts[id] = Shortcut(
                        id=id, name=name, running=running, tasks=tasks
                    )
                self.status.shortcuts = new_shortcuts

    def _voice_assistant_language_changed(
        self, previous_voice_assistant_language: Any = None
    ) -> None:
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

    def _self_wash_base_status_changed(
        self, previous_self_wash_base_status: Any = None
    ) -> None:
        if previous_self_wash_base_status is not None:
            if (
                bool(
                    self.status.started
                    and previous_self_wash_base_status
                    == DreameVacuumSelfWashBaseStatus.WASHING.value
                    or previous_self_wash_base_status
                    == DreameVacuumSelfWashBaseStatus.CLEAN_ADD_WATER.value
                )
                != self.status.washing
            ):
                self._consumable_change = True

            self._map_property_changed(previous_self_wash_base_status)

    def _suction_level_changed(self, previous_suction_level: Any = None) -> None:
        if previous_suction_level is not None and self.status.go_to_zone:
            self.status.go_to_zone.suction_level = None

    def _water_volume_changed(self, previous_water_volume: Any = None) -> None:
        if previous_water_volume is not None and self.status.go_to_zone:
            self.status.go_to_zone.water_volume = None

    def _error_changed(self, previous_error: Any = None) -> None:
        if (
            previous_error is not None
            and self.status.go_to_zone
            and self.status.has_error
        ):
            self._restore_go_to_zone(True)

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

            _LOGGER.debug("Get Cleaning History")
            try:
                # Limit the results
                start = None
                total = self.get_property(DreameVacuumProperty.CLEANING_COUNT)
                if total > 0:
                    start = self.get_property(DreameVacuumProperty.FIRST_CLEANING_DATE)

                if start is None:
                    start = int(time.time())
                if total is None:
                    total = 5
                limit = 40
                if total < 20:
                    limit = total + 20

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
                            json.loads(
                                data["history"] if "history" in data else data["value"]
                            ),
                            self.property_mapping,
                        )
                        if (
                            history_size > 0
                            and cleaning_history[-1].date == history.date
                        ):
                            continue
                        cleaning_history.append(history)
                        history_size = history_size + 1
                        if history_size >= 20 or history_size >= total:
                            break

                    if self.status._cleaning_history != cleaning_history:
                        _LOGGER.debug("Cleaning History Changed")
                        self.status._cleaning_history = cleaning_history
                        if cleaning_history:
                            self.status._last_cleaning_time = cleaning_history[
                                0
                            ].date.replace(tzinfo=datetime.now().astimezone().tzinfo)
                        changed = True
                        if self._ready:
                            self._property_changed()

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
                                json.loads(
                                    data["history"]
                                    if "history" in data
                                    else data["value"]
                                ),
                                self.property_mapping,
                            )
                            if (
                                history_size > 0
                                and cruising_history[-1].date == history.date
                            ):
                                continue
                            cruising_history.append(history)
                            history_size = history_size + 1
                            if history_size >= 20 or history_size >= total:
                                break

                        if self.status._cruising_history != cruising_history:
                            _LOGGER.debug("Cruising History Changed")
                            self.status._cruising_history = cruising_history
                            if cruising_history:
                                self.status._last_cruising_time = cruising_history[
                                    0
                                ].date.replace(
                                    tzinfo=datetime.now().astimezone().tzinfo
                                )
                            changed = True

                if self._ready and changed:
                    self._property_changed()

            except Exception as ex:
                _LOGGER.warning("Get Cleaning History failed!: %s", ex)

    def _property_changed(self) -> None:
        """Call external listener when a property changed"""
        if self._update_callback:
            _LOGGER.debug("Update Callback")
            self._update_callback()

    def _map_changed(self) -> None:
        """Call external listener when a map changed"""
        map_data = self.status.current_map
        if map_data and self.status.started:
            if (
                self.status.go_to_zone is None
                and not self.status._capability.cruising
                and self.status.zone_cleaning
            ):
                if map_data.active_areas and len(map_data.active_areas) == 1:
                    area = map_data.active_areas[0]
                    size = map_data.dimensions.grid_size
                    if area.check_size(size):
                        new_cleaning_mode = None
                        if not (
                            self.capability.self_wash_base
                            or self.capability.mop_pad_lifting
                        ):
                            if (
                                self.status.cleaning_mode
                                == DreameVacuumCleaningMode.MOPPING
                                and not self.status.water_tank_or_mop_installed
                            ):
                                new_cleaning_mode = (
                                    DreameVacuumCleaningMode.SWEEPING.value
                                )
                            elif (
                                self.status.cleaning_mode
                                == DreameVacuumCleaningMode.SWEEPING
                                and self.status.water_tank_or_mop_installed
                            ):
                                new_cleaning_mode = (
                                    DreameVacuumCleaningMode.MOPPING_AND_SWEEPING.value
                                )

                        size = int(map_data.dimensions.grid_size / 2)
                        self.status.go_to_zone = GoToZoneSettings(
                            x=area.x0 + size,
                            y=area.y0 + size,
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
                self.schedule_update(0.01, True)

        if self._map_manager.ready:
            self._property_changed()

    def _update_failed(self, ex) -> None:
        """Call external listener when update failed"""
        if self._error_callback:
            self._error_callback(ex)

    def _action_update_task(self) -> None:
        self._update_task(True)

    def _update_task(self, from_action=False) -> None:
        """Timer task for updating properties periodically"""
        self._update_timer = None

        try:
            self.update(from_action)
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

        self.schedule_update(self._update_interval)

    def _update_cleaning_mode(self, cleaning_mode) -> int:
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(
                self.get_property(DreameVacuumProperty.CLEANING_MODE),
                self.capability.mop_pad_lifting,
            )
            if not(values and len(values) == 3):                
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

    def _update_self_clean_area(self, self_clean_area) -> int:
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(
                self.get_property(DreameVacuumProperty.CLEANING_MODE),
                self.capability.mop_pad_lifting,
            )
            if values and len(values) == 3:
                values[1] = self_clean_area
                return self.set_property(
                    DreameVacuumProperty.CLEANING_MODE, self_clean_area
                )
        return False

    def _update_water_level(self, water_level) -> int:
        if self.capability.self_wash_base:
            values = DreameVacuumDevice.split_group_value(
                self.get_property(DreameVacuumProperty.CLEANING_MODE),
                self.capability.mop_pad_lifting,
            )
            if values and len(values) == 3:
                values[2] = water_level
                if self.set_property(
                    DreameVacuumProperty.CLEANING_MODE,
                    DreameVacuumDevice.combine_group_value(values),
                ):
                    return self.set_property(
                        DreameVacuumProperty.WATER_VOLUME, int(water_level)
                    )
            return False
        else:
            return self.set_property(
                DreameVacuumProperty.WATER_VOLUME, int(water_level)
            )

    def _update_suction_level(self, suction_level) -> int:
        return self.set_property(DreameVacuumProperty.SUCTION_LEVEL, int(suction_level))

    def _set_go_to_zone(self, x, y, size):
        current_cleaning_mode = int(self.status.cleaning_mode.value)
        current_suction_level = int(self.status.suction_level.value)
        current_water_level = int(
            self.status.mop_pad_humidity.value
            if self.capability.self_wash_base
            else self.status.water_volume.value
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
                        if area.check_point(
                            x, y, self.status.current_map.dimensions.grid_size
                        ):
                            cleaning_mode = DreameVacuumCleaningMode.SWEEPING.value
                            break

            if current_cleaning_mode != cleaning_mode:
                new_cleaning_mode = cleaning_mode
            else:
                if (
                    current_cleaning_mode is DreameVacuumCleaningMode.MOPPING.value
                    and not self.status.water_tank_or_mop_installed
                ):
                    current_cleaning_mode = DreameVacuumCleaningMode.SWEEPING.value
                elif (
                    current_cleaning_mode is DreameVacuumCleaningMode.SWEEPING.value
                    and self.status.water_tank_or_mop_installed
                ):
                    current_cleaning_mode = (
                        DreameVacuumCleaningMode.SWEEPING_AND_MOPPING.value
                    )
                else:
                    current_cleaning_mode = None

            if current_water_level != DreameVacuumWaterVolume.LOW.value:
                new_water_level = DreameVacuumWaterVolume.LOW.value
            else:
                current_water_level = None

            current_suction_level = None

        if new_suction_level is not None:
            self._update_suction_level(new_suction_level)

        if new_water_level is not None:
            self._update_water_level(new_water_level)

        if new_cleaning_mode is not None:
            self._update_cleaning_mode(new_cleaning_mode)

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

                if (
                    cleaning_mode is not None
                    and self.status.cleaning_mode.value != cleaning_mode
                ):
                    self._update_cleaning_mode(cleaning_mode)
                if (
                    suction_level is not None
                    and self.status.suction_level.value != suction_level
                ):
                    self._update_suction_level(suction_level)
                if (
                    water_level is not None
                    and self.status.water_volume.value != water_level
                ):
                    self._update_water_level(water_level)

                if stop and self.status.started:
                    self._update_status(
                        DreameVacuumTaskStatus.COMPLETED, DreameVacuumStatus.STANDBY
                    )

                self.schedule_update(3, True)
            else:
                self.status.go_to_zone = None

    @staticmethod
    def split_group_value(value: int, mop_pad_lifting: bool = False) -> list[int]:
        if value is not None:
            value_list = []
            value_list.append((value & 3) if mop_pad_lifting else (value & 1))
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
        info = self._protocol.connect(self._message_callback)
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
            self._request_properties()
            self._last_update_failed = None

            if (
                self.device_connected
                and self._protocol.cloud is not None
                and (not self._ready or not self.available)
            ):
                if self._map_manager:
                    model = self.info.model.split(".")
                    if len(model) == 3:
                        for k, v in json.loads(
                            zlib.decompress(
                                base64.b64decode(DEVICE_KEY), zlib.MAX_WBITS | 32
                            )
                        ).items():
                            if model[2] in v:
                                self._map_manager.set_aes_iv(k)
                                break

                    if not self.capability.lidar_navigation:
                        self._map_manager.set_vslam_map()
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
                    if (
                        self.capability.ai_detection
                        and not self.status.ai_policy_accepted
                    ) or True:
                        try:
                            prop = "prop.s_ai_config"
                            response = self._protocol.cloud.get_batch_device_datas(
                                [prop]
                            )
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
            elif self._protocol.cloud.logged_in:
                if self.two_factor_url:
                    self.two_factor_url = None
                    self._property_changed()

                if self._protocol.connected:
                    self._map_manager.schedule_update(5)

                self.token, self.host = self._protocol.cloud.get_info(self.mac)
                if not self._protocol.dreame_cloud:
                    self._protocol.set_credentials(
                        self.host, self.token, self.mac, self.account_type
                    )

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

    def schedule_update(self, wait: float = None, from_action=False) -> None:
        """Schedule a device update for future"""
        if not wait:
            wait = self._update_interval

        if self._update_timer is not None:
            self._update_timer.cancel()
            del self._update_timer
            self._update_timer = None

        if wait >= 0:
            self._update_timer = Timer(
                wait, self._action_update_task if from_action else self._update_task
            )
            self._update_timer.start()

    def get_property(
        self,
        prop: DreameVacuumProperty
        | DreameVacuumAutoSwitchProperty
        | DreameVacuumStrAIProperty
        | DreameVacuumAIProperty,
    ) -> Any:
        """Get a device property from memory"""
        if isinstance(prop, DreameVacuumAutoSwitchProperty):
            return self.get_auto_switch_property(prop)
        if isinstance(prop, DreameVacuumStrAIProperty) or isinstance(
            prop, DreameVacuumAIProperty
        ):
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

    def get_ai_property(
        self, prop: DreameVacuumStrAIProperty | DreameVacuumAIProperty
    ) -> bool:
        """Get a device AI property from memory"""
        if self.capability.ai_detection and self.ai_data:
            if prop is not None and prop.name in self.ai_data:
                return bool(self.ai_data[prop.name])
        return None

    def set_property(
        self,
        prop: DreameVacuumProperty
        | DreameVacuumAutoSwitchProperty
        | DreameVacuumStrAIProperty
        | DreameVacuumAIProperty,
        value: Any,
    ) -> bool:
        """Sets property value using the existing property mapping and notify listeners
        Property must be set on memory first and notify its listeners because device does not return new value immediately.
        """
        if value is None:
            return False

        if isinstance(prop, DreameVacuumAutoSwitchProperty):
            return self.set_auto_switch_property(prop, value)
        if isinstance(prop, DreameVacuumStrAIProperty) or isinstance(
            prop, DreameVacuumAIProperty
        ):
            return self.set_ai_property(prop, value)

        self.schedule_update(10)
        current_value = self._update_property(prop, value)
        if current_value is not None:
            self._last_change = time.time()
            self._last_settings_request = 0

            try:
                mapping = self.property_mapping[prop]
                result = self._protocol.set_property(
                    mapping["siid"], mapping["piid"], value
                )

                if result is None or result[0]["code"] != 0:
                    _LOGGER.error(
                        "Property not updated: %s: %s -> %s", prop, current_value, value
                    )
                    self._update_property(prop, current_value)
                    if prop.value in self._dirty_data:
                        del self._dirty_data[prop.value]
                else:
                    _LOGGER.info(
                        "Update Property: %s: %s -> %s", prop, current_value, value
                    )

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
                    "Set property failed %s: %s", prop.name, ex
                ) from None

        self.schedule_update(1)
        return False

    def get_map_for_render(
        self, map_index: int, wifi_map: bool = False
    ) -> MapData | None:
        """Makes changes on map data for device related properties for renderer.
        Map manager does not need any device property for parsing and storing map data but map renderer does.
        For example if device is running but not mopping renderer does not show no mopping areas and this function handles that so renderer does not need device data too.
        """
        map_data = self.get_map(map_index)
        if map_data and wifi_map:
            map_data = map_data.wifi_map_data

        if map_data:
            if map_data.need_optimization:
                map_data = self._map_manager.optimizer.optimize(
                    map_data,
                    self._map_manager.selected_map
                    if map_data.saved_map_status == 2
                    else None,
                )
                map_data.need_optimization = False

            map_data = copy.deepcopy(map_data)
            map_data.data = None

            if map_data.optimized_pixel_type is not None:
                map_data.pixel_type = map_data.optimized_pixel_type
                map_data.dimensions = map_data.optimized_dimensions
                if map_data.optimized_charger_position is not None:
                    map_data.charger_position = map_data.optimized_charger_position

                # if not self.status.started and map_data.docked and map_data.robot_position and map_data.charger_position:
                #    map_data.charger_position = copy.deepcopy(map_data.robot_position)

            if map_data.wifi_map:
                return map_data

            if self.status.started and not (
                self.status.zone_cleaning or self.status.go_to_zone
            ):
                # Map data always contains last active areas
                map_data.active_areas = None

            if self.status.started and not self.status.spot_cleaning:
                # Map data always contains last active points
                map_data.active_points = None

            if not self.status.segment_cleaning:
                # Map data always contains last active segments
                map_data.active_segments = None

            if not self.status.cruising:
                # Map data always contains last active path points
                map_data.active_cruise_points = None

            if not map_data.saved_map:
                if self.status.started and (
                    self.status.sweeping or self.status.cruising
                ):
                    # App does not render no mopping areas when cleaning mode is sweeping
                    map_data.no_mopping_areas = None

                if not self.status._capability.cruising:
                    if self.status.go_to_zone:
                        map_data.active_cruise_points = {
                            1: Coordinate(
                                self.status.go_to_zone.x,
                                self.status.go_to_zone.y,
                                False,
                                0,
                            )
                        }
                        map_data.active_areas = None
                        map_data.path = None

                    if map_data.active_areas and len(map_data.active_areas) == 1:
                        area = map_data.active_areas[0]
                        if area.check_size(map_data.dimensions.grid_size):
                            if (
                                self.status.started
                                and not self.status.go_to_zone
                                and self.status.zone_cleaning
                            ):
                                map_data.active_cruise_points = {
                                    1: Coordinate(
                                        area.x0
                                        + int(map_data.dimensions.grid_size / 2),
                                        area.y0
                                        + int(map_data.dimensions.grid_size / 2),
                                        False,
                                        0,
                                    )
                                }
                            map_data.active_areas = None
                            map_data.path = None

                if not self.status.go_to_zone and (
                    (self.status.zone_cleaning and map_data.active_areas)
                    or (self.status.spot_cleaning and map_data.active_points)
                ):
                    # App does not render segments when zone or spot cleaning
                    map_data.segments = None

                # App does not render pet obstacles when pet detection turned off
                if map_data.obstacles and self.status.ai_pet_detection == 0:
                    obstacles = copy.deepcopy(map_data.obstacles)
                    for k, v in obstacles.items():
                        if v.type == ObstacleType.PET:
                            del self._map_data_queue[k]

                if map_data.furnitures and self.status.ai_furniture_detection == 0:
                    map_data.furnitures = {}

                # App adds robot position to paths as last line when map data is line to robot
                if map_data.line_to_robot and map_data.path and map_data.robot_position:
                    map_data.path.append(
                        Path(
                            map_data.robot_position.x,
                            map_data.robot_position.y,
                            PathType.LINE,
                        )
                    )

            if not self.status.customized_cleaning or self.status.cruising:
                # App does not render customized cleaning settings on saved map list
                map_data.cleanset = None

            if map_data.segments and (
                not self.status.custom_order or map_data.saved_map
            ):
                for k, v in map_data.segments.items():
                    map_data.segments[k].order = None

            # Device currently may not be docked but map data can be old and still showing when robot is docked
            map_data.docked = bool(map_data.docked or self.status.docked)

            if (
                not self.capability.lidar_navigation
                and not map_data.saved_map
                and map_data.saved_map_status == 1
                and map_data.docked
            ):
                # For correct scaling of vslam saved map
                map_data.saved_map_status = 2

            if (
                map_data.charger_position == None
                and map_data.docked
                and map_data.robot_position
                and not map_data.saved_map
            ):
                map_data.charger_position = copy.deepcopy(map_data.robot_position)
                if (
                    self.capability.robot_type != RobotType.MOPPING
                    and self.capability.robot_type != RobotType.SWEEPING_AND_MOPPING
                ):
                    map_data.charger_position.a = map_data.robot_position.a + 180

            if map_data.saved_map:
                map_data.active_areas = None
                map_data.active_points = None
                map_data.active_segments = None
                map_data.active_cruise_points = None
                map_data.walls = None
                map_data.no_go_areas = None
                map_data.no_mopping_areas = None
                map_data.pathways = None
                map_data.path = None
                map_data.obstacles = None
                map_data.cleanset = None
                map_data.carpet_pixels = None
                map_data.carpets = None
                map_data.ignored_carpets = None
                map_data.detected_carpets = None
            elif map_data.charger_position and map_data.docked:
                if not map_data.robot_position:
                    map_data.robot_position = copy.deepcopy(map_data.charger_position)

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

        if self._map_manager:
            now = time.time()
            if now - self._last_map_request > 120:
                self._last_map_request = now
                self._map_manager.set_update_interval(self._map_update_interval)
                self._map_manager.schedule_update(0.01)

    def update(self, from_action=False) -> None:
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
            DreameVacuumProperty.LOW_WATER_WARNING,
            DreameVacuumProperty.DRAINAGE_STATUS,
            DreameVacuumProperty.TASK_TYPE,
            DreameVacuumProperty.WATER_CHECK,
        ]

        now = time.time()
        if self.status.active:
            # Only changed when robot is active
            properties.extend(
                [DreameVacuumProperty.CLEANED_AREA, DreameVacuumProperty.CLEANING_TIME]
            )

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
                    DreameVacuumProperty.SENSOR_DIRTY_LEFT,
                    DreameVacuumProperty.SENSOR_DIRTY_TIME_LEFT,
                    DreameVacuumProperty.MOP_PAD_LEFT,
                    DreameVacuumProperty.MOP_PAD_TIME_LEFT,
                    DreameVacuumProperty.DETERGENT_LEFT,
                    DreameVacuumProperty.DETERGENT_TIME_LEFT,
                    DreameVacuumProperty.SILVER_ION_LEFT,
                    DreameVacuumProperty.SILVER_ION_TIME_LEFT,
                    DreameVacuumProperty.SECONDARY_FILTER_LEFT,
                    DreameVacuumProperty.SECONDARY_FILTER_TIME_LEFT,
                ]
            )

        if now - self._last_settings_request > 9.5:
            self._last_settings_request = now

            if not self._consumable_change and self.status.washing:
                properties.extend(
                    [
                        DreameVacuumProperty.DETERGENT_LEFT,
                        DreameVacuumProperty.DETERGENT_TIME_LEFT,
                    ]
                )

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
                ]
            )

            if not self.capability.dnd_task:
                properties.extend(
                    [
                        DreameVacuumProperty.DND,
                        DreameVacuumProperty.DND_START,
                        DreameVacuumProperty.DND_END,
                    ]
                )

            if not self.capability.self_wash_base:
                properties.append(DreameVacuumProperty.WATER_VOLUME)

        if (
            self._map_manager
            and not self.status.running
            and now - self._last_map_list_request > 60
        ):
            properties.extend(
                [DreameVacuumProperty.MAP_LIST, DreameVacuumProperty.RECOVERY_MAP_LIST]
            )
            self._last_map_list_request = time.time()

        if not self._protocol.dreame_cloud or from_action:
            try:
                self._request_properties(properties)
            except Exception as ex:
                self._update_running = False
                raise DeviceUpdateFailedException(ex) from None

        if self._consumable_change:
            self._consumable_change = False

        if self._map_manager:
            self._map_manager.set_update_interval(self._map_update_interval)
            self._map_manager.set_device_running(
                self.status.running, self.status.docked and not self.status.started
            )

        # Reset drainage status after 10 minutes
        if (
            self._draining_complete_time is not None
            and now - self._draining_complete_time > 600
        ):
            self._draining_complete_time = None
            if self.status.draining_complete:
                self.set_property(DreameVacuumProperty.DRAINAGE_STATUS, 0)

        if self.cloud_connected:
            self._request_cleaning_history()

        self._update_running = False

    def call_stream_audio_action(self, property: DreameVacuumProperty, parameters=None):
        return self.call_stream_action(
            DreameVacuumAction.STREAM_AUDIO, property, parameters
        )

    def call_stream_video_action(self, property: DreameVacuumProperty, parameters=None):
        return self.call_stream_action(
            DreameVacuumAction.STREAM_VIDEO, property, parameters
        )

    def call_stream_property_action(
        self, property: DreameVacuumProperty, parameters=None
    ):
        return self.call_stream_action(
            DreameVacuumAction.STREAM_PROPERTY, property, parameters
        )

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
                    "value": str(json.dumps(params, separators=(",", ":"))).replace(
                        " ", ""
                    ),
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

    def call_action(
        self, action: DreameVacuumAction, parameters: dict[str, Any] = None
    ) -> dict[str, Any] | None:
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

        if self.status.draining_complete:
            self.set_property(DreameVacuumProperty.DRAINAGE_STATUS, 0)

        map_action = bool(
            action is DreameVacuumAction.REQUEST_MAP
            or action is DreameVacuumAction.UPDATE_MAP_DATA
        )

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

        # Reset consumable on memory
        if action is DreameVacuumAction.RESET_MAIN_BRUSH:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.MAIN_BRUSH_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SIDE_BRUSH:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SIDE_BRUSH_LEFT, 100)
        elif action is DreameVacuumAction.RESET_FILTER:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.FILTER_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SENSOR:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SENSOR_DIRTY_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SECONDARY_FILTER:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SECONDARY_FILTER_LEFT, 100)
        elif action is DreameVacuumAction.RESET_MOP_PAD:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.MOP_PAD_LEFT, 100)
        elif action is DreameVacuumAction.RESET_SILVER_ION:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.SILVER_ION_LEFT, 100)
        elif action is DreameVacuumAction.RESET_DETERGENT:
            self._consumable_change = True
            self._update_property(DreameVacuumProperty.DETERGENT_LEFT, 100)
        elif action is DreameVacuumAction.START_AUTO_EMPTY:
            self._update_property(
                DreameVacuumProperty.AUTO_EMPTY_STATUS,
                DreameVacuumAutoEmptyStatus.ACTIVE.value,
            )
        elif action is DreameVacuumAction.CLEAR_WARNING:
            self._update_property(
                DreameVacuumProperty.ERROR, DreameVacuumErrorCode.NO_ERROR.value
            )

        # Update listeners
        if cleaning_action or self._consumable_change:
            self._property_changed()

        try:
            result = self._protocol.action(mapping["siid"], mapping["aiid"], parameters)
        except Exception as ex:
            _LOGGER.error("Send action failed %s: %s", action.name, ex)
            self.schedule_update(1, True)
            return

        # Schedule update for retrieving new properties after action sent
        self.schedule_update(3, bool(not map_action))

        if result and result.get("code") == 0:
            _LOGGER.info("Send action %s %s", action.name, parameters)
            self._last_change = time.time()
            if not map_action:
                self._last_settings_request = 0
        else:
            _LOGGER.error(
                "Send action failed %s (%s): %s", action.name, parameters, result
            )

        return result

    def send_command(
        self, command: str, parameters: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Send a raw command to the device. This is mostly useful when trying out
        commands which are not implemented by a given device instance. (Not likely)"""

        if command == "" or parameters is None:
            raise InvalidActionException(f"Invalid Command: ({command}).")

        self.schedule_update(10, True)
        response = self._protocol.send(command, parameters, 3)
        if response:
            _LOGGER.info("Send command response: %s", response)
        self.schedule_update(2, True)

    def set_suction_level(self, suction_level: int) -> bool:
        """Set suction level."""
        if self.status.cruising:
            raise InvalidActionException("Cannot set suction level when cruising")

        if self.status.started and (
            self.status.customized_cleaning
            and not (self.status.zone_cleaning or self.status.spot_cleaning)
        ):
            raise InvalidActionException(
                "Cannot set suction level when customized cleaning is enabled"
            )
        return self._update_suction_level(suction_level)

    def set_cleaning_mode(self, cleaning_mode: int) -> bool:
        """Set cleaning mode."""
        if self.status.cleaning_mode is None:
            raise InvalidActionException(
                "Cleaning mode is not supported on this device"
            )

        if self.status.cruising:
            raise InvalidActionException("Cannot set cleaning mode when cruising")

        cleaning_mode = int(cleaning_mode)
        if cleaning_mode is DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING.value and (
            not self.capability.mopping_after_sweeping
            or (
                self.status.started
                and self.status.cleaning_mode
                is not DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
            )
        ):
            raise InvalidActionException("Cannot set mopping after sweeping")

        if not self.status.auto_mount_mop:  # or not self.status.mop_in_station:
            if cleaning_mode is DreameVacuumCleaningMode.SWEEPING.value:
                if (
                    self.status.water_tank_or_mop_installed
                    and not self.capability.mop_pad_lifting
                ):
                    if self.capability.self_wash_base:
                        raise InvalidActionException(
                            "Cannot set sweeping while mop pads are installed"
                        )
                    else:
                        raise InvalidActionException(
                            "Cannot set sweeping while water tank is installed"
                        )
            elif not self.status.water_tank_or_mop_installed:
                if self.capability.self_wash_base:
                    raise InvalidActionException(
                        "Cannot set mopping while mop pads are not installed"
                    )
                else:
                    raise InvalidActionException(
                        "Cannot set mopping while water tank is not installed"
                    )

        if not PROPERTY_AVAILABILITY[DreameVacuumProperty.CLEANING_MODE.name](self):
            raise InvalidActionException("Cleaning mode unavailable")

        return self._update_cleaning_mode(cleaning_mode)

    def set_self_clean_area(self, self_clean_area: int) -> bool:
        """Set self clean area."""
        current_self_clean_area = self.status.self_clean_area
        if self._update_self_clean_area(self_clean_area):
            if self_clean_area and self_clean_area != current_self_clean_area:
                self.status.previous_self_clean_area = self_clean_area
            return True
        return False

    def set_mop_pad_humidity(self, mop_pad_humidity: int) -> bool:
        """Set mop pad humidity."""
        if self.capability.self_wash_base:
            if self.status.cruising:
                raise InvalidActionException(
                    "Cannot set mop pad humidity when cruising"
                )

            if self.status.started and (
                self.status.customized_cleaning
                and not (self.status.zone_cleaning or self.status.spot_cleaning)
            ):
                raise InvalidActionException(
                    "Cannot set mop pad humidity when customized cleaning is enabled"
                )

            return self._update_water_level(mop_pad_humidity)
        return False

    def set_water_volume(self, water_volume: int) -> bool:
        """Set water volume."""
        if not self.capability.self_wash_base:
            if self.status.cruising:
                raise InvalidActionException("Cannot set water level when cruising")

            if self.status.started and (
                self.status.customized_cleaning
                and not (self.status.zone_cleaning or self.status.spot_cleaning)
            ):
                raise InvalidActionException(
                    "Cannot set water volume when customized cleaning is enabled"
                )

            return self._update_water_level(water_volume)
        return False

    def set_dnd_task(self, enabled: bool, dnd_start: str, dnd_end: str) -> bool:
        """Set do not disturb task"""
        if dnd_start is None or dnd_start == "":
            dnd_start = "22:00"

        if dnd_end is None or dnd_end == "":
            dnd_end = "08:00"

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
            str(json.dumps(self.status.dnd_tasks, separators=(",", ":"))).replace(
                " ", ""
            ),
        )

    def set_dnd(self, enabled: bool) -> bool:
        """Set do not disturb function"""
        enabled = bool(enabled)
        if not self.capability.dnd_task:
            return self.set_property(DreameVacuumProperty.DND, bool(enabled))
        return self.set_dnd_task(
            bool(enabled), self.status.dnd_start, self.status.dnd_end
        )

    def set_dnd_start(self, dnd_start: str) -> bool:
        """Set do not disturb function"""
        time_pattern = re.compile("([0-1][0-9]|2[0-3]):[0-5][0-9]$")
        if not re.match(time_pattern, dnd_start):
            raise InvalidValueException("DND start time is not valid: (%s).", dnd_start)

        if not self.capability.dnd_task:
            return self.set_property(DreameVacuumProperty.DND_START, dnd_start)
        return self.set_dnd_task(self.status.dnd, str(dnd_start), self.status.dnd_end)

    def set_dnd_end(self, dnd_end: str) -> bool:
        """Set do not disturb function"""
        time_pattern = re.compile("([0-1][0-9]|2[0-3]):[0-5][0-9]$")
        if not re.match(time_pattern, dnd_end):
            raise InvalidValueException("DND end time is not valid: (%s).", dnd_end)

        if not self.capability.dnd_task:
            return self.set_property(DreameVacuumProperty.DND_END, dnd_end)
        return self.set_dnd_task(self.status.dnd, self.status.dnd_start, str(dnd_end))

    def set_voice_assistant_language(self, voice_assistant_language: str) -> bool:
        if (
            self.get_property(DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE) is None
            or voice_assistant_language is None
            or len(voice_assistant_language) < 2
            or voice_assistant_language.upper()
            not in DreameVacuumVoiceAssistantLanguage.__members__
        ):
            raise InvalidActionException(
                f"Voice assistant language ({voice_assistant_language}) is not suported"
            )
        return self.set_property(
            DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE,
            DreameVacuumVoiceAssistantLanguage[voice_assistant_language.upper()],
        )

    def locate(self) -> dict[str, Any] | None:
        """Locate the vacuum cleaner."""
        return self.call_action(DreameVacuumAction.LOCATE)

    def start(self) -> dict[str, Any] | None:
        """Start or resume the cleaning task."""
        if self.status.fast_mapping_paused:
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

        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(
                "Cannot start cleaning while draining or self testing"
            )

        self.schedule_update(10, True)

        if not self.status.started:
            self._update_status(
                DreameVacuumTaskStatus.AUTO_CLEANING, DreameVacuumStatus.CLEANING
            )
        elif (
            self.status.paused
            and not self.status.cleaning_paused
            and not self.status.cruising
            and not self.status.scheduled_clean
        ):
            self._update_property(
                DreameVacuumProperty.STATUS, DreameVacuumStatus.CLEANING.value
            )
            if self.status.task_status is not DreameVacuumTaskStatus.COMPLETED:
                new_state = DreameVacuumState.SWEEPING
                if self.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING:
                    new_state = DreameVacuumState.MOPPING
                elif (
                    self.status.cleaning_mode
                    is DreameVacuumCleaningMode.SWEEPING_AND_MOPPING
                ):
                    new_state = DreameVacuumState.SWEEPING_AND_MOPPING
                self._update_property(DreameVacuumProperty.STATE, new_state.value)

        if self._map_manager:
            if not self.status.started:
                self._map_manager.editor.clear_path()
            self._map_manager.editor.refresh_map()

        return self.call_action(DreameVacuumAction.START)

    def start_custom(
        self, status, parameters: dict[str, Any] = None
    ) -> dict[str, Any] | None:
        """Start custom cleaning task."""
        if (
            not self.capability.cruising
            and status != DreameVacuumStatus.ZONE_CLEANING.value
        ):
            self._restore_go_to_zone()

        if (
            status is not DreameVacuumStatus.FAST_MAPPING.value
            and self.status.fast_mapping
        ):
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
                    "piid": PIID(
                        DreameVacuumProperty.CLEANING_PROPERTIES, self.property_mapping
                    ),
                    "value": parameters,
                }
            )

        return self.call_action(DreameVacuumAction.START_CUSTOM, payload)

    def stop(self) -> dict[str, Any] | None:
        """Stop the vacuum cleaner."""
        if self.status.fast_mapping:
            return self.return_to_base()

        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(f"Cannot stop while draining or self testing")

        self.schedule_update(10, True)

        response = None
        if self.status.go_to_zone:
            response = self.call_action(DreameVacuumAction.STOP)

        if self.status.started:
            self._update_status(
                DreameVacuumTaskStatus.COMPLETED, DreameVacuumStatus.STANDBY
            )

            # Clear active segments on current map data
            if self._map_manager:
                if self.status.go_to_zone:
                    self._map_manager.editor.set_active_areas([])
                self._map_manager.editor.set_cruise_points([])
                self._map_manager.editor.set_active_segments([])

        if response:
            return response

        return self.call_action(DreameVacuumAction.STOP)

    def pause(self) -> dict[str, Any] | None:
        """Pause the cleaning task."""
        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(f"Cannot pause while draining or self testing")

        self.schedule_update(10, True)

        if not self.status.paused and self.status.started:
            if self.status.cruising and not self.capability.cruising:
                self._update_property(
                    DreameVacuumProperty.STATE,
                    DreameVacuumState.MONITORING_PAUSED.value,
                )
            else:
                self._update_property(
                    DreameVacuumProperty.STATE, DreameVacuumState.PAUSED.value
                )
            self._update_property(
                DreameVacuumProperty.STATUS, DreameVacuumStatus.PAUSED.value
            )
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

        if self.status.started:
            if not self.status.docked:
                self._update_property(
                    DreameVacuumProperty.STATE, DreameVacuumState.RETURNING.value
                )

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
        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(
                f"Cannot start cleaning while draining or self testing"
            )

        self.schedule_update(10, True)
        if not isinstance(zones, list):
            zones = [zones]

        if suction_level is None or suction_level == "":
            suction_level = self.status.suction_level.value
        else:
            self._update_suction_level(
                suction_level[0] if isinstance(suction_level, list) else suction_level
            )

        if water_volume is None or water_volume == "":
            if self.capability.self_wash_base:
                water_volume = self.status.mop_pad_humidity.value
            else:
                water_volume = self.status.water_volume.value
        else:
            self._update_water_level(
                int(water_volume[0] if isinstance(water_volume, list) else water_volume)
            )

        if cleaning_times is None or cleaning_times == "":
            cleaning_times = 1

        cleanlist = []
        index = 0
        for zone in zones:
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
                        water = self.status.mop_pad_humidity.value
                    else:
                        water = self.status.water_volume.value
            else:
                water = water_volume

            index = index + 1

            x_coords = sorted([zone[0], zone[2]])
            y_coords = sorted([zone[1], zone[3]])

            grid_size = (
                self.status.current_map.dimensions.grid_size
                if self.status.current_map
                else 50
            )
            w = (x_coords[1] - x_coords[0]) / grid_size
            h = (y_coords[1] - y_coords[0]) / grid_size

            if h <= 1.0 or w <= 1.0:
                raise InvalidActionException(
                    f"Zone {index} is smaller than minimum zone size ({h}, {w})"
                )

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

        if not self.capability.cruising:
            self._restore_go_to_zone()
        if not self.status.started or self.status.paused:
            if self._map_manager:
                # Set active areas on current map data is implemented on the app
                if not self.status.started:
                    self._map_manager.editor.clear_path()
                self._map_manager.editor.set_active_areas(zones)

            self._update_status(
                DreameVacuumTaskStatus.ZONE_CLEANING, DreameVacuumStatus.ZONE_CLEANING
            )

        return self.start_custom(
            DreameVacuumStatus.ZONE_CLEANING.value,
            str(json.dumps({"areas": cleanlist}, separators=(",", ":"))).replace(
                " ", ""
            ),
        )

    def clean_segment(
        self,
        selected_segments: int | list[int],
        cleaning_times: int | list[int],
        suction_level: int | list[int],
        water_volume: int | list[int],
    ) -> dict[str, Any] | None:
        """Clean selected segment using id."""
        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(
                f"Cannot start cleaning while draining or self testing"
            )

        if self.status.current_map and not self.status.has_saved_map:
            raise InvalidActionException("Cannot clean segments on current map")

        self.schedule_update(10, True)
        if not isinstance(selected_segments, list):
            selected_segments = [selected_segments]

        if suction_level is None or suction_level == "":
            suction_level = self.status.suction_level.value

        if water_volume is None or water_volume == "":
            if self.capability.self_wash_base:
                water_volume = self.status.mop_pad_humidity.value
            else:
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
                    if (
                        segments
                        and segment_id in segments
                        and self.status.customized_cleaning
                    ):
                        repeat = segments[segment_id].cleaning_times
                    else:
                        repeat = 1
            else:
                repeat = cleaning_times

            if isinstance(suction_level, list):
                if index < len(suction_level):
                    fan = suction_level[index]
                elif (
                    segments
                    and segment_id in segments
                    and self.status.customized_cleaning
                ):
                    fan = segments[segment_id].suction_level
                else:
                    fan = self.status.suction_level.value
            else:
                fan = suction_level

            if isinstance(water_volume, list):
                if index < len(water_volume):
                    water = water_volume[index]
                elif (
                    segments
                    and segment_id in segments
                    and self.status.customized_cleaning
                ):
                    water = segments[segment_id].water_volume
                else:
                    if self.capability.self_wash_base:
                        water = self.status.mop_pad_humidity.value
                    else:
                        water = self.status.water_volume.value
            else:
                water = water_volume

            index = index + 1
            cleanlist.append([segment_id, max(1, repeat), fan, water, index])

        if not self.status.started or self.status.paused:
            if self._map_manager:
                if not self.status.started:
                    self._map_manager.editor.clear_path()

                # Set active segments on current map data is implemented on the app
                self._map_manager.editor.set_active_segments(selected_segments)

            self._update_status(
                DreameVacuumTaskStatus.SEGMENT_CLEANING,
                DreameVacuumStatus.SEGMENT_CLEANING,
            )

        return self.start_custom(
            DreameVacuumStatus.SEGMENT_CLEANING.value,
            str(json.dumps({"selects": cleanlist}, separators=(",", ":"))).replace(
                " ", ""
            ),
        )

    def clean_spot(
        self,
        points: list[int] | list[list[int]],
        cleaning_times: int | list[int],
        suction_level: int | list[int],
        water_volume: int | list[int],
    ) -> dict[str, Any] | None:
        """Clean 1.5 square meters area of selected points."""
        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(
                f"Cannot start cleaning while draining or self testing"
            )

        self.schedule_update(10, True)
        if not isinstance(points, list):
            points = [points]

        if suction_level is None or suction_level == "":
            suction_level = self.status.suction_level.value
        else:
            self._update_suction_level(
                suction_level[0] if isinstance(suction_level, list) else suction_level
            )

        if water_volume is None or water_volume == "":
            if self.capability.self_wash_base:
                water_volume = self.status.mop_pad_humidity.value
            else:
                water_volume = self.status.water_volume.value
        else:
            self._update_water_level(
                int(water_volume[0] if isinstance(water_volume, list) else water_volume)
            )

        if cleaning_times is None or cleaning_times == "":
            cleaning_times = 1

        if len(points) == 0:
            if self.status.current_map and self.status.current_map.robot_position:
                points = [
                    self.status.current_map.robot_position.x,
                    self.status.current_map.robot_position.y,
                ]
            else:
                points = [0, 0]

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
                        water = self.status.mop_pad_humidity.value
                    else:
                        water = self.status.water_volume.value
            else:
                water = water_volume

            index = index + 1

            if self.status.current_map and not self.status.current_map.check_point(
                point[0], point[1]
            ):
                raise InvalidActionException(
                    f"Coordinate ({point[0]}, {point[1]}) is not inside the map"
                )

            cleanlist.append(
                [
                    int(round(point[0])),
                    int(round(point[1])),
                    repeat,
                    fan,
                    water,
                ]
            )

        if not self.status.started or self.status.paused:
            if self._map_manager:
                if not self.status.started:
                    self._map_manager.editor.clear_path()

                # Set active points on current map data is implemented on the app
                self._map_manager.editor.set_active_points(points)

            self._update_status(
                DreameVacuumTaskStatus.SPOT_CLEANING, DreameVacuumStatus.SPOT_CLEANING
            )

        return self.start_custom(
            DreameVacuumStatus.SPOT_CLEANING.value,
            str(json.dumps({"points": cleanlist}, separators=(",", ":"))).replace(
                " ", ""
            ),
        )

    def go_to(self, x, y) -> dict[str, Any] | None:
        """Go to a point and take pictures around."""
        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(
                f"Cannot go to point while draining or self testing"
            )

        if self.status.current_map and not self.status.current_map.check_point(x, y):
            raise InvalidActionException("Coordinate is not inside the map")

        if self.status.battery_level < 15:
            raise InvalidActionException(
                "Low battery capacity. Please start the robot for working after it being fully charged."
            )

        if not self.capability.cruising:
            size = (
                self.status.current_map.dimensions.grid_size
                if self.status.current_map
                else 50
            )
            if self.status.current_map and self.status.current_map.robot_position:
                position = self.status.current_map.robot_position
                if abs(x - position.x) <= size and abs(y - position.y) <= size:
                    raise InvalidActionException(
                        f"Robot is already on selected coordinate"
                    )
            self._set_go_to_zone(x, y, size)
            zone = [
                x - int(size / 2),
                y - int(size / 2),
                x + int(size / 2),
                y + int(size / 2),
            ]

        if not (self.status.started or self.status.paused):
            if self._map_manager:
                # Set active cruise points on current map data is implemented on the app
                self._map_manager.editor.set_cruise_points([[x, y, 0, 0]])

            self._update_property(
                DreameVacuumProperty.STATE, DreameVacuumState.MONITORING.value
            )
            self._update_property(
                DreameVacuumProperty.STATUS, DreameVacuumStatus.CRUISING_POINT.value
            )
            self._update_property(
                DreameVacuumProperty.TASK_STATUS,
                DreameVacuumTaskStatus.CRUISING_POINT.value,
            )

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
                str(json.dumps({"areas": [cleanlist]}, separators=(",", ":"))).replace(
                    " ", ""
                ),
            )
            if not response:
                self._restore_go_to_zone()

            return response

    def follow_path(self, points: list[int] | list[list[int]]) -> dict[str, Any] | None:
        """Start a survaliance job."""
        if not self.capability.cruising:
            raise InvalidActionException("Follow path is supported on this device")

        if self.status.stream_status != DreameVacuumStreamStatus.IDLE:
            raise InvalidActionException(
                f"Follow path only works with live camera streaming"
            )

        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(
                f"Cannot follow path while draining or self testing"
            )

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
                    raise InvalidActionException(
                        f"Coordinate ({point[0]}, {point[1]}) is not inside the map"
                    )

        path = []
        for point in points:
            path.append([int(round(point[0])), int(round(point[1])), 0, 1])

        predefined_points = []
        if self.status.current_map and self.status.current_map.predefined_points:
            for point in self.status.current_map.predefined_points.values():
                predefined_points.append(
                    [int(round(point.x)), int(round(point.y)), 0, 1]
                )

        if len(path) == 0:
            path.extend(predefined_points)

        if len(path) == 0:
            raise InvalidActionException(
                "At least one valid or saved coordinate is required"
            )

        if not self.status.started or self.status.paused:
            self._update_property(
                DreameVacuumProperty.STATE, DreameVacuumState.MONITORING.value
            )
            self._update_property(
                DreameVacuumProperty.STATUS, DreameVacuumStatus.CRUISING_PATH.value
            )
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
        if self.status.draining or self.status.self_testing:
            raise InvalidActionException(
                f"Cannot start cleaning while draining or self testing"
            )

        if not self.status.started:
            if self.status.status is DreameVacuumStatus.STANDBY:
                self._update_property(
                    DreameVacuumProperty.STATE, DreameVacuumState.IDLE.value
                )

            self._update_property(
                DreameVacuumProperty.STATUS, DreameVacuumStatus.SEGMENT_CLEANING.value
            )
            self._update_property(
                DreameVacuumProperty.TASK_STATUS,
                DreameVacuumTaskStatus.SEGMENT_CLEANING.value,
            )

        if self.status.shortcuts and shortcut_id in self.status.shortcuts:
            self.status.shortcuts[shortcut_id].running = True

        return self.start_custom(
            DreameVacuumStatus.SHORTCUT.value,
            str(shortcut_id),
        )

    def start_fast_mapping(self) -> dict[str, Any] | None:
        """Fast map."""
        self.schedule_update(10, True)
        if self.status.fast_mapping:
            return

        if self.status.battery_level < 15:
            raise InvalidActionException(
                "Low battery capacity. Please start the robot for working after it being fully charged."
            )

        if (
            not self.capability.self_wash_base
            and self.status.water_tank_or_mop_installed
            and not self.status.auto_mount_mop
        ):
            raise InvalidActionException(
                "Please make sure the mop pad is not installed before fast mapping."
            )

        self._update_status(
            DreameVacuumTaskStatus.FAST_MAPPING, DreameVacuumStatus.FAST_MAPPING
        )

        if self._map_manager:
            self._map_manager.editor.refresh_map()

        return self.start_custom(DreameVacuumStatus.FAST_MAPPING.value)

    def start_mapping(self) -> dict[str, Any] | None:
        """Create a new map by cleaning whole floor."""
        self.schedule_update(10, True)
        if self._map_manager:
            self._update_status(
                DreameVacuumTaskStatus.AUTO_CLEANING, DreameVacuumStatus.CLEANING
            )
            self._map_manager.editor.reset_map()

        return self.start_custom(DreameVacuumStatus.CLEANING.value, "3")

    def start_self_wash_base(
        self, parameters: dict[str, Any] = None
    ) -> dict[str, Any] | None:
        """Start self-wash base for cleaning or drying the mop."""
        if not self.capability.self_wash_base:
            return

        if self.info and self.info.version <= 1037:
            parameters = None

        payload = None
        if parameters is not None:
            payload = [
                {
                    "piid": PIID(
                        DreameVacuumProperty.CLEANING_PROPERTIES, self.property_mapping
                    ),
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

    def start_draining(self) -> dict[str, Any] | None:
        """Start draining water if self-wash base is present."""
        if self.status.washing_available and self.status.drying_available:
            return self.start_self_wash_base("7,1")

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
        if self.low_water:
            return self.set_property(DreameVacuumProperty.LOW_WATER_WARNING, 1)

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
                "audio": "false"
                if self._remote_control
                or self.status.status is DreameVacuumStatus.SLEEPING
                else "true",
                "random": randrange(65535),
            }
        )
        self._remote_control = True
        mapping = self.property_mapping[DreameVacuumProperty.REMOTE_CONTROL]
        return self._protocol.set_property(mapping["siid"], mapping["piid"], payload, 1)

    def install_voice_pack(
        self, lang_id: int, url: str, md5: str, size: int
    ) -> dict[str, Any] | None:
        """install a custom language pack"""
        payload = (
            '{"id":"%(lang_id)s","url":"%(url)s","md5":"%(md5)s","size":%(size)d}'
            % {"lang_id": lang_id, "url": url, "md5": md5, "size": size}
        )
        mapping = self.property_mapping[DreameVacuumProperty.VOICE_CHANGE]
        return self._protocol.set_property(mapping["siid"], mapping["piid"], payload, 3)

    def set_ai_detection(
        self, settings: dict[str, bool] | int
    ) -> dict[str, Any] | None:
        """Send ai detection parameters to the device."""
        if self.capability.ai_detection:
            if isinstance(settings, int):
                self._update_property(DreameVacuumProperty.AI_DETECTION, settings)
            else:
                self._property_changed()

            if (
                self.status.ai_obstacle_detection
                or self.status.ai_obstacle_image_upload
            ) and (self._protocol.cloud and not self.status.ai_policy_accepted):
                prop = "prop.s_ai_config"
                response = self._protocol.cloud.get_batch_device_datas([prop])
                if response and prop in response and response[prop]:
                    try:
                        self.status.ai_policy_accepted = json.loads(response[prop]).get(
                            "privacyAuthed"
                        )
                    except:
                        pass

                if not self.status.ai_policy_accepted:
                    if self.status.ai_obstacle_detection:
                        self.status.ai_obstacle_detection = False

                    if self.status.ai_obstacle_image_upload:
                        self.status.ai_obstacle_image_upload = False

                    self._property_changed()

                    raise InvalidActionException(
                        "You need to accept privacy policy from the App before enabling AI obstacle detection feature"
                    )

            mapping = self.property_mapping[DreameVacuumProperty.AI_DETECTION]
            if isinstance(settings, int):
                return self._protocol.set_property(
                    mapping["siid"], mapping["piid"], settings, 3
                )
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
            self.ai_data[prop.name] = value
            ai_value = self.get_property(DreameVacuumProperty.AI_DETECTION)
            if isinstance(ai_value, int):
                bit = DreameVacuumAIProperty[prop.name].value
                result = self.set_ai_detection(
                    (ai_value | bit) if value else (ai_value & -(bit + 1))
                )
            else:
                result = self.set_ai_detection(
                    {DreameVacuumStrAIProperty[prop.name].value: bool(value)}
                )
            if result is None or result[0]["code"] != 0:
                _LOGGER.error(
                    "AI Property not updated: %s: %s -> %s",
                    prop.name,
                    current_value,
                    value,
                )
                self.ai_data[prop.name] = current_value
                self._property_changed()
            return result

    def set_auto_switch_settings(self, settings) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            self._property_changed()
            current_settings = json.loads(
                self.get_property(DreameVacuumProperty.AUTO_SWITCH_SETTINGS)
            )
            if len(current_settings):
                for prop in current_settings:
                    if prop["k"] == settings["k"]:
                        prop["v"] = settings["v"]
                self._update_property(
                    DreameVacuumProperty.AUTO_SWITCH_SETTINGS,
                    str(json.dumps(current_settings, separators=(",", ":"))).replace(
                        " ", ""
                    ),
                )
            mapping = self.property_mapping[DreameVacuumProperty.AUTO_SWITCH_SETTINGS]
            return self._protocol.set_property(
                mapping["siid"],
                mapping["piid"],
                str(json.dumps(settings, separators=(",", ":"))).replace(" ", ""),
                1,
            )

    def set_auto_switch_property(
        self, prop: DreameVacuumAutoSwitchProperty, value: int
    ) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            if prop.name not in self.auto_switch_data:
                raise InvalidActionException("Not supported")
            current_value = self.get_auto_switch_property(prop)
            self.auto_switch_data[prop.name] = value
            result = self.set_auto_switch_settings({"k": prop.value, "v": int(value)})
            if result is None or result[0]["code"] != 0:
                _LOGGER.error(
                    "Auto Swtich Property not updated: %s: %s -> %s",
                    prop.name,
                    current_value,
                    value,
                )
                self.auto_switch_data[prop.name] = current_value
                self._property_changed()
            return result
        elif (
            self.capability.self_wash_base
            and prop == DreameVacuumAutoSwitchProperty.AUTO_DRYING
        ):
            return self.set_property(
                DreameVacuumProperty.INTELLIGENT_RECOGNITION, int(value)
            )

    def set_camera_light_brightness(self, brightness: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            if brightness < 40:
                brightness = 40
            current_value = self.status.camera_light_brightness
            self._update_property(
                DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS, str(brightness)
            )
            result = self.call_stream_property_action(
                DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS, {"value": str(brightness)}
            )
            if result is None or result.get("code") != 0:
                self._update_property(
                    DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS, str(current_value)
                )
            return result

    def set_wider_corner_coverage(self, value: int) -> dict[str, Any] | None:
        if self.capability.auto_switch_settings:
            current_value = self.get_auto_switch_property(
                DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE
            )
            if current_value is not None and current_value > 0 and value <= 0:
                value = -current_value
            return self.set_auto_switch_property(
                DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE, value
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

    def rename_shortcut(
        self, shortcut_id: int, shortcut_name: str = ""
    ) -> dict[str, Any] | None:
        """Rename a shortcut"""
        if self.status.started:
            raise InvalidActionException(
                "Cannot rename a shortcut while vacuum is running"
            )

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
                shortcut_name = base64.b64encode(shortcut_name.encode("utf-8")).decode(
                    "utf-8"
                )
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
                self._property_changed()

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
                    self._property_changed()
                return response

    def set_obstacle_ignore(
        self, x, y, obstacle_type, obstacle_ignored
    ) -> dict[str, Any] | None:
        if not self.capability.ai_detection:
            raise InvalidActionException(
                "Obstacle detection is not available on this device"
            )

        if self.status.started:
            raise InvalidActionException(
                "Cannot set obstacle ignore status while vacuum is running"
            )

        if self._map_manager and self.status.current_map:
            if not self.status.current_map.obstacles:
                raise InvalidActionException("Obstacle not found")

            if self.status.current_map.obstacles is None or (
                len(self.status.current_map.obstacles)
                and next(iter(self.status.current_map.obstacles.values())).ignore_status
                is None
            ):
                raise InvalidActionException(
                    "Obstacle ignoring is not supported on this device"
                )

            found = False
            for k, v in self.status.current_map.obstacles.items():
                if int(v.x) == int(x) and int(v.y) == int(y):
                    found = True
                    break

            if not found:
                raise InvalidActionException("Obstacle not found")

            self._map_manager.editor.set_obstacle_ignore(
                x, y, obstacle_type, obstacle_ignored
            )
        return self.update_map_data_async(
            {
                "obstacleignore": [
                    int(x),
                    int(y),
                    int(obstacle_type),
                    1 if obstacle_ignored else 0,
                ]
            }
        )

    def set_router_position(self, x, y):
        if not self.capability.wifi_map:
            raise InvalidActionException("WiFi map is not available on this device")

        if self.status.started:
            raise InvalidActionException(
                "Cannot set router position while vacuum is running"
            )

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
                    "piid": PIID(
                        DreameVacuumProperty.FRAME_INFO, self.property_mapping
                    ),
                    "value": '{"frame_type":"I"}',
                }
            ],
        )

    def update_map_data_async(self, parameters: dict[str, Any]):
        """Send update map action to the device."""
        if self._map_manager:
            self._map_manager.schedule_update(10)
            self._property_changed()
            self._last_map_request = time.time()

        parameters = [
            {
                "piid": PIID(
                    DreameVacuumProperty.MAP_EXTEND_DATA, self.property_mapping
                ),
                "value": str(json.dumps(parameters, separators=(",", ":"))).replace(
                    " ", ""
                ),
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
                else:
                    self._map_manager.request_next_map()
                    self._last_map_list_request = 0

        mapping = self.action_mapping[DreameVacuumAction.UPDATE_MAP_DATA]
        self._protocol.action_async(
            callback, mapping["siid"], mapping["aiid"], parameters
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
                    "piid": PIID(
                        DreameVacuumProperty.MAP_EXTEND_DATA, self.property_mapping
                    ),
                    "value": str(json.dumps(parameters, separators=(",", ":"))).replace(
                        " ", ""
                    ),
                }
            ],
        )

        self.schedule_update(5, True)

        if self._map_manager:
            if self._protocol.dreame_cloud:
                self._map_manager.schedule_update(3)
            else:
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
            return self.update_map_data_async({"nrism": {map_id: {"name": map_name}}})

    def set_map_rotation(
        self, rotation: int, map_id: int = None
    ) -> dict[str, Any] | None:
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
                if map_id is None:
                    map_id = self.status.selected_map.map_id
                self._map_manager.editor.set_rotation(map_id, rotation)

            if map_id is not None:
                return self.update_map_data_async({"smra": {map_id: {"ra": rotation}}})

    def set_restricted_zone(
        self, walls=[], zones=[], no_mops=[]
    ) -> dict[str, Any] | None:
        """Set restricted zones on current saved map."""
        if walls == "":
            walls = []
        if zones == "":
            zones = []
        if no_mops == "":
            no_mops = []

        if self._map_manager:
            self._map_manager.editor.set_zones(walls, zones, no_mops)
        return self.update_map_data_async(
            {"vw": {"line": walls, "rect": zones, "mop": no_mops}}
        )

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
            if not (
                self.get_property(DreameVacuumProperty.CARPET_RECOGNITION) is not None
                or self.get_property(DreameVacuumProperty.CARPET_CLEANING) is not None
            ):
                raise InvalidActionException("Carpets are not supported on this device")
        return self.update_map_data_async(
            {"cpt": {"addcpt": carpets, "nocpt": ignored_carpets}}
        )

    def set_pathway(self, pathways=[]) -> dict[str, Any] | None:
        """Set pathways on current saved map."""
        if pathways == "":
            pathways = []

        if self._map_manager:
            if self.status.current_map and not (
                self.status.current_map.pathways is not None
                or self.capability.floor_material
            ):
                raise InvalidActionException(
                    "Pathways are not supported on this device"
                )

            if self.status.current_map and not self.status.has_saved_map:
                raise InvalidActionException("Cannot edit pathways on current map")
            self._map_manager.editor.set_pathways(pathways)
        else:
            if not (
                self.get_property(DreameVacuumProperty.CARPET_RECOGNITION) is not None
                or self.get_property(DreameVacuumProperty.CARPET_CLEANING) is not None
            ):
                raise InvalidActionException(
                    "Pathways are not supported on this device"
                )
        return self.update_map_data_async({"vws": {"vwsl": pathways}})

    def set_predefined_points(self, points=[]) -> dict[str, Any] | None:
        """Set predefined points on current saved map."""
        if points == "":
            points = []

        if not self.capability.cruising:
            raise InvalidActionException(
                "Predefined points are not supported on this device"
            )

        if self.status.started:
            raise InvalidActionException(
                "Cannot set predefined points while vacuum is running"
            )

        if self.status.current_map:
            for point in points:
                if not self.status.current_map.check_point(point[0], point[1]):
                    raise InvalidActionException(
                        f"Coordinate ({point[0]}, {point[1]}) is not inside the map"
                    )

        predefined_points = []
        for point in points:
            predefined_points.append([point[0], point[1], 0, 1])

        if self._map_manager:
            if self.status.current_map and not self.status.has_saved_map:
                raise InvalidActionException(
                    "Cannot edit predefined points on current map"
                )
            self._map_manager.editor.set_predefined_points(predefined_points[:20])

        return self.update_map_data_async(
            {"spoint": predefined_points[:20], "tpoint": []}
        )

    def set_selected_map(self, map_id: int) -> dict[str, Any] | None:
        """Change currently selected map when multi floor map is enabled."""
        if self.status.multi_map:
            if self._map_manager:
                self._map_manager.editor.set_selected_map(map_id)
            return self.update_map_data_async({"sm": {}, "mapid": map_id})

    def delete_map(self, map_id: int = None) -> dict[str, Any] | None:
        """Delete a map."""
        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot delete a map when temporary map is present"
            )

        if self.status.started:
            raise InvalidActionException("Cannot delete a map while vacuum is running")

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
                    self._map_manager.selected_map
                    and map_id == self._map_manager.selected_map.map_id
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
            response = self._protocol.set_property(
                mapping["siid"],
                mapping["piid"],
                str(
                    json.dumps(
                        {"map_id": map_id, "map_url": map_url}, separators=(",", ":")
                    )
                ).replace(" ", ""),
                3,
            )

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
                    if (
                        self.capability.lidar_navigation
                        and self._map_manager.selected_map
                    ):
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

    def split_segments(
        self, map_id: int, segment: int, line: list[int]
    ) -> dict[str, Any] | None:
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
                    if (
                        self.capability.lidar_navigation
                        and self._map_manager.selected_map
                    ):
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

    def set_cleaning_sequence(
        self, cleaning_sequence: list[int]
    ) -> dict[str, Any] | None:
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
            if (
                cleaning_sequence
                and self.status.segments
                and len(cleaning_sequence) != len(self.status.segments.items())
            ):
                raise InvalidValueException("Invalid size for cleaning sequence")

            cleaning_sequence = self._map_manager.editor.set_cleaning_sequence(
                cleaning_sequence
            )

        return self.update_map_data_async({"cleanOrder": cleaning_sequence})

    def set_cleanset(self, cleanset: dict[str, list[int]]) -> dict[str, Any] | None:
        """Set customized cleaning settings on current map.
        Device will use these settings even you pass another setting for custom segment cleaning.
        """

        if self.status.has_temporary_map:
            raise InvalidActionException(
                "Cannot edit segments when temporary map is present"
            )

        if cleanset is not None:
            return self.update_map_data_async({"customeClean": cleanset})

    def set_custom_cleaning(
        self,
        segment_id: list[int],
        suction_level: list[int],
        water_volume: list[int],
        cleaning_times: list[int],
        cleaning_mode: list[int] = None,
    ) -> dict[str, Any] | None:
        """Set customized cleaning settings on current map.
        Device will use these settings even you pass another setting for custom segment cleaning.
        """

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

            segments = self.status.segments
            if segments:
                count = len(segments.items())
                if (
                    len(segment_id) != count
                    or len(suction_level) != count
                    or len(water_volume) != count
                    or len(cleaning_times) != cleaning_times
                    or (custom_cleaning_mode and len(cleaning_mode) != cleaning_mode)
                ):
                    raise InvalidActionException("Parameter count mismatch!")

            custom_cleaning = []
            index = 0
            for segment in segment_id:
                # for some reason cleanset uses different int values for water volume
                values = [
                    segment,
                    suction_level[index],
                    water_volume[index] + 1,
                    cleaning_times[index],
                ]
                if custom_cleaning_mode:
                    values.append(cleaning_mode[index])
                if segment.mopping_mode is not None:
                    values.append(segment.mopping_mode)
                custom_cleaning.append(values)
                index = index + 1

            return self.set_cleanset(custom_cleaning)

        raise InvalidActionException("Missing parameters!")

    def set_segment_name(
        self, segment_id: int, segment_type: int, custom_name: str = None
    ) -> dict[str, Any] | None:
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
                return self.update_map_data_async({"nsr": segment_info})

    def set_segment_order(self, segment_id: int, order: int) -> dict[str, Any] | None:
        """Update cleaning order of a segment on current map"""
        if (
            order is not None
            and self._map_manager
            and not self.status.has_temporary_map
        ):
            return self.update_map_data_async(
                {
                    "cleanOrder": self._map_manager.editor.set_segment_order(
                        segment_id, order
                    )
                }
            )

    def set_segment_suction_level(
        self, segment_id: int, suction_level: int
    ) -> dict[str, Any] | None:
        """Update suction level of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_suction_level(
                    segment_id, suction_level
                )
            )

    def set_segment_water_volume(
        self, segment_id: int, water_volume: int
    ) -> dict[str, Any] | None:
        """Update water volume of a segment on current map"""
        if (
            not self.capability.self_wash_base
            and self._map_manager
            and not self.status.has_temporary_map
        ):
            return self.set_cleanset(
                self._map_manager.editor.set_segment_water_volume(
                    segment_id, water_volume
                )
            )

    def set_segment_mop_pad_humidity(
        self, segment_id: int, mop_pad_humidity: int
    ) -> dict[str, Any] | None:
        """Update mop pad humidity of a segment on current map"""
        if (
            self.capability.self_wash_base
            and self._map_manager
            and not self.status.has_temporary_map
        ):
            return self.set_cleanset(
                self._map_manager.editor.set_segment_water_volume(
                    segment_id, mop_pad_humidity
                )
            )

    def set_segment_cleaning_mode(
        self, segment_id: int, cleaning_mode: int
    ) -> dict[str, Any] | None:
        """Update mop pad humidity of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_cleaning_mode(
                    segment_id, cleaning_mode
                )
            )

    def set_segment_cleaning_times(
        self, segment_id: int, cleaning_times: int
    ) -> dict[str, Any] | None:
        """Update cleaning times of a segment on current map."""
        if self.status.started:
            raise InvalidActionException(
                "Cannot set room cleaning times while vacuum is running"
            )

        if self._map_manager and not self.status.has_temporary_map:
            return self.set_cleanset(
                self._map_manager.editor.set_segment_cleaning_times(
                    segment_id, cleaning_times
                )
            )

    def set_segment_floor_material(
        self, segment_id: int, floor_material: int
    ) -> dict[str, Any] | None:
        """Update floor material of a segment on current map"""
        if self._map_manager and not self.status.has_temporary_map:
            data = {
                "nsm": self._map_manager.editor.set_segment_floor_material(
                    segment_id, floor_material
                )
            }
            if self.status.selected_map:
                data["map_id"] = self.status.selected_map.map_id
            return self.update_map_data_async(data)

    @property
    def _update_interval(self) -> float:
        """Dynamic update interval of the device for the timer."""
        now = time.time()
        if self._last_update_failed:
            return (
                5
                if now - self._last_update_failed <= 60
                else 10
                if now - self._last_update_failed <= 300
                else 30
            )
        if not -self._last_change <= 60:
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
            and self._protocol.cloud.logged_in
            and self._protocol.cloud.connected
            and (not self._protocol.prefer_cloud or self.device_connected)
        )


class DreameVacuumDeviceStatus:
    """Helper class for device status and int enum type properties.
    This class is used for determining various states of the device by its properties.
    Determined states are used by multiple validation and rendering condition checks.
    Almost of the rules are extracted from mobile app that has a similar class with same purpose.
    """

    _cleaning_history = None
    _last_cleaning_time = None
    _cruising_history = None
    _last_cruising_time = None

    suction_level_list = {v: k for k, v in SUCTION_LEVEL_CODE_TO_NAME.items()}
    water_volume_list = {v: k for k, v in WATER_VOLUME_CODE_TO_NAME.items()}
    mop_pad_humidity_list = {v: k for k, v in MOP_PAD_HUMIDITY_CODE_TO_NAME.items()}
    cleaning_mode_list = {v: k for k, v in CLEANING_MODE_CODE_TO_NAME.items()}
    carpet_sensitivity_list = {v: k for k, v in CARPET_SENSITIVITY_CODE_TO_NAME.items()}
    carpet_cleaning_list = {v: k for k, v in CARPET_CLEANING_CODE_TO_NAME.items()}
    mop_wash_level_list = {v: k for k, v in MOP_WASH_LEVEL_TO_NAME.items()}
    mopping_type_list = {v: k for k, v in MOPPING_TYPE_TO_NAME.items()}
    wider_corner_coverage_list = {
        v: k for k, v in WIDER_CORNER_COVERAGE_TO_NAME.items()
    }
    floor_material_list = {v: k for k, v in FLOOR_MATERIAL_CODE_TO_NAME.items()}
    voice_assistant_language_list = {
        v: k for k, v in VOICE_ASSISTANT_LANGUAGE_TO_NAME.items()
    }
    segment_cleaning_mode_list = {}

    cleaning_mode = None
    mop_pad_humidity = None
    self_clean_area = None
    previous_self_clean_area = 20
    ai_policy_accepted = False
    go_to_zone: GoToZoneSettings = None

    stream_status = None
    stream_session = None

    dnd_tasks = None
    shortcuts = None

    def __init__(self, device):
        self._device: DreameVacuumDevice = device

    def _get_property(self, prop: DreameVacuumProperty) -> Any:
        """Helper function for accessing a property from device"""
        return self._device.get_property(prop)

    @property
    def _capability(self) -> DeviceCapability:
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
        return MOP_PAD_HUMIDITY_CODE_TO_NAME.get(self.mop_pad_humidity, STATE_UNKNOWN)

    @property
    def cleaning_mode_name(self) -> str:
        """Return cleaning mode as string for translation."""
        return CLEANING_MODE_CODE_TO_NAME.get(self.cleaning_mode, STATE_UNKNOWN)

    @property
    def status(self) -> DreameVacuumStatus:
        """Return status of the device."""
        value = self._get_property(DreameVacuumProperty.STATUS)
        if value is not None and value in DreameVacuumStatus._value2member_map_:
            if self.go_to_zone and value == DreameVacuumStatus.ZONE_CLEANING.value:
                return DreameVacuumStatus.CRUISING_POINT
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
            if (
                value is DreameVacuumChargingStatus.CHARGING
                and self.battery_level == 100
            ):
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
        if (
            value is not None
            and value in DreameVacuumAutoEmptyStatus._value2member_map_
        ):
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
        if (
            value is not None
            and value in DreameVacuumRelocationStatus._value2member_map_
        ):
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
        if (
            value is not None
            and value in DreameVacuumSelfWashBaseStatus._value2member_map_
        ):
            return DreameVacuumSelfWashBaseStatus(value)
        if value is not None:
            _LOGGER.debug("SELF_WASH_BASE_STATUS not supported: %s", value)
        return DreameVacuumSelfWashBaseStatus.UNKNOWN

    @property
    def self_wash_base_status_name(self) -> str:
        """Return self-wash base status as string for translation."""
        return SELF_WASH_BASE_STATUS_TO_NAME.get(
            self.self_wash_base_status, STATE_UNKNOWN
        )

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
        if (
            value is not None
            and value in DreameVacuumCarpetSensitivity._value2member_map_
        ):
            return DreameVacuumCarpetSensitivity(value)
        if value is not None:
            _LOGGER.debug("CARPET_SENSITIVITY not supported: %s", value)
        return DreameVacuumCarpetSensitivity.UNKNOWN

    @property
    def carpet_sensitivity_name(self) -> str:
        """Return carpet sensitivity as string for translation."""
        return CARPET_SENSITIVITY_CODE_TO_NAME.get(
            self.carpet_sensitivity, STATE_UNKNOWN
        )

    @property
    def carpet_cleaning(self) -> DreameVacuumCarpetCleaning:
        """Return carpet cleaning of the device."""
        value = self._get_property(DreameVacuumProperty.CARPET_CLEANING)
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
                    if (
                        self.charging_status
                        is DreameVacuumChargingStatus.CHARGING_COMPLETED
                    ):
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
            if (
                value is not None
                and value in DreameVacuumMopWashLevel._value2member_map_
            ):
                return DreameVacuumMopWashLevel(value)
            if value is not None:
                _LOGGER.debug("MOP_WASH_LEVEL not supported: %s", value)
            return DreameVacuumMopWashLevel.UNKNOWN

    @property
    def mop_wash_level_name(self) -> str:
        """Return mop wash level as string for translation."""
        return MOP_WASH_LEVEL_TO_NAME.get(self.mop_wash_level, STATE_UNKNOWN)

    @property
    def mopping_type(self) -> DreameVacuumMoppingType:
        value = self._device.get_auto_switch_property(
            DreameVacuumAutoSwitchProperty.MOPPING_TYPE
        )
        if value is not None:
            if value in DreameVacuumMoppingType._value2member_map_:
                return DreameVacuumMoppingType(value)
            _LOGGER.debug("MOPPING_TYPE not supported: %s", value)
            return DreameVacuumMoppingType.UNKNOWN
        return None

    @property
    def mopping_type_name(self) -> str:
        """Return moping type as string for translation."""
        if (
            self.mopping_type is not None
            and self.mopping_type in DreameVacuumMoppingType._value2member_map_
        ):
            return MOPPING_TYPE_TO_NAME.get(
                DreameVacuumMoppingType(self.mopping_type), STATE_UNKNOWN
            )
        return STATE_UNKNOWN

    @property
    def stream_status_name(self) -> str:
        """Return camera stream status as string for translation."""
        return STREAM_STATUS_TO_NAME.get(self.stream_status, STATE_UNKNOWN)

    @property
    def wider_corner_coverage(self) -> DreameVacuumWiderCornerCoverage:
        value = self._device.get_auto_switch_property(
            DreameVacuumAutoSwitchProperty.WIDER_CORNER_COVERAGE
        )
        if value is not None and value < 0:
            value = 0
        if (
            value is not None
            and value in DreameVacuumWiderCornerCoverage._value2member_map_
        ):
            return DreameVacuumWiderCornerCoverage(value)
        if value is not None:
            _LOGGER.debug("WIDER_CORNER_COVERAGE not supported: %s", value)
        return DreameVacuumWiderCornerCoverage.UNKNOWN

    @property
    def wider_corner_coverage_name(self) -> str:
        """Return moping type as string for translation."""
        wider_corner_coverage = (
            0 if self.wider_corner_coverage == -1 else self.wider_corner_coverage
        )
        if (
            wider_corner_coverage is not None
            and wider_corner_coverage
            in DreameVacuumWiderCornerCoverage._value2member_map_
        ):
            return WIDER_CORNER_COVERAGE_TO_NAME.get(
                DreameVacuumWiderCornerCoverage(wider_corner_coverage), STATE_UNKNOWN
            )
        return STATE_UNKNOWN

    @property
    def low_water_warning(self) -> DreameVacuumLowWaterWarning:
        """Return low water warning of the device."""
        value = self._get_property(DreameVacuumProperty.LOW_WATER_WARNING)
        if (
            value is not None
            and value in DreameVacuumLowWaterWarning._value2member_map_
        ):
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
        return LOW_WATER_WARNING_CODE_TO_DESCRIPTION.get(
            self.low_water_warning, [STATE_UNKNOWN, ""]
        )

    @property
    def voice_assistant_language(self) -> DreameVacuumVoiceAssistantLanguage:
        """Return voice assistant language of the device."""
        value = self._get_property(DreameVacuumProperty.VOICE_ASSISTANT_LANGUAGE)
        if (
            value is not None
            and value in DreameVacuumVoiceAssistantLanguage._value2member_map_
        ):
            return DreameVacuumVoiceAssistantLanguage(value)
        if value is not None:
            _LOGGER.debug("VOICE_ASSISTANT_LANGUAGE not supported: %s", value)
        return DreameVacuumVoiceAssistantLanguage.DEFAULT

    @property
    def voice_assistant_language_name(self) -> str:
        """Return voice assistant language as string for translation."""
        return VOICE_ASSISTANT_LANGUAGE_TO_NAME.get(
            self.voice_assistant_language, STATE_UNKNOWN
        )

    @property
    def drainage_status(self) -> DreameVacuumDrainageStatus:
        """Return drainage status of the device."""
        value = self._get_property(DreameVacuumProperty.DRAINAGE_STATUS)
        if value is not None and value in DreameVacuumDrainageStatus._value2member_map_:
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
                (
                    self._capability.self_wash_base
                    and value == DreameVacuumErrorCode.REMOVE_MOP.value
                )
                or value == DreameVacuumErrorCode.UNKNOWN_WARNING.value
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
        if (
            self.running
            and not self.returning
            and not self.fast_mapping
            and not self.cruising
        ):
            return 1
        elif self._capability.self_wash_base and (self.washing or self.washing_paused):
            if self.has_error or self.has_warning or self.low_water:
                return 6
            if self.charging:
                return 8
            if self.sleeping:
                return 9
            if self.hot_washing:
                return 10
            return 7
        elif self.charging:
            return 2
        elif self.has_error or self.has_warning or self.low_water:
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
            and error is not DreameVacuumErrorCode.BATTERY_LOW
        )

    @property
    def has_warning(self) -> bool:
        """Returns true when a warning is present and available for dismiss."""
        error = self.error
        return bool(
            error.value > 0
            and (
                error is DreameVacuumErrorCode.REMOVE_MOP
                or error is DreameVacuumErrorCode.MOP_REMOVED_2
                or error is DreameVacuumErrorCode.CLEAN_MOP_PAD
                or error is DreameVacuumErrorCode.BLOCKED
                or error is DreameVacuumErrorCode.WATER_TANK_DRY
                or error is DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE
                or error is DreameVacuumErrorCode.MOP_PAD_STOP_ROTATE_2
                or error is DreameVacuumErrorCode.STATION_DISCONNECTED
                or error is DreameVacuumErrorCode.DUST_BAG_FULL
                or error is DreameVacuumErrorCode.UNKNOWN_WARNING
                or error is DreameVacuumErrorCode.UNKNOWN_WARNING_2
            )
        )

    @property
    def dust_collection_available(self) -> bool:
        """Returns true when robot is docked and can start auto emptying."""
        return bool(
            self._get_property(DreameVacuumProperty.DUST_COLLECTION)
            and not self.washing
            and not self.washing_paused
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
            self._capability.mop_pad_unmounting
            and self._get_property(DreameVacuumProperty.AUTO_MOUNT_MOP) == 1
        )

    @property
    def camera_light_brightness(self) -> int:
        if self._capability.stream_status:
            brightness = self._get_property(
                DreameVacuumProperty.CAMERA_LIGHT_BRIGHTNESS
            )
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
        water_tank = self.water_tank
        return bool(
            water_tank is DreameVacuumWaterTank.INSTALLED
            or water_tank is DreameVacuumWaterTank.MOP_INSTALLED
        )

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
        return bool(
            self.cleaning_mode is DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
        )

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
                state is DreameVacuumState.PAUSED
                or state is DreameVacuumState.ERROR
                or state is DreameVacuumState.IDLE
            )
        )

    @property
    def draining(self) -> bool:
        """Returns true when device has a self-wash base and draining is performing."""
        return bool(
            self._capability.drainage
            and self.drainage_status is DreameVacuumDrainageStatus.DRAINING
        )

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
    def self_testing(self) -> bool:
        """Returns true when device is self testing or water checking."""
        status = self.status
        return bool(
            status is DreameVacuumStatus.SELF_TEST
            or status is DreameVacuumStatus.WATER_CHECK
            or self.state is DreameVacuumState.WATER_CHECK
        )

    @property
    def cruising(self) -> bool:
        """Returns true when device is cruising."""
        if self._capability.cruising:
            task_status = self.task_status
            return bool(
                task_status is DreameVacuumTaskStatus.CRUISING_PATH
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT
                or task_status is DreameVacuumTaskStatus.CRUISING_PATH_PAUSED
                or task_status is DreameVacuumTaskStatus.CRUISING_POINT_PAUSED
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
        return bool(self.carpet_cleaning is DreameVacuumCarpetCleaning.AVOIDANCE)

    @property
    def mop_in_station(self) -> bool:
        """Returns true when the mop pad is in the station."""
        value = self._get_property(DreameVacuumProperty.MOP_IN_STATION)
        return bool(value == 1 or value == 4)

    @property
    def auto_add_detergent(self) -> bool:
        """Returns true when auto-add detergent feature is enabled."""
        value = self._get_property(DreameVacuumProperty.AUTO_ADD_DETERGENT)
        return bool(value == 1 or value == 3)

    @property
    def cleaning_paused(self) -> bool:
        """Returns true when device battery is too low for resuming its task and needs to be charged before continuing."""
        return bool(self._get_property(DreameVacuumProperty.CLEANING_PAUSED) > 0)

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
            and (self.status is DreameVacuumStatus.BACK_HOME or self.returning_to_wash)
        )

    @property
    def started(self) -> bool:
        """Returns true when device has an active task.
        Used for preventing updates on settings that relates to currently performing task.
        """
        return bool(
            self.task_status is not DreameVacuumTaskStatus.COMPLETED
            or self.cleaning_paused
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
            list = {}
            for history in self._cleaning_history:
                date = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(history.date.timestamp())
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
                            history.suction_level, STATE_UNKNOWN
                        )
                        .replace("_", " ")
                        .capitalize()
                    )
                if history.completed is not None:
                    list[date][ATTR_COMPLETED] = history.completed
                if history.water_tank_or_mop is not None:
                    list[date][
                        ATTR_MOP_PAD
                        if self._capability.self_wash_base
                        else ATTR_WATER_TANK
                    ] = (
                        WATER_TANK_CODE_TO_NAME.get(
                            history.water_tank_or_mop, STATE_UNKNOWN
                        )
                        .replace("_", " ")
                        .capitalize()
                    )
            return list

    @property
    def cruising_history(self) -> dict[str, Any] | None:
        """Returns the cruising history list as dict."""
        if self._cruising_history:
            list = {}
            for history in self._cruising_history:
                date = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(history.date.timestamp())
                )
                list[date] = {
                    ATTR_CRUISING_TIME: f"{history.cleaning_time} min",
                }
                if history.status is not None:
                    list[date][ATTR_STATUS] = (
                        STATUS_CODE_TO_NAME.get(history.status, STATE_UNKNOWN)
                        .replace("_", " ")
                        .capitalize()
                    )
                if history.cruise_type is not None:
                    list[date][ATTR_CRUISING_TYPE] = history.cruise_type
                if history.map_index is not None:
                    list[date][ATTR_MAP_INDEX] = history.map_index
                if history.map_name is not None and len(history.map_name) > 1:
                    list[date][ATTR_MAP_NAME] = history.map_name
                if history.completed is not None:
                    list[date][ATTR_COMPLETED] = history.completed
            return list

    @property
    def washing(self) -> bool:
        """Returns true the when device is currently performing mop washing."""
        return bool(
            self._capability.self_wash_base
            and (
                self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.WASHING
                or self.self_wash_base_status
                is DreameVacuumSelfWashBaseStatus.CLEAN_ADD_WATER
            )
        )

    @property
    def drying(self) -> bool:
        """Returns true the when device is currently performing mop drying."""
        return bool(
            self._capability.self_wash_base
            and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.DRYING
        )

    @property
    def washing_paused(self) -> bool:
        """Returns true when mop washing paused."""
        return bool(
            self._capability.self_wash_base
            and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.PAUSED
        )

    @property
    def returning_to_wash(self) -> bool:
        """Returns true when the device returning to self-wash base to wash or dry its mop."""
        return bool(
            self._capability.self_wash_base
            and self.self_wash_base_status is DreameVacuumSelfWashBaseStatus.RETURNING
            and (
                self.state is DreameVacuumState.RETURNING
                or self.state is DreameVacuumState.RETURNING_TO_WASH
            )
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
            and self.water_tank_or_mop_installed
            and not (
                self.washing
                or self.washing_paused
                or self.returning_to_wash_paused
                or self.returning_to_wash
                or self.returning
                or self.returning_paused
                or self.cleaning_paused
                or self.drying
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
            1
            if not self._capability.lidar_navigation or not self.multi_map
            else 4
            if self._capability.wifi_map
            else 3
        )

    @property
    def mapping_available(self) -> bool:
        """Returns true when creating a new map is possible."""
        return bool(
            not self.started
            and not self.fast_mapping
            and (
                not self._device.capability.map
                or self.maximum_maps > len(self.map_list)
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
    def dnd(self) -> bool:
        """Returns DND is enabled."""
        if not self._capability.dnd_task:
            return bool(self._get_property(DreameVacuumProperty.DND))
        if self.dnd_tasks and len(self.dnd_tasks):
            return self.dnd_tasks[0].get("en")

    @property
    def dnd_start(self) -> str:
        """Returns DND start time."""
        if not self._capability.dnd_task:
            return self._get_property(DreameVacuumProperty.DND_START)
        if self.dnd_tasks and len(self.dnd_tasks):
            return self.dnd_tasks[0].get("st")
        return "22:00"

    @property
    def dnd_end(self) -> str:
        """Returns DND end time."""
        if not self._capability.dnd_task:
            return self._get_property(DreameVacuumProperty.DND_END)
        if self.dnd_tasks and len(self.dnd_tasks):
            return self.dnd_tasks[0].get("et")
        return "08:00"

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
    def ai_obstacle_detection(self) -> bool:
        return self._device.get_ai_property(
            DreameVacuumAIProperty.AI_OBSTACLE_DETECTION
        )

    @property
    def ai_obstacle_image_upload(self) -> bool:
        return self._device.get_ai_property(
            DreameVacuumAIProperty.AI_OBSTACLE_IMAGE_UPLOAD
        )

    @property
    def ai_pet_detection(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_PET_DETECTION)

    @property
    def ai_furniture_detection(self) -> bool:
        return self._device.get_ai_property(
            DreameVacuumAIProperty.AI_FURNITURE_DETECTION
        )

    @property
    def ai_fluid_detection(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_FLUID_DETECTION)

    @property
    def ai_obstacle_picture(self) -> bool:
        return self._device.get_ai_property(DreameVacuumAIProperty.AI_OBSTACLE_PICTURE)

    @property
    def fill_light(self) -> bool:
        return self._device.get_auto_switch_property(
            DreameVacuumAutoSwitchProperty.FILL_LIGHT
        )

    @property
    def hot_washing(self) -> bool:
        return (
            self._capability.hot_washing
            and self._device.get_auto_switch_property(
                DreameVacuumAutoSwitchProperty.HOT_WASHING
            )
            == 1
        )

    @property
    def auto_drying(self) -> bool:
        if self._device.capability.auto_empty_base:
            if not self._device.capability.auto_switch_settings:
                return bool(
                    self._get_property(DreameVacuumProperty.INTELLIGENT_RECOGNITION)
                )
            return bool(
                self._device.get_auto_switch_property(
                    DreameVacuumAutoSwitchProperty.AUTO_DRYING
                )
                == 1
            )
        return False

    @property
    def stain_avoidance(self) -> bool:
        return bool(
            self._device.get_auto_switch_property(
                DreameVacuumAutoSwitchProperty.STAIN_AVOIDANCE
            )
            == 2
        )

    @property
    def pet_focused_cleaning(self) -> bool:
        return self._device.get_auto_switch_property(
            DreameVacuumAutoSwitchProperty.PET_FOCUSED_CLEANING
        )

    @property
    def custom_order(self) -> bool:
        """Returns true when custom cleaning sequence is set."""
        segments = self.current_segments
        if segments:
            for v in segments.values():
                if v.order:
                    return True
        return False

    @property
    def cleaning_sequence(self) -> list[int] | None:
        """Returns custom cleaning sequence list."""
        segments = self.current_segments
        if segments:
            return (
                list(
                    sorted(
                        segments,
                        key=lambda segment_id: segments[segment_id].order
                        if segments[segment_id].order
                        else 99,
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
        return bool(
            current_map is not None
            and current_map.temporary_map
            and not current_map.empty_map
        )

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
        attributes = {
            ATTR_STATUS: self.status.name,
        }
        if self._capability.custom_cleaning_mode:            
            attributes[ATTR_CLEANING_MODE] = self.cleaning_mode.name
        attributes[
            ATTR_WATER_TANK if not self._capability.self_wash_base else ATTR_MOP_PAD
        ] = self.water_tank_or_mop_installed

        if self._device.cleanup_completed:
            attributes.update(
                {
                    ATTR_CLEANED_AREA: self._get_property(
                        DreameVacuumProperty.CLEANED_AREA
                    ),
                    ATTR_CLEANING_TIME: self._get_property(
                        DreameVacuumProperty.CLEANING_TIME
                    ),
                    ATTR_COMPLETED: True,
                }
            )
        else:
            attributes[ATTR_COMPLETED] = False

        map_data = self.current_map
        if map_data:
            if map_data.active_segments:
                attributes[ATTR_ACTIVE_SEGMENTS] = map_data.active_segments
            elif map_data.active_areas is not None:
                if self.go_to_zone:
                    attributes[ATTR_ACTIVE_CRUISE_POINTS] = {
                        1: Coordinate(self.go_to_zone.x, self.go_to_zone.y, False, 0)
                    }
                else:
                    attributes[ATTR_ACTIVE_AREAS] = map_data.active_areas
            elif map_data.active_points is not None:
                attributes[ATTR_ACTIVE_POINTS] = map_data.active_points
            elif map_data.predefined_points is not None:
                attributes[ATTR_PREDEFINED_POINTS] = map_data.predefined_points
            elif map_data.active_cruise_points is not None:
                attributes[ATTR_ACTIVE_CRUISE_POINTS] = map_data.active_cruise_points
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
            DreameVacuumProperty.CUSTOMIZED_CLEANING,
            DreameVacuumProperty.SERIAL_NUMBER,
            DreameVacuumProperty.NATION_MATCHED,
        ]

        if not self._capability.dnd_task:
            properties.extend(
                [
                    DreameVacuumProperty.DND_START,
                    DreameVacuumProperty.DND_END,
                ]
            )

        attributes = {}
        if not self._capability.self_wash_base:
            attributes[ATTR_WATER_TANK] = self.water_tank_or_mop_installed
            properties.append(DreameVacuumProperty.WATER_VOLUME)
        else:
            attributes[ATTR_MOP_PAD] = self.water_tank_or_mop_installed
            if self.self_clean_area is not None:
                attributes[ATTR_SELF_CLEAN_AREA] = self.self_clean_area
            if self.started and (
                self.customized_cleaning
                and not (self.zone_cleaning or self.spot_cleaning)
            ):
                attributes[ATTR_MOP_PAD_HUMIDITY] = STATE_UNAVAILABLE.capitalize()
                attributes[f"{ATTR_MOP_PAD_HUMIDITY}_list"] = []
            else:
                attributes[ATTR_MOP_PAD_HUMIDITY] = self.mop_pad_humidity_name.replace(
                    "_", " "
                ).capitalize()
                attributes[f"{ATTR_MOP_PAD_HUMIDITY}_list"] = [
                    v.replace("_", " ").capitalize()
                    for v in self.mop_pad_humidity_list.keys()
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
                elif prop is DreameVacuumProperty.WATER_VOLUME:
                    if self.started and (
                        self.customized_cleaning
                        and not (self.zone_cleaning or self.spot_cleaning)
                    ):
                        value = STATE_UNAVAILABLE.capitalize()
                        attributes[f"{prop_name}_list"] = []
                    else:
                        value = self.water_volume_name.capitalize()
                        attributes[f"{prop_name}_list"] = [
                            v.capitalize() for v in self.water_volume_list.keys()
                        ]
                elif prop is DreameVacuumProperty.CLEANING_MODE:
                    value = self.cleaning_mode_name.replace("_", " ").capitalize()
                elif prop is DreameVacuumProperty.CUSTOMIZED_CLEANING:
                    value = (
                        self.customized_cleaning
                        and not self.zone_cleaning
                        and not self.spot_cleaning
                    )
                elif prop is DreameVacuumProperty.TIGHT_MOPPING:
                    value = bool(value == 1)
                attributes[prop_name] = value

        if self._capability.dnd_task and self.dnd_tasks is not None:
            attributes[ATTR_DND] = {}
            for dnd_task in self.dnd_tasks:
                attributes[ATTR_DND][dnd_task["id"]] = {
                    "enabled": dnd_task.get("en"),
                    "start": dnd_task.get("st"),
                    "end": dnd_task.get("et"),
                }
        if self._capability.shortcuts and self.shortcuts is not None:
            attributes[ATTR_SHORTCUTS] = {}
            for id, shortcut in self.shortcuts.items():
                attributes[ATTR_SHORTCUTS][id] = {
                    "name": shortcut.name,
                    "running": shortcut.running,
                    "tasks": shortcut.tasks,
                }

        attributes[ATTR_CLEANING_SEQUENCE] = self.cleaning_sequence
        attributes[ATTR_CHARGING] = self.docked
        attributes[ATTR_STARTED] = self.started
        attributes[ATTR_PAUSED] = self.paused
        attributes[ATTR_RUNNING] = self.running
        attributes[ATTR_RETURNING_PAUSED] = self.returning_paused
        attributes[ATTR_RETURNING] = self.returning
        attributes[ATTR_MAPPING] = self.fast_mapping

        if self._capability.self_wash_base:
            attributes[ATTR_WASHING] = self.washing
            attributes[ATTR_WASHING_PAUSED] = self.washing
            attributes[ATTR_DRYING] = self.drying
            if not self.auto_water_refilling_enabled:
                attributes[ATTR_LOW_WATER] = bool(self.low_water_warning)
            else:
                attributes[ATTR_DRAINING] = self.draining

        if self.map_list:
            attributes[ATTR_ACTIVE_SEGMENTS] = self.active_segments
            if self._capability.lidar_navigation:
                attributes[ATTR_CURRENT_SEGMENT] = (
                    self.current_room.segment_id if self.current_room else 0
                )
            attributes[ATTR_SELECTED_MAP] = (
                self.selected_map.map_name if self.selected_map else None
            )
            attributes[ATTR_ROOMS] = {}
            for k, v in self.map_data_list.items():
                attributes[ATTR_ROOMS][v.map_name] = [
                    {ATTR_ID: j, ATTR_NAME: s.name, ATTR_ICON: s.icon}
                    for (j, s) in sorted(v.segments.items())
                ]

        return attributes

    def consumable_life_warning_description(self, consumable_property) -> str:
        description = CONSUMABLE_TO_LIFE_WARNING_DESCRIPTION.get(consumable_property)
        if description:
            value = self._get_property(consumable_property)
            if value is not None and value >= 0 and value <= 5:
                if value != 0 and len(description) > 1:
                    return description[1]
                return description[0]


class DreameVacuumDeviceInfo:
    """Container of device information."""

    def __init__(self, data):
        self.data = data

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
        if "hw_ver" in self.data:
            return self.data["hw_ver"]
        return None

    @property
    def mac_address(self) -> Optional[str]:
        """MAC address if available."""
        if "mac" in self.data:
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
