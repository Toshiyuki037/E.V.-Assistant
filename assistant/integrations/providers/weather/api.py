"""
E.V.I.E. - Weather API Client

Phase 9

Public weather-data provider.

No authentication or API key is required.
"""

from __future__ import annotations

import requests


FORECAST_BASE_URL = (
    "https://api.open-meteo.com/v1"
)

GEOCODING_BASE_URL = (
    "https://geocoding-api.open-meteo.com/v1"
)


# ---------------------------------------------------------------------------
# Generic Request
# ---------------------------------------------------------------------------

def weather_get(
    base_url: str,
    path: str,
    params: dict | None = None,
):
    url = (
        base_url.rstrip("/")
        + "/"
        + path.lstrip("/")
    )


    response = requests.get(
        url,
        params=params,
        timeout=30,
    )


    if not response.ok:

        raise RuntimeError(
            (
                "Weather API request failed "
                f"with HTTP {response.status_code}: "
                f"{response.text[:1500]}"
            )
        )


    if not (
        response.content
        or b""
    ).strip():

        return {}


    try:

        return response.json()

    except ValueError:

        raise RuntimeError(
            "Weather API returned invalid JSON."
        )


# ---------------------------------------------------------------------------
# Forecast Request
# ---------------------------------------------------------------------------

def forecast_get(
    path: str,
    params: dict | None = None,
):
    return weather_get(
        base_url=FORECAST_BASE_URL,
        path=path,
        params=params,
    )


# ---------------------------------------------------------------------------
# Geocoding Request
# ---------------------------------------------------------------------------

def geocoding_get(
    path: str,
    params: dict | None = None,
):
    return weather_get(
        base_url=GEOCODING_BASE_URL,
        path=path,
        params=params,
    )