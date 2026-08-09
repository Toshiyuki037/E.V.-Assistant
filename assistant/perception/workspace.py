"""
E.V.I.E. - Multi-Workspace Awareness

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Detects the active development workspace and other visible
    VS Code workspaces.

How It Works:
    - Reads the foreground window.
    - Enumerates visible VS Code windows.
    - Extracts workspace names from VS Code titles.
    - Resolves workspace names to local project folders.
    - Retrieves Git branch and modified-file state.
    - Marks which workspace is currently active.

Most Recent Change:
    Added multi-workspace detection for final Phase 4 project routing.
"""

import os
import subprocess
from pathlib import Path

from .system import (
    get_active_window_title,
    get_visible_applications,
)


# ---------------------------------------------------------------------------
# E.V.I.E. Root
# ---------------------------------------------------------------------------

EVIE_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)


# ---------------------------------------------------------------------------
# Command Helper
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

        # Preserve leading Git porcelain spaces.
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
# VS Code Workspace Name
# ---------------------------------------------------------------------------

def infer_workspace_name(
    window_title: str | None,
):
    """
    Typical VS Code titles:

    brain.py - eve-assistant - Visual Studio Code

    index.html - FinalCollegePortfolio - Visual Studio Code
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
        if part.strip()
    ]

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

    if len(parts) >= 2:
        return parts[-1]

    return parts[0]


# ---------------------------------------------------------------------------
# Search Roots
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

        one = Path(
            onedrive
        )

        roots.extend(
            [
                one,
                one / "Desktop",
                one / "Documents",
            ]
        )

    unique = []

    seen = set()

    for root in roots:

        try:
            resolved = root.resolve()

        except OSError:
            continue

        key = str(
            resolved
        ).lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        if resolved.exists():
            unique.append(
                resolved
            )

    return unique


# ---------------------------------------------------------------------------
# Workspace Folder Resolution
# ---------------------------------------------------------------------------

def find_workspace_folder(
    workspace_name: str | None,
):
    if not workspace_name:
        return None

    if (
        EVIE_ROOT.name.lower()
        == workspace_name.lower()
    ):
        return EVIE_ROOT

    # First try direct children.
    for root in get_search_roots():

        if (
            root.name.lower()
            == workspace_name.lower()
        ):
            return root

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

    # Slightly deeper fallback.
    for root in get_search_roots():

        try:
            for child in root.glob(
                "*/*"
            ):

                if not child.is_dir():
                    continue

                if (
                    child.name.lower()
                    == workspace_name.lower()
                ):
                    return child

        except (
            PermissionError,
            OSError,
        ):
            continue

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
    files = []

    for line in get_git_status(
        path
    ):

        if len(line) < 4:
            continue

        file_path = (
            line[3:].strip()
        )

        if file_path:
            files.append(
                file_path
            )

    return files


# ---------------------------------------------------------------------------
# Build Workspace Record
# ---------------------------------------------------------------------------

def build_workspace_record(
    workspace_name: str,
    window_title: str | None = None,
    active: bool = False,
):
    folder = find_workspace_folder(
        workspace_name
    )

    if folder is None:

        return {
            "workspace_name":
                workspace_name,

            "workspace_path":
                None,

            "window_title":
                window_title,

            "git_repository":
                None,

            "git_branch":
                None,

            "modified_files":
                [],

            "active":
                active,

            "resolved":
                False,
        }

    git_root_string = get_git_root(
        folder
    )

    if git_root_string:

        repository = Path(
            git_root_string
        )

    else:

        repository = folder

    branch = (
        get_git_branch(
            repository
        )
        if git_root_string
        else None
    )

    modified = (
        get_modified_files(
            repository
        )
        if git_root_string
        else []
    )

    return {
        "workspace_name":
            folder.name,

        "workspace_path":
            str(folder),

        "window_title":
            window_title,

        "git_repository":
            (
                str(repository)
                if git_root_string
                else None
            ),

        "git_branch":
            branch,

        "modified_files":
            modified,

        "active":
            active,

        "resolved":
            True,
    }


# ---------------------------------------------------------------------------
# All Open VS Code Workspaces
# ---------------------------------------------------------------------------

def get_open_workspaces():
    """
    Returns every visible VS Code workspace that can be inferred
    from the current Windows desktop.
    """

    applications = (
        get_visible_applications()
    )

    active_title = (
        get_active_window_title()
    )

    detected = []

    seen_names = set()

    for app in applications:

        process_name = (
            app.get(
                "process",
                ""
            )
            .lower()
        )

        title = (
            app.get(
                "title"
            )
            or ""
        )

        if (
            process_name != "code.exe"
            and "Visual Studio Code"
            not in title
        ):
            continue

        workspace_name = (
            infer_workspace_name(
                title
            )
        )

        if not workspace_name:
            continue

        normalized = (
            workspace_name.lower()
        )

        if normalized in seen_names:
            continue

        seen_names.add(
            normalized
        )

        is_active = (
            active_title == title
        )

        detected.append(
            build_workspace_record(
                workspace_name=
                    workspace_name,

                window_title=
                    title,

                active=
                    is_active,
            )
        )

    # Active VS Code title may occasionally not appear in enumeration.
    active_name = infer_workspace_name(
        active_title
    )

    if (
        active_name
        and active_name.lower()
        not in seen_names
    ):

        detected.append(
            build_workspace_record(
                workspace_name=
                    active_name,

                window_title=
                    active_title,

                active=True,
            )
        )

    detected.sort(
        key=lambda item: (
            not item[
                "active"
            ],

            item[
                "workspace_name"
            ].lower(),
        )
    )

    return detected


# ---------------------------------------------------------------------------
# Active Workspace
# ---------------------------------------------------------------------------

def get_active_workspace():
    workspaces = (
        get_open_workspaces()
    )

    for workspace in workspaces:

        if workspace.get(
            "active"
        ):
            return workspace

    # Fallback for when VS Code isn't foreground.
    active_title = (
        get_active_window_title()
    )

    workspace_name = (
        infer_workspace_name(
            active_title
        )
    )

    if workspace_name:

        return build_workspace_record(
            workspace_name=
                workspace_name,

            window_title=
                active_title,

            active=True,
        )

    # Final fallback to E.V.I.E.
    return build_workspace_record(
        workspace_name=
            EVIE_ROOT.name,

        window_title=
            None,

        active=False,
    )


# ---------------------------------------------------------------------------
# Compatibility Function
# ---------------------------------------------------------------------------

def get_workspace_context():
    """
    Maintains compatibility with the existing Phase 3 system.

    Returns active workspace plus all detected open workspaces.
    """

    active = (
        get_active_workspace()
    )

    open_workspaces = (
        get_open_workspaces()
    )

    return {
        "workspace_hint":
            active.get(
                "workspace_name"
            ),

        "workspace_name":
            active.get(
                "workspace_name"
            ),

        "workspace_path":
            active.get(
                "workspace_path"
            ),

        "git_repository":
            active.get(
                "git_repository"
            ),

        "git_branch":
            active.get(
                "git_branch"
            ),

        "modified_files":
            active.get(
                "modified_files",
                [],
            ),

        "detection_source":
            "active_window",

        "open_workspaces":
            open_workspaces,
    }


# ---------------------------------------------------------------------------
# Find Workspace By Name
# ---------------------------------------------------------------------------

def find_open_workspace(
    requested_name: str,
):
    requested = (
        requested_name.lower()
    )

    workspaces = (
        get_open_workspaces()
    )

    # Exact match.
    for workspace in workspaces:

        if (
            workspace[
                "workspace_name"
            ].lower()
            == requested
        ):
            return workspace

    # Partial match.
    for workspace in workspaces:

        name = (
            workspace[
                "workspace_name"
            ].lower()
        )

        if (
            requested in name
            or name in requested
        ):
            return workspace

    return None


# ---------------------------------------------------------------------------
# Other Workspace
# ---------------------------------------------------------------------------

def get_other_workspace():
    """
    If exactly one obvious non-active workspace exists, return it.
    """

    workspaces = (
        get_open_workspaces()
    )

    others = [
        workspace

        for workspace
        in workspaces

        if (
            not workspace.get(
                "active"
            )
        )
    ]

    if not others:
        return None

    return others[0]


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Multi-Workspace Context"
    )

    print(
        "-------------------------------"
    )

    workspaces = (
        get_open_workspaces()
    )

    print(
        "Detected workspaces:",
        len(workspaces),
    )

    for workspace in workspaces:

        print()

        print(
            "Workspace:",
            workspace[
                "workspace_name"
            ]
        )

        print(
            "Path:",
            workspace[
                "workspace_path"
            ]
        )

        print(
            "Active:",
            workspace[
                "active"
            ]
        )

        print(
            "Branch:",
            workspace[
                "git_branch"
            ]
        )

        print(
            "Window:",
            workspace[
                "window_title"
            ]
        )