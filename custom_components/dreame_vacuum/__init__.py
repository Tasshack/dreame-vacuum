"""The Dreame Vacuum component."""

from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
import logging
import warnings
from pathlib import Path
from .const import DOMAIN

# Suppress python-miio FutureWarning on Python 3.13
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="miio.miot_device",
)

# Suppress RuntimeWarning overflow encountered in scalar add
warnings.filterwarnings("ignore", category=RuntimeWarning)

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


_LOGGER = logging.getLogger(__name__)


async def _teardown_coordinator(coordinator) -> None:
    """Stop the device of a coordinator that is never going to be used.

    A failed first refresh (cloud discovery failure, auth failure, or setup
    cancellation after Home Assistant's setup timeout) otherwise leaves the
    device running with its worker threads, timers and cloud connections.
    Home Assistant retries setup every ~30 s, so every retry used to leak the
    previous attempt's resources until Home Assistant ran out of memory
    (see https://github.com/Tasshack/dreame-vacuum/issues/1762).
    """
    device = getattr(coordinator, "_device", None)
    if device is None:
        return
    device.listen(None)
    device.listen_error(None)
    try:
        device.disconnect()
    except Exception:
        _LOGGER.exception("Error while disconnecting device after failed setup")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dreame Vacuum from a config entry."""
    coordinator = DreameVacuumDataUpdateCoordinator(hass, entry=entry)
    # Cleanup must cover BaseException: Home Assistant cancels slow setups with
    # CancelledError, which does not derive from Exception.
    try:
        await coordinator.async_config_entry_first_refresh()
    except BaseException:
        await _teardown_coordinator(coordinator)
        raise

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
        if coordinator._unsub_dispatcher:
            coordinator._unsub_dispatcher()
            coordinator._unsub_dispatcher = None
        coordinator._device.listen(None)
        coordinator._device.listen_error(None)
        coordinator._device.disconnect()
        del coordinator._device
        coordinator._device = None
        del hass.data[DOMAIN][entry.entry_id]

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
