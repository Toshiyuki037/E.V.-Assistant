"""
E.V.I.E. - Knowledge File Scanner

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Discovers useful project files inside the currently active workspace.

How It Works:
    Uses Phase 3 workspace detection to identify the active project,
    recursively scans that project, ignores noisy/generated directories,
    and returns supported source/document files.

Most Recent Change:
    Initial Phase 4 repository file discovery system.
"""

from pathlib import Path

from ..perception.workspace import (
    get_workspace_context,
)


# ---------------------------------------------------------------------------
# Supported File Types
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {
    # Python
    ".py",

    # Web
    ".html",
    ".htm",
    ".css",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",

    # C / C++
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",

    # HDL
    ".v",
    ".vh",
    ".sv",
    ".svh",
    ".vhd",
    ".vhdl",

    # Data / configuration
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",

    # Documentation
    ".md",
    ".txt",

    # Shell / scripts
    ".ps1",
    ".sh",
    ".bat",
}


# ---------------------------------------------------------------------------
# Ignored Directories
# ---------------------------------------------------------------------------

IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",

    "venv",
    ".venv",
    "env",

    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",

    "node_modules",

    "dist",
    "build",
    "out",
    "target",

    ".cache",

    "coverage",
    ".coverage",

    "logs",
}


# ---------------------------------------------------------------------------
# Ignored Files
# ---------------------------------------------------------------------------

IGNORED_FILES = {
    ".DS_Store",
    "Thumbs.db",
}


# ---------------------------------------------------------------------------
# Safety Limits
# ---------------------------------------------------------------------------

MAX_FILE_SIZE_BYTES = 2_000_000
MAX_FILES = 5000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_hidden_path(
    path: Path,
) -> bool:
    """
    Treat dot-prefixed folders/files as hidden unless the file type
    is explicitly useful.
    """

    for part in path.parts:
        if (
            part.startswith(".")
            and part not in {
                ".env.example",
            }
        ):
            return True

    return False


def should_ignore_directory(
    directory: Path,
) -> bool:

    return (
        directory.name
        in IGNORED_DIRECTORIES
    )


def is_supported_file(
    path: Path,
) -> bool:

    if not path.is_file():
        return False

    if path.name in IGNORED_FILES:
        return False

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False

    try:
        size = path.stat().st_size
    except OSError:
        return False

    if size > MAX_FILE_SIZE_BYTES:
        return False

    return True


# ---------------------------------------------------------------------------
# Workspace Resolution
# ---------------------------------------------------------------------------

def get_active_workspace_path():
    """
    Uses Phase 3 dynamic workspace detection.
    """

    context = get_workspace_context()

    workspace_path = context.get(
        "workspace_path"
    )

    if not workspace_path:
        return None

    path = Path(
        workspace_path
    )

    if not path.exists():
        return None

    if not path.is_dir():
        return None

    return path


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_workspace(
    workspace_path: str | Path | None = None,
):
    """
    Recursively scans the active workspace for useful source
    and documentation files.
    """

    if workspace_path is None:
        root = get_active_workspace_path()
    else:
        root = Path(
            workspace_path
        ).resolve()

    if root is None:
        return []

    if not root.exists():
        return []

    discovered = []

    try:
        iterator = root.rglob("*")
    except OSError:
        return []

    for path in iterator:

        try:
            relative = path.relative_to(
                root
            )

        except ValueError:
            continue

        # ---------------------------------------------------------------
        # Ignore excluded directories anywhere in the path
        # ---------------------------------------------------------------

        if any(
            part in IGNORED_DIRECTORIES
            for part in relative.parts
        ):
            continue

        # ---------------------------------------------------------------
        # Avoid unrelated hidden content
        # ---------------------------------------------------------------

        if is_hidden_path(
            relative
        ):
            continue

        # ---------------------------------------------------------------
        # File checks
        # ---------------------------------------------------------------

        if not is_supported_file(
            path
        ):
            continue

        try:
            stat = path.stat()

        except (
            OSError,
            PermissionError,
        ):
            continue

        discovered.append(
            {
                "absolute_path":
                    str(path.resolve()),

                "relative_path":
                    relative.as_posix(),

                "filename":
                    path.name,

                "extension":
                    path.suffix.lower(),

                "size_bytes":
                    stat.st_size,

                "modified_time":
                    stat.st_mtime,
            }
        )

        if len(discovered) >= MAX_FILES:
            break

    discovered.sort(
        key=lambda item: (
            item["relative_path"].lower()
        )
    )

    return discovered


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def summarize_scan(
    files,
):
    extensions = {}

    for file in files:

        extension = (
            file["extension"]
            or "no_extension"
        )

        extensions[extension] = (
            extensions.get(
                extension,
                0,
            )
            + 1
        )

    return {
        "file_count":
            len(files),

        "extensions":
            dict(
                sorted(
                    extensions.items(),
                    key=lambda item:
                        item[0],
                )
            ),
    }


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    workspace = (
        get_active_workspace_path()
    )

    print(
        "E.V.I.E. Knowledge Scanner"
    )

    print(
        "---------------------------"
    )

    print(
        "Workspace:",
        workspace,
    )

    files = scan_workspace(
        workspace
    )

    summary = summarize_scan(
        files
    )

    print(
        "\nFiles discovered:",
        summary["file_count"],
    )

    print(
        "\nFile types:"
    )

    for extension, count in (
        summary["extensions"].items()
    ):
        print(
            f"- {extension}: {count}"
        )

    print(
        "\nFiles:"
    )

    for file in files:

        print(
            f"- {file['relative_path']}"
        )