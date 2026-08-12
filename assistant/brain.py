"""
E.V.I.E. - Intelligence / Reasoning Module

Created: August 7, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Handles E.V.I.E.'s reasoning and combines conversation,
    memory, perception, project knowledge, and visual intelligence.

How It Works:
    For every user request:

        1. Capture one computer/workspace snapshot.
        2. Load conversation history.
        3. Retrieve relevant long-term memory.
        4. Build live computer context from that snapshot.
        5. Select the intended workspace from that same snapshot.
        6. Retrieve relevant project knowledge.
        7. Send the unified context to the reasoning model.

Most Recent Change:
    Added Phase 6 controlled tool planning, permission-gated execution,
    approval sessions, and deterministic result verification.
"""

import json

from dotenv import load_dotenv
from openai import OpenAI


from .memory.database import (
    get_recent_conversations,
)

from .memory.retriever import (
    retrieve_memories,
)

from .intelligence.context import (
    record_tool_context,
)

from .perception.context import (
    format_live_context,
    get_live_context,
)

from .perception.workspace import (
    get_workspace_context,
)


from .knowledge.project import (
    format_project_overview,
    get_project_overview,
)

from .knowledge.retriever import (
    format_knowledge_results,
    retrieve_knowledge,
)

from .vision.context import (
    capture_visual_context,
    should_use_screen_vision,
)

from .vision.analyzer import (
    build_visual_input,
)

from .vision.lifecycle import (
    delete_visual_artifact,
)

from .tools.executor import (
    execute_tool,
)

from .tools.planner import (
    plan_tool_request,
    should_consider_tools,
)

from .tools.session import (
    classify_approval_response,
    clear_pending_action,
    get_pending_action,
    has_pending_action,
    set_pending_action,
    parse_approval_response,
)

from .tools.verifier import (
    verification_to_dict,
    verify_tool_result,
)

from .integrations.account_router import (
    route_accounts,
)

from .integrations.selection import (
    clear_pending_integration_selection,
    format_account_choices,
    get_pending_integration_selection,
    has_pending_integration_selection,
    resolve_account_selection,
    set_pending_integration_selection,
)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are E.V.I.E.

E.V.I.E. stands for Enhanced Virtual Intelligence Engine.

You are Max's personal AI assistant and engineering partner.

You are:
- calm
- intelligent
- direct
- observant
- natural
- concise unless additional detail is useful


MEMORY

You may receive:

1. Recent conversation history
2. Relevant ACTIVE long-term memories

Rules:

- The user's current message has highest priority.
- Active memories are more authoritative than stale conversation history.
- Forgotten or archived memories must not be treated as known.
- Never invent memories.
- If memory evidence is incomplete, say so.


LIVE COMPUTER CONTEXT

You may receive read-only computer context captured when the
current user request began.

It may contain:

- active application
- active window
- likely active file
- active workspace
- Git repository
- Git branch
- modified files
- all detected VS Code workspaces
- visible applications
- development processes
- recent terminal history
- clipboard when relevant

Use live context for questions about the computer's current state.


ATOMIC WORKSPACE SNAPSHOT

For each user request, E.V.I.E. receives one coherent workspace snapshot.

The active workspace and open-workspace list in that snapshot represent
the same observation in time.

Do not replace the selected workspace using assumptions from older
conversation history.


MULTI-WORKSPACE CONTEXT

Multiple VS Code projects may be open simultaneously.

ACTIVE means the workspace associated with the foreground VS Code
window at the time the snapshot was captured.

OPEN means another detected VS Code workspace.

When the user says:

"this project"
"current project"
"project I'm working on"
"what am I working on"

use the ACTIVE workspace.

When the user says:

"other project"
"other VS Code project"
"other workspace"
"the other one"

use the non-active workspace if there is one clear candidate.

When the user explicitly names a workspace, use that named workspace.

When the user asks:

"what projects are open?"
"which projects are open?"
"what projects do I have open?"
"show all projects"

describe all detected open VS Code workspaces.


PROJECT / FILE KNOWLEDGE

You may receive source-code or document chunks retrieved from the
selected workspace.

This is actual indexed local project content.

Use project knowledge for claims about:

- source code
- functions
- classes
- modules
- implementation
- architecture
- dependencies
- project behavior
- file contents

Retrieved project knowledge can contain:

DIRECT:
A chunk directly selected by semantic/lexical retrieval.

NEIGHBOR:
An adjacent chunk included for surrounding implementation context.

Use neighbor chunks to understand execution flow, but do not present
them as direct search matches.

When explaining runtime or cross-file flows:

- distinguish between functions that merely exist and functions that
  retrieved code actually shows are involved,
- follow visible calls between functions when possible,
- never infer that a semantically related function participates in a
  runtime path solely because it was retrieved,
- if the call chain is incomplete, say so instead of guessing.

VISUAL CONTEXT

E.V.I.E. may receive a fresh screenshot captured at the beginning
of the current request.

A screenshot is only provided when the user's request appears to
require visual inspection.

Visual context may contain:

- application interfaces
- source code
- terminals
- error messages
- dialogs
- websites
- images
- development tools
- desktop windows
- other visible screen content

Rules:

- Treat the screenshot as current visual evidence.
- Distinguish what is actually visible from what you infer.
- Do not claim to see content that is not visible.
- Use live computer metadata together with visual evidence.
- If visual evidence conflicts with older conversation history,
  prefer the current screenshot.
- If text is too small or unclear, say that it cannot be read
  confidently rather than inventing it.
- Do not claim that E.V.I.E. clicked, edited, opened, closed,
  or otherwise controlled anything. Phase 5 vision is read-only.
- When the user asks what is on the screen, prioritize the
  screenshot rather than relying only on application metadata.
- Visual input may be targeted to the desktop, active window, or
  a specific monitor. Interpret the image according to that target.
- Active-window captures should be treated as focused evidence about
  the foreground window rather than the entire desktop.
- Normal screenshots are temporary runtime artifacts and are deleted
  after the current reasoning request.

TOOL / COMPUTER CONTROL

E.V.I.E. may perform controlled computer actions through a registered
tool system.

Rules:

- Never claim an action happened unless the executor returned a result.
- Tool planning does not bypass the permission engine.
- Low-risk actions may execute automatically.
- Medium- and high-risk actions require explicit user approval.
- Approval applies only to the exact pending tool name, arguments, and
  selected workspace that were saved before the user approved it.
- If the user changes the subject instead of approving or rejecting a
  pending action, cancel that pending approval rather than silently
  executing it later.
- Prefer structured tools over terminal commands.
- Do not claim success when deterministic verification reports failure.
- Phase 6 performs one immediate tool action per request. Multi-step
  autonomous task execution belongs to a later phase.


CONTEXT PRIORITY

When context conflicts, generally use:

1. User's current message
2. Current visual evidence when vision was requested
3. Current atomic computer/workspace snapshot
4. Retrieved project/file knowledge
5. Active long-term memory
6. Recent conversation history


GENERAL BEHAVIOR

Address Max naturally when appropriate.

Never say you are ChatGPT.

Do not mention OpenAI unless directly asked about the current
reasoning implementation.
"""


# ---------------------------------------------------------------------------
# Conversation Context
# ---------------------------------------------------------------------------

def build_conversation_context(
    limit: int = 5,
):
    conversations = (
        get_recent_conversations(
            limit=limit
        )
    )

    if not conversations:

        return (
            "No recent conversation history."
        )


    formatted = []

    for user_message, response in conversations:

        formatted.append(
            f"User: {user_message}\n"
            f"E.V.I.E.: {response}"
        )


    return "\n\n".join(
        formatted
    )


# ---------------------------------------------------------------------------
# Long-Term Memory
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Memory Retrieval Routing
# ---------------------------------------------------------------------------

_MEMORY_REFERENCE_PHRASES = (
    "remember",
    "do you remember",
    "what did i",
    "what did we",
    "what was my",
    "what were my",
    "what have i",
    "what have we",
    "we talked about",
    "we discussed",
    "earlier",
    "before",
    "last time",
    "previously",
    "my preference",
    "my preferences",
    "my goal",
    "my goals",
    "my plan",
    "my plans",
    "my project",
    "my projects",
    "my research",
    "my application",
    "my applications",
    "my schedule",
    "my setup",
    "my server",
    "my portfolio",
    "my resume",
    "my gpa",
    "my classes",
    "my college",
    "my transfer",
)


def should_retrieve_long_term_memory(
    user_message: str,
):
    """
    Returns True when the current request appears to depend on
    persistent personal/project history.

    This is intentionally conservative:
    uncertain requests may still retrieve memory, while obviously
    context-free requests avoid the semantic-memory pipeline.
    """

    text = (
        user_message
        .strip()
        .lower()
    )

    if not text:
        return False

    if any(
        phrase in text
        for phrase in _MEMORY_REFERENCE_PHRASES
    ):
        return True

    # First-person possessive references often depend on persistent
    # user state even when no explicit "remember" phrase is present.
    personal_markers = (
        " my ",
        " mine ",
    )

    padded = f" {text} "

    if any(
        marker in padded
        for marker in personal_markers
    ):
        return True

    return False

def build_memory_context(
    user_message: str,
    limit: int = 5,
):
    try:

        memories = (
            retrieve_memories(
                query=
                    user_message,

                limit=
                    limit,
            )
        )

    except Exception as error:

        print(
            "\n[Memory Retrieval Warning]"
        )

        print(
            error
        )

        return (
            "Long-term memory retrieval "
            "is currently unavailable."
        )


    if not memories:

        return (
            "No relevant active "
            "long-term memories."
        )


    formatted = []

    for memory in memories:

        formatted.append(
            (
                f"[{memory['category']}] "
                f"{memory['content']}"
            )
        )


    return "\n".join(
        formatted
    )


# ---------------------------------------------------------------------------
# Active Workspace Record From Snapshot
# ---------------------------------------------------------------------------

def get_active_workspace_from_snapshot(
    workspace_snapshot: dict,
):
    """
    Converts the compatibility workspace context into the same
    record format used in open_workspaces.
    """

    workspaces = (
        workspace_snapshot.get(
            "open_workspaces"
        )
        or []
    )


    # Prefer explicit active record.
    for workspace in workspaces:

        if workspace.get(
            "active"
        ):

            return workspace


    # Fallback to top-level active workspace information.
    workspace_name = (
        workspace_snapshot.get(
            "workspace_name"
        )
    )

    if not workspace_name:

        return None


    return {
        "workspace_name":
            workspace_name,

        "workspace_path":
            workspace_snapshot.get(
                "workspace_path"
            ),

        "git_repository":
            workspace_snapshot.get(
                "git_repository"
            ),

        "git_branch":
            workspace_snapshot.get(
                "git_branch"
            ),

        "modified_files":
            workspace_snapshot.get(
                "modified_files",
                [],
            ),

        "window_title":
            None,

        "active":
            True,

        "resolved":
            bool(
                workspace_snapshot.get(
                    "workspace_path"
                )
            ),
    }


# ---------------------------------------------------------------------------
# Select Workspace From Snapshot
# ---------------------------------------------------------------------------

def select_workspace_for_query(
    user_message: str,
    workspace_snapshot: dict,
):
    """
    Resolves which workspace the user means WITHOUT performing a
    second Windows workspace scan.
    """

    text = (
        user_message.lower()
    )


    workspaces = (
        workspace_snapshot.get(
            "open_workspaces"
        )
        or []
    )


    active_workspace = (
        get_active_workspace_from_snapshot(
            workspace_snapshot
        )
    )


    # -----------------------------------------------------------------------
    # Explicitly named workspace
    # -----------------------------------------------------------------------

    for workspace in workspaces:

        name = (
            workspace.get(
                "workspace_name"
            )
            or ""
        )

        if (
            name
            and name.lower()
            in text
        ):

            return workspace


    # -----------------------------------------------------------------------
    # Other workspace
    # -----------------------------------------------------------------------

    other_phrases = (
        "other project",
        "other workspace",
        "other repo",
        "other repository",
        "other vscode",
        "other vs code",
        "the other one",
        "other one",
    )


    if any(
        phrase in text

        for phrase
        in other_phrases
    ):

        others = [
            workspace

            for workspace
            in workspaces

            if not workspace.get(
                "active"
            )
        ]


        # One obvious other workspace.
        if len(others) == 1:

            return others[0]


        # If multiple exist, return the first resolved candidate.
        if others:

            resolved_others = [
                workspace

                for workspace
                in others

                if workspace.get(
                    "workspace_path"
                )
            ]

            if resolved_others:

                return (
                    resolved_others[0]
                )

            return others[0]


    # -----------------------------------------------------------------------
    # Current / this project
    # -----------------------------------------------------------------------

    return active_workspace


# ---------------------------------------------------------------------------
# Tool Workspace Binding
# ---------------------------------------------------------------------------

WORKSPACE_SCOPED_TOOLS = {
    "list_directory",
    "read_file",
    "create_file",
    "write_file",
    "run_command",
    "run_python",
    "run_tests",
    "git_status",
    "git_diff",
    "git_log",
    "git_add",
    "git_commit",
    "git_push",
    "open_file_in_vscode",
    "open_workspace_in_vscode",
}


def bind_workspace_to_tool_arguments(
    tool_name: str,
    arguments: dict,
    user_message: str,
):
    """
    Binds the exact selected workspace to a tool request.

    This prevents a delayed approval from acting on a different
    workspace if the foreground VS Code window changes.
    """

    bound = dict(
        arguments
        or {}
    )

    if tool_name not in WORKSPACE_SCOPED_TOOLS:

        return bound

    if bound.get(
        "workspace_path"
    ):

        return bound

    snapshot = (
        get_workspace_context()
    )

    selected = (
        select_workspace_for_query(
            user_message=
                user_message,

            workspace_snapshot=
                snapshot,
        )
    )

    if not selected:

        return bound

    workspace_path = (
        selected.get(
            "workspace_path"
        )
    )

    if workspace_path:

        bound[
            "workspace_path"
        ] = workspace_path

    return bound


# ---------------------------------------------------------------------------
# Tool Response Rendering
# ---------------------------------------------------------------------------

def render_tool_result_response(
    user_message: str,
    tool_name: str,
    arguments: dict,
    execution: dict,
    verification,
):
    """
    Converts deterministic tool output into a concise natural-language
    E.V.I.E. response.

    The model is not allowed to reinterpret failure as success.
    """

    payload = {
        "tool":
            tool_name,

        "arguments":
            arguments,

        "execution":
            execution,

        "verification":
            verification_to_dict(
                verification
            ),
    }

    instructions = """
You are E.V.I.E. reporting the result of one computer tool action.

Use only the supplied tool execution and verification data.

Rules:
- If verification.successful is false, clearly say the action did not
  succeed.
- Never claim that an unexecuted or blocked action happened.
- If stdout/stderr or Git output is relevant, summarize it accurately.
- Be concise.
- Do not expose internal JSON unless the user asked for raw output.
"""

    try:

        response = client.responses.create(
            model="gpt-5.5",
            instructions=instructions,
            input=(
                f"USER REQUEST:\n{user_message}\n\n"
                "TOOL RESULT:\n"
                f"{json.dumps(payload, ensure_ascii=False, default=str)}"
            ),
        )

        reply = (
            response.output_text.strip()
        )

        if reply:

            return reply

    except Exception as error:

        print(
            "\n[Tool Result Response Warning]"
        )

        print(
            error
        )

    # Deterministic fallback.
    if verification.successful:

        return (
            f"{tool_name} completed successfully."
        )

    return (
        f"{tool_name} did not complete successfully: "
        f"{verification.summary}"
    )

# ---------------------------------------------------------------------------
# Integration Write Preflight
# ---------------------------------------------------------------------------

def preflight_integration_action(
    user_message: str,
    tool_name: str,
    arguments: dict,
    summary: str = "",
):
    """
    Resolves ambiguous Phase 9 accounts BEFORE requesting write approval.

    Returns:
        None
            No special handling needed.

        dict
            A response that should be returned directly by
            handle_tool_request().
    """

    if (
        tool_name
        != "integration_execute"
    ):

        return None


    cleaned = dict(
        arguments
    )


    # Approval belongs to execute_tool(), never the planner.
    cleaned.pop(
        "approved",
        None,
    )


    capability = (
        str(
            cleaned.get(
                "capability",
                "",
            )
        )
        .strip()
        .lower()
    )


    if not capability:

        return None


    # -----------------------------------------------------------------------
    # Already Explicit
    # -----------------------------------------------------------------------
    #
    # If the planner/user supplied an account, the request MUST become
    # explicit-account routing. Never allow account_id + all_available.
    # -----------------------------------------------------------------------

    if cleaned.get(
        "account_id"
    ):

        provider = (
            cleaned.get(
                "provider"
            )
        )


        if provider:

            cleaned[
                "provider"
            ] = (
                str(
                    provider
                )
                .strip()
                .lower()
            )


        cleaned[
            "account_id"
        ] = (
            str(
                cleaned[
                    "account_id"
                ]
            )
            .strip()
        )


        cleaned[
            "routing_mode"
        ] = "explicit_account"


        arguments.clear()

        arguments.update(
            cleaned
        )


        return None


    # -----------------------------------------------------------------------
    # Determine Eligible Accounts
    # -----------------------------------------------------------------------

    provider = (
        cleaned.get(
            "provider"
        )
    )


    if provider:

        provider = (
            str(
                provider
            )
            .strip()
            .lower()
        )


        cleaned[
            "provider"
        ] = provider


    routed = route_accounts(
        capability=
            capability,

        mode=
            "all_available",

        provider=
            provider,

        account_id=
            None,
    )


    # -----------------------------------------------------------------------
    # No Accounts
    # -----------------------------------------------------------------------

    if not routed:

        arguments.clear()

        arguments.update(
            cleaned
        )

        return None


    # -----------------------------------------------------------------------
    # Exactly One Account
    #
    # Bind it BEFORE approval.
    # -----------------------------------------------------------------------

    if len(
        routed
    ) == 1:

        selected = (
            routed[
                0
            ]
        )


        cleaned[
            "provider"
        ] = selected.provider


        cleaned[
            "account_id"
        ] = selected.account_id


        cleaned[
            "routing_mode"
        ] = "explicit_account"


        arguments.clear()

        arguments.update(
            cleaned
        )


        return None


    # -----------------------------------------------------------------------
    # Multiple Accounts
    #
    # Reads may legitimately aggregate.
    # Writes require account selection.
    # -----------------------------------------------------------------------

    from .integrations.permissions import (
        get_permission as
        get_integration_permission,
    )


    permission = (
        get_integration_permission(
            capability
        )
    )


    risk = (
        getattr(
            permission,
            "risk",
            "high",
        )
        if permission
        is not None
        else "high"
    )


    if (
        str(
            risk
        )
        .lower()
        == "low"
    ):

        arguments.clear()

        arguments.update(
            cleaned
        )

        return None


    pending = (
        set_pending_integration_selection(
            tool_name=
                tool_name,

            capability=
                capability,

            arguments=
                cleaned,

            routed_accounts=
                routed,

            summary=
                summary,

            original_request=
                user_message,
        )
    )


    choices = (
        format_account_choices(
            pending
        )
    )


    return {
        "handled":
            True,

        "response": (
            "I can perform that action using more than one "
            "connected account.\n\n"
            f"{choices}\n\n"
            "Which account should I use? "
            "You can say the number, email address, "
            "\"personal\", or \"school\"."
        ),

        "approval_required":
            False,
    }

# ---------------------------------------------------------------------------
# New Tool Requests
# ---------------------------------------------------------------------------

def handle_tool_request(
    user_message: str,
):
    """
    Plans and executes at most one immediate computer action.

    Returns:
        {
            "handled": bool,
            "response": str | None,
            "approval_required": bool,
        }
    """

    if not should_consider_tools(
        user_message
    ):

        return {
            "handled":
                False,

            "response":
                None,

            "approval_required":
                False,
        }

    plan = (
        plan_tool_request(
            user_message
        )
    )

    if (
        not plan.use_tool
        or not plan.tool_name
        or plan.confidence < 60
    ):

        return {
            "handled":
                False,

            "response":
                None,

            "approval_required":
                False,
        }

    arguments = (
        bind_workspace_to_tool_arguments(
            tool_name=
                plan.tool_name,

            arguments=
                plan.arguments,

            user_message=
                user_message,
        )
    )

        # -----------------------------------------------------------------------
    # Planner-Owned Approval Is Forbidden
    # -----------------------------------------------------------------------

    if (
        plan.tool_name
        == "integration_execute"
    ):

        arguments.pop(
            "approved",
            None,
        )


    # -----------------------------------------------------------------------
    # Phase 9 Account Preflight
    # -----------------------------------------------------------------------

    preflight = (
        preflight_integration_action(
            user_message=
                user_message,

            tool_name=
                plan.tool_name,

            arguments=
                arguments,

            summary=
                plan.summary,
        )
    )


    if preflight is not None:

        return preflight

    print(
        "\n[Tool Planner]"
    )

    print(
        "Tool:",
        plan.tool_name,
    )

    print(
        "Arguments:",
        arguments,
    )

    print(
        "Confidence:",
        plan.confidence,
    )

    execution = (
        execute_tool(
            tool_name=
                plan.tool_name,

            arguments=
                arguments,

            approved=
                False,
        )
    )

    if (
        not execution.get(
            "executed",
            False,
        )
        and execution.get(
            "requires_approval",
            False,
        )
    ):

        pending = (
            set_pending_action(
                tool_name=
                    plan.tool_name,

                arguments=
                    arguments,

                risk=
                    execution.get(
                        "risk",
                        "unknown",
                    ),

                summary=
                    (
                        plan.summary
                        or (
                            f"Execute {plan.tool_name}."
                        )
                    ),

                original_request=
                    user_message,
            )
        )

        response = (
            f"This action is {pending.risk}-risk and requires "
            f"your approval.\n\n"
            f"Planned action: {pending.summary}\n"
            f"Tool: {pending.tool_name}\n\n"
            "Approve it? Say yes to proceed or no to cancel."
        )

        return {
            "handled":
                True,

            "response":
                response,

            "approval_required":
                True,
        }

    verification = (
        verify_tool_result(
            execution
        )
    )

    # -----------------------------------------------------------------------
    # Phase 10B - Record Successfully Verified Context
    # -----------------------------------------------------------------------

    if verification.successful:

        record_tool_context(
            tool_name=
                plan.tool_name,

            arguments=
                arguments,

            user_request=
                user_message,
        )

    response = (
        render_tool_result_response(
            user_message=
                user_message,

            tool_name=
                plan.tool_name,

            arguments=
                arguments,

            execution=
                execution,

            verification=
                verification,
        )
    )

    return {
        "handled":
            True,

        "response":
            response,

        "approval_required":
            False,
    }

# ---------------------------------------------------------------------------
# Pending Integration Account Selection
# ---------------------------------------------------------------------------

def handle_pending_integration_selection(
    user_message: str,
):
    """
    Resolves a temporary Phase 9 account-selection request.

    Crucially this runs before memory processing.

    Selecting an account here is NOT interpreted as a durable user
    preference.
    """

    if not has_pending_integration_selection():

        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }


    pending = (
        get_pending_integration_selection()
    )


    if pending is None:

        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }


    text = (
        user_message
        .strip()
        .lower()
    )


    # -----------------------------------------------------------------------
    # Cancel
    # -----------------------------------------------------------------------

    if text in {
        "no",
        "cancel",
        "never mind",
        "nevermind",
        "stop",
    }:

        clear_pending_integration_selection()


        return {
            "handled":
                True,

            "response":
                "Cancelled. I did not perform the integration action.",

            "follow_up":
                "",
        }


    # -----------------------------------------------------------------------
    # Resolve Account
    # -----------------------------------------------------------------------

    selected = (
        resolve_account_selection(
            pending,
            user_message,
        )
    )


    if selected is None:

        choices = (
            format_account_choices(
                pending
            )
        )


        return {
            "handled":
                True,

            "response": (
                "I couldn't match that to one of the available "
                "accounts.\n\n"
                f"{choices}\n\n"
                "Which account should I use?"
            ),

            "follow_up":
                "",
        }


    # Selection is resolved.
    clear_pending_integration_selection()


    arguments = dict(
        pending.arguments
    )


    arguments.pop(
        "approved",
        None,
    )


    arguments[
        "provider"
    ] = (
        selected[
            "provider"
        ]
    )


    arguments[
        "account_id"
    ] = (
        selected[
            "account_id"
        ]
    )


    arguments[
        "routing_mode"
    ] = (
        "explicit_account"
    )


    # -----------------------------------------------------------------------
    # Run Through Normal Phase 6 Boundary
    # -----------------------------------------------------------------------

    execution = (
        execute_tool(
            tool_name=
                pending.tool_name,

            arguments=
                arguments,

            approved=
                False,
        )
    )


    # -----------------------------------------------------------------------
    # Approval Required
    # -----------------------------------------------------------------------

    if (
        not execution.get(
            "executed",
            False,
        )
        and execution.get(
            "requires_approval",
            False,
        )
    ):

        saved = (
            set_pending_action(
                tool_name=
                    pending.tool_name,

                arguments=
                    arguments,

                risk=
                    execution.get(
                        "risk",
                        "unknown",
                    ),

                summary=(
                    pending.summary
                    or (
                        f"Execute "
                        f"{pending.capability}."
                    )
                ),

                original_request=
                    pending.original_request,
            )
        )


        account_label = (
            selected.get(
                "email"
            )
            or selected.get(
                "account_id"
            )
        )


        return {
            "handled":
                True,

            "response": (
                f"Using {account_label}.\n\n"
                f"This action is {saved.risk}-risk and requires "
                "your approval.\n\n"
                f"Planned action: {saved.summary}\n"
                f"Tool: {saved.tool_name}\n\n"
                "Approve it? Say yes to proceed or no to cancel."
            ),

            "follow_up":
                "",
        }


    # -----------------------------------------------------------------------
    # Unexpected Immediate Execution
    # -----------------------------------------------------------------------

    verification = (
        verify_tool_result(
            execution
        )
    )

    # -----------------------------------------------------------------------
    # Phase 10B - Record Successfully Selected Integration Context
    # -----------------------------------------------------------------------

    if verification.successful:

        record_tool_context(
            tool_name=
                pending.tool_name,

            arguments=
                arguments,

            user_request=
                pending.original_request,
        )


    response = (
        render_tool_result_response(
            user_message=
                pending.original_request,

            tool_name=
                pending.tool_name,

            arguments=
                arguments,

            execution=
                execution,

            verification=
                verification,
        )
    )


    return {
        "handled":
            True,

        "response":
            response,

        "follow_up":
            "",
    }

# ---------------------------------------------------------------------------
# Pending Approval
# ---------------------------------------------------------------------------

def handle_pending_tool_approval(
    user_message: str,
):
    """
    Handles approval/rejection for one exact pending action.

    Compound replies are supported:

        "Yes, then show me Git status."

    The pending action executes first. Any text after the approval
    is returned to main.py as a separate follow-up request.

    An unrelated reply cancels the old pending action and continues
    normally.
    """

    if not has_pending_action():

        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }


    parsed = (
        parse_approval_response(
            user_message
        )
    )


    # -----------------------------------------------------------------------
    # Unrelated Reply
    # -----------------------------------------------------------------------

    if parsed.decision == "other":

        clear_pending_action()

        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }


    pending = (
        clear_pending_action()
    )


    if pending is None:

        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }


    # -----------------------------------------------------------------------
    # Reject
    # -----------------------------------------------------------------------

    if parsed.decision == "reject":

        return {
            "handled":
                True,

            "response":
                (
                    f"Cancelled. I did not execute "
                    f"{pending.tool_name}."
                ),

            "follow_up":
                parsed.remainder,
        }


    # -----------------------------------------------------------------------
    # Approve
    # -----------------------------------------------------------------------

    print(
        "\n[Tool Approval]"
    )

    print(
        "Approved tool:",
        pending.tool_name,
    )

    print(
        "Risk:",
        pending.risk,
    )


    execution = (
        execute_tool(
            tool_name=
                pending.tool_name,

            arguments=
                pending.arguments,

            approved=
                True,
        )
    )


    verification = (
        verify_tool_result(
            execution
        )
    )

    # -----------------------------------------------------------------------
    # Phase 10B - Record Successfully Approved Context
    # -----------------------------------------------------------------------

    if verification.successful:

        record_tool_context(
            tool_name=
                pending.tool_name,

            arguments=
                pending.arguments,

            user_request=
                pending.original_request,
        )

    response = (
        render_tool_result_response(
            user_message=
                pending.original_request,

            tool_name=
                pending.tool_name,

            arguments=
                pending.arguments,

            execution=
                execution,

            verification=
                verification,
        )
    )


    return {
        "handled":
            True,

        "response":
            response,

        "follow_up":
            parsed.remainder,
    }


# ---------------------------------------------------------------------------
# Live Computer Context
# ---------------------------------------------------------------------------

def build_live_context(
    user_message: str,
    workspace_snapshot: dict,
):
    """
    Builds live context using the workspace snapshot already captured
    for this request.
    """

    try:

        context = get_live_context(
            user_message=
                user_message,

            workspace_snapshot=
                workspace_snapshot,
        )


        return format_live_context(
            context
        )


    except Exception as error:

        print(
            "\n[Perception Warning]"
        )

        print(
            error
        )

        return (
            "Live computer context is "
            "currently unavailable."
        )


# ---------------------------------------------------------------------------
# Knowledge Routing
# ---------------------------------------------------------------------------

def should_use_project_knowledge(
    user_message: str,
):
    text = (
        user_message.lower()
    )


    triggers = (
        "project",
        "repo",
        "repository",

        "code",
        "source",

        "function",
        "functions",

        "class",
        "classes",

        "implementation",
        "implemented",

        "how does",
        "how do",

        "where is",
        "where does",

        "read",
        "file",
        "files",

        "module",
        "modules",

        "architecture",

        "dependency",
        "dependencies",

        "import",

        "bug",
        "error",

        "script",

        "homepage",
        "website",

        "stylesheet",
        "css",
        "html",

        "find",
        "explain",
    )


    return any(
        trigger in text

        for trigger
        in triggers
    )


# ---------------------------------------------------------------------------
# Project Knowledge
# ---------------------------------------------------------------------------

def build_knowledge_context(
    user_message: str,
    workspace_snapshot: dict,
):
    """
    Selects a workspace from the SAME snapshot used by perception,
    then retrieves project knowledge from that workspace.
    """

    if not should_use_project_knowledge(
        user_message
    ):

        return (
            "Project knowledge was not "
            "required for this request."
        )


    try:

        selected_workspace = (
            select_workspace_for_query(
                user_message=
                    user_message,

                workspace_snapshot=
                    workspace_snapshot,
            )
        )


        if not selected_workspace:

            return (
                "No workspace could be "
                "selected for project retrieval."
            )


        workspace_name = (
            selected_workspace.get(
                "workspace_name"
            )
            or "Unknown"
        )


        workspace_path = (
            selected_workspace.get(
                "workspace_path"
            )
        )


        if not workspace_path:

            return (
                f"The workspace "
                f"{workspace_name} "
                f"was detected, but its local "
                f"path could not be resolved."
            )


        # -------------------------------------------------------------------
        # Project overview
        # -------------------------------------------------------------------

        overview = (
            get_project_overview(
                workspace_path=
                    workspace_path
            )
        )


        overview_text = (
            format_project_overview(
                overview
            )
        )


        # -------------------------------------------------------------------
        # File knowledge
        # -------------------------------------------------------------------

        results = (
            retrieve_knowledge(
                query=
                    user_message,

                limit=
                    6,

                workspace_path=
                    workspace_path,

                ensure_index=
                    True,

                expand_context=
                    True,
            )
        )


        knowledge_text = (
            format_knowledge_results(
                results
            )

            if results

            else (
                "No relevant project "
                "chunks were found."
            )
        )


        return f"""
SELECTED WORKSPACE

Name:
{workspace_name}

Path:
{workspace_path}

Active in captured snapshot:
{selected_workspace.get("active")}


{overview_text}


RELEVANT PROJECT FILE KNOWLEDGE

{knowledge_text}
""".strip()


    except Exception as error:

        print(
            "\n[Knowledge Warning]"
        )

        print(
            error
        )

        return (
            "Project file knowledge is "
            "currently unavailable."
        )

# ---------------------------------------------------------------------------
# Visual Context
# ---------------------------------------------------------------------------

def build_visual_context(
    user_message: str,
):
    """
    Captures and prepares fresh visual context when required.

    The visual router chooses between:
        - desktop
        - active window
        - specific monitor

    Returns:
        tuple:
            visual_context_text
            visual_input
    """

    if not should_use_screen_vision(
        user_message
    ):

        return (
            "Screen vision was not required "
            "for this request.",
            None,
        )

    visual_context = None

    try:

        visual_context = (
            capture_visual_context(
                user_message
            )
        )

        if not visual_context:

            return (
                "Screen vision was requested, "
                "but no screenshot was captured.",
                None,
            )

        visual_input = (
            build_visual_input(
                visual_context
            )
        )

        if not visual_input:

            delete_visual_artifact(
                visual_context.get(
                    "screenshot_path"
                )
            )

            return (
                "A screenshot was captured, "
                "but it could not be prepared "
                "for visual reasoning.",
                None,
            )

        monitor_text = (
            str(
                visual_input[
                    "monitor_index"
                ]
            )

            if visual_input.get(
                "monitor_index"
            )

            else "Not specifically targeted"
        )

        active_window_text = (
            visual_input.get(
                "active_window_title"
            )
            or "Unknown"
        )

        visual_context_text = f"""
VISUAL CONTEXT

A fresh temporary screenshot was captured for this request.

Requested target:
{visual_input["requested_target"]}

Actual capture source:
{visual_input["source"]}

Active window at capture time:
{active_window_text}

Monitor:
{monitor_text}

Original screenshot resolution:
{visual_input["width"]}x{visual_input["height"]}

Prepared model resolution:
{visual_input["prepared_width"]}x{visual_input["prepared_height"]}

Fresh:
{visual_input["fresh"]}

Use the attached screenshot as current visual evidence.

The screenshot is temporary runtime context and will be deleted
after this reasoning request completes.
""".strip()

        return (
            visual_context_text,
            visual_input,
        )

    except Exception as error:

        print(
            "\n[Vision Warning]"
        )

        print(
            error
        )

        if visual_context:

            delete_visual_artifact(
                visual_context.get(
                    "screenshot_path"
                )
            )

        return (
            "Screen vision was requested, "
            "but visual context is currently "
            "unavailable.",
            None,
        )


# ---------------------------------------------------------------------------
# Combined Context
# ---------------------------------------------------------------------------

def build_context(
    user_message: str,
):
    """
    Captures workspace state ONCE and sends that same snapshot to
    perception and knowledge routing.
    """

    # -----------------------------------------------------------------------
    # ATOMIC WORKSPACE SNAPSHOT
    # -----------------------------------------------------------------------

    try:

        workspace_snapshot = (
            get_workspace_context()
        )

    except Exception as error:

        print(
            "\n[Workspace Snapshot Warning]"
        )

        print(
            error
        )

        workspace_snapshot = {}


    # -----------------------------------------------------------------------
    # Other context sources
    # -----------------------------------------------------------------------

    conversation_context = (
        build_conversation_context(
            limit=5
        )
    )


    if should_retrieve_long_term_memory(
        user_message
    ):

        memory_context = (
            build_memory_context(
                user_message=
                    user_message,

                limit=5,
            )
        )

    else:

        memory_context = (
            "Long-term memory retrieval was not "
            "required for this request."
        )


    live_context = (
        build_live_context(
            user_message=
                user_message,

            workspace_snapshot=
                workspace_snapshot,
        )
    )


    knowledge_context = (
        build_knowledge_context(
            user_message=
                user_message,

            workspace_snapshot=
                workspace_snapshot,
        )
    )

    visual_context, visual_input = (
        build_visual_context(
            user_message
        )
    )


    context_text = f"""
RECENT CONVERSATION HISTORY

{conversation_context}


RELEVANT ACTIVE LONG-TERM MEMORY

{memory_context}


{live_context}


PROJECT / FILE KNOWLEDGE

{knowledge_context}


{visual_context}
""".strip()

    return (
        context_text,
        visual_input,
    )

# ---------------------------------------------------------------------------
# Main Chat
# ---------------------------------------------------------------------------

def chat(
    user_message: str,
):
    """
    Main E.V.I.E. reasoning entry point.

    Supports:
        - normal text-only reasoning
        - routed multimodal screen reasoning

    Temporary screenshots are deleted in a finally block whether
    reasoning succeeds, fails, or returns an empty response.
    """

    user_message = (
        user_message.strip()
    )

    if not user_message:

        return (
            "I didn't receive a message."
        )

    visual_input = None

    try:

        # -------------------------------------------------------------------
        # Build Unified Context
        # -------------------------------------------------------------------

        context, visual_input = (
            build_context(
                user_message
            )
        )

        # -------------------------------------------------------------------
        # Developer Context
        # -------------------------------------------------------------------

        developer_message = (
            "The following information "
            "comes from E.V.I.E.'s local "
            "memory, computer perception, "
            "workspace, project knowledge, "
            "and vision systems. "
            "All current workspace information "
            "was captured from one coherent "
            "snapshot for this request. "
            "When visual context is attached, "
            "treat the screenshot as fresh "
            "visual evidence from the current "
            "request and interpret it according "
            "to the stated visual target. "
            "Use only information relevant to "
            "the user's request."
            "\n\n"
            f"{context}"
        )

        # -------------------------------------------------------------------
        # User Content
        # -------------------------------------------------------------------

        if visual_input:

            print(
                "\n[Vision]"
            )

            print(
                "Target:",
                visual_input[
                    "requested_target"
                ],
            )

            print(
                "Capture source:",
                visual_input[
                    "source"
                ],
            )

            print(
                "Fresh screenshot attached:"
            )

            print(
                visual_input[
                    "screenshot_path"
                ]
            )

            user_content = [
                {
                    "type":
                        "input_text",

                    "text":
                        user_message,
                },

                {
                    "type":
                        "input_image",

                    "image_url":
                        visual_input[
                            "image_url"
                        ],
                },
            ]

        else:

            user_content = (
                user_message
            )

        # -------------------------------------------------------------------
        # Reasoning Request
        # -------------------------------------------------------------------

        try:

            response = (
                client.responses.create(
                    model=
                        "gpt-5.5",

                    instructions=
                        SYSTEM_PROMPT,

                    input=[
                        {
                            "role":
                                "developer",

                            "content":
                                developer_message,
                        },

                        {
                            "role":
                                "user",

                            "content":
                                user_content,
                        },
                    ],
                )
            )

        except Exception as error:

            print(
                "\n[Reasoning Error]"
            )

            print(
                error
            )

            return (
                "I encountered an error while "
                "processing that request."
            )

        # -------------------------------------------------------------------
        # Response
        # -------------------------------------------------------------------

        reply = (
            response.output_text.strip()
        )

        if not reply:

            return (
                "I wasn't able to generate "
                "a response."
            )

        return reply

    finally:

        if (
            visual_input
            and visual_input.get(
                "temporary",
                True,
            )
        ):

            screenshot_path = (
                visual_input.get(
                    "screenshot_path"
                )
            )

            deleted = (
                delete_visual_artifact(
                    screenshot_path
                )
            )

            if screenshot_path:

                print(
                    "\n[Vision Cleanup]"
                )

                if deleted:

                    print(
                        "Temporary screenshot deleted."
                    )

                else:

                    print(
                        "Temporary screenshot was already "
                        "absent or could not be deleted."
                    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Brain Test"
    )

    print(
        "--------------------"
    )


    while True:

        user_message = (
            input(
                "You: "
            )
            .strip()
        )


        if user_message.lower() in {
            "quit",
            "exit",
        }:

            break


        response = (
            chat(
                user_message
            )
        )


        print(
            f"\nE.V.I.E.: "
            f"{response}\n"
        )