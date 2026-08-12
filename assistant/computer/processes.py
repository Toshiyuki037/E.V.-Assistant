"""
E.V.I.E. - Process Inspection & Safe Termination

Phase 13C

Process reads are unrestricted.
Termination is deliberately bounded:
- PID must be explicit.
- E.V.I.E.'s own process cannot be terminated through this function.
- known critical Windows process names are blocked.
- caller must explicitly pass approved=True.
"""

from __future__ import annotations

import os

from .process_models import ProcessInfo

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


class ProcessBackendUnavailable(RuntimeError):
    pass


CRITICAL_PROCESS_NAMES = {
    "csrss.exe",
    "dwm.exe",
    "lsass.exe",
    "services.exe",
    "smss.exe",
    "wininit.exe",
    "winlogon.exe",
    "system",
    "registry",
}


def _require_psutil():
    if psutil is None:
        raise ProcessBackendUnavailable(
            "Phase 13C process control requires psutil. "
            "Install it with: python -m pip install psutil"
        )


def _safe_value(callable_, default):
    try:
        value = callable_()
        return default if value is None else value
    except Exception:
        return default


def _to_process_info(process) -> ProcessInfo:
    return ProcessInfo(
        pid=int(process.pid),
        name=str(
            _safe_value(process.name, "")
        ),
        executable=str(
            _safe_value(process.exe, "")
        ),
        username=str(
            _safe_value(process.username, "")
        ),
        status=str(
            _safe_value(process.status, "")
        ),
        cpu_percent=float(
            _safe_value(process.cpu_percent, 0.0)
        ),
        memory_percent=float(
            _safe_value(process.memory_percent, 0.0)
        ),
        memory_rss=int(
            _safe_value(
                lambda: process.memory_info().rss,
                0,
            )
        ),
        create_time=float(
            _safe_value(process.create_time, 0.0)
        ),
    )


def list_processes() -> list[ProcessInfo]:
    _require_psutil()

    processes = []

    for process in psutil.process_iter():
        try:
            processes.append(
                _to_process_info(process)
            )
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return sorted(
        processes,
        key=lambda item: (
            -item.memory_rss,
            item.name.lower(),
            item.pid,
        ),
    )


def find_processes(
    query: str,
) -> list[ProcessInfo]:
    text = str(query or "").strip().lower()

    if not text:
        return []

    return [
        item
        for item in list_processes()
        if (
            text in item.name.lower()
            or text in item.executable.lower()
        )
    ]


def get_process(
    pid: int,
) -> ProcessInfo:
    _require_psutil()

    process = psutil.Process(
        int(pid)
    )

    return _to_process_info(
        process
    )


def top_processes(
    *,
    limit: int = 10,
    sort_by: str = "memory",
) -> list[ProcessInfo]:
    items = list_processes()

    if sort_by == "cpu":
        items = sorted(
            items,
            key=lambda item: item.cpu_percent,
            reverse=True,
        )

    elif sort_by == "memory_percent":
        items = sorted(
            items,
            key=lambda item: item.memory_percent,
            reverse=True,
        )

    else:
        items = sorted(
            items,
            key=lambda item: item.memory_rss,
            reverse=True,
        )

    return items[:max(1, int(limit))]


def terminate_process(
    pid: int,
    *,
    approved: bool = False,
    timeout: float = 5.0,
) -> dict:
    _require_psutil()

    if not approved:
        raise PermissionError(
            "Process termination requires explicit approval."
        )

    pid = int(pid)

    if pid == os.getpid():
        raise PermissionError(
            "E.V.I.E. cannot terminate its own process through "
            "the Phase 13C process controller."
        )

    process = psutil.Process(pid)

    name = str(
        _safe_value(process.name, "")
    ).lower()

    if name in CRITICAL_PROCESS_NAMES:
        raise PermissionError(
            f"Refusing to terminate protected process: {name}"
        )

    process.terminate()

    try:
        process.wait(
            timeout=float(timeout)
        )

        terminated = True
        killed = False

    except psutil.TimeoutExpired:
        terminated = False
        killed = False

    return {
        "pid": pid,
        "name": name,
        "terminated": terminated,
        "killed": killed,
    }
