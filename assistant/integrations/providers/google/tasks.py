"""
E.V.I.E. - Google Tasks Integration

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Provides normalized Google Tasks read/create/complete capabilities
    for Phase 9.

Capabilities:
    - tasks.read
    - tasks.create
    - tasks.complete
"""

from __future__ import annotations

from assistant.integrations.models import (
    Task,
)

from .auth import (
    build_google_service,
)


# ---------------------------------------------------------------------------
# Normalize Google Task
# ---------------------------------------------------------------------------

def normalize_google_task(
    account_id: str,
    raw: dict,
):
    return Task(
        id=str(
            raw.get(
                "id",
                "",
            )
        ),

        provider=
            "google",

        account_id=
            account_id,

        title=str(
            raw.get(
                "title",
                "",
            )
        ),

        due_time=str(
            raw.get(
                "due",
                "",
            )
        ),

        completed=(
            raw.get(
                "status"
            )
            == "completed"
        ),

        notes=str(
            raw.get(
                "notes",
                "",
            )
        ),

        metadata={
            "status":
                raw.get(
                    "status",
                    "",
                ),

            "updated":
                raw.get(
                    "updated",
                    "",
                ),

            "completed_at":
                raw.get(
                    "completed",
                    "",
                ),

            "position":
                raw.get(
                    "position",
                    "",
                ),

            "parent":
                raw.get(
                    "parent",
                    "",
                ),

            "web_view_link":
                raw.get(
                    "webViewLink",
                    "",
                ),
        },
    )


# ---------------------------------------------------------------------------
# Default Task List
# ---------------------------------------------------------------------------

def get_default_task_list_id(
    account_id: str,
):
    """
    Returns the first available Google task list.

    Usually this corresponds to the user's primary/default task list.
    """

    service = build_google_service(
        account_id,
        "tasks",
        "v1",
    )


    response = (
        service.tasklists()
        .list(
            maxResults=100
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


    if not items:

        raise RuntimeError(
            (
                "No Google Tasks lists were found "
                f"for {account_id}."
            )
        )


    task_list_id = (
        items[
            0
        ].get(
            "id"
        )
    )


    if not task_list_id:

        raise RuntimeError(
            "Google Tasks returned an invalid task list."
        )


    return task_list_id


# ---------------------------------------------------------------------------
# List Task Lists
# ---------------------------------------------------------------------------

def google_task_lists(
    account_id: str,
):
    service = build_google_service(
        account_id,
        "tasks",
        "v1",
    )


    response = (
        service.tasklists()
        .list(
            maxResults=100
        )
        .execute()
    )


    return (
        response.get(
            "items",
            []
        )
        or []
    )


# ---------------------------------------------------------------------------
# Read Tasks
# ---------------------------------------------------------------------------

def google_tasks_read(
    account_id: str,
    task_list_id: str | None = None,
    max_results: int = 100,
    include_completed: bool = False,
):
    """
    Reads Google Tasks from a task list.
    """

    if not task_list_id:

        task_list_id = (
            get_default_task_list_id(
                account_id
            )
        )


    service = build_google_service(
        account_id,
        "tasks",
        "v1",
    )


    response = (
        service.tasks()
        .list(
            tasklist=
                task_list_id,

            maxResults=
                int(
                    max_results
                ),

            showCompleted=
                bool(
                    include_completed
                ),

            showHidden=
                False,
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
        normalize_google_task(
            account_id,
            raw,
        )

        for raw
        in items
    ]


# ---------------------------------------------------------------------------
# Create Task
# ---------------------------------------------------------------------------

def google_task_create(
    account_id: str,
    title: str,
    notes: str = "",
    due_time: str | None = None,
    task_list_id: str | None = None,
):
    """
    Creates a Google Task.

    due_time should use Google's Tasks API RFC3339 timestamp format.
    """

    title = (
        str(
            title
        )
        .strip()
    )


    if not title:

        raise ValueError(
            "Task title cannot be empty."
        )


    if not task_list_id:

        task_list_id = (
            get_default_task_list_id(
                account_id
            )
        )


    body = {
        "title":
            title,
    }


    if notes:

        body[
            "notes"
        ] = str(
            notes
        )


    if due_time:

        body[
            "due"
        ] = str(
            due_time
        )


    service = build_google_service(
        account_id,
        "tasks",
        "v1",
    )


    raw = (
        service.tasks()
        .insert(
            tasklist=
                task_list_id,

            body=
                body,
        )
        .execute()
    )


    return normalize_google_task(
        account_id,
        raw,
    )


# ---------------------------------------------------------------------------
# Complete Task
# ---------------------------------------------------------------------------

def google_task_complete(
    account_id: str,
    task_id: str,
    task_list_id: str | None = None,
):
    """
    Marks an existing Google Task complete.
    """

    if not task_id:

        raise ValueError(
            "task_id is required."
        )


    if not task_list_id:

        task_list_id = (
            get_default_task_list_id(
                account_id
            )
        )


    service = build_google_service(
        account_id,
        "tasks",
        "v1",
    )


    existing = (
        service.tasks()
        .get(
            tasklist=
                task_list_id,

            task=
                task_id,
        )
        .execute()
    )


    existing[
        "status"
    ] = "completed"


    raw = (
        service.tasks()
        .update(
            tasklist=
                task_list_id,

            task=
                task_id,

            body=
                existing,
        )
        .execute()
    )


    return normalize_google_task(
        account_id,
        raw,
    )