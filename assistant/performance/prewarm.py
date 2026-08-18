"""Background prewarming for E.V.I.E.'s existing semantic-memory singletons."""
from dataclasses import dataclass, field
import os, threading, time

@dataclass
class PrewarmStatus:
    started: bool = False
    running: bool = False
    finished: bool = False
    disabled: bool = False
    started_at: float | None = None
    finished_at: float | None = None
    timings: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)
    @property
    def duration(self):
        if self.started_at is None:
            return None
        return max(0.0, (self.finished_at or time.monotonic()) - self.started_at)

_LOCK = threading.RLock()
_DONE = threading.Event()
_THREAD = None
_STATUS = PrewarmStatus()

def _enabled():
    value = (os.getenv("EVIE_MEMORY_PREWARM") or os.getenv("EVIE_PREWARM_MODE") or "on").strip().lower()
    return value not in {"0", "false", "off", "disabled", "none"}

def _warm_embedding_model():
    from ..memory.embeddings import create_embedding
    t = time.monotonic()
    create_embedding("E.V.I.E. semantic memory prewarm.")
    _STATUS.timings["memory_embedding"] = time.monotonic() - t

def _warm_reranker():
    from ..memory import retriever
    t = time.monotonic()
    getter = None
    for name in ("get_reranker", "get_reranker_model", "_get_reranker", "_get_reranker_model"):
        candidate = getattr(retriever, name, None)
        if callable(candidate):
            getter = candidate
            break
    if getter:
        model = getter()
        predict = getattr(model, "predict", None)
        if callable(predict):
            predict([["E.V.I.E. prewarm query", "E.V.I.E. prewarm candidate"]])
    else:
        retrieve = getattr(retriever, "retrieve_memories", None)
        if callable(retrieve):
            retrieve(query="E.V.I.E. prewarm", limit=2, use_reranker=True)
    _STATUS.timings["memory_reranker"] = time.monotonic() - t

def _worker(delay):
    try:
        if delay:
            time.sleep(delay)
        with _LOCK:
            _STATUS.started = True; _STATUS.running = True; _STATUS.started_at = time.monotonic()
        print("[Performance] Background memory prewarm started.")
        for name, fn in (("memory_embedding", _warm_embedding_model), ("memory_reranker", _warm_reranker)):
            try:
                fn()
            except BaseException as exc:
                with _LOCK:
                    _STATUS.errors[name] = f"{type(exc).__name__}: {exc}"
        with _LOCK:
            _STATUS.running = False; _STATUS.finished = True; _STATUS.finished_at = time.monotonic()
            duration = _STATUS.duration or 0.0; errors = len(_STATUS.errors)
        if errors:
            print(f"[Performance] Memory prewarm finished in {duration:.2f}s with {errors} non-fatal warning(s).")
        else:
            print(f"[Performance] Memory models ready in {duration:.2f}s.")
    finally:
        _DONE.set()

def start_background_prewarm(delay_seconds=1.0):
    global _THREAD
    with _LOCK:
        if not _enabled():
            _STATUS.disabled = True; _STATUS.finished = True; _DONE.set(); return None
        if _THREAD is not None and _THREAD.is_alive():
            return _THREAD
        if _STATUS.finished:
            return _THREAD
        _THREAD = threading.Thread(target=_worker, args=(max(0.0, float(delay_seconds)),), name="evie-model-prewarm", daemon=True)
        _THREAD.start()
        return _THREAD

def wait_for_prewarm(timeout=None):
    return _DONE.wait(timeout)

def get_prewarm_status():
    with _LOCK:
        return PrewarmStatus(_STATUS.started, _STATUS.running, _STATUS.finished, _STATUS.disabled, _STATUS.started_at, _STATUS.finished_at, dict(_STATUS.timings), dict(_STATUS.errors))

def _reset_for_tests():
    global _THREAD, _STATUS
    with _LOCK:
        _THREAD = None; _STATUS = PrewarmStatus(); _DONE.clear()
