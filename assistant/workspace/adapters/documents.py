"""
E.V.I.E. - Research Document Adapter

Phase 12E

Indexes text-readable local research artifacts into the unified workspace.

PDF extraction is intentionally optional:
- if pypdf is installed, PDFs are read
- otherwise PDFs are skipped rather than breaking queries
"""

from __future__ import annotations

from pathlib import Path

from assistant.workspace.controller import (
    new_evidence_id,
)
from assistant.workspace.models import (
    EvidenceItem,
    SOURCE_PDF,
    SOURCE_RESEARCH_NOTE,
)
from assistant.workspace.query_expansion import (
    significant_tokens,
)

from .base import AdapterContext


TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
}


def _read_pdf(
    path: Path,
):
    try:
        from pypdf import PdfReader
    except Exception:
        return ""

    try:
        reader = PdfReader(
            str(
                path
            )
        )

        return "\n".join(
            (
                page.extract_text()
                or ""
            )
            for page in reader.pages
        )
    except Exception:
        return ""


class ResearchDocumentAdapter:
    name = "documents"

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        root = Path(
            context.workspace_path
            or "."
        ).resolve()

        search_roots = (
            context.arguments.get(
                "paths"
            )
            or [
                ".",
            ]
        )

        tokens = significant_tokens(
            query
        )

        scored = []
        seen_paths = set()

        for relative_root in search_roots:
            candidate_root = (
                root
                / relative_root
            ).resolve()

            if not candidate_root.exists():
                continue

            for path in candidate_root.rglob(
                "*"
            ):
                if not path.is_file():
                    continue

                if path in seen_paths:
                    continue

                suffix = path.suffix.lower()

                if (
                    suffix not in TEXT_EXTENSIONS
                    and suffix != ".pdf"
                ):
                    continue

                if any(
                    part in {
                        ".git",
                        "venv",
                        ".venv",
                        "__pycache__",
                        ".pytest_cache",
                        "node_modules",
                        "runtime",
                    }
                    for part in path.parts
                ):
                    continue

                seen_paths.add(
                    path
                )

                if suffix == ".pdf":
                    content = _read_pdf(
                        path
                    )
                    source_type = SOURCE_PDF
                else:
                    try:
                        content = path.read_text(
                            encoding="utf-8",
                            errors="ignore",
                        )
                    except OSError:
                        continue

                    source_type = SOURCE_RESEARCH_NOTE

                if not content.strip():
                    continue

                lowered = (
                    (
                        str(path)
                        + "\n"
                        + content
                    )
                    .lower()
                )

                overlap = sum(
                    1
                    for token in tokens
                    if token in lowered
                )

                if tokens and overlap == 0:
                    continue

                try:
                    relative = str(
                        path.relative_to(
                            root
                        )
                    ).replace(
                        "\\",
                        "/",
                    )
                except ValueError:
                    relative = str(
                        path
                    )

                item = EvidenceItem(
                    evidence_id=new_evidence_id(
                        source_type,
                        relative,
                        content,
                    ),
                    source_type=source_type,
                    source_name="research_documents",
                    source_id=relative,
                    title=path.name,
                    content=content,
                    project=context.project,
                    repository=context.repository,
                    path=relative,
                    relevance=float(
                        max(
                            1,
                            overlap,
                        )
                    ),
                    confidence=1.0,
                    metadata={
                        "extension":
                            suffix,
                        "token_overlap":
                            overlap,
                    },
                )

                scored.append(
                    (
                        overlap,
                        item,
                    )
                )

        scored.sort(
            key=lambda pair: pair[0],
            reverse=True,
        )

        limit = int(
            context.arguments.get(
                "limit",
                30,
            )
            or 30
        )

        return [
            item
            for _, item
            in scored[
                :limit
            ]
        ]
