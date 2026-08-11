"""
E.V.I.E. - Integration Account Selection

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Stores temporary account-selection state when a Phase 9 action can
    execute against more than one connected account.

Important:
    This state is NOT long-term memory.
    It is NOT an account preference.
    It exists only long enough for the user to select an account.
"""

from __future__ import annotations

import json

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from pathlib import Path

from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


RUNTIME_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
)


SELECTION_FILE = (
    RUNTIME_DIRECTORY
    / "pending_selection.json"
)


# ---------------------------------------------------------------------------
# Pending Selection Model
# ---------------------------------------------------------------------------

@dataclass
class PendingIntegrationSelection:
    tool_name: str

    capability: str

    arguments: dict[str, Any]

    routed_accounts: list[
        dict[str, Any]
    ] = field(
        default_factory=list
    )

    summary: str = ""

    original_request: str = ""


# ---------------------------------------------------------------------------
# Runtime Directory
# ---------------------------------------------------------------------------

def ensure_runtime_directory():
    RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


# ---------------------------------------------------------------------------
# Save Pending Selection
# ---------------------------------------------------------------------------

def set_pending_integration_selection(
    tool_name: str,
    capability: str,
    arguments: dict,
    routed_accounts,
    summary: str = "",
    original_request: str = "",
):
    ensure_runtime_directory()


    accounts = []


    for routed in routed_accounts:

        accounts.append(
            {
                "provider":
                    routed.provider,

                "account_id":
                    routed.account_id,

                "display_name":
                    routed.display_name,

                "email":
                    routed.email,

                "capability":
                    routed.capability,
            }
        )


    pending = PendingIntegrationSelection(
        tool_name=
            tool_name,

        capability=
            capability,

        arguments=
            dict(arguments),

        routed_accounts=
            accounts,

        summary=
            summary,

        original_request=
            original_request,
    )


    SELECTION_FILE.write_text(
        json.dumps(
            asdict(pending),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


    return pending


# ---------------------------------------------------------------------------
# Load Pending Selection
# ---------------------------------------------------------------------------

def get_pending_integration_selection():
    if not SELECTION_FILE.exists():

        return None


    try:

        payload = json.loads(
            SELECTION_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


    if not isinstance(
        payload,
        dict,
    ):

        return None


    return PendingIntegrationSelection(
        tool_name=str(
            payload.get(
                "tool_name",
                "",
            )
        ),

        capability=str(
            payload.get(
                "capability",
                "",
            )
        ),

        arguments=dict(
            payload.get(
                "arguments",
                {},
            )
            or {}
        ),

        routed_accounts=list(
            payload.get(
                "routed_accounts",
                [],
            )
            or []
        ),

        summary=str(
            payload.get(
                "summary",
                "",
            )
        ),

        original_request=str(
            payload.get(
                "original_request",
                "",
            )
        ),
    )


# ---------------------------------------------------------------------------
# Has Pending Selection
# ---------------------------------------------------------------------------

def has_pending_integration_selection():
    return (
        get_pending_integration_selection()
        is not None
    )


# ---------------------------------------------------------------------------
# Clear Pending Selection
# ---------------------------------------------------------------------------

def clear_pending_integration_selection():
    pending = (
        get_pending_integration_selection()
    )


    if SELECTION_FILE.exists():

        try:

            SELECTION_FILE.unlink()

        except OSError:

            pass


    return pending


# ---------------------------------------------------------------------------
# Resolve Account Selection
# ---------------------------------------------------------------------------

def resolve_account_selection(
    pending: PendingIntegrationSelection,
    user_message: str,
):
    """
    Supports:

        1
        2
        personal
        school
        gmail
        osu
        email address
        account id
        display name
    """

    text = (
        str(user_message)
        .strip()
        .lower()
    )


    if not text:

        return None


    accounts = (
        pending.routed_accounts
    )


    # -----------------------------------------------------------------------
    # Numeric Selection
    # -----------------------------------------------------------------------

    if text.isdigit():

        index = (
            int(text)
            - 1
        )


        if (
            0
            <= index
            < len(accounts)
        ):

            return accounts[
                index
            ]


    # -----------------------------------------------------------------------
    # Personal
    # ---------------------------------------------------------------------------

    personal_phrases = {
        "personal",
        "personal account",
        "gmail",
        "personal gmail",
        "my personal account",
        "my gmail",
    }


    if text in personal_phrases:

        for account in accounts:

            email = (
                str(
                    account.get(
                        "email",
                        "",
                    )
                )
                .strip()
                .lower()
            )


            if email.endswith(
                "@gmail.com"
            ):

                return account


    # -----------------------------------------------------------------------
    # School / OSU
    # ---------------------------------------------------------------------------

    school_phrases = {
        "school",
        "school account",
        "my school account",
        "osu",
        "oregon state",
        "oregonstate",
        "oregon state account",
    }


    if text in school_phrases:

        for account in accounts:

            email = (
                str(
                    account.get(
                        "email",
                        "",
                    )
                )
                .strip()
                .lower()
            )


            if (
                "oregonstate.edu"
                in email
            ):

                return account


    # -----------------------------------------------------------------------
    # Exact / Contained Identity
    # ---------------------------------------------------------------------------

    for account in accounts:

        candidates = [
            str(
                account.get(
                    "account_id",
                    "",
                )
            ),

            str(
                account.get(
                    "email",
                    "",
                )
            ),

            str(
                account.get(
                    "display_name",
                    "",
                )
            ),
        ]


        for candidate in candidates:

            normalized = (
                candidate
                .strip()
                .lower()
            )


            if not normalized:

                continue


            if (
                text
                == normalized
            ):

                return account


            if (
                normalized
                in text
            ):

                return account


    return None


# ---------------------------------------------------------------------------
# Format Account Choices
# ---------------------------------------------------------------------------

def format_account_choices(
    pending: PendingIntegrationSelection,
):
    lines = []


    for index, account in enumerate(
        pending.routed_accounts,
        start=1,
    ):

        display_name = (
            account.get(
                "display_name"
            )
            or account.get(
                "account_id"
            )
            or "Account"
        )


        email = (
            account.get(
                "email"
            )
            or account.get(
                "account_id"
            )
            or ""
        )


        if email:

            label = (
                f"{index}. "
                f"{display_name} — "
                f"{email}"
            )

        else:

            label = (
                f"{index}. "
                f"{display_name}"
            )


        lines.append(
            label
        )


    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Integration Account Selection"
    )

    print(
        "--------------------------------------"
    )


    print(
        "Selection state file:"
    )

    print(
        SELECTION_FILE
    )