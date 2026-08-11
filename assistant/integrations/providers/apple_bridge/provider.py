"""
E.V.I.E. - Apple Bridge Provider Registration

Created: August 10, 2026
Author: Max Maehara

Phase:
    Phase 9H
"""

from __future__ import annotations

from assistant.integrations.registry import (
    register_integration_capability,
)

from .client import (
    apple_bridge_health,
)


# ---------------------------------------------------------------------------
# Health Capability
# ---------------------------------------------------------------------------

def apple_bridge_status(
    account_id: str | None = None,
):
    """
    Returns bridge health information.

    account_id is accepted for compatibility with Phase 9 account
    routing but is not required by the local bridge itself.
    """

    return apple_bridge_health()


# ---------------------------------------------------------------------------
# Provider Registration
# ---------------------------------------------------------------------------

def load_apple_bridge_provider():

    register_integration_capability(
        provider=
            "apple_bridge",

        name=
            "device.bridge_status",

        function=
            apple_bridge_status,

        risk=
            "low",

        sensitivity=
            "personal",

        description=(
            "Checks whether E.V.I.E.'s trusted Apple bridge is available."
        ),
    )