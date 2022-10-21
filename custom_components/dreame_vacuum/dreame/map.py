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
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageEnhance, PngImagePlugin
from typing import Any
from time import sleep
from io import BytesIO
from typing import Optional, Tuple
from functools import cmp_to_key
from threading import Timer
from .resources import *
from .protocol import MiIODeviceProtocol, MiIOCloudProtocol
from .exceptions import DeviceUpdateFailedException
from .types import (
    PIID,
    DIID,
    DreameVacuumProperty,
    DreameVacuumAction,
    DreameVacuumActionMapping,
    Point,
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
        self, device_connection: MiIODeviceProtocol, cloud_connection: MiIOCloudProtocol
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
        self._available: bool = False
        self._ready: bool = False

        self._init_data()

        self._cloud_connection = cloud_connection
        self._device_connection = device_connection
        self.editor = DreameMapVacuumMapEditor(self)

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

        map_data_result = self._cloud_connection.get_device_property(
            DIID(DreameVacuumProperty.MAP_DATA), 20, self._latest_map_data_time
        )
        if map_data_result is None:
            _LOGGER.warn("Getting map_data from cloud failed")
            map_data_result = []

        object_name_result = self._cloud_connection.get_device_property(
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
                    self._request_next_p_map(
                        self._latest_map_id, next_frame_id)

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
            return self._device_connection.action(mapping["siid"], mapping["aiid"], payload, 0, 2)
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
            and time.time() - self._last_p_request_time < 3
        ):
            return

        self._last_p_request_map_id = map_id
        self._last_p_request_frame_id = frame_id
        self._last_p_request_time = time.time()

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
        result = self._request_map(
            {
                MAP_REQUEST_PARAMETER_REQ_TYPE: 1,
                MAP_REQUEST_PARAMETER_MAP_ID: map_id,
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

        self.update()
        self.schedule_update(self._update_interval)

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
        if self._cloud_connection._logged_in:
            if object_name is None or object_name == "":
                _LOGGER.debug("Get object name from cloud")
                object_name_result = self._cloud_connection.get_device_property(
                    DIID(DreameVacuumProperty.OBJECT_NAME)
                )
                if object_name_result:
                    object_name_result = json.loads(
                        object_name_result[0][MAP_PARAMETER_VALUE])
                    object_name = object_name_result[0]

            if object_name is None or object_name == "":
                object_name = f"{str(self._cloud_connection._uid)}/{str(self._cloud_connection._did)}/0"

            url = self._get_interim_file_url(object_name)
            if url:
                _LOGGER.debug("Request map data from cloud %s", url)
                response = self._cloud_connection.get_file(url)
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
            response = self._cloud_connection.get_interim_file_url(object_name)
            if response and response.get(MAP_PARAMETER_RESULT):
                self._file_urls[object_name] = response[MAP_PARAMETER_RESULT]
                url = self._file_urls[object_name][MAP_PARAMETER_URL]
        return url

    def _decode_map_partial(self, raw_map, timestamp=None, key=None) -> MapDataPartial | None:
        partial_map = DreameVacuumMapDecoder.decode_map_partial(raw_map, key)
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
                    self._queue_partial_map(map_data)

                    if self._map_request_time is None:
                        self._request_i_map()
                        return

                if partial_map.frame_id != self._current_frame_id + 1:
                    if partial_map.frame_id <= self._current_frame_id:
                        self._add_next_map_data()
                        return

                    self._queue_partial_map(map_data)
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
                    partial_map, self._map_data
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
                ) = DreameVacuumMapDecoder.decode_map_data_from_partial(partial_map)
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
                    changed = (
                        self._current_frame_id is None
                        or self._map_data is None
                        or map_data != self._map_data
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
                                    and self._map_data.saved_map_status == 2
                                ):
                                    map_data.active_segments = (
                                        self._map_data.active_segments
                                    )
                                    map_data.active_areas = self._map_data.active_areas
                                    map_data.active_points = self._map_data.active_points
                                    map_data.path = self._map_data.path
                                    map_data.segments = self._map_data.segments
                                    changed = map_data != self._map_data
                                else:
                                    changed = False
                                    map_data.empty_map = True
                            else:
                                self._updated_frame_id = None

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

    def get_map_by_id(self, map_id: int = 0) -> MapData | None:
        if map_id:
            if map_id in self._saved_map_data:
                return self._saved_map_data[map_id]
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
                if self._map_data and not self._map_data.empty_map:
                    _LOGGER.info(
                        "Need map request: %.2f",
                        time.time() - (self._current_timestamp_ms / 1000.0),
                    )
                if self._map_data and not self._map_data.empty_map and time.time() - (self._current_timestamp_ms / 1000.0) > 30:
                    self.request_new_map()
                else:
                    self._request_current_map()
            else:
                if not self._request_map_from_cloud():
                    if self._device_running:
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
                _LOGGER.warning("Map update Failed: %s", traceback.format_exc())
                self._available = False
                if self._error_callback:
                    self._error_callback(DeviceUpdateFailedException(ex))

        self._ready = True
        self._update_running = False

    def set_aes_iv(self, aes_iv: str) -> None:
        if aes_iv:
            DreameVacuumMapDecoder.AES_IV = aes_iv

    def set_update_interval(self, update_interval: float) -> None:
        if self._update_interval != update_interval:
            self._update_interval = update_interval
            self.schedule_update()

    def set_device_running(self, device_running: bool) -> None:
        if self._device_running != device_running:
            self.schedule_update(2)
        self._device_running = device_running

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
            out = result[MAP_PARAMETER_OUT]
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
                        self.schedule_update(1)
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
        if self._map_list_object_name:
            _LOGGER.info("Get Map List: %s", self._map_list_object_name)
            response = self._get_interim_file_data(self._map_list_object_name)
            if response:
                self._need_map_list_request = False
                raw_map = response.decode()
                
                try:
                    map_info = json.loads(raw_map)
                except:
                    _LOGGER.warn("Get Map List failed")
                    return

                saved_map_list = map_info[MAP_PARAMETER_MAPSTR]
                changed = False
                now = time.time()
                map_list = {}
                if saved_map_list:
                    for v in saved_map_list:
                        if v.get(MAP_PARAMETER_MAP):
                            saved_map_data = DreameVacuumMapDecoder.decode_saved_map(
                                v[MAP_PARAMETER_MAP], int(v[MAP_PARAMETER_ANGLE]) if v.get(
                                    MAP_PARAMETER_ANGLE) else 0
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
                                response = self._cloud_connection.get_file_url(
                                    object_name)
                            else:
                                response = self._cloud_connection.get_interim_file_url(
                                    object_name)

                            if response and response.get(MAP_PARAMETER_RESULT):
                                map_url = response[MAP_PARAMETER_RESULT][MAP_PARAMETER_URL]
                                recovery_map_data = DreameVacuumMapDecoder.decode_saved_map(
                                    map_info[MAP_PARAMETER_THB], self._saved_map_data[map_id].rotation)
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
                new_segments = DreameVacuumMapDecoder.get_segments(map_data)
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

    def set_segment_order(self, segment_id: int, order: int) -> list[int] | None:
        map_data = self._map_data
        if (
            map_data
            and map_data.segments
            and segment_id in map_data.segments
            and not map_data.temporary_map
        ):
            cleaning_order = []

            if order > 0:
                index = 1
                # for k in sorted(map_data.segments, key=lambda segment: segment):
                for (k, v) in map_data.segments.items():
                    if not map_data.segments[k].order:
                        map_data.segments[k].order = index
                        map_data.cleanset[str(segment_id)][3] = index
                    index = index + 1

                current_order = map_data.segments[segment_id].order
                if current_order != order:
                    map_data.segments[segment_id].order = order
                    for (k, v) in map_data.segments.items():
                        if k != segment_id and v.order == order:
                            map_data.segments[k].order = current_order
                            map_data.cleanset[str(segment_id)][3] = order

                for segment_id in sorted(
                    map_data.segments,
                    key=lambda segment_id: map_data.segments[segment_id].order,
                ):
                    cleaning_order.append(segment_id)
            else:
                for (k, v) in map_data.segments.items():
                    map_data.segments[k].order = 0
                    map_data.cleanset[str(segment_id)][3] = 0

            self._set_updated_frame_id(map_data.frame_id)
            self.refresh_map()
            return cleaning_order

    def cleanset(self, map_data: MapData) -> list[list[int]] | None:
        cleanset = []
        for (k, v) in map_data.segments.items():
            if v.suction_level is None:
                v.suction_level = 1
            if v.water_volume is None:
                v.water_volume = 2
            if v.cleaning_times is None:
                v.cleaning_times = 1

            cleanset.append(
                [
                    k,
                    v.suction_level,
                    v.water_volume + 1,
                    v.cleaning_times,
                ]
            )
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
            self._set_updated_frame_id(map_data.frame_id)
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
            self._set_updated_frame_id(map_data.frame_id)
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
            self._set_updated_frame_id(map_data.frame_id)
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
                        if custom_name is "":
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

                self._set_updated_frame_id(map_data.frame_id)
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
    AES_IV = ""

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
    def _get_pixel_type(map_data: MapData, pixel) -> MapPixelType:
        if map_data.frame_map:
            segment_id = pixel >> 2

            if 0 < segment_id < 64:
                if segment_id is 63:
                    return MapPixelType.WALL.value
                if segment_id is 62:
                    return MapPixelType.FLOOR.value
                if segment_id is 61:
                    return MapPixelType.UNKNOWN.value
                return segment_id

            segment_id = pixel & 0b00000011
            # as implemented on the app
            if segment_id == 1 or segment_id == 3:
                return MapPixelType.NEW_SEGMENT.value
            if segment_id == 2:
                return MapPixelType.WALL.value
        else:
            if pixel >> 7:
                return MapPixelType.WALL.value

            segment_id = pixel & 0b01111111
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
    def decode_map_partial(raw_map, key=None) -> MapDataPartial | None:
        raw_map = raw_map.replace("_", "/").replace("-", "+")

        if "," in raw_map and key is None:
            values = raw_map.split(",")
            key = values[1]
            raw_map = values[0]

        raw_map = base64.decodebytes(raw_map.encode("utf8"))                           

        if key is not None:
            try:
                key = hashlib.sha256(key.encode()).hexdigest()[0:32].encode('utf8')
                iv = DreameVacuumMapDecoder.AES_IV.encode('utf8')
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                raw_map = decryptor.update(raw_map) + decryptor.finalize()
            except Exception as ex:
                _LOGGER.error("Map data decryption failed: %s. Private key might be missing, please report this issue with your device model https://github.com/Tasshack/dreame-vacuum/issues/new?assignees=Tasshack&labels=bug&template=bug_report.md&title=Map%20data%20decryption%20failed", ex)
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
        partial_map.frame_id = DreameVacuumMapDecoder._read_int_16_le(raw_map, 2)
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
    def decode_map(raw_map: str, rotation: int = 0) -> Tuple[MapData, Optional[MapData]]:
        return DreameVacuumMapDecoder.decode_map_data_from_partial(
            DreameVacuumMapDecoder.decode_map_partial(raw_map), rotation
        )

    @staticmethod
    def decode_saved_map(raw_map: str, rotation: int = 0) -> MapData | None:
        return DreameVacuumMapDecoder.decode_map(raw_map, rotation)[0]

    @staticmethod
    def decode_map_data_from_partial(
        partial_map: MapDataPartial, rotation: int = 0
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
                    r"(?P<operator>[SLl])(?P<x>-?\d+),(?P<y>-?\d+)"
                ).finditer(data_json["tr"])
            ]
            current_position = Point(0, 0)
            map_data.path = []
            for match in matches:
                operator = match["operator"]

                # You will only get "l" paths with in a P frame.
                # It means path is connected with the path from previous frame and it should be rendered as a line.
                absolute_point = operator == "l"
                if operator == "S" or absolute_point:
                    if absolute_point:
                        current_position = Path(
                            int(match["x"]), int(match["y"]), True)
                    else:
                        current_position = Path(
                            int(match["x"]), int(match["y"]), False)
                elif operator == "L":
                    current_position = Path(
                        current_position.x + int(match["x"]),
                        current_position.y + int(match["y"]),
                        True,
                    )
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
                                        if segment_id is 63:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.WALL.value
                                        elif segment_id is 62:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.FLOOR.value
                                        elif segment_id is 61:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.UNKNOWN.value
                                        else:
                                            map_data.pixel_type[x,
                                                                y] = segment_id
                                    else:
                                        segment_id = pixel & 0b00000011
                                        if segment_id == 1 or segment_id == 3:
                                            map_data.pixel_type[x,
                                                                y] = MapPixelType.NEW_SEGMENT.value
                                        elif segment_id == 2:
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
                                        segment_id = pixel & 0b01111111
                                        if segment_id > 0:
                                            if (
                                                map_data.saved_map_status == 1
                                                or map_data.saved_map_status == 0
                                            ):
                                                # as implemented on the app
                                                if segment_id == 1 or segment_id == 3:
                                                    map_data.pixel_type[x,
                                                                        y] = MapPixelType.NEW_SEGMENT.value
                                                elif segment_id == 2:
                                                    map_data.pixel_type[x,
                                                                        y] = MapPixelType.WALL.value
                                            elif segment_id < 64:
                                                map_data.pixel_type[x,
                                                                    y] = segment_id

                    segments = DreameVacuumMapDecoder.get_segments(map_data)
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
        if data_json.get("rism"):
            saved_map_data = DreameVacuumMapDecoder.decode_saved_map(
                data_json["rism"], map_data.rotation
            )

            if saved_map_data is not None:
                saved_map_data.timestamp_ms = map_data.timestamp_ms
                map_data.saved_map_id = saved_map_data.map_id
                if saved_map_data.temporary_map:
                    map_data.temporary_map = saved_map_data.temporary_map

                if map_data.restored_map or map_data.recovery_map:
                    map_data.segments = copy.deepcopy(saved_map_data.segments)
                    map_data.data = saved_map_data.data
                    map_data.pixel_type = saved_map_data.pixel_type
                    map_data.dimensions = saved_map_data.dimensions
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
                    saved_map_data.cleanset = map_data.cleanset

                if map_data.saved_map_status == 2:
                    if not map_data.no_go_areas:
                        map_data.no_go_areas = saved_map_data.no_go_areas
                    if not map_data.no_mopping_areas:
                        map_data.no_mopping_areas = saved_map_data.no_mopping_areas
                    if not map_data.walls:
                        map_data.walls = saved_map_data.walls
                    if (
                        map_data.charger_position is None
                        and not map_data.saved_map
                        and saved_map_data.charger_position
                    ):
                        map_data.charger_position = saved_map_data.charger_position

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
            if data_json["vw"].get("rect"):
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

            if data_json["vw"].get("mop"):
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

            if data_json["vw"].get("line"):
                map_data.walls = [
                    Wall(
                        virtual_wall[0],
                        virtual_wall[1],
                        virtual_wall[2],
                        virtual_wall[3],
                    )
                    for virtual_wall in data_json["vw"]["line"]
                ]

        return map_data, saved_map_data

    @staticmethod
    def decode_p_map_data_from_partial(
        partial_map: MapDataPartial, current_map_data: MapData
    ) -> MapData | None:
        if partial_map.frame_type != MapFrameType.P.value:
            return None

        map_data, saved_map_data = DreameVacuumMapDecoder.decode_map_data_from_partial(
            partial_map
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
        if map_data.charger_position is not None:
            current_map_data.charger_position = map_data.charger_position

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
                            current_map_data, int(data[new_index])
                        )

            # Update size and buffer
            current_map_data.data = bytes(data)
            current_map_data.pixel_type = pixel_type
            current_map_data.dimensions = MapImageDimensions(
                top, left, height, width, grid_size
            )

        if map_data.path:
            # Append new paths received with P frame
            if current_map_data.path:
                current_map_data.path.extend(map_data.path)
            else:
                current_map_data.path = map_data.path

        DreameVacuumMapDecoder.set_robot_segment(current_map_data)

        # if (robotPos.l2r == true && _this.robotPos.l2r == true) {
        #    _this.lastPos = _this.robotPos
        # } else {
        #    _this.lastPos = undefined
        # }
        return current_map_data

    @staticmethod
    def get_segments(map_data: MapData) -> dict[str, Any]:
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

                    item = cleanset[segment_id]

                    map_data.segments[k].suction_level = item[0]
                    map_data.segments[k].water_volume = (
                        item[1] - 1
                    )  # for some reason cleanset uses different int values for water volume
                    map_data.segments[k].cleaning_times = item[2]
                    map_data.segments[k].order = item[3]
                else:
                    map_data.segments[k].suction_level = None
                    map_data.segments[k].water_volume = None
                    map_data.segments[k].cleaning_times = None
                    map_data.segments[k].order = None

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

        if self._map_data is None or self._map_data.path != map_data.path or not self._layers.get(MapRendererLayer.PATH):
            points = []
            self._layers[MapRendererLayer.PATH] = []
            if map_data.path and len(map_data.path) > 1:
                s = map_data.path[0]
                for point in map_data.path[1:]:
                    if point.line:
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


class DreameVacuumMapRenderer:
    MAP_COLOR_SCHEME_LIST: Final = {
        0: MapRendererColorScheme(
            name = "Dreame Light",
        ),
        1: MapRendererColorScheme(
            name = "Dreame Dark",
            floor = (110, 110, 110, 255),
            wall = (64, 64, 64, 255),
            passive_segment = (100, 100, 100, 255),
            new_segment = (0, 91, 244, 255),
            no_go = (133, 0, 0, 128),
            no_go_outline = (149, 0, 0, 200),
            no_mop = (134, 0, 226, 128),
            no_mop_outline = (115, 0, 157, 200),
            virtual_wall = (133, 0, 0, 200),
            active_area = (200, 200, 200, 80),
            active_area_outline = (9, 54, 129, 200),
            active_point = (200, 200, 200, 80),
            active_point_outline = (9, 54, 129, 200),
            path = (200, 200, 200, 255),
            segment = (
                [(13, 64, 155, 255), (0, 55, 150, 255)],
                [(143, 75, 7, 255), (117, 53, 0, 255)],
                [(0, 106, 176, 255), (0, 96, 158, 255)],
                [(76, 107, 36, 255), (44, 107, 36, 255)],
            ),
            settings_icon_background = (255, 255, 255, 185),
            dark = True,
        ),        
        2: MapRendererColorScheme(
            name = "Mijia Light",
            segment = (
                [(131, 178, 255, 255), (105, 142, 204, 255)],
                [(245, 201, 66, 255), (196, 161, 53, 255)],
                [(103, 207, 229, 255), (82, 165, 182, 255)],
                [(255, 155, 101, 255), (204, 124, 81, 255)],
            ),
            new_segment = (131, 178, 255, 255),
            virtual_wall = (255, 45, 45, 200),
            no_go = (230, 30, 30, 128),
            no_go_outline = (255, 45, 45, 200),
        ),
        3: MapRendererColorScheme(
            name = "Mijia Dark",
            segment = (
                [(108, 141, 195, 255), (76, 99, 137, 255)],
                [(188, 157, 62, 255), (133, 111, 44, 255)],
                [(88, 161, 176, 255), (62, 113, 123, 255)],
                [(195, 125, 87, 255), (138, 89, 62, 255)],
            ),
            floor = (150, 150, 150, 255),
            wall = (119, 133, 153, 255),
            new_segment = (99, 148, 230, 255),
            passive_segment = (100, 100, 100, 255),
            no_go = (133, 0, 0, 128),
            no_go_outline = (149, 0, 0, 200),
            no_mop = (134, 0, 226, 128),
            no_mop_outline = (115, 0, 157, 200),
            virtual_wall = (133, 0, 0, 200),
            active_area = (200, 200, 200, 80),
            active_area_outline = (9, 54, 129, 200),
            active_point = (200, 200, 200, 80),
            active_point_outline = (9, 54, 129, 200),
            path = (200, 200, 200, 255),
            settings_icon_background = (255, 255, 255, 185),
            dark = True,
        ),
        4: MapRendererColorScheme(
            name = "Grayscale",
            floor = (100, 100, 100, 255),
            wall = (40, 40, 40, 255),
            passive_segment = (50, 50, 50, 255),
            new_segment = (80, 80, 80, 255),
            no_go = (133, 0, 0, 128),
            no_go_outline = (149, 0, 0, 200),
            no_mop = (134, 0, 226, 128),
            no_mop_outline = (115, 0, 157, 200),
            virtual_wall = (133, 0, 0, 200),
            active_area = (221, 221, 221, 80),
            active_area_outline = (22, 103, 238, 200),
            active_point = (221, 221, 221, 80),
            active_point_outline = (22, 103, 238, 200),
            path = (200, 200, 200, 255),
            segment = (
                [(90, 90, 90, 255), (95, 95, 95, 255)],
                [(80, 80, 80, 255), (85, 85, 85, 255)],
                [(70, 70, 70, 255), (75, 75, 75, 255)],
                [(60, 60, 60, 255), (65, 65, 65, 255)],
            ),
            icon_background = (200, 200, 200, 200),
            settings_icon_background = (255, 255, 255, 205),
            text = (0, 0, 0, 255),
            text_stroke = (0, 0, 0, 100),
            invert = True,
            dark = True,
        ),
    }

    def __init__(self, color_scheme: int = 0, robot_shape: int = 0) -> None:
        self._image = None
        self.color_scheme: MapRendererColorScheme = DreameVacuumMapRenderer.MAP_COLOR_SCHEME_LIST.get(color_scheme, MapRendererColorScheme())
        self.config: MapRendererConfig = MapRendererConfig()
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

        self._charger_icon = None
        self._robot_icon = None
        self._robot_charging_icon = None
        self._robot_cleaning_icon = None
        self._robot_warning_icon = None
        self._robot_sleeping_icon = None
        self._robot_washing_icon = None

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

        self._cleaning_times_icon = [
            Image.open(BytesIO(base64.b64decode(
                MAP_ICON_REPEATS_ONE))).convert("RGBA"),
            Image.open(BytesIO(base64.b64decode(
                MAP_ICON_REPEATS_TWO))).convert("RGBA"),
            Image.open(BytesIO(base64.b64decode(MAP_ICON_REPEATS_THREE))).convert(
                "RGBA"
            ),
        ]

        self._suction_level_icon = [
            Image.open(BytesIO(base64.b64decode(MAP_ICON_SUCTION_LEVEL_QUIET))).convert(
                "RGBA"
            ),
            Image.open(BytesIO(base64.b64decode(MAP_ICON_SUCTION_LEVEL_STANDART))).convert(
                "RGBA"
            ),
            Image.open(BytesIO(base64.b64decode(MAP_ICON_SUCTION_LEVEL_STRONG))).convert(
                "RGBA"
            ),
            Image.open(BytesIO(base64.b64decode(MAP_ICON_SUCTION_LEVEL_TURBO))).convert(
                "RGBA"
            ),
        ]

        self._water_volume_icon = [
            Image.open(BytesIO(base64.b64decode(MAP_ICON_WATER_VOLUME_LOW))).convert(
                "RGBA"
            ),
            Image.open(BytesIO(base64.b64decode(MAP_ICON_WATER_VOLUME_MEDIUM))).convert(
                "RGBA"
            ),
            Image.open(BytesIO(base64.b64decode(MAP_ICON_WATER_VOLUME_HIGH))).convert(
                "RGBA"
            ),
        ]

        self._segment_icons = {}
        for (k, v) in SEGMENT_TYPE_CODE_TO_ICON.items():
            self._segment_icons[k] = Image.open(BytesIO(base64.b64decode(v))).convert(
                "RGBA"
            )
            if self.color_scheme.invert:
                enhancer = ImageEnhance.Brightness(self._segment_icons[k])
                self._segment_icons[k] = enhancer.enhance(0.1)

        self.font_file = base64.b64decode(MAP_FONT)

    @staticmethod
    def _to_buffer(image) -> bytes:
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
    def _calculate_padding(dimensions, no_mopping_areas, no_go_areas, walls, padding) -> list[int]:
        if no_mopping_areas or no_go_areas or walls:
            min_x = 0
            min_y = 0
            max_x = dimensions.width
            max_y = dimensions.height

            if no_mopping_areas:
                for area in no_mopping_areas:
                    p = area.to_img(dimensions)
                    x_coords = sorted([p.x0, p.x1, p.x2, p.x3])
                    y_coords = sorted([p.y0, p.y1, p.y2, p.y3])

                    if x_coords[0] < min_x:
                        min_x = x_coords[0]
                    if x_coords[3] > max_x:
                        max_x = x_coords[3]
                    if y_coords[0] < min_y:
                        min_y = y_coords[0]
                    if y_coords[3] > max_y:
                        max_y = y_coords[3]

            if no_go_areas:
                for area in no_go_areas:
                    p = area.to_img(dimensions)
                    x_coords = sorted([p.x0, p.x1, p.x2, p.x3])
                    y_coords = sorted([p.y0, p.y1, p.y2, p.y3])

                    if x_coords[0] < min_x:
                        min_x = x_coords[0]
                    if x_coords[3] > max_x:
                        max_x = x_coords[3]
                    if y_coords[0] < min_y:
                        min_y = y_coords[0]
                    if y_coords[3] > max_y:
                        max_y = y_coords[3]

            if walls:
                for wall in walls:
                    p = wall.to_img(dimensions)
                    x_coords = sorted([p.x0, p.x1])
                    y_coords = sorted([p.y0, p.y1])

                    if x_coords[0] < min_x:
                        min_x = x_coords[0]
                    if x_coords[1] > max_x:
                        max_x = x_coords[1]
                    if y_coords[0] < min_y:
                        min_y = y_coords[0]
                    if y_coords[1] > max_y:
                        max_y = y_coords[1]

            if min_x < 0:
                padding[0] = padding[0] + int(-min_x)
            if max_x > dimensions.width:
                padding[1] = padding[1] + int(max_x - dimensions.width)
            if min_y < 0:
                padding[2] = padding[2] + int(-min_y)
            if max_y > dimensions.height:
                padding[3] = padding[3] + int(max_y - dimensions.height)

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
        if map_data is None or map_data.empty_map:
            return self.default_map_image

        self.render_complete = False
        now = time.time()

        if map_data.saved_map:
            robot_status = 0

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
            and self._image
        ):
            self.render_complete = True
            _LOGGER.info("Skip render frame, map data not changed")
            return self._to_buffer(self._image)

        if (
            self._map_data is None
            or self._map_data.no_mopping_areas != map_data.no_mopping_areas
            or self._map_data.no_go_areas != map_data.no_go_areas
            or self._map_data.walls != map_data.walls
            or self._map_data.saved_map_status != map_data.saved_map_status
            or self._map_data.restored_map != map_data.restored_map
            or self._map_data.recovery_map != map_data.recovery_map
        ):
            map_data.dimensions.scale = 1
            map_data.dimensions.padding = DreameVacuumMapRenderer._calculate_padding(
                map_data.dimensions,
                map_data.no_mopping_areas,
                map_data.no_go_areas,
                map_data.walls,
                [6, 6, 6, 6]
                if map_data.saved_map or map_data.restored_map or map_data.recovery_map
                else [10, 10, 10, 10],
            )
            self._map_data = None
        else:
            map_data.dimensions.padding = self._map_data.dimensions.padding

        map_data.dimensions.scale = 4 if map_data.saved_map_status == 2 or map_data.saved_map else 3
        
        if self._map_data is None or (
            self._map_data.dimensions.scale != map_data.dimensions.scale
            or self._map_data.rotation != map_data.rotation
        ):
            self._charger_icon = None
            self._robot_sleeping_icon = None
            if (
                self._map_data is None
                or self._map_data.dimensions.scale != map_data.dimensions.scale
            ):
                self._robot_icon = None
                self._robot_charging_icon = None
                self._robot_cleaning_icon = None
                self._robot_warning_icon = None
                self._robot_washing_icon = None

        if (
            self._map_data is None
            or not self._layers.get(MapRendererLayer.IMAGE)
            or self._map_data.active_segments != map_data.active_segments
            or self._map_data.active_areas != map_data.active_areas
            or self._map_data.segments != map_data.segments
            or self._map_data.data != map_data.data
        ):
            self._calibration_points = self._calculate_calibration_points(
                map_data)

            area_colors = {}
            # as implemented on the app
            area_colors[MapPixelType.OUTSIDE.value] = self.color_scheme.outside
            area_colors[MapPixelType.WALL.value] = self.color_scheme.wall
            area_colors[MapPixelType.FLOOR.value] = self.color_scheme.floor
            area_colors[MapPixelType.UNKNOWN.value] = self.color_scheme.floor
            area_colors[MapPixelType.NEW_SEGMENT.value] = self.color_scheme.new_segment

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
                    (
                        map_data.dimensions.height
                        + (
                            map_data.dimensions.padding[2]
                            + map_data.dimensions.padding[3]
                        )
                    ),
                    (
                        map_data.dimensions.width
                        + (
                            map_data.dimensions.padding[0]
                            + map_data.dimensions.padding[1]
                        )
                    ),
                    4,
                ),
                area_colors[MapPixelType.OUTSIDE.value],
                dtype=np.uint8,
            )

            for y in range(map_data.dimensions.height):
                for x in range(map_data.dimensions.width):
                    px_type = int(map_data.pixel_type[x, y])
                    if px_type not in area_colors:
                        px_type = MapPixelType.NEW_SEGMENT.value

                    if px_type != MapPixelType.OUTSIDE.value:
                        xx = (
                            x + map_data.dimensions.padding[0]
                        ) 
                        yy = (
                            (map_data.dimensions.height - y - 1)
                            + map_data.dimensions.padding[2]
                        ) 
                        pixels[yy, xx] = area_colors[px_type]

            pixels = pixels.repeat(map_data.dimensions.scale, axis=0).repeat(map_data.dimensions.scale, axis=1)

            self._layers[MapRendererLayer.IMAGE] = Image.fromarray(pixels)

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

        if map_data.segments and (self.config.icon or self.config.name or self.config.order or self.config.suction_level or self.config.water_volume or self.config.cleaning_times):
            if (
                self._map_data is None
                or self._map_data.segments != map_data.segments
                or self._map_data.cleanset != map_data.cleanset
                or self._map_data.rotation != map_data.rotation
                or not self._layers.get(MapRendererLayer.SEGMENTS)
            ):
                self._layers[MapRendererLayer.SEGMENTS] = self.render_segments(
                    map_data.segments.values(),
                    map_data.cleanset,
                    layer,
                    map_data.dimensions,
                    5 * map_data.dimensions.scale,
                    map_data.rotation,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.SEGMENTS])

        if map_data.charger_position and self.config.charger:
            if (
                self._map_data is None
                or self._map_data.charger_position != map_data.charger_position
                or self._map_data.rotation != map_data.rotation
                or bool(self._robot_status > 5) != bool(robot_status > 5)
                or not self._layers.get(MapRendererLayer.CHARGER)
            ):
                self._layers[MapRendererLayer.CHARGER] = self.render_charger(
                    map_data.charger_position,
                    robot_status,
                    layer,
                    map_data.dimensions,
                    int((7 * map_data.dimensions.scale * scale) * 1.2),
                    map_data.rotation,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.CHARGER])

        if map_data.robot_position and self.config.robot:
            if (
                self._map_data is None
                or self._map_data.robot_position != map_data.robot_position
                or self._map_data.rotation != map_data.rotation
                or self._robot_status != robot_status
                or not self._layers.get(MapRendererLayer.ROBOT)
            ):
                self._layers[MapRendererLayer.ROBOT] = self.render_vacuum(
                    map_data.robot_position,
                    robot_status,
                    layer,
                    map_data.dimensions,
                    int(7 * map_data.dimensions.scale * scale),
                    map_data.rotation,
                    scale,
                )
            layer = Image.alpha_composite(
                layer, self._layers[MapRendererLayer.ROBOT])

        if layer.size != map_image.size:
            layer.thumbnail(map_image.size, Image.Resampling.BOX, reducing_gap=1.5)

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
        size = 15 * 50
        for point in points:
            area = Area(point.x - size, point.y - size, point.x + size, point.y - size, point.x + size, point.y + size, point.x - size, point.y + size)

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
        if len(path) > 1:
            draw = ImageDraw.Draw(new_layer, "RGBA")
            s = path[0].to_img(dimensions)
            for point in path[1:]:
                e = point.to_img(dimensions)
                if point.line:
                    draw.line(
                        [s.x * scale, s.y * scale, e.x * scale, e.y * scale],
                        width=int(width * scale),
                        fill=color,
                    )
                s = e
        return new_layer

    def render_charger(
        self, charger_position, robot_status, layer, dimensions, size, map_rotation, scale
    ):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        if self._charger_icon is None:
            self._charger_icon = (
                Image.open(BytesIO(base64.b64decode(MAP_CHARGER_IMAGE)))
                .convert("RGBA")
                .resize((size, size))
                .rotate(-map_rotation)
            )
            if self.color_scheme.dark:
                enhancer = ImageEnhance.Brightness(self._charger_icon)
                self._charger_icon = enhancer.enhance(0.7)

        point = charger_position.to_img(dimensions)
        new_layer.paste(
            self._charger_icon,
            (int((point.x * scale) - (size / 2)),
             int((point.y * scale) - (size / 2))),
            self._charger_icon,
        )
        
        if robot_status > 5:
            if self._robot_washing_icon is None:
                self._robot_washing_icon = (
                    Image.open(BytesIO(base64.b64decode(MAP_ROBOT_WASHING_IMAGE)))
                    .convert("RGBA")
                    .resize((int(size * 1.25), int(size * 1.25)))
                    .rotate(-map_rotation)
                )
                enhancer = ImageEnhance.Brightness(self._robot_washing_icon)
                if self.color_scheme.dark:
                    self._robot_washing_icon = enhancer.enhance(0.65)

            icon = self._robot_washing_icon

            icon_x = point.x * scale
            icon_y = point.y * scale
            offset = (size * 1.5)
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
        if self._robot_icon is None:            
            if self._robot_shape == 1:
                robot_image = MAP_ROBOT_MOP_IMAGE
            else:
                robot_image = MAP_ROBOT_IMAGE

            self._robot_icon = (
                Image.open(BytesIO(base64.b64decode(robot_image)))
                .convert("RGBA")
                .resize((size, size))
            )

            if self._robot_shape == 0:
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
                    .resize(((int(size * 1.25), int(size * 1.25))))
                )
            status_icon = self._robot_cleaning_icon
        elif robot_status == 2:
            if self._robot_charging_icon is None:
                self._robot_charging_icon = (
                    Image.open(
                        BytesIO(base64.b64decode(MAP_ROBOT_CHARGING_IMAGE)))
                    .convert("RGBA")
                    .resize(((int(size * 1.3), int(size * 1.3))))
                )
            status_icon = self._robot_charging_icon
        elif robot_status == 3 or robot_status == 5 or robot_status == 6:
            if self._robot_warning_icon is None:
                self._robot_warning_icon = (
                    Image.open(
                        BytesIO(base64.b64decode(MAP_ROBOT_WARNING_IMAGE)))
                    .convert("RGBA")
                    .resize(((int(size * 1.3), int(size * 1.3))))
                )
            status_icon = self._robot_warning_icon

        if status_icon:
            new_layer.paste(
                status_icon,
                (
                    int(point.x * scale - (status_icon.size[0] / 2)),
                    int(point.y * scale - (status_icon.size[1] / 2)),
                ),
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
                    sleeping_icon.resize(((int(size * 0.3), int(size * 0.3)))),
                    sleeping_icon.resize(
                        ((int(size * 0.35), int(size * 0.35)))),
                ]

            for k in [[19, 10, 0], [24, 24, 1]]:
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

    def render_segments(
        self, segments, cleanset, layer, dimensions, size, rotation, scale
    ):
        new_layer = Image.new("RGBA", layer.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(new_layer, "RGBA")
        for segment in segments:
            if segment.x is not None and segment.y is not None:
                text = None
                if segment.type == 0 or not self.config.icon:
                    text = segment.name
                elif segment.index > 0:
                    text = str(segment.index)

                text_font = None
                order_font = None
                icon = None
                if text and self.config.name:
                    text_font = ImageFont.truetype(
                        BytesIO(self.font_file),
                        (scale * 19) if segment.index or not self.config.icon > 0 else (scale * 17),
                    )

                if segment.order and self.config.order:
                    order_font = ImageFont.truetype(
                        BytesIO(self.font_file), (scale * 21)
                    )

                p = Point(segment.x, segment.y).to_img(dimensions)
                x = p.x
                y = p.y

                if segment.type != 0 or text_font or not self.config.name:
                    icon_size = size * 1.3
                    icon = self._segment_icons.get(segment.type, 0)
                    x0 = x - size
                    y0 = y - size
                    x1 = x + size
                    y1 = y + size

                    if text_font:
                        tw, th = draw.textsize(text, text_font)
                        ws = tw / 4

                        if segment.index > 0 or not self.config.icon:
                            icon_size = size * 1.35
                            padding = icon_size / 2
                            text_offset = (icon_size / 2) + 2
                            icon_offset = 2
                            th = scale * 23
                        else:
                            icon_size = size * 1.15
                            padding = icon_size / 4
                            icon_offset = padding - 2
                            text_offset = icon_size / 2
                            th = scale * 19

                        if not self.config.icon:
                            text_offset = 0

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
                        draw_text.text(
                            (0, 0),
                            text,
                            font=text_font,
                            fill=self.color_scheme.text,
                            stroke_width=1,
                            stroke_fill=self.color_scheme.text_stroke,
                        )
                        icon_text = icon_text.rotate(-rotation, expand=1)
                        new_layer.paste(
                            icon_text, (int(tx), int(ty)), icon_text)
                    else:
                        draw.ellipse(
                            [x0 * scale, y0 * scale, x1 * scale, y1 * scale],
                            fill=self.color_scheme.icon_background,
                        )

                    if self.config.icon:
                        s = icon_size * scale
                        icon = icon.resize((int(s), int(s))).rotate(-rotation)
                        new_layer.paste(
                            icon, (int(x * scale - (s / 2)),
                                   int(y * scale - (s / 2))), icon
                        )

                custom = (
                    cleanset
                    and segment.suction_level is not None
                    and segment.water_volume is not None
                    and segment.cleaning_times is not None
                    and (self.config.suction_level or self.config.water_volume or self.config.cleaning_times)
                )
                if order_font or custom:
                    if icon or (not self.config.icon and self.config.name):
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
                        
                    if custom:
                        s = scale * 2
                        arrow = (s + 2) * scale

                        if order_font:
                            icon_count = 4
                        else:
                            icon_count = 3

                        if not self.config.suction_level:
                            icon_count = icon_count - 1
                        if not self.config.water_volume:
                            icon_count = icon_count - 1
                        if not self.config.cleaning_times:
                            icon_count = icon_count - 1                            
                    else:
                        icon_count = 1

                    if icon_count == 1:
                        s = scale * 3
                        arrow = 5 * scale
                    else:                        
                        s = scale * 3
                        arrow = 5 * scale
                        
                    padding = s + arrow
                    margin = s if icon_count > 1 else 0
                    radius = size
                    if custom:
                        radius = size - 2

                    icon_w = (
                        ((radius * icon_count * 2) * scale) +
                        (arrow * 2) + (margin * 2)
                    )
                    icon_h = ((radius * 2) * scale) + (arrow * 2)
                    r = icon_h - (padding * 2)
                    icon = Image.new("RGBA", (icon_w, icon_h),
                                     (255, 255, 255, 0))
                    icon_draw = ImageDraw.Draw(icon, "RGBA")

                    if segment.type != 0 or text_font:
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
                        tw, th = icon_draw.textsize(text, order_font)
                        icon_draw.text(
                            (
                                (icon_h - tw) / 2 + margin,
                                (icon_h - th - (4 * scale)) / 2,
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
                        s = icon_size * 0.85 * scale
                        
                        if self.config.suction_level:
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

                        if self.config.water_volume:
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

                        if self.config.cleaning_times:
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

    @property
    def calibration_points(self) -> dict[str, int]:
        return self._calibration_points

    @property
    def default_map_image(self) -> bytes:
        return self._to_buffer(self._default_map_image)

    @property
    def default_calibration_points(self) -> dict[str, int]:
        return self._default_calibration_points
