"""
E.V.I.E. - Notion Data Sources

Phase 9

READ ONLY.

Notion API 2025-09-03+ separates database containers from
data sources. Query operations use data_source_id.
"""

from __future__ import annotations

from .api import (
    notion_get,
    notion_post,
)

from .auth import (
    DEFAULT_ACCOUNT_ID,
)


def _require_data_source_id(
    data_source_id: str,
):

    data_source_id = (
        str(
            data_source_id
        )
        .strip()
    )


    if not data_source_id:

        raise ValueError(
            "Notion data_source_id is required."
        )


    return data_source_id


# ---------------------------------------------------------------------------
# Retrieve Data Source
# ---------------------------------------------------------------------------

def notion_data_source(
    account_id: str = DEFAULT_ACCOUNT_ID,
    data_source_id: str = "",
):

    data_source_id = (
        _require_data_source_id(
            data_source_id
        )
    )


    return notion_get(
        account_id=
            account_id,

        path=(
            f"/data_sources/"
            f"{data_source_id}"
        ),
    )


# ---------------------------------------------------------------------------
# Query Data Source
# ---------------------------------------------------------------------------

def notion_data_source_query(
    account_id: str = DEFAULT_ACCOUNT_ID,
    data_source_id: str = "",
    filter: dict | None = None,
    sorts: list | None = None,
    page_size: int = 100,
    start_cursor: str | None = None,
    result_type: str | None = None,
):

    data_source_id = (
        _require_data_source_id(
            data_source_id
        )
    )


    body = {
        "page_size":
            max(
                1,
                min(
                    100,
                    int(
                        page_size
                    ),
                ),
            ),
    }


    if filter is not None:

        body[
            "filter"
        ] = filter


    if sorts is not None:

        body[
            "sorts"
        ] = sorts


    if start_cursor:

        body[
            "start_cursor"
        ] = start_cursor


    if result_type:

        normalized = (
            str(
                result_type
            )
            .strip()
            .lower()
        )


        if normalized not in {
            "page",
            "data_source",
        }:

            raise ValueError(
                (
                    "result_type must be "
                    "'page' or 'data_source'."
                )
            )


        body[
            "result_type"
        ] = normalized


    return notion_post(
        account_id=
            account_id,

        path=(
            f"/data_sources/"
            f"{data_source_id}"
            "/query"
        ),

        json_body=
            body,
    )