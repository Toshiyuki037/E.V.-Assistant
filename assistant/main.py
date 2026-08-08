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
        - trigger ordinary reasoning

Most Recent Change:
    Improved forget handling so E.V.I.E. can identify and archive
    multiple memories covered by a natural-language forget request.
"""

from brain import chat
from listen import listen
from speak import speak

from memory.database import (
    archive_memories,
    init_memory,
    save_conversation,
    save_memory,
    update_memory,
)

from memory.embeddings import (
    create_memory_embedding,
    sync_memory_embeddings,
)

from memory.manager import (
    RELATION_CONFIDENCE,
    analyze_memory,
    resolve_new_memory,
    select_forget_targets,
    select_update_targets,
    should_auto_delete,
    should_auto_store,
    should_auto_update,
)

from memory.retriever import (
    retrieve_matching_memories,
    retrieve_memories,
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
    Creates a local embedding and stores a new active memory.
    """

    embedding = create_memory_embedding(
        content
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
# Store / Resolve Duplicate / Supersede
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
    Before storing a new memory, retrieve related memories and determine
    whether the new fact is:
        - genuinely new
        - a duplicate
        - a replacement/supersession
        - a contradiction
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
        resolution.relation == "duplicate"
        and resolution.matching_memory_id is not None
        and resolution.confidence >= RELATION_CONFIDENCE
    ):
        existing = next(
            (
                memory
                for memory in candidates
                if memory["id"]
                == resolution.matching_memory_id
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

            embedding = create_memory_embedding(
                content
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
                "\n[Memory Manager: DUPLICATE MERGED]"
            )

            print(
                f"Memory ID: {existing['id']}"
            )

            print(
                f"Memory: {content}"
            )

            return existing["id"]


    # -----------------------------------------------------------------------
    # Supersedes / Contradicts Existing Memory
    # -----------------------------------------------------------------------

    if (
        resolution.relation
        in {
            "supersedes",
            "contradicts",
        }
        and resolution.matching_memory_id is not None
        and resolution.confidence >= RELATION_CONFIDENCE
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
            f"Archived IDs: {archived}"
        )

        print(
            f"New ID: {new_id}"
        )

        print(
            f"Memory: {content}"
        )

        return new_id


    # -----------------------------------------------------------------------
    # Distinct New Memory
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
# Manual Remember Command
# ---------------------------------------------------------------------------

def handle_manual_memory(
    user_text,
):
    """
    Handles explicit:
        remember that ...
    """

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
            "Tell me what you'd like me to remember."
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
        f"\nE.V.I.E.: {response}\n"
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
    """
    Analyzes each normal user message and performs the appropriate
    long-term memory operation.

    Possible actions:
        none
        store
        update
        delete
    """

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

            candidates = retrieve_matching_memories(
                query=search_query,
                limit=10,
            )

            print(
                "\n[Memory Manager: UPDATE CANDIDATES]"
            )

            for candidate in candidates:

                print(
                    f"ID {candidate['id']}: "
                    f"{candidate['content']}"
                )

            selection = select_update_targets(
                user_message=user_text,
                new_content=analysis.content,
                candidates=candidates,
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
                if selection.confidence >= 75
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

                archived = archive_memories(
                    selected_ids,
                    reason="superseded",
                    superseded_by=new_id,
                )

                print(
                    "\n[Memory Manager: UPDATE]"
                )

                print(
                    f"Archived IDs: {archived}"
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
                    "\n[Memory Manager: UPDATE -> STORE]"
                )

                print(
                    "No old memory was confidently matched."
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

            candidates = retrieve_matching_memories(
                query=analysis.target_query,
                limit=12,
            )

            print(
                "\n[Memory Manager: FORGET CANDIDATES]"
            )

            if not candidates:

                print(
                    "No candidate memories found."
                )

            else:

                for candidate in candidates:

                    print(
                        f"ID {candidate['id']}: "
                        f"{candidate['content']}"
                    )

            selection = select_forget_targets(
                user_message=user_text,
                target_query=analysis.target_query,
                candidates=candidates,
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
                    "No matching memories were selected."
                )

                return

            # The user explicitly requested forgetting.
            # Candidate retrieval + LLM target selection has already happened,
            # so this threshold can be somewhat lower than normal automatic
            # memory modification thresholds.
            if selection.confidence < 65:

                print(
                    "\n[Memory Manager: FORGET]"
                )

                print(
                    "Memory selection confidence was too low "
                    "to modify storage."
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
                f"Archived IDs: {archived}"
            )

            return


    except Exception as error:

        # Memory subsystem problems should never prevent E.V.I.E.
        # from continuing normal conversation.

        print(
            "\n[Memory Manager Warning]"
        )

        print(
            error
        )


# ---------------------------------------------------------------------------
# Process User Prompt
# ---------------------------------------------------------------------------

def process_prompt(
    user_text,
):
    """
    Main processing pipeline for both terminal and voice prompts.
    """

    user_text = user_text.strip()

    if not user_text:
        return

    print(
        f"\nYou: {user_text}"
    )


    # -----------------------------------------------------------------------
    # Manual Memory
    # -----------------------------------------------------------------------

    if handle_manual_memory(
        user_text
    ):
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

    print(
        f"\nE.V.I.E.: {response}\n"
    )


    # -----------------------------------------------------------------------
    # Persistent Conversation History
    # -----------------------------------------------------------------------

    save_conversation(
        user_text,
        response,
    )


    # -----------------------------------------------------------------------
    # Voice Output
    # -----------------------------------------------------------------------

    speak(
        response
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
    # Invalid Mode
    # -----------------------------------------------------------------------

    else:

        print(
            "\nChoose T for terminal, "
            "V for voice, or Q to quit."
        )