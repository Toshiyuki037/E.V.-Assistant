"""
E.V.I.E. - Notion Provider Registration

Phase 9

Capabilities:
    notion.search
    notion.page
    notion.page_content
    notion.block_children
    notion.data_source
    notion.data_source_query

    notion.read_document
    notion.document
    notion.block_update
    notion.block_delete

Safety:
    Reads:
        low risk

    Writes / updates:
        medium risk
        explicit approval required

    Deletes:
        high risk
        explicit approval required
"""

from __future__ import annotations

from assistant.integrations.registry import (
    register_integration_capability,
)

from .data_sources import (
    notion_data_source,
    notion_data_source_query,
)

from .document import (
    notion_delete_block,
    notion_document,
    notion_read_document,
    notion_update_text_block,
)

from .pages import (
    notion_block_children,
    notion_page,
    notion_page_content,
)

from .search import (
    notion_search,
)


# ---------------------------------------------------------------------------
# Provider Loader
# ---------------------------------------------------------------------------

def load_notion_provider():

    # -----------------------------------------------------------------------
    # Search
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.search",

        function=
            notion_search,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Searches pages and data sources shared "
            "with the connected Notion integration."
        ),
    )


    # -----------------------------------------------------------------------
    # Page Metadata
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.page",

        function=
            notion_page,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Reads Notion page metadata "
            "and properties."
        ),
    )


    # -----------------------------------------------------------------------
    # Page Content
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.page_content",

        function=
            notion_page_content,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Reads first-level content blocks "
            "from a Notion page."
        ),
    )


    # -----------------------------------------------------------------------
    # Block Children
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.block_children",

        function=
            notion_block_children,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Reads child blocks from a Notion block."
        ),
    )


    # -----------------------------------------------------------------------
    # Data Source
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.data_source",

        function=
            notion_data_source,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Reads a Notion data source schema."
        ),
    )


    # -----------------------------------------------------------------------
    # Data Source Query
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.data_source_query",

        function=
            notion_data_source_query,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Queries rows from a Notion data source."
        ),
    )


    # -----------------------------------------------------------------------
    # High-Level Document Read
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.read_document",

        function=
            notion_read_document,

        risk=
            "low",

        sensitivity=
            "private",

        description=(
            "Finds and reads a Notion page by title "
            "or a named section inside that page."
        ),
    )


    # -----------------------------------------------------------------------
    # High-Level Document Write
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.document",

        function=
            notion_document,

        risk=
            "medium",

        sensitivity=
            "private",

        description=(
            "Appends documentation to a Notion page "
            "or named section, creating the section "
            "when necessary."
        ),
    )


    # -----------------------------------------------------------------------
    # Block Update
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.block_update",

        function=
            notion_update_text_block,

        risk=
            "medium",

        sensitivity=
            "private",

        description=(
            "Updates text inside an existing "
            "Notion block."
        ),
    )


    # -----------------------------------------------------------------------
    # Block Delete
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "notion",

        name=
            "notion.block_delete",

        function=
            notion_delete_block,

        risk=
            "high",

        sensitivity=
            "private",

        description=(
            "Deletes an existing Notion block."
        ),
    )