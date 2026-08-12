"""
E.V.I.E. - Streaming Input Coordinator

Created: August 12, 2026
Author: Max Maehara

Phase 14D

Purpose:
    Coordinates provisional and finalized streaming speech before it
    reaches reasoning or E.V.I.E.'s authoritative request pipeline.

Architecture:
    This module does NOT:
        - execute tools
        - mutate memory
        - perform reasoning
        - control workflows
        - control the computer
        - replace process_prompt()

    It only tracks:
        - provisional transcript versions
        - conservatively committed sentences
        - final authoritative text
        - action-sensitive requests
        - stale provisional generations

Safety:
    Provisional reasoning is READ-ONLY.

    Action-sensitive requests are never eligible for provisional
    reasoning.

    Finalized speech remains authoritative and continues through the
    existing E.V.I.E. Phase 1-13 routing architecture.
"""

from __future__ import annotations

import re

from dataclasses import (
    dataclass,
)


# ---------------------------------------------------------------------------
# Action-Sensitive Language
# ---------------------------------------------------------------------------

_ACTION_WORDS = {
    "add",
    "approve",
    "archive",
    "book",
    "buy",
    "cancel",
    "change",
    "click",
    "close",
    "commit",
    "copy",
    "create",
    "delete",
    "download",
    "edit",
    "email",
    "execute",
    "fill",
    "focus",
    "forget",
    "install",
    "launch",
    "message",
    "modify",
    "move",
    "open",
    "order",
    "paste",
    "play",
    "post",
    "press",
    "push",
    "remember",
    "remove",
    "rename",
    "reply",
    "run",
    "save",
    "schedule",
    "sell",
    "send",
    "set",
    "skip",
    "submit",
    "terminate",
    "trash",
    "type",
    "uninstall",
    "update",
    "upload",
    "write",
}


_ACTION_PHRASES = (
    "turn on",
    "turn off",
    "log in",
    "sign in",
    "sign out",
    "shut down",
    "restart the",
    "restart my",
    "go to",
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(
    frozen=True
)
class StreamingInputSnapshot:
    """
    Immutable view of one streaming-input version.
    """

    version: int

    text: str

    final: bool

    action_sensitive: bool

    provisional_reasoning_allowed: bool

    invalidates_previous: bool


# ---------------------------------------------------------------------------
# Text Helpers
# ---------------------------------------------------------------------------

def normalize_streaming_text(
    text: str,
) -> str:
    """
    Normalizes whitespace without changing transcript meaning.
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


def is_action_sensitive(
    text: str,
) -> bool:
    """
    Conservatively identifies speech that may represent an external,
    persistent, or executable action.

    False positives are acceptable.

    A false positive only delays provisional reasoning until the final
    transcript.

    A false negative could allow unnecessary provisional processing for
    an action-bearing request.
    """

    normalized = (
        normalize_streaming_text(
            text
        )
        .lower()
    )


    if not normalized:

        return False


    padded = (
        f" {normalized} "
    )


    # -----------------------------------------------------------------------
    # Multi-Word Action Phrases
    # -----------------------------------------------------------------------

    for phrase in _ACTION_PHRASES:

        if (
            f" {phrase} "
            in padded
        ):

            return True


    # -----------------------------------------------------------------------
    # Single Action Words
    # -----------------------------------------------------------------------

    words = set(
        re.findall(
            r"[a-zA-Z']+",
            normalized,
        )
    )


    if (
        words
        & _ACTION_WORDS
    ):

        return True


    return False


# ---------------------------------------------------------------------------
# Streaming Input Coordinator
# ---------------------------------------------------------------------------

class StreamingInputCoordinator:
    """
    Tracks one spoken utterance across:

        early provisional hypotheses
        stable committed sentences
        final authoritative transcription

    Version numbers allow downstream reasoning/TTS workers to suppress
    stale output.

    Example:

        v1:
            "What is a transistor?"

        v2:
            "What is a transistor and why is it important?"

    Once v2 exists, work belonging to v1 is stale.
    """

    def __init__(
        self,
    ):

        self.reset()


    # -----------------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------------

    def reset(
        self,
    ):

        self.version = 0

        self.committed_sentences = []

        self.final_text = ""

        self._current_text = ""


    # -----------------------------------------------------------------------
    # Current Text
    # -----------------------------------------------------------------------

    @property
    def current_text(
        self,
    ) -> str:

        if self.final_text:

            return (
                self.final_text
            )


        if self._current_text:

            return (
                self._current_text
            )


        return (
            " ".join(
                self.committed_sentences
            )
            .strip()
        )


    # -----------------------------------------------------------------------
    # Version Check
    # -----------------------------------------------------------------------

    def is_current(
        self,
        version: int,
    ) -> bool:
        """
        Returns whether a downstream worker version is still current.
        """

        return (
            int(
                version
            )
            == self.version
        )


    # -----------------------------------------------------------------------
    # Build Snapshot
    # -----------------------------------------------------------------------

    def _snapshot(
        self,
        *,
        text: str,
        final: bool,
        invalidates_previous: bool,
    ) -> StreamingInputSnapshot:

        action_sensitive = (
            is_action_sensitive(
                text
            )
        )


        return (
            StreamingInputSnapshot(
                version=
                    self.version,

                text=
                    text,

                final=
                    final,

                action_sensitive=
                    action_sensitive,

                provisional_reasoning_allowed=
                    (
                        bool(
                            text
                        )
                        and not final
                        and not action_sensitive
                    ),

                invalidates_previous=
                    invalidates_previous,
            )
        )


    # -----------------------------------------------------------------------
    # Early Provisional Candidate
    # -----------------------------------------------------------------------

    def provisional_candidate(
        self,
        text: str,
    ) -> StreamingInputSnapshot:
        """
        Publishes an early READ-ONLY reasoning candidate.

        This path is intentionally more responsive than conservative
        transcript commitment because provisional reasoning is:

            - read-only
            - version-bound
            - cancellable
            - not an execution gateway

        Action-sensitive text remains blocked.
        """

        text = (
            normalize_streaming_text(
                text
            )
        )


        if not text:

            return (
                self._snapshot(
                    text=
                        self.current_text,

                    final=
                        False,

                    invalidates_previous=
                        False,
                )
            )


        # -------------------------------------------------------------------
        # Duplicate Candidate
        # -------------------------------------------------------------------

        if (
            text
            == self._current_text
        ):

            return (
                self._snapshot(
                    text=
                        text,

                    final=
                        False,

                    invalidates_previous=
                        False,
                )
            )


        previous = (
            self._current_text
        )


        self.version += 1

        self._current_text = (
            text
        )


        return (
            self._snapshot(
                text=
                    text,

                final=
                    False,

                invalidates_previous=
                    bool(
                        previous
                        and previous
                        != text
                    ),
            )
        )


    # -----------------------------------------------------------------------
    # Conservative Sentence Commit
    # -----------------------------------------------------------------------

    def commit_sentence(
        self,
        sentence: str,
    ) -> StreamingInputSnapshot:
        """
        Adds one conservatively stable sentence.

        If the exact sentence already exists as the active early
        provisional candidate, it becomes committed without restarting
        provisional reasoning or creating a new version.
        """

        sentence = (
            normalize_streaming_text(
                sentence
            )
        )


        if not sentence:

            return (
                self._snapshot(
                    text=
                        self.current_text,

                    final=
                        False,

                    invalidates_previous=
                        False,
                )
            )


        # -------------------------------------------------------------------
        # Existing Stable Duplicate
        # -------------------------------------------------------------------

        if (
            self.committed_sentences

            and self.committed_sentences[
                -1
            ]
            == sentence
        ):

            return (
                self._snapshot(
                    text=
                        self.current_text,

                    final=
                        False,

                    invalidates_previous=
                        False,
                )
            )


        # -------------------------------------------------------------------
        # Candidate Text After This Commit
        # -------------------------------------------------------------------

        candidate_text = (
            " ".join(
                [
                    *self.committed_sentences,
                    sentence,
                ]
            )
            .strip()
        )


        # -------------------------------------------------------------------
        # Early Candidate Already Matches
        # -------------------------------------------------------------------
        #
        # The same text transitioned from provisional to conservative
        # commitment.
        #
        # Do not increment version or restart downstream reasoning.
        # -------------------------------------------------------------------

        if (
            candidate_text
            == self._current_text
        ):

            self.committed_sentences.append(
                sentence
            )


            return (
                self._snapshot(
                    text=
                        self._current_text,

                    final=
                        False,

                    invalidates_previous=
                        False,
                )
            )


        # -------------------------------------------------------------------
        # New Committed State
        # -------------------------------------------------------------------

        previous = (
            self.current_text
        )


        self.committed_sentences.append(
            sentence
        )


        new_text = (
            " ".join(
                self.committed_sentences
            )
            .strip()
        )


        self.version += 1

        self._current_text = (
            new_text
        )


        return (
            self._snapshot(
                text=
                    new_text,

                final=
                    False,

                invalidates_previous=
                    bool(
                        previous
                        and previous
                        != new_text
                    ),
            )
        )


    # -----------------------------------------------------------------------
    # Finalize
    # -----------------------------------------------------------------------

    def finalize(
        self,
        text: str,
    ) -> StreamingInputSnapshot:
        """
        Makes the finalized Whisper transcript authoritative.

        Any provisional reasoning associated with a different previous
        version becomes stale.

        Final text still goes through the existing authoritative
        process_prompt() architecture outside this module.
        """

        text = (
            normalize_streaming_text(
                text
            )
        )


        previous = (
            self.current_text
        )


        changed = (
            text
            != previous
        )


        # -------------------------------------------------------------------
        # Final Version
        # -------------------------------------------------------------------
        #
        # Always advance to a final version.
        #
        # This ensures provisional downstream workers can be invalidated
        # even when the finalized wording exactly matches the provisional
        # wording.
        # -------------------------------------------------------------------

        self.version += 1


        self.final_text = (
            text
        )


        self._current_text = (
            text
        )


        return (
            self._snapshot(
                text=
                    text,

                final=
                    True,

                invalidates_previous=
                    (
                        bool(
                            previous
                        )
                        and changed
                    ),
            )
        )