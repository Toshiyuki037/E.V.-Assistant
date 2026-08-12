import pytest

import assistant.computer.notifications as notifications
import assistant.computer.settings as settings
from assistant.computer.capabilities import (
    get_action_risk,
)
from assistant.computer.models import (
    DeviceRisk,
)
from assistant.computer.system_actions import (
    lock_workstation,
    supported_system_actions,
)


def test_notification_action_is_low_risk():
    assert (
        get_action_risk(
            "notification.send"
        )
        == DeviceRisk.LOW
    )


def test_settings_open_action_is_low_risk():
    assert (
        get_action_risk(
            "settings.open"
        )
        == DeviceRisk.LOW
    )


def test_settings_page_resolution_is_allowlisted():
    assert (
        settings.resolve_settings_page(
            "display"
        )
        == "ms-settings:display"
    )

    with pytest.raises(ValueError):
        settings.resolve_settings_page(
            "cmd.exe"
        )


def test_lock_requires_explicit_approval():
    with pytest.raises(PermissionError):
        lock_workstation(
            approved=False,
        )


def test_high_risk_power_actions_are_not_implemented():
    actions = supported_system_actions()

    assert (
        actions["shutdown"]["implemented"]
        is False
    )

    assert (
        actions["restart"]["implemented"]
        is False
    )

    assert (
        actions["sleep"]["implemented"]
        is False
    )


def test_notification_payload_validation():
    with pytest.raises(ValueError):
        notifications.send_windows_notification(
            "",
            "hello",
        )

    with pytest.raises(ValueError):
        notifications.send_windows_notification(
            "E.V.I.E.",
            "",
        )
