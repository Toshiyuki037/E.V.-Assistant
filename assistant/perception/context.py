"""
E.V.I.E. - Live Context Router

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Collects and formats live computer context for E.V.I.E.

How It Works:
    Receives a single workspace snapshot captured for the current
    user request.

    This prevents perception and knowledge systems from observing
    different active workspaces during the same reasoning cycle.

    Additional context such as:
        - all open VS Code workspaces
        - visible applications
        - terminal history
        - clipboard

    is included only when relevant.

Most Recent Change:
    Added single-snapshot context routing and improved detection of
    questions about all currently open projects/workspaces.
"""

from datetime import datetime

import pyperclip

from .system import (
    get_system_context,
)

from .workspace import (
    get_workspace_context,
)


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------

def get_clipboard_context(
    max_characters: int = 1500,
):
    """
    Reads text clipboard content only when explicitly requested
    by the context router.
    """

    try:

        value = pyperclip.paste()

        if not isinstance(
            value,
            str,
        ):
            return None

        value = value.strip()

        if not value:
            return None

        return value[
            :max_characters
        ]

    except Exception:

        return None


# ---------------------------------------------------------------------------
# Context Routing
# ---------------------------------------------------------------------------

def determine_context_needs(
    user_message: str,
):
    """
    Determines which live context sections are relevant to the
    current request.
    """

    text = user_message.lower()


    # -----------------------------------------------------------------------
    # Clipboard
    # -----------------------------------------------------------------------

    wants_clipboard = any(
        phrase in text

        for phrase in (
            "clipboard",
            "copied",
            "what did i copy",
            "what i copied",
            "paste",
            "pasted",
        )
    )


    # -----------------------------------------------------------------------
    # Terminal
    # -----------------------------------------------------------------------

    wants_terminal = any(
        phrase in text

        for phrase in (
            "terminal",
            "powershell",
            "command",
            "commands",
            "shell",
            "console",
            "terminal history",
            "command history",
            "recently run",
            "recently ran",
            "last command",
        )
    )


    # -----------------------------------------------------------------------
    # Visible applications
    # -----------------------------------------------------------------------

    wants_apps = any(
        phrase in text

        for phrase in (
            "applications",
            "application",
            "apps",
            "programs",
            "what is open",
            "what's open",
            "open apps",
            "open applications",
            "running apps",
            "running applications",
        )
    )


    # -----------------------------------------------------------------------
    # Workspace / Git
    # -----------------------------------------------------------------------

    wants_workspace = any(
        phrase in text

        for phrase in (
            "project",
            "projects",
            "workspace",
            "workspaces",
            "repo",
            "repository",
            "branch",
            "git",
            "modified",
            "changes",
            "working on",
            "file",
            "files",
            "code",
            "vscode",
            "vs code",
        )
    )


    # -----------------------------------------------------------------------
    # Multiple Workspaces
    # -----------------------------------------------------------------------

    wants_all_workspaces = (
        any(
            phrase in text

            for phrase in (
                "other project",
                "other workspace",
                "other repo",
                "other repository",
                "other vscode",
                "other vs code",

                "both projects",
                "both workspaces",
                "two projects",
                "two workspaces",

                "all projects",
                "all workspaces",
                "all repos",
                "all repositories",

                "compare the projects",
                "compare projects",

                "projects currently open",
                "workspaces currently open",
                "repos currently open",
            )
        )

        or (
            (
                "project" in text
                or "projects" in text
            )
            and "open" in text
        )

        or (
            (
                "workspace" in text
                or "workspaces" in text
            )
            and "open" in text
        )

        or (
            (
                "repo" in text
                or "repos" in text
                or "repository" in text
                or "repositories" in text
            )
            and "open" in text
        )
    )


    return {
        "system":
            True,

        "workspace":
            (
                wants_workspace
                or wants_all_workspaces
            ),

        "all_workspaces":
            wants_all_workspaces,

        "applications":
            wants_apps,

        "terminal":
            wants_terminal,

        "clipboard":
            wants_clipboard,
    }


# ---------------------------------------------------------------------------
# Live Context Collection
# ---------------------------------------------------------------------------

def get_live_context(
    user_message: str,
    workspace_snapshot: dict | None = None,
    system_snapshot: dict | None = None,
):
    """
    Builds live context using snapshots captured for this request.

    If snapshots are not supplied, they are collected here.

    brain.py should normally supply the workspace snapshot so
    perception and project knowledge use identical workspace state.
    """

    needs = determine_context_needs(
        user_message
    )


    # -----------------------------------------------------------------------
    # System snapshot
    # -----------------------------------------------------------------------

    if system_snapshot is None:

        system = get_system_context()

    else:

        system = system_snapshot


    # -----------------------------------------------------------------------
    # Workspace snapshot
    # -----------------------------------------------------------------------

    if needs[
        "workspace"
    ]:

        if workspace_snapshot is None:

            workspace = (
                get_workspace_context()
            )

        else:

            workspace = (
                workspace_snapshot
            )

    else:

        workspace = None


    # -----------------------------------------------------------------------
    # Clipboard
    # -----------------------------------------------------------------------

    clipboard = (
        get_clipboard_context()

        if needs[
            "clipboard"
        ]

        else None
    )


    return {
        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "needs":
            needs,

        "system":
            system,

        "workspace":
            workspace,

        "clipboard":
            clipboard,
    }


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------

def format_active_application(
    system: dict,
):
    process = system.get(
        "active_process"
    )

    if not process:

        return "Unknown"

    return (
        process.get(
            "name"
        )
        or "Unknown"
    )


def format_visible_apps(
    system: dict,
):
    applications = (
        system.get(
            "visible_applications"
        )
        or []
    )

    if not applications:

        return (
            "No visible applications detected."
        )

    lines = []

    seen = set()

    for app in applications:

        name = (
            app.get(
                "process"
            )
            or "Unknown"
        )

        title = (
            app.get(
                "title"
            )
            or ""
        )

        key = (
            name.lower(),
            title.lower(),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        lines.append(
            f"- {name}: {title}"
        )

        if len(lines) >= 15:
            break

    return "\n".join(
        lines
    )


def format_terminal(
    system: dict,
):
    history = (
        system.get(
            "recent_terminal_history"
        )
        or []
    )

    processes = (
        system.get(
            "development_processes"
        )
        or []
    )


    history_text = (
        "\n".join(
            f"- {command}"

            for command
            in history
        )

        if history

        else (
            "No recent PowerShell "
            "history available."
        )
    )


    process_text = (
        "\n".join(
            (
                f"- {process['name']} "
                f"(PID {process['pid']})"
            )

            for process
            in processes
        )

        if processes

        else (
            "No notable development "
            "processes detected."
        )
    )


    return f"""
Recent shell history:
{history_text}

Development processes:
{process_text}
""".strip()


def format_open_workspaces(
    workspace_context: dict,
):
    workspaces = (
        workspace_context.get(
            "open_workspaces"
        )
        or []
    )

    if not workspaces:

        return (
            "No open VS Code workspaces detected."
        )

    blocks = []

    for workspace in workspaces:

        active_text = (
            "ACTIVE"

            if workspace.get(
                "active"
            )

            else "OPEN"
        )

        blocks.append(
            f"""
[{active_text}]

Workspace:
{workspace.get("workspace_name") or "Unknown"}

Path:
{workspace.get("workspace_path") or "Unresolved"}

Git branch:
{workspace.get("git_branch") or "Unknown"}

Window:
{workspace.get("window_title") or "Unknown"}
""".strip()
        )

    return "\n\n".join(
        blocks
    )


# ---------------------------------------------------------------------------
# Main Context Formatter
# ---------------------------------------------------------------------------

def format_live_context(
    context: dict,
):
    system = (
        context.get(
            "system"
        )
        or {}
    )

    workspace = (
        context.get(
            "workspace"
        )
    )

    needs = (
        context.get(
            "needs",
            {},
        )
    )

    sections = []


    # -----------------------------------------------------------------------
    # Core computer state
    # -----------------------------------------------------------------------

    sections.append(
        f"""
LIVE COMPUTER CONTEXT

Timestamp:
{context.get("timestamp")}

Active application:
{format_active_application(system)}

Active window:
{system.get("active_window") or "Unknown"}

Likely active file:
{system.get("active_file") or "Unknown"}
""".strip()
    )


    # -----------------------------------------------------------------------
    # Active workspace
    # -----------------------------------------------------------------------

    if workspace:

        modified = (
            workspace.get(
                "modified_files"
            )
            or []
        )


        modified_text = (
            "\n".join(
                f"- {file}"

                for file
                in modified
            )

            if modified

            else "None"
        )


        sections.append(
            f"""
ACTIVE WORKSPACE

Workspace:
{workspace.get("workspace_name") or "Unknown"}

Workspace path:
{workspace.get("workspace_path") or "Unknown"}

Git repository:
{workspace.get("git_repository") or "Not detected"}

Git branch:
{workspace.get("git_branch") or "Unknown"}

Modified files:
{modified_text}
""".strip()
        )


    # -----------------------------------------------------------------------
    # All VS Code Workspaces
    # -----------------------------------------------------------------------

    if (
        workspace
        and needs.get(
            "all_workspaces"
        )
    ):

        sections.append(
            f"""
OPEN VS CODE WORKSPACES

{format_open_workspaces(workspace)}
""".strip()
        )


    # -----------------------------------------------------------------------
    # Applications
    # -----------------------------------------------------------------------

    if needs.get(
        "applications"
    ):

        sections.append(
            f"""
VISIBLE APPLICATIONS

{format_visible_apps(system)}
""".strip()
        )


    # -----------------------------------------------------------------------
    # Terminal
    # -----------------------------------------------------------------------

    if needs.get(
        "terminal"
    ):

        sections.append(
            f"""
TERMINAL CONTEXT

{format_terminal(system)}
""".strip()
        )


    # -----------------------------------------------------------------------
    # Clipboard
    # -----------------------------------------------------------------------

    if needs.get(
        "clipboard"
    ):

        clipboard = (
            context.get(
                "clipboard"
            )

            or (
                "No text clipboard "
                "content."
            )
        )

        sections.append(
            f"""
CLIPBOARD CONTEXT

{clipboard}
""".strip()
        )


    return "\n\n".join(
        sections
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    test_message = (
        "What projects do I currently have open?"
    )

    snapshot = (
        get_workspace_context()
    )

    context = (
        get_live_context(
            user_message=
                test_message,

            workspace_snapshot=
                snapshot,
        )
    )

    print(
        format_live_context(
            context
        )
    )