"""
E.V.I.E. - GitHub Provider Registration

Phase 9

IMPORTANT:
    This provider is intentionally READ ONLY.

    There is no:
        github.repo.delete
        github.repo.update
        github.contents.write
        github.issue.create
        github.issue.comment
        github.pull.merge
        github.workflow.dispatch
"""

from __future__ import annotations

from assistant.integrations.registry import (
    register_integration_capability,
)

from .activity import (
    github_actions,
    github_notifications,
    github_workflows,
)

from .repos import (
    github_commits,
    github_issues,
    github_profile,
    github_pull_requests,
    github_repositories,
    github_repository,
)


def load_github_provider():

    register_integration_capability(
        provider="github",
        name="github.profile",
        function=github_profile,
        risk="low",
        sensitivity="personal",
        description=(
            "Reads the authenticated GitHub profile."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.repos",
        function=github_repositories,
        risk="low",
        sensitivity="private",
        description=(
            "Lists GitHub repositories visible to the authenticated user."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.repo",
        function=github_repository,
        risk="low",
        sensitivity="private",
        description=(
            "Reads one GitHub repository."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.commits",
        function=github_commits,
        risk="low",
        sensitivity="private",
        description=(
            "Reads commits from a GitHub repository."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.issues",
        function=github_issues,
        risk="low",
        sensitivity="private",
        description=(
            "Reads issues from a GitHub repository."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.pulls",
        function=github_pull_requests,
        risk="low",
        sensitivity="private",
        description=(
            "Reads pull requests from a GitHub repository."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.notifications",
        function=github_notifications,
        risk="low",
        sensitivity="private",
        description=(
            "Reads GitHub notifications for the authenticated user."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.workflows",
        function=github_workflows,
        risk="low",
        sensitivity="private",
        description=(
            "Reads GitHub Actions workflow definitions for a repository."
        ),
    )

    register_integration_capability(
        provider="github",
        name="github.actions",
        function=github_actions,
        risk="low",
        sensitivity="private",
        description=(
            "Reads GitHub Actions workflow runs for a repository."
        ),
    )