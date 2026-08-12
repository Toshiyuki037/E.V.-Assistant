"""
Phase 14C2 transcript-state tests.
"""

from assistant.voice.transcript_state import (
    TranscriptState,
    normalize_text,
    split_complete_sentences,
)


def test_normalize_text():

    assert (
        normalize_text(
            "  hello   there \n world "
        )
        == "hello there world"
    )


def test_split_complete_sentences():

    sentences, tail = (
        split_complete_sentences(
            "Hello there. How are you? I am"
        )
    )


    assert sentences == [
        "Hello there.",
        "How are you?",
    ]


    assert tail == "I am"


def test_incomplete_sentence_is_not_committed():

    state = (
        TranscriptState(
            required_stability=2
        )
    )


    update = (
        state.update_partial(
            "What is a transistor"
        )
    )


    assert (
        update.committed_text
        == ""
    )


    assert (
        update.unstable_text
        == "What is a transistor"
    )


def test_sentence_requires_multiple_stable_updates():

    state = (
        TranscriptState(
            required_stability=2
        )
    )


    first = (
        state.update_partial(
            "A transistor is a switch."
        )
    )


    second = (
        state.update_partial(
            "A transistor is a switch."
        )
    )


    assert (
        first.newly_committed
        == ()
    )


    assert (
        second.newly_committed
        == (
            "A transistor is a switch.",
        )
    )


def test_committed_sentence_is_not_reemitted():

    state = (
        TranscriptState(
            required_stability=2
        )
    )


    state.update_partial(
        "Sentence one."
    )


    state.update_partial(
        "Sentence one."
    )


    update = (
        state.update_partial(
            "Sentence one. Sentence two"
        )
    )


    assert (
        update.newly_committed
        == ()
    )


    assert (
        update.committed_text
        == "Sentence one."
    )


def test_second_sentence_can_commit_later():

    state = (
        TranscriptState(
            required_stability=2
        )
    )


    state.update_partial(
        "Sentence one."
    )


    state.update_partial(
        "Sentence one."
    )


    state.update_partial(
        "Sentence one. Sentence two."
    )


    update = (
        state.update_partial(
            "Sentence one. Sentence two."
        )
    )


    assert (
        update.newly_committed
        == (
            "Sentence two.",
        )
    )


    assert (
        update.committed_text
        == (
            "Sentence one. "
            "Sentence two."
        )
    )


def test_partial_rewrite_is_detected():

    state = (
        TranscriptState()
    )


    state.update_partial(
        "What is on my calendar"
    )


    update = (
        state.update_partial(
            "What is on the calendar"
        )
    )


    assert (
        update.rewritten
        is True
    )


def test_growing_partial_is_not_called_rewrite():

    state = (
        TranscriptState()
    )


    state.update_partial(
        "What is on my"
    )


    update = (
        state.update_partial(
            "What is on my calendar"
        )
    )


    assert (
        update.rewritten
        is False
    )


def test_finalization_commits_completed_sentences():

    state = (
        TranscriptState(
            required_stability=3
        )
    )


    state.update_partial(
        "Hello world."
    )


    final = (
        state.finalize(
            "Hello world."
        )
    )


    assert (
        final.final
        is True
    )


    assert (
        final.committed_text
        == "Hello world."
    )


    assert (
        final.newly_committed
        == (
            "Hello world.",
        )
    )


def test_finalization_preserves_unpunctuated_tail():

    state = (
        TranscriptState()
    )


    final = (
        state.finalize(
            "Sentence one. unfinished thought"
        )
    )


    assert (
        final.committed_text
        == "Sentence one."
    )


    assert (
        final.unstable_text
        == "unfinished thought"
    )


def test_final_transcript_can_reconcile_partial_wording():

    state = (
        TranscriptState(
            required_stability=2
        )
    )


    state.update_partial(
        "Turn on the light."
    )


    state.update_partial(
        "Turn on the light."
    )


    final = (
        state.finalize(
            "Turn on the lights."
        )
    )


    assert (
        final.rewritten
        is True
    )


    assert (
        final.committed_text
        == "Turn on the lights."
    )