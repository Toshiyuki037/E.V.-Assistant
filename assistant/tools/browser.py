"""
E.V.I.E. - Browser Tools

Created: August 9, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Exposes controlled browser operations through E.V.I.E.'s
    Phase 6 tool registry.

Phase:
    Phase 6 Tool Layer
    Phase 8 Browser Intelligence & Control

Security:
    Phase 8 does not bypass Phase 6.

    Every browser operation exposed to E.V.I.E. is registered with
    an explicit risk classification.

Risk Policy:
    LOW:
        read-only state
        navigation
        search
        tab management
        scrolling

    MEDIUM:
        typing into webpages
        clicking arbitrary page elements

Important:
    Phase 7 may compose these tools but does not directly call
    Playwright.
"""

from __future__ import annotations

import webbrowser

from urllib.parse import (
    urlparse,
)

from assistant.browser.actions import (
    click_by_role,
    click_text,
    fill_label,
    fill_placeholder,
    press_key,
    scroll_page,
)

from assistant.browser.context import (
    get_browser_state,
    get_page_context,
)

from assistant.browser.research import (
    read_current_source,
    search_web,
)

from assistant.browser.session import (
    activate_tab,
    close_browser,
    close_tab,
    go_back,
    go_forward,
    navigate,
    new_page,
    reload_page,
    start_browser,
)

from .registry import (
    register_tool,
)


# ---------------------------------------------------------------------------
# Safe URL
# ---------------------------------------------------------------------------

def validate_http_url(
    url: str,
):
    """
    Validates a normal HTTP/HTTPS URL.
    """

    if not url:

        raise ValueError(
            "No URL was provided."
        )


    url = (
        str(
            url
        )
        .strip()
    )


    parsed = urlparse(
        url
    )


    if parsed.scheme not in {
        "http",
        "https",
    }:

        raise ValueError(
            "Only HTTP and HTTPS URLs are allowed."
        )


    if not parsed.netloc:

        raise ValueError(
            "URL does not contain a valid host."
        )


    return url


# ---------------------------------------------------------------------------
# Legacy Default-Browser URL Opening
# ---------------------------------------------------------------------------

def open_url(
    url: str,
):
    """
    Opens a safe URL in the user's default browser.

    Preserved from Phase 6.
    """

    url = validate_http_url(
        url
    )


    opened = webbrowser.open(
        url,
        new=2,
    )


    return {
        "url":
            url,

        "opened":
            bool(
                opened
            ),
    }


# ---------------------------------------------------------------------------
# Managed Browser Startup
# ---------------------------------------------------------------------------

def browser_start(
    headless: bool = False,
):
    browser = start_browser(
        headless=headless
    )


    return {
        "connected":
            browser.is_connected(),
    }


# ---------------------------------------------------------------------------
# Browser State
# ---------------------------------------------------------------------------

def browser_get_state(
    include_text: bool = False,
):
    return get_browser_state(
        include_text=include_text
    )


# ---------------------------------------------------------------------------
# Read Page
# ---------------------------------------------------------------------------

def browser_read_page(
    max_characters: int = 25_000,
):
    return read_current_source(
        max_characters=max_characters
    )


# ---------------------------------------------------------------------------
# Complete Page Context
# ---------------------------------------------------------------------------

def browser_get_page_context():
    return get_page_context()


# ---------------------------------------------------------------------------
# New Tab
# ---------------------------------------------------------------------------

def browser_new_tab(
    url: str | None = None,
):
    page = new_page(
        url=url
    )


    return {
        "opened":
            True,

        "title":
            page.title(),

        "url":
            page.url,
    }


# ---------------------------------------------------------------------------
# Navigate
# ---------------------------------------------------------------------------

def browser_navigate(
    url: str,
):
    return navigate(
        url
    )


# ---------------------------------------------------------------------------
# Activate Tab
# ---------------------------------------------------------------------------

def browser_activate_tab(
    tab_index: int,
):
    page = activate_tab(
        tab_index
    )


    return {
        "active_tab":
            int(
                tab_index
            ),

        "title":
            page.title(),

        "url":
            page.url,
    }


# ---------------------------------------------------------------------------
# Close Tab
# ---------------------------------------------------------------------------

def browser_close_tab(
    tab_index: int | None = None,
):
    return close_tab(
        tab_index=tab_index
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def browser_back():
    return go_back()


def browser_forward():
    return go_forward()


def browser_reload():
    return reload_page()


# ---------------------------------------------------------------------------
# Scroll
# ---------------------------------------------------------------------------

def browser_scroll(
    direction: str = "down",
    amount: int = 700,
):
    return scroll_page(
        direction=direction,
        amount=amount,
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def browser_search_web(
    query: str,
    limit: int = 10,
):
    return search_web(
        query=query,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Click
# ---------------------------------------------------------------------------

def browser_click_role(
    role: str,
    name: str,
    exact: bool = False,
):
    return click_by_role(
        role=role,
        name=name,
        exact=exact,
    )


def browser_click_text(
    text: str,
    exact: bool = False,
):
    return click_text(
        text=text,
        exact=exact,
    )


# ---------------------------------------------------------------------------
# Fill
# ---------------------------------------------------------------------------

def browser_fill_label(
    label: str,
    value: str,
    exact: bool = False,
):
    return fill_label(
        label=label,
        value=value,
        exact=exact,
    )


def browser_fill_placeholder(
    placeholder: str,
    value: str,
    exact: bool = False,
):
    return fill_placeholder(
        placeholder=placeholder,
        value=value,
        exact=exact,
    )


# ---------------------------------------------------------------------------
# Keyboard
# ---------------------------------------------------------------------------

def browser_press(
    key: str,
):
    return press_key(
        key
    )


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------

def browser_shutdown():
    close_browser()


    return {
        "closed":
            True,
    }


# ---------------------------------------------------------------------------
# Registration - Phase 6 Legacy
# ---------------------------------------------------------------------------

register_tool(
    name="open_url",

    description=(
        "Opens an HTTP or HTTPS URL in the user's default browser."
    ),

    category="browser",

    risk="low",

    function=open_url,
)


# ---------------------------------------------------------------------------
# Registration - Phase 8 Read / Navigation
# ---------------------------------------------------------------------------

register_tool(
    name="browser_start",

    description=(
        "Starts E.V.I.E.'s managed Chromium browser."
    ),

    category="browser",

    risk="low",

    function=browser_start,
)


register_tool(
    name="browser_get_state",

    description=(
        "Returns E.V.I.E.'s managed browser tabs, active tab, "
        "page titles, URLs, and optionally visible text."
    ),

    category="browser",

    risk="low",

    function=browser_get_state,
)


register_tool(
    name="browser_read_page",

    description=(
        "Reads the active managed browser page and returns its title, "
        "URL, visible text, and useful links for reasoning/research."
    ),

    category="browser",

    risk="low",

    function=browser_read_page,
)


register_tool(
    name="browser_get_page_context",

    description=(
        "Returns structured active-page context including visible text, "
        "links, buttons, and form inputs."
    ),

    category="browser",

    risk="low",

    function=browser_get_page_context,
)


register_tool(
    name="browser_new_tab",

    description=(
        "Creates a new managed browser tab and optionally navigates "
        "it to an HTTP/HTTPS URL."
    ),

    category="browser",

    risk="low",

    function=browser_new_tab,
)


register_tool(
    name="browser_navigate",

    description=(
        "Navigates the active managed browser tab to an HTTP/HTTPS URL."
    ),

    category="browser",

    risk="low",

    function=browser_navigate,
)


register_tool(
    name="browser_activate_tab",

    description=(
        "Activates a managed browser tab using its 1-based tab index."
    ),

    category="browser",

    risk="low",

    function=browser_activate_tab,
)


register_tool(
    name="browser_close_tab",

    description=(
        "Closes a managed browser tab. Defaults to the active tab."
    ),

    category="browser",

    risk="low",

    function=browser_close_tab,
)


register_tool(
    name="browser_back",

    description=(
        "Navigates backward in the active managed browser tab."
    ),

    category="browser",

    risk="low",

    function=browser_back,
)


register_tool(
    name="browser_forward",

    description=(
        "Navigates forward in the active managed browser tab."
    ),

    category="browser",

    risk="low",

    function=browser_forward,
)


register_tool(
    name="browser_reload",

    description=(
        "Reloads the active managed browser tab."
    ),

    category="browser",

    risk="low",

    function=browser_reload,
)


register_tool(
    name="browser_scroll",

    description=(
        "Scrolls the active managed browser page up or down."
    ),

    category="browser",

    risk="low",

    function=browser_scroll,
)


register_tool(
    name="browser_search_web",

    description=(
        "Searches the live web in E.V.I.E.'s managed browser and "
        "returns search-result links for research."
    ),

    category="browser",

    risk="low",

    function=browser_search_web,
)


# ---------------------------------------------------------------------------
# Registration - Interaction
# ---------------------------------------------------------------------------

register_tool(
    name="browser_click_role",

    description=(
        "Clicks a page element by accessible role and name. "
        "Because arbitrary clicks may cause page actions, approval "
        "is required."
    ),

    category="browser",

    risk="medium",

    function=browser_click_role,
)


register_tool(
    name="browser_click_text",

    description=(
        "Clicks the first visible page element matching text. "
        "Because arbitrary clicks may cause page actions, approval "
        "is required."
    ),

    category="browser",

    risk="medium",

    function=browser_click_text,
)


register_tool(
    name="browser_fill_label",

    description=(
        "Fills a page input identified by its label. "
        "Typing into webpages requires approval."
    ),

    category="browser",

    risk="medium",

    function=browser_fill_label,
)


register_tool(
    name="browser_fill_placeholder",

    description=(
        "Fills a page input identified by its placeholder. "
        "Typing into webpages requires approval."
    ),

    category="browser",

    risk="medium",

    function=browser_fill_placeholder,
)


register_tool(
    name="browser_press",

    description=(
        "Sends a keyboard key to the active managed browser page. "
        "This may submit forms or trigger actions and therefore "
        "requires approval."
    ),

    category="browser",

    risk="medium",

    function=browser_press,
)


register_tool(
    name="browser_shutdown",

    description=(
        "Closes E.V.I.E.'s managed Chromium browser."
    ),

    category="browser",

    risk="low",

    function=browser_shutdown,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    from pprint import (
        pprint,
    )


    print(
        "E.V.I.E. Browser Tools"
    )

    print(
        "-----------------------"
    )


    pprint(
        browser_start()
    )


    pprint(
        browser_new_tab(
            "https://example.com"
        )
    )


    pprint(
        browser_get_state()
    )


    pprint(
        browser_read_page(
            max_characters=3000
        )
    )


    input(
        "\nPress Enter to close..."
    )


    pprint(
        browser_shutdown()
    )