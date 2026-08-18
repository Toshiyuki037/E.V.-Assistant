from pathlib import Path
import re
import shutil
import py_compile

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "assistant" / "main.py"
SPEAK = ROOT / "assistant" / "speak.py"


def backup(path: Path):
    target = path.with_suffix(path.suffix + ".phase16cde.bak")
    if not target.exists():
        shutil.copy2(path, target)
        print("Backup:", target)


def patch_main_imports(text: str) -> str:
    imports = (
        "from .performance.conversation_fastpath import (\n"
        "    handle_fast_conversation,\n"
        ")\n\n"
        "from .performance.context_budget import (\n"
        "    context_budget_for_profile,\n"
        ")\n\n"
        "from .performance.project_bridge import (\n"
        "    augment_with_project_evidence,\n"
        ")\n\n"
        "from .voice.tts_prewarm import (\n"
        "    start_tts_prewarm,\n"
        ")\n"
    )

    if "from .performance.conversation_fastpath import (" in text:
        return text

    anchor = (
        "from .performance import (\n"
        "    classify_request_cost,\n"
        "    performance_request_context,\n"
        "    start_background_prewarm,\n"
        ")\n"
    )

    if anchor not in text:
        raise RuntimeError("Phase 16A/B import block not found in assistant/main.py.")

    return text.replace(anchor, anchor + "\n" + imports, 1)


def patch_fast_conversation(text: str) -> str:
    if "phase16_fast_conversation" in text:
        return text

    process_start = text.find("def process_prompt(")
    if process_start == -1:
        raise RuntimeError("Could not locate process_prompt() in assistant/main.py.")

    request_print = re.search(
        r'    print\(\s*f["\']\\nYou:\s*\{user_text\}["\']\s*\)\s*',
        text[process_start:],
        re.MULTILINE,
    )

    if request_print is None:
        raise RuntimeError("Could not locate the existing You: {user_text} print inside process_prompt().")

    absolute_end = process_start + request_print.end()

    block = (
        "\n"
        "    # -----------------------------------------------------------------------\n"
        "    # Phase 16C - Deterministic Conversational Fast Path\n"
        "    # -----------------------------------------------------------------------\n\n"
        "    phase16_fast_conversation = (\n"
        "        handle_fast_conversation(\n"
        "            user_text\n"
        "        )\n"
        "    )\n\n"
        "    if phase16_fast_conversation.handled:\n\n"
        "        complete_response(\n"
        "            user_text,\n"
        "            phase16_fast_conversation.response,\n"
        "        )\n\n"
        "        return\n\n"
    )

    return text[:absolute_end] + block + text[absolute_end:]


def patch_project_evidence(text: str) -> str:
    if "phase16_context_budget = (" in text:
        return text

    old = (
        "            contextual_user_text = (\n"
        "                build_contextual_expansion_prompt(\n"
        "                    user_text\n"
        "                )\n"
        "            )\n\n\n"
        "            reasoning_text = (\n"
        "                apply_response_length_policy(\n"
        "                    contextual_user_text,\n"
        "                    voice_mode=\n"
        "                        True,\n"
        "                )\n"
        "            )\n"
    )

    new = (
        "            phase16_context_budget = (\n"
        "                context_budget_for_profile(\n"
        "                    phase16_cost_profile\n"
        "                )\n"
        "            )\n\n\n"
        "            contextual_user_text = (\n"
        "                build_contextual_expansion_prompt(\n"
        "                    user_text\n"
        "                )\n"
        "            )\n\n\n"
        "            contextual_user_text = (\n"
        "                augment_with_project_evidence(\n"
        "                    contextual_user_text,\n"
        "                    allow_project_knowledge=(\n"
        "                        phase16_cost_profile.allow_project_knowledge\n"
        "                    ),\n"
        "                    limit=phase16_context_budget.project_items,\n"
        "                    max_characters=phase16_context_budget.project_characters,\n"
        "                )\n"
        "            )\n\n\n"
        "            reasoning_text = (\n"
        "                apply_response_length_policy(\n"
        "                    contextual_user_text,\n"
        "                    voice_mode=\n"
        "                        True,\n"
        "                )\n"
        "            )\n"
    )

    if old not in text:
        raise RuntimeError("Could not locate the current contextual_user_text/reasoning_text block.")

    return text.replace(old, new, 1)


def patch_tts_prewarm(text: str) -> str:
    if re.search(r"(?m)^start_tts_prewarm\(\)\s*$", text):
        return text

    match = re.search(
        r"(?m)^start_background_prewarm\(\s*\n\s*delay_seconds=1\.0\s*\n\)\s*$",
        text,
    )

    if match is None:
        raise RuntimeError("Could not locate Phase 16A start_background_prewarm() call.")

    replacement = match.group(0) + "\n\nstart_tts_prewarm()"
    return text[:match.start()] + replacement + text[match.end():]


def patch_main(text: str) -> str:
    text = patch_main_imports(text)
    text = patch_fast_conversation(text)
    text = patch_project_evidence(text)
    text = patch_tts_prewarm(text)
    return text


def patch_speak(text: str) -> str:
    if "from .voice.low_latency import (" not in text:
        anchor = "from __future__ import annotations\n"
        if anchor not in text:
            raise RuntimeError("Could not locate speak.py future import.")
        text = text.replace(
            anchor,
            anchor
            + "\nfrom .voice.low_latency import (\n"
              "    prepare_low_latency_chunks,\n"
              ")\n",
            1,
        )

    start = text.find("def speak_streaming_response")
    if start == -1:
        raise RuntimeError("Could not locate speak_streaming_response() in assistant/speak.py.")

    if "prepare_low_latency_chunks(" in text[start:]:
        return text

    pattern = re.compile(
        r"    chunks = \(\s*prepare_spoken_chunks\(\s*text,\s*sentences_per_chunk=\s*sentences_per_chunk,\s*max_chunk_characters=\s*max_chunk_characters,\s*\)\s*\)",
        re.MULTILINE,
    )

    match = pattern.search(text, start)
    if match is None:
        raise RuntimeError("Could not locate prepare_spoken_chunks() block in speak_streaming_response().")

    original = match.group(0)
    addition = (
        "\n\n"
        "    chunks = (\n"
        "        prepare_low_latency_chunks(\n"
        "            chunks\n"
        "        )\n"
        "    )"
    )

    return text[:match.start()] + original + addition + text[match.end():]


def main():
    for path in (MAIN, SPEAK):
        if not path.exists():
            raise SystemExit(f"Missing expected file: {path}")
        backup(path)

    main_text = patch_main(MAIN.read_text(encoding="utf-8"))
    MAIN.write_text(main_text, encoding="utf-8")

    speak_text = patch_speak(SPEAK.read_text(encoding="utf-8"))
    SPEAK.write_text(speak_text, encoding="utf-8")

    py_compile.compile(str(MAIN), doraise=True)
    py_compile.compile(str(SPEAK), doraise=True)

    print()
    print("Phase 16C/D/E applied successfully.")
    print("assistant/main.py and assistant/speak.py compile successfully.")


if __name__ == "__main__":
    main()
