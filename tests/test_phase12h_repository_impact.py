import assistant.workspace.repository.store as repo_store

from assistant.workspace.repository.controller import index_repository
from assistant.coding.impact import analyze_file_impact, analyze_change_scope


def test_impact_analysis_finds_dependents(tmp_path, monkeypatch):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path / "runtime",
    )

    package = tmp_path / "assistant"
    package.mkdir()

    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "service.py").write_text(
        "from .core import VALUE\ndef read(): return VALUE\n",
        encoding="utf-8",
    )
    (package / "main.py").write_text(
        "from .service import read\nprint(read())\n",
        encoding="utf-8",
    )

    index_repository(
        str(tmp_path),
        repository="impact-test",
    )

    analysis = analyze_file_impact(
        "impact-test",
        "assistant/core.py",
    )

    paths = {
        item["node"].path
        for item in analysis["transitive_importers"]
    }

    assert "assistant/service.py" in paths
    assert "assistant/main.py" in paths


def test_change_scope_combines_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path / "runtime",
    )

    package = tmp_path / "assistant"
    package.mkdir()

    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "a.py").write_text("A = 1\n", encoding="utf-8")
    (package / "b.py").write_text("from .a import A\n", encoding="utf-8")

    index_repository(
        str(tmp_path),
        repository="scope-test",
    )

    result = analyze_change_scope(
        "scope-test",
        [
            "assistant/a.py",
            "assistant/b.py",
        ],
    )

    assert len(result["analyses"]) == 2
