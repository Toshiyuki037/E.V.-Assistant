"""
E.V.I.E. - Browser Session

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Owns E.V.I.E.'s managed Playwright browser session.

Phase:
    Phase 8 - Browser Intelligence & Control

Capabilities:
    - lazy Chromium launch
    - persistent in-process browser session
    - tab/page management
    - active-page tracking
    - URL validation
    - navigation
    - back / forward / reload
    - clean shutdown

Important:
    This subsystem owns browser state.

    Natural-language planning remains in Phase 6 / Phase 7.
"""

from __future__ import annotations

from urllib.parse import (
    urlparse,
)

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


# ---------------------------------------------------------------------------
# Browser State
# ---------------------------------------------------------------------------

_playwright: Playwright | None = None

_browser: Browser | None = None

_context: BrowserContext | None = None

_active_page: Page | None = None


# ---------------------------------------------------------------------------
# URL Validation
# ---------------------------------------------------------------------------

def validate_url(
    url: str,
):
    """
    Allows normal HTTP/HTTPS navigation only.
    """

    if not url:

        raise ValueError(
            "No URL was provided."
        )


    url = str(
        url
    ).strip()


    parsed = urlparse(
        url
    )


    if parsed.scheme not in {
        "http",
        "https",
    }:

        raise ValueError(
            (
                "Browser navigation supports "
                "HTTP and HTTPS URLs only."
            )
        )


    if not parsed.netloc:

        raise ValueError(
            "URL does not contain a host."
        )


    return url


# ---------------------------------------------------------------------------
# Browser Startup
# ---------------------------------------------------------------------------

def start_browser(
    headless: bool = False,
):
    """
    Starts E.V.I.E.'s managed Chromium browser.

    Existing sessions are reused.
    """

    global _playwright
    global _browser
    global _context
    global _active_page


    if (
        _browser is not None
        and _browser.is_connected()
        and _context is not None
    ):

        return _browser


    _playwright = (
        sync_playwright()
        .start()
    )


    _browser = (
        _playwright.chromium.launch(
            headless=headless,
        )
    )


    _context = (
        _browser.new_context()
    )


    _active_page = None


    return _browser


# ---------------------------------------------------------------------------
# Browser
# ---------------------------------------------------------------------------

def get_browser():
    """
    Returns the active browser, launching it if necessary.
    """

    if (
        _browser is None
        or not _browser.is_connected()
    ):

        start_browser(
            headless=False
        )


    return _browser


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

def get_browser_context():
    """
    Returns the active browser context.
    """

    global _context


    get_browser()


    if _context is None:

        raise RuntimeError(
            "Browser context is unavailable."
        )


    return _context


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def get_pages():
    """
    Returns all open tabs/pages.
    """

    context = (
        get_browser_context()
    )


    return [
        page
        for page
        in context.pages
        if not page.is_closed()
    ]


# ---------------------------------------------------------------------------
# Active Page
# ---------------------------------------------------------------------------

def set_active_page(
    page: Page,
):
    """
    Marks a page as E.V.I.E.'s active browser page.
    """

    global _active_page


    if page.is_closed():

        raise RuntimeError(
            "Cannot activate a closed page."
        )


    _active_page = page


    try:

        page.bring_to_front()

    except Exception:

        pass


    return page


def get_active_page():
    """
    Returns E.V.I.E.'s currently tracked page.

    Falls back to the newest open page.
    """

    global _active_page


    if (
        _active_page is not None
        and not _active_page.is_closed()
    ):

        return _active_page


    pages = (
        get_pages()
    )


    if pages:

        _active_page = (
            pages[-1]
        )

        return _active_page


    context = (
        get_browser_context()
    )


    _active_page = (
        context.new_page()
    )


    return _active_page


# ---------------------------------------------------------------------------
# Page by Index
# ---------------------------------------------------------------------------

def get_page_by_index(
    tab_index: int,
):
    """
    Returns a 1-based tab index.
    """

    pages = (
        get_pages()
    )


    tab_index = int(
        tab_index
    )


    if (
        tab_index < 1
        or tab_index > len(pages)
    ):

        raise IndexError(
            (
                "Invalid browser tab index: "
                f"{tab_index}"
            )
        )


    return pages[
        tab_index - 1
    ]


# ---------------------------------------------------------------------------
# New Tab
# ---------------------------------------------------------------------------

def new_page(
    url: str | None = None,
):
    """
    Opens a new browser tab.
    """

    context = (
        get_browser_context()
    )


    page = (
        context.new_page()
    )


    set_active_page(
        page
    )


    if url:

        navigate(
            url,
            page=page,
        )


    return page


# ---------------------------------------------------------------------------
# Activate Tab
# ---------------------------------------------------------------------------

def activate_tab(
    tab_index: int,
):
    """
    Activates an existing browser tab.
    """

    page = (
        get_page_by_index(
            tab_index
        )
    )


    set_active_page(
        page
    )


    return page


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def navigate(
    url: str,
    page: Page | None = None,
):
    """
    Navigates the active or supplied page.
    """

    url = validate_url(
        url
    )


    if page is None:

        page = (
            get_active_page()
        )


    set_active_page(
        page
    )


    response = page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30_000,
    )


    return {
        "url":
            page.url,

        "title":
            safe_title(
                page
            ),

        "status":
            (
                response.status
                if response
                else None
            ),
    }


# ---------------------------------------------------------------------------
# Back
# ---------------------------------------------------------------------------

def go_back():
    """
    Navigates backward in the active tab.
    """

    page = (
        get_active_page()
    )


    response = page.go_back(
        wait_until="domcontentloaded",
        timeout=30_000,
    )


    return {
        "url":
            page.url,

        "title":
            safe_title(
                page
            ),

        "status":
            (
                response.status
                if response
                else None
            ),
    }


# ---------------------------------------------------------------------------
# Forward
# ---------------------------------------------------------------------------

def go_forward():
    """
    Navigates forward in the active tab.
    """

    page = (
        get_active_page()
    )


    response = page.go_forward(
        wait_until="domcontentloaded",
        timeout=30_000,
    )


    return {
        "url":
            page.url,

        "title":
            safe_title(
                page
            ),

        "status":
            (
                response.status
                if response
                else None
            ),
    }


# ---------------------------------------------------------------------------
# Reload
# ---------------------------------------------------------------------------

def reload_page():
    """
    Reloads the active browser tab.
    """

    page = (
        get_active_page()
    )


    response = page.reload(
        wait_until="domcontentloaded",
        timeout=30_000,
    )


    return {
        "url":
            page.url,

        "title":
            safe_title(
                page
            ),

        "status":
            (
                response.status
                if response
                else None
            ),
    }


# ---------------------------------------------------------------------------
# Close Tab
# ---------------------------------------------------------------------------

def close_tab(
    tab_index: int | None = None,
):
    """
    Closes a tab.

    Defaults to the active tab.
    """

    global _active_page


    pages = (
        get_pages()
    )


    if not pages:

        return {
            "closed":
                False,

            "remaining_tabs":
                0,
        }


    if tab_index is None:

        page = (
            get_active_page()
        )

    else:

        page = (
            get_page_by_index(
                tab_index
            )
        )


    page.close()


    if (
        _active_page is page
    ):

        _active_page = None


    remaining = (
        get_pages()
    )


    if remaining:

        set_active_page(
            remaining[-1]
        )


    return {
        "closed":
            True,

        "remaining_tabs":
            len(
                remaining
            ),
    }


# ---------------------------------------------------------------------------
# Safe Title
# ---------------------------------------------------------------------------

def safe_title(
    page: Page,
):
    try:

        return page.title()

    except Exception:

        return ""


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------

def close_browser():
    """
    Closes the managed browser and Playwright runtime.
    """

    global _playwright
    global _browser
    global _context
    global _active_page


    if _context is not None:

        try:

            _context.close()

        except Exception:

            pass


    if _browser is not None:

        try:

            _browser.close()

        except Exception:

            pass


    if _playwright is not None:

        try:

            _playwright.stop()

        except Exception:

            pass


    _active_page = None

    _context = None

    _browser = None

    _playwright = None


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Browser Session"
    )

    print(
        "-------------------------"
    )


    start_browser(
        headless=False
    )


    first = new_page(
        "https://example.com"
    )


    print(
        "First:",
        safe_title(first),
        first.url,
    )


    second = new_page(
        "https://playwright.dev"
    )


    print(
        "Second:",
        safe_title(second),
        second.url,
    )


    print(
        "Tabs:",
        len(
            get_pages()
        ),
    )


    navigate(
        "https://www.python.org"
    )


    print(
        "Navigate:",
        get_active_page().url,
    )


    go_back()

    print(
        "Back:",
        get_active_page().url,
    )


    go_forward()

    print(
        "Forward:",
        get_active_page().url,
    )


    reload_page()

    print(
        "Reload:",
        get_active_page().url,
    )


    close_tab()

    print(
        "Remaining tabs:",
        len(
            get_pages()
        ),
    )


    input(
        "\nPress Enter to close..."
    )


    close_browser()