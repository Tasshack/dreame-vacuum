"""Diagnostics support for Dreame Vacuum."""

from __future__ import annotations

import base64
import gzip
import traceback
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .dreame import (
    DreameVacuumAutoSwitchProperty,
    DreameVacuumProperty,
    DreameVacuumStrAIProperty,
)

try:
    from homeassistant.helpers.device_registry import DeviceEntry
except ImportError:
    DeviceEntry = Any

EXCLUDED_KEYS = [
    "SERIAL_NUMBER",
    "WIFI_MAP",
    "ap",
    "auth_key",
    "did",
    "dvc_key",
    "host",
    "last_updated_time",
    "mac",
    "object_name",
    "password",
    "token",
    "username",
]

EXCLUDED_MAP_KEYS = ["path", "small_path"]


def _get(target: Any, name: str, default: Any = None) -> Any:
    if target is None:
        return default
    try:
        return getattr(target, name, default)
    except Exception as ex:
        return f"<{type(ex).__name__}: {ex}>"


def _sanitize(value: Any, seen: set[int] | None = None) -> Any:
    if isinstance(value, Enum):
        value = value.value if isinstance(value.value, (bool, int, float, str)) else value.name
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(bytes(value)).decode("ascii")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value)
    if seen is None:
        seen = set()
    marker = id(value)
    if marker in seen:
        return f"<recursive {type(value).__name__}>"
    seen.add(marker)
    try:
        if isinstance(value, dict):
            return {
                str(k): _sanitize(v, seen) for k, v in value.items() if str(k) not in EXCLUDED_KEYS
            }
        if isinstance(value, (list, tuple, set, frozenset)):
            return [_sanitize(v, seen) for v in value]
        as_dict = getattr(value, "as_dict", None)
        if callable(as_dict):
            try:
                return _sanitize(as_dict(), seen)
            except Exception:
                pass
        if hasattr(value, "__dict__"):
            return {
                k: _sanitize(v, seen)
                for k, v in vars(value).items()
                if not k.startswith("_") and k not in EXCLUDED_KEYS
            }
    finally:
        seen.discard(marker)
    return repr(value)


def _entities(
    hass: HomeAssistant, entry: ConfigEntry, device: Any, device_id: str | None = None
) -> dict[str, Any]:
    mirrors: dict[str, Any] = {}
    data = _get(device, "data")
    if isinstance(data, dict):
        names = {prop.value: prop.name.lower() for prop in DreameVacuumProperty}
        for did, value in data.items():
            did_value = did.value if isinstance(did, Enum) else did
            if did_value in names:
                mirrors[names[did_value]] = value
    for source in ("auto_switch_data", "ai_data"):
        parsed = _get(device, source)
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                mirrors[str(key).lower()] = value
    capability_list = _get(_get(device, "capability"), "list")
    status = _get(device, "status")
    status_type = type(status)
    component = (hass.data.get("entity_components") or {}).get(Platform.VACUUM)
    registry = er.async_get(hass)
    entries_for_config_entry = getattr(er, "async_entries_for_config_entry", None)
    if entries_for_config_entry is not None:
        registry_entries = entries_for_config_entry(registry, entry.entry_id)
    else:
        registry_entries = [
            registry_entry
            for registry_entry in registry.entities.values()
            if registry_entry.config_entry_id == entry.entry_id
        ]
    vacuum: dict[str, Any] = {}
    disabled: list[str] = []
    availability: dict[str, bool] = {}
    for registry_entry in registry_entries:
        if device_id is not None and registry_entry.device_id != device_id:
            continue
        if _get(registry_entry, "disabled_by") is not None or _get(registry_entry, "hidden_by") is not None:
            disabled.append(registry_entry.entity_id)
            continue
        state = hass.states.get(registry_entry.entity_id)
        usable = state is not None and state.state != STATE_UNAVAILABLE
        availability[registry_entry.entity_id] = usable
        if usable and registry_entry.entity_id.split(".")[0] == Platform.VACUUM:
            attributes = _get(
                component.get_entity(registry_entry.entity_id) if component is not None else None,
                "extra_state_attributes",
            )
            if not isinstance(attributes, dict):
                own = set(_get(status, "attributes") or {})
                attributes = {k: v for k, v in state.attributes.items() if k in own}
            computed: dict[str, Any] = {"entity_id": registry_entry.entity_id}
            for key, value in attributes.items():
                if key.endswith("_list"):
                    continue
                if isinstance(value, str) and hasattr(status_type, f"{key}_name"):
                    continue
                if capability_list is not None and value == capability_list:
                    continue
                mirror = mirrors.get(key)
                if mirror is not None:
                    if type(value) is type(mirror) and value == mirror:
                        continue
                    if (
                        isinstance(value, bool)
                        and isinstance(mirror, int)
                        and not isinstance(mirror, bool)
                        and value == (mirror > 0)
                    ):
                        continue
                computed[key] = value
            vacuum = computed
    details: dict[str, Any] = {}
    if vacuum:
        details["vacuum"] = vacuum
    if disabled:
        details["disabled"] = disabled
    if availability:
        details["availability"] = availability
    return details


def _capabilities(device: Any) -> list[str] | None:
    capability = _get(device, "capability")
    if capability is None:
        return None
    return sorted(
        name.upper()
        for name in dir(capability)
        if not name.startswith("_") and _get(capability, name) is True
    )


def _device_details(device: Any) -> dict[str, Any] | None:
    if device is None:
        return None
    serial = _get(_get(device, "status"), "serial_number")
    return {
        "model": _get(_get(device, "info"), "model"),
        "serial_number": serial[:7] + "*" * len(serial[7:]) if isinstance(serial, str) else serial,
    }


def _properties(device: Any) -> dict[str, Any] | None:
    data = _get(device, "data")
    if not isinstance(data, dict):
        return None
    requested = {prop.value for prop in (_get(device, "_default_properties") or DreameVacuumProperty)}
    packed = tuple(
        f'"{prop.value}"'
        for group in (DreameVacuumAutoSwitchProperty, DreameVacuumStrAIProperty)
        for prop in group
        if isinstance(prop.value, str)
    )
    names = {prop.value: prop.name for prop in DreameVacuumProperty}
    properties: dict[str, Any] = {}
    for did, value in data.items():
        did_value = did.value if isinstance(did, Enum) else did
        if did_value not in requested:
            continue
        if isinstance(value, str) and any(
            key in value for key in ('"object_name"', '"mapobj"', *packed)
        ):
            continue
        if isinstance(did_value, int):
            properties[names.get(did_value, f"UNKNOWN_{did_value}")] = value
        else:
            properties[str(did_value)] = value
    for source in ("auto_switch_data", "ai_data"):
        parsed = _get(device, source)
        if isinstance(parsed, dict):
            properties.update(parsed)
    return dict(sorted(properties.items()))


def _map_payloads(device: Any) -> dict[str, Any] | None:
    if device is None:
        return None
    manager = _get(device, "_map_manager")
    if manager is None:
        return None
    from .dreame.map import DreameVacuumMapRenderer

    status = _get(device, "status")
    encoded_by_path: dict[str, str] = {}

    def build(path: str, map_data: Any) -> Any:
        if map_data is None:
            return None
        try:
            render_data = device.get_map_for_render(map_data)
            if render_data is None:
                raise ValueError("get_map_for_render returned no data")
            for attribute in EXCLUDED_MAP_KEYS:
                setattr(render_data, attribute, None)
            encoded = DreameVacuumMapRenderer.get_data(render_data, device.capability, 0, False)
        except Exception as ex:
            return _failure(ex)
        encoded_by_path[path] = encoded
        return base64.b64encode(gzip.compress(encoded.encode("utf-8"), 9)).decode("ascii")

    groups: dict[str, Any] = {}
    current = build("current", _get(manager, "_map_data"))
    if current is not None:
        groups["current"] = current

    saved: dict[str, Any] = {}
    recovery: dict[str, Any] = {}
    for map_id, map_data in (_get(manager, "_saved_map_data") or {}).items():
        path = f"saved/{map_id}"
        entry = build(path, map_data)
        if entry is None:
            continue
        saved[str(map_id)] = entry
        items: list[Any] = []
        for index, info in enumerate(_get(map_data, "recovery_map_list") or [], 1):
            cached = build(f"{path}/recovery/{index}", _get(info, "map_data"))
            if cached is not None:
                items.append(cached)
        if items:
            recovery[str(map_id)] = items
    if saved:
        groups["saved"] = saved
    if recovery:
        groups["recovery"] = recovery

    cache = _get(status, "_history_map_data")
    if not isinstance(cache, dict):
        cache = {}
    for group, attribute in (("history", "_cleaning_history"), ("cruising", "_cruising_history")):
        section: dict[str, Any] = {}
        stored = 0
        for index, item in enumerate(_get(status, attribute) or [], 1):
            if stored >= 5:
                break
            object_name = _get(item, "object_name")
            if not object_name or object_name not in cache:
                continue
            path = f"{group}/{index}"
            entry = build(path, cache[object_name])
            current_encoded = encoded_by_path.get("current")
            if (
                group == "history"
                and index == 1
                and current_encoded is not None
                and encoded_by_path.get(path) == current_encoded
            ):
                entry = "current"
            elif isinstance(entry, str):
                stored += 1
            section[_sanitize(_get(item, "date")) or str(index)] = entry
        if section:
            groups[group] = section

    return groups


def _entry_details(entry: ConfigEntry) -> dict[str, Any]:
    return {
        "data": dict(entry.data),
        "options": dict(_get(entry, "options") or {}),
    }


def _failure(ex: Exception) -> dict[str, Any]:
    return {
        "diagnostics_error": f"{type(ex).__name__}: {ex}",
        "diagnostics_traceback": traceback.format_exc().splitlines(),
    }


def _section(builder: Any, *args: Any) -> Any:
    try:
        return _sanitize(builder(*args))
    except Exception as ex:
        return _failure(ex)


async def _async_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device_id: str | None = None
) -> dict[str, Any]:
    coordinator = (hass.data.get(DOMAIN) or {}).get(entry.entry_id)
    device = _get(coordinator, "device")
    try:
        map_data = await hass.async_add_executor_job(_map_payloads, device)
    except Exception as ex:
        map_data = _failure(ex)
    return {
        "generated_at": dt_util.utcnow().isoformat(),
        "device": _section(_device_details, device),
        "entry": _section(_entry_details, entry),
        "capabilities": _section(_capabilities, device),
        "properties": _section(_properties, device),
        "entities": _section(_entities, hass, entry, device, device_id),
        "map_data": map_data,
    }


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return await _async_diagnostics(hass, entry)


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device."""
    return await _async_diagnostics(hass, entry, device.id)
