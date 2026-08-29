from types import SimpleNamespace
from unittest.mock import Mock

from custom_components.dreame_vacuum.dreame.device import DreameVacuumDevice
from custom_components.dreame_vacuum.dreame.types import (
    DreameVacuumCleanWaterTankStatus,
    DreameVacuumProperty,
)


def _cloud_device(*, clean_water_status: int, low_water: bool) -> DreameVacuumDevice:
    device = DreameVacuumDevice("Test vacuum", None, None)
    device._protocol = SimpleNamespace(
        cloud=SimpleNamespace(connected=True),
        connected=True,
        dreame_cloud=True,
        prefer_cloud=True,
    )
    device.capability = SimpleNamespace(backup_map=False)
    device.status = SimpleNamespace(
        active=False,
        low_water=low_water,
        map_backup_status=False,
        map_recovery_status=False,
        started=False,
        washing=False,
    )
    device.data[DreameVacuumProperty.CLEAN_WATER_TANK_STATUS.value] = clean_water_status
    device._last_settings_request = float("inf")
    device._map_manager = None
    device._dirty_data = {}
    device._dirty_auto_switch_data = {}
    device._dirty_ai_data = {}
    device._consumable_change = False
    device._draining_complete_time = None
    device._request_properties = Mock()
    device._request_cleaning_history = Mock()
    return device


def test_cloud_water_status_is_polled_while_low() -> None:
    device = _cloud_device(
        clean_water_status=DreameVacuumCleanWaterTankStatus.LOW_WATER.value,
        low_water=True,
    )

    device.update()
    device.update()

    device._request_properties.assert_called_once_with(
        [
            DreameVacuumProperty.LOW_WATER_WARNING,
            DreameVacuumProperty.CLEAN_WATER_TANK_STATUS,
        ]
    )


def test_cloud_water_status_is_not_polled_after_refill() -> None:
    device = _cloud_device(
        clean_water_status=DreameVacuumCleanWaterTankStatus.INSTALLED.value,
        low_water=False,
    )

    device.update()

    device._request_properties.assert_not_called()
