"""
E.V.I.E. - Coding Transaction Persistence

Phase 12I
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    CodingTransaction,
    FileSnapshot,
    CommandRecord,
    transaction_to_dict,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

TRANSACTION_RUNTIME = (
    PROJECT_ROOT
    / "runtime"
    / "coding"
    / "transactions"
)


def _safe(
    value: str,
):
    return (
        str(
            value
            or ""
        )
        .replace(
            "/",
            "_",
        )
        .replace(
            "\\",
            "_",
        )
        .replace(
            ":",
            "_",
        )
    )


def transaction_path(
    transaction_id: str,
):
    return (
        TRANSACTION_RUNTIME
        / (
            _safe(
                transaction_id
            )
            + ".json"
        )
    )


def save_transaction(
    transaction: CodingTransaction,
):
    TRANSACTION_RUNTIME.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = transaction_path(
        transaction.transaction_id
    )

    temp = path.with_suffix(
        ".json.tmp"
    )

    temp.write_text(
        json.dumps(
            transaction_to_dict(
                transaction
            ),
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temp.replace(
        path
    )

    return transaction


def load_transaction(
    transaction_id: str,
):
    path = transaction_path(
        transaction_id
    )

    if not path.exists():
        return None

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    snapshots = {
        key:
            FileSnapshot(
                **value
            )
        for key, value
        in (
            data.get(
                "snapshots",
                {}
            )
            or {}
        ).items()
    }

    commands = [
        CommandRecord(
            **item
        )
        for item
        in (
            data.get(
                "commands",
                []
            )
            or []
        )
    ]

    data[
        "snapshots"
    ] = snapshots

    data[
        "commands"
    ] = commands

    return CodingTransaction(
        **data
    )
