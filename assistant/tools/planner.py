"""
E.V.I.E. - Tool Planner

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Converts natural-language action requests into one structured
    E.V.I.E. tool request.

Important:
    This module plans actions only.

    It does not execute tools and cannot bypass E.V.I.E.'s
    permission engine or executor.
"""

import json
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# Structured Plan
# ---------------------------------------------------------------------------

class ToolPlan(BaseModel):
    use_tool: bool = False

    tool_name: str = ""

    arguments_json: str = "{}"

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    summary: str = ""

    @property
    def arguments(self) -> dict[str, Any]:
        """
        Decodes planner arguments from a JSON object string.

        A fixed string field keeps the structured-output schema simple
        while still supporting different argument shapes per tool.
        """

        try:
            value = json.loads(
                self.arguments_json
                or "{}"
            )

        except json.JSONDecodeError:
            return {}

        if not isinstance(
            value,
            dict,
        ):
            return {}

        return value


# ---------------------------------------------------------------------------
# Tool Argument Guide
# ---------------------------------------------------------------------------

TOOL_ARGUMENT_GUIDE = {
    "list_directory": {
        "path": "optional relative path; default '.'",
    },

    "read_file": {
        "path": "required workspace-relative file path",
    },

    "create_file": {
        "path": "required workspace-relative new file path",
        "content": "optional text content",
    },

    "write_file": {
        "path": "required workspace-relative existing file path",
        "content": "required replacement text",
    },

    "run_command": {
        "arguments": (
            "required argument-array using an approved executable; "
            "never a shell command string"
        ),
        "cwd": "optional workspace-relative working directory",
    },

    "run_python": {
        "arguments": "optional Python argument-array",
        "cwd": "optional workspace-relative working directory",
    },

    "run_tests": {
        "test_path": "optional pytest path",
        "cwd": "optional workspace-relative working directory",
    },

    "git_status": {},

    "git_diff": {
        "staged": "optional boolean",
    },

    "git_log": {
        "limit": "optional integer, default 10",
    },

    "git_add": {
        "paths": "required list of workspace-relative paths",
    },

    "git_commit": {
        "message": "required commit message",
    },

    "git_push": {
        "remote": "optional remote name, default origin",
        "branch": "optional branch",
    },

    "open_application": {
        "name": (
            "required approved application alias such as "
            "vscode, chrome, notepad, explorer, powershell"
        ),
    },

    "focus_application": {
        "name": (
            "required approved application alias such as "
            "vscode, chrome, notepad, explorer, powershell"
        ),
    },

    "open_url": {
        "url": "required HTTP or HTTPS URL",
    },

    "open_file_in_vscode": {
        "path": "required workspace-relative file path",
        "line": "optional line number >= 1",
    },

    "open_workspace_in_vscode": {},
}


# ---------------------------------------------------------------------------
# Intent Routing
# ---------------------------------------------------------------------------

TOOL_INTENT_TERMS = (
    "open ",
    "launch ",
    "focus ",
    "switch to ",
    "bring up ",
    "run ",
    "test ",
    "tests",
    "execute ",
    "create ",
    "make a file",
    "write ",
    "edit ",
    "change ",
    "replace ",
    "stage ",
    "add to git",
    "commit ",
    "push ",
    "git status",
    "git diff",
    "git log",
    "show my git",
    "show git",
    "what changed",
    "what have i changed",
    "browse ",
    "go to ",
    "visit ",
    "open url",
    "open website",
)


def should_consider_tools(
    user_message: str,
) -> bool:
    """
    Fast local gate that avoids an extra planner request for obviously
    conversational prompts.
    """

    text = user_message.strip().lower()

    if not text:
        return False

    return any(
        term in text
        for term in TOOL_INTENT_TERMS
    )


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

def build_tool_catalog() -> str:
    lines = []

    for name, arguments in TOOL_ARGUMENT_GUIDE.items():

        lines.append(
            f"TOOL: {name}"
        )

        if arguments:

            lines.append(
                "ARGUMENTS:"
            )

            for argument, description in arguments.items():

                lines.append(
                    f"- {argument}: {description}"
                )

        else:

            lines.append(
                "ARGUMENTS: none"
            )

        lines.append(
            ""
        )

    return "\n".join(
        lines
    ).strip()


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

def plan_tool_request(
    user_message: str,
):
    """
    Returns exactly one ToolPlan.

    The executor remains authoritative. A planned tool is never
    automatically trusted merely because the model selected it.
    """

    if not should_consider_tools(
        user_message
    ):

        return ToolPlan(
            use_tool=False,
            confidence=100,
            summary=(
                "The message does not appear to request "
                "a computer action."
            ),
        )

    catalog = build_tool_catalog()

    instructions = """
You are E.V.I.E.'s computer-action planner.

Your only job is to decide whether the user's current message asks
E.V.I.E. to perform ONE immediate computer action using one available
tool.

Rules:

1. Do not execute anything.
2. Select only tools from the provided catalog.
3. Return use_tool=false for informational questions that do not ask
   for an action.
4. Put tool arguments in arguments_json as a valid JSON OBJECT STRING.
   Example: {"paths":["assistant/tools/git.py"]} must be returned as
   a string containing that JSON object.
5. Never invent paths, URLs, commit messages, file contents, application
   names, or command arguments that the user did not provide or that
   cannot be safely inferred from the request.
6. Prefer structured tools over run_command.
7. Use run_command only when no dedicated tool represents the requested
   action.
8. Do not put shell metacharacters, pipes, redirects, &&, ||, ;, or
   PowerShell expressions into run_command. Its arguments must be a
   normal argv list.
9. Do not include workspace_path. The host application binds the
   selected workspace after planning.
10. If the user asks for multiple separate actions, choose only the first
   immediately actionable step. Multi-step autonomy belongs to a later
   phase.
11. The summary must briefly describe the proposed action, not hidden
    reasoning.
"""

    prompt = f"""
USER REQUEST:
{user_message}

AVAILABLE TOOLS:
{catalog}
""".strip()

    try:

        response = client.responses.parse(
            model="gpt-5.5",
            instructions=instructions,
            input=prompt,
            text_format=ToolPlan,
        )

        plan = response.output_parsed

        if plan is None:

            return ToolPlan(
                use_tool=False,
                confidence=0,
                summary=(
                    "The tool planner returned no structured result."
                ),
            )

        if (
            plan.use_tool
            and plan.tool_name
            not in TOOL_ARGUMENT_GUIDE
        ):

            return ToolPlan(
                use_tool=False,
                confidence=0,
                summary=(
                    "The planner selected an unknown tool."
                ),
            )

        return plan

    except Exception as error:

        print(
            "\n[Tool Planner Warning]"
        )

        print(
            error
        )

        return ToolPlan(
            use_tool=False,
            confidence=0,
            summary=(
                "Tool planning is temporarily unavailable."
            ),
        )


if __name__ == "__main__":

    print(
        "E.V.I.E. Tool Planner"
    )

    print(
        "----------------------"
    )

    tests = (
        "What's 2 + 2?",
        "Show me my Git status.",
        "Open assistant/memory/retriever.py in VS Code.",
        "Stage assistant/tools/git.py.",
    )

    for message in tests:

        print()
        print(
            "User:",
            message,
        )

        print(
            plan_tool_request(
                message
            )
        )
