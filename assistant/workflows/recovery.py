"""
E.V.I.E. - Workflow Recovery

Phase 11C

Purpose:
Repair interrupted workflow runs after process or machine restart.

Safety rule:
A stale step marked "running" is never assumed successful.
It is reset to pending so the workflow resumes from the last verified
checkpoint.

Approval-paused runs remain approval-paused.
Completed/failed/cancelled runs are not modified.
"""

from __future__ import annotations

from .audit import (
    record_audit_event,
)

from .models import (
    RUN_AWAITING_APPROVAL,
    RUN_CANCELLED,
    RUN_COMPLETED,
    RUN_FAILED,
    RUN_PAUSED,
    RUN_RUNNING,
    STEP_AWAITING_APPROVAL,
    STEP_PENDING,
    STEP_RUNNING,
)

from .state import (
    list_active_runs,
    save_run,
)


TERMINAL_RUN_STATUSES = {
    RUN_COMPLETED,
    RUN_FAILED,
    RUN_CANCELLED,
}


def repair_interrupted_run(
    run,
):
    if (
        run.status
        in TERMINAL_RUN_STATUSES
    ):

        return run


    changed = False


    for step in run.steps:

        if (
            step.status
            == STEP_RUNNING
        ):

            step.status = (
                STEP_PENDING
            )

            step.error = (
                None
            )

            changed = True


            record_audit_event(
                run.run_id,
                "step_recovered",

                workflow_id=
                    run.workflow_id,

                step_id=
                    step.step_id,

                message=(
                    "Interrupted running step reset "
                    "to pending after restart."
                ),
            )


    if run.pending_action:

        run.status = (
            RUN_AWAITING_APPROVAL
        )

    elif (
        run.status
        in {
            RUN_RUNNING,
            RUN_PAUSED,
        }
    ):

        run.status = (
            RUN_PAUSED
        )


    if changed:

        save_run(
            run
        )


        record_audit_event(
            run.run_id,
            "run_recovered",

            workflow_id=
                run.workflow_id,

            message=(
                "Workflow run repaired after restart."
            ),
        )


    return run


def recover_active_runs():
    recovered = []


    for run in (
        list_active_runs()
    ):

        recovered.append(
            repair_interrupted_run(
                run
            )
        )


    return recovered
