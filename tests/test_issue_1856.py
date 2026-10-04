"""Issue #1856: CLEANING_PROGRESS_INFO must never be requested.

v2.0.0 added did 69 to the first get_properties batch. Its payload is huge, so
the batch times out and cloud discovery fails with error 80001.
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _bootstrap import load_device  # noqa: E402

device_module = load_device()
DreameVacuumProperty = device_module.DreameVacuumProperty


class FakeProtocol:
    def __init__(self, *args, **kwargs) -> None:
        self.cloud = None
        self.dreame_cloud = True
        self.prefer_cloud = False
        self.requested = []

    def get_properties(self, properties, timeout=None):
        self.requested.append(list(properties))
        return []


def load_device_instance():
    device_module.DreameVacuumProtocol = FakeProtocol
    device = device_module.DreameVacuumDevice("test", "127.0.0.1", "token")
    # Info is read by capability load that runs on the first property response
    device.info = SimpleNamespace(model="test.productions.vacuum.c102cn", mac_address="00:11:22:33:44:55", version=1)
    return device


def main():
    device = load_device_instance()

    assert DreameVacuumProperty.CLEANING_PROGRESS_INFO not in device._default_properties, (
        "CLEANING_PROGRESS_INFO is requested in the first batch and times out cloud discovery"
    )
    assert DreameVacuumProperty.STATE in device._default_properties
    assert DreameVacuumProperty.BATTERY_LEVEL in device._default_properties
    assert len(device._default_properties) > 100

    device._request_properties()

    assert device._protocol.requested, "no get_properties batch was sent"
    for batch in device._protocol.requested:
        for prop in batch:
            assert prop["did"] != str(DreameVacuumProperty.CLEANING_PROGRESS_INFO.value), f"did 69 requested: {batch}"

    print(f"PASS: {len(device._protocol.requested)} batches, no did 69")


if __name__ == "__main__":
    main()
