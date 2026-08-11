"""
E.V.I.E. - Integration Permissions

Phase 9 introduces data sensitivity in addition to Phase 6 action risk.

Action Risk:
    How dangerous is the action itself?

Data Sensitivity:
    How private is the information being accessed?
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)


# ---------------------------------------------------------------------------
# Sensitivity Levels
# ---------------------------------------------------------------------------

SENSITIVITY_PUBLIC = "public"

SENSITIVITY_PERSONAL = "personal"

SENSITIVITY_PRIVATE = "private"

SENSITIVITY_SENSITIVE = "sensitive"

SENSITIVITY_FINANCIAL = "financial"


# ---------------------------------------------------------------------------
# Integration Permission
# ---------------------------------------------------------------------------

@dataclass(
    frozen=True
)
class IntegrationPermission:
    capability: str

    risk: str

    sensitivity: str

    description: str


# ---------------------------------------------------------------------------
# Default Capability Policies
# ---------------------------------------------------------------------------

DEFAULT_PERMISSIONS = {

    # -----------------------------------------------------------------------
    # Calendar
    # -----------------------------------------------------------------------

    "calendar.read":
        IntegrationPermission(
            capability=
                "calendar.read",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Read calendar events.",
        ),


    "calendar.create":
        IntegrationPermission(
            capability=
                "calendar.create",

            risk=
                "medium",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Create calendar events.",
        ),


    "calendar.write":
        IntegrationPermission(
            capability=
                "calendar.write",

            risk=
                "medium",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Create or modify calendar events.",
        ),


    # -----------------------------------------------------------------------
    # Email
    # -----------------------------------------------------------------------

    "email.read":
        IntegrationPermission(
            capability=
                "email.read",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read email messages.",
        ),


    "email.search":
        IntegrationPermission(
            capability=
                "email.search",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Search email messages.",
        ),


    "email.send":
        IntegrationPermission(
            capability=
                "email.send",

            risk=
                "high",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Send an email message.",
        ),


    # -----------------------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------------------

    "tasks.read":
        IntegrationPermission(
            capability=
                "tasks.read",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Read tasks.",
        ),


    "tasks.create":
        IntegrationPermission(
            capability=
                "tasks.create",

            risk=
                "medium",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Create a task.",
        ),


    "tasks.complete":
        IntegrationPermission(
            capability=
                "tasks.complete",

            risk=
                "medium",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Mark a task complete.",
        ),


    # -----------------------------------------------------------------------
    # Messages
    # -----------------------------------------------------------------------

    "messages.read":
        IntegrationPermission(
            capability=
                "messages.read",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read personal messages.",
        ),


    "messages.send":
        IntegrationPermission(
            capability=
                "messages.send",

            risk=
                "high",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Send a personal message.",
        ),


    # -----------------------------------------------------------------------
    # Location
    # -----------------------------------------------------------------------

    "location.read":
        IntegrationPermission(
            capability=
                "location.read",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_SENSITIVE,

            description=
                "Read device or approved location data.",
        ),


    # -----------------------------------------------------------------------
    # Finance
    # -----------------------------------------------------------------------

    "finance.read":
        IntegrationPermission(
            capability=
                "finance.read",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read portfolio and financial account data.",
        ),


    "finance.account_numbers":
        IntegrationPermission(
            capability=
                "finance.account_numbers",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read financial account identifiers.",
        ),


    "finance.accounts":
        IntegrationPermission(
            capability=
                "finance.accounts",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read financial accounts.",
        ),


    "finance.account":
        IntegrationPermission(
            capability=
                "finance.account",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read one financial account.",
        ),


    "finance.balances":
        IntegrationPermission(
            capability=
                "finance.balances",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read financial account balances.",
        ),


    "finance.positions":
        IntegrationPermission(
            capability=
                "finance.positions",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read investment positions.",
        ),


    "finance.performance":
        IntegrationPermission(
            capability=
                "finance.performance",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read and calculate portfolio performance.",
        ),


    "finance.orders":
        IntegrationPermission(
            capability=
                "finance.orders",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read existing investment orders.",
        ),


    "finance.transactions":
        IntegrationPermission(
            capability=
                "finance.transactions",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_FINANCIAL,

            description=
                "Read financial transaction history.",
        ),


    # -----------------------------------------------------------------------
    # Market Data
    # -----------------------------------------------------------------------

    "market.quote":
        IntegrationPermission(
            capability=
                "market.quote",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PUBLIC,

            description=
                "Read a market quote.",
        ),


    "market.quotes":
        IntegrationPermission(
            capability=
                "market.quotes",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PUBLIC,

            description=
                "Read market quotes.",
        ),


    "market.history":
        IntegrationPermission(
            capability=
                "market.history",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PUBLIC,

            description=
                "Read historical market data.",
        ),

    # -----------------------------------------------------------------------
    # Weather
    # -----------------------------------------------------------------------

    "weather.location":
        IntegrationPermission(
            capability=
                "weather.location",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PUBLIC,

            description=
                "Resolve a public weather location.",
        ),


    "weather.current":
        IntegrationPermission(
            capability=
                "weather.current",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PUBLIC,

            description=
                "Read current public weather conditions.",
        ),


    "weather.forecast":
        IntegrationPermission(
            capability=
                "weather.forecast",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PUBLIC,

            description=
                "Read a public multi-day weather forecast.",
        ),


    "weather.hourly":
        IntegrationPermission(
            capability=
                "weather.hourly",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PUBLIC,

            description=
                "Read a public hourly weather forecast.",
        ),

    # -----------------------------------------------------------------------
    # GitHub
    # -----------------------------------------------------------------------

    "github.profile":
        IntegrationPermission(
            capability=
                "github.profile",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Read the authenticated GitHub profile.",
        ),


    "github.repos":
        IntegrationPermission(
            capability=
                "github.repos",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read GitHub repositories.",
        ),


    "github.repo":
        IntegrationPermission(
            capability=
                "github.repo",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read one GitHub repository.",
        ),


    "github.commits":
        IntegrationPermission(
            capability=
                "github.commits",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read GitHub commits.",
        ),


    "github.issues":
        IntegrationPermission(
            capability=
                "github.issues",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read GitHub issues.",
        ),


    "github.pulls":
        IntegrationPermission(
            capability=
                "github.pulls",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read GitHub pull requests.",
        ),


    "github.notifications":
        IntegrationPermission(
            capability=
                "github.notifications",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read GitHub notifications.",
        ),


    "github.workflows":
        IntegrationPermission(
            capability=
                "github.workflows",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read GitHub Actions workflows.",
        ),


    "github.actions":
        IntegrationPermission(
            capability=
                "github.actions",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read GitHub Actions workflow runs.",
        ),

    # -----------------------------------------------------------------------
    # Notion
    # -----------------------------------------------------------------------

    "notion.search":
        IntegrationPermission(
            capability="notion.search",
            risk="low",
            sensitivity=SENSITIVITY_PRIVATE,
            description="Search Notion content.",
        ),

    "notion.page":
        IntegrationPermission(
            capability="notion.page",
            risk="low",
            sensitivity=SENSITIVITY_PRIVATE,
            description="Read Notion page metadata.",
        ),

    "notion.page_content":
        IntegrationPermission(
            capability="notion.page_content",
            risk="low",
            sensitivity=SENSITIVITY_PRIVATE,
            description="Read Notion page content.",
        ),

    "notion.block_children":
        IntegrationPermission(
            capability="notion.block_children",
            risk="low",
            sensitivity=SENSITIVITY_PRIVATE,
            description="Read Notion child blocks.",
        ),

    "notion.data_source":
        IntegrationPermission(
            capability="notion.data_source",
            risk="low",
            sensitivity=SENSITIVITY_PRIVATE,
            description="Read a Notion data source.",
        ),

    "notion.data_source_query":
        IntegrationPermission(
            capability="notion.data_source_query",
            risk="low",
            sensitivity=SENSITIVITY_PRIVATE,
            description="Query a Notion data source.",
        ),

        "notion.read_document":
        IntegrationPermission(
            capability=
                "notion.read_document",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Read a Notion page or named section.",
        ),


    "notion.document":
        IntegrationPermission(
            capability=
                "notion.document",

            risk=
                "medium",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Append documentation to a Notion page or section.",
        ),


    "notion.block_update":
        IntegrationPermission(
            capability=
                "notion.block_update",

            risk=
                "medium",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Edit text in an existing Notion block.",
        ),


    "notion.block_delete":
        IntegrationPermission(
            capability=
                "notion.block_delete",

            risk=
                "high",

            sensitivity=
                SENSITIVITY_PRIVATE,

            description=
                "Delete an existing Notion block.",
        ),

        
    # -----------------------------------------------------------------------
    # Media
    # -----------------------------------------------------------------------

    "media.read":
        IntegrationPermission(
            capability=
                "media.read",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Read media playback state.",
        ),


    "media.control":
        IntegrationPermission(
            capability=
                "media.control",

            risk=
                "low",

            sensitivity=
                SENSITIVITY_PERSONAL,

            description=
                "Control media playback.",
        ),
}


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

def get_permission(
    capability: str,
):
    return DEFAULT_PERMISSIONS.get(
        capability
    )