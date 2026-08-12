"""
E.V.I.E. Phase 14D Provisional Reasoning Stream Tests

Phase 14D2:
    - streamed response sentence accumulation
    - stale-version suppression
    - manual invalidation

Phase 14D4:
    - candidate debounce
    - rapid candidate coalescing
    - single-flight reasoning
    - pending candidate cancellation

No:
    - network
    - OpenAI API
    - microphone
    - Whisper
    - CUDA
    - F5-TTS
    - tools
    - memory mutation

is required.
"""

from __future__ import annotations

import threading
import time

from assistant.voice.reasoning_stream import (
    ProvisionalReasoningWorker,
    ResponseSentenceAccumulator,
)


# ---------------------------------------------------------------------------
# Sentence Accumulator
# ---------------------------------------------------------------------------

def test_sentence_accumulator_waits_for_complete_sentence():

    accumulator = (
        ResponseSentenceAccumulator()
    )


    first = (
        accumulator.add(
            "A transistor is"
        )
    )


    assert first == []


    second = (
        accumulator.add(
            " a switch."
        )
    )


    assert second == [
        "A transistor is a switch."
    ]


def test_sentence_accumulator_handles_multiple_sentences():

    accumulator = (
        ResponseSentenceAccumulator()
    )


    sentences = (
        accumulator.add(
            (
                "Sentence one. "
                "Sentence two! "
                "Sentence three?"
            )
        )
    )


    assert sentences == [
        "Sentence one.",
        "Sentence two!",
        "Sentence three?",
    ]


def test_sentence_accumulator_preserves_incomplete_tail():

    accumulator = (
        ResponseSentenceAccumulator()
    )


    sentences = (
        accumulator.add(
            "Sentence one. unfinished"
        )
    )


    assert sentences == [
        "Sentence one."
    ]


    assert (
        accumulator.flush()
        == "unfinished"
    )


def test_sentence_accumulator_combines_split_deltas():

    accumulator = (
        ResponseSentenceAccumulator()
    )


    assert (
        accumulator.add(
            "Electrical "
        )
        == []
    )


    assert (
        accumulator.add(
            "engineering is "
        )
        == []
    )


    assert (
        accumulator.add(
            "important."
        )
        == [
            "Electrical engineering is important."
        ]
    )


def test_sentence_accumulator_flushes_remaining_text():

    accumulator = (
        ResponseSentenceAccumulator()
    )


    accumulator.add(
        "Incomplete response"
    )


    assert (
        accumulator.flush()
        == "Incomplete response"
    )


    assert (
        accumulator.buffer
        == ""
    )


# ---------------------------------------------------------------------------
# Basic Worker Streaming
# ---------------------------------------------------------------------------

def test_worker_emits_streamed_sentences():

    events = []

    finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        for delta in (
            "A transistor ",
            "is a switch. ",
            "It controls current.",
        ):

            if not is_current():

                return


            on_delta(
                delta
            )


        finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            emit_fn=
                events.append,

            debounce_seconds=
                0.0,
        )
    )


    assert (
        worker.start(
            version=1,

            text=
                "What is a transistor?",
        )
        is True
    )


    assert finished.wait(
        timeout=1.0
    )


    time.sleep(
        0.02
    )


    sentences = [
        event.text

        for event in events

        if event.kind
        == "sentence"
    ]


    assert sentences == [
        "A transistor is a switch.",
        "It controls current.",
    ]


def test_worker_emits_started_event():

    events = []

    finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            emit_fn=
                events.append,

            debounce_seconds=
                0.0,
        )
    )


    worker.start(
        version=1,

        text=
            "What is a transistor?",
    )


    assert finished.wait(
        timeout=1.0
    )


    time.sleep(
        0.02
    )


    started = [
        event

        for event in events

        if event.kind
        == "started"
    ]


    assert len(
        started
    ) == 1


    assert (
        started[0].version
        == 1
    )


    assert (
        started[0].text
        == "What is a transistor?"
    )


def test_worker_emits_finished_event():

    events = []

    stream_finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        on_delta(
            "Done."
        )

        stream_finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            emit_fn=
                events.append,

            debounce_seconds=
                0.0,
        )
    )


    worker.start(
        version=1,

        text=
            "Test.",
    )


    assert stream_finished.wait(
        timeout=1.0
    )


    time.sleep(
        0.02
    )


    assert any(
        event.kind
        == "finished"

        for event in events
    )


# ---------------------------------------------------------------------------
# Version / Stale Output
# ---------------------------------------------------------------------------

def test_new_version_suppresses_old_output():

    events = []

    first_started = (
        threading.Event()
    )

    release_first = (
        threading.Event()
    )

    second_finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        if (
            text
            == "Old question."
        ):

            first_started.set()


            on_delta(
                "Old "
            )


            release_first.wait(
                timeout=1.0
            )


            if is_current():

                on_delta(
                    "response."
                )


            return


        if is_current():

            on_delta(
                "New response."
            )


        second_finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            emit_fn=
                events.append,

            debounce_seconds=
                0.0,
        )
    )


    worker.start(
        version=1,

        text=
            "Old question.",
    )


    assert first_started.wait(
        timeout=1.0
    )


    worker.start(
        version=2,

        text=
            "New question.",
    )


    release_first.set()


    assert second_finished.wait(
        timeout=1.0
    )


    time.sleep(
        0.02
    )


    old_sentences = [
        event

        for event in events

        if (
            event.kind
            == "sentence"

            and event.version
            == 1
        )
    ]


    assert old_sentences == []


    new_sentences = [
        event.text

        for event in events

        if (
            event.kind
            == "sentence"

            and event.version
            == 2
        )
    ]


    assert new_sentences == [
        "New response."
    ]


def test_manual_invalidation_suppresses_remaining_output():

    events = []

    started = (
        threading.Event()
    )

    release = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        started.set()


        on_delta(
            "This is "
        )


        release.wait(
            timeout=1.0
        )


        if is_current():

            on_delta(
                "stale."
            )


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            emit_fn=
                events.append,

            debounce_seconds=
                0.0,
        )
    )


    worker.start(
        version=4,

        text=
            "Question.",
    )


    assert started.wait(
        timeout=1.0
    )


    worker.invalidate(
        4
    )


    release.set()


    time.sleep(
        0.05
    )


    sentences = [
        event

        for event in events

        if (
            event.kind
            == "sentence"

            and event.version
            == 4
        )
    ]


    assert sentences == []


def test_old_version_is_rejected():

    calls = []


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                lambda text, **kwargs:
                    calls.append(
                        text
                    ),

            debounce_seconds=
                0.01,
        )
    )


    worker.start(
        version=5,
        text="Current.",
    )


    result = (
        worker.start(
            version=4,
            text="Old.",
        )
    )


    assert result is False


# ---------------------------------------------------------------------------
# Phase 14D4 - Debounce / Coalescing
# ---------------------------------------------------------------------------

def test_rapid_candidates_are_coalesced():

    calls = []

    finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        calls.append(
            text
        )


        if is_current():

            on_delta(
                "Final candidate response."
            )


        finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            debounce_seconds=
                0.05,
        )
    )


    worker.start(
        version=1,

        text=
            "What is a transist?",
    )


    time.sleep(
        0.01
    )


    worker.start(
        version=2,

        text=
            "What is a transistor?",
    )


    time.sleep(
        0.01
    )


    worker.start(
        version=3,

        text=
            (
                "What is a transistor "
                "and why is it important?"
            ),
    )


    assert finished.wait(
        timeout=1.0
    )


    assert calls == [
        (
            "What is a transistor "
            "and why is it important?"
        )
    ]


def test_debounce_waits_before_starting_reasoning():

    started = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        started.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            debounce_seconds=
                0.10,
        )
    )


    worker.start(
        version=1,

        text=
            "What is a transistor?",
    )


    # The worker should not immediately launch.
    assert (
        started.wait(
            timeout=0.03
        )
        is False
    )


    # It should launch after debounce.
    assert started.wait(
        timeout=1.0
    )


def test_duplicate_candidate_replaces_without_parallel_generation():

    calls = []

    finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        calls.append(
            text
        )

        finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            debounce_seconds=
                0.05,
        )
    )


    worker.start(
        version=1,
        text="Question.",
    )


    time.sleep(
        0.01
    )


    worker.start(
        version=1,
        text="Question.",
    )


    assert finished.wait(
        timeout=1.0
    )


    assert calls == [
        "Question."
    ]


# ---------------------------------------------------------------------------
# Phase 14D4 - Single Flight
# ---------------------------------------------------------------------------

def test_only_one_reasoning_generation_runs_at_once():

    active = 0

    maximum_active = 0

    calls = []

    lock = (
        threading.Lock()
    )


    first_started = (
        threading.Event()
    )

    release_first = (
        threading.Event()
    )

    second_finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        nonlocal active
        nonlocal maximum_active


        with lock:

            active += 1

            maximum_active = max(
                maximum_active,
                active,
            )


        calls.append(
            text
        )


        if len(
            calls
        ) == 1:

            first_started.set()


            release_first.wait(
                timeout=1.0
            )


        if is_current():

            on_delta(
                "Response."
            )


        with lock:

            active -= 1


        if len(
            calls
        ) >= 2:

            second_finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            debounce_seconds=
                0.02,
        )
    )


    worker.start(
        version=1,

        text=
            "First candidate.",
    )


    assert first_started.wait(
        timeout=1.0
    )


    worker.start(
        version=2,

        text=
            "Second candidate.",
    )


    # Allow version 2 to survive its debounce period while
    # version 1 is deliberately still running.

    time.sleep(
        0.06
    )


    assert maximum_active == 1


    assert calls == [
        "First candidate."
    ]


    release_first.set()


    assert second_finished.wait(
        timeout=1.0
    )


    assert maximum_active == 1


    assert calls == [
        "First candidate.",
        "Second candidate.",
    ]


def test_latest_candidate_wins_while_generation_is_active():

    calls = []


    first_started = (
        threading.Event()
    )

    release_first = (
        threading.Event()
    )

    replacement_finished = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        calls.append(
            text
        )


        if len(
            calls
        ) == 1:

            first_started.set()


            release_first.wait(
                timeout=1.0
            )


            return


        replacement_finished.set()


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            debounce_seconds=
                0.02,
        )
    )


    worker.start(
        version=1,

        text=
            "First.",
    )


    assert first_started.wait(
        timeout=1.0
    )


    worker.start(
        version=2,

        text=
            "Second.",
    )


    time.sleep(
        0.005
    )


    worker.start(
        version=3,

        text=
            "Third.",
    )


    time.sleep(
        0.05
    )


    # Neither replacement should run concurrently.
    assert calls == [
        "First."
    ]


    release_first.set()


    assert replacement_finished.wait(
        timeout=1.0
    )


    assert calls == [
        "First.",
        "Third.",
    ]


# ---------------------------------------------------------------------------
# Phase 14D4 - Pending Cancellation
# ---------------------------------------------------------------------------

def test_invalidate_cancels_pending_candidate():

    calls = []


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        calls.append(
            text
        )


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            debounce_seconds=
                0.05,
        )
    )


    worker.start(
        version=1,

        text=
            "Pending candidate.",
    )


    worker.invalidate(
        1
    )


    time.sleep(
        0.10
    )


    assert calls == []


def test_invalidate_without_version_cancels_pending_candidate():

    calls = []


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        calls.append(
            text
        )


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            debounce_seconds=
                0.05,
        )
    )


    worker.start(
        version=1,

        text=
            "Pending.",
    )


    worker.invalidate()


    time.sleep(
        0.10
    )


    assert calls == []


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------

def test_current_reasoning_error_is_emitted():

    events = []

    started = (
        threading.Event()
    )


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        started.set()

        raise RuntimeError(
            "test failure"
        )


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            emit_fn=
                events.append,

            debounce_seconds=
                0.0,
        )
    )


    worker.start(
        version=1,

        text=
            "Question.",
    )


    assert started.wait(
        timeout=1.0
    )


    time.sleep(
        0.02
    )


    errors = [
        event

        for event in events

        if event.kind
        == "error"
    ]


    assert len(
        errors
    ) == 1


    assert (
        "test failure"
        in errors[0].text
    )