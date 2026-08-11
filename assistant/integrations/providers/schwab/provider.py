"""
E.V.I.E. - Schwab Provider Registration

Phase 9

IMPORTANT:
    This provider is intentionally READ ONLY.

    There is no:
        finance.trade
        orders.create
        orders.replace
        orders.cancel
"""

from __future__ import annotations

from assistant.integrations.registry import (
    register_integration_capability,
)

from .accounts import (
    schwab_account,
    schwab_account_numbers,
    schwab_accounts,
    schwab_balances,
    schwab_orders,
    schwab_portfolio_performance,
    schwab_positions,
    schwab_transactions,
)

from .auth import (
    connect_schwab_account,
    disconnect_schwab_account,
)

from .market import (
    schwab_price_history,
    schwab_quote,
    schwab_quotes,
)


# ---------------------------------------------------------------------------
# Provider Loader
# ---------------------------------------------------------------------------

def load_schwab_provider():

    # -----------------------------------------------------------------------
    # Account OAuth
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "schwab",

        name=
            "account.connect",

        function=
            connect_schwab_account,

        risk=
            "medium",

        sensitivity=
            "financial",

        description=(
            "Connects Charles Schwab using OAuth."
        ),
    )


    register_integration_capability(
        provider=
            "schwab",

        name=
            "account.disconnect",

        function=
            disconnect_schwab_account,

        risk=
            "high",

        sensitivity=
            "financial",

        description=(
            "Disconnects the Charles Schwab integration."
        ),
    )


    # -----------------------------------------------------------------------
    # Brokerage Discovery
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.account_numbers",

        function=
            schwab_account_numbers,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads authorized Schwab brokerage account identifiers "
            "and API account hashes."
        ),
    )


    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.accounts",

        function=
            schwab_accounts,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads Schwab brokerage accounts."
        ),
    )


    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.account",

        function=
            schwab_account,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads one Schwab brokerage account."
        ),
    )


    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.balances",

        function=
            schwab_balances,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads Schwab account balances and available cash."
        ),
    )


    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.positions",

        function=
            schwab_positions,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads Schwab portfolio positions."
        ),
    )


    # -----------------------------------------------------------------------
    # Portfolio Performance
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.performance",

        function=
            schwab_portfolio_performance,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads and calculates current Schwab portfolio "
            "performance including today's gain or loss, "
            "portfolio value, and position contributions."
        ),
    )


    # -----------------------------------------------------------------------
    # Orders - READ ONLY
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.orders",

        function=
            schwab_orders,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads existing Schwab orders. "
            "Does not place orders."
        ),
    )


    # -----------------------------------------------------------------------
    # Transactions
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "schwab",

        name=
            "finance.transactions",

        function=
            schwab_transactions,

        risk=
            "low",

        sensitivity=
            "financial",

        description=(
            "Reads Schwab account transaction history."
        ),
    )


    # -----------------------------------------------------------------------
    # Market Data
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "schwab",

        name=
            "market.quote",

        function=
            schwab_quote,

        risk=
            "low",

        sensitivity=
            "public",

        description=(
            "Reads a current Schwab market quote."
        ),
    )


    register_integration_capability(
        provider=
            "schwab",

        name=
            "market.quotes",

        function=
            schwab_quotes,

        risk=
            "low",

        sensitivity=
            "public",

        description=(
            "Reads current Schwab market quotes."
        ),
    )


    register_integration_capability(
        provider=
            "schwab",

        name=
            "market.history",

        function=
            schwab_price_history,

        risk=
            "low",

        sensitivity=
            "public",

        description=(
            "Reads historical market price candles from Schwab."
        ),
    )