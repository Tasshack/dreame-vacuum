from __future__ import annotations
import io
import math
import time
import base64
import json
import re
import zlib
import logging
import traceback
import copy
import numpy as np
import hashlib
from py_mini_racer import MiniRacer
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageEnhance, PngImagePlugin, ImageFilter
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
    ObstacleType,
    PathType,
    Point,
    Obstacle,
    MapDataPartial,
    MapData,
    MapFrameType,
    MapPixelType,
    Path,
    Area,
    Wall,
    Segment,
    MapImageDimensions,
    MapRendererLayer,
    MapRendererColorScheme,
    MapRendererConfig,
    MAP_COLOR_SCHEME_LIST,
    MAP_ICON_SET_LIST,
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
    MAP_PARAMETER_ID,
    MAP_PARAMETER_INFO,
    MAP_PARAMETER_FIRST,
    MAP_PARAMETER_OBJNAME,
    MAP_PARAMETER_RESULT,
    MAP_PARAMETER_URL,
    MAP_PARAMETER_EXPIRES_TIME,
    MAP_PARAMETER_THB,
    MAP_PARAMETER_OBJECT_NAME,
    MAP_PARAMETER_MD5,
    MAP_REQUEST_PARAMETER_MAP_ID,
    MAP_REQUEST_PARAMETER_FRAME_ID,
    MAP_REQUEST_PARAMETER_FRAME_TYPE,
    MAP_REQUEST_PARAMETER_REQ_TYPE,
    MAP_REQUEST_PARAMETER_FORCE_TYPE,
    MAP_REQUEST_PARAMETER_TYPE,
    MAP_REQUEST_PARAMETER_INDEX,
    MAP_REQUEST_PARAMETER_ROOM_ID,
    MAP_DATA_PARAMETER_CLASS,
    MAP_DATA_PARAMETER_SIZE,
    MAP_DATA_PARAMETER_X,
    MAP_DATA_PARAMETER_Y,
    MAP_DATA_PARAMETER_PIXEL_SIZE,
    MAP_DATA_PARAMETER_LAYERS,
    MAP_DATA_PARAMETER_ENTITIES,
    MAP_DATA_PARAMETER_META_DATA,
    MAP_DATA_PARAMETER_VERSION,
    MAP_DATA_PARAMETER_ROTATION,
    MAP_DATA_PARAMETER_TYPE,
    MAP_DATA_PARAMETER_POINTS,
    MAP_DATA_PARAMETER_PIXELS,
    MAP_DATA_PARAMETER_SEGMENT_ID,
    MAP_DATA_PARAMETER_ACTIVE,
    MAP_DATA_PARAMETER_NAME,
    MAP_DATA_PARAMETER_DIMENSIONS,
    MAP_DATA_PARAMETER_MIN,
    MAP_DATA_PARAMETER_MAX,
    MAP_DATA_PARAMETER_MID,
    MAP_DATA_PARAMETER_AVG,
    MAP_DATA_PARAMETER_PIXEL_COUNT,
    MAP_DATA_PARAMETER_COMPRESSED_PIXELS,
    MAP_DATA_PARAMETER_ROBOT_POSITION,
    MAP_DATA_PARAMETER_CHARGER_POSITION,
    MAP_DATA_PARAMETER_NO_MOP_AREA,
    MAP_DATA_PARAMETER_NO_GO_AREA,
    MAP_DATA_PARAMETER_ACTIVE_ZONE,
    MAP_DATA_PARAMETER_VIRTUAL_WALL,
    MAP_DATA_PARAMETER_PATH,
    MAP_DATA_PARAMETER_FLOOR,
    MAP_DATA_PARAMETER_WALL,
    MAP_DATA_PARAMETER_SEGMENT,
)

_LOGGER = logging.getLogger(__name__)

class DreameMapVacuumMapManager:
    def __init__(
        self, _protocol: DreameVacuumProtocol
    ) -> None:
        self._map_list_object_name: str = None
        self._map_list_md5: str = None
        self._recovery_map_list_object_name: str = None
        self._update_callback = None
        self._error_callback = None
        self._update_timer: Timer = None
        self._update_running: bool = False
        self._update_interval: float = 10
        self._device_running: bool = False
        self._device_docked: bool = False
        self._available: bool = False
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
        self._recovery_map_data: dict[int, MapData] = {}
        self._need_map_request: bool = False
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

    def _request_map_from_cloud(self) -> bool:
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

        if (
            self._latest_map_data_time is None
            or self._latest_map_data_time < request_start_time
        ):
            self._latest_map_data_time = request_start_time

        if (
            self._latest_object_name_time is None
            or self._latest_object_name_time < request_start_time
        ):
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
            _LOGGER.warn("Getting map_data from cloud failed")
            map_data_result = []

        object_name_result = self._protocol.cloud.get_device_property(
            DIID(DreameVacuumProperty.OBJECT_NAME), 1, self._latest_object_name_time
        )
        if object_name_result is None:
            _LOGGER.warn("Getting object_name from cloud failed")
            object_name_result = []

        next_frame_id = 1

        if len(map_data_result):
            self._latest_map_data_time = map_data_result[0][MAP_PARAMETER_TIME] + 1

        if len(object_name_result):
            self._latest_object_name_time = object_name_result[0][MAP_PARAMETER_TIME] + 1

        for data in map_data_result:
            value = json.loads(data[MAP_PARAMETER_VALUE])
            pmap = value[0]
            timestamp = None
            if data.get(MAP_PARAMETER_TIME):
                timestamp = data[MAP_PARAMETER_TIME] * 1000

            partial_map = self._decode_map_partial(pmap, timestamp)

            if partial_map:
                if partial_map.frame_type == MapFrameType.I.value:
                    self._add_map_data(partial_map)
                else:
                    self._queue_partial_map(partial_map)

        if self._current_frame_id:
            next_frame_id = self._current_frame_id + 1

        partial_map = self._unqueue_partial_map(
            self._latest_map_id, next_frame_id
        )
        if partial_map:
            self._add_map_data(partial_map)
        else:
            if len(object_name_result) == 0:
                self._delete_invalid_partial_maps()
                tmpLen = self._partial_map_queue_size()
                if tmpLen > 8:
                    self.request_new_map()
                elif tmpLen > 4:
                    self._request_missing_p_map()
                elif tmpLen > 0 and len(map_data_result) > 0:
                    self._request_next_p_map(self._latest_map_id, next_frame_id)

        if len(object_name_result) == 1:
            object_name = json.loads(
                object_name_result[0][MAP_PARAMETER_VALUE])
            if object_name:
                _LOGGER.info("New object name received: %s", object_name[0])
                timestamp = None
                if object_name_result[0].get(MAP_PARAMETER_TIME):
                    timestamp = object_name_result[0][MAP_PARAMETER_TIME] * 1000
                response, key = self._get_object_file_data(
                    object_name[0], timestamp)
                if response:
                    partial_map = self._decode_map_partial(
                        response.decode(), timestamp, key
                    )
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
                                self.request_new_map()

        return len(map_data_result) or len(object_name_result)

    def _request_map(self, parameters: dict[str, Any] = None) -> dict[str, Any] | None:
        if parameters is None:
            parameters = {
                MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.I.name,
            }

        payload = [{"piid": PIID(DreameVacuumProperty.FRAME_INFO), MAP_PARAMETER_VALUE: str(
            json.dumps(parameters, separators=(",", ":"))).replace(" ", "")}]

        try:
            _LOGGER.info("Request map from device %s", payload)
            mapping = DreameVacuumActionMapping[DreameVacuumAction.REQUEST_MAP]
            return self._protocol.action(mapping["siid"], mapping["aiid"], payload, 0)
        except Exception as ex:
            _LOGGER.warning("Send request map failed: %s", ex)
        return None

    def _request_i_map(self, start_time: int = None) -> bool:
        if not self._request_i_map_available:
            return self.request_new_map()

        parameters = {
            MAP_REQUEST_PARAMETER_REQ_TYPE: 1,
            MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.I.name,
            MAP_REQUEST_PARAMETER_FORCE_TYPE: 1,
        }

        if start_time:
            parameters[MAP_PARAMETER_TIME] = start_time

        result = self._request_map(parameters)
        if result and result[MAP_PARAMETER_CODE] == 0:
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
                                    object_name = f'{object_name},{values[2]}'

            if has_map:
                self._latest_object_name_time = int(
                    self._last_robot_time / 1000) + 1
                self._map_request_time = None

            if object_name:
                self._add_map_data_file(object_name, self._last_robot_time)
            if raw_map_data:
                self._add_raw_map_data(raw_map_data, self._last_robot_time)
            return True

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
                
        result = self._request_map({
                MAP_REQUEST_PARAMETER_MAP_ID: map_id,
                MAP_REQUEST_PARAMETER_FRAME_ID: frame_id,
                MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.P.name,
            })
        return bool(result and result[MAP_PARAMETER_CODE] == 0)

    def _request_next_p_map(self, map_id: int, frame_id: int) -> bool:
        key = f"{map_id}:{frame_id}"
        if key in self._request_queue and self._request_queue[key]:
            return

        self._request_queue[key] = True

        result = self._request_map({
                MAP_REQUEST_PARAMETER_MAP_ID: map_id,
                MAP_REQUEST_PARAMETER_REQ_TYPE: 1,
                MAP_REQUEST_PARAMETER_FRAME_ID: frame_id,
                MAP_REQUEST_PARAMETER_FRAME_TYPE: MapFrameType.P.name,
            })
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

    def _request_current_map(self, map_request_time: int = None) -> bool:
        if self._request_i_map_available:
            return self._request_i_map(map_request_time)

        return self._request_map_from_cloud()

    def _map_data_changed(self) -> None:
        if self._ready and self._update_callback:
            _LOGGER.debug("Update callback")
            self._update_callback()

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
        for (k, v) in map_data_queue.items():
            if k != self._latest_map_id:
                del self._map_data_queue[k]

        if (
            self._latest_map_id not in self._map_data_queue
            or not self._map_data_queue[self._latest_map_id]
        ):
            return

        map_data_queue = copy.deepcopy(
            self._map_data_queue[self._latest_map_id])
        for (k, v) in map_data_queue.items():
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

        if (
            self._latest_map_id not in self._map_data_queue
            or not self._map_data_queue[self._latest_map_id]
        ):
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
                _LOGGER.debug("Get object name from cloud")
                object_name_result = self._protocol.cloud.get_device_property(
                    DIID(DreameVacuumProperty.OBJECT_NAME)
                )
                if object_name_result:
                    object_name_result = json.loads(
                        object_name_result[0][MAP_PARAMETER_VALUE])
                    object_name = object_name_result[0]

            if object_name is None or object_name == "":
                object_name = f"{str(self._protocol.cloud.user_id)}/{str(self._protocol.cloud.device_id)}/0"

            url = self._get_interim_file_url(object_name)
            if url:
                _LOGGER.debug("Request map data from cloud %s", url)
                response = self._protocol.cloud.get_file(url)
                if response is not None:
                    return response
                _LOGGER.warning("Request map data from cloud failed %s", url)
                if self._file_urls.get(object_name):
                    del self._file_urls[object_name]

    def _get_interim_file_url(self, object_name: str) -> str | None:
        url = None
        if self._file_urls and self._file_urls.get(object_name):
            object = self._file_urls[object_name]
            now = int(round(time.time()))
            if object[MAP_PARAMETER_EXPIRES_TIME] - now > 60:
                url = f'{object[MAP_PARAMETER_URL]}&current={str(now)}'

        if url is None:
            response = self._protocol.cloud.get_interim_file_url(object_name)
            if response and response.get(MAP_PARAMETER_RESULT):
                self._file_urls[object_name] = response[MAP_PARAMETER_RESULT]
                url = self._file_urls[object_name][MAP_PARAMETER_URL]
        return url

    def _decode_map_partial(self, raw_map, timestamp=None, key=None) -> MapDataPartial | None:
        partial_map = DreameVacuumMapDecoder.decode_map_partial(raw_map, self._aes_iv, key)
        if partial_map is not None:
            # After restart or unsuccessful start robot returns timestamp_ms as uptime and that messes up with the latest map/frame id detection.
            # I could not figure out how app handles with this issue but i have added this code to update time stamp as request/object time.

            if timestamp and (
                partial_map.timestamp_ms is None
                or partial_map.timestamp_ms < 1577826000000
            ):
                partial_map.timestamp_ms = timestamp

            if (
                self._latest_map_timestamp_ms is None
                or partial_map.timestamp_ms > self._latest_map_timestamp_ms
            ):
                self._latest_map_timestamp_ms = partial_map.timestamp_ms
                self._latest_map_id = partial_map.map_id

        return partial_map

    def _add_map_data_file(self, object_name: str, timestamp) -> None:
        response, key = self._get_object_file_data(object_name, timestamp)
        if response is not None:
            self._add_raw_map_data(response.decode(), timestamp, key)

    def _add_raw_map_data(self, raw_map: str, timestamp=None, key=None) -> bool:
        return self._add_map_data(self._decode_map_partial(raw_map, timestamp, key))

    def _add_map_data(self, partial_map: MapDataPartial) -> None:
        if partial_map is not None:
            if (
                partial_map.timestamp_ms is not None
                and self._current_timestamp_ms is not None
                and self._current_timestamp_ms is not None
                and self._current_frame_id
                and self._current_timestamp_ms > partial_map.timestamp_ms
            ):
                _LOGGER.debug(
                    "Skip frame %s, timestamp %s:%s < %s:%s",
                    partial_map.frame_type,
                    partial_map.frame_id,
                    partial_map.timestamp_ms,
                    self._current_frame_id,
                    self._current_timestamp_ms,
                )
                return

            if (
                self._current_map_id is not None
                and self._current_map_id != self._latest_map_id
            ):
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
                return

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
                    return

            if partial_map.frame_type == MapFrameType.P.value:
                if (
                    self._current_frame_id is not None
                    and self._map_data is not None
                    and self._map_data.restored_map
                ):
                    _LOGGER.debug("Current map data removed")
                    self._map_data = None
                    self._current_frame_id = None
                    self._current_map_id = None

                if self._current_frame_id is None or self._map_data is None:
                    self._queue_partial_map(partial_map)

                    if self._map_request_time is None:
                        self._request_i_map()
                        return

                if partial_map.frame_id != self._current_frame_id + 1:
                    if partial_map.frame_id <= self._current_frame_id:
                        self._add_next_map_data()
                        return

                    self._queue_partial_map(partial_map)
                    self._delete_invalid_partial_maps()

                    if self._partial_map_queue_size() > 0:
                        self._request_next_p_map(
                            partial_map.map_id, self._current_frame_id + 1
                        )
                    else:
                        self._add_next_map_data()
                    return

                current_robot_position = copy.deepcopy(
                    self._map_data.robot_position) if self._map_data.robot_position else None

                map_data = DreameVacuumMapDecoder.decode_p_map_data_from_partial(
                    partial_map, self._map_data, self._vslam_map,
                )
                if map_data:
                    self._map_data = map_data
                    self._map_data.last_updated = time.time()
                    self._updated_frame_id = None
                    self._current_frame_id = map_data.frame_id
                    self._current_map_id = map_data.map_id
                    self._current_timestamp_ms = map_data.timestamp_ms

                    _LOGGER.info(
                        "Decode P map %d %d", map_data.map_id, map_data.frame_id
                    )

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
                    return

                if map_data.empty_map:
                    if self._map_data is None or not self._map_data.empty_map:
                        self._init_data()
                        self._map_data = map_data
                        self._current_frame_id = map_data.frame_id
                        self._current_map_id = map_data.map_id
                        self._current_timestamp_ms = map_data.timestamp_ms

                        self._map_data_changed()
                    self._add_next_map_data()
                    return

                if saved_map_data is not None and saved_map_data.saved_map:
                    if saved_map_data.map_id in self._saved_map_data:
                        map_data.temporary_map = False
                        self._selected_map_id = saved_map_data.map_id
                        saved_map_data.map_name = self._saved_map_data[
                            saved_map_data.map_id
                        ].map_name
                        saved_map_data.custom_name = self._saved_map_data[
                            saved_map_data.map_id
                        ].custom_name
                        saved_map_data.rotation = self._saved_map_data[
                            saved_map_data.map_id
                        ].rotation
                        saved_map_data.map_index = self._saved_map_data[
                            saved_map_data.map_id
                        ].map_index

                        saved_map_data.timestamp_ms = map_data.timestamp_ms
                        if (
                            saved_map_data
                            != self._saved_map_data[saved_map_data.map_id]
                            or saved_map_data.segments
                            != self._saved_map_data[saved_map_data.map_id].segments
                        ):
                            saved_map_data.last_updated = time.time()
                            self._saved_map_data[saved_map_data.map_id] = saved_map_data

                            _LOGGER.debug(
                                "Decode saved map %s: %s",
                                saved_map_data.map_id,
                                saved_map_data.map_name,
                            )
                    elif not map_data.temporary_map:
                        if not self._map_list:
                            saved_map_data.last_updated = time.time()
                            self._saved_map_data[saved_map_data.map_id] = saved_map_data

                            _LOGGER.info(
                                "Add saved map from new map %s", saved_map_data.map_id
                            )
                            self._refresh_map_list()
                            if self._map_data:
                                self._map_data_changed()

                        if self._device_running:
                            self.request_next_map_list()
                        else:
                            self.request_map_list()

                if not map_data.saved_map:
                    if self._vslam_map:
                        if map_data.saved_map_status == 1 and saved_map_data and self._device_docked:
                            map_data.segments = copy.deepcopy(saved_map_data.segments)
                            map_data.data = copy.deepcopy(saved_map_data.data)
                            map_data.pixel_type = copy.deepcopy(saved_map_data.pixel_type)
                            map_data.dimensions = copy.deepcopy(saved_map_data.dimensions)
                            map_data.charger_position = copy.deepcopy(saved_map_data.charger_position)
                            map_data.no_go_areas = saved_map_data.no_go_areas
                            map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                            map_data.walls = saved_map_data.walls
                            map_data.robot_position = None
                            map_data.docked = True
                            #map_data.restored_map = True
                            map_data.path = None
                            map_data.need_optimization = False
                            map_data.saved_map_status = 2
                        elif map_data.robot_position is None and map_data.restored_map and not self._device_docked and self._map_data and not map_data.docked:
                            map_data.robot_position = self._map_data.robot_position

                    changed = (
                        self._current_frame_id is None
                        or self._map_data is None
                        or map_data != self._map_data
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
                            if map_data.frame_id <= self._updated_frame_id:
                                if (
                                    not self._map_data.empty_map
                                    and (self._map_data.saved_map_status == 2 or (self._vslam_map and self._map_data.saved_map_status == 1))
                                ):
                                    map_data.active_segments = (
                                        self._map_data.active_segments
                                    )
                                    map_data.active_areas = self._map_data.active_areas
                                    map_data.active_points = self._map_data.active_points
                                    map_data.path = self._map_data.path
                                    map_data.segments = self._map_data.segments
                                    map_data.cleanset = self._map_data.cleanset
                                    changed = map_data != self._map_data
                                else:
                                    changed = False
                                    map_data.empty_map = True
                            else:
                                self._updated_frame_id = None

                        if self._map_data and not changed and map_data.need_optimization and not self._map_data.need_optimization:
                            map_data.need_optimization = False
                            map_data.optimized_pixel_type = copy.deepcopy(self._map_data.optimized_pixel_type)
                            map_data.optimized_dimensions = copy.deepcopy(self._map_data.optimized_dimensions)
                            map_data.optimized_charger_position = copy.deepcopy(self._map_data.optimized_charger_position)

                        self._map_data = map_data
                        self._current_frame_id = map_data.frame_id
                        self._current_map_id = map_data.map_id
                        self._current_timestamp_ms = map_data.timestamp_ms

                        if changed:
                            _LOGGER.info(
                                "Decode I map %d %d", map_data.map_id, map_data.frame_id
                            )

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

    def _add_next_map_data(self) -> None:
        next_partial_map = self._unqueue_next_partial_map()
        if next_partial_map is not None:
            _LOGGER.debug("Continue to next map data")
            self._add_map_data(next_partial_map)

    def _refresh_map_list(self) -> None:
        index = 1
        new_map_list = []
        for (map_id, saved_map_data) in sorted(self._saved_map_data.items()):
            new_map_list.append(map_id)
            if saved_map_data.custom_name is None:
                saved_map_data.map_name = f"Map {str(index)}"
            else:
                saved_map_data.map_name = saved_map_data.custom_name
            saved_map_data.map_index = index
            index = index + 1
        self._map_list = new_map_list

    def get_map(self, map_index: int = 0) -> MapData | None:
        if map_index:
            if map_index <= len(self._map_list):
                return self._saved_map_data[self._map_list[map_index - 1]]
            return None
        return self._map_data

    def listen(self, callback) -> None:
        self._update_callback = callback

    def listen_error(self, callback) -> None:
        self._error_callback = callback

    def schedule_update(self, wait: float = None) -> None:
        if not wait:
            wait = self._update_interval
        if self._update_timer is not None:
            self._update_timer.cancel()
            del self._update_timer
            self._update_timer = None
        if wait >= 0:
            self._update_timer = Timer(wait, self._update_task)
            self._update_timer.start()

    def update(self) -> None:
        if self._update_running:
            return

        self._update_running = True

        _LOGGER.debug("Map update: %s", self._update_interval)
        try:
            if (self._map_list_object_name and self._need_map_list_request is None) or (self._need_map_list_request and not self._device_running):
                self.request_map_list()

            # Not supported Yet
            # if self._recovery_map_list_object_name and self._need_recovery_map_list_request is None or (self._need_recovery_map_list_request and not self._device_running):
            #    self.request_recovery_map_list()

            if self._map_request_time is not None or self._need_map_request:
                self._updated_frame_id = None
                self._map_request_count = self._map_request_count + 1
                if self._map_request_count >= 16:
                    self._map_request_time = None
                    self._need_map_request = False
                else:
                    self._request_current_map(self._map_request_time)
            elif self._map_data is None or (
                self._device_running
                and (
                    time.time() - (self._current_timestamp_ms / 1000.0) > 15
                    or self._map_data.empty_map
                )
            ):
                self._updated_frame_id = None
                if self._map_data and not self._map_data.empty_map:
                    _LOGGER.info(
                        "Need map request: %.2f",
                        time.time() - (self._current_timestamp_ms / 1000.0),
                    )
                # if self._map_data and not self._map_data.empty_map and time.time() - (self._current_timestamp_ms / 1000.0) > 30:
                #    self.request_new_map()
                # else:
                if self._protocol.cloud.logged_in:
                    self._request_current_map()
            elif not self._request_map_from_cloud() and self._device_running:
                _LOGGER.info("No new map data received, retrying")
                sleep(0.5)
                if not self._request_map_from_cloud():
                    _LOGGER.info(
                        "No new map data received on second try")

            if not self._available:
                self._available = True
                self._map_data_changed()
        except Exception as ex:
            if self._available:
                _LOGGER.warning("Map update Failed: %s",
                                traceback.format_exc())
                self._available = False
                if self._error_callback:
                    self._error_callback(DeviceUpdateFailedException(ex))

        self._ready = True
        self._update_running = False

    def set_aes_iv(self, aes_iv: str) -> None:
        if aes_iv:
            self._aes_iv = aes_iv

    def set_vslam_map(self) -> None:
        self._vslam_map = True

    def set_update_interval(self, update_interval: float) -> None:
        if self._update_interval != update_interval:
            self._update_interval = update_interval
            self.schedule_update()

    def set_device_running(self, running: bool, docked: bool) -> None:
        if self._device_running != running or self._device_docked != docked:
            self._device_running = running
            if self._device_docked != docked:
                if self._vslam_map and docked and self._map_data and self._map_data.saved_map_status == 1:
                    saved_map_data = self._map_manager.selected_map
                    self._map_data.segments = copy.deepcopy(saved_map_data.segments)
                    self._map_data.data = copy.deepcopy(saved_map_data.data)
                    self._map_data.pixel_type = copy.deepcopy(saved_map_data.pixel_type)
                    self._map_data.dimensions = copy.deepcopy(saved_map_data.dimensions)
                    self._map_data.charger_position = copy.deepcopy(saved_map_data.charger_position)
                    self._map_data.no_go_areas = saved_map_data.no_go_areas
                    self._map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                    self._map_data.walls = saved_map_data.walls
                    self._map_data.robot_position = self._map_data.charger_position
                    self._map_data.docked = True
                    #self._map_data.restored_map = True
                    self._map_data.path = None
                    self._map_data.need_optimization = False
                    self._map_data.saved_map_status = 2
                    self._map_data.last_updated = time.time()
                    self._map_data_changed()
                    
                self._device_docked = docked

            self.schedule_update(2)

    def set_device_docked(self, device_docked: bool) -> None:
        if self._device_docked != device_docked:
            self.schedule_update(2)
        self._device_docked = device_docked

    def request_new_map(self) -> None:
        if self._new_map_request_time and time.time() - self._new_map_request_time < 10:
            if time.time() - self._new_map_request_time > 3:
                self._new_map_request_time = time.time()
                self._request_map_from_cloud()
            return

        self._new_map_request_time = time.time()
        if self._map_data is None:
            return self._request_i_map()
        else:
            result = self._request_map()
            if result and result[MAP_PARAMETER_CODE] == 0:
                self._request_map_from_cloud()

    def request_next_map(self) -> None:
        self._map_request_count = 0
        self._need_map_request = True
        self.schedule_update(2)

    def request_next_map_list(self) -> None:
        self._need_map_list_request = True

    def set_map_list_object_name(self, map_list: dict[int, str]) -> bool:
        if map_list and map_list != "":
            md5 = map_list.get(MAP_PARAMETER_MD5)
            object_name = map_list.get(MAP_PARAMETER_OBJECT_NAME)
            if map_list and object_name and object_name != "":
                if self._map_list_object_name != object_name or self._map_list_md5 != md5:
                    self._map_list_object_name = object_name
                    if not self._device_running and self._map_list_md5 is not None:
                        self.request_next_map_list()
                        self.schedule_update(2)
                    self._map_list_md5 = md5
                    return True
        return False

    def set_recovery_map_list_object_name(self, map_list: dict[int, str]) -> bool:
        if map_list and map_list != "":
            object_name = map_list.get(MAP_PARAMETER_OBJECT_NAME)
            if map_list and object_name and object_name != "":
                if self._recovery_map_list_object_name != object_name:
                    self._recovery_map_list_object_name = object_name
                    self._need_recovery_map_list_request = True
                    return True
        return False

    def request_map_list(self) -> None:
        if self._map_list_object_name and self._protocol.cloud.logged_in:
            _LOGGER.info("Get Map List: %s", self._map_list_object_name)
            try:
                response = self._get_interim_file_data(
                    self._map_list_object_name)
            except Exception as ex:
                _LOGGER.warn("Get Map List failed: %s", ex)
                return

            if response:
                self._need_map_list_request = False
                raw_map = response.decode()

                try:
                    map_info = json.loads(raw_map)
                except:
                    _LOGGER.warn("Get Map List json parse failed")
                    return

                saved_map_list = map_info[MAP_PARAMETER_MAPSTR]
                changed = False
                now = time.time()
                map_list = {}
                if saved_map_list:
                    for v in saved_map_list:
                        if v.get(MAP_PARAMETER_MAP):
                            saved_map_data = DreameVacuumMapDecoder.decode_saved_map(
                                v[MAP_PARAMETER_MAP], self._vslam_map, int(v[MAP_PARAMETER_ANGLE]) if v.get(
                                    MAP_PARAMETER_ANGLE) else 0, self._aes_iv
                            )
                            if saved_map_data is not None:
                                name = v.get(MAP_PARAMETER_NAME)
                                if name:
                                    saved_map_data.custom_name = name
                                    saved_map_data.map_name = name
                                map_list[saved_map_data.map_id] = saved_map_data

                    for (map_id, saved_map_data) in sorted(map_list.items()):
                        if map_id in self._saved_map_data:
                            if self._selected_map_id == map_id and self._map_data:
                                saved_map_data.cleanset = self._map_data.cleanset
                            else:
                                saved_map_data.cleanset = self._saved_map_data[map_id].cleanset

                            if self._saved_map_data[map_id] != saved_map_data:
                                _LOGGER.info("Saved map changed: %s", map_id)
                                changed = True
                                saved_map_data.last_updated = now
                                if (
                                    self._map_data is None
                                    or self._selected_map_id != map_id
                                ):
                                    self._saved_map_data[map_id] = saved_map_data
                                else:
                                    self._saved_map_data[
                                        map_id
                                    ].custom_name = saved_map_data.custom_name
                                    self._saved_map_data[
                                        map_id
                                    ].rotation = saved_map_data.rotation
                        else:
                            saved_map_data.last_updated = now
                            self._saved_map_data[map_id] = saved_map_data
                            _LOGGER.info("Add saved map: %s", map_id)
                            changed = True

                current_map_list = self._saved_map_data.copy()
                for map_id in current_map_list.keys():
                    if map_id not in map_list:
                        del self._saved_map_data[map_id]
                        changed = True

                selected_map_id = map_info[MAP_PARAMETER_CURR_ID]
                if (
                    selected_map_id in self._saved_map_data
                    and self._selected_map_id != selected_map_id
                ):
                    self._selected_map_id = selected_map_id
                    changed = True

                if changed == True:
                    self._refresh_map_list()
                    if self._map_data:
                        self._map_data_changed()

    def request_recovery_map_list(self) -> None:
        if self._recovery_map_list_object_name:
            now = time.time()
            response = self._get_interim_file_data(
                self._recovery_map_list_object_name)
            if response:
                self._need_recovery_map_list_request = False
                raw_map = response.decode()
                recovery_map_list = json.loads(raw_map)
                for recovery_map in recovery_map_list:
                    map_id = recovery_map[MAP_PARAMETER_ID]
                    if map_id in self._map_list:
                        map_info_list = recovery_map[MAP_PARAMETER_INFO]
                        for map_info in map_info_list:
                            first = map_info[MAP_PARAMETER_FIRST]
                            map_time = map_info[MAP_PARAMETER_TIME]
                            object_name = map_info[MAP_PARAMETER_OBJNAME]
                            if object_name.endswith('mb.tbz2'):
                                response = self._protocol.cloud.get_file_url(
                                    object_name)
                            else:
                                response = self._protocol.cloud.get_interim_file_url(
                                    object_name)

                            if response and response.get(MAP_PARAMETER_RESULT):
                                _LOGGER.info(
                                    "Get recovery map file url result: %s", response)
                                map_url = response[MAP_PARAMETER_RESULT][MAP_PARAMETER_URL]
                                recovery_map_data = DreameVacuumMapDecoder.decode_saved_map(
                                    map_info[MAP_PARAMETER_THB], self._vslam_map, self._saved_map_data[map_id].rotation, self._aes_iv)
                                # TODO: store recovery map

    @property
    def _request_i_map_available(self) -> bool:
        return bool(
            not (
                self._map_data is not None
                and (
                    (
                        self._map_data.saved_map_status == 0
                        and not self._map_data.empty_map
                    )
                    or self._map_data.saved_map_status == 1
                    or self._map_data.restored_map
                    or self._map_data.temporary_map
                )
            )
        )

    @property
    def map_list(self) -> list[int] | None:
        return self._saved_map_data.keys()

    @property
    def map_data_list(self) -> dict[int, MapData] | None:
        return self._saved_map_data

    @property
    def selected_map(self) -> MapData | None:
        if self._map_data:
            if (
                self._selected_map_id is not None
                and self._selected_map_id in self._saved_map_data
            ):
                return self._saved_map_data[self._selected_map_id]

            if (
                self._map_list
                and len(self._map_list) == 1
                and self._map_list[0] in self._saved_map_data
            ):
                return self._saved_map_data[self._map_list[0]]


class DreameMapVacuumMapEditor:
    """ Every map change must be handled on memory before actually requesting it to the device because it takes too much time to get the updated map from the cloud.
    This class handles user edits on stored map data like updating customized cleaning settings or setting active segments on segment cleaning.
    Original app has a similar class to handle the same issue (Works optimistically) """

    def __init__(self, map_manager) -> None:
        self._previous_cleaning_sequence: dict[int, list[int]] = {}
        self.map_manager = map_manager

    def _set_updated_frame_id(self, frame_id) -> None:
        self.map_manager._updated_frame_id = frame_id

    def refresh_map(self, map_id: int = None) -> None:
        if map_id:
            if self._saved_map_data and map_id in self._saved_map_data:
                self._saved_map_data[map_id].last_updated = time.time()
            return
        if self._map_data is not None:
            self._map_data.last_updated = time.time()

    def set_active_areas(self, active_areas: list[list[int]]) -> None:
        map_data = self._map_data
        if map_data is not None:
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

    def clear_path(self) -> None:
        map_data = self._map_data
        if map_data is not None:
            map_data.path = None
            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()

    def reset_map(self) -> None:
        map_data = self._map_data
        if map_data is not None:
            map_data.dimensions.width = 0
            map_data.dimensions.height = 0
            map_data.segments = {}
            map_data.path = None
            map_data.empty_map = True
            map_data.saved_map_status = 0
            self._set_updated_frame_id(map_data.frame_id + 2)
            self.refresh_map()

    def set_rotation(self, map_id: int, rotation: int) -> None:
        if map_id in self._saved_map_data:
            self._saved_map_data[map_id].rotation = rotation
            if self._map_data is not None and map_id == self._selected_map_id:
                self._map_data.rotation = rotation
                self.refresh_map()
            self.refresh_map(map_id)

    def set_map_name(self, map_id: int, name: str) -> None:
        if map_id in self._saved_map_data:
            self._saved_map_data[map_id].custom_name = name
            self._saved_map_data[map_id].map_name = name
            self.refresh_map(map_id)
            self.refresh_map()

    def select_map(self, map_id: int) -> None:
        if map_id != self._selected_map_id:
            self.set_current_map(map_id)

    def set_current_map(self, map_id: int) -> None:
        if map_id and map_id in self._saved_map_data:
            saved_map_data = copy.deepcopy(self._saved_map_data[map_id])
            saved_map_data.docked = self._map_data.docked
            saved_map_data.timestamp_ms = self._current_timestamp_ms
            saved_map_data.frame_id = None
            saved_map_data.map_name = None
            saved_map_data.map_index = 0
            saved_map_data.custom_name = None
            saved_map_data.saved_map = False
            saved_map_data.restored_map = True
            saved_map_data.temporary_map = False
            saved_map_data.empty_map = False
            saved_map_data.saved_map_status = 2
            DreameVacuumMapDecoder.set_segment_cleanset(
                saved_map_data, saved_map_data.cleanset
            )
            self.map_manager._map_data = saved_map_data
            self.map_manager._current_frame_id = None
            self.map_manager._current_map_id = map_id
            self.map_manager._selected_map_id = map_id
            self.refresh_map()

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
                if len(self.map_manager._map_list) > 1:
                    self.set_current_map(self.map_manager._map_list[-1])
                else:
                    self.map_manager._map_data = None
                    self._updated_frame_id = None
                    self._selected_map_id = None

            del self.map_manager._saved_map_data[map_id]
            self.map_manager._refresh_map_list()
            self.map_manager.request_next_map_list()

    def merge_segments(self, map_id: int, segments: list[int]) -> None:
        saved_map_data = self._saved_map_data
        if (
            saved_map_data
            and map_id in saved_map_data
            and len(segments) == 2
        ):
            map_data = saved_map_data[map_id]
            if (
                map_data.segments
                and segments[0] in map_data.segments
                and segments[1] in map_data.segments
            ):
                if segments[1] not in map_data.segments[segments[0]].neighbors:
                    _LOGGER.error(
                        "Segments are not neighbors with each other: %s", segments
                    )
                    return

                data = np.zeros((map_data.dimensions.width *
                                map_data.dimensions.height), np.uint8)
                for y in range(map_data.dimensions.height):
                    for x in range(map_data.dimensions.width):
                        index = y * map_data.dimensions.width + x
                        if (map_data.data[index] & 0x3F) == segments[1]:
                            data[index] = segments[0]
                        else:
                            data[index] = map_data.data[index]

                        if int(map_data.pixel_type[x, y]) == segments[1]:
                            map_data.pixel_type[x, y] = segments[0]

                map_data.data = bytes(data)
                del self.map_manager._saved_map_data[map_id].segments[segments[1]]
                new_segments = DreameVacuumMapDecoder.get_segments(map_data, self.map_manager._vslam_map)
                map_data.segments[segments[0]].x = new_segments[segments[0]].x
                map_data.segments[segments[0]].y = new_segments[segments[0]].y

                for (k, v) in map_data.segments.items():
                    if segments[1] in v.neighbors:
                        map_data.segments[k].neighbors.remove(segments[1])

                DreameVacuumMapDecoder.set_segment_color_index(map_data)
                if self._map_data and map_id == self._selected_map_id:
                    self.set_current_map(map_id)
                self.refresh_map(map_id)

    def split_segments(self, map_id: int, segment: int, line: list[int]) -> None:
        if self._saved_map_data and map_id in self._saved_map_data:
            if self._map_data and map_id == self._selected_map_id:
                self.set_current_map(map_id)
            self.refresh_map(map_id)

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
                map_data.temporary_map = False
                map_data.saved_map = False
                map_data.saved_map_status = 0
                map_data.restored_map = True
                map_data.empty_map = False
                map_data.cleanset = {}
                DreameVacuumMapDecoder.set_segment_cleanset(
                    map_data, map_data.cleanset
                )
                self.map_manager._map_data = map_data
                self.map_manager._selected_map_id = new_map.map_id
                self.map_manager.request_next_map_list()
                self.refresh_map()

    def restore_map(self, map_id: int, map_url: str) -> None:
        self.map_manager.request_next_map_list()

    def set_cleaning_sequence(self, cleaning_sequence: list[int]) -> list[int] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and not map_data.temporary_map
        ):
            new_cleaning_sequence = []
            if cleaning_sequence:
                index = 1
                for k in (
                        cleaning_sequence
                        if (
                            len(cleaning_sequence) == len(
                                map_data.segments.items())
                            and all(k in cleaning_sequence for k in map_data.segments.keys())
                        )
                        else sorted(map_data.segments.keys())
                ):
                    map_data.segments[k].order = index
                    map_data.cleanset[str(k)][3] = map_data.segments[k].order
                    new_cleaning_sequence.append(k)
                    index = index + 1
            else:
                for v in map_data.segments.values():
                    if v.order:
                        self._previous_cleaning_sequence[map_data.map_id] = [(k) for k, v in sorted(
                            map_data.segments.items(), key=lambda s: s[1].order) if v.order]
                        break

                for k in map_data.segments.keys():
                    map_data.segments[k].order = 0
                    map_data.cleanset[str(k)][3] = 0

            if self._saved_map_data and map_data.map_id in self._saved_map_data:
                self._saved_map_data[map_data.map_id].cleanset = copy.deepcopy(
                    map_data.cleanset)

            self._set_updated_frame_id(map_data.frame_id + 1)
            self.refresh_map()
            return [(k) for k, v in sorted(map_data.segments.items(), key=lambda s: s[1].order) if v.order]

    def set_segment_order(self, segment_id: int, order: int) -> list[int] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
            and not map_data.temporary_map
        ):
            if order > 0:
                if (
                    not map_data.segments[segment_id].order
                    and map_data.map_id in self._previous_cleaning_sequence
                    and len(self._previous_cleaning_sequence[map_data.map_id]) == len(map_data.segments.items())
                    and all(k in self._previous_cleaning_sequence[map_data.map_id] for k in map_data.segments.keys())
                ):
                    cleaning_sequence = self.set_cleaning_sequence(
                        self._previous_cleaning_sequence[map_data.map_id])
                    del self._previous_cleaning_sequence[map_data.map_id]
                    return cleaning_sequence

                index = 1
                for k in sorted(map_data.segments.keys()):
                    if not map_data.segments[k].order:
                        map_data.segments[k].order = index
                        map_data.cleanset[str(
                            k)][3] = map_data.segments[k].order
                    index = index + 1

                current_order = map_data.segments[segment_id].order
                if current_order != order:
                    map_data.segments[segment_id].order = order
                    map_data.cleanset[str(segment_id)][3] = order
                    for k, v in map_data.segments.items():
                        if k != segment_id and v.order == order:
                            map_data.segments[k].order = current_order
                            map_data.cleanset[str(
                                k)][3] = map_data.segments[k].order
            else:
                for v in map_data.segments.values():
                    if v.order:
                        self._previous_cleaning_sequence[map_data.map_id] = [(k) for k, v in sorted(
                            map_data.segments.items(), key=lambda s: s[1].order) if v.order]
                        break

                for k in map_data.segments.keys():
                    map_data.segments[k].order = 0
                    map_data.cleanset[str(k)][3] = 0

            if self._saved_map_data and map_data.map_id in self._saved_map_data:
                self._saved_map_data[map_data.map_id].cleanset = copy.deepcopy(
                    map_data.cleanset)

            self._set_updated_frame_id(map_data.frame_id + 1)
            self.refresh_map()
            return [(k) for k, v in sorted(map_data.segments.items(), key=lambda s: s[1].order) if v.order]

    def cleanset(self, map_data: MapData) -> list[list[int]] | None:
        cleanset = []
        for (k, v) in map_data.segments.items():
            if v.suction_level is None:
                v.suction_level = 1
            if v.water_volume is None:
                v.water_volume = 2
            if v.cleaning_times is None:
                v.cleaning_times = 1

            settings = [
                k,
                v.suction_level,
                v.water_volume + 1,
                v.cleaning_times,
            ]

            if v.cleaning_mode is not None:
                settings.append(v.cleaning_mode)

            cleanset.append(settings)
        return cleanset

    def set_segment_suction_level(self, segment_id: int, suction_level: int) -> list[list[int]] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
            and not map_data.temporary_map
        ):
            map_data.segments[segment_id].suction_level = suction_level
            map_data.cleanset[str(segment_id)][0] = suction_level
            if self._saved_map_data and map_data.map_id in self._saved_map_data:
                self._saved_map_data[map_data.map_id].cleanset = copy.deepcopy(
                    map_data.cleanset)
            self._set_updated_frame_id(map_data.frame_id + 1)
            self.refresh_map()
            return self.cleanset(map_data)

    def set_segment_water_volume(self, segment_id: int, water_volume: int) -> list[list[int]] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
        ):
            map_data.segments[segment_id].water_volume = water_volume
            map_data.cleanset[str(segment_id)][1] = water_volume + 1
            if self._saved_map_data and map_data.map_id in self._saved_map_data:
                self._saved_map_data[map_data.map_id].cleanset = copy.deepcopy(
                    map_data.cleanset)
            self._set_updated_frame_id(map_data.frame_id + 1)
            self.refresh_map()
            return self.cleanset(map_data)

    def set_segment_cleaning_times(self, segment_id: int, cleaning_times: int) -> list[list[int]] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
            and not map_data.temporary_map
        ):
            map_data.segments[segment_id].cleaning_times = cleaning_times
            map_data.cleanset[str(segment_id)][2] = cleaning_times
            if self._saved_map_data and map_data.map_id in self._saved_map_data:
                self._saved_map_data[map_data.map_id].cleanset = copy.deepcopy(
                    map_data.cleanset)
            self._set_updated_frame_id(map_data.frame_id + 1)
            self.refresh_map()
            return self.cleanset(map_data)

    def set_segment_cleaning_mode(self, segment_id: int, cleaning_mode: int) -> list[list[int]] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
            and not map_data.temporary_map
        ):
            map_data.segments[segment_id].cleaning_mode = cleaning_mode
            map_data.cleanset[str(segment_id)][4] = cleaning_mode
            if self._saved_map_data and map_data.map_id in self._saved_map_data:
                self._saved_map_data[map_data.map_id].cleanset = copy.deepcopy(
                    map_data.cleanset)
            self._set_updated_frame_id(map_data.frame_id + 1)
            self.refresh_map()
            return self.cleanset(map_data)

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
                    map_data.segments[segment_id].index = map_data.segments[
                        segment_id
                    ].next_type_index(segment_type, map_data.segments)

                map_data.segments[segment_id].set_name()

                self._saved_map_data[self._selected_map_id].segments[
                    segment_id
                ].custom_name = map_data.segments[segment_id].custom_name
                self._saved_map_data[self._selected_map_id].segments[
                    segment_id
                ].index = map_data.segments[segment_id].index
                self._saved_map_data[self._selected_map_id].segments[
                    segment_id
                ].type = map_data.segments[segment_id].type
                self._saved_map_data[self._selected_map_id].segments[
                    segment_id
                ].set_name()
                self.refresh_map(self._selected_map_id)

                for (k, v) in map_data.segments.items():
                    if map_data.segments[k].custom_name is not None:
                        segment_info[k] = {MAP_PARAMETER_NAME: base64.b64encode(
                            map_data.segments[k].custom_name.encode("utf-8")
                        ).decode("utf-8"), MAP_REQUEST_PARAMETER_TYPE: 0, MAP_REQUEST_PARAMETER_INDEX: 0}
                    elif map_data.segments[k].type:
                        segment_info[k] = {MAP_REQUEST_PARAMETER_TYPE: map_data.segments[k].type,
                                           MAP_REQUEST_PARAMETER_INDEX: map_data.segments[k].index}
                    else:
                        segment_info[k] = {}

                    if map_data.segments[k].unique_id:
                        segment_info[k][MAP_REQUEST_PARAMETER_ROOM_ID] = map_data.segments[k].unique_id

                self._set_updated_frame_id(map_data.frame_id + 1)
                self.refresh_map()
                return segment_info

    def set_zones(self, walls, no_go_areas, no_mopping_areas) -> None:
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

        if walls:
            map_data.walls = [
                Wall(
                    wall[0],
                    wall[1],
                    wall[2],
                    wall[3],
                )
                for wall in walls
            ]
        else:
            map_data.walls = []

        self._saved_map_data[
            self._selected_map_id
        ].no_go_areas = map_data.no_go_areas
        self._saved_map_data[
            self._selected_map_id
        ].no_mopping_areas = map_data.no_mopping_areas
        self._saved_map_data[self._selected_map_id].walls = map_data.walls
        self._set_updated_frame_id(map_data.frame_id + 1)
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
        return int.from_bytes(data[offset: offset + 1], byteorder="big", signed=True)

    @staticmethod
    def _read_int_8_le(data: bytes, offset: int = 0) -> int:
        return int.from_bytes(
            data[offset: offset + 1], byteorder="little", signed=True
        )

    @staticmethod
    def _read_int_16(data: bytes, offset: int = 0) -> int:
        return int.from_bytes(data[offset: offset + 2], byteorder="big", signed=True)

    @staticmethod
    def _read_int_16_le(data: bytes, offset: int = 0) -> int:
        return int.from_bytes(
            data[offset: offset + 2], byteorder="little", signed=True
        )

    @staticmethod
    def _compare_segment_neighbors(r1: Segment, r2: Segment) -> bool:
        alen = 0
        blen = 0
        if r1.neighbors:
            alen = len(r1.neighbors)
        if r2.neighbors:
            blen = len(r2.neighbors)

        if alen == blen:
            return r1.segment_id - r2.segment_id

        return blen - alen

    @staticmethod
    def _compare_colors(c1: list[int], c2: list[int]) -> bool:
        return c1[1] - c2[1] if c1[1] != c2[1] else c1[0] - c2[0]

    @staticmethod
    def _get_pixel_type(map_data: MapData, pixel, vslam_map: bool = False) -> MapPixelType:
        if map_data.frame_map:
            segment_id = pixel >> 2

            if 0 < segment_id < 64:
                if segment_id == 63:
                    return MapPixelType.WALL.value
                if segment_id == 62:
                    return MapPixelType.FLOOR.value
                if segment_id == 61:
                    return MapPixelType.UNKNOWN.value
                return segment_id

            segment_id = pixel & 0x3f
            # as implemented on the app
            if segment_id == 1 or segment_id == 3:
                return MapPixelType.NEW_SEGMENT.value
            if segment_id == 2:
                return MapPixelType.WALL.value
        elif vslam_map:
            segment_id = pixel & 0b01111111
            if segment_id == 1:
                return MapPixelType.NEW_SEGMENT.value
            elif segment_id == 3:
                return MapPixelType.NEW_SEGMENT_UNKNOWN.value
            elif segment_id == 2:         
                return MapPixelType.WALL.value
        else:
            if pixel >> 7:
                return MapPixelType.WALL.value

            segment_id = pixel & 0x3f
            if segment_id > 0:
                if map_data.saved_map_status == 1 or map_data.saved_map_status == 0:
                    # as implemented on the app
                    if segment_id == 1 or segment_id == 3:
                        return MapPixelType.NEW_SEGMENT.value
                    if segment_id == 2:
                        return MapPixelType.WALL.value
                    return MapPixelType.OUTSIDE.value

                return segment_id

        return MapPixelType.OUTSIDE.value

    @staticmethod
    def _get_segment_center(map_data, segment_id: int, center: int, vertical: bool) -> int | None:
        # Find center point implemented as on the app
        lines = []
        zero_pixels = -1
        segment_pixel = 0
        line = None

        for k in range(
            map_data.dimensions.height if vertical else map_data.dimensions.width
        ):
            pixel_type = (
                map_data.data[
                    (k * map_data.dimensions.width + center)
                    if vertical
                    else (center * map_data.dimensions.width + k)
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
    def decode_map_partial(raw_map, iv=None, key=None) -> MapDataPartial | None:
        _LOGGER.debug("raw_map: %s", raw_map)
        raw_map = raw_map.replace("_", "/").replace("-", "+")

        if "," in raw_map and key is None:
            values = raw_map.split(",")
            key = values[1]
            raw_map = values[0]

        raw_map = base64.decodebytes(raw_map.encode("utf8"))

        if key is not None:
            if iv is None:
                iv = ""
            try:
                key = hashlib.sha256(key.encode()).hexdigest()[
                    0:32].encode('utf8')
                cipher = Cipher(algorithms.AES(key), modes.CBC(
                    iv.encode("utf8")), backend=default_backend())
                decryptor = cipher.decryptor()
                raw_map = decryptor.update(raw_map) + decryptor.finalize()
            except Exception as ex:
                _LOGGER.error(f"Map data decryption failed: {ex}. Private key might be missing, please report this issue with your device model https://github.com/Tasshack/dreame-vacuum/issues/new?assignees=Tasshack&labels=bug&template=bug_report.md&title=Map%20data%20decryption%20failed")
                return None

        try:
            raw_map = zlib.decompress(raw_map)
            if not raw_map or len(raw_map) < DreameVacuumMapDecoder.HEADER_SIZE:
                _LOGGER.error("Wrong header size for map")
                return None
        except Exception as ex:
            _LOGGER.error("Map data decompression failed: %s", ex)
            return None

        partial_map = MapDataPartial()
        partial_map.map_id = DreameVacuumMapDecoder._read_int_16_le(raw_map)
        partial_map.frame_id = DreameVacuumMapDecoder._read_int_16_le(
            raw_map, 2)
        partial_map.frame_type = DreameVacuumMapDecoder._read_int_8(raw_map, 4)
        partial_map.raw = raw_map
        image_size = DreameVacuumMapDecoder.HEADER_SIZE + (
            DreameVacuumMapDecoder._read_int_16_le(raw_map, 19)
            * DreameVacuumMapDecoder._read_int_16_le(raw_map, 21)
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
    def decode_map(raw_map: str, vslam_map: bool, rotation: int = 0, iv: str = None, key: str = None) -> Tuple[MapData, Optional[MapData]]:
        return DreameVacuumMapDecoder.decode_map_data_from_partial(
            DreameVacuumMapDecoder.decode_map_partial(raw_map, iv, key), vslam_map, rotation
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
        map_data.dimensions = MapImageDimensions(
            top, left, height, width, grid_size)
        data_json = partial_map.data_json
        if data_json is None:
            data_json = {}

        _LOGGER.debug("Map Data Json: %s", data_json)

        map_data.rotation = rotation
        if "mra" in data_json:
            map_data.rotation = int(data_json["mra"])

        if "robot_mode" in data_json:
            map_data.robot_mode = int(data_json["robot_mode"])

        if "map_used_times" in data_json:
            map_data.used_times = int(data_json["map_used_times"])

        if "cs" in data_json:
            map_data.cleaned_area = int(data_json["cs"])

        map_data.docked = bool(data_json.get("oc") and data_json["oc"])

        map_data.l2r = bool(data_json.get("l2r") and data_json["l2r"])
        map_data.frame_map = bool(data_json.get(
            "fsm") and data_json["fsm"] == 1)
        map_data.restored_map = bool(
            data_json.get("rpur") and data_json["rpur"] == 1)
        map_data.saved_map_status = -1
        if "ris" in data_json:
            map_data.saved_map_status = data_json["ris"]
        map_data.clean_log = bool(
            data_json.get("iscleanlog") and data_json["iscleanlog"] == True
        )
        map_data.recovery_map = bool(
            data_json.get("us") and data_json["us"] == 1)
        map_data.new_map = bool("risp" in data_json and data_json["risp"] == 0)

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

        if (
            data_json.get("nc") and data_json["nc"]
        ) or map_data.charger_position.a == 32767:
            map_data.charger_position = None

        if (
            (data_json.get("nr") and data_json["nr"])
            or map_data.robot_position.a == 32767
        ):
            map_data.robot_position = None

        if not map_data.saved_map and not map_data.recovery_map:
            map_data.index = 0

        if data_json.get("tr"):
            matches = [
                m.groupdict()
                for m in re.compile(
                    r"(?P<operator>[MWSLl])(?P<x>-?\d+),(?P<y>-?\d+)"
                ).finditer(data_json["tr"])
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
                        PathType.LINE
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

        if "ai_obstacle" in data_json:
            map_data.obstacles = []
            for obstacle in data_json["ai_obstacle"]:
                if len(obstacle) >= 4:
                    obstacle_type = int(obstacle[2])
                    if obstacle_type in ObstacleType._value2member_map_:
                        if len(obstacle) >= 7 and int(obstacle[4]) >= 1000:
                            map_data.obstacles.append(Obstacle(float(obstacle[0]), float(obstacle[1]), ObstacleType(
                                obstacle_type), int(float(obstacle[3]) * 100), obstacle[4], obstacle[5], obstacle[6]))
                        else:
                            map_data.obstacles.append(Obstacle(float(obstacle[0]), float(
                                obstacle[1]), ObstacleType(obstacle_type), int(float(obstacle[3]) * 100)))

        map_data.empty_map = map_data.frame_type == MapFrameType.I.value
        if (width * height) > 0:
            map_data.data = raw[DreameVacuumMapDecoder.HEADER_SIZE:image_size]
            map_data.empty_map = bool(width == 2 and height == 2)
            if map_data.empty_map:
                for y in range(height):
                    for x in range(width):
                        if map_data.data[(width * y) + x] > 0:
                            map_data.empty_map = False
                            break

            map_data.pixel_type = np.full(
                (width, height), MapPixelType.OUTSIDE.value, dtype=np.uint8)
            if not map_data.empty_map:
                if map_data.frame_type == MapFrameType.I.value:
                    if map_data.frame_map:
                        for y in range(height):
                            for x in range(width):
                                pixel = map_data.data[(width * y) + x]
                                if pixel > 0:
                                    map_data.empty_map = False
                                    segment_id = pixel >> 2
                                    if 0 < segment_id < 64:
                                        if segment_id == 63:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.WALL.value
                                        elif segment_id == 62:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.FLOOR.value
                                        elif segment_id == 61:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.UNKNOWN.value
                                        else:
                                            map_data.pixel_type[x,
                                                                y] = segment_id
                                    else:
                                        segment_id = pixel & 0x3f
                                        if segment_id == 1 or segment_id == 3:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.NEW_SEGMENT.value
                                        elif segment_id == 2:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.WALL.value
                    elif (
                        map_data.saved_map_status == 1
                        or map_data.saved_map_status == 0
                    ):
                        for y in range(height):
                            for x in range(width):
                                segment_id = map_data.data[(
                                    width * y) + x] & 0x3f
                                # as implemented on the app
                                if segment_id == 1 or segment_id == 3:
                                    map_data.empty_map = False
                                    map_data.pixel_type[x,
                                                        y] = MapPixelType.NEW_SEGMENT.value
                                elif segment_id == 2:
                                    map_data.empty_map = False
                                    map_data.pixel_type[x,
                                                        y] = MapPixelType.WALL.value
                    elif vslam_map and not map_data.saved_map:
                        for y in range(height):
                            for x in range(width):
                                segment_id = map_data.data[(width * y) + x] & 0b00000011
                                if segment_id == 1:
                                    map_data.empty_map = False
                                    map_data.pixel_type[x,
                                                        y] = MapPixelType.NEW_SEGMENT.value
                                elif segment_id == 3:
                                    map_data.empty_map = False
                                    map_data.pixel_type[x,
                                                        y] = MapPixelType.NEW_SEGMENT_UNKNOWN.value
                                elif segment_id == 2:                                        
                                    map_data.empty_map = False
                                    map_data.pixel_type[x,
                                                        y] = MapPixelType.WALL.value
                    else:
                        for y in range(height):
                            for x in range(width):
                                pixel = map_data.data[(width * y) + x]
                                if pixel > 0:
                                    map_data.empty_map = False
                                    if pixel >> 7:
                                        map_data.pixel_type[x,
                                                            y] = MapPixelType.WALL.value
                                    else:
                                        segment_id = pixel & 0x3f
                                        if segment_id > 0:
                                            map_data.pixel_type[x,
                                                                y] = segment_id

                    segments = DreameVacuumMapDecoder.get_segments(map_data, vslam_map)
                    if segments and data_json.get("seg_inf"):
                        seg_inf = data_json["seg_inf"]
                        for (k, v) in segments.items():
                            if seg_inf.get(str(k)):
                                segment_info = seg_inf[str(k)]
                                if segment_info.get("nei_id"):
                                    segments[k].neighbors = segment_info["nei_id"]
                                if segment_info.get("type"):
                                    segments[k].type = segment_info["type"]
                                if segment_info.get("index"):
                                    segments[k].index = segment_info["index"]
                                if segment_info.get("roomID"):
                                    segments[k].unique_id = segment_info["roomID"]
                                if segment_info.get(MAP_PARAMETER_NAME):
                                    segments[k].custom_name = base64.b64decode(
                                        segment_info.get(MAP_PARAMETER_NAME)
                                    ).decode("utf-8")
                                segments[k].set_name()

                    map_data.segments = segments

        saved_map_data = None
        restored_map = map_data.restored_map

        if data_json.get("rism"):
            saved_map_data = DreameVacuumMapDecoder.decode_saved_map(
                data_json["rism"],
                vslam_map,
                map_data.rotation,
            )

            if saved_map_data is not None:
                saved_map_data.timestamp_ms = map_data.timestamp_ms
                map_data.saved_map_id = saved_map_data.map_id
                if saved_map_data.temporary_map:
                    map_data.temporary_map = saved_map_data.temporary_map

                if restored_map or map_data.recovery_map or (map_data.saved_map_status == 2 and map_data.empty_map):
                    map_data.segments = copy.deepcopy(saved_map_data.segments)
                    map_data.data = saved_map_data.data
                    map_data.pixel_type = saved_map_data.pixel_type
                    map_data.dimensions = saved_map_data.dimensions
                    
                    if map_data.empty_map:
                        map_data.restored_map = False
                        restored_map = True
                        map_data.empty_map = False
                else:
                    if saved_map_data.segments is not None:
                        if map_data.segments is None and (
                            map_data.saved_map_status == 1
                            or map_data.saved_map_status == 0
                        ):
                            map_data.segments = {}

                        for (k, v) in saved_map_data.segments.items():
                            if map_data.segments and k in map_data.segments:
                                # as implemented on the app
                                map_data.segments[k].icon = v.icon
                                map_data.segments[k].name = v.name
                                map_data.segments[k].custom_name = v.custom_name
                                map_data.segments[k].type = v.type
                                map_data.segments[k].index = v.index
                                map_data.segments[k].unique_id = v.unique_id
                                map_data.segments[k].neighbors = v.neighbors
                                if map_data.saved_map_status == 2:
                                    map_data.segments[k].x = v.x
                                    map_data.segments[k].y = v.y

                if not saved_map_data.cleanset:
                    saved_map_data.cleanset = copy.deepcopy(map_data.cleanset)

                if (
                    (map_data.saved_map_status == 2 or map_data.docked)
                    and map_data.charger_position is None
                    and not map_data.saved_map
                    and saved_map_data.charger_position
                ):
                    map_data.charger_position = saved_map_data.charger_position

                if map_data.saved_map_status == 2:
                    map_data.no_go_areas = saved_map_data.no_go_areas
                    map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                    map_data.walls = saved_map_data.walls

                    if vslam_map:
                        map_data.segments = copy.deepcopy(saved_map_data.segments)
                        map_data.charger_position = copy.deepcopy(saved_map_data.charger_position)

        if (
            not map_data.saved_map
            and map_data.robot_position is None
            and map_data.docked
            and map_data.charger_position
        ):
            map_data.robot_position = copy.deepcopy(map_data.charger_position)

        if map_data.segments:
            if not map_data.saved_map:
                DreameVacuumMapDecoder.set_segment_cleanset(
                    map_data, map_data.cleanset)
                DreameVacuumMapDecoder.set_robot_segment(map_data)
                
            if map_data.saved_map_status == 2 or map_data.saved_map:
                DreameVacuumMapDecoder.set_segment_color_index(map_data)

        if data_json.get("vw"):
            if data_json["vw"].get("rect") and not map_data.no_go_areas:
                    map_data.no_go_areas = []
                    for area in data_json["vw"]["rect"]:
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

            if data_json["vw"].get("mop") and not map_data.no_mopping_areas:
                map_data.no_mopping_areas = []
                for area in data_json["vw"]["mop"]:
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

            if data_json["vw"].get("line") and not map_data.walls:
                map_data.walls = [
                    Wall(
                        virtual_wall[0],
                        virtual_wall[1],
                        virtual_wall[2],
                        virtual_wall[3],
                    )
                    for virtual_wall in data_json["vw"]["line"]
                ]

        if vslam_map and not map_data.saved_map:
            map_data.need_optimization = not restored_map

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
        current_map_data.temporary_map = map_data.temporary_map
        current_map_data.saved_map = False
        current_map_data.empty_map = False
        current_map_data.restored_map = False
        current_map_data.recovery_map = False
        current_map_data.clean_log = False

        if map_data.charger_position is not None and (not vslam_map or current_map_data.saved_map_status != 2):
            current_map_data.charger_position = map_data.charger_position

        if map_data.obstacles is not None:
            current_map_data.obstacles = map_data.obstacles

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
                current_dimensions.left
                + (current_dimensions.width * current_dimensions.grid_size),
            )
            max_top = max(
                new_dimensions.top + (new_dimensions.height * grid_size),
                current_dimensions.top
                + (current_dimensions.height * current_dimensions.grid_size),
            )

            # Calculate new image size
            width = int((max_left - left) / grid_size)
            height = int((max_top - top) / grid_size)

            # Create new buffer
            data = np.zeros((width * height), np.uint8)
            pixel_type = np.full(
                (width, height), MapPixelType.OUTSIDE.value, dtype=np.uint8)

            # Calculate old image offset
            left_offset = int(
                (current_dimensions.left - left) / current_dimensions.grid_size
            )
            top_offset = int(
                (current_dimensions.top - top) / current_dimensions.grid_size
            )

            # Copy old image to buffer
            for y in range(current_dimensions.height):
                for x in range(current_dimensions.width):
                    data[
                        (width * (top_offset + y)) + left_offset + x
                    ] = current_map_data.data[(current_dimensions.width * y) + x]
                    pixel_type[
                        left_offset + x, top_offset + y
                    ] = current_map_data.pixel_type[x, y]

            # Calculate new image offset
            left_offset = int((new_dimensions.left - left) / grid_size)
            top_offset = int((new_dimensions.top - top) / grid_size)

            # Copy new image to buffer at calculated offset
            for y in range(new_dimensions.height):
                for x in range(new_dimensions.width):
                    current_index = (new_dimensions.width * y) + x
                    if map_data.data[current_index]:
                        new_index = (width * (top_offset + y)) + \
                            left_offset + x
                        # Add current buffer value to new buffer value for finding the new pixel value
                        data[new_index] = data[new_index] + \
                            map_data.data[current_index]
                        # Calculate the new pixel type from updated buffer value
                        pixel_type[
                            left_offset + x, top_offset + y
                        ] = DreameVacuumMapDecoder._get_pixel_type(
                            current_map_data, int(data[new_index]), vslam_map,
                        )

            # Update size and buffer
            current_map_data.data = bytes(data)
            current_map_data.pixel_type = pixel_type
            current_map_data.dimensions = MapImageDimensions(
                top, left, height, width, grid_size
            )

            if vslam_map:
                current_map_data.need_optimization = True

        if map_data.path:
            # Append new paths received with P frame
            if current_map_data.path:
                current_map_data.path.extend(map_data.path)
            else:
                current_map_data.path = map_data.path

        DreameVacuumMapDecoder.set_robot_segment(current_map_data)

        # if robotPos.l2r == True and self._robotPos.l2r == True:
        #    self._lastPos = self._robotPos
        # else:
        #    self._lastPos = None
        return current_map_data

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

                    if x < segments[segment_id].x0:
                        segments[segment_id].x0 = x
                    elif x > segments[segment_id].x1:
                        segments[segment_id].x1 = x

                    if y < segments[segment_id].y0:
                        segments[segment_id].y0 = y
                    elif y > segments[segment_id].y1:
                        segments[segment_id].y1 = y

        if segments:
            for (k, v) in segments.items():
                x = int(math.ceil((v.x1 - v.x0) / 2 + v.x0))
                y = int(math.ceil((v.y1 - v.y0) / 2 + v.y0))

                if map_data.saved_map:                
                    if vslam_map:
                        if map_data.pixel_type[x, y] != k:
                            startI = -1
                            endI = -1
                            for i in range(map_data.dimensions.width):
                                value = map_data.pixel_type[i, y]
                                if startI == -1:
                                    if value == k:
                                        startI = i
                                elif value != k or i == (map_data.dimensions.width - 1):
                                    endI = (i - 1)
                                    break

                            if startI != -1 and endI != -1:
                                x = (endI - startI) + startI
                    else:
                        center_x = DreameVacuumMapDecoder._get_segment_center(
                            map_data, k, y, False
                        )
                        if center_x is not None:
                            center_y = DreameVacuumMapDecoder._get_segment_center(
                                map_data, k, center_x, True
                            )
                            if center_y is not None:
                                x = center_x
                                y = center_y

                segments[k].x0 = (
                    int(
                        map_data.dimensions.left
                        + (v.x0 * map_data.dimensions.grid_size)
                    )
                )
                segments[k].y0 = (
                    int(
                        map_data.dimensions.top +
                        (v.y0 * map_data.dimensions.grid_size)
                        - map_data.dimensions.grid_size
                    )
                )
                segments[k].x1 = (
                    int(
                        map_data.dimensions.left
                        + (v.x1 * map_data.dimensions.grid_size)
                        + map_data.dimensions.grid_size
                    )
                )
                segments[k].y1 = (
                    int(
                        map_data.dimensions.top +
                        (v.y1 * map_data.dimensions.grid_size)
                    )
                )
                segments[k].x = int(
                    map_data.dimensions.left +
                    (x * map_data.dimensions.grid_size)
                )
                segments[k].y = int(
                    map_data.dimensions.top +
                    (y * map_data.dimensions.grid_size)
                )
                segments[k].set_name()
        return segments

    @staticmethod
    def set_robot_segment(map_data: MapData) -> None:
        if (
            map_data.segments and
            map_data.saved_map_status == 2
            and map_data.robot_position is not None
        ):
            map_data.robot_segment = map_data.pixel_type[
                int((map_data.robot_position.x - map_data.dimensions.left) /
                    map_data.dimensions.grid_size),
                int((map_data.robot_position.y - map_data.dimensions.top) /
                    map_data.dimensions.grid_size),
            ]
            if map_data.robot_segment not in map_data.segments:
                map_data.robot_segment = 0
        else:
            map_data.robot_segment = None

    @staticmethod
    def set_segment_cleanset(map_data: MapData, cleanset: dict[str, list[int]]) -> None:
        if map_data is not None and map_data.segments is not None:
            for (k, v) in map_data.segments.items():
                if cleanset is not None:
                    segment_id = str(k)
                    if segment_id not in cleanset:
                        cleanset[segment_id] = [
                            1,
                            3,
                            1,
                            0,
                        ]  # Cleanset returns empty on restored map but robot uses these default values when that happens
                        if map_data.segments[k].cleaning_mode is not None:
                            cleanset[segment_id].append(2)

                    item = cleanset[segment_id]

                    map_data.segments[k].suction_level = item[0]
                    map_data.segments[k].water_volume = (
                        item[1] - 1
                    )  # for some reason cleanset uses different int values for water volume
                    map_data.segments[k].cleaning_times = item[2]
                    map_data.segments[k].order = item[3]
                    map_data.segments[k].cleaning_mode = item[4] if len(
                        item) > 4 else None
                else:
                    map_data.segments[k].suction_level = None
                    map_data.segments[k].water_volume = None
                    map_data.segments[k].cleaning_times = None
                    map_data.segments[k].order = None
                    map_data.segments[k].cleaning_mode = None

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

            for (i, j) in area_color_index.items():
                area_color_num[j][1] = area_color_num[j][1] + 1

            area_color_num = sorted(
                area_color_num.values(),
                key=cmp_to_key(DreameVacuumMapDecoder._compare_colors),
            )

            for area_color in area_color_num:
                color = area_color[0]
                if color not in used_ids:
                    area_color_index[segment.segment_id] = color
                    break

            if segment.segment_id not in area_color_index:
                area_color_index[segment.segment_id] = 0

        for i in area_color_index:
            map_data.segments[i].color_index = area_color_index[i]


class DreameVacuumMapDataRenderer:
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
        self._default_map_image = Image.open(
            BytesIO(base64.b64decode(DEFAULT_MAP_DATA_IMAGE))
        ).convert("RGBA")

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
            round((x + DreameVacuumMapDataRenderer.HALF_INT16) / 10),
            DreameVacuumMapDataRenderer.MAX
            - round((y + DreameVacuumMapDataRenderer.HALF_INT16) / 10),
        ]

    @staticmethod
    def _convert_angle(angle: int) -> int:
        return (((180 - angle) if (angle < 180) else (360 - angle + 180)) + 270) % 360

    @staticmethod
    def _to_buffer(image, extra_data: str) -> bytes:
        buffer = io.BytesIO()
        info = PngImagePlugin.PngInfo()
        info.add_text("ValetudoMap", extra_data, zip=True)
        image.save(buffer, format="PNG", pnginfo=info)
        return buffer.getvalue()

    def render_map(self, map_data: MapData, robot_status: int = 0) -> bytes:
        if map_data is None or map_data.empty_map:
            return self.default_map_image

        if (
            self._map_data
            and self._map_data == map_data
            and self._map_data.segments == map_data.segments
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
            self._left = round(
                (map_data.dimensions.left +
                 DreameVacuumMapDataRenderer.HALF_INT16) / 10
            )
            self._top = round(
                (map_data.dimensions.top + DreameVacuumMapDataRenderer.HALF_INT16) / 10
            )
            self._grid_size = round(map_data.dimensions.grid_size / 10)

        map_data_json = {
            MAP_DATA_PARAMETER_CLASS: "ValetudoMap",
            MAP_DATA_PARAMETER_SIZE: {
                MAP_DATA_PARAMETER_X: DreameVacuumMapDataRenderer.MAX,
                MAP_DATA_PARAMETER_Y: DreameVacuumMapDataRenderer.MAX,
            },
            MAP_DATA_PARAMETER_PIXEL_SIZE: self._grid_size,
            MAP_DATA_PARAMETER_LAYERS: [],
            MAP_DATA_PARAMETER_ENTITIES: [],
            MAP_DATA_PARAMETER_META_DATA: {MAP_DATA_PARAMETER_VERSION: 2, MAP_DATA_PARAMETER_ROTATION: map_data.rotation},
        }

        if map_data.robot_position:
            if (
                self._map_data is None
                or self._map_data.robot_position != map_data.robot_position
                or not self._layers.get(MapRendererLayer.ROBOT)
            ):
                self._layers[MapRendererLayer.ROBOT] = {
                    MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_ROBOT_POSITION,
                    MAP_DATA_PARAMETER_POINTS: DreameVacuumMapDataRenderer._convert_coordinates(
                        map_data.robot_position.x, map_data.robot_position.y
                    ),
                    MAP_DATA_PARAMETER_META_DATA: {
                        MAP_PARAMETER_ANGLE: DreameVacuumMapDataRenderer._convert_angle(
                            map_data.robot_position.a
                        )
                    },
                }
            map_data_json[MAP_DATA_PARAMETER_ENTITIES].append(
                self._layers[MapRendererLayer.ROBOT])

        if map_data.charger_position:
            if (
                self._map_data is None
                or self._map_data.charger_position != map_data.charger_position
                or not self._layers.get(MapRendererLayer.CHARGER)
            ):
                self._layers[MapRendererLayer.CHARGER] = {
                    MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_CHARGER_POSITION,
                    MAP_DATA_PARAMETER_POINTS: DreameVacuumMapDataRenderer._convert_coordinates(
                        map_data.charger_position.x, map_data.charger_position.y
                    ),
                    MAP_DATA_PARAMETER_META_DATA: {
                        MAP_PARAMETER_ANGLE: DreameVacuumMapDataRenderer._convert_angle(
                            map_data.charger_position.a
                        )
                    },
                }
            map_data_json[MAP_DATA_PARAMETER_ENTITIES].append(
                self._layers[MapRendererLayer.CHARGER])

        if map_data.no_mopping_areas:
            if (
                self._map_data is None
                or self._map_data.no_mopping_areas != map_data.no_mopping_areas
                or not self._layers.get(MapRendererLayer.NO_MOP)
            ):
                self._layers[MapRendererLayer.NO_MOP] = []
                for area in map_data.no_mopping_areas:
                    a = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x0, area.y0
                    )
                    b = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x1, area.y1
                    )
                    c = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x2, area.y2
                    )
                    d = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x3, area.y3
                    )
                    self._layers[MapRendererLayer.NO_MOP].append(
                        {
                            MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_NO_MOP_AREA,
                            MAP_DATA_PARAMETER_POINTS: [a[0], a[1], b[0], b[1], c[0], c[1], d[0], d[1]],
                        }
                    )
            map_data_json[MAP_DATA_PARAMETER_ENTITIES].extend(
                self._layers[MapRendererLayer.NO_MOP])

        if map_data.no_go_areas:
            if (
                self._map_data is None
                or self._map_data.no_go_areas != map_data.no_go_areas
                or not self._layers.get(MapRendererLayer.NO_GO)
            ):
                self._layers[MapRendererLayer.NO_GO] = []
                for area in map_data.no_go_areas:
                    a = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x0, area.y0
                    )
                    b = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x1, area.y1
                    )
                    c = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x2, area.y2
                    )
                    d = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x3, area.y3
                    )

                    self._layers[MapRendererLayer.NO_GO].append(
                        {
                            MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_NO_GO_AREA,
                            MAP_DATA_PARAMETER_POINTS: [a[0], a[1], b[0], b[1], c[0], c[1], d[0], d[1]],
                        }
                    )
            map_data_json[MAP_DATA_PARAMETER_ENTITIES].extend(
                self._layers[MapRendererLayer.NO_GO])

        if map_data.active_areas:
            if (
                self._map_data is None
                or self._map_data.active_areas != map_data.active_areas
                or not self._layers.get(MapRendererLayer.ACTIVE_AREA)
            ):
                self._layers[MapRendererLayer.ACTIVE_AREA] = []
                for area in map_data.active_areas:
                    a = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x0, area.y0
                    )
                    b = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x1, area.y1
                    )
                    c = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x2, area.y2
                    )
                    d = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x3, area.y3
                    )

                    self._layers[MapRendererLayer.ACTIVE_AREA].append(
                        {
                            MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_ACTIVE_ZONE,
                            MAP_DATA_PARAMETER_POINTS: [a[0], a[1], b[0], b[1], c[0], c[1], d[0], d[1]],
                        }
                    )
            map_data_json[MAP_DATA_PARAMETER_ENTITIES].extend(
                self._layers[MapRendererLayer.ACTIVE_AREA])

        if map_data.active_points:
            if (
                self._map_data is None
                or self._map_data.active_points != map_data.active_points
                or not self._layers.get(MapRendererLayer.ACTIVE_POINT)
            ):
                self._layers[MapRendererLayer.ACTIVE_POINT] = []
                size = 15 * map_data.dimensions.grid_size
                for point in map_data.active_points:
                    area = Area(point.x - size, point.y - size, point.x + size, point.y -
                                size, point.x + size, point.y + size, point.x - size, point.y + size)

                    a = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x0, area.y0
                    )
                    b = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x1, area.y1
                    )
                    c = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x2, area.y2
                    )
                    d = DreameVacuumMapDataRenderer._convert_coordinates(
                        area.x3, area.y3
                    )

                    self._layers[MapRendererLayer.ACTIVE_POINT].append(
                        {
                            MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_ACTIVE_ZONE,
                            MAP_DATA_PARAMETER_POINTS: [a[0], a[1], b[0], b[1], c[0], c[1], d[0], d[1]],
                        }
                    )
            map_data_json[MAP_DATA_PARAMETER_ENTITIES].extend(
                self._layers[MapRendererLayer.ACTIVE_POINT])

        if map_data.walls:
            if self._map_data is None or self._map_data.walls != map_data.walls or not self._layers.get(MapRendererLayer.WALL):
                self._layers[MapRendererLayer.WALL] = []
                for wall in map_data.walls:
                    a = DreameVacuumMapDataRenderer._convert_coordinates(
                        wall.x0, wall.y0
                    )
                    b = DreameVacuumMapDataRenderer._convert_coordinates(
                        wall.x1, wall.y1
                    )

                    self._layers[MapRendererLayer.WALL].append(
                        {
                            MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_VIRTUAL_WALL,
                            MAP_DATA_PARAMETER_POINTS: [a[0], a[1], b[0], b[1]],
                        }
                    )
            map_data_json[MAP_DATA_PARAMETER_ENTITIES].extend(
                self._layers[MapRendererLayer.WALL])

        if self._map_data is None or len(self._map_data.path) != len(map_data.path) or not self._layers.get(MapRendererLayer.PATH):
            points = []
            self._layers[MapRendererLayer.PATH] = []
            if map_data.path and len(map_data.path) > 1:
                s = map_data.path[0]
                for point in map_data.path[1:]:
                    if point.path_type == PathType.LINE:
                        point = point
                        a = DreameVacuumMapDataRenderer._convert_coordinates(
                            s.x, s.y)
                        b = DreameVacuumMapDataRenderer._convert_coordinates(
                            point.x, point.y
                        )

                        points.extend([a[0], a[1], b[0], b[1]])
                    else:
                        self._layers[MapRendererLayer.PATH].append(
                            {
                                MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_PATH,
                                MAP_DATA_PARAMETER_POINTS: points,
                            }
                        )
                        points = []
                    s = point
            self._layers[MapRendererLayer.PATH].append(
                {
                    MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_PATH,
                    MAP_DATA_PARAMETER_POINTS: points,
                }
            )
        map_data_json[MAP_DATA_PARAMETER_ENTITIES].extend(
            self._layers[MapRendererLayer.PATH])

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

                    coords[1] = (
                        DreameVacuumMapDataRenderer.MAX / self._grid_size
                    ) - coords[1]

                    coords[0] = round(coords[0])
                    coords[1] = round(coords[1])

                    if segment_id == MapPixelType.WALL.value:
                        wall_pixels.append(coords)
                    elif segment_id == MapPixelType.FLOOR.value or segment_id == MapPixelType.UNKNOWN.value:
                        floor_pixels.append(coords)
                    elif segment_id > 0 and segment_id < 61:
                        if (
                            map_data.active_segments
                            and segment_id not in map_data.active_segments
                        ):
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
                        MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_FLOOR,
                        MAP_DATA_PARAMETER_PIXELS: [
                            val
                            for sublist in sorted(
                                floor_pixels,
                                key=cmp_to_key(
                                    DreameVacuumMapDataRenderer._coordinate_tuple_sort
                                ),
                            )
                            for val in sublist
                        ],
                    }
                )

            if wall_pixels:
                self._layers[MapRendererLayer.IMAGE].append(
                    {
                        MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_WALL,
                        MAP_DATA_PARAMETER_PIXELS: [
                            val
                            for sublist in sorted(
                                wall_pixels,
                                key=cmp_to_key(
                                    DreameVacuumMapDataRenderer._coordinate_tuple_sort
                                ),
                            )
                            for val in sublist
                        ],
                    }
                )

            if segments:
                for (k, v) in segments.items():
                    name = None
                    if map_data.segments:
                        name = f"Room {k}"
                        if k in map_data.segments:
                            name = map_data.segments[k].name
                    self._layers[MapRendererLayer.IMAGE].append(
                        {
                            MAP_DATA_PARAMETER_TYPE: MAP_DATA_PARAMETER_SEGMENT,
                            MAP_DATA_PARAMETER_PIXELS: [
                                val
                                for sublist in sorted(
                                    v,
                                    key=cmp_to_key(
                                        DreameVacuumMapDataRenderer._coordinate_tuple_sort
                                    ),
                                )
                                for val in sublist
                            ],
                            MAP_DATA_PARAMETER_META_DATA: {
                                MAP_DATA_PARAMETER_SEGMENT_ID: k,
                                MAP_DATA_PARAMETER_ACTIVE: True
                                if map_data.active_segments
                                and k in map_data.active_segments
                                else False,
                                MAP_DATA_PARAMETER_NAME: name,
                            },
                        }
                    )

            for layers in self._layers[MapRendererLayer.IMAGE]:
                pixels = layers[MAP_DATA_PARAMETER_PIXELS]
                layers[MAP_DATA_PARAMETER_DIMENSIONS] = {
                    MAP_DATA_PARAMETER_X: {
                        MAP_DATA_PARAMETER_MIN: 65535,
                        MAP_DATA_PARAMETER_MAX: -65535,
                        MAP_DATA_PARAMETER_MID: None,
                        MAP_DATA_PARAMETER_AVG: None,
                    },
                    MAP_DATA_PARAMETER_Y: {
                        MAP_DATA_PARAMETER_MIN: 65535,
                        MAP_DATA_PARAMETER_MAX: -65535,
                        MAP_DATA_PARAMETER_MID: None,
                        MAP_DATA_PARAMETER_AVG: None,
                    },
                    MAP_DATA_PARAMETER_PIXEL_COUNT: len(pixels) / 2,
                }

                sum_x = 0
                sum_y = 0
                for i in range(0, len(pixels), 2):
                    sum_x = sum_x + pixels[i]
                    sum_y = sum_y + pixels[i + 1]

                    if pixels[i] < layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_MIN]:
                        layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_MIN] = pixels[i]

                    if pixels[i] > layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_MAX]:
                        layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_MAX] = pixels[i]

                    if pixels[i + 1] < layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_MIN]:
                        layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_MIN] = pixels[i + 1]

                    if pixels[i + 1] > layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_MAX]:
                        layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_MAX] = pixels[i + 1]

                layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_MID] = round(
                    (
                        layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_MAX]
                        + layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_MIN]
                    )
                    / 2
                )
                layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_MID] = round(
                    (
                        layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_MAX]
                        + layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_MIN]
                    )
                    / 2
                )

                if sum_x:
                    layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_X][MAP_DATA_PARAMETER_AVG] = round(
                        sum_x / (len(pixels) / 2))
                if sum_y:
                    layers[MAP_DATA_PARAMETER_DIMENSIONS][MAP_DATA_PARAMETER_Y][MAP_DATA_PARAMETER_AVG] = round(
                        sum_y / (len(pixels) / 2))

                current_x_start = -65535
                current_y = -65535
                current_count = 0
                compressed_pixels = []

                for i in range(0, len(pixels), 2):
                    x = pixels[i]
                    y = pixels[i + 1]

                    if y != current_y or x > (current_x_start + current_count):
                        compressed_pixels.extend(
                            [current_x_start, current_y, current_count]
                        )
                        current_x_start = x
                        current_y = y
                        current_count = 1
                    elif x != current_x_start:
                        current_count = current_count + 1

                compressed_pixels.extend(
                    [current_x_start, current_y, current_count])
                layers[MAP_DATA_PARAMETER_COMPRESSED_PIXELS] = compressed_pixels[3:]
                layers[MAP_DATA_PARAMETER_PIXELS] = []

        map_data_json[MAP_DATA_PARAMETER_LAYERS].extend(
            self._layers[MapRendererLayer.IMAGE])

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
        return self.default_map_image


class DreameVacuumMapRenderer:
    def __init__(self, color_scheme: str = None, icon_set: str = None, map_objects: list[str] = None, robot_shape: int = 0) -> None:
        self.color_scheme: MapRendererColorScheme = MAP_COLOR_SCHEME_LIST.get(
            color_scheme, MapRendererColorScheme())
        self.icon_set: int = MAP_ICON_SET_LIST.get(icon_set, 0)
        self.config: MapRendererConfig = MapRendererConfig()
        if map_objects is not None:
            for attr in self.config.__dict__.keys():
                if attr not in map_objects:
                    setattr(self.config, attr, False)

        self._map_data: MapData = None
        self.render_complete: bool = True
        self._layers: dict[MapRendererLayer, Any] = {}
        self._robot_status: int = None
        self._robot_shape: int = robot_shape
        self._calibration_points: dict[str, int] = None
        self._default_calibration_points: dict[str, int] = [
            {MAP_PARAMETER_VACUUM: {MAP_DATA_PARAMETER_X: 0, MAP_DATA_PARAMETER_Y: 0},
                MAP_PARAMETER_MAP: {MAP_DATA_PARAMETER_X: 0, MAP_DATA_PARAMETER_Y: 0}},
            {MAP_PARAMETER_VACUUM: {MAP_DATA_PARAMETER_X: 1000, MAP_DATA_PARAMETER_Y: 0},
                MAP_PARAMETER_MAP: {MAP_DATA_PARAMETER_X: 0, MAP_DATA_PARAMETER_Y: 0}},
            {MAP_PARAMETER_VACUUM: {MAP_DATA_PARAMETER_X: 0, MAP_DATA_PARAMETER_Y: 1000},
                MAP_PARAMETER_MAP: {MAP_DATA_PARAMETER_X: 0, MAP_DATA_PARAMETER_Y: 0}},
        ]

        self._image = None
        self._charger_icon = None
        self._robot_icon = None
        self._robot_charging_icon = None
        self._robot_cleaning_icon = None
        self._robot_warning_icon = None
        self._robot_sleeping_icon = None
        self._robot_washing_icon = None
        self._robot_cleaning_direction_icon = None
        self._obstacle_background = None

        default_map_image = Image.open(
            BytesIO(base64.b64decode(DEFAULT_MAP_IMAGE))
        ).convert("RGBA")
        self._default_map_image = ImageOps.expand(
            default_map_image.resize(
                (
                    int(default_map_image.size[0] * 0.8),
                    int(default_map_image.size[1] * 0.8),
                )
            ),
            border=(50, 75, 50, 75),
        )
        
        icon_set = SEGMENT_ICONS_DREAME
        repeats = MAP_ICON_REPEATS_DREAME
        suction_level = MAP_ICON_SUCTION_LEVEL_DREAME
        water_volume = MAP_ICON_WATER_VOLUME_DREAME
        cleaning_mode = MAP_ICON_CLEANING_MODE_DREAME

        self._segment_icons = {}
        if self.icon_set == 1:
            icon_set = SEGMENT_ICONS_DREAME_OLD
        elif self.icon_set == 2:
            icon_set = SEGMENT_ICONS_MIJIA
            repeats = MAP_ICON_REPEATS_MIJIA
            suction_level = MAP_ICON_SUCTION_LEVEL_MIJIA
            water_volume = MAP_ICON_WATER_VOLUME_MIJIA
            cleaning_mode = MAP_ICON_CLEANING_MODE_MIJIA
        elif self.icon_set == 3:
            icon_set = SEGMENT_ICONS_MATERIAL
            repeats = MAP_ICON_REPEATS_MATERIAL
            suction_level = MAP_ICON_SUCTION_LEVEL_MATERIAL
            water_volume = MAP_ICON_WATER_VOLUME_MATERIAL
            cleaning_mode = MAP_ICON_CLEANING_MODE_MATERIAL

        self._cleaning_times_icon = [Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in repeats]
        self._suction_level_icon = [Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in suction_level]
        self._water_volume_icon = [Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in water_volume]
        self._cleaning_mode_icon = [Image.open(BytesIO(base64.b64decode(icon))).convert("RGBA") for icon in cleaning_mode]

        for (k, v) in icon_set.items():
            self._segment_icons[k] = Image.open(BytesIO(base64.b64decode(v))).convert(
                "RGBA"
            )
            if self.color_scheme.invert:
                enhancer = ImageEnhance.Brightness(self._segment_icons[k])
                self._segment_icons[k] = enhancer.enhance(0.1)

        self._obstacle_icons = {}
        for (k, v) in OBSTACLE_TYPE_TO_ICON.items():
            self._obstacle_icons[k] = Image.open(BytesIO(base64.b64decode(v))).convert(
                "RGBA"
            )

        self.font_file = zlib.decompress(
            base64.b64decode(MAP_FONT), zlib.MAX_WBITS | 32)

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

            return [min_x, min_y, max_x, max_y]

    @staticmethod
    def _calculate_padding(dimensions, active_areas, no_mopping_areas, no_go_areas, walls, segments, padding, min_width, min_height, scale) -> list[int]:
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
    def _calculate_calibration_points(map_data: MapData) -> dict[str, int] | None:
        if (map_data.dimensions.width * map_data.dimensions.height) > 0:
            calibration_points = []
            for point in [Point(0, 0), Point(1000, 0), Point(0, 1000)]:
                img_point = point.to_img(map_data.dimensions).rotated(
                    map_data.dimensions, map_data.rotation
                )
                calibration_points.append(
                    {
                        MAP_PARAMETER_VACUUM: {MAP_DATA_PARAMETER_X: point.x, MAP_DATA_PARAMETER_Y: point.y},
                        MAP_PARAMETER_MAP: {MAP_DATA_PARAMETER_X: int(img_point.x), MAP_DATA_PARAMETER_Y: int(img_point.y)},
                    }
                )
            return calibration_points

    def render_map(self, map_data: MapData, robot_status: int = 0) -> bytes:
        if map_data is None or map_data.empty_map or (map_data.dimensions.width * map_data.dimensions.height) < 2:
            return self.default_map_image

        self.render_complete = False
        now = time.time()

        if map_data.saved_map:
            robot_status = 0
        try:
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
                and self._map_data.segments == map_data.segments
                and self._map_data.frame_id == map_data.frame_id
                and self._image 
            ):
                self.render_complete = True
                _LOGGER.info("Skip render frame, map data not changed")
                return self._to_buffer(self._image)

            scale = 4 if map_data.saved_map_status == 2 or map_data.saved_map else 3

            if not map_data.saved_map:
                if (
                    self._map_data is None
                    or self._map_data.segments != map_data.segments
                    or self._map_data.dimensions != map_data.dimensions
                ):
                    map_data.dimensions.bounds = DreameVacuumMapRenderer._calculate_bounds(
                        map_data.dimensions,
                        map_data.segments
                    )

                    if self._map_data and self._map_data.dimensions.bounds != map_data.dimensions.bounds:
                        self._map_data = None
                else:
                    map_data.dimensions.bounds = self._map_data.dimensions.bounds

            if (
                self._map_data is None
                or self._map_data.active_areas != map_data.active_areas
                or self._map_data.no_mopping_areas != map_data.no_mopping_areas
                or self._map_data.no_go_areas != map_data.no_go_areas
                or self._map_data.walls != map_data.walls
                or self._map_data.segments != map_data.segments
                or self._map_data.dimensions != map_data.dimensions
                or self._map_data.restored_map != map_data.restored_map
            ):
                map_data.dimensions.padding = DreameVacuumMapRenderer._calculate_padding(
                    map_data.dimensions,
                    map_data.active_areas,
                    map_data.no_mopping_areas,
                    map_data.no_go_areas,
                    map_data.walls,
                    map_data.segments,
                    [14, 14, 14, 14],
                    120,
                    80,
                    scale
                )

                if self._map_data and self._map_data.dimensions.padding != map_data.dimensions.padding:
                    self._map_data = None
            else:
                map_data.dimensions.padding = self._map_data.dimensions.padding

            map_data.dimensions.scale = scale
            
            if self._map_data and self._map_data.dimensions.scale != scale:
                self._map_data = None

            if self._map_data is None or self._map_data.rotation != map_data.rotation:
                self._charger_icon = None
                self._robot_sleeping_icon = None
                self._obstacle_background = None

                if (
                    self._map_data is None
                ):
                    self._robot_icon = None
                    self._robot_charging_icon = None
                    self._robot_cleaning_icon = None
                    self._robot_warning_icon = None
                    self._robot_washing_icon = None
                    self._robot_cleaning_direction_icon = None

            if (
                self._map_data is None
                or not self._layers.get(MapRendererLayer.IMAGE)
                or self._map_data.active_segments != map_data.active_segments
                or self._map_data.active_areas != map_data.active_areas
                or self._map_data.segments != map_data.segments
                or self._map_data.data != map_data.data
            ):
                area_colors = {}
                # as implemented on the app
                area_colors[MapPixelType.OUTSIDE.value] = self.color_scheme.outside
                area_colors[MapPixelType.WALL.value] = self.color_scheme.wall
                area_colors[MapPixelType.FLOOR.value] = self.color_scheme.floor
                area_colors[MapPixelType.NEW_SEGMENT.value] = self.color_scheme.new_segment
                area_colors[MapPixelType.UNKNOWN.value] = self.color_scheme.floor
                area_colors[MapPixelType.OBSTACLE_WALL.value] = self.color_scheme.wall
                area_colors[MapPixelType.NEW_SEGMENT_UNKNOWN.value] = self.color_scheme.new_segment
                
                if map_data.segments is not None:
                    for (k, v) in map_data.segments.items():
                        if self.config.color:
                            if map_data.active_segments and k not in map_data.active_segments:
                                area_colors[k] = self.color_scheme.passive_segment
                            elif v.color_index is not None:
                                area_colors[k] = self.color_scheme.segment[
                                    v.color_index
                                ][0]
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

                min_x = map_data.dimensions.width - 1
                min_y = map_data.dimensions.height - 1
                max_x = 0
                max_y = 0
                for y in range(map_data.dimensions.height):
                    for x in range(map_data.dimensions.width):
                        px_type = int(
                            map_data.pixel_type[x, map_data.dimensions.height - y - 1])
                        if px_type != MapPixelType.OUTSIDE.value:
                            pixels[y, x] = area_colors[px_type] if px_type in area_colors else area_colors[MapPixelType.NEW_SEGMENT.value]

                            max_x = max(x, max_x)
                            min_x = min(x, min_x)
                            max_y = max(y, max_y)
                            min_y = min(y, min_y)        
                                
                if map_data.dimensions.bounds:
                    #min_x = max(0, min(map_data.dimensions.bounds[0], min_x))
                    #max_x = min((map_data.dimensions.width - 1), max(map_data.dimensions.bounds[2], max_x))
                    #min_y = max(0, min(map_data.dimensions.bounds[1], min_y))
                    #max_y = min((map_data.dimensions.height - 1), max(map_data.dimensions.bounds[3], max_y))
                    min_x = max(min(map_data.dimensions.bounds[0], min_x), min_x)
                    max_x = min(max(map_data.dimensions.bounds[2], max_x), max_x)
                    min_y = max(min(map_data.dimensions.bounds[1], min_y), min_y)
                    max_y = min(max(map_data.dimensions.bounds[3], max_y), max_y)

                if (
                    (
                        min_x != (map_data.dimensions.width - 1) and
                        min_y != (map_data.dimensions.height - 1) and
                        max_x != 0 and
                        max_y != 0
                    ) and
                    (
                        min_x != 0 or
                        min_y != 0 or
                        max_x != (map_data.dimensions.width - 1) or
                        max_y != (map_data.dimensions.height - 1)
                    )
                ):  
                    map_data.dimensions.crop = [min_x * scale, min_y * scale, (map_data.dimensions.width - (
                        max_x + 1)) * scale, (map_data.dimensions.height - (max_y + 1)) * scale]
                    pixels = pixels[min_y:(max_y + 1), min_x:(max_x + 1)]
                        
                if self._map_data and self._map_data.dimensions.crop != map_data.dimensions.crop:
                    self._map_data = None

                self._layers[MapRendererLayer.IMAGE] = ImageOps.expand(
                    Image.fromarray(pixels.repeat(
                        scale, axis=0).repeat(scale, axis=1)),
                    border=tuple(map_data.dimensions.padding)
                )
            else:
                map_data.dimensions.crop = self._map_data.dimensions.crop

            self._calibration_points = self._calculate_calibration_points(
                map_data)

            image = self.render_objects(
                map_data,
                robot_status,
                self._layers[MapRendererLayer.IMAGE],
                2,
            )

            if map_data.rotation == 90:
                image = image.transpose(Image.ROTATE_90)
            elif map_data.rotation == 180:
                image = image.transpose(Image.ROTATE_180)
            elif map_data.rotation == 270:
                image = image.transpose(Image.ROTATE_270)

            _LOGGER.info(
                "Render frame: %s:%s took: %.2f",
                map_data.map_id,
                map_data.frame_id,
                time.time() - now
            )

            self._map_data = map_data
            self._robot_status = robot_status
            self._image = image
        except Exception:
            _LOGGER.error("Map render Failed: %s", traceback.format_exc())

        self.render_complete = True
        return self._to_buffer(self._image)

    def render_objects(
        self,
        map_data,
        robot_status,
        map_image,
        scale,
    ):
        if self._map_data is None or not self._layers.get(MapRendererLayer.OBJECTS):
            self._layers[MapRendererLayer.OBJECTS] = Image.new(
                "RGBA",
                [int(map_image.size[0] * scale),
                 int(map_image.size[1] * scale)],
                (255, 255, 255, 0),
            )
        layer = self._layers[MapRendererLayer.OBJECTS]
        layer.paste((255, 255, 255, 0), [
                    0, 0, layer.size[0], layer.size[1]])

        line_width = 3
        border_width = 2
        
        if map_data.rotation == 0 or map_data.rotation == 180:
            width = (map_data.dimensions.width) + ((map_data.dimensions.padding[0] + map_data.dimensions.padding[2] - map_data.dimensions.crop[0] - map_data.dimensions.crop[2]) / map_data.dimensions.scale)
            robot_icon_size = width * 0.037
            icon_size = width * 0.03
        else:
            height = (map_data.dimensions.height) + ((map_data.dimensions.padding[1] + map_data.dimensions.padding[3] - map_data.dimensions.crop[1] - map_data.dimensions.crop[3]) / map_data.dimensions.scale)
            robot_icon_size = height * 0.037
            icon_size = height * 0.03
            
        robot_icon_size = max(7, min(14, robot_icon_size))
        icon_size = max(5, min(10, icon_size))
            
        if map_data.path and self.config.path:
            if (
                self._map_data is None
                or self._map_data.path != map_data.path
                or not self._layers.get(MapRendererLayer.PATH)
            ):
                self._layers[MapRendererLayer.PATH] = self.render_path(
                    map_data.path,
                    self.color_scheme.path,
                    layer,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.PATH])

        if map_data.no_mopping_areas and self.config.no_mop:
            if (
                self._map_data is None
                or self._map_data.no_mopping_areas != map_data.no_mopping_areas
                or not self._layers.get(MapRendererLayer.NO_MOP)
            ):
                self._layers[MapRendererLayer.NO_MOP] = self.render_areas(
                    map_data.no_mopping_areas,
                    self.color_scheme.no_mop_outline,
                    self.color_scheme.no_mop,
                    layer,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.NO_MOP])

        if map_data.no_go_areas and self.config.no_go:
            if (
                self._map_data is None
                or self._map_data.no_go_areas != map_data.no_go_areas
                or not self._layers.get(MapRendererLayer.NO_GO)
            ):
                self._layers[MapRendererLayer.NO_GO] = self.render_areas(
                    map_data.no_go_areas,
                    self.color_scheme.no_go_outline,
                    self.color_scheme.no_go,
                    layer,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.NO_GO])

        if map_data.walls and self.config.virtual_wall:
            if (
                self._map_data is None
                or self._map_data.walls != map_data.walls
                or not self._layers.get(MapRendererLayer.WALL)
            ):
                self._layers[MapRendererLayer.WALL] = self.render_walls(
                    map_data.walls,
                    self.color_scheme.virtual_wall,
                    layer,
                    map_data.dimensions,
                    line_width,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.WALL])

        if map_data.active_areas and self.config.active_area:
            if (
                self._map_data is None
                or self._map_data.active_areas != map_data.active_areas
                or not self._layers.get(MapRendererLayer.ACTIVE_AREA)
            ):
                self._layers[MapRendererLayer.ACTIVE_AREA] = self.render_areas(
                    map_data.active_areas,
                    self.color_scheme.active_area_outline,
                    self.color_scheme.active_area,
                    layer,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.ACTIVE_AREA])

        if map_data.active_points and self.config.active_point:
            if (
                self._map_data is None
                or self._map_data.active_points != map_data.active_points
                or not self._layers.get(MapRendererLayer.ACTIVE_POINT)
            ):
                self._layers[MapRendererLayer.ACTIVE_POINT] = self.render_points(
                    map_data.active_points,
                    self.color_scheme.active_point_outline,
                    self.color_scheme.active_point,
                    layer,
                    map_data.dimensions,
                    border_width,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.ACTIVE_POINT])

        if map_data.segments and (self.config.icon or self.config.name or self.config.order or self.config.suction_level or self.config.water_volume or self.config.cleaning_times or self.config.cleaning_mode):
            if (
                self._map_data is None
                or self._map_data.segments != map_data.segments
                or self._map_data.rotation != map_data.rotation
                or bool(self._map_data.cleanset) != bool(map_data.cleanset)
                or not self._layers.get(MapRendererLayer.SEGMENTS)
            ):
                if MapRendererLayer.SEGMENTS not in self._layers:
                    self._layers[MapRendererLayer.SEGMENTS] = {}
                else:
                    for k in list(self._layers[MapRendererLayer.SEGMENTS].keys()).copy():
                        if k not in map_data.segments:
                            del self._layers[MapRendererLayer.SEGMENTS][k]

                for k, v in map_data.segments.items():
                    if (
                        self._map_data is None
                        or k not in self._layers[MapRendererLayer.SEGMENTS]
                        or not self._map_data.segments
                        or k not in self._map_data.segments
                        or self._map_data.segments[k] != v
                        or self._map_data.rotation != map_data.rotation
                        or bool(self._map_data.cleanset) != bool(map_data.cleanset)
                    ):
                        self._layers[MapRendererLayer.SEGMENTS][k] = self.render_segment(
                            v,
                            bool(map_data.cleanset),
                            layer,
                            map_data.dimensions,
                            int(icon_size * map_data.dimensions.scale),
                            map_data.rotation,
                            scale,
                        )

            if self._layers[MapRendererLayer.SEGMENTS]:
                for k, v in sorted(self._layers[MapRendererLayer.SEGMENTS].items(), reverse=True):
                    layer = Image.alpha_composite(layer, v)

        if map_data.charger_position and self.config.charger:
            if (
                self._map_data is None
                or self._map_data.charger_position != map_data.charger_position
                or self._map_data.rotation != map_data.rotation
                or bool(self._robot_status > 5) != bool(robot_status > 5)
                or not self._layers.get(MapRendererLayer.CHARGER)
            ):
                #def correct_charger_position(chargerPos, pixel_type, width, height, x, y, gridWidth, borderValue):                 
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
                if self._robot_shape != 1 and self.icon_set == 2:
                    offset = int(robot_icon_size * 21.42)
                    charger_position = Point(
                        charger_position.x - offset * math.cos(charger_position.a * math.pi / 180), 
                        charger_position.y - offset * math.sin(charger_position.a * math.pi / 180), 
                        charger_position.a
                    )

                self._layers[MapRendererLayer.CHARGER] = self.render_charger(
                    charger_position,
                    robot_status,
                    layer,
                    map_data.dimensions,
                    int((robot_icon_size * map_data.dimensions.scale) * 1.2),
                    map_data.rotation,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.CHARGER])

        if map_data.robot_position and self.config.robot:
            if (
                self._map_data is None
                or self._map_data.robot_position != map_data.robot_position
                or self._map_data.charger_position != map_data.charger_position
                or self._map_data.rotation != map_data.rotation
                or self._robot_status != robot_status
                or self._map_data.docked != map_data.docked
                or not self._layers.get(MapRendererLayer.ROBOT)
            ):
                robot_position = map_data.robot_position

                if map_data.docked:
                    # Calculate charger angle
                    charger_angle = map_data.charger_position.a
                    if self._robot_shape != 1:
                        offset = int(robot_icon_size * 21.42)

                        if self.icon_set != 2:
                            if (
                                charger_angle > -45
                                and charger_angle < 45
                            ):
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
                        charger_angle + 180 if self._robot_shape != 2 else charger_angle
                    )

                self._layers[MapRendererLayer.ROBOT] = self.render_vacuum(
                    robot_position,
                    robot_status,
                    layer,
                    map_data.dimensions,
                    int(robot_icon_size * map_data.dimensions.scale),
                    map_data.rotation,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.ROBOT])

        if map_data.obstacles and self.config.obstacle:
            if (
                self._map_data is None
                or self._map_data.obstacles != map_data.obstacles
                or self._map_data.rotation != map_data.rotation
                or not self._layers.get(MapRendererLayer.OBSTACLES)
            ):
                self._layers[MapRendererLayer.OBSTACLES] = self.render_obstacles(
                    map_data.obstacles,
                    layer,
                    map_data.dimensions,
                    int((icon_size * 2) * map_data.dimensions.scale),
                    map_data.rotation,
                    scale,
                )

            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.OBSTACLES])

        if layer.size != map_image.size:
            layer.thumbnail(
                map_image.size, Image.Resampling.BOX, reducing_gap=1.5)

        return Image.alpha_composite(
            map_image,
            layer,
        )

    def render_areas(self, areas, color, fill, layer, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for area in areas:
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

    def render_points(self, points, color, fill, layer, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        size = 15 * dimensions.grid_size
        for point in points:
            area = Area(point.x - size, point.y - size, point.x + size, point.y -
                        size, point.x + size, point.y + size, point.x - size, point.y + size)

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

    def render_walls(self, walls, color, layer, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for wall in walls:
            p = wall.to_img(dimensions)
            draw.line(
                [p.x0 * scale, p.y0 * scale, p.x1 * scale, p.y1 * scale],
                color,
                width=(width * scale),
            )
        return new_layer

    def render_path(self, path, color, layer, dimensions, width, scale):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        sweep = []
        mop = []
        sweep_path = []
        mop_path = []
        path_type = ""

        for point in path:
            p = point.to_img(dimensions)
            if point.path_type == PathType.LINE:
                l = [p.x * scale, p.y * scale]
                if path_type == PathType.SWEEP_AND_MOP or path_type == PathType.SWEEP:
                    sweep_path.extend(l)

                if path_type == PathType.SWEEP_AND_MOP or path_type == PathType.MOP:
                    mop_path.extend(l)
            else:
                if mop_path:
                    mop.append(mop_path)

                if sweep_path:
                    sweep.append(sweep_path)

                path_type = point.path_type
                if path_type == PathType.SWEEP_AND_MOP or path_type == PathType.SWEEP:
                    sweep_path = [p.x * scale, p.y * scale]
                else:
                    sweep_path = []

                if path_type == PathType.SWEEP_AND_MOP or path_type == PathType.MOP:
                    mop_path = [p.x * scale, p.y * scale]
                else:
                    mop_path = []

        if sweep_path:
            sweep.append(sweep_path)

        if mop_path:
            mop.append(mop_path)

        for path in mop:
            size = width * scale * 12
            draw.line(
                path,
                width=int(size),
                fill=(color[0], color[1], color[2], 100),
                joint='curve',
            )

        for path in sweep:
            size = width * scale
            draw.line(
                path,
                width=int(size),
                fill=color,
                joint='curve',
            )
            size = int(math.floor(size / 2))
            draw.ellipse([
                path[-2] - size,
                path[-1] - size,
                path[-2] + size,
                path[-1] + size,
            ],
                fill=color,
            )
            draw.ellipse([
                path[0] - size,
                path[1] - size,
                path[0] + size,
                path[1] + size,
            ],
                fill=color,
            )

        return new_layer

    def render_charger(
        self, charger_position, robot_status, layer, dimensions, size, map_rotation, scale
    ):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        icon_size = int(size * scale)
        if self._charger_icon is None:
            if self.icon_set == 3:
                charger_image = MAP_CHARGER_IMAGE_MATERIAL
                icon_size = int(icon_size * 1.2)
            elif self.icon_set == 2:
                charger_image = MAP_CHARGER_IMAGE_MIJIA
                icon_size = int(icon_size * 1.5)
            else:
                if self._robot_shape == 1:
                    charger_image = MAP_CHARGER_VSLAM_IMAGE_DREAME
                    icon_size = int(icon_size * 1.5)
                else:
                    charger_image = MAP_CHARGER_IMAGE_DREAME

            self._charger_icon = (
                Image.open(BytesIO(base64.b64decode(charger_image)))
                .convert("RGBA")
                .resize((icon_size, icon_size), resample=Image.Resampling.NEAREST)
            )

            if self.icon_set == 3:
                self._charger_icon = DreameVacuumMapRenderer._set_icon_color(
                            self._charger_icon,
                            icon_size,
                            (0, 255, 126),
                        )

            if self.color_scheme.dark:
                enhancer = ImageEnhance.Brightness(self._charger_icon)
                self._charger_icon = enhancer.enhance(0.7)

        charger_icon = self._charger_icon.rotate(charger_position.a if self._robot_shape == 1 or self.icon_set == 2 or self.icon_set == 3 else (-map_rotation), expand=1)

        point = charger_position.to_img(dimensions)
        new_layer.paste(
            charger_icon,
            (int((point.x * scale) - (charger_icon.size[0] / 2)),
             int((point.y * scale) - (charger_icon.size[1] / 2))),
            charger_icon,
        )

        if robot_status > 5:
            if self._robot_washing_icon is None:
                self._robot_washing_icon = (
                    Image.open(
                        BytesIO(base64.b64decode(MAP_ROBOT_WASHING_IMAGE)))
                    .convert("RGBA")
                    .resize((int(icon_size * 1.25), int(icon_size * 1.25)), resample=Image.Resampling.NEAREST)
                    .rotate(-map_rotation)
                )
                enhancer = ImageEnhance.Brightness(self._robot_washing_icon)
                if self.color_scheme.dark:
                    self._robot_washing_icon = enhancer.enhance(0.65)

            icon = self._robot_washing_icon

            icon_x = point.x * scale
            icon_y = point.y * scale
            offset = (icon_size * 1.5)
            if map_rotation == 90:
                icon_x = icon_x + offset
            elif map_rotation == 180:
                icon_y = icon_y + offset
            elif map_rotation == 270:
                icon_x = icon_x - offset
            else:
                icon_y = icon_y - offset

            new_layer.paste(
                icon,
                (int(icon_x - (icon.size[0] / 2)),
                 int(icon_y - (icon.size[1] / 2))),
                icon,
            )
        return new_layer

    def render_vacuum(
        self, robot_position, robot_status, layer, dimensions, size, map_rotation, scale
    ):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        icon_size = int(size * scale)
        if self._robot_icon is None:
            robot_icon_size = icon_size
            if self.icon_set == 2:
                robot_icon_size = int(icon_size * 1.4)
                if self._robot_shape == 2:
                    robot_image = MAP_ROBOT_MOP_IMAGE_MIJIA
                elif self._robot_shape == 1:
                    robot_image = MAP_ROBOT_VSLAM_IMAGE_MIJIA
                else:
                    robot_image = MAP_ROBOT_LIDAR_IMAGE_MIJIA
            else:
                if self._robot_shape == 2:
                    robot_image = MAP_ROBOT_MOP_IMAGE_DREAME
                elif self._robot_shape == 1:
                    if self.icon_set == 3:
                        robot_image = MAP_ROBOT_VSLAM_IMAGE_DREAME_LIGHT
                    else:
                        robot_image = MAP_ROBOT_VSLAM_IMAGE_DREAME_DARK
                else:
                    if self.icon_set == 3:
                        robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_LIGHT
                    else:
                        robot_image = MAP_ROBOT_LIDAR_IMAGE_DREAME_DARK
                
            self._robot_icon = (
                Image.open(BytesIO(base64.b64decode(robot_image)))
                .convert("RGBA")
                .resize((robot_icon_size, robot_icon_size), resample=Image.Resampling.NEAREST)
            )

            if self._robot_shape != 2 and self.icon_set != 2 and self.icon_set != 3:
                enhancer = ImageEnhance.Brightness(self._robot_icon)
                if self.color_scheme.dark:
                    self._robot_icon = enhancer.enhance(1.5)
                else:
                    self._robot_icon = enhancer.enhance(0.9)

        icon = self._robot_icon.rotate(robot_position.a)
        point = robot_position.to_img(dimensions)

        status_icon = None
        if robot_status == 1:
            if self._robot_cleaning_icon is None:
                self._robot_cleaning_icon = (
                    Image.open(
                        BytesIO(base64.b64decode(MAP_ROBOT_CLEANING_IMAGE)))
                    .convert("RGBA")
                    .resize(((int(icon_size * 1.25), int(icon_size * 1.25))), resample=Image.Resampling.NEAREST)
                )
            status_icon = self._robot_cleaning_icon

            if self.config.cleaning_direction:
                if self._robot_cleaning_direction_icon is None:
                    self._robot_cleaning_direction_icon = (
                        Image.open(
                            BytesIO(base64.b64decode(MAP_ROBOT_CLEANING_DIRECTION_IMAGE)))
                        .convert("RGBA")
                        .resize(((int(icon_size * 1.5), int(icon_size * 1.5))), resample=Image.Resampling.NEAREST)
                    )
                
                ico = self._robot_cleaning_direction_icon.rotate(robot_position.a, expand=1)

                offset = int(icon_size / 2)
                x = point.x + offset * math.cos(-robot_position.a * math.pi / 180) 
                y = point.y + offset * math.sin(-robot_position.a * math.pi / 180)
                new_layer.paste(ico,
                    (
                        int(x * scale - (ico.size[0] / 2)),
                        int(y * scale - (ico.size[1] / 2)),
                    )
                )
        elif robot_status == 2:
            if self._robot_charging_icon is None:
                self._robot_charging_icon = (
                    Image.open(
                        BytesIO(base64.b64decode(MAP_ROBOT_CHARGING_IMAGE)))
                    .convert("RGBA")
                    .resize(((int(icon_size * 1.3), int(icon_size * 1.3))), resample=Image.Resampling.NEAREST)
                )
            status_icon = self._robot_charging_icon
        elif robot_status == 3 or robot_status == 5 or robot_status == 6:
            if self._robot_warning_icon is None:
                self._robot_warning_icon = (
                    Image.open(
                        BytesIO(base64.b64decode(MAP_ROBOT_WARNING_IMAGE)))
                    .convert("RGBA")
                    .resize(((int(icon_size * 1.3), int(icon_size * 1.3))), resample=Image.Resampling.NEAREST)
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
                mask
            )

        new_layer.paste(
            icon,
            (
                int(point.x * scale - (icon.size[0] / 2)),
                int(point.y * scale - (icon.size[1] / 2)),
            ),
            icon,
        )

        if robot_status == 4 or robot_status == 5:
            if self._robot_sleeping_icon is None:
                sleeping_icon = (
                    Image.open(
                        BytesIO(base64.b64decode(MAP_ROBOT_SLEEPING_IMAGE)))
                    .convert("RGBA")
                    .rotate(-map_rotation, expand=1)
                )
                enhancer = ImageEnhance.Brightness(sleeping_icon)
                if not self.color_scheme.dark:
                    sleeping_icon = enhancer.enhance(0.7)

                self._robot_sleeping_icon = [
                    sleeping_icon.resize(((int(icon_size * 0.3), int(icon_size * 0.3))), resample=Image.Resampling.NEAREST),
                    sleeping_icon.resize(
                        ((int(icon_size * 0.35), int(icon_size * 0.35))), resample=Image.Resampling.NEAREST),
                ]
                
            for k in [[int(icon_size * 0.34), int(icon_size * 0.18), 0], [int(icon_size * 0.43), int(icon_size * 0.43), 1]]:
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
        self, segment, cleanset, layer, dimensions, size, rotation, scale
    ):        
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        if segment.x is not None and segment.y is not None:
            text = None
            icon = self._segment_icons.get(segment.type) if self.config.icon else None
            if segment.type == 0 or icon is None:
                text = segment.name if (self._robot_shape != 1 or icon is not None) or segment.custom_name is not None else segment.letter if self.icon_set != 2 else None
            elif segment.index > 0:
                text = str(segment.index)

            text_font = None
            order_font = None            
            if text and self.config.name:
                text_font = ImageFont.truetype(
                    BytesIO(self.font_file),
                    int((size * 1.9)) if segment.index or icon is None else int((size * 1.7)),
                )

            if segment.order and self.config.order:
                order_font = ImageFont.truetype(
                    BytesIO(self.font_file), int((size * 2.1))
                )

            p = Point(segment.x, segment.y).to_img(dimensions)
            x = p.x
            y = p.y            

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

                        if segment.index > 0 or icon is None:
                            icon_size = size * 1.35
                            padding = icon_size / 2
                            text_offset = (icon_size / 2) + 2
                            icon_offset = 2
                            th = int(size * 2.3)
                        else:
                            icon_size = size * 1.15
                            padding = icon_size * 0.35
                            icon_offset = padding - 2
                            text_offset = icon_size / 2
                            th = int(size * 1.9)

                        if icon is None:
                            text_offset = 0
                            padding = -(icon_size / 4)

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

                        if self.config.icon:
                            draw.rounded_rectangle(
                                [
                                    int(x0 * scale),
                                    int(y0 * scale),
                                    int(x1 * scale),
                                    int(y1 * scale),
                                ],
                                fill=self.color_scheme.icon_background,
                                radius=((size * scale)),
                            )

                        icon_text = Image.new(
                            "RGBA", (tw, th), (255, 255, 255, 0))
                        draw_text = ImageDraw.Draw(icon_text, "RGBA")

                        if self.config.icon:
                            stroke_width = 1
                            text_color = self.color_scheme.text
                            stroke_color = self.color_scheme.text_stroke
                        else:
                            stroke_width = 4
                            if self.color_scheme.dark:
                                text_color = (240, 240, 240, 255)
                                stroke_color = (0, 0, 0, 210)
                            else:
                                text_color = (15, 15, 15, 255)
                                stroke_color = (255, 255, 255, 210)

                        draw_text.text(
                            (0, 0),
                            text,
                            font=text_font,
                            fill=text_color,
                            stroke_width=stroke_width,
                            stroke_fill=stroke_color,
                        )
                        icon_text = icon_text.rotate(-rotation, expand=1)
                        new_layer.paste(
                            icon_text, (int(tx), int(ty)), icon_text)
                    elif icon is not None:
                        draw.ellipse(
                            [x0 * scale, y0 * scale, x1 * scale, y1 * scale],
                            fill=self.color_scheme.icon_background,
                        )

                    if icon is not None:
                        s = icon_size * scale
                        icon = icon.resize((int(s), int(s))).rotate(-rotation, expand=1)
                        new_layer.paste(
                            icon, (int(x * scale - (icon.size[0] / 2)),
                                   int(y * scale - (icon.size[1] / 2))), icon
                        )

            custom = (
                cleanset
                and (self.config.suction_level or self.config.water_volume or self.config.cleaning_times or self.config.cleaning_mode)
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
                cleaning_mode = None if segment.cleaning_mode is None or segment.cleaning_mode < 0 or segment.cleaning_mode > 3 else segment.cleaning_mode
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
                else:
                    icon_count = 1

                if not icon and not self.config.icon:
                    arrow = 0

                radius = size
                arrow = int(round(radius * 0.6))
                s = int(round(radius * 0.25))
                margin = s if icon_count > 1 else 0
                if custom:
                    radius = size - 2

                icon_w = (
                    ((radius * icon_count * 2) * scale) +
                    (arrow * 2) + (margin * 2)
                )
                icon_h = ((radius * 2) * scale) + (arrow * 2)
                icon = Image.new("RGBA", (icon_w, icon_h),
                                 (255, 255, 255, 0))
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

                padding = s + arrow
                r = icon_h - (padding * 2)
                ellipse_x1 = padding + margin
                ellipse_x2 = ellipse_x1 + r
                if order_font:
                    icon_draw.ellipse(
                        [ellipse_x1, padding, ellipse_x2, icon_h - padding],
                        fill=self.color_scheme.segment[
                            segment.color_index
                        ][1],
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
                            self.color_scheme.segment[segment.color_index][
                                1
                            ],
                        )

                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2,
                                (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(
                                    2
                                    + ellipse_x1
                                    + ((ellipse_x2 - ellipse_x1) / 2)
                                    - ico.size[0] / 2
                                ),
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
                            self.color_scheme.segment[segment.color_index][
                                1
                            ],
                        )
                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2,
                                (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(
                                    2
                                    + ellipse_x1
                                    + ((ellipse_x2 - ellipse_x1) / 2)
                                    - ico.size[0] / 2
                                ),
                                int(((icon_h / 2) - ico.size[1] / 2)),
                            ),
                            ico,
                        )

                        ellipse_x1 = ellipse_x2 + (margin * 2)
                        ellipse_x2 = ellipse_x1 + r

                    if self.config.water_volume and segment.water_volume is not None and cleaning_mode != 0:     
                        if self.icon_set == 3:
                            s = icon_size * 0.95 * scale
                        elif self.icon_set == 2:
                            s = icon_size * 1.2 * scale
                        else:
                            s = icon_size * 0.85 * scale

                        ico = DreameVacuumMapRenderer._set_icon_color(
                            self._water_volume_icon[segment.water_volume - 1],
                            s,
                            self.color_scheme.segment[segment.color_index][
                                1
                            ],
                        )

                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2,
                                (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(
                                    2
                                    + ellipse_x1
                                    + ((ellipse_x2 - ellipse_x1) / 2)
                                    - ico.size[0] / 2
                                ),
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
                            self.color_scheme.segment[segment.color_index][
                                1
                            ],
                        )

                        icon_draw.ellipse(
                            [ellipse_x1, padding, ellipse_x2,
                                (icon_h - padding)],
                            fill=self.color_scheme.settings_icon_background,
                        )
                        icon.paste(
                            ico,
                            (
                                int(
                                    2
                                    + ellipse_x1
                                    + ((ellipse_x2 - ellipse_x1) / 2)
                                    - ico.size[0] / 2
                                ),
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

    def render_obstacles(self, obstacles, layer, dimensions, size, rotation, scale):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        icon_size = (size * scale * 0.85)
        draw = ImageDraw.Draw(new_layer, "RGBA")

        if self._obstacle_background is None:
            self._obstacle_background = (
                Image.open(BytesIO(base64.b64decode(MAP_ICON_OBSTACLE_BG_DREAME)))
                .convert("RGBA")
                .rotate(-rotation)
            )
            self._obstacle_background.thumbnail(
                (size * scale * scale, size * scale * scale), Image.Resampling.LANCZOS)

        bg_size = int(round((size * scale * 0.5) / 2))
        offset = -8 * scale
        if rotation == 90:
            y_offset = 0
            x_offset = offset
        elif rotation == 180:
            y_offset = offset
            x_offset = 0
        elif rotation == 270:
            y_offset = 0
            x_offset = -offset
        else:
            x_offset = 0
            y_offset = -offset

        for obstacle in obstacles:
            icon = self._obstacle_icons.get(obstacle.obstacle_type.value)
            if icon:
                p = obstacle.to_img(dimensions)
                x = p.x
                y = p.y

                new_layer.paste(
                    self._obstacle_background, (int(round(x * scale - (self._obstacle_background.size[0] / 2) + x_offset)),
                                                int(round(y * scale - (self._obstacle_background.size[1] / 2) + y_offset)))
                )

                draw.ellipse(
                    [(x - bg_size) * scale, (y - bg_size) * scale,
                     (x + bg_size) * scale, (y + bg_size) * scale],
                    fill=self.color_scheme.segment[0][0],
                )

                icon = icon.resize(
                    (int(icon_size), int(icon_size))).rotate(-rotation)
                new_layer.paste(
                    icon, (int(round(x * scale - (icon_size / 2))),
                           int(round(y * scale - (icon_size / 2)))), icon
                )

        return new_layer

    @property
    def calibration_points(self) -> dict[str, int]:
        return self._calibration_points

    @property
    def default_map_image(self) -> bytes:
        return self._to_buffer(self._default_map_image)

    @property
    def disconnected_map_image(self) -> bytes:
        if self._image:
            return self._to_buffer(self._image.filter(ImageFilter.GaussianBlur(13)))
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
                    if (data[index - 1] == 1 and data[index + 1] == 1) or (data[index + width] == 1 and data[index - width] == 1):
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
                        l = (0 if i == 0 else data[index - 1])
                        r = (0 if i == (width - 1) else data[index + 1])
                        t = (0 if j == (height - 1) else data[index + width])
                        b = (0 if j == 0 else data[index - width])
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
                
        self._update_border_value(
            data, width, height, stroke)

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
                                self._add_line(
                                    vLine, covertlines, allLines)
                                del verticalLines[i]
                                hasFind = True
                                break
                            elif lastLine.y == vLine.y[1]:
                                vLine.findEnd = False
                                self._add_line(
                                    vLine, covertlines, allLines)
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

                                self._add_line(
                                    vLine, covertlines, allLines)
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
                                self._add_line(
                                    hLine, covertlines, allLines)
                                del horizontalLines[i]
                                hasFind = True
                                break
                            elif lastLine.x == hLine.x[1]:
                                hLine.findEnd = False
                                self._add_line(
                                    hLine, covertlines, allLines)
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

                                self._add_line(
                                    hLine, covertlines, allLines)
                                del horizontalLines[i]
                                hasFind = True
                                break

                    if not hasFind:
                        break
                    
            totalLength = 0
            for i in range(len(covertlines)):
                item = covertlines[i]
                totalLength = totalLength + item.length

            paths.append(Paths(
                clines = covertlines,
                alines = allLines,
                length = totalLength
            ))

        return paths

    def _fill_map_data_2(self, data, width, height):
        while True:
            first_point = self._find_first_empty_point(
                data, width, height)
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
                        verticalLines.append(CLine(x = i, y = [startY, lastY], ishorizontal = False, direction = direction, length = (lastY - startY)))
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
                        horizontalLines.append(CLine(x = [startX, lastX], y = j, ishorizontal = True, direction = direction, length = (lastX - startX)))
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
                                if (line.x > nLine.x and line.direction == DIR_LEFT) or (line.x < nLine.x and line.direction == DIR_RIGHT):
                                    if abs(line.x - nLine.x) <= 10:
                                        _ys = self._check_intersect(
                                            line.y, nLine.y)
                                        if _ys != None:
                                            xs = [line.x + 1, nLine.x - 1]
                                            if line.x > nLine.x:
                                                xs = [nLine.x + 1, line.x - 1]
                                            weight = self._find_original_points(
                                                original_data, data, width, xs, _ys)
                        elif line.ishorizontal == True and nLine.ishorizontal == True:
                            if line.direction != nLine.direction:
                                if (line.y > nLine.y and line.direction == DIR_BOTTOM) or (line.y < nLine.y and line.direction == DIR_TOP):
                                    if abs(line.y - nLine.y) <= 10:
                                        _xs = self._check_intersect(
                                            line.x, nLine.x)
                                        if _xs != None:
                                            ys = [line.y + 1, nLine.y - 1]
                                            if line.y > nLine.y:
                                                ys = [nLine.y + 1, line.y - 1]
                                            weight = self._find_original_points(
                                                original_data, data, width, _xs, ys)

        if needFill:
            for i in range(len(data)):
                if data[i] == stroke:
                    data[i] = 1

            self._fill_map_data_2(data, width, height)
            self._update_border_value(
                data, width, height, stroke)
            self._fill_cross_line(
                data, width, height, stroke)

    def _fill_angle(self, data, width, stroke, angle):
        bottom = 5
        right = 6
        top = 7
        left = 8

        l1 = angle.lines[0]
        l2 = angle.lines[len(angle.lines) - 1]
        if len(angle.lines) == 2 or len(angle.lines) > 22:
            nextAngle = Angle(lines = [l2])
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
            nextAngle = Angle(lines = [l2])
            if (l2.ishorizontal):
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
                        
        nextAngle = Angle(lines = [l2])
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
                        verticalLines.append(CLine(x = i, y = [startY, lastY], ishorizontal = False, length = (lastY - startY)))
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
                        horizontalLines.append(CLine(x = [startX, lastX], y = j, ishorizontal = True, length = (lastX - startX)))
                        startX = lastX
                        continue
                startX = -1

        if not horizontalLines:
            return False

        paths = self._find_bounds(
            data, width, horizontalLines, verticalLines)
        
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
                        angle = self._fill_angle(
                            data, width, stroke, angle)

                    if angle.horizontalDir == dirnone:
                        angle.horizontalDir = horizontalDir
                    angle.lines.append(line)
                else:
                    verticalDir = top if line.findEnd else bottom
                    if angle.verticalDir != dirnone and angle.verticalDir != verticalDir:
                        angle = self._fill_angle(
                            data, width, stroke, angle)
                    if angle.verticalDir == dirnone:
                        angle.verticalDir = verticalDir
                    angle.lines.append(line)

                if line.length >= 7 or i == len(allLines):
                    angle = self._fill_angle(
                        data, width, stroke, angle)

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
                    if  not isCross:
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
                        vLines.append([[i, startY],[i, lastY]])
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
                        hLines.append([[startX, j],[lastX, j]])

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
            if lastX != None:
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
            if lastX != None:
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
            if lastY != None:
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
            if lastY != None:
                if cY - lastY <= 11:
                    charger_position.a = 90
                    charger_position.y = lastY + 0.5

        return charger_position

    def _merge_saved_map_data(self, map_data, saved_map_data, original_data = None):
        if saved_map_data:
            maxX = map_data.dimensions.left + \
                (map_data.dimensions.width * map_data.dimensions.grid_size)
            maxY = map_data.dimensions.top + \
                (map_data.dimensions.height * map_data.dimensions.grid_size)

            if maxX < saved_map_data.dimensions.left + (saved_map_data.dimensions.width * saved_map_data.dimensions.grid_size):
                maxX = saved_map_data.dimensions.left + \
                    (saved_map_data.dimensions.width *
                        saved_map_data.dimensions.grid_size)

            if maxY < saved_map_data.dimensions.top + (saved_map_data.dimensions.height * saved_map_data.dimensions.grid_size):
                maxY = saved_map_data.dimensions.top + \
                    (saved_map_data.dimensions.height *
                        saved_map_data.dimensions.grid_size)

            left = map_data.dimensions.left
            top = map_data.dimensions.top

            if saved_map_data.dimensions.left < left:
                left = saved_map_data.dimensions.left

            if saved_map_data.dimensions.top < top:
                top = saved_map_data.dimensions.top

            width = int((maxX - left) / saved_map_data.dimensions.grid_size)
            height = int((maxY - top) / saved_map_data.dimensions.grid_size)
            
            si = int((saved_map_data.dimensions.left - left) /
                        saved_map_data.dimensions.grid_size)
            sj = int((saved_map_data.dimensions.top - top) /
                        saved_map_data.dimensions.grid_size)

            sim = (si + saved_map_data.dimensions.width)
            sjm = (sj + saved_map_data.dimensions.height)

            ni = int((map_data.dimensions.left - left) /
                        map_data.dimensions.grid_size)
            nj = int((map_data.dimensions.top - top) /
                        map_data.dimensions.grid_size)

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
                            if original_data[(j - nj) * map_data.dimensions.width + (i - ni)] == 2 and pixel_type[i, j] != 0:
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

    def optimize(self, map_data, saved_map_data = None, js_optimizer = True):
        if map_data.saved_map:
            return map_data

        try:
            now = time.time()

            if js_optimizer:
                if self._js_optimizer == None:                
                    self._js_optimizer = MiniRacer()
                    self._js_optimizer.eval(base64.b64decode(MAP_OPTIMIZER_JS))
                    
                data = map_data.pixel_type.tolist()
                data_size = [map_data.dimensions.left, map_data.dimensions.top, map_data.dimensions.width, map_data.dimensions.height, map_data.dimensions.grid_size]
                saved_data = saved_map_data.pixel_type.tolist() if saved_map_data else None
                saved_data_size = [saved_map_data.dimensions.left, saved_map_data.dimensions.top, saved_map_data.dimensions.width, saved_map_data.dimensions.height, saved_map_data.dimensions.grid_size] if saved_map_data else None
                charger_position = None
                if map_data.charger_position:
                    left = map_data.dimensions.left
                    top = map_data.dimensions.top

                    if saved_map_data:
                        if saved_map_data.dimensions.left < left:
                            left = saved_map_data.dimensions.left

                        if saved_map_data.dimensions.top < top:
                            top = saved_map_data.dimensions.top

                    charger_position = [(map_data.charger_position.x - left) / map_data.dimensions.grid_size, (map_data.charger_position.y - top) / map_data.dimensions.grid_size, map_data.charger_position.a]

                result = self._js_optimizer.call('optimize', data, data_size, saved_data, saved_data_size, charger_position)
                if result and result[0]:
                    map_data.optimized_pixel_type = np.array(result[0], dtype=np.uint8)
            
                    dimensions = result[1]
                    map_data.optimized_dimensions = MapImageDimensions(dimensions[1], dimensions[0], dimensions[3], dimensions[2], map_data.dimensions.grid_size)
                    
                    if result[2] and map_data.charger_position:
                        charger = result[2]
                        #map_data.optimized_charger_position = Point(charger[0] * map_data.dimensions.grid_size + left, charger[1] * map_data.dimensions.grid_size + top, charger[2])
            else:
                width = map_data.dimensions.width
                height = map_data.dimensions.height
                clean_data = np.zeros((width * height), np.uint8).tolist()
        
                data_map = {255:2, 253:1, 250:3}
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
                        new_charger_position.x = int((new_charger_position.x - left) / map_data.dimensions.grid_size)
                        new_charger_position.y = int((new_charger_position.y - top) / map_data.dimensions.grid_size)
                        if new_charger_position.y >= 0 and new_charger_position.x >= 0 and new_charger_position.y < height and new_charger_position.x < width and clean_data[int(math.floor(new_charger_position.y)) * width + int(math.floor(new_charger_position.x))]:
                            new_charger_position = self._calculate_charger_position(clean_data, width, height, 6, new_charger_position)
                            map_data.optimized_charger_position = Point(int(new_charger_position.x * map_data.dimensions.grid_size) + left, int(new_charger_position.y * map_data.dimensions.grid_size) + top, new_charger_position.a)
                            
                    self._find_outline(clean_data, width, height, 6, False)
                    self._fill_map_data_2(clean_data, width, height)
                    self._update_border_value(clean_data, width, height, 7)

                    if saved_map_data:
                        self._find_obstacle_border(clean_data, width, height, 3)
                        self._obstacle_data(original_data, width, height)
                    else:
                        self._clean_small_obstacle(clean_data, width, height, 3)        
        
                    currentPointNum = 0
                    data_map = {7:255, 2:255, 3:(0 if saved_map_data else 250)}
                    for j in range(height):
                        for i in range(width):
                            clean_value = clean_data[j * width + i]
                            if clean_value != 0:
                                currentPointNum = currentPointNum + 1
                                pixel_type[i, j] = data_map.get(clean_value, 253)

                    if (not ((currentPointNum * 100) / pointNum) < 50 and pointNum > 2000):
                        map_data.optimized_pixel_type = pixel_type

                self._merge_saved_map_data(map_data, saved_map_data, original_data)

            _LOGGER.info(
                "Optimize Map Data: %s:%s took: %.2f",
                map_data.map_id,
                map_data.frame_id,
                time.time() - now,
            )
        except Exception as ex:
            _LOGGER.warning("Optimize map failed: %s", ex)

            self._merge_saved_map_data(map_data, saved_map_data)
                
            #_LOGGER.warn(f"""
            #var data = {map_data.pixel_type.tolist()};
            #var data_size = {[map_data.dimensions.left, map_data.dimensions.top, map_data.dimensions.width, map_data.dimensions.height, map_data.dimensions.grid_size]};
            #var saved_data = {saved_map_data.pixel_type.tolist() if saved_map_data else "undefined"};
            #var saved_data_size = {[saved_map_data.dimensions.left, saved_map_data.dimensions.top, saved_map_data.dimensions.width, saved_map_data.dimensions.height, saved_map_data.dimensions.grid_size] if saved_map_data else "undefined"};
            #var charger_position = {[map_data.charger_position.x, map_data.charger_position.y, map_data.charger_position.a] if map_data.charger_position else "undefined"};
            #    """)

        return map_data
