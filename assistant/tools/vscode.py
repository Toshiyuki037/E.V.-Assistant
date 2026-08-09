"""
E.V.I.E. - Visual Studio Code Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides controlled VS Code project actions.

Current Tools:
    - open_workspace_in_vscode
    - open_file_in_vscode

Security:
    File operations remain restricted to the selected workspace.
"""

import os
import shutil
import subprocess
from pathlib import Path

from .filesystem import (
    get_active_workspace_path,
    resolve_workspace_path,
)

from .registry import (
    register_tool,
)


# ---------------------------------------------------------------------------
# VS Code Detection
# ---------------------------------------------------------------------------

def find_vscode():
    command = shutil.which(
        "code"
    )

    if command:

        return command

    local_appdata = (
        os.environ.get(
            "LOCALAPPDATA",
            ""
        )
    )

    candidate = (
        Path(
            local_appdata
        )
        / "Programs"
        / "Microsoft VS Code"
        / "Code.exe"
    )

    if candidate.exists():

        return str(
            candidate
        )

    raise FileNotFoundError(
        "Visual Studio Code executable could not be located."
    )


# ---------------------------------------------------------------------------
# Open Workspace
# ---------------------------------------------------------------------------

def open_workspace_in_vscode(
    workspace_path=None,
):
    if workspace_path:

        workspace = Path(
            workspace_path
        ).resolve()

    else:

        workspace = (
            get_active_workspace_path()
        )

    if not workspace.exists():

        raise FileNotFoundError(
            str(
                workspace
            )
        )

    executable = (
        find_vscode()
    )

    subprocess.Popen(
        [
            executable,
            str(
                workspace
            ),
        ],
        shell=False,
    )

    return {
        "workspace":
            str(
                workspace
            ),

        "opened":
            True,
    }


# ---------------------------------------------------------------------------
# Open File
# ---------------------------------------------------------------------------

def open_file_in_vscode(
    path: str,
    line: int | None = None,
    workspace_path=None,
):
    root, target = (
        resolve_workspace_path(
            path,
            workspace_path,
        )
    )

    if not target.exists():

        raise FileNotFoundError(
            str(
                target
            )
        )

    if not target.is_file():

        raise IsADirectoryError(
            str(
                target
            )
        )

    executable = (
        find_vscode()
    )

    if line is not None:

        line = int(
            line
        )

        if line < 1:

            raise ValueError(
                "Line number must be >= 1."
            )

        target_argument = (
            f"{target}:{line}"
        )

        command = [
            executable,
            "--goto",
            target_argument,
        ]

    else:

        command = [
            executable,
            str(
                target
            ),
        ]

    subprocess.Popen(
        command,
        cwd=str(
            root
        ),
        shell=False,
    )

    return {
        "workspace":
            str(root),

        "file":
            str(
                target.relative_to(
                    root
                )
            ),

        "line":
            line,

        "opened":
            True,
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name="open_workspace_in_vscode",
    description=(
        "Opens the selected workspace in "
        "Visual Studio Code."
    ),
    category="vscode",
    risk="low",
    function=open_workspace_in_vscode,
)


register_tool(
    name="open_file_in_vscode",
    description=(
        "Opens a workspace file in Visual "
        "Studio Code, optionally at a line."
    ),
    category="vscode",
    risk="low",
    function=open_file_in_vscode,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. VS Code Tools"
    )

    print(
        "-----------------------"
    )

    print(
        "VS Code:"
    )

    print(
        find_vscode()
    )

    print()

    print(
        "Active workspace:"
    )

    print(
        get_active_workspace_path()
    )