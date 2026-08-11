"""
Phase 12N pending-plan persistence tests.
"""

import assistant.coding.pending as pending_module

from assistant.coding.models import (
    EngineeringEdit,
    EngineeringPlan,
)

from assistant.coding.pending import (
    load_pending_engineering,
    pending_plan_from_payload,
    save_pending_plan,
)


def test_pending_plan_round_trip(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        pending_module,
        "PENDING_FILE",
        tmp_path
        / "pending.json",
    )

    plan = EngineeringPlan(
        goal="Fix display.",
        repository="test",
        planned_paths=[
            "example.py"
        ],
        edits=[
            EngineeringEdit(
                path="example.py",
                content="VALUE = 2\n",
            )
        ],
        targeted_commands=[
            [
                "python",
                "-m",
                "py_compile",
                "example.py",
            ]
        ],
        regression_command=[
            "python",
            "-m",
            "pytest",
            "-q",
        ],
        confidence=95,
    )

    save_pending_plan(
        plan,
        root_path=".",
        candidate_paths=[
            "example.py"
        ],
    )

    payload = load_pending_engineering()

    assert payload[
        "state"
    ] == "awaiting_execution_approval"

    restored = pending_plan_from_payload(
        payload
    )

    assert restored.goal == plan.goal
    assert restored.planned_paths == [
        "example.py"
    ]
    assert restored.edits[
        0
    ].path == "example.py"
