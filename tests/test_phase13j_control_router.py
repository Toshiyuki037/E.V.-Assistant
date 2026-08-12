
import pytest

import assistant.computer.control_executor as executor
from assistant.computer.control_context import ControlContext
from assistant.computer.control_models import (
    AttemptStatus,
    ComputerControlRequest,
    ControlMethod,
)
from assistant.computer.control_policy import (
    may_fallback_after,
    ordered_methods,
)


def test_default_method_order_puts_vision_last():
    request = ComputerControlRequest(
        action="vision.click",
        approved=True,
    )

    methods = ordered_methods(
        request
    )

    assert methods[-1] == ControlMethod.VISION


def test_vision_can_be_disabled():
    request = ComputerControlRequest(
        action="vision.click",
        allow_vision=False,
        approved=True,
    )

    assert (
        ControlMethod.VISION
        not in ordered_methods(
            request
        )
    )


def test_fallback_only_continues_for_absence_or_unsupported():
    assert may_fallback_after(
        AttemptStatus.UNSUPPORTED
    )

    assert may_fallback_after(
        AttemptStatus.NOT_FOUND
    )

    assert not may_fallback_after(
        AttemptStatus.AMBIGUOUS
    )

    assert not may_fallback_after(
        AttemptStatus.BLOCKED
    )

    assert not may_fallback_after(
        AttemptStatus.FAILED
    )


def test_medium_risk_action_requires_approval():
    request = ComputerControlRequest(
        action="accessibility.invoke",
        target="Notepad",
        approved=False,
    )

    with pytest.raises(PermissionError):
        executor.execute_computer_control(
            request
        )


def test_native_window_action_uses_native_first(
    monkeypatch,
):
    monkeypatch.setattr(
        executor,
        "focus_local_window",
        lambda target: {
            "title": target,
            "success": True,
        },
    )

    request = ComputerControlRequest(
        action="window.focus",
        target="Notepad",
        approved=True,
    )

    result = executor.execute_computer_control(
        request
    )

    assert result.success is True
    assert result.method == "native"
    assert (
        result.attempts[-1].status
        == AttemptStatus.SUCCESS
    )


def test_dom_action_uses_browser_session(
    monkeypatch,
):
    sentinel = object()

    monkeypatch.setattr(
        executor,
        "click_local_dom_element",
        lambda session, **kwargs: {
            "success": True,
            "verified": True,
            "session_ok": session is sentinel,
        },
    )

    request = ComputerControlRequest(
        action="browser.dom.click",
        arguments={
            "selector": "#hello",
        },
        approved=True,
    )

    context = ControlContext(
        request=request,
        browser_session=sentinel,
    )

    result = executor.execute_computer_control(
        request,
        context=context,
    )

    assert result.success is True
    assert result.method == "dom"
    assert (
        result.result["session_ok"]
        is True
    )
