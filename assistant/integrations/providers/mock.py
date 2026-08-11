"""
E.V.I.E. - Mock Integration Provider

Purpose:
    Tests the Phase 9 integration architecture without requiring
    external accounts, credentials, OAuth, or network access.

This provider should be removed from real user workflows later, but it
is useful for validating the integration registry and normalized models.
"""

from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
)

from ..models import (
    Event,
    FinancialPosition,
    Message,
)

from ..registry import (
    register_integration_capability,
)


# ---------------------------------------------------------------------------
# Mock Calendar
# ---------------------------------------------------------------------------

def mock_calendar_events():
    tomorrow = (
        datetime.now()
        + timedelta(
            days=1
        )
    )


    return [
        Event(
            id="mock-event-1",
            provider="mock",
            account_id="personal",
            title="Research Meeting",
            start_time=(
                tomorrow
                .replace(
                    hour=9,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                .isoformat()
            ),
            end_time=(
                tomorrow
                .replace(
                    hour=10,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                .isoformat()
            ),
            location="Engineering Building",
            attendees=[
                "Matt"
            ],
        )
    ]


# ---------------------------------------------------------------------------
# Mock Email
# ---------------------------------------------------------------------------

def mock_search_email(
    query: str,
):
    return [
        Message(
            id="mock-message-1",
            provider="mock",
            account_id="personal",
            sender="Matt",
            recipients=[
                "Max"
            ],
            subject="Paperwork",
            body=(
                "I will send the signed form. "
                "You can submit everything once "
                "you receive my copy."
            ),
            timestamp=(
                datetime.now()
                .isoformat()
            ),
            conversation_id="mock-thread-1",
        )
    ]


# ---------------------------------------------------------------------------
# Mock Portfolio
# ---------------------------------------------------------------------------

def mock_portfolio():
    return [
        FinancialPosition(
            symbol="NVDA",
            quantity=10,
            market_value=1500.00,
            day_change=25.00,
            day_change_percent=1.69,
        ),

        FinancialPosition(
            symbol="MSFT",
            quantity=5,
            market_value=2200.00,
            day_change=-8.00,
            day_change_percent=-0.36,
        ),
    ]


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def load_mock_provider():

    register_integration_capability(
        provider="mock",
        name="calendar.read",

        function=
            mock_calendar_events,

        risk="low",

        sensitivity="personal",

        description=(
            "Returns mock calendar events "
            "for Phase 9 testing."
        ),
    )


    register_integration_capability(
        provider="mock",
        name="email.search",

        function=
            mock_search_email,

        risk="low",

        sensitivity="private",

        description=(
            "Searches mock email messages "
            "for Phase 9 testing."
        ),
    )


    register_integration_capability(
        provider="mock",
        name="finance.read",

        function=
            mock_portfolio,

        risk="low",

        sensitivity="financial",

        description=(
            "Returns a mock portfolio "
            "for Phase 9 testing."
        ),
    )