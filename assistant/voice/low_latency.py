from __future__ import annotations


def prepare_low_latency_chunks(
    chunks: list[str],
):
    """
    Preserve all spoken content while making only the first chunk one sentence.
    """

    if not chunks:
        return []

    from assistant.speech_formatter import (
        split_sentences,
    )

    sentences = []

    for chunk in chunks:
        sentences.extend(
            split_sentences(
                chunk
            )
        )

    if not sentences:
        return list(
            chunks
        )

    result = [
        sentences[
            0
        ]
    ]

    remaining = sentences[
        1:
    ]

    for index in range(
        0,
        len(
            remaining
        ),
        2,
    ):
        chunk = " ".join(
            remaining[
                index:
                index
                + 2
            ]
        ).strip()

        if chunk:
            result.append(
                chunk
            )

    return result
