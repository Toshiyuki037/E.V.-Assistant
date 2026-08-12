import pytest

import assistant.computer.audio as audio
import assistant.computer.camera as camera
import assistant.computer.microphone as microphone
from assistant.computer.capabilities import (
    get_action_risk,
)
from assistant.computer.models import (
    DeviceRisk,
)


def test_microphone_and_camera_capture_are_medium_risk():
    assert (
        get_action_risk(
            "microphone.capture"
        )
        == DeviceRisk.MEDIUM
    )

    assert (
        get_action_risk(
            "camera.capture"
        )
        == DeviceRisk.MEDIUM
    )


def test_audio_device_set_is_low_risk():
    assert (
        get_action_risk(
            "audio.set_evie_device"
        )
        == DeviceRisk.LOW
    )


def test_microphone_capture_duration_is_bounded(
    tmp_path,
):
    if (
        microphone.sd is None
        or microphone.np is None
    ):
        pytest.skip(
            "microphone dependencies unavailable"
        )

    with pytest.raises(ValueError):
        microphone.record_microphone_wav(
            str(
                tmp_path
                / "too-long.wav"
            ),
            duration_seconds=31,
        )


def test_camera_negative_index_is_rejected():
    if camera.cv2 is None:
        pytest.skip(
            "OpenCV unavailable"
        )

    with pytest.raises(ValueError):
        camera.inspect_camera(
            -1
        )


def test_audio_device_listing_returns_structured_devices():
    if audio.sd is None:
        pytest.skip(
            "sounddevice unavailable"
        )

    devices = audio.list_audio_devices()

    assert isinstance(
        devices,
        list,
    )

    if devices:
        assert devices[0].index >= 0
        assert isinstance(
            devices[0].name,
            str,
        )
