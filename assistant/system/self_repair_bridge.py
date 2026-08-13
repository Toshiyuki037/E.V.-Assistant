"""
E.V.I.E. - Health to Self-Engineering Bridge

Phase 15J

Purpose:
    Converts health/diagnostic evidence plus architecture ownership metadata
    into a bounded, approval-aware repair request for E.V.I.E.'s existing
    self-engineering/coding system.

Important:
    This module does not assume a specific coding-agent implementation.
    Instead, it accepts an executor callback supplied by the existing
    self-engineering architecture.

Safety:
    - unknown components fail closed
    - repair paths are bounded by Phase 15I ownership metadata
    - high-risk repairs require explicit approval
    - no source code is modified without an executor being provided
    - required regression tests travel with the repair request
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import (
    Any,
    Callable,
)

from .failures import (
    get_component_state,
)

from .repair_scope import (
    build_repair_scope,
)


@dataclass(frozen=True)
class RepairRequest:
    component: str

    issue: str

    found: bool

    approved: bool = False

    phase: int | None = None

    owner: str = ""

    risk: str = ""

    allowed_paths: tuple[str, ...] = ()

    required_tests: tuple[str, ...] = ()

    dependencies: tuple[str, ...] = ()

    last_failure_at: str = ""

    consecutive_failures: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class RepairBridgeResult:
    component: str

    success: bool

    status: str

    detail: str = ""

    request: RepairRequest | None = None

    executor_result: Any = None


def repair_request_to_dict(
    request: RepairRequest,
):
    return asdict(
        request
    )


def build_repair_request(
    component: str,
    *,
    issue: str | None = None,
    approved: bool = False,
):
    normalized = (
        str(
            component
            or ""
        )
        .strip()
        .lower()
    )

    scope = (
        build_repair_scope(
            normalized
        )
    )

    if not scope.found:

        return RepairRequest(
            component=
                normalized,

            issue=
                str(
                    issue
                    or ""
                ),

            found=
                False,

            approved=
                False,
        )


    failure = (
        get_component_state(
            normalized
        )
    )


    resolved_issue = (
        str(
            issue
            or failure.last_error
            or "Component reported unhealthy behavior."
        )
        .strip()
    )


    return RepairRequest(
        component=
            normalized,

        issue=
            resolved_issue,

        found=
            True,

        approved=
            bool(
                approved
            ),

        phase=
            scope.phase,

        owner=
            scope.owner,

        risk=
            scope.risk,

        allowed_paths=
            scope.allowed_paths,

        required_tests=
            scope.required_tests,

        dependencies=
            scope.dependencies,

        last_failure_at=
            failure.last_failure_at,

        consecutive_failures=
            failure.consecutive_failures,

        metadata={
            "ownership_notes":
                scope.notes,
        },
    )


def validate_repair_request(
    request: RepairRequest,
):
    problems = []


    if not request.found:

        problems.append(
            "No architecture ownership record exists for this component."
        )


    if not request.component:

        problems.append(
            "Repair request has no component."
        )


    if not request.issue:

        problems.append(
            "Repair request has no diagnostic issue."
        )


    if not request.allowed_paths:

        problems.append(
            "Repair request has no bounded repair paths."
        )


    if request.risk not in {
        "low",
        "medium",
        "high",
    }:

        problems.append(
            "Repair request has an invalid risk level."
        )


    return (
        len(
            problems
        )
        == 0,
        problems,
    )


def repair_requires_approval(
    request: RepairRequest,
):
    """
    All source-code repair requires approval.

    High-risk ownership stays explicitly visible so the caller can
    apply stronger approval/authorization policy if desired.
    """

    return True


def render_repair_prompt(
    request: RepairRequest,
):
    valid, problems = (
        validate_repair_request(
            request
        )
    )

    if not valid:

        return (
            "Repair request is invalid: "
            + "; ".join(
                problems
            )
        )


    allowed = (
        "\n".join(
            f"- {path}"
            for path
            in request.allowed_paths
        )
    )


    tests = (
        "\n".join(
            f"- {path}"
            for path
            in request.required_tests
        )
        if request.required_tests
        else "- No specific tests registered; run the full regression suite."
    )


    dependencies = (
        ", ".join(
            request.dependencies
        )
        if request.dependencies
        else "None explicitly registered"
    )


    return f"""
E.V.I.E. SELF-ENGINEERING REPAIR REQUEST

Component:
{request.component}

Owning Phase:
{request.phase}

Owner:
{request.owner}

Risk:
{request.risk}

Observed Issue:
{request.issue}

Consecutive Failures:
{request.consecutive_failures}

Last Failure:
{request.last_failure_at or "Unknown"}

ALLOWED REPAIR PATHS:
{allowed}

REQUIRED TARGETED TESTS:
{tests}

DEPENDENCIES:
{dependencies}

REPAIR RULES:

1. Diagnose the root cause before modifying code.
2. Do not modify files outside ALLOWED REPAIR PATHS.
3. Preserve completed Phase 1-14 behavior unless the repair explicitly
   requires a compatible correction.
4. Make the smallest architecture-consistent change that resolves the issue.
5. Run targeted tests after changes.
6. Run the complete regression suite before reporting success.
7. If tests regress, rollback or correct the repair.
8. Do not commit automatically unless a separate commit approval is granted.
9. Re-run the relevant health/diagnostic check after tests pass.
10. Report exactly what changed, what was tested, and whether health recovered.
""".strip()


def execute_repair_bridge(
    request: RepairRequest,
    *,
    executor: Callable[
        [RepairRequest, str],
        Any,
    ] | None = None,
):
    valid, problems = (
        validate_repair_request(
            request
        )
    )

    if not valid:

        return RepairBridgeResult(
            component=
                request.component,

            success=
                False,

            status=
                "INVALID",

            detail=
                "; ".join(
                    problems
                ),

            request=
                request,
        )


    if repair_requires_approval(
        request
    ) and not request.approved:

        return RepairBridgeResult(
            component=
                request.component,

            success=
                False,

            status=
                "APPROVAL_REQUIRED",

            detail=
                "Source-code repair requires explicit approval.",

            request=
                request,
        )


    if executor is None:

        return RepairBridgeResult(
            component=
                request.component,

            success=
                False,

            status=
                "EXECUTOR_REQUIRED",

            detail=(
                "No self-engineering executor was supplied. "
                "The bounded repair request is ready for the existing coding agent."
            ),

            request=
                request,
        )


    prompt = (
        render_repair_prompt(
            request
        )
    )


    try:

        result = (
            executor(
                request,
                prompt,
            )
        )

    except Exception as error:

        return RepairBridgeResult(
            component=
                request.component,

            success=
                False,

            status=
                "EXECUTOR_FAILED",

            detail=
                str(
                    error
                ),

            request=
                request,
        )


    return RepairBridgeResult(
        component=
            request.component,

        success=
            True,

        status=
            "DISPATCHED",

        detail=
            "Repair request dispatched to the self-engineering executor.",

        request=
            request,

        executor_result=
            result,
    )
