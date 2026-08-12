"""
E.V.I.E. - Windows Notifications

Phase 13E

Uses winotify for Windows toast notifications.

This is an application integration, not UI clicking.
"""

from __future__ import annotations

import sys

from .notification_models import NotificationResult


IS_WINDOWS = sys.platform == "win32"


class NotificationBackendUnavailable(RuntimeError):
    pass


def _load_winotify():
    try:
        from winotify import Notification
    except ImportError as error:
        raise NotificationBackendUnavailable(
            "Phase 13E Windows notifications require winotify. "
            "Install it with: python -m pip install winotify"
        ) from error

    return Notification


def send_windows_notification(
    title: str,
    message: str,
    *,
    app_id: str = "E.V.I.E.",
) -> NotificationResult:
    if not IS_WINDOWS:
        raise NotificationBackendUnavailable(
            "Windows toast notifications are only available on Windows."
        )

    title_text = str(title or "").strip()
    message_text = str(message or "").strip()

    if not title_text:
        raise ValueError(
            "Notification title cannot be empty."
        )

    if not message_text:
        raise ValueError(
            "Notification message cannot be empty."
        )

    Notification = _load_winotify()

    try:
        toast = Notification(
            app_id=str(app_id),
            title=title_text,
            msg=message_text,
        )

        toast.show()

    except Exception as error:
        return NotificationResult(
            title=title_text,
            message=message_text,
            success=False,
            backend="winotify",
            detail=str(error),
        )

    return NotificationResult(
        title=title_text,
        message=message_text,
        success=True,
        backend="winotify",
        detail="Notification submitted.",
    )
