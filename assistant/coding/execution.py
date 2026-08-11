"""
E.V.I.E. - Coding Command Execution

Phase 12J

Purpose:
Run explicit validation commands within a coding transaction.

Security model:
- shell=False
- executable + args are passed as a list
- cwd is always the transaction repository root
- records stdout/stderr/return code
- does not accept arbitrary shell strings
"""

from __future__ import annotations

from datetime import datetime, timezone
import subprocess

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


def run_transaction_command(
    transaction_id: str,
    command: list[str],
    *,
    mark_as: str = "",
    timeout: int = 120,
):
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

    started = _now()

    result = subprocess.run(
        [
            str(
                part
            )
            for part
            in command
        ],
        cwd=transaction.root_path,
        capture_output=True,
        text=True,
        shell=False,
        timeout=timeout,
        check=False,
    )

    record = CommandRecord(
        command=" ".join(
            str(
                part
            )
            for part
            in command
        ),
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        started_at=started,
        completed_at=_now(),
    )

    transaction.commands.append(
        record
    )

    if mark_as == "targeted_tests":
        transaction.targeted_tests_passed = (
            result.returncode == 0
        )

    elif mark_as == "regression":
        transaction.regression_passed = (
            result.returncode == 0
        )

    transaction.status = (
        "validated"
        if result.returncode == 0
        else "validation_failed"
    )

    save_transaction(
        transaction
    )

    return record
