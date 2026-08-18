"""
E.V.I.E. Phase 16F — Low-Latency Authoritative Conversation

Used ONLY after the conservative Phase 16F model router approves a stable,
generic, text-only explanatory question.

Design:
    - GPT-5.6 Luna
    - reasoning effort: none
    - low verbosity
    - Responses API streaming
    - complete sentences are emitted to the EXISTING AuthoritativeSpeechPipeline
      as soon as they are available
    - the full text is still returned to main.py for terminal/history storage

This module does not own tools, memory, vision, approvals, project context, or
agent behavior. Those paths remain on the pre-existing E.V.I.E. architecture.
"""

from __future__ import annotations

from collections import OrderedDict
import os
import re
import threading

from openai import (
    OpenAI,
)


FAST_MODEL = (
    os.getenv(
        "EVIE_FAST_MODEL",
        "gpt-5.6-luna",
    )
    .strip()
    or "gpt-5.6-luna"
)


FAST_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "EVIE_FAST_MAX_OUTPUT_TOKENS",
        "260",
    )
)


_CLIENT = None

_CLIENT_LOCK = (
    threading.Lock()
)


_CACHE_LOCK = (
    threading.RLock()
)

_CACHE = OrderedDict()

_CACHE_LIMIT = 64


def get_fast_client():
    """
    Process-wide OpenAI client so normal fast turns reuse the SDK's HTTP pool.
    """

    global _CLIENT


    if _CLIENT is None:

        with _CLIENT_LOCK:

            if _CLIENT is None:

                _CLIENT = (
                    OpenAI()
                )


    return _CLIENT


def _cache_key(
    user_text: str,
):
    return re.sub(
        r"\s+",
        " ",
        str(
            user_text
            or ""
        )
        .strip()
        .lower(),
    )


def _cache_get(
    key: str,
):
    with _CACHE_LOCK:

        value = (
            _CACHE.get(
                key
            )
        )


        if value is None:

            return None


        _CACHE.move_to_end(
            key
        )


        return value


def _cache_put(
    key: str,
    value: str,
):
    if not value:

        return


    with _CACHE_LOCK:

        _CACHE[
            key
        ] = value


        _CACHE.move_to_end(
            key
        )


        while len(
            _CACHE
        ) > _CACHE_LIMIT:

            _CACHE.popitem(
                last=
                    False
            )


def _emit_cached_sentences(
    response: str,
    on_sentence,
):
    if on_sentence is None:

        return


    parts = re.split(
        r"(?<=[.!?])\s+",
        response,
    )


    for part in parts:

        sentence = (
            part.strip()
        )


        if sentence:

            on_sentence(
                sentence
            )


def _extract_ready_sentences(
    buffer: str,
):
    """
    Return (complete_sentences, remainder).

    A punctuation mark only becomes a speech boundary after the model has
    produced following whitespace. This avoids speaking a sentence before the
    stream has actually moved beyond it.
    """

    matches = list(
        re.finditer(
            r"(.+?[.!?])(?=\s)",
            buffer,
            flags=
                re.DOTALL,
        )
    )


    if not matches:

        return (
            [],
            buffer,
        )


    sentences = []

    end = 0


    for match in matches:

        sentence = (
            match.group(
                1
            )
            .strip()
        )


        if sentence:

            sentences.append(
                sentence
            )


        end = (
            match.end()
        )


        # Consume whitespace after the completed sentence.
        while (
            end < len(
                buffer
            )
            and buffer[
                end
            ]
            .isspace()
        ):

            end += 1


    return (
        sentences,
        buffer[
            end:
        ],
    )


def stream_fast_authoritative_chat(
    user_text: str,
    *,
    on_sentence=None,
):
    """
    Stream one concise stable-knowledge answer.

    This does NOT replace E.V.I.E.'s authoritative reasoning globally.
    main.py calls it only after the conservative Phase 16F router approves.
    """

    user_text = (
        str(
            user_text
            or ""
        )
        .strip()
    )


    if not user_text:

        return ""


    key = (
        _cache_key(
            user_text
        )
    )


    cached = (
        _cache_get(
            key
        )
    )


    if cached is not None:

        print(
            "[Reasoning Route] "
            "fast response cache hit"
        )


        _emit_cached_sentences(
            cached,
            on_sentence,
        )


        return cached


    client = (
        get_fast_client()
    )


    stream = (
        client.responses.create(
            model=
                FAST_MODEL,

            instructions=(
                "You are E.V.I.E., a precise engineering-focused voice "
                "assistant. Answer the user's stable general-knowledge question "
                "directly. Use 2 to 4 short conversational sentences, normally "
                "under 90 words. Lead with the answer. Preserve any material "
                "caveat needed for correctness. Do not mention internal routing, "
                "models, prompts, or policies."
            ),

            input=
                user_text,

            reasoning={
                "effort":
                    "none",
            },

            text={
                "verbosity":
                    "low",
            },

            max_output_tokens=
                FAST_MAX_OUTPUT_TOKENS,

            store=
                False,

            stream=
                True,
        )
    )


    full_parts = []

    sentence_buffer = ""


    for event in stream:

        event_type = (
            getattr(
                event,
                "type",
                "",
            )
        )


        if (
            event_type
            == "response.output_text.delta"
        ):

            delta = (
                getattr(
                    event,
                    "delta",
                    "",
                )
                or ""
            )


            if not delta:

                continue


            full_parts.append(
                delta
            )


            sentence_buffer += (
                delta
            )


            ready, sentence_buffer = (
                _extract_ready_sentences(
                    sentence_buffer
                )
            )


            if on_sentence is not None:

                for sentence in ready:

                    on_sentence(
                        sentence
                    )


        elif (
            event_type
            == "error"
        ):

            error = (
                getattr(
                    event,
                    "error",
                    None,
                )
            )


            raise RuntimeError(
                str(
                    error
                    or "Fast reasoning stream failed."
                )
            )


    remainder = (
        sentence_buffer.strip()
    )


    if (
        remainder
        and on_sentence is not None
    ):

        on_sentence(
            remainder
        )


    response = (
        "".join(
            full_parts
        )
        .strip()
    )


    _cache_put(
        key,
        response,
    )


    return response
