"""
E.V.I.E. - Google Calendar Integration

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Capabilities:
    - calendar.read
    - calendar.create
"""

from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from assistant.integrations.models import (
    Event,
)

from .auth import (
    build_google_service,
)


# ---------------------------------------------------------------------------
# Time Extraction
# ---------------------------------------------------------------------------

def extract_event_time(
    block: dict,
):
    return (
        block.get(
            "dateTime"
        )
        or block.get(
            "date"
        )
        or ""
    )


# ---------------------------------------------------------------------------
# Normalize Event
# ---------------------------------------------------------------------------

def normalize_google_event(
    account_id: str,
    item: dict,
):
    attendees = []


    for attendee in (
        item.get(
            "attendees",
            []
        )
        or []
    ):

        email = attendee.get(
            "email"
        )


        if email:

            attendees.append(
                email
            )


    return Event(
        id=str(
            item.get(
                "id",
                "",
            )
        ),

        provider=
            "google",

        account_id=
            account_id,

        title=str(
            item.get(
                "summary",
                "(No title)",
            )
        ),

        start_time=
            extract_event_time(
                item.get(
                    "start",
                    {},
                )
            ),

        end_time=
            extract_event_time(
                item.get(
                    "end",
                    {},
                )
            ),

        location=str(
            item.get(
                "location",
                "",
            )
        ),

        attendees=
            attendees,

        description=str(
            item.get(
                "description",
                "",
            )
        ),

        calendar_name=
            "primary",

        metadata={
            "html_link":
                item.get(
                    "htmlLink"
                ),

            "status":
                item.get(
                    "status"
                ),
        },
    )


# ---------------------------------------------------------------------------
# Read Events
# ---------------------------------------------------------------------------

def google_calendar_events(
    account_id: str,
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 50,
):
    service = build_google_service(
        account_id,
        "calendar",
        "v3",
    )


    if time_min is None:

        time_min = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )


    arguments = {
        "calendarId":
            "primary",

        "timeMin":
            time_min,

        "maxResults":
            int(
                max_results
            ),

        "singleEvents":
            True,

        "orderBy":
            "startTime",
    }


    if time_max:

        arguments[
            "timeMax"
        ] = time_max


    response = (
        service.events()
        .list(
            **arguments
        )
        .execute()
    )


    items = (
        response.get(
            "items",
            []
        )
        or []
    )


    return [
        normalize_google_event(
            account_id,
            item,
        )

        for item
        in items
    ]


# ---------------------------------------------------------------------------
# Create Event
# ---------------------------------------------------------------------------

def google_calendar_create_event(
    account_id: str,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: list[str] | None = None,
    timezone_name: str | None = None,
    calendar_id: str = "primary",
    send_updates: str = "none",
):
    """
    Creates a timed Google Calendar event.

    start_time/end_time must be RFC3339 datetimes.

    If the values already contain a UTC offset, timezone_name may be
    omitted.
    """

    title = (
        str(
            title
        )
        .strip()
    )


    if not title:

        raise ValueError(
            "Calendar event title is required."
        )


    if not start_time:

        raise ValueError(
            "Calendar event start_time is required."
        )


    if not end_time:

        raise ValueError(
            "Calendar event end_time is required."
        )


    start = {
        "dateTime":
            str(
                start_time
            ),
    }


    end = {
        "dateTime":
            str(
                end_time
            ),
    }


    if timezone_name:

        start[
            "timeZone"
        ] = timezone_name

        end[
            "timeZone"
        ] = timezone_name


    body = {
        "summary":
            title,

        "start":
            start,

        "end":
            end,
    }


    if description:

        body[
            "description"
        ] = str(
            description
        )


    if location:

        body[
            "location"
        ] = str(
            location
        )


    if attendees:

        body[
            "attendees"
        ] = [
            {
                "email":
                    email
            }

            for email
            in attendees
        ]


    service = build_google_service(
        account_id,
        "calendar",
        "v3",
    )


    item = (
        service.events()
        .insert(
            calendarId=
                calendar_id,

            body=
                body,

            sendUpdates=
                send_updates,
        )
        .execute()
    )


    return normalize_google_event(
        account_id,
        item,
    )