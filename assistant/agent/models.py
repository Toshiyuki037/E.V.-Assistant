"""
E.V.I.E. - Agent Models

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Shared Phase 7 task structures.

Capabilities:
    - represents individual agent steps
    - represents initial agent plans
    - represents persistent multi-step tasks
    - represents final agent execution results
    - supports persistent continuation / replanning state

Most Recent Change:
    Added continuation_count so dynamically extended Phase 7 tasks
    persist correctly across application restarts.
"""

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import Any


# ---------------------------------------------------------------------------
# Agent Step
# ---------------------------------------------------------------------------

@dataclass
class AgentStep:
    """
    Represents one concrete Phase 7 computer action.
    """

    step_number: int

    description: str

    tool_name: str = ""

    arguments: dict[str, Any] = field(
        default_factory=dict
    )

    status: str = "pending"

    attempts: int = 0

    result: Any = None

    error: str | None = None


# ---------------------------------------------------------------------------
# Agent Plan
# ---------------------------------------------------------------------------

@dataclass
class AgentPlan:
    """
    Represents the initial plan produced by the Phase 7 planner.
    """

    goal: str

    use_agent: bool = False

    steps: list[AgentStep] = field(
        default_factory=list
    )

    confidence: int = 0

    summary: str = ""


# ---------------------------------------------------------------------------
# Persistent Agent Task
# ---------------------------------------------------------------------------

@dataclass
class AgentTask:
    """
    Represents the complete persistent state of an active Phase 7 task.

    This object is written to runtime/agent/current_task.json so
    E.V.I.E. can pause for approval, resume after ordinary restarts,
    replan after failures, and dynamically continue unfinished goals.
    """

    goal: str

    steps: list[AgentStep]

    workspace_path: str | None = None

    status: str = "planned"

    current_step_index: int = 0

    total_executions: int = 0

    replan_count: int = 0

    continuation_count: int = 0

    pending_action: dict[str, Any] | None = None

    final_summary: str = ""

    created_at: str = ""

    updated_at: str = ""


# ---------------------------------------------------------------------------
# Agent Result
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """
    Represents the result returned to main.py after Phase 7 runs,
    pauses, completes, fails, or is cancelled.
    """

    success: bool

    status: str

    goal: str

    message: str = ""

    requires_approval: bool = False

    pending_action: dict[str, Any] | None = None

    steps: list[AgentStep] = field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# Serialization Helpers
# ---------------------------------------------------------------------------

def step_to_dict(
    step: AgentStep,
):
    """
    Converts an AgentStep into a JSON-serializable dictionary.
    """

    return asdict(
        step
    )


def plan_to_dict(
    plan: AgentPlan,
):
    """
    Converts an AgentPlan into a JSON-serializable dictionary.
    """

    return asdict(
        plan
    )


def task_to_dict(
    task: AgentTask,
):
    """
    Converts an AgentTask into a JSON-serializable dictionary.
    """

    return asdict(
        task
    )


def result_to_dict(
    result: AgentResult,
):
    """
    Converts an AgentResult into a JSON-serializable dictionary.
    """

    return asdict(
        result
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Agent Models"
    )

    print(
        "----------------------"
    )


    step = AgentStep(
        step_number=1,

        description=(
            "Run a Python script."
        ),

        tool_name=
            "run_python",

        arguments={
            "arguments":
                [
                    "example.py"
                ]
        },
    )


    plan = AgentPlan(
        goal=(
            "Run example.py and "
            "debug it until successful."
        ),

        use_agent=True,

        steps=[
            step
        ],

        confidence=100,

        summary=(
            "Adaptive execution task."
        ),
    )


    task = AgentTask(
        goal=
            plan.goal,

        steps=
            plan.steps,

        workspace_path=
            None,
    )


    print(
        "Step:"
    )

    print(
        step_to_dict(
            step
        )
    )


    print()

    print(
        "Plan:"
    )

    print(
        plan_to_dict(
            plan
        )
    )


    print()

    print(
        "Task:"
    )

    print(
        task_to_dict(
            task
        )
    )