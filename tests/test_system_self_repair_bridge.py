from assistant.system.self_repair_bridge import (
    build_repair_request,
    execute_repair_bridge,
    render_repair_prompt,
    validate_repair_request,
)


def test_known_component_builds_bounded_request():
    request = (
        build_repair_request(
            "computer.control",
            issue=
                "Fullscreen action failed.",
        )
    )

    assert request.found is True
    assert request.phase == 13
    assert request.risk == "high"
    assert "assistant/computer/" in request.allowed_paths


def test_unknown_component_fails_closed():
    request = (
        build_repair_request(
            "invented.component",
            issue=
                "broken",
        )
    )

    valid, problems = (
        validate_repair_request(
            request
        )
    )

    assert valid is False
    assert problems


def test_repair_requires_approval():
    request = (
        build_repair_request(
            "memory.database",
            issue=
                "SQLite failure",
        )
    )

    result = (
        execute_repair_bridge(
            request
        )
    )

    assert result.success is False
    assert result.status == "APPROVAL_REQUIRED"


def test_approved_request_without_executor_fails_safe():
    request = (
        build_repair_request(
            "memory.database",
            issue=
                "SQLite failure",
            approved=
                True,
        )
    )

    result = (
        execute_repair_bridge(
            request
        )
    )

    assert result.success is False
    assert result.status == "EXECUTOR_REQUIRED"


def test_approved_request_dispatches_to_executor():
    request = (
        build_repair_request(
            "memory.database",
            issue=
                "SQLite failure",
            approved=
                True,
        )
    )

    calls = []


    def executor(
        repair_request,
        prompt,
    ):
        calls.append(
            (
                repair_request,
                prompt,
            )
        )

        return {
            "status":
                "accepted"
        }


    result = (
        execute_repair_bridge(
            request,
            executor=
                executor,
        )
    )

    assert result.success is True
    assert result.status == "DISPATCHED"
    assert calls
    assert "ALLOWED REPAIR PATHS" in calls[0][1]


def test_rendered_prompt_contains_safety_rules():
    request = (
        build_repair_request(
            "voice.tts",
            issue=
                "TTS regression",
        )
    )

    prompt = (
        render_repair_prompt(
            request
        )
    )

    assert "Do not modify files outside" in prompt
    assert "complete regression suite" in prompt
    assert "Do not commit automatically" in prompt
