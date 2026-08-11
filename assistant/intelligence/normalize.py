"""
E.V.I.E. - Natural Language Input Normalization

Phase 10D

Purpose:
    Performs conservative normalization of common conversational,
    typing, and speech-recognition errors before intent detection.

Important:
    This layer is intentionally conservative.

    It may normalize common command-language mistakes such as:

        "hat about" -> "what about"
        "what abut" -> "what about"
        "how bout" -> "how about"
        "git hub" -> "github"
        "calender" -> "calendar"

    It must NOT broadly spell-correct user entities such as:

        repository names
        file paths
        URLs
        email addresses
        stock symbols
        Git branches
        code
        Notion page titles
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Exact / Phrase Normalizations
# ---------------------------------------------------------------------------

PHRASE_REPLACEMENTS = (
    # -----------------------------------------------------------------------
    # Conversational follow-ups
    # -----------------------------------------------------------------------

    (
        r"\bhat about\b",
        "what about",
    ),

    (
        r"\bwhat abut\b",
        "what about",
    ),

    (
        r"\bwhat bout\b",
        "what about",
    ),

    (
        r"\bwut about\b",
        "what about",
    ),

    (
        r"\bwat about\b",
        "what about",
    ),

    (
        r"\bhow bout\b",
        "how about",
    ),

    (
        r"\bhow abut\b",
        "how about",
    ),

    (
        r"\bdo that agin\b",
        "do that again",
    ),

    (
        r"\bdo it agin\b",
        "do it again",
    ),

    (
        r"\btry agin\b",
        "try again",
    ),

    (
        r"\buse the othr account\b",
        "use the other account",
    ),

    (
        r"\buse my othr account\b",
        "use my other account",
    ),


    # -----------------------------------------------------------------------
    # Common service names
    # -----------------------------------------------------------------------

    (
        r"\bgit hub\b",
        "github",
    ),

    (
        r"\bgit-hub\b",
        "github",
    ),

    (
        r"\bspot ify\b",
        "spotify",
    ),

    (
        r"\bnot ion\b",
        "notion",
    ),

    (
        r"\bschwabb\b",
        "schwab",
    ),


    # -----------------------------------------------------------------------
    # Common command vocabulary
    # -----------------------------------------------------------------------

    (
        r"\bcalender\b",
        "calendar",
    ),

    (
        r"\bcalandar\b",
        "calendar",
    ),

    (
        r"\brepositry\b",
        "repository",
    ),

    (
        r"\brepositiories\b",
        "repositories",
    ),

    (
        r"\brepositries\b",
        "repositories",
    ),

    (
        r"\bforcast\b",
        "forecast",
    ),

    (
        r"\bforecase\b",
        "forecast",
    ),

    (
        r"\bwheather\b",
        "weather",
    ),

    (
        r"\bwetaher\b",
        "weather",
    ),

    (
        r"\bnotifcations\b",
        "notifications",
    ),

    (
        r"\bcommitts\b",
        "commits",
    ),

    (
        r"\btransations\b",
        "transactions",
    ),

    (
        r"\bportolio\b",
        "portfolio",
    ),

    (
        r"\bdocumention\b",
        "documentation",
    ),

    (
        r"\bdocumantation\b",
        "documentation",
    ),
)


# ---------------------------------------------------------------------------
# Protected Token Detection
# ---------------------------------------------------------------------------

def _looks_protected(
    text: str,
):
    """
    Returns True when an entire input resembles structured data rather
    than ordinary conversational language.

    This is intentionally conservative.
    """

    stripped = (
        str(
            text
            or ""
        )
        .strip()
    )


    if not stripped:

        return False


    # URL
    if re.search(
        r"https?://",
        stripped,
        flags=re.IGNORECASE,
    ):

        return True


    # Email
    if re.fullmatch(
        r"[^\s@]+@[^\s@]+\.[^\s@]+",
        stripped,
    ):

        return True


    # Obvious Windows / Unix path
    if (
        re.match(
            r"^[A-Za-z]:\\",
            stripped,
        )
        or stripped.startswith(
            "/"
        )
    ):

        return True


    return False


# ---------------------------------------------------------------------------
# Whitespace Cleanup
# ---------------------------------------------------------------------------

def _normalize_whitespace(
    text: str,
):
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )


    text = re.sub(
        r" *\n *",
        "\n",
        text,
    )


    return text.strip()


# ---------------------------------------------------------------------------
# Main Normalizer
# ---------------------------------------------------------------------------

def normalize_user_input(
    user_message: str,
):
    """
    Conservatively normalize natural-language command phrasing.

    The returned value should be used for intent detection/planning.

    The original user message should still be retained for:
        - conversation history
        - display
        - audit logs
        - memory
    """

    if not isinstance(
        user_message,
        str,
    ):

        return user_message


    original = (
        user_message
        .strip()
    )


    if not original:

        return original


    if _looks_protected(
        original
    ):

        return original


    normalized = original


    for pattern, replacement in (
        PHRASE_REPLACEMENTS
    ):

        normalized = re.sub(
            pattern,
            replacement,
            normalized,
            flags=re.IGNORECASE,
        )


    normalized = (
        _normalize_whitespace(
            normalized
        )
    )


    return normalized


# ---------------------------------------------------------------------------
# Detect Meaningful Change
# ---------------------------------------------------------------------------

def input_was_normalized(
    user_message: str,
):
    if not isinstance(
        user_message,
        str,
    ):

        return False


    return (
        normalize_user_input(
            user_message
        )
        != user_message.strip()
    )


# ---------------------------------------------------------------------------
# Standalone Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    tests = (
        "hat about Corvallis?",
        "what abut Nvidia?",
        "how bout tomorrow?",
        "show my git hub repos",
        "whats on my calender tomorrow",
        "whats the wheather in Honolulu",
        "read my documantation page",
        "use my othr account",
        "E.V.-Assistant",
        "FPGA-NN-MODELING",
        "assistant/tools/planner.py",
        "https://github.com/Toshiyuki037/E.V.-Assistant",
    )


    for value in tests:

        print(
            repr(
                value
            ),
            "->",
            repr(
                normalize_user_input(
                    value
                )
            ),
        )