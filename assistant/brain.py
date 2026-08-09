"""
E.V.I.E. - Intelligence / Reasoning Module

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Handles E.V.I.E.'s reasoning and combines conversation,
    memory, perception, and project knowledge.

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
    Added atomic workspace snapshots so perception and project
    knowledge cannot disagree about which workspace was active
    during a single request.
"""

from dotenv import load_dotenv
from openai import OpenAI


from .memory.database import (
    get_recent_conversations,
)

from .memory.retriever import (
    retrieve_memories,
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


CONTEXT PRIORITY

When context conflicts, generally use:

1. User's current message
2. Current atomic computer/workspace snapshot
3. Retrieved project/file knowledge
4. Active long-term memory
5. Recent conversation history


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


    memory_context = (
        build_memory_context(
            user_message=
                user_message,

            limit=5,
        )
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


    return f"""
RECENT CONVERSATION HISTORY

{conversation_context}


RELEVANT ACTIVE LONG-TERM MEMORY

{memory_context}


{live_context}


PROJECT / FILE KNOWLEDGE

{knowledge_context}
""".strip()


# ---------------------------------------------------------------------------
# Main Chat
# ---------------------------------------------------------------------------

def chat(
    user_message: str,
):
    user_message = (
        user_message.strip()
    )


    if not user_message:

        return (
            "I didn't receive a message."
        )


    context = (
        build_context(
            user_message
        )
    )


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
                        (
                            "The following information "
                            "comes from E.V.I.E.'s local "
                            "memory, computer perception, "
                            "workspace, and project knowledge "
                            "systems. All current workspace "
                            "information was captured from one "
                            "coherent snapshot for this request. "
                            "Use only information relevant to "
                            "the user's current request."
                            "\n\n"
                            f"{context}"
                        ),
                },

                {
                    "role":
                        "user",

                    "content":
                        user_message,
                },
            ],
        )
    )


    reply = (
        response.output_text.strip()
    )


    if not reply:

        return (
            "I wasn't able to generate "
            "a response."
        )


    return reply


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