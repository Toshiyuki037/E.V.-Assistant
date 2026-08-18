from assistant.performance.fast_path import classify_request_cost, should_run_intelligent_memory
from assistant.performance.request_context import current_performance_hints, performance_request_context

def test_general_question_is_fast():
    p = classify_request_cost("How does a transistor work?")
    assert not p.run_intelligent_memory
    assert not p.allow_long_term_memory
    assert not p.allow_project_knowledge

def test_social_turn_is_fast():
    assert classify_request_cost("Good morning").mode == "fast"

def test_personal_recall_preserves_memory():
    p = classify_request_cost("What did I decide about my FPGA research?")
    assert p.run_intelligent_memory and p.allow_long_term_memory

def test_durable_personal_statement_preserves_memory():
    assert should_run_intelligent_memory("I prefer concise spoken answers.")

def test_project_question_preserves_project_retrieval_only():
    p = classify_request_cost("Where is memory retrieval implemented in this project?")
    assert not p.run_intelligent_memory
    assert not p.allow_long_term_memory
    assert p.allow_project_knowledge

def test_context_restores():
    before = current_performance_hints()
    with performance_request_context(allow_long_term_memory=False, allow_project_knowledge=False, reason="test"):
        assert not current_performance_hints().allow_long_term_memory
    assert current_performance_hints() == before
