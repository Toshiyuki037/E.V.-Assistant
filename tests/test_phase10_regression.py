"""
E.V.I.E. - Phase 10 Regression Tests

Purpose:
Locks down Phase 10 unified command intelligence without requiring
live APIs, OpenAI calls, or connected-service network access.

Covers:
- capability aliases
- fail-closed unknown capabilities
- short-term conversation state
- contextual follow-ups
- entity replacement
- global input normalization
- explicit preferences
- shared integration argument preparation
"""

import json

import pytest

from assistant.intelligence.aliases import (
    normalize_capability,
)

from assistant.intelligence.context import (
    clear_conversation_state,
    get_planner_conversation_context,
    looks_like_contextual_followup,
    record_tool_context,
)

from assistant.intelligence.integration_runtime import (
    prepare_integration_arguments,
    prepare_tool_arguments,
)

from assistant.intelligence.normalize import (
    input_was_normalized,
    normalize_user_input,
)

from assistant.intelligence.preferences import (
    apply_integration_preferences,
    clear_default_provider_account,
    clear_default_weather_location,
    get_default_provider_account,
    get_default_weather_location,
    handle_preference_command,
    load_preferences,
    set_default_provider_account,
    set_default_weather_location,
)

from assistant.intelligence.resolver import (
    resolve_contextual_request,
)

import assistant.intelligence.preferences as preferences_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_phase10_state(
    tmp_path,
    monkeypatch,
):
    """
    Isolates conversation state and preference storage for every test.
    """

    clear_conversation_state()

    runtime_dir = (
        tmp_path
        / "runtime"
        / "intelligence"
    )

    preferences_file = (
        runtime_dir
        / "preferences.json"
    )

    monkeypatch.setattr(
        preferences_module,
        "RUNTIME_DIRECTORY",
        runtime_dir,
    )

    monkeypatch.setattr(
        preferences_module,
        "PREFERENCES_FILE",
        preferences_file,
    )

    yield

    clear_conversation_state()


# ---------------------------------------------------------------------------
# Phase 10A - Capability Normalization
# ---------------------------------------------------------------------------

def test_github_legacy_alias_normalizes():
    assert (
        normalize_capability(
            "repos.read"
        )
        == "github.repos"
    )


def test_finance_alias_normalizes():
    assert (
        normalize_capability(
            "portfolio"
        )
        == "finance.performance"
    )


def test_weather_alias_normalizes():
    assert (
        normalize_capability(
            "forecast"
        )
        == "weather.forecast"
    )


def test_notion_alias_normalizes():
    assert (
        normalize_capability(
            "notion.document.read"
        )
        == "notion.read_document"
    )


def test_unknown_capability_is_preserved_fail_closed():
    assert (
        normalize_capability(
            "finance.trade"
        )
        == "finance.trade"
    )

    assert (
        normalize_capability(
            "github.repo.delete"
        )
        == "github.repo.delete"
    )


# ---------------------------------------------------------------------------
# Phase 10B - Conversation State
# ---------------------------------------------------------------------------

def test_weather_context_is_recorded():
    record_tool_context(
        "integration_execute",
        {
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
                    "Honolulu",
            },
        },
        "What is the weather in Honolulu?",
    )

    context = (
        get_planner_conversation_context()
    )

    assert context[
        "last_provider"
    ] == "weather"

    assert context[
        "last_capability"
    ] == "weather.current"

    assert context[
        "active_location"
    ] == "Honolulu"


def test_contextual_followup_detected():
    record_tool_context(
        "integration_execute",
        {
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
                    "Honolulu",
            },
        },
        "What is the weather in Honolulu?",
    )

    assert (
        looks_like_contextual_followup(
            "What about tomorrow?"
        )
        is True
    )


def test_unrelated_message_is_not_contextual_followup():
    record_tool_context(
        "integration_execute",
        {
            "capability":
                "weather.current",
            "provider":
                "weather",
            "arguments": {
                "location":
                    "Honolulu",
            },
        },
        "What is the weather in Honolulu?",
    )

    assert (
        looks_like_contextual_followup(
            "Explain neural networks."
        )
        is False
    )


# ---------------------------------------------------------------------------
# Phase 10C - Contextual Resolution
# ---------------------------------------------------------------------------

def test_weather_location_replacement():
    record_tool_context(
        "integration_execute",
        {
            "capability":
                "weather.forecast",
            "provider":
                "weather",
            "account_id":
                "public",
            "routing_mode":
                "explicit_account",
            "arguments": {
                "location":
                    "Honolulu",
                "days":
                    7,
            },
        },
        "What is the forecast for Honolulu?",
    )

    resolved = (
        resolve_contextual_request(
            "What about Corvallis?"
        )
    )

    assert resolved[
        "capability"
    ] == "weather.forecast"

    assert resolved[
        "arguments"
    ][
        "location"
    ] == "Corvallis"

    assert resolved[
        "arguments"
    ][
        "days"
    ] == 7


def test_weather_tomorrow_changes_capability():
    record_tool_context(
        "integration_execute",
        {
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
                    "Honolulu",
            },
        },
        "What is the weather in Honolulu?",
    )

    resolved = (
        resolve_contextual_request(
            "What about tomorrow?"
        )
    )

    assert resolved[
        "capability"
    ] == "weather.forecast"

    assert resolved[
        "arguments"
    ][
        "location"
    ] == "Honolulu"

    assert resolved[
        "arguments"
    ][
        "days"
    ] == 2


def test_github_operation_changes_but_repo_is_preserved():
    record_tool_context(
        "integration_execute",
        {
            "capability":
                "github.commits",
            "provider":
                "github",
            "account_id":
                "primary",
            "routing_mode":
                "explicit_account",
            "arguments": {
                "repo":
                    "E.V.-Assistant",
            },
        },
        "Show my latest commits.",
    )

    resolved = (
        resolve_contextual_request(
            "What about issues?"
        )
    )

    assert resolved[
        "capability"
    ] == "github.issues"

    assert resolved[
        "arguments"
    ][
        "repo"
    ] == "E.V.-Assistant"


def test_notion_section_changes_but_page_is_preserved():
    record_tool_context(
        "integration_execute",
        {
            "capability":
                "notion.read_document",
            "provider":
                "notion",
            "account_id":
                "primary",
            "routing_mode":
                "explicit_account",
            "arguments": {
                "page_title":
                    "Documentation",
            },
        },
        "Read my Documentation page.",
    )

    resolved = (
        resolve_contextual_request(
            "What about Phase 8?"
        )
    )

    assert resolved[
        "capability"
    ] == "notion.read_document"

    assert resolved[
        "arguments"
    ][
        "page_title"
    ] == "Documentation"

    assert resolved[
        "arguments"
    ][
        "section"
    ] == "Phase 8"


def test_finance_symbol_replacement():
    record_tool_context(
        "integration_execute",
        {
            "capability":
                "market.quote",
            "provider":
                "schwab",
            "account_id":
                "primary",
            "routing_mode":
                "explicit_account",
            "arguments": {
                "symbol":
                    "TSLA",
            },
        },
        "What is Tesla trading at?",
    )

    resolved = (
        resolve_contextual_request(
            "What about Nvidia?"
        )
    )

    assert resolved[
        "capability"
    ] == "market.quote"

    assert resolved[
        "arguments"
    ][
        "symbol"
    ] == "NVDA"


# ---------------------------------------------------------------------------
# Phase 10D - Input Normalization
# ---------------------------------------------------------------------------

def test_followup_typo_normalizes():
    assert (
        normalize_user_input(
            "hat about Corvallis?"
        )
        == "what about Corvallis?"
    )


def test_common_service_typo_normalizes():
    assert (
        normalize_user_input(
            "show my git hub repos"
        )
        == "show my github repos"
    )


def test_weather_typo_normalizes():
    assert (
        normalize_user_input(
            "whats the wheather in Honolulu"
        )
        == "whats the weather in Honolulu"
    )


def test_normalization_change_detection():
    assert (
        input_was_normalized(
            "what abut Nvidia?"
        )
        is True
    )

    assert (
        input_was_normalized(
            "What about Nvidia?"
        )
        is False
    )


def test_project_entity_is_not_broadly_spell_corrected():
    assert (
        normalize_user_input(
            "FPGA-NN-MODELING"
        )
        == "FPGA-NN-MODELING"
    )

    assert (
        normalize_user_input(
            "E.V.-Assistant"
        )
        == "E.V.-Assistant"
    )


# ---------------------------------------------------------------------------
# Phase 10E - Preferences
# ---------------------------------------------------------------------------

def test_default_weather_location_round_trip():
    set_default_weather_location(
        "Honolulu"
    )

    assert (
        get_default_weather_location()
        == "Honolulu"
    )


def test_default_weather_location_can_be_cleared():
    set_default_weather_location(
        "Honolulu"
    )

    assert (
        clear_default_weather_location()
        is True
    )

    assert (
        get_default_weather_location()
        == ""
    )


def test_weather_preference_command():
    response = (
        handle_preference_command(
            "Set my default weather location to Corvallis."
        )
    )

    assert response == (
        "Default weather location "
        "set to Corvallis."
    )

    assert (
        get_default_weather_location()
        == "Corvallis"
    )


def test_provider_account_round_trip():
    set_default_provider_account(
        "github",
        "primary",
    )

    assert (
        get_default_provider_account(
            "github"
        )
        == "primary"
    )

    assert (
        clear_default_provider_account(
            "github"
        )
        is True
    )

    assert (
        get_default_provider_account(
            "github"
        )
        == ""
    )


def test_weather_preference_injection():
    set_default_weather_location(
        "Honolulu"
    )

    prepared = (
        apply_integration_preferences(
            {
                "capability":
                    "weather.current",
                "provider":
                    "weather",
                "account_id":
                    "public",
                "routing_mode":
                    "explicit_account",
            }
        )
    )

    assert prepared[
        "arguments"
    ][
        "location"
    ] == "Honolulu"


def test_explicit_weather_location_beats_preference():
    set_default_weather_location(
        "Honolulu"
    )

    prepared = (
        apply_integration_preferences(
            {
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
                        "Corvallis",
                },
            }
        )
    )

    assert prepared[
        "arguments"
    ][
        "location"
    ] == "Corvallis"


def test_provider_account_preference_injection():
    set_default_provider_account(
        "github",
        "primary",
    )

    prepared = (
        apply_integration_preferences(
            {
                "capability":
                    "github.repos",
                "provider":
                    "github",
            }
        )
    )

    assert prepared[
        "account_id"
    ] == "primary"

    assert prepared[
        "routing_mode"
    ] == "explicit_account"


# ---------------------------------------------------------------------------
# Shared Phase 10 Integration Runtime
# ---------------------------------------------------------------------------

def test_shared_runtime_normalizes_capability():
    prepared = (
        prepare_integration_arguments(
            {
                "capability":
                    "repos.read",
                "provider":
                    "github",
            }
        )
    )

    assert prepared[
        "capability"
    ] == "github.repos"


def test_shared_runtime_applies_weather_preference():
    set_default_weather_location(
        "Honolulu"
    )

    prepared = (
        prepare_integration_arguments(
            {
                "capability":
                    "weather.current",
                "provider":
                    "weather",
                "account_id":
                    "public",
                "routing_mode":
                    "explicit_account",
            }
        )
    )

    assert prepared[
        "arguments"
    ][
        "location"
    ] == "Honolulu"


def test_prepare_tool_arguments_ignores_non_integrations():
    original = {
        "path":
            "assistant/main.py",
    }

    prepared = (
        prepare_tool_arguments(
            "read_file",
            original,
        )
    )

    assert prepared == original


def test_prepare_tool_arguments_handles_integrations():
    set_default_weather_location(
        "Honolulu"
    )

    prepared = (
        prepare_tool_arguments(
            "integration_execute",
            {
                "capability":
                    "weather",
                "provider":
                    "weather",
                "account_id":
                    "public",
                "routing_mode":
                    "explicit_account",
            },
        )
    )

    assert prepared[
        "capability"
    ] == "weather.current"

    assert prepared[
        "arguments"
    ][
        "location"
    ] == "Honolulu"


def test_preferences_file_is_valid_json():
    set_default_weather_location(
        "Honolulu"
    )

    data = json.loads(
        preferences_module
        .PREFERENCES_FILE
        .read_text(
            encoding="utf-8"
        )
    )

    assert data[
        "weather_location"
    ] == "Honolulu"
