"""
E.V.I.E. - Integration Registry

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Central registry for Phase 9 personal-service integrations.

Architecture:
    Providers register normalized capabilities here.

    The rest of E.V.I.E. requests capabilities rather than directly
    importing Gmail, Outlook, Spotify, Apple, Schwab, or other provider
    implementations.

Important:
    Registering a provider does NOT authenticate or connect to an
    external service.

    Provider definitions, account connections, OAuth, credentials,
    and runtime connection state remain separate concerns.

Capabilities:
    - provider capability registration
    - capability lookup
    - capability enumeration
    - provider enumeration
    - provider-specific capability listing
    - duplicate-safe registration
    - default provider-definition loading
    - development registry reset
    - reliable standalone diagnostic mode
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import (
    Any,
    Callable,
)


# ---------------------------------------------------------------------------
# Integration Capability
# ---------------------------------------------------------------------------

@dataclass
class IntegrationCapability:
    """
    Represents one provider capability exposed to Phase 9.

    Example:

        provider:
            google

        name:
            calendar.read
    """

    provider: str

    name: str

    function: Callable[..., Any]

    risk: str

    sensitivity: str

    description: str = ""


# ---------------------------------------------------------------------------
# Registry State
# ---------------------------------------------------------------------------

_CAPABILITIES: dict[
    tuple[str, str],
    IntegrationCapability,
] = {}


_DEFAULTS_LOADED = False


# ---------------------------------------------------------------------------
# Normalize Names
# ---------------------------------------------------------------------------

def normalize_name(
    value: str,
):
    """
    Normalizes provider and capability identifiers.
    """

    return (
        str(
            value
        )
        .strip()
        .lower()
    )


# ---------------------------------------------------------------------------
# Register Capability
# ---------------------------------------------------------------------------

def register_integration_capability(
    provider: str,
    name: str,
    function,
    risk: str,
    sensitivity: str,
    description: str = "",
):
    """
    Registers one provider capability.

    Registration is duplicate-safe.

    Registering the same provider/capability pair again replaces the
    previous definition, which is useful during development and
    provider reloads.
    """

    provider = normalize_name(
        provider
    )

    name = normalize_name(
        name
    )

    risk = normalize_name(
        risk
    )

    sensitivity = normalize_name(
        sensitivity
    )


    if not provider:

        raise ValueError(
            "Integration provider cannot be empty."
        )


    if not name:

        raise ValueError(
            "Integration capability name cannot be empty."
        )


    if not callable(
        function
    ):

        raise TypeError(
            (
                "Integration capability "
                "function must be callable."
            )
        )


    key = (
        provider,
        name,
    )


    capability = IntegrationCapability(
        provider=provider,
        name=name,
        function=function,
        risk=risk,
        sensitivity=sensitivity,
        description=(
            str(
                description
            )
            .strip()
        ),
    )


    _CAPABILITIES[
        key
    ] = capability


    return capability


# ---------------------------------------------------------------------------
# Get Capability
# ---------------------------------------------------------------------------

def get_integration_capability(
    provider: str,
    name: str,
):
    """
    Returns one registered provider capability.

    Returns None when the provider/capability pair is not registered.
    """

    provider = normalize_name(
        provider
    )

    name = normalize_name(
        name
    )


    return _CAPABILITIES.get(
        (
            provider,
            name,
        )
    )


# ---------------------------------------------------------------------------
# Capability Exists
# ---------------------------------------------------------------------------

def has_integration_capability(
    provider: str,
    name: str,
):
    """
    Returns whether the requested provider capability is registered.
    """

    return (
        get_integration_capability(
            provider,
            name,
        )
        is not None
    )


# ---------------------------------------------------------------------------
# List Capabilities
# ---------------------------------------------------------------------------

def list_integration_capabilities():
    """
    Returns all currently registered integration capabilities.
    """

    return sorted(
        _CAPABILITIES.values(),
        key=lambda item: (
            item.provider,
            item.name,
        ),
    )


# ---------------------------------------------------------------------------
# List Providers
# ---------------------------------------------------------------------------

def list_integration_providers():
    """
    Returns all providers with at least one registered capability.
    """

    return sorted(
        {
            capability.provider
            for capability
            in _CAPABILITIES.values()
        }
    )


# ---------------------------------------------------------------------------
# List One Provider
# ---------------------------------------------------------------------------

def list_provider_capabilities(
    provider: str,
):
    """
    Returns capabilities registered under one provider.
    """

    provider = normalize_name(
        provider
    )


    return [
        capability
        for capability
        in list_integration_capabilities()
        if capability.provider
        == provider
    ]


# ---------------------------------------------------------------------------
# Default Provider Loading
# ---------------------------------------------------------------------------

def load_default_integrations(
    include_mock: bool = False,
):
    """
    Loads built-in provider capability definitions.

    This function registers capability definitions only.

    It MUST NOT:

        - open OAuth flows
        - access stored secrets
        - connect accounts
        - make provider network requests
        - retrieve user data

    Those operations belong to later Phase 9 account and connection
    layers.

    Mock loading is opt-in so fake development data can never silently
    appear in normal E.V.I.E. operation.
    """

    global _DEFAULTS_LOADED


    # -----------------------------------------------------------------------
    # Future Real Providers
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # Real Providers
    # -----------------------------------------------------------------------

    from .providers.google.provider import (
        load_google_provider,
    )

    load_google_provider()

    from .providers.spotify.provider import (
        load_spotify_provider,
    )

    load_spotify_provider()

    from .providers.apple_bridge.provider import (
        load_apple_bridge_provider,
    )

    load_apple_bridge_provider()

    from .providers.schwab.provider import (
        load_schwab_provider,
    )

    load_schwab_provider()

    from .providers.weather.provider import (
        load_weather_provider,
    )

    load_weather_provider()

    from .providers.github.provider import (
        load_github_provider,
    )

    load_github_provider()

    from .providers.notion.provider import (
        load_notion_provider,
    )

    load_notion_provider()

    # -----------------------------------------------------------------------
    # Development Mock
    # -----------------------------------------------------------------------

    if include_mock:

        from .providers.mock import (
            load_mock_provider,
        )


        load_mock_provider()


    _DEFAULTS_LOADED = True


    return list_integration_capabilities()


# ---------------------------------------------------------------------------
# Defaults Loaded
# ---------------------------------------------------------------------------

def defaults_loaded():
    """
    Returns whether the default provider-definition loader has run in
    this Python process.
    """

    return _DEFAULTS_LOADED


# ---------------------------------------------------------------------------
# Clear Registry
# ---------------------------------------------------------------------------

def clear_integration_registry():
    """
    Clears all registered integration capabilities.

    Intended primarily for development and tests.
    """

    global _DEFAULTS_LOADED


    _CAPABILITIES.clear()

    _DEFAULTS_LOADED = False


# ---------------------------------------------------------------------------
# Registry Summary
# ---------------------------------------------------------------------------

def get_registry_summary():
    """
    Returns a lightweight diagnostic representation of registry state.
    """

    capabilities = (
        list_integration_capabilities()
    )


    return {
        "defaults_loaded":
            defaults_loaded(),

        "provider_count":
            len(
                list_integration_providers()
            ),

        "capability_count":
            len(
                capabilities
            ),

        "providers":
            list_integration_providers(),

        "capabilities":
            [
                {
                    "provider":
                        capability.provider,

                    "name":
                        capability.name,

                    "risk":
                        capability.risk,

                    "sensitivity":
                        capability.sensitivity,

                    "description":
                        capability.description,
                }

                for capability
                in capabilities
            ],
    }


# ---------------------------------------------------------------------------
# Standalone Diagnostic
# ---------------------------------------------------------------------------

def run_standalone_test():
    """
    Runs the registry diagnostic.

    Important:
        When Python executes this module through:

            python -m assistant.integrations.registry

        this file runs as __main__.

        Provider modules import the canonical package module:

            assistant.integrations.registry

        That would otherwise create two separate module instances and
        therefore two separate in-memory _CAPABILITIES dictionaries.

        To avoid the duplicate-module issue, the standalone diagnostic
        explicitly imports and uses the canonical package module.
    """

    import importlib


    canonical_registry = (
        importlib.import_module(
            "assistant.integrations.registry"
        )
    )


    canonical_registry.clear_integration_registry()


    canonical_registry.load_default_integrations(
        include_mock=True
    )


    print(
        "E.V.I.E. Integration Registry"
    )

    print(
        "-----------------------------"
    )


    print()


    providers = (
        canonical_registry
        .list_integration_providers()
    )


    print(
        "Providers:",
        providers,
    )


    print()


    capabilities = (
        canonical_registry
        .list_integration_capabilities()
    )


    print(
        "Capabilities registered:",
        len(
            capabilities
        ),
    )


    print()


    for capability in capabilities:

        print(
            (
                f"{capability.provider}:"
                f"{capability.name}"
            )
        )

        print(
            "  Risk:",
            capability.risk,
        )

        print(
            "  Sensitivity:",
            capability.sensitivity,
        )

        print(
            "  Description:",
            capability.description,
        )

        print()


# ---------------------------------------------------------------------------
# Standalone Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    run_standalone_test()