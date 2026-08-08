"""
E.V.I.E. - Intelligence / Reasoning Module

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Handles E.V.I.E.'s primary language reasoning.

How It Works:
    Retrieves recent conversation history and the most relevant
    active long-term memories before calling the current reasoning model.

Most Recent Change:
    Integrated hybrid semantic memory retrieval with reranking.
"""

from dotenv import load_dotenv
from openai import OpenAI

from memory.database import get_recent_conversations
from memory.retriever import retrieve_memories


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# E.V.I.E. Personality
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

Be concise unless additional detail is useful.

You may receive:

1. Recent conversation history
2. Relevant ACTIVE long-term memories

Memory rules:

- Active long-term memory is more authoritative than older
  conversational statements about durable facts.
- The user's current message overrides conflicting older context.
- If information has been updated, use the newest active information.
- Forgotten or archived memories must not be treated as known.
- Never invent memories.
- Do not claim to remember something unless it appears in active
  memory or valid current conversation context.
- If information is incomplete, say so.

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
# Long-Term Memory Context
# ---------------------------------------------------------------------------

def build_memory_context(
    user_message: str,
    limit: int = 5,
) -> str:

    memories = retrieve_memories(
        query=user_message,
        limit=limit,
    )

    if not memories:
        return "No relevant active long-term memories were found."

    formatted = []

    for memory in memories:
        formatted.append(
            f"[{memory['category']}] {memory['content']}"
        )

    return "\n".join(formatted)


# ---------------------------------------------------------------------------
# Main Chat Function
# ---------------------------------------------------------------------------

def chat(
    user_message: str,
) -> str:

    user_message = user_message.strip()

    if not user_message:
        return "I didn't receive a message."

    conversation_context = build_conversation_context(
        limit=5
    )

    memory_context = build_memory_context(
        user_message=user_message,
        limit=5,
    )

    context = f"""
RECENT CONVERSATION HISTORY

{conversation_context}


RELEVANT ACTIVE LONG-TERM MEMORY

{memory_context}
"""

    response = client.responses.create(
        model="gpt-5.5",
        instructions=SYSTEM_PROMPT,
        input=[
            {
                "role": "developer",
                "content": (
                    "The following context comes from E.V.I.E.'s "
                    "local context and memory systems. "
                    "Use it only when relevant.\n\n"
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
        return "I wasn't able to generate a response."

    return reply


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("E.V.I.E. Brain Test")
    print("--------------------")

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() in {
            "quit",
            "exit",
        }:
            break

        response = chat(
            user_message
        )

        print(
            f"\nE.V.I.E.: {response}\n"
        )