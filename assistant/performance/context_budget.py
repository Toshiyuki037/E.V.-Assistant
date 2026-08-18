from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextBudget:
    conversation_turns: int
    memory_items: int
    project_items: int
    project_characters: int
    mode: str


def context_budget_for_profile(
    profile,
):
    mode = str(
        getattr(
            profile,
            "mode",
            "full",
        )
        or "full"
    ).lower()

    if mode == "fast":
        return ContextBudget(
            3,
            0,
            0,
            0,
            "fast",
        )

    if mode == "project":
        return ContextBudget(
            4,
            0,
            6,
            7000,
            "project",
        )

    if mode in {
        "contextual",
        "important",
    }:
        return ContextBudget(
            6,
            5,
            4,
            5000,
            mode,
        )

    return ContextBudget(
        8,
        8,
        8,
        9000,
        "full",
    )
