"""
E.V.I.E. - Browser Context

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Converts live browser state into structured reasoning context.

Phase:
    Phase 8 - Browser Intelligence & Control

Capabilities:
    - tab enumeration
    - active tab detection
    - visible page text extraction
    - link extraction
    - button extraction
    - input extraction
    - page summaries
"""

from __future__ import annotations

from .session import (
    get_active_page,
    get_pages,
    safe_title,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_PAGE_TEXT = 20_000

MAX_LINKS = 75

MAX_BUTTONS = 50

MAX_INPUTS = 50


# ---------------------------------------------------------------------------
# Trim Text
# ---------------------------------------------------------------------------

def trim_text(
    text: str,
    limit: int,
):
    if not text:

        return ""


    text = str(
        text
    )


    if len(text) <= limit:

        return text


    return (
        text[:limit]
        + "\n\n[Browser text truncated]"
    )


# ---------------------------------------------------------------------------
# Page Description
# ---------------------------------------------------------------------------

def describe_page(
    page,
    index: int,
    active_page=None,
):
    """
    Describes one browser tab.
    """

    return {
        "index":
            index,

        "active":
            page is active_page,

        "title":
            safe_title(
                page
            ),

        "url":
            page.url,
    }


# ---------------------------------------------------------------------------
# Visible Page Text
# ---------------------------------------------------------------------------

def get_visible_text(
    page=None,
    max_characters: int = MAX_PAGE_TEXT,
):
    """
    Reads visible text from the current page.
    """

    if page is None:

        page = (
            get_active_page()
        )


    try:

        text = page.locator(
            "body"
        ).inner_text(
            timeout=10_000
        )

    except Exception:

        text = ""


    return trim_text(
        text,
        int(
            max_characters
        ),
    )


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def get_page_links(
    page=None,
    limit: int = MAX_LINKS,
):
    """
    Returns visible links from the active page.
    """

    if page is None:

        page = (
            get_active_page()
        )


    locator = page.locator(
        "a[href]"
    )


    count = min(
        locator.count(),
        int(limit),
    )


    links = []


    for index in range(
        count
    ):

        item = (
            locator.nth(
                index
            )
        )


        try:

            if not item.is_visible():

                continue


            text = (
                item.inner_text(
                    timeout=2_000
                )
                .strip()
            )


            href = (
                item.get_attribute(
                    "href"
                )
                or ""
            )


            if not href:

                continue


            links.append(
                {
                    "text":
                        text[:300],

                    "href":
                        href,
                }
            )


        except Exception:

            continue


    return links


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------

def get_page_buttons(
    page=None,
    limit: int = MAX_BUTTONS,
):
    """
    Returns visible button-like elements.
    """

    if page is None:

        page = (
            get_active_page()
        )


    locator = page.get_by_role(
        "button"
    )


    count = min(
        locator.count(),
        int(limit),
    )


    buttons = []


    for index in range(
        count
    ):

        item = (
            locator.nth(
                index
            )
        )


        try:

            if not item.is_visible():

                continue


            text = (
                item.inner_text(
                    timeout=2_000
                )
                .strip()
            )


            buttons.append(
                {
                    "index":
                        index + 1,

                    "text":
                        text[:300],
                }
            )


        except Exception:

            continue


    return buttons


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def get_page_inputs(
    page=None,
    limit: int = MAX_INPUTS,
):
    """
    Returns useful information about visible input elements.
    """

    if page is None:

        page = (
            get_active_page()
        )


    locator = page.locator(
        "input, textarea"
    )


    count = min(
        locator.count(),
        int(limit),
    )


    inputs = []


    for index in range(
        count
    ):

        item = (
            locator.nth(
                index
            )
        )


        try:

            if not item.is_visible():

                continue


            inputs.append(
                {
                    "index":
                        index + 1,

                    "type":
                        (
                            item.get_attribute(
                                "type"
                            )
                            or ""
                        ),

                    "name":
                        (
                            item.get_attribute(
                                "name"
                            )
                            or ""
                        ),

                    "placeholder":
                        (
                            item.get_attribute(
                                "placeholder"
                            )
                            or ""
                        ),

                    "aria_label":
                        (
                            item.get_attribute(
                                "aria-label"
                            )
                            or ""
                        ),
                }
            )


        except Exception:

            continue


    return inputs


# ---------------------------------------------------------------------------
# Browser State
# ---------------------------------------------------------------------------

def get_browser_state(
    include_text: bool = False,
):
    """
    Returns structured browser state.
    """

    pages = (
        get_pages()
    )


    active_page = (
        get_active_page()
    )


    tabs = []


    for index, page in enumerate(
        pages,
        start=1,
    ):

        tabs.append(
            describe_page(
                page,
                index,
                active_page,
            )
        )


    active_index = None


    for index, page in enumerate(
        pages,
        start=1,
    ):

        if page is active_page:

            active_index = index

            break


    result = {
        "tab_count":
            len(
                pages
            ),

        "active_tab":
            active_index,

        "active_title":
            safe_title(
                active_page
            ),

        "active_url":
            active_page.url,

        "tabs":
            tabs,
    }


    if include_text:

        result[
            "visible_text"
        ] = get_visible_text(
            active_page
        )


    return result


# ---------------------------------------------------------------------------
# Complete Page Context
# ---------------------------------------------------------------------------

def get_page_context():
    """
    Returns reasoning-oriented context for the active page.
    """

    page = (
        get_active_page()
    )


    return {
        "title":
            safe_title(
                page
            ),

        "url":
            page.url,

        "visible_text":
            get_visible_text(
                page
            ),

        "links":
            get_page_links(
                page
            ),

        "buttons":
            get_page_buttons(
                page
            ),

        "inputs":
            get_page_inputs(
                page
            ),
    }


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    from pprint import (
        pprint,
    )

    from .session import (
        close_browser,
        new_page,
        start_browser,
    )


    start_browser(
        headless=False
    )


    new_page(
        "https://example.com"
    )


    pprint(
        get_page_context()
    )


    input(
        "\nPress Enter to close..."
    )


    close_browser()