"""
E.V.I.E. - Schwab Accounts

Phase 9

READ ONLY.

Provides:
- authorized brokerage account identifiers
- brokerage accounts
- balances
- positions
- portfolio performance
- orders
- transactions

No order placement, replacement, or cancellation functions exist in
this module.
"""

from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from .api import (
    schwab_get,
)

from .auth import (
    DEFAULT_ACCOUNT_ID,
)


# ---------------------------------------------------------------------------
# Authorized Brokerage Accounts
# ---------------------------------------------------------------------------

def schwab_account_numbers(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    return schwab_get(
        account_id=
            account_id,

        path=
            "/accounts/accountNumbers",
    )


# ---------------------------------------------------------------------------
# Brokerage Accounts
# ---------------------------------------------------------------------------

def schwab_accounts(
    account_id: str = DEFAULT_ACCOUNT_ID,
    include_positions: bool = True,
):
    params = {}


    if include_positions:

        params[
            "fields"
        ] = "positions"


    return schwab_get(
        account_id=
            account_id,

        path=
            "/accounts",

        params=
            params,
    )


# ---------------------------------------------------------------------------
# One Brokerage Account
# ---------------------------------------------------------------------------

def schwab_account(
    account_id: str = DEFAULT_ACCOUNT_ID,
    account_hash: str = "",
    include_positions: bool = True,
):
    if not account_hash:

        raise ValueError(
            "Schwab account_hash is required."
        )


    params = {}


    if include_positions:

        params[
            "fields"
        ] = "positions"


    return schwab_get(
        account_id=
            account_id,

        path=(
            f"/accounts/"
            f"{account_hash}"
        ),

        params=
            params,
    )


# ---------------------------------------------------------------------------
# Balances
# ---------------------------------------------------------------------------

def schwab_balances(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    """
    Returns normalized balance information for every authorized account.

    Schwab's original balance dictionaries are preserved.
    """

    accounts = (
        schwab_accounts(
            account_id=
                account_id,

            include_positions=
                False,
        )
    )


    results = []


    for item in (
        accounts
        or []
    ):

        securities = (
            item.get(
                "securitiesAccount",
                {},
            )
            or {}
        )


        results.append(
            {
                "type":
                    securities.get(
                        "type"
                    ),

                "account_number":
                    securities.get(
                        "accountNumber"
                    ),

                "current_balances":
                    securities.get(
                        "currentBalances",
                        {},
                    ),

                "initial_balances":
                    securities.get(
                        "initialBalances",
                        {},
                    ),

                "projected_balances":
                    securities.get(
                        "projectedBalances",
                        {},
                    ),

                "aggregated_balance":
                    item.get(
                        "aggregatedBalance",
                        {},
                    ),
            }
        )


    return results


# ---------------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------------

def schwab_positions(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    accounts = (
        schwab_accounts(
            account_id=
                account_id,

            include_positions=
                True,
        )
    )


    positions = []


    for item in (
        accounts
        or []
    ):

        securities = (
            item.get(
                "securitiesAccount",
                {},
            )
            or {}
        )


        account_number = (
            securities.get(
                "accountNumber",
                "",
            )
        )


        for position in (
            securities.get(
                "positions",
                [],
            )
            or []
        ):

            normalized = dict(
                position
            )


            normalized[
                "_account_number"
            ] = account_number


            positions.append(
                normalized
            )


    return positions


# ---------------------------------------------------------------------------
# Portfolio Performance
# ---------------------------------------------------------------------------

def schwab_portfolio_performance(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    """
    Calculates current portfolio and current-day performance using
    Schwab's position-level performance fields.

    READ ONLY.
    """

    accounts = (
        schwab_accounts(
            account_id=
                account_id,

            include_positions=
                True,
        )
    )


    holdings = []

    total_market_value = 0.0

    total_day_profit_loss = 0.0

    total_open_profit_loss = 0.0

    total_cash = 0.0

    total_liquidation_value = 0.0


    for item in (
        accounts
        or []
    ):

        securities = (
            item.get(
                "securitiesAccount",
                {},
            )
            or {}
        )


        account_number = (
            securities.get(
                "accountNumber",
                "",
            )
            or ""
        )


        current_balances = (
            securities.get(
                "currentBalances",
                {},
            )
            or {}
        )


        total_cash += float(
            current_balances.get(
                "cashBalance",
                0.0,
            )
            or 0.0
        )


        total_liquidation_value += float(
            current_balances.get(
                "liquidationValue",
                0.0,
            )
            or 0.0
        )


        positions = (
            securities.get(
                "positions",
                [],
            )
            or []
        )


        for position in positions:

            instrument = (
                position.get(
                    "instrument",
                    {},
                )
                or {}
            )


            symbol = str(
                instrument.get(
                    "symbol",
                    "",
                )
                or ""
            )


            description = str(
                instrument.get(
                    "description",
                    "",
                )
                or ""
            )


            asset_type = str(
                instrument.get(
                    "assetType",
                    "",
                )
                or ""
            )


            quantity = float(
                position.get(
                    "longQuantity",
                    0.0,
                )
                or 0.0
            )


            short_quantity = float(
                position.get(
                    "shortQuantity",
                    0.0,
                )
                or 0.0
            )


            market_value = float(
                position.get(
                    "marketValue",
                    0.0,
                )
                or 0.0
            )


            average_price = float(
                position.get(
                    "averagePrice",
                    0.0,
                )
                or 0.0
            )


            day_profit_loss = float(
                position.get(
                    "currentDayProfitLoss",
                    0.0,
                )
                or 0.0
            )


            day_profit_loss_percent = float(
                position.get(
                    "currentDayProfitLossPercentage",
                    0.0,
                )
                or 0.0
            )


            open_profit_loss = float(
                position.get(
                    "longOpenProfitLoss",
                    0.0,
                )
                or 0.0
            )


            net_change = float(
                instrument.get(
                    "netChange",
                    0.0,
                )
                or 0.0
            )


            total_market_value += (
                market_value
            )


            total_day_profit_loss += (
                day_profit_loss
            )


            total_open_profit_loss += (
                open_profit_loss
            )


            holdings.append(
                {
                    "account_number":
                        account_number,

                    "symbol":
                        symbol,

                    "description":
                        description,

                    "asset_type":
                        asset_type,

                    "quantity":
                        quantity,

                    "short_quantity":
                        short_quantity,

                    "average_price":
                        average_price,

                    "market_value":
                        market_value,

                    "day_profit_loss":
                        day_profit_loss,

                    "day_profit_loss_percent":
                        day_profit_loss_percent,

                    "open_profit_loss":
                        open_profit_loss,

                    "net_change":
                        net_change,
                }
            )


    # -----------------------------------------------------------------------
    # Calculate portfolio-level day percentage
    # -----------------------------------------------------------------------

    previous_position_value = (
        total_market_value
        - total_day_profit_loss
    )


    if previous_position_value:

        total_day_profit_loss_percent = (
            total_day_profit_loss
            / previous_position_value
            * 100.0
        )


    else:

        total_day_profit_loss_percent = (
            0.0
        )


    # -----------------------------------------------------------------------
    # Sort contributors
    # -----------------------------------------------------------------------

    gainers = sorted(
        [
            holding
            for holding in holdings
            if (
                holding[
                    "day_profit_loss"
                ]
                > 0
            )
        ],

        key=lambda holding: (
            holding[
                "day_profit_loss"
            ]
        ),

        reverse=True,
    )


    losers = sorted(
        [
            holding
            for holding in holdings
            if (
                holding[
                    "day_profit_loss"
                ]
                < 0
            )
        ],

        key=lambda holding: (
            holding[
                "day_profit_loss"
            ]
        ),
    )


    by_percent_gain = sorted(
        [
            holding
            for holding in holdings
            if (
                holding[
                    "day_profit_loss_percent"
                ]
                > 0
            )
        ],

        key=lambda holding: (
            holding[
                "day_profit_loss_percent"
            ]
        ),

        reverse=True,
    )


    by_percent_loss = sorted(
        [
            holding
            for holding in holdings
            if (
                holding[
                    "day_profit_loss_percent"
                ]
                < 0
            )
        ],

        key=lambda holding: (
            holding[
                "day_profit_loss_percent"
            ]
        ),
    )


    # -----------------------------------------------------------------------
    # Result
    # -----------------------------------------------------------------------

    return {
        "portfolio_market_value":
            round(
                total_market_value,
                2,
            ),

        "account_liquidation_value":
            round(
                total_liquidation_value,
                2,
            ),

        "cash_balance":
            round(
                total_cash,
                2,
            ),

        "day_profit_loss":
            round(
                total_day_profit_loss,
                2,
            ),

        "day_profit_loss_percent":
            round(
                total_day_profit_loss_percent,
                4,
            ),

        "open_profit_loss":
            round(
                total_open_profit_loss,
                2,
            ),

        "positions_count":
            len(
                holdings
            ),

        "holdings":
            holdings,

        "top_gainers":
            gainers[
                :5
            ],

        "top_losers":
            losers[
                :5
            ],

        "top_percent_gainers":
            by_percent_gain[
                :5
            ],

        "top_percent_losers":
            by_percent_loss[
                :5
            ],
    }


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def schwab_orders(
    account_id: str = DEFAULT_ACCOUNT_ID,
    account_hash: str = "",
    from_time: str | None = None,
    to_time: str | None = None,
    max_results: int = 100,
    status: str | None = None,
):
    if not account_hash:

        raise ValueError(
            "Schwab account_hash is required."
        )


    now = (
        datetime.now(
            timezone.utc
        )
    )


    if to_time is None:

        to_time = (
            now.isoformat()
        )


    if from_time is None:

        from_time = (
            (
                now
                - timedelta(
                    days=30
                )
            )
            .isoformat()
        )


    params = {
        "fromEnteredTime":
            from_time,

        "toEnteredTime":
            to_time,

        "maxResults":
            max(
                1,
                min(
                    3000,
                    int(
                        max_results
                    ),
                ),
            ),
    }


    if status:

        params[
            "status"
        ] = (
            str(
                status
            )
            .upper()
        )


    return schwab_get(
        account_id=
            account_id,

        path=(
            f"/accounts/"
            f"{account_hash}"
            "/orders"
        ),

        params=
            params,
    )


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def schwab_transactions(
    account_id: str = DEFAULT_ACCOUNT_ID,
    account_hash: str = "",
    start_date: str | None = None,
    end_date: str | None = None,
    transaction_types: str = "TRADE",
    symbol: str | None = None,
):
    if not account_hash:

        raise ValueError(
            "Schwab account_hash is required."
        )


    now = (
        datetime.now(
            timezone.utc
        )
    )


    if end_date is None:

        end_date = (
            now.isoformat()
        )


    if start_date is None:

        start_date = (
            (
                now
                - timedelta(
                    days=30
                )
            )
            .isoformat()
        )


    params = {
        "startDate":
            start_date,

        "endDate":
            end_date,

        "types":
            transaction_types,
    }


    if symbol:

        params[
            "symbol"
        ] = (
            str(
                symbol
            )
            .upper()
        )


    return schwab_get(
        account_id=
            account_id,

        path=(
            f"/accounts/"
            f"{account_hash}"
            "/transactions"
        ),

        params=
            params,
    )