from __future__ import annotations

WAKE_FORMS = (
    "evie",
    "eevee",
    "ev",
    "ev.",
    "e.v",
    "e.v.",
    "e.v.i.e",
    "e.v.i.e.",
)

SLEEP_COMMANDS = {
    "go to sleep",
    "sleep",
    "stand by",
    "standby",
    "go to standby",

    "that's all",
    "thats all",

    "that's all evie",
    "thats all evie",

    "that's all ev",
    "thats all ev",

    "you can go to sleep",
    "you can sleep now",

    "go back to sleep",
}

def normalize_voice_text(text: str) -> str:
    return " ".join(
        str(text or "").strip().lower().split()
    ).rstrip(".!?")


def is_sleep_command(text: str) -> bool:
    return normalize_voice_text(text) in SLEEP_COMMANDS


def extract_wake_request(text: str) -> tuple[bool, str]:
    lowered = normalize_voice_text(text)

    for form in WAKE_FORMS:

        if lowered == form:
            return True, ""

        comma_prefix = form + ","

        if lowered.startswith(comma_prefix):
            return (
                True,
                lowered[len(comma_prefix):].strip(),
            )

        space_prefix = form + " "

        if lowered.startswith(space_prefix):
            return (
                True,
                lowered[len(space_prefix):].strip(),
            )

    return False, ""
