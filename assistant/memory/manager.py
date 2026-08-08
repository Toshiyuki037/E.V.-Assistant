"""
E.V.I.E. - Intelligent Memory Manager

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Reasons about how information should modify E.V.I.E.'s
    long-term memory.

How It Works:
    Handles:
        - new memory detection
        - updates
        - forgetting
        - duplicate detection
        - contradiction detection
        - target selection

    This module reasons about memory but does not directly
    modify SQLite.

Most Recent Change:
    Added semantic duplicate/contradiction resolution and
    multi-memory forget/update targeting.
"""

from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

MemoryAction = Literal[
    "none",
    "store",
    "update",
    "delete",
]


MemoryCategory = Literal[
    "project",
    "research",
    "decision",
    "milestone",
    "preference",
    "profile",
    "hardware",
    "software",
    "procedure",
    "person",
    "episodic",
    "general",
]


MemoryRelation = Literal[
    "new",
    "duplicate",
    "supersedes",
    "contradicts",
    "related",
]


# ---------------------------------------------------------------------------
# Structured Models
# ---------------------------------------------------------------------------

class MemoryAnalysis(BaseModel):
    action: MemoryAction

    content: str

    target_query: str

    category: MemoryCategory

    importance: int

    permanence: int

    confidence: int


class MemoryResolution(BaseModel):
    relation: MemoryRelation

    matching_memory_id: int | None

    confidence: int

    explanation: str


class MemoryTargetSelection(BaseModel):
    memory_ids: list[int]

    confidence: int

    explanation: str


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

AUTO_STORE_IMPORTANCE = 70
AUTO_STORE_PERMANENCE = 60
AUTO_STORE_CONFIDENCE = 75

AUTO_UPDATE_CONFIDENCE = 80
AUTO_DELETE_CONFIDENCE = 85

RELATION_CONFIDENCE = 82


# ---------------------------------------------------------------------------
# Main Memory Analysis Prompt
# ---------------------------------------------------------------------------

MEMORY_MANAGER_PROMPT = """
You are the memory manager for E.V.I.E.,
Enhanced Virtual Intelligence Engine.

Do not answer the user.

Determine whether the user's message should modify durable
long-term memory.

Choose exactly one action:

none
store
update
delete

STORE:
New durable information worth remembering.

UPDATE:
Current information changes, replaces, corrects, or supersedes
existing information.

DELETE:
The user explicitly wants stored information forgotten.

NONE:
No long-term memory operation is needed.

Good memories include:
- project facts
- research details
- important decisions
- milestones
- stable preferences
- hardware configuration
- software configuration
- procedures
- durable goals
- meaningful events

Do NOT normally store:
- greetings
- casual questions
- temporary moods
- casual small talk
- temporary debugging chatter
- transient errors

When writing content:

Create a concise standalone fact.

Prefer:
"Max's development computer uses an RTX 4070 GPU."

Avoid:
"The user said..."
"The user's..."
"Max said..."

For UPDATE:
target_query should describe the OLD information to locate.

For DELETE:
target_query should describe the topic or facts the user wants
forgotten. It may refer to MORE THAN ONE stored memory.

For STORE:
target_query should normally be blank.

Categories:

project
research
decision
milestone
preference
profile
hardware
software
procedure
person
episodic
general

Scores:
importance 0-100
permanence 0-100
confidence 0-100

Be conservative.

Do not invent information.
"""


# ---------------------------------------------------------------------------
# Analyze Message
# ---------------------------------------------------------------------------

def analyze_memory(
    user_message: str,
):
    user_message = (
        user_message.strip()
    )

    if not user_message:
        return MemoryAnalysis(
            action="none",
            content="",
            target_query="",
            category="general",
            importance=0,
            permanence=0,
            confidence=100,
        )

    response = client.responses.parse(
        model="gpt-5.5",
        instructions=MEMORY_MANAGER_PROMPT,
        input=user_message,
        text_format=MemoryAnalysis,
    )

    analysis = (
        response.output_parsed
    )

    if analysis is None:
        return MemoryAnalysis(
            action="none",
            content="",
            target_query="",
            category="general",
            importance=0,
            permanence=0,
            confidence=0,
        )

    return analysis


# ---------------------------------------------------------------------------
# Storage Threshold Helpers
# ---------------------------------------------------------------------------

def should_auto_store(
    analysis,
):
    return (
        analysis.action == "store"
        and analysis.importance
        >= AUTO_STORE_IMPORTANCE
        and analysis.permanence
        >= AUTO_STORE_PERMANENCE
        and analysis.confidence
        >= AUTO_STORE_CONFIDENCE
        and bool(
            analysis.content.strip()
        )
    )


def should_auto_update(
    analysis,
):
    return (
        analysis.action == "update"
        and analysis.confidence
        >= AUTO_UPDATE_CONFIDENCE
        and bool(
            analysis.content.strip()
        )
    )


def should_auto_delete(
    analysis,
):
    return (
        analysis.action == "delete"
        and analysis.confidence
        >= AUTO_DELETE_CONFIDENCE
        and bool(
            analysis.target_query.strip()
        )
    )


# ---------------------------------------------------------------------------
# Format Candidate Memories
# ---------------------------------------------------------------------------

def format_candidates(
    candidates,
):
    if not candidates:
        return "No candidate memories."

    blocks = []

    for memory in candidates:
        blocks.append(
            (
                f"ID: {memory['id']}\n"
                f"Category: {memory['category']}\n"
                f"Content: {memory['content']}"
            )
        )

    return "\n\n".join(
        blocks
    )


# ---------------------------------------------------------------------------
# Resolve New Memory Against Existing Memories
# ---------------------------------------------------------------------------

def resolve_new_memory(
    new_content: str,
    candidates,
):
    if not candidates:
        return MemoryResolution(
            relation="new",
            matching_memory_id=None,
            confidence=100,
            explanation=(
                "No existing candidate memories."
            ),
        )

    prompt = f"""
NEW MEMORY:

{new_content}


EXISTING CANDIDATES:

{format_candidates(candidates)}


Determine the relationship between the NEW MEMORY and the most
relevant existing candidate.

Choose:

new:
No existing candidate represents the same durable fact.

duplicate:
The new memory and an existing memory express essentially the
same fact.

supersedes:
The new information clearly replaces an older value/state for
the same subject.

contradicts:
The facts concern the same subject but conflict, and it is not
clear that the newer statement intentionally replaces the old.

related:
They concern the same topic but represent distinct facts.

Return the ID of the most relevant existing memory when
appropriate.

Do not merge two distinct devices, projects, people, or events
merely because they are similar.
"""

    response = client.responses.parse(
        model="gpt-5.5",
        instructions=(
            "You are E.V.I.E.'s memory relationship resolver. "
            "Do not answer the user. Classify memory relationships."
        ),
        input=prompt,
        text_format=MemoryResolution,
    )

    resolution = (
        response.output_parsed
    )

    if resolution is None:
        return MemoryResolution(
            relation="new",
            matching_memory_id=None,
            confidence=0,
            explanation=(
                "Relationship analysis failed."
            ),
        )

    return resolution


# ---------------------------------------------------------------------------
# Select Memories To Update
# ---------------------------------------------------------------------------

def select_update_targets(
    user_message: str,
    new_content: str,
    candidates,
):
    if not candidates:
        return MemoryTargetSelection(
            memory_ids=[],
            confidence=100,
            explanation=(
                "No existing memories match."
            ),
        )

    prompt = f"""
USER MESSAGE:

{user_message}


NEW CURRENT FACT:

{new_content}


CANDIDATE MEMORIES:

{format_candidates(candidates)}


Select every memory that represents an OLD state or fact that is
being replaced by the user's new current information.

Do not select related-but-distinct memories.

For example:

Old:
"Max's FPGA project uses VHDL."

New:
"Max's FPGA project uses Verilog."

Select the VHDL memory.

If several duplicate memories represent the same outdated fact,
select all of them.
"""

    response = client.responses.parse(
        model="gpt-5.5",
        instructions=(
            "Select which existing E.V.I.E. memories are "
            "superseded by current user information."
        ),
        input=prompt,
        text_format=MemoryTargetSelection,
    )

    result = response.output_parsed

    if result is None:
        return MemoryTargetSelection(
            memory_ids=[],
            confidence=0,
            explanation=(
                "Target selection failed."
            ),
        )

    return result


# ---------------------------------------------------------------------------
# Select Memories To Forget
# ---------------------------------------------------------------------------

def select_forget_targets(
    user_message: str,
    target_query: str,
    candidates,
):
    if not candidates:

        return MemoryTargetSelection(
            memory_ids=[],
            confidence=100,
            explanation="No candidate memories exist.",
        )

    prompt = f"""
USER REQUEST:

{user_message}


FORGET TOPIC:

{target_query}


CANDIDATE MEMORIES:

{format_candidates(candidates)}


The user has explicitly requested that E.V.I.E. forget information.

Select EVERY candidate memory that contains information covered
by the forget request.

Important rules:

1. Interpret the user's request by meaning, not exact wording.

2. If the user asks to forget a category of information, select
   every memory that would allow E.V.I.E. to reconstruct that
   information.

3. Do not require the candidate to contain every word from the request.

4. Do not select unrelated memories.

Example:

User:
"Forget which GPU I use for E.V.I.E. development."

Candidate:
"E.V.I.E. development laptop has an NVIDIA GeForce RTX 4070 GPU."

This MUST be selected because it directly reveals the GPU used
for E.V.I.E. development.

Another candidate:
"Max's primary development computer uses an RTX 4070 GPU."

This should also be selected if it is being used for development.

Return all matching memory IDs.

Confidence means confidence that the selected IDs correctly satisfy
the user's explicit forget request.
"""

    response = client.responses.parse(
        model="gpt-5.5",
        instructions=(
            "You are E.V.I.E.'s long-term memory deletion selector. "
            "The user has explicitly requested forgetting. "
            "Select every candidate memory whose stored information "
            "falls within that request."
        ),
        input=prompt,
        text_format=MemoryTargetSelection,
    )

    result = response.output_parsed

    if result is None:

        return MemoryTargetSelection(
            memory_ids=[],
            confidence=0,
            explanation="Forget target selection failed.",
        )

    return result