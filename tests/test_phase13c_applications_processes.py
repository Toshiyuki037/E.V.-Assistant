import os

import pytest

import assistant.computer.applications as applications
import assistant.computer.processes as processes
from assistant.computer.process_models import (
    ProcessInfo,
)


def test_common_windows_alias_resolves_deterministically(
    monkeypatch,
):
    monkeypatch.setattr(
        applications.shutil,
        "which",
        lambda name: (
            r"C:\Windows\System32\notepad.exe"
            if name.lower() == "notepad.exe"
            else None
        ),
    )

    result = applications.resolve_application(
        "notepad"
    )

    assert result.endswith(
        "notepad.exe"
    )


def test_find_processes_filters_name_and_executable(
    monkeypatch,
):
    monkeypatch.setattr(
        processes,
        "list_processes",
        lambda: [
            ProcessInfo(
                pid=10,
                name="Code.exe",
                executable=r"C:\Apps\Code.exe",
            ),
            ProcessInfo(
                pid=20,
                name="python.exe",
                executable=r"C:\Python\python.exe",
            ),
        ],
    )

    result = processes.find_processes(
        "code"
    )

    assert len(result) == 1
    assert result[0].pid == 10


def test_process_termination_requires_explicit_approval():
    with pytest.raises(PermissionError):
        processes.terminate_process(
            os.getpid(),
            approved=False,
        )


def test_self_termination_is_blocked_even_when_approved():
    if processes.psutil is None:
        pytest.skip("psutil not installed")

    with pytest.raises(PermissionError):
        processes.terminate_process(
            os.getpid(),
            approved=True,
        )


def test_resource_state_has_cpu_memory_and_disk():
    import assistant.computer.resources as resources

    if resources.psutil is None:
        pytest.skip("psutil not installed")

    state = resources.get_resource_state()

    assert "cpu" in state
    assert "memory" in state
    assert "disk" in state
    assert state["memory"]["total"] > 0
