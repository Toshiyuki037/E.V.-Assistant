"""
E.V.I.E. - GitHub Authentication / Configuration

Phase 9

GitHub uses a fine-grained personal access token stored in:

    runtime/integrations/github/config.json

Expected format:

    {
        "account_id": "primary",
        "username": "YOUR_GITHUB_USERNAME",
        "token": "github_pat_..."
    }

The config file MUST be excluded from Git.
"""

from __future__ import annotations

import json

from pathlib import Path


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

PROVIDER = "github"

DEFAULT_ACCOUNT_ID = "primary"


# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[4]
)


GITHUB_CONFIG_PATH = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
    / "github"
    / "config.json"
)


# ---------------------------------------------------------------------------
# Load Configuration
# ---------------------------------------------------------------------------

def load_github_config():
    if not GITHUB_CONFIG_PATH.exists():

        raise RuntimeError(
            (
                "GitHub configuration file was not found: "
                f"{GITHUB_CONFIG_PATH}"
            )
        )


    try:

        config = json.loads(
            GITHUB_CONFIG_PATH.read_text(
                encoding="utf-8"
            )
        )


    except json.JSONDecodeError as error:

        raise RuntimeError(
            (
                "GitHub config.json contains invalid JSON: "
                f"{error}"
            )
        ) from error


    except OSError as error:

        raise RuntimeError(
            (
                "Could not read GitHub config.json: "
                f"{error}"
            )
        ) from error


    if not isinstance(
        config,
        dict,
    ):

        raise RuntimeError(
            (
                "GitHub config.json must contain "
                "a JSON object."
            )
        )


    account_id = (
        str(
            config.get(
                "account_id",
                DEFAULT_ACCOUNT_ID,
            )
        )
        .strip()
        or DEFAULT_ACCOUNT_ID
    )


    username = (
        str(
            config.get(
                "username",
                "",
            )
        )
        .strip()
    )


    token = (
        str(
            config.get(
                "token",
                "",
            )
        )
        .strip()
    )


    if not username:

        raise RuntimeError(
            (
                "GitHub username is missing "
                "from config.json."
            )
        )


    if not token:

        raise RuntimeError(
            (
                "GitHub token is missing "
                "from config.json."
            )
        )


    return {
        "account_id":
            account_id,

        "username":
            username,

        "token":
            token,
    }


# ---------------------------------------------------------------------------
# Configuration State
# ---------------------------------------------------------------------------

def github_configured():
    try:

        load_github_config()

        return True


    except Exception:

        return False


# ---------------------------------------------------------------------------
# Access Token
# ---------------------------------------------------------------------------

def get_github_token(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    config = (
        load_github_config()
    )


    configured_account = (
        str(
            config[
                "account_id"
            ]
        )
        .strip()
        .lower()
    )


    requested_account = (
        str(
            account_id
        )
        .strip()
        .lower()
    )


    if (
        requested_account
        != configured_account
    ):

        raise RuntimeError(
            (
                "Requested GitHub account does "
                "not match configured account: "
                f"{account_id}"
            )
        )


    return config[
        "token"
    ]


# ---------------------------------------------------------------------------
# Username
# ---------------------------------------------------------------------------

def get_github_username():
    return (
        load_github_config()[
            "username"
        ]
    )


# ---------------------------------------------------------------------------
# Standalone Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. GitHub Configuration"
    )

    print(
        "-----------------------------"
    )


    try:

        config = (
            load_github_config()
        )


        print(
            "Configured:",
            True,
        )


        print(
            "Account ID:",
            config[
                "account_id"
            ],
        )


        print(
            "Username:",
            config[
                "username"
            ],
        )


        # Never print the actual token.
        print(
            "Token present:",
            bool(
                config[
                    "token"
                ]
            ),
        )


    except Exception as error:

        print(
            "Configured:",
            False,
        )


        print(
            "Error:",
            str(
                error
            ),
        )