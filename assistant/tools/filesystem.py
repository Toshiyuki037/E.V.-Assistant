"""
E.V.I.E. - Filesystem Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides workspace-scoped filesystem access.

Security:
    Relative paths are resolved inside the selected workspace.

    Tools refuse to escape outside the workspace unless future
    permission policies explicitly allow broader access.

Current Tools:
    - list_directory
    - read_file
    - create_file
    - write_file

Most Recent Change:
    Initial Phase 6 controlled filesystem tools.
"""

from pathlib import Path

from .registry import (
    register_tool,
)

from ..perception.workspace import (
    get_workspace_context,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_READ_CHARACTERS = (
    100_000
)


# ---------------------------------------------------------------------------
# Workspace Resolution
# ---------------------------------------------------------------------------

def get_active_workspace_path():
    """
    Retrieves the currently selected development workspace.
    """

    context = (
        get_workspace_context()
    )

    workspace_path = (
        context.get(
            "workspace_path"
        )
    )

    if not workspace_path:

        raise RuntimeError(
            "No active workspace could be resolved."
        )

    return Path(
        workspace_path
    ).resolve()


# ---------------------------------------------------------------------------
# Safe Path Resolution
# ---------------------------------------------------------------------------

def resolve_workspace_path(
    relative_path: str = ".",
    workspace_path=None,
):
    """
    Resolves a path while preventing directory traversal outside
    the selected workspace.
    """

    if workspace_path:

        root = Path(
            workspace_path
        ).resolve()

    else:

        root = (
            get_active_workspace_path()
        )

    requested = Path(
        relative_path
        or "."
    )

    if requested.is_absolute():

        candidate = (
            requested.resolve()
        )

    else:

        candidate = (
            root
            / requested
        ).resolve()

    try:

        candidate.relative_to(
            root
        )

    except ValueError:

        raise PermissionError(
            (
                "Filesystem access outside "
                "the workspace is blocked."
            )
        )

    return (
        root,
        candidate,
    )


# ---------------------------------------------------------------------------
# List Directory
# ---------------------------------------------------------------------------

def list_directory(
    path: str = ".",
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
            f"Directory does not exist: {target}"
        )

    if not target.is_dir():

        raise NotADirectoryError(
            str(target)
        )

    entries = []

    for item in sorted(
        target.iterdir(),
        key=lambda item:
            (
                not item.is_dir(),
                item.name.lower(),
            ),
    ):

        entries.append(
            {
                "name":
                    item.name,

                "type":
                    (
                        "directory"
                        if item.is_dir()
                        else "file"
                    ),

                "relative_path":
                    str(
                        item.relative_to(
                            root
                        )
                    ),

                "size":
                    (
                        item.stat().st_size
                        if item.is_file()
                        else None
                    ),
            }
        )

    return {
        "workspace":
            str(root),

        "directory":
            str(
                target.relative_to(
                    root
                )
            ),

        "entries":
            entries,
    }


# ---------------------------------------------------------------------------
# Read File
# ---------------------------------------------------------------------------

def read_file(
    path: str,
    workspace_path=None,
    max_characters:
        int = MAX_READ_CHARACTERS,
):
    root, target = (
        resolve_workspace_path(
            path,
            workspace_path,
        )
    )

    if not target.exists():

        raise FileNotFoundError(
            f"File does not exist: {target}"
        )

    if not target.is_file():

        raise IsADirectoryError(
            str(target)
        )

    content = target.read_text(
        encoding="utf-8",
        errors="replace",
    )

    truncated = (
        len(content)
        > max_characters
    )

    if truncated:

        content = content[
            :max_characters
        ]

    return {
        "workspace":
            str(root),

        "path":
            str(
                target.relative_to(
                    root
                )
            ),

        "characters":
            len(content),

        "truncated":
            truncated,

        "content":
            content,
    }


# ---------------------------------------------------------------------------
# Create File
# ---------------------------------------------------------------------------

def create_file(
    path: str,
    content: str = "",
    workspace_path=None,
):
    root, target = (
        resolve_workspace_path(
            path,
            workspace_path,
        )
    )

    if target.exists():

        raise FileExistsError(
            (
                "Refusing to overwrite "
                f"existing file: {target}"
            )
        )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        content,
        encoding="utf-8",
    )

    return {
        "workspace":
            str(root),

        "path":
            str(
                target.relative_to(
                    root
                )
            ),

        "created":
            True,

        "characters":
            len(content),
    }


# ---------------------------------------------------------------------------
# Write Existing File
# ---------------------------------------------------------------------------

def write_file(
    path: str,
    content: str,
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
            (
                "write_file only modifies "
                "existing files. Use "
                "create_file for new files."
            )
        )

    if not target.is_file():

        raise IsADirectoryError(
            str(target)
        )

    original = target.read_text(
        encoding="utf-8",
        errors="replace",
    )

    target.write_text(
        content,
        encoding="utf-8",
    )

    return {
        "workspace":
            str(root),

        "path":
            str(
                target.relative_to(
                    root
                )
            ),

        "written":
            True,

        "previous_characters":
            len(original),

        "new_characters":
            len(content),
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name="list_directory",
    description=(
        "Lists files and directories inside "
        "the active workspace."
    ),
    category="filesystem",
    risk="low",
    function=list_directory,
)


register_tool(
    name="read_file",
    description=(
        "Reads a UTF-8 text file inside "
        "the active workspace."
    ),
    category="filesystem",
    risk="low",
    function=read_file,
)


register_tool(
    name="create_file",
    description=(
        "Creates a new file inside the "
        "active workspace."
    ),
    category="filesystem",
    risk="medium",
    function=create_file,
)


register_tool(
    name="write_file",
    description=(
        "Replaces the contents of an existing "
        "file inside the active workspace."
    ),
    category="filesystem",
    risk="medium",
    function=write_file,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Filesystem Tools"
    )

    print(
        "--------------------------"
    )

    print()

    print(
        "Active workspace:"
    )

    print(
        get_active_workspace_path()
    )

    print()

    result = list_directory(
        "."
    )

    print(
        "Entries:"
    )

    for entry in result[
        "entries"
    ][
        :20
    ]:

        print(
            (
                f"- {entry['type']}: "
                f"{entry['relative_path']}"
            )
        )