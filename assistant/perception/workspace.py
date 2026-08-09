"""
E.V.I.E. - Dynamic Workspace Awareness

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Determines which development project is currently active.

Capabilities:
    - Active VS Code workspace detection
    - Dynamic project folder resolution
    - Git repository detection
    - Git branch
    - Modified/untracked files

Most Recent Change:
    Replaced the fixed E.V.I.E. workspace with dynamic project detection.
"""

import os
import subprocess
from pathlib import Path

from .system import (
    get_active_window_title,
)


# ---------------------------------------------------------------------------
# Default Project Root
# ---------------------------------------------------------------------------

EVIE_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)


# ---------------------------------------------------------------------------
# Read-Only Command Helper
# ---------------------------------------------------------------------------

def run_command(
    command: list[str],
    cwd: Path | None = None,
):
    try:
        result = subprocess.run(
            command,
            cwd=(
                str(cwd)
                if cwd
                else None
            ),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            return None

        # IMPORTANT:
        # Keep leading Git status spaces.
        output = result.stdout.rstrip()

        return (
            output
            if output
            else None
        )

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        OSError,
    ):
        return None


# ---------------------------------------------------------------------------
# Workspace Name From Window
# ---------------------------------------------------------------------------

def infer_workspace_name(
    window_title: str | None,
):
    """
    VS Code commonly formats titles roughly as:

    brain.py - eve-assistant - Visual Studio Code
    """

    if not window_title:
        return None

    if (
        "Visual Studio Code"
        not in window_title
    ):
        return None

    parts = [
        part.strip()
        for part in window_title.split(
            " - "
        )
    ]

    # Remove VS Code suffix.
    parts = [
        part
        for part in parts
        if (
            "Visual Studio Code"
            not in part
        )
    ]

    if not parts:
        return None

    # When a file and workspace both exist:
    # brain.py - eve-assistant
    if len(parts) >= 2:
        return parts[-1]

    return parts[0]


# ---------------------------------------------------------------------------
# Likely Development Roots
# ---------------------------------------------------------------------------

def get_search_roots():
    home = Path.home()

    roots = [
        home / "Desktop",
        home / "Documents",
        home / "Projects",
        home / "Repos",
        home / "source" / "repos",
    ]

    onedrive = os.environ.get(
        "OneDrive"
    )

    if onedrive:
        one = Path(onedrive)

        roots.extend(
            [
                one / "Desktop",
                one / "Documents",
                one,
            ]
        )

    unique = []

    seen = set()

    for root in roots:
        try:
            resolved = (
                root.resolve()
            )
        except OSError:
            continue

        key = str(
            resolved
        ).lower()

        if key in seen:
            continue

        seen.add(key)

        if resolved.exists():
            unique.append(
                resolved
            )

    return unique


# ---------------------------------------------------------------------------
# Resolve Workspace Folder
# ---------------------------------------------------------------------------

def find_workspace_folder(
    workspace_name: str | None,
):
    if not workspace_name:
        return EVIE_ROOT

    # E.V.I.E. itself is an easy exact match.
    if (
        EVIE_ROOT.name.lower()
        == workspace_name.lower()
    ):
        return EVIE_ROOT

    for root in get_search_roots():

        # Root itself could be workspace.
        if (
            root.name.lower()
            == workspace_name.lower()
        ):
            return root

        # Keep search shallow intentionally.
        try:
            children = list(
                root.iterdir()
            )
        except (
            PermissionError,
            OSError,
        ):
            continue

        for child in children:
            if not child.is_dir():
                continue

            if (
                child.name.lower()
                == workspace_name.lower()
            ):
                return child

    return None


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def get_git_root(
    path: Path,
):
    output = run_command(
        [
            "git",
            "rev-parse",
            "--show-toplevel",
        ],
        cwd=path,
    )

    return output


def get_git_branch(
    path: Path,
):
    return run_command(
        [
            "git",
            "branch",
            "--show-current",
        ],
        cwd=path,
    )


def get_git_status(
    path: Path,
):
    output = run_command(
        [
            "git",
            "status",
            "--short",
        ],
        cwd=path,
    )

    if not output:
        return []

    return output.splitlines()


def get_modified_files(
    path: Path,
):
    status_lines = get_git_status(
        path
    )

    files = []

    for line in status_lines:

        # Git porcelain format:
        # XY<space>filename
        if len(line) < 4:
            continue

        file_path = line[
            3:
        ].strip()

        if file_path:
            files.append(
                file_path
            )

    return files


# ---------------------------------------------------------------------------
# Dynamic Workspace Context
# ---------------------------------------------------------------------------

def get_workspace_context():
    active_window = (
        get_active_window_title()
    )

    workspace_hint = (
        infer_workspace_name(
            active_window
        )
    )

    detected_folder = (
        find_workspace_folder(
            workspace_hint
        )
    )

    if detected_folder is None:
        detected_folder = EVIE_ROOT

    git_root_string = (
        get_git_root(
            detected_folder
        )
    )

    if git_root_string:
        repository = Path(
            git_root_string
        )
    else:
        repository = (
            detected_folder
        )

    git_branch = (
        get_git_branch(
            repository
        )
        if git_root_string
        else None
    )

    modified_files = (
        get_modified_files(
            repository
        )
        if git_root_string
        else []
    )

    return {
        "workspace_hint":
            workspace_hint,

        "workspace_name":
            detected_folder.name,

        "workspace_path":
            str(
                detected_folder
            ),

        "git_repository":
            (
                str(repository)
                if git_root_string
                else None
            ),

        "git_branch":
            git_branch,

        "modified_files":
            modified_files,

        "detection_source":
            (
                "active_window"
                if workspace_hint
                else "fallback"
            ),
    }


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    context = (
        get_workspace_context()
    )

    print(
        "E.V.I.E. Workspace Context"
    )

    print(
        "---------------------------"
    )

    for key, value in context.items():
        print(
            f"{key}: {value}"
        )