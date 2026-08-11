"""
E.V.I.E. - Phase 9 Regression Tests

Purpose:
    Lock down the Phase 9 integration architecture so later phases
    cannot silently break Google, Spotify, Schwab, permissions,
    routing, or the integration execution bridge.

Run:
    pytest -q tests/test_phase9_regression.py
"""

from __future__ import annotations

import inspect

import pytest


# ---------------------------------------------------------------------------
# Core imports
# ---------------------------------------------------------------------------

def test_core_phase9_imports():
    import assistant.integrations.accounts
    import assistant.integrations.aggregator
    import assistant.integrations.capabilities
    import assistant.integrations.credentials
    import assistant.integrations.permissions
    import assistant.integrations.registry
    import assistant.tools.executor
    import assistant.tools.integrations
    import assistant.tools.planner


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def test_integration_execute_is_registered():
    from assistant.tools.registry import (
        get_tool,
        load_default_tools,
    )

    load_default_tools()

    tool = get_tool(
        "integration_execute"
    )

    assert tool is not None
    assert tool.name == "integration_execute"
    assert callable(tool.function)


# ---------------------------------------------------------------------------
# Provider registration
# ---------------------------------------------------------------------------

def test_required_phase9_providers_register():
    from assistant.integrations.registry import (
        list_integration_providers,
        load_default_integrations,
    )

    load_default_integrations()

    providers = set(
        list_integration_providers()
    )

    assert "google" in providers
    assert "spotify" in providers
    assert "schwab" in providers


# ---------------------------------------------------------------------------
# Permission policy
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    (
        "capability",
        "expected_risk",
    ),
    [
        ("tasks.read", "low"),
        ("tasks.create", "medium"),
        ("email.search", "low"),
        ("email.send", "high"),
        ("calendar.read", "low"),
        ("calendar.create", "medium"),
        ("media.read", "low"),
        ("media.control", "low"),
        ("finance.positions", "low"),
        ("finance.balances", "low"),
        ("finance.performance", "low"),
        ("finance.orders", "low"),
        ("finance.transactions", "low"),
        ("market.quote", "low"),
        ("market.quotes", "low"),
        ("market.history", "low"),
    ],
)
def test_integration_permission_risks(
    capability,
    expected_risk,
):
    from assistant.integrations.permissions import (
        get_permission,
    )

    permission = get_permission(
        capability
    )

    assert permission is not None
    assert permission.risk == expected_risk


def test_unknown_financial_write_is_not_permitted():
    from assistant.integrations.permissions import (
        get_permission,
    )

    assert get_permission(
        "finance.trade"
    ) is None

    assert get_permission(
        "orders.create"
    ) is None

    assert get_permission(
        "orders.replace"
    ) is None

    assert get_permission(
        "orders.cancel"
    ) is None


# ---------------------------------------------------------------------------
# Executor classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    (
        "capability",
        "expected_risk",
    ),
    [
        ("tasks.read", "low"),
        ("tasks.create", "medium"),
        ("email.send", "high"),
        ("finance.positions", "low"),
        ("finance.performance", "low"),
        ("market.quote", "low"),
        ("finance.trade", "high"),
    ],
)
def test_executor_integration_risk(
    capability,
    expected_risk,
):
    from assistant.tools.executor import (
        determine_effective_risk,
    )

    from assistant.tools.registry import (
        get_tool,
        load_default_tools,
    )

    load_default_tools()

    tool = get_tool(
        "integration_execute"
    )

    assert tool is not None

    risk = determine_effective_risk(
        tool,
        {
            "capability":
                capability,
        },
    )

    assert risk == expected_risk


# ---------------------------------------------------------------------------
# Planner fast gate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message",
    [
        "What stocks do I own?",
        "How much is my portfolio up today?",
        "What's Tesla trading at?",
        "What's my Schwab cash balance?",
        "What Google tasks do I have?",
        "Search my Gmail for Schwab",
        "What am I listening to on Spotify?",
        "What browser tabs do you have open?",
        "Read the current webpage.",
        "Show me my Git status.",
    ],
)
def test_planner_gate_accepts_tool_requests(
    message,
):
    from assistant.tools.planner import (
        should_consider_tools,
    )

    assert should_consider_tools(
        message
    ) is True


@pytest.mark.parametrize(
    "message",
    [
        "What's 2 + 2?",
        "Explain Ohm's law.",
        "What is a linked list?",
    ],
)
def test_planner_gate_does_not_force_normal_questions(
    message,
):
    from assistant.tools.planner import (
        should_consider_tools,
    )

    assert should_consider_tools(
        message
    ) is False


# ---------------------------------------------------------------------------
# Schwab read-only lockdown
# ---------------------------------------------------------------------------

def test_schwab_performance_signature_stays_read_only():
    from assistant.integrations.providers.schwab.accounts import (
        schwab_portfolio_performance,
    )

    signature = inspect.signature(
        schwab_portfolio_performance
    )

    assert "account_id" in signature.parameters
    assert "period" not in signature.parameters


def test_schwab_provider_has_no_trade_functions():
    import assistant.integrations.providers.schwab.accounts as accounts
    import assistant.integrations.providers.schwab.provider as provider

    forbidden_names = (
        "schwab_place_order",
        "schwab_replace_order",
        "schwab_cancel_order",
        "schwab_trade",
        "finance_trade",
    )

    for name in forbidden_names:
        assert not hasattr(
            accounts,
            name,
        )

        assert not hasattr(
            provider,
            name,
        )


# ---------------------------------------------------------------------------
# Google capability names
# ---------------------------------------------------------------------------

def test_google_core_capability_names_exist():
    from assistant.integrations.registry import (
        get_integration_capability,
        load_default_integrations,
    )

    load_default_integrations()

    expected = (
        "email.search",
        "email.send",
        "calendar.read",
        "calendar.create",
        "contacts.search",
        "tasks.read",
        "tasks.create",
        "tasks.complete",
    )

    for capability in expected:
        registered = (
            get_integration_capability(
                "google",
                capability,
            )
        )

        assert registered is not None


# ---------------------------------------------------------------------------
# Spotify capability names
# ---------------------------------------------------------------------------

def test_spotify_core_capability_names_exist():
    from assistant.integrations.registry import (
        get_integration_capability,
        load_default_integrations,
    )

    load_default_integrations()

    expected = (
        "media.read",
        "media.current",
        "media.devices",
        "media.search",
        "media.pause",
        "media.resume",
        "media.next",
        "media.previous",
        "media.volume",
        "media.seek",
        "media.transfer",
        "media.play",
    )

    for capability in expected:
        registered = (
            get_integration_capability(
                "spotify",
                capability,
            )
        )

        assert registered is not None


# ---------------------------------------------------------------------------
# Schwab capability names
# ---------------------------------------------------------------------------

def test_schwab_core_capability_names_exist():
    from assistant.integrations.registry import (
        get_integration_capability,
        load_default_integrations,
    )

    load_default_integrations()

    expected = (
        "finance.account_numbers",
        "finance.accounts",
        "finance.account",
        "finance.balances",
        "finance.positions",
        "finance.performance",
        "finance.orders",
        "finance.transactions",
        "market.quote",
        "market.quotes",
        "market.history",
    )

    for capability in expected:
        registered = (
            get_integration_capability(
                "schwab",
                capability,
            )
        )

        assert registered is not None
