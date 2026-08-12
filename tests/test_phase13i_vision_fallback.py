import pytest
from assistant.computer.capabilities import get_action_risk
from assistant.computer.models import DeviceRisk
from assistant.computer.vision_fallback import (
    choose_visual_target,
    normalize_visual_target,
    validate_visual_target,
)

def test_vision_capture_is_read_only():
    assert get_action_risk("vision.capture") == DeviceRisk.READ

def test_vision_click_is_medium_risk():
    assert get_action_risk("vision.click") == DeviceRisk.MEDIUM

def test_visual_target_normalization_and_center():
    target = normalize_visual_target({
        "label": "Save",
        "x": 100,
        "y": 200,
        "width": 40,
        "height": 20,
        "confidence": 0.95,
    })
    assert target.center == (120, 210)

def test_visual_target_rejects_low_confidence():
    target = normalize_visual_target({
        "label": "Button",
        "x": 10,
        "y": 10,
        "width": 20,
        "height": 20,
        "confidence": 0.4,
    })
    with pytest.raises(ValueError):
        validate_visual_target(
            target,
            screen_width=1920,
            screen_height=1080,
            min_confidence=0.8,
        )

def test_visual_target_ambiguity_is_rejected():
    items = [
        normalize_visual_target({
            "label": "A", "x": 0, "y": 0, "width": 10, "height": 10, "confidence": 0.91
        }),
        normalize_visual_target({
            "label": "B", "x": 20, "y": 20, "width": 10, "height": 10, "confidence": 0.89
        }),
    ]
    with pytest.raises(LookupError):
        choose_visual_target(items, min_confidence=0.8)

def test_visual_click_requires_explicit_approval():
    from assistant.computer.vision_actions import click_visual_target
    target = normalize_visual_target({
        "label": "Test",
        "x": 10,
        "y": 10,
        "width": 20,
        "height": 20,
        "confidence": 0.99,
    })
    with pytest.raises(PermissionError):
        click_visual_target(
            target,
            screen_width=1920,
            screen_height=1080,
            approved=False,
        )
