from listen import listen
from speak import speak


print("EVE is online.")

while True:
    input("Press Enter to speak...")

    text = listen()

    print("You:", text)

    if text.lower() in {"quit", "exit", "goodbye"}:
        break

    speak(f"You said: {text}")