"""
E.V.I.E. - GitHub Activity

Phase 9

READ ONLY.

Provides:
- GitHub notifications
- GitHub Actions workflows
- GitHub Actions workflow runs
"""

from __future__ import annotations

from .api import (
    github_get,
)

from .auth import (
    DEFAULT_ACCOUNT_ID,
    get_github_username,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_owner(
    owner: str | None,
):
    owner = (
        str(
            owner
            or ""
        )
        .strip()
    )

    if owner:
        return owner

    return (
        get_github_username()
    )


def _require_repo(
    repo: str,
):
    repo = (
        str(
            repo
        )
        .strip()
    )

    if not repo:

        raise ValueError(
            "GitHub repository is required."
        )

    return repo


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def github_notifications(
    account_id: str = DEFAULT_ACCOUNT_ID,
    all: bool = False,
    participating: bool = False,
    per_page: int = 50,
):
    return github_get(
        account_id=
            account_id,

        path=
            "/notifications",

        params={
            "all":
                str(
                    bool(
                        all
                    )
                ).lower(),

            "participating":
                str(
                    bool(
                        participating
                    )
                ).lower(),

            "per_page":
                max(
                    1,
                    min(
                        100,
                        int(
                            per_page
                        ),
                    ),
                ),
        },
    )


# ---------------------------------------------------------------------------
# GitHub Actions Workflows
# ---------------------------------------------------------------------------

def github_workflows(
    account_id: str = DEFAULT_ACCOUNT_ID,
    repo: str = "",
    owner: str | None = None,
    per_page: int = 50,
):
    repo = (
        _require_repo(
            repo
        )
    )

    owner = (
        _resolve_owner(
            owner
        )
    )

    return github_get(
        account_id=
            account_id,

        path=(
            f"/repos/"
            f"{owner}/"
            f"{repo}"
            "/actions/workflows"
        ),

        params={
            "per_page":
                max(
                    1,
                    min(
                        100,
                        int(
                            per_page
                        ),
                    ),
                ),
        },
    )


# ---------------------------------------------------------------------------
# GitHub Actions Workflow Runs
# ---------------------------------------------------------------------------

def github_actions(
    account_id: str = DEFAULT_ACCOUNT_ID,
    repo: str = "",
    owner: str | None = None,
    branch: str | None = None,
    status: str | None = None,
    per_page: int = 30,
):
    repo = (
        _require_repo(
            repo
        )
    )

    owner = (
        _resolve_owner(
            owner
        )
    )

    params = {
        "per_page":
            max(
                1,
                min(
                    100,
                    int(
                        per_page
                    ),
                ),
            ),
    }


    if branch:

        params[
            "branch"
        ] = branch


    if status:

        params[
            "status"
        ] = status


    return github_get(
        account_id=
            account_id,

        path=(
            f"/repos/"
            f"{owner}/"
            f"{repo}"
            "/actions/runs"
        ),

        params=
            params,
    )