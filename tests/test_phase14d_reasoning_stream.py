"""
E.V.I.E. Phase 14D2 provisional reasoning stream tests.

No network, API, microphone, CUDA, tools, or memory mutation required.
"""

import time

from assistant.voice.reasoning_stream import (
    ProvisionalReasoningWorker,
    ResponseSentenceAccumulator,
)


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
            "Sentence one. Sentence two! Sentence three?"
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


def test_worker_emits_streamed_sentences():

    events = []


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


    time.sleep(
        0.05
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


def test_new_version_suppresses_old_output():

    events = []


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        on_delta(
            "Old "
        )


        time.sleep(
            0.05
        )


        if is_current():

            on_delta(
                "response."
            )


    worker = (
        ProvisionalReasoningWorker(
            stream_fn=
                fake_stream,

            emit_fn=
                events.append,
        )
    )


    worker.start(
        version=1,

        text=
            "Old question.",
    )


    time.sleep(
        0.01
    )


    worker.start(
        version=2,

        text=
            "New question.",
    )


    time.sleep(
        0.10
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


def test_manual_invalidation_suppresses_remaining_output():

    events = []


    def fake_stream(
        text,
        *,
        on_delta,
        is_current,
    ):

        on_delta(
            "This is "
        )


        time.sleep(
            0.05
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
        )
    )


    worker.start(
        version=4,

        text=
            "Question.",
    )


    time.sleep(
        0.01
    )


    worker.invalidate(
        4
    )


    time.sleep(
        0.08
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