"""
E.V.I.E. - Integration Router

Provider-independent execution interface for Phase 9.

This module does not perform natural-language planning.

It resolves a requested provider/capability and invokes the registered
provider implementation.
"""

from __future__ import annotations

from .registry import (
    get_integration_capability,
)

from .results import (
    IntegrationResult,
)


def execute_integration(
    provider: str,
    capability: str,
    **arguments,
):
    registered = (
        get_integration_capability(
            provider,
            capability,
        )
    )


    if registered is None:

        return IntegrationResult(
            success=False,
            provider=provider,
            capability=capability,
            error=(
                "Integration capability "
                "is not registered."
            ),
        )


    try:

        result = registered.function(
            **arguments
        )


        return IntegrationResult(
            success=True,
            provider=provider,
            capability=capability,
            data=result,
        )


    except Exception as error:

        return IntegrationResult(
            success=False,
            provider=provider,
            capability=capability,
            error=str(
                error
            ),
        )