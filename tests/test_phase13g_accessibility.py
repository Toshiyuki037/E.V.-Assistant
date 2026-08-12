import pytest

import assistant.computer.accessibility as accessibility
from assistant.computer.accessibility_models import (
    UIElementInfo,
)
from assistant.computer.capabilities import (
    get_action_risk,
)
from assistant.computer.models import (
    DeviceRisk,
)


def test_accessibility_inspection_is_read_only_risk():
    assert (
        get_action_risk(
            "accessibility.inspect"
        )
        == DeviceRisk.READ
    )


def test_accessibility_invocation_is_medium_risk():
    assert (
        get_action_risk(
            "accessibility.invoke"
        )
        == DeviceRisk.MEDIUM
    )


def test_find_ui_elements_filters_structured_tree(
    monkeypatch,
):
    monkeypatch.setattr(
        accessibility,
        "inspect_ui_tree",
        lambda *args, **kwargs: [
            UIElementInfo(
                name="File",
                control_type="MenuItem",
                automation_id="FileMenu",
            ).to_dict(),
            UIElementInfo(
                name="Edit",
                control_type="MenuItem",
                automation_id="EditMenu",
            ).to_dict(),
        ],
    )

    result = accessibility.find_ui_elements(
        "Notepad",
        name="file",
        control_type="MenuItem",
    )

    assert len(result) == 1
    assert result[0]["name"] == "File"


def test_find_ui_elements_requires_selector():
    with pytest.raises(ValueError):
        accessibility.find_ui_elements(
            "Notepad"
        )


def test_ui_element_model_serializes_patterns_and_path():
    item = UIElementInfo(
        name="Save",
        control_type="Button",
        patterns=[
            "invoke",
        ],
        path=[
            0,
            3,
            2,
        ],
    )

    payload = item.to_dict()

    assert payload["name"] == "Save"
    assert payload["patterns"] == [
        "invoke",
    ]
    assert payload["path"] == [
        0,
        3,
        2,
    ]
