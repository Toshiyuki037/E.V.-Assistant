"""
E.V.I.E. - Browser Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides safe browser navigation capabilities.

Security:
    Only HTTP and HTTPS URLs are accepted.

    file:, javascript:, data:, shell:, and other protocols are blocked.

Current Tool:
    - open_url
"""

import webbrowser
from urllib.parse import urlparse

from .registry import (
    register_tool,
)


# ---------------------------------------------------------------------------
# URL Validation
# ---------------------------------------------------------------------------

def validate_url(
    url: str,
):
    url = (
        url.strip()
    )

    if not url:

        raise ValueError(
            "URL cannot be empty."
        )

    parsed = urlparse(
        url
    )

    if parsed.scheme.lower() not in {
        "http",
        "https",
    }:

        raise PermissionError(
            (
                "Only HTTP and HTTPS URLs "
                "may be opened."
            )
        )

    if not parsed.netloc:

        raise ValueError(
            "URL must contain a valid host."
        )

    return url


# ---------------------------------------------------------------------------
# Open URL
# ---------------------------------------------------------------------------

def open_url(
    url: str,
):
    validated = (
        validate_url(
            url
        )
    )

    opened = webbrowser.open(
        validated,
        new=2,
    )

    return {
        "url":
            validated,

        "opened":
            bool(
                opened
            ),
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name="open_url",
    description=(
        "Opens an HTTP or HTTPS URL in "
        "the default browser."
    ),
    category="browser",
    risk="low",
    function=open_url,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Browser Tools"
    )

    print(
        "-----------------------"
    )

    safe = (
        "https://example.com"
    )

    print(
        "Safe URL:",
        validate_url(
            safe
        ),
    )

    print()

    try:

        validate_url(
            "file:///C:/Windows/System32"
        )

    except Exception as error:

        print(
            "Blocked URL test:"
        )

        print(
            error
        )