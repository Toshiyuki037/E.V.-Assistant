"""
E.V.I.E. - Knowledge File Reader

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Safely reads supported text/source files discovered by
    E.V.I.E.'s knowledge scanner.

How It Works:
    Ensures files remain inside the selected workspace, applies
    size limits, detects supported file types, and returns structured
    file content and metadata.

Most Recent Change:
    Initial Phase 4 safe local file-reading system.
"""

from pathlib import Path

from .scanner import (
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_EXTENSIONS,
    get_active_workspace_path,
    scan_workspace,
)


# ---------------------------------------------------------------------------
# Language / Type Mapping
# ---------------------------------------------------------------------------

FILE_TYPES = {
    ".py": "Python",

    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".js": "JavaScript",
    ".jsx": "JavaScript JSX",
    ".ts": "TypeScript",
    ".tsx": "TypeScript TSX",

    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",

    ".v": "Verilog",
    ".vh": "Verilog Header",
    ".sv": "SystemVerilog",
    ".svh": "SystemVerilog Header",
    ".vhd": "VHDL",
    ".vhdl": "VHDL",

    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Configuration",
    ".csv": "CSV",

    ".md": "Markdown",
    ".txt": "Text",

    ".ps1": "PowerShell",
    ".sh": "Shell",
    ".bat": "Windows Batch",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_file_type(
    path: Path,
):
    return FILE_TYPES.get(
        path.suffix.lower(),
        "Text",
    )


def is_path_inside_workspace(
    path: Path,
    workspace: Path,
):
    """
    Prevents the reader from following a requested path outside
    the current workspace.
    """

    try:

        path.resolve().relative_to(
            workspace.resolve()
        )

        return True

    except ValueError:
        return False


# ---------------------------------------------------------------------------
# File Reading
# ---------------------------------------------------------------------------

def read_file(
    file_path: str | Path,
    workspace_path: str | Path | None = None,
):
    """
    Reads one supported text/source file.

    Returns a dictionary on success or failure.
    """

    if workspace_path is None:

        workspace = (
            get_active_workspace_path()
        )

    else:

        workspace = Path(
            workspace_path
        ).resolve()

    if workspace is None:

        return {
            "success": False,
            "error":
                "No active workspace detected.",
        }

    path = Path(
        file_path
    )

    # Relative requests are resolved against workspace.
    if not path.is_absolute():

        path = (
            workspace
            / path
        )

    try:
        path = path.resolve()

    except OSError:

        return {
            "success": False,
            "error":
                "Unable to resolve file path.",
        }

    # ---------------------------------------------------------------
    # Workspace boundary
    # ---------------------------------------------------------------

    if not is_path_inside_workspace(
        path,
        workspace,
    ):

        return {
            "success": False,
            "error":
                "File is outside the active workspace.",
        }

    # ---------------------------------------------------------------
    # Existence
    # ---------------------------------------------------------------

    if not path.exists():

        return {
            "success": False,
            "error":
                "File does not exist.",
        }

    if not path.is_file():

        return {
            "success": False,
            "error":
                "Path is not a file.",
        }

    # ---------------------------------------------------------------
    # Type
    # ---------------------------------------------------------------

    extension = (
        path.suffix.lower()
    )

    if (
        extension
        not in SUPPORTED_EXTENSIONS
    ):

        return {
            "success": False,
            "error":
                (
                    "Unsupported file type: "
                    f"{extension or 'none'}"
                ),
        }

    # ---------------------------------------------------------------
    # Size
    # ---------------------------------------------------------------

    try:
        size = (
            path.stat().st_size
        )

    except OSError:

        return {
            "success": False,
            "error":
                "Unable to inspect file.",
        }

    if size > MAX_FILE_SIZE_BYTES:

        return {
            "success": False,
            "error":
                (
                    "File exceeds the "
                    "configured size limit."
                ),
        }

    # ---------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------

    try:

        content = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    except (
        OSError,
        PermissionError,
    ) as error:

        return {
            "success": False,
            "error": str(error),
        }

    # ---------------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------------

    try:

        relative_path = (
            path.relative_to(
                workspace
            )
            .as_posix()
        )

    except ValueError:

        relative_path = (
            path.name
        )

    line_count = (
        len(
            content.splitlines()
        )
    )

    return {
        "success": True,

        "absolute_path":
            str(path),

        "relative_path":
            relative_path,

        "filename":
            path.name,

        "extension":
            extension,

        "file_type":
            get_file_type(
                path
            ),

        "size_bytes":
            size,

        "character_count":
            len(content),

        "line_count":
            line_count,

        "content":
            content,
    }


# ---------------------------------------------------------------------------
# Read By Relative Path
# ---------------------------------------------------------------------------

def read_workspace_file(
    relative_path: str,
):
    return read_file(
        relative_path
    )


# ---------------------------------------------------------------------------
# Find File
# ---------------------------------------------------------------------------

def find_file(
    filename: str,
):
    """
    Finds files with an exact filename in the current workspace.
    """

    files = scan_workspace()

    target = (
        filename.lower()
    )

    return [
        file
        for file in files
        if (
            file["filename"].lower()
            == target
        )
    ]


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Knowledge Reader"
    )

    print(
        "--------------------------"
    )

    workspace = (
        get_active_workspace_path()
    )

    print(
        "Workspace:",
        workspace,
    )

    if workspace is None:

        raise SystemExit(
            "No workspace detected."
        )

    # ---------------------------------------------------------------
    # Prefer brain.py as the first test when present.
    # ---------------------------------------------------------------

    matches = find_file(
        "brain.py"
    )

    if matches:

        selected = (
            matches[0][
                "relative_path"
            ]
        )

    else:

        files = scan_workspace()

        if not files:

            raise SystemExit(
                "No readable files discovered."
            )

        selected = (
            files[0][
                "relative_path"
            ]
        )

    print(
        "\nReading:",
        selected,
    )

    result = read_file(
        selected,
        workspace,
    )

    if not result[
        "success"
    ]:

        print(
            "\nRead failed:"
        )

        print(
            result["error"]
        )

        raise SystemExit(1)

    print(
        "\nStatus: OK"
    )

    print(
        "Type:",
        result["file_type"],
    )

    print(
        "Lines:",
        result["line_count"],
    )

    print(
        "Characters:",
        result[
            "character_count"
        ],
    )

    print(
        "Size:",
        result["size_bytes"],
        "bytes",
    )

    print(
        "\nPreview:"
    )

    print(
        "--------------------------"
    )

    preview_lines = (
        result["content"]
        .splitlines()[:30]
    )

    print(
        "\n".join(
            preview_lines
        )
    )