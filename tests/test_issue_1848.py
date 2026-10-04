"""Issue #1848: SCHEDULED_CLEAN 4 is a manual mopping after sweeping run, not a schedule.

r9419h reports SCHEDULED_CLEAN 4 with TASK_TYPE 1 for a manually started
"mopping after sweeping" run, which the app and the robot both accept setting
changes on. Counting 4 as a schedule hid fan speed and the suction select for
the whole run.

Run from the repo root:
    python3 tests/test_issue_1848.py
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
    DreameVacuumStatus,
    DreameVacuumTaskStatus,
    DreameVacuumTaskType,
)


class FakeDevice:
    """Status only reaches the device through get_property and capability."""

    def __init__(self, properties, task_type_capability):
        self.properties = properties
        self.capability = SimpleNamespace(task_type=task_type_capability)

    def get_property(self, prop):
        return self.properties.get(prop)


def _status(scheduled_clean, task_type=None, started=True, task_type_capability=True):
    properties = {
        DreameVacuumProperty.SCHEDULED_CLEAN: scheduled_clean,
        DreameVacuumProperty.TASK_TYPE: task_type,
        DreameVacuumProperty.TASK_STATUS: (
            DreameVacuumTaskStatus.AUTO_CLEANING if started else DreameVacuumTaskStatus.COMPLETED
        ),
        DreameVacuumProperty.STATUS: DreameVacuumStatus.CLEANING if started else DreameVacuumStatus.CHARGING,
    }
    return DreameVacuumDeviceStatus(FakeDevice(properties, task_type_capability))


def main():
    # Manual mopping after sweeping run: settings must stay editable.
    assert _status(4, DreameVacuumTaskType.STANDARD).scheduled_clean is False
    assert _status(4, DreameVacuumTaskType.STANDARD_PAUSED).scheduled_clean is False

    # A real schedule from the app reports 1 and TASK_TYPE 7, and stays hidden.
    assert _status(1, DreameVacuumTaskType.SCHEDULED).scheduled_clean is True
    assert _status(1, DreameVacuumTaskType.SCHEDULED_PAUSED).scheduled_clean is True

    # 4 is untouched when the device does not report TASK_TYPE, so models that
    # report it for a real schedule keep hiding their settings.
    assert _status(4, None, task_type_capability=False).scheduled_clean is True
    assert _status(4, DreameVacuumTaskType.SCHEDULED).scheduled_clean is True

    # Unrelated values are unchanged.
    assert _status(2, DreameVacuumTaskType.SCHEDULED).scheduled_clean is True
    assert _status(0, DreameVacuumTaskType.STANDARD).scheduled_clean is False
    assert _status(None, DreameVacuumTaskType.STANDARD).scheduled_clean is False
    assert _status(3, DreameVacuumTaskType.STANDARD).scheduled_clean is False

    # Nothing runs, so nothing is a schedule.
    assert _status(1, DreameVacuumTaskType.SCHEDULED, started=False).scheduled_clean is False
    assert _status(4, DreameVacuumTaskType.STANDARD, started=False).scheduled_clean is False

    # Values are re-read on every access, so a run going 0 -> 4 and back needs no reset.
    status = _status(0, DreameVacuumTaskType.STANDARD)
    assert status.scheduled_clean is False
    status._device.properties[DreameVacuumProperty.SCHEDULED_CLEAN] = 4
    assert status.scheduled_clean is False
    status._device.properties[DreameVacuumProperty.SCHEDULED_CLEAN] = 1
    assert status.scheduled_clean is True

    print("issue 1848: manual mopping after sweeping run (SCHEDULED_CLEAN 4) no longer reads as a schedule")


if __name__ == "__main__":
    main()
