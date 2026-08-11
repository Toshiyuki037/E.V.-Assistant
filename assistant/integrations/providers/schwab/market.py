"""
E.V.I.E. - Schwab Market Data

Phase 9

Read-only market-data capabilities.
"""

from __future__ import annotations

from .api import (
    schwab_get,
)

from .auth import (
    DEFAULT_ACCOUNT_ID,
)


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

def schwab_quotes(
    account_id: str = DEFAULT_ACCOUNT_ID,
    symbols=None,
    fields: str = "all",
    indicative: bool = False,
):
    if isinstance(
        symbols,
        str,
    ):

        symbols_value = (
            symbols
        )


    elif isinstance(
        symbols,
        (
            list,
            tuple,
            set,
        ),
    ):

        symbols_value = (
            ",".join(
                str(
                    symbol
                )
                .strip()
                .upper()

                for symbol
                in symbols

                if str(
                    symbol
                ).strip()
            )
        )


    else:

        raise ValueError(
            "symbols must be a ticker or list of tickers."
        )


    if not symbols_value:

        raise ValueError(
            "At least one market symbol is required."
        )


    return schwab_get(
        account_id=
            account_id,

        api=
            "market",

        path=
            "/quotes",

        params={
            "symbols":
                symbols_value,

            "fields":
                fields,

            "indicative":
                str(
                    bool(
                        indicative
                    )
                ).lower(),
        },
    )


def schwab_quote(
    account_id: str = DEFAULT_ACCOUNT_ID,
    symbol: str = "",
):
    symbol = (
        str(
            symbol
        )
        .strip()
        .upper()
    )


    if not symbol:

        raise ValueError(
            "Market symbol is required."
        )


    result = (
        schwab_quotes(
            account_id=
                account_id,

            symbols=[
                symbol
            ],
        )
    )


    if isinstance(
        result,
        dict,
    ):

        return (
            result.get(
                symbol
            )
            or result
        )


    return result


# ---------------------------------------------------------------------------
# Price History
# ---------------------------------------------------------------------------

def schwab_price_history(
    account_id: str = DEFAULT_ACCOUNT_ID,
    symbol: str = "",
    period_type: str = "month",
    period: int = 1,
    frequency_type: str = "daily",
    frequency: int = 1,
    start_date: int | None = None,
    end_date: int | None = None,
    need_extended_hours_data: bool = False,
    need_previous_close: bool = True,
):
    symbol = (
        str(
            symbol
        )
        .strip()
        .upper()
    )


    if not symbol:

        raise ValueError(
            "Market symbol is required."
        )


    params = {
        "symbol":
            symbol,

        "periodType":
            period_type,

        "period":
            int(
                period
            ),

        "frequencyType":
            frequency_type,

        "frequency":
            int(
                frequency
            ),

        "needExtendedHoursData":
            str(
                bool(
                    need_extended_hours_data
                )
            ).lower(),

        "needPreviousClose":
            str(
                bool(
                    need_previous_close
                )
            ).lower(),
    }


    if start_date is not None:

        params[
            "startDate"
        ] = int(
            start_date
        )


    if end_date is not None:

        params[
            "endDate"
        ] = int(
            end_date
        )


    return schwab_get(
        account_id=
            account_id,

        api=
            "market",

        path=
            "/pricehistory",

        params=
            params,
    )