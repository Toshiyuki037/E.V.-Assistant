"""
E.V.I.E. - Notion Intelligent Document Operations

Phase 9

Purpose:
    High-level Notion document operations.

Capabilities:
    - find a page by title
    - read a page
    - read a named section
    - append documentation to a page
    - append documentation beneath a named section
    - automatically create a missing section
    - update an existing text block
    - delete an existing block

Safety:
    Risk classification is handled by the Phase 6 executor through
    the registered integration capability.
"""

from __future__ import annotations

from .api import (
    notion_get,
    notion_post,
    notion_request,
)

from .auth import (
    DEFAULT_ACCOUNT_ID,
)


# ---------------------------------------------------------------------------
# Text Helpers
# ---------------------------------------------------------------------------

def _normalize(
    value,
):
    return (
        str(
            value
            or ""
        )
        .strip()
        .lower()
    )


def _rich_text(
    content: str,
):
    return [
        {
            "type":
                "text",

            "text": {
                "content":
                    str(
                        content
                    )
            },
        }
    ]


# ---------------------------------------------------------------------------
# Page Title
# ---------------------------------------------------------------------------

def _page_title(
    page: dict,
):
    properties = (
        page.get(
            "properties",
            {},
        )
        or {}
    )


    for property_value in (
        properties.values()
    ):

        if not isinstance(
            property_value,
            dict,
        ):
            continue


        if (
            property_value.get(
                "type"
            )
            != "title"
        ):
            continue


        title_items = (
            property_value.get(
                "title",
                [],
            )
            or []
        )


        return "".join(
            str(
                item.get(
                    "plain_text",
                    "",
                )
                or ""
            )

            for item
            in title_items
        ).strip()


    return ""


# ---------------------------------------------------------------------------
# Block Plain Text
# ---------------------------------------------------------------------------

def _block_plain_text(
    block: dict,
):
    block_type = (
        block.get(
            "type",
            "",
        )
    )


    block_data = (
        block.get(
            block_type,
            {},
        )
        or {}
    )


    rich_text = (
        block_data.get(
            "rich_text",
            [],
        )
        or []
    )


    return "".join(
        str(
            item.get(
                "plain_text",
                "",
            )
            or ""
        )

        for item
        in rich_text
    ).strip()


# ---------------------------------------------------------------------------
# Find Page
# ---------------------------------------------------------------------------

def find_notion_page(
    account_id: str = DEFAULT_ACCOUNT_ID,
    page_title: str = "",
):
    page_title = (
        str(
            page_title
        )
        .strip()
    )


    if not page_title:

        raise ValueError(
            "Notion page_title is required."
        )


    response = notion_post(
        account_id=
            account_id,

        path=
            "/search",

        json_body={
            "query":
                page_title,

            "filter": {
                "property":
                    "object",

                "value":
                    "page",
            },

            "page_size":
                100,
        },
    )


    pages = (
        response.get(
            "results",
            [],
        )
        or []
    )


    if not pages:

        raise RuntimeError(
            (
                "No Notion page matched: "
                f"{page_title}"
            )
        )


    target = (
        _normalize(
            page_title
        )
    )


    # Prefer exact title matches.
    for page in pages:

        title = (
            _page_title(
                page
            )
        )


        if (
            _normalize(
                title
            )
            == target
        ):

            return page


    # Fall back to the first Notion search result.
    return pages[0]


# ---------------------------------------------------------------------------
# Read All Direct Children
# ---------------------------------------------------------------------------

def get_all_block_children(
    account_id: str,
    block_id: str,
):
    results = []

    cursor = None


    while True:

        params = {
            "page_size":
                100,
        }


        if cursor:

            params[
                "start_cursor"
            ] = cursor


        response = notion_get(
            account_id=
                account_id,

            path=(
                f"/blocks/"
                f"{block_id}"
                "/children"
            ),

            params=
                params,
        )


        results.extend(
            response.get(
                "results",
                [],
            )
            or []
        )


        if not response.get(
            "has_more"
        ):

            break


        cursor = (
            response.get(
                "next_cursor"
            )
        )


        if not cursor:

            break


    return results


# ---------------------------------------------------------------------------
# Heading Helpers
# ---------------------------------------------------------------------------

HEADING_LEVELS = {
    "heading_1":
        1,

    "heading_2":
        2,

    "heading_3":
        3,

    "heading_4":
        4,
}


def find_section_heading(
    account_id: str,
    page_id: str,
    section: str,
):
    target = (
        _normalize(
            section
        )
    )


    blocks = (
        get_all_block_children(
            account_id=
                account_id,

            block_id=
                page_id,
        )
    )


    # First try exact heading text.
    for index, block in enumerate(
        blocks
    ):

        block_type = (
            block.get(
                "type"
            )
        )


        if (
            block_type
            not in HEADING_LEVELS
        ):

            continue


        text = (
            _block_plain_text(
                block
            )
        )


        if (
            _normalize(
                text
            )
            == target
        ):

            return {
                "block":
                    block,

                "index":
                    index,

                "blocks":
                    blocks,
            }


    # Then allow a conservative substring match.
    for index, block in enumerate(
        blocks
    ):

        block_type = (
            block.get(
                "type"
            )
        )


        if (
            block_type
            not in HEADING_LEVELS
        ):

            continue


        text = (
            _normalize(
                _block_plain_text(
                    block
                )
            )
        )


        if (
            target
            and target in text
        ):

            return {
                "block":
                    block,

                "index":
                    index,

                "blocks":
                    blocks,
            }


    return None


# ---------------------------------------------------------------------------
# Read Page / Section
# ---------------------------------------------------------------------------

def notion_read_document(
    account_id: str = DEFAULT_ACCOUNT_ID,
    page_title: str = "",
    section: str | None = None,
):
    page = (
        find_notion_page(
            account_id=
                account_id,

            page_title=
                page_title,
        )
    )


    page_id = (
        page[
            "id"
        ]
    )


    blocks = (
        get_all_block_children(
            account_id=
                account_id,

            block_id=
                page_id,
        )
    )


    # -----------------------------------------------------------------------
    # Entire page
    # -----------------------------------------------------------------------

    if not section:

        return {
            "page_id":
                page_id,

            "page_title":
                _page_title(
                    page
                ),

            "section":
                None,

            "blocks":
                blocks,
        }


    # -----------------------------------------------------------------------
    # Named section
    # -----------------------------------------------------------------------

    section_info = (
        find_section_heading(
            account_id=
                account_id,

            page_id=
                page_id,

            section=
                section,
        )
    )


    if not section_info:

        raise RuntimeError(
            (
                "Could not find Notion section "
                f"'{section}' in page "
                f"'{page_title}'."
            )
        )


    heading = (
        section_info[
            "block"
        ]
    )


    heading_index = (
        section_info[
            "index"
        ]
    )


    all_blocks = (
        section_info[
            "blocks"
        ]
    )


    heading_type = (
        heading.get(
            "type"
        )
    )


    heading_level = (
        HEADING_LEVELS.get(
            heading_type,
            4,
        )
    )


    section_blocks = []


    for block in (
        all_blocks[
            heading_index + 1:
        ]
    ):

        block_type = (
            block.get(
                "type"
            )
        )


        if (
            block_type
            in HEADING_LEVELS
        ):

            level = (
                HEADING_LEVELS[
                    block_type
                ]
            )


            if (
                level
                <= heading_level
            ):

                break


        section_blocks.append(
            block
        )


    return {
        "page_id":
            page_id,

        "page_title":
            _page_title(
                page
            ),

        "section":
            section,

        "heading":
            heading,

        "blocks":
            section_blocks,
    }


# ---------------------------------------------------------------------------
# Append Children
# ---------------------------------------------------------------------------

def _append_children(
    account_id: str,
    parent_id: str,
    children: list,
    position: dict | None = None,
):
    body = {
        "children":
            children,
    }


    if position is not None:

        body[
            "position"
        ] = position


    return notion_request(
        account_id=
            account_id,

        method=
            "PATCH",

        path=(
            f"/blocks/"
            f"{parent_id}"
            "/children"
        ),

        json_body=
            body,
    )


# ---------------------------------------------------------------------------
# Append Paragraph
# ---------------------------------------------------------------------------

def append_paragraph(
    account_id: str,
    parent_id: str,
    content: str,
    position: dict | None = None,
):
    return _append_children(
        account_id=
            account_id,

        parent_id=
            parent_id,

        children=[
            {
                "object":
                    "block",

                "type":
                    "paragraph",

                "paragraph": {
                    "rich_text":
                        _rich_text(
                            content
                        ),
                },
            }
        ],

        position=
            position,
    )


# ---------------------------------------------------------------------------
# Create Heading
# ---------------------------------------------------------------------------

def create_section_heading(
    account_id: str,
    page_id: str,
    section: str,
):
    response = (
        _append_children(
            account_id=
                account_id,

            parent_id=
                page_id,

            children=[
                {
                    "object":
                        "block",

                    "type":
                        "heading_2",

                    "heading_2": {
                        "rich_text":
                            _rich_text(
                                section
                            ),
                    },
                }
            ],

            position={
                "type":
                    "end",
            },
        )
    )


    created_blocks = (
        response.get(
            "results",
            [],
        )
        or []
    )


    if not created_blocks:

        raise RuntimeError(
            (
                "Notion returned no block after "
                f"creating section '{section}'."
            )
        )


    return created_blocks[0]


# ---------------------------------------------------------------------------
# Document / Append
# ---------------------------------------------------------------------------

def notion_document(
    account_id: str = DEFAULT_ACCOUNT_ID,
    page_title: str = "",
    content: str = "",
    section: str | None = None,
):
    page_title = (
        str(
            page_title
        )
        .strip()
    )


    content = (
        str(
            content
        )
        .strip()
    )


    if not page_title:

        raise ValueError(
            "Notion page_title is required."
        )


    if not content:

        raise ValueError(
            "Notion content is required."
        )


    page = (
        find_notion_page(
            account_id=
                account_id,

            page_title=
                page_title,
        )
    )


    page_id = (
        page[
            "id"
        ]
    )


    actual_title = (
        _page_title(
            page
        )
    )


    # -----------------------------------------------------------------------
    # Root-page append
    # -----------------------------------------------------------------------

    if not section:

        result = (
            append_paragraph(
                account_id=
                    account_id,

                parent_id=
                    page_id,

                content=
                    content,

                position={
                    "type":
                        "end",
                },
            )
        )


        return {
            "success":
                True,

            "page_id":
                page_id,

            "page_title":
                actual_title,

            "section":
                None,

            "section_created":
                False,

            "content":
                content,

            "result":
                result,
        }


    section = (
        str(
            section
        )
        .strip()
    )


    # -----------------------------------------------------------------------
    # Locate section
    # -----------------------------------------------------------------------

    section_info = (
        find_section_heading(
            account_id=
                account_id,

            page_id=
                page_id,

            section=
                section,
        )
    )


    section_created = False


    # -----------------------------------------------------------------------
    # Missing section -> create it
    # -----------------------------------------------------------------------

    if not section_info:

        heading = (
            create_section_heading(
                account_id=
                    account_id,

                page_id=
                    page_id,

                section=
                    section,
            )
        )


        section_created = True


    else:

        heading = (
            section_info[
                "block"
            ]
        )


    heading_id = (
        heading[
            "id"
        ]
    )


    # -----------------------------------------------------------------------
    # Insert directly after heading
    # -----------------------------------------------------------------------

    result = (
        append_paragraph(
            account_id=
                account_id,

            parent_id=
                page_id,

            content=
                content,

            position={
                "type":
                    "after_block",

                "after_block": {
                    "id":
                        heading_id,
                },
            },
        )
    )


    return {
        "success":
            True,

        "page_id":
            page_id,

        "page_title":
            actual_title,

        "section":
            section,

        "section_created":
            section_created,

        "content":
            content,

        "result":
            result,
    }


# ---------------------------------------------------------------------------
# Update Existing Text Block
# ---------------------------------------------------------------------------

def notion_update_text_block(
    account_id: str = DEFAULT_ACCOUNT_ID,
    block_id: str = "",
    content: str = "",
):
    block_id = (
        str(
            block_id
        )
        .strip()
    )


    content = (
        str(
            content
        )
        .strip()
    )


    if not block_id:

        raise ValueError(
            "Notion block_id is required."
        )


    if not content:

        raise ValueError(
            "Notion content is required."
        )


    block = notion_get(
        account_id=
            account_id,

        path=(
            f"/blocks/"
            f"{block_id}"
        ),
    )


    block_type = (
        block.get(
            "type"
        )
    )


    editable_types = {
        "paragraph",
        "heading_1",
        "heading_2",
        "heading_3",
        "heading_4",
        "bulleted_list_item",
        "numbered_list_item",
        "quote",
        "to_do",
        "toggle",
        "callout",
    }


    if (
        block_type
        not in editable_types
    ):

        raise RuntimeError(
            (
                "Notion block type cannot be "
                "safely text-edited: "
                f"{block_type}"
            )
        )


    body = {
        block_type: {
            "rich_text":
                _rich_text(
                    content
                )
        }
    }


    # Preserve checkbox state.
    if (
        block_type
        == "to_do"
    ):

        existing_data = (
            block.get(
                "to_do",
                {},
            )
            or {}
        )


        if (
            "checked"
            in existing_data
        ):

            body[
                "to_do"
            ][
                "checked"
            ] = (
                existing_data[
                    "checked"
                ]
            )


    result = notion_request(
        account_id=
            account_id,

        method=
            "PATCH",

        path=(
            f"/blocks/"
            f"{block_id}"
        ),

        json_body=
            body,
    )


    return {
        "success":
            True,

        "block_id":
            block_id,

        "block_type":
            block_type,

        "content":
            content,

        "result":
            result,
    }


# ---------------------------------------------------------------------------
# Delete Existing Block
# ---------------------------------------------------------------------------

def notion_delete_block(
    account_id: str = DEFAULT_ACCOUNT_ID,
    block_id: str = "",
):
    block_id = (
        str(
            block_id
        )
        .strip()
    )


    if not block_id:

        raise ValueError(
            "Notion block_id is required."
        )


    result = notion_request(
        account_id=
            account_id,

        method=
            "DELETE",

        path=(
            f"/blocks/"
            f"{block_id}"
        ),
    )


    return {
        "success":
            True,

        "block_id":
            block_id,

        "result":
            result,
    }