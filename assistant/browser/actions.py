"""
E.V.I.E. - Browser Actions

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Provides browser interaction primitives for E.V.I.E.

Phase:
    Phase 8 - Browser Intelligence & Control

Capabilities:
    - click by accessible role/name
    - click by visible text
    - fill by label
    - fill by placeholder
    - keyboard presses
    - scrolling

Important:
    These functions do not perform permission checks.

    Permission enforcement remains in Phase 6 tools.
"""

from __future__ import annotations

from .session import (
    get_active_page,
    set_active_page,
)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

def page_result(
    page,
):
    """
    Returns lightweight resulting browser state.
    """

    try:

        title = (
            page.title()
        )

    except Exception:

        title = ""


    return {
        "title":
            title,

        "url":
            page.url,
    }


# ---------------------------------------------------------------------------
# Click by Role
# ---------------------------------------------------------------------------

def click_by_role(
    role: str,
    name: str,
    exact: bool = False,
):
    """
    Clicks an element using its accessibility role and name.
    """

    page = (
        get_active_page()
    )


    set_active_page(
        page
    )


    locator = page.get_by_role(
        role,
        name=name,
        exact=exact,
    )


    locator.first.click(
        timeout=15_000,
    )


    page.wait_for_timeout(
        300
    )


    return page_result(
        page
    )


# ---------------------------------------------------------------------------
# Click by Text
# ---------------------------------------------------------------------------

def click_text(
    text: str,
    exact: bool = False,
):
    """
    Clicks the first visible element containing the requested text.
    """

    page = (
        get_active_page()
    )


    locator = page.get_by_text(
        text,
        exact=exact,
    )


    locator.first.click(
        timeout=15_000,
    )


    page.wait_for_timeout(
        300
    )


    return page_result(
        page
    )


# ---------------------------------------------------------------------------
# Fill by Label
# ---------------------------------------------------------------------------

def fill_label(
    label: str,
    value: str,
    exact: bool = False,
):
    """
    Fills an input using its visible/accessible label.
    """

    page = (
        get_active_page()
    )


    locator = page.get_by_label(
        label,
        exact=exact,
    )


    locator.first.fill(
        value,
        timeout=15_000,
    )


    return {
        **page_result(
            page
        ),

        "filled":
            True,
    }


# ---------------------------------------------------------------------------
# Fill by Placeholder
# ---------------------------------------------------------------------------

def fill_placeholder(
    placeholder: str,
    value: str,
    exact: bool = False,
):
    """
    Fills an input using its placeholder.
    """

    page = (
        get_active_page()
    )


    locator = page.get_by_placeholder(
        placeholder,
        exact=exact,
    )


    locator.first.fill(
        value,
        timeout=15_000,
    )


    return {
        **page_result(
            page
        ),

        "filled":
            True,
    }


# ---------------------------------------------------------------------------
# Keyboard
# ---------------------------------------------------------------------------

def press_key(
    key: str,
):
    """
    Sends a keyboard key to the active page.
    """

    page = (
        get_active_page()
    )


    page.keyboard.press(
        key
    )


    page.wait_for_timeout(
        300
    )


    return page_result(
        page
    )


# ---------------------------------------------------------------------------
# Scroll
# ---------------------------------------------------------------------------

def scroll_page(
    direction: str = "down",
    amount: int = 700,
):
    """
    Scrolls the active page.
    """

    page = (
        get_active_page()
    )


    direction = (
        direction
        .strip()
        .lower()
    )


    amount = abs(
        int(
            amount
        )
    )


    if direction == "down":

        delta = amount

    elif direction == "up":

        delta = -amount

    else:

        raise ValueError(
            (
                "direction must be "
                "'up' or 'down'."
            )
        )


    page.mouse.wheel(
        0,
        delta,
    )


    page.wait_for_timeout(
        300
    )


    return page_result(
        page
    )