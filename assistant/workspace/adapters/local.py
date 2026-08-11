"""
E.V.I.E. - Local Workspace Adapter

Phase 12D Retrieval Fix

Searches local workspace files using token overlap instead of requiring
the entire natural-language question to appear verbatim.
"""

from __future__ import annotations

from pathlib import Path

from assistant.workspace.controller import new_evidence_id
from assistant.workspace.models import (
    EvidenceItem,
    SOURCE_CODE,
    SOURCE_DOCUMENTATION,
    SOURCE_LOCAL_FILE,
)
from assistant.workspace.query_expansion import (
    significant_tokens,
)

from .base import AdapterContext


DEFAULT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml",
    ".ini", ".cfg", ".html", ".js", ".ts", ".tsx", ".jsx",
    ".vhd", ".vhdl", ".sv", ".c", ".cpp", ".h", ".hpp",
}

DEFAULT_IGNORES = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache",
    "node_modules", "runtime", ".idea",
}


class LocalWorkspaceAdapter:
    name = "local"

    def __init__(
        self,
        *,
        max_file_bytes: int = 500_000,
        max_results: int = 50,
    ):
        self.max_file_bytes = max_file_bytes
        self.max_results = max_results

    def _source_type(
        self,
        path: Path,
    ):
        if path.suffix.lower() == ".py":
            return SOURCE_CODE

        if path.suffix.lower() in {
            ".md",
            ".txt",
        }:
            return SOURCE_DOCUMENTATION

        return SOURCE_LOCAL_FILE

    def _iter_files(
        self,
        root: Path,
    ):
        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if any(
                part in DEFAULT_IGNORES
                for part in path.parts
            ):
                continue

            if path.suffix.lower() not in DEFAULT_EXTENSIONS:
                continue

            try:
                if path.stat().st_size > self.max_file_bytes:
                    continue
            except OSError:
                continue

            yield path

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        root = Path(
            context.workspace_path
            or "."
        ).resolve()

        tokens = significant_tokens(
            query
        )

        scored = []

        for path in self._iter_files(root):
            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            relative = str(
                path.relative_to(root)
            ).replace("\\", "/")

            haystack = (
                relative
                + "\n"
                + content
            ).lower()

            if tokens:
                overlap = sum(
                    1
                    for token in tokens
                    if token in haystack
                )

                if overlap == 0:
                    continue
            else:
                overlap = 1

            evidence_id = new_evidence_id(
                self._source_type(path),
                relative,
                content,
            )

            scored.append(
                (
                    overlap,
                    EvidenceItem(
                        evidence_id=evidence_id,
                        source_type=self._source_type(path),
                        source_name="local_workspace",
                        source_id=relative,
                        title=path.name,
                        content=content,
                        project=context.project,
                        repository=context.repository,
                        path=relative,
                        relevance=float(overlap),
                        confidence=1.0,
                        metadata={
                            "absolute_path": str(path),
                            "extension": path.suffix.lower(),
                            "token_overlap": overlap,
                        },
                    ),
                )
            )

        scored.sort(
            key=lambda pair: pair[0],
            reverse=True,
        )

        return [
            item
            for _, item
            in scored[
                :self.max_results
            ]
        ]
