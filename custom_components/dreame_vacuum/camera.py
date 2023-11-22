from __future__ import annotations

import collections
import voluptuous as vol
from enum import IntEnum
import time
import asyncio
import traceback
from typing import Any, Dict, Final
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from aiohttp import web

from homeassistant.components.camera import (
    Camera,
    CameraEntityDescription,
    CameraView,
    ENTITY_ID_FORMAT,
    DEFAULT_CONTENT_TYPE,
    TOKEN_CHANGE_INTERVAL,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, CONTENT_TYPE_MULTIPART
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform, entity_registry
from .recorder import CAMERA_UNRECORDED_ATTRIBUTES

from .const import (
    DOMAIN,
    CONF_COLOR_SCHEME,
    CONF_ICON_SET,
    CONF_MAP_OBJECTS,
    CONF_LOW_RESOLUTION,
    CONF_SQUARE,
    MAP_OBJECTS,
    LOGGER,
)

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame.const import (
    STATE_UNKNOWN,
    STATUS_CODE_TO_NAME,
    ATTR_CALIBRATION,
    ATTR_CLEANING_HISTORY_PICTURE,
    ATTR_CRUISING_HISTORY_PICTURE,
    ATTR_OBSTACLE_PICTURE,
    ATTR_RECOVERY_MAP_PICTURE,
    ATTR_RECOVERY_MAP_FILE,
    ATTR_WIFI_MAP_PICTURE,
)
from .dreame.map import (
    DreameVacuumMapRenderer,
    DreameVacuumMapDataJsonRenderer,
)

DREAME_TOKEN_CHANGE_INTERVAL: Final = timedelta(minutes=60)

JSON_CONTENT_TYPE: Final = "application/json"
PNG_CONTENT_TYPE: Final = "image/png"

MAP_IMAGE_URL: Final = "/api/camera_proxy/{0}?token={1}&v={2}"
HISTORY_MAP_IMAGE_URL: Final = (
    "/api/camera_history_map_proxy/{0}?token={1}&index={2}&v={3}"
)
OBSTACLE_IMAGE_URL: Final = (
    "/api/camera_map_obstacle_proxy/{0}?token={1}&index={2}&v={3}"
)
RECOVERY_MAP_IMAGE_URL: Final = (
    "/api/camera_recovery_map_proxy/{0}?token={1}&index={2}&v={3}"
)
WIFI_MAP_IMAGE_URL: Final = "/api/camera_wifi_map_proxy/{0}?token={1}&v={2}"


class DreameVacuumMapType(IntEnum):
    FLOOR_MAP = 0
    WIFI_MAP = 1
    JSON_MAP_DATA = 2


@dataclass
class DreameVacuumCameraEntityDescription(
    DreameVacuumEntityDescription, CameraEntityDescription
):
    """Describes Dreame Vacuum Camera entity."""

    map_type: DreameVacuumMapType = DreameVacuumMapType.FLOOR_MAP


MAP_ICON = "mdi:map"

CAMERAS: tuple[CameraEntityDescription, ...] = (
    DreameVacuumCameraEntityDescription(key="map", icon=MAP_ICON),
    DreameVacuumCameraEntityDescription(
        key="map_data",
        icon=MAP_ICON,
        entity_category=EntityCategory.CONFIG,
        map_type=DreameVacuumMapType.JSON_MAP_DATA,
        entity_registry_enabled_default=False,
    ),
)


class CameraDataView(CameraView):
    """Camera view to serve the map data."""

    url = "/api/camera_map_data_proxy/{entity_id}"
    name = "api:camera:map_data"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera data."""
        if not camera.map_data_json:
            if not camera.available:
                raise web.HTTPServiceUnavailable()

            resources = request.query.get("resources")
            return web.Response(
                body=camera.map_data_string(
                    resources
                    and (resources == True or resources == "true" or resources == "1")
                ),
                content_type=JSON_CONTENT_TYPE,
            )
        raise web.HTTPNotFound()


class CameraObstacleView(CameraView):
    """Camera view to serve the map data obstacle image."""

    url = "/api/camera_map_obstacle_proxy/{entity_id}"
    name = "api:camera:map_obstacle"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera obstacle image."""
        if camera.map_index == 0:
            if not camera.available:
                raise web.HTTPServiceUnavailable()

            crop = request.query.get("crop")
            box = request.query.get("box")
            file = request.query.get("file")
            file = file and (file == True or file == "true" or file == "1")
            result, object_name = await camera.obstacle_image(
                request.query.get("index", 1),
                not box or (box and (box == True or box == "true" or box == "1")),
                not crop or (crop and (crop == True or crop == "true" or crop == "1")),
            )
            if result:
                response = web.Response(
                    body=result,
                    content_type=DEFAULT_CONTENT_TYPE,
                )
                if file:
                    response.headers[
                        "Content-Disposition"
                    ] = f'attachment; filename={object_name.replace(".jpg","").replace(".jpeg","")}.jpg'
                return response

        raise web.HTTPNotFound()


class CameraObstacleHistoryView(CameraView):
    """Camera view to serve the map history data obstacle image."""

    url = "/api/camera_map_obstacle_history_proxy/{entity_id}"
    name = "api:camera:map_obstacle_history"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera obstacle image."""
        if camera.map_index == 0:
            if not camera.available:
                raise web.HTTPServiceUnavailable()

            crop = request.query.get("crop")
            box = request.query.get("box")
            file = request.query.get("file")
            file = file and (file == True or file == "true" or file == "1")
            cruising = request.query.get("cruising")
            result, object_name = await camera.obstacle_history_image(
                request.query.get("index", 1),
                request.query.get("history_index", 1),
                cruising
                and (cruising == True or cruising == "true" or cruising == "1"),
                not box or (box and (box == True or box == "true" or box == "1")),
                not crop or (crop and (crop == True or crop == "true" or crop == "1")),
            )
            if result:
                response = web.Response(
                    body=result,
                    content_type=DEFAULT_CONTENT_TYPE,
                )
                if file:
                    response.headers[
                        "Content-Disposition"
                    ] = f'attachment; filename={object_name.replace(".jpg","").replace(".jpeg","")}.jpg'
                return response

        raise web.HTTPNotFound()


class CameraHistoryView(CameraView):
    """Camera view to serve the cleaning or cruising history map."""

    url = "/api/camera_history_map_proxy/{entity_id}"
    name = "api:camera:history_map"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera cleaning history or cruising data."""
        if not camera.map_data_json and camera.map_index == 0:
            if not camera.available:
                raise web.HTTPServiceUnavailable()

            data = request.query.get("data")
            data = data and (data == True or data == "true" or data == "1")
            cruising = request.query.get("cruising")
            resources = request.query.get("resources")
            info = request.query.get("info")
            result = await camera.history_map_image(
                request.query.get("index", 1),
                not info or (info and (info == True or info == "true" or info == "1")),
                cruising
                and (cruising == True or cruising == "true" or cruising == "1"),
                data,
                data
                and resources
                and (resources == True or resources == "true" or resources == "1"),
            )
            if result:
                return web.Response(
                    body=result,
                    content_type=JSON_CONTENT_TYPE if data else PNG_CONTENT_TYPE,
                )
        raise web.HTTPNotFound()


class CameraRecoveryView(CameraView):
    """Camera view to serve the recovery map."""

    url = "/api/camera_recovery_map_proxy/{entity_id}"
    name = "api:camera:recovery_map"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera recovery map data."""
        if not camera.map_data_json:
            if not camera.available:
                raise web.HTTPServiceUnavailable()

            index = request.query.get("index", 1)
            file = request.query.get("file")
            file = file and (file == True or file == "true" or file == "1")
            if file:
                result, map_url, object_name = await camera.recovery_map_file(index)
            else:
                data = request.query.get("data")
                data = data and (data == True or data == "true" or data == "1")
                resources = request.query.get("resources")
                info = request.query.get("info")
                result = await camera.recovery_map(
                    index,
                    not info
                    or (info and (info == True or info == "true" or info == "1")),
                    data,
                    data
                    and resources
                    and (resources == True or resources == "true" or resources == "1"),
                )
            if result:
                response = web.Response(
                    body=result,
                    content_type="application/x-tar+gzip"
                    if file
                    else JSON_CONTENT_TYPE
                    if data
                    else PNG_CONTENT_TYPE,
                )
                if file:
                    response.headers[
                        "Content-Disposition"
                    ] = f'attachment; filename={object_name.replace("/", "-").replace(".mb.tbz2", "")}.mb.tbz2'
                return response
        raise web.HTTPNotFound()


class CameraWifiView(CameraView):
    """Camera view to serve the saved wifi map."""

    url = "/api/camera_wifi_map_proxy/{entity_id}"
    name = "api:camera:wifi_map"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera wifi map data."""
        if not camera.map_data_json:
            if not camera.available:
                raise web.HTTPServiceUnavailable()

            data = request.query.get("data")
            data = data and (data == True or data == "true" or data == "1")
            resources = request.query.get("resources")
            result = await camera.wifi_map_data(
                data,
                data
                and resources
                and (resources == True or resources == "true" or resources == "1"),
            )
            if result:
                return web.Response(
                    body=result,
                    content_type=JSON_CONTENT_TYPE if data else PNG_CONTENT_TYPE,
                )
        raise web.HTTPNotFound()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Vacuum Camera based on a config entry."""
    coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.device.capability.map:
        color_scheme = entry.options.get(CONF_COLOR_SCHEME)
        icon_set = entry.options.get(CONF_ICON_SET)
        low_resolution = entry.options.get(CONF_LOW_RESOLUTION, False)
        square = entry.options.get(CONF_SQUARE, False)
        map_objects = entry.options.get(CONF_MAP_OBJECTS, MAP_OBJECTS.keys())

        async_add_entities(
            DreameVacuumCameraEntity(
                coordinator,
                description,
                color_scheme,
                icon_set,
                map_objects,
                low_resolution,
                square,
            )
            for description in CAMERAS
        )

        update_map_cameras = partial(
            async_update_map_cameras,
            coordinator,
            {},
            async_add_entities,
            color_scheme,
            icon_set,
            map_objects,
            low_resolution,
            square,
        )
        platform = entity_platform.current_platform.get()
        platform.async_register_entity_service(
            "update", {}, DreameVacuumCameraEntity.async_update.__name__
        )
        coordinator.async_add_listener(update_map_cameras)
        update_map_cameras()

        hass.http.register_view(CameraDataView(hass.data["camera"]))
        hass.http.register_view(CameraObstacleView(hass.data["camera"]))
        hass.http.register_view(CameraObstacleHistoryView(hass.data["camera"]))
        hass.http.register_view(CameraHistoryView(hass.data["camera"]))
        hass.http.register_view(CameraRecoveryView(hass.data["camera"]))
        hass.http.register_view(CameraWifiView(hass.data["camera"]))


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True


@callback
def async_update_map_cameras(
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, list[DreameVacuumCameraEntity]],
    async_add_entities,
    color_scheme: str,
    icon_set: str,
    map_objects: list[str],
    low_resolution: bool,
    square: bool,
) -> None:
    new_indexes = set(
        [k for k in range(1, len(coordinator.device.status.map_list) + 1)]
    )
    current_ids = set(current)
    new_entities = []

    for map_index in current_ids - new_indexes:
        async_remove_map_cameras(map_index, coordinator, current)

    for map_index in new_indexes - current_ids:
        current[map_index] = [
            DreameVacuumCameraEntity(
                coordinator,
                DreameVacuumCameraEntityDescription(
                    entity_category=EntityCategory.CONFIG,
                    icon="mdi:map-search",
                ),
                color_scheme,
                icon_set,
                map_objects,
                low_resolution,
                square,
                map_index,
            )
        ]

        if coordinator.device.capability.wifi_map and not low_resolution:
            current[map_index].append(
                DreameVacuumCameraEntity(
                    coordinator,
                    DreameVacuumCameraEntityDescription(
                        entity_category=EntityCategory.CONFIG,
                        icon="mdi:wifi-settings",
                        map_type=DreameVacuumMapType.WIFI_MAP,
                        entity_registry_enabled_default=False,
                    ),
                    color_scheme,
                    icon_set,
                    map_objects,
                    True,
                    square,
                    map_index,
                )
            )

        new_entities = new_entities + current[map_index]

    if new_entities:
        async_add_entities(new_entities)


def async_remove_map_cameras(
    map_index: str,
    coordinator: DreameVacuumDataUpdateCoordinator,
    current: dict[str, DreameVacuumCameraEntity],
) -> None:
    registry = entity_registry.async_get(coordinator.hass)
    entities = current[map_index]
    for entity in entities:
        if entity.entity_id in registry.entities:
            registry.async_remove(entity.entity_id)
        del entity
    del current[map_index]


class DreameVacuumCameraEntity(DreameVacuumEntity, Camera):
    """Defines a Dreame Vacuum Camera entity."""

    _unrecorded_attributes = frozenset(CAMERA_UNRECORDED_ATTRIBUTES)

    def __init__(
        self,
        coordinator: DreameVacuumDataUpdateCoordinator,
        description: DreameVacuumCameraEntityDescription,
        color_scheme: str = None,
        icon_set: str = None,
        map_objects: list[str] = None,
        low_resolution: bool = False,
        square: bool = False,
        map_index: int = 0,
    ) -> None:
        """Initialize a Dreame Vacuum Camera entity."""
        super().__init__(coordinator, description)
        self._generate_entity_id(ENTITY_ID_FORMAT)
        self.content_type = PNG_CONTENT_TYPE
        self.stream = None
        self._access_token_update_counter = 0
        self.access_tokens = collections.deque([], 2)
        self.async_update_token()
        self._rtsp_to_webrtc = False
        self._should_poll = True
        self._last_updated = -1
        self._frame_id = -1
        self._last_map_request = 0
        self._attr_is_streaming = True
        self._calibration_points = None
        self._task_status = None
        self._error = None
        self._proxy_renderer = None

        self._available = self.device.device_connected and self.device.cloud_connected
        if description.map_type == DreameVacuumMapType.JSON_MAP_DATA:
            self._renderer = DreameVacuumMapDataJsonRenderer()
            self.content_type = JSON_CONTENT_TYPE
        else:
            self._renderer = DreameVacuumMapRenderer(
                color_scheme,
                icon_set,
                ["charger"] if self.wifi_map else map_objects,
                self.device.capability.robot_type,
                low_resolution,
                square,
            )
            if not self.wifi_map:
                self._proxy_renderer = DreameVacuumMapRenderer(
                    color_scheme,
                    icon_set,
                    map_objects,
                    self.device.capability.robot_type,
                    low_resolution,
                    square,
                    False,
                )
        self._image = None
        self._default_map = True
        self._proxy_images = {}
        self.map_index = map_index
        self._state = STATE_UNAVAILABLE
        if self.map_index == 0 and not self.map_data_json:
            self._image = self._renderer.default_map_image

        map_data = self._map_data
        self._map_id = map_data.map_id if map_data else None

        if self.map_index:
            if map_data:
                self._map_name = map_data.custom_name
            else:
                self._map_name = None
            self._set_map_name(self.wifi_map)
            self._attr_unique_id = f"{self.device.mac}_{'wifi_' if self.wifi_map else ''}map_{self.map_index}"
            self.entity_id = f"camera.{self.device.name.lower().replace(' ','_')}_{'wifi_' if self.wifi_map else ''}map_{self.map_index}"
        else:
            self._attr_name = f"{self.device.name} Current {'Wifi ' if self.wifi_map else ''}{description.name}"
            self._attr_unique_id = f"{self.device.mac}_map_{'wifi_' if self.wifi_map else ''}{description.key}"
            self.entity_id = f"camera.{self.device.name.lower().replace(' ','_')}_{'wifi_' if self.wifi_map else ''}{description.key.lower()}"

        if self.map_index == 0 or self.map_data_json:
            self.update()

    def _set_map_name(self, wifi_map) -> None:
        name = (
            f"{self.map_index}"
            if self._map_name is None
            else f"{self._map_name.replace('_', ' ').replace('-', ' ').title()}"
        )
        self._attr_name = (
            f"{self.device.name} Saved {'Wifi ' if wifi_map else ''}Map {name}"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fetch state from the device."""
        self._available = self.device.cloud_connected
        self._last_map_request = 0
        map_data = self._map_data
        if (
            map_data
            and self.available
            and (self.map_index > 0 or self.device.status.located)
        ):
            if self.map_index > 0:
                if self._map_name != map_data.custom_name:
                    self._map_name = map_data.custom_name
                    self._set_map_name(self.wifi_map)

                if self._map_id != map_data.map_id:
                    self._map_id = map_data.map_id
                    self._frame_id = None
                    self._last_updated = None

            if self._default_map == True or self._frame_id != map_data.frame_id or self._last_updated != map_data.last_updated:
                self._frame_id = map_data.frame_id
                if (
                    not self.device.status.active
                    #or self._task_status != self.device.status.task_status
                    or self._error != self.device.status.error
                    or self._last_updated is None
                ):
                    self.update()
            elif (
                self._error != self.device.status.error
                #or self._task_status != self.device.status.task_status
            ):
                self.update()

            self._task_status = self.device.status.task_status
            self._error = self.device.status.error
        else:
            self.update()
        self.async_write_ha_state()

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        if self._should_poll is True:
            self._should_poll = False
            now = time.time()
            if now - self._last_map_request >= self.frame_interval:
                self._last_map_request = now
                if self.map_index == 0:
                    self.device.update_map()
                self.update()
            self._should_poll = True
        return self._image

    async def handle_async_still_stream(
        self, request: web.Request, interval: float
    ) -> web.StreamResponse:
        """Generate an HTTP MJPEG stream from camera images."""
        response = web.StreamResponse()
        response.content_type = CONTENT_TYPE_MULTIPART.format("--frameboundary")
        await response.prepare(request)

        last_image = None
        while True:
            img_bytes = await self.async_camera_image()
            if not img_bytes:
                img_bytes = self._default_map_image

            if img_bytes != last_image:
                # Always write twice, otherwise chrome ignores last frame and displays previous frame after second one
                for k in range(2):
                    await response.write(
                        bytes(
                            "--frameboundary\r\n"
                            "Content-Type: {}\r\n"
                            "Content-Length: {}\r\n\r\n".format(
                                self.content_type, len(img_bytes)
                            ),
                            "utf-8",
                        )
                        + img_bytes
                        + b"\r\n"
                    )
                last_image = img_bytes
            await asyncio.sleep(interval)
        return response

    @callback
    def async_update_token(self) -> None:
        """Update the used token."""
        if self._access_token_update_counter:
            self._access_token_update_counter = self._access_token_update_counter + 1

        if (
            not self._access_token_update_counter
            or self._access_token_update_counter
            > int(
                DREAME_TOKEN_CHANGE_INTERVAL.total_seconds()
                / TOKEN_CHANGE_INTERVAL.total_seconds()
            )
        ):
            self._access_token_update_counter = 1
            super().async_update_token()

    async def async_update(self) -> None:
        self._frame_id = None
        self._last_updated = None
        self.update()

    def __del__(self):
        if self._renderer:
            del self._renderer
            self._renderer = None
        if self._proxy_renderer:
            del self._proxy_renderer
            self._proxy_renderer = None

    def update(self) -> None:
        map_data = self._map_data
        if (
            map_data
            and self.available
            and (self.map_index > 0 or self.device.status.located)
        ):
            if (
                self.map_index == 0
                and not self.map_data_json
                and map_data.last_updated != self._last_updated
                and not self._renderer.render_complete
            ):
                LOGGER.warning("Waiting render complete")

            if (
                self._renderer.render_complete
                and map_data.last_updated != self._last_updated
            ):
                if self.map_index == 0 and not self.map_data_json:
                    LOGGER.debug("Update map")

                self._last_updated = map_data.last_updated
                self._frame_id = map_data.frame_id
                self._default_map = False
                if map_data.timestamp_ms and not map_data.saved_map:
                    self._state = datetime.fromtimestamp(
                        int(map_data.timestamp_ms / 1000)
                    )
                elif map_data.last_updated:
                    self._state = datetime.fromtimestamp(int(map_data.last_updated))

                self.coordinator.hass.async_create_task(
                    self._update_image(
                        self.device.get_map_for_render(self._map_data),
                        self.device.status.robot_status,
                    )
                )
        elif not self._default_map:
            self._image = self._default_map_image
            self._default_map = True
            self._frame_id = -1
            self._last_updated = -1
            self._state = STATE_UNAVAILABLE

    async def obstacle_image(self, index, box=False, crop=False):
        if self.map_index == 0 and not self.map_data_json:
            response, obstacle = await self.hass.async_add_executor_job(
                self.device.obstacle_image, index
            )
            if response and obstacle:
                return (
                    self._get_proxy_obstacle_image(
                        response, obstacle, box, crop, "obstacle"
                    ),
                    obstacle.object_name,
                )
        return (None, None)

    async def obstacle_history_image(
        self, index, history_index, cruising, box=False, crop=False
    ):
        if self.map_index == 0 and not self.map_data_json:
            response, obstacle = await self.hass.async_add_executor_job(
                self.device.obstacle_history_image, index, history_index, cruising
            )
            if response and obstacle:
                return (
                    self._get_proxy_obstacle_image(
                        response, obstacle, box, crop, "obstacle_history", 1
                    ),
                    obstacle.object_name,
                )
        return (None, None)

    async def history_map_image(
        self, index, info_text, cruising, data_string, include_resources
    ):
        if self.map_index == 0 and not self.map_data_json:
            map_data = await self.hass.async_add_executor_job(
                self.device.history_map, index, cruising
            )
            if map_data:
                map_data = self.device.get_map_for_render(map_data)
                if data_string:
                    return self._renderer.get_data_string(
                        map_data,
                        self._renderer.get_resources(self.device.capability)
                        if include_resources
                        else None,
                    )
                return self._get_proxy_image(
                    index, map_data, info_text, "cruising" if cruising else "cleaning"
                )

    async def recovery_map_file(self, index):
        if not self.map_data_json and not self.wifi_map:
            if self.map_index == 0:
                selected_map = self.device.status.selected_map
                map_id = selected_map.map_id if selected_map else None
            else:
                map_id = self._map_id
            if map_id:
                return await self.hass.async_add_executor_job(
                    self.device.recovery_map_file, map_id, index
                )
        return (None, None, None)

    async def recovery_map(self, index, info_text, data_string, include_resources):
        if not self.map_data_json and not self.wifi_map:
            if self.map_index == 0:
                selected_map = self.device.status.selected_map
                map_data = (
                    self.device.recovery_map(selected_map.map_id, index)
                    if selected_map
                    else None
                )
            else:
                map_data = self.device.recovery_map(self._map_id, index)
            if map_data:
                map_data = self.device.get_map_for_render(map_data)
                if data_string:
                    return self._renderer.get_data_string(
                        map_data,
                        self._renderer.get_resources(self.device.capability)
                        if include_resources
                        else None,
                    )
                else:
                    return self._get_proxy_image(index, map_data, info_text, "recovery")

    async def wifi_map_data(self, data_string, include_resources):
        if not self.map_data_json and not self.wifi_map:
            map_data = (
                self.device.status.selected_map
                if self.map_index == 0
                else self.device.get_map(self.map_index)
            )
            if map_data:
                map_data = map_data.wifi_map_data
                if map_data:
                    map_data = self.device.get_map_for_render(map_data)
                    if data_string:
                        return self._renderer.get_data_string(
                            map_data,
                            self._renderer.get_resources(self.device.capability)
                            if include_resources
                            else None,
                        )
                    else:
                        return self._get_proxy_image(
                            map_data.map_index
                            if self.map_index == 0
                            else self.map_index,
                            map_data,
                            False,
                            "wifi",
                            1,
                        )

    def map_data_string(self, include_resources) -> str | None:
        if not self.map_data_json and self._map_data:
            return self._renderer.get_data_string(
                self.device.get_map_for_render(self._map_data),
                self._renderer.get_resources(self.device.capability)
                if include_resources
                else None,
                self.device.status.robot_status,
            )
        return "{}"

    async def _update_image(self, map_data, robot_status) -> None:
        try:
            self._image = self._renderer.render_map(map_data, robot_status)
            if (
                not self.map_data_json
                and self._calibration_points != self._renderer.calibration_points
            ):
                self._calibration_points = self._renderer.calibration_points
                self.coordinator.async_set_updated_data()
        except Exception:
            LOGGER.warn("Map render Failed: %s", traceback.format_exc())

    def _get_proxy_image(self, index, map_data, info_text, cache_key, max_item=2):
        item_key = f"i{index}_t{int(info_text)}_d{int(map_data.last_updated)}"
        if cache_key not in self._proxy_images:
            self._proxy_images[cache_key] = {}
        if item_key in self._proxy_images[cache_key]:
            return self._proxy_images[cache_key][item_key]
        image = self._proxy_renderer.render_map(map_data, 0, info_text)
        if image:
            keys = self._proxy_images[cache_key].keys()
            while len(self._proxy_images[cache_key]) >= max_item:
                del self._proxy_images[cache_key][
                    next(iter(self._proxy_images[cache_key]))
                ]
            self._proxy_images[cache_key][item_key] = image
            return image

    def _get_proxy_obstacle_image(
        self, data, obstacle, box, crop, cache_key, max_item=3
    ):
        item_key = f"b{int(box)}_c{int(crop)}_d{obstacle.id}"
        if cache_key not in self._proxy_images:
            self._proxy_images[cache_key] = {}
        if item_key in self._proxy_images[cache_key]:
            return self._proxy_images[cache_key][item_key]
        image = self._renderer.render_obstacle_image(
            data,
            obstacle,
            self.device.capability.obstacle_image_crop,
            box,
            crop,
        )
        if image:
            while len(self._proxy_images[cache_key]) >= max_item:
                del self._proxy_images[cache_key][
                    next(iter(self._proxy_images[cache_key]))
                ]
            self._proxy_images[cache_key][item_key] = image
            return image

    @property
    def resources(self):
        if self.map_index == 0 and not self.map_data_json:
            return self._renderer.get_resources(self.device.capability)

    @property
    def wifi_map(self) -> bool:
        return bool(self.entity_description.map_type == DreameVacuumMapType.WIFI_MAP)

    @property
    def map_data_json(self) -> bool:
        return bool(
            self.entity_description.map_type == DreameVacuumMapType.JSON_MAP_DATA
        )

    @property
    def _map_data(self) -> Any:
        map_data = self.device.get_map(self.map_index)
        if self.wifi_map and map_data:
            return map_data.wifi_map_data
        return map_data

    @property
    def _default_map_image(self) -> Any:
        if self._image and not self.available:
            return self._renderer.disconnected_map_image
        return self._renderer.default_map_image

    @property
    def frame_interval(self) -> float:
        return 0.25

    @property
    def supported_features(self) -> int:
        return 0

    @property
    def state(self) -> str:
        """Return the status of the map."""
        return self._state

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available
    
    @property
    def entity_picture(self) -> str:
        """Return a link to the camera feed as entity picture."""
        map_data = self._map_data
        return MAP_IMAGE_URL.format(self.entity_id, self.access_tokens[-1], int(map_data.last_updated) if map_data and map_data.last_updated else 0)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if not self.map_data_json:
            map_data = self._map_data
            if (
                map_data
                and not map_data.empty_map
                and (self.map_index > 0 or self.device.status.located)
            ):
                attributes = map_data.as_dict()
                if not attributes:
                    attributes = {}

                attributes[ATTR_CALIBRATION] = (
                    self._calibration_points
                    if self._calibration_points
                    else self._renderer.calibration_points
                )
            elif self.available:
                attributes = {
                    ATTR_CALIBRATION: self._renderer.default_calibration_points
                }

            if not attributes:
                attributes = {}

            token = self.access_tokens[-1]
            if self.map_index == 0:

                def get_key(index, history):
                    return f"{index}: {time.strftime('%m/%d %H:%M', time.localtime(history.date.timestamp()))} - {STATUS_CODE_TO_NAME.get(history.status, STATE_UNKNOWN).replace('_', ' ').title()} {'(Completed)' if history.completed else '(Interrupted)'}"

                if self.device.status._cleaning_history is not None:
                    cleaning_history = {}
                    index = 1
                    for history in self.device.status._cleaning_history:
                        key = get_key(index, history)
                        cleaning_history[key] = HISTORY_MAP_IMAGE_URL.format(
                            self.entity_id,
                            token,
                            index,
                            int(history.date.timestamp()),
                        )
                        index = index + 1
                    attributes[ATTR_CLEANING_HISTORY_PICTURE] = cleaning_history

                if self.device.status._cruising_history is not None:
                    cruising_history = {}
                    index = 1
                    for history in self.device.status._cruising_history:
                        key = get_key(index, history)
                        cruising_history[
                            key
                        ] = f"{HISTORY_MAP_IMAGE_URL.format(self.entity_id, token, index, int(history.date.timestamp()))}&cruising=1"
                        index = index + 1
                    attributes[ATTR_CRUISING_HISTORY_PICTURE] = cruising_history

                if map_data and map_data.obstacles is not None:
                    obstacles = {}
                    total = len(map_data.obstacles)
                    if total:
                        index = total
                        for k in reversed(map_data.obstacles):
                            obstacle = map_data.obstacles[k]
                            if index == total and obstacle.picture_status is not None and obstacle.picture_status.value != 2:
                                index = index - 1
                                continue

                            key = f"{index}: {obstacle.type.name.replace('_', ' ').title()}"
                            if obstacle.possibility:
                                key = f"{key} %{obstacle.possibility}"
                            if obstacle.segment:
                                key = f"{key} ({obstacle.segment})"
                            if obstacle.ignore_status and int(obstacle.ignore_status) > 0:
                                key = f"{key} ({obstacle.ignore_status.name.replace('_', ' ').title()})"

                            obstacles[key] = OBSTACLE_IMAGE_URL.format(
                                self.entity_id, token, index, obstacle.id
                            )
                            index = index - 1

                    attributes[ATTR_OBSTACLE_PICTURE] = obstacles

            if not self.wifi_map:
                if self.map_index == 0:
                    selected_map = self.device.status.selected_map
                    recovery_map_list = (
                        selected_map.recovery_map_list if selected_map else None
                    )
                else:
                    recovery_map_list = map_data.recovery_map_list

                if recovery_map_list is not None:
                    recovery_map = {}
                    recovery_file = {}
                    index = len(recovery_map_list)
                    for map in reversed(recovery_map_list):
                        key = f"{time.strftime('%x %X', time.localtime(map.date.timestamp()))}: Map{index} ({map.map_type.name.title()})"
                        recovery_map[key] = RECOVERY_MAP_IMAGE_URL.format(
                            self.entity_id, token, index, int(map.date.timestamp())
                        )
                        recovery_file[key] = f"{recovery_map[key]}&file=1"
                        index = index - 1
                    attributes[ATTR_RECOVERY_MAP_PICTURE] = recovery_map
                    attributes[ATTR_RECOVERY_MAP_FILE] = recovery_file

                if self.map_index == 0:
                    selected_map = self.device.status.selected_map
                    wifi_map_data = selected_map.wifi_map_data if selected_map else None
                else:
                    wifi_map_data = map_data.wifi_map_data

                if wifi_map_data:
                    attributes[ATTR_WIFI_MAP_PICTURE] = WIFI_MAP_IMAGE_URL.format(
                        self.entity_id,
                        token,
                        int(
                            wifi_map_data.last_updated
                            if wifi_map_data.last_updated
                            else map_data.last_updated
                        ),
                    )
            return attributes
