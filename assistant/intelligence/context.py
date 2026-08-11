"""
E.V.I.E. - Short-Term Conversation State

Phase 10B

Purpose:
    Stores temporary conversational/tool context for the current
    E.V.I.E. runtime session.

This is intentionally separate from Phase 2 long-term memory.

Examples:

    User:
        What's the weather in Honolulu?

    State:
        provider = weather
        capability = weather.current
        location = Honolulu

    User:
        What about tomorrow?

    The planner can inherit Honolulu from this temporary state.

State is updated only after a successfully verified tool execution.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import (
    asdict,
    dataclass,
    field,
)

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import json
from typing import Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONTEXT_TTL_MINUTES = 30


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class ConversationState:
    last_tool: str = ""

    last_provider: str = ""

    last_capability: str = ""

    last_account_id: str = ""

    last_routing_mode: str = ""

    last_arguments: dict = field(
        default_factory=dict
    )

    active_entities: dict = field(
        default_factory=dict
    )

    active_document: str = ""

    active_section: str = ""

    active_repo: str = ""

    active_location: str = ""

    active_symbol: str = ""

    last_user_request: str = ""

    updated_at: str = ""


_STATE = ConversationState()


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

def _utc_now():
    return datetime.now(
        timezone.utc
    )


def _parse_time(
    value: str,
):
    if not value:

        return None

    try:

        return datetime.fromisoformat(
            value
        )

    except ValueError:

        return None


# ---------------------------------------------------------------------------
# Expiration
# ---------------------------------------------------------------------------

def state_is_expired():
    updated = (
        _parse_time(
            _STATE.updated_at
        )
    )


    if updated is None:

        return True


    age = (
        _utc_now()
        - updated
    )


    return (
        age
        > timedelta(
            minutes=
                CONTEXT_TTL_MINUTES
        )
    )


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def clear_conversation_state():
    global _STATE

    _STATE = ConversationState()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_conversation_state():
    if state_is_expired():

        clear_conversation_state()


    return deepcopy(
        _STATE
    )


def conversation_state_to_dict():
    state = (
        get_conversation_state()
    )


    return asdict(
        state
    )


# ---------------------------------------------------------------------------
# Integration Argument Extraction
# ---------------------------------------------------------------------------

def _extract_integration_context(
    arguments: dict,
):
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


    account_id = (
        str(
            arguments.get(
                "account_id",
                "",
            )
            or ""
        )
        .strip()
    )


    routing_mode = (
        str(
            arguments.get(
                "routing_mode",
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
            {},
        )
        or {}
    )


    if not isinstance(
        nested,
        dict,
    ):

        nested = {}


    return {
        "provider":
            provider,

        "capability":
            capability,

        "account_id":
            account_id,

        "routing_mode":
            routing_mode,

        "arguments":
            deepcopy(
                nested
            ),
    }


# ---------------------------------------------------------------------------
# Entity Extraction
# ---------------------------------------------------------------------------

def _extract_entities(
    arguments: dict,
):
    entities = {}


    supported_keys = (
        "location",
        "repo",
        "owner",
        "page_title",
        "page_id",
        "section",
        "symbol",
        "symbols",
        "query",
        "days",
        "hours",
        "period",
        "date",
        "start_date",
        "end_date",
        "device_id",
    )


    for key in supported_keys:

        if (
            key in arguments
            and arguments[
                key
            ] is not None
        ):

            entities[
                key
            ] = deepcopy(
                arguments[
                    key
                ]
            )


    return entities


# ---------------------------------------------------------------------------
# Record Successful Tool Context
# ---------------------------------------------------------------------------

def record_tool_context(
    tool_name: str,
    arguments: dict | None = None,
    user_request: str = "",
):
    """
    Records context from a successfully verified tool execution.

    IMPORTANT:
        Call this only after verification.successful is True.
    """

    global _STATE


    arguments = (
        dict(
            arguments
            or {}
        )
    )


    state = (
        get_conversation_state()
    )


    state.last_tool = (
        str(
            tool_name
            or ""
        )
        .strip()
        .lower()
    )


    state.last_user_request = (
        str(
            user_request
            or ""
        )
        .strip()
    )


    # -----------------------------------------------------------------------
    # Phase 9 Integration
    # -----------------------------------------------------------------------

    if (
        state.last_tool
        == "integration_execute"
    ):

        integration = (
            _extract_integration_context(
                arguments
            )
        )


        state.last_provider = (
            integration[
                "provider"
            ]
        )


        state.last_capability = (
            integration[
                "capability"
            ]
        )


        state.last_account_id = (
            integration[
                "account_id"
            ]
        )


        state.last_routing_mode = (
            integration[
                "routing_mode"
            ]
        )


        state.last_arguments = (
            integration[
                "arguments"
            ]
        )


        entities = (
            _extract_entities(
                state.last_arguments
            )
        )


        # Merge rather than discard useful active context.
        state.active_entities.update(
            entities
        )


        # ---------------------------------------------------------------
        # Named Active Context
        # ---------------------------------------------------------------

        if entities.get(
            "page_title"
        ):

            state.active_document = (
                str(
                    entities[
                        "page_title"
                    ]
                )
            )


        if entities.get(
            "section"
        ):

            state.active_section = (
                str(
                    entities[
                        "section"
                    ]
                )
            )


        if entities.get(
            "repo"
        ):

            state.active_repo = (
                str(
                    entities[
                        "repo"
                    ]
                )
            )


        if entities.get(
            "location"
        ):

            state.active_location = (
                str(
                    entities[
                        "location"
                    ]
                )
            )


        if entities.get(
            "symbol"
        ):

            state.active_symbol = (
                str(
                    entities[
                        "symbol"
                    ]
                )
            )


    # -----------------------------------------------------------------------
    # Normal Phase 6 Tool
    # -----------------------------------------------------------------------

    else:

        state.last_arguments = (
            deepcopy(
                arguments
            )
        )


        state.active_entities.update(
            _extract_entities(
                arguments
            )
        )


    state.updated_at = (
        _utc_now()
        .isoformat()
    )


    _STATE = state


    return get_conversation_state()


# ---------------------------------------------------------------------------
# Planner Context
# ---------------------------------------------------------------------------

def get_planner_conversation_context():
    """
    Returns temporary context in a planner-friendly structure.
    """

    state = (
        get_conversation_state()
    )


    if not state.updated_at:

        return {}


    return {
        "last_tool":
            state.last_tool,

        "last_provider":
            state.last_provider,

        "last_capability":
            state.last_capability,

        "last_account_id":
            state.last_account_id,

        "last_routing_mode":
            state.last_routing_mode,

        "last_arguments":
            deepcopy(
                state.last_arguments
            ),

        "active_entities":
            deepcopy(
                state.active_entities
            ),

        "active_document":
            state.active_document,

        "active_section":
            state.active_section,

        "active_repo":
            state.active_repo,

        "active_location":
            state.active_location,

        "active_symbol":
            state.active_symbol,

        "last_user_request":
            state.last_user_request,

        "updated_at":
            state.updated_at,
    }


def format_planner_conversation_context():
    context = (
        get_planner_conversation_context()
    )


    if not context:

        return (
            "[no active Phase 10 "
            "conversation state]"
        )


    return json.dumps(
        context,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


# ---------------------------------------------------------------------------
# Follow-Up Detection
# ---------------------------------------------------------------------------

def looks_like_contextual_followup(
    user_message: str,
):
    """
    Conservative gate for messages that may depend on current
    short-term conversation state.
    """

    if not user_message:

        return False


    if not (
        get_planner_conversation_context()
    ):

        return False


    text = (
        str(
            user_message
        )
        .strip()
        .lower()
    )


    phrases = (
        "what about ",
        "how about ",
        "and tomorrow",
        "what about tomorrow",
        "how about tomorrow",
        "what about today",
        "what about this week",
        "what about next week",
        "do that again",
        "do it again",
        "run that again",
        "check again",
        "try again",
        "the same one",
        "same one",
        "that one",
        "that repo",
        "that repository",
        "that page",
        "that document",
        "that section",
        "under it",
        "under that",
        "add that",
        "add it",
        "read that",
        "read it",
        "use the other account",
        "use my other account",
        "what about there",
        "how about there",
    )


    if any(
        phrase in text
        for phrase
        in phrases
    ):

        return True


    short_references = {
        "tomorrow",
        "today",
        "again",
        "there",
        "that one",
        "the other one",
    }


    return (
        text
        in short_references
    )


# ---------------------------------------------------------------------------
# Standalone Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    clear_conversation_state()


    record_tool_context(
        tool_name=
            "integration_execute",

        arguments={
            "capability":
                "weather.current",

            "provider":
                "weather",

            "account_id":
                "public",

            "routing_mode":
                "explicit_account",

            "arguments": {
                "location":
                    "Honolulu"
            },
        },

        user_request=
            "What's the weather in Honolulu?",
    )


    print(
        format_planner_conversation_context()
    )


    print()


    print(
        "Follow-up:",
        looks_like_contextual_followup(
            "What about tomorrow?"
        ),
    )