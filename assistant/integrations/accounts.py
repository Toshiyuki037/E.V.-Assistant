"""
E.V.I.E. - Integration Accounts

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Represents connected external accounts independently of provider.

Phase:
    Phase 9B - Accounts, Authentication & Connection State
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import Any


# ---------------------------------------------------------------------------
# Integration Account
# ---------------------------------------------------------------------------

@dataclass
class IntegrationAccount:
    account_id: str

    provider: str

    display_name: str = ""

    email: str = ""

    connected: bool = False

    authenticated: bool = False

    scopes: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def account_to_dict(
    account: IntegrationAccount,
):
    return asdict(
        account
    )


def account_from_dict(
    data: dict,
):
    return IntegrationAccount(
        account_id=str(
            data.get(
                "account_id",
                "",
            )
        ),

        provider=str(
            data.get(
                "provider",
                "",
            )
        ),

        display_name=str(
            data.get(
                "display_name",
                "",
            )
        ),

        email=str(
            data.get(
                "email",
                "",
            )
        ),

        connected=bool(
            data.get(
                "connected",
                False,
            )
        ),

        authenticated=bool(
            data.get(
                "authenticated",
                False,
            )
        ),

        scopes=list(
            data.get(
                "scopes",
                [],
            )
        ),

        metadata=dict(
            data.get(
                "metadata",
                {},
            )
        ),
    )