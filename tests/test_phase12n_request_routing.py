"""
Phase 12N request routing tests.
"""

from assistant.coding.request_planner import (
    plan_coding_request,
)


def test_explicit_self_fix_detected():
    result = plan_coding_request(
        (
            "Diagnose and fix the protocol schedule "
            "time display in your own code."
        )
    )

    assert result.handled
    assert result.action == "plan_change"


def test_ordinary_bug_discussion_not_hijacked():
    result = plan_coding_request(
        "Why might timezone formatting bugs happen?"
    )

    assert not result.handled


def test_commit_approval_detected():
    result = plan_coding_request(
        "Approve the commit."
    )

    assert result.handled
    assert result.action == "approve_commit"
