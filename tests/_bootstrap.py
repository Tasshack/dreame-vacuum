"""Import the dreame device layer without Home Assistant installed.

Stubs the two modules that pull in HA/network dependencies (protocol, map) so
device.py can be imported and its status logic exercised standalone.

Usage:
    from _bootstrap import load_device
    device_module = load_device()
"""

import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_device():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    for name in ("custom_components", "custom_components.dreame_vacuum"):
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules.setdefault(name, module)
    sys.modules["custom_components.dreame_vacuum"].__path__ = [
        os.path.join(ROOT, "custom_components", "dreame_vacuum")
    ]

    package = "custom_components.dreame_vacuum.dreame"
    protocol = types.ModuleType(f"{package}.protocol")
    protocol.DreameVacuumProtocol = type("DreameVacuumProtocol", (), {})
    sys.modules[f"{package}.protocol"] = protocol

    map_module = types.ModuleType(f"{package}.map")
    map_module.DreameMapVacuumMapManager = type("DreameMapVacuumMapManager", (), {})
    map_module.DreameVacuumMapDecoder = type("DreameVacuumMapDecoder", (), {})
    sys.modules[f"{package}.map"] = map_module

    import custom_components.dreame_vacuum.dreame.device as device

    return device
