"""
E.V.I.E. - Streamed Speech Reconciliation

Phase 14E5

Purpose:
    Prevents the authoritative synchronous voice response from repeating
    an opening sentence already started by the provisional streaming
    voice path.

Only VOICE output is changed.
Terminal/final response text remains untouched.
"""

from __future__ import annotations

import re
import threading
import time
from difflib import SequenceMatcher


DEFAULT_EXPIRY_SECONDS = 45.0

# Conservative enough to avoid deleting unrelated sentences while
# tolerating small wording changes such as "part" vs "component".
PREFIX_SIMILARITY_THRESHOLD = 0.86


def normalize_spoken_sentence(
    text: str,
) -> str:

    text = str(
        text
        or ""
    )

    for token in (
        "**",
        "__",
        "`",
        "*",
    ):

        text = text.replace(
            token,
            "",
        )


    text = re.sub(
        r"(?m)^#+\s*",
        "",
        text,
    )


    text = re.sub(
        r"[^a-zA-Z0-9\s']+",
        " ",
        text,
    )


    text = re.sub(
        r"\s+",
        " ",
        text,
    )


    return text.strip().casefold()


def split_spoken_sentences(
    text: str,
):

    text = str(
        text
        or ""
    ).strip()


    if not text:
        return []


    return [
        item.strip()

        for item in re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        if item.strip()
    ]


def sentence_similarity(
    first: str,
    second: str,
) -> float:

    left = normalize_spoken_sentence(
        first
    )

    right = normalize_spoken_sentence(
        second
    )


    if not left or not right:
        return 0.0


    if left == right:
        return 1.0


    return (
        SequenceMatcher(
            None,
            left,
            right,
        )
        .ratio()
    )


class SpokenPrefixTracker:
    """
    One-shot tracker for provisional sentences that actually BEGIN
    playback.

    Recording at playback start is intentional:
        final synchronous speak() may begin preparing while provisional
        playback is still underway.

        play_audio() serialization guarantees the final audio cannot
        physically overtake the already-started provisional chunk.
    """

    def __init__(
        self,
        *,
        expiry_seconds: float = DEFAULT_EXPIRY_SECONDS,
        similarity_threshold: float = PREFIX_SIMILARITY_THRESHOLD,
    ):

        self.expiry_seconds = max(
            0.0,
            float(
                expiry_seconds
            ),
        )

        self.similarity_threshold = float(
            similarity_threshold
        )

        self._lock = threading.Lock()

        self._sentences = []

        self._updated_at = 0.0


    def clear(self):

        with self._lock:

            self._sentences = []

            self._updated_at = 0.0


    def note(
        self,
        text: str,
    ):

        text = str(
            text
            or ""
        ).strip()


        if not text:
            return False


        sentences = split_spoken_sentences(
            text
        )


        if not sentences:
            return False


        now = time.monotonic()


        with self._lock:

            if (
                self._updated_at
                and self.expiry_seconds > 0
                and (
                    now
                    - self._updated_at
                )
                > self.expiry_seconds
            ):

                self._sentences = []


            for sentence in sentences:

                if not normalize_spoken_sentence(
                    sentence
                ):

                    continue


                if (
                    self._sentences
                    and sentence_similarity(
                        self._sentences[-1],
                        sentence,
                    )
                    >= 0.98
                ):

                    continue


                self._sentences.append(
                    sentence
                )


            self._updated_at = now


        return True


    def snapshot(self):

        now = time.monotonic()


        with self._lock:

            if (
                self._updated_at
                and self.expiry_seconds > 0
                and (
                    now
                    - self._updated_at
                )
                > self.expiry_seconds
            ):

                self._sentences = []

                self._updated_at = 0.0


            return list(
                self._sentences
            )


    def consume_prefix(
        self,
        text: str,
    ) -> str:

        text = str(
            text
            or ""
        ).strip()


        if not text:

            self.clear()

            return ""


        spoken = self.snapshot()

        self.clear()


        if not spoken:
            return text


        final_sentences = split_spoken_sentences(
            text
        )


        if not final_sentences:
            return text


        remove_count = 0


        for streamed_sentence, final_sentence in zip(
            spoken,
            final_sentences,
        ):

            similarity = sentence_similarity(
                streamed_sentence,
                final_sentence,
            )


            if (
                similarity
                < self.similarity_threshold
            ):

                break


            remove_count += 1


        if remove_count <= 0:
            return text


        return " ".join(
            final_sentences[
                remove_count:
            ]
        ).strip()
