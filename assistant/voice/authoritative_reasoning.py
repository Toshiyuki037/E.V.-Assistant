from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from ..brain import SYSTEM_PROMPT, build_context, client
from ..vision.lifecycle import delete_visual_artifact


@dataclass(frozen=True)
class AuthoritativeStreamEvent:
    kind: str
    text: str


class ResponseSentenceAccumulator:
    def __init__(self):
        self.buffer = ""

    def add(self, delta: str) -> list[str]:
        delta = str(delta or "")
        if not delta:
            return []

        self.buffer += delta
        completed = []

        while True:
            match = re.search(
                r"^(.+?[.!?])(?=\s|$)",
                self.buffer,
                flags=re.DOTALL,
            )

            if match is None:
                break

            sentence = match.group(1).strip()

            if sentence:
                completed.append(sentence)

            self.buffer = self.buffer[match.end():].lstrip()

        return completed

    def flush(self) -> str:
        trailing = self.buffer.strip()
        self.buffer = ""
        return trailing


def _developer_message(context: str) -> str:
    return (
        "The following information comes from E.V.I.E.'s local memory, "
        "computer perception, workspace, project knowledge, and vision systems. "
        "All current workspace information was captured from one coherent "
        "snapshot for this request. When visual context is attached, treat the "
        "screenshot as fresh visual evidence from the current request and "
        "interpret it according to the stated visual target. Use only "
        "information relevant to the user's request.\n\n"
        f"{context}"
    )


def _context_query_from_reasoning_prompt(user_message: str) -> str:
    """
    Recover the original user request for context routing.

    Phase 14/15 response-length policy intentionally appends an INTERNAL
    reasoning instruction to the final reasoning prompt. That instruction
    must still reach the reasoning model, but it must NOT be treated as
    user intent by build_context(), because words inside the policy such as
    "architecture" can falsely trigger project/file knowledge retrieval.

    This function strips only the known internal policy suffix for the
    context-routing call. The full original `user_message` remains unchanged
    and is still sent to the reasoning model.
    """
    value = str(user_message or "").strip()

    marker = (
        "\n\n"
        "[E.V.I.E. RESPONSE-LENGTH POLICY — INTERNAL RUNTIME INSTRUCTION]"
    )

    if marker in value:
        value = value.split(
            marker,
            1,
        )[0].strip()

    return value


def stream_authoritative_chat(
    user_message: str,
    *,
    on_sentence: Callable[[str], None] | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> str:
    """
    Streams the ONE authoritative normal-reasoning response after final STT.
    This is not speculative and never runs from partial Whisper hypotheses.

    Architecture is unchanged:
        - full reasoning prompt still goes to the model
        - context/memory/project routing still uses build_context()
        - sentence accumulation is unchanged
        - on_sentence/on_delta callbacks are unchanged
        - authoritative speech/chunking/TTS remain external and unchanged

    The only fix is that build_context() receives the original user request
    rather than the appended internal response-length instruction.
    """
    user_message = str(user_message or "").strip()

    if not user_message:
        return "I didn't receive a message."

    visual_input = None
    accumulator = ResponseSentenceAccumulator()
    full_text = []

    try:
        context_query = _context_query_from_reasoning_prompt(
            user_message
        )

        context, visual_input = build_context(
            context_query
        )

        developer_message = _developer_message(
            context
        )

        if visual_input:
            print("\n[Vision]")
            print(
                "Target:",
                visual_input["requested_target"],
            )
            print(
                "Capture source:",
                visual_input["source"],
            )
            print(
                "Fresh screenshot attached:"
            )
            print(
                visual_input["screenshot_path"]
            )

            user_content = [
                {
                    "type":
                        "input_text",

                    "text":
                        user_message,
                },

                {
                    "type":
                        "input_image",

                    "image_url":
                        visual_input["image_url"],
                },
            ]

        else:
            user_content = user_message

        with client.responses.stream(
            model="gpt-5.5",
            instructions=SYSTEM_PROMPT,
            input=[
                {
                    "role":
                        "developer",

                    "content":
                        developer_message,
                },

                {
                    "role":
                        "user",

                    "content":
                        user_content,
                },
            ],
        ) as stream:

            for event in stream:
                if (
                    getattr(
                        event,
                        "type",
                        "",
                    )
                    != "response.output_text.delta"
                ):
                    continue

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

                full_text.append(
                    delta
                )

                if on_delta is not None:
                    on_delta(
                        delta
                    )

                for sentence in accumulator.add(
                    delta
                ):
                    if on_sentence is not None:
                        on_sentence(
                            sentence
                        )

        trailing = accumulator.flush()

        if (
            trailing
            and on_sentence is not None
        ):
            on_sentence(
                trailing
            )

        response = (
            "".join(
                full_text
            )
            .strip()
        )

        if not response:
            return (
                "I wasn't able to generate "
                "a response."
            )

        return response

    except Exception as error:
        print(
            "\n[Authoritative Streaming Error]"
        )

        print(
            error
        )

        return (
            "I encountered an error while "
            "processing that request."
        )

    finally:
        if (
            visual_input
            and visual_input.get(
                "temporary",
                True,
            )
        ):
            screenshot_path = (
                visual_input.get(
                    "screenshot_path"
                )
            )

            if screenshot_path:
                try:
                    delete_visual_artifact(
                        screenshot_path
                    )

                    print(
                        "\n[Vision Cleanup]"
                    )

                    print(
                        "Temporary screenshot deleted."
                    )

                except Exception as error:
                    print(
                        "\n[Vision Cleanup Warning]"
                    )

                    print(
                        error
                    )
