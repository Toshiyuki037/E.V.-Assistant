"""
E.V.I.E. - Browser Research

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Provides live-web search and research extraction for E.V.I.E.

Phase:
    Phase 8 - Browser Intelligence & Control

Capabilities:
    - multi-provider web search
    - search challenge detection
    - Bing search-result extraction
    - DuckDuckGo fallback
    - Bing redirect decoding
    - DuckDuckGo redirect decoding
    - canonical result URLs
    - page/source extraction
    - source metadata
    - research-oriented link extraction

Architecture:
    This module provides browser research primitives.

    Phase 7 remains responsible for:
        - deciding what to research
        - choosing sources
        - opening multiple sources
        - follow-up searches
        - comparison
        - final synthesis

Security:
    All browser functions exposed to the reasoning system still pass
    through Phase 6 registered tools.

Most Recent Change:
    Added canonical URL extraction so Bing tracking redirects are
    converted into the actual destination URLs before being returned
    to E.V.I.E.
"""

from __future__ import annotations

import base64

from urllib.parse import (
    parse_qs,
    quote_plus,
    unquote,
    urljoin,
    urlparse,
)

from .context import (
    get_page_links,
    get_visible_text,
)

from .session import (
    get_active_page,
    navigate,
    safe_title,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_RESULTS = 10

SEARCH_RENDER_WAIT_MS = 1200


# ---------------------------------------------------------------------------
# Search Providers
# ---------------------------------------------------------------------------

SEARCH_PROVIDERS = (
    {
        "name":
            "bing",

        "url":
            (
                "https://www.bing.com/"
                "search?q={query}"
            ),
    },

    {
        "name":
            "duckduckgo",

        "url":
            (
                "https://html.duckduckgo.com/"
                "html/?q={query}"
            ),
    },
)


# ---------------------------------------------------------------------------
# Search Block Detection
# ---------------------------------------------------------------------------

BLOCK_MARKERS = (
    "unusual traffic",
    "automated queries",
    "verify you are human",
    "verify you're human",
    "captcha",
    "our systems have detected",
    "why did this happen",
)


def page_is_blocked(
    page,
):
    """
    Detects obvious search-provider anti-automation pages.
    """

    title = (
        safe_title(
            page
        )
        .lower()
    )


    url = (
        page.url
        .lower()
    )


    try:

        text = (
            get_visible_text(
                page,
                max_characters=5000,
            )
            .lower()
        )

    except Exception:

        text = ""


    if (
        "/sorry/"
        in url
    ):

        return True


    combined = (
        title
        + "\n"
        + url
        + "\n"
        + text
    )


    return any(
        marker in combined
        for marker
        in BLOCK_MARKERS
    )


# ---------------------------------------------------------------------------
# HTTP URL Validation
# ---------------------------------------------------------------------------

def is_http_url(
    url: str,
):
    """
    Returns True only for normal HTTP/HTTPS URLs.
    """

    if not url:

        return False


    try:

        parsed = urlparse(
            url
        )

    except Exception:

        return False


    return (
        parsed.scheme
        in {
            "http",
            "https",
        }
        and bool(
            parsed.netloc
        )
    )


# ---------------------------------------------------------------------------
# Absolute URL
# ---------------------------------------------------------------------------

def normalize_href(
    base_url: str,
    href: str,
):
    """
    Converts relative URLs into absolute URLs.
    """

    if not href:

        return ""


    href = (
        str(
            href
        )
        .strip()
    )


    try:

        return urljoin(
            base_url,
            href,
        )

    except Exception:

        return href


# ---------------------------------------------------------------------------
# Base64 Padding
# ---------------------------------------------------------------------------

def add_base64_padding(
    value: str,
):
    """
    Adds missing Base64 padding characters.
    """

    remainder = (
        len(value)
        % 4
    )


    if remainder:

        value += (
            "="
            * (
                4
                - remainder
            )
        )


    return value


# ---------------------------------------------------------------------------
# Bing Redirect Decoder
# ---------------------------------------------------------------------------

def decode_bing_redirect(
    url: str,
):
    """
    Attempts to decode Bing's tracking redirect.

    Bing frequently returns URLs such as:

        https://www.bing.com/ck/a?...&u=a1aHR0cHM6Ly9...

    The `u` parameter commonly contains:

        a1 + base64(destination_url)

    This function extracts and decodes the real destination.
    """

    try:

        parsed = urlparse(
            url
        )

    except Exception:

        return url


    host = (
        parsed.netloc
        .lower()
    )


    if (
        "bing.com"
        not in host
    ):

        return url


    query = parse_qs(
        parsed.query
    )


    values = (
        query.get(
            "u"
        )
        or []
    )


    if not values:

        return url


    encoded = (
        values[0]
    )


    try:

        encoded = unquote(
            encoded
        )

    except Exception:

        pass


    # Bing commonly prefixes base64 destinations with "a1".

    if encoded.startswith(
        "a1"
    ):

        encoded = (
            encoded[
                2:
            ]
        )


    encoded = add_base64_padding(
        encoded
    )


    try:

        decoded_bytes = (
            base64.urlsafe_b64decode(
                encoded.encode(
                    "ascii"
                )
            )
        )


        decoded = (
            decoded_bytes.decode(
                "utf-8"
            )
            .strip()
        )


    except Exception:

        return url


    if is_http_url(
        decoded
    ):

        return decoded


    return url


# ---------------------------------------------------------------------------
# DuckDuckGo Redirect Decoder
# ---------------------------------------------------------------------------

def decode_duckduckgo_redirect(
    url: str,
):
    """
    Extracts the destination from DuckDuckGo redirect URLs.
    """

    try:

        parsed = urlparse(
            url
        )

    except Exception:

        return url


    host = (
        parsed.netloc
        .lower()
    )


    if (
        "duckduckgo.com"
        not in host
    ):

        return url


    query = parse_qs(
        parsed.query
    )


    values = (
        query.get(
            "uddg"
        )
        or []
    )


    if not values:

        return url


    try:

        candidate = unquote(
            values[0]
        )

    except Exception:

        candidate = (
            values[0]
        )


    if is_http_url(
        candidate
    ):

        return candidate


    return url


# ---------------------------------------------------------------------------
# Result URL Cleanup
# ---------------------------------------------------------------------------

def clean_result_url(
    url: str,
):
    """
    Converts search-engine tracking URLs to canonical destinations.
    """

    if not url:

        return ""


    cleaned = decode_bing_redirect(
        url
    )


    if cleaned != url:

        return cleaned


    cleaned = (
        decode_duckduckgo_redirect(
            url
        )
    )


    return cleaned


# ---------------------------------------------------------------------------
# Result Filtering
# ---------------------------------------------------------------------------

def result_is_useful(
    url: str,
):
    """
    Rejects obvious search-provider internal/navigation links.
    """

    if not is_http_url(
        url
    ):

        return False


    try:

        parsed = urlparse(
            url
        )

    except Exception:

        return False


    host = (
        parsed.netloc
        .lower()
    )


    path = (
        parsed.path
        .lower()
    )


    # -----------------------------------------------------------------------
    # Bing Internal Pages
    # -----------------------------------------------------------------------

    if (
        "bing.com"
        in host
    ):

        if path.startswith(
            "/search"
        ):

            return False


        if path.startswith(
            "/ck/"
        ):

            # A Bing tracking URL that failed decoding should not be
            # treated as a canonical research source.

            return False


    # -----------------------------------------------------------------------
    # Google Internal Pages
    # -----------------------------------------------------------------------

    if (
        "google.com"
        in host
    ):

        if (
            path.startswith(
                "/search"
            )
            or path.startswith(
                "/sorry"
            )
        ):

            return False


    # -----------------------------------------------------------------------
    # DuckDuckGo Internal Pages
    # -----------------------------------------------------------------------

    if (
        "duckduckgo.com"
        in host
    ):

        if (
            path == "/"
            or path.startswith(
                "/html"
            )
        ):

            return False


    return True


# ---------------------------------------------------------------------------
# Bing Extraction
# ---------------------------------------------------------------------------

def extract_bing_results(
    page,
    limit: int,
):
    """
    Extracts organic Bing results.
    """

    results = []

    seen = set()


    locator = page.locator(
        "li.b_algo h2 a"
    )


    try:

        count = locator.count()

    except Exception:

        count = 0


    for index in range(
        count
    ):

        item = (
            locator.nth(
                index
            )
        )


        try:

            title = (
                item.inner_text(
                    timeout=2000
                )
                .strip()
            )


            href = (
                item.get_attribute(
                    "href"
                )
                or ""
            )


        except Exception:

            continue


        href = normalize_href(
            page.url,
            href,
        )


        href = clean_result_url(
            href
        )


        if not title:

            continue


        if not result_is_useful(
            href
        ):

            continue


        if href in seen:

            continue


        seen.add(
            href
        )


        results.append(
            {
                "title":
                    title[
                        :500
                    ],

                "url":
                    href,
            }
        )


        if (
            len(results)
            >= limit
        ):

            break


    return results


# ---------------------------------------------------------------------------
# DuckDuckGo Extraction
# ---------------------------------------------------------------------------

def extract_duckduckgo_results(
    page,
    limit: int,
):
    """
    Extracts results from DuckDuckGo's HTML endpoint.
    """

    results = []

    seen = set()


    locator = page.locator(
        "a.result__a"
    )


    try:

        count = locator.count()

    except Exception:

        count = 0


    for index in range(
        count
    ):

        item = (
            locator.nth(
                index
            )
        )


        try:

            title = (
                item.inner_text(
                    timeout=2000
                )
                .strip()
            )


            href = (
                item.get_attribute(
                    "href"
                )
                or ""
            )


        except Exception:

            continue


        href = normalize_href(
            page.url,
            href,
        )


        href = clean_result_url(
            href
        )


        if not title:

            continue


        if not result_is_useful(
            href
        ):

            continue


        if href in seen:

            continue


        seen.add(
            href
        )


        results.append(
            {
                "title":
                    title[
                        :500
                    ],

                "url":
                    href,
            }
        )


        if (
            len(results)
            >= limit
        ):

            break


    return results


# ---------------------------------------------------------------------------
# Generic Extraction
# ---------------------------------------------------------------------------

def extract_generic_results(
    page,
    limit: int,
):
    """
    Generic extraction fallback.

    Used if a search provider changes its normal result selectors.
    """

    raw_links = (
        get_page_links(
            page,
            limit=250,
        )
    )


    results = []

    seen = set()


    for link in raw_links:

        title = (
            link.get(
                "text",
                ""
            )
            .strip()
        )


        href = (
            link.get(
                "href",
                ""
            )
        )


        href = normalize_href(
            page.url,
            href,
        )


        href = clean_result_url(
            href
        )


        if not title:

            continue


        if len(title) < 3:

            continue


        if not result_is_useful(
            href
        ):

            continue


        if href in seen:

            continue


        seen.add(
            href
        )


        results.append(
            {
                "title":
                    title[
                        :500
                    ],

                "url":
                    href,
            }
        )


        if (
            len(results)
            >= limit
        ):

            break


    return results


# ---------------------------------------------------------------------------
# Provider Extraction
# ---------------------------------------------------------------------------

def extract_provider_results(
    provider_name: str,
    page,
    limit: int,
):
    """
    Runs provider-specific extraction first.
    """

    if (
        provider_name
        == "bing"
    ):

        results = (
            extract_bing_results(
                page,
                limit,
            )
        )


    elif (
        provider_name
        == "duckduckgo"
    ):

        results = (
            extract_duckduckgo_results(
                page,
                limit,
            )
        )


    else:

        results = []


    if results:

        return results


    return extract_generic_results(
        page,
        limit,
    )


# ---------------------------------------------------------------------------
# Search Provider
# ---------------------------------------------------------------------------

def search_provider(
    provider: dict,
    query: str,
    limit: int,
):
    """
    Searches one configured provider.
    """

    encoded_query = quote_plus(
        query
    )


    url = (
        provider[
            "url"
        ]
        .format(
            query=encoded_query
        )
    )


    navigate(
        url
    )


    page = (
        get_active_page()
    )


    page.wait_for_timeout(
        SEARCH_RENDER_WAIT_MS
    )


    blocked = (
        page_is_blocked(
            page
        )
    )


    if blocked:

        return {
            "success":
                False,

            "provider":
                provider[
                    "name"
                ],

            "blocked":
                True,

            "url":
                page.url,

            "title":
                safe_title(
                    page
                ),

            "results":
                [],
        }


    results = (
        extract_provider_results(
            provider[
                "name"
            ],
            page,
            limit,
        )
    )


    return {
        "success":
            bool(
                results
            ),

        "provider":
            provider[
                "name"
            ],

        "blocked":
            False,

        "url":
            page.url,

        "title":
            safe_title(
                page
            ),

        "results":
            results,
    }


# ---------------------------------------------------------------------------
# Search Web
# ---------------------------------------------------------------------------

def search_web(
    query: str,
    limit: int = MAX_RESULTS,
):
    """
    Searches the live web.

    Providers are attempted in order until usable results are returned.
    """

    query = (
        str(
            query
        )
        .strip()
    )


    if not query:

        raise ValueError(
            "Search query cannot be empty."
        )


    limit = int(
        limit
    )


    if limit < 1:

        raise ValueError(
            (
                "Search result limit "
                "must be at least 1."
            )
        )


    if limit > 25:

        limit = 25


    attempts = []


    for provider in SEARCH_PROVIDERS:

        attempt = (
            search_provider(
                provider,
                query,
                limit,
            )
        )


        attempts.append(
            {
                "provider":
                    attempt[
                        "provider"
                    ],

                "blocked":
                    attempt[
                        "blocked"
                    ],

                "success":
                    attempt[
                        "success"
                    ],

                "url":
                    attempt[
                        "url"
                    ],
            }
        )


        if (
            attempt[
                "success"
            ]
            and attempt[
                "results"
            ]
        ):

            return {
                "query":
                    query,

                "provider":
                    attempt[
                        "provider"
                    ],

                "search_url":
                    attempt[
                        "url"
                    ],

                "title":
                    attempt[
                        "title"
                    ],

                "results":
                    attempt[
                        "results"
                    ],

                "attempts":
                    attempts,
            }


    active_page = (
        get_active_page()
    )


    return {
        "query":
            query,

        "provider":
            None,

        "search_url":
            active_page.url,

        "title":
            safe_title(
                active_page
            ),

        "results":
            [],

        "attempts":
            attempts,

        "error":
            (
                "No search provider returned "
                "usable results."
            ),
    }


# ---------------------------------------------------------------------------
# Read Current Source
# ---------------------------------------------------------------------------

def read_current_source(
    max_characters: int = 25_000,
    link_limit: int = 40,
):
    """
    Extracts the active browser page as a research source.
    """

    page = (
        get_active_page()
    )


    links = (
        get_page_links(
            page,
            limit=link_limit,
        )
    )


    normalized_links = []


    seen = set()


    for link in links:

        href = (
            link.get(
                "href",
                ""
            )
        )


        href = normalize_href(
            page.url,
            href,
        )


        href = clean_result_url(
            href
        )


        if not is_http_url(
            href
        ):

            continue


        if href in seen:

            continue


        seen.add(
            href
        )


        normalized_links.append(
            {
                "text":
                    link.get(
                        "text",
                        ""
                    ),

                "url":
                    href,
            }
        )


    return {
        "title":
            safe_title(
                page
            ),

        "url":
            page.url,

        "text":
            get_visible_text(
                page,
                max_characters=
                    max_characters,
            ),

        "links":
            normalized_links,
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
        start_browser,
    )


    print(
        "E.V.I.E. Browser Research"
    )

    print(
        "--------------------------"
    )


    start_browser(
        headless=False
    )


    result = search_web(
        (
            "Playwright Python "
            "browser automation"
        ),
        limit=5,
    )


    pprint(
        result
    )


    input(
        "\nPress Enter to close..."
    )


    close_browser()