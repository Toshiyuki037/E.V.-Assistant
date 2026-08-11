"""
Phase 12F Research Adapter Regression
"""

import assistant.research.state as state


from assistant.research.controller import (
    create_project,
    add_hypothesis,
)


from assistant.workspace.adapters.base import (
    AdapterContext,
)


from assistant.workspace.adapters.research import (
    ResearchAdapter,
)


def test_research_adapter(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        state,
        "ROOT",
        tmp_path
        / "research",
    )


    project = create_project(
        "FPGA Research",
        "Study FPGA neural network architecture.",
        project_id=
            "fpga-research",
    )


    add_hypothesis(
        project.project_id,
        (
            "Pipelining improves "
            "FPGA timing closure."
        ),
    )


    adapter = ResearchAdapter()


    results = adapter.search(
        "timing closure",
        AdapterContext(
            project=
                project.project_id,
        ),
    )


    assert results

    assert any(
        (
            "timing closure"
            in item.content.lower()
        )
        for item
        in results
    )