"""
E.V.I.E. - Audio Device Enumeration

Phase 13F

Uses sounddevice/PortAudio for structured local audio-device discovery.

Important:
Changing sounddevice.default.device only changes E.V.I.E.'s process-local
default for future captures/playback. It does NOT change the Windows-wide
default audio device.
"""

from __future__ import annotations

from .media_models import AudioDeviceInfo

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None


class AudioBackendUnavailable(RuntimeError):
    pass


def _require_sounddevice():
    if sd is None:
        raise AudioBackendUnavailable(
            "Phase 13F audio control requires sounddevice. "
            "Install it with: python -m pip install sounddevice"
        )


def _default_devices() -> tuple[int | None, int | None]:
    _require_sounddevice()

    try:
        value = sd.default.device
    except Exception:
        return None, None

    if isinstance(value, (tuple, list)):
        input_index = value[0] if len(value) > 0 else None
        output_index = value[1] if len(value) > 1 else None
    else:
        input_index = value
        output_index = value

    try:
        input_index = int(input_index)
    except Exception:
        input_index = None

    try:
        output_index = int(output_index)
    except Exception:
        output_index = None

    return input_index, output_index


def list_audio_devices() -> list[AudioDeviceInfo]:
    _require_sounddevice()

    devices = sd.query_devices()
    host_apis = sd.query_hostapis()
    default_input, default_output = _default_devices()

    result = []

    for index, device in enumerate(devices):
        host_api_index = int(
            device.get("hostapi", -1)
        )

        host_name = ""

        if 0 <= host_api_index < len(host_apis):
            host_name = str(
                host_apis[host_api_index].get(
                    "name",
                    "",
                )
            )

        result.append(
            AudioDeviceInfo(
                index=index,
                name=str(
                    device.get(
                        "name",
                        f"Audio device {index}",
                    )
                ),
                host_api=host_name,
                max_input_channels=int(
                    device.get(
                        "max_input_channels",
                        0,
                    )
                ),
                max_output_channels=int(
                    device.get(
                        "max_output_channels",
                        0,
                    )
                ),
                default_sample_rate=float(
                    device.get(
                        "default_samplerate",
                        0.0,
                    )
                ),
                is_default_input=(
                    index == default_input
                ),
                is_default_output=(
                    index == default_output
                ),
            )
        )

    return result


def list_microphones() -> list[AudioDeviceInfo]:
    return [
        device
        for device in list_audio_devices()
        if device.max_input_channels > 0
    ]


def list_output_devices() -> list[AudioDeviceInfo]:
    return [
        device
        for device in list_audio_devices()
        if device.max_output_channels > 0
    ]


def get_default_audio_devices() -> dict:
    input_index, output_index = _default_devices()

    devices = {
        device.index: device
        for device in list_audio_devices()
    }

    return {
        "input": (
            devices[input_index].to_dict()
            if input_index in devices
            else None
        ),
        "output": (
            devices[output_index].to_dict()
            if output_index in devices
            else None
        ),
    }


def set_evie_audio_device(
    *,
    input_index: int | None = None,
    output_index: int | None = None,
) -> dict:
    """
    Set E.V.I.E.'s process-local PortAudio defaults.

    This is intentionally not a Windows-wide default-device mutation.
    """

    _require_sounddevice()

    current_input, current_output = _default_devices()

    final_input = (
        current_input
        if input_index is None
        else int(input_index)
    )

    final_output = (
        current_output
        if output_index is None
        else int(output_index)
    )

    devices = list_audio_devices()
    valid_indices = {
        device.index
        for device in devices
    }

    if (
        final_input is not None
        and final_input not in valid_indices
    ):
        raise ValueError(
            f"Unknown input audio device index: {final_input}"
        )

    if (
        final_output is not None
        and final_output not in valid_indices
    ):
        raise ValueError(
            f"Unknown output audio device index: {final_output}"
        )

    if final_input is not None:
        input_device = next(
            device
            for device in devices
            if device.index == final_input
        )

        if input_device.max_input_channels <= 0:
            raise ValueError(
                f"Audio device {final_input} has no input channels."
            )

    if final_output is not None:
        output_device = next(
            device
            for device in devices
            if device.index == final_output
        )

        if output_device.max_output_channels <= 0:
            raise ValueError(
                f"Audio device {final_output} has no output channels."
            )

    sd.default.device = (
        final_input,
        final_output,
    )

    return get_default_audio_devices()
