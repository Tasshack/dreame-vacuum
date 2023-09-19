from __future__ import annotations

import collections
import voluptuous as vol
from enum import IntEnum
import time
import asyncio
import traceback
from typing import Any, Dict
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from aiohttp import web

from homeassistant.components.camera import Camera, CameraEntityDescription, CameraView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, CONTENT_TYPE_MULTIPART
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform, entity_registry

from .const import (
    DOMAIN,
    CONF_COLOR_SCHEME,
    CONF_ICON_SET,
    CONF_MAP_OBJECTS,
    CONF_LOW_RESOLUTION,
    CONF_SQUARE,
    MAP_OBJECTS,
    ATTR_CALIBRATION,
    CONTENT_TYPE,
    LOGGER,
)

from .coordinator import DreameVacuumDataUpdateCoordinator
from .entity import DreameVacuumEntity, DreameVacuumEntityDescription
from .dreame.map import (
    DreameVacuumMapRenderer,
    DreameVacuumMapDataJsonRenderer,
)


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
        if not camera.available:
            raise web.HTTPServiceUnavailable()
        if not camera.map_data_json:
            return web.Response(body=camera.map_data_string, content_type="application/json")
        raise web.HTTPNotFound()

class CameraObstacleView(CameraView):
    """Camera view to serve the map data obstacle image."""

    url = "/api/camera_map_obstacle_proxy/{entity_id}"
    name = "api:camera:map_obstacle"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera obstacle image."""
        if not camera.available:
            raise web.HTTPServiceUnavailable()
        
        if camera.map_index == 0:
            crop = request.query.get("crop")
            result = await camera.obstacle_image(request.query.get("index", 1), crop and (crop == True or crop == "true" or crop == "1"))
            if result:
                return web.Response(body=result, content_type="image/jpeg")
        
        raise web.HTTPNotFound()

class CameraHistoryView(CameraView):
    """Camera view to serve the cleaning history map."""

    url = "/api/camera_map_history_proxy/{entity_id}"
    name = "api:camera:map_history"

    async def handle(self, request: web.Request, camera: Camera) -> web.Response:
        """Serve camera cleaning history data."""
        if not camera.available:
            raise web.HTTPServiceUnavailable()
                
        if not camera.map_data_json and camera.map_index == 0:
            data = request.query.get("data")
            data = data and (data == True or data == "true" or data == "1")
            result = await camera.cleaning_history_map(request.query.get("index", 1), data)
            if result:
                return web.Response(body=result, content_type="application/json" if data else "image/jpeg")
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
        hass.http.register_view(CameraHistoryView(hass.data["camera"]))


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
    del current[map_index]


class DreameVacuumCameraEntity(DreameVacuumEntity, Camera):
    """Defines a Dreame Vacuum Camera entity."""

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
        self.content_type = CONTENT_TYPE
        self.stream = None
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

        self._available = self.device.device_connected and self.device.cloud_connected
        if description.map_type == DreameVacuumMapType.JSON_MAP_DATA:
            self._renderer = DreameVacuumMapDataJsonRenderer()
        else:
            self._renderer = DreameVacuumMapRenderer(
                color_scheme,
                icon_set,
                ["charger"] if self.wifi_map else map_objects,
                self.device.capability.robot_type,
                low_resolution,
                square,
            )

        self._image = None
        self._default_map = True
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
            self.entity_id = f"camera.{self.device.name.lower()}_{'wifi_' if self.wifi_map else ''}map_{self.map_index}"
        else:
            self._attr_name = f"{self.device.name} Current {'Wifi ' if self.wifi_map else ''}{description.name}"
            self._attr_unique_id = f"{self.device.mac}_map_{'wifi_' if self.wifi_map else ''}{description.key}"
            self.entity_id = f"camera.{self.device.name.lower()}_{'wifi_' if self.wifi_map else ''}{description.key.lower()}"

        if self.map_index == 0 and not self.map_data_json:
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

            if self._default_map == True or self._frame_id != map_data.frame_id:
                self._frame_id = map_data.frame_id
                if (
                    not self.device.status.active
                    or self._task_status != self.device.status.task_status
                    or self._last_updated is None
                ):
                    self.update()
            elif self._task_status != self.device.status.task_status:
                self.update()

            self._task_status = self.device.status.task_status
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

    async def async_update(self) -> None:
        self._frame_id = None
        self._last_updated = None
        self.update()

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

    async def obstacle_image(self, index, crop = False):
        if self.map_index == 0 and not self.map_data_json:
            response, obstacle = await self.hass.async_add_executor_job(self.device.obstacle_image, index)
            if response and obstacle:
                return self._renderer.render_obstacle_image(response, obstacle, self.device.capability.obstacle_image_crop, crop)

    async def cleaning_history_map(self, index, data_string):
        if self.map_index == 0 and not self.map_data_json:
            map_data = await self.hass.async_add_executor_job(self.device.cleaning_history_map, index)
            if map_data:
                map_data = self.device.get_map_for_render(map_data)
                if data_string:
                    return self._renderer.get_data_string(map_data)
                else:
                    return self._renderer.render_map(map_data, 0, False)

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

    @property
    def wifi_map(self) -> bool:
        return bool(self.entity_description.map_type == DreameVacuumMapType.WIFI_MAP)

    @property
    def map_data_json(self) -> bool:
        return bool(self.entity_description.map_type == DreameVacuumMapType.JSON_MAP_DATA)

    @property
    def _map_data(self) -> Any:
        map_data = self.device.get_map(self.map_index)
        if self.wifi_map and map_data:
            return map_data.wifi_map_data
        return map_data

    @property
    def _default_map_image(self) -> Any:
        if self._image and (
            not self.device.device_connected or not self.device.cloud_connected
        ):
            return self._renderer.disconnected_map_image
        return self._renderer.default_map_image

    @property
    def map_data_string(self) -> str | None:
        if not self.map_data_json and self._map_data:
            return self._renderer.get_data_string(self.device.get_map_for_render(self._map_data), self.device.status.robot_status)
        return "{}"

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
    def extra_state_attributes(self) -> Dict[str, Any]:
        if not self.map_data_json:
            map_data = self._map_data
            if (
                map_data
                and not map_data.empty_map
                and (self.map_index > 0 or self.device.status.located)
            ):
                attributes = map_data.as_dict()
                if attributes:
                    attributes[ATTR_CALIBRATION] = (
                        self._calibration_points
                        if self._calibration_points
                        else self._renderer.calibration_points
                    )
                return attributes
            elif self.available:
                return {ATTR_CALIBRATION: self._renderer.default_calibration_points}
