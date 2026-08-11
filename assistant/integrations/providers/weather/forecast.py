"""
E.V.I.E. - Weather Forecast

Phase 9

Provides normalized current, daily, and hourly weather data.
"""

from __future__ import annotations

from .api import (
    forecast_get,
)

from .geocoding import (
    resolve_weather_location,
)


# ---------------------------------------------------------------------------
# Resolve Coordinates
# ---------------------------------------------------------------------------

def _resolve_coordinates(
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    if (
        latitude is not None
        and longitude is not None
    ):

        return {
            "name":
                location or "",

            "latitude":
                float(latitude),

            "longitude":
                float(longitude),

            "country":
                None,

            "admin1":
                None,

            "timezone":
                "auto",
        }


    if not location:

        raise ValueError(
            (
                "Weather request requires either "
                "location or latitude/longitude."
            )
        )


    return resolve_weather_location(
        location
    )


# ---------------------------------------------------------------------------
# Location Label
# ---------------------------------------------------------------------------

def _location_label(
    resolved: dict,
):
    parts = []


    for key in (
        "name",
        "admin1",
        "country",
    ):

        value = resolved.get(
            key
        )


        if (
            value
            and value not in parts
        ):

            parts.append(
                str(value)
            )


    return ", ".join(
        parts
    )


# ---------------------------------------------------------------------------
# Current Weather
# ---------------------------------------------------------------------------

def weather_current(
    account_id: str = "public",
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    del account_id


    resolved = _resolve_coordinates(
        location=location,
        latitude=latitude,
        longitude=longitude,
    )


    result = forecast_get(
        "/forecast",
        params={
            "latitude":
                resolved["latitude"],

            "longitude":
                resolved["longitude"],

            "current":
                (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "relative_humidity_2m,"
                    "precipitation,"
                    "rain,"
                    "showers,"
                    "snowfall,"
                    "weather_code,"
                    "cloud_cover,"
                    "wind_speed_10m,"
                    "wind_direction_10m,"
                    "wind_gusts_10m"
                ),

            "temperature_unit":
                "fahrenheit",

            "wind_speed_unit":
                "mph",

            "precipitation_unit":
                "inch",

            "timezone":
                "auto",
        },
    )


    return {
        "location":
            _location_label(
                resolved
            ),

        "latitude":
            result.get(
                "latitude"
            ),

        "longitude":
            result.get(
                "longitude"
            ),

        "timezone":
            result.get(
                "timezone"
            ),

        "current":
            result.get(
                "current",
                {},
            ),

        "units":
            result.get(
                "current_units",
                {},
            ),
    }


# ---------------------------------------------------------------------------
# Daily Forecast
# ---------------------------------------------------------------------------

def weather_forecast(
    account_id: str = "public",
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    days: int = 7,
):
    del account_id


    resolved = _resolve_coordinates(
        location=location,
        latitude=latitude,
        longitude=longitude,
    )


    days = max(
        1,
        min(
            16,
            int(days),
        ),
    )


    result = forecast_get(
        "/forecast",
        params={
            "latitude":
                resolved["latitude"],

            "longitude":
                resolved["longitude"],

            "daily":
                (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "apparent_temperature_max,"
                    "apparent_temperature_min,"
                    "sunrise,"
                    "sunset,"
                    "precipitation_sum,"
                    "rain_sum,"
                    "showers_sum,"
                    "snowfall_sum,"
                    "precipitation_probability_max,"
                    "wind_speed_10m_max,"
                    "wind_gusts_10m_max"
                ),

            "forecast_days":
                days,

            "temperature_unit":
                "fahrenheit",

            "wind_speed_unit":
                "mph",

            "precipitation_unit":
                "inch",

            "timezone":
                "auto",
        },
    )


    return {
        "location":
            _location_label(
                resolved
            ),

        "latitude":
            result.get(
                "latitude"
            ),

        "longitude":
            result.get(
                "longitude"
            ),

        "timezone":
            result.get(
                "timezone"
            ),

        "daily":
            result.get(
                "daily",
                {},
            ),

        "units":
            result.get(
                "daily_units",
                {},
            ),
    }


# ---------------------------------------------------------------------------
# Hourly Forecast
# ---------------------------------------------------------------------------

def weather_hourly(
    account_id: str = "public",
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    days: int = 2,
):
    del account_id


    resolved = _resolve_coordinates(
        location=location,
        latitude=latitude,
        longitude=longitude,
    )


    days = max(
        1,
        min(
            7,
            int(days),
        ),
    )


    result = forecast_get(
        "/forecast",
        params={
            "latitude":
                resolved["latitude"],

            "longitude":
                resolved["longitude"],

            "hourly":
                (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "relative_humidity_2m,"
                    "precipitation_probability,"
                    "precipitation,"
                    "rain,"
                    "showers,"
                    "snowfall,"
                    "weather_code,"
                    "cloud_cover,"
                    "visibility,"
                    "wind_speed_10m,"
                    "wind_direction_10m,"
                    "wind_gusts_10m"
                ),

            "forecast_days":
                days,

            "temperature_unit":
                "fahrenheit",

            "wind_speed_unit":
                "mph",

            "precipitation_unit":
                "inch",

            "timezone":
                "auto",
        },
    )


    return {
        "location":
            _location_label(
                resolved
            ),

        "latitude":
            result.get(
                "latitude"
            ),

        "longitude":
            result.get(
                "longitude"
            ),

        "timezone":
            result.get(
                "timezone"
            ),

        "hourly":
            result.get(
                "hourly",
                {},
            ),

        "units":
            result.get(
                "hourly_units",
                {},
            ),
    }