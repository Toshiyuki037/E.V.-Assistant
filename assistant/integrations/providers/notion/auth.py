"""
E.V.I.E. - Notion Authentication / Configuration

Phase 9

Reads the Notion token from:

    runtime/integrations/notion/config.json

Expected format:

    {
        "account_id": "primary",
        "token": "ntn_..."
    }
"""

from __future__ import annotations

import json

from pathlib import Path


PROVIDER = "notion"

DEFAULT_ACCOUNT_ID = "primary"


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[4]
)


NOTION_CONFIG_PATH = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
    / "notion"
    / "config.json"
)


def load_notion_config():

    if not NOTION_CONFIG_PATH.exists():

        raise RuntimeError(
            (
                "Notion configuration file was not found: "
                f"{NOTION_CONFIG_PATH}"
            )
        )


    try:

        config = json.loads(
            NOTION_CONFIG_PATH.read_text(
                encoding="utf-8"
            )
        )


    except json.JSONDecodeError as error:

        raise RuntimeError(
            (
                "Notion config.json contains invalid JSON: "
                f"{error}"
            )
        ) from error


    if not isinstance(
        config,
        dict,
    ):

        raise RuntimeError(
            "Notion config.json must contain a JSON object."
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


    token = (
        str(
            config.get(
                "token",
                "",
            )
        )
        .strip()
    )


    if not token:

        raise RuntimeError(
            "Notion token is missing from config.json."
        )


    return {
        "account_id":
            account_id,

        "token":
            token,
    }


def get_notion_token(
    account_id: str = DEFAULT_ACCOUNT_ID,
):

    config = (
        load_notion_config()
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
                "Requested Notion account does not match "
                "the configured account: "
                f"{account_id}"
            )
        )


    return config[
        "token"
    ]