"""
E.V.I.E. - Project Intelligence

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Produces structured high-level information about a selected
    development project.

How It Works:
    Can summarize either:
        - the current active workspace
        - an explicitly selected workspace

Most Recent Change:
    Added explicit workspace support for multi-project Phase 4 routing.
"""

from pathlib import Path

from .scanner import (
    get_active_workspace_path,
    scan_workspace,
    summarize_scan,
)


# ---------------------------------------------------------------------------
# Entry Point Detection
# ---------------------------------------------------------------------------

LIKELY_ENTRY_POINTS = {
    "main.py",
    "app.py",
    "server.py",

    "index.py",
    "index.js",
    "index.ts",

    "index.html",

    "package.json",
    "README.md",
}


def find_entry_points(
    files,
):

    results = []

    for file in files:

        if (
            file["filename"]
            in LIKELY_ENTRY_POINTS
        ):

            results.append(
                file[
                    "relative_path"
                ]
            )

    return results


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def get_project_overview(
    workspace_path=None,
):

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
                "No workspace detected.",
        }

    if not workspace.exists():

        return {
            "success": False,
            "error":
                "Workspace path does not exist.",
        }

    files = scan_workspace(
        workspace
    )

    summary = summarize_scan(
        files
    )

    directories = sorted(
        {
            file[
                "relative_path"
            ].split("/")[0]

            for file in files

            if "/" in file[
                "relative_path"
            ]
        }
    )

    return {
        "success":
            True,

        "workspace_name":
            workspace.name,

        "workspace_path":
            str(workspace),

        "file_count":
            summary[
                "file_count"
            ],

        "file_types":
            summary[
                "extensions"
            ],

        "top_level_directories":
            directories,

        "likely_entry_points":
            find_entry_points(
                files
            ),
    }


# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------

def format_project_overview(
    overview,
):

    if not overview.get(
        "success"
    ):

        return (
            "Project overview unavailable."
        )

    directories = (
        ", ".join(
            overview[
                "top_level_directories"
            ]
        )

        or "None"
    )

    entry_points = (
        "\n".join(
            f"- {path}"

            for path in overview[
                "likely_entry_points"
            ]
        )

        or "None detected"
    )

    return f"""
PROJECT KNOWLEDGE

Project:
{overview['workspace_name']}

Path:
{overview['workspace_path']}

Readable files:
{overview['file_count']}

Top-level source directories:
{directories}

Likely entry points:
{entry_points}
""".strip()


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        format_project_overview(
            get_project_overview()
        )
    )