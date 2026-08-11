"""
E.V.I.E. - Explicit User Preferences

Phase 10E

Purpose:
Stores explicitly configured command-routing preferences.

This is separate from:
    - Phase 2 long-term semantic memory
    - Phase 10 short-term conversation state

Preferences are NEVER inferred from recent usage.
"""

from __future__ import annotations

import json

from pathlib import Path


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

RUNTIME_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "intelligence"
)

PREFERENCES_FILE = (
    RUNTIME_DIRECTORY
    / "preferences.json"
)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_PREFERENCES = {
    "weather_location": "",
    "provider_accounts": {},
}


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------

def ensure_runtime_directory():
    RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_preferences():
    ensure_runtime_directory()


    preferences = {
        "weather_location":
            "",

        "provider_accounts":
            {},
    }


    if not PREFERENCES_FILE.exists():

        return preferences


    try:

        data = json.loads(
            PREFERENCES_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return preferences


    if not isinstance(
        data,
        dict,
    ):

        return preferences


    weather_location = (
        data.get(
            "weather_location"
        )
    )


    if isinstance(
        weather_location,
        str,
    ):

        preferences[
            "weather_location"
        ] = weather_location.strip()


    provider_accounts = (
        data.get(
            "provider_accounts"
        )
    )


    if isinstance(
        provider_accounts,
        dict,
    ):

        preferences[
            "provider_accounts"
        ] = {
            str(provider)
            .strip()
            .lower():
                str(account_id)
                .strip()

            for provider, account_id
            in provider_accounts.items()

            if (
                str(provider).strip()
                and str(account_id).strip()
            )
        }


    return preferences


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_preferences(
    preferences: dict,
):
    ensure_runtime_directory()


    PREFERENCES_FILE.write_text(
        json.dumps(
            preferences,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


    return preferences


# ---------------------------------------------------------------------------
# Default Weather Location
# ---------------------------------------------------------------------------

def set_default_weather_location(
    location: str,
):
    location = (
        str(
            location
            or ""
        )
        .strip()
    )


    if not location:

        raise ValueError(
            "Weather location cannot be empty."
        )


    preferences = (
        load_preferences()
    )


    preferences[
        "weather_location"
    ] = location


    save_preferences(
        preferences
    )


    return location


def get_default_weather_location():
    preferences = (
        load_preferences()
    )


    return (
        str(
            preferences.get(
                "weather_location",
                "",
            )
            or ""
        )
        .strip()
    )


def clear_default_weather_location():
    preferences = (
        load_preferences()
    )


    preferences[
        "weather_location"
    ] = ""


    save_preferences(
        preferences
    )


    return True


# ---------------------------------------------------------------------------
# Provider Accounts
# ---------------------------------------------------------------------------

def set_default_provider_account(
    provider: str,
    account_id: str,
):
    provider = (
        str(
            provider
            or ""
        )
        .strip()
        .lower()
    )


    account_id = (
        str(
            account_id
            or ""
        )
        .strip()
    )


    if not provider:

        raise ValueError(
            "Provider cannot be empty."
        )


    if not account_id:

        raise ValueError(
            "Account ID cannot be empty."
        )


    preferences = (
        load_preferences()
    )


    accounts = (
        preferences.setdefault(
            "provider_accounts",
            {},
        )
    )


    accounts[
        provider
    ] = account_id


    save_preferences(
        preferences
    )


    return account_id


def get_default_provider_account(
    provider: str,
):
    provider = (
        str(
            provider
            or ""
        )
        .strip()
        .lower()
    )


    if not provider:

        return ""


    preferences = (
        load_preferences()
    )


    accounts = (
        preferences.get(
            "provider_accounts",
            {}
        )
        or {}
    )


    if not isinstance(
        accounts,
        dict,
    ):

        return ""


    return (
        str(
            accounts.get(
                provider,
                "",
            )
            or ""
        )
        .strip()
    )


def clear_default_provider_account(
    provider: str,
):
    provider = (
        str(
            provider
            or ""
        )
        .strip()
        .lower()
    )


    if not provider:

        return False


    preferences = (
        load_preferences()
    )


    accounts = (
        preferences.setdefault(
            "provider_accounts",
            {},
        )
    )


    if provider not in accounts:

        return False


    del accounts[
        provider
    ]


    save_preferences(
        preferences
    )


    return True


# ---------------------------------------------------------------------------
# Apply Preferences
# ---------------------------------------------------------------------------

def apply_integration_preferences(
    arguments: dict,
):
    """
    Applies explicitly stored preferences.

    Explicit user/planner arguments always win.
    """

    if not isinstance(
        arguments,
        dict,
    ):

        return arguments


    arguments = dict(
        arguments
    )


    provider = (
        str(
            arguments.get(
                "provider",
                "",
            )
            or ""
        )
        .strip()
        .lower()
    )


    capability = (
        str(
            arguments.get(
                "capability",
                "",
            )
            or ""
        )
        .strip()
        .lower()
    )


    nested = (
        arguments.get(
            "arguments",
            {}
        )
        or {}
    )


    if not isinstance(
        nested,
        dict,
    ):

        nested = {}


    nested = dict(
        nested
    )


    # -----------------------------------------------------------------------
    # Weather
    # -----------------------------------------------------------------------

    if (
        provider
        == "weather"
        and capability.startswith(
            "weather."
        )
        and not nested.get(
            "location"
        )
        and not nested.get(
            "latitude"
        )
        and not nested.get(
            "longitude"
        )
    ):

        location = (
            get_default_weather_location()
        )


        if location:

            nested[
                "location"
            ] = location


    # -----------------------------------------------------------------------
    # Provider Account
    # -----------------------------------------------------------------------

    if (
        provider
        and not arguments.get(
            "account_id"
        )
    ):

        account_id = (
            get_default_provider_account(
                provider
            )
        )


        if account_id:

            arguments[
                "account_id"
            ] = account_id

            arguments[
                "routing_mode"
            ] = "explicit_account"


    if nested:

        arguments[
            "arguments"
        ] = nested


    return arguments


# ---------------------------------------------------------------------------
# Explicit Preference Commands
# ---------------------------------------------------------------------------

def handle_preference_command(
    user_message: str,
):
    """
    Deterministically handles explicit preference commands.

    Returns:
        str | None
    """

    text = (
        str(
            user_message
            or ""
        )
        .strip()
    )


    if not text:

        return None


    lowered = (
        text.lower()
    )


    # -----------------------------------------------------------------------
    # Weather Location
    # -----------------------------------------------------------------------

    weather_prefixes = (
        (
            "remember that when i ask for weather, use ",
            "weather",
        ),

        (
            "when i ask for weather, use ",
            "weather",
        ),

        (
            "set my default weather location to ",
            "weather",
        ),

        (
            "change my default weather location to ",
            "weather",
        ),
    )


    for prefix, _ in weather_prefixes:

        if lowered.startswith(
            prefix
        ):

            location = (
                text[
                    len(prefix):
                ]
                .strip()
                .rstrip(".")
            )


            if not location:

                return (
                    "Tell me which weather "
                    "location to use."
                )


            set_default_weather_location(
                location
            )


            return (
                "Default weather location "
                f"set to {location}."
            )


    if lowered in {
        "clear my default weather location",
        "forget my default weather location",
        "remove my default weather location",
    }:

        clear_default_weather_location()


        return (
            "Default weather location cleared."
        )


    # -----------------------------------------------------------------------
    # Provider Account
    # -----------------------------------------------------------------------

    account_prefix = (
        "set my default "
    )


    account_marker = (
        " account to "
    )


    if (
        lowered.startswith(
            account_prefix
        )
        and account_marker
        in lowered
    ):

        body = (
            text[
                len(account_prefix):
            ]
        )


        marker_index = (
            body.lower().find(
                account_marker
            )
        )


        if marker_index > 0:

            provider = (
                body[
                    :marker_index
                ]
                .strip()
                .lower()
            )


            account_id = (
                body[
                    marker_index
                    + len(
                        account_marker
                    ):
                ]
                .strip()
                .rstrip(".")
            )


            if (
                provider
                and account_id
            ):

                set_default_provider_account(
                    provider,
                    account_id,
                )


                return (
                    f"Default {provider} account "
                    f"set to {account_id}."
                )


    return None


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Preferences"
    )

    print(
        "---------------------"
    )


    print(
        load_preferences()
    )