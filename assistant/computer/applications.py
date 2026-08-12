"""
E.V.I.E. - Windows Application Discovery & Launch

Phase 13C

Application launching prefers deterministic executable resolution.
It does not use UI clicking.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

from .process_models import ApplicationLaunchResult


WINDOWS_APP_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
}


def _candidate_paths_for_common_apps(
    name: str,
) -> list[Path]:
    lowered = name.lower().strip()

    local = Path(
        os.environ.get(
            "LOCALAPPDATA",
            "",
        )
    )

    program_files = Path(
        os.environ.get(
            "ProgramFiles",
            "",
        )
    )

    candidates: list[Path] = []

    if lowered in {
        "code",
        "vscode",
        "visual studio code",
    }:
        candidates.extend(
            [
                local
                / "Programs"
                / "Microsoft VS Code"
                / "Code.exe",

                program_files
                / "Microsoft VS Code"
                / "Code.exe",
            ]
        )

    elif lowered in {
        "spotify",
    }:
        candidates.extend(
            [
                local
                / "Microsoft"
                / "WindowsApps"
                / "Spotify.exe",

                local
                / "Spotify"
                / "Spotify.exe",
            ]
        )

    elif lowered in {
        "chrome",
        "google chrome",
    }:
        candidates.extend(
            [
                program_files
                / "Google"
                / "Chrome"
                / "Application"
                / "chrome.exe",

                Path(
                    os.environ.get(
                        "ProgramFiles(x86)",
                        "",
                    )
                )
                / "Google"
                / "Chrome"
                / "Application"
                / "chrome.exe",
            ]
        )

    return [
        path
        for path in candidates
        if str(path)
    ]


def resolve_application(
    application: str,
) -> str:
    requested = str(
        application
        or ""
    ).strip()

    if not requested:
        raise ValueError(
            "Application name cannot be empty."
        )

    path = Path(requested)

    if path.is_file():
        return str(
            path.resolve()
        )

    alias = WINDOWS_APP_ALIASES.get(
        requested.lower()
    )

    if alias:
        resolved = shutil.which(alias)

        if resolved:
            return resolved

        return alias

    direct = shutil.which(requested)

    if direct:
        return direct

    for candidate in _candidate_paths_for_common_apps(
        requested
    ):
        if candidate.is_file():
            return str(candidate)

    raise FileNotFoundError(
        f"Could not resolve installed application: {application}"
    )


def launch_application(
    application: str,
    *,
    arguments: list[str] | None = None,
    cwd: str | None = None,
) -> ApplicationLaunchResult:
    executable = resolve_application(
        application
    )

    command = [
        executable,
        *[
            str(item)
            for item in (
                arguments
                or []
            )
        ],
    ]

    try:
        process = subprocess.Popen(
            command,
            cwd=cwd or None,
            shell=False,
            close_fds=True,
        )

    except OSError as error:
        return ApplicationLaunchResult(
            requested=application,
            executable=executable,
            pid=None,
            success=False,
            message=str(error),
        )

    return ApplicationLaunchResult(
        requested=application,
        executable=executable,
        pid=int(process.pid),
        success=True,
        message="Application launched.",
    )
