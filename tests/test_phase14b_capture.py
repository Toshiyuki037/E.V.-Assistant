"""
Phase 14B microphone capture support tests.

These tests validate utterance-buffer behavior without requiring
live microphone hardware or CUDA inference.
"""

import numpy as np

from assistant.listen import (
    UtteranceBuffer,
)


def _frame(
    value: int,
    samples: int = 480,
):
    return np.full(
        (
            samples,
            1,
        ),
        value,
        dtype=np.int16,
    )


def test_pre_roll_is_retained_before_start():

    buffer = (
        UtteranceBuffer(
            pre_roll_frames=3
        )
    )


    buffer.add_pre_roll(
        _frame(
            100
        )
    )

    buffer.add_pre_roll(
        _frame(
            200
        )
    )


    buffer.start()


    audio = (
        buffer.audio()
    )


    assert audio is not None

    assert len(audio) == (
        480
        * 2
    )


    assert audio[0][0] == 100

    assert audio[480][0] == 200


def test_pre_roll_discards_oldest_frames():

    buffer = (
        UtteranceBuffer(
            pre_roll_frames=2
        )
    )


    buffer.add_pre_roll(
        _frame(
            100
        )
    )

    buffer.add_pre_roll(
        _frame(
            200
        )
    )

    buffer.add_pre_roll(
        _frame(
            300
        )
    )


    buffer.start()


    audio = (
        buffer.audio()
    )


    assert audio is not None

    assert len(audio) == (
        480
        * 2
    )


    assert audio[0][0] == 200

    assert audio[480][0] == 300


def test_active_frames_append_after_pre_roll():

    buffer = (
        UtteranceBuffer(
            pre_roll_frames=2
        )
    )


    buffer.add_pre_roll(
        _frame(
            100
        )
    )


    buffer.start()


    buffer.add_frame(
        _frame(
            500
        )
    )


    buffer.add_frame(
        _frame(
            900
        )
    )


    audio = (
        buffer.audio()
    )


    assert audio is not None

    assert len(audio) == (
        480
        * 3
    )


    assert audio[0][0] == 100

    assert audio[480][0] == 500

    assert audio[960][0] == 900


def test_empty_buffer_returns_none():

    buffer = (
        UtteranceBuffer()
    )


    assert (
        buffer.audio()
        is None
    )


def test_add_active_frame_before_start_fails():

    buffer = (
        UtteranceBuffer()
    )


    try:

        buffer.add_frame(
            _frame(
                100
            )
        )

    except RuntimeError:

        pass

    else:

        raise AssertionError(
            "Expected RuntimeError."
        )


def test_reset_clears_buffer_state():

    buffer = (
        UtteranceBuffer(
            pre_roll_frames=2
        )
    )


    buffer.add_pre_roll(
        _frame(
            100
        )
    )


    buffer.start()


    buffer.add_frame(
        _frame(
            500
        )
    )


    buffer.reset()


    assert buffer.started is False

    assert (
        buffer.audio()
        is None
    )