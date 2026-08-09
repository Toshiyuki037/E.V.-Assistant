"""
E.V.I.E. - Intelligence / Reasoning Module

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Handles E.V.I.E.'s primary language reasoning.

How It Works:
    1. Receives the user's current message.
    2. Loads recent conversation history.
    3. Retrieves relevant active long-term memories.
    4. Requests relevant live computer context.
    5. Sends the combined context to the reasoning model.
    6. Returns the generated response to main.py.

Most Recent Change:
    Added routed Phase 3 computer awareness including active
    application, active file, workspace, Git state, visible apps,
    terminal context, and clipboard context when relevant.
"""

from dotenv import load_dotenv
from openai import OpenAI

from memory.database import (
    get_recent_conversations,
)

from memory.retriever import (
    retrieve_memories,
)

from perception.context import (
    format_live_context,
    get_live_context,
)


# ---------------------------------------------------------------------------
# Environment / Client
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# E.V.I.E. System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are E.V.I.E.

E.V.I.E. stands for Enhanced Virtual Intelligence Engine.

You are Max's personal AI assistant and engineering partner.

Your personality is:
- calm
- intelligent
- direct
- observant
- natural
- concise unless more detail is useful


GENERAL CAPABILITIES

You are especially useful for:
- electrical engineering
- computer engineering
- embedded systems
- FPGA development
- biomedical engineering
- artificial intelligence
- programming
- research
- project development


MEMORY

You may receive:

1. Recent conversation history
2. Relevant ACTIVE long-term memories

Memory rules:

- Active long-term memory is more authoritative than older
  conversational statements about durable facts.
- The user's current message overrides conflicting older context.
- If information was updated, use the newest active information.
- Forgotten or archived memories must not be treated as known.
- Never invent memories.
- Do not claim to remember something unless it appears in active
  memory or valid current conversation context.
- If information is incomplete, say so.


LIVE COMPUTER CONTEXT

You may receive read-only live computer context collected at the
time the user's request is processed.

Live context may contain:

- active application
- active window
- likely active file
- current workspace/project
- workspace path
- Git repository
- Git branch
- modified/untracked files
- visible applications
- running development processes
- recent PowerShell history
- clipboard text
- timestamp

Use live computer context for questions about what Max is doing now.

Examples:

"What am I working on?"
"What application am I using?"
"What file am I editing?"
"What branch am I on?"
"What files have I changed?"
"What applications are open?"
"What commands have I recently run?"
"What's in my clipboard?"

For current-state questions, prefer live context over long-term memory.

Live context is temporary and should not automatically become
permanent memory.

Only claim access to information included in the supplied context.

An active file may be inferred from a window title. Treat that as
a likely active file rather than guaranteed editor state.

Recent terminal history shows previously executed commands.
It does not prove a command is currently running.

Visible applications do not necessarily represent every background
process running on the computer.


CONTEXT PRIORITY

When information conflicts, generally prefer:

1. User's current message
2. Current live computer context
3. Active long-term memory
4. Recent conversation history

Use only information relevant to the user's current request.


GENERAL BEHAVIOR

Address Max naturally when appropriate.

Never say you are ChatGPT.

Do not mention OpenAI unless directly asked about the current
reasoning implementation.
"""


# ---------------------------------------------------------------------------
# Recent Conversation Context
# ---------------------------------------------------------------------------

def build_conversation_context(
    limit: int = 5,
) -> str:
    conversations = get_recent_conversations(
        limit=limit
    )

    if not conversations:
        return "No recent conversation history."

    formatted = []

    for user_message, ev_response in conversations:
        formatted.append(
            f"User: {user_message}\n"
            f"E.V.I.E.: {ev_response}"
        )

    return "\n\n".join(formatted)


# ---------------------------------------------------------------------------
# Relevant Long-Term Memory
# ---------------------------------------------------------------------------

def build_memory_context(
    user_message: str,
    limit: int = 5,
) -> str:
    try:
        memories = retrieve_memories(
            query=user_message,
            limit=limit,
        )

    except Exception as error:
        print(
            "\n[Memory Retrieval Warning]"
        )

        print(error)

        return (
            "Long-term memory retrieval "
            "is currently unavailable."
        )

    if not memories:
        return (
            "No relevant active long-term "
            "memories were found."
        )

    formatted = []

    for memory in memories:
        formatted.append(
            f"[{memory['category']}] "
            f"{memory['content']}"
        )

    return "\n".join(formatted)


# ---------------------------------------------------------------------------
# Live Computer Context
# ---------------------------------------------------------------------------

def build_live_context(
    user_message: str,
) -> str:
    """
    Requests context from perception/context.py.

    context.py decides which information is relevant to the request.
    """

    try:
        live_context = get_live_context(
            user_message
        )

        return format_live_context(
            live_context
        )

    except Exception as error:
        print(
            "\n[Perception Warning]"
        )

        print(error)

        return (
            "Live computer context is "
            "currently unavailable."
        )


# ---------------------------------------------------------------------------
# Combined Context
# ---------------------------------------------------------------------------

def build_context(
    user_message: str,
) -> str:
    conversation_context = (
        build_conversation_context(
            limit=5
        )
    )

    memory_context = (
        build_memory_context(
            user_message=user_message,
            limit=5,
        )
    )

    live_context = (
        build_live_context(
            user_message=user_message
        )
    )

    return f"""
RECENT CONVERSATION HISTORY

{conversation_context}


RELEVANT ACTIVE LONG-TERM MEMORY

{memory_context}


{live_context}
""".strip()


# ---------------------------------------------------------------------------
# Main Reasoning Function
# ---------------------------------------------------------------------------

def chat(
    user_message: str,
) -> str:
    user_message = user_message.strip()

    if not user_message:
        return "I didn't receive a message."

    context = build_context(
        user_message
    )

    response = client.responses.create(
        model="gpt-5.5",

        instructions=SYSTEM_PROMPT,

        input=[
            {
                "role": "developer",
                "content": (
                    "The following information comes from "
                    "E.V.I.E.'s local memory and live "
                    "perception systems. Use only the "
                    "parts relevant to the current request."
                    "\n\n"
                    f"{context}"
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
    )

    reply = response.output_text.strip()

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

        user_message = input(
            "You: "
        ).strip()

        if user_message.lower() in {
            "quit",
            "exit",
        }:
            break

        response = chat(
            user_message
        )

        print(
            f"\nE.V.I.E.: "
            f"{response}\n"
        )