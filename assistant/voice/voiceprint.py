"""
E.V.I.E. - Lightweight Voice Identity Signal

Phase 14

IMPORTANT:
    Voice identity is ONE trust signal only.

    It MUST NOT bypass:
        - trusted-device state
        - authenticated session state
        - explicit confirmation
        - frozen Phase 1-13 dangerous-action authorization

Public API:
    save_voiceprint(...)
    verify_voiceprint(...)
    verify_voiceprint_audio(...)
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)

from pathlib import (
    Path,
)

import numpy as np
import soundfile as sf


@dataclass(
    frozen=True
)
class VoiceIdentityResult:

    matched: bool

    similarity: float

    threshold: float


def _mono(
    audio: np.ndarray,
) -> np.ndarray:

    audio = (
        np.asarray(
            audio,
            dtype=np.float32,
        )
    )


    if audio.ndim == 2:

        audio = (
            audio.mean(
                axis=1
            )
        )


    return (
        audio.reshape(
            -1
        )
    )


def _feature_vector(
    audio: np.ndarray,
    sample_rate: int,
) -> np.ndarray:

    audio = (
        _mono(
            audio
        )
    )


    if audio.size < max(
        256,
        int(
            sample_rate
        )
        // 4,
    ):

        raise ValueError(
            "Voice sample is too short."
        )


    audio = (
        audio
        - float(
            audio.mean()
        )
    )


    peak = (
        float(
            np.max(
                np.abs(
                    audio
                )
            )
        )
        or 1.0
    )


    audio = (
        audio
        / peak
    )


    frame = 1024

    hop = 512

    window = (
        np.hanning(
            frame
        )
        .astype(
            np.float32
        )
    )


    spectra = []


    for start in range(
        0,
        max(
            1,
            audio.size
            - frame
            + 1,
        ),
        hop,
    ):

        chunk = (
            audio[
                start:
                start
                + frame
            ]
        )


        if chunk.size < frame:

            chunk = (
                np.pad(
                    chunk,
                    (
                        0,
                        frame
                        - chunk.size,
                    ),
                )
            )


        magnitude = (
            np.abs(
                np.fft.rfft(
                    chunk
                    * window
                )
            )
            + 1e-8
        )


        spectra.append(
            np.log(
                magnitude
            )
        )


    spectrum = (
        np.vstack(
            spectra
        )
    )


    bins = (
        spectrum.shape[
            1
        ]
    )


    edges = (
        np.linspace(
            0,
            bins,
            33,
            dtype=int,
        )
    )


    pooled = []


    for left, right in zip(
        edges[
            :-1
        ],
        edges[
            1:
        ],
    ):

        band = (
            spectrum[
                :,
                left:
                    max(
                        left
                        + 1,
                        right,
                    )
            ]
        )


        pooled.extend(
            [
                float(
                    band.mean()
                ),
                float(
                    band.std()
                ),
            ]
        )


    vector = (
        np.asarray(
            pooled,
            dtype=np.float32,
        )
    )


    norm = (
        float(
            np.linalg.norm(
                vector
            )
        )
        or 1.0
    )


    return (
        vector
        / norm
    )


def voiceprint_from_audio(
    audio,
    sample_rate: int,
) -> np.ndarray:

    return (
        _feature_vector(
            np.asarray(
                audio
            ),
            int(
                sample_rate
            ),
        )
    )


def voiceprint_from_wav(
    path: str
    | Path,
) -> np.ndarray:

    audio, sample_rate = (
        sf.read(
            str(
                path
            ),
            always_2d=False,
        )
    )


    return (
        voiceprint_from_audio(
            audio,
            int(
                sample_rate
            ),
        )
    )


def save_voiceprint(
    wav_path: str
    | Path,
    output_path: str
    | Path,
):

    vector = (
        voiceprint_from_wav(
            wav_path
        )
    )


    output_path = (
        Path(
            output_path
        )
    )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    np.save(
        str(
            output_path
        ),
        vector,
    )


    return (
        output_path
    )


def _verify_vector(
    current: np.ndarray,
    enrolled_path: str
    | Path,
    *,
    threshold: float,
) -> VoiceIdentityResult:

    enrolled = (
        np.load(
            str(
                enrolled_path
            )
        )
        .astype(
            np.float32
        )
    )


    if current.shape != enrolled.shape:

        return (
            VoiceIdentityResult(
                matched=False,
                similarity=0.0,
                threshold=float(
                    threshold
                ),
            )
        )


    similarity = (
        float(
            np.dot(
                current,
                enrolled,
            )
            / (
                (
                    np.linalg.norm(
                        current
                    )
                    or 1.0
                )
                * (
                    np.linalg.norm(
                        enrolled
                    )
                    or 1.0
                )
            )
        )
    )


    return (
        VoiceIdentityResult(
            matched=(
                similarity
                >= float(
                    threshold
                )
            ),
            similarity=
                similarity,
            threshold=
                float(
                    threshold
                ),
        )
    )


def verify_voiceprint(
    wav_path: str
    | Path,
    enrolled_path: str
    | Path,
    *,
    threshold: float = 0.94,
) -> VoiceIdentityResult:

    current = (
        voiceprint_from_wav(
            wav_path
        )
    )


    return (
        _verify_vector(
            current,
            enrolled_path,
            threshold=
                threshold,
        )
    )


def verify_voiceprint_audio(
    audio,
    sample_rate: int,
    enrolled_path: str
    | Path,
    *,
    threshold: float = 0.94,
) -> VoiceIdentityResult:

    current = (
        voiceprint_from_audio(
            audio,
            int(
                sample_rate
            ),
        )
    )


    return (
        _verify_vector(
            current,
            enrolled_path,
            threshold=
                threshold,
        )
    )
