"""
E.V.I.E. - Visual Studio Code Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides controlled Visual Studio Code project actions.

Current Tools:
    - open_workspace_in_vscode
    - open_file_in_vscode

Capabilities:
    - open workspace
    - open workspace in a new VS Code window
    - open workspace file
    - open workspace file at a specific line
    - open workspace file in a new VS Code window

Security:
    File operations remain restricted to the selected workspace.

    open_file_in_vscode() resolves files through the existing
    workspace-scoped filesystem layer.

Most Recent Change:
    Added explicit new-window support for Phase 7 agentic tasks.
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
    """
    Locates Visual Studio Code.

    Prefers the `code` command available on PATH and falls back
    to the normal per-user Windows installation path.
    """

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
        (
            "Visual Studio Code executable "
            "could not be located."
        )
    )


# ---------------------------------------------------------------------------
# Resolve Workspace
# ---------------------------------------------------------------------------

def resolve_vscode_workspace(
    workspace_path=None,
):
    """
    Resolves the workspace used for a VS Code action.
    """

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


    if not workspace.is_dir():

        raise NotADirectoryError(
            str(
                workspace
            )
        )


    return workspace


# ---------------------------------------------------------------------------
# Launch VS Code Command
# ---------------------------------------------------------------------------

def launch_vscode(
    command: list[str],
    cwd=None,
):
    """
    Starts VS Code without shell=True.

    Returns the spawned process ID when available.
    """

    process = subprocess.Popen(
        command,
        cwd=(
            str(cwd)
            if cwd is not None
            else None
        ),
        shell=False,
    )


    return {
        "pid":
            process.pid,

        "command":
            command,
    }


# ---------------------------------------------------------------------------
# Open Workspace
# ---------------------------------------------------------------------------

def open_workspace_in_vscode(
    workspace_path=None,
    new_window: bool = False,
):
    """
    Opens a workspace in Visual Studio Code.

    Args:
        workspace_path:
            Workspace directory to open.

        new_window:
            When True, explicitly requests a new VS Code window.
    """

    workspace = (
        resolve_vscode_workspace(
            workspace_path
        )
    )


    executable = (
        find_vscode()
    )


    command = [
        executable,
    ]


    if new_window:

        command.append(
            "--new-window"
        )


    command.append(
        str(
            workspace
        )
    )


    launch_result = (
        launch_vscode(
            command,
            cwd=workspace,
        )
    )


    return {
        "workspace":
            str(
                workspace
            ),

        "opened":
            True,

        "new_window":
            bool(
                new_window
            ),

        "pid":
            launch_result[
                "pid"
            ],

        "command":
            launch_result[
                "command"
            ],
    }


# ---------------------------------------------------------------------------
# Open File
# ---------------------------------------------------------------------------

def open_file_in_vscode(
    path: str,
    line: int | None = None,
    workspace_path=None,
    new_window: bool = False,
):
    """
    Opens a workspace file in Visual Studio Code.

    Args:
        path:
            File path relative to the selected workspace.

        line:
            Optional 1-based source-code line number.

        workspace_path:
            Workspace containing the requested file.

        new_window:
            When True, explicitly requests a new VS Code window.

    Security:
        The target file must remain inside the selected workspace.
    """

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


    command = [
        executable,
    ]


    # -----------------------------------------------------------------------
    # New Window
    # -----------------------------------------------------------------------

    if new_window:

        command.append(
            "--new-window"
        )


    # -----------------------------------------------------------------------
    # Optional Line Navigation
    # -----------------------------------------------------------------------

    if line is not None:

        line = int(
            line
        )


        if line < 1:

            raise ValueError(
                (
                    "Line number must "
                    "be >= 1."
                )
            )


        target_argument = (
            f"{target}:{line}"
        )


        command.extend(
            [
                "--goto",
                target_argument,
            ]
        )

    else:

        command.append(
            str(
                target
            )
        )


    launch_result = (
        launch_vscode(
            command,
            cwd=root,
        )
    )


    return {
        "workspace":
            str(
                root
            ),

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

        "new_window":
            bool(
                new_window
            ),

        "pid":
            launch_result[
                "pid"
            ],

        "command":
            launch_result[
                "command"
            ],
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name=
        "open_workspace_in_vscode",

    description=(
        "Opens the selected workspace in Visual Studio Code. "
        "Set new_window=True when the user explicitly requests "
        "a separate or new VS Code window."
    ),

    category=
        "vscode",

    risk=
        "low",

    function=
        open_workspace_in_vscode,
)


register_tool(
    name=
        "open_file_in_vscode",

    description=(
        "Opens a workspace file in Visual Studio Code, optionally "
        "at a source-code line. Set new_window=True when the user "
        "explicitly requests a separate or new VS Code window."
    ),

    category=
        "vscode",

    risk=
        "low",

    function=
        open_file_in_vscode,
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


    print()

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


    print()

    print(
        "Tool signatures:"
    )

    import inspect


    print(
        "open_workspace_in_vscode",
        inspect.signature(
            open_workspace_in_vscode
        ),
    )


    print(
        "open_file_in_vscode",
        inspect.signature(
            open_file_in_vscode
        ),
    )