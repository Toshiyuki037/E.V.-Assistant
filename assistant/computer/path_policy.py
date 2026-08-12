"""
E.V.I.E. - Filesystem Path Policy

Phase 13D

All filesystem mutations are canonicalized and classified before execution.
System-critical paths are denied. Sensitive development/credential paths
require explicit approval.
"""

from __future__ import annotations

import os
from pathlib import Path

from .filesystem_models import PathRisk


def canonicalize_path(
    value: str | os.PathLike,
) -> Path:
    text = os.path.expandvars(
        os.path.expanduser(
            str(value)
        )
    ).strip()

    if not text:
        raise ValueError(
            "Filesystem path cannot be empty."
        )

    return Path(text).resolve(
        strict=False
    )


def _normalized(
    path: Path,
) -> str:
    return str(path).replace(
        "/",
        "\\",
    ).lower()


def _protected_roots() -> list[Path]:
    roots = []

    for key in (
        "SystemRoot",
        "ProgramFiles",
        "ProgramFiles(x86)",
    ):
        value = os.environ.get(
            key,
            ""
        )

        if value:
            roots.append(
                canonicalize_path(
                    value
                )
            )

    return roots


def _sensitive_names() -> set[str]:
    return {
        ".git",
        ".env",
        ".ssh",
        ".aws",
        ".azure",
        ".gnupg",
        "credentials",
        "secrets",
        "tokens",
        "runtime",
    }


def classify_path(
    value: str | os.PathLike,
) -> PathRisk:
    path = canonicalize_path(
        value
    )

    normalized = _normalized(
        path
    )

    for root in _protected_roots():
        root_text = _normalized(
            root
        )

        if (
            normalized == root_text
            or normalized.startswith(
                root_text
                + "\\"
            )
        ):
            return PathRisk.PROTECTED

    parts = {
        part.lower()
        for part in path.parts
    }

    if parts.intersection(
        _sensitive_names()
    ):
        return PathRisk.SENSITIVE

    return PathRisk.NORMAL


def assert_mutation_allowed(
    value: str | os.PathLike,
    *,
    approved: bool = False,
):
    risk = classify_path(
        value
    )

    if risk == PathRisk.PROTECTED:
        raise PermissionError(
            (
                "Filesystem mutation denied for protected "
                f"path: {canonicalize_path(value)}"
            )
        )

    if (
        risk == PathRisk.SENSITIVE
        and not approved
    ):
        raise PermissionError(
            (
                "Filesystem mutation requires explicit "
                f"approval for sensitive path: "
                f"{canonicalize_path(value)}"
            )
        )

    return risk
