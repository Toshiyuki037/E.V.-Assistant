"""
E.V.I.E. - Research Planning

Phase 12G

Deterministic planning helpers built from structured project state.
These are intentionally model-free so they can be used in workflows
and background protocols.
"""

from __future__ import annotations

from .controller import (
    summarize_project,
)


def build_research_status(
    project_id: str,
):
    summary = summarize_project(
        project_id
    )

    return {
        "project_id":
            project_id,

        "open_hypotheses":
            summary[
                "open_hypotheses"
            ],

        "active_experiments":
            summary[
                "active_experiments"
            ],

        "latest_results":
            summary[
                "latest_results"
            ],

        "counts":
            summary[
                "counts"
            ],
    }


def next_research_actions(
    project_id: str,
):
    status = build_research_status(
        project_id
    )

    actions = []

    if status[
        "open_hypotheses"
    ]:
        actions.append(
            (
                "Review evidence for open hypotheses "
                "and identify the highest-information experiment."
            )
        )

    if status[
        "active_experiments"
    ]:
        actions.append(
            (
                "Review active experiments and record any "
                "new measurements or results."
            )
        )

    if not status[
        "latest_results"
    ]:
        actions.append(
            (
                "Prioritize completing or designing an experiment "
                "that produces a measurable result."
            )
        )

    if not actions:
        actions.append(
            (
                "Review the project timeline and define the next "
                "research question."
            )
        )

    return actions
