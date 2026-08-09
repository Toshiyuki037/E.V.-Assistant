"""
E.V.I.E. - Git Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides controlled Git operations for E.V.I.E.

Security:
    Git commands execute only inside a resolved workspace.

    Read-only Git actions are low risk.
    Repository-changing actions require approval.
    Remote/destructive actions are high risk.

Current Tools:
    - git_status
    - git_diff
    - git_log
    - git_add
    - git_commit
    - git_push
"""

import subprocess
from pathlib import Path

from .filesystem import (
    get_active_workspace_path,
    resolve_workspace_path,
)

from .registry import (
    register_tool,
)


DEFAULT_TIMEOUT = 60
MAX_OUTPUT_CHARACTERS = 50_000


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

def get_git_workspace(
    workspace_path=None,
):
    if workspace_path:

        root = Path(
            workspace_path
        ).resolve()

    else:

        root = (
            get_active_workspace_path()
        )

    if not (
        root
        / ".git"
    ).exists():

        raise RuntimeError(
            (
                "Selected workspace does "
                "not appear to be a Git repository."
            )
        )

    return root


# ---------------------------------------------------------------------------
# Core Git Runner
# ---------------------------------------------------------------------------

def run_git(
    arguments: list[str],
    workspace_path=None,
    timeout: int = DEFAULT_TIMEOUT,
):
    """
    Executes Git without shell=True.
    """

    root = get_git_workspace(
        workspace_path
    )

    command = [
        "git",
        *[
            str(argument)
            for argument
            in arguments
        ],
    ]

    try:

        result = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )

        stdout = (
            result.stdout
            or ""
        )

        stderr = (
            result.stderr
            or ""
        )

        return {
            "workspace":
                str(root),

            "command":
                command,

            "exit_code":
                result.returncode,

            "stdout":
                stdout[
                    :MAX_OUTPUT_CHARACTERS
                ],

            "stderr":
                stderr[
                    :MAX_OUTPUT_CHARACTERS
                ],

            "stdout_truncated":
                (
                    len(stdout)
                    > MAX_OUTPUT_CHARACTERS
                ),

            "stderr_truncated":
                (
                    len(stderr)
                    > MAX_OUTPUT_CHARACTERS
                ),

            "timed_out":
                False,
        }

    except subprocess.TimeoutExpired as error:

        return {
            "workspace":
                str(root),

            "command":
                command,

            "exit_code":
                None,

            "stdout":
                (
                    error.stdout
                    or ""
                ),

            "stderr":
                (
                    error.stderr
                    or ""
                ),

            "timed_out":
                True,
        }


# ---------------------------------------------------------------------------
# Git Status
# ---------------------------------------------------------------------------

def git_status(
    workspace_path=None,
):
    return run_git(
        [
            "status",
            "--short",
            "--branch",
        ],
        workspace_path,
    )


# ---------------------------------------------------------------------------
# Git Diff
# ---------------------------------------------------------------------------

def git_diff(
    staged: bool = False,
    workspace_path=None,
):
    arguments = [
        "diff",
    ]

    if staged:

        arguments.append(
            "--staged"
        )

    return run_git(
        arguments,
        workspace_path,
    )


# ---------------------------------------------------------------------------
# Git Log
# ---------------------------------------------------------------------------

def git_log(
    limit: int = 10,
    workspace_path=None,
):
    limit = max(
        1,
        min(
            int(limit),
            50,
        ),
    )

    return run_git(
        [
            "log",
            f"-{limit}",
            "--oneline",
            "--decorate",
        ],
        workspace_path,
    )


# ---------------------------------------------------------------------------
# Git Add
# ---------------------------------------------------------------------------

def git_add(
    paths: list[str],
    workspace_path=None,
):
    if not paths:

        raise ValueError(
            "At least one path is required."
        )

    root = get_git_workspace(
        workspace_path
    )

    safe_paths = []

    for path in paths:

        _, resolved = (
            resolve_workspace_path(
                path,
                root,
            )
        )

        relative = (
            resolved.relative_to(
                root
            )
        )

        safe_paths.append(
            str(relative)
        )

    return run_git(
        [
            "add",
            "--",
            *safe_paths,
        ],
        root,
    )


# ---------------------------------------------------------------------------
# Git Commit
# ---------------------------------------------------------------------------

def git_commit(
    message: str,
    workspace_path=None,
):
    message = (
        message.strip()
    )

    if not message:

        raise ValueError(
            "Commit message cannot be empty."
        )

    if len(message) > 300:

        raise ValueError(
            (
                "Commit message is too long. "
                "Maximum is 300 characters."
            )
        )

    return run_git(
        [
            "commit",
            "-m",
            message,
        ],
        workspace_path,
    )


# ---------------------------------------------------------------------------
# Git Push
# ---------------------------------------------------------------------------

def git_push(
    remote: str = "origin",
    branch: str | None = None,
    workspace_path=None,
):
    arguments = [
        "push",
        remote,
    ]

    if branch:

        arguments.append(
            branch
        )

    return run_git(
        arguments,
        workspace_path,
        timeout=120,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name="git_status",
    description=(
        "Shows the Git status of the selected workspace."
    ),
    category="git",
    risk="low",
    function=git_status,
)


register_tool(
    name="git_diff",
    description=(
        "Shows unstaged or staged Git differences."
    ),
    category="git",
    risk="low",
    function=git_diff,
)


register_tool(
    name="git_log",
    description=(
        "Shows recent Git commit history."
    ),
    category="git",
    risk="low",
    function=git_log,
)


register_tool(
    name="git_add",
    description=(
        "Stages selected workspace files for Git."
    ),
    category="git",
    risk="medium",
    function=git_add,
)


register_tool(
    name="git_commit",
    description=(
        "Creates a Git commit from currently staged changes."
    ),
    category="git",
    risk="medium",
    function=git_commit,
)


register_tool(
    name="git_push",
    description=(
        "Pushes repository commits to a configured remote."
    ),
    category="git",
    risk="high",
    function=git_push,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Git Tools"
    )

    print(
        "-------------------"
    )

    print()

    result = git_status()

    print(
        "Git status:"
    )

    print(
        result["stdout"]
        or result["stderr"]
    )

    print()

    print(
        "Recent commits:"
    )

    result = git_log(
        limit=5
    )

    print(
        result["stdout"]
        or result["stderr"]
    )