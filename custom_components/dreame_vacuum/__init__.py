"""The Dreame Vacuum component."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import DreameVacuumDataUpdateCoordinator

PLATFORMS = (
    Platform.VACUUM,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.CAMERA,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dreame Vacuum from a config entry."""
    coordinator = DreameVacuumDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Set up all platforms for this device/entry.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Dreame Vacuum config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: DreameVacuumDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        coordinator.device.listen(None)
        coordinator.device.disconnect()
        del coordinator.device
        coordinator._device = None
        del hass.data[DOMAIN][entry.entry_id]

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
