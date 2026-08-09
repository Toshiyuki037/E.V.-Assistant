"""
E.V.I.E. - Terminal Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides controlled terminal execution inside E.V.I.E.'s
    selected workspace.

Current Tools:
    - run_command
    - run_python
    - run_tests

Capabilities:
    - explicit argument-list execution
    - workspace-scoped working directories
    - timeout protection
    - stdout / stderr capture
    - output truncation
    - Python virtual-environment preservation
    - invalid PYTHONHASHSEED sanitization

Security:
    Commands are executed with shell=False.

    Risk classification and approval remain controlled by
    assistant/tools/executor.py and permissions.py.

Important:
    run_python() uses the SAME Python interpreter currently running
    E.V.I.E. instead of WindowsApps/system Python.

    This prevents E.V.I.E.'s agent from accidentally switching away
    from its active virtual environment.

Most Recent Change:
    Added deterministic Python interpreter selection and sanitized
    invalid PYTHONHASHSEED values that could otherwise crash Python
    before user code executes.
"""

import os
import shlex
import subprocess
import sys

from pathlib import Path

from .filesystem import (
    get_active_workspace_path,
    resolve_workspace_path,
)

from .registry import (
    register_tool,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 60

MAX_OUTPUT_CHARACTERS = 20_000


# ---------------------------------------------------------------------------
# Output Truncation
# ---------------------------------------------------------------------------

def truncate_output(
    text: str | None,
    limit: int = MAX_OUTPUT_CHARACTERS,
):
    """
    Prevents extremely large command output from flooding
    E.V.I.E.'s context.

    Returns:
        truncated_text,
        was_truncated
    """

    if text is None:

        return (
            "",
            False,
        )


    text = str(
        text
    )


    if len(text) <= limit:

        return (
            text,
            False,
        )


    suffix = (
        "\n\n"
        "[Output truncated by E.V.I.E.]"
    )


    keep = (
        max(
            0,
            limit
            - len(suffix)
        )
    )


    return (
        text[
            :keep
        ]
        + suffix,

        True,
    )


# ---------------------------------------------------------------------------
# Workspace Resolution
# ---------------------------------------------------------------------------

def resolve_terminal_workspace(
    workspace_path=None,
):
    """
    Resolves the workspace used by terminal actions.
    """

    if workspace_path:

        workspace = Path(
            workspace_path
        ).resolve()

    else:

        workspace = Path(
            get_active_workspace_path()
        ).resolve()


    if not workspace.exists():

        raise FileNotFoundError(
            str(
                workspace
            )
        )


    if not workspace.is_dir():

        raise NotADirectoryError(
            str(
                workspace
            )
        )


    return workspace


# ---------------------------------------------------------------------------
# Working Directory Resolution
# ---------------------------------------------------------------------------

def resolve_terminal_cwd(
    cwd=".",
    workspace_path=None,
):
    """
    Resolves a working directory while keeping it inside the
    selected workspace.
    """

    workspace = (
        resolve_terminal_workspace(
            workspace_path
        )
    )


    if (
        cwd is None
        or str(cwd).strip() == ""
        or str(cwd).strip() == "."
    ):

        return (
            workspace,
            workspace,
        )


    root, target = (
        resolve_workspace_path(
            str(cwd),
            workspace,
        )
    )


    if not target.exists():

        raise FileNotFoundError(
            str(
                target
            )
        )


    if not target.is_dir():

        raise NotADirectoryError(
            str(
                target
            )
        )


    return (
        root,
        target,
    )


# ---------------------------------------------------------------------------
# Python Environment Validation
# ---------------------------------------------------------------------------

def valid_python_hash_seed(
    value,
):
    """
    Returns True when PYTHONHASHSEED contains a valid value.

    Python accepts:
        random

    or an integer:
        0 through 4294967295
    """

    if value is None:

        return True


    value = str(
        value
    ).strip()


    if not value:

        return True


    if value.lower() == "random":

        return True


    try:

        number = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return False


    return (
        0
        <= number
        <= 4294967295
    )


# ---------------------------------------------------------------------------
# Sanitized Python Environment
# ---------------------------------------------------------------------------

def build_python_environment():
    """
    Creates an environment for Python subprocesses.

    E.V.I.E. inherits the current process environment, but removes an
    invalid PYTHONHASHSEED before starting another Python interpreter.

    This fixes crashes such as:

        Fatal Python error:
        config_init_hash_seed:
        PYTHONHASHSEED must be "random" or an integer...

    Only the invalid setting is removed. Other environment variables
    remain intact.
    """

    environment = (
        os.environ.copy()
    )


    hash_seed = (
        environment.get(
            "PYTHONHASHSEED"
        )
    )


    if not valid_python_hash_seed(
        hash_seed
    ):

        environment.pop(
            "PYTHONHASHSEED",
            None,
        )


    return environment


# ---------------------------------------------------------------------------
# Command Display
# ---------------------------------------------------------------------------

def command_to_text(
    command,
):
    """
    Creates a readable command representation for audit/results.
    """

    return " ".join(
        shlex.quote(
            str(item)
        )
        for item
        in command
    )


# ---------------------------------------------------------------------------
# Core Process Runner
# ---------------------------------------------------------------------------

def execute_process(
    command,
    cwd,
    timeout=DEFAULT_TIMEOUT,
    environment=None,
):
    """
    Executes one subprocess with shell=False and captures its result.
    """

    if not command:

        raise ValueError(
            "No command was provided."
        )


    command = [
        str(item)
        for item
        in command
    ]


    timeout = int(
        timeout
    )


    if timeout < 1:

        raise ValueError(
            "Timeout must be at least 1 second."
        )


    timed_out = False


    try:

        process = subprocess.run(
            command,

            cwd=str(
                cwd
            ),

            capture_output=True,

            text=True,

            shell=False,

            timeout=timeout,

            env=environment,

            errors="replace",
        )


        exit_code = (
            process.returncode
        )


        stdout = (
            process.stdout
            or ""
        )


        stderr = (
            process.stderr
            or ""
        )


    except subprocess.TimeoutExpired as error:

        timed_out = True

        exit_code = None


        stdout = (
            error.stdout
            or ""
        )


        stderr = (
            error.stderr
            or ""
        )


        if isinstance(
            stdout,
            bytes,
        ):

            stdout = stdout.decode(
                "utf-8",
                errors="replace",
            )


        if isinstance(
            stderr,
            bytes,
        ):

            stderr = stderr.decode(
                "utf-8",
                errors="replace",
            )


    stdout, stdout_truncated = (
        truncate_output(
            stdout
        )
    )


    stderr, stderr_truncated = (
        truncate_output(
            stderr
        )
    )


    return {
        "command":
            command,

        "command_text":
            command_to_text(
                command
            ),

        "exit_code":
            exit_code,

        "stdout":
            stdout,

        "stderr":
            stderr,

        "stdout_truncated":
            stdout_truncated,

        "stderr_truncated":
            stderr_truncated,

        "timed_out":
            timed_out,
    }


# ---------------------------------------------------------------------------
# Run Generic Command
# ---------------------------------------------------------------------------

def run_command(
    arguments,
    cwd=".",
    workspace_path=None,
    timeout=DEFAULT_TIMEOUT,
):
    """
    Runs an executable using explicit argument-list semantics.

    Example:

        run_command(
            arguments=[
                "git",
                "status",
                "--short",
            ]
        )

    Security:
        shell=False is always used.

        Permission/risk classification is handled by the central
        Phase 6 executor.
    """

    if not arguments:

        raise ValueError(
            "run_command requires arguments."
        )


    if not isinstance(
        arguments,
        (
            list,
            tuple,
        ),
    ):

        raise TypeError(
            (
                "run_command arguments must "
                "be a list or tuple."
            )
        )


    workspace, working_directory = (
        resolve_terminal_cwd(
            cwd=cwd,

            workspace_path=
                workspace_path,
        )
    )


    command = [
        str(item)
        for item
        in arguments
    ]


    result = execute_process(
        command=
            command,

        cwd=
            working_directory,

        timeout=
            timeout,

        environment=
            os.environ.copy(),
    )


    return {
        "workspace":
            str(
                workspace
            ),

        "cwd":
            str(
                working_directory
            ),

        **result,
    }


# ---------------------------------------------------------------------------
# Run Python
# ---------------------------------------------------------------------------

def run_python(
    arguments=None,
    cwd=".",
    workspace_path=None,
    timeout=DEFAULT_TIMEOUT,
):
    """
    Runs Python inside the selected workspace.

    IMPORTANT:
        This uses sys.executable.

        Therefore, when E.V.I.E. itself is running from:

            eve-assistant/venv/Scripts/python.exe

        run_python() uses that SAME interpreter.

        It does NOT rely on WindowsApps, PATH ordering, or whatever
        interpreter VS Code happens to have selected.

    Example:

        run_python(
            arguments=[
                "TypewriterTest/typewriter.py"
            ]
        )

    Equivalent to:

        <E.V.I.E. venv python> TypewriterTest/typewriter.py
    """

    if arguments is None:

        arguments = []


    if not isinstance(
        arguments,
        (
            list,
            tuple,
        ),
    ):

        raise TypeError(
            (
                "run_python arguments must "
                "be a list or tuple."
            )
        )


    workspace, working_directory = (
        resolve_terminal_cwd(
            cwd=cwd,

            workspace_path=
                workspace_path,
        )
    )


    python_executable = Path(
        sys.executable
    ).resolve()


    if not python_executable.exists():

        raise FileNotFoundError(
            (
                "Current Python interpreter "
                "could not be located: "
                f"{python_executable}"
            )
        )


    command = [
        str(
            python_executable
        ),
    ]


    command.extend(
        str(item)
        for item
        in arguments
    )


    environment = (
        build_python_environment()
    )


    result = execute_process(
        command=
            command,

        cwd=
            working_directory,

        timeout=
            timeout,

        environment=
            environment,
    )


    return {
        "workspace":
            str(
                workspace
            ),

        "cwd":
            str(
                working_directory
            ),

        "python_executable":
            str(
                python_executable
            ),

        "pythonhashseed_sanitized":
            (
                not valid_python_hash_seed(
                    os.environ.get(
                        "PYTHONHASHSEED"
                    )
                )
            ),

        **result,
    }


# ---------------------------------------------------------------------------
# Run Tests
# ---------------------------------------------------------------------------

def run_tests(
    arguments=None,
    cwd=".",
    workspace_path=None,
    timeout=120,
):
    """
    Runs pytest using E.V.I.E.'s current Python interpreter.

    Using:

        python -m pytest

    is more reliable than relying on a separate `pytest` executable
    appearing on PATH.
    """

    if arguments is None:

        arguments = []


    if not isinstance(
        arguments,
        (
            list,
            tuple,
        ),
    ):

        raise TypeError(
            (
                "run_tests arguments must "
                "be a list or tuple."
            )
        )


    test_arguments = [
        "-m",
        "pytest",
    ]


    test_arguments.extend(
        str(item)
        for item
        in arguments
    )


    return run_python(
        arguments=
            test_arguments,

        cwd=
            cwd,

        workspace_path=
            workspace_path,

        timeout=
            timeout,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name=
        "run_command",

    description=(
        "Runs an executable with explicit argument-list semantics "
        "inside the selected workspace. The command must be supplied "
        "through the arguments list. shell=False is always used."
    ),

    category=
        "terminal",

    risk=
        "low",

    function=
        run_command,
)


register_tool(
    name=
        "run_python",

    description=(
        "Runs Python using E.V.I.E.'s current Python interpreter "
        "inside the selected workspace. Supply Python arguments in "
        "the arguments list, for example "
        "arguments=['TypewriterTest/typewriter.py']. "
        "Invalid PYTHONHASHSEED values are sanitized automatically."
    ),

    category=
        "terminal",

    risk=
        "low",

    function=
        run_python,
)


register_tool(
    name=
        "run_tests",

    description=(
        "Runs pytest through E.V.I.E.'s current Python interpreter "
        "inside the selected workspace. Optional pytest arguments are "
        "supplied through the arguments list."
    ),

    category=
        "terminal",

    risk=
        "low",

    function=
        run_tests,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Terminal Tools"
    )

    print(
        "-----------------------"
    )


    print()

    print(
        "Current Python:"
    )

    print(
        sys.executable
    )


    print()

    print(
        "Active workspace:"
    )

    print(
        get_active_workspace_path()
    )


    print()

    print(
        "PYTHONHASHSEED:"
    )

    print(
        repr(
            os.environ.get(
                "PYTHONHASHSEED"
            )
        )
    )


    print()

    print(
        "PYTHONHASHSEED valid:"
    )

    print(
        valid_python_hash_seed(
            os.environ.get(
                "PYTHONHASHSEED"
            )
        )
    )


    print()

    print(
        "TEST 1 - Basic Python"
    )


    result = run_python(
        arguments=[
            "-c",
            (
                "import sys; "
                "print('E.V.I.E. terminal tool works'); "
                "print(sys.executable)"
            ),
        ]
    )


    print(
        result
    )