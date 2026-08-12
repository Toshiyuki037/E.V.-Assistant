"""
Phase 14H interruptible playback tests.
"""

from __future__ import annotations

import threading
import time

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

        self.write_started = (
            threading.Event()
        )

        self.release_write = (
            threading.Event()
        )

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

        self.write_started.set()

        # tiny delay gives interruption thread a chance to run
        time.sleep(
            0.002
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


def install_fake(
    monkeypatch,
):

    FakeOutputStream.created = []

    monkeypatch.setattr(
        playback_module.sd,
        "OutputStream",
        FakeOutputStream,
    )


def test_playback_is_written_in_small_blocks(
    monkeypatch,
):

    install_fake(
        monkeypatch
    )

    player = (
        PersistentAudioPlayer(
            write_block_ms=20,
        )
    )

    audio = (
        np.zeros(
            2400,
            dtype=np.float32,
        )
    )

    assert player.play(
        audio,
        24000,
    )

    stream = (
        FakeOutputStream.created[
            0
        ]
    )

    assert len(
        stream.writes
    ) > 1

    player.close()


def test_stop_current_interrupts_active_chunk(
    monkeypatch,
):

    install_fake(
        monkeypatch
    )

    player = (
        PersistentAudioPlayer(
            write_block_ms=10,
        )
    )

    audio = (
        np.zeros(
            24000,
            dtype=np.float32,
        )
    )

    result = {}

    thread = (
        threading.Thread(
            target=
                lambda:
                    result.setdefault(
                        "completed",
                        player.play(
                            audio,
                            24000,
                        ),
                    )
        )
    )

    thread.start()

    deadline = (
        time.time()
        + 1.0
    )

    while (
        not player.is_speaking
        and time.time()
        < deadline
    ):

        time.sleep(
            0.001
        )

    assert player.is_speaking

    player.stop_current()

    thread.join(
        timeout=1.0
    )

    assert not thread.is_alive()

    assert (
        result[
            "completed"
        ]
        is False
    )

    player.close()
