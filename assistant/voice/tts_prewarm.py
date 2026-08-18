from __future__ import annotations

import threading
import time


_LOCK = threading.RLock()

_THREAD = None

_FINISHED = False

_ERROR = ""


def _worker():
    global _FINISHED
    global _ERROR

    try:

        # Do not fight the semantic model prewarm for the GPU.
        try:
            from assistant.performance.prewarm import (
                wait_for_prewarm,
            )

            wait_for_prewarm(
                timeout=
                    30.0
            )

        except Exception:
            pass


        from assistant.speak import (
            synthesize_audio,
        )


        started = (
            time.monotonic()
        )


        # Silent first inference: warms F5 reference preprocessing and
        # inference kernels without playing anything.
        synthesize_audio(
            "Ready."
        )


        print(
            (
                "[Performance] TTS inference prewarmed in "
                f"{time.monotonic() - started:.2f}s."
            )
        )


    except Exception as error:

        _ERROR = str(
            error
        )

        print(
            (
                "[Performance] TTS prewarm warning: "
                f"{error}"
            )
        )


    finally:

        _FINISHED = (
            True
        )


def start_tts_prewarm():
    global _THREAD

    with _LOCK:

        if (
            _THREAD is not None
            and _THREAD.is_alive()
        ):
            return _THREAD


        if _FINISHED:
            return _THREAD


        _THREAD = (
            threading.Thread(
                target=
                    _worker,
                daemon=
                    True,
                name=
                    "evie-tts-prewarm",
            )
        )


        _THREAD.start()


        return _THREAD
