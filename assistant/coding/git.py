"""
E.V.I.E. - Safe Git Read Helpers

Phase 12I

Read-only Git inspection used to establish repository baselines.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run_git(
    root_path: str,
    arguments: list[str],
):
    result = subprocess.run(
        [
            "git",
            *arguments,
        ],
        cwd=str(
            Path(
                root_path
            ).resolve()
        ),
        capture_output=True,
        text=True,
        check=False,
    )

    return result


def current_branch(
    root_path: str,
):
    result = _run_git(
        root_path,
        [
            "branch",
            "--show-current",
        ],
    )

    if result.returncode != 0:
        return ""

    return (
        result.stdout
        .strip()
    )


def current_commit(
    root_path: str,
):
    result = _run_git(
        root_path,
        [
            "rev-parse",
            "HEAD",
        ],
    )

    if result.returncode != 0:
        return ""

    return (
        result.stdout
        .strip()
    )


def working_tree_status(
    root_path: str,
):
    result = _run_git(
        root_path,
        [
            "status",
            "--porcelain",
        ],
    )

    if result.returncode != 0:
        return []

    return [
        line
        for line
        in result.stdout.splitlines()
        if line.strip()
    ]


def diff_text(
    root_path: str,
):
    result = _run_git(
        root_path,
        [
            "diff",
            "--",
        ],
    )

    return (
        result.stdout
        if result.returncode == 0
        else ""
    )
