"""The Dreame Vacuum component."""

from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from pathlib import Path
from .const import DOMAIN

from .coordinator import DreameVacuumDataUpdateCoordinator

PLATFORMS = (
    Platform.VACUUM,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.CAMERA,
    Platform.TIME,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dreame Vacuum from a config entry."""
    coordinator = DreameVacuumDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Register frontend
    # frontend_js = f"/{DOMAIN}/frontend.js"
    # if DATA_EXTRA_MODULE_URL not in hass.data:
    #    hass.data[DATA_EXTRA_MODULE_URL] = set()
    # if frontend_js not in (
    #    hass.data[DATA_EXTRA_MODULE_URL].urls
    #    if hasattr(hass.data[DATA_EXTRA_MODULE_URL], "urls")
    #    else hass.data[DATA_EXTRA_MODULE_URL]
    # ):
    #    hass.data[DATA_EXTRA_MODULE_URL].add(frontend_js)
    #    hass.http.register_static_path(frontend_js, str(Path(Path(__file__).parent / "frontend.js")), True)

    # Set up all platforms for this device/entry.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Dreame Vacuum config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        coordinator._device.listen(None)
        coordinator._device.disconnect()
        del coordinator._device
        coordinator._device = None
        del hass.data[DOMAIN][entry.entry_id]

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
