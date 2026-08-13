"""
E.V.I.E. - Speech Response Formatter

Phase 14 Rolling Speech Update

Purpose:
    Cleans E.V.I.E. text for speech while preserving the complete response.

Compatibility:
    prepare_spoken_text() keeps the existing concise behavior by default.
    New rolling/full-response speech uses prepare_spoken_chunks().

Rolling speech:
    - complete response remains visible in terminal
    - speech is divided into small chunks
    - default chunk size is 2 sentences
    - no response content is intentionally discarded
"""

from __future__ import annotations

import re


SHORT_RESPONSE_CHARACTERS = 160
MAX_SPEECH_CHARACTERS = 260
MAX_SENTENCES = 2

DEFAULT_SENTENCES_PER_CHUNK = 2
DEFAULT_CHUNK_CHARACTERS = 340


def remove_markdown(
    text: str,
) -> str:
    text = re.sub(
        r"```[\w+-]*",
        "",
        text,
    )

    text = text.replace(
        "```",
        "",
    )

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

    text = re.sub(
        r"(?m)^#+\s*",
        "",
        text,
    )

    text = re.sub(
        r"(?m)^\s*[-•]\s+",
        "",
        text,
    )

    text = re.sub(
        r"(?m)^\s*\d+[.)]\s+",
        "",
        text,
    )

    return text


def normalize_whitespace(
    text: str,
) -> str:
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def split_sentences(
    text: str,
):
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


def limit_sentences(
    text: str,
    maximum: int = MAX_SENTENCES,
) -> str:
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


def limit_characters(
    text: str,
    maximum: int = MAX_SPEECH_CHARACTERS,
) -> str:
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


def prepare_full_spoken_text(
    response: str,
) -> str:
    """
    Clean a complete response for speech without truncating its meaning.
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

    return text


def prepare_spoken_text(
    response: str,
    *,
    full_response: bool = False,
) -> str:
    """
    Backwards-compatible spoken-text preparation.

    full_response=False:
        preserves the prior concise Phase 14 behavior.

    full_response=True:
        returns the complete cleaned response for rolling speech.
    """

    text = prepare_full_spoken_text(
        response
    )

    if not text:
        return ""

    if full_response:
        return text

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

    text = limit_sentences(
        text,
        MAX_SENTENCES,
    )

    text = limit_characters(
        text,
        MAX_SPEECH_CHARACTERS,
    )

    return text


def _split_long_sentence(
    sentence: str,
    maximum: int,
):
    """
    Preserve a long sentence by splitting it at word boundaries instead of
    discarding the tail.
    """

    sentence = (
        str(
            sentence
            or ""
        )
        .strip()
    )

    if not sentence:
        return []

    if len(
        sentence
    ) <= maximum:
        return [
            sentence
        ]

    words = (
        sentence.split()
    )

    parts = []

    current = []

    current_length = 0

    for word in words:

        extra = (
            len(
                word
            )
            + (
                1
                if current
                else 0
            )
        )

        if (
            current
            and current_length
            + extra
            > maximum
        ):
            parts.append(
                " ".join(
                    current
                )
            )

            current = [
                word
            ]

            current_length = len(
                word
            )

        else:
            current.append(
                word
            )

            current_length += extra

    if current:
        parts.append(
            " ".join(
                current
            )
        )

    return parts


def prepare_spoken_chunks(
    response: str,
    *,
    sentences_per_chunk: int = DEFAULT_SENTENCES_PER_CHUNK,
    max_chunk_characters: int = DEFAULT_CHUNK_CHARACTERS,
):
    """
    Convert one complete response into ordered speech chunks.

    Default:
        2 sentences per F5 generation.

    Character limit is a per-chunk safety bound, not a whole-response limit.
    """

    text = prepare_full_spoken_text(
        response
    )

    if not text:
        return []

    sentences_per_chunk = max(
        1,
        int(
            sentences_per_chunk
        ),
    )

    max_chunk_characters = max(
        80,
        int(
            max_chunk_characters
        ),
    )

    raw_sentences = split_sentences(
        text
    )

    if not raw_sentences:
        raw_sentences = [
            text
        ]

    sentences = []

    for sentence in raw_sentences:
        sentences.extend(
            _split_long_sentence(
                sentence,
                max_chunk_characters,
            )
        )

    chunks = []

    current = []

    current_characters = 0

    for sentence in sentences:

        separator = (
            1
            if current
            else 0
        )

        would_exceed_characters = (
            current
            and (
                current_characters
                + separator
                + len(
                    sentence
                )
                > max_chunk_characters
            )
        )

        would_exceed_sentences = (
            len(
                current
            )
            >= sentences_per_chunk
        )

        if (
            would_exceed_characters
            or would_exceed_sentences
        ):
            chunks.append(
                " ".join(
                    current
                )
                .strip()
            )

            current = []

            current_characters = 0

            separator = 0

        current.append(
            sentence
        )

        current_characters += (
            separator
            + len(
                sentence
            )
        )

    if current:
        chunks.append(
            " ".join(
                current
            )
            .strip()
        )

    return [
        chunk
        for chunk
        in chunks
        if chunk
    ]
