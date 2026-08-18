"""Cheap conservative Phase 16B request-cost classifier."""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class RequestCostProfile:
    run_intelligent_memory: bool
    allow_long_term_memory: bool
    allow_project_knowledge: bool
    mode: str
    reason: str

EXPLICIT_MEMORY = ("remember that", "remember ", "forget that", "forget ", "save this", "store this", "update my memory")
PERSONAL_RECALL = (
    "do you remember", "what did i ", "what did we ", "what was my ", "what is my ", "what's my ",
    "my preference", "last time", "previously", "earlier we", "earlier i", "we decided", "we discussed",
    "i told you", "i said before", "our previous", "from before", "my goal", "my project", "my research", "my plan",
)
PROJECT_SIGNALS = (
    "this project", "my project", "our project", "codebase", "workspace", "repository", " repo ", "implemented",
    "implementation", "which file", "what file", "assistant/", "assistant\\", ".py", ".js", ".ts", ".cpp", ".vhd", ".sv",
)
SOCIAL = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "thanks", "thank you", "okay", "ok", "yes", "no", "cool", "nice"}
FIRST_PERSON_DURABLE = re.compile(r"\b(i am|i'm|i prefer|i like|i dislike|i want|i need|i plan|i study|i work|i live|i use|i have|i own|my favorite|my preferred|my default|my goal|my plan|my project|my research)\b", re.I)
QUESTION_START = re.compile(r"^\s*(what|why|how|when|where|who|which|is|are|can|could|would|should|do|does|did)\b", re.I)
GENERIC_QUESTION = re.compile(r"^\s*(what is|what's|who is|why|how|explain|define|calculate|convert|is |are |can )", re.I)

def _norm(text):
    return re.sub(r"\s+", " ", str(text or "").strip().lower())

def _has(text, phrases):
    return any(p in text for p in phrases)

def _project(text):
    if _has(text, PROJECT_SIGNALS):
        return True
    if text.startswith(("where is ", "where does ")):
        return _has(text, ("memory", "planner", "router", "handler", "function", "class", "module", "code", "project"))
    return False

def classify_request_cost(user_text):
    text = _norm(user_text)
    if not text:
        return RequestCostProfile(False, False, False, "fast", "empty")
    if _has(text, EXPLICIT_MEMORY):
        return RequestCostProfile(True, True, False, "important", "explicit_memory")
    if _has(text, PERSONAL_RECALL):
        return RequestCostProfile(True, True, _project(text), "contextual", "personal_recall")
    if FIRST_PERSON_DURABLE.search(text) and not QUESTION_START.search(text):
        return RequestCostProfile(True, True, _project(text), "contextual", "durable_first_person_information")
    if _project(text):
        return RequestCostProfile(False, False, True, "project", "project_knowledge")
    if text.strip(" .!?,") in SOCIAL:
        return RequestCostProfile(False, False, False, "fast", "social_fast_path")
    if GENERIC_QUESTION.search(text):
        return RequestCostProfile(False, False, False, "fast", "general_reasoning")
    if not FIRST_PERSON_DURABLE.search(text):
        return RequestCostProfile(False, False, False, "fast", "nonpersonal_request")
    return RequestCostProfile(True, True, True, "full", "ambiguous_preserve_context")

def should_run_intelligent_memory(user_text):
    return classify_request_cost(user_text).run_intelligent_memory
