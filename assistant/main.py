"""
E.V. Assistant - Main Application Controller

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Main entry point for the E.V. Assistant. Controls the user interaction
    loop and allows E.V. to receive input through either the terminal or
    microphone.

How It Works:
    1. User selects terminal or voice input.
    2. Voice input is converted to text through listen.py.
    3. The prompt is sent to brain.py for processing.
    4. The generated response is displayed in the terminal.
    5. speak.py converts the response into E.V.'s voice and plays it.

Most Recent Change:
    Added support for both terminal and microphone input through the same
    E.V. processing pipeline.
"""

from brain import chat
from listen import listen
from speak import speak
from memory import init_memory, save_conversation


def process_prompt(user_text):
    if not user_text:
        return

    print(f"\nYou: {user_text}")

    response = chat(user_text)

    print(f"\nE.V.: {response}\n")

    save_conversation(user_text, response)

    speak(response)


init_memory()

print("\nE.V. Online")
print("-------------------------")
print("[T] Terminal")
print("[V] Voice")
print("[Q] Quit")
print("-------------------------")

while True:
    mode = input("\nMode: ").strip().lower()

    if mode in {"q", "quit", "exit"}:
        print("E.V. Offline")
        break

    if mode in {"t", "terminal"}:
        user_text = input("You: ").strip()

        if user_text.lower() in {"quit", "exit"}:
            break

        process_prompt(user_text)

    elif mode in {"v", "voice"}:
        user_text = listen()

        if not user_text:
            print("I didn't hear anything.")
            continue

        process_prompt(user_text)

    else:
        print("Choose T, V, or Q.")