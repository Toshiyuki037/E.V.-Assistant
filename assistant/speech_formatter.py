"""
E.V.I.E. - Speech Response Formatter

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Converts E.V.I.E.'s full text responses into shorter,
    cleaner text for F5-TTS.

How It Works:
    The complete response remains visible in the terminal.
    This module removes unnecessary formatting and limits
    the amount of text sent to the voice model.

Most Recent Change:
    Added spoken-response optimization for Phase 3.
"""

import re


MAX_SPEECH_CHARACTERS = 550
MAX_SENTENCES = 5


def remove_markdown(text: str) -> str:
    """Remove formatting that should not be spoken."""

    # Code fences
    text = text.replace("```text", "")
    text = text.replace("```python", "")
    text = text.replace("```powershell", "")
    text = text.replace("```", "")

    # Inline code
    text = text.replace("`", "")

    # Bold / italics
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")

    # Markdown headings
    text = re.sub(
        r"(?m)^#+\s*",
        "",
        text,
    )

    # Bullets
    text = re.sub(
        r"(?m)^\s*[-•]\s+",
        "",
        text,
    )

    return text


def normalize_whitespace(text: str) -> str:
    """Convert excessive whitespace into normal spaces."""

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def limit_sentences(
    text: str,
    maximum: int = MAX_SENTENCES,
) -> str:
    """Limit how many sentences are spoken."""

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    if len(sentences) <= maximum:
        return text

    return " ".join(
        sentences[:maximum]
    )


def limit_characters(
    text: str,
    maximum: int = MAX_SPEECH_CHARACTERS,
) -> str:
    """Prevent extremely long TTS generations."""

    if len(text) <= maximum:
        return text

    shortened = text[:maximum]

    if " " in shortened:
        shortened = shortened.rsplit(
            " ",
            1,
        )[0]

    shortened = shortened.rstrip(
        " ,;:-"
    )

    if shortened:
        if shortened[-1] not in ".!?":
            shortened += "."

    return shortened


def prepare_spoken_text(response: str) -> str:
    """
    Prepare E.V.I.E.'s response for speech.

    The original response is not changed.
    """

    if not response:
        return ""

    text = response.strip()

    text = remove_markdown(text)

    text = normalize_whitespace(text)

    text = limit_sentences(
        text,
        MAX_SENTENCES,
    )

    text = limit_characters(
        text,
        MAX_SPEECH_CHARACTERS,
    )

    return text


if __name__ == "__main__":

    sample = """
    You're working on the **eve-assistant** project.

    Your active file is `main.py`.

    You're currently on the `main` Git branch.

    You have several modified files.

    E.V.I.E. can see this information through the
    Phase 3 perception system.
    """

    print("Original:")
    print(sample)

    print("\nSpoken:")
    print(
        prepare_spoken_text(sample)
    )