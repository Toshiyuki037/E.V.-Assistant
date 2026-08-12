"""
E.V.I.E. - Read-Only Filesystem Search

Phase 13 Final

Purpose:
    Safely locates files and directories outside the active workspace.

Important:
    Uses actual Windows known-folder locations when available, including
    redirected OneDrive Desktop/Documents folders.

Security:
    - read-only
    - bounded traversal
    - bounded results
    - default roots remain inside the user's profile
"""

from __future__ import annotations

import os
from pathlib import Path
import winreg

from .registry import register_tool


# ---------------------------------------------------------------------------
# Windows Known Folders
# ---------------------------------------------------------------------------

def _windows_user_shell_folders():
    """
    Reads the real Windows shell-folder mappings.

    This correctly handles redirected locations such as:

        C:\\Users\\name\\OneDrive\\Desktop

    instead of assuming:

        C:\\Users\\name\\Desktop
    """

    folders = {}

    if os.name != "nt":
        return folders

    try:

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            (
                r"Software\Microsoft\Windows"
                r"\CurrentVersion\Explorer\User Shell Folders"
            ),
        )

    except OSError:

        return folders


    aliases = {
        "desktop":
            "Desktop",

        "documents":
            "Personal",

        "downloads":
            "{374DE290-123F-4565-9164-39C4925E467B}",

        "pictures":
            "My Pictures",

        "music":
            "My Music",

        "videos":
            "My Video",
    }


    for alias, registry_name in aliases.items():

        try:

            value, _ = winreg.QueryValueEx(
                key,
                registry_name,
            )

        except OSError:

            continue


        expanded = os.path.expandvars(
            str(value)
        )


        path = Path(
            expanded
        ).expanduser()


        folders[
            alias
        ] = path.resolve(
            strict=False
        )


    winreg.CloseKey(
        key
    )


    return folders


# ---------------------------------------------------------------------------
# Known Root Construction
# ---------------------------------------------------------------------------

def get_known_search_roots():
    """
    Returns the actual useful user search roots.
    """

    home = Path.home().resolve(
        strict=False
    )


    roots = {
        "home":
            home,

        "desktop":
            home / "Desktop",

        "documents":
            home / "Documents",

        "downloads":
            home / "Downloads",

        "pictures":
            home / "Pictures",

        "music":
            home / "Music",

        "videos":
            home / "Videos",
    }


    # -----------------------------------------------------------------------
    # Replace assumptions with actual Windows shell locations.
    # -----------------------------------------------------------------------

    roots.update(
        _windows_user_shell_folders()
    )


    # -----------------------------------------------------------------------
    # Add OneDrive explicitly when present.
    # -----------------------------------------------------------------------

    one_drive = os.environ.get(
        "OneDrive"
    )


    if one_drive:

        one_drive_path = Path(
            one_drive
        ).resolve(
            strict=False
        )


        roots[
            "onedrive"
        ] = one_drive_path


        one_drive_desktop = (
            one_drive_path
            / "Desktop"
        )


        if one_drive_desktop.exists():

            roots[
                "onedrive_desktop"
            ] = one_drive_desktop


        one_drive_documents = (
            one_drive_path
            / "Documents"
        )


        if one_drive_documents.exists():

            roots[
                "onedrive_documents"
            ] = one_drive_documents


    return roots


# ---------------------------------------------------------------------------
# Traversal Policy
# ---------------------------------------------------------------------------

SKIP_DIRECTORIES = {
    ".git",
    ".svn",
    ".hg",

    ".venv",
    "venv",

    "__pycache__",

    "node_modules",

    "AppData",

    ".cache",
    ".npm",
    ".cargo",
    ".rustup",

    "$RECYCLE.BIN",
    "System Volume Information",
}


# ---------------------------------------------------------------------------
# Root Resolution
# ---------------------------------------------------------------------------

def _resolve_roots(
    roots,
    *,
    allow_test_roots: bool = False,
):
    known = get_known_search_roots()


    if not roots:

        # Search the most likely user locations first.

        roots = [
            "desktop",
            "onedrive_desktop",
            "documents",
            "onedrive_documents",
            "downloads",
            "onedrive",
            "home",
        ]


    resolved = []


    for root in roots:

        root_text = str(
            root
        ).strip()


        alias = root_text.lower()


        if alias in known:

            path = known[
                alias
            ]

        else:

            path = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        root_text
                    )
                )
            ).resolve(
                strict=False
            )


            if not allow_test_roots:

                home = Path.home().resolve(
                    strict=False
                )


                try:

                    path.relative_to(
                        home
                    )

                except ValueError:

                    raise PermissionError(
                        (
                            "Filesystem search root must remain "
                            "inside the user's home directory: "
                            f"{path}"
                        )
                    )


        if not path.exists():

            continue


        if not path.is_dir():

            continue


        if path in resolved:

            continue


        resolved.append(
            path
        )


    return resolved


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_filesystem(
    query: str,
    roots=None,
    *,
    kind: str = "any",
    max_results: int = 25,
    max_depth: int = 8,
    _allow_test_roots: bool = False,
):
    """
    Searches user folders for matching files/directories.

    Matching is case-insensitive and substring-based.
    """

    query_text = str(
        query
        or ""
    ).strip()


    if not query_text:

        raise ValueError(
            "Filesystem search query cannot be empty."
        )


    kind = str(
        kind
        or "any"
    ).strip().lower()


    if kind not in {
        "any",
        "file",
        "directory",
    }:

        raise ValueError(
            (
                "kind must be one of: "
                "any, file, directory"
            )
        )


    max_results = max(
        1,
        min(
            int(
                max_results
            ),
            100,
        ),
    )


    max_depth = max(
        0,
        min(
            int(
                max_depth
            ),
            16,
        ),
    )


    search_roots = _resolve_roots(
        roots,
        allow_test_roots=
            _allow_test_roots,
    )


    needle = query_text.casefold()


    matches = []


    visited_paths = set()


    for root in search_roots:

        root = root.resolve(
            strict=False
        )


        root_parts = len(
            root.parts
        )


        for (
            current_root,
            directory_names,
            file_names,
        ) in os.walk(
            root
        ):

            current = Path(
                current_root
            )


            canonical_current = str(
                current.resolve(
                    strict=False
                )
            ).casefold()


            # ---------------------------------------------------------------
            # Avoid searching duplicate trees through overlapping roots.
            # ---------------------------------------------------------------

            if canonical_current in visited_paths:

                directory_names[:] = []

                continue


            visited_paths.add(
                canonical_current
            )


            depth = (
                len(
                    current.parts
                )
                - root_parts
            )


            if depth >= max_depth:

                directory_names[:] = []

            else:

                directory_names[:] = [
                    name
                    for name
                    in directory_names
                    if (
                        name
                        not in SKIP_DIRECTORIES

                        and not name.startswith(
                            "."
                        )
                    )
                ]


            # ---------------------------------------------------------------
            # Directory Matches
            # ---------------------------------------------------------------

            if kind in {
                "any",
                "directory",
            }:

                for name in directory_names:

                    if needle not in name.casefold():

                        continue


                    path = (
                        current
                        / name
                    ).resolve(
                        strict=False
                    )


                    matches.append(
                        {
                            "name":
                                name,

                            "path":
                                str(
                                    path
                                ),

                            "kind":
                                "directory",

                            "root":
                                str(
                                    root
                                ),
                        }
                    )


                    if len(matches) >= max_results:

                        return {
                            "query":
                                query_text,

                            "kind":
                                kind,

                            "roots":
                                [
                                    str(item)
                                    for item
                                    in search_roots
                                ],

                            "matches":
                                matches,

                            "count":
                                len(
                                    matches
                                ),

                            "truncated":
                                True,
                        }


            # ---------------------------------------------------------------
            # File Matches
            # ---------------------------------------------------------------

            if kind in {
                "any",
                "file",
            }:

                for name in file_names:

                    if needle not in name.casefold():

                        continue


                    path = (
                        current
                        / name
                    ).resolve(
                        strict=False
                    )


                    matches.append(
                        {
                            "name":
                                name,

                            "path":
                                str(
                                    path
                                ),

                            "kind":
                                "file",

                            "root":
                                str(
                                    root
                                ),
                        }
                    )


                    if len(matches) >= max_results:

                        return {
                            "query":
                                query_text,

                            "kind":
                                kind,

                            "roots":
                                [
                                    str(item)
                                    for item
                                    in search_roots
                                ],

                            "matches":
                                matches,

                            "count":
                                len(
                                    matches
                                ),

                            "truncated":
                                True,
                        }


    return {
        "query":
            query_text,

        "kind":
            kind,

        "roots":
            [
                str(item)
                for item
                in search_roots
            ],

        "matches":
            matches,

        "count":
            len(
                matches
            ),

        "truncated":
            False,
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name=
        "search_filesystem",

    description=(
        "Read-only filesystem discovery tool. "
        "Searches actual Windows user folders, including redirected "
        "OneDrive Desktop/Documents locations, for files or directories "
        "by name and returns real absolute paths. "
        "Use this whenever a requested project/workspace/file location "
        "is unknown. Prefer this over run_python, PowerShell, os.walk, "
        "path guessing, or repeated list_directory calls."
    ),

    category=
        "filesystem",

    risk=
        "low",

    function=
        search_filesystem,
)