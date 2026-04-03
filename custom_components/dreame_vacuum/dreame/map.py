from __future__ import annotations
import io
import math
import time
import base64
import json
import zlib
import re
import logging
import traceback
import copy
import numpy as np
import hashlib
import textwrap
from py_mini_racer import MiniRacer
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization, hashes
from PIL import (
    Image,
    ImageDraw,
    ImageOps,
    ImageFont,
    ImageEnhance,
    PngImagePlugin,
    ImageFilter,
)
from typing import Any
from time import sleep
from io import BytesIO
from typing import Optional, Tuple
from functools import cmp_to_key
from threading import Timer
from .resources import *
from .protocol import DreameVacuumProtocol
from .exceptions import DeviceUpdateFailedException
from .types import (
    PIID,
    DIID,
    DreameVacuumProperty,
    DreameVacuumAction,
    DreameVacuumActionMapping,
    DreameVacuumDeviceCapability,
    RobotType,
    CleansetType,
    ObstacleType,
    Obstacle,
    FurnitureType,
    Furniture,
    PathType,
    Point,
    Coordinate,
    MapDataPartial,
    MapData,
    MapFrameType,
    MapPixelType,
    Path,
    Area,
    Wall,
    Carpet,
    Polygon,
    Segment,
    StartupMethod,
    CleanupMethod,
    TaskEndType,
    RecoveryMapType,
    ObstacleIgnoreStatus,
    SegmentSkipReason,
    MapImageDimensions,
    MapRendererLayer,
    MapRendererColorScheme,
    MapRendererConfig,
    MapRendererData,
    MapRendererResources,
    RecoveryMapInfo,
    DreameVacuumFloorMaterial,
    DreameVacuumFloorMaterialDirection,
    MAP_COLOR_SCHEME_LIST,
    SEGMENT_TYPE_CODE_TO_NAME,
    FURNITURE_TYPE_TO_DIMENSIONS,
    FURNITURE_V2_TYPE_TO_DIMENSIONS,
    FURNITURE_V2_TYPE_MIJIA_TO_DIMENSIONS,
    ALine,
    CLine,
    Paths,
    Angle,
)
from .const import (
    MAP_PARAMETER_NAME,
    MAP_PARAMETER_VALUE,
    MAP_PARAMETER_TIME,
    MAP_PARAMETER_CODE,
    MAP_PARAMETER_OUT,
    MAP_PARAMETER_MAP,
    MAP_PARAMETER_ANGLE,
    MAP_PARAMETER_MAPSTR,
    MAP_PARAMETER_CURR_ID,
    MAP_PARAMETER_VACUUM,
    MAP_PARAMETER_EXPIRES_TIME,
    MAP_PARAMETER_URL,
    MAP_REQUEST_PARAMETER_MAP_ID,
    MAP_REQUEST_PARAMETER_FRAME_ID,
    MAP_REQUEST_PARAMETER_FRAME_TYPE,
    MAP_REQUEST_PARAMETER_REQ_TYPE,
    MAP_REQUEST_PARAMETER_FORCE_TYPE,
    MAP_REQUEST_PARAMETER_TYPE,
    MAP_REQUEST_PARAMETER_INDEX,
    MAP_REQUEST_PARAMETER_ROOM_ID,
    MAP_DATA_JSON_CLASS,
    MAP_DATA_JSON_PARAMETER_CLASS,
    MAP_DATA_JSON_PARAMETER_SIZE,
    MAP_DATA_JSON_PARAMETER_X,
    MAP_DATA_JSON_PARAMETER_Y,
    MAP_DATA_JSON_PARAMETER_PIXEL_SIZE,
    MAP_DATA_JSON_PARAMETER_LAYERS,
    MAP_DATA_JSON_PARAMETER_ENTITIES,
    MAP_DATA_JSON_PARAMETER_META_DATA,
    MAP_DATA_JSON_PARAMETER_VERSION,
    MAP_DATA_JSON_PARAMETER_ROTATION,
    MAP_DATA_JSON_PARAMETER_TYPE,
    MAP_DATA_JSON_PARAMETER_POINTS,
    MAP_DATA_JSON_PARAMETER_PIXELS,
    MAP_DATA_JSON_PARAMETER_SEGMENT_ID,
    MAP_DATA_JSON_PARAMETER_ACTIVE,
    MAP_DATA_JSON_PARAMETER_NAME,
    MAP_DATA_JSON_PARAMETER_DIMENSIONS,
    MAP_DATA_JSON_PARAMETER_MIN,
    MAP_DATA_JSON_PARAMETER_MAX,
    MAP_DATA_JSON_PARAMETER_MID,
    MAP_DATA_JSON_PARAMETER_AVG,
    MAP_DATA_JSON_PARAMETER_PIXEL_COUNT,
    MAP_DATA_JSON_PARAMETER_COMPRESSED_PIXELS,
    MAP_DATA_JSON_PARAMETER_ROBOT_POSITION,
    MAP_DATA_JSON_PARAMETER_CHARGER_POSITION,
    MAP_DATA_JSON_PARAMETER_NO_MOP_AREA,
    MAP_DATA_JSON_PARAMETER_NO_GO_AREA,
    MAP_DATA_JSON_PARAMETER_ACTIVE_ZONE,
    MAP_DATA_JSON_PARAMETER_VIRTUAL_WALL,
    MAP_DATA_JSON_PARAMETER_PATH,
    MAP_DATA_JSON_PARAMETER_FLOOR,
    MAP_DATA_JSON_PARAMETER_WALL,
    MAP_DATA_JSON_PARAMETER_SEGMENT,
)

_LOGGER = logging.getLogger(__name__)


class DreameMapVacuumMapManager:
    def __init__(self, _protocol: DreameVacuumProtocol) -> None:
        self._map_list_object_name: str = None
        self._map_list_md5: str = None
        self._recovery_map_list_object_name: str = None
        self._update_callback = None
        self._change_callback = None
        self._error_callback = None
        self._update_timer: Timer = None
        self._update_running: bool = False
        self._update_interval: float = 10
        self._device_running: bool = False
        self._device_docked: bool = False
        self._available: bool = False
        self._disconnected: bool = False
        self._ready: bool = False
        self._connected: bool = True
        self._vslam_map: bool = False

        self._init_data()

        self._protocol = _protocol
        self.editor = DreameMapVacuumMapEditor(self)
        self.optimizer = DreameVacuumMapOptimizer()

    def _init_data(self) -> None:
        self._map_data: MapData = None
        self._current_frame_id: int = None
        self._current_map_id: int = None
        self._current_timestamp_ms: int = None
        self._file_urls: dict[str, str] = {}
        self._saved_map_data: dict[int, MapData] = {}
        self._map_list: list[int] = []
        self._need_map_request: bool = False
        self._need_new_map: bool = False
        self._need_map_list_request: bool = None
        self._need_recovery_map_list_request: bool = None
        self._map_data_queue: dict[int, MapData] = {}
        self._updated_frame_id: int = None
        self._selected_map_id: int = None
        self._request_queue: dict[str, bool] = {}
        self._latest_map_data_time: int = None
        self._latest_object_name_time: int = None
        self._latest_map_timestamp_ms: int = None
        self._latest_map_id: int = None
        self._last_p_request_map_id: int = None
        self._last_p_request_frame_id: int = None
        self._last_p_request_time: int = None
        self._last_robot_time: int = None
        self._map_request_time: int = None
        self._map_request_count: int = 0
        self._new_map_request_time: int = None
        self._aes_iv: str = None
        self._aes_key: str = None
        self._capability: DreameVacuumDeviceCapability = None

    def _request_map_from_cloud(self) -> bool:
        if self._protocol.cloud.dreame_cloud:
            return True

        if self._current_timestamp_ms is not None:
            start_time = self._current_timestamp_ms
            request_start_time = int(math.floor(start_time / 1000.0))
        else:
            request_start_time = 0
            if self._latest_object_name_time is not None:
                request_start_time = self._latest_object_name_time
            elif self._map_request_time is not None:
                request_start_time = self._map_request_time
            elif self._last_robot_time is not None:
                request_start_time = int(self._last_robot_time / 1000)

        if self._latest_map_data_time is None or self._latest_map_data_time < request_start_time:
            self._latest_map_data_time = request_start_time

        if self._latest_object_name_time is None or self._latest_object_name_time < request_start_time:
            self._latest_object_name_time = request_start_time

        map_data_result = self._protocol.cloud.get_device_property(
            DIID(DreameVacuumProperty.MAP_DATA), 20, self._latest_map_data_time
        )

        if not self._protocol.cloud.connected:
            if self._connected:
                self._connected = False
                self._map_data_changed()
            return False
        elif not self._connected:
            self._connected = True
            self._map_data_changed()

        if map_data_result is None:
            _LOGGER.warning("Getting map_data from cloud failed")
            map_data_result = []

        object_name_result = self._protocol.cloud.get_device_property(
            DIID(DreameVacuumProperty.OBJECT_NAME), 1, self._latest_object_name_time
        )
        if object_name_result is None:
            _LOGGER.warning("Getting object_name from cloud failed")

        partial_map_data = None
        if len(map_data_result):
            partial_map_data = []
            self._latest_map_data_time = map_data_result[0][MAP_PARAMETER_TIME] + 1

            for data in map_data_result:
                partial_map_data.append(
                    self._decode_map_partial(
                        json.loads(data[MAP_PARAMETER_VALUE if MAP_PARAMETER_VALUE in data else "val"])[0],
                        data[MAP_PARAMETER_TIME] * 1000 if data.get(MAP_PARAMETER_TIME) else None,
                    )
                )

        object_name = None
        object_name_timestamp = None
        if object_name_result:
            data = object_name_result[0]
            if MAP_PARAMETER_TIME in data:
                timestamp = data[MAP_PARAMETER_TIME]
                self._latest_object_name_time = timestamp + 1

            if len(object_name_result) == 1:
                object_name = json.loads(data[MAP_PARAMETER_VALUE if MAP_PARAMETER_VALUE in data else "val"])[0]
                if timestamp:
                    object_name_timestamp = timestamp * 1000

        self._add_cloud_map_data(partial_map_data, object_name, object_name_timestamp)
        return len(map_data_result) or object_name is not None

    def _request_map(self, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        if parameters is None:
            parameters = {
                MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.I.name,
            }

        payload = [
            {
                "piid": PIID(DreameVacuumProperty.FRAME_INFO),
                MAP_PARAMETER_VALUE: str(json.dumps(parameters, separators=(",", ":"))).replace(" ", ""),
            }
        ]

        try:
            _LOGGER.info("Request map from device %s", payload)
            mapping = DreameVacuumActionMapping[DreameVacuumAction.REQUEST_MAP]
            return self._protocol.action(mapping["siid"], mapping["aiid"], payload, 0)
        except Exception as ex:
            _LOGGER.warning("Send request map failed: %s", ex)
        return None

    def _request_i_map(self, start_time: int = None) -> bool:
        if not self._request_i_map_available and not self._protocol.dreame_cloud:
            return self.request_new_map()

        parameters = {
            MAP_REQUEST_PARAMETER_REQ_TYPE: 1,
            MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.I.name,
            MAP_REQUEST_PARAMETER_FORCE_TYPE: 1,
        }

        if start_time:
            parameters[MAP_PARAMETER_TIME] = start_time

        result = self._request_map(parameters)
        if result and MAP_PARAMETER_CODE in result and result[MAP_PARAMETER_CODE] == 0:
            out = result[MAP_PARAMETER_OUT]
            _LOGGER.info("Response from device %s", out)
            has_map = False
            object_name = None
            raw_map_data = None
            for prop in out:
                value = prop[MAP_PARAMETER_VALUE]
                if value != "":
                    piid = prop["piid"]
                    if piid == PIID(DreameVacuumProperty.OBJECT_NAME):
                        has_map = True
                        object_name = value
                    elif piid == PIID(DreameVacuumProperty.MAP_DATA):
                        has_map = True
                        raw_map_data = value
                    elif piid == PIID(DreameVacuumProperty.ROBOT_TIME):
                        self._last_robot_time = int(value)
                        if start_time is None:
                            self._map_request_time = self._last_robot_time
                            self._map_request_count = 1
                    elif piid == PIID(DreameVacuumProperty.OLD_MAP_DATA):
                        if not has_map:
                            values = value.split(",")
                            if values[0] == "0":
                                raw_map_data = values[1]
                            else:
                                object_name = values[1]
                                if len(values) == 3:
                                    object_name = f"{object_name},{values[2]}"

            if has_map:
                self._latest_object_name_time = int(self._last_robot_time / 1000) + 1
                self._map_request_time = None

            if object_name:
                self._add_map_data_file(object_name, self._last_robot_time)
                return True
            if raw_map_data:
                self._add_raw_map_data(raw_map_data, self._last_robot_time)
                return True
            return False

        self._request_map_from_cloud()
        return False

    def _request_missing_p_map(self) -> bool:
        if self._map_data is None:
            return

        if self._partial_map_queue_size() == 0:
            return

        frame_id = self._current_frame_id + 1
        map_id = self._current_map_id

        if (
            self._last_p_request_time is not None
            and self._last_p_request_map_id == map_id
            and self._last_p_request_frame_id == frame_id
            and (time.time() - self._last_p_request_time) < 3
        ):
            return

        self._last_p_request_map_id = map_id
        self._last_p_request_frame_id = frame_id
        self._last_p_request_time = time.time()

        _LOGGER.info("Request missing P map: %s", frame_id)
        result = self._request_map(
            {
                MAP_REQUEST_PARAMETER_MAP_ID: map_id,
                MAP_REQUEST_PARAMETER_FRAME_ID: frame_id,
                MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.P.name,
            }
        )
        return bool(result and result[MAP_PARAMETER_CODE] == 0)

    def _request_next_p_map(self, map_id: int, frame_id: int) -> bool:
        key = f"{map_id}:{frame_id}"
        if key in self._request_queue and self._request_queue[key]:
            return

        self._request_queue[key] = True
        _LOGGER.info("Request next P map: %s", frame_id)
        result = self._request_map(
            {
                MAP_REQUEST_PARAMETER_MAP_ID: map_id,
                MAP_REQUEST_PARAMETER_REQ_TYPE: 1,
                MAP_REQUEST_PARAMETER_FRAME_ID: frame_id,
                MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.P.name,
            }
        )
        if result and result[MAP_PARAMETER_CODE] == 0:
            del self._request_queue[key]
            object_name = None
            raw_map_data = None
            timestamp = None

            for prop in result[MAP_PARAMETER_OUT]:
                value = prop[MAP_PARAMETER_VALUE]
                if value != "":
                    piid = prop["piid"]
                    if piid == PIID(DreameVacuumProperty.OBJECT_NAME):
                        object_name = value
                    elif piid == PIID(DreameVacuumProperty.MAP_DATA):
                        raw_map_data = value
                    elif piid == PIID(DreameVacuumProperty.ROBOT_TIME):
                        timestamp = int(value)

            if object_name:
                self._add_map_data_file(object_name, timestamp)
            if raw_map_data:
                _LOGGER.info("Lost P map received: %s:%s", map_id, frame_id)
                self._add_raw_map_data(raw_map_data, timestamp)

            if not raw_map_data and self._vslam_map and not object_name:
                self.request_new_map()
                return False
            return True
        return False

    def _request_t_map(self) -> None:
        result = self._request_map({MAP_REQUEST_PARAMETER_FRAME_TYPE: "T"})
        if result and result[MAP_PARAMETER_CODE] == 0:
            self.request_map_list()

    def _request_w_map(self) -> None:
        try:
            _LOGGER.info("Request wifi map from device")
            mapping = DreameVacuumActionMapping[DreameVacuumAction.WIFI_MAP]
            return self._protocol.action(mapping["siid"], mapping["aiid"], None, 0)
        except Exception as ex:
            _LOGGER.warning("Send request map failed: %s", ex)
        return None

    def _request_current_map(self, map_request_time: int = None) -> bool:
        if self._request_i_map_available or self._protocol.dreame_cloud:
            return self._request_i_map(map_request_time)

        return self._request_map_from_cloud()

    def _map_data_updated(self) -> None:
        if self._update_callback:
            _LOGGER.debug("Update callback")
            self._update_callback()

    def _map_data_changed(self, saved_map=False) -> None:
        if self._change_callback:
            _LOGGER.debug("Change callback")
            self._change_callback(saved_map)

    def _update_task(self) -> None:
        if self._update_timer is not None:
            self._update_timer.cancel()
            self._update_timer = None

        start = time.time()
        self.update()
        self.schedule_update(max(self._update_interval - (time.time() - start), 1))

    def _queue_partial_map(self, map_data) -> None:
        if map_data.map_id != self._latest_map_id:
            return
        next_frame_id = 0

        if self._current_map_id is not None and self._current_map_id == self._latest_map_id:
            next_frame_id = self._current_frame_id + 1

        if map_data.map_id not in self._map_data_queue:
            self._map_data_queue[map_data.map_id] = {}

        if map_data.frame_id < next_frame_id:
            return
        self._map_data_queue[map_data.map_id][map_data.frame_id] = map_data

    def _delete_invalid_partial_maps(self) -> None:
        if self._latest_map_id is None:
            return

        if self._current_frame_id is None:
            return

        frame_id = self._current_frame_id
        map_data_queue = copy.deepcopy(self._map_data_queue)
        for k, v in map_data_queue.items():
            if k != self._latest_map_id:
                del self._map_data_queue[k]

        if self._latest_map_id not in self._map_data_queue or not self._map_data_queue[self._latest_map_id]:
            return

        map_data_queue = copy.deepcopy(self._map_data_queue[self._latest_map_id])
        for k, v in map_data_queue.items():
            if k <= frame_id:
                del self._map_data_queue[self._latest_map_id][k]

    def _unqueue_next_partial_map(self) -> MapData | None:
        if (
            self._latest_map_id is None
            or self._current_frame_id is None
            or self._current_map_id != self._latest_map_id
        ):
            return

        frame_id = self._current_frame_id + 1
        if (
            self._latest_map_id not in self._map_data_queue
            or not self._map_data_queue[self._latest_map_id]
            or frame_id not in self._map_data_queue[self._latest_map_id]
        ):
            return

        map_data = self._map_data_queue[self._latest_map_id][frame_id]

        if map_data:
            del self._map_data_queue[self._latest_map_id][frame_id]
            return map_data

    def _unqueue_partial_map(self, map_id: int, frame_id: int) -> MapData | None:
        if (
            map_id in self._map_data_queue
            and self._map_data_queue[map_id]
            and frame_id in self._map_data_queue[map_id]
        ):
            map_data = self._map_data_queue[map_id][frame_id]
            del self._map_data_queue[map_id][frame_id]
            return map_data

    def _partial_map_queue_size(self) -> int:
        if self._latest_map_timestamp_ms is None:
            return 0

        if self._latest_map_id not in self._map_data_queue or not self._map_data_queue[self._latest_map_id]:
            return 0

        return len(self._map_data_queue[self._latest_map_id])

    def _get_object_file_data(self, object_name: str = "", timestamp=None) -> Tuple[Any, Optional[str]]:
        key = None
        if object_name and "," in object_name:
            values = object_name.split(",")
            object_name = values[0]
            key = values[1]
        response = self._get_interim_file_data(object_name, timestamp)
        return response, key

    def _get_interim_file_data(self, object_name: str = "", timestamp=None) -> str | None:
        if self._protocol.cloud.logged_in:
            if object_name is None or object_name == "":
                _LOGGER.info("Get object name from cloud")
                if self._protocol.cloud.dreame_cloud:
                    object_name_result = self._protocol.cloud.get_properties(DIID(DreameVacuumProperty.OBJECT_NAME))
                    if object_name_result:
                        object_name_result = object_name_result[0][MAP_PARAMETER_VALUE]
                        object_name = object_name_result[0]
                else:
                    object_name_result = self._protocol.cloud.get_device_property(
                        DIID(DreameVacuumProperty.OBJECT_NAME)
                    )
                    if object_name_result:
                        object_name_result = json.loads(object_name_result[0][MAP_PARAMETER_VALUE])
                        object_name = object_name_result[0]

            if object_name is None or object_name == "":
                object_name = self._protocol.cloud.object_name

            url = self._get_file_url(object_name)
            if url:
                _LOGGER.info("Request map data from cloud %s", url)
                response = self._protocol.cloud.get_file(url)
                if response is not None:
                    return response
                _LOGGER.warning("Request map data from cloud failed %s", url)
                if self._file_urls.get(object_name):
                    del self._file_urls[object_name]

    def _get_file_url(self, object_name: str, interim: bool = True) -> str | None:
        url = None
        now = int(round(time.time()))
        if self._file_urls and self._file_urls.get(object_name):
            object = self._file_urls[object_name]
            if object[MAP_PARAMETER_EXPIRES_TIME] - now > 60:
                url = f"{object[MAP_PARAMETER_URL]}&current={str(now)}"

        if url is None:
            response = (
                self._protocol.cloud.get_interim_file_url(object_name)
                if interim
                else self._protocol.cloud.get_file_url(object_name)
            )
            if response:
                self._file_urls[object_name] = {
                    MAP_PARAMETER_URL: response,
                    MAP_PARAMETER_EXPIRES_TIME: now + (30 * 60),
                }
                url = self._file_urls[object_name][MAP_PARAMETER_URL]
        return url

    def _decode_map_partial(self, raw_map, timestamp=None, key=None) -> MapDataPartial | None:
        partial_map = DreameVacuumMapDecoder.decode_map_partial(raw_map, self._aes_iv, key)
        if partial_map is not None:
            # After restart or unsuccessful start robot returns timestamp_ms as uptime and that messes up with the latest map/frame id detection.
            # I could not figure out how app handles with this issue but i have added this code to update time stamp as request/object time.

            if timestamp and (partial_map.timestamp_ms is None or partial_map.timestamp_ms < 1577826000000):
                partial_map.timestamp_ms = timestamp

            if self._latest_map_timestamp_ms is None or partial_map.timestamp_ms > self._latest_map_timestamp_ms:
                self._latest_map_timestamp_ms = partial_map.timestamp_ms
                self._latest_map_id = partial_map.map_id

        return partial_map

    def _add_cloud_map_data(self, partial_map_data, object_name, object_name_timestamp):
        if partial_map_data:
            for partial_map in partial_map_data:
                if partial_map.frame_type == MapFrameType.I.value:
                    self._add_map_data(partial_map)
                else:
                    self._queue_partial_map(partial_map)

        next_frame_id = 1
        if self._current_frame_id:
            next_frame_id = self._current_frame_id + 1

        if (
            not self._add_map_data(self._unqueue_partial_map(self._latest_map_id, next_frame_id))
            and object_name is None
        ):
            self._delete_invalid_partial_maps()
            tmpLen = self._partial_map_queue_size()
            if tmpLen > 8:
                if self._protocol.dreame_cloud:
                    self._request_map()
                else:
                    self.request_new_map()
            elif tmpLen > 4:
                self._request_missing_p_map()
            elif tmpLen > 0 and partial_map_data:
                self._request_next_p_map(self._latest_map_id, next_frame_id)

        if object_name is not None:
            self._need_new_map = False
            _LOGGER.info("New object name received: %s", object_name)
            response, key = self._get_object_file_data(object_name, object_name_timestamp)
            if response:
                partial_map = self._decode_map_partial(response.decode(), object_name_timestamp, key)
                if partial_map:
                    if self._map_data is None or partial_map.frame_type == MapFrameType.I.value:
                        return self._add_map_data(partial_map)

                    self._queue_partial_map(partial_map)
                    next_partial_map = self._unqueue_next_partial_map()
                    if next_partial_map:
                        self._add_map_data(next_partial_map)
                    else:
                        self._delete_invalid_partial_maps()
                        if self._partial_map_queue_size() > 8:
                            if self._protocol.dreame_cloud:
                                self._request_map()
                            else:
                                self.request_new_map()

    def _add_map_data_file(self, object_name: str, timestamp) -> None:
        response, key = self._get_object_file_data(object_name, timestamp)
        if response is not None:
            self._add_raw_map_data(response.decode(), timestamp, key)

    def _add_raw_map_data(self, raw_map: str, timestamp=None, key=None) -> bool:
        return self._add_map_data(self._decode_map_partial(raw_map, timestamp, key))

    def _add_map_data(self, partial_map: MapDataPartial) -> None:
        if partial_map is None:
            return False

        if (
            partial_map.timestamp_ms is not None
            and self._current_timestamp_ms is not None
            and self._current_frame_id
            and self._current_timestamp_ms > partial_map.timestamp_ms
        ):
            _LOGGER.info(
                "Skip frame %s, timestamp %s:%s < %s:%s",
                partial_map.frame_type,
                partial_map.frame_id,
                partial_map.timestamp_ms,
                self._current_frame_id,
                self._current_timestamp_ms,
            )
            return True

        if self._current_map_id is not None and self._current_map_id != self._latest_map_id:
            _LOGGER.info(
                "Map ID Changed: %s -> %s",
                self._current_map_id,
                self._latest_map_id,
            )

            self._current_frame_id = None
            self._current_map_id = None
            self._updated_frame_id = None
            # self.request_next_map_list()

        if partial_map.map_id != self._latest_map_id:
            _LOGGER.info(
                "Skip frame, map_id %s != %s",
                partial_map.map_id,
                self._latest_map_id,
            )
            # self._add_next_map_data()
            return True

        if (
            self._current_frame_id is not None
            and self._current_frame_id is not None
            and partial_map.frame_id < self._current_frame_id
        ):
            if (
                partial_map.frame_type != MapFrameType.I.value
                or partial_map.timestamp_ms <= self._current_timestamp_ms
            ):
                _LOGGER.info(
                    "Skip frame, frame id %s:%s < %s:%s",
                    partial_map.map_id,
                    partial_map.frame_id,
                    self._current_map_id,
                    self._current_frame_id,
                )
                # self._add_next_map_data()
                return True

        if partial_map.frame_type == MapFrameType.P.value:
            if self._current_frame_id is not None and self._map_data is not None and self._map_data.restored_map:
                _LOGGER.debug("Current map data removed")
                self._map_data = None
                self._current_frame_id = None
                self._current_map_id = None

            if self._current_frame_id is None or self._map_data is None:
                self._queue_partial_map(partial_map)

                if self._map_request_time is None:
                    self._request_i_map()
                    return True

            if partial_map.frame_id != self._current_frame_id + 1:
                if partial_map.frame_id <= self._current_frame_id:
                    self._add_next_map_data()
                    return True

                self._queue_partial_map(partial_map)
                self._delete_invalid_partial_maps()

                tmpLen = self._partial_map_queue_size()
                if tmpLen > 0:
                    if self._protocol.dreame_cloud:
                        if tmpLen > 8:
                            self._request_map()
                        elif tmpLen > 4:
                            self._request_missing_p_map()
                        else:
                            next_frame_id = 1
                            if self._current_frame_id:
                                next_frame_id = self._current_frame_id + 1
                            self._request_next_p_map(self._latest_map_id, next_frame_id)
                    else:
                        self._request_next_p_map(partial_map.map_id, self._current_frame_id + 1)
                else:
                    self._add_next_map_data()
                return True

            current_robot_position = (
                copy.deepcopy(self._map_data.robot_position) if self._map_data.robot_position else None
            )

            map_data = DreameVacuumMapDecoder.decode_p_map_data_from_partial(
                partial_map,
                self._map_data,
                self._vslam_map,
            )
            if map_data:
                if map_data.carpet_pixels and self._map_data.dimensions != map_data.dimensions:
                    map_data.carpet_pixels = DreameVacuumMapDecoder.get_carpets(map_data, self.selected_map)

                DreameVacuumMapDecoder.set_carpet_cleanset(map_data, map_data.carpet_cleanset, self._capability)

                self._map_data = map_data
                self._map_data.last_updated = time.time()
                self._updated_frame_id = None
                self._current_frame_id = map_data.frame_id
                self._current_map_id = map_data.map_id
                self._current_timestamp_ms = map_data.timestamp_ms

                _LOGGER.info("Decode P map %d %d", map_data.map_id, map_data.frame_id)

                if not self._device_running or current_robot_position != map_data.robot_position:
                    self._map_data_changed()

        elif partial_map.frame_type == MapFrameType.I.value:
            self._need_map_request = False
            self._delete_invalid_partial_maps()

            (
                map_data,
                saved_map_data,
            ) = DreameVacuumMapDecoder.decode_map_data_from_partial(partial_map, self._vslam_map)
            if map_data is None:
                self._add_next_map_data()
                return True

            if map_data.empty_map:
                if self._map_data is None or not self._map_data.empty_map:
                    self._init_data()
                    self._map_data = map_data
                    self._current_frame_id = map_data.frame_id
                    self._current_map_id = map_data.map_id
                    self._current_timestamp_ms = map_data.timestamp_ms

                    self._map_data_changed()
                self._add_next_map_data()
                return True

            if saved_map_data is not None and saved_map_data.saved_map:
                if not saved_map_data.carpet_cleanset:
                    saved_map_data.carpet_cleanset = map_data.carpet_cleanset
                DreameVacuumMapDecoder.set_carpet_cleanset(
                    saved_map_data, saved_map_data.carpet_cleanset, self._capability
                )
                DreameVacuumMapDecoder.set_floor_material(saved_map_data, self._capability)
                DreameVacuumMapDecoder.set_segment_cleanset(
                    saved_map_data,
                    map_data.cleanset,
                    self._capability,
                )

                if saved_map_data.map_id in self._saved_map_data:
                    map_data.temporary_map = False
                    self._selected_map_id = saved_map_data.map_id
                    saved_map_data.map_name = self._saved_map_data[saved_map_data.map_id].map_name
                    saved_map_data.custom_name = self._saved_map_data[saved_map_data.map_id].custom_name
                    saved_map_data.rotation = self._saved_map_data[saved_map_data.map_id].rotation
                    saved_map_data.map_index = self._saved_map_data[saved_map_data.map_id].map_index
                    saved_map_data.recovery_map_list = self._saved_map_data[saved_map_data.map_id].recovery_map_list

                    saved_map_data.timestamp_ms = map_data.timestamp_ms
                    if (
                        saved_map_data != self._saved_map_data[saved_map_data.map_id]
                        or saved_map_data.segments != self._saved_map_data[saved_map_data.map_id].segments
                    ):
                        saved_map_data.last_updated = time.time()
                        if saved_map_data.wifi_map_data:
                            saved_map_data.wifi_map_data.last_updated = saved_map_data.last_updated
                        self._saved_map_data[saved_map_data.map_id] = saved_map_data
                        if not self._protocol.dreame_cloud:
                            self.request_next_map_list()

                        _LOGGER.debug(
                            "Decode saved map %s: %s",
                            saved_map_data.map_id,
                            saved_map_data.map_name,
                        )
                elif not map_data.temporary_map:
                    if not self._map_list:
                        saved_map_data.last_updated = time.time()
                        if saved_map_data.wifi_map_data:
                            saved_map_data.wifi_map_data.last_updated = saved_map_data.last_updated
                        self._saved_map_data[saved_map_data.map_id] = saved_map_data

                        _LOGGER.info("Add saved map from new map %s", saved_map_data.map_id)
                        self._refresh_map_list()
                        if self._map_data:
                            self._map_data_changed()

                    if not self._protocol.dreame_cloud:
                        if self._device_running:
                            self.request_next_map_list()
                        else:
                            self.request_map_list()

            DreameVacuumMapDecoder.set_floor_material(map_data, self._capability)
            DreameVacuumMapDecoder.set_segment_cleanset(map_data, map_data.cleanset, self._capability)
            DreameVacuumMapDecoder.set_carpet_cleanset(map_data, map_data.carpet_cleanset, self._capability)

            if not map_data.saved_map:
                if map_data.saved_map_id and map_data.saved_map_id in self._saved_map_data:
                    map_data.map_index = self._saved_map_data[map_data.saved_map_id].map_index

                if self._vslam_map:
                    if map_data.saved_map_status == 1 and saved_map_data and self._device_docked:
                        map_data.segments = copy.deepcopy(saved_map_data.segments)
                        map_data.data = copy.deepcopy(saved_map_data.data)
                        map_data.pixel_type = copy.deepcopy(saved_map_data.pixel_type)
                        map_data.dimensions = copy.deepcopy(saved_map_data.dimensions)
                        map_data.charger_position = copy.deepcopy(saved_map_data.charger_position)
                        map_data.no_go_areas = saved_map_data.no_go_areas
                        map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                        map_data.virtual_walls = saved_map_data.virtual_walls
                        map_data.robot_position = None
                        map_data.docked = True
                        # map_data.restored_map = True
                        map_data.path = None
                        map_data.need_optimization = False
                        map_data.saved_map_status = 2
                    elif (
                        map_data.robot_position is None
                        and map_data.restored_map
                        and not self._device_docked
                        and self._map_data
                        and not map_data.docked
                    ):
                        map_data.robot_position = self._map_data.robot_position

                changed = (
                    self._current_frame_id is None
                    or self._map_data is None
                    or map_data != self._map_data
                    or map_data.rotation != self._map_data.rotation
                    or map_data.segments != self._map_data.segments
                )

                if (
                    changed
                    or self._current_frame_id != map_data.frame_id
                    or self._current_timestamp_ms != map_data.timestamp_ms
                ):
                    if (
                        self._current_frame_id is not None
                        and self._map_data is not None
                        and self._updated_frame_id is not None
                    ):
                        if map_data.frame_id <= self._updated_frame_id + 1:
                            if not self._map_data.empty_map and (
                                self._map_data.saved_map_status == 2
                                or (self._vslam_map and self._map_data.saved_map_status == 1)
                            ):
                                map_data.active_segments = self._map_data.active_segments
                                map_data.active_areas = self._map_data.active_areas
                                map_data.active_points = self._map_data.active_points
                                map_data.active_cruise_points = self._map_data.active_cruise_points
                                map_data.path = self._map_data.path
                                map_data.segments = self._map_data.segments
                                map_data.floor_material = self._map_data.floor_material
                                map_data.hidden_segments = self._map_data.hidden_segments
                                map_data.cleanset = self._map_data.cleanset
                                map_data.carpet_cleanset = self._map_data.carpet_cleanset
                                map_data.cleaning_sequence = self._map_data.cleaning_sequence
                                map_data.mop_type = self._map_data.mop_type
                                changed = map_data != self._map_data
                            else:
                                changed = False
                                map_data.empty_map = True
                        else:
                            self._updated_frame_id = None

                    if (
                        self._map_data
                        and not changed
                        and map_data.need_optimization
                        and not self._map_data.need_optimization
                    ):
                        map_data.need_optimization = False
                        map_data.optimized_pixel_type = copy.deepcopy(self._map_data.optimized_pixel_type)
                        map_data.optimized_dimensions = copy.deepcopy(self._map_data.optimized_dimensions)
                        map_data.optimized_charger_position = copy.deepcopy(self._map_data.optimized_charger_position)

                    self._map_data = map_data
                    self._current_frame_id = map_data.frame_id
                    self._current_map_id = map_data.map_id
                    self._current_timestamp_ms = map_data.timestamp_ms

                    if changed:
                        _LOGGER.info("Decode I map %d %d", map_data.map_id, map_data.frame_id)
                        self._map_data.last_updated = time.time()
                        self._map_data_changed()
                    else:
                        _LOGGER.info(
                            "Decode map %d %d not changed",
                            map_data.map_id,
                            map_data.frame_id,
                        )

        if self._current_frame_id is None and self._map_data is not None:
            self._map_data = None
            self._map_data_changed()

        self._add_next_map_data()
        return True

    def _add_next_map_data(self) -> None:
        next_partial_map = self._unqueue_next_partial_map()
        if next_partial_map is not None:
            _LOGGER.debug("Continue to next map data")
            self._add_map_data(next_partial_map)

    def _refresh_map_list(self) -> None:
        index = 1
        new_map_list = []
        for map_id, saved_map_data in sorted(self._saved_map_data.items()):
            new_map_list.append(map_id)
            if saved_map_data.custom_name is None:
                saved_map_data.map_name = f"Map {str(index)}"
            else:
                saved_map_data.map_name = saved_map_data.custom_name
            saved_map_data.map_index = index
            index = index + 1
        self._map_list = new_map_list

    def _refresh_recovery_map_list(self) -> None:
        index = 1
        for map_id, saved_map_data in sorted(self._saved_map_data.items()):
            if saved_map_data.recovery_map_list:
                for recovery_map_data in saved_map_data.recovery_map_list:
                    map_type = recovery_map_data.map_type.name.replace("_", " ").title()
                    if saved_map_data.custom_name is None:
                        recovery_map_data.map_name = f"Recovery Map {str(index)} ({map_type})"
                    else:
                        recovery_map_data.map_name = (
                            f"{saved_map_data.custom_name} Recovery Map {str(index)} ({map_type})"
                        )
                    recovery_map_data.map_index = index
                    index = index + 1

    def handle_properties(self, properties):
        if not self._ready:
            return

        has_map = False
        object_name = None
        raw_map_data = None

        for prop in properties:
            value = prop[MAP_PARAMETER_VALUE]
            if value != "":
                piid = prop["piid"]
                if piid == PIID(DreameVacuumProperty.OBJECT_NAME):
                    has_map = True
                    object_name = value
                elif piid == PIID(DreameVacuumProperty.MAP_DATA):
                    has_map = True
                    raw_map_data = value
                elif piid == PIID(DreameVacuumProperty.OLD_MAP_DATA):
                    if not has_map:
                        values = value.split(",")
                        if values[0] == "0":
                            raw_map_data = values[1]
                        else:
                            object_name = values[1]
                            if len(values) == 3:
                                object_name = f"{object_name},{values[2]}"

        if has_map:
            self._map_request_time = None

        if object_name or raw_map_data:
            partial_map_data = None
            timestamp = int(time.time() * 1000)

            if raw_map_data:
                partial_map_data = [self._decode_map_partial(raw_map_data, timestamp)]
            self._add_cloud_map_data(partial_map_data, object_name, timestamp)

    def get_map(self, map_index: int = 0) -> MapData | None:
        if map_index:
            if map_index <= len(self._map_list):
                return self._saved_map_data[self._map_list[map_index - 1]]
            return None
        return self._map_data

    def get_aes_key(self):
        if self._aes_key is None:
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
            response = self._protocol.action(
                14,
                1,
                [
                    {
                        "piid": 5,
                        "value": base64.b64encode(
                            private_key.public_key().public_bytes(
                                encoding=serialization.Encoding.DER,
                                format=serialization.PublicFormat.SubjectPublicKeyInfo,
                            )
                        ).decode(),
                    }
                ],
            )

            if not (
                response is None or "out" not in response or not response["out"] or "value" not in response["out"][0]
            ):
                response = response["out"][0]["value"].replace("-", "+").replace("_", "/")
                while len(response) % 4 != 0:
                    response += "="

                self._aes_key = base64.b64decode(
                    base64.b64encode(
                        serialization.load_der_private_key(
                            private_key.private_bytes(
                                encoding=serialization.Encoding.DER,
                                format=serialization.PrivateFormat.PKCS8,
                                encryption_algorithm=serialization.NoEncryption(),
                            ),
                            password=None,
                        ).decrypt(
                            base64.b64decode(response),
                            asym_padding.OAEP(
                                mgf=asym_padding.MGF1(algorithm=hashes.SHA1()),
                                algorithm=hashes.SHA1(),
                                label=None,
                            ),
                        )
                    ).decode()
                ).decode("utf-8")
        return self._aes_key

    def get_obstacle_image(self, map_data, index):
        index = str(index)
        if map_data and map_data.obstacles and index in map_data.obstacles:
            obstacle = map_data.obstacles[index]
            if (
                obstacle.file_name
                and len(obstacle.file_name) > 1
                and (obstacle.picture_status is None or obstacle.picture_status.value == 2)
            ):
                try:
                    if self._protocol.dreame_cloud and self._capability.local_storage:
                        _LOGGER.info(
                            "Obstacle image local file name: %s",
                            obstacle.file_name,
                        )
                        file = self._protocol.cloud.get_device_file(obstacle.file_name, "obstacle")
                        if file:
                            key = self.get_aes_key()
                            if not key:
                                _LOGGER.warning("Failed to get obstacle aes key! (%s)", obstacle.file_name)
                                return None, None

                            cipher = Cipher(
                                algorithms.AES(hashlib.md5(key.encode("utf-8")).hexdigest().encode("utf-8")),
                                modes.CBC(base64.b64decode(self._capability.resources_aes_iv)),
                            )
                            decryptor = cipher.decryptor()
                            unpadder = padding.PKCS7(128).unpadder()
                            return (
                                (unpadder.update(decryptor.update(file) + decryptor.finalize()) + unpadder.finalize()),
                                obstacle,
                            )
                    elif obstacle.key and len(obstacle.key) > 1:
                        object_name = (
                            f"{obstacle.file_name}-{obstacle.object_id}"
                            if self._protocol.dreame_cloud and obstacle.object_id
                            else obstacle.file_name
                        )
                        _LOGGER.info(
                            "Obstacle image object name: %s",
                            object_name,
                        )
                        response = self._get_file_url(object_name, False)
                        if response:
                            response = self._protocol.cloud.get_file(response)
                            if response:
                                response = base64.b64encode(response).decode("utf-8")

                                cipher = Cipher(
                                    algorithms.AES(
                                        bytearray.fromhex(hashlib.md5((obstacle.key).encode("utf-8")).hexdigest())
                                    ),
                                    modes.ECB(),
                                    backend=default_backend(),
                                )
                                decryptor = cipher.decryptor()
                                unpadder = padding.PKCS7(128).unpadder()
                                return (
                                    (
                                        unpadder.update(
                                            decryptor.update(base64.b64decode(response[response.find(",") + 1 :]))
                                            + decryptor.finalize()
                                        )
                                        + unpadder.finalize()
                                    ),
                                    obstacle,
                                )
                except:
                    _LOGGER.warning(
                        "Obstacle (%s) image decryption failed: %s",
                        index,
                        traceback.format_exc(),
                    )
        return (None, None)

    def get_history_map(self, object_name, key=None):
        if object_name and len(object_name):
            try:
                _LOGGER.info(
                    "History map object name: %s",
                    object_name,
                )
                response = self._get_file_url(object_name, self._protocol.cloud.dreame_cloud)
                if response:
                    response = self._protocol.cloud.get_file(response)
                    if response:
                        map_data, saved_map_data = DreameVacuumMapDecoder.decode_map(
                            response.decode(), self._vslam_map, None, self._aes_iv, key
                        )
                        if map_data:
                            DreameVacuumMapDecoder.set_segment_cleanset(
                                map_data,
                                map_data.cleanset,
                                self._capability,
                            )
                            DreameVacuumMapDecoder.set_carpet_cleanset(
                                map_data, map_data.carpet_cleanset, self._capability
                            )
                            DreameVacuumMapDecoder.set_floor_material(map_data, self._capability)

                            map_data.history_map = True
                            if map_data.need_optimization:
                                map_data = self.optimizer.optimize(map_data, saved_map_data)
                                map_data.need_optimization = False
                            return map_data
            except Exception as ex:
                _LOGGER.warning(
                    "History map decoding failed: %s",
                    traceback.format_exc(),
                )

    def get_recovery_map(self, map_id, index):
        if map_id in self._map_list:
            recovery_map_list = self._saved_map_data[map_id].recovery_map_list
            index = int(index) - 1
            if recovery_map_list and len(recovery_map_list) > index:
                if recovery_map_list[index].map_data is None:
                    if (
                        recovery_map_list[index].raw_map is None
                        and recovery_map_list[index].map_object_name is not None
                    ):
                        try:
                            response = self._get_interim_file_data(recovery_map_list[index].map_object_name)
                            if response:
                                recovery_map_list[index].raw_map = response.decode()
                        except Exception as ex:
                            _LOGGER.warning("Get Recovery Map Object failed: %s", ex)
                            return

                    if recovery_map_list[index].raw_map:
                        recovery_map_list[index].map_data = DreameVacuumMapDecoder.decode_saved_map(
                            recovery_map_list[index].raw_map,
                            self._vslam_map,
                            self._saved_map_data[map_id].rotation,
                            self._aes_iv,
                        )
                        recovery_map_list[index].map_data.last_updated = recovery_map_list[index].date.timestamp()
                        recovery_map_list[index].map_data.recovery_map_type = recovery_map_list[index].map_type
                        recovery_map_list[index].map_data.recovery_map = True
                return recovery_map_list[index].map_data

    def get_recovery_map_file(self, map_id, index):
        if map_id in self._map_list:
            recovery_map_list = self._saved_map_data[map_id].recovery_map_list
            index = int(index) - 1
            if recovery_map_list and len(recovery_map_list) > index:
                object_name = recovery_map_list[index].object_name
                if object_name and object_name != "":
                    _LOGGER.info(
                        "Recovery map object name: %s",
                        object_name,
                    )
                    map_url = self._get_file_url(
                        object_name,
                        not (object_name.endswith("mb.tbz2") and not self._protocol.dreame_cloud),
                    )
                    _LOGGER.info("Recovery map file url: %s = %s", object_name, map_url)
                    if map_url:
                        return (
                            self._protocol.cloud.get_file(map_url),
                            map_url,
                            object_name,
                        )
        return None, None, None

    def listen(self, change_callback, update_callback) -> None:
        self._change_callback = change_callback
        self._update_callback = update_callback

    def listen_error(self, callback) -> None:
        self._error_callback = callback

    def disconnect(self) -> None:
        """Disconnect from map and cancel timers"""
        self._disconnected = True
        self.schedule_update(-1)
        self._update_callback = None
        self._change_callback = None
        self._error_callback = None

    def schedule_update(self, wait: float = None) -> None:
        if wait == None:
            wait = self._update_interval
        if self._update_timer is not None:
            self._update_timer.cancel()
            del self._update_timer
            self._update_timer = None
        if wait >= 0 and not self._disconnected:
            self._update_timer = Timer(wait, self._update_task)
            self._update_timer.start()

    def update(self) -> None:
        if self._update_running:
            return

        self._update_running = True

        _LOGGER.debug("Map update: %s", self._update_interval)
        try:
            if (self._map_list_object_name and self._need_map_list_request is None) or (
                self._need_map_list_request and not self._device_running
            ):
                self.request_map_list()

            if self._recovery_map_list_object_name and self._need_recovery_map_list_request:
                self.request_recovery_map_list()

            if self._need_new_map:
                self.request_new_map()
                self._need_new_map = False
            elif self._map_request_time is not None or self._need_map_request:
                self._updated_frame_id = None
                self._map_request_count = self._map_request_count + 1
                if self._map_request_count >= 6:
                    self._map_request_time = None
                    self._need_map_request = False
                elif (
                    not self._request_current_map(self._map_request_time)
                    and self._protocol.dreame_cloud
                    and self._map_request_count == 2
                    and self._map_data is None
                ):
                    object_name_result = self._protocol.cloud.get_properties(DIID(DreameVacuumProperty.OBJECT_NAME))
                    if object_name_result and MAP_PARAMETER_VALUE in object_name_result[0]:
                        self._add_cloud_map_data(
                            None, object_name_result[0][MAP_PARAMETER_VALUE], object_name_result[0].get("updateDate")
                        )
            elif not self._protocol.dreame_cloud:
                if self._map_data is None or (
                    self._device_running
                    and (time.time() - (self._current_timestamp_ms / 1000.0) > 15 or self._map_data.empty_map)
                ):
                    self._updated_frame_id = None
                    if self._map_data and not self._map_data.empty_map:
                        _LOGGER.info(
                            "Need map request: %.2f",
                            time.time() - (self._current_timestamp_ms / 1000.0),
                        )
                    if self._protocol.cloud.logged_in:
                        self._request_current_map()
                elif not self._request_map_from_cloud() and self._device_running:
                    _LOGGER.debug("No new map data received, retrying")
                    sleep(1)
                    if not self._request_map_from_cloud():
                        self.schedule_update(1)
                        _LOGGER.debug("No new map data received on second try")
            elif self._protocol.cloud.connected:
                if not self._connected:
                    self._connected = True
                    self._map_data_changed()

                if self._map_data is None or (
                    self._device_running
                    and (
                        (self._map_data.last_updated and time.time() - (self._map_data.last_updated) > 60)
                        or self._map_data.empty_map
                    )
                ):
                    if self._map_data and not self._map_data.empty_map:
                        _LOGGER.info(
                            "Need map request: %.2f",
                            time.time() - (self._map_data.last_updated),
                        )
                        self._request_map()
                    else:
                        self._request_current_map()
            elif self._connected:
                self._connected = False
                self._map_data_changed()

            if not self._available and self._connected:
                self._available = True
                self._map_data_changed()
        except Exception as ex:
            if self._available:
                _LOGGER.warning("Map update Failed: %s", traceback.format_exc())
                self._available = False
                if self._error_callback:
                    self._error_callback(DeviceUpdateFailedException(ex))

        self._ready = True
        self._update_running = False

    def set_capability(self, capability) -> None:
        if capability:
            self._capability = capability
            if not capability.lidar_navigation:
                self._vslam_map = True
            self._aes_iv = capability.key

    def set_update_interval(self, update_interval: float) -> None:
        if self._update_interval != update_interval:
            self._update_interval = update_interval
            self.schedule_update()

    def set_device_running(self, running: bool, docked: bool) -> None:
        if self._device_running != running:
            self._device_running = running

        if self._device_docked != docked:
            if docked:
                if not self._vslam_map:
                    self._request_map()
                elif self._map_data and self._map_data.saved_map_status == 1:
                    saved_map_data = self.selected_map
                    self._map_data.segments = copy.deepcopy(saved_map_data.segments)
                    self._map_data.data = copy.deepcopy(saved_map_data.data)
                    self._map_data.pixel_type = copy.deepcopy(saved_map_data.pixel_type)
                    self._map_data.dimensions = copy.deepcopy(saved_map_data.dimensions)
                    self._map_data.charger_position = copy.deepcopy(saved_map_data.charger_position)
                    self._map_data.no_go_areas = saved_map_data.no_go_areas
                    self._map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                    self._map_data.virtual_walls = saved_map_data.virtual_walls
                    self._map_data.robot_position = self._map_data.charger_position
                    self._map_data.docked = True
                    # self._map_data.restored_map = True
                    self._map_data.path = None
                    self._map_data.need_optimization = False
                    self._map_data.saved_map_status = 2
                    self._map_data.last_updated = time.time()
                    self._map_data.optimized_pixel_type = None
                    self._map_data.optimized_charger_position = None
                    self._map_data_changed()

            self._device_docked = docked
            self.schedule_update(2)

    def set_device_docked(self, device_docked: bool) -> None:
        if self._device_docked != device_docked:
            self.schedule_update(2)
        self._device_docked = device_docked

    def request_new_map(self) -> None:
        if (
            self._new_map_request_time
            and time.time() - self._new_map_request_time < 10
            and not self._protocol.dreame_cloud
        ):
            if time.time() - self._new_map_request_time > 3:
                self._new_map_request_time = time.time()
                self._request_map_from_cloud()
            return

        self._new_map_request_time = time.time()
        if self._map_data is None:
            return self._request_i_map()
        else:
            result = self._request_map()
            if result and result[MAP_PARAMETER_CODE] == 0 and not self._protocol.dreame_cloud:
                self._request_map_from_cloud()

    def request_next_map(self, request_new=False) -> None:
        self._map_request_count = 0
        self._need_map_request = True
        if request_new:
            self._need_new_map = True
        self.schedule_update(2)

    def request_next_map_list(self) -> None:
        self._need_map_list_request = True

    def request_next_recovery_map_list(self) -> None:
        self._need_recovery_map_list_request = True

    def set_map_list_object_name(self, object_name: str, md5: str = None) -> bool:
        if object_name and object_name != "":
            if self._map_list_object_name != object_name or self._map_list_md5 != md5:
                self._map_list_object_name = object_name
                if not self._device_running and self._map_list_md5 is not None:
                    self.request_next_map_list()
                    self.schedule_update(3)
                self._map_list_md5 = md5
                return True
        return False

    def set_recovery_map_list_object_name(self, object_name: str) -> bool:
        if object_name and object_name != "":
            if self._recovery_map_list_object_name != object_name:
                self._recovery_map_list_object_name = object_name
                self._need_recovery_map_list_request = True
                return True
        return False

    def request_map_list(self) -> None:
        if self._map_list_object_name and self._protocol.cloud.logged_in:
            _LOGGER.info("Get Map List: %s", self._map_list_object_name)
            try:
                response = self._get_interim_file_data(self._map_list_object_name)
            except Exception as ex:
                _LOGGER.warning("Get Map List failed: %s", ex)
                return

            if response:
                self._need_map_list_request = False
                try:
                    map_info = json.loads(response.decode())
                except:
                    _LOGGER.warning("Get Map List json parse failed")
                    return

                saved_map_list = map_info[MAP_PARAMETER_MAPSTR]
                changed = False
                now = time.time()
                map_list = {}
                if saved_map_list:
                    for v in saved_map_list:
                        raw_map = None
                        if v.get(MAP_PARAMETER_MAP):
                            raw_map = v[MAP_PARAMETER_MAP]
                        elif map_info.get("server") == 1 and "rismobj" in v:
                            try:
                                response = self._get_interim_file_data(v["rismobj"])
                                if response:
                                    raw_map = response.decode()
                            except Exception as ex:
                                _LOGGER.warning("Get Saved Map Object failed: %s", ex)
                                return

                        if raw_map:
                            try:
                                saved_map_data = DreameVacuumMapDecoder.decode_saved_map(
                                    raw_map,
                                    self._vslam_map,
                                    int(v[MAP_PARAMETER_ANGLE]) if v.get(MAP_PARAMETER_ANGLE) else 0,
                                    self._aes_iv,
                                )
                            except Exception as ex:
                                _LOGGER.error("Parse saved map failed: %s", traceback.format_exc())
                                return

                            if saved_map_data is not None:
                                name = v.get(MAP_PARAMETER_NAME)
                                saved_map_data.object_name = v.get("mapobj")
                                if name:
                                    saved_map_data.custom_name = name
                                    saved_map_data.map_name = name
                                map_list[saved_map_data.map_id] = saved_map_data

                    for map_id, saved_map_data in sorted(map_list.items()):
                        if map_id in self._saved_map_data:
                            if self._selected_map_id == map_id and self._map_data:
                                saved_map_data.cleanset = self._map_data.cleanset
                                saved_map_data.carpet_cleanset = self._map_data.carpet_cleanset
                            else:
                                saved_map_data.cleanset = self._saved_map_data[map_id].cleanset
                                saved_map_data.carpet_cleanset = self._saved_map_data[map_id].carpet_cleanset

                            DreameVacuumMapDecoder.set_segment_cleanset(
                                saved_map_data,
                                saved_map_data.cleanset,
                                self._capability,
                            )
                            DreameVacuumMapDecoder.set_carpet_cleanset(
                                saved_map_data, saved_map_data.carpet_cleanset, self._capability
                            )
                            DreameVacuumMapDecoder.set_floor_material(saved_map_data, self._capability)

                            if saved_map_data.saved_furnitures is not None:
                                saved_map_data.furnitures = saved_map_data.saved_furnitures

                            if self._saved_map_data[map_id] != saved_map_data:
                                _LOGGER.info("Saved map changed: %s", map_id)
                                changed = True
                                saved_map_data.last_updated = now
                                if saved_map_data.wifi_map_data:
                                    saved_map_data.wifi_map_data.last_updated = saved_map_data.last_updated
                                saved_map_data.recovery_map_list = self._saved_map_data[map_id].recovery_map_list
                                if self._map_data is None or self._selected_map_id != map_id:
                                    self._saved_map_data[map_id] = saved_map_data
                                else:
                                    self._saved_map_data[map_id].custom_name = saved_map_data.custom_name
                                    self._saved_map_data[map_id].rotation = saved_map_data.rotation
                            else:
                                _LOGGER.info("Saved map not changed: %s", map_id)
                        else:
                            saved_map_data.last_updated = now
                            if saved_map_data.wifi_map_data:
                                saved_map_data.wifi_map_data.last_updated = saved_map_data.last_updated
                            self._saved_map_data[map_id] = saved_map_data
                            _LOGGER.info("Add saved map: %s", map_id)
                            changed = True

                selected_map_id = map_info[MAP_PARAMETER_CURR_ID]
                current_map_list = self._saved_map_data.copy()
                for map_id in current_map_list.keys():
                    if map_id not in map_list and map_id != selected_map_id:
                        del self._saved_map_data[map_id]
                        changed = True

                if selected_map_id in self._saved_map_data and self._selected_map_id != selected_map_id:
                    self._selected_map_id = selected_map_id
                    changed = True

                if changed == True:
                    self._refresh_map_list()
                    if self._map_data:
                        self._map_data_changed(True)
                    self.request_next_recovery_map_list()

    def request_recovery_map_list(self) -> None:
        if self._recovery_map_list_object_name:
            if self._vslam_map:
                self._need_recovery_map_list_request = False
                return
            _LOGGER.info("Get Recovery Map List: %s", self._recovery_map_list_object_name)
            response = self._get_file_url(self._recovery_map_list_object_name)
            if response:
                self._need_recovery_map_list_request = False
                response = self._protocol.cloud.get_file(response)
                if response:
                    try:
                        recovery_map_list = json.loads(response.decode())
                    except:
                        _LOGGER.warning("Get Recovery Map List json parse failed")
                        return

                    changed = False
                    for recovery_map in recovery_map_list:
                        map_id = recovery_map["id"]
                        if map_id in self._map_list:
                            recovery_map_list = []
                            map_info_list = recovery_map["info"]
                            for map_info in map_info_list:
                                recovery_map_list.append(
                                    RecoveryMapInfo(
                                        map_id,
                                        map_info.get("time"),
                                        map_info.get("thb"),
                                        map_info.get("rismobj"),
                                        map_info.get("objname"),
                                        map_info.get("first", -1),
                                    )
                                )
                            if len(recovery_map_list) > 2:
                                recovery_map_list.sort(
                                    key=cmp_to_key(
                                        lambda a, b: (
                                            int(a.map_type) - int(b.map_type)
                                            if a.map_type is RecoveryMapType.EDITED
                                            and b.map_type is RecoveryMapType.BACKUP
                                            else 1 if a.date > b.date else -1
                                        )
                                    )
                                )

                            if (
                                not self._saved_map_data[map_id].recovery_map_list
                                or len(self._saved_map_data[map_id].recovery_map_list) != len(recovery_map_list)
                                or not all(
                                    self._saved_map_data[map_id].recovery_map_list[i].__dict__
                                    == recovery_map_list[i].__dict__
                                    for i in range(len(self._saved_map_data[map_id].recovery_map_list))
                                )
                            ):
                                self._saved_map_data[map_id].last_updated = time.time()
                                self._saved_map_data[map_id].recovery_map_list = recovery_map_list
                                _LOGGER.info("Saved recovery map list changed: %s", map_id)
                                changed = True

                    if changed:
                        self._refresh_recovery_map_list()
                        if self._connected:
                            self._map_data_changed(True)
                    else:
                        _LOGGER.info("Saved recovery map list not changed: %s", map_id)

    @property
    def _request_i_map_available(self) -> bool:
        return bool(
            not (
                self._map_data is not None
                and (
                    (self._map_data.saved_map_status == 0 and not self._map_data.empty_map)
                    or self._map_data.saved_map_status == 1
                    or self._map_data.restored_map
                    or self._map_data.temporary_map
                )
            )
        )

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def map_list(self) -> list[int] | None:
        return self._saved_map_data.keys()

    @property
    def map_data_list(self) -> dict[int, MapData] | None:
        return self._saved_map_data

    @property
    def selected_map(self) -> MapData | None:
        if self._map_data:
            if self._selected_map_id is not None and self._selected_map_id in self._saved_map_data:
                return self._saved_map_data[self._selected_map_id]

            if self._map_list and len(self._map_list) == 1 and self._map_list[0] in self._saved_map_data:
                return self._saved_map_data[self._map_list[0]]

    @property
    def cleaning_sequence(self) -> list | None:
        map_data = self._map_data
        return (
            [
                (k)
                for k, v in sorted(
                    map_data.segments.items(),
                    key=lambda s: (
                        s[1].order if s[1].order != None else (64 if self._capability.cleaning_sequence_v2 else 0)
                    ),
                )
                if (v.order or self._capability.cleaning_sequence_v2) and v.visibility != False
            ]
            if map_data and map_data.segments
            else []
        )


class DreameMapVacuumMapEditor:
    """Every map change must be handled on memory before actually requesting it to the device because it takes too much time to get the updated map from the cloud.
    This class handles user edits on stored map data like updating customized cleaning settings or setting active segments on segment cleaning.
    Original app has a similar class to handle the same issue (Works optimistically)"""

    def __init__(self, map_manager) -> None:
        self.map_manager: DreameMapVacuumMapManager = map_manager

    def _set_updated_frame_id(self, frame_id) -> None:
        self.map_manager._updated_frame_id = frame_id

    def _refresh_map(self, map_id: int = None) -> None:
        if map_id:
            if self._saved_map_data and map_id in self._saved_map_data:
                self._saved_map_data[map_id].last_updated = time.time()
                self.map_manager._map_data_updated()
            return
        if self._map_data is not None:
            self._map_data.last_updated = time.time()
            self.map_manager._map_data_updated()

    def refresh_map(self, map_id: int = None) -> None:
        timer = Timer(0.5, self._refresh_map, [map_id])
        timer.start()

    def set_active_areas(self, active_areas: list[list[int]]) -> None:
        map_data = self._map_data
        if map_data is not None:
            map_data.active_cruise_points = None
            map_data.active_areas = []
            for area in active_areas:
                x_coords = sorted([area[0], area[2]])
                y_coords = sorted([area[1], area[3]])
                map_data.active_areas.append(
                    Area(
                        x_coords[0],
                        y_coords[0],
                        x_coords[1],
                        y_coords[0],
                        x_coords[1],
                        y_coords[1],
                        x_coords[0],
                        y_coords[1],
                    )
                )
            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()

    def set_active_segments(self, active_segments: list[int]) -> None:
        map_data = self._map_data
        if map_data is not None:
            map_data.active_segments = active_segments
            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()

    def set_active_points(self, active_points: list[list[int]]) -> None:
        map_data = self._map_data
        if map_data is not None:
            map_data.active_points = []
            for point in active_points:
                map_data.active_points.append(
                    Point(
                        point[0],
                        point[1],
                    )
                )
            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()

    def set_cruise_points(self, active_cruise_points: list[list[int]]) -> None:
        map_data = self._map_data
        if map_data is not None:
            map_data.active_cruise_points = {}
            index = 0
            if active_cruise_points:
                map_data.path = None
                map_data.obstacles = None
                map_data.active_areas = None
                map_data.active_segments = None
                for point in active_cruise_points:
                    index = index + 1
                    map_data.active_cruise_points[index] = Coordinate(
                        point[0],
                        point[1],
                        bool(point[2]),
                        point[3],
                    )
            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()

    def clear_path(self) -> None:
        map_data = self._map_data
        if map_data is not None:
            map_data.path = None
            # map_data.obstacles = None
            # map_data.active_cruise_points = None
            map_data.active_areas = None
            map_data.active_segments = None
            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()

    def reset_map(self) -> None:
        map_data = self._map_data
        if map_data is not None and not map_data.new_map and not map_data.empty_map:
            map_data.dimensions.width = 0
            map_data.dimensions.height = 0
            map_data.segments = {}
            map_data.floor_material = None
            map_data.carpet_cleanset = None
            map_data.hidden_segments = None
            map_data.path = None
            map_data.carpets = None
            map_data.detected_carpets = None
            map_data.deleted_carpets = None
            map_data.carpet_pixels = None
            map_data.obstacles = None
            map_data.empty_map = True
            map_data.saved_map_status = 0
            self._set_updated_frame_id(map_data.frame_id + 1)
            self.refresh_map()

    def set_rotation(self, map_id: int, rotation: int) -> None:
        if map_id in self._saved_map_data:
            self._saved_map_data[map_id].rotation = rotation
            if self.map_manager._capability.floor_material:
                DreameVacuumMapDecoder.set_floor_material(self._saved_map_data[map_id], self.map_manager._capability)
            if self._map_data is not None and map_id == self._selected_map_id:
                self._map_data.rotation = rotation
                if self.map_manager._capability.floor_material:
                    DreameVacuumMapDecoder.set_floor_material(self._map_data, self.map_manager._capability)
                self.refresh_map()
            self.refresh_map(map_id)

    def set_map_name(self, map_id: int, name: str) -> None:
        if map_id in self._saved_map_data:
            if name and len(name):
                self._saved_map_data[map_id].custom_name = name
                self._saved_map_data[map_id].map_name = name
            else:
                self._saved_map_data[map_id].custom_name = None
                self._saved_map_data[map_id].map_name = f"Map {str(self._saved_map_data[map_id].map_index)}"
            self.refresh_map(map_id)
            self.refresh_map()

    def set_selected_map(self, map_id: int) -> None:
        if map_id != self._selected_map_id:
            self.set_current_map(map_id)

    def set_current_map(self, map_id: int) -> None:
        if map_id and map_id in self._saved_map_data:
            saved_map_data = copy.deepcopy(self._saved_map_data[map_id])
            saved_map_data.docked = self._map_data.docked
            saved_map_data.timestamp_ms = self._current_timestamp_ms
            saved_map_data.frame_id = None
            saved_map_data.map_name = None
            saved_map_data.saved_map_id = map_id
            saved_map_data.custom_name = None
            saved_map_data.saved_map = False
            saved_map_data.restored_map = True
            saved_map_data.temporary_map = False
            saved_map_data.empty_map = False
            saved_map_data.saved_map_status = 2
            DreameVacuumMapDecoder.set_segment_cleanset(
                saved_map_data,
                saved_map_data.cleanset,
                self.map_manager._capability,
            )
            DreameVacuumMapDecoder.set_carpet_cleanset(
                saved_map_data, saved_map_data.carpet_cleanset, self.map_manager._capability
            )
            DreameVacuumMapDecoder.set_floor_material(saved_map_data, self.map_manager._capability)
            self.map_manager._map_data = saved_map_data
            self.map_manager._current_frame_id = None
            self.map_manager._current_map_id = map_id
            self.map_manager._selected_map_id = map_id
            self.refresh_map()
            self.refresh_map(map_id)

    def set_carpet_area(self, carpets, deleted_carpets):
        map_data = self._map_data
        if (
            not map_data
            or not self._selected_map_id
            or (map_data.carpets is None and map_data.deleted_carpets is None)
        ):
            return

        new_carpets = []
        carpet_types = [] if self.map_manager._capability.carpet_type else None
        carpet_tassels = [] if self.map_manager._capability.carpet_tassel else None
        if carpets:
            carpet_id = self.map_manager._capability.carpet_id
            if not carpet_id:  ## Fallback for older vacuum plugins that does not have carpet id indicator
                for map_carpet in map_data.carpets:
                    if map_carpet.id is not None:
                        carpet_id = True
                        break

            if carpet_id:
                carpet_id = 1
                for i in range(len(carpets)):
                    carpet = carpets[i]
                    if len(carpet) < 5 or carpet[4] < 0:
                        if self.map_manager._capability.carpet_material:
                            carpet_id = -1
                        else:
                            flag = True
                            found = False

                            while flag:
                                found = False
                                for map_carpet in map_data.carpets:
                                    if map_carpet.id == carpet_id:
                                        carpet_id = carpet_id + 1
                                        found = True
                                        break
                                flag = found

                        if len(carpet) < 5:
                            carpets[i].append(carpet_id)
                        else:
                            carpets[i][4] = carpet_id
                        carpet_id = carpet_id + 1
            else:
                for i in range(len(carpets)):
                    if len(carpets[i]) > 4:
                        carpets[i] = carpets[i][:4]

            for i in range(len(carpets)):
                carpet = carpets[i]
                carpet_type = None
                if carpet_types is not None:
                    carpet_type = 7
                    if len(carpet) > 6:
                        if (
                            carpet[6] == 5
                            or carpet[6] == 6
                            or (carpet[6] == 8 and self.map_manager._capability.floor_mats)
                        ):
                            carpet_type = carpet[6]
                    elif len(carpet) > 4 and carpet[4] >= 0:
                        for map_carpet in map_data.carpets:
                            if map_carpet.id == carpet[4]:
                                carpet_type = map_carpet.carpet_type
                                break

                    carpet_types.append([carpet[4], carpet_type])

                carpet_tassel = None
                hidden = None
                if carpet_tassels is not None:
                    hidden = 0
                    carpet_tassel = [0, 0, 0, 0, 0]
                    if len(carpet) > 4 and carpet[4] >= 0:
                        for map_carpet in map_data.carpets:
                            if map_carpet.id == carpet[4]:
                                carpet_tassel = map_carpet.tassel
                                hidden = map_carpet.hidden
                                break
                    if len(carpet) > 7 and carpet[7] and len(carpet[7]) == 5:
                        carpet_tassel = carpet[7]

                    carpet_tassels.append([carpet[4], carpet_tassel])

                new_carpets.append(
                    Carpet(
                        carpet[4] if len(carpet) > 4 else None,
                        carpet[0],
                        carpet[1],
                        carpet[2],
                        carpet[1],
                        carpet[2],
                        carpet[3],
                        carpet[0],
                        carpet[3],
                        carpet[5] if len(carpet) > 5 else None,
                        carpet_type,
                        None,
                        None,
                        None,
                        hidden,
                        carpet_tassel,
                    )
                )

                if len(carpet) > 6:  ## Remove carpet type from array to be sent to device
                    carpets[i] = carpet[:6]

        map_data.carpets = new_carpets
        DreameVacuumMapDecoder.set_carpet_cleanset(map_data, map_data.carpet_cleanset, self.map_manager._capability)

        new_deleted_carpets = []
        if deleted_carpets:
            for carpet in deleted_carpets:
                x_coords = sorted([carpet[0], carpet[2]])
                y_coords = sorted([carpet[1], carpet[3]])
                new_deleted_carpets.append(
                    Carpet(
                        None,
                        x_coords[0],
                        y_coords[0],
                        x_coords[1],
                        y_coords[0],
                        x_coords[1],
                        y_coords[1],
                        x_coords[0],
                        y_coords[1],
                    )
                )
        map_data.deleted_carpets = new_deleted_carpets

        self._saved_map_data[self._selected_map_id].carpets = map_data.carpets
        self._saved_map_data[self._selected_map_id].deleted_carpets = map_data.deleted_carpets
        self._set_updated_frame_id(map_data.frame_id)
        self.refresh_map(self._selected_map_id)
        self.refresh_map()
        return carpets, deleted_carpets, carpet_types, carpet_tassels

    def set_carpet_type(self, carpet_types) -> dict[str, list[int]]:
        map_data = self._map_data
        if (
            not map_data
            or not self._selected_map_id
            or not (map_data.detected_carpets is not None or map_data.carpets is not None)
        ):
            return

        def set_carpet_cleaning(carpet, carpet_type, object_type):
            if map_data.carpet_cleanset is not None and not (
                carpet.carpet_cleaning == 0 or carpet.carpet_cleaning is None or carpet.carpet_cleaning > 0
            ):
                if carpet_type == 7 or not self.map_manager._capability.mop_pad_unmounting:
                    carpet.carpet_cleaning = 2
                elif carpet_type == 5:
                    carpet.carpet_cleaning = 1
                elif carpet_type == 6:
                    carpet.carpet_cleaning = 3
                elif carpet_type == 8:
                    carpet.carpet_cleaning = 7

                for cleanset in map_data.carpet_cleanset:
                    if cleanset[0] == object_type and cleanset[1] == carpet.id:
                        cleanset[2] = carpet.carpet_cleaning

        carpet_type = {}
        key = "origincpt"
        for carpet in map_data.detected_carpets:
            if key in carpet_types:
                for selected_carpet in carpet_types[key]:
                    if selected_carpet[0] == carpet.id:
                        if carpet.carpet_type != selected_carpet[1]:
                            carpet.carpet_type = selected_carpet[1]
                            set_carpet_cleaning(carpet, carpet.carpet_type, 0)
                        break
            if key not in carpet_type:
                carpet_type[key] = []
            carpet_type[key].append([carpet.id, carpet.carpet_type if carpet.carpet_type else 7])

        key = "addcpt"
        for carpet in map_data.carpets:
            if key in carpet_types:
                for selected_carpet in carpet_types[key]:
                    if selected_carpet[0] == carpet.id:
                        if carpet.carpet_type != selected_carpet[1]:
                            carpet.carpet_type = selected_carpet[1]
                            set_carpet_cleaning(carpet, carpet.carpet_type, 1)
                        break
            if key not in carpet_type:
                carpet_type[key] = []
            carpet_type[key].append([carpet.id, carpet.carpet_type if carpet.carpet_type else 7])

        if self.map_manager._capability.carpet_material:
            key = "roomcpt"
            for k, v in map_data.segments.items():
                if key in carpet_types:
                    for selected_carpet in carpet_types[key]:
                        if selected_carpet[0] == k:
                            if v.floor_material != selected_carpet[1]:
                                v.floor_material = selected_carpet[1]
                                set_carpet_cleaning(v, v.floor_material, 2)
                            break
                if key not in carpet_type:
                    carpet_type[key] = []
                carpet_type[key].append([k, v.floor_material if v.floor_material else 0])

        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            self._saved_map_data[self._selected_map_id].carpet_cleanset = map_data.carpet_cleanset.copy()
            DreameVacuumMapDecoder.set_carpet_cleanset(
                self._saved_map_data[self._selected_map_id],
                self._saved_map_data[self._selected_map_id].carpet_cleanset,
                self.map_manager._capability,
            )
            self.refresh_map(self._selected_map_id)

        self._set_updated_frame_id(map_data.frame_id)
        self.refresh_map()
        return carpet_type

    def set_virtual_thresholds(self, virtual_thresholds) -> None:
        map_data = self._map_data
        if (
            not map_data
            or not self._selected_map_id
            or not (map_data.virtual_thresholds is not None or map_data.passable_thresholds is not None)
        ):
            return

        thresholds = []
        if virtual_thresholds:
            for line in virtual_thresholds:
                thresholds.append(
                    Wall(
                        line[0],
                        line[1],
                        line[2],
                        line[3],
                    )
                )

        if map_data.passable_thresholds is not None:
            map_data.passable_thresholds = thresholds
        else:
            map_data.virtual_thresholds = thresholds

        self._set_updated_frame_id(map_data.frame_id)
        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            self._saved_map_data[self._selected_map_id].virtual_thresholds = map_data.virtual_thresholds
            self._saved_map_data[self._selected_map_id].passable_thresholds = map_data.passable_thresholds
            self.refresh_map(self._selected_map_id)
        self.refresh_map()

    def set_thresholds(self, passable_thresholds, impassable_thresholds, ramps) -> None:
        map_data = self._map_data
        if not map_data or not self._selected_map_id or map_data.passable_thresholds is None:
            return

        if passable_thresholds:
            map_data.passable_thresholds = [
                Wall(
                    wall[0],
                    wall[1],
                    wall[2],
                    wall[3],
                )
                for wall in passable_thresholds
            ]
        else:
            map_data.passable_thresholds = []

        if impassable_thresholds:
            map_data.impassable_thresholds = [
                Wall(
                    wall[0],
                    wall[1],
                    wall[2],
                    wall[3],
                )
                for wall in impassable_thresholds
            ]
        else:
            map_data.impassable_thresholds = []

        map_data.ramps = []
        if ramps:
            for area in ramps:
                x_coords = sorted([area[0], area[2]])
                y_coords = sorted([area[1], area[3]])
                map_data.ramps.append(
                    Area(
                        x_coords[0],
                        y_coords[0],
                        x_coords[1],
                        y_coords[0],
                        x_coords[1],
                        y_coords[1],
                        x_coords[0],
                        y_coords[1],
                        area[4],
                    )
                )

        self._set_updated_frame_id(map_data.frame_id)
        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            self._saved_map_data[self._selected_map_id].passable_thresholds = map_data.passable_thresholds
            self._saved_map_data[self._selected_map_id].impassable_thresholds = map_data.impassable_thresholds
            self._saved_map_data[self._selected_map_id].ramps = map_data.ramps
            self.refresh_map(self._selected_map_id)
        self.refresh_map()

    def set_furnitures(self, furnitures) -> dict[str, list[int | float]]:
        map_data = self._map_data
        if not map_data or not self._selected_map_id or map_data.furnitures is None or not map_data.furniture_version:
            return

        if map_data.furniture_version >= 2:
            furniture_id = 0
            for furniture in furnitures:
                if furniture[0] < 0:
                    flag = True
                    found = False

                    while flag:
                        found = False
                        for map_furniture in map_data.furnitures.values():
                            if map_furniture.furniture_id == furniture_id:
                                furniture_id = furniture_id + 1
                                found = True
                                break
                        flag = found

                    furniture[0] = furniture_id
                    furniture_id = furniture_id + 1

        map_data.furnitures = {}
        index = 0
        for furniture in furnitures:
            if (
                furniture[1] not in FurnitureType._value2member_map_
                or (
                    map_data.furniture_version >= 2
                    and not self.map_manager._capability.extended_furnitures
                    and ((furniture[1] > 13 and furniture[1] != 25) or furniture[1] == 8)
                )
                or (map_data.furniture_version < 2 and furniture[1] >= 10)
                or (not self.map_manager._capability.pet_furniture and furniture[1] >= 10 and furniture[1] <= 13)
            ):
                continue

            map_data.furnitures[index] = Furniture(
                furniture_id=furniture[0] if map_data.furniture_version >= 2 else None,
                type=FurnitureType(furniture[1]),
                segment_id=furniture[2],
                width=furniture[3],
                height=furniture[4],
                x0=int(furniture[5] - (furniture[3] / 2)),
                y0=int(furniture[6] - (furniture[4] / 2)),
                x=furniture[5],
                y=furniture[6],
                angle=furniture[7],
                scale=furniture[8],
                edit_type=furniture[9],
                modified=furniture[10],
            )
            index = index + 1
        if map_data.furniture_version >= 2:
            return {
                "mapfurniture_v2": [
                    [
                        furniture.furniture_id,
                        25 if furniture.type.value == 8 else 8 if furniture.type.value == 25 else furniture.type.value,
                        furniture.segment_id,
                        furniture.width,
                        furniture.height,
                        0,
                        furniture.x,
                        furniture.y,
                        0,
                        furniture.angle,
                        0,
                        0,
                        furniture.scale,
                        furniture.edit_type,
                        furniture.modified,
                    ]
                    for furniture in map_data.furnitures.values()
                ]
            }
        return {
            "mapfurniture": [
                [
                    furniture.x,
                    furniture.y,
                    furniture.type.value,
                    furniture.edit_type,
                    furniture.x0,
                    furniture.y0,
                    furniture.width,
                    furniture.height,
                    furniture.angle,
                    furniture.scale,
                ]
                for furniture in map_data.furnitures.values()
            ],
            "mfet": [1 if furniture.modified else 0 for furniture in map_data.furnitures.values()],
        }

    def set_curtains(self, curtains) -> None:
        map_data = self._map_data
        if not map_data or not self._selected_map_id or map_data.curtains is None:
            return

        map_data.curtains = []
        for line in curtains:
            map_data.curtains.append(
                Wall(
                    line[0],
                    line[1],
                    line[2],
                    line[3],
                )
            )

        self._set_updated_frame_id(map_data.frame_id)
        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            self._saved_map_data[self._selected_map_id].curtains = map_data.curtains
            self.refresh_map(self._selected_map_id)
        self.refresh_map()

    def set_predefined_points(self, predefined_points) -> None:
        map_data = self._map_data
        if not map_data or not self._selected_map_id or map_data.predefined_points is None:
            return

        map_data.predefined_points = []
        if predefined_points:
            for point in predefined_points:
                map_data.predefined_points.append(
                    Coordinate(
                        point[0],
                        point[1],
                        bool(point[2]),
                        point[3],
                    )
                )

        self._saved_map_data[self._selected_map_id].predefined_points = map_data.predefined_points
        self._set_updated_frame_id(map_data.frame_id)
        self.refresh_map(self._selected_map_id)
        self.refresh_map()
        return

    def set_obstacle_ignore(self, x, y, obstacle_ignored):
        map_data = self._map_data
        if not map_data or not map_data.obstacles:
            return

        for k, v in map_data.obstacles.items():
            if int(v.x) == int(x) and int(v.y) == int(y):
                map_data.obstacles[k].ignore_status = (
                    ObstacleIgnoreStatus.MANUALLY_IGNORED
                    if bool(obstacle_ignored)
                    else ObstacleIgnoreStatus.NOT_IGNORED
                )
                break

        self._set_updated_frame_id(map_data.frame_id)
        self.refresh_map()
        return

    def set_router_position(self, x, y):
        map_data = self._map_data
        if not map_data or not self._selected_map_id or map_data.router_position is None:
            return

        router_position = Point(int(x), int(y))
        self._saved_map_data[self._selected_map_id].router_position = router_position
        if self._saved_map_data[self._selected_map_id].wifi_map_data:
            self._saved_map_data[self._selected_map_id].wifi_map_data.router_position = router_position
        map_data.router_position = router_position
        if map_data.wifi_map_data:
            map_data.wifi_map_data.router_position = router_position
        self._set_updated_frame_id(map_data.frame_id)
        self.refresh_map(self._selected_map_id)
        self.refresh_map()
        return

    def delete_map(self, map_id: int = None) -> None:
        map_data = self._map_data
        if map_data and map_data.temporary_map:
            return

        if map_id is None:
            self.map_manager._map_data = None
            self.map_manager._selected_map_id = None
            self.map_manager._updated_frame_id = None
            self.map_manager._saved_map_data = {}
            self.map_manager._refresh_map_list()
            self.map_manager.request_next_map_list()
        else:
            if self._saved_map_data and map_id not in self._saved_map_data:
                self.map_manager.schedule_update(2)
                return

            if map_data and self._selected_map_id == map_id:
                if len(self.map_manager._map_list) >= 2:
                    for id in reversed(self.map_manager._saved_map_data.keys()):
                        if id != map_id:
                            del self.map_manager._saved_map_data[map_id]
                            self.map_manager._refresh_map_list()
                            self.set_current_map(id)
                            break
                else:
                    del self.map_manager._saved_map_data[map_id]
                    self.map_manager._map_data = None
                    self._updated_frame_id = None
                    self.map_manager._selected_map_id = None
                    self.map_manager._refresh_map_list()
            else:
                del self.map_manager._saved_map_data[map_id]
                self.map_manager._refresh_map_list()

            self.map_manager.request_next_map_list()

    def save_temporary_map(self) -> None:
        if self._map_data and self._map_data.temporary_map:
            self._map_data.temporary_map = False
            self.refresh_map()
            self.map_manager.request_next_map_list()

    def discard_temporary_map(self) -> None:
        if self._map_data and self._map_data.temporary_map and self._selected_map_id:
            self.set_current_map(self._selected_map_id)
            self.map_manager.request_next_map_list()

    def replace_temporary_map(self, map_id: int = None) -> None:
        map_data = self._map_data
        if map_data and map_data.temporary_map:
            if not map_id and self._selected_map_id:
                map_id = self._selected_map_id

            if map_id in self._saved_map_data:
                new_map = copy.deepcopy(map_data)
                new_map.map_id = new_map.saved_map_id
                new_map.saved_map_id = None
                new_map.saved_map_status = -1
                new_map.saved_map = True
                new_map.cleanset = {}
                self.map_manager._saved_map_data[new_map.map_id] = new_map
                del self.map_manager._saved_map_data[map_id]
                self.map_manager._refresh_map_list()

                map_data.saved_map_id = new_map.map_id
                if map_data.saved_map_id and map_data.saved_map_id in self._saved_map_data:
                    map_data.map_index = self._saved_map_data[map_data.saved_map_id].map_index
                else:
                    map_data.map_index = 0
                map_data.temporary_map = False
                map_data.saved_map = False
                map_data.saved_map_status = 0
                map_data.restored_map = True
                map_data.empty_map = False
                map_data.cleanset = {}
                DreameVacuumMapDecoder.set_segment_cleanset(
                    map_data,
                    map_data.cleanset,
                    self.map_manager._capability,
                )
                DreameVacuumMapDecoder.set_carpet_cleanset(
                    map_data, map_data.carpet_cleanset, self.map_manager._capability
                )
                DreameVacuumMapDecoder.set_floor_material(map_data, self.map_manager._capability)
                self.map_manager._map_data = map_data
                self.map_manager._selected_map_id = new_map.map_id
                self.map_manager.request_next_map_list()
                self.refresh_map()

    def restore_map(self, recovery_map_info: RecoveryMapInfo) -> None:
        if recovery_map_info and recovery_map_info.map_id in self.map_manager._map_list:
            self.map_manager.schedule_update(15)

            if recovery_map_info.raw_map is None and recovery_map_info.map_object_name is not None:
                try:
                    response = self._get_interim_file_data(recovery_map_info.map_object_name)
                    if response:
                        recovery_map_info.raw_map = response.decode()
                except Exception as ex:
                    _LOGGER.warning("Get Recovery Map Object failed: %s", ex)
                    return

            recovery_map_data = (
                (
                    DreameVacuumMapDecoder.decode_saved_map(
                        recovery_map_info.raw_map,
                        self.map_manager._vslam_map,
                        self._saved_map_data[recovery_map_info.map_id].rotation,
                        self.map_manager._aes_iv,
                    )
                )
                if recovery_map_info.map_data is None
                else recovery_map_info.map_data
            )
            recovery_map_data.recovery_map = False
            recovery_map_data.saved_map = True
            recovery_map_data.map_name = self._saved_map_data[recovery_map_info.map_id].map_name
            recovery_map_data.custom_name = self._saved_map_data[recovery_map_info.map_id].custom_name
            recovery_map_data.rotation = self._saved_map_data[recovery_map_info.map_id].rotation
            recovery_map_data.map_index = self._saved_map_data[recovery_map_info.map_id].map_index
            recovery_map_data.recovery_map_list = self._saved_map_data[recovery_map_info.map_id].recovery_map_list
            recovery_map_data.timestamp_ms = self._saved_map_data[recovery_map_info.map_id].timestamp_ms
            recovery_map_data.last_updated = time.time()
            if recovery_map_data.wifi_map:
                recovery_map_data.wifi_map.last_updated = time.time()

            self._saved_map_data[recovery_map_info.map_id] = recovery_map_data
            self.refresh_map(recovery_map_info.map_id)
            if recovery_map_info.map_id == self._selected_map_id:
                self.set_current_map(recovery_map_info.map_id)
                # self._map_data.restored_map = False
                DreameVacuumMapDecoder.set_floor_material(self._map_data, self.map_manager._capability)

            self.map_manager._map_request_count = 0
            self.map_manager._map_request_time = None
            self.map_manager._need_map_request = True
            self.map_manager._need_map_list_request = True

    def set_cleaning_sequence(self, cleaning_sequence: list[int]) -> list[int] | None:
        map_data = self._map_data
        if map_data and map_data.segments and not map_data.temporary_map:
            cleaning_sequence_v2 = self.map_manager._capability.cleaning_sequence_v2
            new_cleaning_sequence = []

            if cleaning_sequence_v2 and not cleaning_sequence:
                cleaning_sequence = [v.id for v in map_data.segments.values()]

            if cleaning_sequence:
                index = len(cleaning_sequence) + 1
                for k in map_data.segments.keys():
                    if k not in cleaning_sequence:
                        if cleaning_sequence_v2:
                            map_data.segments[k].order = index
                            index = index + 1
                        else:
                            map_data.segments[k].order = 0
                            map_data.cleanset[str(k)][3] = 0

                index = 1
                for k in cleaning_sequence:
                    if int(k) in map_data.segments.keys():
                        map_data.segments[k].order = index
                        if not cleaning_sequence_v2:
                            map_data.cleanset[str(k)][3] = index
                        new_cleaning_sequence.append(k)
                        index = index + 1
            else:
                for k in map_data.segments.keys():
                    map_data.segments[k].order = 0
                    map_data.cleanset[str(k)][3] = 0

            if cleaning_sequence_v2:
                map_data.cleaning_sequence = {
                    str(k): map_data.segments[k].order
                    for k in sorted(map_data.segments.keys(), key=lambda k: map_data.segments[k].id)
                    if map_data.segments[k].visibility != False
                }

            if self._saved_map_data and map_data.map_id in self._saved_map_data:
                if cleaning_sequence_v2:
                    self._saved_map_data[self._selected_map_id].cleaning_sequence = map_data.cleaning_sequence.copy()
                else:
                    self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)

            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()
            return self.map_manager.cleaning_sequence

    def set_segment_order(self, segment_id: int, order: int) -> list[int] | None:
        if order is None or (isinstance(order, str) and not order.isnumeric()):
            order = 0
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments and not map_data.temporary_map:
            cleaning_sequence_v2 = self.map_manager._capability.cleaning_sequence_v2
            if not order and cleaning_sequence_v2:
                order = max([v.order for v in map_data.segments.values() if v.order]) + 1

            if order > 0:
                current_order = map_data.segments[segment_id].order
                if current_order != order:
                    map_data.segments[segment_id].order = order
                    if not cleaning_sequence_v2:
                        map_data.cleanset[str(segment_id)][3] = order
                    for k, v in map_data.segments.items():
                        if k != segment_id and v.order == order:
                            map_data.segments[k].order = (
                                (len(self.map_manager.cleaning_sequence) + 1) if not current_order else current_order
                            )
            else:
                map_data.segments[segment_id].order = 0

            index = 1
            for k in self.map_manager.cleaning_sequence:
                if map_data.segments[k].order or cleaning_sequence_v2:
                    map_data.segments[k].order = index
                    if not cleaning_sequence_v2:
                        map_data.cleanset[str(k)][3] = index
                    index = index + 1
                else:
                    map_data.cleanset[str(k)][3] = 0

            if cleaning_sequence_v2:
                map_data.cleaning_sequence = {
                    str(k): map_data.segments[k].order
                    for k in sorted(map_data.segments.keys(), key=lambda k: map_data.segments[k].id)
                }

            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                if cleaning_sequence_v2:
                    self._saved_map_data[self._selected_map_id].cleaning_sequence = map_data.cleaning_sequence.copy()
                else:
                    self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)

            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()

            return self.map_manager.cleaning_sequence

    def set_floor_material(self, floor_material: dict[str, list], map_id) -> Any:
        if self._saved_map_data and map_id in self._saved_map_data:
            map_data = self._saved_map_data[map_id]
            if map_data.segments and not self._map_data.temporary_map:
                carpet_type = {}
                for segment_id in map_data.segments.keys():
                    key = str(segment_id)
                    if key in floor_material and len(floor_material[key]) == 2:
                        map_data.segments[segment_id].floor_material = floor_material[key][0]
                        if self.map_manager._capability.floor_direction_cleaning and floor_material[key][0] == 1:
                            map_data.segments[segment_id].floor_material_direction = floor_material[key][1]
                            map_data.segments[segment_id].floor_material_rotated_direction = (
                                floor_material[key][1]
                                if map_data.rotation == 0 or map_data.rotation == 180
                                else 90 if floor_material[key][1] == 0 else 0
                            )
                        else:
                            map_data.segments[segment_id].floor_material_direction = None
                            map_data.segments[segment_id].floor_material_rotated_direction = None
                    else:
                        map_data.segments[segment_id].floor_material = 0
                        map_data.segments[segment_id].floor_material_direction = None
                        map_data.segments[segment_id].floor_material_rotated_direction = None

                    DreameVacuumMapDecoder.set_segment_floor_material(
                        map_data, segment_id, map_data.floor_material, self.map_manager._capability
                    )

                if self._map_data and map_id == self._selected_map_id:
                    map_data = self._map_data
                    if map_data.segments:
                        for segment_id in map_data.segments.keys():
                            key = str(segment_id)
                            if key in floor_material and len(floor_material[key]) == 2:
                                material = floor_material[key][0]
                                if (
                                    self.map_manager._capability.carpet_material
                                    and map_data.segments[segment_id].floor_material != material
                                    and (
                                        (material >= 5 and material <= 6)
                                        or (
                                            map_data.segments[segment_id].floor_material >= 5
                                            and map_data.segments[segment_id].floor_material <= 6
                                            and material == 7
                                        )
                                    )
                                ):
                                    carpet_type[segment_id] = material
                                    if map_data.carpet_cleanset is not None and not (
                                        map_data.segments[segment_id].carpet_cleaning == 0
                                        or map_data.segments[segment_id].carpet_cleaning is None
                                        or map_data.segments[segment_id].carpet_cleaning > 0
                                    ):
                                        if material == 7 or not self.map_manager._capability.mop_pad_unmounting:
                                            map_data.segments[segment_id].carpet_cleaning = 2
                                        elif material == 5:
                                            map_data.segments[segment_id].carpet_cleaning = 1
                                        elif material == 6:
                                            map_data.segments[segment_id].carpet_cleaning = 3

                                        for cleanset in map_data.carpet_cleanset:
                                            if cleanset[0] == 2 and cleanset[1] == segment_id:
                                                cleanset[2] = map_data.segments[segment_id].carpet_cleaning

                                map_data.segments[segment_id].floor_material = material
                                if self.map_manager._capability.floor_direction_cleaning and material == 1:
                                    map_data.segments[segment_id].floor_material_direction = floor_material[key][1]
                                    map_data.segments[segment_id].floor_material_rotated_direction = (
                                        floor_material[key][1]
                                        if map_data.rotation == 0 or map_data.rotation == 180
                                        else 90 if floor_material[key][1] == 0 else 0
                                    )
                                else:
                                    map_data.segments[segment_id].floor_material_direction = None
                                    map_data.segments[segment_id].floor_material_rotated_direction = None
                            else:
                                map_data.segments[segment_id].floor_material = 0
                                map_data.segments[segment_id].floor_material_direction = None
                                map_data.segments[segment_id].floor_material_rotated_direction = None

                            DreameVacuumMapDecoder.set_segment_floor_material(
                                map_data,
                                segment_id,
                                map_data.floor_material,
                                self.map_manager._capability,
                            )

                        self._saved_map_data[map_id].carpet_cleanset = map_data.carpet_cleanset.copy()
                        DreameVacuumMapDecoder.set_carpet_cleanset(
                            self._saved_map_data[map_id],
                            self._saved_map_data[map_id].carpet_cleanset,
                            self.map_manager._capability,
                        )

                        self._set_updated_frame_id(map_data.frame_id)
                        self.refresh_map()

                self.refresh_map(map_id)

                return {
                    str(k): (
                        {
                            "material": v.floor_material,
                            "direction": v.floor_material_direction,
                        }
                        if v.floor_material_direction is not None
                        and self.map_manager._capability.floor_direction_cleaning
                        else {
                            "material": v.floor_material if k not in carpet_type else 6 if carpet_type[k] == 7 else 7
                        }
                    )
                    for k, v in self._saved_map_data[map_id].segments.items()
                }, ([[k, v] for k, v in carpet_type.items()] if carpet_type else None)
        return {}, None

    def set_hidden_segments(self, hidden_segments, map_id):
        if self._saved_map_data and map_id in self._saved_map_data:
            map_data = self._saved_map_data[map_id]
            if map_data.segments and not self._map_data.temporary_map:
                for segment_id, segment in map_data.segments.items():
                    segment.visibility = segment_id not in hidden_segments
                    if not segment.visibility:
                        segment.order = None

                    if self._map_data and map_id == self._selected_map_id:
                        if segment.visibility and segment_id not in self._map_data.segments:
                            self._map_data.segments[segment_id] = copy.deepcopy(segment)

                hidden_segments = [k for k, v in map_data.segments.items() if v.visibility == False]
                hidden_segments.sort()
                map_data.hidden_segments = hidden_segments
                DreameVacuumMapDecoder.set_segment_cleanset(
                    map_data,
                    map_data.cleanset,
                    self.map_manager._capability,
                )

                if self._map_data and map_id == self._selected_map_id:
                    map_data = self._map_data
                    if map_data.segments:
                        map_data.hidden_segments = hidden_segments
                        for segment_id, segment in map_data.segments.items():
                            segment.visibility = segment_id not in hidden_segments
                            if not segment.visibility:
                                segment.order = None

                        DreameVacuumMapDecoder.set_segment_cleanset(
                            map_data,
                            map_data.cleanset,
                            self.map_manager._capability,
                        )
                        self._set_updated_frame_id(map_data.frame_id)
                        self.refresh_map()
                self.refresh_map(map_id)
                return hidden_segments
        return []

    def set_mop_type(self, mop_type, map_id):
        if self._saved_map_data and map_id in self._saved_map_data:
            map_data = self._saved_map_data[map_id]
            if map_data.segments and not self._map_data.temporary_map:
                for segment_id, segment in map_data.segments.items():
                    if segment_id in mop_type and mop_type[segment_id]:
                        mop = mop_type[segment_id].upper()
                        if mop == "A" or mop == "B" or mop == "C":
                            segment.mop_type = mop

                mop_types = {
                    str(k): (1 if v.mop_type == "C" else 2 if v.mop_type == "B" else 3)
                    for k, v in dict(sorted(map_data.segments.items())).items()
                }
                map_data.mop_type = mop_types

                DreameVacuumMapDecoder.set_segment_cleanset(
                    map_data,
                    map_data.cleanset,
                    self.map_manager._capability,
                )

                if self._map_data and map_id == self._selected_map_id:
                    map_data = self._map_data
                    if map_data.segments:
                        map_data.mop_type = mop_types
                        for segment_id, segment in map_data.segments.items():
                            if segment_id in mop_type and mop_type[segment_id]:
                                mop = mop_type[segment_id].upper()
                                if mop == "A" or mop == "B" or mop == "C":
                                    segment.mop_type = mop

                        DreameVacuumMapDecoder.set_segment_cleanset(
                            map_data,
                            map_data.cleanset,
                            self.map_manager._capability,
                        )
                        self._set_updated_frame_id(map_data.frame_id)
                        self.refresh_map()
                self.refresh_map(map_id)
                return mop_types
        return {}

    def set_segment_type(self, segment_type, map_id):
        if self._saved_map_data and map_id in self._saved_map_data:
            map_data = self._saved_map_data[map_id]
            if map_data.segments and not self._map_data.temporary_map:
                segment_info = {}
                for segment_id, segment in map_data.segments.items():
                    segment_id = str(segment_id)
                    if segment_id in segment_type and len(segment_type[segment_id]) == 3:
                        segment.type = segment_type[segment_id][0]
                        segment.index = segment_type[segment_id][1]
                        segment.custom_name = segment_type[segment_id][2]
                    else:
                        segment.type = 0
                        segment.index = 0
                        segment.custom_name = None

                    if segment.custom_name:
                        segment_info[segment_id] = {
                            MAP_PARAMETER_NAME: base64.b64encode(segment.custom_name.encode("utf-8")).decode("utf-8"),
                            MAP_REQUEST_PARAMETER_TYPE: 0,
                            MAP_REQUEST_PARAMETER_INDEX: 0,
                        }
                    elif segment.type:
                        segment_info[segment_id] = {
                            MAP_REQUEST_PARAMETER_TYPE: segment.type,
                            MAP_REQUEST_PARAMETER_INDEX: segment.index,
                        }
                    else:
                        segment_info[segment_id] = {}

                    if segment.unique_id:
                        segment_info[segment_id][MAP_REQUEST_PARAMETER_ROOM_ID] = segment.unique_id

                if self._map_data and map_id == self._selected_map_id:
                    map_data = self._map_data
                    if map_data.segments:
                        for segment_id, segment in map_data.segments.items():
                            segment_id = str(segment_id)
                            if segment_id in segment_type and len(segment_type[segment_id]) == 3:
                                segment.type = segment_type[segment_id][0]
                                segment.index = segment_type[segment_id][1]
                                segment.custom_name = segment_type[segment_id][2]
                            else:
                                segment.type = 0
                                segment.index = 0
                                segment.custom_name = None
                        self._set_updated_frame_id(map_data.frame_id)
                        self.refresh_map()

                self.refresh_map(map_id)
                return segment_info
        return {}

    def cleanset(self, map_data: MapData) -> list[list[int]] | None:
        cleanset = []
        for k, v in map_data.segments.items():
            if v.suction_level is None:
                v.suction_level = 1
            if v.water_volume is None:
                v.water_volume = 2
            if v.cleaning_times is None:
                v.cleaning_times = 1

            settings = [
                k,
                v.suction_level,
                v.wetness_level if v.wetness_level != None else v.water_volume + 1,
                v.cleaning_times,
            ]

            if self.map_manager._capability.custom_cleaning_mode:
                settings.append(v.cleaning_mode if v.cleaning_mode is not None else 2)

            if (
                self.map_manager._capability.cleaning_route
                or self.map_manager._capability.segment_mopping_type
                or self.map_manager._capability.segment_mopping_settings
            ):
                settings.append(v.mopping_settings if v.mopping_settings else 0)

            if self.map_manager._capability.mop_temperature:
                settings.append(v.mop_temperature if v.mop_temperature is not None else 0)

            if self.map_manager._capability.mop_pressure:
                if len(settings) == 6:
                    settings.extend([0, 0])
                elif len(settings) == 7:
                    settings.append(0)

                settings.append(v.mop_pressure if v.mop_pressure is not None else 1)

            cleanset.append(settings)
        return cleanset

    def set_carpet_cleanset(self, carpet_cleanset: list[list[int]]) -> None:
        DreameVacuumMapDecoder.set_carpet_cleanset(self._map_data, carpet_cleanset, self.map_manager._capability)
        self._map_data.carpet_cleanset = carpet_cleanset
        self._set_updated_frame_id(self._map_data.frame_id)
        self.refresh_map()

    def set_custom_carpet_settings(self, carpet_cleanset: list[list[int]]) -> None:
        map_data = self._map_data
        if map_data is not None and map_data.carpet_cleanset:
            cleanset = []
            new_carpet_cleanset = map_data.carpet_cleanset.copy()
            for selected_carpet in carpet_cleanset:
                for carpet in new_carpet_cleanset:
                    if carpet[0] == selected_carpet[0] and carpet[1] == selected_carpet[1]:
                        if len(carpet) > 3:
                            carpet[3] = selected_carpet[3]
                        cleanset.append(carpet.copy())
                        break
            self.set_carpet_cleanset(new_carpet_cleanset)
            carpet_cleanset = cleanset
        return carpet_cleanset

    def set_custom_carpet_cleaning(self, carpet_cleanset: list[list[int]]) -> None:
        map_data = self._map_data
        if map_data is not None and map_data.carpet_cleanset:
            cleanset = []
            new_carpet_cleanset = map_data.carpet_cleanset.copy()
            for selected_carpet in carpet_cleanset:
                for carpet in new_carpet_cleanset:
                    if carpet[0] == selected_carpet[0] and carpet[1] == selected_carpet[1]:
                        carpet[2] = selected_carpet[2]
                        item = [carpet[0], carpet[1], carpet[2]]
                        if len(carpet) > 3 and self.map_manager._capability.carpet_cleanset_v3:
                            if (
                                carpet[2] == -1
                                or len(selected_carpet) < 4
                                or selected_carpet[3] == -1
                                or selected_carpet[3] is None
                            ):
                                carpet[3] = -1
                            else:
                                carpet[3] = selected_carpet[3]
                                item.append(carpet[3])
                        cleanset.append(item)
                        break
            self.set_carpet_cleanset(new_carpet_cleanset)
            carpet_cleanset = cleanset
        return carpet_cleanset

    def set_segment_suction_level(
        self, segment_id: int, suction_level: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments and not map_data.temporary_map:
            map_data.segments[segment_id].suction_level = suction_level
            map_data.cleanset[str(segment_id)][0] = suction_level
            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_water_volume(
        self, segment_id: int, water_volume: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments:
            map_data.segments[segment_id].water_volume = water_volume
            map_data.cleanset[str(segment_id)][1] = water_volume + 1
            if map_data.segments[segment_id].custom_mopping_route is not None:
                values = DreameVacuumMapDecoder.split_mopping_settings(map_data.segments[segment_id].mopping_settings)
                if values:
                    # Set mopping mode or water volume according to the mopping effect switch
                    values[2 if map_data.segments[segment_id].custom_mopping_route == -1 else 1] = water_volume
                    map_data.segments[segment_id].mopping_settings = DreameVacuumMapDecoder.combine_mopping_settings(
                        values
                    )
                    map_data.cleanset[str(segment_id)][5] = map_data.segments[segment_id].mopping_settings

            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_wetness_level(
        self, segment_id: int, wetness_level: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments:
            wetness_level = int(wetness_level)
            map_data.cleanset[str(segment_id)][1] = wetness_level
            map_data.segments[segment_id].wetness_level = wetness_level

            if wetness_level > (14 if self.map_manager._capability.mop_clean_frequency else 26):
                map_data.segments[segment_id].water_volume = 3
            elif wetness_level < 6:
                map_data.segments[segment_id].water_volume = 1
            else:
                map_data.segments[segment_id].water_volume = 2

            if map_data.segments[segment_id].custom_mopping_route is not None:
                map_data.segments[segment_id].custom_mopping_route = 0

                values = DreameVacuumMapDecoder.split_mopping_settings(map_data.segments[segment_id].mopping_settings)
                if values:
                    values[1] = 0
                    values[2] = 0
                    map_data.segments[segment_id].mopping_settings = DreameVacuumMapDecoder.combine_mopping_settings(
                        values
                    )
                    map_data.cleanset[str(segment_id)][5] = map_data.segments[segment_id].mopping_settings

            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_cleaning_times(
        self, segment_id: int, cleaning_times: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments and not map_data.temporary_map:
            map_data.segments[segment_id].cleaning_times = cleaning_times
            map_data.cleanset[str(segment_id)][2] = cleaning_times
            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_cleaning_mode(
        self, segment_id: int, cleaning_mode: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
            and not map_data.temporary_map
            and map_data.segments[segment_id].cleaning_mode is not None
        ):
            map_data.segments[segment_id].cleaning_mode = cleaning_mode
            map_data.cleanset[str(segment_id)][4] = cleaning_mode
            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_custom_mopping_route(
        self, segment_id: int, custom_mopping_route: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments:
            if map_data.segments[segment_id].custom_mopping_route is not None:
                map_data.segments[segment_id].custom_mopping_route = custom_mopping_route
                values = DreameVacuumMapDecoder.split_mopping_settings(map_data.segments[segment_id].mopping_settings)
                if values:
                    # Set mopping effect switch or cleaning route
                    if map_data.segments[segment_id].custom_mopping_route == -1:
                        values[2] = map_data.segments[segment_id].water_volume
                        map_data.segments[segment_id].cleaning_route = 1 if values[2] == 2 else values[2]
                    else:
                        values[2] = 0
                        values[0] = custom_mopping_route + 1
                        map_data.segments[segment_id].cleaning_route = values[0]

                    map_data.segments[segment_id].mopping_settings = DreameVacuumMapDecoder.combine_mopping_settings(
                        values
                    )
                    map_data.cleanset[str(segment_id)][5] = map_data.segments[segment_id].mopping_settings

            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_cleaning_route(
        self, segment_id: int, cleaning_route: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments:
            if map_data.segments[segment_id].cleaning_route is not None:
                map_data.segments[segment_id].cleaning_route = cleaning_route
                values = DreameVacuumMapDecoder.split_mopping_settings(map_data.segments[segment_id].mopping_settings)
                if values:
                    values[2] = 0
                    values[0] = cleaning_route
                    map_data.segments[segment_id].custom_mopping_route = values[2] - 1
                    map_data.segments[segment_id].mopping_settings = DreameVacuumMapDecoder.combine_mopping_settings(
                        values
                    )
                    map_data.cleanset[str(segment_id)][5] = map_data.segments[segment_id].mopping_settings

            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_mop_temperature(
        self, segment_id: int, mop_temperature: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments and not map_data.temporary_map:
            map_data.segments[segment_id].mop_temperature = mop_temperature
            map_data.cleanset[str(segment_id)][6] = mop_temperature
            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_mop_pressure(
        self, segment_id: int, mop_pressure: int, refresh_map: bool = True
    ) -> list[list[int]] | None:
        map_data = self._map_data
        if map_data and map_data.segments and segment_id in map_data.segments and not map_data.temporary_map:
            map_data.segments[segment_id].mop_pressure = mop_pressure
            map_data.cleanset[str(segment_id)][7] = mop_pressure
            if (
                self._saved_map_data
                and self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                self._saved_map_data[self._selected_map_id].cleanset = copy.deepcopy(map_data.cleanset)
            if refresh_map:
                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return self.cleanset(map_data)

    def set_segment_floor_material(
        self, segment_id: int, floor_material: int, direction: int = None
    ) -> list[list[int]] | None:
        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            map_data = self._saved_map_data[self._selected_map_id]
            if map_data and map_data.segments:
                if direction is not None:
                    if floor_material != 1:
                        direction = None
                    elif map_data.rotation == 90 or map_data.rotation == 270:
                        direction = 0 if direction else 90

                carpet_type = {}
                if segment_id in map_data.segments:
                    if (
                        self.map_manager._capability.carpet_material
                        and map_data.segments[segment_id].floor_material != floor_material
                        and (
                            (floor_material >= 5 and floor_material <= 6)
                            or (
                                map_data.segments[segment_id].floor_material >= 5
                                and map_data.segments[segment_id].floor_material <= 6
                                and floor_material == 7
                            )
                        )
                    ):
                        carpet_type[segment_id] = floor_material

                    map_data.segments[segment_id].floor_material = floor_material
                    map_data.segments[segment_id].floor_material_direction = direction
                    if direction is not None:
                        map_data.segments[segment_id].floor_material_rotated_direction = (
                            direction
                            if map_data.rotation == 0 or map_data.rotation == 180
                            else 90 if direction == 0 else 0
                        )
                    else:
                        map_data.segments[segment_id].floor_material_rotated_direction = None
                    DreameVacuumMapDecoder.set_segment_floor_material(
                        map_data,
                        segment_id,
                        map_data.floor_material,
                        self.map_manager._capability,
                    )
                self.refresh_map(self._selected_map_id)

                map_data = self._map_data
                if map_data and not map_data.temporary_map and map_data.segments and segment_id in map_data.segments:
                    map_data.segments[segment_id].floor_material = floor_material
                    map_data.segments[segment_id].floor_material_direction = direction
                    if direction is not None:
                        map_data.segments[segment_id].floor_material_rotated_direction = (
                            direction
                            if map_data.rotation == 0 or map_data.rotation == 180
                            else 90 if direction == 0 else 0
                        )
                    else:
                        map_data.segments[segment_id].floor_material_rotated_direction = None

                    DreameVacuumMapDecoder.set_segment_floor_material(
                        map_data,
                        segment_id,
                        map_data.floor_material,
                        self.map_manager._capability,
                    )
                    self._set_updated_frame_id(map_data.frame_id)
                    self.refresh_map()

                return {
                    str(k): (
                        {
                            "material": v.floor_material,
                            "direction": v.floor_material_direction,
                        }
                        if v.floor_material_direction is not None
                        and self.map_manager._capability.floor_direction_cleaning
                        else {
                            "material": v.floor_material if k not in carpet_type else 6 if carpet_type[k] == 7 else 7
                        }
                    )
                    for k, v in self._saved_map_data[self._selected_map_id].segments.items()
                }, ([[k, v] for k, v in carpet_type.items()] if carpet_type else None)
        return {}, None

    def set_segment_visibility(self, segment_id: int, visibility: int) -> list[list[int]] | None:
        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            map_data = self._saved_map_data[self._selected_map_id]
            if map_data and map_data.segments:
                if segment_id in map_data.segments:
                    map_data.segments[segment_id].visibility = visibility
                    if not visibility:
                        map_data.segments[segment_id].order = None
                    if map_data.segments[segment_id] and segment_id not in self._map_data.segments:
                        self._map_data.segments[segment_id] = copy.deepcopy(map_data.segments[segment_id])

                hidden_segments = [k for k, v in map_data.segments.items() if v.visibility == False]
                hidden_segments.sort()
                map_data.hidden_segments = hidden_segments
                DreameVacuumMapDecoder.set_segment_cleanset(
                    map_data,
                    map_data.cleanset,
                    self.map_manager._capability,
                )
                self.refresh_map(self._selected_map_id)

                map_data = self._map_data
                if map_data and map_data.segments and not map_data.temporary_map:
                    map_data.hidden_segments = hidden_segments
                    if segment_id in map_data.segments:
                        map_data.segments[segment_id].visibility = visibility
                        if not visibility:
                            map_data.segments[segment_id].order = None

                    DreameVacuumMapDecoder.set_segment_cleanset(
                        map_data,
                        map_data.cleanset,
                        self.map_manager._capability,
                    )
                    self._set_updated_frame_id(map_data.frame_id)
                    self.refresh_map()
            return hidden_segments
        return []

    def set_segment_mop_type(self, segment_id: int, mop_type: str) -> dict[str, int] | None:
        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            map_data = self._saved_map_data[self._selected_map_id]
            if map_data and map_data.segments:
                if segment_id in map_data.segments:
                    map_data.segments[segment_id].mop_type = mop_type

                mop_types = {
                    str(k): (1 if v.mop_type == "C" else 2 if v.mop_type == "B" else 3)
                    for k, v in dict(sorted(map_data.segments.items())).items()
                }
                map_data.mop_type = mop_types
                self.refresh_map(self._selected_map_id)

                map_data = self._map_data
                if map_data and map_data.segments and not map_data.temporary_map:
                    map_data.mop_type = mop_types
                    if segment_id in map_data.segments:
                        map_data.segments[segment_id].mop_type = mop_type

                    self._set_updated_frame_id(map_data.frame_id)
                    self.refresh_map()
            return mop_types
        return {}

    def set_segment_name(self, segment_id: int, segment_type: int, custom_name: str = None) -> dict[str, Any] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
            and self._selected_map_id
            and not map_data.temporary_map
        ):
            if (
                map_data.segments[segment_id].type != segment_type
                or map_data.segments[segment_id].custom_name != custom_name
            ):
                segment_info = {}
                map_data.segments[segment_id].type = segment_type
                if segment_type == 0:
                    map_data.segments[segment_id].index = 0
                    if custom_name is not None:
                        if custom_name == "":
                            custom_name = None
                        map_data.segments[segment_id].custom_name = custom_name
                else:
                    map_data.segments[segment_id].custom_name = None
                    map_data.segments[segment_id].index = map_data.segments[segment_id].next_type_index(
                        segment_type, map_data.segments
                    )

                map_data.segments[segment_id].set_name()

                self._saved_map_data[self._selected_map_id].segments[segment_id].custom_name = map_data.segments[
                    segment_id
                ].custom_name
                self._saved_map_data[self._selected_map_id].segments[segment_id].index = map_data.segments[
                    segment_id
                ].index
                self._saved_map_data[self._selected_map_id].segments[segment_id].type = map_data.segments[
                    segment_id
                ].type
                self._saved_map_data[self._selected_map_id].segments[segment_id].set_name()
                self.refresh_map(self._selected_map_id)

                for k, v in map_data.segments.items():
                    if v.custom_name is not None:
                        segment_info[k] = {
                            MAP_PARAMETER_NAME: base64.b64encode(v.custom_name.encode("utf-8")).decode("utf-8"),
                            MAP_REQUEST_PARAMETER_TYPE: 0,
                            MAP_REQUEST_PARAMETER_INDEX: 0,
                        }
                    elif v.type:
                        segment_info[k] = {
                            MAP_REQUEST_PARAMETER_TYPE: v.type,
                            MAP_REQUEST_PARAMETER_INDEX: v.index,
                        }
                    else:
                        segment_info[k] = {}

                    if v.unique_id:
                        segment_info[k][MAP_REQUEST_PARAMETER_ROOM_ID] = v.unique_id

                self._set_updated_frame_id(map_data.frame_id)
                self.refresh_map()
                return segment_info

    def set_zones(self, virtual_walls, no_go_areas, no_mopping_areas) -> None:
        map_data = self._map_data
        if not map_data or not self._selected_map_id:
            return

        map_data.no_mopping_areas = []
        if no_mopping_areas:
            for area in no_mopping_areas:
                x_coords = sorted([area[0], area[2]])
                y_coords = sorted([area[1], area[3]])
                map_data.no_mopping_areas.append(
                    Area(
                        x_coords[0],
                        y_coords[0],
                        x_coords[1],
                        y_coords[0],
                        x_coords[1],
                        y_coords[1],
                        x_coords[0],
                        y_coords[1],
                    )
                )

        map_data.no_go_areas = []
        if no_go_areas:
            for area in no_go_areas:
                x_coords = sorted([area[0], area[2]])
                y_coords = sorted([area[1], area[3]])
                map_data.no_go_areas.append(
                    Area(
                        x_coords[0],
                        y_coords[0],
                        x_coords[1],
                        y_coords[0],
                        x_coords[1],
                        y_coords[1],
                        x_coords[0],
                        y_coords[1],
                    )
                )

        if virtual_walls:
            map_data.virtual_walls = [
                Wall(
                    wall[0],
                    wall[1],
                    wall[2],
                    wall[3],
                )
                for wall in virtual_walls
            ]
        else:
            map_data.virtual_walls = []

        self._set_updated_frame_id(map_data.frame_id)
        if (
            self._saved_map_data
            and self._selected_map_id is not None
            and self._selected_map_id in self._saved_map_data
        ):
            self._saved_map_data[self._selected_map_id].no_go_areas = map_data.no_go_areas
            self._saved_map_data[self._selected_map_id].no_mopping_areas = map_data.no_mopping_areas
            self._saved_map_data[self._selected_map_id].virtual_walls = map_data.virtual_walls
            self.refresh_map(self._selected_map_id)
        self.refresh_map()

    @property
    def _map_data(self) -> MapData | None:
        return self.map_manager._map_data

    @property
    def _saved_map_data(self) -> MapData | None:
        return self.map_manager._saved_map_data

    @property
    def _selected_map_id(self) -> int | None:
        return self.map_manager._selected_map_id

    @property
    def _current_timestamp_ms(self) -> int | None:
        return self.map_manager._current_timestamp_ms


class DreameVacuumMapDecoder:
    HEADER_SIZE = 27

    @staticmethod
    def _read_int_8(data: bytes, offset: int = 0) -> int:
        return int.from_bytes(data[offset : offset + 1], byteorder="big", signed=True)

    @staticmethod
    def _read_int_8_le(data: bytes, offset: int = 0) -> int:
        return int.from_bytes(data[offset : offset + 1], byteorder="little", signed=True)

    @staticmethod
    def _read_int_16(data: bytes, offset: int = 0) -> int:
        return int.from_bytes(data[offset : offset + 2], byteorder="big", signed=True)

    @staticmethod
    def _read_int_16_le(data: bytes, offset: int = 0) -> int:
        return int.from_bytes(data[offset : offset + 2], byteorder="little", signed=True)

    @staticmethod
    def _compare_segment_neighbors(r1: Segment, r2: Segment) -> bool:
        alen = 0
        blen = 0
        if r1.neighbors:
            alen = len(r1.neighbors)
        if r2.neighbors:
            blen = len(r2.neighbors)

        if alen == blen:
            return r1.id - r2.id

        return blen - alen

    @staticmethod
    def _compare_colors(c1: list[int], c2: list[int]) -> bool:
        return c1[1] - c2[1] if c1[1] != c2[1] else c1[0] - c2[0]

    @staticmethod
    def _get_pixel_type(map_data: MapData, pixel, vslam_map: bool = False) -> tuple[MapPixelType, bool]:
        if map_data.frame_map:
            carpet = bool((pixel & 0x03) == 3)
            segment_id = pixel >> 2

            if 0 < segment_id < 64:
                if segment_id == 63:
                    return (MapPixelType.WALL.value, carpet)
                if segment_id == 62:
                    return (MapPixelType.FLOOR.value, carpet)
                if segment_id == 61:
                    return (MapPixelType.UNKNOWN.value, carpet)
                return (segment_id, carpet)

            segment_id = pixel & 0x03
            # as implemented on the app
            if segment_id == 1 or segment_id == 3:
                return (MapPixelType.NEW_SEGMENT.value, carpet)
            if segment_id == 2:
                return (MapPixelType.WALL.value, carpet)
        elif vslam_map:
            carpet = bool((pixel & 0x03) == 3)
            segment_id = pixel & 0x7F
            if segment_id == 1 or segment_id == 3:
                return (MapPixelType.NEW_SEGMENT.value, carpet)
            elif segment_id == 2:
                return (MapPixelType.WALL.value, carpet)
        else:
            carpet = bool((pixel & 0x40) == 64)
            segment_id = pixel & 0x3F
            if pixel >> 7:
                return (
                    (100 + segment_id) if segment_id else MapPixelType.WALL.value,
                    carpet,
                )

            # carpet = bool(pixel & 0x03 == 3)
            if segment_id > 0:
                if map_data.saved_map_status == 1 or map_data.saved_map_status == 0:
                    # as implemented on the app
                    if segment_id == 1 or segment_id == 3:
                        return (MapPixelType.NEW_SEGMENT.value, carpet)
                    if segment_id == 2:
                        return (MapPixelType.WALL.value, carpet)
                    return (MapPixelType.OUTSIDE.value, False)

                return (segment_id, carpet)

        return (MapPixelType.OUTSIDE.value, False)

    @staticmethod
    def _get_segment_center(map_data, segment_id: int, center: int, vertical: bool) -> int | None:
        # Find center point implemented as on the app
        lines = []
        zero_pixels = -1
        segment_pixel = 0
        line = None

        for k in range(map_data.dimensions.height if vertical else map_data.dimensions.width):
            pixel_type = (
                map_data.data[
                    (k * map_data.dimensions.width + center) if vertical else (center * map_data.dimensions.width + k)
                ]
                & 0x3F
            )
            if pixel_type == segment_id:
                segment_pixel = k
                zero_pixels = 0
                if line is None:
                    line = [segment_pixel]
            elif pixel_type == 0:
                if zero_pixels >= 0:
                    zero_pixels = zero_pixels + 1
                    if zero_pixels >= 4 and line is not None:
                        line.append(segment_pixel)
                        lines.append(line)
                        line = None
            elif line is not None:
                line.append(segment_pixel)
                lines.append(line)
                line = None

        if line is not None:
            line.append(segment_pixel)
            lines.append(line)
            line = None

        if lines:
            maxLine = lines[0]
            if len(lines) > 1:
                for item in lines[1:]:
                    if item[1] - item[0] > maxLine[1] - maxLine[0]:
                        maxLine = item

            return int(math.ceil((maxLine[1] - maxLine[0]) / 2 + maxLine[0]))
        return None

    @staticmethod
    def _find_px_type(x, y, map_data: MapData) -> int:
        pixel_type = map_data.pixel_type
        dimensions = map_data.dimensions
        if map_data.combined_pixel_type is not None:
            pixel_type = map_data.combined_pixel_type
            dimensions = map_data.combined_dimensions
        x = int((x - dimensions.left) / dimensions.grid_size)
        y = int((y - dimensions.top) / dimensions.grid_size)

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

        def find(xx, yy, distance, steps):
            if steps > 50:
                return 0

            for dx, dy in directions:
                nx = xx + dx * distance
                ny = yy + dy * distance
                if 0 <= nx < pixel_type.shape[0] - 1 and 0 <= ny < pixel_type.shape[1] - 1:
                    px = pixel_type[nx, ny]
                    if px is not None:
                        if 100 < px < 200:
                            px -= 100
                        if px != 255 and px != 0:
                            return int(px)
            return find(xx, yy, distance + 1, steps + 1)

        if 0 <= x < pixel_type.shape[0] - 1 and 0 <= y < pixel_type.shape[1] - 1:
            px = pixel_type[x, y]
            if px is not None:
                if 100 < px < 200:
                    px -= 100
                if px == 255 or px == 0:
                    return find(x, y, 1, 1)
                else:
                    return int(px)

        return find(x, y, 1, 1)

    @staticmethod
    def decode_map_partial(raw_data, iv=None, key=None) -> MapDataPartial | None:
        _LOGGER.debug("raw_map: %s", raw_data)
        raw_map = raw_data.replace("_", "/").replace("-", "+")

        if len(raw_map) < 3:
            return None

        if "," in raw_map and key is None:
            values = raw_map.split(",")
            key = values[1]
            raw_map = values[0]

        raw_map = base64.decodebytes(raw_map.encode("utf8"))

        if key is not None:
            if iv is None:
                iv = ""
            try:
                cipher = Cipher(
                    algorithms.AES(hashlib.sha256(key.encode()).hexdigest()[0:32].encode("utf8")),
                    modes.CBC(iv.encode("utf8")),
                    backend=default_backend(),
                )
                decryptor = cipher.decryptor()
                raw_map = decryptor.update(raw_map) + decryptor.finalize()
            except Exception as ex:
                _LOGGER.error(
                    f"Map data decryption failed: {ex}. Private key might be missing, please report this issue with your device model https://github.com/Tasshack/dreame-vacuum/issues/new?assignees=Tasshack&labels=bug&template=bug_report.md&title=Map%20data%20decryption%20failed"
                )
                return None

        try:
            raw_map = zlib.decompress(raw_map)
            if not raw_map or len(raw_map) < DreameVacuumMapDecoder.HEADER_SIZE:
                _LOGGER.error("Wrong header size for map")
                return None
        except Exception as ex:
            _LOGGER.error("Map data decompression failed: %s\n%s", ex, raw_data)
            return None

        partial_map = MapDataPartial()
        partial_map.map_id = DreameVacuumMapDecoder._read_int_16_le(raw_map)
        partial_map.frame_id = DreameVacuumMapDecoder._read_int_16_le(raw_map, 2)
        partial_map.frame_type = DreameVacuumMapDecoder._read_int_8(raw_map, 4)
        partial_map.raw = raw_map
        image_size = DreameVacuumMapDecoder.HEADER_SIZE + (
            DreameVacuumMapDecoder._read_int_16_le(raw_map, 19) * DreameVacuumMapDecoder._read_int_16_le(raw_map, 21)
        )
        if len(raw_map) >= image_size:
            try:
                data_json = json.loads(raw_map[image_size:].decode("utf8"))
                if data_json.get("timestamp_ms"):
                    partial_map.timestamp_ms = int(data_json["timestamp_ms"])

                partial_map.data_json = data_json
            except:
                pass
        return partial_map

    @staticmethod
    def decode_map(
        raw_map: str,
        vslam_map: bool,
        rotation: int = 0,
        iv: str = None,
        key: str = None,
    ) -> Tuple[MapData, Optional[MapData]]:
        return DreameVacuumMapDecoder.decode_map_data_from_partial(
            DreameVacuumMapDecoder.decode_map_partial(raw_map, iv, key),
            vslam_map,
            rotation,
        )

    @staticmethod
    def decode_saved_map(raw_map: str, vslam_map: bool, rotation: int = 0, iv: str = None) -> MapData | None:
        return DreameVacuumMapDecoder.decode_map(raw_map, vslam_map, rotation, iv)[0]

    @staticmethod
    def decode_map_data_from_partial(
        partial_map: MapDataPartial, vslam_map: bool, rotation: int = 0
    ) -> MapData | None:
        if partial_map is None:
            return

        map_data = MapData()
        map_data.map_id = partial_map.map_id
        map_data.frame_id = partial_map.frame_id
        map_data.frame_type = partial_map.frame_type
        map_data.timestamp_ms = partial_map.timestamp_ms

        raw = partial_map.raw
        map_data.robot_position = Point(
            DreameVacuumMapDecoder._read_int_16_le(raw, 5),
            DreameVacuumMapDecoder._read_int_16_le(raw, 7),
            DreameVacuumMapDecoder._read_int_16_le(raw, 9),
        )
        map_data.charger_position = Point(
            DreameVacuumMapDecoder._read_int_16_le(raw, 11),
            DreameVacuumMapDecoder._read_int_16_le(raw, 13),
            DreameVacuumMapDecoder._read_int_16_le(raw, 15),
        )

        grid_size = DreameVacuumMapDecoder._read_int_16_le(raw, 17)
        width = DreameVacuumMapDecoder._read_int_16_le(raw, 19)
        height = DreameVacuumMapDecoder._read_int_16_le(raw, 21)
        left = DreameVacuumMapDecoder._read_int_16_le(raw, 23)
        top = DreameVacuumMapDecoder._read_int_16_le(raw, 25)

        image_size = DreameVacuumMapDecoder.HEADER_SIZE + width * height
        data_json = partial_map.data_json
        if data_json is None:
            data_json = {}

        _LOGGER.debug("Map Data Json: %s", data_json)

        saved_map_data = None
        try:
            if "origin" in data_json and data_json["origin"] and len(data_json["origin"]) > 1:
                left = data_json["origin"][0]
                top = data_json["origin"][1]

            map_data.dimensions = MapImageDimensions(top, left, height, width, grid_size)

            map_data.rotation = rotation

            if map_data.frame_type != MapFrameType.W.value:
                if "mra" in data_json:
                    map_data.rotation = int(data_json["mra"])

                if "cs" in data_json:
                    map_data.cleaned_area = int(data_json["cs"])

                if "ct" in data_json:
                    value = data_json["ct"]
                    if isinstance(value, int) or isinstance(value, float) or isinstance(value, str):
                        map_data.cleaning_time = int(value)

                if "wm" in data_json:
                    map_data.work_status = int(data_json["wm"])

                if "cf" in data_json:
                    map_data.completed = bool(data_json["cf"] == 1)

                if "clean_finish_remain_electricity" in data_json:
                    map_data.remaining_battery = int(data_json["clean_finish_remain_electricity"])

                map_data.customized_cleaning = data_json.get("customeClean")
                map_data.docked = bool("oc" in data_json and data_json["oc"])
                map_data.line_to_robot = bool("l2r" in data_json and data_json["l2r"])
                map_data.frame_map = bool(data_json.get("fsm") and data_json["fsm"] == 1)
                map_data.restored_map = bool(data_json.get("rpur") and data_json["rpur"] == 1)
                map_data.saved_map_status = -1
                if "ris" in data_json:
                    map_data.saved_map_status = data_json["ris"]
                map_data.clean_log = bool(data_json.get("iscleanlog") and data_json["iscleanlog"] == True)
                map_data.recovery_map = bool("us" in data_json and data_json["us"] == 1)
                map_data.new_map = bool("risp" in data_json and data_json["risp"] == 0)
                if "smd" in data_json:
                    map_data.startup_method = (
                        StartupMethod(data_json["smd"])
                        if data_json["smd"] in StartupMethod._value2member_map_
                        else StartupMethod.OTHER
                    )
                if "ctyi" in data_json:
                    map_data.task_end_type = (
                        TaskEndType(data_json["ctyi"])
                        if data_json["ctyi"] in TaskEndType._value2member_map_
                        else TaskEndType.OTHER
                    )
                if "cmc" in data_json:
                    map_data.cleanup_method = (
                        CleanupMethod(data_json["cmc"])
                        if data_json["cmc"] in CleanupMethod._value2member_map_
                        else CleanupMethod.OTHER
                    )
                if "ds" in data_json:
                    map_data.dust_collection_count = int(data_json.get("ds", 0))
                if "wt" in data_json:
                    map_data.mop_wash_count = int(data_json.get("wt", 0))
                map_data.multiple_cleaning_time = data_json.get("multime")
                map_data.dos = data_json.get("dos")
                map_data.mopping_mode = data_json.get("mooClean")
                map_data.temporary_map = bool(
                    data_json.get("suw")
                    and (data_json["suw"] == 6 or data_json["suw"] == 5)
                    and data_json.get("fsm") is None
                )
                map_data.saved_map = bool(
                    map_data.frame_type == MapFrameType.I.value
                    and not map_data.restored_map
                    and not map_data.frame_map
                    and map_data.saved_map_status == -1
                    and not map_data.clean_log
                )

                if (data_json.get("nc") and data_json["nc"]) or map_data.charger_position.a == 32767:
                    map_data.charger_position = None

                if (data_json.get("nr") and data_json["nr"]) or map_data.robot_position.a == 32767:
                    map_data.robot_position = None

                if not map_data.saved_map and not map_data.recovery_map:
                    map_data.index = 0

                if data_json.get("tr"):
                    matches = [
                        m.groupdict()
                        for m in re.compile(r"(?P<operator>[MWSLl])(?P<x>-?\d+),(?P<y>-?\d+)").finditer(
                            data_json["tr"]
                        )
                    ]
                    current_position = Point(0, 0)
                    map_data.path = []
                    for match in matches:
                        operator = match["operator"]
                        x = int(match["x"])
                        y = int(match["y"])

                        if operator == "L":
                            current_position = Path(
                                current_position.x + x,
                                current_position.y + y,
                                PathType.LINE,
                            )
                        else:
                            # You will only get "l" paths with in a P frame.
                            # It means path is connected with the path from previous frame and it should be rendered as a line.
                            if operator == "l":
                                operator = "L"
                            current_position = Path(x, y, PathType(operator))

                        map_data.path.append(current_position)

                if data_json.get("sa") and isinstance(data_json["sa"], list):
                    map_data.active_segments = [sa[0] for sa in data_json["sa"]]

                if "delsr" in data_json:
                    map_data.hidden_segments = data_json["delsr"]

                if data_json.get("da2"):
                    if data_json["da2"].get("areas"):
                        map_data.active_areas = []
                        for area in data_json["da2"]["areas"]:
                            x_coords = sorted([area[0], area[2]])
                            y_coords = sorted([area[1], area[3]])
                            map_data.active_areas.append(
                                Area(
                                    x_coords[0],
                                    y_coords[0],
                                    x_coords[1],
                                    y_coords[0],
                                    x_coords[1],
                                    y_coords[1],
                                    x_coords[0],
                                    y_coords[1],
                                )
                            )

                if data_json.get("sp"):
                    map_data.active_points = []
                    for point in data_json["sp"]:
                        map_data.active_points.append(Point(point[0], point[1]))

                if "cleanset" in data_json:
                    map_data.cleanset = data_json["cleanset"]
                    if isinstance(map_data.cleanset, str):
                        map_data.cleanset = json.loads(map_data.cleanset)
                    map_data.sequence = True

                if "carpetcleanset" in data_json:
                    map_data.carpet_cleanset = data_json["carpetcleanset"]
                    if isinstance(map_data.carpet_cleanset, str):
                        map_data.carpet_cleanset = json.loads(map_data.carpet_cleanset)
            else:
                map_data.need_optimization = True
                map_data.wifi_map = True

            carpet_pixels = []
            map_data.empty_map = (
                map_data.frame_type == MapFrameType.I.value or map_data.frame_type == MapFrameType.W.value
            )
            if (width * height) > 0:
                map_data.data = raw[DreameVacuumMapDecoder.HEADER_SIZE : image_size]
                map_data.empty_map = bool(width == 2 and height == 2)
                if map_data.empty_map:
                    for y in range(height):
                        for x in range(width):
                            if map_data.data[(width * y) + x] > 0:
                                map_data.empty_map = False
                                break

                np.seterr(over="ignore")
                map_data.pixel_type = np.full((width, height), MapPixelType.OUTSIDE.value, dtype=np.uint8)
                if not map_data.empty_map:
                    map_data.empty_map = True
                    if map_data.frame_type == MapFrameType.W.value:
                        try:
                            for y in range(height):
                                for x in range(width):
                                    pixel = map_data.data[(width * y) + x] & 15
                                    if pixel > 0:
                                        map_data.empty_map = False
                                        map_data.pixel_type[x, y] = MapPixelType(pixel)
                        except:
                            pass
                    elif map_data.frame_type == MapFrameType.I.value:
                        if map_data.frame_map:
                            for y in range(height):
                                for x in range(width):
                                    pixel = map_data.data[(width * y) + x]
                                    if pixel > 0:
                                        if pixel & 0x03 == 3:
                                            carpet_pixels.append((x, y))
                                        map_data.empty_map = False
                                        segment_id = pixel >> 2
                                        if 0 < segment_id < 64:
                                            if segment_id == 63:
                                                map_data.pixel_type[x, y] = MapPixelType.WALL.value
                                            elif segment_id == 62:
                                                map_data.pixel_type[x, y] = MapPixelType.FLOOR.value
                                            elif segment_id == 61:
                                                map_data.pixel_type[x, y] = MapPixelType.UNKNOWN.value
                                            else:
                                                map_data.pixel_type[x, y] = segment_id
                                        else:
                                            segment_id = pixel & 0x3F
                                            if segment_id == 1 or segment_id == 3:
                                                map_data.pixel_type[x, y] = MapPixelType.NEW_SEGMENT.value
                                            elif segment_id == 2:
                                                map_data.pixel_type[x, y] = MapPixelType.WALL.value
                        elif map_data.saved_map_status == 1 or map_data.saved_map_status == 0:
                            for y in range(height):
                                for x in range(width):
                                    pixel = map_data.data[(width * y) + x]
                                    if pixel > 0:
                                        if pixel & 0x03 == 3:
                                            carpet_pixels.append((x, y))
                                        segment_id = pixel & 0x3F
                                        # as implemented on the app
                                        if segment_id == 1 or segment_id == 3:
                                            map_data.empty_map = False
                                            map_data.pixel_type[x, y] = MapPixelType.NEW_SEGMENT.value
                                        elif segment_id == 2:
                                            map_data.empty_map = False
                                            map_data.pixel_type[x, y] = MapPixelType.WALL.value
                        elif (
                            vslam_map and not map_data.saved_map and not map_data.recovery_map
                        ) or map_data.saved_map_status == 2:
                            for y in range(height):
                                for x in range(width):
                                    pixel = map_data.data[(width * y) + x]
                                    if pixel & 0x03 == 3:
                                        carpet_pixels.append((x, y))
                                    segment_id = pixel & 0x3F
                                    if segment_id > 0:
                                        map_data.empty_map = False
                                        if segment_id == 2:
                                            map_data.pixel_type[x, y] = MapPixelType.WALL.value
                                        else:
                                            map_data.pixel_type[x, y] = MapPixelType.NEW_SEGMENT.value
                        else:
                            for y in range(height):
                                for x in range(width):
                                    pixel = map_data.data[(width * y) + x]
                                    if pixel > 0:
                                        if (pixel & 0x40) == 64:
                                            carpet_pixels.append((x, y))
                                        map_data.empty_map = False
                                        segment_id = pixel & 0x3F
                                        if pixel >> 7:
                                            map_data.pixel_type[x, y] = (
                                                (100 + segment_id) if segment_id else MapPixelType.WALL.value
                                            )
                                        else:
                                            if segment_id > 0:
                                                map_data.pixel_type[x, y] = segment_id

                        if carpet_pixels:
                            map_data.carpet_pixels = carpet_pixels

                        segments = DreameVacuumMapDecoder.get_segments(map_data, vslam_map)
                        if segments and "seg_inf" in data_json:
                            seg_inf = data_json["seg_inf"]
                            for k, v in segments.items():
                                if seg_inf.get(str(k)):
                                    segment_info = seg_inf[str(k)]
                                    if segment_info.get("nei_id") is not None:
                                        segments[k].neighbors = segment_info["nei_id"]
                                    if segment_info.get("type") is not None:
                                        segments[k].type = segment_info["type"]
                                    if segment_info.get("index") is not None:
                                        segments[k].index = segment_info["index"]
                                    if segment_info.get("roomID") is not None:
                                        segments[k].unique_id = segment_info["roomID"]
                                    if segment_info.get("direction") is not None:
                                        segments[k].floor_material_direction = segment_info["direction"]
                                    if segment_info.get("material") is not None:
                                        material = segment_info["material"]
                                        if material in DreameVacuumFloorMaterial._value2member_map_:
                                            segments[k].floor_material = material
                                        elif material == 3:
                                            segments[k].floor_material = DreameVacuumFloorMaterial.WOOD.value
                                            segments[k].floor_material_direction = (
                                                DreameVacuumFloorMaterialDirection.VERTICAL.value
                                            )
                                        elif material == 4:
                                            segments[k].floor_material = DreameVacuumFloorMaterial.WOOD.value
                                            segments[k].floor_material_direction = (
                                                DreameVacuumFloorMaterialDirection.HORIZONTAL.value
                                            )
                                        else:
                                            segments[k].floor_material = DreameVacuumFloorMaterial.NONE.value
                                    if segment_info.get(MAP_PARAMETER_NAME):
                                        segments[k].custom_name = base64.b64decode(
                                            segment_info.get(MAP_PARAMETER_NAME)
                                        ).decode("utf-8")
                                    segments[k].visibility = (
                                        bool(k not in map_data.hidden_segments)
                                        if map_data.hidden_segments is not None
                                        else True
                                    )
                                    segments[k].set_name()

                        map_data.segments = segments

            if map_data.wifi_map:
                map_data.robot_position = None
                return map_data, saved_map_data

            restored_map = map_data.restored_map

            if "whmp" in data_json:
                router_position = data_json["whmp"]
                if router_position and len(router_position) > 1:
                    map_data.router_position = Point(
                        router_position[0],
                        router_position[1],
                    )

            wifi_map = data_json.get("whm")
            if map_data.saved_map and wifi_map and len(wifi_map) > 1:
                wifi_map_data = DreameVacuumMapDecoder.decode_saved_map(data_json["whm"], False, map_data.rotation)
                if wifi_map_data:
                    map_data.wifi_map_data = wifi_map_data
                    if map_data.wifi_map_data.router_position is None:
                        map_data.wifi_map_data.router_position = map_data.router_position

            if "rism" in data_json:
                _LOGGER.info("Decoding saved map: %s", map_data.map_id)
                saved_map_data = DreameVacuumMapDecoder.decode_saved_map(
                    data_json["rism"],
                    vslam_map,
                    map_data.rotation,
                )

                if saved_map_data is not None:
                    _LOGGER.info("Decoded saved map: %s -> %s", map_data.map_id, saved_map_data.map_id)
                    saved_map_data.timestamp_ms = map_data.timestamp_ms
                    map_data.saved_map_id = saved_map_data.map_id

                    if saved_map_data.temporary_map:
                        map_data.temporary_map = saved_map_data.temporary_map

                    if (
                        restored_map
                        or map_data.recovery_map
                        or (
                            map_data.saved_map_status == 2
                            and (map_data.empty_map or (not map_data.frame_map and not vslam_map))
                        )
                    ):
                        map_data.segments = copy.deepcopy(saved_map_data.segments)
                        map_data.cleaning_sequence = saved_map_data.cleaning_sequence
                        map_data.mop_type = saved_map_data.mop_type
                        if saved_map_data.floor_material is not None:
                            map_data.floor_material = copy.deepcopy(saved_map_data.floor_material)
                        if map_data.hidden_segments is None and saved_map_data.hidden_segments is not None:
                            map_data.hidden_segments = copy.deepcopy(saved_map_data.hidden_segments)

                        if map_data.saved_map_status == 2 and not map_data.frame_map:
                            left = min(map_data.dimensions.left, saved_map_data.dimensions.left)
                            top = min(map_data.dimensions.top, saved_map_data.dimensions.top)
                            width = int(
                                (
                                    max(
                                        map_data.dimensions.left
                                        + (map_data.dimensions.width * map_data.dimensions.grid_size),
                                        saved_map_data.dimensions.left
                                        + (saved_map_data.dimensions.width * saved_map_data.dimensions.grid_size),
                                    )
                                    - left
                                )
                                / saved_map_data.dimensions.grid_size
                            )
                            height = int(
                                (
                                    max(
                                        map_data.dimensions.top
                                        + (map_data.dimensions.height * map_data.dimensions.grid_size),
                                        saved_map_data.dimensions.top
                                        + (saved_map_data.dimensions.height * saved_map_data.dimensions.grid_size),
                                    )
                                    - top
                                )
                                / saved_map_data.dimensions.grid_size
                            )
                            si = int((saved_map_data.dimensions.left - left) / saved_map_data.dimensions.grid_size)
                            sj = int((saved_map_data.dimensions.top - top) / saved_map_data.dimensions.grid_size)
                            sim = si + saved_map_data.dimensions.width
                            sjm = sj + saved_map_data.dimensions.height
                            ni = int((map_data.dimensions.left - left) / map_data.dimensions.grid_size)
                            nj = int((map_data.dimensions.top - top) / map_data.dimensions.grid_size)
                            nim = ni + map_data.dimensions.width
                            njm = nj + map_data.dimensions.height
                            pixel_type = np.zeros((width, height), np.uint8)

                            for j in range(height):
                                for i in range(width):
                                    if j >= sj and i >= si and j < sjm and i < sim:
                                        saved_value = saved_map_data.data[
                                            (i - si) + ((j - sj) * saved_map_data.dimensions.width)
                                        ]
                                        segment_id = saved_value & 0x3F
                                    else:
                                        saved_value = -1
                                        segment_id = 0

                                    if map_data.restored_map and segment_id and saved_value != -1:
                                        if saved_value >> 7 == 1:
                                            pixel_type[i, j] = 255
                                        elif saved_value == 63:
                                            pixel_type[i, j] = 253
                                        else:
                                            pixel_type[i, j] = segment_id
                                    elif j >= nj and i >= ni and j < njm and i < nim:
                                        value = int(map_data.pixel_type[(i - ni), ((j - nj))])
                                        if value == 255:
                                            pixel_type[i, j] = value
                                        elif value == 253:
                                            pixel_type[i, j] = segment_id if segment_id else 254

                            map_data.combined_pixel_type = pixel_type
                            map_data.combined_dimensions = MapImageDimensions(
                                top, left, height, width, map_data.dimensions.grid_size
                            )

                            if map_data.restored_map:
                                map_data.carpet_pixels = DreameVacuumMapDecoder.get_carpets(map_data, saved_map_data)
                        else:
                            # map_data.data = saved_map_data.data
                            map_data.combined_pixel_type = saved_map_data.pixel_type
                            map_data.combined_dimensions = saved_map_data.dimensions
                            map_data.carpet_pixels = saved_map_data.carpet_pixels

                        if map_data.empty_map:
                            map_data.restored_map = False
                            restored_map = True
                            map_data.empty_map = False
                    else:
                        if saved_map_data.segments is not None:
                            if map_data.segments is None and (
                                map_data.saved_map_status == 1 or map_data.saved_map_status == 0
                            ):
                                map_data.segments = {}

                            map_data.cleaning_sequence = saved_map_data.cleaning_sequence
                            map_data.mop_type = saved_map_data.mop_type

                            for k, v in saved_map_data.segments.items():
                                if map_data.segments and k in map_data.segments:
                                    # as implemented on the app
                                    map_data.segments[k].icon = v.icon
                                    map_data.segments[k].name = v.name
                                    map_data.segments[k].custom_name = v.custom_name
                                    map_data.segments[k].type = v.type
                                    map_data.segments[k].index = v.index
                                    map_data.segments[k].unique_id = v.unique_id
                                    map_data.segments[k].neighbors = v.neighbors
                                    map_data.segments[k].floor_material = v.floor_material
                                    map_data.segments[k].floor_material_direction = v.floor_material_direction
                                    map_data.segments[k].visibility = v.visibility
                                    map_data.segments[k].color_index = v.color_index
                                    map_data.segments[k].carpet_cleaning = v.carpet_cleaning
                                    map_data.segments[k].carpet_preferences = v.carpet_preferences
                                    if map_data.saved_map_status == 2:
                                        map_data.segments[k].x = v.x
                                        map_data.segments[k].y = v.y

                    if not saved_map_data.cleanset:
                        saved_map_data.cleanset = copy.deepcopy(map_data.cleanset)

                    if (
                        (map_data.saved_map_status == 2 or map_data.docked)
                        and map_data.charger_position is None
                        and not map_data.saved_map
                        and not map_data.recovery_map
                        and saved_map_data.charger_position
                    ):
                        map_data.charger_position = saved_map_data.charger_position

                    # map_data.walls_info = saved_map_data.walls_info
                    # map_data.walls_info_new = saved_map_data.walls_info_new
                    # map_data.ai_outborders_ar_origin = saved_map_data.ai_outborders_ar_origin
                    # map_data.ai_furniture_ar_origin = saved_map_data.ai_furniture_ar_origin
                    # map_data.ai_furniture_ar_origin_v2 = saved_map_data.ai_furniture_ar_origin_v2

                    if map_data.saved_map_status == 2:
                        map_data.no_go_areas = saved_map_data.no_go_areas
                        map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                        map_data.virtual_walls = saved_map_data.virtual_walls
                        map_data.virtual_thresholds = saved_map_data.virtual_thresholds
                        map_data.passable_thresholds = saved_map_data.passable_thresholds
                        map_data.impassable_thresholds = saved_map_data.impassable_thresholds
                        map_data.ramps = saved_map_data.ramps
                        map_data.carpets = saved_map_data.carpets
                        map_data.deleted_carpets = saved_map_data.deleted_carpets
                        map_data.detected_carpets = saved_map_data.detected_carpets
                        map_data.router_position = saved_map_data.router_position
                        map_data.curtains = saved_map_data.curtains
                        map_data.hidden_segments = saved_map_data.hidden_segments
                        map_data.predefined_points = saved_map_data.predefined_points
                        map_data.router_position = saved_map_data.router_position
                        map_data.cleaning_sequence = saved_map_data.cleaning_sequence
                        map_data.mop_type = saved_map_data.mop_type

                        if map_data.clean_log:
                            map_data.wifi_map_data = DreameVacuumMapDecoder.decode_wifi_map_data(
                                map_data, saved_map_data.wifi_map_data
                            )
                        if saved_map_data.saved_furnitures is not None:
                            map_data.furnitures = saved_map_data.saved_furnitures
                            map_data.furniture_version = saved_map_data.furniture_version
                            saved_map_data.furnitures = saved_map_data.saved_furnitures

                        if vslam_map:
                            map_data.segments = copy.deepcopy(saved_map_data.segments)
                            map_data.charger_position = copy.deepcopy(saved_map_data.charger_position)

                    if not map_data.carpet_pixels:
                        map_data.carpet_pixels = DreameVacuumMapDecoder.get_carpets(map_data, saved_map_data)

            if (
                not map_data.saved_map
                and map_data.robot_position is None
                and map_data.docked
                and map_data.charger_position
            ):
                map_data.robot_position = copy.deepcopy(map_data.charger_position)

            if map_data.segments:
                DreameVacuumMapDecoder.set_station_segment(map_data)

                if not map_data.saved_map:
                    DreameVacuumMapDecoder.set_robot_segment(map_data)

                if map_data.saved_map or next(iter(map_data.segments.values())).color_index is None:
                    DreameVacuumMapDecoder.set_segment_color_index(map_data)

            if "cleanareaorder" in data_json:
                map_data.cleaning_sequence = {}
                for item in data_json["cleanareaorder"]:
                    for k, v in item.items():
                        map_data.cleaning_sequence[k] = v
                        break

                map_data.cleaning_sequence = dict(
                    sorted(map_data.cleaning_sequence.items(), key=lambda item: int(item[0]))
                )

            if "room_id_type" in data_json:
                map_data.mop_type = {}
                for k, v in data_json["room_id_type"].items():
                    if v == 1:
                        map_data.mop_type[k] = "C"
                    elif v == 2:
                        map_data.mop_type[k] = "B"
                    else:
                        map_data.mop_type[k] = "A"

            if "nopush" in data_json:
                map_data.notified = bool(data_json["nopush"])

            if "funiture_info" in data_json:
                map_data.furniture_version = 2
                map_data.saved_furnitures = {}
                index = 0
                for furniture in data_json["funiture_info"]:
                    index = index + 1
                    furniture_type = int(furniture[1])
                    if furniture_type == 8:
                        furniture_type = 25
                    elif furniture_type == 25:
                        furniture_type = 8

                    if furniture[3] > 0 and furniture[4] > 0:
                        if furniture_type in FurnitureType._value2member_map_:
                            map_data.saved_furnitures[index] = Furniture(
                                int(furniture[6]),
                                int(furniture[7]),
                                int(furniture[6] - (furniture[3] / 2)),
                                int(furniture[7] - (furniture[4] / 2)),
                                furniture[3],
                                furniture[4],
                                FurnitureType(furniture_type),
                                furniture[13] if len(furniture) >= 14 and furniture[13] else 0,
                                furniture[9],
                                furniture[12],
                                furniture[0],
                                furniture[2],
                            )
                        elif furniture_type != 27 and furniture_type != 28:  ## Missing furnitures from app
                            _LOGGER.debug("Unknown furniture type: %s", furniture_type)

            if map_data.furnitures is None:
                furniture_key = (
                    "ai_furniture_user"
                    if "ai_furniture_user" in data_json and len(data_json["ai_furniture_user"])
                    else (
                        "ai_furniture_new"
                        if "ai_furniture_new" in data_json and len(data_json["ai_furniture_new"])
                        else "ai_furniture"
                    )
                )
                if furniture_key in data_json:
                    map_data.furniture_version = (
                        1 if furniture_key == "ai_furniture_user" or furniture_key == "ai_furniture_new" else 0
                    )
                    map_data.furnitures = {}
                    index = 0
                    for furniture in data_json[furniture_key]:
                        size = len(furniture)
                        if size >= 4:
                            furniture_type = int(furniture[2])
                            index = index + 1
                            if furniture_type in FurnitureType._value2member_map_:
                                center_x = int(furniture[0])
                                center_y = int(furniture[1])
                                start_x0 = center_x
                                start_y0 = center_y
                                rect_width = 0
                                rect_height = 0
                                angle = 0
                                scale = 1.0
                                if size >= 8:
                                    map_data.furniture_version = 1
                                    start_x0 = int(furniture[4])
                                    start_y0 = int(furniture[5])
                                    rect_width = abs(int(furniture[6]))
                                    rect_height = abs(int(furniture[7]))
                                    if size >= 9:
                                        angle = float(furniture[8])
                                        if furniture_key == "ai_furniture":
                                            if angle == 180:
                                                angle = 0
                                            elif angle == 0:
                                                angle = 180
                                    if size >= 10:
                                        scale = float(furniture[9])
                                else:
                                    map_data.furniture_version = 0

                                map_data.furnitures[index] = Furniture(
                                    center_x,
                                    center_y,
                                    start_x0,
                                    start_y0,
                                    rect_width,
                                    rect_height,
                                    FurnitureType(furniture_type),
                                    int(furniture[3]),
                                    angle,
                                    scale,
                                )

            if "ai_obstacle" in data_json:
                map_data.obstacles = {}
                index = 1
                for obstacle in data_json["ai_obstacle"]:
                    size = len(obstacle)
                    if size >= 4:
                        obstacle_type = int(obstacle[2])
                        if obstacle_type not in ObstacleType._value2member_map_:
                            if obstacle_type == 160 or obstacle_type == 166:
                                continue
                            obstacle_type = ObstacleType.OBSTACLE.value

                        id = obstacle[4]
                        x = float(obstacle[0])
                        y = float(obstacle[1])
                        possibility = int(float(obstacle[3]) * 100)
                        ignore_status = (
                            int(obstacle[-1])
                            if len(str(obstacle[-1])) == 1 and (int(obstacle[-1]) >= 0 or int(obstacle[-1]) <= 4)
                            else None
                        )

                        if (
                            ignore_status == ObstacleIgnoreStatus.HIDDEN.value
                            or ignore_status == ObstacleIgnoreStatus.ERROR.value
                        ):
                            continue

                        if size >= 7 and (float(id) >= 1000 or obstacle_type == ObstacleType.BLOCKED_ROOM.value):
                            if size >= 8:
                                map_data.obstacles[str(index)] = Obstacle(
                                    x,
                                    y,
                                    ObstacleType(obstacle_type),
                                    possibility,
                                    id,
                                    obstacle[5],
                                    obstacle[6],
                                    float(obstacle[7]) * 100,
                                    float(obstacle[8]) * 100,
                                    float(obstacle[9]) * 100 if size >= 10 else None,
                                    float(obstacle[10]) * 100 if size >= 11 else None,
                                    int(obstacle[11]) if size >= 13 else 2,
                                    ignore_status,
                                )
                            else:
                                map_data.obstacles[str(index)] = Obstacle(
                                    x,
                                    y,
                                    ObstacleType(obstacle_type),
                                    possibility,
                                    id,
                                    obstacle[6],
                                    obstacle[5],
                                )
                        else:
                            map_data.obstacles[str(index)] = Obstacle(
                                x, y, ObstacleType(obstacle_type), possibility, ignore_status=ignore_status
                            )
                        index = index + 1

                DreameVacuumMapDecoder.set_obstacle_segment(map_data)

            def parseAreas(areas):
                if areas is not None:
                    map_areas = []
                    for area in areas:
                        x_coords = sorted([area[0], area[2]])
                        y_coords = sorted([area[1], area[3]])
                        map_areas.append(
                            Area(
                                x_coords[0],
                                y_coords[0],
                                x_coords[1],
                                y_coords[0],
                                x_coords[1],
                                y_coords[1],
                                x_coords[0],
                                y_coords[1],
                                area[4] if len(area) > 4 else None,
                            )
                        )
                    return map_areas

            def parseLines(lines):
                if lines is not None:
                    return [
                        Wall(
                            wall[0],
                            wall[1],
                            wall[2],
                            wall[3],
                        )
                        for wall in lines
                    ]

            def parseCarpets(carpets):
                if carpets is not None:
                    map_carpets = []
                    for carpet in carpets:
                        map_carpets.append(
                            Carpet(
                                int(carpet[4]) if len(carpet) > 4 else None,
                                carpet[0],
                                carpet[1],
                                carpet[2],
                                carpet[1],
                                carpet[2],
                                carpet[3],
                                carpet[0],
                                carpet[3],
                                carpet[5] if len(carpet) > 5 else None,
                                carpet[6] if len(carpet) > 6 else None,
                                None,
                                None,
                                None,
                                carpet[7] if len(carpet) > 7 else None,
                                carpet[8:13] if len(carpet) > 12 else None,
                            )
                        )
                    return map_carpets

            if "vw" in data_json:
                virtual_walls = data_json["vw"]
                if virtual_walls:
                    if not map_data.no_go_areas:
                        map_data.no_go_areas = parseAreas(virtual_walls.get("rect"))
                    if not map_data.no_mopping_areas:
                        map_data.no_mopping_areas = parseAreas(virtual_walls.get("mop"))
                    if not map_data.virtual_walls:
                        map_data.virtual_walls = parseLines(virtual_walls.get("line"))
                    if not map_data.carpets:
                        map_data.carpets = parseCarpets(virtual_walls.get("addcpt"))
                    if not map_data.deleted_carpets:
                        map_data.deleted_carpets = parseCarpets(virtual_walls.get("nocpt"))

            recommended_virtual_walls = data_json.get("rec_vw")
            if recommended_virtual_walls:
                map_data.recommended_area_type = recommended_virtual_walls.get("type")
                map_data.recommended_no_go_areas = parseAreas(recommended_virtual_walls.get("rect"))
                map_data.recommended_no_mopping_areas = parseAreas(recommended_virtual_walls.get("mop"))
                map_data.recommended_virtual_walls = parseLines(recommended_virtual_walls.get("line"))
                map_data.recommended_carpets = parseCarpets(recommended_virtual_walls.get("carpet"))

            if "vws" in data_json:
                virtual_thresholds = data_json["vws"]
                if not map_data.virtual_thresholds:
                    map_data.virtual_thresholds = parseLines(virtual_thresholds.get("vwsl"))
                if "npthrsd" in virtual_thresholds:
                    map_data.passable_thresholds = map_data.virtual_thresholds
                    map_data.virtual_thresholds = None

                    if not map_data.impassable_thresholds:
                        map_data.impassable_thresholds = parseLines(virtual_thresholds["npthrsd"])
                if not map_data.ramps:
                    map_data.ramps = parseAreas(virtual_thresholds.get("ramp"))
                if not map_data.cliffs:
                    map_data.cliffs = parseLines(virtual_thresholds.get("cliff"))

            recommended_virtual_thresholds = data_json.get("rec_vws")
            if recommended_virtual_thresholds:
                map_data.recommended_threshold_type = recommended_virtual_walls.get("type")
                map_data.recommended_virtual_thresholds = parseAreas(recommended_virtual_thresholds.get("vwsl"))
                if "npthrsd" in recommended_virtual_thresholds:
                    map_data.recommended_passable_thresholds = map_data.recommended_virtual_thresholds
                    map_data.recommended_virtual_thresholds = None
                    map_data.recommended_impassable_thresholds = parseLines(recommended_virtual_thresholds["npthrsd"])
                map_data.recommended_ramps = parseAreas(recommended_virtual_thresholds.get("ramp"))
                map_data.recommended_cliffs = parseLines(recommended_virtual_thresholds.get("cliff"))

            if "ct" in data_json:
                curtains = data_json["ct"]
                if isinstance(curtains, dict) and "line" in curtains and not map_data.curtains:
                    map_data.curtains = []
                    for line in curtains["line"]:
                        map_data.curtains.append(
                            Wall(
                                line[0],
                                line[1],
                                line[2],
                                line[3],
                            )
                        )

            if "carpet_polygon" in data_json and len(data_json["carpet_polygon"]):
                map_data.detected_carpets = []
                for carpet_id in data_json["carpet_polygon"]:
                    carpet = data_json["carpet_polygon"][carpet_id]
                    if len(carpet) > 0 and len(carpet[0]) >= 8:
                        coords = carpet[0]
                        x_coords = []
                        y_coords = []
                        for k in range(0, len(coords), 2):
                            x_coords.append(coords[k])
                            y_coords.append(coords[k + 1])

                        max_x = max(x_coords)
                        max_y = max(y_coords)
                        min_x = min(x_coords)
                        min_y = min(y_coords)

                        map_data.detected_carpets.append(
                            Carpet(
                                int(carpet_id),
                                min_x,
                                min_y,
                                max_x,
                                min_y,
                                max_x,
                                max_y,
                                min_x,
                                max_y,
                                False,
                                int(carpet[1]) if len(carpet) > 1 else None,
                                None,
                                None,
                                coords,
                                not (len(carpet) <= 2 or carpet[2] == 0),
                            )
                        )
            elif "carpet_info" in data_json:
                map_data.detected_carpets = []
                for carpet_id in data_json["carpet_info"]:
                    carpet = data_json["carpet_info"][carpet_id]
                    map_data.detected_carpets.append(
                        Carpet(
                            int(carpet_id),
                            carpet[0],
                            carpet[1],
                            carpet[2],
                            carpet[1],
                            carpet[2],
                            carpet[3],
                            carpet[0],
                            carpet[3],
                            carpet[6] if len(carpet) > 6 else None,
                            None,
                            carpet[5] if len(carpet) > 5 else None,
                            carpet[4],
                        )
                    )

            if ("sneak_areas_end" in data_json or "sneak_areas" in data_json) and not map_data.low_lying_areas:
                map_data.low_lying_areas = []
                areas = data_json["sneak_areas_end" if "sneak_areas_end" in data_json else "sneak_areas"]
                for area in areas:
                    coords = area["roi"]
                    x_coords = []
                    y_coords = []
                    for k in range(0, len(coords), 2):
                        x_coords.append(coords[k])
                        y_coords.append(coords[k + 1])

                    max_x = max(x_coords)
                    max_y = max(y_coords)
                    min_x = min(x_coords)
                    min_y = min(y_coords)

                    map_data.low_lying_areas.append(
                        Polygon(
                            area["id"],
                            min_x,
                            min_y,
                            max_x,
                            min_y,
                            max_x,
                            max_y,
                            min_x,
                            max_y,
                            coords,
                            area.get("type"),
                            area.get("hide"),
                            area.get("ms"),
                            area.get("area"),
                        )
                    )

            if "pointinfo" in data_json:
                points = data_json["pointinfo"]
                if points:
                    if isinstance(points, list):
                        points = points[0]
                    if not map_data.predefined_points:
                        if "spoint" in points:
                            map_data.predefined_points = []
                            for point in points["spoint"]:
                                map_data.predefined_points.append(
                                    Coordinate(
                                        point[0],
                                        point[1],
                                        bool(point[2]),
                                        point[3],
                                    )
                                )
                        else:
                            map_data.predefined_points = []

                    if "tpoint" in points and not map_data.active_cruise_points:
                        map_data.active_cruise_points = {}
                        index = 0
                        for point in points["tpoint"]:
                            index = index + 1
                            map_data.active_cruise_points[index] = Coordinate(
                                point[0],
                                point[1],
                                bool(point[2]),
                                point[3],
                            )
                elif not map_data.predefined_points:
                    map_data.predefined_points = []

            if "tpointinfo" in data_json:
                map_data.task_cruise_points = {}
                for point in data_json["tpointinfo"]:
                    index = index + 1
                    map_data.task_cruise_points[index] = Coordinate(
                        point[0],
                        point[1],
                        bool(point[2]),
                        point[3],
                    )

            if "area_clean_detail" in data_json:
                values = data_json["area_clean_detail"]
                if values:
                    map_data.blocked_segments = {
                        v[0]: ([SegmentSkipReason(v[1]), v[2], v[3]] if len(v) > 3 else [SegmentSkipReason(v[1])])
                        for v in values
                        if v[1] in SegmentSkipReason._value2member_map_
                    }

            if "decmap" in data_json or map_data.multiple_cleaning_time:
                map_data.cleaning_map_data = DreameVacuumMapDecoder.decode_cleaning_map_data(
                    map_data, data_json.get("decmap")
                )
                if map_data.cleaning_map_data:
                    map_data.cleaned_segments = map_data.cleaning_map_data.cleaned_segments
                    map_data.has_dirty_area = map_data.cleaning_map_data.has_dirty_area
                    map_data.has_cleaned_area = map_data.cleaning_map_data.has_cleaned_area

            if map_data.obstacles:
                obstacles = copy.deepcopy(map_data.obstacles)
                for k, v in obstacles.items():
                    if v.type == ObstacleType.BLOCKED_ROOM:
                        if (
                            map_data.blocked_segments
                            and v.segment_id in map_data.blocked_segments
                            and (
                                len(map_data.blocked_segments[v.segment_id]) <= 4
                                or map_data.blocked_segments[v.segment_id][4] != 0
                            )
                        ):
                            blocked_segment = map_data.blocked_segments[v.segment_id]
                            obstacle = map_data.obstacles[k]
                            obstacle.reason = blocked_segment[0]
                            if len(blocked_segment) > 1:
                                obstacle.x = blocked_segment[1]
                                obstacle.y = blocked_segment[2]
                        else:
                            del map_data.obstacles[k]

            if map_data.blocked_segments and not map_data.cleaning_map:
                for k, v in map_data.blocked_segments.items():
                    if len(v) <= 4 or v[4] != 0:
                        found = False
                        if map_data.obstacles:
                            for obstacle in map_data.obstacles.values():
                                if obstacle.type == ObstacleType.BLOCKED_ROOM and obstacle.segment_id == k:
                                    found = True
                                    break

                        if not found:
                            obstacle = Obstacle(k, 0, ObstacleType.BLOCKED_ROOM, None)
                            obstacle.reason = v[0]
                            if obstacle.segment_id in map_data.segments:
                                segment = map_data.segments[obstacle.segment_id]
                                obstacle.x = segment.x
                                obstacle.y = segment.y
                                obstacle.segment = segment.name
                                obstacle.color_index = segment.color_index

                            if len(v) > 1:
                                obstacle.x = v[1]
                                obstacle.y = v[2]

                            if not map_data.obstacles:
                                map_data.obstacles = {}
                            map_data.obstacles[str(len(map_data.obstacles) + 1 if map_data.obstacles else 1)] = (
                                obstacle
                            )

            # map_data.ai_outborders_user = data_json.get("ai_outborders_user")
            # map_data.ai_outborders = data_json.get("ai_outborders")
            # map_data.ai_outborders_new = data_json.get("ai_outborders_new")
            # map_data.ai_outborders_2d = data_json.get("ai_outborders_2d")
            # map_data.ai_outborders_ar_origin = data_json.get("ai_outborders_ar_origin")
            # map_data.ai_furniture_ar_origin = data_json.get("ai_furniture_ar_origin")
            # map_data.ai_furniture_ar_origin_v2 = data_json.get("ai_furniture_ar_origin_v2")
            # map_data.ai_furniture_warning = data_json.get("ai_furniture_warning")
            # if "walls_info" in data_json:
            #    map_data.walls_info = data_json["walls_info"]
            # if "walls_info_new" in data_json:
            #    map_data.walls_info = data_json["walls_info_new"]

            if vslam_map and not map_data.saved_map:
                map_data.need_optimization = not restored_map
        except Exception:
            _LOGGER.error("Map Parse Failed: %s", traceback.format_exc())

        return map_data, saved_map_data

    @staticmethod
    def decode_p_map_data_from_partial(
        partial_map: MapDataPartial, current_map_data: MapData, vslam_map: bool
    ) -> MapData | None:
        if partial_map.frame_type != MapFrameType.P.value:
            return None

        map_data, saved_map_data = DreameVacuumMapDecoder.decode_map_data_from_partial(
            partial_map,
            vslam_map,
        )
        if map_data is None:
            return None

        current_map_data.frame_id = map_data.frame_id
        current_map_data.robot_position = map_data.robot_position
        current_map_data.timestamp_ms = map_data.timestamp_ms
        current_map_data.docked = map_data.docked
        current_map_data.line_to_robot = map_data.line_to_robot
        current_map_data.temporary_map = map_data.temporary_map
        current_map_data.saved_map = False
        current_map_data.empty_map = False
        current_map_data.restored_map = False
        current_map_data.recovery_map = False
        current_map_data.clean_log = False

        if map_data.docked is not None:
            current_map_data.docked = map_data.docked

        if map_data.charger_position is not None and (not vslam_map or current_map_data.saved_map_status != 2):
            current_map_data.charger_position = map_data.charger_position

        if map_data.obstacles is not None:
            current_map_data.obstacles = map_data.obstacles

        if map_data.detected_carpets is not None:
            current_map_data.detected_carpets = map_data.detected_carpets

        if map_data.active_cruise_points is not None:
            current_map_data.active_cruise_points = map_data.active_cruise_points

        if map_data.low_lying_areas is not None:
            current_map_data.low_lying_areas = map_data.low_lying_areas

        if map_data.carpet_cleanset is not None:
            current_map_data.carpet_cleanset = map_data.carpet_cleanset

        # P map only returns difference between its previous frame.
        # Calculate new map size and update the buffer according to the received data at received offset.
        if map_data.data:
            current_dimensions = current_map_data.dimensions
            new_dimensions = map_data.dimensions

            # Find max image size
            grid_size = new_dimensions.grid_size
            left = min(new_dimensions.left, current_dimensions.left)
            top = min(new_dimensions.top, current_dimensions.top)
            max_left = max(
                new_dimensions.left + (new_dimensions.width * grid_size),
                current_dimensions.left + (current_dimensions.width * current_dimensions.grid_size),
            )
            max_top = max(
                new_dimensions.top + (new_dimensions.height * grid_size),
                current_dimensions.top + (current_dimensions.height * current_dimensions.grid_size),
            )

            # Calculate new image size
            width = int((max_left - left) / grid_size)
            height = int((max_top - top) / grid_size)

            # Create new buffer
            data = np.zeros((width * height), np.uint8)
            pixel_type = np.full((width, height), MapPixelType.OUTSIDE.value, dtype=np.uint8)

            # Calculate old image offset
            left_offset = int((current_dimensions.left - left) / current_dimensions.grid_size)
            top_offset = int((current_dimensions.top - top) / current_dimensions.grid_size)

            # Copy old image to buffer
            for y in range(current_dimensions.height):
                for x in range(current_dimensions.width):
                    data[(width * (top_offset + y)) + left_offset + x] = current_map_data.data[
                        (current_dimensions.width * y) + x
                    ]
                    pixel_type[left_offset + x, top_offset + y] = current_map_data.pixel_type[x, y]

            # Calculate new image offset
            left_offset = int((new_dimensions.left - left) / grid_size)
            top_offset = int((new_dimensions.top - top) / grid_size)

            # Copy new image to buffer at calculated offset
            for y in range(new_dimensions.height):
                for x in range(new_dimensions.width):
                    current_index = (new_dimensions.width * y) + x
                    if map_data.data[current_index]:
                        new_index = (width * (top_offset + y)) + left_offset + x
                        # Add current buffer value to new buffer value for finding the new pixel value
                        data[new_index] = data[new_index] + map_data.data[current_index]
                        # Calculate the new pixel type from updated buffer value
                        pixel_type[left_offset + x, top_offset + y], carpet = DreameVacuumMapDecoder._get_pixel_type(
                            current_map_data,
                            int(data[new_index]),
                            vslam_map,
                        )
                        if carpet and current_map_data.carpet_pixels is None:
                            current_map_data.carpet_pixels = []

                        if current_map_data.carpet_pixels is not None:
                            coord = (left_offset + x, top_offset + y)
                            if not carpet and coord in current_map_data.carpet_pixels:
                                current_map_data.carpet_pixels.remove(coord)
                            elif carpet and coord not in current_map_data.carpet_pixels:
                                current_map_data.carpet_pixels.append(coord)

            # Update size and buffer
            current_map_data.data = bytes(data)
            current_map_data.pixel_type = pixel_type
            current_map_data.dimensions = MapImageDimensions(top, left, height, width, grid_size)

            if vslam_map:
                current_map_data.need_optimization = True

        if map_data.path:
            # Append new paths received with P frame
            if current_map_data.path:
                current_map_data.path.extend(map_data.path)
            else:
                current_map_data.path = map_data.path

        DreameVacuumMapDecoder.set_robot_segment(current_map_data)
        DreameVacuumMapDecoder.set_station_segment(current_map_data)
        DreameVacuumMapDecoder.set_obstacle_segment(current_map_data)
        return current_map_data

    @staticmethod
    def decode_wifi_map_data(map_data, wifi_map_data):
        if (
            wifi_map_data
            and not map_data.saved_map
            and not map_data.empty_map
            and not wifi_map_data.empty_map
            and wifi_map_data.wifi_map
        ):
            wifi_map = MapData()
            wifi_map.map_id = wifi_map_data.map_id
            wifi_map.frame_id = wifi_map_data.frame_id
            wifi_map.frame_type = wifi_map_data.frame_type
            wifi_map.timestamp_ms = map_data.timestamp_ms
            wifi_map.rotation = wifi_map_data.rotation
            wifi_map.router_position = wifi_map_data.router_position
            wifi_map.charger_position = map_data.charger_position
            wifi_map.robot_position = map_data.robot_position
            wifi_map.docked = map_data.docked
            wifi_map.saved_map_status = map_data.saved_map_status
            wifi_map.need_optimization = True
            wifi_map.saved_map = False
            wifi_map.wifi_map = True
            wifi_map.last_updated = map_data.timestamp_ms / 1000.0
            if wifi_map.docked and wifi_map.robot_position is None:
                wifi_map.robot_position = map_data.charger_position

            left = min(map_data.dimensions.left, wifi_map_data.dimensions.left)
            top = min(map_data.dimensions.top, wifi_map_data.dimensions.top)
            width = int(
                (
                    max(
                        map_data.dimensions.left + (map_data.dimensions.width * map_data.dimensions.grid_size),
                        wifi_map_data.dimensions.left
                        + (wifi_map_data.dimensions.width * wifi_map_data.dimensions.grid_size),
                    )
                    - left
                )
                / wifi_map_data.dimensions.grid_size
            )
            height = int(
                (
                    max(
                        map_data.dimensions.top + (map_data.dimensions.height * map_data.dimensions.grid_size),
                        wifi_map_data.dimensions.top
                        + (wifi_map_data.dimensions.height * wifi_map_data.dimensions.grid_size),
                    )
                    - top
                )
                / wifi_map_data.dimensions.grid_size
            )
            si = int((wifi_map_data.dimensions.left - left) / wifi_map_data.dimensions.grid_size)
            sj = int((wifi_map_data.dimensions.top - top) / wifi_map_data.dimensions.grid_size)
            sim = si + wifi_map_data.dimensions.width
            sjm = sj + wifi_map_data.dimensions.height
            ni = int((map_data.dimensions.left - left) / map_data.dimensions.grid_size)
            nj = int((map_data.dimensions.top - top) / map_data.dimensions.grid_size)
            nim = ni + map_data.dimensions.width
            njm = nj + map_data.dimensions.height
            pixel_type = np.zeros((width, height), np.uint8)

            for j in range(height):
                for i in range(width):
                    if j >= nj and i >= ni and j < njm and i < nim:
                        value = int(map_data.pixel_type[(i - ni), ((j - nj))])
                        if value == 255:
                            pixel_type[i, j] = 2
                        elif value:
                            pixel_type[i, j] = max(
                                (
                                    wifi_map_data.data[(i - si) + ((j - sj) * wifi_map_data.dimensions.width)] & 15
                                    if j >= sj and i >= si and j < sjm and i < sim
                                    else 0
                                ),
                                10,
                            )

            wifi_map.pixel_type = pixel_type
            wifi_map.dimensions = MapImageDimensions(top, left, height, width, map_data.dimensions.grid_size)
            wifi_map_data.data = None
            return wifi_map
        return wifi_map_data

    @staticmethod
    def decode_cleaning_map_data(map_data, cleaning_map_str):
        partial_cleaning_map = None
        if cleaning_map_str and len(cleaning_map_str) > 1:
            partial_cleaning_map = DreameVacuumMapDecoder.decode_map_partial(cleaning_map_str)
            if partial_cleaning_map is None:
                return

        cleaning_map = MapData()
        if partial_cleaning_map:
            cleaning_map.map_id = partial_cleaning_map.map_id
            cleaning_map.frame_id = partial_cleaning_map.frame_id
            cleaning_map.frame_type = partial_cleaning_map.frame_type
            cleaning_map.timestamp_ms = partial_cleaning_map.timestamp_ms
            cleaning_map.cleaned_segments = partial_cleaning_map.data_json.get("CleanArea")
        else:
            cleaning_map.map_id = map_data.map_id
            cleaning_map.frame_id = map_data.frame_id
            cleaning_map.frame_type = map_data.frame_type
            cleaning_map.timestamp_ms = map_data.timestamp_ms

        cleaning_map.dimensions = map_data.dimensions
        cleaning_map.charger_position = map_data.charger_position
        cleaning_map.robot_position = map_data.robot_position
        cleaning_map.segments = map_data.segments
        cleaning_map.pixel_type = map_data.pixel_type.copy()
        cleaning_map.rotation = map_data.rotation
        cleaning_map.saved_map_status = map_data.saved_map_status
        cleaning_map.docked = map_data.docked
        cleaning_map.dos = map_data.dos
        cleaning_map.multiple_cleaning_time = map_data.multiple_cleaning_time
        cleaning_map.mop_wash_count = map_data.mop_wash_count
        cleaning_map.dust_collection_count = map_data.dust_collection_count
        cleaning_map.cleanup_method = map_data.cleanup_method
        cleaning_map.startup_method = map_data.startup_method
        cleaning_map.blocked_segments = map_data.blocked_segments
        cleaning_map.last_updated = map_data.timestamp_ms / 1000.0
        cleaning_map.history_map = True
        cleaning_map.saved_map = False
        cleaning_map.cleaning_map = True
        if cleaning_map.docked and cleaning_map.robot_position is None:
            cleaning_map.robot_position = map_data.charger_position

        if partial_cleaning_map:
            grid_size = DreameVacuumMapDecoder._read_int_16_le(partial_cleaning_map.raw, 17)
            width = DreameVacuumMapDecoder._read_int_16_le(partial_cleaning_map.raw, 19)
            height = DreameVacuumMapDecoder._read_int_16_le(partial_cleaning_map.raw, 21)
            left = DreameVacuumMapDecoder._read_int_16_le(partial_cleaning_map.raw, 23)
            top = DreameVacuumMapDecoder._read_int_16_le(partial_cleaning_map.raw, 25)

            data = partial_cleaning_map.raw[
                DreameVacuumMapDecoder.HEADER_SIZE : DreameVacuumMapDecoder.HEADER_SIZE + width * height
            ]

            cleaning_map.has_dirty_area = False
            cleaning_map.has_cleaned_area = False

            for y in range(height):
                for x in range(width):
                    value = data[int(y * width + x)] & 0x03
                    if value > 0:
                        xx = int(((left + (x * grid_size)) - map_data.dimensions.left) / map_data.dimensions.grid_size)
                        yy = int(((top + (y * grid_size)) - map_data.dimensions.top) / map_data.dimensions.grid_size)
                        if cleaning_map.check_point(xx, yy, True):
                            if value == 1:
                                cleaning_map.pixel_type[xx, yy] = 249
                                cleaning_map.has_cleaned_area = True
                            elif value == 2:
                                cleaning_map.pixel_type[xx, yy] = 250
                                cleaning_map.has_dirty_area = True
        return cleaning_map

    @staticmethod
    def optimize_wifi_map(map_data):
        if map_data.wifi_map:
            if map_data.need_optimization:
                map_data.optimized_pixel_type = np.copy(map_data.pixel_type)
                map_data.optimized_dimensions = map_data.dimensions
                map_data.optimized_dimensions.left = (
                    map_data.optimized_dimensions.original_left - map_data.optimized_dimensions.offset
                )
                map_data.optimized_dimensions.top = (
                    map_data.optimized_dimensions.original_top - map_data.optimized_dimensions.offset
                )

                if not map_data.empty_map:
                    for y in range(map_data.dimensions.height):
                        for x in range(map_data.dimensions.width):
                            if int(map_data.pixel_type[x, y]) > 2:
                                max_count = 0
                                max_px = -1
                                value_count = [0, 0, 0, 0]
                                for delta in range(3, 6):
                                    for n in range(y - delta, y + delta + 1):
                                        for m in range(x - delta, x + delta + 1):
                                            if (
                                                n < 0
                                                or n >= map_data.dimensions.height
                                                or m < 0
                                                or m >= map_data.dimensions.width
                                            ):
                                                continue

                                            px = int(map_data.pixel_type[m, n]) - 11
                                            if px >= 0:
                                                value_count[px] = value_count[px] + 1
                                                if value_count[px] > max_count:
                                                    max_count = value_count[px]
                                                    max_px = px

                                    if max_px >= 0:
                                        map_data.optimized_pixel_type[x, y] = MapPixelType(max_px + 11)
                                        break
                map_data.need_optimization = False
        return map_data

    @staticmethod
    def get_segments(map_data: MapData, vslam_map: bool) -> dict[str, Any]:
        segments = {}
        for y in range(map_data.dimensions.height):
            for x in range(map_data.dimensions.width):
                segment_id = int(map_data.pixel_type[x, y])
                if segment_id > 0 and segment_id < 64:
                    if segment_id not in segments:
                        segments[segment_id] = Segment(segment_id, x, y, x, y)
                        continue

                    if x < segments[segment_id].coords[0]:
                        segments[segment_id].coords[0] = x
                    elif x > segments[segment_id].coords[2]:
                        segments[segment_id].coords[2] = x

                    if y < segments[segment_id].coords[1]:
                        segments[segment_id].coords[1] = y
                    elif y > segments[segment_id].coords[3]:
                        segments[segment_id].coords[3] = y

        if segments:
            for segment in segments.values():
                x = int(math.ceil((segment.coords[2] - segment.coords[0]) / 2 + segment.coords[0]))
                y = int(math.ceil((segment.coords[3] - segment.coords[1]) / 2 + segment.coords[1]))

                if map_data.saved_map:
                    if vslam_map:
                        if map_data.pixel_type[x, y] != segment.id:
                            startI = -1
                            endI = -1
                            for i in range(map_data.dimensions.width):
                                value = map_data.pixel_type[i, y]
                                if startI == -1:
                                    if value == segment.id:
                                        startI = i
                                elif value != segment.id or i == (map_data.dimensions.width - 1):
                                    endI = i - 1
                                    break

                            if startI != -1 and endI != -1:
                                x = (endI - startI) + startI
                    else:
                        center_x = DreameVacuumMapDecoder._get_segment_center(map_data, segment.id, y, False)
                        if center_x is not None:
                            center_y = DreameVacuumMapDecoder._get_segment_center(map_data, segment.id, center_x, True)
                            if center_y is not None:
                                x = center_x
                                y = center_y

                segment.x = math.floor(
                    map_data.dimensions.left + (x * map_data.dimensions.grid_size) + (map_data.dimensions.offset)
                )
                segment.y = math.floor(
                    map_data.dimensions.top + (y * map_data.dimensions.grid_size) + (map_data.dimensions.offset)
                )
                segment.calculate_coords(map_data.dimensions)
                segment.set_name()
        return segments

    @staticmethod
    def set_robot_segment(map_data: MapData) -> None:
        if map_data.segments and map_data.saved_map_status == 2 and map_data.robot_position is not None:
            map_data.robot_segment = DreameVacuumMapDecoder._find_px_type(
                map_data.robot_position.x, map_data.robot_position.y, map_data
            )

            if map_data.robot_segment not in map_data.segments:
                map_data.robot_segment = 0
                for k, v in map_data.segments.items():
                    if v.check_point(
                        map_data.robot_position.x,
                        map_data.robot_position.y,
                        map_data.dimensions.grid_size * 4,
                    ):
                        map_data.robot_segment = k
                        break
        else:
            map_data.robot_segment = None

    @staticmethod
    def set_station_segment(map_data: MapData) -> None:
        if map_data.segments and map_data.charger_position is not None:
            map_data.station_segment = DreameVacuumMapDecoder._find_px_type(
                map_data.charger_position.x, map_data.charger_position.y, map_data
            )

            if map_data.station_segment not in map_data.segments:
                map_data.station_segment = 0
                for k, v in map_data.segments.items():
                    if v.check_point(
                        map_data.charger_position.x,
                        map_data.charger_position.y,
                        map_data.dimensions.grid_size * 4,
                    ):
                        map_data.station_segment = k
                        break
        else:
            map_data.station_segment = None

    @staticmethod
    def set_obstacle_segment(map_data: MapData) -> None:
        if map_data.segments and map_data.obstacles:
            for k, obstacle in map_data.obstacles.items():
                if obstacle.type == ObstacleType.BLOCKED_ROOM:
                    if obstacle.segment_id in map_data.segments:
                        segment = map_data.segments[obstacle.segment_id]
                        map_data.obstacles[k].x = segment.x
                        map_data.obstacles[k].y = segment.y
                        map_data.obstacles[k].segment = segment.name
                        map_data.obstacles[k].color_index = segment.color_index
                else:
                    segment = DreameVacuumMapDecoder._find_px_type(obstacle.x, obstacle.y, map_data)

                    if segment not in map_data.segments:
                        for v in map_data.segments.values():
                            if v.check_point(
                                obstacle.x,
                                obstacle.y,
                                map_data.dimensions.grid_size * 4,
                            ):
                                map_data.obstacles[k].segment = v.name
                                map_data.obstacles[k].color_index = v.color_index
                                break
                    else:
                        map_data.obstacles[k].segment = map_data.segments[segment].name
                        map_data.obstacles[k].color_index = map_data.segments[segment].color_index

    @staticmethod
    def set_segment_cleanset(
        map_data: MapData,
        cleanset: dict[str, list[int]],
        capability: DreameVacuumDeviceCapability = None,
    ) -> None:
        if map_data is not None and map_data.segments is not None:
            default_cleanset = [
                1,
                3,
                1,
                0,
            ]  # Cleanset returns empty on restored map but robot uses these default values when that happens

            if capability:
                if capability.custom_cleaning_mode:
                    default_cleanset.append(2)

                if capability.cleaning_route:
                    default_cleanset.append(33)
                elif capability.segment_mopping_type:
                    default_cleanset.append(2)
                elif capability.segment_mopping_settings:
                    default_cleanset.append(546)

                if capability.wetness_level:
                    default_cleanset[1] = 16

                if capability.mop_temperature:
                    default_cleanset.append(0)

                if capability.mop_pressure:
                    if len(default_cleanset) == 6:
                        default_cleanset.extend([0, 0])
                    elif len(default_cleanset) == 7:
                        default_cleanset.append(0)

                    default_cleanset.append(1)

            cleanset_type = CleansetType.NONE
            if cleanset is not None:
                cleanset_type = CleansetType.DEFAULT
                if len(cleanset) == 0:
                    if capability:
                        if capability.wetness_level:
                            cleanset_type = (
                                CleansetType.WETNESS_LEVEL_MAX_15
                                if capability.mop_clean_frequency
                                else CleansetType.WETNESS_LEVEL
                            )
                        elif capability.cleaning_route:
                            cleanset_type = CleansetType.CLEANING_ROUTE
                        elif capability.segment_mopping_settings:
                            cleanset_type = CleansetType.CUSTOM_MOPPING_ROUTE
                        elif capability.custom_cleaning_mode:
                            cleanset_type = CleansetType.CLEANING_MODE
                else:
                    for k, v in cleanset.items():
                        if len(v) > 5 and v[5] > 0:
                            cleanset_type = CleansetType.CLEANING_MODE
                            if capability:
                                if capability.wetness_level:
                                    cleanset_type = (
                                        CleansetType.WETNESS_LEVEL_MAX_15
                                        if capability.mop_clean_frequency
                                        else CleansetType.WETNESS_LEVEL
                                    )
                                elif capability.cleaning_route:
                                    cleanset_type = CleansetType.CLEANING_ROUTE
                                elif capability.segment_mopping_settings:
                                    cleanset_type = CleansetType.CUSTOM_MOPPING_ROUTE
                                break
                        if len(v) > 4:
                            cleanset_type = CleansetType.CLEANING_MODE
                            break

            for k, v in map_data.segments.items():
                map_data.segments[k].cleanset_type = cleanset_type
                if cleanset_type != CleansetType.NONE:
                    segment_id = str(k)
                    if segment_id not in cleanset:
                        cleanset[segment_id] = default_cleanset.copy()

                    item = cleanset[segment_id]
                    map_data.segments[k].suction_level = item[0]
                    map_data.segments[k].water_volume = (
                        item[1] - 1 if item[1] > 1 and item[1] < 5 else 1
                    )  # for some reason cleanset uses different int values for water volume
                    map_data.segments[k].cleaning_times = item[2]

                    if capability.auto_change_mop:
                        map_data.segments[k].mop_type = map_data.mop_type.get(segment_id, 1)

                    if len(item) > 4:
                        map_data.segments[k].cleaning_mode = item[4]
                        if len(item) > 5 and cleanset_type != CleansetType.CLEANING_MODE:
                            map_data.segments[k].mopping_settings = item[5]
                            # Logic for custom room mopping effect settings (mopping effect, mop pad humidity/wetness, route)
                            if item[5] > 0:
                                values = DreameVacuumMapDecoder.split_mopping_settings(
                                    map_data.segments[k].mopping_settings
                                )
                                if values:
                                    if values[2] == 0:  # Means custom mopping route enabled
                                        map_data.segments[k].custom_mopping_route = values[0] - 1
                                        map_data.segments[k].water_volume = values[1]
                                        map_data.segments[k].cleaning_route = values[0]
                                    elif values[2] <= 3:
                                        map_data.segments[k].custom_mopping_route = -1
                                        map_data.segments[k].cleaning_route = 1 if values[2] == 2 else values[2]
                                        map_data.segments[k].water_volume = values[2]

                                    if cleanset_type == CleansetType.WETNESS_LEVEL:
                                        map_data.segments[k].custom_mopping_route = 0
                                        if values[2] == 0 and values[1] == 0:
                                            map_data.segments[k].wetness_level = item[1] if item[1] else 16
                                            if map_data.segments[k].wetness_level > 26:
                                                map_data.segments[k].water_volume = 3
                                            elif map_data.segments[k].wetness_level < 6:
                                                map_data.segments[k].water_volume = 1
                                            else:
                                                map_data.segments[k].water_volume = 2
                                        elif map_data.segments[k].water_volume == 1:
                                            map_data.segments[k].wetness_level = 5
                                        elif map_data.segments[k].water_volume == 3:
                                            map_data.segments[k].wetness_level = 27
                                        else:
                                            map_data.segments[k].wetness_level = 16
                                    elif cleanset_type == CleansetType.WETNESS_LEVEL_MAX_15:
                                        map_data.segments[k].custom_mopping_route = 0
                                        if values[2] == 0 and values[1] == 0:
                                            map_data.segments[k].wetness_level = item[1] if item[1] else 10
                                            if map_data.segments[k].wetness_level > 14:
                                                map_data.segments[k].water_volume = 3
                                            elif map_data.segments[k].wetness_level < 6:
                                                map_data.segments[k].water_volume = 1
                                            else:
                                                map_data.segments[k].water_volume = 2
                                        elif map_data.segments[k].water_volume == 1:
                                            map_data.segments[k].wetness_level = 5
                                        elif map_data.segments[k].water_volume == 3:
                                            map_data.segments[k].wetness_level = 15
                                        else:
                                            map_data.segments[k].wetness_level = 10

                        if capability.mop_temperature:
                            map_data.segments[k].mop_temperature = item[6] if len(item) > 6 else 0

                        if capability.mop_pressure:
                            map_data.segments[k].mop_pressure = item[7] if len(item) > 7 else 1
                    else:
                        map_data.segments[k].mopping_settings = None
                        map_data.segments[k].cleaning_route = None
                        map_data.segments[k].custom_mopping_route = None
                        map_data.segments[k].wetness_level = None
                        map_data.segments[k].mop_pressure = None
                        map_data.segments[k].mop_temperature = None
                else:
                    map_data.segments[k].suction_level = None
                    map_data.segments[k].water_volume = None
                    map_data.segments[k].wetness_level = None
                    map_data.segments[k].cleaning_times = None
                    map_data.segments[k].order = None
                    map_data.segments[k].cleaning_mode = None
                    map_data.segments[k].mopping_settings = None
                    map_data.segments[k].cleaning_route = None
                    map_data.segments[k].custom_mopping_route = None
                    map_data.segments[k].mop_pressure = None
                    map_data.segments[k].mop_temperature = None

            if cleanset_type != CleansetType.NONE:
                cleaning_sequence_v2 = capability.cleaning_sequence_v2 and map_data.cleaning_sequence
                cleaning_sequence = map_data.cleaning_sequence if cleaning_sequence_v2 else (cleanset or {})
                hidden_segments = set(map_data.hidden_segments or [])

                sequence = sorted(
                    [
                        (int(k), v if cleaning_sequence_v2 else v[3])
                        for k, v in cleaning_sequence.items()
                        if int(k) not in hidden_segments and (cleaning_sequence_v2 or (len(v) > 3 and v[3]))
                    ],
                    key=lambda x: x[1],
                )
                ordered_keys = [k for k, v in sequence]
                for i, k in enumerate(ordered_keys, 1):
                    if k in map_data.segments:
                        map_data.segments[k].order = i

                if cleaning_sequence_v2:
                    index = len(ordered_keys) + 1
                    for k in list(sorted(map_data.segments.keys())):
                        if map_data.segments[k].order is None and map_data.segments[k].visibility != False:
                            map_data.segments[k].order = index
                            index = index + 1

    @staticmethod
    def set_carpet_cleanset(
        map_data: MapData, cleanset: list[list[int]], capability: DreameVacuumDeviceCapability = None
    ):
        if (
            map_data is not None
            and cleanset is not None
            and (map_data.detected_carpets or map_data.carpets or capability.carpet_material)
        ):
            for setting in cleanset:
                if len(setting) > 1:
                    if setting[0] == 2:
                        if capability.carpet_material:
                            if map_data.segments and setting[1] in map_data.segments:
                                map_data.segments[setting[1]].set_custom_carpet_settings(
                                    setting[2] if len(setting) > 2 else -1, setting[3] if len(setting) > 3 else None
                                )
                    else:
                        carpets = map_data.detected_carpets if setting[0] == 0 else map_data.carpets
                        if carpets:
                            for carpet in carpets:
                                if carpet.id == setting[1]:
                                    carpet.set_custom_carpet_settings(
                                        setting[2] if len(setting) > 2 else -1,
                                        setting[3] if len(setting) > 3 else None,
                                    )
                                    break

    @staticmethod
    def split_mopping_settings(value: int) -> list[int]:
        if value is not None:
            value_list = []
            for i in range(3):
                value_list.append(value & 15)
                value = value >> 4
            return value_list

    @staticmethod
    def combine_mopping_settings(values: list[int]) -> int:
        if values and len(values) == 3:
            value = 0 ^ values[2]
            value = value << 4 ^ values[1]
            return value << 4 ^ values[0]

    @staticmethod
    def set_segment_color_index(map_data: MapData) -> None:
        """Find segment color index as implemented on the app"""
        area_color_index = {}
        sorted_segments = sorted(
            map_data.segments.values(),
            key=cmp_to_key(DreameVacuumMapDecoder._compare_segment_neighbors),
        )
        for segment in sorted_segments:
            used_ids = []
            if segment.neighbors is not None:
                for nid in segment.neighbors:
                    if nid in area_color_index:
                        used_ids.append(area_color_index[nid])

            area_color_num = {}
            for i in range(4):
                area_color_num[i] = [i, 0]

            for i, j in area_color_index.items():
                area_color_num[j][1] = area_color_num[j][1] + 1

            area_color_num = sorted(
                area_color_num.values(),
                key=cmp_to_key(DreameVacuumMapDecoder._compare_colors),
            )

            for area_color in area_color_num:
                color = area_color[0]
                if color not in used_ids:
                    area_color_index[segment.id] = color
                    break

            if segment.id not in area_color_index:
                area_color_index[segment.id] = 0

        for k, v in area_color_index.items():
            map_data.segments[k].color_index = v

    @staticmethod
    def get_carpets(map_data: MapData, saved_map_data: MapData) -> list[tuple]:
        if saved_map_data and saved_map_data.carpet_pixels:
            left_offset = 0
            if saved_map_data.dimensions.left < map_data.dimensions.left:
                left_offset = int(
                    (map_data.dimensions.left - saved_map_data.dimensions.left) / map_data.dimensions.grid_size
                )
            top_offset = 0
            if saved_map_data.dimensions.top < map_data.dimensions.top:
                top_offset = int(
                    (map_data.dimensions.top - saved_map_data.dimensions.top) / map_data.dimensions.grid_size
                )

            if left_offset != 0 or top_offset != 0:
                carpet_pixels = []
                for point in saved_map_data.carpet_pixels:
                    x = point[0] - left_offset
                    y = point[1] - top_offset
                    if x >= 0 and x < map_data.dimensions.width and y >= 0 and y < map_data.dimensions.height:
                        value = int(map_data.pixel_type[x, y])
                        if value > 0:
                            carpet_pixels.append((x, y))

                return carpet_pixels
            else:
                return saved_map_data.carpet_pixels
        return None

    @staticmethod
    def set_segment_floor_material(
        map_data: MapData, segment_id: int, floor_material, capability: DreameVacuumDeviceCapability
    ) -> None:
        if floor_material is not None and map_data.segments and segment_id in map_data.segments:
            material = map_data.segments[segment_id].floor_material
            material_direction = map_data.segments[segment_id].floor_material_direction
            if material is not None:
                if material > 4:
                    if material > 7 or (
                        capability is not None and not (capability.carpet_type and capability.carpet_material)
                    ):
                        material = 0

                    floor_material[segment_id] = material
                else:
                    if capability.floor_direction_cleaning and material == 1:
                        if material_direction is None:
                            material_direction = 0
                            map_data.segments[segment_id].floor_material_direction = material_direction
                    else:
                        material_direction = None
                        map_data.segments[segment_id].floor_material_direction = None

                    if material_direction is not None:
                        map_data.segments[segment_id].floor_material_rotated_direction = (
                            material_direction
                            if map_data.rotation == 0 or map_data.rotation == 180
                            else 90 if material_direction == 0 else 0
                        )

                    floor_material[segment_id] = (
                        0
                        if material <= 0 or material > 2
                        else (
                            3
                            if material == 2
                            else (
                                2
                                if material_direction == 90
                                or (map_data.segments[segment_id].x1 - map_data.segments[segment_id].x0)
                                <= (map_data.segments[segment_id].y1 - map_data.segments[segment_id].y0)
                                else 1
                            )
                        )
                    )
            elif capability and capability.floor_material:
                floor_material[segment_id] = 0
                map_data.segments[segment_id].floor_material = 0
                if capability.floor_direction_cleaning:
                    map_data.segments[segment_id].floor_material_direction = 0
                    map_data.segments[segment_id].floor_material_rotated_direction = (
                        0 if map_data.rotation == 0 or map_data.rotation == 180 else 90
                    )
                else:
                    map_data.segments[segment_id].floor_material_direction = None
                    map_data.segments[segment_id].floor_material_rotated_direction = None

    @staticmethod
    def set_floor_material(map_data: MapData, capability: DreameVacuumDeviceCapability = None) -> None:
        if map_data.segments:
            floor_material = {}
            for k in map_data.segments.keys():
                DreameVacuumMapDecoder.set_segment_floor_material(map_data, k, floor_material, capability)
            map_data.floor_material = floor_material if floor_material else None


class DreameVacuumMapDataJsonRenderer:
    HALF_INT16 = 32768
    HALF_INT16_UPPER_HALF = 32767
    MAX = round(((HALF_INT16 + HALF_INT16_UPPER_HALF) / 10))

    def __init__(self) -> None:
        self._map_data: MapData = None
        self._map_data_json: dict[str, Any] = None
        self._left: int = 0
        self._top: int = 0
        self._grid_size: int = 0
        self.render_complete: bool = True
        self._layers: dict[MapRendererLayer, dict[str, Any]] = {}

        self._default_map_data: str = base64.b64decode(DEFAULT_MAP_DATA)
        self._default_map_image = Image.open(BytesIO(base64.b64decode(DEFAULT_MAP_DATA_IMAGE))).convert("RGBA")

    @staticmethod
    def _coordinate_tuple_sort(a: list[int], b: list[int]) -> bool:
        xA = a[0]
        yA = a[1]
        xB = b[0]
        yB = b[1]

        if yB > yA:
            return -1
        if xB > xA:
            return 1
        return 0

    @staticmethod
    def _convert_coordinates(x: int, y: int) -> int:
        return [
            round((x + DreameVacuumMapDataJsonRenderer.HALF_INT16) / 10),
            DreameVacuumMapDataJsonRenderer.MAX - round((y + DreameVacuumMapDataJsonRenderer.HALF_INT16) / 10),
        ]

    @staticmethod
    def _convert_angle(angle: int) -> int:
        return (((180 - angle) if (angle < 180) else (360 - angle + 180)) + 270) % 360

    @staticmethod
    def _to_buffer(image, extra_data: str) -> bytes:
        buffer = io.BytesIO()
        info = PngImagePlugin.PngInfo()
        info.add_text(MAP_DATA_JSON_CLASS, extra_data, zip=True)
        image.save(buffer, format="PNG", pnginfo=info)
        return buffer.getvalue()

    def render_map(self, map_data: MapData, robot_status: int = 0, station_status: int = 0) -> bytes:
        if map_data is None or map_data.empty_map:
            return self.default_map_image

        if (
            self._map_data
            and self._map_data == map_data
            and self._map_data.frame_id == map_data.frame_id
            and self._map_data_json
        ):
            _LOGGER.debug("Skip render map data, not changed")
            return self._to_buffer(
                self._default_map_image,
                json.dumps(self._map_data_json, separators=(",", ":")),
            )

        now = time.time()
        self.render_complete = False
        if (
            self._map_data is None
            or self._map_data.dimensions != map_data.dimensions
            or self._map_data.map_id != map_data.map_id
            or self._map_data.saved_map_status != map_data.saved_map_status
        ):
            self._map_data = None
            self._left = round((map_data.dimensions.left + DreameVacuumMapDataJsonRenderer.HALF_INT16) / 10)
            self._top = round((map_data.dimensions.top + DreameVacuumMapDataJsonRenderer.HALF_INT16) / 10)
            self._grid_size = round(map_data.dimensions.grid_size / 10)

        map_data_json = {
            MAP_DATA_JSON_PARAMETER_CLASS: MAP_DATA_JSON_CLASS,
            MAP_DATA_JSON_PARAMETER_SIZE: {
                MAP_DATA_JSON_PARAMETER_X: DreameVacuumMapDataJsonRenderer.MAX,
                MAP_DATA_JSON_PARAMETER_Y: DreameVacuumMapDataJsonRenderer.MAX,
            },
            MAP_DATA_JSON_PARAMETER_PIXEL_SIZE: self._grid_size,
            MAP_DATA_JSON_PARAMETER_LAYERS: [],
            MAP_DATA_JSON_PARAMETER_ENTITIES: [],
            MAP_DATA_JSON_PARAMETER_META_DATA: {
                MAP_DATA_JSON_PARAMETER_VERSION: 2,
                MAP_DATA_JSON_PARAMETER_ROTATION: map_data.rotation,
            },
        }

        if map_data.robot_position:
            if (
                self._map_data is None
                or self._map_data.robot_position != map_data.robot_position
                or not self._layers.get(MapRendererLayer.ROBOT)
            ):
                self._layers[MapRendererLayer.ROBOT] = {
                    MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_ROBOT_POSITION,
                    MAP_DATA_JSON_PARAMETER_POINTS: DreameVacuumMapDataJsonRenderer._convert_coordinates(
                        map_data.robot_position.x, map_data.robot_position.y
                    ),
                    MAP_DATA_JSON_PARAMETER_META_DATA: {
                        MAP_PARAMETER_ANGLE: DreameVacuumMapDataJsonRenderer._convert_angle(map_data.robot_position.a)
                    },
                }
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].append(self._layers[MapRendererLayer.ROBOT])

        if map_data.charger_position:
            if (
                self._map_data is None
                or self._map_data.charger_position != map_data.charger_position
                or not self._layers.get(MapRendererLayer.CHARGER)
            ):
                self._layers[MapRendererLayer.CHARGER] = {
                    MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_CHARGER_POSITION,
                    MAP_DATA_JSON_PARAMETER_POINTS: DreameVacuumMapDataJsonRenderer._convert_coordinates(
                        map_data.charger_position.x, map_data.charger_position.y
                    ),
                    MAP_DATA_JSON_PARAMETER_META_DATA: {
                        MAP_PARAMETER_ANGLE: DreameVacuumMapDataJsonRenderer._convert_angle(
                            map_data.charger_position.a
                        )
                    },
                }
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].append(self._layers[MapRendererLayer.CHARGER])

        if map_data.no_mopping_areas:
            if (
                self._map_data is None
                or self._map_data.no_mopping_areas != map_data.no_mopping_areas
                or not self._layers.get(MapRendererLayer.NO_MOP)
            ):
                self._layers[MapRendererLayer.NO_MOP] = []
                for area in map_data.no_mopping_areas:
                    if not area.hidden:
                        a = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x0, area.y0)
                        b = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x1, area.y1)
                        c = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x2, area.y2)
                        d = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x3, area.y3)
                        self._layers[MapRendererLayer.NO_MOP].append(
                            {
                                MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_NO_MOP_AREA,
                                MAP_DATA_JSON_PARAMETER_POINTS: [
                                    a[0],
                                    a[1],
                                    b[0],
                                    b[1],
                                    c[0],
                                    c[1],
                                    d[0],
                                    d[1],
                                ],
                            }
                        )
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].extend(self._layers[MapRendererLayer.NO_MOP])

        if map_data.no_go_areas:
            if (
                self._map_data is None
                or self._map_data.no_go_areas != map_data.no_go_areas
                or not self._layers.get(MapRendererLayer.NO_GO)
            ):
                self._layers[MapRendererLayer.NO_GO] = []
                for area in map_data.no_go_areas:
                    a = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x0, area.y0)
                    b = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x1, area.y1)
                    c = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x2, area.y2)
                    d = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x3, area.y3)

                    self._layers[MapRendererLayer.NO_GO].append(
                        {
                            MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_NO_GO_AREA,
                            MAP_DATA_JSON_PARAMETER_POINTS: [
                                a[0],
                                a[1],
                                b[0],
                                b[1],
                                c[0],
                                c[1],
                                d[0],
                                d[1],
                            ],
                        }
                    )
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].extend(self._layers[MapRendererLayer.NO_GO])

        if map_data.active_areas:
            if (
                self._map_data is None
                or self._map_data.active_areas != map_data.active_areas
                or not self._layers.get(MapRendererLayer.ACTIVE_AREA)
            ):
                self._layers[MapRendererLayer.ACTIVE_AREA] = []
                for area in map_data.active_areas:
                    a = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x0, area.y0)
                    b = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x1, area.y1)
                    c = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x2, area.y2)
                    d = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x3, area.y3)

                    self._layers[MapRendererLayer.ACTIVE_AREA].append(
                        {
                            MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_ACTIVE_ZONE,
                            MAP_DATA_JSON_PARAMETER_POINTS: [
                                a[0],
                                a[1],
                                b[0],
                                b[1],
                                c[0],
                                c[1],
                                d[0],
                                d[1],
                            ],
                        }
                    )
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].extend(self._layers[MapRendererLayer.ACTIVE_AREA])

        if map_data.active_points:
            if (
                self._map_data is None
                or self._map_data.active_points != map_data.active_points
                or not self._layers.get(MapRendererLayer.ACTIVE_POINT)
            ):
                self._layers[MapRendererLayer.ACTIVE_POINT] = []
                size = 15 * map_data.dimensions.grid_size
                for point in map_data.active_points:
                    area = Area(
                        point.x - size,
                        point.y - size,
                        point.x + size,
                        point.y - size,
                        point.x + size,
                        point.y + size,
                        point.x - size,
                        point.y + size,
                    )

                    a = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x0, area.y0)
                    b = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x1, area.y1)
                    c = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x2, area.y2)
                    d = DreameVacuumMapDataJsonRenderer._convert_coordinates(area.x3, area.y3)

                    self._layers[MapRendererLayer.ACTIVE_POINT].append(
                        {
                            MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_ACTIVE_ZONE,
                            MAP_DATA_JSON_PARAMETER_POINTS: [
                                a[0],
                                a[1],
                                b[0],
                                b[1],
                                c[0],
                                c[1],
                                d[0],
                                d[1],
                            ],
                        }
                    )
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].extend(self._layers[MapRendererLayer.ACTIVE_POINT])

        if map_data.virtual_walls:
            if (
                self._map_data is None
                or self._map_data.virtual_walls != map_data.virtual_walls
                or not self._layers.get(MapRendererLayer.WALL)
            ):
                self._layers[MapRendererLayer.WALL] = []
                for wall in map_data.virtual_walls:
                    a = DreameVacuumMapDataJsonRenderer._convert_coordinates(wall.x0, wall.y0)
                    b = DreameVacuumMapDataJsonRenderer._convert_coordinates(wall.x1, wall.y1)

                    self._layers[MapRendererLayer.WALL].append(
                        {
                            MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_VIRTUAL_WALL,
                            MAP_DATA_JSON_PARAMETER_POINTS: [a[0], a[1], b[0], b[1]],
                        }
                    )
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].extend(self._layers[MapRendererLayer.WALL])

        if map_data.path and (
            self._map_data is None
            or self._map_data.path is None
            or len(self._map_data.path) != len(map_data.path)
            or not self._layers.get(MapRendererLayer.PATH)
        ):
            points = []
            self._layers[MapRendererLayer.PATH] = []
            if map_data.path and len(map_data.path) > 1:
                s = map_data.path[0]
                for point in map_data.path[1:]:
                    if point.path_type == PathType.LINE:
                        point = point
                        a = DreameVacuumMapDataJsonRenderer._convert_coordinates(s.x, s.y)
                        b = DreameVacuumMapDataJsonRenderer._convert_coordinates(point.x, point.y)

                        points.extend([a[0], a[1], b[0], b[1]])
                    else:
                        self._layers[MapRendererLayer.PATH].append(
                            {
                                MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_PATH,
                                MAP_DATA_JSON_PARAMETER_POINTS: points,
                            }
                        )
                        points = []
                    s = point
            self._layers[MapRendererLayer.PATH].append(
                {
                    MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_PATH,
                    MAP_DATA_JSON_PARAMETER_POINTS: points,
                }
            )
            map_data_json[MAP_DATA_JSON_PARAMETER_ENTITIES].extend(self._layers[MapRendererLayer.PATH])

        floor_pixels = []
        wall_pixels = []
        segments = {}

        if (
            self._map_data is None
            or self._map_data.active_segments != map_data.active_segments
            or self._map_data.active_areas != map_data.active_areas
            or self._map_data.segments != map_data.segments
            or self._map_data.data != map_data.data
            or not self._layers.get(MapRendererLayer.IMAGE)
        ):
            self._layers[MapRendererLayer.IMAGE] = []
            for y in range(map_data.dimensions.height):
                for x in range(map_data.dimensions.width):
                    segment_id = int(map_data.pixel_type[x, y])
                    coords = [
                        (x + (self._left / self._grid_size)),
                        (y + (self._top / self._grid_size)),
                    ]

                    coords[1] = (DreameVacuumMapDataJsonRenderer.MAX / self._grid_size) - coords[1]

                    coords[0] = round(coords[0])
                    coords[1] = round(coords[1])

                    if segment_id == MapPixelType.WALL.value:
                        wall_pixels.append(coords)
                    elif segment_id == MapPixelType.FLOOR.value or segment_id == MapPixelType.UNKNOWN.value:
                        floor_pixels.append(coords)
                    elif segment_id > 0 and segment_id < 61:
                        if map_data.active_segments and segment_id not in map_data.active_segments:
                            floor_pixels.append(coords)
                        else:
                            if not map_data.segments:
                                segment_id = 1

                            if segment_id not in segments:
                                segments[segment_id] = []
                            segments[segment_id].append(coords)

            if floor_pixels:
                self._layers[MapRendererLayer.IMAGE].append(
                    {
                        MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_FLOOR,
                        MAP_DATA_JSON_PARAMETER_PIXELS: [
                            val
                            for sublist in sorted(
                                floor_pixels,
                                key=cmp_to_key(DreameVacuumMapDataJsonRenderer._coordinate_tuple_sort),
                            )
                            for val in sublist
                        ],
                    }
                )

            if wall_pixels:
                self._layers[MapRendererLayer.IMAGE].append(
                    {
                        MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_WALL,
                        MAP_DATA_JSON_PARAMETER_PIXELS: [
                            val
                            for sublist in sorted(
                                wall_pixels,
                                key=cmp_to_key(DreameVacuumMapDataJsonRenderer._coordinate_tuple_sort),
                            )
                            for val in sublist
                        ],
                    }
                )

            if segments:
                for k, v in segments.items():
                    name = None
                    if map_data.segments:
                        name = f"Room {k}"
                        if k in map_data.segments:
                            name = map_data.segments[k].name
                    self._layers[MapRendererLayer.IMAGE].append(
                        {
                            MAP_DATA_JSON_PARAMETER_TYPE: MAP_DATA_JSON_PARAMETER_SEGMENT,
                            MAP_DATA_JSON_PARAMETER_PIXELS: [
                                val
                                for sublist in sorted(
                                    v,
                                    key=cmp_to_key(DreameVacuumMapDataJsonRenderer._coordinate_tuple_sort),
                                )
                                for val in sublist
                            ],
                            MAP_DATA_JSON_PARAMETER_META_DATA: {
                                MAP_DATA_JSON_PARAMETER_SEGMENT_ID: k,
                                MAP_DATA_JSON_PARAMETER_ACTIVE: (
                                    True if map_data.active_segments and k in map_data.active_segments else False
                                ),
                                MAP_DATA_JSON_PARAMETER_NAME: name,
                            },
                        }
                    )

            for layers in self._layers[MapRendererLayer.IMAGE]:
                pixels = layers[MAP_DATA_JSON_PARAMETER_PIXELS]
                layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS] = {
                    MAP_DATA_JSON_PARAMETER_X: {
                        MAP_DATA_JSON_PARAMETER_MIN: 65535,
                        MAP_DATA_JSON_PARAMETER_MAX: -65535,
                        MAP_DATA_JSON_PARAMETER_MID: None,
                        MAP_DATA_JSON_PARAMETER_AVG: None,
                    },
                    MAP_DATA_JSON_PARAMETER_Y: {
                        MAP_DATA_JSON_PARAMETER_MIN: 65535,
                        MAP_DATA_JSON_PARAMETER_MAX: -65535,
                        MAP_DATA_JSON_PARAMETER_MID: None,
                        MAP_DATA_JSON_PARAMETER_AVG: None,
                    },
                    MAP_DATA_JSON_PARAMETER_PIXEL_COUNT: len(pixels) / 2,
                }

                sum_x = 0
                sum_y = 0
                for i in range(0, len(pixels), 2):
                    sum_x = sum_x + pixels[i]
                    sum_y = sum_y + pixels[i + 1]

                    if (
                        pixels[i]
                        < layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][
                            MAP_DATA_JSON_PARAMETER_MIN
                        ]
                    ):
                        layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][
                            MAP_DATA_JSON_PARAMETER_MIN
                        ] = pixels[i]

                    if (
                        pixels[i]
                        > layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][
                            MAP_DATA_JSON_PARAMETER_MAX
                        ]
                    ):
                        layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][
                            MAP_DATA_JSON_PARAMETER_MAX
                        ] = pixels[i]

                    if (
                        pixels[i + 1]
                        < layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][
                            MAP_DATA_JSON_PARAMETER_MIN
                        ]
                    ):
                        layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][
                            MAP_DATA_JSON_PARAMETER_MIN
                        ] = pixels[i + 1]

                    if (
                        pixels[i + 1]
                        > layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][
                            MAP_DATA_JSON_PARAMETER_MAX
                        ]
                    ):
                        layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][
                            MAP_DATA_JSON_PARAMETER_MAX
                        ] = pixels[i + 1]

                layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][MAP_DATA_JSON_PARAMETER_MID] = (
                    round(
                        (
                            layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][
                                MAP_DATA_JSON_PARAMETER_MAX
                            ]
                            + layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][
                                MAP_DATA_JSON_PARAMETER_MIN
                            ]
                        )
                        / 2
                    )
                )
                layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][MAP_DATA_JSON_PARAMETER_MID] = (
                    round(
                        (
                            layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][
                                MAP_DATA_JSON_PARAMETER_MAX
                            ]
                            + layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][
                                MAP_DATA_JSON_PARAMETER_MIN
                            ]
                        )
                        / 2
                    )
                )

                if sum_x:
                    layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_X][
                        MAP_DATA_JSON_PARAMETER_AVG
                    ] = round(sum_x / (len(pixels) / 2))
                if sum_y:
                    layers[MAP_DATA_JSON_PARAMETER_DIMENSIONS][MAP_DATA_JSON_PARAMETER_Y][
                        MAP_DATA_JSON_PARAMETER_AVG
                    ] = round(sum_y / (len(pixels) / 2))

                current_x_start = -65535
                current_y = -65535
                current_count = 0
                compressed_pixels = []

                for i in range(0, len(pixels), 2):
                    x = pixels[i]
                    y = pixels[i + 1]

                    if y != current_y or x > (current_x_start + current_count):
                        compressed_pixels.extend([current_x_start, current_y, current_count])
                        current_x_start = x
                        current_y = y
                        current_count = 1
                    elif x != current_x_start:
                        current_count = current_count + 1

                compressed_pixels.extend([current_x_start, current_y, current_count])
                layers[MAP_DATA_JSON_PARAMETER_COMPRESSED_PIXELS] = compressed_pixels[3:]
                layers[MAP_DATA_JSON_PARAMETER_PIXELS] = []

        map_data_json[MAP_DATA_JSON_PARAMETER_LAYERS].extend(self._layers[MapRendererLayer.IMAGE])

        self._map_data = map_data
        self._map_data_json = map_data_json
        _LOGGER.debug(
            "Render Map Data: %s:%s took: %.2f",
            map_data.map_id,
            map_data.frame_id,
            time.time() - now,
        )
        self.render_complete = True
        return self._to_buffer(
            self._default_map_image,
            json.dumps(self._map_data_json, separators=(",", ":")),
        )

    @property
    def default_map_image(self) -> bytes:
        return self._to_buffer(self._default_map_image, self._default_map_data)

    @property
    def disconnected_map_image(self) -> bytes:
        return self._default_map_image


class DreameVacuumMapRenderer:
    MAP_FONT_UNPACKED = None

    def __init__(
        self,
        color_scheme: str = None,
        icon_set: int = None,
        hidden_map_objects: list[str] = None,
        robot_type: int = 0,
        low_resolution: bool = False,
        square: bool = False,
        cache: bool = True,
    ) -> None:
        self.color_scheme: MapRendererColorScheme = MAP_COLOR_SCHEME_LIST.get(color_scheme, MapRendererColorScheme())
        self.icon_set: int = icon_set
        self.config: MapRendererConfig = MapRendererConfig()
        if hidden_map_objects is not None:
            for attr in self.config.__dict__.keys():
                if attr in hidden_map_objects:
                    setattr(self.config, attr, False)

        self._map_data: MapData = None
        self.render_complete: bool = True
        self._layers: dict[MapRendererLayer, Any] = {}
        self._robot_status: int = None
        self._station_status: int = None
        self._robot_type: int = robot_type
        self._low_resolution: bool = low_resolution
        self._low_memory: bool = low_resolution
        self._square: bool = square
        self._cache: bool = cache
        self._has_mask: bool = False
        self._calibration_points: dict[str, int] = None
        self._default_calibration_points: dict[str, int] = [
            {
                MAP_PARAMETER_VACUUM: {
                    MAP_DATA_JSON_PARAMETER_X: 0,
                    MAP_DATA_JSON_PARAMETER_Y: 0,
                },
                MAP_PARAMETER_MAP: {
                    MAP_DATA_JSON_PARAMETER_X: 0,
                    MAP_DATA_JSON_PARAMETER_Y: 0,
                },
            },
            {
                MAP_PARAMETER_VACUUM: {
                    MAP_DATA_JSON_PARAMETER_X: 1000,
                    MAP_DATA_JSON_PARAMETER_Y: 0,
                },
                MAP_PARAMETER_MAP: {
                    MAP_DATA_JSON_PARAMETER_X: 0,
                    MAP_DATA_JSON_PARAMETER_Y: 0,
                },
            },
            {
                MAP_PARAMETER_VACUUM: {
                    MAP_DATA_JSON_PARAMETER_X: 0,
                    MAP_DATA_JSON_PARAMETER_Y: 1000,
                },
                MAP_PARAMETER_MAP: {
                    MAP_DATA_JSON_PARAMETER_X: 0,
                    MAP_DATA_JSON_PARAMETER_Y: 0,
                },
            },
        ]

        self._image = None
        self._charger_icon = None
        self._robot_icon = None
        self._robot_charging_icon = None
        self._robot_cleaning_icon = None
        self._robot_warning_icon = None
        self._robot_sleeping_icon = None
        self._robot_washing_icon = None
        self._robot_hot_washing_icon = None
        self._robot_drying_icon = None
        self._robot_hot_drying_icon = None
        self._robot_dust_bag_drying_icon = None
        self._robot_emptying_icon = None
        self._robot_cleaning_direction_icon = None
        self._obstacle_background = None
        self._obstacle_hidden_background = None
        self._cruise_path_point_background = None
        self._cruise_point_background = None
        self._furniture_background = None
        self._wifi_icon = None
        self._font_file = None
        self._light_font_file = None
        self._default_map_image = None
        self._obstacle_bottom_left_icon = None
        self._obstacle_top_left_icon = None
        self._obstacle_bottom_right_icon = None
        self._obstacle_top_right_icon = None
        self._map_problem_icon = None

        self._segment_icons = {}
        self._obstacle_icons = {}
        self._obstacle_hidden_icons = {}
        self._furniture_icons = {}
        self._furniture_images = {}

        if self._low_memory:
            self.config.obstacle = False
            self.config.pet = False
            self.config.furniture = False

        if self.icon_set == 2:
            repeats = MAP_ICON_REPEATS_MIJIA
            suction_level = MAP_ICON_SUCTION_LEVEL_MIJIA
            water_volume = MAP_ICON_WATER_VOLUME_MIJIA
            cleaning_mode = MAP_ICON_CLEANING_MODE_MIJIA
        elif self.icon_set == 3:
            repeats = MAP_ICON_REPEATS_MATERIAL
            suction_level = MAP_ICON_SUCTION_LEVEL_MATERIAL
            water_volume = MAP_ICON_WATER_VOLUME_MATERIAL
            cleaning_mode = MAP_ICON_CLEANING_MODE_MATERIAL
        else:
            repeats = MAP_ICON_REPEATS_DREAME
            suction_level = MAP_ICON_SUCTION_LEVEL_DREAME
            water_volume = MAP_ICON_WATER_VOLUME_DREAME
            cleaning_mode = MAP_ICON_CLEANING_MODE_DREAME

        if self.config.cleaning_times:
            self._cleaning_times_icon = [
                Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in repeats
            ]
        if self.config.suction_level:
            self._suction_level_icon = [
                Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in suction_level
            ]
        if self.config.water_volume:
            self._water_volume_icon = [
                Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in water_volume
            ]
            self._mop_pad_humidity_icon = [
                Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA")
                for icon in (
                    MAP_ICON_MOP_PAD_HUMIDITY_MATERIAL if self.icon_set == 3 else MAP_ICON_MOP_PAD_HUMIDITY_DREAME
                )
            ]
        if self.config.cleaning_mode:
            self._cleaning_mode_icon = [
                Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in cleaning_mode
            ]
        if self.config.mopping_mode:
            self._cleaning_route_icon = [
                Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA")
                for icon in (
                    MAP_ICON_CLEANING_ROUTE_MATERIAL if self.icon_set == 3 else MAP_ICON_CLEANING_ROUTE_DREAME
                )
            ]
            self._custom_mopping_route_icon = [
                Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA")
                for icon in MAP_ICON_CUSTOM_MOPPING_ROUTE_DREAME
            ]

    @staticmethod
    def _to_buffer(image) -> bytes:
        if image:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()

    @staticmethod
    def _set_icon_color(image, size, color):
        ico = image.resize((int(size), int(size)))
        pixdata = ico.load()
        for yy in range(ico.size[1]):
            for xx in range(ico.size[0]):
                if (
                    pixdata[xx, yy][0] > 80
                    and pixdata[xx, yy][1] > 80
                    and pixdata[xx, yy][2] > 80
                    and pixdata[xx, yy][3] > 80
                ):
                    pixdata[xx, yy] = color

        return ico

    @staticmethod
    def _calculate_bounds(dimensions, segments) -> list[int]:
        if segments:
            min_x = dimensions.width - 1
            min_y = dimensions.height - 1
            max_x = 0
            max_y = 0
            for segment in segments.values():
                p = segment.to_coord(dimensions)
                x_coords = [int(p.x0), int(p.x1)]
                y_coords = [int(p.y0), int(p.y1)]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

            return [min_x, min_y, max_x, min_y]

    @staticmethod
    def _calculate_padding(
        dimensions,
        active_areas,
        no_mopping_areas,
        no_go_areas,
        walls,
        virtual_thresholds,
        passable_thresholds,
        impassable_thresholds,
        ramps,
        furnitures,
        furniture_version,
        curtains,
        segments,
        padding,
        min_width,
        min_height,
        scale,
        icon_set,
    ) -> list[int]:
        min_x = 0
        min_y = 0
        max_x = dimensions.width
        max_y = dimensions.height

        if segments:
            for segment in segments.values():
                p = segment.to_coord(dimensions)
                x_coords = sorted([int(p.x0), int(p.x1)])
                y_coords = sorted([int(p.y0), int(p.y1)])
                min_x = min(x_coords[0], min_x)
                max_x = max(x_coords[1], max_x)
                min_y = min(y_coords[0], min_y)
                max_y = max(y_coords[1], max_y)

        if active_areas:
            for area in active_areas:
                p = area.to_coord(dimensions)
                x_coords = [p.x0, p.x1, p.x2, p.x3]
                y_coords = [p.y0, p.y1, p.y2, p.y3]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if no_mopping_areas:
            for area in no_mopping_areas:
                p = area.to_coord(dimensions)
                x_coords = [p.x0, p.x1, p.x2, p.x3]
                y_coords = [p.y0, p.y1, p.y2, p.y3]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if no_go_areas:
            for area in no_go_areas:
                p = area.to_coord(dimensions)
                x_coords = [p.x0, p.x1, p.x2, p.x3]
                y_coords = [p.y0, p.y1, p.y2, p.y3]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if walls:
            for wall in walls:
                p = wall.to_coord(dimensions)
                x_coords = [p.x0, p.x1]
                y_coords = [p.y0, p.y1]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if virtual_thresholds:
            for line in virtual_thresholds:
                p = line.to_coord(dimensions)
                x_coords = [p.x0, p.x1]
                y_coords = [p.y0, p.y1]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if passable_thresholds:
            for line in passable_thresholds:
                p = line.to_coord(dimensions)
                x_coords = [p.x0, p.x1]
                y_coords = [p.y0, p.y1]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if impassable_thresholds:
            for line in impassable_thresholds:
                p = line.to_coord(dimensions)
                x_coords = [p.x0, p.x1]
                y_coords = [p.y0, p.y1]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if ramps:
            for area in ramps:
                p = area.to_coord(dimensions)
                x_coords = [p.x0, p.x1, p.x2, p.x3]
                y_coords = [p.y0, p.y1, p.y2, p.y3]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if furnitures:
            if furniture_version >= 3:
                furniture_images = (
                    FURNITURE_V2_TYPE_MIJIA_TO_IMAGE
                    if furniture_version == 5
                    else FURNITURE_V3_TYPE_TO_IMAGE if furniture_version == 6 else FURNITURE_V2_TYPE_TO_IMAGE
                )
                furniture_icons = FURNITURE_V2_TYPE_TO_ICON
            else:
                furniture_images = FURNITURE_TYPE_TO_IMAGE
                furniture_icons = FURNITURE_TYPE_TO_ICON

            for k, v in furnitures.items():
                p = Point(v.x, v.y).to_coord(dimensions)
                w = 0
                h = 0
                if v.width and v.height:
                    if v.type.value not in furniture_images:
                        continue
                    w = int((v.width / dimensions.grid_size) / 2)
                    h = int((v.height / dimensions.grid_size) / 2)
                elif v.type.value not in furniture_icons:
                    continue
                min_x = min(p.x - w, min_x)
                max_x = max(p.x + w, max_x)
                min_y = min(p.y - h, min_y)
                max_y = max(p.y + h, max_y)

        if curtains:
            for line in curtains:
                p = line.to_coord(dimensions)
                x_coords = [p.x0, p.x1]
                y_coords = [p.y0, p.y1]
                min_x = min(min(x_coords), min_x)
                max_x = max(max(x_coords), max_x)
                min_y = min(min(y_coords), min_y)
                max_y = max(max(y_coords), max_y)

        if min_x < 0:
            padding[0] = padding[0] + int(-min_x)
        if max_x > dimensions.width:
            padding[2] = padding[2] + int(max_x - dimensions.width)
        if min_y < 0:
            padding[1] = padding[1] + int(-min_y)
        if max_y > dimensions.height:
            padding[3] = padding[3] + int(max_y - dimensions.height)

        if dimensions.width + padding[0] + padding[2] < min_width:
            size = int((min_width - dimensions.width + padding[0] + padding[2]) / 2)
            padding[0] = padding[0] + size
            padding[2] = padding[2] + size

        if dimensions.height + padding[1] + padding[3] < min_height:
            size = int((min_height - dimensions.height + padding[1] + padding[3]) / 2)
            padding[1] = padding[1] + size
            padding[3] = padding[3] + size

        for k in range(4):
            padding[k] = padding[k] * scale

        return padding

    @staticmethod
    def _round_coord(coord, grid_size):
        remainder = coord % grid_size
        if remainder <= grid_size / 2:
            return coord - remainder
        return coord + grid_size - remainder

    @staticmethod
    def _get_carpet_coords(carpet, dimensions):
        grid_size = dimensions.grid_size
        if carpet.ellipse:
            x0 = DreameVacuumMapRenderer._round_coord(carpet.x0 - dimensions.offset, grid_size) + dimensions.offset
            y0 = DreameVacuumMapRenderer._round_coord(carpet.y0 - dimensions.offset, grid_size) + dimensions.offset
            x2 = DreameVacuumMapRenderer._round_coord(carpet.x2, grid_size)
            y2 = DreameVacuumMapRenderer._round_coord(carpet.y2, grid_size)

            x_coords = sorted([x0, x2])
            y_coords = sorted([y0, y2])

            return (
                int(math.ceil((x_coords[0] - x_coords[1] - dimensions.left) / grid_size)),
                int(math.ceil((y_coords[0] - y_coords[1] - dimensions.top) / grid_size)),
                int(math.ceil(((x_coords[0] + x_coords[1] - dimensions.left) / grid_size) + 1)),
                int(math.ceil(((y_coords[0] + y_coords[1] - dimensions.top) / grid_size) + 1)),
            )
        else:
            left = dimensions.left
            top = dimensions.top
            if left % dimensions.grid_size != 0 or top % dimensions.grid_size != 0:
                left = left + (dimensions.offset)
                top = top + (dimensions.offset)

            x_coords = sorted([carpet.x0, carpet.x2])
            y_coords = sorted([carpet.y0, carpet.y2])

            return (
                int(math.ceil((x_coords[0] - left) / grid_size)),
                int(math.ceil((y_coords[0] - top) / grid_size)),
                int(math.ceil((x_coords[1] - left) / grid_size)),
                int(math.ceil((y_coords[1] - top) / grid_size)),
            )

    @staticmethod
    def _optimize_carpet_pixels(carpet_pixels, dimensions, pixel_type):
        carpet_data = {}
        for pixel in carpet_pixels:
            x = pixel[0]
            y = pixel[1]
            for xx in range(max(0, x - 1), min(x + 3, dimensions.width - 1)):
                for yy in range(max(0, y - 1), min(y + 2, dimensions.height - 1)):
                    val = int(pixel_type[xx, yy])
                    if val > 0 and val <= 100:
                        carpet_data[(xx, yy)] = 1
        return carpet_data

    @staticmethod
    def _check_carpet(x, y, carpet, dimensions, pixel_type=None):
        if pixel_type is not None and (
            pixel_type > 100
            or pixel_type <= 0
            or (pixel_type <= 100 and not carpet.polygon and carpet.segments and pixel_type not in carpet.segments)
        ):
            return False

        if carpet.ellipse or carpet.ignored_areas or carpet.polygon:
            x = (x * dimensions.grid_size) + dimensions.left
            y = (y * dimensions.grid_size) + dimensions.top

        if carpet.ellipse and not (
            (x - carpet.x0) * (x - carpet.x0) / (carpet.x2 * carpet.x2)
            + (y - carpet.y0) * (y - carpet.y0) / (carpet.y2 * carpet.y2)
            < 1
        ):
            return False

        if carpet.ignored_areas and isinstance(carpet.ignored_areas, list):
            for area in carpet.ignored_areas:
                if (
                    area
                    and isinstance(area, list)
                    and len(area) > 3
                    and x >= area[0]
                    and x <= area[2]
                    and y >= area[1]
                    and y <= area[3]
                ):
                    return False

        if carpet.polygon and len(carpet.polygon) <= 100:
            check = False
            polygon = carpet.polygon
            for i in range(0, len(polygon), 2):
                j = len(polygon) - 2 if i == 0 else i - 2

                sx = polygon[i]
                sy = polygon[i + 1]
                tx = polygon[j]
                ty = polygon[j + 1]

                if sx == x and sy == y and tx == x and ty == y:
                    return True
                if sy == ty and sy == y and (sx > x and tx < x or sx < x and tx > x):
                    return True
                if sy < y and ty >= y or sy >= y and ty < y:
                    xx = sx + (y - sy) * (tx - sx) / (ty - sy)
                    if xx == x:
                        return True
                    if xx > x:
                        check = not check
            return check
        return True

    @staticmethod
    def _calculate_calibration_points(map_data: MapData) -> dict[str, int] | None:
        if (map_data.dimensions.width * map_data.dimensions.height) > 0:
            calibration_points = []
            for point in [Point(0, 0), Point(1000, 0), Point(0, 1000)]:
                img_point = point.to_img(map_data.dimensions).rotated(map_data.dimensions, map_data.rotation)
                calibration_points.append(
                    {
                        MAP_PARAMETER_VACUUM: {
                            MAP_DATA_JSON_PARAMETER_X: point.x,
                            MAP_DATA_JSON_PARAMETER_Y: point.y,
                        },
                        MAP_PARAMETER_MAP: {
                            MAP_DATA_JSON_PARAMETER_X: int(img_point.x),
                            MAP_DATA_JSON_PARAMETER_Y: int(img_point.y),
                        },
                    }
                )
            return calibration_points

    @staticmethod
    def _alpha_composite(source, destination):
        srcA = source[3] / 255.0
        dstA = destination[3] / 255.0
        outA = srcA + dstA * (1 - srcA)
        if outA:
            outRGB = []
            for i in range(3):
                outRGB.append((float(source[i]) * srcA + float(destination[i]) * dstA * (1 - srcA)) / outA)
            return (int(outRGB[0]), int(outRGB[1]), int(outRGB[2]), int(outA * 255))
        return source

    @staticmethod
    def _combine_layers(cached_layers, layer_size, parent, sub):
        cached_layers[parent] = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        if sub in cached_layers:
            for k, v in sorted(cached_layers[sub].items()):
                if v is not None:
                    try:
                        cached_layers[parent] = Image.alpha_composite(cached_layers[parent], v)
                    except:
                        pass

    @staticmethod
    def _coords_on_line(x0, y0, x1, y1, spacing, size=None):
        x = x1 - x0
        y = y1 - y0
        count = size - 1 if size else math.floor(math.sqrt(x * x + y * y) / spacing)
        points = []
        for i in range(count + 1):
            points.append((x0 + x * (i / count), y0 + y * (i / count)))
        return points

    @staticmethod
    def color_to_tuple(color: str):
        if not color or len(color) < 3:
            return None

        color = color.strip().lower()
        if color.startswith("#"):
            hex_value = color[1:]
            if len(hex_value) == 3:
                r = int(hex_value[0] * 2, 16)
                g = int(hex_value[1] * 2, 16)
                b = int(hex_value[2] * 2, 16)
                return (r, g, b, 255)
            if len(hex_value) == 4:
                r = int(hex_value[0] * 2, 16)
                g = int(hex_value[1] * 2, 16)
                b = int(hex_value[2] * 2, 16)
                a = int(hex_value[3] * 2, 16)
                return (r, g, b, a)
            if len(hex_value) == 6:
                r = int(hex_value[0:2], 16)
                g = int(hex_value[2:4], 16)
                b = int(hex_value[4:6], 16)
                return (r, g, b, 255)
            if len(hex_value) == 8:
                r = int(hex_value[0:2], 16)
                g = int(hex_value[2:4], 16)
                b = int(hex_value[4:6], 16)
                a = int(hex_value[6:8], 16)
                return (r, g, b, a)
            return None

        rgb_match = re.match(r"rgba?\((.*?)\)", color)
        if rgb_match:
            parts = [p.strip() for p in rgb_match.group(1).split(",")]
            if len(parts) == 3:
                r, g, b = map(int, parts)
                return (r, g, b, 255)
            if len(parts) == 4:
                r, g, b = map(int, parts[:3])
                a = float(parts[3])
                return (r, g, b, a)
            return None
        return None

    @staticmethod
    def get_resources(capability, icon_set, as_json=False) -> MapRendererResources | str:
        if icon_set == 2:
            if capability.robot_type == RobotType.MOPPING:
                robot_image = MAP_ROBOT_MOP_IMAGE_MIJIA
            elif capability.robot_type == RobotType.VSLAM:
                robot_image = MAP_ROBOT_VSLAM_IMAGE_MIJIA
            else:
                robot_image = MAP_ROBOT_LIDAR_IMAGE_MIJIA
        else:
            if capability.robot_type == RobotType.MOPPING:
                robot_image = MAP_ROBOT_MOP_IMAGE_DREAME
            elif capability.robot_type == RobotType.SWEEPING_AND_MOPPING:
                robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_LIGHT
            elif capability.robot_type == RobotType.VSLAM:
                if icon_set == 3:
                    robot_image = MAP_ROBOT_VSLAM_IMAGE_DREAME_LIGHT
                else:
                    robot_image = MAP_ROBOT_VSLAM_IMAGE_DREAME_DARK
            else:
                if icon_set == 3:
                    robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_LIGHT
                else:
                    robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_DARK

        if icon_set == 3:
            charger_image = MAP_CHARGER_IMAGE_MATERIAL
        elif icon_set == 2:
            charger_image = MAP_CHARGER_IMAGE_MIJIA
        else:
            if capability.robot_type == RobotType.VSLAM:
                charger_image = MAP_CHARGER_VSLAM_IMAGE_DREAME
            else:
                charger_image = MAP_CHARGER_IMAGE_DREAME

        icons = SEGMENT_ICONS_DREAME
        if icon_set == 1:
            icons = SEGMENT_ICONS_DREAME_OLD
        elif icon_set == 2:
            icons = SEGMENT_ICONS_MIJIA
        elif icon_set == 3:
            icons = SEGMENT_ICONS_MATERIAL

        if icon_set == 2:
            repeats = MAP_ICON_REPEATS_MIJIA
            suction_level = MAP_ICON_SUCTION_LEVEL_MIJIA
            water_volume = MAP_ICON_WATER_VOLUME_MIJIA
            cleaning_mode = MAP_ICON_CLEANING_MODE_MIJIA
        elif icon_set == 3:
            repeats = MAP_ICON_REPEATS_MATERIAL
            suction_level = MAP_ICON_SUCTION_LEVEL_MATERIAL
            water_volume = MAP_ICON_WATER_VOLUME_MATERIAL
            cleaning_mode = MAP_ICON_CLEANING_MODE_MATERIAL
        else:
            repeats = MAP_ICON_REPEATS_DREAME
            suction_level = MAP_ICON_SUCTION_LEVEL_DREAME
            water_volume = MAP_ICON_WATER_VOLUME_DREAME
            cleaning_mode = MAP_ICON_CLEANING_MODE_DREAME

        if DreameVacuumMapRenderer.MAP_FONT_UNPACKED is None:
            DreameVacuumMapRenderer.MAP_FONT_UNPACKED = zlib.decompress(
                base64.b64decode(MAP_FONT_LIGHT), zlib.MAX_WBITS | 32
            )

        resources = MapRendererResources(
            icon_set=icon_set,
            robot_type=capability.robot_type.value,
            robot=robot_image,
            charger=charger_image,
            charging=MAP_ROBOT_CHARGING_IMAGE,
            cleaning=MAP_ROBOT_CLEANING_IMAGE,
            warning=MAP_ROBOT_WARNING_IMAGE,
            sleeping=MAP_ROBOT_SLEEPING_IMAGE,
            cleaning_direction=MAP_ROBOT_CLEANING_DIRECTION_IMAGE,
            selected_segment=MAP_ICON_SELECTED_SEGMENT,
            cruise_point_background=MAP_ICON_CRUISE_POINT_DREAME,
            segment={k: {"name": SEGMENT_TYPE_CODE_TO_NAME.get(k), "icon": v} for k, v in icons.items()},
            default_map_image=DEFAULT_MAP_IMAGE,
            font=base64.b64encode(DreameVacuumMapRenderer.MAP_FONT_UNPACKED).decode("utf-8"),
            rotate=MAP_ICON_ROTATE,
            delete=MAP_ICON_DELETE,
            resize=MAP_ICON_RESIZE,
            move=MAP_ICON_MOVE,
            problem=MAP_ICON_PROBLEM,
            clean=MAP_ICON_CLEAN,
            settings=MAP_ICON_SETTINGS,
            edit=MAP_ICON_EDIT,
        )

        if capability.customized_cleaning:
            resources.repeats = repeats
            resources.suction_level = suction_level
            resources.water_volume = water_volume
            resources.mop_pad_humidity = (
                MAP_ICON_MOP_PAD_HUMIDITY_MATERIAL if icon_set == 3 else MAP_ICON_MOP_PAD_HUMIDITY_DREAME
            )
            if capability.custom_cleaning_mode:
                resources.cleaning_mode = cleaning_mode
                if capability.cleaning_route:
                    resources.cleaning_route = (
                        MAP_ICON_CLEANING_ROUTE_MATERIAL if icon_set == 3 else MAP_ICON_CLEANING_ROUTE_DREAME
                    )
                elif capability.segment_mopping_settings:
                    resources.custom_mopping_route = MAP_ICON_CUSTOM_MOPPING_ROUTE_DREAME

                if capability.mop_temperature:
                    resources.mop_temperature = (
                        MAP_ICON_MOP_TEMPERATURE_MATERIAL if icon_set == 3 else MAP_ICON_MOP_TEMPERATURE_DREAME
                    )

                if capability.mop_pressure:
                    resources.mop_pressure = (
                        MAP_ICON_MOP_PRESSURE_MATERIAL if icon_set == 3 else MAP_ICON_MOP_PRESSURE_DREAME
                    )

        if capability.self_wash_base:
            resources.washing = MAP_ROBOT_WASHING_IMAGE
            resources.drying = MAP_ROBOT_DRYING_IMAGE
            if capability.hot_washing:
                resources.hot_washing = MAP_ROBOT_HOT_WASHING_IMAGE
                resources.hot_drying = MAP_ROBOT_HOT_DRYING_IMAGE

        if capability.auto_empty_base:
            resources.emptying = MAP_ROBOT_EMPTYING_IMAGE
            resources.emptying_animation = MAP_ROBOT_EMPTYING_ANIMATION

        if capability.dust_bag_drying or capability.manual_dust_bag_drying:
            resources.dust_bag_drying = MAP_ROBOT_DUST_BAG_DRYING_IMAGE
            resources.dust_bag_drying_animation = MAP_ROBOT_DUST_BAG_DRYING_ANIMATION

        if capability.wifi_map:
            resources.wifi = MAP_WIFI_IMAGE_DREAME

        if capability.camera_streaming or capability.furnitures_v2 or capability.saved_furnitures:
            resources.cruise_path_point_background = MAP_ICON_CRUISE_POINT_BG_DREAME
            resources.obstacle_background = MAP_ICON_OBSTACLE_BG_DREAME
            resources.obstacle_hidden_background = MAP_ICON_OBSTACLE_HIDDEN_BG_DREAME
            resources.obstacle = {
                i.value: {
                    "name": i.name.replace("_", " ").capitalize(),
                    "icon": OBSTACLE_TYPE_TO_ICON.get(i.value),
                    "hidden_icon": OBSTACLE_TYPE_TO_HIDDEN_ICON.get(i.value),
                }
                for i in ObstacleType
            }
            furniture_types = [i for i in FurnitureType]
            if not capability.pet_furniture:
                furniture_types = list(
                    set(furniture_types)
                    - set(
                        [
                            FurnitureType.LITTER_BOX,
                            FurnitureType.PET_BED,
                            FurnitureType.FOOD_BOWL,
                            FurnitureType.PET_TOILET,
                            FurnitureType.ENCLOSED_LITTER_BOX,
                        ]
                    )
                )

            if not capability.extended_furnitures:
                furniture_types = list(set(furniture_types) - set([i for i in FurnitureType if i.value > 13]))
                if capability.furnitures_v2:
                    furniture_types.remove(8)
                    furniture_types.insert(7, FurnitureType.ROUND_COFFEE_TABLE)

            if capability.furnitures_v2:
                if icon_set == 2 and capability.mijia:
                    dimensions = FURNITURE_V2_TYPE_MIJIA_TO_DIMENSIONS
                    images = FURNITURE_V2_TYPE_MIJIA_TO_IMAGE
                else:
                    dimensions = FURNITURE_V2_TYPE_TO_DIMENSIONS
                    images = FURNITURE_V3_TYPE_TO_IMAGE if capability.furnitures_v3 else FURNITURE_V2_TYPE_TO_IMAGE

                resources.furniture = {
                    i.value: {
                        "name": i.name.replace("_", " ").capitalize(),
                        "icon": FURNITURE_V2_TYPE_TO_ICON.get(i.value),
                        "image": images.get(i.value),
                        "dimensions": dimensions.get(i.value),
                    }
                    for i in furniture_types
                    if i.value in dimensions
                }
            else:
                resources.furniture = {
                    i.value: {
                        "name": i.name.replace("_", " ").capitalize(),
                        "icon": FURNITURE_V2_TYPE_TO_ICON.get(i.value),
                        "image": FURNITURE_TYPE_TO_IMAGE.get(i.value),
                        "dimensions": FURNITURE_TYPE_TO_DIMENSIONS.get(i.value),
                    }
                    for i in furniture_types
                }

        if as_json:
            resources = json.dumps(
                resources,
                default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value is not None),
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )

        return resources

    @staticmethod
    def get_data(
        map_data: MapData,
        capability: DreameVacuumDeviceCapability,
        icon_set: int = 0,
        include_resources: bool = False,
        robot_status: int = 0,
        station_status: int = 0,
        as_string: bool = True,
    ) -> str:
        resources = DreameVacuumMapRenderer.get_resources(capability, icon_set) if include_resources else None

        if not map_data or map_data.empty_map or (map_data.dimensions.width * map_data.dimensions.height) < 2:
            map_data_json = MapRendererData(
                size=[
                    0,
                    0,
                    0,
                    0,
                    1,
                    1,
                    0,
                    0,
                    [0, 0, 0, 0],
                ],
                data=None,
                empty_map=True,
                resources=resources,
            )
        else:
            if map_data.optimized_pixel_type is not None:
                map_data.pixel_type = map_data.optimized_pixel_type
                map_data.dimensions = map_data.optimized_dimensions
                if map_data.optimized_charger_position is not None:
                    map_data.charger_position = map_data.optimized_charger_position

            pixels = {}
            min_x = map_data.dimensions.width - 1
            min_y = map_data.dimensions.height - 1
            max_x = 0
            max_y = 0
            for y in range(map_data.dimensions.height):
                for x in range(map_data.dimensions.width):
                    px_type = int(map_data.pixel_type[x, y])
                    if px_type:
                        if px_type in pixels:
                            pixels[px_type].extend([x, y])
                        else:
                            pixels[px_type] = [x, y]
                        max_x = max(x, max_x)
                        min_x = min(x, min_x)
                        max_y = max(y, max_y)
                        min_y = min(y, min_y)

            if map_data.carpet_pixels:
                px_type = 512
                for px in map_data.carpet_pixels:
                    if px_type in pixels:
                        pixels[px_type].extend([px[0], px[1]])
                    else:
                        pixels[px_type] = [px[0], px[1]]

            crop = [0, 0, 0, 0]

            if not map_data.saved_map:
                map_data.dimensions.bounds = DreameVacuumMapRenderer._calculate_bounds(
                    map_data.dimensions, map_data.segments
                )

            if map_data.dimensions.bounds:
                min_x = max(min(map_data.dimensions.bounds[0], min_x), min_x)
                max_x = min(max(map_data.dimensions.bounds[2], max_x), max_x)
                min_y = max(min(map_data.dimensions.bounds[1], min_y), min_y)
                max_y = min(max(map_data.dimensions.bounds[3], max_y), max_y)

            if (
                min_x != (map_data.dimensions.width - 1)
                and min_y != (map_data.dimensions.height - 1)
                and max_x != 0
                and max_y != 0
            ) and (
                min_x != 0
                or min_y != 0
                or max_x != (map_data.dimensions.width - 1)
                or max_y != (map_data.dimensions.height - 1)
            ):
                crop = [
                    min_x,
                    (map_data.dimensions.height - (max_y + 1)),
                    (map_data.dimensions.width - (max_x + 1)),
                    min_y,
                ]

            for layer in pixels.keys():
                current_x_start = -1
                current_y = -1
                current_count = 0
                compressed_pixels = []
                coords = pixels[layer]
                for i in range(0, len(coords), 2):
                    x = coords[i]
                    y = coords[i + 1]
                    if y != current_y or x > (current_x_start + current_count):
                        compressed_pixels.extend([current_x_start, current_y, current_count])
                        current_x_start = x
                        current_y = y
                        current_count = 1
                    elif x != current_x_start:
                        current_count = current_count + 1
                compressed_pixels.extend([current_x_start, current_y, current_count])
                pixels[layer] = compressed_pixels[3:]

            path_types = {"S": 1, "W": 2, "M": 3}
            paths = None
            if map_data.path:
                paths = []
                coords = [
                    path_types.get(map_data.path[0].path_type),
                    map_data.path[0].x,
                    map_data.path[0].y,
                ]
                for path in map_data.path[1:]:
                    if path.path_type.value != "L":
                        paths.append(coords)
                        coords = [path_types.get(path.path_type)]
                    coords.extend([path.x, path.y])

                if len(coords) > 2:
                    paths.append(coords)

            map_data_json = MapRendererData(
                data=pixels,
                size=[
                    map_data.dimensions.left,
                    map_data.dimensions.top,
                    map_data.dimensions.original_left,
                    map_data.dimensions.original_top,
                    map_data.dimensions.width if not map_data.empty_map else 1,
                    map_data.dimensions.height if not map_data.empty_map else 1,
                    map_data.dimensions.grid_size,
                    map_data.rotation,
                    crop,
                ],
                need_optimization=True if map_data.need_optimization else None,
                map_id=map_data.map_id,
                saved_map_id=map_data.saved_map_id,
                map_index=map_data.map_index,
                saved_map_status=map_data.saved_map_status,
                empty_map=map_data.empty_map,
                temporary_map=map_data.temporary_map,
                frame_id=map_data.frame_id,
                active_segments=map_data.active_segments,
                cleanset=(
                    bool(map_data.cleanset)
                    if not map_data.temporary_map and not map_data.saved_map and not map_data.wifi_map
                    else False
                ),
                sequence=(
                    bool(map_data.sequence)
                    if not map_data.temporary_map and not map_data.saved_map and not map_data.wifi_map
                    else False
                ),
                change_mop=(
                    bool(map_data.change_mop)
                    if not map_data.temporary_map and not map_data.saved_map and not map_data.wifi_map
                    else False
                ),
                docked=map_data.docked,
                floor_material=map_data.floor_material,
                hidden_segments=map_data.hidden_segments,
                blocked_segments=map_data.blocked_segments if map_data.blocked_segments else None,
                robot_status=robot_status if not map_data.saved_map and not map_data.wifi_map else 0,
                station_status=station_status if not map_data.saved_map and not map_data.wifi_map else 0,
                saved_map=map_data.saved_map,
                wifi_map=map_data.wifi_map,
                history_map=map_data.history_map,
                recovery_map=map_data.recovery_map,
                path=paths if not map_data.saved_map and not map_data.wifi_map else [],
                robot_position=(
                    [
                        map_data.robot_position.x,
                        map_data.robot_position.y,
                        map_data.robot_position.a,
                    ]
                    if map_data.robot_position
                    else None
                ),
                charger_position=(
                    [
                        map_data.charger_position.x,
                        map_data.charger_position.y,
                        map_data.charger_position.a,
                    ]
                    if map_data.charger_position
                    else None
                ),
                router_position=(
                    [
                        map_data.router_position.x,
                        map_data.router_position.y,
                    ]
                    if map_data.router_position
                    else None
                ),
                station_segment=map_data.station_segment,
                # ai_outborders_user=map_data.ai_outborders_user,
                # ai_outborders=map_data.ai_outborders,
                # ai_outborders_new=map_data.ai_outborders_new,
                # ai_outborders_2d=map_data.ai_outborders_2d,
                # ai_furniture_warning=map_data.ai_furniture_warning,
                # walls_info=map_data.walls_info,
                # walls_info_new=map_data.walls_info_new,
                startup_method=map_data.startup_method if map_data.history_map else None,
                cleanup_method=map_data.cleanup_method if map_data.history_map else None,
                second_cleaning=map_data.second_cleaning,
                second_mopping=map_data.second_mopping,
                mop_wash_count=map_data.mop_wash_count if map_data.history_map else None,
                recommended_carpets=map_data.recommended_carpets,
                recommended_ramps=map_data.recommended_ramps,
                recommended_cliffs=map_data.recommended_cliffs,
                recommended_virtual_thresholds=map_data.recommended_virtual_thresholds,
                recommended_passable_thresholds=map_data.recommended_passable_thresholds,
                recommended_impassible_thresholds=map_data.recommended_impassible_thresholds,
                recommended_virtual_walls=map_data.recommended_virtual_walls,
                recommended_no_go_areas=map_data.recommended_no_go_areas,
                recommended_no_mopping_areas=map_data.recommended_no_mopping_areas,
                recommended_area_type=map_data.recommended_area_type,
                recommended_threshold_type=map_data.recommended_threshold_type,
                dust_collection_count=map_data.dust_collection_count if map_data.history_map else None,
                dos=map_data.dos,
                multiple_cleaning_time=map_data.multiple_cleaning_time,
                task_interrupt_reason=map_data.task_interrupt_reason if map_data.history_map else None,
                task_end_type=map_data.task_end_type if map_data.history_map else None,
                cleaning_status=map_data.cleaning_status if map_data.history_map else None,
                cleaning_map=map_data.cleaning_map,
                cleaning_map_data=(
                    DreameVacuumMapRenderer.get_data(
                        map_data.cleaning_map_data, capability, icon_set, False, 0, 0, False
                    )
                    if map_data.history_map and map_data.cleaning_map_data
                    else None
                ),
                wifi_map_data=(
                    DreameVacuumMapRenderer.get_data(map_data.wifi_map_data, capability, icon_set, False, 0, 0, False)
                    if (map_data.history_map or map_data.saved_map) and map_data.wifi_map_data
                    else None
                ),
                has_cleaned_area=map_data.has_cleaned_area,
                has_dirty_area=map_data.has_dirty_area,
                cleaned_segments=map_data.cleaned_segments,
                cleaned_area=map_data.cleaned_area,
                cleaning_time=map_data.cleaning_time,
                work_status=map_data.work_status,
                completed=map_data.completed,
                remaining_battery=map_data.remaining_battery,
                zone_cleaning=map_data.zone_cleaning,
                segments=(
                    [
                        [
                            k,
                            v.x,
                            v.y,
                            v.type,
                            base64.b64encode(v.custom_name.encode("utf-8")).decode("utf-8") if v.custom_name else None,
                            v.index,
                            v.color_index,
                            v.neighbors,
                            v.order,
                            v.suction_level,
                            v.water_volume,
                            v.cleaning_times,
                            v.cleaning_mode if v.cleanset_type != CleansetType.DEFAULT else None,
                            v.custom_mopping_route if v.cleanset_type == CleansetType.CUSTOM_MOPPING_ROUTE else None,
                            v.cleaning_route if v.cleanset_type != CleansetType.CUSTOM_MOPPING_ROUTE else None,
                            (
                                v.wetness_level
                                if v.cleanset_type == CleansetType.WETNESS_LEVEL
                                or v.cleanset_type == CleansetType.WETNESS_LEVEL_MAX_15
                                else None
                            ),
                            v.floor_material,
                            v.floor_material_direction,
                            v.visibility,
                            [v.x0, v.y0, v.x1, v.y1],
                            v.carpet_cleaning,
                            v.carpet_preferences,
                            v.mop_temperature,
                            v.mop_pressure,
                            v.mop_type,
                        ]
                        for (k, v) in map_data.segments.items()
                    ]
                    if map_data.segments
                    else None
                ),
                active_areas=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                        ]
                        for area in map_data.active_areas
                    ]
                    if map_data.active_areas
                    else []
                ),
                active_points=(
                    [[point.x0, point.y0] for point in map_data.active_points] if map_data.active_points else []
                ),
                active_cruise_points=(
                    [
                        [point.x, point.y, point.type, point.completed]
                        for point in map_data.active_cruise_points.values()
                    ]
                    if map_data.active_cruise_points
                    else []
                ),
                task_cruise_points=bool(map_data.task_cruise_points),
                virtual_walls=(
                    [
                        [virtual_wall.x0, virtual_wall.y0, virtual_wall.x1, virtual_wall.y1]
                        for virtual_wall in map_data.virtual_walls
                    ]
                    if map_data.virtual_walls
                    else []
                ),
                no_mop=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                            area.angle,
                            1 if area.hidden else 0,
                        ]
                        for area in map_data.no_mopping_areas
                    ]
                    if map_data.no_mopping_areas
                    else []
                ),
                no_go=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                            area.angle,
                        ]
                        for area in map_data.no_go_areas
                    ]
                    if map_data.no_go_areas
                    else []
                ),
                obstacles=(
                    [
                        [
                            k,
                            v.x,
                            v.y,
                            v.type.value,
                            v.possibility,
                            v.ignore_status,
                            v.picture_status,
                            v.id,
                            v.pos_x,
                            v.pos_y,
                            v.width,
                            v.height,
                            v.segment,
                            v.color_index,
                            v.segment_id,
                            v.reason.name.replace("_", " ").capitalize() if v.reason else None,
                        ]
                        for k, v in map_data.obstacles.items()
                    ]
                    if map_data.obstacles is not None
                    else None
                ),
                predefined_points=(
                    [[point.x, point.y] for point in map_data.predefined_points]
                    if map_data.predefined_points is not None
                    else None
                ),
                carpets=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                            area.id,
                            area.ellipse,
                            area.carpet_cleaning,
                            area.carpet_preferences,
                            area.carpet_type,
                            area.hidden,
                            area.tassel,
                        ]
                        for area in map_data.carpets
                    ]
                    if map_data.carpets is not None
                    else None
                ),
                deleted_carpets=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                            area.id,
                        ]
                        for area in map_data.deleted_carpets
                    ]
                    if map_data.deleted_carpets is not None
                    else None
                ),
                detected_carpets=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                            area.id,
                            area.ellipse,
                            area.carpet_cleaning,
                            area.carpet_preferences,
                            area.carpet_type,
                            area.hidden,
                            None,
                            area.ignored_areas,
                            area.segments,
                            area.polygon,
                        ]
                        for area in map_data.detected_carpets
                    ]
                    if map_data.detected_carpets is not None
                    else None
                ),
                virtual_thresholds=(
                    [[wall.x0, wall.y0, wall.x1, wall.y1] for wall in map_data.virtual_thresholds]
                    if map_data.virtual_thresholds is not None
                    else None
                ),
                passable_thresholds=(
                    [[wall.x0, wall.y0, wall.x1, wall.y1] for wall in map_data.passable_thresholds]
                    if map_data.passable_thresholds is not None
                    else None
                ),
                impassable_thresholds=(
                    [[wall.x0, wall.y0, wall.x1, wall.y1] for wall in map_data.impassable_thresholds]
                    if map_data.impassable_thresholds is not None
                    else None
                ),
                ramps=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                            area.angle,
                        ]
                        for area in map_data.ramps
                    ]
                    if map_data.ramps is not None
                    else None
                ),
                low_lying_areas=(
                    [
                        [
                            area.x0,
                            area.y0,
                            area.x1,
                            area.y1,
                            area.x2,
                            area.y2,
                            area.x3,
                            area.y3,
                            area.id,
                            area.polygon,
                            area.type,
                            area.hidden,
                            area.ms,
                            area.area,
                        ]
                        for area in map_data.low_lying_areas
                    ]
                    if map_data.low_lying_areas is not None
                    else None
                ),
                furnitures=(
                    [
                        [
                            area.x,
                            area.y,
                            area.width,
                            area.height,
                            area.type.value,
                            area.edit_type,
                            area.angle,
                            area.scale,
                            area.segment_id,
                            area.furniture_id,
                        ]
                        for key, area in map_data.furnitures.items()
                    ]
                    if map_data.furnitures is not None
                    else None
                ),
                furniture_version=map_data.furniture_version,
                curtains=(
                    [[wall.x0, wall.y0, wall.x1, wall.y1] for wall in map_data.curtains]
                    if map_data.curtains is not None
                    else None
                ),
                resources=resources,
            )

        if as_string:
            return json.dumps(
                map_data_json,
                default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value is not None),
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        return map_data_json

    def render_obstacle_image(
        self,
        image_bytes,
        obstacle: Obstacle,
        obstacle_image_crop: bool,
        render_box: bool = True,
        crop_image: bool = False,
        color: str = None,
    ):
        if image_bytes:
            if (
                not obstacle
                or not (obstacle.width and obstacle.height and obstacle.pos_x != None and obstacle.pos_y != None)
                or (not crop_image and not render_box)
            ):
                return image_bytes

            image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            w = image.size[0]
            h = image.size[1]
            crop = (int((h * 105) / 100.0) - h) * 2
            if obstacle_image_crop:
                if crop_image and h > 400:
                    image = image.crop((crop, 0, w - crop, h - int(crop / 2)))
                    w = image.size[0]
            elif crop_image:
                crop = int(round(crop * 0.55))
                image = image.crop((crop, 0, w - crop, h))
                w = image.size[0]

            if render_box and obstacle.width and obstacle.height and obstacle.type is not ObstacleType.BLOCKED_ROOM:
                x = obstacle.pos_x - 4
                y = obstacle.pos_y - 4
                width = obstacle.width + 8
                height = obstacle.height + 8

                if color:
                    stroke = 2
                    radius = 6
                    border_color = color
                    bg_color = (color[0], color[1], color[2], 25)
                else:
                    stroke = 3
                    radius = 0
                    border_color = (49, 85, 225, 255)
                    bg_color = (49, 85, 225, 30)

                x0 = ((x * w) / 100.0) - stroke
                y0 = ((y * h) / 100.0) - stroke
                x1 = (x0 + ((width * w) / 100.0)) + stroke
                y1 = (y0 + ((height * h) / 100.0)) + stroke

                if x0 <= 0:
                    new_x = int(w * 0.5 / 100.0)
                    x1 = x1 + new_x - x0
                    x0 = new_x
                if y0 <= 0:
                    new_y = int(h * 0.5 / 100.0)
                    y1 = y1 + new_y - y0
                    y0 = new_y

                if x1 >= w:
                    x1 = w - int(w * 0.5 / 100.0)
                if y1 >= image.size[1]:
                    y1 = image.size[1] - int(image.size[1] * 0.5 / 100.0)

                scale = 2
                new_layer = Image.new("RGBA", (image.size[0] * scale, image.size[1] * scale), (255, 255, 255, 0))
                draw = ImageDraw.Draw(new_layer, "RGBA")
                draw.rounded_rectangle(
                    [
                        int(round(x0 * scale)),
                        int(round(y0 * scale)),
                        int(round(x1 * scale)),
                        int(round(y1 * scale)),
                    ],
                    fill=bg_color,
                    outline=border_color,
                    width=stroke * scale,
                    radius=radius * scale,
                )
                if new_layer.size != image.size:
                    new_layer.thumbnail(image.size, Image.Resampling.LANCZOS)
                image = Image.alpha_composite(image, new_layer)

                if not color:
                    if self._obstacle_bottom_left_icon is None:
                        self._obstacle_bottom_left_icon = Image.open(
                            BytesIO(base64.b64decode(MAP_ROBOT_OBSTACLE_BOTTOM_LEFT_IMAGE))
                        ).convert("RGBA")
                        self._obstacle_top_left_icon = Image.open(
                            BytesIO(base64.b64decode(MAP_ROBOT_OBSTACLE_TOP_LEFT_IMAGE))
                        ).convert("RGBA")
                        self._obstacle_bottom_right_icon = Image.open(
                            BytesIO(base64.b64decode(MAP_ROBOT_OBSTACLE_BOTTOM_RIGHT_IMAGE))
                        ).convert("RGBA")
                        self._obstacle_top_right_icon = Image.open(
                            BytesIO(base64.b64decode(MAP_ROBOT_OBSTACLE_TOP_RIGHT_IMAGE))
                        ).convert("RGBA")

                    icon_size = int(round(5 * h / 100.0))
                    obstacle_bottom_left_icon = self._obstacle_bottom_left_icon.resize((icon_size, icon_size))
                    obstacle_top_left_icon = self._obstacle_top_left_icon.resize((icon_size, icon_size))
                    obstacle_bottom_right_icon = self._obstacle_bottom_right_icon.resize((icon_size, icon_size))
                    obstacle_top_right_icon = self._obstacle_top_right_icon.resize((icon_size, icon_size))

                    offset = 6
                    new_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
                    draw = ImageDraw.Draw(new_layer, "RGBA")
                    new_layer.paste(
                        obstacle_top_left_icon,
                        (int(round(x0 + offset)), int(round(y0 + offset))),
                    )
                    new_layer.paste(
                        obstacle_bottom_left_icon,
                        (
                            int(round(x0 + offset)),
                            int(round(y1 - obstacle_bottom_left_icon.size[1] - offset)),
                        ),
                    )
                    new_layer.paste(
                        obstacle_bottom_right_icon,
                        (
                            int(round(x1 - obstacle_top_right_icon.size[0] - offset)),
                            int(round(y1 - obstacle_bottom_right_icon.size[1] - offset)),
                        ),
                    )
                    new_layer.paste(
                        obstacle_top_right_icon,
                        (
                            int(round(x1 - obstacle_top_right_icon.size[0] - offset)),
                            int(round(y0 + offset)),
                        ),
                    )
                    image = Image.alpha_composite(image, new_layer)

            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="JPEG")
            return buffer.getvalue()

    def render_map(
        self,
        map_data: MapData,
        robot_status: int = 0,
        station_status: int = 0,
        info_text: bool = False,
    ) -> bytes:
        if map_data is None or map_data.empty_map or (map_data.dimensions.width * map_data.dimensions.height) < 2:
            return self.default_map_image

        self.render_complete = False
        now = time.time()

        if map_data.saved_map:
            robot_status = 0
            station_status = 0
        try:
            if self._cache:
                if (
                    self._map_data is None
                    or self._map_data.dimensions != map_data.dimensions
                    or self._map_data.map_id != map_data.map_id
                    or self._map_data.saved_map_status != map_data.saved_map_status
                ):
                    self._map_data = None

                if (
                    self._map_data
                    and self._map_data == map_data
                    and self._robot_status == robot_status
                    and self._station_status == station_status
                    and self._map_data.segments == map_data.segments
                    and self._map_data.frame_id == map_data.frame_id
                    and self._image
                ):
                    self.render_complete = True
                    _LOGGER.info("Skip render frame, map data not changed")
                    return self._to_buffer(self._image)

            scale = (
                2
                if self._low_resolution
                else (
                    4
                    if (map_data.saved_map_status == 2 or map_data.restored_map)
                    and not map_data.recovery_map
                    and not map_data.history_map
                    else 2 if (map_data.wifi_map or map_data.history_map) and self._cache else 3
                )
            )
            object_scale = 2

            render_material = False
            render_carpet = bool(
                (not map_data.saved_map or map_data.history_map or map_data.recovery_map) and self.config.carpet
            )
            if (map_data.saved_map_status == 2 or map_data.saved_map) and not map_data.wifi_map:
                render_material = self.config.material and map_data.floor_material
                render_carpet = render_carpet and bool(
                    map_data.carpets or map_data.detected_carpets or map_data.deleted_carpets or map_data.carpet_pixels
                )

            if scale == 3 and (render_material or render_carpet):
                scale = 2 if info_text else 4

            if not map_data.saved_map:
                if (
                    self._map_data is None
                    or self._map_data.segments != map_data.segments
                    or self._map_data.dimensions != map_data.dimensions
                    or self._map_data.saved_map_id != map_data.saved_map_id
                ):
                    map_data.dimensions.bounds = DreameVacuumMapRenderer._calculate_bounds(
                        map_data.dimensions, map_data.segments
                    )

                    if self._map_data and (
                        self._map_data.dimensions.bounds != map_data.dimensions.bounds
                        or self._map_data.saved_map_id != map_data.saved_map_id
                    ):
                        self._map_data = None
                else:
                    map_data.dimensions.bounds = self._map_data.dimensions.bounds

            if (
                not self._cache
                or self._map_data is None
                or self._map_data.active_areas != map_data.active_areas
                or self._map_data.no_mopping_areas != map_data.no_mopping_areas
                or self._map_data.no_go_areas != map_data.no_go_areas
                or self._map_data.virtual_walls != map_data.virtual_walls
                or self._map_data.virtual_thresholds != map_data.virtual_thresholds
                or self._map_data.passable_thresholds != map_data.passable_thresholds
                or self._map_data.impassable_thresholds != map_data.impassable_thresholds
                or self._map_data.ramps != map_data.ramps
                or self._map_data.carpets != map_data.carpets
                or self._map_data.curtains != map_data.curtains
                or self._map_data.segments != map_data.segments
                or self._map_data.dimensions != map_data.dimensions
                or self._map_data.restored_map != map_data.restored_map
            ):
                map_data.dimensions.padding = DreameVacuumMapRenderer._calculate_padding(
                    map_data.dimensions,
                    map_data.active_areas if self.config.active_area else None,
                    map_data.no_mopping_areas if self.config.no_mop else None,
                    map_data.no_go_areas if self.config.no_go else None,
                    map_data.virtual_walls if self.config.virtual_wall else None,
                    map_data.virtual_thresholds if self.config.pathway else None,
                    map_data.passable_thresholds if self.config.pathway else None,
                    map_data.impassable_thresholds if self.config.pathway else None,
                    map_data.ramps if self.config.ramp else None,
                    map_data.furnitures if self.config.furniture else None,
                    map_data.furniture_version,
                    map_data.curtains if self.config.curtain else None,
                    map_data.segments,
                    [14, 14, 14, 14],
                    120,
                    80,
                    scale,
                    self.icon_set,
                )

                if self._cache and self._map_data and self._map_data.dimensions.padding != map_data.dimensions.padding:
                    self._map_data = None
            else:
                map_data.dimensions.padding = self._map_data.dimensions.padding

            map_data.dimensions.scale = scale
            segment_mask = None

            if not self._low_memory and self.config.path and map_data.path and self._robot_type != RobotType.VSLAM:
                if not self._cache or self._map_data is None or self._map_data.path != map_data.path:
                    self._has_mask = False
                    for path in map_data.path:
                        if path.path_type == PathType.SWEEP_AND_MOP or path.path_type == PathType.MOP:
                            self._has_mask = True
                            break
            else:
                self._has_mask = False

            cached_layers = self._layers if self._cache else {}
            if self._cache and not self._has_mask and cached_layers.get(MapRendererLayer.PATH_MASK):
                del cached_layers[MapRendererLayer.PATH_MASK]

            if self._cache and self._map_data and self._map_data.dimensions.scale != scale:
                self._map_data = None

            if not self._cache or (self._map_data is None or self._map_data.rotation != map_data.rotation):
                self._robot_sleeping_icon = None
                self._obstacle_background = None
                self._obstacle_hidden_background = None
                self._cruise_path_point_background = None
                self._cruise_point_background = None
                self._furniture_background = None

                if self._map_data is None:
                    self._robot_charging_icon = None
                    self._robot_cleaning_icon = None
                    self._robot_warning_icon = None
                    self._robot_washing_icon = None
                    self._robot_hot_washing_icon = None
                    self._robot_drying_icon = None
                    self._robot_hot_drying_icon = None
                    self._robot_dust_bag_drying_icon = None
                    self._robot_emptying_icon = None
                    self._robot_cleaning_direction_icon = None

            bg_color = (
                ((0, 0, 0, 255) if self.color_scheme.dark or self.color_scheme.invert else (255, 255, 255, 255))
                if info_text
                else ((0, 0, 0, 0) if map_data.wifi_map else self.color_scheme.outside)
            )

            if (
                not self._cache
                or self._map_data is None
                or not cached_layers.get(MapRendererLayer.IMAGE)
                or self._map_data.active_segments != map_data.active_segments
                or self._map_data.active_areas != map_data.active_areas
                or self._map_data.segments != map_data.segments
                or self._map_data.data != map_data.data
                or (self._has_mask and not cached_layers.get(MapRendererLayer.PATH_MASK))
                or (render_material and self._map_data.floor_material != map_data.floor_material)
                or (
                    render_carpet
                    and (
                        self._map_data.carpets != map_data.carpets
                        or self._map_data.deleted_carpets != map_data.deleted_carpets
                        or self._map_data.detected_carpets != map_data.detected_carpets
                        or self._map_data.carpet_pixels != map_data.carpet_pixels
                    )
                )
            ):
                area_colors = {}
                # as implemented on the app
                if map_data.cleaning_map:
                    area_colors[MapPixelType.OUTSIDE.value] = bg_color
                    area_colors[MapPixelType.WALL.value] = self.color_scheme.wall
                    area_colors[MapPixelType.DIRTY_AREA.value] = (
                        self.color_scheme.clean_area if map_data.second_cleaning else self.color_scheme.dirty_area
                    )
                    area_colors[MapPixelType.CLEAN_AREA.value] = self.color_scheme.clean_area
                    area_colors[MapPixelType.NEW_SEGMENT.value] = self.color_scheme.passive_segment
                elif map_data.wifi_map:
                    area_colors[MapPixelType.OUTSIDE.value] = bg_color
                    area_colors[MapPixelType.WIFI_EXCELLENT.value] = (
                        129,
                        168,
                        245,
                        255,
                    )
                    area_colors[MapPixelType.WIFI_HIGH.value] = (161, 189, 242, 255)
                    area_colors[MapPixelType.WIFI_LOW.value] = (205, 218, 239, 255)
                    area_colors[MapPixelType.WIFI_POOR.value] = (217, 226, 239, 255)
                    area_colors[MapPixelType.WIFI_UNREACHED.value] = (
                        229,
                        234,
                        238,
                        255,
                    )
                    area_colors[MapPixelType.WIFI_WALL.value] = (160, 160, 160, 255)
                    area_colors[MapPixelType.NEW_SEGMENT.value] = area_colors[MapPixelType.OUTSIDE.value]
                else:
                    area_colors[MapPixelType.OUTSIDE.value] = bg_color
                    area_colors[MapPixelType.WALL.value] = self.color_scheme.wall
                    area_colors[MapPixelType.FLOOR.value] = self.color_scheme.floor
                    area_colors[MapPixelType.NEW_SEGMENT.value] = self.color_scheme.new_segment
                    area_colors[MapPixelType.UNKNOWN.value] = self.color_scheme.floor
                    area_colors[MapPixelType.OBSTACLE_WALL.value] = self.color_scheme.wall

                if map_data.cleaning_map:
                    if map_data.blocked_segments:
                        for k in map_data.blocked_segments.keys():
                            area_colors[k] = (255, 255, 255, 255)
                elif map_data.segments is not None:
                    for k, v in map_data.segments.items():
                        area_colors[100 + k] = self.color_scheme.wall
                        if not map_data.cleaning_map and not map_data.zone_cleaning:
                            if self.config.color:
                                if map_data.hidden_segments and k in map_data.hidden_segments:
                                    area_colors[k] = self.color_scheme.hidden_segment
                                    area_colors[100 + k] = self.color_scheme.hidden_segment
                                elif map_data.active_segments and k not in map_data.active_segments:
                                    area_colors[k] = self.color_scheme.passive_segment
                                elif v.color_index is not None:
                                    area_colors[k] = self.color_scheme.segment[v.color_index][0]
                            else:
                                area_colors[k] = area_colors[MapPixelType.FLOOR.value]

                pixels = np.full(
                    (
                        map_data.dimensions.height,
                        map_data.dimensions.width,
                        4,
                    ),
                    area_colors[MapPixelType.OUTSIDE.value],
                    dtype=np.uint8,
                )

                if self._has_mask:
                    mask_color = (255, 255, 255, 255)
                    mask = np.full(
                        (
                            map_data.dimensions.height,
                            map_data.dimensions.width,
                            4,
                        ),
                        (255, 255, 255, 0),
                        dtype=np.uint8,
                    )

                if map_data.history_map and map_data.blocked_segments:
                    segment_mask = np.full(
                        (
                            map_data.dimensions.height,
                            map_data.dimensions.width,
                            4,
                        ),
                        (255, 255, 255, 0),
                        dtype=np.uint8,
                    )

                min_x = map_data.dimensions.width - 1
                min_y = map_data.dimensions.height - 1
                max_x = 0
                max_y = 0

                for y in range(map_data.dimensions.height):
                    for x in range(map_data.dimensions.width):
                        px_type = int(map_data.pixel_type[x, map_data.dimensions.height - y - 1])

                        if px_type != 0:
                            pixels[y, x] = area_colors.get(px_type, area_colors[255 if px_type > 100 else 253])

                            max_x = max(x, max_x)
                            min_x = min(x, min_x)
                            max_y = max(y, max_y)
                            min_y = min(y, min_y)

                            if self._has_mask and px_type <= 100:
                                mask[y, x] = mask_color

                            if segment_mask is not None:
                                if px_type in map_data.blocked_segments:
                                    segment_mask[y, x] = self.color_scheme.blocked_segment

                if render_material or render_carpet:
                    floor_scale = 2
                    pixels = pixels.repeat(floor_scale, axis=0).repeat(floor_scale, axis=1)
                    if render_material:
                        floor_material = self.render_floor_material(
                            pixels,
                            map_data.floor_material,
                            map_data.hidden_segments,
                            map_data.pixel_type,
                            self.color_scheme.material_color,
                            map_data.dimensions,
                            floor_scale,
                        )
                        if floor_material is not None:
                            pixels = floor_material
                            _LOGGER.debug("Render MATERIAL")

                    carpet = None
                    if render_carpet:
                        carpet = self.render_carpets(
                            pixels,
                            map_data.pixel_type,
                            map_data.carpets,
                            map_data.deleted_carpets,
                            map_data.detected_carpets,
                            map_data.carpet_pixels,
                            map_data.segments,
                            map_data.hidden_segments,
                            self.color_scheme.carpet_color,
                            self.color_scheme.carpet_color_detected,
                            map_data.dimensions,
                            floor_scale,
                        )

                        if carpet is not None:
                            _LOGGER.debug("Render CARPET")
                            pixels = carpet

                    if scale != floor_scale:
                        pixels = pixels.repeat(scale / floor_scale, axis=0).repeat(scale / floor_scale, axis=1)
                else:
                    pixels = pixels.repeat(scale, axis=0).repeat(scale, axis=1)

                if self._has_mask:
                    mask = mask.repeat(scale, axis=0).repeat(scale, axis=1)

                if segment_mask is not None:
                    segment_mask = segment_mask.repeat(scale, axis=0).repeat(scale, axis=1)

                if map_data.dimensions.bounds:
                    # min_x = max(0, min(map_data.dimensions.bounds[0], min_x))
                    # max_x = min((map_data.dimensions.width - 1), max(map_data.dimensions.bounds[2], max_x))
                    # min_y = max(0, min(map_data.dimensions.bounds[1], min_y))
                    # max_y = min((map_data.dimensions.height - 1), max(map_data.dimensions.bounds[3], max_y))
                    min_x = max(min(map_data.dimensions.bounds[0], min_x), min_x)
                    max_x = min(max(map_data.dimensions.bounds[2], max_x), max_x)
                    min_y = max(min(map_data.dimensions.bounds[1], min_y), min_y)
                    max_y = min(max(map_data.dimensions.bounds[3], max_y), max_y)

                if (
                    min_x != (map_data.dimensions.width - 1)
                    and min_y != (map_data.dimensions.height - 1)
                    and max_x != 0
                    and max_y != 0
                ) and (
                    min_x != 0
                    or min_y != 0
                    or max_x != (map_data.dimensions.width - 1)
                    or max_y != (map_data.dimensions.height - 1)
                ):
                    from_y = min_y * scale
                    to_y = (max_y + 1) * scale
                    from_x = min_x * scale
                    to_x = (max_x + 1) * scale
                    pixels = pixels[from_y:to_y, from_x:to_x]
                    if self._has_mask:
                        mask = mask[from_y:to_y, from_x:to_x]
                    if segment_mask is not None:
                        segment_mask = segment_mask[from_y:to_y, from_x:to_x]
                    map_data.dimensions.crop = [
                        from_x,
                        from_y,
                        (map_data.dimensions.width - (max_x + 1)) * scale,
                        (map_data.dimensions.height - (max_y + 1)) * scale,
                    ]

                if self._map_data and self._map_data.dimensions.crop != map_data.dimensions.crop:
                    self._map_data = None

                image = Image.fromarray(pixels)
                if self._square and not map_data.wifi_map:  # and not map_data.saved_map:
                    height = image.size[0] + map_data.dimensions.padding[0] + map_data.dimensions.padding[2]
                    width = image.size[1] + map_data.dimensions.padding[1] + map_data.dimensions.padding[3]
                    if height != width:
                        dif = int(abs(height - width) / 2)
                        if height < width:
                            map_data.dimensions.padding[0] = map_data.dimensions.padding[0] + dif
                            map_data.dimensions.padding[2] = map_data.dimensions.padding[2] + dif
                        else:
                            map_data.dimensions.padding[1] = map_data.dimensions.padding[1] + dif
                            map_data.dimensions.padding[3] = map_data.dimensions.padding[3] + dif

                cached_layers[MapRendererLayer.IMAGE] = ImageOps.expand(
                    Image.fromarray(pixels),
                    border=tuple(map_data.dimensions.padding),
                    fill=bg_color,
                )

                if self._has_mask:
                    if self._cache and self._map_data:
                        self._map_data.path = None

                    cached_layers[MapRendererLayer.PATH_MASK] = ImageOps.expand(
                        Image.fromarray(mask.repeat(object_scale, axis=0).repeat(object_scale, axis=1)),
                        border=(
                            map_data.dimensions.padding[0] * object_scale,
                            map_data.dimensions.padding[1] * object_scale,
                            map_data.dimensions.padding[2] * object_scale,
                            map_data.dimensions.padding[3] * object_scale,
                        ),
                        fill=(255, 255, 255, 0),
                    )

                if segment_mask is not None:
                    segment_mask = ImageOps.expand(
                        Image.fromarray(segment_mask),
                        border=(
                            map_data.dimensions.padding[0],
                            map_data.dimensions.padding[1],
                            map_data.dimensions.padding[2],
                            map_data.dimensions.padding[3],
                        ),
                        fill=(255, 255, 255, 0),
                    )
            else:
                map_data.dimensions.crop = self._map_data.dimensions.crop

            self._calibration_points = self._calculate_calibration_points(map_data)

            image = cached_layers[MapRendererLayer.IMAGE]

            if not map_data.saved_map and map_data.path and self.config.path:
                if (
                    not self._cache
                    or self._map_data is None
                    or self._map_data.path != map_data.path
                    or not cached_layers.get(MapRendererLayer.PATH)
                ):
                    cached_layers[MapRendererLayer.PATH] = self.render_path(
                        map_data.path,
                        self.color_scheme.path,
                        self.color_scheme.mop_path,
                        (
                            int(image.size[0] * object_scale),
                            int(image.size[1] * object_scale),
                        ),
                        cached_layers.get(MapRendererLayer.PATH_MASK),
                        map_data.dimensions,
                        0.375 * scale * object_scale,
                        object_scale,
                    )
                    cached_layers[MapRendererLayer.PATH].thumbnail(image.size, Image.Resampling.BOX, reducing_gap=1.5)
                    _LOGGER.debug("Render PATH")
                image = Image.alpha_composite(image, cached_layers[MapRendererLayer.PATH])
            elif self._cache and cached_layers.get(MapRendererLayer.PATH):
                del cached_layers[MapRendererLayer.PATH]

            image = self.render_objects(cached_layers, map_data, robot_status, station_status, image, object_scale)

            if segment_mask is not None:
                image = Image.alpha_composite(
                    image,
                    self.render_blocked_segments(
                        map_data.blocked_segments,
                        map_data.segments,
                        image.size,
                        segment_mask,
                        map_data.dimensions,
                        map_data.rotation,
                        map_data.cleaning_map,
                    ),
                )

            if map_data.rotation == 90:
                image = image.transpose(Image.ROTATE_90)
            elif map_data.rotation == 180:
                image = image.transpose(Image.ROTATE_180)
            elif map_data.rotation == 270:
                image = image.transpose(Image.ROTATE_270)

            if info_text:
                base_width = 490  # int(round(image.size[0] / 4 * 3))
                if image.size[0] > base_width:
                    image = image.resize(
                        (
                            base_width,
                            int((float(image.size[1]) * float((base_width / float(image.size[0]))))),
                        ),
                        Image.Resampling.LANCZOS,
                    )

                header_text = f"{time.strftime(('%Y.%m.%d %H:%M:%S' if bool(map_data.saved_map or map_data.recovery_map or map_data.wifi_map) else '%m/%d %H:%M'), time.localtime(map_data.last_updated))}"
                if map_data.history_map:
                    if map_data.task_cruise_points is None:
                        if map_data.startup_method is not None:
                            header_text = f"{header_text} | {map_data.startup_method.name.replace('_', ' ').title().replace('App', 'APP')}"

                        if map_data.second_cleaning:
                            header_text = f"{header_text} | Second Cleaning"
                        elif map_data.cleanup_method is not None:
                            header_text = f"{header_text} | {map_data.cleanup_method.name.replace('_', ' ').title()}"
                elif map_data.recovery_map and map_data.recovery_map_type is not RecoveryMapType.UNKNOWN:
                    header_text = f"{header_text} | {map_data.recovery_map_type.name.replace('_', ' ').title()}"

                image_width = image.size[0]
                min_width = base_width  # int(160 * scale)
                if image_width < min_width:
                    image_width = min_width

                text_draw = ImageDraw.Draw(image, "RGBA")
                text_size = int(image_width * 0.035)
                if self._light_font_file is None:
                    self._light_font_file = zlib.decompress(base64.b64decode(MAP_FONT_LIGHT), zlib.MAX_WBITS | 32)

                text_font = ImageFont.truetype(BytesIO(self._light_font_file), text_size)
                if map_data.history_map:
                    value_font = ImageFont.truetype(BytesIO(self._light_font_file), int(text_size * 1.8))
                    name_font = ImageFont.truetype(BytesIO(self._light_font_file), int(text_size * 0.8))
                left, top, width, height = text_draw.textbbox((0, 0), header_text, font=text_font)
                max_width = image_width * 0.9
                if width > max_width:
                    lines = textwrap.wrap(header_text, width=int(max_width / (text_size / 2)))
                else:
                    lines = [header_text]

                if map_data.history_map and not map_data.task_cruise_points:
                    header_text = ""
                    if map_data.mop_wash_count:
                        header_text = f"Self-Cleaned"
                        if map_data.mop_wash_count > 1:
                            header_text = f"{header_text} {map_data.mop_wash_count}x"

                    if map_data.dust_collection_count:
                        if len(header_text):
                            header_text = f"{header_text} | "
                        header_text = f"{header_text}Auto-Emptied"
                        if map_data.dust_collection_count > 1:
                            header_text = f"{header_text} {map_data.dust_collection_count}x"

                    if len(header_text):
                        lines.append(header_text)

                max_width = 0
                header_height = int(text_size * 5) if map_data.history_map else text_size
                total_height = header_height

                line_sizes = []
                for line in lines:
                    left, top, width, height = text_draw.textbbox((0, 0), line, font=text_font)
                    line_sizes.append((width, height))
                    max_width = max(max_width, width)
                    total_height = total_height + height

                padding = int((min_width - image.size[0]) / 2)
                if padding < 0:
                    padding = 0
                image = ImageOps.expand(
                    image,
                    border=(
                        padding,
                        int(total_height) + int(padding / 2),
                        padding,
                        int(padding / 2),
                    ),
                    fill=bg_color,
                )
                image_width = image.size[0]
                text_draw = ImageDraw.Draw(image, "RGBA")

                text_color = (120, 120, 120, 255)
                value_color = (0, 0, 0, 255)
                if self.color_scheme.dark or self.color_scheme.invert:
                    text_color = (135, 135, 135, 255)
                    value_color = (255, 255, 255, 255)

                if map_data.history_map:
                    cruising_map = bool(map_data.task_cruise_points is not None)
                    map_type = "Cruising" if cruising_map else "Cleaning"
                    header_lines = [
                        (str(map_data.cleaning_time), f"{map_type} Time", "min"),
                        (
                            "Interrupted" if map_data.completed == False else "Completed",
                            f"{map_type} Status",
                            "",
                        ),
                    ]

                    if not cruising_map:
                        header_lines.append((str(map_data.cleaned_area), f"{map_type} Area", "m²"))

                    for i in range(len(header_lines)):
                        value = header_lines[i][0]
                        name = header_lines[i][1]
                        unit = header_lines[i][2]
                        left, top, value_width, value_height = text_draw.textbbox((0, 0), value, font=value_font)
                        left, top, unit_width, unit_height = text_draw.textbbox((0, 0), unit, font=name_font)
                        left, top, name_width, name_height = text_draw.textbbox((0, 0), name, font=name_font)
                        y = text_size
                        x = int(image_width * 0.06)
                        pos = []
                        if len(header_lines) == 3:
                            if i == 0:
                                value_x = x + name_width / 2
                                t1 = value_width / 2
                                t2 = unit_width / 2
                                t3 = text_size / 4
                                pos.extend(
                                    [
                                        (value_x - t1 - t2 - t3, y),
                                        (x, y + (text_size * 2)),
                                        (
                                            value_x - t2 + t1 + t3,
                                            y + value_height - unit_height,
                                        ),
                                    ]
                                )
                            elif i == 1:
                                pos.extend(
                                    [
                                        (image_width - x - value_width, text_size),
                                        (
                                            image_width - x - name_width - ((value_width - name_width) / 2),
                                            y + (text_size * 2),
                                        ),
                                    ]
                                )
                            elif i == 2:
                                t1 = text_size / 2
                                pos.extend(
                                    [
                                        (
                                            ((image_width - value_width - unit_width - t1) / 2),
                                            y,
                                        ),
                                        (
                                            (image_width - name_width) / 2,
                                            y + (text_size * 2),
                                        ),
                                        (
                                            ((image_width - unit_width + value_width + t1) / 2),
                                            y + value_height - unit_height,
                                        ),
                                    ]
                                )
                        elif len(header_lines) == 2:
                            if i == 0:
                                t1 = text_size / 2
                                pos.extend(
                                    [
                                        (
                                            ((image_width - value_width - unit_width - t1) / 2) - (image_width / 4),
                                            y,
                                        ),
                                        (
                                            ((image_width - name_width) / 2) - (image_width / 4),
                                            y + (text_size * 2),
                                        ),
                                        (
                                            ((image_width - unit_width + value_width + t1) / 2) - (image_width / 4),
                                            y + value_height - unit_height,
                                        ),
                                    ]
                                )
                            elif i == 1:
                                pos.extend(
                                    [
                                        (
                                            ((image_width - value_width) / 2) + (image_width / 4),
                                            y,
                                        ),
                                        (
                                            ((image_width - name_width) / 2) + (image_width / 4),
                                            y + (text_size * 2),
                                        ),
                                    ]
                                )

                        for k in range(len(pos)):
                            style = (value_color, value_font) if k == 0 else (text_color, name_font)
                            text_draw.text(pos[k], header_lines[i][k], fill=style[0], font=style[1])

                x = (image_width - max_width) / 2
                line_y = header_height
                for i in range(len(lines)):
                    line_x = x + (max_width - line_sizes[i][0]) / 2
                    text_draw.text((line_x, line_y), lines[i], fill=text_color, font=text_font)
                    line_y = line_y + line_sizes[i][1]

            _LOGGER.info(
                "Render frame: %s:%s took: %.2f",
                map_data.map_id,
                map_data.frame_id,
                time.time() - now,
            )

            if self._cache:
                self._map_data = map_data
                self._robot_status = robot_status
                self._station_status = station_status
                self._image = image
        except Exception:
            _LOGGER.error("Map render Failed: %s", traceback.format_exc())

        self.render_complete = True
        return self._to_buffer(self._image if self._cache else image)

    def render_objects(self, cached_layers, map_data, robot_status, station_status, map_image, scale):
        layer_size = (int(map_image.size[0] * scale), int(map_image.size[1] * scale))
        line_width = 3 if map_data.dimensions.scale > 2 else 1
        border_width = 2 if map_data.dimensions.scale > 2 else 1
        changes = []
        layers = []

        if map_data.rotation == 0 or map_data.rotation == 180 or self._square:
            width = (map_data.dimensions.width) + (
                (
                    map_data.dimensions.padding[0]
                    + map_data.dimensions.padding[2]
                    - map_data.dimensions.crop[0]
                    - map_data.dimensions.crop[2]
                )
                / map_data.dimensions.scale
            )
            robot_icon_size = width * 0.037
            icon_size = width * (0.022 if self._square else 0.027)
        else:
            height = (map_data.dimensions.height) + (
                (
                    map_data.dimensions.padding[1]
                    + map_data.dimensions.padding[3]
                    - map_data.dimensions.crop[1]
                    - map_data.dimensions.crop[3]
                )
                / map_data.dimensions.scale
            )
            robot_icon_size = height * 0.037
            icon_size = height * 0.027

        robot_icon_size = max(7, min(14, robot_icon_size))
        icon_size = max(3, min(12, icon_size))
        segment_icon_size = icon_size

        if map_data.dimensions.scale <= 2:
            robot_icon_size = robot_icon_size * 0.7
            icon_size = icon_size * 1.3

        layer = MapRendererLayer.NO_MOP
        if (
            (not map_data.saved_map or map_data.recovery_map)
            and map_data.no_mopping_areas
            and self.config.no_mop
            and (not robot_status or robot_status < 100)
        ):
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.no_mopping_areas != map_data.no_mopping_areas
                or (not robot_status or self._robot_status < 100) != (not robot_status or robot_status < 100)
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_areas(
                    map_data.no_mopping_areas,
                    self.color_scheme.no_mop_outline,
                    self.color_scheme.no_mop,
                    layer_size,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.NO_GO
        if (not map_data.saved_map or map_data.recovery_map) and map_data.no_go_areas and self.config.no_go:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.no_go_areas != map_data.no_go_areas
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_areas(
                    map_data.no_go_areas,
                    self.color_scheme.no_go_outline,
                    self.color_scheme.no_go,
                    layer_size,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.WALL
        if (not map_data.saved_map or map_data.recovery_map) and map_data.virtual_walls and self.config.virtual_wall:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.virtual_walls != map_data.virtual_walls
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_walls(
                    map_data.virtual_walls,
                    self.color_scheme.virtual_wall,
                    layer_size,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.VIRTUAL_THRESHOLD
        if map_data.virtual_thresholds and self.config.pathway:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.virtual_thresholds != map_data.virtual_thresholds
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_walls(
                    map_data.virtual_thresholds,
                    self.color_scheme.virtual_threshold,
                    layer_size,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.PASSABLE_THRESHOLD
        if map_data.passable_thresholds and self.config.pathway:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.passable_thresholds != map_data.passable_thresholds
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_thresholds(
                    map_data.passable_thresholds,
                    self.color_scheme.passable_threshold_outline,
                    self.color_scheme.passable_threshold,
                    layer_size,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.IMPASSABLE_THRESHOLD
        if map_data.impassable_thresholds and self.config.pathway:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.impassable_thresholds != map_data.impassable_thresholds
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_thresholds(
                    map_data.impassable_thresholds,
                    self.color_scheme.impassable_threshold_outline,
                    self.color_scheme.impassable_threshold,
                    layer_size,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.RAMP
        if map_data.ramps and self.config.ramp:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.ramps != map_data.ramps
                or self._map_data.rotation != map_data.rotation
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_ramps(
                    map_data.ramps,
                    self.color_scheme.ramp_outline,
                    self.color_scheme.ramp,
                    layer_size,
                    map_data.dimensions,
                    line_width,
                    scale,
                    map_data.rotation,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.CURTAIN
        if map_data.curtains and self.config.curtain:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.curtains != map_data.curtains
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_curtains(
                    map_data.curtains,
                    self.color_scheme.curtain,
                    layer_size,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.LOW_LYING_AREA
        if map_data.low_lying_areas and self.config.low_lying_area:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.low_lying_areas != map_data.low_lying_areas
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_low_lying_areas(
                    map_data.low_lying_areas,
                    layer_size,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.FURNITURES
        if map_data.furnitures and self.config.furniture:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.furnitures != map_data.furnitures
                or self._map_data.rotation != map_data.rotation
                or not cached_layers.get(layer)
            ):
                if layer not in cached_layers:
                    cached_layers[MapRendererLayer.FURNITURE] = {}
                else:
                    for k in list(cached_layers[MapRendererLayer.FURNITURE].keys()).copy():
                        if k not in map_data.furnitures:
                            del cached_layers[MapRendererLayer.FURNITURE][k]

                changed = False
                for k, v in map_data.furnitures.items():
                    if (
                        not self._cache
                        or self._map_data is None
                        or k not in cached_layers[MapRendererLayer.FURNITURE]
                        or not self._map_data.furnitures
                        or k not in self._map_data.furnitures
                        or self._map_data.furnitures[k] != v
                        or self._map_data.rotation != map_data.rotation
                        or self._map_data.hidden_segments != map_data.hidden_segments
                    ):
                        changed = True
                        cached_layers[MapRendererLayer.FURNITURE][k] = self.render_furniture(
                            v,
                            map_data.furniture_version,
                            map_data.hidden_segments,
                            layer_size,
                            map_data.dimensions,
                            int((icon_size * 1.2) * map_data.dimensions.scale),
                            map_data.rotation,
                            scale,
                        )

                if changed:
                    changes.append(layer)
                    DreameVacuumMapRenderer._combine_layers(
                        cached_layers, layer_size, layer, MapRendererLayer.FURNITURE
                    )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.ACTIVE_AREA
        if not map_data.saved_map and map_data.active_areas and self.config.active_area:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.active_areas != map_data.active_areas
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_areas(
                    map_data.active_areas,
                    self.color_scheme.active_area_outline,
                    self.color_scheme.active_area,
                    layer_size,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.ACTIVE_POINT
        if not map_data.saved_map and map_data.active_points and self.config.active_point:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.active_points != map_data.active_points
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_points(
                    map_data.active_points,
                    self.color_scheme.active_point_outline,
                    self.color_scheme.active_point,
                    layer_size,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.SEGMENTS
        if (
            map_data.segments
            and not (map_data.history_map and map_data.task_cruise_points)
            and not map_data.zone_cleaning
            and (
                self.config.icon
                or self.config.name
                or self.config.order
                or self.config.suction_level
                or self.config.water_volume
                or self.config.cleaning_times
                or self.config.cleaning_mode
                or self.config.mopping_mode
            )
        ):
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.segments != map_data.segments
                or self._map_data.rotation != map_data.rotation
                or (not self._map_data.cleaning_map and self._map_data.active_segments != map_data.active_segments)
                or (not self._map_data.cleaning_map and self._map_data.hidden_segments != map_data.hidden_segments)
                or (self._map_data.cleaning_map and self._map_data.blocked_segments != map_data.blocked_segments)
                or bool((not map_data.saved_map or map_data.recovery_map) and self._map_data.cleanset)
                != bool((not map_data.saved_map or map_data.recovery_map) and map_data.cleanset)
                or not cached_layers.get(layer)
            ):
                if MapRendererLayer.SEGMENT not in cached_layers:
                    cached_layers[MapRendererLayer.SEGMENT] = {}
                else:
                    for k in list(cached_layers[MapRendererLayer.SEGMENT].keys()).copy():
                        if k not in map_data.segments:
                            del cached_layers[MapRendererLayer.SEGMENT][k]

                changed = False
                for k in sorted(map_data.segments.keys()):
                    v = map_data.segments[k]
                    if (
                        not self._cache
                        or self._map_data is None
                        or k not in cached_layers[MapRendererLayer.SEGMENT]
                        or not self._map_data.segments
                        or k not in self._map_data.segments
                        or self._map_data.segments[k] != v
                        or self._map_data.rotation != map_data.rotation
                        or bool((not map_data.saved_map or map_data.recovery_map) and self._map_data.cleanset)
                        != bool((not map_data.saved_map or map_data.recovery_map) and map_data.cleanset)
                        or bool(
                            (
                                (not map_data.active_segments or k in map_data.active_segments)
                                and (not map_data.hidden_segments or k not in map_data.hidden_segments)
                                and not map_data.cleaning_map
                            )
                        )
                        != bool(
                            (
                                (not self._map_data.active_segments or k in self._map_data.active_segments)
                                and (not self._map_data.hidden_segments or k not in self._map_data.hidden_segments)
                                and not self._map_data.cleaning_map
                            )
                        )
                        or bool(
                            (map_data.cleaning_map and (map_data.blocked_segments and k in map_data.blocked_segments))
                        )
                        != bool(
                            (
                                self._map_data.cleaning_map
                                and self._map_data.blocked_segments
                                and k in self._map_data.blocked_segments
                            )
                        ),
                    ):
                        changed = True
                        cached_layers[MapRendererLayer.SEGMENT][k] = self.render_segment(
                            v,
                            bool((not map_data.saved_map or map_data.recovery_map) and map_data.cleanset),
                            bool((not map_data.saved_map or map_data.recovery_map) and map_data.sequence),
                            layer_size,
                            map_data.dimensions,
                            int(segment_icon_size * map_data.dimensions.scale),
                            map_data.rotation,
                            scale,
                            (
                                (not map_data.active_segments or k in map_data.active_segments)
                                and (not map_data.hidden_segments or k not in map_data.hidden_segments)
                                and not map_data.cleaning_map
                            ),
                            (map_data.cleaning_map and map_data.blocked_segments and k in map_data.blocked_segments),
                        )

                if changed:
                    changes.append(layer)
                    DreameVacuumMapRenderer._combine_layers(cached_layers, layer_size, layer, MapRendererLayer.SEGMENT)
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.CHARGER
        if map_data.charger_position and self.config.charger:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.charger_position != map_data.charger_position
                or self._map_data.rotation != map_data.rotation
                or self._station_status != station_status
                or not cached_layers.get(layer)
            ):
                # def correct_charger_position(chargerPos, pixel_type, width, height, x, y, gridWidth, borderValue):
                #    newChargerPos = copy.deepcopy(chargerPos)
                #    tmpAngle = newChargerPos.a % 360

                #    if tmpAngle < 0:
                #        tmpAngle += 360

                #    chargerX = int((newChargerPos.x - x) / gridWidth)
                #    chargerY = int((newChargerPos.y - y) / gridWidth)
                #    value = pixel_type[chargerX, chargerY]

                #    if value == borderValue or chargerX < 0 or chargerX >= width or chargerY < 0 or chargerY >= height:
                #        return chargerPos

                #    isChargerInMap = value != 0
                #    delta = 3

                #    for crossDelta in range(4):
                #        if tmpAngle > 45 and tmpAngle < 135 or tmpAngle > 225 and tmpAngle < 315:
                #            startY = 0 if ((chargerY - delta) < 0) else (chargerY - delta)
                #            endY = (height - 1) if ((chargerY + delta) > (height - 1)) else (chargerY + delta)

                #            if tmpAngle > 45 and tmpAngle < 135:
                #                if isChargerInMap:
                #                    endY = chargerY
                #                else:
                #                    startY = chargerY
                #            else:
                #                if isChargerInMap:
                #                    startY = chargerY
                #                else:
                #                    endY = chargerY

                #            findY = -1

                #            for j in range(startY, endY + 1):
                #                startX = -1

                #                for i in range(width):
                #                    leftIndex = (i - 1) if ((i - 1) >= 0) else -1
                #                    rightIndex = (i + 1) if ((i + 1) < width) else -1

                #                    if pixel_type[i, j] == borderValue and (i == 0 or leftIndex != -1 and pixel_type[leftIndex, j] != borderValue):
                #                        startX = i

                #                        if pixel_type[i + 1, j] != borderValue:
                #                            if (chargerX + crossDelta) >= startX and (chargerX - crossDelta) <= i:
                #                                if findY == -1:
                #                                    findY = j
                #                                elif abs(chargerY - j) < abs(findY - j):
                #                                    findY = j
                #                            startX = -1

                #                        continue

                #                    if pixel_type[i, j] == borderValue and startX != -1 and (i == (width - 1) or rightIndex != -1 and pixel_type[rightIndex, j] != borderValue):
                #                        if (chargerX + crossDelta) >= startX and (chargerX - crossDelta) <= i:
                #                            if findY == -1:
                #                                findY = j
                #                            elif abs(chargerY - j) < abs(findY - j):
                #                                findY = j

                #                        startX = -1
                #            if findY != -1:
                #                newChargerPos.y = y + findY * gridWidth
                #                break
                #        else:
                #            _startX = 0 if ((chargerX - delta) < 0) else (chargerX - delta)
                #            endX = (width - 1) if ((chargerX + delta) > (width - 1)) else (chargerX + delta)

                #            if tmpAngle >= 0 and tmpAngle <= 45 or tmpAngle >= 315 and tmpAngle < 360:
                #                if isChargerInMap:
                #                    endX = chargerX
                #                else:
                #                    _startX = chargerX
                #            else:
                #                if isChargerInMap:
                #                    _startX = chargerX
                #                else:
                #                    endX = chargerX

                #            findX = -1

                #            for _i in range(_startX, endX + 1):
                #                _startY = -1

                #                for _j in range(height):
                #                    topIndex = (_j - 1) if ((_j - 1) >= 0) else -1
                #                    bottomIndex = (_j + 1) if ((_j + 1) < height) else -1

                #                    if pixel_type[_i, _j] == borderValue and (_j == 0 or topIndex != -1 and pixel_type[_i, topIndex] != borderValue):
                #                        _startY = _j

                #                        if pixel_type[_i, (_j + 1)] != borderValue:
                #                            if ((chargerY + crossDelta) >= _startY) and ((chargerY - crossDelta) <= _j):
                #                                if findX == -1:
                #                                    findX = _i
                #                                elif abs(chargerX - _i) < abs(findX - _i):
                #                                    findX = _i
                #                            _startY = -1

                #                        continue

                #                    if pixel_type[_i, _j] == borderValue and _startY != -1 and (_j == height - 1 or bottomIndex != -1 and pixel_type[_i, bottomIndex] != borderValue):
                #                        if ((chargerY + crossDelta) >= _startY) and ((chargerY - crossDelta) <= _j):
                #                            if findX == -1:
                #                                findX = _i
                #                            elif abs(chargerX - _i) < abs(findX - _i):
                #                                findX = _i

                #                        _startY = -1

                #            if findX != -1:
                #                newChargerPos.x = x + findX * gridWidth
                #                break

                #    return newChargerPos

                charger_position = map_data.charger_position
                offset = 0
                if self._robot_type != RobotType.VSLAM and self.icon_set == 2:
                    offset = int(robot_icon_size * 21.42)
                elif self._robot_type == RobotType.VSLAM and self.icon_set == 3:
                    offset = int(-robot_icon_size * 18)

                if offset:
                    charger_position = Point(
                        charger_position.x - offset * math.cos(charger_position.a * math.pi / 180),
                        charger_position.y - offset * math.sin(charger_position.a * math.pi / 180),
                        charger_position.a,
                    )

                changes.append(layer)
                cached_layers[layer] = self.render_charger(
                    charger_position,
                    station_status,
                    layer_size,
                    map_data.dimensions,
                    int((robot_icon_size * (map_data.dimensions.scale if map_data.dimensions.scale > 2 else 3)) * 1.2),
                    map_data.rotation,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.ROBOT
        if not map_data.saved_map and map_data.robot_position and self.config.robot:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.robot_position != map_data.robot_position
                or self._map_data.charger_position != map_data.charger_position
                or self._map_data.rotation != map_data.rotation
                or self._robot_status != robot_status
                or self._station_status != station_status
                or self._map_data.docked != map_data.docked
                or not cached_layers.get(layer)
            ):
                robot_position = map_data.robot_position

                if map_data.docked and map_data.charger_position:
                    # Calculate charger angle
                    charger_angle = map_data.charger_position.a
                    if self._robot_type != RobotType.VSLAM:
                        offset = int(
                            robot_icon_size * (15 if self._robot_type == RobotType.SWEEPING_AND_MOPPING else 21.42)
                        )

                        if self.icon_set != 2:
                            if charger_angle > -45 and charger_angle < 45:
                                charger_angle = 0
                            elif (
                                charger_angle > -45
                                and charger_angle <= 45
                                or charger_angle > 315
                                and charger_angle <= 405
                            ):
                                charger_angle = 0
                            elif (
                                charger_angle > 45
                                and charger_angle <= 135
                                or charger_angle > -315
                                and charger_angle <= -225
                            ):
                                charger_angle = 90
                            elif (
                                charger_angle > 135
                                and charger_angle <= 225
                                or charger_angle > -225
                                and charger_angle <= -135
                            ):
                                charger_angle = 180
                            elif (
                                charger_angle > 225
                                and charger_angle <= 315
                                or charger_angle > -135
                                and charger_angle <= -45
                            ):
                                charger_angle = 270
                    else:
                        offset = int(robot_icon_size * 35.71)

                    robot_position = Point(
                        map_data.charger_position.x + offset * math.cos(charger_angle * math.pi / 180),
                        map_data.charger_position.y + offset * math.sin(charger_angle * math.pi / 180),
                        (
                            charger_angle + 180
                            if self._robot_type != RobotType.MOPPING
                            and self._robot_type != RobotType.SWEEPING_AND_MOPPING
                            else charger_angle
                        ),
                    )

                changes.append(layer)
                cached_layers[layer] = self.render_vacuum(
                    robot_position,
                    robot_status,
                    layer_size,
                    map_data.dimensions,
                    int(robot_icon_size * (map_data.dimensions.scale if map_data.dimensions.scale > 2 else 3)),
                    map_data.rotation,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.ROUTER
        if map_data.router_position and map_data.wifi_map:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.router_position != map_data.router_position
                or self._map_data.rotation != map_data.rotation
                or not cached_layers.get(layer)
            ):
                changes.append(layer)
                cached_layers[layer] = self.render_router(
                    map_data.router_position,
                    layer_size,
                    map_data.dimensions,
                    int((robot_icon_size * 1.25) * map_data.dimensions.scale),
                    map_data.rotation,
                    scale,
                )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.OBSTACLES
        if not map_data.saved_map and map_data.obstacles and (self.config.obstacle or self.config.pet):
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.obstacles != map_data.obstacles
                or self._map_data.rotation != map_data.rotation
                or not cached_layers.get(layer)
            ):
                if MapRendererLayer.OBSTACLE not in cached_layers:
                    cached_layers[MapRendererLayer.OBSTACLE] = {}
                else:
                    for k in list(cached_layers[MapRendererLayer.OBSTACLE].keys()).copy():
                        if k not in map_data.obstacles:
                            del cached_layers[MapRendererLayer.OBSTACLE][k]

                changed = False
                for k, v in map_data.obstacles.items():
                    if (
                        not self.config.obstacle
                        and v.type != ObstacleType.PET
                        and v.type != ObstacleType.LIQUID_STAIN
                        and v.type != ObstacleType.DRIED_STAIN
                        and v.type != ObstacleType.UNCLEANABLE_STAIN
                        and v.type != ObstacleType.DETECTED_STAIN
                        and v.type != ObstacleType.CLEANED_STAIN
                        and v.type != ObstacleType.SKIPPED_UNCLEANABLE_STAIN
                        and v.type != ObstacleType.CLEANED_DRIED_STAIN
                        and v.type != ObstacleType.LARGE_PARTICLES
                        and v.type != ObstacleType.CLEANED_LARGE_PARTICLES
                    ):
                        continue
                    if (
                        not self.config.stain
                        and v.type != ObstacleType.LIQUID_STAIN
                        and v.type != ObstacleType.DRIED_STAIN
                        and v.type != ObstacleType.UNCLEANABLE_STAIN
                        and v.type != ObstacleType.DETECTED_STAIN
                        and v.type != ObstacleType.CLEANED_STAIN
                        and v.type != ObstacleType.SKIPPED_UNCLEANABLE_STAIN
                        and v.type != ObstacleType.CLEANED_DRIED_STAIN
                    ):
                        continue
                    elif not self.config.pet and (
                        v.type == ObstacleType.PET
                        or v.type == ObstacleType.FOOD_BOWL
                        or v.type == ObstacleType.PET_BED
                    ):
                        continue
                    elif (
                        v.type == ObstacleType.BLOCKED_ROOM and not map_data.history_map and not map_data.cleaning_map
                    ):
                        continue

                    if (
                        not self._cache
                        or self._map_data is None
                        or k not in cached_layers[MapRendererLayer.OBSTACLE]
                        or not self._map_data.obstacles
                        or k not in self._map_data.obstacles
                        or self._map_data.obstacles[k] != v
                        or self._map_data.rotation != map_data.rotation
                    ):
                        obstacle_image = self.render_obstacle(
                            v,
                            layer_size,
                            map_data.dimensions,
                            int((icon_size * 1.2) * map_data.dimensions.scale),
                            map_data.rotation,
                            scale,
                        )
                        if obstacle_image:
                            changed = True
                            cached_layers[MapRendererLayer.OBSTACLE][k] = obstacle_image
                        elif k in cached_layers[MapRendererLayer.OBSTACLE]:
                            del cached_layers[MapRendererLayer.OBSTACLE][k]

                if changed:
                    changes.append(layer)
                    DreameVacuumMapRenderer._combine_layers(
                        cached_layers, layer_size, layer, MapRendererLayer.OBSTACLE
                    )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        layer = MapRendererLayer.CRUISE_POINTS
        if not map_data.saved_map and map_data.active_cruise_points:  # and self.config.cruise_point:
            layers.append(layer)
            if (
                not self._cache
                or self._map_data is None
                or self._map_data.active_cruise_points != map_data.active_cruise_points
                or self._map_data.rotation != map_data.rotation
                or not cached_layers.get(layer)
            ):
                if MapRendererLayer.CRUISE_POINT not in cached_layers:
                    cached_layers[MapRendererLayer.CRUISE_POINT] = {}
                else:
                    for k in list(cached_layers[MapRendererLayer.CRUISE_POINT].keys()).copy():
                        if k not in map_data.active_cruise_points:
                            del cached_layers[MapRendererLayer.CRUISE_POINT][k]

                changed = False
                for k, v in map_data.active_cruise_points.items():
                    if (
                        self._map_data is None
                        or k not in cached_layers[MapRendererLayer.CRUISE_POINT]
                        or not self._map_data.active_cruise_points
                        or k not in self._map_data.active_cruise_points
                        or self._map_data.active_cruise_points[k] != v
                        or self._map_data.rotation != map_data.rotation
                    ):
                        changed = True
                        cached_layers[MapRendererLayer.CRUISE_POINT][k] = self.render_cruise_point(
                            k,
                            v,
                            layer_size,
                            map_data.dimensions,
                            int(round(icon_size * 1.25 * map_data.dimensions.scale)),
                            map_data.rotation,
                            scale,
                        )

                if changed:
                    changes.append(layer)
                    DreameVacuumMapRenderer._combine_layers(
                        cached_layers, layer_size, layer, MapRendererLayer.CRUISE_POINT
                    )
        elif self._cache and cached_layers.get(layer):
            changes.append(layer)
            del cached_layers[layer]

        if changes or not self._cache:
            cached_layers[MapRendererLayer.OBJECTS] = Image.new(
                "RGBA",
                [layer_size[0], layer_size[1]],
                (255, 255, 255, 0),
            )
            for l in layers:
                if cached_layers.get(l):
                    if l in changes:
                        _LOGGER.debug("Render %s", l.name)
                    cached_layers[MapRendererLayer.OBJECTS] = Image.alpha_composite(
                        cached_layers[MapRendererLayer.OBJECTS], cached_layers[l]
                    )

            if layer_size != map_image.size:
                cached_layers[MapRendererLayer.OBJECTS].thumbnail(
                    map_image.size, Image.Resampling.BOX, reducing_gap=1.5
                )
        else:
            if not cached_layers.get(MapRendererLayer.OBJECTS):
                return map_image

        return Image.alpha_composite(
            map_image,
            cached_layers[MapRendererLayer.OBJECTS],
        )

    def render_areas(self, areas, color, fill, layer_size, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for area in areas:
            p = area.to_img(dimensions)
            draw.polygon(
                [
                    p.x0 * scale,
                    p.y0 * scale,
                    p.x1 * scale,
                    p.y1 * scale,
                    p.x2 * scale,
                    p.y2 * scale,
                    p.x3 * scale,
                    p.y3 * scale,
                ],
                fill,
                color,
                width=(width * scale),
            )
        return new_layer

    def render_points(self, points, color, fill, layer_size, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        size = 15 * dimensions.grid_size
        for point in points:
            area = Area(
                point.x - size,
                point.y - size,
                point.x + size,
                point.y - size,
                point.x + size,
                point.y + size,
                point.x - size,
                point.y + size,
            )

            p = area.to_img(dimensions)
            coords = [
                p.x0 * scale,
                p.y0 * scale,
                p.x1 * scale,
                p.y1 * scale,
                p.x2 * scale,
                p.y2 * scale,
                p.x3 * scale,
                p.y3 * scale,
            ]
            draw.polygon(coords, fill, color, width=(width * scale))
        return new_layer

    def render_walls(self, walls, color, layer_size, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for wall in walls:
            p = wall.to_img(dimensions)
            draw.line(
                [p.x0 * scale, p.y0 * scale, p.x1 * scale, p.y1 * scale],
                color,
                width=(width * scale),
            )
        return new_layer

    def render_thresholds(self, thresholds, color, fill, layer_size, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for wall in thresholds:
            p = wall.to_img(dimensions)

            thickness = width * 8
            w = -(p.y1 - p.y0)
            h = p.x1 - p.x0
            t = math.sqrt(w * w + h * h)
            x = w / t * thickness / 2
            y = h / t * thickness / 2

            draw.polygon(
                [
                    (p.x0 - x) * scale,
                    (p.y0 - y) * scale,
                    (p.x1 - x) * scale,
                    (p.y1 - y) * scale,
                    (p.x1 + x) * scale,
                    (p.y1 + y) * scale,
                    (p.x0 + x) * scale,
                    (p.y0 + y) * scale,
                ],
                fill,
                color,
                width=(width * scale),
            )

            thickness = thickness - width
            x = w / t * thickness / 2
            y = h / t * thickness / 2

            coords = [
                (p.x0 - x) * scale,
                (p.y0 - y) * scale,
                (p.x1 - x) * scale,
                (p.y1 - y) * scale,
                (p.x1 + x) * scale,
                (p.y1 + y) * scale,
                (p.x0 + x) * scale,
                (p.y0 + y) * scale,
            ]

            bp = DreameVacuumMapRenderer._coords_on_line(coords[0], coords[1], coords[2], coords[3], thickness * scale)
            tp = DreameVacuumMapRenderer._coords_on_line(coords[6], coords[7], coords[4], coords[5], thickness * scale)

            for i in range(len(tp) - 1):
                draw.line(
                    [tp[i][0], tp[i][1], bp[i + 1][0], bp[i + 1][1]], color, width=(width * scale), joint="curve"
                )
        return new_layer

    def render_curtains(self, curtains, color, layer_size, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for wall in curtains:
            p = wall.to_img(dimensions)

            w = -(p.y1 - p.y0)
            h = p.x1 - p.x0
            t = math.sqrt(w * w + h * h)
            x = w / t * 5
            y = h / t * 5

            coords = [
                (p.x0 - x) * scale,
                (p.y0 - y) * scale,
                (p.x1 - x) * scale,
                (p.y1 - y) * scale,
                (p.x1 + x) * scale,
                (p.y1 + y) * scale,
                (p.x0 + x) * scale,
                (p.y0 + y) * scale,
            ]

            t = int(
                math.floor(
                    math.sqrt((wall.x0 - wall.x1) * (wall.x0 - wall.x1) + (wall.y0 - wall.y1) * (wall.y0 - wall.y1))
                    / 150
                )
            )
            tp = DreameVacuumMapRenderer._coords_on_line(coords[6], coords[7], coords[4], coords[5], 0, t + 1)
            bp = DreameVacuumMapRenderer._coords_on_line(coords[0], coords[1], coords[2], coords[3], 0, t + 1)

            path = []
            for i in range(0, len(tp) - 1, 2):
                path.extend([tp[i][0], tp[i][1], bp[i + 1][0], bp[i + 1][1]])
            draw.line(path, color, width=(width * scale), joint="curve")

        return new_layer

    def render_ramps(self, ramps, color, fill, layer_size, dimensions, width, scale, rotation):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for area in ramps:
            p = area.to_img(dimensions)
            draw.polygon(
                [
                    p.x0 * scale,
                    p.y0 * scale,
                    p.x1 * scale,
                    p.y1 * scale,
                    p.x2 * scale,
                    p.y2 * scale,
                    p.x3 * scale,
                    p.y3 * scale,
                ],
                fill,
                color,
                width=(width * scale),
            )

            p0 = Point(area.x0, area.y0).to_img(dimensions)
            p1 = Point(area.x2, area.y2).to_img(dimensions)

            x_coords = sorted([p0.x, p1.x])
            y_coords = sorted([p0.y, p1.y])
            min_x = x_coords[0]
            min_y = y_coords[0]
            max_x = x_coords[1]
            max_y = y_coords[1]
            w = max_x - min_x
            h = max_y - min_y

            m = min(w, h)
            s = width
            size = 8.165 * dimensions.scale

            if m < size:
                s /= 2
                size = m * 0.6

            sx = int(w / size)
            sy = int(h / size)
            rw = size * 0.6
            rh = rw / 2
            xx = (w - sx * rw) / (sx + 1)
            yy = (h - sy * rh) / (sy + 1)

            arrow_image = Image.new("RGBA", (int(w * scale), int(h * scale)), (255, 255, 255, 0))
            arrow_draw = ImageDraw.Draw(arrow_image, "RGBA")

            for k in range(sx):
                for j in range(sy):
                    x = xx * (k + 1) + rw * k
                    y = h - yy * (j + 1) - rh * j
                    arrow_draw.line(
                        [x * scale, y * scale, (x + rh) * scale, (y - rh) * scale, (x + (rh * 2)) * scale, y * scale],
                        width=int(s * scale),
                        fill=color,
                        joint="curve",
                    )

            arrow_image = arrow_image.rotate(area.angle, expand=1)
            new_layer.paste(
                arrow_image,
                (
                    int(((min_x + (w / 2)) * scale) - (arrow_image.size[0] / 2)),
                    int(((min_y + (h / 2)) * scale) - (arrow_image.size[1] / 2)),
                ),
                arrow_image,
            )

        return new_layer

    def render_path(self, path, color, mop_color, layer_size, mask, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        sweep = []
        mop = []
        sweep_path = []
        mop_path = []
        path_type = ""

        for point in path:
            p = point.to_img(dimensions, True)
            if point.path_type == PathType.LINE:
                l = [p.x * scale, p.y * scale]
                if path_type == PathType.SWEEP_AND_MOP or (path_type == PathType.SWEEP or self._low_memory):
                    sweep_path.extend(l)

                if not self._low_memory and (path_type == PathType.SWEEP_AND_MOP or path_type == PathType.MOP):
                    mop_path.extend(l)
            else:
                if mop_path:
                    mop.append(mop_path)

                if sweep_path:
                    sweep.append(sweep_path)

                path_type = point.path_type
                if path_type == PathType.SWEEP_AND_MOP or (path_type == PathType.SWEEP or self._low_memory):
                    sweep_path = [p.x * scale, p.y * scale]
                else:
                    sweep_path = []

                if not self._low_memory and (path_type == PathType.SWEEP_AND_MOP or path_type == PathType.MOP):
                    mop_path = [p.x * scale, p.y * scale]
                else:
                    mop_path = []

        if sweep_path:
            sweep.append(sweep_path)

        if mop_path:
            mop.append(mop_path)

        if mop and mask:
            mop_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
            mop_draw = ImageDraw.Draw(mop_layer, "RGBA")

        for path in mop:
            size = width * scale * 10.5
            (mop_draw if mask else draw).line(
                path,
                width=int(round(size)),
                fill=mop_color,
                joint="curve",
            )

        if mop and mask:
            new_layer.paste(mop_layer, (0, 0), mask=mask)

        for path in sweep:
            size = width * scale
            draw.line(
                path,
                width=int(round(size)),
                fill=color,
                joint="curve",
            )
            size = int(math.floor(size / 2))
            draw.ellipse(
                [
                    path[-2] - size,
                    path[-1] - size,
                    path[-2] + size,
                    path[-1] + size,
                ],
                fill=color,
            )
            draw.ellipse(
                [
                    path[0] - size,
                    path[1] - size,
                    path[0] + size,
                    path[1] + size,
                ],
                fill=color,
            )

        return new_layer

    def render_charger(
        self,
        charger_position,
        station_status,
        layer_size,
        dimensions,
        size,
        map_rotation,
        scale,
    ):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        icon_size = int(size * scale)
        if self.icon_set == 3:
            icon_size = int(icon_size * 1.2)
        elif self.icon_set == 2:
            icon_size = int(icon_size * 1.5)
        elif self._robot_type == RobotType.VSLAM:
            icon_size = int(icon_size * 1.5)

        if self._charger_icon is None:
            if self.icon_set == 3:
                charger_image = MAP_CHARGER_IMAGE_MATERIAL
            elif self.icon_set == 2:
                charger_image = MAP_CHARGER_IMAGE_MIJIA
            else:
                if self._robot_type == RobotType.VSLAM:
                    charger_image = MAP_CHARGER_VSLAM_IMAGE_DREAME
                else:
                    charger_image = MAP_CHARGER_IMAGE_DREAME
            self._charger_icon = Image.open(BytesIO(base64.b64decode(charger_image))).convert("RGBA")

            if self.icon_set == 3:
                self._charger_icon = DreameVacuumMapRenderer._set_icon_color(
                    self._charger_icon,
                    icon_size,
                    (0, 255, 126),
                )

            if self.color_scheme.dark:
                enhancer = ImageEnhance.Brightness(self._charger_icon)
                self._charger_icon = enhancer.enhance(0.7)

        charger_icon = self._charger_icon.resize((icon_size, icon_size), resample=Image.Resampling.NEAREST).rotate(
            (
                charger_position.a
                if self._robot_type == RobotType.VSLAM
                or self.icon_set == 0
                or self.icon_set == 2
                or self.icon_set == 3
                else (-map_rotation)
            ),
            expand=1,
        )

        point = charger_position.to_img(dimensions)
        new_layer.paste(
            charger_icon,
            (
                int((point.x * scale) - (charger_icon.size[0] / 2)),
                int((point.y * scale) - (charger_icon.size[1] / 2)),
            ),
            charger_icon,
        )

        if station_status > 0 and not self._low_memory:
            hot_washing = False
            if station_status >= 10:
                hot_washing = True
                station_status = station_status - 10

            if station_status == 1:
                if self._robot_emptying_icon is None:
                    self._robot_emptying_icon = (
                        Image.open(BytesIO(base64.b64decode(MAP_ROBOT_EMPTYING_IMAGE)))
                        .convert("RGBA")
                        .resize(
                            (int(icon_size * 1.25), int(icon_size * 1.25)),
                            resample=Image.Resampling.NEAREST,
                        )
                        .rotate(-map_rotation, expand=1)
                    )
                offset = icon_size * 1.2
                icon = self._robot_emptying_icon
            elif station_status < 4:
                if not hot_washing and self._robot_washing_icon is None:
                    self._robot_washing_icon = (
                        Image.open(BytesIO(base64.b64decode(MAP_ROBOT_WASHING_IMAGE)))
                        .convert("RGBA")
                        .resize(
                            (int(icon_size * 1.25), int(icon_size * 1.25)),
                            resample=Image.Resampling.NEAREST,
                        )
                        .rotate(-map_rotation, expand=1)
                    )
                    enhancer = ImageEnhance.Brightness(self._robot_washing_icon)
                    if self.color_scheme.dark:
                        self._robot_washing_icon = enhancer.enhance(0.65)

                if hot_washing and self._robot_hot_washing_icon is None:
                    self._robot_hot_washing_icon = (
                        Image.open(BytesIO(base64.b64decode(MAP_ROBOT_HOT_WASHING_IMAGE)))
                        .convert("RGBA")
                        .resize(
                            (int(icon_size * 1.25), int(icon_size * 1.25)),
                            resample=Image.Resampling.NEAREST,
                        )
                        .rotate(-map_rotation, expand=1)
                    )
                    enhancer = ImageEnhance.Brightness(self._robot_hot_washing_icon)
                    if self.color_scheme.dark:
                        self._robot_hot_washing_icon = enhancer.enhance(0.65)

                offset = icon_size * 1.5
                icon = self._robot_hot_washing_icon if hot_washing else self._robot_washing_icon
            else:
                offset = icon_size * 1.2

                if station_status == 5 or station_status == 6:
                    if self._robot_dust_bag_drying_icon is None:
                        self._robot_dust_bag_drying_icon = (
                            Image.open(BytesIO(base64.b64decode(MAP_ROBOT_DUST_BAG_DRYING_IMAGE)))
                            .convert("RGBA")
                            .resize(
                                (int(icon_size * 1.25), int(icon_size * 1.25)),
                                resample=Image.Resampling.NEAREST,
                            )
                            .rotate(-map_rotation, expand=1)
                        )

                    icon = self._robot_dust_bag_drying_icon
                else:
                    if not hot_washing and self._robot_drying_icon is None:
                        self._robot_drying_icon = (
                            Image.open(BytesIO(base64.b64decode(MAP_ROBOT_DRYING_IMAGE)))
                            .convert("RGBA")
                            .resize(
                                (int(icon_size * 1.25), int(icon_size * 1.25)),
                                resample=Image.Resampling.NEAREST,
                            )
                            .rotate(-map_rotation, expand=1)
                        )

                    if hot_washing and self._robot_hot_drying_icon is None:
                        self._robot_hot_drying_icon = (
                            Image.open(BytesIO(base64.b64decode(MAP_ROBOT_HOT_DRYING_IMAGE)))
                            .convert("RGBA")
                            .resize(
                                (int(icon_size * 1.25), int(icon_size * 1.25)),
                                resample=Image.Resampling.NEAREST,
                            )
                            .rotate(-map_rotation, expand=1)
                        )
                    icon = self._robot_hot_drying_icon if hot_washing else self._robot_drying_icon

            icon_x = point.x * scale
            icon_y = point.y * scale
            if map_rotation == 90:
                icon_x = icon_x + offset
            elif map_rotation == 180:
                icon_y = icon_y + offset
            elif map_rotation == 270:
                icon_x = icon_x - offset
            else:
                icon_y = icon_y - offset

            new_layer.paste(icon, (int(icon_x - (icon.size[0] / 2)), int(icon_y - (icon.size[1] / 2))))

        return new_layer

    def render_vacuum(
        self,
        robot_position,
        robot_status,
        layer_size,
        dimensions,
        size,
        map_rotation,
        scale,
    ):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        icon_size = int(size * scale)
        robot_icon_size = (
            int(icon_size * 1.4)
            if self.icon_set == 2 or (self._robot_type == RobotType.VSLAM and self.icon_set == 3)
            else icon_size
        )
        if self._robot_icon is None:
            if self.icon_set == 2:
                if self._robot_type == RobotType.MOPPING:
                    robot_image = MAP_ROBOT_MOP_IMAGE_MIJIA
                elif self._robot_type == RobotType.VSLAM:
                    robot_image = MAP_ROBOT_VSLAM_IMAGE_MIJIA
                else:
                    robot_image = MAP_ROBOT_LIDAR_IMAGE_MIJIA
            else:
                if self._robot_type == RobotType.MOPPING:
                    robot_image = MAP_ROBOT_MOP_IMAGE_DREAME
                elif self._robot_type == RobotType.SWEEPING_AND_MOPPING:
                    robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_LIGHT
                elif self._robot_type == RobotType.VSLAM:
                    if self.icon_set == 3:
                        robot_image = MAP_ROBOT_VSLAM_IMAGE_DREAME_LIGHT
                    else:
                        robot_image = MAP_ROBOT_VSLAM_IMAGE_DREAME_DARK
                else:
                    if self.icon_set == 3:
                        robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_LIGHT
                    else:
                        robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_DARK

            self._robot_icon = Image.open(BytesIO(base64.b64decode(robot_image))).convert("RGBA")

            if (
                self._robot_type != RobotType.MOPPING
                and self._robot_type != RobotType.SWEEPING_AND_MOPPING
                and self.icon_set != 2
                and self.icon_set != 3
            ):
                enhancer = ImageEnhance.Brightness(self._robot_icon)
                if self.color_scheme.dark:
                    self._robot_icon = enhancer.enhance(1.5)
                else:
                    self._robot_icon = enhancer.enhance(0.9)

        icon = self._robot_icon.resize(
            (robot_icon_size, robot_icon_size),
            resample=Image.Resampling.NEAREST,
        ).rotate(robot_position.a, expand=1)
        point = robot_position.to_img(dimensions)

        if not self._low_memory:
            status_icon = None
            has_warning = False
            if robot_status >= 100:
                robot_status = robot_status - 100
            if robot_status >= 10:
                has_warning = True
                robot_status = robot_status - 10

            if robot_status == 1:
                if self._robot_cleaning_icon is None:
                    self._robot_cleaning_icon = (
                        Image.open(BytesIO(base64.b64decode(MAP_ROBOT_CLEANING_IMAGE)))
                        .convert("RGBA")
                        .resize(
                            ((int(icon_size * 1.25), int(icon_size * 1.25))),
                            resample=Image.Resampling.NEAREST,
                        )
                    )
                status_icon = self._robot_cleaning_icon

                if self.config.cleaning_direction:
                    if self._robot_cleaning_direction_icon is None:
                        self._robot_cleaning_direction_icon = (
                            Image.open(BytesIO(base64.b64decode(MAP_ROBOT_CLEANING_DIRECTION_IMAGE)))
                            .convert("RGBA")
                            .resize(
                                ((int(icon_size * 1.5), int(icon_size * 1.5))),
                            )
                        )

                    ico = self._robot_cleaning_direction_icon.rotate(robot_position.a, expand=1)

                    offset = int(icon_size * 0.3)
                    x = point.x + offset * math.cos(-robot_position.a * math.pi / 180)
                    y = point.y + offset * math.sin(-robot_position.a * math.pi / 180)
                    new_layer.paste(
                        ico,
                        (
                            int(x * scale - (ico.size[0] / 2)),
                            int(y * scale - (ico.size[1] / 2)),
                        ),
                    )
            elif robot_status == 2:
                if self._robot_charging_icon is None:
                    self._robot_charging_icon = (
                        Image.open(BytesIO(base64.b64decode(MAP_ROBOT_CHARGING_IMAGE)))
                        .convert("RGBA")
                        .resize(
                            ((int(icon_size * 1.3), int(icon_size * 1.3))),
                            resample=Image.Resampling.NEAREST,
                        )
                    )
                status_icon = self._robot_charging_icon
            elif has_warning:
                if self._robot_warning_icon is None:
                    self._robot_warning_icon = (
                        Image.open(BytesIO(base64.b64decode(MAP_ROBOT_WARNING_IMAGE)))
                        .convert("RGBA")
                        .resize(
                            ((int(icon_size * 1.3), int(icon_size * 1.3))),
                            resample=Image.Resampling.NEAREST,
                        )
                    )
                status_icon = self._robot_warning_icon

            if status_icon:
                mask = Image.new("L", status_icon.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, status_icon.size[0], status_icon.size[1]), fill=255)
                new_layer.paste(
                    status_icon,
                    (
                        int(point.x * scale - (status_icon.size[0] / 2)),
                        int(point.y * scale - (status_icon.size[1] / 2)),
                    ),
                    mask,
                )

        new_layer.paste(
            icon,
            (
                int(point.x * scale - (icon.size[0] / 2)),
                int(point.y * scale - (icon.size[1] / 2)),
            ),
            icon,
        )

        if not self._low_memory and robot_status == 3:
            if self._robot_sleeping_icon is None:
                sleeping_icon = (
                    Image.open(BytesIO(base64.b64decode(MAP_ROBOT_SLEEPING_IMAGE)))
                    .convert("RGBA")
                    .rotate(-map_rotation, expand=1)
                )
                enhancer = ImageEnhance.Brightness(sleeping_icon)
                if not self.color_scheme.dark:
                    sleeping_icon = enhancer.enhance(0.7)

                self._robot_sleeping_icon = [
                    sleeping_icon.resize(
                        ((int(icon_size * 0.3), int(icon_size * 0.3))),
                        resample=Image.Resampling.NEAREST,
                    ),
                    sleeping_icon.resize(
                        ((int(icon_size * 0.35), int(icon_size * 0.35))),
                        resample=Image.Resampling.NEAREST,
                    ),
                ]

            for k in [
                [int(icon_size * 0.34), int(icon_size * 0.18), 0],
                [int(icon_size * 0.43), int(icon_size * 0.43), 1],
            ]:
                status_icon = self._robot_sleeping_icon[k[2]]
                if map_rotation == 90:
                    x = point.x + k[1]
                    y = point.y + k[0]
                elif map_rotation == 180:
                    x = point.x - k[0]
                    y = point.y + k[1]
                elif map_rotation == 270:
                    x = point.x - k[1]
                    y = point.y - k[0]
                else:
                    x = point.x + k[0]
                    y = point.y - k[1]

                new_layer.paste(
                    status_icon,
                    (
                        int(x * scale - (status_icon.size[0] / 2)),
                        int(y * scale - (status_icon.size[1] / 2)),
                    ),
                    status_icon,
                )
        return new_layer

    def render_segment(
        self,
        segment,
        cleanset,
        sequence,
        layer_size,
        dimensions,
        size,
        rotation,
        scale,
        active,
        blocked,
    ):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        if segment.x is not None and segment.y is not None:
            active = active and not blocked
            text = None
            if segment.type not in self._segment_icons:
                icon_set = SEGMENT_ICONS_DREAME
                if self.icon_set == 1:
                    icon_set = SEGMENT_ICONS_DREAME_OLD
                elif self.icon_set == 2:
                    icon_set = SEGMENT_ICONS_MIJIA
                elif self.icon_set == 3:
                    icon_set = SEGMENT_ICONS_MATERIAL

                if segment.type in icon_set:
                    self._segment_icons[segment.type] = Image.open(
                        BytesIO(base64.b64decode(icon_set[segment.type]))
                    ).convert("RGBA")
                    if self.color_scheme.invert and not (self.config.name_background and self.icon_set != 2):
                        enhancer = ImageEnhance.Brightness(self._segment_icons[segment.type])
                        self._segment_icons[segment.type] = enhancer.enhance(0.1)

            icon = self._segment_icons.get(segment.type) if self.config.icon else None
            if segment.type == 0 or self.config.name or icon is None:
                text = (
                    segment.name
                    if (self._robot_type != RobotType.VSLAM or icon is not None)
                    or (segment.custom_name is not None and segment.type == 0)
                    or self.icon_set == 2
                    else segment.letter
                )
            elif segment.index > 0:
                text = str(segment.index)

            text_font = None
            order_font = None
            render_font = text and (self.config.name or segment.type == 0 or segment.index > 0)
            if self._font_file is None and (render_font or (segment.order and self.config.order and sequence)):
                self._font_file = zlib.decompress(base64.b64decode(MAP_FONT), zlib.MAX_WBITS | 32)

            if render_font and self._font_file:
                text_font = ImageFont.truetype(
                    BytesIO(self._font_file),
                    int((size * 1.9)) if segment.index or icon is None else int((size * 1.7)),
                )

            if active and segment.order and self.config.order and sequence:
                order_font = ImageFont.truetype(BytesIO(self._font_file), int((size * 2.1)))

            p = Point(segment.x, segment.y).to_img(dimensions)
            x = p.x
            y = p.y

            if blocked:
                offset = size * 1.5
                x_offset = 0
                y_offset = -offset
                if rotation == 90:
                    y_offset = 0
                    x_offset = offset
                elif rotation == 180:
                    y_offset = offset
                elif rotation == 270:
                    y_offset = 0
                    x_offset = -offset

                x = x + x_offset
                y = y + y_offset

            if self.config.name or self.config.icon:
                if segment.type or text_font or not self.config.name:
                    icon_size = size * (1.75 if self.icon_set == 1 else 1.3)
                    x0 = x - size
                    y0 = y - size
                    x1 = x + size
                    y1 = y + size

                    if text_font:
                        left, top, tw, th = draw.textbbox((0, 0), text, text_font)
                        ws = tw / 4

                        if segment.index or icon is None:
                            icon_size = size * 1.35
                            padding = icon_size / 2
                            text_offset = (icon_size / 2) + 2
                            icon_offset = 2
                            th = int(round(size * 2.3))
                        else:
                            icon_size = size * 1.15
                            padding = icon_size * 0.35
                            icon_offset = padding - 2
                            text_offset = icon_size / 2
                            th = int(round(size * 1.9))

                        if icon is None:
                            text_offset = 0
                            padding = -(icon_size / 4)

                        name_background = self.config.icon or (self.config.name_background and self.config.name)

                        stroke_width = dimensions.scale
                        if blocked:
                            stroke_color = self.color_scheme.blocked_segment
                            text_color = (
                                stroke_color[0],
                                stroke_color[1],
                                stroke_color[2],
                                255,
                            )
                        elif not name_background:
                            if self.color_scheme.dark:
                                text_color = (240, 240, 240, 255)
                                stroke_color = (0, 0, 0, 200)
                            else:
                                text_color = (15, 15, 15, 255)
                                stroke_color = (255, 255, 255, 200)
                        elif self.config.icon or self.config.name:
                            stroke_width = 1
                            if self.config.name_background and self.icon_set != 2 and self.color_scheme.invert:
                                text_color = (240, 240, 240, 255)
                                stroke_color = (240, 240, 240, 200)
                            else:
                                text_color = self.color_scheme.text
                                stroke_color = self.color_scheme.text_stroke

                        th = th + int(stroke_width * 2)

                        if rotation == 90 or rotation == 270:
                            y0 = y0 - ws - padding
                            y1 = y1 + ws + padding

                            if rotation == 90:
                                ty = (y - ws + text_offset) * scale
                                tx = (x - (th / 4)) * scale
                                y = y - ws - icon_offset
                            else:
                                ty = (y - ws - text_offset) * scale
                                tx = (x - (th / 4)) * scale
                                y = y + ws + icon_offset
                        else:
                            x0 = x0 - ws - padding
                            x1 = x1 + ws + padding

                            if rotation == 0:
                                tx = (x - ws + text_offset) * scale
                                ty = (y - (th / 4)) * scale
                                x = x - ws - icon_offset
                            else:
                                tx = (x - ws - text_offset) * scale
                                ty = (y - (th / 4)) * scale
                                x = x + ws + icon_offset

                        if (
                            name_background
                            # and not self.config.name_background
                            and active
                            and not blocked
                        ):
                            draw.rounded_rectangle(
                                [
                                    int(x0 * scale),
                                    int(y0 * scale),
                                    int(x1 * scale),
                                    int(y1 * scale),
                                ],
                                fill=(
                                    self.color_scheme.segment[segment.color_index][1]
                                    if name_background and self.config.name_background and self.icon_set != 2
                                    else self.color_scheme.icon_background
                                ),
                                radius=((size * scale)),
                            )

                        icon_text = Image.new("RGBA", (tw, th), (255, 255, 255, 0))
                        draw_text = ImageDraw.Draw(icon_text, "RGBA")

                        draw_text.text(
                            (0, 0),
                            text,
                            font=text_font,
                            fill=text_color,
                            stroke_width=stroke_width,
                            stroke_fill=stroke_color,
                        )
                        icon_text = icon_text.rotate(-rotation, expand=1)
                        new_layer.paste(icon_text, (int(tx), int(ty)), icon_text)
                        if self.icon_set == 1:
                            icon_size *= 1.3
                    elif active:  # and not self.config.name_background
                        draw.ellipse(
                            [x0 * scale, y0 * scale, x1 * scale, y1 * scale],
                            fill=(
                                self.color_scheme.segment[segment.color_index][1]
                                if self.config.name_background and self.icon_set != 2
                                else self.color_scheme.icon_background
                            ),
                        )

                    if icon is not None:
                        s = icon_size * scale
                        if blocked:
                            icon = DreameVacuumMapRenderer._set_icon_color(
                                icon,
                                s,
                                text_color,
                            )
                        else:
                            icon = icon.resize((int(s), int(s)))
                        icon = icon.rotate(-rotation, expand=1)
                        new_layer.paste(
                            icon,
                            (
                                int(x * scale - (icon.size[0] / 2)),
                                int(y * scale - (icon.size[1] / 2)),
                            ),
                            icon,
                        )

            custom = (
                active
                and not blocked
                and cleanset
                and (
                    self.config.suction_level
                    or self.config.water_volume
                    or self.config.cleaning_times
                    or self.config.cleaning_mode
                )
            )
            if order_font or custom:
                offset = size * 2.7
                x_offset = 0
                y_offset = -offset

                if rotation == 90:
                    y_offset = 0
                    x_offset = offset
                elif rotation == 180:
                    y_offset = offset
                elif rotation == 270:
                    y_offset = 0
                    x_offset = -offset

                x = p.x + x_offset
                y = p.y + y_offset
                cleaning_mode = (
                    None
                    if segment.cleaning_mode is None or segment.cleaning_mode < 0 or segment.cleaning_mode > 3
                    else segment.cleaning_mode
                )
                if custom:
                    s = scale * 2
                    arrow = (s + 2) * scale
                    if order_font:
                        icon_count = 5
                    else:
                        icon_count = 4

                    if not self.config.suction_level or segment.suction_level is None:
                        icon_count = icon_count - 1
                    if not self.config.water_volume or segment.water_volume is None:
                        icon_count = icon_count - 1
                    if not self.config.cleaning_times or segment.cleaning_times is None:
                        icon_count = icon_count - 1
                    if not self.config.cleaning_mode or cleaning_mode is None:
                        icon_count = icon_count - 1
                    if cleaning_mode == 0 or cleaning_mode == 1:
                        icon_count = icon_count - 1
                    if (
                        self.config.mopping_mode
                        and segment.custom_mopping_route is None
                        and segment.cleaning_route is not None
                        and cleaning_mode == 1
                    ):
                        icon_count = icon_count + 1
                else:
                    icon_count = 1

                if not icon and not self.config.icon:
                    arrow = 0

                radius = size
                arrow = int(round(radius * 0.6))
                margin = int(round(size * 0.3)) if icon_count > 1 else 0
                if custom:
                    radius = size - 2

                icon_w = ((radius * icon_count * 2) * scale) + (arrow * 2) + (margin * 2)
                icon_h = ((radius * 2) * scale) + (arrow * 2)
                icon = Image.new("RGBA", (icon_w, icon_h), (255, 255, 255, 0))
                icon_draw = ImageDraw.Draw(icon, "RGBA")

                if arrow and (segment.type != 0 or text_font):
                    xx = icon_w / 2
                    yy = icon_h - 2
                    icon_draw.polygon(
                        [
                            (xx, yy),
                            (xx - arrow, yy - arrow),
                            (xx + arrow, yy - arrow),
                        ],
                        fill=self.color_scheme.settings_background,
                    )

                icon_draw.rounded_rectangle(
                    [arrow, arrow, icon_w - arrow, icon_h - arrow],
                    fill=self.color_scheme.settings_background,
                    radius=((icon_h - (arrow * 2)) / 2),
                )

                padding = int(round((size * 0.3) + (size * 0.6)))
                r = icon_h - (padding * 2)
                ellipse_x1 = padding + margin
                ellipse_x2 = ellipse_x1 + r
                if order_font:
                    icon_draw.ellipse(
                        [ellipse_x1, padding, ellipse_x2, icon_h - padding],
                        fill=self.color_scheme.segment[segment.color_index][1],
                    )
                    text = str(segment.order)
                    left, top, tw, th = icon_draw.textbbox((0, 0), text, order_font)
                    icon_draw.text(
                        (
                            (icon_h - tw) / 2 + margin,
                            (icon_h - th - int(round(radius * 0.4))) / 2,
                        ),
                        text,
                        font=order_font,
                        fill=self.color_scheme.order,
                        stroke_width=1,
                        stroke_fill=self.color_scheme.text_stroke,
                    )

                    ellipse_x1 = ellipse_x2 + (margin * 2)
                    ellipse_x2 = ellipse_x1 + r

                if custom:
                    icon_size = size * 1.45

                    if self.config.cleaning_mode and cleaning_mode is not None:
                        if self.icon_set == 2:
                            s = icon_size * 1.2 * scale
                        else:
                            s = icon_size * 0.85 * scale

                        ico = DreameVacuumMapRenderer._set_icon_color(
                            self._cleaning_mode_icon[segment.cleaning_mode],
                            s,
                            self.color_scheme.segment[segment.color_index][1],
                        )

                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2, (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(2 + ellipse_x1 + ((ellipse_x2 - ellipse_x1) / 2) - ico.size[0] / 2),
                                int(((icon_h / 2) - ico.size[1] / 2)),
                            ),
                            ico,
                        )

                        ellipse_x1 = ellipse_x2 + (margin * 2)
                        ellipse_x2 = ellipse_x1 + r

                    if self.config.suction_level and segment.suction_level is not None and cleaning_mode != 1:
                        if self.icon_set == 2:
                            s = icon_size * 1.2 * scale
                        else:
                            s = icon_size * 0.85 * scale

                        ico = DreameVacuumMapRenderer._set_icon_color(
                            self._suction_level_icon[segment.suction_level],
                            s,
                            self.color_scheme.segment[segment.color_index][1],
                        )
                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2, (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(2 + ellipse_x1 + ((ellipse_x2 - ellipse_x1) / 2) - ico.size[0] / 2),
                                int(((icon_h / 2) - ico.size[1] / 2)),
                            ),
                            ico,
                        )

                        ellipse_x1 = ellipse_x2 + (margin * 2)
                        ellipse_x2 = ellipse_x1 + r

                    if self.config.water_volume and segment.water_volume is not None and cleaning_mode != 0:
                        water = segment.water_volume - 1
                        if self.config.mopping_mode and segment.custom_mopping_route is not None:
                            s = icon_size * 1.05 * scale
                            ico = self._custom_mopping_route_icon[(water * 3) + (segment.cleaning_route - 1)]
                        elif self.config.mopping_mode and segment.cleaning_route is not None:
                            if self.icon_set == 3:
                                s = icon_size * 0.95 * scale
                            else:
                                s = icon_size * scale
                            ico = self._mop_pad_humidity_icon[water]
                        else:
                            if self.icon_set == 3:
                                s = icon_size * 0.95 * scale
                            elif self.icon_set == 2:
                                s = icon_size * 1.2 * scale
                            ico = self._water_volume_icon[water]

                        ico = DreameVacuumMapRenderer._set_icon_color(
                            ico,
                            s,
                            self.color_scheme.segment[segment.color_index][1],
                        )

                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2, (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(2 + ellipse_x1 + ((ellipse_x2 - ellipse_x1) / 2) - ico.size[0] / 2),
                                int(((icon_h / 2) - ico.size[1] / 2)),
                            ),
                            ico,
                        )

                        ellipse_x1 = ellipse_x2 + (margin * 2)
                        ellipse_x2 = ellipse_x1 + r

                    if (
                        self.config.mopping_mode
                        and segment.custom_mopping_route is None
                        and segment.cleaning_route is not None
                        and cleaning_mode == 1
                    ):
                        if self.icon_set == 3:
                            s = icon_size * 0.85 * scale
                        else:
                            s = icon_size * 0.7 * scale
                        ico = DreameVacuumMapRenderer._set_icon_color(
                            self._cleaning_route_icon[segment.cleaning_route - 1],
                            s,
                            self.color_scheme.segment[segment.color_index][1],
                        )
                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2, (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(2 + ellipse_x1 + ((ellipse_x2 - ellipse_x1) / 2) - ico.size[0] / 2),
                                int(((icon_h / 2) - ico.size[1] / 2)),
                            ),
                            ico,
                        )

                        ellipse_x1 = ellipse_x2 + (margin * 2)
                        ellipse_x2 = ellipse_x1 + r

                    if self.config.cleaning_times and segment.cleaning_times is not None:
                        if self.icon_set == 3 or self.icon_set == 2:
                            s = icon_size * 0.95 * scale
                        else:
                            s = icon_size * 0.85 * scale

                        ico = DreameVacuumMapRenderer._set_icon_color(
                            self._cleaning_times_icon[segment.cleaning_times - 1],
                            s,
                            self.color_scheme.segment[segment.color_index][1],
                        )

                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2, (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(2 + ellipse_x1 + ((ellipse_x2 - ellipse_x1) / 2) - ico.size[0] / 2),
                                int(((icon_h / 2) - ico.size[1] / 2)),
                            ),
                            ico,
                        )

                icon = icon.rotate(-rotation, expand=1)
                new_layer.paste(
                    icon,
                    (
                        int((x * scale) - ((icon.size[0]) / 2)),
                        int((y * scale) - ((icon.size[1]) / 2)),
                    ),
                    icon,
                )
        return new_layer

    def render_obstacle(self, obstacle, layer_size, dimensions, size, rotation, scale):
        if obstacle.ignore_status == 1:
            if (
                obstacle.type.value not in self._obstacle_hidden_icons
                and obstacle.type.value in OBSTACLE_TYPE_TO_HIDDEN_ICON
            ):
                self._obstacle_hidden_icons[obstacle.type.value] = Image.open(
                    BytesIO(base64.b64decode(OBSTACLE_TYPE_TO_HIDDEN_ICON[obstacle.type.value]))
                ).convert("RGBA")
            icon = self._obstacle_hidden_icons.get(obstacle.type.value)
        else:
            if obstacle.type.value not in self._obstacle_icons and obstacle.type.value in OBSTACLE_TYPE_TO_ICON:
                self._obstacle_icons[obstacle.type.value] = Image.open(
                    BytesIO(base64.b64decode(OBSTACLE_TYPE_TO_ICON[obstacle.type.value]))
                ).convert("RGBA")
            icon = self._obstacle_icons.get(obstacle.type.value)

        if icon:
            new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
            icon_size = size * scale * (1 if obstacle.ignore_status == 1 else 0.85)
            draw = ImageDraw.Draw(new_layer, "RGBA")

            if obstacle.ignore_status != 2 and self._obstacle_background is None:
                self._obstacle_background = Image.open(BytesIO(base64.b64decode(MAP_ICON_OBSTACLE_BG_DREAME))).convert(
                    "RGBA"
                )
                s = int(size * scale * 2)
                self._obstacle_background.thumbnail((s, s), Image.Resampling.LANCZOS)
                self._obstacle_background = self._obstacle_background.rotate(-rotation, expand=1)

            if obstacle.ignore_status == 2 and self._obstacle_hidden_background is None:
                self._obstacle_hidden_background = Image.open(
                    BytesIO(base64.b64decode(MAP_ICON_OBSTACLE_HIDDEN_BG_DREAME))
                ).convert("RGBA")
                s = int((size * 0.75) * scale * 2)
                self._obstacle_hidden_background.thumbnail((s, s), Image.Resampling.LANCZOS)
                self._obstacle_hidden_background = self._obstacle_hidden_background.rotate(-rotation, expand=1)

            background_image = (
                self._obstacle_hidden_background if obstacle.ignore_status == 2 else self._obstacle_background
            )
            bg_size = int((min(background_image.size[1], background_image.size[0]) / scale / 4) * 1.25)
            offset = int(-(size * (0.15 if obstacle.ignore_status == 2 else 0.2)) * scale)

            p = obstacle.to_img(dimensions)
            x = p.x
            y = p.y
            # if self.icon_set != 2:
            pos_offset = (
                max(background_image.size[1], background_image.size[0])
                * (1.35 if obstacle.ignore_status == 2 else 0.95)
                / scale
                / 2
            )
            # else:
            #    pos_offset = 0

            if rotation == 90:
                y_offset = 0
                x_offset = offset
                x = x + pos_offset
            elif rotation == 180:
                y_offset = offset
                x_offset = 0
                y = y + pos_offset
            elif rotation == 270:
                y_offset = 0
                x_offset = -offset
                x = x - pos_offset
            else:
                x_offset = 0
                y_offset = -offset
                y = y - pos_offset

            new_layer.paste(
                background_image,
                (
                    int(round(x * scale - (background_image.size[0] / 2) + x_offset)),
                    int(round(y * scale - (background_image.size[1] / 2) + y_offset)),
                ),
            )

            if obstacle.ignore_status == 2:
                icon = DreameVacuumMapRenderer._set_icon_color(
                    icon,
                    icon_size,
                    (34, 109, 242, 240),
                ).rotate(-rotation, expand=1)
            else:
                draw.ellipse(
                    [
                        (x - bg_size) * scale,
                        (y - bg_size) * scale,
                        (x + bg_size) * scale,
                        (y + bg_size) * scale,
                    ],
                    fill=(
                        (230, 143, 9, 255)
                        if obstacle.type == ObstacleType.BLOCKED_ROOM
                        else (
                            (212, 212, 212, 255)
                            if obstacle.ignore_status == 1
                            else (
                                (128, 128, 128, 255)
                                if self.icon_set != 2
                                and (
                                    obstacle.type == ObstacleType.LIQUID_STAIN
                                    or obstacle.type == ObstacleType.DRIED_STAIN
                                    or obstacle.type == ObstacleType.UNCLEANABLE_STAIN
                                    or obstacle.type == ObstacleType.DETECTED_STAIN
                                )
                                else (
                                    (255, 140, 188, 255)
                                    if self.icon_set != 2
                                    and (
                                        obstacle.type == ObstacleType.PET
                                        or obstacle.type == ObstacleType.FOOD_BOWL
                                        or obstacle.type == ObstacleType.PET_BED
                                    )
                                    else (
                                        (97, 173, 31, 255)
                                        if self.icon_set != 2
                                        and (
                                            obstacle.type == ObstacleType.CLEANED_LARGE_PARTICLES
                                            or obstacle.type == ObstacleType.CLEANED_DRIED_STAIN
                                            or obstacle.type == ObstacleType.SKIPPED_UNCLEANABLE_STAIN
                                            or obstacle.type == ObstacleType.CLEANED_STAIN
                                        )
                                        else self.color_scheme.obstacle_bg
                                    )
                                )
                            )
                        )
                    ),
                )
                icon = icon.resize((int(icon_size), int(icon_size))).rotate(-rotation, expand=1)

            new_layer.paste(
                icon,
                (
                    int(round(x * scale - (icon_size / 2))),
                    int(round(y * scale - (icon_size / 2))),
                ),
                icon,
            )

            return new_layer

    def render_cruise_point(self, index, cruise_point, layer_size, dimensions, size, rotation, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        if cruise_point.type == 1 and self._cruise_path_point_background is None:
            self._cruise_path_point_background = Image.open(
                BytesIO(base64.b64decode(MAP_ICON_CRUISE_POINT_BG_DREAME))
            ).convert("RGBA")
            s = int(size * scale * 3)
            self._cruise_path_point_background.thumbnail((s, s), Image.Resampling.LANCZOS)
            self._cruise_path_point_background = self._cruise_path_point_background.rotate(-rotation, expand=1)

        if cruise_point.type != 1 and self._cruise_point_background is None:
            self._cruise_point_background = Image.open(
                BytesIO(base64.b64decode(MAP_ICON_CRUISE_POINT_DREAME))
            ).convert("RGBA")
            s = int(round(size * scale * 2))
            self._cruise_point_background.thumbnail((s, s), Image.Resampling.LANCZOS)
            self._cruise_point_background = self._cruise_point_background.rotate(-rotation, expand=1)

        background_image = (
            self._cruise_point_background if cruise_point.type != 1 else self._cruise_path_point_background
        )
        bg_size = int(min(background_image.size[1], background_image.size[0]) / scale / 4)
        offset = int(-bg_size * 1.25)

        p = cruise_point.to_img(dimensions)
        x = p.x
        y = p.y
        pos_offset = (
            max(background_image.size[1], background_image.size[0])
            * (1.75 if cruise_point.type != 1 else 1.20)
            / scale
            / 3
        )

        if rotation == 90:
            y_offset = 0
            x_offset = offset
            x = x + pos_offset
        elif rotation == 180:
            y_offset = offset
            x_offset = 0
            y = y + pos_offset
        elif rotation == 270:
            y_offset = 0
            x_offset = -offset
            x = x - pos_offset
        else:
            x_offset = 0
            y_offset = -offset
            y = y - pos_offset

        new_layer.paste(
            background_image,
            (
                int(round(x * scale - (background_image.size[0] / 2) + x_offset)),
                int(round(y * scale - (background_image.size[1] / 2) + y_offset)),
            ),
        )

        if cruise_point.type == 1:
            draw.ellipse(
                [
                    (x - bg_size) * scale,
                    (y - bg_size) * scale,
                    (x + bg_size) * scale,
                    (y + bg_size) * scale,
                ],
                fill=(212, 212, 212, 255) if cruise_point.completed else (34, 109, 242, 255),
            )

        if cruise_point.type == 1:
            text_box = Image.new("RGBA", (bg_size * 2 * scale, bg_size * 2 * scale), (255, 255, 255, 0))
            text_box_draw = ImageDraw.Draw(text_box, "RGBA")

            if self._font_file is None:
                self._font_file = zlib.decompress(base64.b64decode(MAP_FONT), zlib.MAX_WBITS | 32)

            font = ImageFont.truetype(BytesIO(self._font_file), int((bg_size * 1.5 * scale)))

            text = str(index)
            left, top, tw, th = text_box_draw.textbbox((0, 0), text, font)
            text_box_draw.text(
                (
                    (text_box.size[1] - tw) / 2,
                    (text_box.size[1] - th - int(round(size * 0.4))) / 2,
                ),
                text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=1,
                stroke_fill=(255, 255, 255, 100),
            )
            text_box = text_box.rotate(-rotation, expand=1)
            new_layer.paste(
                text_box,
                (int(round((x - bg_size) * scale)), int(round((y - bg_size) * scale))),
                text_box,
            )

        return new_layer

    def render_furniture(
        self, furniture, furniture_version, hidden_segments, layer_size, dimensions, size, rotation, scale
    ):
        draw_image = furniture.width and furniture.height
        furniture_type = furniture.type.value
        if hidden_segments and furniture.segment_id and furniture.segment_id in hidden_segments:
            return None

        if draw_image:
            if furniture_version == 6:
                furniture_images = FURNITURE_V3_TYPE_TO_IMAGE
            elif furniture_version == 5:
                furniture_images = FURNITURE_V2_TYPE_MIJIA_TO_IMAGE
            elif furniture_version < 3:
                furniture_images = FURNITURE_TYPE_TO_IMAGE
            else:
                furniture_images = FURNITURE_V2_TYPE_TO_IMAGE

            if furniture_type not in self._furniture_images and furniture_type in furniture_images:
                image = Image.open(BytesIO(base64.b64decode(furniture_images[furniture_type]))).convert("RGBA")
                if furniture_version == 6:
                    self._furniture_images[furniture_type] = image
                else:
                    img = np.array(image)
                    if self.icon_set != 2:
                        img[..., 3] = 235 * (img[..., 3] > 0)
                    self._furniture_images[furniture_type] = Image.fromarray(img)
            icon = self._furniture_images.get(furniture_type)
        else:
            furniture_icons = FURNITURE_V2_TYPE_TO_ICON if furniture_version >= 3 else FURNITURE_TYPE_TO_ICON
            if furniture_type not in self._furniture_icons and furniture_type in furniture_icons:
                self._furniture_icons[furniture_type] = Image.open(
                    BytesIO(base64.b64decode(furniture_icons[furniture_type]))
                ).convert("RGBA")
            icon = self._furniture_icons.get(furniture_type)
        if icon:
            new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
            if draw_image:
                w = (furniture.width / dimensions.grid_size) * dimensions.scale
                h = (furniture.height / dimensions.grid_size) * dimensions.scale
                p = Point(
                    furniture.x,
                    furniture.y,
                ).to_img(dimensions)
                x = p.x
                y = p.y

                img = icon.rotate(furniture.angle, expand=1)
                if furniture_version >= 3:
                    img = img.resize(
                        (int(w * scale), int(h * scale)),
                        resample=Image.Resampling.LANCZOS,
                    )
                else:
                    img.thumbnail((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
                img = img.rotate(-(furniture.angle * 2), expand=1)

                new_layer.paste(
                    img,
                    (
                        int((x * scale) - ((img.size[0]) / 2)),
                        int((y * scale) - ((img.size[1]) / 2)),
                    ),
                    img,
                )
            else:
                icon_size = size * scale * 1.15
                if self._furniture_background is None:
                    self._furniture_background = Image.open(
                        BytesIO(base64.b64decode(MAP_ICON_OBSTACLE_BG_DREAME))
                    ).convert("RGBA")
                    s = int(size * scale * 2)
                    self._furniture_background.thumbnail((s, s), Image.Resampling.LANCZOS)
                    self._furniture_background = self._furniture_background.rotate(-rotation, expand=1)

                offset = int(-(size * 0.2) * scale)

                p = furniture.to_img(dimensions)
                x = p.x
                y = p.y
                pos_offset = (
                    (self._furniture_background.size[1] * (1.15 if rotation == 90 or rotation == 270 else 0.9))
                    / scale
                    / 2
                )

                if rotation == 90:
                    y_offset = 0
                    x_offset = offset
                    x = x + pos_offset
                elif rotation == 180:
                    y_offset = offset
                    x_offset = 0
                    y = y + pos_offset
                elif rotation == 270:
                    y_offset = 0
                    x_offset = -offset
                    x = x - pos_offset
                else:
                    x_offset = 0
                    y_offset = -offset
                    y = y - pos_offset

                new_layer.paste(
                    self._furniture_background,
                    (
                        int(round(x * scale - (self._furniture_background.size[0] / 2) + x_offset)),
                        int(round(y * scale - (self._furniture_background.size[1] / 2) + y_offset)),
                    ),
                )

                icon = icon.resize((int(icon_size), int(icon_size))).rotate(-rotation, expand=1)

                new_layer.paste(
                    icon,
                    (
                        int(round(x * scale - (icon_size / 2))),
                        int(round(y * scale - (icon_size / 2))),
                    ),
                    icon,
                )

            return new_layer

    def render_router(
        self,
        router_position,
        layer_size,
        dimensions,
        size,
        rotation,
        scale,
    ):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        icon_size = int(size * scale)
        if self._wifi_icon is None:
            self._wifi_icon = (
                Image.open(BytesIO(base64.b64decode(MAP_WIFI_IMAGE_DREAME)))
                .convert("RGBA")
                .resize((icon_size, icon_size), resample=Image.Resampling.NEAREST)
            )

        point = router_position.to_img(dimensions)
        bg_size = (size * 1.2) / 2
        draw.ellipse(
            [
                int((point.x - bg_size) * scale),
                int((point.y - bg_size) * scale),
                int((point.x + bg_size) * scale),
                int((point.y + bg_size) * scale),
            ],
            fill=(34, 98, 211, 255) if self.color_scheme.dark else (34, 109, 242, 255),
        )
        wifi_icon = self._wifi_icon.rotate(-rotation, expand=1)
        new_layer.paste(
            wifi_icon,
            (
                int((point.x * scale) - (wifi_icon.size[0] / 2)),
                int((point.y * scale) - (wifi_icon.size[1] / 2)),
            ),
            wifi_icon,
        )

        return new_layer

    def render_floor_material(self, image, floor_material, hidden_segments, pixel_type, color, dimensions, scale):
        tile_w = 12
        floor_w = 4
        floor_h = 16

        height = dimensions.height * scale
        tiles = {}
        for k, v in floor_material.items():
            if v > 0 and v < 4:
                if v not in tiles:
                    tiles[v] = [k]
                else:
                    tiles[v].append(k)

        if tiles:
            color_map = {}
            for floor_type, tile in tiles.items():
                if tile:
                    if floor_type == 1:
                        w = math.floor(2 * dimensions.width / floor_h)
                        h = math.floor(dimensions.height / floor_w)
                        y_start = 1
                        x_start = 0
                        x_multiplier = floor_h / 2
                        y_multiplier = floor_w
                    elif floor_type == 2:
                        w = math.floor(dimensions.width / floor_w)
                        h = math.floor(2 * dimensions.height / floor_h)
                        y_start = 0
                        x_start = 1
                        x_multiplier = floor_w
                        y_multiplier = floor_h / 2
                    else:
                        w = math.floor(dimensions.width / tile_w)
                        h = math.floor(dimensions.height / tile_w)
                        y_start = 0
                        x_start = 0
                        x_multiplier = tile_w
                        y_multiplier = tile_w

                    for x in range(1, w + 1):
                        for y in range(y_start, dimensions.height):
                            xx = int(x * x_multiplier)
                            if xx < dimensions.width and (
                                floor_type != 1
                                or (
                                    (math.floor((y - 1) / floor_w) % 2 == 0 and x % 2 == 0)
                                    or (math.floor((y - 1) / floor_w) % 2 == 1 and x % 2 == 1)
                                )
                            ):
                                val = int(pixel_type[xx, y])
                                if val > 100 and val < 200:
                                    val = val - 100
                                    if not hidden_segments or val not in hidden_segments:
                                        continue

                                if val > 0 and val < 63 and val in tile:
                                    x_index = (xx * scale) + 1
                                    y_index = (height - 1) - (y * scale) - 1

                                    if val not in color_map:
                                        cc = DreameVacuumMapRenderer._alpha_composite(color, image[y_index, x_index])
                                        color_map[val] = cc
                                    else:
                                        cc = color_map[val]
                                    image[y_index, x_index] = cc
                                    y_index = y_index + 1
                                    image[y_index, x_index] = cc

                    for x in range(x_start, dimensions.width):
                        for y in range(1, h + 1):
                            yy = int(y * y_multiplier)
                            if yy < dimensions.height and (
                                floor_type != 2
                                or (
                                    (math.floor((x - 1) / floor_w) % 2 == 0 and y % 2 == 0)
                                    or (math.floor((x - 1) / floor_w) % 2 == 1 and y % 2 == 1)
                                )
                            ):
                                val = int(pixel_type[x, yy])
                                if val > 100 and val < 200:
                                    val = val - 100
                                    if not hidden_segments or val not in hidden_segments:
                                        continue

                                if val > 0 and val < 63 and val in tile:
                                    x_index = x * scale
                                    y_index = (height - 1) - ((yy * scale) + 1)
                                    if val not in color_map:
                                        cc = DreameVacuumMapRenderer._alpha_composite(color, image[y_index, x_index])
                                        color_map[val] = cc
                                    else:
                                        cc = color_map[val]
                                    image[y_index, x_index] = cc
                                    x_index = x_index + 1
                                    image[y_index, x_index] = cc
            return image

    def render_carpets(
        self,
        image,
        pixel_type,
        carpets,
        deleted_carpets,
        detected_carpets,
        carpet_pixels,
        segments,
        hidden_segments,
        color,
        detected_color,
        dimensions,
        scale,
    ):
        carpet_data = {}
        left = dimensions.left
        top = dimensions.top
        if left % dimensions.grid_size != 0 or top % dimensions.grid_size != 0:
            left = left + (dimensions.offset)
            top = top + (dimensions.offset)

        if detected_carpets:
            optimimized_carpet_pixels = None
            for carpet in detected_carpets:
                if not carpet.hidden:
                    x0, y0, x1, y1 = DreameVacuumMapRenderer._get_carpet_coords(carpet, dimensions)
                    for x in range(max(0, x0), min(x1, dimensions.width - 1)):
                        for y in range(max(y0, 0), min(y1, dimensions.height - 1)):
                            val = int(pixel_type[x, y])
                            if val > 100 and val < 200:
                                val = val - 100
                                if not hidden_segments or val not in hidden_segments:
                                    continue
                            if not DreameVacuumMapRenderer._check_carpet(x, y, carpet, dimensions, val):
                                continue

                            if carpet.polygon and len(carpet.polygon) > 100 and carpet_pixels:
                                if optimimized_carpet_pixels is None:
                                    optimimized_carpet_pixels = DreameVacuumMapRenderer._optimize_carpet_pixels(
                                        carpet_pixels, dimensions, pixel_type
                                    )
                                if (x, y) not in optimimized_carpet_pixels:
                                    continue
                            carpet_data[(x, y)] = 1
        elif carpet_pixels:
            carpet_data = DreameVacuumMapRenderer._optimize_carpet_pixels(carpet_pixels, dimensions, pixel_type)

        if deleted_carpets:
            for carpet in deleted_carpets:
                x0, y0, x1, y1 = DreameVacuumMapRenderer._get_carpet_coords(carpet, dimensions)
                for x in range(x0, x1):
                    for y in range(y0, y1):
                        if (x, y) in carpet_data:
                            del carpet_data[(x, y)]

        if segments:
            for k in segments.keys():
                segment = segments[k]
                if segment.floor_material and segment.floor_material > 4 and segment.floor_material < 8:
                    x0 = int((segment.x0 - dimensions.left) / dimensions.grid_size) - 1
                    y0 = int((segment.y0 - dimensions.top) / dimensions.grid_size) - 1
                    x1 = int((segment.x1 - dimensions.left) / dimensions.grid_size) + 1
                    y1 = int((segment.y1 - dimensions.top) / dimensions.grid_size) + 1
                    for x in range(x0 - 1, x1 + 1):
                        for y in range(y0 - 1, y1 + 1):
                            if x < 0 or x >= dimensions.width or y < 0 or y >= dimensions.height:
                                continue
                            val = int(pixel_type[x, y])
                            if val > 100 and val < 200:
                                val = val - 100
                                if not hidden_segments or val not in hidden_segments:
                                    continue
                            if val == int(k):
                                carpet_data[(x, y)] = 1

        if carpets:
            for carpet in carpets:
                if not carpet.hidden:
                    x0, y0, x1, y1 = DreameVacuumMapRenderer._get_carpet_coords(carpet, dimensions)
                    for x in range(x0, x1):
                        for y in range(y0, y1):
                            if DreameVacuumMapRenderer._check_carpet(x, y, carpet, dimensions):
                                carpet_data[(x, y)] = 2

        color_map = {}
        for coord, px_type in carpet_data.items():
            if px_type != 0:
                x_index = coord[0] * scale
                y_index = (dimensions.height - coord[1] - 1) * scale
                render_color = detected_color if px_type == 1 else color
                for i in range(2):
                    if (
                        y_index >= 0
                        and y_index < dimensions.height * scale
                        and x_index >= 0
                        and x_index < dimensions.width * scale
                    ):
                        val = f"{image[y_index, x_index]}{px_type}"
                        if val not in color_map:
                            cc = DreameVacuumMapRenderer._alpha_composite(render_color, image[y_index, x_index])
                            color_map[val] = cc
                        else:
                            cc = color_map[val]
                        image[y_index, x_index] = cc
                        x_index = x_index + 1
                        y_index = y_index + 1

        return image

    def render_blocked_segments(
        self,
        blocked_segments,
        segments,
        layer_size,
        segment_mask,
        dimensions,
        rotation,
        cleaning_map,
    ):
        mask_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        mask_layer.paste(segment_mask, (0, 0))

        if self._map_problem_icon is None:
            self._map_problem_icon = Image.open(BytesIO(base64.b64decode(MAP_ICON_PROBLEM))).convert("RGBA")

        if rotation == 0 or rotation == 180 or self._square:
            width = (dimensions.width) + (
                (dimensions.padding[0] + dimensions.padding[2] - dimensions.crop[0] - dimensions.crop[2])
                / dimensions.scale
            )
            icon_size = width * (0.06 if self._square else 0.07) * dimensions.scale
        else:
            height = (dimensions.height) + (
                (dimensions.padding[1] + dimensions.padding[3] - dimensions.crop[1] - dimensions.crop[3])
                / dimensions.scale
            )
            icon_size = height * 0.07 * dimensions.scale

        if cleaning_map:
            icon_size = int(icon_size * 0.7)

        problem_icon = self._map_problem_icon.resize((int(icon_size), int(icon_size))).rotate(-rotation, expand=1)

        mask_layer.paste(segment_mask, (0, 0))
        for k in blocked_segments.keys():
            if k in segments:
                segment = segments[k]
                p = Point(segment.x, segment.y).to_img(dimensions)
                mask_layer.paste(
                    problem_icon,
                    (
                        int(p.x - (problem_icon.size[0] / 2)),
                        int(p.y - (problem_icon.size[1] / 2)),
                    ),
                    mask=problem_icon,
                )

        return mask_layer

    def render_low_lying_areas(self, areas, layer_size, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for area in areas:
            if area.hidden:
                continue
            coords = []
            for i in range(0, len(area.polygon), 2):
                coords.extend(
                    [
                        (
                            ((area.polygon[i] - dimensions.left) / dimensions.grid_size) * dimensions.scale
                            + dimensions.padding[0]
                            - dimensions.crop[0]
                        )
                        * scale,
                        (
                            (
                                (
                                    ((dimensions.height) * dimensions.grid_size - 1)
                                    - (area.polygon[i + 1] - dimensions.top)
                                )
                                / dimensions.grid_size
                            )
                            * dimensions.scale
                            + dimensions.padding[1]
                            - dimensions.crop[1]
                        )
                        * scale,
                    ]
                )
            draw.polygon(
                coords,
                self.color_scheme.low_lying_area,
                (
                    self.color_scheme.auto_low_lying_area_outline
                    if area.type == 0
                    else self.color_scheme.manual_low_lying_area_outline
                ),
                width=(width * scale),
            )
        return new_layer

    @property
    def calibration_points(self) -> dict[str, int]:
        return self._calibration_points

    @property
    def default_map_image(self) -> bytes:
        if self._default_map_image is None:
            default_map_image = Image.open(BytesIO(base64.b64decode(DEFAULT_MAP_IMAGE))).convert("RGBA")
            self._default_map_image = ImageOps.expand(
                default_map_image.resize(
                    (
                        int(default_map_image.size[0] * 0.8),
                        int(default_map_image.size[1] * 0.8),
                    )
                ),
                border=(50, 75, 50, 75),
            )
        return self._to_buffer(self._default_map_image)

    @property
    def disconnected_map_image(self) -> bytes:
        if self._image:
            return self._to_buffer(self._image.filter(ImageFilter.GaussianBlur(7 if self._low_resolution else 12)))
        return self.default_map_image

    @property
    def default_calibration_points(self) -> dict[str, int]:
        return self._default_calibration_points


class DreameVacuumMapOptimizer:
    def __init__(self) -> None:
        self._js_optimizer = None

    def _clean_wall(self, data, width, height):
        for j in range(1, height - 1):
            for i in range(1, width - 1):
                index = j * width + i
                if data[index] == 1:
                    num = 0
                    if data[index - 1] != 1:
                        num = num + 1
                    if data[index + 1] != 1:
                        num = num + 1
                    if data[index + width] != 1:
                        num = num + 1
                    if data[index - width] != 1:
                        num = num + 1
                    if num > 2:
                        data[index] = 0

        for j in range(1, height - 1):
            for i in range(1, width - 1):
                index = j * width + i
                if data[index] == 2:
                    if (data[index - 1] == 1 and data[index + 1] == 1) or (
                        data[index + width] == 1 and data[index - width] == 1
                    ):
                        data[index] = 1

        for i in range(len(data)):
            if data[i] == 2:
                data[i] = 0

    def _obstacle_data(self, data, width, height):
        for it in range(2):
            for j in range(height):
                for i in range(width):
                    index = j * width + i
                    cValue = data[index]
                    if cValue == 2:
                        l = 0 if i == 0 else data[index - 1]
                        r = 0 if i == (width - 1) else data[index + 1]
                        t = 0 if j == (height - 1) else data[index + width]
                        b = 0 if j == 0 else data[index - width]
                        if (l == 0 and r == 2) or (l == 2 and r == 0) or (t == 0 and b == 2) or (t == 2 and b == 0):
                            data[index] = 0

    def _find_first_empty_point(self, data, width, height):
        size = len(data)

        for i in range(width):
            if data[i] == 0:
                return [i, 0]

            if data[(height - 1) * width + i] == 0:
                return [i, (height - 1)]

        for j in range(height):
            if data[j * width] == 0:
                return [0, j]

            if data[j * width + (width - 1)] == 0:
                return [(width - 1), j]

    def _find_zero_point(self, data, width, height, point):
        finds = []
        x = point[0]
        y = point[1]
        for _j in range(y - 1, y + 2):
            for _i in range(x - 1, x + 2):
                if _j == y or _i == x:
                    index = _j * width + _i
                    if data[index] == 0:
                        data[index] = 255
                        finds.append([_i, _j])
        return finds

    def _fill_map_data(self, data, width, height, fill):
        self._fill_map_data_2(data, width, height)

        size = len(data)
        ssize = 3

        for it in range(2):
            for i in range(width):
                startY = -1
                isEmpty = False
                for j in range(height):
                    index = j * width + i
                    if data[index] != 0:
                        if isEmpty and startY >= 0:
                            if (j - startY - 1) <= ssize:
                                for _j in range(startY + 1, j):
                                    num = 0
                                    if i > 0 and _j > 0:
                                        for __i in range(i - 1, i + 2):
                                            for __j in range(_j - 1, _j + 2):
                                                if __i != i and __j != _j:
                                                    if __i == i or __j == _j:
                                                        ind = __j * width + __i
                                                        if ind >= 0 and ind < size and data[__j * width + __i] != 0:
                                                            num = num + 1
                                    else:
                                        num = 5

                                    if num >= 3:
                                        data[_j * width + i] = fill

                            isEmpty = False
                        startY = j
                    else:
                        if startY >= 0:
                            isEmpty = True

            for j in range(height):
                startX = -1
                isEmpty = False
                for i in range(width):
                    index = j * width + i
                    if data[index] != 0:
                        if isEmpty and startX >= 0:
                            if (i - startX - 1) <= ssize:
                                for _i in range(startX + 1, i):
                                    num = 0
                                    if _i > 0 and j > 0:
                                        for __i in range(_i - 1, _i + 2):
                                            for __j in range(j - 1, j + 2):
                                                if __i != _i and __j != j:
                                                    if __i == _i or __j == j:
                                                        ind = __j * width + __i
                                                        if ind >= 0 and ind < size and data[__j * width + __i] != 0:
                                                            num = num + 1
                                    else:
                                        num = 5

                                    if num >= 3:
                                        data[j * width + _i] = fill

                            isEmpty = False

                        startX = i
                    else:
                        if startX >= 0:
                            isEmpty = True

    def _denoise(self, data, width, height):
        tmpMapInfo = data.copy()
        ssize = 20
        for i in range(width):
            startY = -1
            for j in range(height):
                index = j * width + i
                if data[index] != 0:
                    if startY < 0:
                        startY = j
                    continue

                if startY != -1 and (j - startY) <= ssize:
                    isBorder = False
                    if i == 0 or i == (width - 1) or (j - startY) <= 2:
                        isBorder = True

                    if not isBorder:
                        _i = i - 1
                        isBorder = True
                        for k in range(startY, j):
                            if tmpMapInfo[k * width + _i] == 1:
                                isBorder = False
                                break

                    if not isBorder:
                        _i = i + 1
                        isBorder = True
                        for k in range(startY, j):
                            if tmpMapInfo[k * width + _i] == 1:
                                isBorder = False
                                break

                    if isBorder:
                        for k in range(startY, j):
                            data[k * width + i] = 0

                startY = -1

        for j in range(height):
            startX = -1
            for i in range(width):
                index = j * width + i
                if data[index] != 0:
                    if startX < 0:
                        startX = i
                    continue

                if startX != -1 and (i - startX) <= ssize:
                    isBorder = False
                    if j == 0 or j == (height - 1) or (i - startX) <= 2:
                        isBorder = True

                    if not isBorder:
                        _j = j - 1
                        isBorder = True
                        for k in range(startX, i):
                            if tmpMapInfo[_j * width + k] == 1:
                                isBorder = False
                                break

                    if not isBorder:
                        _j = j + 1
                        isBorder = True
                        for k in range(startX, i):
                            if tmpMapInfo[_j * width + k] == 1:
                                isBorder = False
                                break

                    if isBorder:
                        for k in range(startX, i):
                            data[j * width + k] = 0

                startX = -1

        ssize = 2
        for i in range(width):
            startY = -1
            for j in range(height):
                index = j * width + i
                if data[index] != 0:
                    if startY < 0:
                        startY = j
                    continue

                if startY != -1 and (j - startY) <= ssize:
                    for k in range(startY, j):
                        data[k * width + i] = 0

                startY = -1

        for j in range(height):
            startX = -1
            for i in range(width):
                index = j * width + i
                if data[index] != 0:
                    if startX < 0:
                        startX = i
                    continue

                if startX != -1 and (i - startX) <= ssize:
                    for k in range(startX, i):
                        data[j * width + k] = 0

                startX = -1

    def _update_border_value(self, data, width, height, stroke):
        for j in range(height):
            for i in range(width):
                index = j * width + i
                if data[index] != 0:
                    if j == 0 or j == (height - 1) or i == 0 or i == (width - 1):
                        data[index] = stroke
                    else:
                        hasFind = False
                        for _i in range(i - 1, i + 2):
                            for _j in range(j - 1, j + 2):
                                if data[_j * width + _i] == 0:
                                    hasFind = True
                                    break
                            if hasFind:
                                break

                        if hasFind:
                            data[index] = stroke

    def _fill_cross_line(self, data, width, height, stroke):
        size = len(data)
        for i in range(width):
            startY = -1
            for j in range(height):
                index = j * width + i
                lastY = j - 1
                if data[index] == stroke and j != (height - 1):
                    if startY < 0:
                        startY = j
                    continue

                if startY >= 0:
                    if j == (height - 1) and data[index] == stroke:
                        lastY = j

                    if lastY == startY:
                        startY = -1
                        continue

                    crossNum = 0
                    for _j in range(startY, lastY + 1):
                        _i = i - 1
                        if _i >= 0:
                            cIndex = _j * width + _i
                            if cIndex < size and data[cIndex] == stroke:
                                crossNum = crossNum + 1

                        _i = i + 1
                        if _i < width:
                            cIndex = _j * width + _i
                            if cIndex < size and data[cIndex] == stroke:
                                crossNum = crossNum + 1

                        if crossNum > 2:
                            break

                    if crossNum > 2:
                        for _j in range(startY, lastY + 1):
                            _i = i - 1
                            if _i >= 0:
                                cIndex = _j * width + _i
                                if cIndex < size and data[cIndex] == 0:
                                    data[cIndex] = 1

                            _i = i + 1
                            if _i < width:
                                cIndex = _j * width + _i
                                if cIndex < size and data[cIndex] == 0:
                                    data[cIndex] = 1

                startY = -1

        for j in range(height):
            startX = -1
            for i in range(width):
                index = j * width + i
                lastX = i - 1
                if data[index] == stroke and i != (width - 1):
                    if startX < 0:
                        startX = i
                    continue

                if startX >= 0:
                    if data[index] == stroke and i == (width - 1):
                        lastX = i

                    if lastX == startX:
                        startX = -1
                        continue

                    crossNum = 0
                    for _i in range(startX, lastX + 1):
                        _j = j - 1
                        if _j >= 0:
                            cIndex = _j * width + _i
                            if cIndex < size and data[cIndex] == stroke:
                                crossNum = crossNum + 1

                        _j = j + 1
                        if _j < width:
                            cIndex = _j * width + _i
                            if cIndex < size and data[cIndex] == stroke:
                                crossNum = crossNum + 1

                        if crossNum > 2:
                            break

                    if crossNum > 2:
                        for _i in range(startX, lastX + 1):
                            _j = j - 1
                            if _j >= 0:
                                cIndex = _j * width + _i
                                if cIndex < size and data[cIndex] == 0:
                                    data[cIndex] = 1

                            _j = j + 1
                            if _j < width:
                                cIndex = _j * width + _i
                                if cIndex < size and data[cIndex] == 0:
                                    data[cIndex] = 1

                startX = -1

        for i in range(len(data)):
            if data[i] == stroke:
                data[i] = 1

        self._update_border_value(data, width, height, stroke)

    def _check_intersect(self, arr1, arr2) -> list[int]:
        if arr1[0] >= arr2[1] or arr2[0] >= arr1[1]:
            return None

        def sort_data(a, b):
            return a - b

        tmp = arr1 + arr2
        tmp.sort(key=cmp_to_key(sort_data))
        return [tmp[1], tmp[2]]

    def _find_original_points(self, original_data, data, width, xs, ys) -> float:
        if xs[0] > xs[1]:
            tmp = xs[0]
            xs[0] = xs[1]
            xs[1] = tmp

        if ys[0] > ys[1]:
            tmp = ys[0]
            ys[0] = ys[1]
            ys[1] = tmp

        num = 0
        for i in range(xs[0], xs[1] + 1):
            for j in range(ys[0], ys[1] + 1):
                value = original_data[j * width + i]
                if value != 0:
                    num = num + 1

        weight = num / ((xs[1] - xs[0] + 1) * (ys[1] - ys[0] + 1))
        if weight > 0.5:
            size = len(data)
            for i in range(xs[0], xs[1] + 1):
                for j in range(ys[0], ys[1] + 1):
                    nIndex = j * width + i
                    if nIndex < size:
                        data[nIndex] = 1
        return weight

    def _add_line(self, line, covertlines, allLines):
        aLine = ALine()
        if line.ishorizontal:
            aLine.p0.y = line.y
            aLine.p1.y = line.y
            if line.findEnd:
                aLine.p0.x = line.x[0]
                aLine.p1.x = line.x[1]
            else:
                aLine.p0.x = line.x[1]
                aLine.p1.x = line.x[0]
            aLine.length = abs(line.x[1] - line.x[0])
        else:
            aLine.p0.x = line.x
            aLine.p1.x = line.x
            aLine.length = abs(line.y[1] - line.y[0])
            if line.findEnd:
                aLine.p0.y = line.y[0]
                aLine.p1.y = line.y[1]
            else:
                aLine.p0.y = line.y[1]
                aLine.p1.y = line.y[0]
        covertlines.append(aLine)
        allLines.append(line)

    def _find_bounds(self, data, width, horizontalLines, verticalLines) -> list[Paths]:
        paths = []
        size = len(data)

        while horizontalLines:
            startLine = horizontalLines.pop(0)
            startLine.findEnd = True
            covertlines = []
            allLines = []
            self._add_line(startLine, covertlines, allLines)
            while True:
                lastLine = allLines[len(allLines) - 1]
                if lastLine.ishorizontal:
                    hasFind = False

                    lines = verticalLines.copy()
                    for i in range(len(lines)):
                        vLine = lines[i]

                        x = lastLine.x[0]
                        if lastLine.findEnd:
                            x = lastLine.x[1]

                        if x == vLine.x:
                            if lastLine.y == vLine.y[0]:
                                vLine.findEnd = True
                                self._add_line(vLine, covertlines, allLines)
                                del verticalLines[i]
                                hasFind = True
                                break
                            elif lastLine.y == vLine.y[1]:
                                vLine.findEnd = False
                                self._add_line(vLine, covertlines, allLines)
                                del verticalLines[i]
                                hasFind = True
                                break
                            elif lastLine.y > vLine.y[0] and lastLine.y < vLine.y[1]:
                                if lastLine.findEnd:
                                    nIndex = (lastLine.y + 1) * width + x - 1
                                    if nIndex < size and data[nIndex] == 0:
                                        vLine.y[1] = lastLine.y
                                        vLine.findEnd = False
                                    else:
                                        vLine.y[0] = lastLine.y
                                        vLine.findEnd = True
                                else:
                                    nIndex = (lastLine.y + 1) * width + x + 1
                                    if nIndex < size and data[nIndex] == 0:
                                        vLine.y[1] = lastLine.y
                                        vLine.findEnd = False
                                    else:
                                        vLine.y[0] = lastLine.y
                                        vLine.findEnd = True

                                self._add_line(vLine, covertlines, allLines)
                                del verticalLines[i]
                                hasFind = True
                                break

                    if not hasFind:
                        break
                else:
                    hasFind = False
                    _y = lastLine.y[0]
                    if lastLine.findEnd:
                        _y = lastLine.y[1]

                    if _y == startLine.y and lastLine.x == startLine.x[0]:
                        break

                    lines = horizontalLines.copy()
                    for i in range(len(lines)):
                        hLine = lines[i]

                        y = lastLine.y[0]
                        if lastLine.findEnd:
                            y = lastLine.y[1]

                        if y == hLine.y:
                            if lastLine.x == hLine.x[0]:
                                hLine.findEnd = True
                                self._add_line(hLine, covertlines, allLines)
                                del horizontalLines[i]
                                hasFind = True
                                break
                            elif lastLine.x == hLine.x[1]:
                                hLine.findEnd = False
                                self._add_line(hLine, covertlines, allLines)
                                del horizontalLines[i]
                                hasFind = True
                                break
                            elif lastLine.x > hLine.x[0] and lastLine.x < hLine.x[1]:
                                if lastLine.findEnd:
                                    nIndex = (y - 1) * width + lastLine.x - 1
                                    if nIndex < size and data[nIndex] == 0:
                                        hLine.x[0] = lastLine.x
                                        hLine.findEnd = True
                                    else:
                                        hLine.x[1] = lastLine.x
                                        hLine.findEnd = False
                                else:
                                    nIndex = (y + 1) * width + lastLine.x - 1
                                    if nIndex < size and data[nIndex] == 0:
                                        hLine.x[0] = lastLine.x
                                        hLine.findEnd = True
                                    else:
                                        hLine.x[1] = lastLine.x
                                        hLine.findEnd = False

                                self._add_line(hLine, covertlines, allLines)
                                del horizontalLines[i]
                                hasFind = True
                                break

                    if not hasFind:
                        break

            totalLength = 0
            for i in range(len(covertlines)):
                item = covertlines[i]
                totalLength = totalLength + item.length

            paths.append(Paths(clines=covertlines, alines=allLines, length=totalLength))

        return paths

    def _fill_map_data_2(self, data, width, height):
        while True:
            first_point = self._find_first_empty_point(data, width, height)
            if first_point is None:
                break

            data[first_point[1] * width + first_point[0]] = 255
            needFindPoints = [first_point]
            while needFindPoints:
                needFindPoints.extend(self._find_zero_point(data, width, height, needFindPoints.pop(0)))

        for i in range(len(data)):
            if data[i] == 0:
                data[i] = 3
            elif data[i] == 255:
                data[i] = 0

    def _link_adjacent_areas(self, original_data, data, width, height, stroke):
        horizontalLines = []
        verticalLines = []
        DIR_LEFT = 1
        DIR_RIGHT = 2
        DIR_TOP = 3
        DIR_BOTTOM = 4
        size = len(data)
        for i in range(width):
            startY = -1
            for j in range(height):
                index = j * width + i
                lastY = j - 1
                if data[index] == stroke and j != height - 1:
                    isCross = False
                    if (i != 0 and data[index - 1] == stroke) or (i != (width - 1) and data[index + 1] == stroke):
                        isCross = True
                    if startY < 0 and isCross:
                        startY = j
                        continue

                    if not isCross:
                        continue

                    lastY = j

                if startY >= 0:
                    if j == (height - 1) and data[index] == stroke:
                        lastY = j

                    if lastY == startY:
                        startY = -1
                        continue

                    isCross = False
                    direction = DIR_LEFT
                    lastIndex = lastY * width + i
                    if data[lastIndex - 1] == stroke or data[lastIndex + 1] == stroke:
                        isCross = True

                    if i == 0:
                        direction = DIR_LEFT
                    elif i == (width - 1):
                        direction = DIR_RIGHT
                    elif data[lastIndex - 1] == stroke:
                        if data[lastIndex + 1] != 0:
                            direction = DIR_LEFT
                        else:
                            direction = DIR_RIGHT
                    elif data[lastIndex + 1] == stroke:
                        if data[lastIndex - 1] != 0:
                            direction = DIR_RIGHT
                        else:
                            direction = DIR_LEFT

                    if isCross:
                        verticalLines.append(
                            CLine(
                                x=i,
                                y=[startY, lastY],
                                ishorizontal=False,
                                direction=direction,
                                length=(lastY - startY),
                            )
                        )
                        startY = lastY
                        continue
                startY = -1

        for j in range(height):
            startX = -1
            for i in range(width):
                index = j * width + i
                lastX = i - 1
                if data[index] == stroke and i != (width - 1):
                    isCross = False
                    nIndex = index - width
                    nnIndex = index + width
                    if data[nIndex] == stroke or data[nnIndex] == stroke:
                        isCross = True
                    if startX < 0 and isCross:
                        startX = i
                        continue
                    if not isCross:
                        continue

                    lastX = i

                if startX >= 0:
                    if data[index] == stroke and i == (width - 1):
                        lastX = i

                    if lastX == startX:
                        startX = -1
                        continue

                    isCross = False
                    direction = DIR_TOP
                    lastIndex = j * width + lastX
                    nIndex = lastIndex - width
                    nnIndex = lastIndex + width
                    if (nIndex >= 0 and data[nIndex] == stroke) or (nnIndex < size and data[nnIndex] == stroke):
                        isCross = True

                    if j == 0:
                        direction = DIR_BOTTOM
                    elif j == (height - 1):
                        direction = DIR_TOP
                    elif data[nIndex] == stroke:
                        if data[nnIndex] != 0:
                            direction = DIR_BOTTOM
                        else:
                            direction = DIR_TOP
                    elif data[nnIndex] == stroke:
                        if data[nIndex] != 0:
                            direction = DIR_TOP
                        else:
                            direction = DIR_BOTTOM

                    if isCross:
                        horizontalLines.append(
                            CLine(
                                x=[startX, lastX],
                                y=j,
                                ishorizontal=True,
                                direction=direction,
                                length=(lastX - startX),
                            )
                        )
                        startX = lastX
                        continue

                startX = -1

        paths = self._find_bounds(data, width, horizontalLines, verticalLines)
        needFill = len(paths) > 1
        while len(paths) > 1:
            lines = paths.pop(0).alines

            for l in range(len(lines)):
                line = lines[l]
                for i in range(len(paths)):
                    nLines = paths[i].alines
                    for j in range(len(nLines)):
                        nLine = nLines[j]
                        if line.ishorizontal == False and nLine.ishorizontal == False:
                            if line.direction != nLine.direction:
                                if (line.x > nLine.x and line.direction == DIR_LEFT) or (
                                    line.x < nLine.x and line.direction == DIR_RIGHT
                                ):
                                    if abs(line.x - nLine.x) <= 10:
                                        _ys = self._check_intersect(line.y, nLine.y)
                                        if _ys is not None:
                                            xs = [line.x + 1, nLine.x - 1]
                                            if line.x > nLine.x:
                                                xs = [nLine.x + 1, line.x - 1]
                                            weight = self._find_original_points(original_data, data, width, xs, _ys)
                        elif line.ishorizontal == True and nLine.ishorizontal == True:
                            if line.direction != nLine.direction:
                                if (line.y > nLine.y and line.direction == DIR_BOTTOM) or (
                                    line.y < nLine.y and line.direction == DIR_TOP
                                ):
                                    if abs(line.y - nLine.y) <= 10:
                                        _xs = self._check_intersect(line.x, nLine.x)
                                        if _xs is not None:
                                            ys = [line.y + 1, nLine.y - 1]
                                            if line.y > nLine.y:
                                                ys = [nLine.y + 1, line.y - 1]
                                            weight = self._find_original_points(original_data, data, width, _xs, ys)

        if needFill:
            for i in range(len(data)):
                if data[i] == stroke:
                    data[i] = 1

            self._fill_map_data_2(data, width, height)
            self._update_border_value(data, width, height, stroke)
            self._fill_cross_line(data, width, height, stroke)

    def _fill_angle(self, data, width, stroke, angle):
        bottom = 5
        right = 6
        top = 7
        left = 8

        l1 = angle.lines[0]
        l2 = angle.lines[len(angle.lines) - 1]
        if len(angle.lines) == 2 or len(angle.lines) > 22:
            nextAngle = Angle(lines=[l2])
            if l2.ishorizontal:
                nextAngle.horizontalDir = right if l2.findEnd else left
            else:
                nextAngle.verticalDir = top if l2.findEnd else bottom
            return nextAngle

        minx = None
        miny = None
        maxx = None
        maxy = None
        if l1.ishorizontal:
            if angle.horizontalDir == right:
                minx = l1.x[1]
            else:
                maxx = l1.x[0]

            if angle.verticalDir == top:
                miny = l1.y
            else:
                maxy = l1.y

            if l2.ishorizontal:
                if angle.horizontalDir == right:
                    maxx = l2.x[0]
                else:
                    minx = l2.x[1]

                if angle.verticalDir == top:
                    maxy = l2.y
                else:
                    miny = l2.y
            else:
                if angle.horizontalDir == right:
                    maxx = l2.x
                else:
                    minx = l2.x
                if angle.verticalDir == top:
                    maxy = l2.y[0]
                else:
                    miny = l2.y[1]
        else:
            if angle.verticalDir == top:
                miny = l1.y[1]
            else:
                maxy = l1.y[0]

            if angle.horizontalDir == right:
                minx = l1.x
            else:
                maxx = l1.x

            if l2.ishorizontal:
                if angle.horizontalDir == right:
                    maxx = l2.x[0]
                else:
                    minx = l2.x[1]
                if angle.verticalDir == top:
                    maxy = l2.y
                else:
                    miny = l2.y

            else:
                if angle.horizontalDir == right:
                    maxx = l2.x
                else:
                    minx = l2.x

                if angle.verticalDir == top:
                    maxy = l2.y[0]
                else:
                    miny = l2.y[1]

        if minx is None or miny is None or maxx is None or maxy is None:
            nextAngle = Angle(lines=[l2])
            if l2.ishorizontal:
                nextAngle.horizontalDir = right if l2.findEnd else left
            else:
                nextAngle.verticalDir = top if l2.findEnd else bottom
            return nextAngle

        if l1.ishorizontal and l2.ishorizontal and ((maxy - miny) <= 3):
            if angle.horizontalDir == right:
                minx = l1.x[0]
                maxx = l2.x[1]
            else:
                minx = l2.x[0]
                maxx = l1.x[1]
        elif not l1.ishorizontal and not l2.ishorizontal and ((maxx - minx) <= 3):
            if angle.verticalDir == top:
                miny = l1.y[0]
                maxy = l2.y[1]
            else:
                miny = l2.y[0]
                maxy = l1.y[1]

        num = 0
        for i in range(minx, maxx + 1):
            for j in range(miny, maxy + 1):
                index = j * width + i
                if data[index] == 0:
                    num = num + 1

        if num < 20 or num < (((maxx - minx + 1) * (maxy - miny + 1) * 2) / 3):
            for i in range(minx, maxx + 1):
                for j in range(miny, maxy + 1):
                    index = j * width + i
                    if index < len(data) and data[index] == 0:
                        data[index] = stroke

        nextAngle = Angle(lines=[l2])
        if l2.ishorizontal:
            nextAngle.horizontalDir = right if l2.findEnd else left
        else:
            nextAngle.verticalDir = top if l2.findEnd else bottom
        return nextAngle

    def _find_outline(self, data, width, height, stroke, first):
        horizontalLines = []
        verticalLines = []
        size = len(data)

        for i in range(width):
            startY = -1
            for j in range(height):
                index = j * width + i
                lastY = j - 1
                if data[index] == stroke and j != (height - 1):
                    isCross = False
                    if (i != 0 and data[index - 1] == stroke) or (i != (width - 1) and data[index + 1] == stroke):
                        isCross = True
                    if startY < 0 and isCross:
                        startY = j
                        continue
                    if not isCross:
                        continue
                    lastY = j

                if startY >= 0:
                    if j == (height - 1) and data[index] == stroke:
                        lastY = j
                    if lastY == startY:
                        startY = -1
                        continue
                    isCross = False
                    lastIndex = lastY * width + i
                    if data[lastIndex - 1] == stroke or data[lastIndex + 1] == stroke:
                        isCross = True

                    if isCross:
                        verticalLines.append(
                            CLine(
                                x=i,
                                y=[startY, lastY],
                                ishorizontal=False,
                                length=(lastY - startY),
                            )
                        )
                        startY = lastY
                        continue
                startY = -1

        for j in range(height):
            startX = -1
            for i in range(width):
                index = j * width + i
                lastX = i - 1
                if data[index] == stroke and i != (width - 1):
                    isCross = False
                    if data[index - width] == stroke or data[index + width] == stroke:
                        isCross = True
                    if startX < 0 and isCross:
                        startX = i
                        continue
                    if not isCross:
                        continue

                    lastX = i

                if startX >= 0:
                    if data[index] == stroke and i == (width - 1):
                        lastX = i

                    if lastX == startX:
                        startX = -1
                        continue
                    isCross = False
                    nIndex = lastIndex - width
                    nnIndex = lastIndex + width
                    if (nIndex >= 0 and data[nIndex] == stroke) or (nnIndex < size and data[nnIndex] == stroke):
                        isCross = True

                    if isCross:
                        horizontalLines.append(
                            CLine(
                                x=[startX, lastX],
                                y=j,
                                ishorizontal=True,
                                length=(lastX - startX),
                            )
                        )
                        startX = lastX
                        continue
                startX = -1

        if not horizontalLines:
            return False

        paths = self._find_bounds(data, width, horizontalLines, verticalLines)

        covertlines = None
        allLines = None
        totalLen = 0
        tmp = []
        for i in range(len(paths)):
            item = paths[i]
            plen = item.length
            if plen > totalLen:
                if covertlines and totalLen < 80:
                    tmp.append(covertlines)
                totalLen = plen
                covertlines = item.clines
                allLines = item.alines
            else:
                if plen < 80:
                    tmp.append(item.clines)

        if first and tmp:
            clearPos = []
            for i in range(len(tmp)):
                clearPos.append([tmp[i][0].p0.x, tmp[i][0].p0.y])

            while clearPos:
                pos = clearPos.pop()
                x = pos[0]
                y = pos[1]
                data[y * width + x] = 0
                for _i in range(x - 1, x + 2):
                    for _j in range(y - 1, y + 2):
                        if _i == x or _j == y:
                            index = (_j * width) + _i
                            if index < len(data) and data[index] != 0:
                                clearPos.append([_i, _j])

        bottom = 5
        right = 6
        top = 7
        left = 8
        dirnone = 0

        angle = Angle()
        for i in range(len(allLines) + 1):
            line = allLines[0 if i == len(allLines) else i]

            if i == 0:
                angle.lines.append(line)
                angle.horizontalDir = right
            else:
                if line.ishorizontal:
                    horizontalDir = right if line.findEnd else left
                    if angle.horizontalDir != dirnone and angle.horizontalDir != horizontalDir:
                        angle = self._fill_angle(data, width, stroke, angle)

                    if angle.horizontalDir == dirnone:
                        angle.horizontalDir = horizontalDir
                    angle.lines.append(line)
                else:
                    verticalDir = top if line.findEnd else bottom
                    if angle.verticalDir != dirnone and angle.verticalDir != verticalDir:
                        angle = self._fill_angle(data, width, stroke, angle)
                    if angle.verticalDir == dirnone:
                        angle.verticalDir = verticalDir
                    angle.lines.append(line)

                if line.length >= 7 or i == len(allLines):
                    angle = self._fill_angle(data, width, stroke, angle)

        return True

    def _find_obstacle_border(self, data, width, height, stroke):
        size = len(data)
        for j in range(height):
            for i in range(width):
                index = j * width + i
                if data[index] == stroke:
                    if j == 0 or j == (height - 1) or i == 0 or i == (width - 1):
                        data[index] = 2
                        continue
                    hasFind = False
                    for _i in range(i - 1, i + 2):
                        for _j in range(j - 1, j + 2):
                            nIndex = _j * width + _i
                            if nIndex < size and data[nIndex] != stroke and data[nIndex] != 2:
                                hasFind = True
                                break
                        if hasFind:
                            break

                    if hasFind:
                        data[index] = 2

    def _clean_small_obstacle(self, data, width, height, stroke):
        for i in range(width):
            startY = -1
            for j in range(height):
                index = j * width + i
                if data[index] == stroke:
                    if startY < 0:
                        startY = j
                    continue
                if startY != -1 and (j - startY) <= 3:
                    for k in range(startY, j):
                        data[k * width + i] = 1
                startY = -1
        for j in range(height):
            startX = -1
            for i in range(width):
                index = j * width + i
                if data[index] == stroke:
                    if startX < 0:
                        startX = i
                    continue
                if startX != -1 and (i - startX) <= 3:
                    for k in range(startX, i):
                        data[j * width + k] = 1
                startX = -1

    def _calculate_charger_position(self, data, width, height, stroke, charger_position):
        vLines = []
        hLines = []
        for i in range(width):
            startY = -1
            for j in range(height):
                index = j * width + i
                lastY = j - 1
                if data[index] == stroke and j != (height - 1):
                    isCross = False
                    if (i != 0 and data[index - 1] == stroke) or (i != width - 1 and data[index + 1] == stroke):
                        isCross = True
                    if startY < 0 and isCross:
                        startY = j
                        continue
                    if not isCross:
                        continue
                    lastY = j
                if startY >= 0:
                    if j == height - 1 and data[index] == stroke:
                        lastY = j
                    if lastY == startY:
                        startY = -1
                        continue
                    isCross = False
                    lastIndex = lastY * width + i
                    if data[lastIndex - 1] == stroke or data[lastIndex + 1] == stroke:
                        isCross = True

                    if isCross:
                        vLines.append([[i, startY], [i, lastY]])
                        startY = lastY
                        continue
                startY = -1

        for j in range(height):
            startX = -1
            for i in range(width):
                index = j * width + i
                lastX = i - 1
                if data[index] == stroke and i != width - 1:
                    isCross = False
                    if data[index - width] == stroke or data[index + width] == stroke:
                        isCross = True
                    if startX < 0 and isCross:
                        startX = i
                        continue
                    if not isCross:
                        continue
                    lastX = i
                if startX >= 0:
                    if data[index] == stroke and i == width - 1:
                        lastX = i

                    if lastX == startX:
                        startX = -1
                        continue
                    isCross = False
                    lastIndex = j * width + lastX
                    if data[lastIndex - width] == stroke or data[lastIndex + width] == stroke:
                        isCross = True

                    if isCross:
                        hLines.append([[startX, j], [lastX, j]])

                        startX = lastX
                        continue
                startX = -1

        cX = math.floor(charger_position.x)
        cY = math.floor(charger_position.y)
        if abs(charger_position.a - 180) <= 30:
            charger_position.a = 180
            lastX = None
            for i in range(len(vLines)):
                line = vLines[i]
                lx = line[0][0]
                minY = line[0][1] if line[0][1] < line[1][1] else line[1][1]
                maxY = line[0][1] if line[0][1] > line[1][1] else line[1][1]
                if lx >= cX and cY >= minY and cY <= maxY:
                    if lastX == None or lx < lastX:
                        lastX = lx
            if lastX is not None:
                if lastX - cX <= 11:
                    charger_position.a = 180
                    charger_position.x = lastX + 0.5
        elif abs(charger_position.a - 360) <= 30 or abs(charger_position.a) <= 3:
            charger_position.a = 360
            lastX = None
            for i in range(len(vLines)):
                line = vLines[i]
                lx = line[0][0]
                minY = line[0][1] if line[0][1] < line[1][1] else line[1][1]
                maxY = line[0][1] if line[0][1] > line[1][1] else line[1][1]
                if lx <= cX and cY >= minY and cY <= maxY:
                    if lastX == None or lx > lastX:
                        lastX = lx
            if lastX is not None:
                if cX - lastX <= 11:
                    charger_position.a = 360
                    charger_position.x = lastX + 0.5
        elif abs(abs(charger_position.a - 270) <= 30):
            lastY = None
            for i in range(len(hLines)):
                line = hLines[i]
                ly = line[0][1]
                minX = line[0][0] if line[0][0] < line[1][0] else line[1][0]
                maxX = line[0][0] if line[0][0] > line[1][0] else line[1][0]
                if ly >= cY and cX >= minX and cX <= maxX:
                    if lastY == None or ly < lastY:
                        lastY = ly
            if lastY is not None:
                if lastY - cY <= 11:
                    charger_position.a = 270
                    charger_position.y = lastY + 0.5
        elif abs(abs(charger_position.a - 90) <= 30):
            lastY = None
            for i in range(len(hLines)):
                line = hLines[i]
                ly = line[0][1]
                minX = line[0][0] if line[0][0] < line[1][0] else line[1][0]
                maxX = line[0][0] if line[0][0] > line[1][0] else line[1][0]
                if ly <= cY and cX >= minX and cX <= maxX:
                    if lastY == None or ly > lastY:
                        lastY = ly
            if lastY is not None:
                if cY - lastY <= 11:
                    charger_position.a = 90
                    charger_position.y = lastY + 0.5

        return charger_position

    def _merge_saved_map_data(self, map_data, saved_map_data, original_data=None):
        if saved_map_data:
            maxX = map_data.dimensions.left + (map_data.dimensions.width * map_data.dimensions.grid_size)
            maxY = map_data.dimensions.top + (map_data.dimensions.height * map_data.dimensions.grid_size)

            if maxX < saved_map_data.dimensions.left + (
                saved_map_data.dimensions.width * saved_map_data.dimensions.grid_size
            ):
                maxX = saved_map_data.dimensions.left + (
                    saved_map_data.dimensions.width * saved_map_data.dimensions.grid_size
                )

            if maxY < saved_map_data.dimensions.top + (
                saved_map_data.dimensions.height * saved_map_data.dimensions.grid_size
            ):
                maxY = saved_map_data.dimensions.top + (
                    saved_map_data.dimensions.height * saved_map_data.dimensions.grid_size
                )

            left = map_data.dimensions.left
            top = map_data.dimensions.top

            if saved_map_data.dimensions.left < left:
                left = saved_map_data.dimensions.left

            if saved_map_data.dimensions.top < top:
                top = saved_map_data.dimensions.top

            width = int((maxX - left) / saved_map_data.dimensions.grid_size)
            height = int((maxY - top) / saved_map_data.dimensions.grid_size)

            si = int((saved_map_data.dimensions.left - left) / saved_map_data.dimensions.grid_size)
            sj = int((saved_map_data.dimensions.top - top) / saved_map_data.dimensions.grid_size)

            sim = si + saved_map_data.dimensions.width
            sjm = sj + saved_map_data.dimensions.height

            ni = int((map_data.dimensions.left - left) / map_data.dimensions.grid_size)
            nj = int((map_data.dimensions.top - top) / map_data.dimensions.grid_size)

            nim = ni + map_data.dimensions.width
            njm = nj + map_data.dimensions.height

            pixel_type = np.zeros((width, height), np.uint8)
            data = map_data.optimized_pixel_type if map_data.optimized_pixel_type is not None else map_data.pixel_type

            for j in range(height):
                for i in range(width):
                    if j >= sj and i >= si and j < sjm and i < sim:
                        saved_value = int(saved_map_data.pixel_type[(i - si), (j - sj)])
                    else:
                        saved_value = 0

                    if j >= nj and i >= ni and j < njm and i < nim:
                        clean_value = int(data[(i - ni), (j - nj)])
                    else:
                        clean_value = 0

                    if saved_value != 0:
                        if saved_value != 255:
                            pixel_type[i, j] = saved_value
                        else:
                            if clean_value != 0 and clean_value != 255:
                                pixel_type[i, j] = 254
                            else:
                                pixel_type[i, j] = 255
                    elif clean_value != 0:
                        if clean_value == 255:
                            pixel_type[i, j] = 255
                        else:
                            pixel_type[i, j] = 254

            if original_data is not None:
                for j in range(height):
                    for i in range(width):
                        if j >= nj and i >= ni and j < njm and i < nim:
                            if (
                                original_data[(j - nj) * map_data.dimensions.width + (i - ni)] == 2
                                and pixel_type[i, j] != 0
                            ):
                                dis = 3
                                hasBorder = False
                                for _j in range(j - dis, j + dis + 1):
                                    for _i in range(i - dis, i + dis):
                                        if _j < 0 or _i < 0 or _j >= height or _i >= width:
                                            continue
                                        if hasBorder:
                                            break
                                        if pixel_type[_i, _j] == 255:
                                            hasBorder = True
                                            break

                                if not hasBorder:
                                    pixel_type[i, j] = 251

            map_data.optimized_pixel_type = pixel_type
            map_data.optimized_dimensions = MapImageDimensions(top, left, height, width, map_data.dimensions.grid_size)

    def optimize(self, map_data, saved_map_data=None, js_optimizer=True):
        if map_data.need_optimization:
            if map_data.saved_map:
                map_data.need_optimization = False
                return map_data

            if map_data.wifi_map:
                return DreameVacuumMapDecoder.optimize_wifi_map(map_data)

            try:
                now = time.time()

                if js_optimizer:
                    if self._js_optimizer == None:
                        self._js_optimizer = MiniRacer()
                        self._js_optimizer.eval(base64.b64decode(MAP_OPTIMIZER_JS).decode("utf-8"))

                    data = map_data.pixel_type.tolist()
                    data_size = [
                        map_data.dimensions.left,
                        map_data.dimensions.top,
                        map_data.dimensions.width,
                        map_data.dimensions.height,
                        map_data.dimensions.grid_size,
                    ]
                    saved_data = saved_map_data.pixel_type.tolist() if saved_map_data else None
                    saved_data_size = (
                        [
                            saved_map_data.dimensions.left,
                            saved_map_data.dimensions.top,
                            saved_map_data.dimensions.width,
                            saved_map_data.dimensions.height,
                            saved_map_data.dimensions.grid_size,
                        ]
                        if saved_map_data
                        else None
                    )
                    charger_position = None
                    if map_data.charger_position:
                        left = map_data.dimensions.left
                        top = map_data.dimensions.top

                        if saved_map_data:
                            if saved_map_data.dimensions.left < left:
                                left = saved_map_data.dimensions.left

                            if saved_map_data.dimensions.top < top:
                                top = saved_map_data.dimensions.top

                        charger_position = [
                            (map_data.charger_position.x - left) / map_data.dimensions.grid_size,
                            (map_data.charger_position.y - top) / map_data.dimensions.grid_size,
                            map_data.charger_position.a,
                        ]

                    result = self._js_optimizer.call(
                        "optimize",
                        data,
                        data_size,
                        saved_data,
                        saved_data_size,
                        charger_position,
                    )
                    if result and result[0]:
                        map_data.optimized_pixel_type = np.array(result[0], dtype=np.uint8)

                        dimensions = result[1]
                        map_data.optimized_dimensions = MapImageDimensions(
                            dimensions[1],
                            dimensions[0],
                            dimensions[3],
                            dimensions[2],
                            map_data.dimensions.grid_size,
                        )

                        if result[2] and map_data.charger_position:
                            charger = result[2]
                            # map_data.optimized_charger_position = Point(charger[0] * map_data.dimensions.grid_size + left, charger[1] * map_data.dimensions.grid_size + top, charger[2])
                else:
                    width = map_data.dimensions.width
                    height = map_data.dimensions.height
                    clean_data = np.zeros((width * height), np.uint8).tolist()

                    data_map = {255: 2, 253: 1, 250: 3}
                    pointNum = 0
                    for j in range(height):
                        for i in range(width):
                            index = j * width + i
                            clean_data[index] = int(map_data.pixel_type[i, j])
                            if clean_data[index]:
                                pointNum = pointNum + 1
                                clean_data[index] = data_map.get(clean_data[index], 0)

                    original_data = clean_data.copy()
                    pixel_type = np.zeros((width, height), np.uint8)

                    self._clean_wall(clean_data, width, height)
                    self._fill_map_data(clean_data, width, height, 3)
                    self._denoise(clean_data, width, height)
                    self._update_border_value(clean_data, width, height, 5)
                    self._fill_cross_line(clean_data, width, height, 5)
                    self._link_adjacent_areas(original_data, clean_data, width, height, 5)

                    result = self._find_outline(clean_data, width, height, 5, True)
                    if result:
                        self._fill_map_data_2(clean_data, width, height)
                        self._update_border_value(clean_data, width, height, 6)
                        if map_data.charger_position:
                            left = map_data.dimensions.left
                            top = map_data.dimensions.top

                            if saved_map_data:
                                if saved_map_data.dimensions.left < left:
                                    left = saved_map_data.dimensions.left

                                if saved_map_data.dimensions.top < top:
                                    top = saved_map_data.dimensions.top

                            new_charger_position = copy.deepcopy(map_data.charger_position)
                            new_charger_position.x = int(
                                (new_charger_position.x - left) / map_data.dimensions.grid_size
                            )
                            new_charger_position.y = int(
                                (new_charger_position.y - top) / map_data.dimensions.grid_size
                            )
                            if (
                                new_charger_position.y >= 0
                                and new_charger_position.x >= 0
                                and new_charger_position.y < height
                                and new_charger_position.x < width
                                and clean_data[
                                    int(math.floor(new_charger_position.y)) * width
                                    + int(math.floor(new_charger_position.x))
                                ]
                            ):
                                new_charger_position = self._calculate_charger_position(
                                    clean_data, width, height, 6, new_charger_position
                                )
                                map_data.optimized_charger_position = Point(
                                    int(new_charger_position.x * map_data.dimensions.grid_size) + left,
                                    int(new_charger_position.y * map_data.dimensions.grid_size) + top,
                                    new_charger_position.a,
                                )

                        self._find_outline(clean_data, width, height, 6, False)
                        self._fill_map_data_2(clean_data, width, height)
                        self._update_border_value(clean_data, width, height, 7)

                        if saved_map_data:
                            self._find_obstacle_border(clean_data, width, height, 3)
                            self._obstacle_data(original_data, width, height)
                        else:
                            self._clean_small_obstacle(clean_data, width, height, 3)

                        currentPointNum = 0
                        data_map = {7: 255, 2: 255, 3: (0 if saved_map_data else 250)}
                        for j in range(height):
                            for i in range(width):
                                clean_value = clean_data[j * width + i]
                                if clean_value != 0:
                                    currentPointNum = currentPointNum + 1
                                    pixel_type[i, j] = data_map.get(clean_value, 253)

                        if not ((currentPointNum * 100) / pointNum) < 50 and pointNum > 2000:
                            map_data.optimized_pixel_type = pixel_type

                    self._merge_saved_map_data(map_data, saved_map_data, original_data)

                _LOGGER.info(
                    "Optimize Map Data: %s:%s took: %.2f",
                    map_data.map_id,
                    map_data.frame_id,
                    time.time() - now,
                )
            except:
                _LOGGER.warning("Optimize map failed: %s", traceback.format_exc())

                self._merge_saved_map_data(map_data, saved_map_data)

                # _LOGGER.warning(f"""
                # var data = {map_data.pixel_type.tolist()};
                # var data_size = {[map_data.dimensions.left, map_data.dimensions.top, map_data.dimensions.width, map_data.dimensions.height, map_data.dimensions.grid_size]};
                # var saved_data = {saved_map_data.pixel_type.tolist() if saved_map_data else "undefined"};
                # var saved_data_size = {[saved_map_data.dimensions.left, saved_map_data.dimensions.top, saved_map_data.dimensions.width, saved_map_data.dimensions.height, saved_map_data.dimensions.grid_size] if saved_map_data else "undefined"};
                # var charger_position = {[map_data.charger_position.x, map_data.charger_position.y, map_data.charger_position.a] if map_data.charger_position else "undefined"};
                #    """)

        map_data.need_optimization = False
        return map_data
