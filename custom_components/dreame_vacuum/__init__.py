"""The Dreame Vacuum component."""

from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import warnings
from importlib import import_module
from .const import DOMAIN

## Dynamically load frontend.py so that it can be easily stripped
try:
    frontend = import_module(f"{__package__}.frontend")
except ModuleNotFoundError as ex:
    if ex.name != f"{__package__}.frontend":
        raise
    frontend = None

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


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Dreame Vacuum integration."""
    if frontend is not None and hass.config_entries.async_entries(DOMAIN):
        await frontend.setup(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dreame Vacuum from a config entry."""

    coordinator = DreameVacuumDataUpdateCoordinator(hass, entry=entry)

    try:        
        await coordinator.async_load_locale(hass)
        await coordinator.async_config_entry_first_refresh()
    except BaseException:
        if coordinator._unsub_dispatcher:
            coordinator._unsub_dispatcher()
            coordinator._unsub_dispatcher = None

        if coordinator._device is not None:
            coordinator._device.listen(None)
            coordinator._device.listen_error(None)
            try:
                await hass.async_add_executor_job(coordinator._device.disconnect)
            except Exception:
                pass
            finally:
                coordinator._device = None
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

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
        try:
            await hass.async_add_executor_job(coordinator._device.disconnect)
        finally:
            coordinator._device = None
            hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of a Dreame Vacuum config entry."""
    if frontend is not None:
        await frontend.remove(hass, entry)


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
