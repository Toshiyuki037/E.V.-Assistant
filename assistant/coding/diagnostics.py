"""
E.V.I.E. - Coding Failure Diagnostics

Phase 12K

Purpose:
Normalize compile/test failures into a compact diagnostic record that can
be consumed by bounded repair planning.

This module is deterministic and model-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re


@dataclass
class FailureDiagnostic:
    command: str
    returncode: int
    summary: str
    error_type: str = ""
    file_paths: list[str] = field(default_factory=list)
    line_numbers: list[int] = field(default_factory=list)
    raw_stdout: str = ""
    raw_stderr: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


TRACEBACK_FILE_RE = re.compile(
    r'File "([^"]+)", line (\d+)'
)

PYTEST_FILE_RE = re.compile(
    r'([A-Za-z0-9_./\\-]+\.py):(\d+):'
)


def diagnose_command_failure(
    record,
):
    stdout = (
        getattr(
            record,
            "stdout",
            "",
        )
        or ""
    )

    stderr = (
        getattr(
            record,
            "stderr",
            "",
        )
        or ""
    )

    combined = (
        stdout
        + "\n"
        + stderr
    ).strip()

    lowered = combined.lower()

    if "syntaxerror" in lowered:
        error_type = "syntax_error"
    elif "importerror" in lowered:
        error_type = "import_error"
    elif "modulenotfounderror" in lowered:
        error_type = "module_not_found"
    elif "assertionerror" in lowered or "failed" in lowered:
        error_type = "test_failure"
    elif "timeout" in lowered:
        error_type = "timeout"
    else:
        error_type = "command_failure"

    paths = []
    lines = []

    for match in TRACEBACK_FILE_RE.finditer(
        combined
    ):
        path = match.group(
            1
        )

        line = int(
            match.group(
                2
            )
        )

        if path not in paths:
            paths.append(
                path
            )

        lines.append(
            line
        )

    for match in PYTEST_FILE_RE.finditer(
        combined
    ):
        path = match.group(
            1
        )

        line = int(
            match.group(
                2
            )
        )

        if path not in paths:
            paths.append(
                path
            )

        lines.append(
            line
        )

    summary = (
        combined[
            :2000
        ]
        if combined
        else (
            f"Command exited with "
            f"{getattr(record, 'returncode', -1)}."
        )
    )

    return FailureDiagnostic(
        command=
            getattr(
                record,
                "command",
                "",
            ),

        returncode=
            int(
                getattr(
                    record,
                    "returncode",
                    -1,
                )
                or 0
            ),

        summary=
            summary,

        error_type=
            error_type,

        file_paths=
            paths,

        line_numbers=
            lines,

        raw_stdout=
            stdout,

        raw_stderr=
            stderr,
    )
