"""Issue #1847: CleanGenius selects are permanently unavailable on the Aqua10 Ultra Roller.

r95475 has a roller mop that can never be detached, so the device has no
`mop_pad_unmounting` capability and `mop_pad_installed` used to fall back to the
water tank check. MOP_PAD_INSTALLED is not read there on purpose: older firmwares
report it permanently as 1.

Run from the repo root:
    python3 tests/test_issue_1847.py
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _bootstrap import load_device  # noqa: E402

device_module = load_device()

from custom_components.dreame_vacuum.dreame.device import DreameVacuumDeviceStatus  # noqa: E402
from custom_components.dreame_vacuum.dreame.types import (  # noqa: E402
    DreameVacuumAutoSwitchProperty,
    DreameVacuumProperty,
    DreameVacuumTaskStatus,
)

CLEANGENIUS_AVAILABLE = device_module.PROPERTY_AVAILABILITY[DreameVacuumAutoSwitchProperty.CLEANGENIUS.name]


def _status(tank, mop_pad_installed=None, cleangenius_switch=0, unmounting=False, **capability):
    """Build a real status on a fake device, status only reaches the device via get_property/capability."""
    properties = {
        DreameVacuumProperty.WATER_TANK: tank,
        DreameVacuumProperty.TASK_STATUS: DreameVacuumTaskStatus.COMPLETED.value,
        DreameVacuumAutoSwitchProperty.CLEANGENIUS: cleangenius_switch,
    }
    if mop_pad_installed is not None:
        properties[DreameVacuumProperty.MOP_PAD_INSTALLED] = mop_pad_installed
    fake_capability = {
        "mop_pad_unmounting": unmounting,
        "embedded_tank": False,
        "cleangenius": True,
        "cruising": False,
    }
    fake_capability.update(capability)
    device = SimpleNamespace(get_property=properties.get, capability=SimpleNamespace(**fake_capability))
    return DreameVacuumDeviceStatus(device)


def _available(status):
    """Evaluate the CleanGenius availability lambda the way the entity layer does."""
    return CLEANGENIUS_AVAILABLE(SimpleNamespace(status=status, capability=status._capability))


def main():
    # Fixed or roller mop, tank reported: the pad cannot be detached, so it is installed.
    roller = _status(1)
    assert roller.mop_pad_installed is True
    assert _available(roller) is True
    assert roller.started is False and roller.fast_mapping is False and roller.cruising is False
    assert roller.spot_cleaning is False and roller.zone_cleaning is False

    # The reported failure: no tank reported at all, the roller mop is still attached.
    assert _status(0).mop_pad_installed is True
    # ... but CleanGenius stays hidden while neither tank nor mop is on the robot.
    assert _available(_status(0)) is False
    assert _available(_status(0, embedded_tank=True)) is True

    # Unmounting capable devices keep honouring MOP_PAD_INSTALLED.
    assert _status(1, mop_pad_installed=0, unmounting=True).mop_pad_installed is True
    assert _status(1, mop_pad_installed=1, unmounting=True).mop_pad_installed is False
    assert _available(_status(1, mop_pad_installed=0, unmounting=True)) is True
    assert _available(_status(1, mop_pad_installed=1, unmounting=True)) is False

    # CleanGenius is active when the switch is on and the pad counts as installed.
    assert _status(1, cleangenius_switch=1).cleangenius_cleaning is True
    assert _status(1, cleangenius=1, mop_pad_installed=1, unmounting=True).cleangenius_cleaning is False
    assert _status(1, cleangenius_switch=1, cleangenius=False).cleangenius_cleaning is False
    assert _status(1, cleangenius_switch=0).cleangenius_cleaning is False

    print("PASS: issue 1847 - detachable pads report their state, attached pads stay installed")


if __name__ == "__main__":
    main()
