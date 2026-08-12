"""
E.V.I.E. - Speech Response Formatter

Created: August 8, 2026
Last Edited: August 12, 2026
Author: Max Maehara

Purpose:
    Converts E.V.I.E.'s complete text responses into concise,
    natural spoken responses for F5-TTS.

How It Works:
    The full response remains visible in the terminal.

    Voice output is intentionally much shorter so E.V.I.E. begins
    and finishes speaking quickly while preserving the essential
    answer.

Phase 14A:
    Reduced spoken response size substantially to lower TTS
    generation and playback latency before Phase 14 streaming.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Short answers should be spoken exactly as generated.
SHORT_RESPONSE_CHARACTERS = 160

# Longer terminal responses are compressed for speech.
MAX_SPEECH_CHARACTERS = 260
MAX_SENTENCES = 2


# ---------------------------------------------------------------------------
# Markdown Cleanup
# ---------------------------------------------------------------------------

def remove_markdown(
    text: str,
) -> str:
    """
    Removes formatting that should not be spoken.
    """

    # -----------------------------------------------------------------------
    # Code Fences
    # -----------------------------------------------------------------------

    text = re.sub(
        r"```[\w+-]*",
        "",
        text,
    )

    text = text.replace(
        "```",
        "",
    )


    # -----------------------------------------------------------------------
    # Inline Code / Emphasis
    # -----------------------------------------------------------------------

    text = text.replace(
        "`",
        "",
    )

    text = text.replace(
        "**",
        "",
    )

    text = text.replace(
        "__",
        "",
    )

    text = text.replace(
        "*",
        "",
    )


    # -----------------------------------------------------------------------
    # Headings
    # -----------------------------------------------------------------------

    text = re.sub(
        r"(?m)^#+\s*",
        "",
        text,
    )


    # -----------------------------------------------------------------------
    # Bullets
    # -----------------------------------------------------------------------

    text = re.sub(
        r"(?m)^\s*[-•]\s+",
        "",
        text,
    )


    # -----------------------------------------------------------------------
    # Numbered Markdown Lists
    # -----------------------------------------------------------------------

    text = re.sub(
        r"(?m)^\s*\d+[.)]\s+",
        "",
        text,
    )


    return text


# ---------------------------------------------------------------------------
# Whitespace
# ---------------------------------------------------------------------------

def normalize_whitespace(
    text: str,
) -> str:
    """
    Converts excessive whitespace into normal spaces.
    """

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ---------------------------------------------------------------------------
# Sentence Splitting
# ---------------------------------------------------------------------------

def split_sentences(
    text: str,
):
    """
    Splits normal prose into useful speech-sized sentences.
    """

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        sentence.strip()
        for sentence
        in sentences
        if sentence.strip()
    ]


# ---------------------------------------------------------------------------
# Sentence Limit
# ---------------------------------------------------------------------------

def limit_sentences(
    text: str,
    maximum: int = MAX_SENTENCES,
) -> str:
    """
    Limits long responses to the first few useful sentences.
    """

    sentences = split_sentences(
        text
    )

    if len(
        sentences
    ) <= maximum:

        return text


    return " ".join(
        sentences[
            :maximum
        ]
    )


# ---------------------------------------------------------------------------
# Character Limit
# ---------------------------------------------------------------------------

def limit_characters(
    text: str,
    maximum: int = MAX_SPEECH_CHARACTERS,
) -> str:
    """
    Prevents expensive long F5-TTS generations.
    """

    if len(
        text
    ) <= maximum:

        return text


    shortened = text[
        :maximum
    ]


    if " " in shortened:

        shortened = (
            shortened.rsplit(
                " ",
                1,
            )[0]
        )


    shortened = shortened.rstrip(
        " ,;:-"
    )


    if (
        shortened
        and shortened[-1]
        not in ".!?"
    ):

        shortened += "."


    return shortened


# ---------------------------------------------------------------------------
# Spoken Text Preparation
# ---------------------------------------------------------------------------

def prepare_spoken_text(
    response: str,
) -> str:
    """
    Prepares E.V.I.E.'s terminal response for speech.

    The original response is never changed.

    Short responses are preserved.

    Long responses are reduced to a concise spoken representation.
    """

    if not response:

        return ""


    text = response.strip()

    text = remove_markdown(
        text
    )

    text = normalize_whitespace(
        text
    )


    # -----------------------------------------------------------------------
    # Preserve Naturally Short Responses
    # -----------------------------------------------------------------------
    #
    # A response is only considered naturally short when BOTH:
    #
    #     - its character count is small
    #     - its sentence count is already within the speech limit
    #
    # This prevents several short sentences from bypassing the
    # Phase 14A spoken-response compression.
    # -----------------------------------------------------------------------

    sentences = split_sentences(
        text
    )


    if (
        len(
            text
        )
        <= SHORT_RESPONSE_CHARACTERS

        and len(
            sentences
        )
        <= MAX_SENTENCES
    ):

        return text


    # -----------------------------------------------------------------------
    # Compress Longer / Multi-Sentence Responses
    # -----------------------------------------------------------------------

    text = limit_sentences(
        text,
        MAX_SENTENCES,
    )


    text = limit_characters(
        text,
        MAX_SPEECH_CHARACTERS,
    )


    return text


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    sample = """
A transistor is a tiny electronic component that controls the
flow of electric current.

It's mainly used in two ways:

1. As a switch. A small signal can turn a larger current on or off.

2. As an amplifier. A weak signal can control a stronger one.

Most modern transistors are made from semiconductors.
"""

    print(
        "Original:"
    )

    print(
        sample
    )


    print(
        "\nSpoken:"
    )

    print(
        prepare_spoken_text(
            sample
        )
    )