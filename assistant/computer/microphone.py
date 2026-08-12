"""
E.V.I.E. - Microphone Capture

Phase 13F

Provides bounded fixed-duration microphone recording to WAV.

Continuous streaming/VAD belongs to Phase 14 Voice 2.0.
"""

from __future__ import annotations

from pathlib import Path
import wave

from .media_models import CaptureResult

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None


class MicrophoneBackendUnavailable(RuntimeError):
    pass


def _require_backend():
    if sd is None or np is None:
        raise MicrophoneBackendUnavailable(
            "Phase 13F microphone capture requires numpy and sounddevice."
        )


def record_microphone_wav(
    path: str,
    *,
    duration_seconds: float = 2.0,
    sample_rate: int = 16000,
    channels: int = 1,
    device_index: int | None = None,
) -> CaptureResult:
    _require_backend()

    duration = float(
        duration_seconds
    )

    if duration <= 0:
        raise ValueError(
            "Microphone duration must be positive."
        )

    if duration > 30:
        raise ValueError(
            "Phase 13F microphone capture is bounded to 30 seconds."
        )

    rate = int(
        sample_rate
    )

    channel_count = int(
        channels
    )

    if rate <= 0:
        raise ValueError(
            "sample_rate must be positive."
        )

    if channel_count not in {
        1,
        2,
    }:
        raise ValueError(
            "Phase 13F microphone capture supports 1 or 2 channels."
        )

    target = Path(
        path
    ).resolve(
        strict=False
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame_count = int(
        duration * rate
    )

    audio = sd.rec(
        frame_count,
        samplerate=rate,
        channels=channel_count,
        dtype="int16",
        device=device_index,
    )

    sd.wait()

    data = np.asarray(
        audio,
        dtype=np.int16,
    )

    with wave.open(
        str(target),
        "wb",
    ) as wav:
        wav.setnchannels(
            channel_count
        )
        wav.setsampwidth(
            2
        )
        wav.setframerate(
            rate
        )
        wav.writeframes(
            data.tobytes()
        )

    verified = (
        target.exists()
        and target.stat().st_size > 44
    )

    return CaptureResult(
        kind="microphone_wav",
        path=str(target),
        success=verified,
        detail=(
            "Microphone capture complete."
            if verified
            else "Microphone capture could not be verified."
        ),
    )
