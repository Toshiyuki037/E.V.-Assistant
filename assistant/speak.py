"""
E.V.I.E. - Voice Synthesis Module

Phase 14 Rolling Speech Update
Phase 16E Low-Latency First Chunk

Behavior:
    The first speech chunk is synthesized immediately.
    As soon as playback of that chunk begins, the synthesis worker can prepare
    the following chunk. This repeats until the complete response has played.

Phase 16E:
    The first rolling speech chunk is reduced to one sentence. Later chunks
    remain paired. This improves time-to-first-audio without discarding any
    response content.

The resident LuxTTS worker remains protected by one process-wide TTS lock.
"""

from __future__ import annotations

import queue
import threading

from pathlib import (
    Path,
)

from .voice.luxtts_client import (
    CLIENT,
)

from .speech_formatter import (
    prepare_spoken_chunks,
)

from .telemetry import (
    mark,
    span,
)

from .voice.low_latency import (
    prepare_low_latency_chunks,
)

from .voice.playback import (
    PLAYER,
)


ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parent
    .parent
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

REF_TEXT = (
    REF_TEXT_FILE
    .read_text(
        encoding="utf-8"
    )
    .strip()
)


print(
    "Preparing E.V.I.E. LuxTTS backend..."
)

_TTS_LOCK = (
    threading.Lock()
)

_ACTIVE_SPEECH_LOCK = (
    threading.RLock()
)

_ACTIVE_SPEECH_CANCEL = None

print(
    "E.V.I.E. LuxTTS backend configured."
)


def synthesize_audio(
    text: str,
):
    """
    LuxTTS adapter for E.V.I.E.'s existing speech architecture.

    Contract remains unchanged:
        text -> (audio, sample_rate)

    LuxTTS itself runs in its dedicated Conda environment through
    the persistent worker client.
    """

    text = (
        str(
            text
            or ""
        )
        .strip()
    )

    if not text:
        return (
            None,
            0,
        )

    with _TTS_LOCK:
        return (
            CLIENT.synthesize(
                text
            )
        )

def play_audio(
    audio,
    sample_rate: int,
):
    return (
        PLAYER.play(
            audio,
            int(
                sample_rate
            ),
        )
    )


def _set_active_cancel(
    cancel_event,
):
    global _ACTIVE_SPEECH_CANCEL

    with _ACTIVE_SPEECH_LOCK:
        previous = (
            _ACTIVE_SPEECH_CANCEL
        )

        _ACTIVE_SPEECH_CANCEL = (
            cancel_event
        )

    if (
        previous is not None
        and previous
        is not cancel_event
    ):
        previous.set()


def _clear_active_cancel(
    cancel_event,
):
    global _ACTIVE_SPEECH_CANCEL

    with _ACTIVE_SPEECH_LOCK:
        if (
            _ACTIVE_SPEECH_CANCEL
            is cancel_event
        ):
            _ACTIVE_SPEECH_CANCEL = (
                None
            )


def stop_audio():
    with _ACTIVE_SPEECH_LOCK:
        cancel_event = (
            _ACTIVE_SPEECH_CANCEL
        )

    if cancel_event is not None:
        cancel_event.set()

    PLAYER.stop_current()


def pause_audio():
    PLAYER.pause_current()


def resume_audio():
    PLAYER.resume_current()


def audio_is_speaking() -> bool:
    return (
        PLAYER.is_speaking
    )


def audio_is_paused() -> bool:
    return (
        PLAYER.is_paused
    )


def close_audio():
    stop_audio()

    PLAYER.close()

    CLIENT.stop()


def _audio_duration(
    audio,
    sample_rate: int,
):
    try:
        return (
            len(
                audio
            )
            / float(
                sample_rate
            )
        )

    except Exception:
        return 0.0


def speak_streaming_response(
    text: str,
    *,
    sentences_per_chunk: int = 2,
    max_chunk_characters: int = 340,
):
    """
    Speak the entire response using rolling LuxTTS synthesis.

    Pipeline:
        first sentence synthesize
            ↓
        first sentence playback
            + following two-sentence chunk synthesis in parallel
            ↓
        next chunk playback
            + following chunk synthesis in parallel
            ↓
        ...until complete
    """

    chunks = (
        prepare_spoken_chunks(
            text,
            sentences_per_chunk=
                sentences_per_chunk,
            max_chunk_characters=
                max_chunk_characters,
        )
    )


    # -----------------------------------------------------------------------
    # Phase 16E - Lower Time To First Audio
    # -----------------------------------------------------------------------
    #
    # Preserve every sentence while making only the FIRST synthesis chunk
    # one sentence. Remaining speech stays grouped in two-sentence chunks.
    # -----------------------------------------------------------------------

    chunks = (
        prepare_low_latency_chunks(
            chunks
        )
    )


    if not chunks:
        return

    cancel_event = (
        threading.Event()
    )

    _set_active_cancel(
        cancel_event
    )

    audio_queue = (
        queue.Queue(
            maxsize=
                2,
        )
    )

    sentinel = (
        object()
    )

    def synthesis_worker():
        try:
            for index, chunk in enumerate(
                chunks
            ):
                if cancel_event.is_set():
                    break

                mark(
                    "tts_generation_started"
                )

                with span(
                    "tts_generation",
                    chunk_index=
                        index,
                    characters=
                        len(
                            chunk
                        ),
                ):
                    audio, sample_rate = (
                        synthesize_audio(
                            chunk
                        )
                    )

                mark(
                    "tts_generation_finished"
                )

                if cancel_event.is_set():
                    break

                audio_queue.put(
                    (
                        index,
                        chunk,
                        audio,
                        sample_rate,
                    )
                )

        except Exception as error:
            print(
                "\n[Rolling Speech Synthesis Warning]"
            )

            print(
                error
            )

        finally:
            audio_queue.put(
                sentinel
            )

    worker = (
        threading.Thread(
            target=
                synthesis_worker,
            daemon=
                True,
            name=
                "evie-rolling-tts-synthesis",
        )
    )

    worker.start()

    first_audio = True

    try:
        while not cancel_event.is_set():
            item = (
                audio_queue.get()
            )

            if item is sentinel:
                break

            (
                index,
                chunk,
                audio,
                sample_rate,
            ) = item

            if (
                audio is None
                or int(
                    sample_rate
                )
                <= 0
            ):
                continue

            if first_audio:
                mark(
                    "audio_playback_started"
                )

                mark(
                    "first_audio_started"
                )

                first_audio = False

            audio_duration = (
                _audio_duration(
                    audio,
                    int(
                        sample_rate
                    ),
                )
            )

            with span(
                "tts_playback",
                chunk_index=
                    index,
                audio_seconds=
                    round(
                        audio_duration,
                        3,
                    ),
            ):
                play_audio(
                    audio,
                    int(
                        sample_rate
                    ),
                )

            if cancel_event.is_set():
                break

        mark(
            "audio_playback_finished"
        )

    finally:
        cancel_event.set()

        worker.join(
            timeout=
                2.0,
        )

        _clear_active_cancel(
            cancel_event
        )


def speak(
    text: str,
):
    """
    Backwards-compatible public speech function.

    It now uses rolling full-response synthesis rather than one giant TTS call.
    """

    text = (
        str(
            text
            or ""
        )
        .strip()
    )

    if not text:
        return

    return (
        speak_streaming_response(
            text
        )
    )
