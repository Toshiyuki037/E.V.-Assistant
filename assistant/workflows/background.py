"""
E.V.I.E. - Workflow Background Runtime

Phase 11F

Purpose:
Run the persistent scheduler in a lightweight background loop.

Usage:
    python -m assistant.workflows.background

This is intentionally a simple process loop for V1.
A later always-on/server phase can move this service to systemd,
Windows Services, Docker, or another process supervisor.
"""

from __future__ import annotations

import argparse
import signal
import time

from .scheduler import (
    scheduler_tick,
)


_running = True


def _stop(
    *_,
):
    global _running
    _running = False


def run_background_scheduler(
    poll_seconds: int = 30,
    verbose: bool = True,
):
    global _running

    _running = True


    signal.signal(
        signal.SIGINT,
        _stop,
    )


    if hasattr(
        signal,
        "SIGTERM",
    ):

        signal.signal(
            signal.SIGTERM,
            _stop,
        )


    if verbose:

        print(
            "E.V.I.E. workflow scheduler online."
        )

        print(
            (
                "Polling every "
                f"{poll_seconds} second(s)."
            )
        )


    while _running:

        results = (
            scheduler_tick()
        )


        if (
            verbose
            and results
        ):

            for result in results:

                print(
                    (
                        "[Workflow Scheduler] "
                        f"{result}"
                    )
                )


        slept = 0


        while (
            _running
            and slept
            < poll_seconds
        ):

            time.sleep(
                1
            )

            slept += 1


    if verbose:

        print(
            "E.V.I.E. workflow scheduler stopped."
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--poll",
        type=int,
        default=30,
        help=(
            "Scheduler polling interval "
            "in seconds."
        ),
    )

    arguments = (
        parser.parse_args()
    )


    run_background_scheduler(
        poll_seconds=max(
            1,
            arguments.poll,
        )
    )


if __name__ == "__main__":

    main()
