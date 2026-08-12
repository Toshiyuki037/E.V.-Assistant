from assistant.computer.action_catalog import ACTION_SCHEMAS
from assistant.computer.desktop_layout import resolve_user_path
from assistant.computer.capabilities import get_action_risk
from assistant.computer.models import DeviceRisk


def test_required_actions():
    for action in ("monitor.list", "window.close", "window.place", "filesystem.exists", "filesystem.inspect"):
        assert action in ACTION_SCHEMAS


def test_desktop_alias_resolves_outside_repo():
    path = resolve_user_path("Desktop/EVIE-Phase13-Test.txt")
    normalized = path.lower().replace("/", "\\")
    assert normalized.endswith(r"\desktop\evie-phase13-test.txt")
    assert r"\eve-assistant\desktop\evie-phase13-test.txt" not in normalized


def test_window_close_risk():
    assert get_action_risk("window.close") == DeviceRisk.MEDIUM


def test_filesystem_exists_risk():
    assert get_action_risk("filesystem.exists") == DeviceRisk.READ


def test_window_place_risk():
    assert get_action_risk("window.place") == DeviceRisk.LOW
