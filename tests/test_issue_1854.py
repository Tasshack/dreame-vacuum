"""Issue #1854: r2216o reports WATER_TANK 2 and 3, so every mopping option disappeared.

Run from the repo root:
    python3 tests/test_issue_1854.py
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _bootstrap import load_device

load_device()

from custom_components.dreame_vacuum.dreame.device import DreameVacuumDeviceStatus
from custom_components.dreame_vacuum.dreame.types import (
    DreameVacuumProperty,
    DreameVacuumWaterTank,
)


def _status(tank, mop_in_station=None, mop_pad_installed=None, **capability):
    """Build a real status on a fake device. Status only reaches the device via get_property/capability."""
    properties = {DreameVacuumProperty.WATER_TANK: tank}
    if mop_in_station is not None:
        properties[DreameVacuumProperty.MOP_IN_STATION] = mop_in_station
    if mop_pad_installed is not None:
        properties[DreameVacuumProperty.MOP_PAD_INSTALLED] = mop_pad_installed
    fake_capability = {"mop_pad_unmounting": False, "embedded_tank": False}
    fake_capability.update(capability)
    device = SimpleNamespace(get_property=properties.get, capability=SimpleNamespace(**fake_capability))
    return DreameVacuumDeviceStatus(device)


def main():
    # Firmware aliases and enum values alike mean something is installed on the robot,
    # even with a mop pad reported in the station.
    for raw, expected in (
        (1, DreameVacuumWaterTank.INSTALLED),
        (3, DreameVacuumWaterTank.INSTALLED),
        (2, DreameVacuumWaterTank.MOP_INSTALLED),
        (10, DreameVacuumWaterTank.MOP_INSTALLED),
    ):
        assert _status(raw, mop_in_station=1).water_tank_or_mop_installed is True, raw
        assert _status(raw).water_tank is expected, raw
        assert _status(raw).mop_in_station is False, raw

    # Nothing installed: 99 is IN_STATION and must never count as installed.
    for raw in (0, None, -1, 99):
        assert _status(raw, mop_in_station=1).water_tank_or_mop_installed is False, raw
        assert _status(raw, mop_in_station=1).mop_in_station is True, raw

    assert _status(0).water_tank is DreameVacuumWaterTank.NOT_INSTALLED
    assert _status(None).water_tank is DreameVacuumWaterTank.UNKNOWN
    assert _status(-1).water_tank is DreameVacuumWaterTank.UNKNOWN
    assert _status(99).water_tank is DreameVacuumWaterTank.IN_STATION
    assert _status(0, mop_in_station=1).water_tank is DreameVacuumWaterTank.IN_STATION

    # Capability driven overrides stay intact.
    assert _status(0, embedded_tank=True).water_tank_or_mop_installed is True
    assert _status(0, mop_pad_unmounting=True, mop_pad_installed=0).water_tank_or_mop_installed is True
    assert _status(3, mop_pad_unmounting=True, mop_pad_installed=1).water_tank_or_mop_installed is True

    print("issue 1854: water tank aliases resolved, no false installed states")


if __name__ == "__main__":
    main()