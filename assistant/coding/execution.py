"""
E.V.I.E. - Coding Command Execution

Phase 12J / Phase 12N

Purpose:
Run explicit validation commands within a coding transaction.

Security model:

- shell=False
- executable + args are passed as a list
- cwd is always the transaction repository root
- records stdout/stderr/return code
- does not accept arbitrary shell strings
- Python commands are pinned to the interpreter currently running E.V.I.E.
"""

from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import subprocess
import sys

from .models import (
    CommandRecord,
)

from .state import (
    load_transaction,
    save_transaction,
)


def _now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def _normalize_command(
    command,
):
    """
    Convert a validated command sequence into a subprocess-safe list.

    Important:
    If the command starts with "python" or "python.exe", replace that
    executable with sys.executable.

    This ensures validation runs inside the same Python environment that
    is currently running E.V.I.E., rather than accidentally resolving to
    another Python installation through Windows PATH.
    """

    normalized = [
        str(
            part
        )
        for part
        in command
    ]

    if not normalized:
        return normalized

    executable = (
        normalized[
            0
        ]
        .strip()
        .lower()
    )

    if executable in {
        "python",
        "python.exe",
    }:
        normalized[
            0
        ] = sys.executable

    return normalized


def run_transaction_command(
    transaction_id: str,
    command: list[str],
    *,
    mark_as: str = "",
    timeout: int = 120,
):
    """
    Run one controlled command inside a coding transaction.

    The command must already be represented as a list of executable
    arguments. No shell parsing is performed.

    Example:

        [
            "python",
            "-m",
            "pytest",
            "-q",
        ]

    becomes:

        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ]

    before subprocess execution.
    """

    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            (
                "Coding transaction does not exist: "
                f"{transaction_id}"
            )
        )

    if not command:
        raise ValueError(
            "Command list cannot be empty."
        )


    # -----------------------------------------------------------------------
    # Normalize executable
    # -----------------------------------------------------------------------

    normalized_command = (
        _normalize_command(
            command
        )
    )


    if not normalized_command:
        raise ValueError(
            "Normalized command list cannot be empty."
        )


    # -----------------------------------------------------------------------
    # Start command record
    # -----------------------------------------------------------------------

    started = _now()


    # -----------------------------------------------------------------------
    # Controlled process execution
    # -----------------------------------------------------------------------

    try:

        result = subprocess.run(
            normalized_command,
            cwd=
                transaction.root_path,
            capture_output=
                True,
            text=
                True,
            shell=
                False,
            timeout=
                timeout,
            check=
                False,
        )


        returncode = (
            result.returncode
        )

        stdout = (
            result.stdout
            or ""
        )

        stderr = (
            result.stderr
            or ""
        )


    except subprocess.TimeoutExpired as error:

        returncode = 124

        stdout = (
            error.stdout
            or ""
        )

        stderr = (
            error.stderr
            or ""
        )


        if isinstance(
            stdout,
            bytes,
        ):
            stdout = stdout.decode(
                errors="replace"
            )


        if isinstance(
            stderr,
            bytes,
        ):
            stderr = stderr.decode(
                errors="replace"
            )


        timeout_message = (
            f"Command timed out after {timeout} seconds."
        )


        if stderr:

            stderr = (
                f"{stderr}\n"
                f"{timeout_message}"
            )

        else:

            stderr = (
                timeout_message
            )


    except OSError as error:

        returncode = 127

        stdout = ""

        stderr = (
            f"{type(error).__name__}: {error}"
        )


    # -----------------------------------------------------------------------
    # Persist command record
    # -----------------------------------------------------------------------

    record = CommandRecord(
        command=
            " ".join(
                normalized_command
            ),

        returncode=
            returncode,

        stdout=
            stdout,

        stderr=
            stderr,

        started_at=
            started,

        completed_at=
            _now(),
    )


    transaction.commands.append(
        record
    )


    # -----------------------------------------------------------------------
    # Update validation state
    # -----------------------------------------------------------------------

    if (
        mark_as
        == "targeted_tests"
    ):

        transaction.targeted_tests_passed = (
            returncode
            == 0
        )


    elif (
        mark_as
        == "regression"
    ):

        transaction.regression_passed = (
            returncode
            == 0
        )


    # -----------------------------------------------------------------------
    # Transaction status
    # -----------------------------------------------------------------------

    transaction.status = (
        "validated"
        if returncode
        == 0
        else "validation_failed"
    )


    if returncode == 0:

        transaction.error = ""

    else:

        transaction.error = (
            stderr
            or stdout
            or (
                "Command failed with return code "
                f"{returncode}."
            )
        )


    # -----------------------------------------------------------------------
    # Persist state
    # -----------------------------------------------------------------------

    save_transaction(
        transaction
    )


    return record