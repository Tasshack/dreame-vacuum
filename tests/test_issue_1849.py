"""Issue #1849: a one second MOP_PAD_INSTALLED flicker must not reset the cleaning mode.

r9419h reports MOP_PAD_INSTALLED 0 -> 1 -> 0 for about a second while docking or
undocking. 0 means "installed" on that model, so the middle value made
DreameVacuumDevice._water_tank_changed believe nothing was installed and wrote
CLEANING_MODE = sweeping (5122) to the robot, losing the selected
mopping_after_sweeping (5123) for the next run.

The app for those models never writes the mode, it only restricts the option list,
so the integration must not write either.

Run from the repo root:
    python3 tests/test_issue_1849.py
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _bootstrap import load_device  # noqa: E402

device_module = load_device()
DreameVacuumDevice = device_module.DreameVacuumDevice
DreameVacuumDeviceStatus = device_module.DreameVacuumDeviceStatus
DreameVacuumProperty = device_module.DreameVacuumProperty
DreameVacuumCleaningMode = device_module.DreameVacuumCleaningMode
DreameVacuumTaskStatus = device_module.DreameVacuumTaskStatus


class Capability:
    """Capability stub: everything defaults to False, only the flags under test are set."""

    def __init__(self, **flags):
        self.__dict__.update(flags)

    def __getattr__(self, name):
        return False


def make_device(**capability):
    """Fake r9419h idle on the dock with the mop pad installed and mode mopping_after_sweeping."""
    properties = {
        DreameVacuumProperty.CLEANING_MODE: DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING.value,
        DreameVacuumProperty.WATER_TANK: 0,
        DreameVacuumProperty.MOP_PAD_INSTALLED: 0,
        DreameVacuumProperty.TASK_STATUS: DreameVacuumTaskStatus.COMPLETED.value,
        DreameVacuumProperty.CHARGING_STATUS: 1,
        DreameVacuumProperty.STATUS: device_module.DreameVacuumStatus.CHARGING.value,
    }
    device = SimpleNamespace(
        properties=properties,
        get_property=properties.get,
        capability=Capability(mop_pad_unmounting=True, **capability),
        _ready=True,
        _previous_cleaning_mode=None,
        cleaning_mode_writes=[],
    )
    device.status = DreameVacuumDeviceStatus(device)
    device.status.cleaning_mode = DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
    device._update_cleaning_mode = lambda mode: device.cleaning_mode_writes.append(mode)
    return device


def water_tank_changed(device):
    DreameVacuumDevice._water_tank_changed(device)


def main():
    # r9419h: mop pad lifting, embedded tank reported as absent, mop pad installed
    device = make_device(mop_pad_lifting=True, embedded_tank=False, mopping_after_sweeping=True)
    assert device.status.water_tank_or_mop_installed is True
    full_list = dict(device.status.cleaning_mode_list)

    # MOP_PAD_INSTALLED 0 -> 1 -> 0 while idle on the dock
    for raw in (1, 0):
        device.properties[DreameVacuumProperty.MOP_PAD_INSTALLED] = raw
        water_tank_changed(device)

        assert device.cleaning_mode_writes == [], f"CLEANING_MODE written on MOP_PAD_INSTALLED {raw}"
        assert device.status.cleaning_mode is DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING, raw
        assert device.status.water_tank_or_mop_installed is (raw == 0), raw

        if raw == 1:
            # Nothing installed: mopping options are hidden, current mode stays selectable
            options = set(device.status.cleaning_mode_list.values())
            assert options == {
                DreameVacuumCleaningMode.SWEEPING,
                DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING,
            }, options
            assert device._previous_cleaning_mode is DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING
        else:
            # Pad reported installed again: full option list is back
            assert device.status.cleaning_mode_list == full_list, device.status.cleaning_mode_list

    # Nothing was written over the whole flicker
    assert device.cleaning_mode_writes == []
    assert device._previous_cleaning_mode is DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING

    # An older non mop pad lifting device must not be written to either
    old = make_device(mop_pad_lifting=False, sweep_with_mop=False, mopping_after_sweeping=False)
    old.properties[DreameVacuumProperty.MOP_PAD_INSTALLED] = 1
    water_tank_changed(old)
    assert old.cleaning_mode_writes == [], "CLEANING_MODE written on an older device"
    assert old._previous_cleaning_mode is DreameVacuumCleaningMode.MOPPING_AFTER_SWEEPING

    # Already sweeping: there is no other mode to remember
    old.status.cleaning_mode = DreameVacuumCleaningMode.SWEEPING
    old._previous_cleaning_mode = None
    water_tank_changed(old)
    assert old._previous_cleaning_mode is None
    assert old.cleaning_mode_writes == []

    print("PASS: no CLEANING_MODE write on a MOP_PAD_INSTALLED flicker, mode and options kept")


if __name__ == "__main__":
    main()
