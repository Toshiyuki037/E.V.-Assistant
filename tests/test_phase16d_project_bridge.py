from assistant.performance.project_bridge import augment_with_project_evidence

def test_disabled_project_bridge_is_identity():
    text = "Where is memory retrieval implemented?"
    assert augment_with_project_evidence(text, allow_project_knowledge=False) == text
