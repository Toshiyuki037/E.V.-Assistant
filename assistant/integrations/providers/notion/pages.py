"""
E.V.I.E. - Notion Pages

Phase 9

READ ONLY.
"""

from __future__ import annotations

from .api import (
    notion_get,
)

from .auth import (
    DEFAULT_ACCOUNT_ID,
)


def _require_id(
    value: str,
    name: str,
):

    value = (
        str(
            value
        )
        .strip()
    )


    if not value:

        raise ValueError(
            f"Notion {name} is required."
        )


    return value


# ---------------------------------------------------------------------------
# Page Metadata
# ---------------------------------------------------------------------------

def notion_page(
    account_id: str = DEFAULT_ACCOUNT_ID,
    page_id: str = "",
):

    page_id = (
        _require_id(
            page_id,
            "page_id",
        )
    )


    return notion_get(
        account_id=
            account_id,

        path=(
            f"/pages/"
            f"{page_id}"
        ),
    )


# ---------------------------------------------------------------------------
# Page Content
# ---------------------------------------------------------------------------

def notion_page_content(
    account_id: str = DEFAULT_ACCOUNT_ID,
    page_id: str = "",
    page_size: int = 100,
):

    page_id = (
        _require_id(
            page_id,
            "page_id",
        )
    )


    return notion_get(
        account_id=
            account_id,

        path=(
            f"/blocks/"
            f"{page_id}"
            "/children"
        ),

        params={
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
        },
    )


# ---------------------------------------------------------------------------
# Arbitrary Block Children
# ---------------------------------------------------------------------------

def notion_block_children(
    account_id: str = DEFAULT_ACCOUNT_ID,
    block_id: str = "",
    page_size: int = 100,
):

    block_id = (
        _require_id(
            block_id,
            "block_id",
        )
    )


    return notion_get(
        account_id=
            account_id,

        path=(
            f"/blocks/"
            f"{block_id}"
            "/children"
        ),

        params={
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
        },
    )