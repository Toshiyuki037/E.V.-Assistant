"""
E.V.I.E. - Google Provider Registration

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Phase:
    Phase 9
"""

from __future__ import annotations

from assistant.integrations.registry import (
    register_integration_capability,
)

from .auth import (
    connect_google_account,
    disconnect_google_account,
)

from .calendar import (
    google_calendar_create_event,
    google_calendar_events,
)

from .contacts import (
    search_google_contacts,
)

from .gmail import (
    google_gmail_search,
    google_gmail_send,
)

from .tasks import (
    google_task_complete,
    google_task_create,
    google_tasks_read,
)


def load_google_provider():

    # -----------------------------------------------------------------------
    # Account
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "google",

        name=
            "account.connect",

        function=
            connect_google_account,

        risk=
            "medium",

        sensitivity=
            "private",

        description=(
            "Connects a Google account using OAuth."
        ),
    )


    register_integration_capability(
        provider=
            "google",

        name=
            "account.disconnect",

        function=
            disconnect_google_account,

        risk=
            "high",

        sensitivity=
            "private",

        description=(
            "Disconnects a Google account."
        ),
    )


    # -----------------------------------------------------------------------
    # Gmail
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "google",

        name=
            "email.search",

        function=
            google_gmail_search,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Searches and reads Gmail messages."
        ),
    )


    register_integration_capability(
        provider=
            "google",

        name=
            "email.send",

        function=
            google_gmail_send,

        risk=
            "high",

        sensitivity=
            "private",

        description=(
            "Sends an email through Gmail."
        ),
    )


    # -----------------------------------------------------------------------
    # Calendar
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "google",

        name=
            "calendar.read",

        function=
            google_calendar_events,

        risk=
            "low",

        sensitivity=
            "personal",

        description=(
            "Reads Google Calendar events."
        ),
    )


    register_integration_capability(
        provider=
            "google",

        name=
            "calendar.create",

        function=
            google_calendar_create_event,

        risk=
            "medium",

        sensitivity=
            "personal",

        description=(
            "Creates a Google Calendar event."
        ),
    )


    # -----------------------------------------------------------------------
    # Contacts
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "google",

        name=
            "contacts.search",

        function=
            search_google_contacts,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Searches Google Contacts."
        ),
    )


    # -----------------------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "google",

        name=
            "tasks.read",

        function=
            google_tasks_read,

        risk=
            "low",

        sensitivity=
            "personal",

        description=(
            "Reads Google Tasks."
        ),
    )


    register_integration_capability(
        provider=
            "google",

        name=
            "tasks.create",

        function=
            google_task_create,

        risk=
            "medium",

        sensitivity=
            "personal",

        description=(
            "Creates a Google Task."
        ),
    )


    register_integration_capability(
        provider=
            "google",

        name=
            "tasks.complete",

        function=
            google_task_complete,

        risk=
            "medium",

        sensitivity=
            "personal",

        description=(
            "Marks a Google Task complete."
        ),
    )