"""
E.V.I.E. - Research Workspace Adapter

Phase 12F

Purpose:
Expose structured Phase 12F research records through the unified
Phase 12 workspace evidence model.

This adapter does not modify research state.
It only converts saved research records into EvidenceItem objects
for cross-source retrieval and synthesis.
"""

from __future__ import annotations


from assistant.research.state import (
    list_all,
    load,
)

from assistant.workspace.controller import (
    new_evidence_id,
)

from assistant.workspace.models import (
    EvidenceItem,
)

from assistant.workspace.query_expansion import (
    significant_tokens,
)

from .base import (
    AdapterContext,
)


# ---------------------------------------------------------------------------
# Research Record Types
# ---------------------------------------------------------------------------

RESEARCH_KINDS = (
    (
        "projects",
        "research_project",
    ),
    (
        "papers",
        "research_paper",
    ),
    (
        "hypotheses",
        "research_hypothesis",
    ),
    (
        "experiments",
        "research_experiment",
    ),
    (
        "results",
        "research_result",
    ),
    (
        "decisions",
        "research_decision",
    ),
    (
        "timeline",
        "research_timeline",
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record_id(
    data: dict,
):
    for key in (
        "project_id",
        "paper_id",
        "hypothesis_id",
        "experiment_id",
        "result_id",
        "decision_id",
        "event_id",
    ):

        value = data.get(
            key
        )

        if value:
            return str(
                value
            )

    return ""


def _record_title(
    data: dict,
):
    for key in (
        "name",
        "title",
        "statement",
        "decision",
        "summary",
        "goal",
    ):

        value = data.get(
            key
        )

        if value:
            return str(
                value
            )

    return (
        _record_id(
            data
        )
        or "Research Record"
    )


def _record_content(
    data: dict,
):
    lines = []

    for key, value in data.items():

        if value in (
            None,
            "",
            [],
            {},
        ):
            continue

        lines.append(
            f"{key}: {value}"
        )

    return "\n".join(
        lines
    )


def _project_membership(
    project_id: str,
):
    """
    Returns the object IDs belonging to one research project.

    This lets a workspace query scoped to a project avoid returning
    unrelated papers/experiments from other research projects.
    """

    if not project_id:
        return None


    project = load(
        "projects",
        project_id,
    )


    if project is None:
        return None


    return {
        "projects":
            {
                project.project_id
            },

        "papers":
            set(
                project.paper_ids
            ),

        "hypotheses":
            set(
                project.hypothesis_ids
            ),

        "experiments":
            set(
                project.experiment_ids
            ),

        "results":
            set(
                project.result_ids
            ),

        "decisions":
            set(
                project.decision_ids
            ),

        "timeline":
            set(
                project.timeline_event_ids
            ),
    }


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class ResearchAdapter:
    name = "research"


    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:

        tokens = significant_tokens(
            query
        )


        limit = int(
            context.arguments.get(
                "limit",
                50,
            )
            or 50
        )


        requested_project = (
            context.arguments.get(
                "project_id"
            )
            or context.project
            or ""
        )


        membership = (
            _project_membership(
                requested_project
            )
            if requested_project
            else None
        )


        scored = []


        # -------------------------------------------------------------------
        # Search Every Structured Research Record
        # -------------------------------------------------------------------

        for (
            kind,
            source_type,
        ) in RESEARCH_KINDS:

            records = list_all(
                kind
            )


            for record in records:

                data = vars(
                    record
                )


                record_id = (
                    _record_id(
                        data
                    )
                )


                # -----------------------------------------------------------
                # Project Filtering
                # -----------------------------------------------------------

                if membership is not None:

                    allowed_ids = (
                        membership.get(
                            kind,
                            set(),
                        )
                    )


                    if (
                        record_id
                        not in allowed_ids
                    ):
                        continue


                title = (
                    _record_title(
                        data
                    )
                )


                content = (
                    _record_content(
                        data
                    )
                )


                haystack = (
                    f"{title}\n{content}"
                    .lower()
                )


                overlap = sum(
                    1
                    for token in tokens
                    if token
                    in haystack
                )


                if (
                    tokens
                    and overlap == 0
                ):
                    continue


                evidence_id = (
                    new_evidence_id(
                        source_type,
                        record_id,
                        content,
                    )
                )


                item = EvidenceItem(
                    evidence_id=
                        evidence_id,

                    source_type=
                        source_type,

                    source_name=
                        "research",

                    source_id=
                        record_id,

                    title=
                        title,

                    content=
                        content,

                    project=
                        requested_project,

                    repository=
                        context.repository,

                    relevance=
                        float(
                            max(
                                1,
                                overlap,
                            )
                        ),

                    confidence=
                        1.0,

                    metadata={
                        "research_kind":
                            kind,

                        "research_id":
                            record_id,

                        "raw":
                            data,
                    },
                )


                scored.append(
                    (
                        overlap,
                        item,
                    )
                )


        # -------------------------------------------------------------------
        # Ranking
        # -------------------------------------------------------------------

        scored.sort(
            key=lambda pair:
                pair[
                    0
                ],
            reverse=True,
        )


        return [
            item
            for _, item
            in scored[
                :limit
            ]
        ]