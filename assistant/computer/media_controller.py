"""
E.V.I.E. - Local Media Hardware Controller

Phase 13F

Kept separate from the main computer controller to avoid coupling future
Voice 2.0 streaming state to filesystem/window/process control.
"""

from __future__ import annotations

from .audio import (
    get_default_audio_devices,
    list_audio_devices,
    list_microphones,
    list_output_devices,
    set_evie_audio_device,
)
from .camera import (
    capture_camera_frame,
    list_cameras,
)
from .microphone import (
    record_microphone_wav,
)


def list_local_audio_devices():
    return [
        device.to_dict()
        for device in list_audio_devices()
    ]


def list_local_microphones():
    return [
        device.to_dict()
        for device in list_microphones()
    ]


def list_local_output_devices():
    return [
        device.to_dict()
        for device in list_output_devices()
    ]


def get_local_default_audio_devices():
    return get_default_audio_devices()


def set_local_evie_audio_device(
    *,
    input_index: int | None = None,
    output_index: int | None = None,
):
    return set_evie_audio_device(
        input_index=input_index,
        output_index=output_index,
    )


def record_local_microphone(
    path: str,
    *,
    duration_seconds: float = 2.0,
    sample_rate: int = 16000,
    channels: int = 1,
    device_index: int | None = None,
):
    return record_microphone_wav(
        path,
        duration_seconds=duration_seconds,
        sample_rate=sample_rate,
        channels=channels,
        device_index=device_index,
    ).to_dict()


def list_local_cameras(
    *,
    max_index: int = 5,
):
    return [
        camera.to_dict()
        for camera in list_cameras(
            max_index=max_index
        )
    ]


def capture_local_camera_frame(
    path: str,
    *,
    camera_index: int = 0,
):
    return capture_camera_frame(
        path,
        camera_index=camera_index,
    ).to_dict()
