"""
E.V.I.E. - Weather Provider Registration

Phase 9

Public read-only weather provider.
"""

from __future__ import annotations

from assistant.integrations.registry import (
    register_integration_capability,
)

from .forecast import (
    weather_current,
    weather_forecast,
    weather_hourly,
)

from .geocoding import (
    weather_location_search,
)


# ---------------------------------------------------------------------------
# Provider Loader
# ---------------------------------------------------------------------------

def load_weather_provider():

    register_integration_capability(
        provider=
            "weather",

        name=
            "weather.location",

        function=
            weather_location_search,

        risk=
            "low",

        sensitivity=
            "public",

        description=(
            "Resolves a place name into weather coordinates."
        ),
    )


    register_integration_capability(
        provider=
            "weather",

        name=
            "weather.current",

        function=
            weather_current,

        risk=
            "low",

        sensitivity=
            "public",

        description=(
            "Reads current weather conditions for a location."
        ),
    )


    register_integration_capability(
        provider=
            "weather",

        name=
            "weather.forecast",

        function=
            weather_forecast,

        risk=
            "low",

        sensitivity=
            "public",

        description=(
            "Reads a multi-day weather forecast for a location."
        ),
    )


    register_integration_capability(
        provider=
            "weather",

        name=
            "weather.hourly",

        function=
            weather_hourly,

        risk=
            "low",

        sensitivity=
            "public",

        description=(
            "Reads an hourly weather forecast for a location."
        ),
    )