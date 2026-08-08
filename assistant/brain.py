"""
E.V. Assistant - Intelligence / Reasoning Module

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Handles E.V.'s reasoning, personality, conversation context,
    and communication with the current language model.

How It Works:
    1. Receives the user's message from main.py.
    2. Loads recent conversations from memory.py.
    3. Adds relevant recent history to E.V.'s context.
    4. Sends the prompt and context to the OpenAI Responses API.
    5. Returns E.V.'s response text to main.py.

    The reasoning layer is kept separate from E.V.'s voice,
    memory, and input systems so the current cloud model can
    later be replaced by a locally hosted LLM.

Most Recent Change:
    Added retrieval of recent persistent conversations from
    memory/memory.db and included them as context for E.V.
"""

from dotenv import load_dotenv
from openai import OpenAI

from memory import get_recent_conversations


# ---------------------------------------------------------------------------
# Environment / Client Initialization
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
- Concise unless more detail is useful

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

Use the provided memory when it is relevant.

Do not claim to remember something unless it appears in the provided
memory or current conversation.

If memory is incomplete, say so rather than inventing information.

Address Max naturally when appropriate.

Never say you are ChatGPT.
Do not mention OpenAI unless directly asked about the underlying model
or implementation.
"""


# ---------------------------------------------------------------------------
# Memory Formatting
# ---------------------------------------------------------------------------

def build_memory_context(limit: int = 5) -> str:
    """
    Retrieves recent conversations from E.V.'s local SQLite database
    and formats them for use as model context.
    """

    recent_conversations = get_recent_conversations(limit=limit)

    if not recent_conversations:
        return "No previous conversation memory is currently available."

    formatted_memory = []

    for user_message, ev_response in recent_conversations:
        formatted_memory.append(
            f"User: {user_message}\n"
            f"E.V.: {ev_response}"
        )

    return "\n\n".join(formatted_memory)


# ---------------------------------------------------------------------------
# Main Reasoning Function
# ---------------------------------------------------------------------------

def chat(user_message: str) -> str:
    """
    Sends a user message to E.V.'s current reasoning model.

    Recent persistent conversation history is retrieved locally
    and supplied as additional context.
    """

    user_message = user_message.strip()

    if not user_message:
        return "I didn't receive a message."

    memory_context = build_memory_context(limit=5)

    response = client.responses.create(
        model="gpt-5.5",

        instructions=SYSTEM_PROMPT,

        input=[
            {
                "role": "developer",
                "content": (
                    "The following information comes from E.V.'s local "
                    "persistent memory. Use it only when relevant to the "
                    "user's current request.\n\n"
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

        if message.lower() in {"quit", "exit"}:
            break

        answer = chat(message)

        print(f"E.V.: {answer}")