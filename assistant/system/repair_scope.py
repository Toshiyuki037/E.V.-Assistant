"""
E.V.I.E. - Repair Scope Builder

Phase 15I

Purpose:
    Converts architecture ownership metadata into a bounded repair scope.

This does not edit code. It only prepares deterministic constraints that
the future Phase 15J self-engineering bridge can consume.
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
)

from .ownership import (
    get_ownership,
)


@dataclass(frozen=True)
class RepairScope:
    component: str

    found: bool

    phase: int | None = None

    owner: str = ""

    allowed_paths: tuple[str, ...] = ()

    required_tests: tuple[str, ...] = ()

    dependencies: tuple[str, ...] = ()

    risk: str = ""

    notes: str = ""


def build_repair_scope(
    component: str,
):
    record = (
        get_ownership(
            component
        )
    )

    if record is None:

        return RepairScope(
            component=
                str(
                    component
                    or ""
                )
                .strip()
                .lower(),

            found=
                False,
        )


    return RepairScope(
        component=
            record.component,

        found=
            True,

        phase=
            record.phase,

        owner=
            record.owner,

        allowed_paths=
            record.repair_paths,

        required_tests=
            record.tests,

        dependencies=
            record.dependencies,

        risk=
            record.risk,

        notes=
            record.notes,
    )


def repair_scope_to_dict(
    scope: RepairScope,
):
    return asdict(
        scope
    )
