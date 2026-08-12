"""
E.V.I.E. - Speech Recognition Module

Phase 14H addition:
    exposes on_speech_started callback from the VAD boundary.

This callback is intentionally fired immediately when VAD confirms speech,
before final transcription exists.

It is the correct low-latency hook for interrupting E.V.I.E. playback.
"""

from __future__ import annotations

import os
import tempfile
import threading
import time
import wave

from collections import (
    deque,
)

import numpy as np
import sounddevice as sd

from faster_whisper import (
    WhisperModel,
)

from .voice.stt_config import (
    CONDITION_ON_PREVIOUS_TEXT,
    FINAL_BEAM_SIZE,
    PARTIAL_BEAM_SIZE,
    WHISPER_HOTWORDS,
    WHISPER_LANGUAGE,
    WHISPER_MODEL_NAME,
    WHISPER_VAD_FILTER,
)

from .voice.transcription import (
    PartialTranscriber,
    TranscriptEvent,
    TranscriptionResult,
)

from .voice.transcript_state import (
    TranscriptState,
)

from .voice.streaming_input import (
    StreamingInputCoordinator,
)

from .voice.vad import (
    DEFAULT_FRAME_DURATION_MS,
    DEFAULT_SAMPLE_RATE,
    VoiceActivityDetector,
    frame_samples,
)


SAMPLE_RATE = DEFAULT_SAMPLE_RATE
CHANNELS = 1

FRAME_DURATION_MS = DEFAULT_FRAME_DURATION_MS

FRAME_SAMPLES = (
    frame_samples(
        sample_rate=SAMPLE_RATE,
        frame_duration_ms=FRAME_DURATION_MS,
    )
)


PRE_ROLL_SECONDS = 0.50

LISTEN_TIMEOUT_SECONDS = 12.0

MAX_UTTERANCE_SECONDS = 45.0

PARTIAL_INITIAL_DELAY_SECONDS = 1.25

PARTIAL_INTERVAL_SECONDS = 1.20

VAD_SPEECH_THRESHOLD = 0.010

VAD_START_FRAMES = 2

VAD_END_SILENCE_MS = 2000

VAD_MINIMUM_UTTERANCE_MS = 180


PRE_ROLL_FRAMES = max(
    1,
    int(
        round(
            (
                PRE_ROLL_SECONDS
                * 1000.0
            )
            / FRAME_DURATION_MS
        )
    ),
)


print(
    "Loading speech recognition..."
)

print(
    (
        "STT model: "
        f"{WHISPER_MODEL_NAME}"
    )
)

print(
    "STT language: English only"
)


whisper = (
    WhisperModel(
        WHISPER_MODEL_NAME,
        device="cuda",
        compute_type="float16",
    )
)


_WHISPER_LOCK = (
    threading.Lock()
)


print(
    "Speech recognition ready."
)


def create_vad():

    return (
        VoiceActivityDetector(
            sample_rate=SAMPLE_RATE,
            frame_duration_ms=FRAME_DURATION_MS,
            speech_threshold=VAD_SPEECH_THRESHOLD,
            start_frames=VAD_START_FRAMES,
            end_silence_ms=VAD_END_SILENCE_MS,
            minimum_utterance_ms=VAD_MINIMUM_UTTERANCE_MS,
        )
    )


class UtteranceBuffer:

    def __init__(
        self,
        *,
        pre_roll_frames: int = PRE_ROLL_FRAMES,
    ):

        self.pre_roll = (
            deque(
                maxlen=max(
                    1,
                    int(
                        pre_roll_frames
                    ),
                )
            )
        )

        self.recorded_frames = []

        self.started = False


    def reset(
        self,
    ):
        """
        Clears all captured utterance state so this buffer can be reused
        safely after interruption or cancellation.
        """

        self.pre_roll.clear()

        self.recorded_frames.clear()

        self.started = False


    def add_pre_roll(
        self,
        frame: np.ndarray,
    ):

        if self.started:

            return

        self.pre_roll.append(
            np.asarray(
                frame,
                dtype=np.int16,
            )
            .copy()
        )


    def start(
        self,
    ):

        if self.started:

            return

        self.recorded_frames.extend(
            list(
                self.pre_roll
            )
        )

        self.pre_roll.clear()

        self.started = True


    def add_frame(
        self,
        frame: np.ndarray,
    ):

        if not self.started:

            raise RuntimeError(
                "UtteranceBuffer has not started."
            )

        self.recorded_frames.append(
            np.asarray(
                frame,
                dtype=np.int16,
            )
            .copy()
        )


    def audio(
        self,
    ):

        if not self.recorded_frames:

            return None

        return (
            np.concatenate(
                self.recorded_frames,
                axis=0,
            )
            .astype(
                np.int16,
                copy=False,
            )
        )


def write_temporary_wav(
    audio: np.ndarray,
) -> str:

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
    ) as temp:

        filename = (
            temp.name
        )

    with wave.open(
        filename,
        "wb",
    ) as wav:

        wav.setnchannels(
            CHANNELS
        )

        wav.setsampwidth(
            2
        )

        wav.setframerate(
            SAMPLE_RATE
        )

        wav.writeframes(
            audio.tobytes()
        )

    return filename


def transcribe_audio_result(
    audio: np.ndarray,
    *,
    beam_size: int = FINAL_BEAM_SIZE,
) -> TranscriptionResult:

    filename = None

    try:

        filename = (
            write_temporary_wav(
                audio
            )
        )

        with _WHISPER_LOCK:

            segments, _ = (
                whisper.transcribe(
                    filename,

                    language=
                        WHISPER_LANGUAGE,

                    task=
                        "transcribe",

                    beam_size=
                        int(
                            beam_size
                        ),

                    vad_filter=
                        WHISPER_VAD_FILTER,

                    condition_on_previous_text=
                        CONDITION_ON_PREVIOUS_TEXT,

                    hotwords=
                        WHISPER_HOTWORDS,

                    temperature=
                        0.0,
                )
            )

            segment_list = (
                list(
                    segments
                )
            )

        text = " ".join(
            segment.text.strip()

            for segment
            in segment_list

            if segment.text.strip()
        ).strip()

        return (
            TranscriptionResult(
                text=text,
                language=WHISPER_LANGUAGE,
                language_probability=None,
            )
        )

    finally:

        if filename and os.path.exists(
            filename
        ):

            try:

                os.remove(
                    filename
                )

            except OSError:

                pass


def transcribe_partial_audio_result(
    audio: np.ndarray,
) -> TranscriptionResult:

    return (
        transcribe_audio_result(
            audio,
            beam_size=PARTIAL_BEAM_SIZE,
        )
    )


def transcribe_final_audio_result(
    audio: np.ndarray,
) -> TranscriptionResult:

    return (
        transcribe_audio_result(
            audio,
            beam_size=FINAL_BEAM_SIZE,
        )
    )


class LiveTranscriptController:

    def __init__(
        self,
        *,
        required_stability: int = 2,
        on_streaming_candidate=None,
        on_streaming_final=None,
    ):

        self.state = (
            TranscriptState(
                required_stability=
                    required_stability,
            )
        )

        self.language = (
            WHISPER_LANGUAGE
        )

        self.language_probability = None

        self.streaming_input = (
            StreamingInputCoordinator()
        )

        self.on_streaming_candidate = (
            on_streaming_candidate
        )

        self.on_streaming_final = (
            on_streaming_final
        )


    def handle_partial(
        self,
        event: TranscriptEvent,
    ):

        update = (
            self.state.update_partial(
                event.text
            )
        )

        print(
            (
                "[Partial — en] "
                f"{event.text}"
            )
        )

        if (
            self.on_streaming_candidate
            is not None
        ):

            for sentence in (
                update.newly_committed
            ):

                snapshot = (
                    self.streaming_input
                    .commit_sentence(
                        sentence
                    )
                )

                if (
                    snapshot
                    .provisional_reasoning_allowed
                ):

                    self.on_streaming_candidate(
                        snapshot
                    )

        if update.rewritten:

            print(
                "[Transcript revised]"
            )

        return update


    def finalize(
        self,
        result: TranscriptionResult,
    ):

        update = (
            self.state.finalize(
                result.text
            )
        )

        snapshot = (
            self.streaming_input.finalize(
                result.text
            )
        )

        if (
            self.on_streaming_final
            is not None
        ):

            self.on_streaming_final(
                snapshot
            )

        print(
            (
                "[Final transcript — en] "
                f"{result.text}"
            )
        )

        if update.rewritten:

            print(
                "[Final transcript reconciled]"
            )

        return update


def record_utterance(
    *,
    on_streaming_candidate=None,
    on_streaming_final=None,
    on_speech_started=None,
):
    """
    Captures one utterance.

    on_speech_started:
        called immediately when VAD confirms speech onset.
        This is intentionally earlier than partial/final transcription.
    """

    print(
        "\nListening..."
    )

    detector = (
        create_vad()
    )

    buffer = (
        UtteranceBuffer()
    )

    transcript_controller = (
        LiveTranscriptController(
            required_stability=2,
            on_streaming_candidate=
                on_streaming_candidate,
            on_streaming_final=
                on_streaming_final,
        )
    )

    partial_worker = (
        PartialTranscriber(
            transcribe_fn=
                transcribe_partial_audio_result,
            emit_fn=
                transcript_controller.handle_partial,
            sample_rate=
                SAMPLE_RATE,
        )
    )

    listen_started_at = (
        time.monotonic()
    )

    speech_started_at = None

    next_partial_at = None

    try:

        with sd.InputStream(
            samplerate=
                SAMPLE_RATE,
            channels=
                CHANNELS,
            dtype=
                "int16",
            blocksize=
                FRAME_SAMPLES,
        ) as stream:

            while True:

                frame, overflowed = (
                    stream.read(
                        FRAME_SAMPLES
                    )
                )

                frame = (
                    np.asarray(
                        frame,
                        dtype=np.int16,
                    )
                    .copy()
                )

                vad_result = (
                    detector.process_frame(
                        frame
                    )
                )

                if not buffer.started:

                    buffer.add_pre_roll(
                        frame
                    )

                    if vad_result.speech_started:

                        buffer.start()

                        speech_started_at = (
                            time.monotonic()
                        )

                        next_partial_at = (
                            speech_started_at
                            + PARTIAL_INITIAL_DELAY_SECONDS
                        )

                        partial_worker.start()

                        print(
                            "Speech detected."
                        )

                        if (
                            on_speech_started
                            is not None
                        ):

                            try:

                                on_speech_started()

                            except Exception as error:

                                print(
                                    (
                                        "[Speech-start callback warning] "
                                        f"{error}"
                                    )
                                )

                    else:

                        if (
                            time.monotonic()
                            - listen_started_at
                            >= LISTEN_TIMEOUT_SECONDS
                        ):

                            print(
                                "Listening timed out."
                            )

                            return (
                                None,
                                transcript_controller,
                            )

                        continue

                else:

                    buffer.add_frame(
                        frame
                    )

                now = (
                    time.monotonic()
                )

                if (
                    next_partial_at
                    is not None
                    and now >= next_partial_at
                    and not vad_result.speech_ended
                ):

                    snapshot = (
                        buffer.audio()
                    )

                    if snapshot is not None:

                        partial_worker.submit(
                            snapshot
                        )

                    next_partial_at = (
                        now
                        + PARTIAL_INTERVAL_SECONDS
                    )

                if vad_result.speech_ended:

                    print(
                        "Speech complete."
                    )

                    break

                if (
                    speech_started_at
                    is not None
                    and (
                        now
                        - speech_started_at
                    )
                    >= MAX_UTTERANCE_SECONDS
                ):

                    print(
                        "Maximum utterance length reached."
                    )

                    break

    finally:

        partial_worker.stop(
            wait=True
        )

    return (
        buffer.audio(),
        transcript_controller,
    )


def listen(
    *,
    on_streaming_candidate=None,
    on_streaming_final=None,
    on_speech_started=None,
):

    audio, transcript_controller = (
        record_utterance(
            on_streaming_candidate=
                on_streaming_candidate,
            on_streaming_final=
                on_streaming_final,
            on_speech_started=
                on_speech_started,
        )
    )

    if audio is None:

        return ""

    print(
        "Finalizing transcription..."
    )

    result = (
        transcribe_final_audio_result(
            audio
        )
    )

    text = (
        result.text.strip()
    )

    if not text:

        return ""

    transcript_controller.finalize(
        result
    )

    return text


if __name__ == "__main__":

    result = (
        listen()
    )

    print(
        "\nTranscription:"
    )

    print(
        result
        or "<nothing>"
    )
