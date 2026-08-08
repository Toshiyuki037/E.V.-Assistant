from brain import chat
from listen import listen
from speak import speak


def process_prompt(user_text):
    if not user_text:
        return

    print(f"\nYou: {user_text}")

    response = chat(user_text)

    print(f"\nE.V.: {response}\n")

    speak(response)


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

    elif mode in {"t", "terminal"}:
        user_text = input("You: ").strip()

        if user_text.lower() in {"quit", "exit"}:
            break

        process_prompt(user_text)

    elif mode in {"v", "voice"}:
        user_text = listen()

        if not user_text:
            print("I didn't hear anything.")
            continue

        if user_text.lower() in {"quit", "exit", "goodbye"}:
            print("E.V. Offline")
            break

        process_prompt(user_text)

    else:
        print("Choose T for terminal, V for voice, or Q to quit.")