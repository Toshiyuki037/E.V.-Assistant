"""
E.V.I.E. - Capability Aliases

Phase 10A

Purpose:
Normalizes alternate or legacy capability names into the
canonical capability names registered by E.V.I.E.

Important:
Aliases do NOT grant permissions.

A normalized capability must still exist in the integration
registry before it may be executed.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Capability Aliases
# ---------------------------------------------------------------------------

CAPABILITY_ALIASES = {

    # -----------------------------------------------------------------------
    # Weather
    # -----------------------------------------------------------------------

    "weather":
        "weather.current",

    "current_weather":
        "weather.current",

    "current weather":
        "weather.current",

    "forecast":
        "weather.forecast",

    "weather forecast":
        "weather.forecast",

    "hourly_forecast":
        "weather.hourly",

    "hourly forecast":
        "weather.hourly",

    "hourly_weather":
        "weather.hourly",

    "hourly weather":
        "weather.hourly",


    # -----------------------------------------------------------------------
    # GitHub
    # -----------------------------------------------------------------------

    "github repositories":
        "github.repos",

    "github.repositories":
        "github.repos",

    "repos.read":
        "github.repos",

    "repositories.read":
        "github.repos",

    "github.repository":
        "github.repo",

    "repo.read":
        "github.repo",

    "commits.read":
        "github.commits",

    "github.commit":
        "github.commits",

    "issues.read":
        "github.issues",

    "pulls.read":
        "github.pulls",

    "pull_requests.read":
        "github.pulls",

    "github.pull_requests":
        "github.pulls",

    "notifications.read":
        "github.notifications",

    "workflows.read":
        "github.workflows",

    "actions.read":
        "github.actions",


    # -----------------------------------------------------------------------
    # Finance / Schwab
    # -----------------------------------------------------------------------

    "portfolio":
        "finance.performance",

    "portfolio.performance":
        "finance.performance",

    "portfolio performance":
        "finance.performance",

    "finance.portfolio":
        "finance.performance",

    "holdings":
        "finance.positions",

    "portfolio.positions":
        "finance.positions",

    "cash":
        "finance.balances",

    "cash.balance":
        "finance.balances",

    "cash balance":
        "finance.balances",

    "account.balance":
        "finance.balances",

    "balances.read":
        "finance.balances",

    "transactions.read":
        "finance.transactions",

    "orders.read":
        "finance.orders",


    # -----------------------------------------------------------------------
    # Market Data
    # -----------------------------------------------------------------------

    "quote":
        "market.quote",

    "stock.quote":
        "market.quote",

    "market.price":
        "market.quote",

    "stock.price":
        "market.quote",

    "quotes":
        "market.quotes",

    "price.history":
        "market.history",

    "market.price_history":
        "market.history",


    # -----------------------------------------------------------------------
    # Notion
    # -----------------------------------------------------------------------

    "notion.document.read":
        "notion.read_document",

    "notion.read":
        "notion.read_document",

    "notion.read_page":
        "notion.read_document",

    "notion.page.read":
        "notion.read_document",

    "notion.write":
        "notion.document",

    "notion.document.write":
        "notion.document",

    "notion.append":
        "notion.document",

    "notion.edit_block":
        "notion.block_update",

    "notion.delete_block":
        "notion.block_delete",


    # -----------------------------------------------------------------------
    # Google / Common Legacy Forms
    # -----------------------------------------------------------------------

    "gmail.read":
        "email.read",

    "gmail.search":
        "email.search",

    "gmail.send":
        "email.send",

    "google.calendar.read":
        "calendar.read",

    "google.calendar.create":
        "calendar.create",

    "google.tasks.read":
        "tasks.read",

    "google.tasks.create":
        "tasks.create",

    "google.tasks.complete":
        "tasks.complete",


    # -----------------------------------------------------------------------
    # Spotify / Media
    # -----------------------------------------------------------------------

    "spotify.read":
        "media.read",

    "spotify.playback":
        "media.read",

    "spotify.control":
        "media.control",

    "media.playback":
        "media.read",
}


# ---------------------------------------------------------------------------
# Normalize Text
# ---------------------------------------------------------------------------

def _normalize_name(
    capability: str,
):
    """
    Produces a stable capability lookup string.
    """

    return (
        capability
        .strip()
        .lower()
    )


# ---------------------------------------------------------------------------
# Normalize Capability
# ---------------------------------------------------------------------------

def normalize_capability(
    capability: str,
):
    """
    Converts an alias into its canonical capability.

    Canonical names pass through unchanged.
    Unknown names also pass through unchanged so that registry
    validation can reject them safely.
    """

    if not isinstance(
        capability,
        str,
    ):

        return capability


    normalized = (
        _normalize_name(
            capability
        )
    )


    return CAPABILITY_ALIASES.get(
        normalized,
        normalized,
    )


# ---------------------------------------------------------------------------
# Alias Check
# ---------------------------------------------------------------------------

def is_capability_alias(
    capability: str,
):
    if not isinstance(
        capability,
        str,
    ):

        return False


    normalized = (
        _normalize_name(
            capability
        )
    )


    return (
        normalized
        in CAPABILITY_ALIASES
    )