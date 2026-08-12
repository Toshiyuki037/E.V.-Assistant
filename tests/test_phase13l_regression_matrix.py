
import pytest

import assistant.computer.control_executor as executor
from assistant.computer.control_models import (
    ComputerControlRequest,
)
from assistant.computer.control_policy import (
    ordered_methods,
)


def test_vision_remains_last_method():
    request = ComputerControlRequest(
        action="vision.click",
        approved=True,
    )

    assert (
        ordered_methods(request)[-1].value
        == "vision"
    )


def test_vision_can_be_disabled_globally_for_request():
    request = ComputerControlRequest(
        action="vision.click",
        approved=True,
        allow_vision=False,
    )

    assert "vision" not in [
        method.value
        for method in ordered_methods(
            request
        )
    ]


def test_approval_denial_stops_before_execution():
    request = ComputerControlRequest(
        action="accessibility.invoke",
        target="Notepad",
        approved=False,
    )

    with pytest.raises(PermissionError):
        executor.execute_computer_control(
            request
        )


def test_protected_filesystem_write_cannot_be_lowered_to_vision():
    request = ComputerControlRequest(
        action="filesystem.write",
        target=r"C:\Windows\System32\evie-test.txt",
        arguments={
            "content": "blocked",
        },
        approved=True,
    )

    result = executor.execute_computer_control(
        request
    )

    assert result.success is False

    methods = [
        attempt.method.value
        for attempt in result.attempts
    ]

    assert "vision" not in methods
