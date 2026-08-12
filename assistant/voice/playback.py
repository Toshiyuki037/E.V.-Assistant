"""
E.V.I.E. - Persistent Interruptible Audio Playback Controller

Phase 14I

Adds:
    - interrupt
    - pause
    - resume
    - speaking / paused state

Audio is written in short blocks so control changes take effect quickly.
"""

from __future__ import annotations

import threading
import time

import numpy as np
import sounddevice as sd


DEFAULT_WRITE_BLOCK_MS = 20


class PersistentAudioPlayer:

    def __init__(
        self,
        *,
        dtype: str = "float32",
        write_block_ms: int = DEFAULT_WRITE_BLOCK_MS,
    ):

        self.dtype = str(
            dtype
        )

        self.write_block_ms = max(
            5,
            int(
                write_block_ms
            ),
        )

        self._stream_lock = (
            threading.RLock()
        )

        self._stream = None

        self._sample_rate = None

        self._channels = None

        self._closed = False

        self._stop_requested = (
            threading.Event()
        )

        self._pause_requested = (
            threading.Event()
        )

        self._speaking = (
            threading.Event()
        )


    @property
    def is_speaking(
        self,
    ) -> bool:

        return (
            self._speaking.is_set()
        )


    @property
    def is_paused(
        self,
    ) -> bool:

        return (
            self._pause_requested.is_set()
        )


    @staticmethod
    def _normalize_audio(
        audio,
    ):

        array = (
            np.asarray(
                audio
            )
        )


        if array.size == 0:

            return None


        if array.ndim == 1:

            array = (
                array.reshape(
                    -1,
                    1,
                )
            )


        elif array.ndim != 2:

            raise ValueError(
                (
                    "Audio must be mono or "
                    "two-dimensional PCM."
                )
            )


        return (
            np.asarray(
                array,
                dtype=np.float32,
            )
        )


    def _close_stream_locked(
        self,
    ):

        stream = (
            self._stream
        )

        self._stream = None

        self._sample_rate = None

        self._channels = None


        if stream is None:

            return


        try:

            stream.stop()

        except Exception:

            pass


        try:

            stream.close()

        except Exception:

            pass


    def _ensure_stream_locked(
        self,
        *,
        sample_rate: int,
        channels: int,
    ):

        if self._closed:

            raise RuntimeError(
                "PersistentAudioPlayer is closed."
            )


        if (
            self._stream is not None
            and self._sample_rate
            == int(
                sample_rate
            )
            and self._channels
            == int(
                channels
            )
        ):

            return (
                self._stream
            )


        self._close_stream_locked()


        stream = (
            sd.OutputStream(
                samplerate=
                    int(
                        sample_rate
                    ),

                channels=
                    int(
                        channels
                    ),

                dtype=
                    self.dtype,

                blocksize=
                    0,
            )
        )


        stream.start()


        self._stream = (
            stream
        )

        self._sample_rate = (
            int(
                sample_rate
            )
        )

        self._channels = (
            int(
                channels
            )
        )


        return (
            stream
        )


    def play(
        self,
        audio,
        sample_rate: int,
    ) -> bool:

        sample_rate = int(
            sample_rate
        )


        if sample_rate <= 0:

            return False


        array = (
            self._normalize_audio(
                audio
            )
        )


        if array is None:

            return False


        channels = int(
            array.shape[
                1
            ]
        )


        with self._stream_lock:

            if self._closed:

                return False


            self._stop_requested.clear()

            self._pause_requested.clear()


            stream = (
                self._ensure_stream_locked(
                    sample_rate=
                        sample_rate,

                    channels=
                        channels,
                )
            )


        block_frames = max(
            1,
            int(
                round(
                    sample_rate
                    * (
                        self.write_block_ms
                        / 1000.0
                    )
                )
            ),
        )


        self._speaking.set()


        try:

            start = 0

            total = int(
                array.shape[
                    0
                ]
            )


            while start < total:

                if (
                    self._stop_requested.is_set()
                ):

                    return False


                while (
                    self._pause_requested.is_set()
                    and not self._stop_requested.is_set()
                ):

                    time.sleep(
                        0.01
                    )


                if (
                    self._stop_requested.is_set()
                ):

                    return False


                end = min(
                    total,
                    start
                    + block_frames,
                )


                block = (
                    array[
                        start:end
                    ]
                )


                try:

                    stream.write(
                        block
                    )


                except Exception:

                    if (
                        self._stop_requested.is_set()
                    ):

                        return False


                    raise


                start = (
                    end
                )


            return True


        finally:

            self._speaking.clear()

            self._pause_requested.clear()


    def pause_current(
        self,
    ):

        if self._speaking.is_set():

            self._pause_requested.set()


    def resume_current(
        self,
    ):

        self._pause_requested.clear()


    def stop_current(
        self,
    ):

        self._stop_requested.set()

        self._pause_requested.clear()


        with self._stream_lock:

            stream = (
                self._stream
            )

            self._stream = None

            self._sample_rate = None

            self._channels = None


        if stream is None:

            return


        try:

            stream.abort()

        except Exception:

            pass


        try:

            stream.close()

        except Exception:

            pass


    def close(
        self,
    ):

        self._stop_requested.set()

        self._pause_requested.clear()


        with self._stream_lock:

            if self._closed:

                return


            self._closed = (
                True
            )


            self._close_stream_locked()


PLAYER = (
    PersistentAudioPlayer()
)
