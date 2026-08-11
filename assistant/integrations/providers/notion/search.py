"""
E.V.I.E. - Notion Search

Phase 9

READ ONLY.
"""

from __future__ import annotations

from .api import (
    notion_post,
)

from .auth import (
    DEFAULT_ACCOUNT_ID,
)


def notion_search(
    account_id: str = DEFAULT_ACCOUNT_ID,
    query: str = "",
    object_type: str | None = None,
    page_size: int = 50,
):

    query = (
        str(
            query
        )
        .strip()
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


    if query:

        body[
            "query"
        ] = query


    if object_type:

        normalized_type = (
            str(
                object_type
            )
            .strip()
            .lower()
        )


        if normalized_type not in {
            "page",
            "data_source",
        }:

            raise ValueError(
                (
                    "Notion object_type must be "
                    "'page' or 'data_source'."
                )
            )


        body[
            "filter"
        ] = {
            "property":
                "object",

            "value":
                normalized_type,
        }


    return notion_post(
        account_id=
            account_id,

        path=
            "/search",

        json_body=
            body,
    )