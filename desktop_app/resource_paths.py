"""
E.V.I.E. packaged/source runtime path helpers.

This module keeps packaging behavior in the desktop layer. It does not modify
the certified assistant backend.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


APP_NAME = "E.V.I.E."


def is_frozen() -> bool:
    return bool(
        getattr(
            sys,
            "frozen",
            False,
        )
    )


def resource_root() -> Path:
    """
    Root containing bundled read-only resources.

    Source run:
        eve-assistant\

    PyInstaller onedir run:
        E.V.I.E\_internal\
    """

    if is_frozen():
        return Path(
            sys._MEIPASS
        ).resolve()

    return (
        Path(__file__)
        .resolve()
        .parents[1]
    )


def application_dir() -> Path:
    """
    Directory containing EVIE.exe in a frozen build.

    The installer is deliberately per-user, so this location is writable and
    can safely contain the app's runtime directory.
    """

    if is_frozen():
        return (
            Path(sys.executable)
            .resolve()
            .parent
        )

    return resource_root()


def resource_path(
    *parts: str,
) -> Path:
    return (
        resource_root()
        .joinpath(
            *parts
        )
    )


def runtime_path(
    *parts: str,
) -> Path:
    root = (
        application_dir()
        / "runtime"
    )

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return root.joinpath(
        *parts
    )


def prepare_runtime_environment():
    """
    Establish a deterministic working directory for code in the existing
    backend that intentionally uses relative runtime paths.

    In development this remains the project root.
    In the installed build this is the per-user application directory.
    """

    target = application_dir()

    try:
        os.chdir(
            target
        )
    except OSError:
        pass

    for relative in (
        ("runtime",),
        ("runtime", "telemetry"),
        ("runtime", "voice_cache"),
    ):
        try:
            target.joinpath(
                *relative
            ).mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError:
            pass
