"""
E.V.I.E. - Main Application Controller

Created: August 7, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Main runtime for Enhanced Virtual Intelligence Engine.

How It Works:
    Supports voice and terminal input.

    Incoming messages may:
        - create long-term memories
        - merge duplicate memories
        - supersede outdated memories
        - update existing memories
        - forget/archive one or multiple memories
        - use live computer context
        - trigger normal reasoning

    The complete response is displayed in the terminal while a cleaned,
    shorter version is sent to E.V.I.E.'s voice model.

Most Recent Change:
    Added Phase 6 controlled computer-tool requests and explicit
    approval continuation while preserving memory, voice, and normal reasoning.
"""

from .brain import (
    chat,
    handle_pending_tool_approval,
    handle_tool_request,
)
from .listen import listen
from .speak import speak
from .speech_formatter import prepare_spoken_text

from .memory.database import (
    archive_memories,
    init_memory,
    save_conversation,
    save_memory,
    update_memory,
)

from .memory.embeddings import (
    create_memory_embedding,
    sync_memory_embeddings,
)

from .memory.manager import (
    RELATION_CONFIDENCE,
    analyze_memory,
    resolve_new_memory,
    select_forget_targets,
    select_update_targets,
    should_auto_delete,
    should_auto_store,
    should_auto_update,
)

from .memory.retriever import (
    retrieve_matching_memories,
    retrieve_memories,
)


# ---------------------------------------------------------------------------
# Speak Model Response
# ---------------------------------------------------------------------------

def speak_response(
    response: str,
):
    """
    Keeps the complete response in the terminal while sending a cleaner,
    shorter representation to F5-TTS.
    """

    spoken_response = (
        prepare_spoken_text(
            response
        )
    )

    if not spoken_response:
        return

    speak(
        spoken_response
    )


# ---------------------------------------------------------------------------
# Store Memory
# ---------------------------------------------------------------------------

def store_memory(
    content,
    category,
    importance,
    permanence,
    confidence,
    source,
):
    """
    Creates a local semantic embedding and stores a new memory.
    """

    embedding = (
        create_memory_embedding(
            content
        )
    )

    memory_id = save_memory(
        content=content,
        category=category,
        importance=importance,
        permanence=permanence,
        confidence=confidence,
        source=source,
        embedding=embedding,
    )

    return memory_id


# ---------------------------------------------------------------------------
# Resolve New Memory
# ---------------------------------------------------------------------------

def store_with_resolution(
    content,
    category,
    importance,
    permanence,
    confidence,
    source,
):
    """
    Determines whether incoming information is:

        - new
        - duplicate
        - superseding old information
        - contradictory
        - merely related
    """

    candidates = retrieve_memories(
        query=content,
        limit=5,
    )

    resolution = resolve_new_memory(
        new_content=content,
        candidates=candidates,
    )


    # -----------------------------------------------------------------------
    # Duplicate
    # -----------------------------------------------------------------------

    if (
        resolution.relation
        == "duplicate"

        and resolution.matching_memory_id
        is not None

        and resolution.confidence
        >= RELATION_CONFIDENCE
    ):

        existing = next(
            (
                memory
                for memory in candidates

                if (
                    memory["id"]
                    == resolution.matching_memory_id
                )
            ),
            None,
        )

        if existing is not None:

            improved_importance = max(
                existing["importance"],
                importance,
            )

            improved_permanence = max(
                existing["permanence"],
                permanence,
            )

            improved_confidence = max(
                existing["confidence"],
                confidence,
            )

            embedding = (
                create_memory_embedding(
                    content
                )
            )

            update_memory(
                memory_id=existing["id"],
                content=content,
                category=category,
                importance=improved_importance,
                permanence=improved_permanence,
                confidence=improved_confidence,
                source=source,
                embedding=embedding,
            )

            print(
                "\n[Memory Manager: "
                "DUPLICATE MERGED]"
            )

            print(
                f"Memory ID: "
                f"{existing['id']}"
            )

            print(
                f"Memory: {content}"
            )

            return existing["id"]


    # -----------------------------------------------------------------------
    # Supersession / Contradiction
    # -----------------------------------------------------------------------

    if (
        resolution.relation
        in {
            "supersedes",
            "contradicts",
        }

        and resolution.matching_memory_id
        is not None

        and resolution.confidence
        >= RELATION_CONFIDENCE
    ):

        new_id = store_memory(
            content=content,
            category=category,
            importance=importance,
            permanence=permanence,
            confidence=confidence,
            source=source,
        )

        archived = archive_memories(
            [
                resolution.matching_memory_id
            ],
            reason=resolution.relation,
            superseded_by=new_id,
        )

        print(
            "\n[Memory Manager: SUPERSEDE]"
        )

        print(
            f"Archived IDs: "
            f"{archived}"
        )

        print(
            f"New ID: {new_id}"
        )

        print(
            f"Memory: {content}"
        )

        return new_id


    # -----------------------------------------------------------------------
    # New Distinct Memory
    # -----------------------------------------------------------------------

    memory_id = store_memory(
        content=content,
        category=category,
        importance=importance,
        permanence=permanence,
        confidence=confidence,
        source=source,
    )

    print(
        "\n[Memory Manager: STORE]"
    )

    print(
        f"ID: {memory_id}"
    )

    print(
        f"Memory: {content}"
    )

    return memory_id


# ---------------------------------------------------------------------------
# Explicit Remember Command
# ---------------------------------------------------------------------------

def handle_manual_memory(
    user_text,
):
    prefix = "remember that "

    if not user_text.lower().startswith(
        prefix
    ):
        return False

    content = user_text[
        len(prefix):
    ].strip()

    if not content:

        response = (
            "Tell me what you'd like "
            "me to remember."
        )

    else:

        store_with_resolution(
            content=content,
            category="general",
            importance=100,
            permanence=100,
            confidence=100,
            source="manual",
        )

        response = (
            "I'll remember that."
        )

    print(
        f"\nE.V.I.E.: "
        f"{response}\n"
    )

    speak(
        response
    )

    return True


# ---------------------------------------------------------------------------
# Intelligent Memory Processing
# ---------------------------------------------------------------------------

def process_intelligent_memory(
    user_text,
):
    try:

        analysis = analyze_memory(
            user_text
        )


        # -------------------------------------------------------------------
        # NONE
        # -------------------------------------------------------------------

        if analysis.action == "none":
            return


        # -------------------------------------------------------------------
        # STORE
        # -------------------------------------------------------------------

        if should_auto_store(
            analysis
        ):

            store_with_resolution(
                content=analysis.content,
                category=analysis.category,
                importance=analysis.importance,
                permanence=analysis.permanence,
                confidence=analysis.confidence,
                source="automatic",
            )

            return


        # -------------------------------------------------------------------
        # UPDATE
        # -------------------------------------------------------------------

        if should_auto_update(
            analysis
        ):

            search_query = (
                analysis.target_query.strip()
                or analysis.content
            )

            candidates = (
                retrieve_matching_memories(
                    query=search_query,
                    limit=10,
                )
            )

            print(
                "\n[Memory Manager: "
                "UPDATE CANDIDATES]"
            )

            if candidates:

                for candidate in candidates:

                    print(
                        f"ID "
                        f"{candidate['id']}: "
                        f"{candidate['content']}"
                    )

            else:

                print(
                    "No candidates found."
                )

            selection = (
                select_update_targets(
                    user_message=user_text,
                    new_content=analysis.content,
                    candidates=candidates,
                )
            )

            print(
                f"Selected IDs: "
                f"{selection.memory_ids}"
            )

            print(
                f"Selection confidence: "
                f"{selection.confidence}"
            )

            selected_ids = (
                selection.memory_ids

                if (
                    selection.confidence
                    >= 75
                )

                else []
            )

            new_id = store_memory(
                content=analysis.content,
                category=analysis.category,
                importance=analysis.importance,
                permanence=analysis.permanence,
                confidence=analysis.confidence,
                source="automatic",
            )

            if selected_ids:

                archived = (
                    archive_memories(
                        selected_ids,
                        reason="superseded",
                        superseded_by=new_id,
                    )
                )

                print(
                    "\n[Memory Manager: UPDATE]"
                )

                print(
                    f"Archived IDs: "
                    f"{archived}"
                )

                print(
                    f"New ID: {new_id}"
                )

                print(
                    f"New memory: "
                    f"{analysis.content}"
                )

            else:

                print(
                    "\n[Memory Manager: "
                    "UPDATE -> STORE]"
                )

                print(
                    "No old memory was "
                    "confidently matched."
                )

                print(
                    f"New ID: {new_id}"
                )

            return


        # -------------------------------------------------------------------
        # FORGET / ARCHIVE
        # -------------------------------------------------------------------

        if should_auto_delete(
            analysis
        ):

            candidates = (
                retrieve_matching_memories(
                    query=analysis.target_query,
                    limit=12,
                )
            )

            print(
                "\n[Memory Manager: "
                "FORGET CANDIDATES]"
            )

            if not candidates:

                print(
                    "No candidate "
                    "memories found."
                )

            else:

                for candidate in candidates:

                    print(
                        f"ID "
                        f"{candidate['id']}: "
                        f"{candidate['content']}"
                    )

            selection = (
                select_forget_targets(
                    user_message=user_text,
                    target_query=(
                        analysis.target_query
                    ),
                    candidates=candidates,
                )
            )

            print(
                f"Selected IDs: "
                f"{selection.memory_ids}"
            )

            print(
                f"Selection confidence: "
                f"{selection.confidence}"
            )

            if not selection.memory_ids:

                print(
                    "\n[Memory Manager: FORGET]"
                )

                print(
                    "No matching memories "
                    "were selected."
                )

                return


            # Candidate retrieval and model-based selection have
            # already occurred. This threshold protects against
            # ambiguous memory deletion.

            if selection.confidence < 65:

                print(
                    "\n[Memory Manager: FORGET]"
                )

                print(
                    "Memory selection confidence "
                    "was too low to modify storage."
                )

                return

            archived = archive_memories(
                selection.memory_ids,
                reason="forgotten",
            )

            print(
                "\n[Memory Manager: FORGET]"
            )

            print(
                f"Archived IDs: "
                f"{archived}"
            )

            return


    except Exception as error:

        # Memory failures must not crash E.V.I.E.

        print(
            "\n[Memory Manager Warning]"
        )

        print(
            error
        )


# ---------------------------------------------------------------------------
# Process User Prompt
# ---------------------------------------------------------------------------

def complete_response(
    user_text: str,
    response: str,
):
    """
    Displays, stores, and speaks one completed E.V.I.E. response.
    """

    print(
        f"\nE.V.I.E.: "
        f"{response}\n"
    )

    save_conversation(
        user_text,
        response,
    )

    speak_response(
        response
    )


def process_prompt(
    user_text,
):
    """
    Shared processing pipeline used by terminal and voice input.

    Order matters:

        1. Resolve an existing tool approval.
        2. Handle explicit memory commands.
        3. Handle a new immediate computer-action request.
        4. Run intelligent memory analysis.
        5. Fall back to normal reasoning.

    Tool requests are intercepted before automatic memory analysis so
    commands such as "open Chrome" or "stage this file" are not stored
    as durable user facts.
    """

    user_text = (
        user_text.strip()
    )

    if not user_text:
        return


    print(
        f"\nYou: {user_text}"
    )


    # -----------------------------------------------------------------------
    # Pending Tool Approval
    # -----------------------------------------------------------------------

    approval_result = (
        handle_pending_tool_approval(
            user_text
        )
    )

    if approval_result.get(
        "handled",
        False,
    ):

        response = (
            approval_result.get(
                "response"
            )
            or "Done."
        )

        follow_up = (
            approval_result.get(
                "follow_up",
                ""
            ).strip()
        )


        # Report the completed/cancelled pending action first.
        complete_response(
            user_text,
            response,
        )


        # -----------------------------------------------------------------------
        # Compound Request
        # -----------------------------------------------------------------------

        if follow_up:

            print(
                "\n[Tool Follow-Up]"
            )

            print(
                "Continuing with:",
                follow_up,
            )

            process_prompt(
                follow_up
            )


        return


    # -----------------------------------------------------------------------
    # Explicit Memory
    # -----------------------------------------------------------------------

    if handle_manual_memory(
        user_text
    ):

        return


    # -----------------------------------------------------------------------
    # Immediate Computer Tool Request
    # -----------------------------------------------------------------------

    tool_result = (
        handle_tool_request(
            user_text
        )
    )

    if tool_result.get(
        "handled",
        False,
    ):

        response = (
            tool_result.get(
                "response"
            )
            or (
                "I processed the requested "
                "computer action."
            )
        )

        complete_response(
            user_text,
            response,
        )

        return


    # -----------------------------------------------------------------------
    # Intelligent Memory
    # -----------------------------------------------------------------------

    process_intelligent_memory(
        user_text
    )


    # -----------------------------------------------------------------------
    # Main Reasoning
    # -----------------------------------------------------------------------

    response = chat(
        user_text
    )


    complete_response(
        user_text,
        response,
    )


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

init_memory()


print(
    "Preparing semantic memory..."
)


missing_embeddings = (
    sync_memory_embeddings()
)


if missing_embeddings:

    print(
        f"Generated "
        f"{missing_embeddings} "
        f"missing memory embeddings."
    )


print(
    "\nE.V.I.E. Online"
)


print(
    "-------------------------"
)


print(
    "[T] Terminal"
)


print(
    "[V] Voice"
)


print(
    "[Q] Quit"
)


print(
    "-------------------------"
)


# ---------------------------------------------------------------------------
# Main Application Loop
# ---------------------------------------------------------------------------

while True:

    mode = input(
        "\nMode: "
    ).strip().lower()


    # -----------------------------------------------------------------------
    # Quit
    # -----------------------------------------------------------------------

    if mode in {
        "q",
        "quit",
        "exit",
    }:

        print(
            "\nE.V.I.E. Offline"
        )

        break


    # -----------------------------------------------------------------------
    # Terminal Input
    # -----------------------------------------------------------------------

    elif mode in {
        "t",
        "terminal",
    }:

        user_text = input(
            "You: "
        ).strip()

        if user_text.lower() in {
            "quit",
            "exit",
        }:

            print(
                "\nE.V.I.E. Offline"
            )

            break

        process_prompt(
            user_text
        )


    # -----------------------------------------------------------------------
    # Voice Input
    # -----------------------------------------------------------------------

    elif mode in {
        "v",
        "voice",
    }:

        user_text = listen()

        if not user_text:

            print(
                "\nI didn't hear anything."
            )

            continue

        if user_text.lower() in {
            "quit",
            "exit",
            "goodbye",
        }:

            print(
                "\nE.V.I.E. Offline"
            )

            break

        process_prompt(
            user_text
        )


    # -----------------------------------------------------------------------
    # Invalid Input
    # -----------------------------------------------------------------------

    else:

        print(
            "\nChoose T for terminal, "
            "V for voice, or Q to quit."
        )