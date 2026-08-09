"""
E.V.I.E. - Live Context Router

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Collects live computer awareness and selects which information
    should be supplied to E.V.I.E.'s reasoning model.

How It Works:
    Context is collected locally.

    Sensitive or noisy context such as clipboard contents and
    terminal history is only included when relevant to the user's
    current request.

Most Recent Change:
    Added context routing and reduced unnecessary context exposure.
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
# Routing
# ---------------------------------------------------------------------------

def determine_context_needs(
    user_message: str,
):
    """
    Returns which live-context sections are relevant.
    """

    text = user_message.lower()

    wants_clipboard = any(
        phrase in text
        for phrase in (
            "clipboard",
            "copied",
            "copy",
            "paste",
            "pasted",
        )
    )

    wants_terminal = any(
        phrase in text
        for phrase in (
            "terminal",
            "powershell",
            "command",
            "commands",
            "shell",
            "console",
            "history",
            "ran",
            "run last",
        )
    )

    wants_apps = any(
        phrase in text
        for phrase in (
            "applications",
            "application",
            "apps",
            "programs",
            "running",
            "open app",
            "open applications",
        )
    )

    wants_workspace = any(
        phrase in text
        for phrase in (
            "project",
            "workspace",
            "repo",
            "repository",
            "branch",
            "git",
            "modified",
            "changes",
            "working on",
            "file",
            "files",
            "coding",
        )
    )

    wants_system = any(
        phrase in text
        for phrase in (
            "what am i doing",
            "right now",
            "current",
            "active",
            "window",
            "application",
            "app",
            "what am i using",
            "what am i working on",
            "file",
        )
    )

    # Always provide a small core awareness layer.
    return {
        "system": True,

        "workspace": (
            wants_workspace
            or wants_system
        ),

        "applications":
            wants_apps,

        "terminal":
            wants_terminal,

        "clipboard":
            wants_clipboard,
    }


# ---------------------------------------------------------------------------
# Context Collection
# ---------------------------------------------------------------------------

def get_live_context(
    user_message: str,
):
    needs = determine_context_needs(
        user_message
    )

    system = (
        get_system_context()
    )

    workspace = (
        get_workspace_context()
        if needs["workspace"]
        else None
    )

    clipboard = (
        get_clipboard_context()
        if needs["clipboard"]
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
    system,
):
    process = system.get(
        "active_process"
    )

    if not process:
        return "Unknown"

    return (
        process.get("name")
        or "Unknown"
    )


def format_visible_apps(
    system,
):
    applications = (
        system.get(
            "visible_applications"
        )
        or []
    )

    if not applications:
        return "No visible applications detected."

    lines = []

    seen = set()

    for app in applications:
        name = (
            app.get("process")
            or "Unknown"
        )

        title = (
            app.get("title")
            or ""
        )

        key = (
            name.lower(),
            title.lower(),
        )

        if key in seen:
            continue

        seen.add(key)

        lines.append(
            f"- {name}: {title}"
        )

        if len(lines) >= 15:
            break

    return "\n".join(
        lines
    )


def format_terminal(
    system,
):
    history = (
        system.get(
            "recent_terminal_history"
        )
        or []
    )

    development_processes = (
        system.get(
            "development_processes"
        )
        or []
    )

    history_text = (
        "\n".join(
            f"- {command}"
            for command in history
        )
        if history
        else "No recent PowerShell history available."
    )

    processes_text = (
        "\n".join(
            (
                f"- {process['name']} "
                f"(PID {process['pid']})"
            )
            for process
            in development_processes
        )
        if development_processes
        else "No notable development processes detected."
    )

    return f"""
Recent shell history:
{history_text}

Development processes:
{processes_text}
""".strip()


# ---------------------------------------------------------------------------
# Human-Readable Context
# ---------------------------------------------------------------------------

def format_live_context(
    context: dict,
):
    system = context.get(
        "system"
    ) or {}

    workspace = context.get(
        "workspace"
    )

    needs = context.get(
        "needs",
        {},
    )

    sections = []


    # -----------------------------------------------------------------------
    # Core
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
    # Workspace
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
                for file in modified
            )
            if modified
            else "None"
        )

        sections.append(
            f"""
WORKSPACE CONTEXT

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
            or "No text clipboard content."
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
        "What project am I working on right now?"
    )

    context = get_live_context(
        test_message
    )

    print(
        format_live_context(
            context
        )
    )