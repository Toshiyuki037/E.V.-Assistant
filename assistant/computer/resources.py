"""
E.V.I.E. - Local Resource State

Phase 13C

Read-only CPU, memory, disk and battery telemetry.
"""

from __future__ import annotations

import os
import platform
import shutil
import time

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


class ResourceBackendUnavailable(RuntimeError):
    pass


def _require_psutil():
    if psutil is None:
        raise ResourceBackendUnavailable(
            "Phase 13C resource/process telemetry requires psutil. "
            "Install it with: python -m pip install psutil"
        )


def get_resource_state() -> dict:
    _require_psutil()

    virtual = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage(os.getcwd())

    battery = None

    try:
        value = psutil.sensors_battery()

        if value is not None:
            battery = {
                "percent": float(value.percent),
                "plugged_in": bool(value.power_plugged),
                "seconds_left": int(value.secsleft),
            }
    except Exception:
        battery = None

    return {
        "cpu": {
            "logical_count": psutil.cpu_count(logical=True),
            "physical_count": psutil.cpu_count(logical=False),
            "percent": float(
                psutil.cpu_percent(interval=0.15)
            ),
            "load_average": (
                list(os.getloadavg())
                if hasattr(os, "getloadavg")
                else []
            ),
        },
        "memory": {
            "total": int(virtual.total),
            "available": int(virtual.available),
            "used": int(virtual.used),
            "percent": float(virtual.percent),
            "swap_total": int(swap.total),
            "swap_used": int(swap.used),
            "swap_percent": float(swap.percent),
        },
        "disk": {
            "path": os.getcwd(),
            "total": int(disk.total),
            "used": int(disk.used),
            "free": int(disk.free),
            "percent": float(disk.percent),
        },
        "battery": battery,
        "host": {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "timestamp": time.time(),
    }
