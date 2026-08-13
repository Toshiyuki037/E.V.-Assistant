"""
E.V.I.E. - Unified Voice Presentation Policy

Final Phase 14/15 polish.

Purpose:
    Apply one global voice-output policy AFTER every response source:
        - LLM reasoning
        - deterministic Phase 15/system responses
        - tools/integrations
        - agent/workflow
        - computer control

Core behavior:
    - concise by default
    - preserve operationally important information
    - never alter the full terminal/UI response
    - explicit detail requests may speak the full response
    - contextual expansion phrases ("tell me more", "elaborate", etc.)
      can expand the previous authoritative answer
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import threading

from .response_length import explicitly_requests_detail


@dataclass(frozen=True)
class VoicePresentation:
    mode: str
    text: str
    full_response: str
    was_condensed: bool


_STATE_LOCK = threading.RLock()
_LAST_USER_TEXT = ""
_LAST_FULL_RESPONSE = ""
_LAST_SPOKEN_RESPONSE = ""

_EXPANSION_PHRASES = (
    "elaborate",
    "tell me more",
    "go into detail",
    "go into more detail",
    "explain further",
    "explain more",
    "break that down",
    "break it down",
    "give me the details",
    "give me more detail",
    "what exactly is wrong",
    "what exactlys wrong",
    "what exactly's wrong",
    "what exactly happened",
    "why exactly",
    "expand on that",
    "continue explaining",
)

_CRITICAL_MARKERS = (
    "error",
    "failed",
    "failure",
    "broken",
    "degraded",
    "unavailable",
    "warning",
    "approval",
    "permission",
    "security",
    "risk",
    "requires",
    "required",
    "cannot",
    "can't",
    "could not",
    "next step",
    "next action",
    "important caveat",
)


def _normalize(text: str):
    return " ".join(str(text or "").strip().lower().split()).strip(" .!?")


def remember_authoritative_response(user_text: str, full_response: str, spoken_response: str = ""):
    global _LAST_USER_TEXT, _LAST_FULL_RESPONSE, _LAST_SPOKEN_RESPONSE
    with _STATE_LOCK:
        _LAST_USER_TEXT = str(user_text or "").strip()
        _LAST_FULL_RESPONSE = str(full_response or "").strip()
        _LAST_SPOKEN_RESPONSE = str(spoken_response or "").strip()


def get_last_authoritative_response():
    with _STATE_LOCK:
        return {
            "user_text": _LAST_USER_TEXT,
            "full_response": _LAST_FULL_RESPONSE,
            "spoken_response": _LAST_SPOKEN_RESPONSE,
        }


def is_contextual_expansion_request(user_text: str):
    text = _normalize(user_text)
    return bool(text) and any(phrase in text for phrase in _EXPANSION_PHRASES)


def build_contextual_expansion_prompt(user_text: str):
    if not is_contextual_expansion_request(user_text):
        return str(user_text or "")

    previous = get_last_authoritative_response()
    full_response = previous.get("full_response", "").strip()

    if not full_response:
        return str(user_text or "")

    return (
        str(user_text or "").strip()
        + "\n\n[E.V.I.E. CONTEXTUAL EXPANSION]\n"
        + "The user is asking to expand the previous authoritative answer. "
          "Continue the same topic rather than starting a new subject. "
          "Explain the most useful additional detail without merely repeating "
          "the prior wording.\n\nPrevious authoritative answer:\n"
        + full_response
    )


def _clean_for_speech(text: str):
    value = str(text or "")
    value = re.sub(r"```[\s\S]*?```", " ", value)
    value = value.replace("`", "").replace("**", "").replace("__", "")
    value = re.sub(r"(?m)^#+\s*", "", value)
    value = re.sub(r"(?m)^\s*[-•]\s+", "", value)
    value = re.sub(r"(?m)^\s*\d+[.)]\s+", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _sentences(text: str):
    cleaned = _clean_for_speech(text)
    if not cleaned:
        return []
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", cleaned)
        if item.strip()
    ]


def _word_count(text: str):
    return len(re.findall(r"\b[\w'-]+\b", text))


def _clip_words(text: str, maximum: int):
    words = text.split()
    if len(words) <= maximum:
        return text
    clipped = " ".join(words[:maximum]).rstrip(" ,;:-")
    if clipped and clipped[-1] not in ".!?":
        clipped += "."
    return clipped


def _compact_capability_inventory(full_response: str):
    if "supported core capabilities include" not in full_response.lower():
        return ""
    return (
        "I can handle conversation, memory, research, coding, web and browser "
        "work, connected services, computer awareness and control, vision, "
        "workflows, and system diagnostics. I also have voice authentication, "
        "wake and speech systems, telemetry, and health monitoring. If you want, "
        "I can break down any capability."
    )


def _compact_healthy_inventory(full_response: str):
    lower = full_response.lower()
    healthy_signal = (
        "overall system health: healthy" in lower
        or "overall: healthy" in lower
        or "i’m healthy" in lower
        or "i'm healthy" in lower
    )
    if not healthy_signal:
        return ""

    caveat = ""
    if (
        "not run a fresh deep diagnostic" in lower
        or "not run a fresh diagnostic" in lower
    ):
        caveat = (
            " I haven't run a fresh deep diagnostic in this exact turn, "
            "so that's based on my latest verified health state."
        )

    return (
        "Yes. My latest health state is healthy across memory, tools, "
        "integrations, voice, agent workflows, vision, GPU acceleration, "
        "and runtime infrastructure."
        + caveat
    )


def _critical_sentences(sentences):
    selected = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(marker in lower for marker in _CRITICAL_MARKERS):
            selected.append(sentence)
    return selected


def _generic_condense(full_response: str, *, maximum_words: int = 115):
    sentences = _sentences(full_response)
    if not sentences:
        return ""

    selected = []
    for sentence in sentences[:2]:
        if sentence not in selected:
            selected.append(sentence)

    for sentence in _critical_sentences(sentences):
        if sentence not in selected:
            selected.append(sentence)

    result = " ".join(selected).strip()

    if _word_count(result) < 45 and len(sentences) > 2:
        for sentence in sentences[2:]:
            if sentence in selected:
                continue
            selected.append(sentence)
            result = " ".join(selected).strip()
            if _word_count(result) >= 65:
                break

    return _clip_words(result, maximum_words)


def prepare_voice_presentation(user_text: str, full_response: str):
    full_response = str(full_response or "").strip()

    if not full_response:
        return VoicePresentation("empty", "", "", False)

    detailed = (
        explicitly_requests_detail(user_text)
        or is_contextual_expansion_request(user_text)
    )

    if detailed:
        spoken = _clean_for_speech(full_response)
        result = VoicePresentation("detailed", spoken, full_response, False)
        remember_authoritative_response(user_text, full_response, spoken)
        return result

    spoken = _compact_capability_inventory(full_response)
    if not spoken:
        spoken = _compact_healthy_inventory(full_response)
    if not spoken:
        spoken = _generic_condense(full_response)
    if not spoken:
        spoken = _clean_for_speech(full_response)

    result = VoicePresentation(
        "concise",
        spoken,
        full_response,
        _clean_for_speech(full_response) != spoken,
    )
    remember_authoritative_response(user_text, full_response, spoken)
    return result
