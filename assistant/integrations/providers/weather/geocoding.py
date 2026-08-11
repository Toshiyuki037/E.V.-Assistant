"""
E.V.I.E. - Weather Geocoding

Phase 9

Resolves human-readable locations into coordinates.

Important:
    Open-Meteo geocoding uses fuzzy search. E.V.I.E. therefore
    retrieves multiple candidates and ranks them rather than trusting
    the first returned result.
"""

from __future__ import annotations

import re

from .api import (
    geocoding_get,
)


# ---------------------------------------------------------------------------
# US State Names
# ---------------------------------------------------------------------------

US_STATES = {
    "alabama",
    "alaska",
    "arizona",
    "arkansas",
    "california",
    "colorado",
    "connecticut",
    "delaware",
    "florida",
    "georgia",
    "hawaii",
    "idaho",
    "illinois",
    "indiana",
    "iowa",
    "kansas",
    "kentucky",
    "louisiana",
    "maine",
    "maryland",
    "massachusetts",
    "michigan",
    "minnesota",
    "mississippi",
    "missouri",
    "montana",
    "nebraska",
    "nevada",
    "new hampshire",
    "new jersey",
    "new mexico",
    "new york",
    "north carolina",
    "north dakota",
    "ohio",
    "oklahoma",
    "oregon",
    "pennsylvania",
    "rhode island",
    "south carolina",
    "south dakota",
    "tennessee",
    "texas",
    "utah",
    "vermont",
    "virginia",
    "washington",
    "west virginia",
    "wisconsin",
    "wyoming",
}


# ---------------------------------------------------------------------------
# Normalize Text
# ---------------------------------------------------------------------------

def _normalize_text(
    value,
):
    value = str(
        value
        or ""
    ).strip().lower()


    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )


    return " ".join(
        value.split()
    )


# ---------------------------------------------------------------------------
# Parse Location Query
# ---------------------------------------------------------------------------

def _parse_location_query(
    location: str,
):
    """
    Attempts to separate:

        Corvallis, Oregon
        Corvallis Oregon

    into:

        city = Corvallis
        region = Oregon

    without incorrectly chopping ordinary multi-word city names.
    """

    original = (
        str(location)
        .strip()
    )


    if not original:

        raise ValueError(
            "Weather location is required."
        )


    # -----------------------------------------------------------------------
    # Explicit comma form
    # -----------------------------------------------------------------------

    if "," in original:

        parts = [
            part.strip()
            for part
            in original.split(",")
            if part.strip()
        ]


        if len(parts) >= 2:

            return {
                "query":
                    parts[0],

                "region_hint":
                    parts[1],

                "country_code":
                    (
                        "US"
                        if _normalize_text(
                            parts[1]
                        ) in US_STATES
                        else None
                    ),
            }


    # -----------------------------------------------------------------------
    # Detect trailing US state name
    # -----------------------------------------------------------------------

    normalized = (
        _normalize_text(
            original
        )
    )


    for state in sorted(
        US_STATES,
        key=len,
        reverse=True,
    ):

        suffix = (
            " "
            + state
        )


        if normalized.endswith(
            suffix
        ):

            city_length = (
                len(normalized)
                - len(suffix)
            )


            city = (
                normalized[
                    :city_length
                ]
                .strip()
            )


            if city:

                return {
                    "query":
                        city,

                    "region_hint":
                        state,

                    "country_code":
                        "US",
                }


    return {
        "query":
            original,

        "region_hint":
            None,

        "country_code":
            None,
    }


# ---------------------------------------------------------------------------
# Normalize API Result
# ---------------------------------------------------------------------------

def _normalize_result(
    item: dict,
):
    return {
        "id":
            item.get(
                "id"
            ),

        "name":
            item.get(
                "name"
            ),

        "latitude":
            item.get(
                "latitude"
            ),

        "longitude":
            item.get(
                "longitude"
            ),

        "country":
            item.get(
                "country"
            ),

        "country_code":
            item.get(
                "country_code"
            ),

        "admin1":
            item.get(
                "admin1"
            ),

        "admin2":
            item.get(
                "admin2"
            ),

        "timezone":
            item.get(
                "timezone"
            ),

        "population":
            item.get(
                "population",
                0,
            )
            or 0,

        "feature_code":
            item.get(
                "feature_code"
            ),
    }


# ---------------------------------------------------------------------------
# Candidate Score
# ---------------------------------------------------------------------------

def _score_location(
    item: dict,
    query: str,
    region_hint: str | None = None,
):
    score = 0


    query_norm = (
        _normalize_text(
            query
        )
    )


    name_norm = (
        _normalize_text(
            item.get(
                "name"
            )
        )
    )


    admin1_norm = (
        _normalize_text(
            item.get(
                "admin1"
            )
        )
    )


    country_norm = (
        _normalize_text(
            item.get(
                "country"
            )
        )
    )


    region_norm = (
        _normalize_text(
            region_hint
        )
    )


    # -----------------------------------------------------------------------
    # Exact city name is the strongest signal
    # -----------------------------------------------------------------------

    if name_norm == query_norm:

        score += 1000


    elif name_norm.startswith(
        query_norm
    ):

        score += 300


    elif query_norm in name_norm:

        score += 100


    # -----------------------------------------------------------------------
    # Requested state / province
    # -----------------------------------------------------------------------

    if region_norm:

        if admin1_norm == region_norm:

            score += 1000


        elif region_norm in admin1_norm:

            score += 500


    # -----------------------------------------------------------------------
    # Prefer populated places when otherwise tied
    # -----------------------------------------------------------------------

    feature_code = str(
        item.get(
            "feature_code",
            "",
        )
        or ""
    ).upper()


    if feature_code.startswith(
        "PPL"
    ):

        score += 100


    population = int(
        item.get(
            "population",
            0,
        )
        or 0
    )


    # Small tie-breaker only.
    score += min(
        population / 1_000_000,
        50,
    )


    # -----------------------------------------------------------------------
    # US hint
    # -----------------------------------------------------------------------

    if (
        region_norm in US_STATES
        and country_norm
        in {
            "united states",
            "united states of america",
        }
    ):

        score += 200


    return score


# ---------------------------------------------------------------------------
# Search Location
# ---------------------------------------------------------------------------

def weather_location_search(
    account_id: str = "public",
    location: str = "",
    limit: int = 10,
):
    del account_id


    parsed = (
        _parse_location_query(
            location
        )
    )


    query = (
        parsed[
            "query"
        ]
    )


    region_hint = (
        parsed[
            "region_hint"
        ]
    )


    country_code = (
        parsed[
            "country_code"
        ]
    )


    params = {
        "name":
            query,

        # Retrieve several candidates so we can rank them ourselves.
        "count":
            max(
                5,
                min(
                    100,
                    int(limit),
                ),
            ),

        "language":
            "en",

        "format":
            "json",
    }


    if country_code:

        params[
            "countryCode"
        ] = country_code


    result = (
        geocoding_get(
            "/search",
            params=params,
        )
    )


    raw_results = (
        result.get(
            "results",
            [],
        )
        or []
    )


    normalized = [
        _normalize_result(
            item
        )
        for item
        in raw_results
    ]


    ranked = sorted(
        normalized,

        key=lambda item: (
            _score_location(
                item,
                query=query,
                region_hint=region_hint,
            )
        ),

        reverse=True,
    )


    return ranked[
        :max(
            1,
            int(limit),
        )
    ]


# ---------------------------------------------------------------------------
# Resolve Best Location
# ---------------------------------------------------------------------------

def resolve_weather_location(
    location: str,
):
    results = (
        weather_location_search(
            location=location,
            limit=10,
        )
    )


    if not results:

        raise RuntimeError(
            (
                "Could not resolve weather location: "
                f"{location}"
            )
        )


    parsed = (
        _parse_location_query(
            location
        )
    )


    query_norm = (
        _normalize_text(
            parsed[
                "query"
            ]
        )
    )


    region_norm = (
        _normalize_text(
            parsed[
                "region_hint"
            ]
        )
    )


    # -----------------------------------------------------------------------
    # Require a reasonable city match
    # -----------------------------------------------------------------------

    valid = []


    for result in results:

        name_norm = (
            _normalize_text(
                result.get(
                    "name"
                )
            )
        )


        admin1_norm = (
            _normalize_text(
                result.get(
                    "admin1"
                )
            )
        )


        if name_norm != query_norm:

            continue


        if (
            region_norm
            and admin1_norm
            != region_norm
        ):

            continue


        valid.append(
            result
        )


    if valid:

        return valid[0]


    # -----------------------------------------------------------------------
    # Bare city request
    # -----------------------------------------------------------------------

    if not region_norm:

        exact_city = [
            result
            for result
            in results
            if _normalize_text(
                result.get(
                    "name"
                )
            )
            == query_norm
        ]


        if exact_city:

            return exact_city[0]


    raise RuntimeError(
        (
            "Could not confidently resolve weather location: "
            f"{location}"
        )
    )