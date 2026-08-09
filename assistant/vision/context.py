"""
E.V.I.E. - Visual Context Router

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Determines when screen vision is required and selects the most
    appropriate visual target.

Targets:
    - desktop
    - active window
    - specific monitor
    - no vision

Most Recent Change:
    Added intelligent visual targeting, monitor selection,
    active-window capture, perception metadata, and stale-image cleanup.
"""

import re

from .capture import (
    capture_active_window,
    capture_desktop,
    capture_monitor,
)

from .lifecycle import (
    cleanup_stale_visual_artifacts,
)

from ..perception.system import (
    get_active_window_title,
)


VISION_TRIGGERS = (
    "screen",
    "look at this",
    "look at my",
    "what am i looking at",
    "what do you see",
    "what can you see",
    "see this",
    "see my screen",
    "on my screen",
    "what is on my screen",
    "what's on my screen",
    "whats on my screen",
    "visible",
    "visually",
    "error on",
    "error shown",
    "what error",
    "dialog",
    "popup",
    "pop-up",
    "window looks",
    "what's wrong here",
    "whats wrong here",
    "what is wrong here",
    "look at the error",
    "look at the window",
    "look at the terminal",
    "webpage do you see",
    "page do you see",
    "code i currently have visible",
    "code visible",
)


DESKTOP_TRIGGERS = (
    "my screen",
    "whole screen",
    "entire screen",
    "entire desktop",
    "whole desktop",
    "desktop",
    "everything on my screen",
    "all monitors",
    "both monitors",
)


ACTIVE_WINDOW_TRIGGERS = (
    "this window",
    "active window",
    "current window",
    "window",
    "terminal",
    "error",
    "dialog",
    "popup",
    "pop-up",
    "webpage",
    "page",
    "code",
    "visible",
    "what am i looking at",
    "look at this",
    "what do you see",
)


def should_use_screen_vision(
    user_message: str,
):
    """
    Returns True only when the request appears to require visual evidence.
    """

    text = (
        user_message.lower()
    )

    return any(
        trigger in text
        for trigger in VISION_TRIGGERS
    )


def extract_monitor_index(
    user_message: str,
):
    """
    Extracts a requested physical monitor number when present.
    """

    text = (
        user_message.lower()
    )

    patterns = (
        r"\bmonitor\s*(\d+)\b",
        r"\bscreen\s*(\d+)\b",
        r"\bdisplay\s*(\d+)\b",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            return int(
                match.group(1)
            )

    word_numbers = {
        "first monitor": 1,
        "monitor one": 1,
        "second monitor": 2,
        "monitor two": 2,
        "third monitor": 3,
        "monitor three": 3,
    }

    for phrase, number in (
        word_numbers.items()
    ):

        if phrase in text:

            return number

    return None


def select_visual_target(
    user_message: str,
):
    """
    Selects the visual surface best suited to the request.
    """

    if not should_use_screen_vision(
        user_message
    ):
        return {
            "required":
                False,

            "target":
                "none",

            "monitor_index":
                None,
        }

    text = (
        user_message.lower()
    )

    monitor_index = (
        extract_monitor_index(
            user_message
        )
    )

    if monitor_index is not None:

        return {
            "required":
                True,

            "target":
                "monitor",

            "monitor_index":
                monitor_index,
        }

    if any(
        trigger in text
        for trigger in DESKTOP_TRIGGERS
    ):

        return {
            "required":
                True,

            "target":
                "desktop",

            "monitor_index":
                None,
        }

    if any(
        trigger in text
        for trigger in ACTIVE_WINDOW_TRIGGERS
    ):

        return {
            "required":
                True,

            "target":
                "active_window",

            "monitor_index":
                None,
        }

    return {
        "required":
            True,

        "target":
            "active_window",

        "monitor_index":
            None,
    }


def capture_visual_context(
    user_message: str,
):
    """
    Captures a fresh visual context only when needed.
    """

    routing = (
        select_visual_target(
            user_message
        )
    )

    if not routing[
        "required"
    ]:
        return None

    cleanup_stale_visual_artifacts(
        max_age_minutes=60
    )

    target = (
        routing[
            "target"
        ]
    )

    if target == "monitor":

        capture = (
            capture_monitor(
                routing[
                    "monitor_index"
                ]
            )
        )

    elif target == "desktop":

        capture = (
            capture_desktop()
        )

    else:

        capture = (
            capture_active_window(
                fallback_to_desktop=True
            )
        )

    capture[
        "requested_target"
    ] = target

    capture[
        "active_window_title"
    ] = (
        get_active_window_title()
    )

    return capture


if __name__ == "__main__":

    from .lifecycle import (
        delete_visual_artifact,
    )

    test_messages = (
        "What do you see on my screen?",
        "Explain the code I currently have visible.",
        "What error is visible in this window?",
    )

    print(
        "E.V.I.E. Visual Context Router"
    )

    print(
        "------------------------------"
    )

    for message in test_messages:

        context = None

        try:

            routing = (
                select_visual_target(
                    message
                )
            )

            print()

            print(
                "Test message:",
                message,
            )

            print(
                "Vision required:",
                routing[
                    "required"
                ],
            )

            print(
                "Target:",
                routing[
                    "target"
                ],
            )

            context = (
                capture_visual_context(
                    message
                )
            )

            print(
                "Visual context:",
                context,
            )

        finally:

            if context:

                delete_visual_artifact(
                    context.get(
                        "screenshot_path"
                    )
                )

    print()

    print(
        "Temporary test screenshots deleted."
    )
