"""
E.V.I.E. - Safe Local System Actions

Phase 13E

Only a small bounded action set is exposed here.

- lock workstation requires explicit approval
- opening Windows Settings is handled separately
- shutdown/restart/sleep are intentionally NOT implemented in Phase 13E
"""

from __future__ import annotations

import ctypes
import sys


IS_WINDOWS = sys.platform == "win32"


class SystemActionUnavailable(RuntimeError):
    pass


def lock_workstation(
    *,
    approved: bool = False,
) -> dict:
    if not IS_WINDOWS:
        raise SystemActionUnavailable(
            "Lock workstation is only available on Windows."
        )

    if not approved:
        raise PermissionError(
            "Locking the workstation requires explicit approval."
        )

    user32 = ctypes.WinDLL(
        "user32",
        use_last_error=True,
    )

    user32.LockWorkStation.argtypes = []
    user32.LockWorkStation.restype = ctypes.c_bool

    success = bool(
        user32.LockWorkStation()
    )

    if not success:
        raise RuntimeError(
            "Windows rejected LockWorkStation."
        )

    return {
        "action": "lock_workstation",
        "success": True,
    }


def supported_system_actions() -> dict[str, dict]:
    return {
        "lock_workstation": {
            "risk": "medium",
            "approval_required": True,
        },
        "shutdown": {
            "risk": "high",
            "implemented": False,
        },
        "restart": {
            "risk": "high",
            "implemented": False,
        },
        "sleep": {
            "risk": "high",
            "implemented": False,
        },
    }
