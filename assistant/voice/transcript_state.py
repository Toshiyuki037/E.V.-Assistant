"""
E.V.I.E. - Transcript State Machine

Created: August 12, 2026
Author: Max Maehara

Phase 14C2

Purpose:
    Tracks partial speech-recognition text and conservatively commits
    stable completed sentences.

Architecture:
    This module does NOT:
        - access the microphone
        - run Whisper
        - perform reasoning
        - trigger tools
        - speak responses

    It only manages transcript state.

Goals:
    - distinguish committed text from unstable partial text
    - commit complete sentences conservatively
    - require sentence stability across multiple partial updates
    - tolerate partial transcript rewrites
    - reconcile the final transcript cleanly
"""

from __future__ import annotations

import re

from dataclasses import (
    dataclass,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_REQUIRED_STABILITY = 2


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------

@dataclass(
    frozen=True
)
class TranscriptStateUpdate:
    full_text: str

    committed_text: str

    unstable_text: str

    newly_committed: tuple[str, ...]

    rewritten: bool

    final: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_text(
    text: str,
) -> str:
    """
    Normalizes transcript whitespace while preserving wording.
    """

    return (
        " ".join(
            str(
                text
                or ""
            )
            .split()
        )
        .strip()
    )


def split_complete_sentences(
    text: str,
):
    """
    Returns:

        complete_sentences
        unstable_tail

    A sentence is considered complete only when it ends in:
        .
        !
        ?

    Example:

        "Hello there. How are"

    becomes:

        ["Hello there."]
        "How are"
    """

    text = (
        normalize_text(
            text
        )
    )


    if not text:

        return (
            [],
            "",
        )


    matches = list(
        re.finditer(
            r".+?[.!?](?=\s|$)",
            text,
        )
    )


    if not matches:

        return (
            [],
            text,
        )


    sentences = []

    end_index = 0


    for match in matches:

        sentence = (
            match.group(
                0
            )
            .strip()
        )


        if sentence:

            sentences.append(
                sentence
            )


        end_index = (
            match.end()
        )


    tail = (
        text[
            end_index:
        ]
        .strip()
    )


    return (
        sentences,
        tail,
    )


def common_prefix_length(
    first,
    second,
):
    """
    Number of equal items at the start of two sequences.
    """

    count = 0


    for left, right in zip(
        first,
        second,
    ):

        if left != right:

            break


        count += 1


    return count


# ---------------------------------------------------------------------------
# Transcript State
# ---------------------------------------------------------------------------

class TranscriptState:
    """
    Conservative partial-transcript state machine.

    A sentence becomes committed only when:

        1. it ends in sentence punctuation
        2. it appears unchanged in consecutive partial updates
        3. it has not already been committed

    Committed text is never retracted during ordinary partial updates.

    The final transcript may reconcile differences at utterance end.
    """

    def __init__(
        self,
        *,
        required_stability: int = DEFAULT_REQUIRED_STABILITY,
    ):

        self.required_stability = max(
            1,
            int(
                required_stability
            ),
        )


        self.reset()


    # -----------------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------------

    def reset(
        self,
    ):
        self.full_text = ""

        self.committed_sentences = []

        self.unstable_text = ""

        self._previous_complete_sentences = []

        self._sentence_stability = []


    # -----------------------------------------------------------------------
    # Committed Text
    # -----------------------------------------------------------------------

    @property
    def committed_text(
        self,
    ):
        return (
            " ".join(
                self.committed_sentences
            )
            .strip()
        )


    # -----------------------------------------------------------------------
    # Partial Update
    # -----------------------------------------------------------------------

    def update_partial(
        self,
        text: str,
    ) -> TranscriptStateUpdate:
        """
        Processes one partial transcript.
        """

        text = (
            normalize_text(
                text
            )
        )


        rewritten = (
            bool(
                self.full_text
            )
            and not text.startswith(
                self.full_text
            )
            and not self.full_text.startswith(
                text
            )
        )


        self.full_text = text


        complete_sentences, tail = (
            split_complete_sentences(
                text
            )
        )


        # -------------------------------------------------------------------
        # Determine Sentence Stability
        # -------------------------------------------------------------------

        previous = (
            self._previous_complete_sentences
        )


        shared = (
            common_prefix_length(
                previous,
                complete_sentences,
            )
        )


        new_stability = []


        for index, sentence in enumerate(
            complete_sentences
        ):

            if (
                index < shared
                and index < len(
                    self._sentence_stability
                )
            ):

                stability = (
                    self._sentence_stability[
                        index
                    ]
                    + 1
                )


            else:

                stability = 1


            new_stability.append(
                stability
            )


        self._previous_complete_sentences = (
            list(
                complete_sentences
            )
        )


        self._sentence_stability = (
            new_stability
        )


        # -------------------------------------------------------------------
        # Commit Stable Sentences
        # -------------------------------------------------------------------

        newly_committed = []


        committed_count = len(
            self.committed_sentences
        )


        for index in range(
            committed_count,
            len(
                complete_sentences
            ),
        ):

            sentence = (
                complete_sentences[
                    index
                ]
            )


            stability = (
                new_stability[
                    index
                ]
            )


            if (
                stability
                < self.required_stability
            ):

                break


            self.committed_sentences.append(
                sentence
            )


            newly_committed.append(
                sentence
            )


        # -------------------------------------------------------------------
        # Unstable Tail
        # -------------------------------------------------------------------

        unstable_parts = []


        if (
            len(
                complete_sentences
            )
            > len(
                self.committed_sentences
            )
        ):

            unstable_parts.extend(
                complete_sentences[
                    len(
                        self.committed_sentences
                    ):
                ]
            )


        if tail:

            unstable_parts.append(
                tail
            )


        self.unstable_text = (
            " ".join(
                unstable_parts
            )
            .strip()
        )


        return (
            TranscriptStateUpdate(
                full_text=
                    self.full_text,

                committed_text=
                    self.committed_text,

                unstable_text=
                    self.unstable_text,

                newly_committed=
                    tuple(
                        newly_committed
                    ),

                rewritten=
                    rewritten,

                final=
                    False,
            )
        )


    # -----------------------------------------------------------------------
    # Final Reconciliation
    # -----------------------------------------------------------------------

    def finalize(
        self,
        text: str,
    ) -> TranscriptStateUpdate:
        """
        Reconciles state against the final transcription.

        The final transcript becomes authoritative for the completed
        utterance.

        Any complete sentences not already committed are committed now.

        Any remaining unpunctuated tail is preserved as unstable_text
        because it is still part of the user's finalized utterance.
        """

        text = (
            normalize_text(
                text
            )
        )


        rewritten = (
            bool(
                self.full_text
            )
            and text
            != self.full_text
        )


        self.full_text = text


        complete_sentences, tail = (
            split_complete_sentences(
                text
            )
        )


        previous_committed = (
            list(
                self.committed_sentences
            )
        )


        # Final transcription is authoritative.
        self.committed_sentences = (
            list(
                complete_sentences
            )
        )


        newly_committed = []


        common = (
            common_prefix_length(
                previous_committed,
                self.committed_sentences,
            )
        )


        newly_committed.extend(
            self.committed_sentences[
                common:
            ]
        )


        self.unstable_text = (
            tail
        )


        self._previous_complete_sentences = (
            list(
                complete_sentences
            )
        )


        self._sentence_stability = [
            self.required_stability

            for _
            in complete_sentences
        ]


        return (
            TranscriptStateUpdate(
                full_text=
                    self.full_text,

                committed_text=
                    self.committed_text,

                unstable_text=
                    self.unstable_text,

                newly_committed=
                    tuple(
                        newly_committed
                    ),

                rewritten=
                    rewritten,

                final=
                    True,
            )
        )