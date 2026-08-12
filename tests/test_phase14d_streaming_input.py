"""
E.V.I.E. Phase 14D1 streaming-input coordinator tests.
"""

from assistant.voice.streaming_input import (
    StreamingInputCoordinator,
    is_action_sensitive,
    normalize_streaming_text,
)


def test_normalize_streaming_text():

    assert (
        normalize_streaming_text(
            "  What   is \n a transistor? "
        )
        == "What is a transistor?"
    )


def test_question_is_safe_for_provisional_reasoning():

    coordinator = (
        StreamingInputCoordinator()
    )


    snapshot = (
        coordinator.commit_sentence(
            "What is a transistor?"
        )
    )


    assert (
        snapshot.provisional_reasoning_allowed
        is True
    )


    assert (
        snapshot.action_sensitive
        is False
    )


def test_action_request_waits_for_finalization():

    coordinator = (
        StreamingInputCoordinator()
    )


    snapshot = (
        coordinator.commit_sentence(
            "Open Chrome."
        )
    )


    assert (
        snapshot.action_sensitive
        is True
    )


    assert (
        snapshot.provisional_reasoning_allowed
        is False
    )


def test_file_delete_is_action_sensitive():

    assert (
        is_action_sensitive(
            "Delete that file."
        )
        is True
    )


def test_memory_write_is_action_sensitive():

    assert (
        is_action_sensitive(
            "Remember that my test is tomorrow."
        )
        is True
    )


def test_normal_reasoning_is_not_action_sensitive():

    assert (
        is_action_sensitive(
            "Why do transistors amplify signals?"
        )
        is False
    )


def test_committed_sentences_create_versions():

    coordinator = (
        StreamingInputCoordinator()
    )


    first = (
        coordinator.commit_sentence(
            "Sentence one."
        )
    )


    second = (
        coordinator.commit_sentence(
            "Sentence two."
        )
    )


    assert first.version == 1

    assert second.version == 2


    assert (
        second.text
        == "Sentence one. Sentence two."
    )


def test_old_version_becomes_stale():

    coordinator = (
        StreamingInputCoordinator()
    )


    first = (
        coordinator.commit_sentence(
            "What is a transistor?"
        )
    )


    coordinator.commit_sentence(
        "Actually explain a MOSFET."
    )


    assert (
        coordinator.is_current(
            first.version
        )
        is False
    )


def test_duplicate_sentence_does_not_create_new_version():

    coordinator = (
        StreamingInputCoordinator()
    )


    first = (
        coordinator.commit_sentence(
            "Sentence one."
        )
    )


    second = (
        coordinator.commit_sentence(
            "Sentence one."
        )
    )


    assert (
        second.version
        == first.version
    )


def test_final_transcript_is_authoritative():

    coordinator = (
        StreamingInputCoordinator()
    )


    provisional = (
        coordinator.commit_sentence(
            "Turn on the light."
        )
    )


    final = (
        coordinator.finalize(
            "Turn on the lights."
        )
    )


    assert final.final is True

    assert (
        final.text
        == "Turn on the lights."
    )


    assert (
        final.invalidates_previous
        is True
    )


    assert (
        coordinator.is_current(
            provisional.version
        )
        is False
    )


def test_matching_final_still_becomes_final():

    coordinator = (
        StreamingInputCoordinator()
    )


    provisional = (
        coordinator.commit_sentence(
            "What is a transistor?"
        )
    )


    final = (
        coordinator.finalize(
            "What is a transistor?"
        )
    )


    assert final.final is True

    assert (
        final.invalidates_previous
        is False
    )


    assert (
        final.version
        > provisional.version
    )


def test_final_action_request_is_not_provisional():

    coordinator = (
        StreamingInputCoordinator()
    )


    final = (
        coordinator.finalize(
            "Open Chrome."
        )
    )


    assert final.final is True

    assert final.action_sensitive is True

    assert (
        final.provisional_reasoning_allowed
        is False
    )