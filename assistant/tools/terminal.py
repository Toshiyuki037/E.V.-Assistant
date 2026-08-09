"""
E.V.I.E. - Terminal Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides controlled subprocess execution inside the current
    E.V.I.E. workspace.

Security:
    Commands are passed as argument arrays rather than shell strings.

    shell=True is never used.

    Only explicitly allowed executables may run through this module.

Most Recent Change:
    Initial Phase 6 safe terminal execution tools.
"""

import shutil
import subprocess

from pathlib import Path

from .permissions import (
    classify_command_risk,
)

from .registry import (
    register_tool,
)

from .filesystem import (
    get_active_workspace_path,
    resolve_workspace_path,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 60

MAX_OUTPUT_CHARACTERS = (
    50_000
)


ALLOWED_EXECUTABLES = {
    "python",
    "python.exe",

    "py",
    "py.exe",

    "pytest",
    "pytest.exe",

    "pip",
    "pip.exe",

    "pip3",
    "pip3.exe",

    "node",
    "node.exe",

    "npm",
    "npm.cmd",

    "npx",
    "npx.cmd",
}


# ---------------------------------------------------------------------------
# Executable Validation
# ---------------------------------------------------------------------------

def normalize_executable(
    executable: str,
):
    return Path(
        executable
    ).name.lower()


def validate_executable(
    executable: str,
):
    normalized = (
        normalize_executable(
            executable
        )
    )

    if (
        normalized
        not in ALLOWED_EXECUTABLES
    ):

        raise PermissionError(
            (
                "Executable is not approved "
                "for E.V.I.E. terminal tools: "
                f"{executable}"
            )
        )

    return normalized


# ---------------------------------------------------------------------------
# Command Formatting
# ---------------------------------------------------------------------------

def command_to_text(
    arguments: list[str],
):
    return " ".join(
        str(argument)
        for argument in arguments
    )


# ---------------------------------------------------------------------------
# Core Command Runner
# ---------------------------------------------------------------------------

def run_command(
    arguments: list[str],
    cwd: str = ".",
    workspace_path=None,
    timeout: int = DEFAULT_TIMEOUT,
):
    """
    Runs an explicitly allowed executable without invoking a shell.

    Returns stdout, stderr, exit code, timeout status, and risk
    classification.
    """

    if not arguments:

        raise ValueError(
            "Command arguments cannot be empty."
        )

    arguments = [
        str(argument)
        for argument in arguments
    ]

    validate_executable(
        arguments[0]
    )

    root, working_directory = (
        resolve_workspace_path(
            cwd,
            workspace_path,
        )
    )

    if not working_directory.exists():

        raise FileNotFoundError(
            (
                "Working directory does "
                f"not exist: {working_directory}"
            )
        )

    if not working_directory.is_dir():

        raise NotADirectoryError(
            str(
                working_directory
            )
        )

    command_text = (
        command_to_text(
            arguments
        )
    )

    risk = (
        classify_command_risk(
            command_text
        )
    )

    try:

        result = subprocess.run(
            arguments,
            cwd=str(
                working_directory
            ),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
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

            "cwd":
                str(
                    working_directory
                ),

            "command":
                arguments,

            "command_text":
                command_text,

            "risk":
                risk,

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

            "cwd":
                str(
                    working_directory
                ),

            "command":
                arguments,

            "command_text":
                command_text,

            "risk":
                risk,

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
# Python Runner
# ---------------------------------------------------------------------------

def run_python(
    arguments=None,
    cwd: str = ".",
    workspace_path=None,
    timeout: int = DEFAULT_TIMEOUT,
):
    """
    Executes Python with argument-list semantics.

    Example:

        run_python(
            ["-m", "assistant.memory.database"]
        )
    """

    if arguments is None:

        arguments = []

    command = [
        "python",
        *arguments,
    ]

    return run_command(
        arguments=command,
        cwd=cwd,
        workspace_path=
            workspace_path,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Test Runner
# ---------------------------------------------------------------------------

def run_tests(
    test_path: str | None = None,
    cwd: str = ".",
    workspace_path=None,
    timeout: int = 120,
):
    """
    Runs pytest inside the selected workspace.
    """

    arguments = [
        "python",
        "-m",
        "pytest",
    ]

    if test_path:

        arguments.append(
            test_path
        )

    return run_command(
        arguments=arguments,
        cwd=cwd,
        workspace_path=
            workspace_path,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name="run_command",
    description=(
        "Runs an approved executable with "
        "explicit argument-list semantics "
        "inside the active workspace."
    ),
    category="terminal",
    risk="low",
    function=run_command,
)


register_tool(
    name="run_python",
    description=(
        "Runs Python inside the active "
        "workspace."
    ),
    category="terminal",
    risk="low",
    function=run_python,
)


register_tool(
    name="run_tests",
    description=(
        "Runs pytest for the active project."
    ),
    category="terminal",
    risk="low",
    function=run_tests,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Terminal Tools"
    )

    print(
        "------------------------"
    )

    print()

    result = run_python(
        [
            "-c",
            "print('E.V.I.E. terminal tool works')",
        ]
    )

    print(
        "Exit code:",
        result[
            "exit_code"
        ],
    )

    print(
        "STDOUT:"
    )

    print(
        result[
            "stdout"
        ]
    )

    print(
        "STDERR:"
    )

    print(
        result[
            "stderr"
        ]
    )