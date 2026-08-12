"""
Phase 14 persistent playback tests.

sounddevice is mocked; no physical speaker is required.
"""

from __future__ import annotations

import numpy as np

import assistant.voice.playback as playback_module

from assistant.voice.playback import (
    PersistentAudioPlayer,
)


class FakeOutputStream:

    created = []

    def __init__(
        self,
        *,
        samplerate,
        channels,
        dtype,
        blocksize,
    ):

        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize

        self.started = False
        self.closed = False
        self.aborted = False

        self.writes = []

        self.__class__.created.append(
            self
        )


    def start(
        self,
    ):

        self.started = True


    def write(
        self,
        audio,
    ):

        self.writes.append(
            np.asarray(
                audio
            )
            .copy()
        )


    def stop(
        self,
    ):

        pass


    def abort(
        self,
    ):

        self.aborted = True


    def close(
        self,
    ):

        self.closed = True


def install_fake_stream(
    monkeypatch,
):

    FakeOutputStream.created = []


    monkeypatch.setattr(
        playback_module.sd,
        "OutputStream",
        FakeOutputStream,
    )


def test_reuses_same_stream_for_matching_format(
    monkeypatch,
):

    install_fake_stream(
        monkeypatch
    )


    player = (
        PersistentAudioPlayer()
    )


    audio = (
        np.zeros(
            100,
            dtype=np.float32,
        )
    )


    assert player.play(
        audio,
        24000,
    )


    assert player.play(
        audio,
        24000,
    )


    assert len(
        FakeOutputStream.created
    ) == 1


    assert len(
        FakeOutputStream.created[
            0
        ].writes
    ) == 2


    player.close()


def test_mono_audio_is_written_as_single_channel(
    monkeypatch,
):

    install_fake_stream(
        monkeypatch
    )


    player = (
        PersistentAudioPlayer()
    )


    player.play(
        np.zeros(
            50,
            dtype=np.float32,
        ),
        24000,
    )


    stream = (
        FakeOutputStream.created[
            0
        ]
    )


    assert (
        stream.channels
        == 1
    )


    assert (
        stream.writes[
            0
        ].shape
        == (
            50,
            1,
        )
    )


    player.close()


def test_format_change_reopens_stream(
    monkeypatch,
):

    install_fake_stream(
        monkeypatch
    )


    player = (
        PersistentAudioPlayer()
    )


    player.play(
        np.zeros(
            50,
            dtype=np.float32,
        ),
        24000,
    )


    player.play(
        np.zeros(
            50,
            dtype=np.float32,
        ),
        16000,
    )


    assert len(
        FakeOutputStream.created
    ) == 2


    player.close()


def test_stop_current_aborts_stream(
    monkeypatch,
):

    install_fake_stream(
        monkeypatch
    )


    player = (
        PersistentAudioPlayer()
    )


    player.play(
        np.zeros(
            50,
            dtype=np.float32,
        ),
        24000,
    )


    stream = (
        FakeOutputStream.created[
            0
        ]
    )


    player.stop_current()


    assert stream.aborted

    assert stream.closed


    # Next chunk opens a clean stream.
    player.play(
        np.zeros(
            50,
            dtype=np.float32,
        ),
        24000,
    )


    assert len(
        FakeOutputStream.created
    ) == 2


    player.close()
