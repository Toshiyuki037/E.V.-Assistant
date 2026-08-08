"""
E.V. Assistant - Main Application Controller

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Main entry point for E.V.

    Handles terminal input, voice input, AI reasoning,
    persistent memory, and spoken output.

How It Works:
    1. User chooses terminal or voice input.
    2. Voice input is converted to text by listen.py.
    3. Explicit memory commands are processed locally.
    4. Normal prompts are sent to brain.py.
    5. Conversations are saved to memory.db.
    6. Responses are spoken through speak.py.

Most Recent Change:
    Added explicit long-term memory using the command
    "remember that ...".
"""

from brain import chat
from listen import listen
from memory import (
    init_memory,
    save_conversation,
    save_memory,
)
from speak import speak


# ---------------------------------------------------------------------------
# Prompt Processing
# ---------------------------------------------------------------------------

def process_prompt(
    user_text: str,
):
    user_text = user_text.strip()

    if not user_text:
        return

    print(f"\nYou: {user_text}")

    lowered = user_text.lower()


    # -----------------------------------------------------------------------
    # Explicit Long-Term Memory
    # -----------------------------------------------------------------------

    remember_prefix = "remember that "

    if lowered.startswith(
        remember_prefix
    ):
        memory_text = user_text[
            len(remember_prefix):
        ].strip()

        if not memory_text:
            response = (
                "Tell me what you'd like me "
                "to remember."
            )

        else:
            save_memory(
                memory_text,
                category="general",
            )

            response = (
                "I'll remember that."
            )

        print(
            f"\nE.V.: {response}\n"
        )

        speak(response)

        return


    # -----------------------------------------------------------------------
    # Normal Conversation
    # -----------------------------------------------------------------------

    response = chat(
        user_text
    )

    print(
        f"\nE.V.: {response}\n"
    )

    save_conversation(
        user_text,
        response,
    )

    speak(response)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

init_memory()

print("\nE.V. Online")

print("-------------------------")
print("[T] Terminal")
print("[V] Voice")
print("[Q] Quit")
print("-------------------------")


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

while True:
    mode = input(
        "\nMode: "
    ).strip().lower()


    # -----------------------------------------------------------------------
    # Quit
    # -----------------------------------------------------------------------

    if mode in {
        "q",
        "quit",
        "exit",
    }:
        print(
            "\nE.V. Offline"
        )

        break


    # -----------------------------------------------------------------------
    # Terminal Input
    # -----------------------------------------------------------------------

    elif mode in {
        "t",
        "terminal",
    }:
        user_text = input(
            "You: "
        ).strip()

        if user_text.lower() in {
            "quit",
            "exit",
        }:
            print(
                "\nE.V. Offline"
            )

            break

        process_prompt(
            user_text
        )


    # -----------------------------------------------------------------------
    # Voice Input
    # -----------------------------------------------------------------------

    elif mode in {
        "v",
        "voice",
    }:
        user_text = listen()

        if not user_text:
            print(
                "\nI didn't hear anything."
            )

            continue

        if user_text.lower() in {
            "quit",
            "exit",
            "goodbye",
        }:
            print(
                "\nE.V. Offline"
            )

            break

        process_prompt(
            user_text
        )


    # -----------------------------------------------------------------------
    # Invalid Input
    # -----------------------------------------------------------------------

    else:
        print(
            "\nChoose T for terminal, "
            "V for voice, or Q to quit."
        )