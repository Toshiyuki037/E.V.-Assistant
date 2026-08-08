"""
E.V. Assistant - Intelligence / Reasoning Module

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Handles E.V.'s reasoning, personality, persistent context,
    and communication with the current language model.

How It Works:
    1. Receives user text from main.py.
    2. Loads recent conversation history.
    3. Loads saved long-term memories.
    4. Builds a context package.
    5. Sends the user request and context to the language model.
    6. Returns the generated response to main.py.

Most Recent Change:
    Added long-term memory retrieval alongside persistent
    conversation history.
"""

from dotenv import load_dotenv
from openai import OpenAI

from memory import (
    get_all_memories,
    get_recent_conversations,
)


# ---------------------------------------------------------------------------
# Environment / Client
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# E.V. Personality
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are E.V.

You are Max's personal AI assistant and engineering partner.

Your personality is:
- Calm
- Intelligent
- Direct
- Observant
- Natural
- Concise unless detail is useful

You are especially useful for:
- Electrical engineering
- Computer engineering
- Embedded systems
- FPGA development
- Biomedical engineering
- Artificial intelligence
- Programming
- Research
- Project development

You may receive two forms of memory:

1. Recent conversation history
2. Long-term persistent memories

Use memory when it is relevant.

Do not claim to remember information that does not appear in
the provided memory or current conversation.

If memory is incomplete, say so instead of inventing details.

Address Max naturally when appropriate.

Never say you are ChatGPT.

Do not mention OpenAI unless directly asked about the underlying
model or implementation.
"""


# ---------------------------------------------------------------------------
# Memory Formatting
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
            f"E.V.: {ev_response}"
        )

    return "\n\n".join(formatted)


def build_long_term_memory_context(
    limit: int = 20,
) -> str:
    memories = get_all_memories(
        limit=limit
    )

    if not memories:
        return "No long-term memories stored."

    formatted = []

    for (
        memory_id,
        content,
        category,
        created_at,
    ) in memories:

        formatted.append(
            f"[{category}] {content}"
        )

    return "\n".join(formatted)


# ---------------------------------------------------------------------------
# Main Reasoning Function
# ---------------------------------------------------------------------------

def chat(user_message: str) -> str:
    user_message = user_message.strip()

    if not user_message:
        return "I didn't receive a message."

    recent_context = build_conversation_context(
        limit=5
    )

    long_term_context = build_long_term_memory_context(
        limit=20
    )

    memory_context = f"""
RECENT CONVERSATION HISTORY

{recent_context}


LONG-TERM MEMORY

{long_term_context}
"""

    response = client.responses.create(
        model="gpt-5.5",
        instructions=SYSTEM_PROMPT,
        input=[
            {
                "role": "developer",
                "content": (
                    "The following information comes from "
                    "E.V.'s local memory system. "
                    "Use it only when relevant.\n\n"
                    f"{memory_context}"
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
        return "I wasn't able to generate a response."

    return reply


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("E.V. Brain Test")
    print("----------------")

    while True:
        message = input("You: ").strip()

        if message.lower() in {
            "quit",
            "exit",
        }:
            break

        answer = chat(message)

        print(f"\nE.V.: {answer}\n")