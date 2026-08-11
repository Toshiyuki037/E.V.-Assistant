"""
E.V.I.E. - GitHub Repositories

Phase 9

READ ONLY.
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


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def github_profile(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    return github_get(
        account_id=
            account_id,

        path=
            "/user",
    )


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

def github_repositories(
    account_id: str = DEFAULT_ACCOUNT_ID,
    visibility: str = "all",
    affiliation: str = "owner,collaborator,organization_member",
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 100,
):
    return github_get(
        account_id=
            account_id,

        path=
            "/user/repos",

        params={
            "visibility":
                visibility,

            "affiliation":
                affiliation,

            "sort":
                sort,

            "direction":
                direction,

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
# One Repository
# ---------------------------------------------------------------------------

def github_repository(
    account_id: str = DEFAULT_ACCOUNT_ID,
    repo: str = "",
    owner: str | None = None,
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
        ),
    )


# ---------------------------------------------------------------------------
# Commits
# ---------------------------------------------------------------------------

def github_commits(
    account_id: str = DEFAULT_ACCOUNT_ID,
    repo: str = "",
    owner: str | None = None,
    branch: str | None = None,
    author: str | None = None,
    path: str | None = None,
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
            "sha"
        ] = branch

    if author:

        params[
            "author"
        ] = author

    if path:

        params[
            "path"
        ] = path

    return github_get(
        account_id=
            account_id,

        path=(
            f"/repos/"
            f"{owner}/"
            f"{repo}"
            "/commits"
        ),

        params=
            params,
    )


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

def github_issues(
    account_id: str = DEFAULT_ACCOUNT_ID,
    repo: str = "",
    owner: str | None = None,
    state: str = "open",
    labels: str | None = None,
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

    params = {
        "state":
            state,

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

    if labels:

        params[
            "labels"
        ] = labels

    result = github_get(
        account_id=
            account_id,

        path=(
            f"/repos/"
            f"{owner}/"
            f"{repo}"
            "/issues"
        ),

        params=
            params,
    )

    # GitHub's issues endpoint also returns pull requests.
    # This capability intentionally filters them out.
    return [
        item
        for item
        in (
            result
            or []
        )
        if "pull_request"
        not in item
    ]


# ---------------------------------------------------------------------------
# Pull Requests
# ---------------------------------------------------------------------------

def github_pull_requests(
    account_id: str = DEFAULT_ACCOUNT_ID,
    repo: str = "",
    owner: str | None = None,
    state: str = "open",
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
            "/pulls"
        ),

        params={
            "state":
                state,

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