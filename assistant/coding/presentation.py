"""
E.V.I.E. - Self-Engineering Presentation

Phase 12N
"""

from __future__ import annotations


def format_engineering_plan(
    plan,
    *,
    candidate_paths,
):
    lines = [
        "Self-engineering plan ready.",
        f"Goal: {plan.goal}",
        f"Confidence: {plan.confidence}",
        (
            "Impact risk: "
            f"{plan.metadata.get('impact_risk', 'unknown')}"
        ),
        "Candidate files inspected:",
    ]

    for path in candidate_paths:
        lines.append(
            f"- {path}"
        )

    lines.append(
        "Planned files to modify:"
    )

    if plan.planned_paths:
        for path in plan.planned_paths:
            lines.append(
                f"- {path}"
            )
    else:
        lines.append(
            "- none"
        )

    if plan.targeted_commands:
        lines.append(
            "Targeted validation:"
        )

        for command in plan.targeted_commands:
            lines.append(
                "- "
                + " ".join(
                    command
                )
            )

    if plan.regression_command:
        lines.append(
            "Full regression:"
        )
        lines.append(
            "- "
            + " ".join(
                plan.regression_command
            )
        )

    if plan.rationale:
        lines.append(
            "Rationale:"
        )
        lines.append(
            plan.rationale
        )

    if plan.planned_paths:
        lines.append(
            (
                "No files have been changed yet. "
                "Approve execution to let me create a branch, "
                "apply the plan, run validation and full regression, "
                "then stop before commit."
            )
        )

    return "\n".join(
        lines
    )


def format_execution_result(
    result,
):
    status = result.get(
        "status",
        ""
    )

    lines = [
        (
            "Self-engineering status: "
            f"{status}"
        )
    ]

    transaction_id = result.get(
        "transaction_id",
        "",
    )

    if transaction_id:
        lines.append(
            (
                "Transaction: "
                f"{transaction_id}"
            )
        )

    review = result.get(
        "review"
    )

    if isinstance(
        review,
        dict,
    ):
        lines.append(
            "Changed files:"
        )

        for path in (
            review.get(
                "changed_paths",
                []
            )
            or []
        ):
            lines.append(
                f"- {path}"
            )

        lines.append(
            (
                "Targeted tests passed: "
                f"{review.get('targeted_tests_passed')}"
            )
        )

        lines.append(
            (
                "Full regression passed: "
                f"{review.get('regression_passed')}"
            )
        )

        diff = (
            review.get(
                "diff",
                ""
            )
            or ""
        )

        if diff:
            lines.append(
                "Diff:"
            )
            lines.append(
                diff[
                    :12000
                ]
            )

    if status == "awaiting_commit_approval":
        lines.append(
            (
                "The change is validated and waiting for "
                "explicit commit approval."
            )
        )

    return "\n".join(
        lines
    )
