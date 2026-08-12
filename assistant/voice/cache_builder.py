"""
E.V.I.E. - Phase 14A.5 Acknowledgement Cache Builder

Purpose:
    Generates a small set of acknowledgement WAV files ahead of time.

Phase 14A.5:
    Adds silence padding around generated speech so short cached
    acknowledgements do not lose their beginning or ending during playback.

Run:

    python -m assistant.voice.cache_builder
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from f5_tts.api import F5TTS


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


REF_AUDIO = (
    ROOT
    / "evie-voice"
    / "references"
    / "evie-neutral.wav"
)


REF_TEXT_FILE = (
    ROOT
    / "evie-voice"
    / "references"
    / "evie-neutral.txt"
)


CACHE_DIR = (
    ROOT
    / "runtime"
    / "voice_cache"
)


# ---------------------------------------------------------------------------
# Audio Padding
# ---------------------------------------------------------------------------

LEADING_SILENCE_SECONDS = 0.15

TRAILING_SILENCE_SECONDS = 0.20


# ---------------------------------------------------------------------------
# Cached Phrases
# ---------------------------------------------------------------------------

PHRASES = {
    "on_it.wav":
        "On it. ",

    "got_it.wav":
        "Got it. ",

    "checking.wav":
        "Checking. ",

    "working_on_it.wav":
        "I'm working on it. ",

    "one_moment.wav":
        "One moment. ",

    "yes_boss.wav":
        "Yes boss. ",

    "got_it_boss.wav":
        "Got it boss. ",
}


# ---------------------------------------------------------------------------
# Add Silence Padding
# ---------------------------------------------------------------------------

def add_silence_padding(
    path: Path,
):
    """
    Adds leading and trailing silence around a generated WAV.

    Leading silence gives the Windows/audio-device playback path time
    to wake before the first phoneme.

    Trailing silence prevents the final phoneme from sounding clipped.
    """

    audio, sample_rate = (
        sf.read(
            str(
                path
            ),
            always_2d=True,
        )
    )


    channels = (
        audio.shape[
            1
        ]
    )


    leading_frames = int(
        sample_rate
        * LEADING_SILENCE_SECONDS
    )


    trailing_frames = int(
        sample_rate
        * TRAILING_SILENCE_SECONDS
    )


    leading_silence = (
        np.zeros(
            (
                leading_frames,
                channels,
            ),
            dtype=audio.dtype,
        )
    )


    trailing_silence = (
        np.zeros(
            (
                trailing_frames,
                channels,
            ),
            dtype=audio.dtype,
        )
    )


    padded = (
        np.concatenate(
            [
                leading_silence,
                audio,
                trailing_silence,
            ],
            axis=0,
        )
    )


    # Return mono files to mono if F5 generated mono.
    if channels == 1:

        padded = (
            padded[
                :,
                0
            ]
        )


    sf.write(
        str(
            path
        ),
        padded,
        sample_rate,
    )


# ---------------------------------------------------------------------------
# Cache Builder
# ---------------------------------------------------------------------------

def build_cache(
    *,
    overwrite: bool = False,
):
    """
    Generates acknowledgement audio files.

    Existing files are reused unless overwrite=True.
    """

    print(
        "Preparing E.V.I.E. acknowledgement cache..."
    )


    # -----------------------------------------------------------------------
    # Validate Reference Files
    # -----------------------------------------------------------------------

    if not REF_AUDIO.is_file():

        raise FileNotFoundError(
            (
                "Reference audio not found: "
                f"{REF_AUDIO}"
            )
        )


    if not REF_TEXT_FILE.is_file():

        raise FileNotFoundError(
            (
                "Reference text not found: "
                f"{REF_TEXT_FILE}"
            )
        )


    # -----------------------------------------------------------------------
    # Cache Directory
    # -----------------------------------------------------------------------

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    print(
        "Cache directory:"
    )

    print(
        CACHE_DIR
    )


    # -----------------------------------------------------------------------
    # Reference Text
    # -----------------------------------------------------------------------

    ref_text = (
        REF_TEXT_FILE
        .read_text(
            encoding="utf-8"
        )
        .strip()
    )


    if not ref_text:

        raise ValueError(
            "Reference text file is empty."
        )


    # -----------------------------------------------------------------------
    # Load F5 Once
    # -----------------------------------------------------------------------

    print(
        "Loading E.V.I.E. voice model "
        "for acknowledgement generation..."
    )


    tts = F5TTS(
        model=
            "F5TTS_v1_Base"
    )


    print(
        "Voice model ready."
    )


    generated = 0
    skipped = 0


    # -----------------------------------------------------------------------
    # Generate Each Phrase
    # -----------------------------------------------------------------------

    for filename, phrase in PHRASES.items():

        output_path = (
            CACHE_DIR
            / filename
        )


        if (
            output_path.exists()
            and not overwrite
        ):

            print(
                (
                    "Already cached: "
                    f"{filename}"
                )
            )

            skipped += 1

            continue


        print(
            (
                f"Generating "
                f"{filename}: "
                f"{phrase}"
            )
        )


        # -------------------------------------------------------------------
        # Generate Raw Voice
        # -------------------------------------------------------------------

        tts.infer(
            ref_file=
                str(
                    REF_AUDIO
                ),

            ref_text=
                ref_text,

            gen_text=
                phrase,

            file_wave=
                str(
                    output_path
                ),
        )


        if not output_path.is_file():

            raise RuntimeError(
                (
                    "F5-TTS returned without "
                    "creating "
                    f"{output_path}"
                )
            )


        # -------------------------------------------------------------------
        # Add Pre-Roll / Post-Roll
        # -------------------------------------------------------------------

        add_silence_padding(
            output_path
        )


        print(
            (
                "Created and padded: "
                f"{output_path}"
            )
        )


        generated += 1


    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    print()

    print(
        "Acknowledgement cache complete."
    )

    print(
        f"Generated: {generated}"
    )

    print(
        f"Skipped: {skipped}"
    )

    print(
        (
            "Leading silence: "
            f"{LEADING_SILENCE_SECONDS:.2f}s"
        )
    )

    print(
        (
            "Trailing silence: "
            f"{TRAILING_SILENCE_SECONDS:.2f}s"
        )
    )

    print(
        f"Location: {CACHE_DIR}"
    )


    return {
        "generated":
            generated,

        "skipped":
            skipped,

        "directory":
            str(
                CACHE_DIR
            ),
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    build_cache(
        overwrite=True
    )