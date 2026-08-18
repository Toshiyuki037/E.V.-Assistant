from assistant.performance import prewarm

def test_background_prewarm_is_idempotent(monkeypatch):
    prewarm._reset_for_tests()
    calls = []
    monkeypatch.setattr(prewarm, "_enabled", lambda: True)
    monkeypatch.setattr(prewarm, "_warm_embedding_model", lambda: calls.append("embedding"))
    monkeypatch.setattr(prewarm, "_warm_reranker", lambda: calls.append("reranker"))
    first = prewarm.start_background_prewarm(delay_seconds=0.0)
    second = prewarm.start_background_prewarm(delay_seconds=0.0)
    assert first is not None
    assert second is first
    assert prewarm.wait_for_prewarm(timeout=1.0)
    assert calls == ["embedding", "reranker"]
    status = prewarm.get_prewarm_status()
    assert status.finished is True
    assert status.running is False

def test_model_failure_is_nonfatal(monkeypatch):
    prewarm._reset_for_tests()
    monkeypatch.setattr(prewarm, "_enabled", lambda: True)
    def fail(): raise RuntimeError("synthetic")
    monkeypatch.setattr(prewarm, "_warm_embedding_model", fail)
    monkeypatch.setattr(prewarm, "_warm_reranker", lambda: None)
    prewarm.start_background_prewarm(delay_seconds=0.0)
    assert prewarm.wait_for_prewarm(timeout=1.0)
    assert "memory_embedding" in prewarm.get_prewarm_status().errors
