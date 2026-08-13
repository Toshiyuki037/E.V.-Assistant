from assistant.system.repair_scope import (
    build_repair_scope,
)


def test_build_known_repair_scope():
    scope = (
        build_repair_scope(
            "memory.database"
        )
    )

    assert scope.found is True
    assert scope.phase == 2
    assert "assistant/memory/" in scope.allowed_paths


def test_high_risk_scope_remains_high_risk():
    scope = (
        build_repair_scope(
            "computer.control"
        )
    )

    assert scope.found is True
    assert scope.risk == "high"


def test_unknown_scope_fails_closed():
    scope = (
        build_repair_scope(
            "invented.component"
        )
    )

    assert scope.found is False
    assert scope.allowed_paths == ()
