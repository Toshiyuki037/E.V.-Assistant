"""
E.V.I.E. - Single Tool Planner

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Converts simple natural-language computer requests into one
    controlled Phase 6 tool action.

Capabilities:
    - single-action tool planning
    - exact registered tool signatures
    - active-workspace grounding
    - recent-conversation referent grounding
    - follow-up references such as "it", "that", and "the one you found"
    - compatibility with existing brain.py tool-routing logic
    - lazy OpenAI client initialization
    - safe argument parsing
    - no direct execution

Important:
    This planner handles ONE immediate computer action only.

    Multi-step, adaptive, iterative, debugging, and retry-until-success
    requests belong to Phase 7.

Most Recent Change:
    Restored ToolPlan.arguments compatibility for brain.py while keeping
    arguments_json as the structured model output field.
"""

import inspect
import json

from dotenv import load_dotenv
from openai import OpenAI

from pydantic import (
    BaseModel,
    Field,
)

from assistant.memory.database import (
    get_recent_conversations,
)

from assistant.perception.workspace import (
    get_workspace_context,
)

from .registry import (
    list_tools,
    load_default_tools,
)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------------------------
# Lazy OpenAI Client
# ---------------------------------------------------------------------------

def get_openai_client():
    """
    Creates the planner OpenAI client only when planning is needed.
    """

    return OpenAI()


# ---------------------------------------------------------------------------
# Structured Planner Output
# ---------------------------------------------------------------------------

class ToolPlan(BaseModel):
    """
    Structured result returned by the Phase 6 tool planner.

    arguments_json:
        Raw JSON string returned by the structured-output model.

    arguments:
        Compatibility property used by brain.py. It converts
        arguments_json into a Python dictionary.
    """

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
    def arguments(
        self,
    ):
        """
        Compatibility property expected by brain.py.

        Always returns a dictionary.
        """

        if not self.arguments_json:

            return {}


        try:

            value = json.loads(
                self.arguments_json
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            return {}


        if not isinstance(
            value,
            dict,
        ):

            return {}


        return value


# ---------------------------------------------------------------------------
# Planner Instructions
# ---------------------------------------------------------------------------

TOOL_PLANNER_PROMPT = """
You are E.V.I.E.'s Phase 6 single-action computer tool planner.

Your job is to decide whether the CURRENT user message requests ONE
immediate computer action.

If exactly one computer action should occur:

    use_tool = true

If no computer action is needed:

    use_tool = false

If the request is clearly multi-step, adaptive, iterative, debugging,
or asks E.V.I.E. to continue working based on future results:

    use_tool = false

Those requests belong to Phase 7.


GENERAL RULES

1. Use ONLY registered tools.

2. Never invent tool names.

3. Use exact parameter names from registered Python signatures.

4. Never claim a tool executed.

5. Never invent file paths.

6. Never invent URLs.

7. Never invent application names.

8. Never invent workspace paths.

9. Prefer dedicated tools over run_command.

10. Plan no more than ONE computer action.

11. Do not turn ordinary questions into tool actions.

12. Preserve specific objects from recent conversation.

13. Never replace a specific previously identified object with a more
    generic destination.

14. If a conversational reference is ambiguous, do not guess.


CONVERSATIONAL REFERENTS

The CURRENT user message may depend on recent conversation.

Examples:

    "Open it."
    "Open that."
    "Run it."
    "Run that."
    "Open the one you found."
    "Open that video."
    "Open it on YouTube."
    "Go there."
    "Open that repo."
    "Show me that file."
    "Focus it."

Use RECENT CONVERSATION CONTEXT to resolve these references.

The most recent relevant explicit object has priority.


YOUTUBE EXAMPLE

Earlier:

User:
    Hacksmith on YouTube

E.V.I.E.:
    Hacksmith Industries:
    https://www.youtube.com/@theHacksmith

Current user:
    Open it on YouTube.

Correct:

    use_tool = true
    tool_name = open_url

    arguments:
        {
            "url":
                "https://www.youtube.com/@theHacksmith"
        }

Incorrect:

    {
        "url":
            "https://www.youtube.com"
    }


FILE EXAMPLE

Earlier:

E.V.I.E.:
    Memory retrieval is implemented in:
    assistant/memory/retriever.py

Current user:
    Open it in VS Code.

Correct:

    open_file_in_vscode(
        path="assistant/memory/retriever.py"
    )


AMBIGUITY

If multiple plausible referents exist:

    use_tool = false

Do not guess.


URL RULES

If recent context includes a specific URL and the user refers to it,
preserve that exact URL.

Do not simplify a specific page/channel/video into a generic domain.


WORKSPACE RULES

For tools supporting workspace_path:

- use an explicitly named workspace when available
- otherwise use current active workspace
- never invent a workspace


PHASE 6 EXAMPLES

User:
    Show me my Git status.

Result:
    use_tool = true
    tool_name = git_status


User:
    Open Chrome.

Result:
    use_tool = true
    tool_name = open_application


User:
    Open assistant/main.py in VS Code.

Result:
    use_tool = true
    tool_name = open_file_in_vscode


NO TOOL EXAMPLE

User:
    What's 2 + 2?

Result:
    use_tool = false


PHASE 7 EXAMPLE

User:
    Run the tests and fix whatever fails.

Result:
    use_tool = false

TERSE NAVIGATION REQUESTS:

Users often omit verbs in natural speech.

A short phrase that combines a subject with an application or website
may still represent navigation intent.

Examples:

"Hacksmith on YouTube"
"OpenAI on GitHub"
"ESPN in Chrome"

When the intent is clearly to navigate/search using a website, prefer
the relevant safe browser action rather than asking an unnecessary
clarifying question.

For a YouTube subject without a specific known URL, opening a YouTube
search URL is acceptable.

Example:

User:
    Hacksmith on YouTube

Correct:

    open_url(
        url="https://www.youtube.com/results?search_query=Hacksmith"
    )

Do not invent a specific video URL or channel URL unless that exact URL
already exists in conversation context.

FOLLOW-UP REFERENCES:

If E.V.I.E. just identified or opened a specific URL, phrases such as:

    "open it"
    "go there"
    "open that"
    "open it on YouTube"

should preserve the most recent specific relevant URL.

Do not replace a specific URL with the generic site homepage.
"""


# ---------------------------------------------------------------------------
# Registered Tool Contracts
# ---------------------------------------------------------------------------

def describe_tools():
    """
    Returns exact callable signatures for all currently registered tools.
    """

    load_default_tools()

    blocks = []


    for tool in list_tools():

        try:

            signature = inspect.signature(
                tool.function
            )

        except (
            TypeError,
            ValueError,
        ):

            signature = (
                "(signature unavailable)"
            )


        blocks.append(
            (
                f"Tool: {tool.name}\n"
                f"Category: {tool.category}\n"
                f"Risk: {tool.risk}\n"
                f"Signature: "
                f"{tool.name}{signature}\n"
                f"Description: "
                f"{tool.description}"
            )
        )


    return "\n\n".join(
        blocks
    )


# ---------------------------------------------------------------------------
# Registered Tool Names
# ---------------------------------------------------------------------------

def get_tool_names():
    load_default_tools()

    return {
        tool.name
        for tool
        in list_tools()
    }


# ---------------------------------------------------------------------------
# Current Workspace
# ---------------------------------------------------------------------------

def get_current_workspace():
    try:

        context = (
            get_workspace_context()
        )

    except Exception:

        return {}


    if not isinstance(
        context,
        dict,
    ):

        return {}


    return context


# ---------------------------------------------------------------------------
# Conversation Record Helper
# ---------------------------------------------------------------------------

def first_value(
    data,
    keys,
):
    if data is None:

        return ""


    for key in keys:

        try:

            value = data[
                key
            ]

        except (
            KeyError,
            TypeError,
            IndexError,
        ):

            value = None


        if value:

            return str(
                value
            )


    return ""


# ---------------------------------------------------------------------------
# Tuple Fallback
# ---------------------------------------------------------------------------

def extract_tuple_conversation(
    conversation,
):
    if not isinstance(
        conversation,
        (
            tuple,
            list,
        ),
    ):

        return (
            "",
            "",
        )


    string_values = []


    for item in conversation:

        if isinstance(
            item,
            str,
        ):

            string_values.append(
                item
            )


    if len(string_values) >= 2:

        return (
            string_values[-2],
            string_values[-1],
        )


    if len(string_values) == 1:

        return (
            string_values[0],
            "",
        )


    return (
        "",
        "",
    )


# ---------------------------------------------------------------------------
# Recent Conversation Grounding
# ---------------------------------------------------------------------------

def get_reference_context(
    limit: int = 6,
):
    try:

        conversations = (
            get_recent_conversations(
                limit=limit
            )
        )

    except TypeError:

        try:

            conversations = (
                get_recent_conversations(
                    limit
                )
            )

        except Exception:

            return ""

    except Exception:

        return ""


    if not conversations:

        return ""


    blocks = []


    for conversation in conversations:

        user_text = first_value(
            conversation,
            (
                "user_message",
                "user_text",
                "prompt",
                "user",
                "input",
            ),
        )


        assistant_text = first_value(
            conversation,
            (
                "assistant_response",
                "assistant_text",
                "response",
                "assistant",
                "reply",
                "output",
            ),
        )


        if (
            not user_text
            and not assistant_text
        ):

            (
                user_text,
                assistant_text,
            ) = extract_tuple_conversation(
                conversation
            )


        if user_text:

            blocks.append(
                (
                    "User:\n"
                    f"{user_text}"
                )
            )


        if assistant_text:

            blocks.append(
                (
                    "E.V.I.E.:\n"
                    f"{assistant_text}"
                )
            )


    text = "\n\n".join(
        blocks
    )


    if len(text) > 12000:

        text = text[
            -12000:
        ]


    return text


# ---------------------------------------------------------------------------
# Tool Consideration Gate
# ---------------------------------------------------------------------------

def should_consider_tools(
    user_message: str,
):
    """
    Fast gate used by brain.py before semantic tool planning.
    """

    if not user_message:

        return False


    text = (
        user_message
        .strip()
        .lower()
    )


    if not text:

        return False


    referent_actions = (
        "open it",
        "open that",
        "open this",
        "open the one",
        "run it",
        "run that",
        "run this",
        "run the one",
        "show it",
        "show that",
        "focus it",
        "focus that",
        "launch it",
        "launch that",
        "execute it",
        "execute that",
        "play it",
        "play that",
        "go there",
        "go to it",
        "go to that",
        "navigate there",
        "navigate to it",
    )


    if any(
        phrase in text
        for phrase
        in referent_actions
    ):

        return True


    action_terms = (
        "open ",
        "close ",
        "focus ",
        "show me",
        "run ",
        "execute ",
        "launch ",
        "create ",
        "write ",
        "edit ",
        "modify ",
        "delete ",
        "remove ",
        "stage ",
        "commit ",
        "push ",
        "git status",
        "git log",
        "git diff",
        "git add",
        "pytest",
        "install ",
        "uninstall ",
        "browse ",
        "go to ",
        "navigate ",
        "youtube",
        "website",
        "url",
        "vscode",
        "vs code",
        "chrome",
        "notepad",
        "explorer",
        "powershell",
        "terminal",
    )


    return any(
        term in text
        for term
        in action_terms
    )


# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------

def parse_arguments(
    arguments_json: str,
):
    """
    Converts planner JSON to a dictionary.
    """

    if not arguments_json:

        return {}


    try:

        arguments = json.loads(
            arguments_json
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        return {}


    if not isinstance(
        arguments,
        dict,
    ):

        return {}


    return arguments


# ---------------------------------------------------------------------------
# Workspace Injection
# ---------------------------------------------------------------------------

def inject_workspace(
    tool_name: str,
    arguments: dict,
):
    if (
        "workspace_path"
        in arguments
    ):

        return arguments


    load_default_tools()


    selected_tool = None


    for tool in list_tools():

        if tool.name == tool_name:

            selected_tool = tool

            break


    if selected_tool is None:

        return arguments


    try:

        parameters = inspect.signature(
            selected_tool.function
        ).parameters

    except (
        TypeError,
        ValueError,
    ):

        return arguments


    if (
        "workspace_path"
        not in parameters
    ):

        return arguments


    workspace = (
        get_current_workspace()
    )


    workspace_path = (
        workspace.get(
            "workspace_path"
        )
    )


    if workspace_path:

        arguments[
            "workspace_path"
        ] = workspace_path


    return arguments


# ---------------------------------------------------------------------------
# Build Prompt
# ---------------------------------------------------------------------------

def build_planner_prompt(
    user_message: str,
):
    recent_context = (
        get_reference_context()
    )


    workspace_context = (
        get_current_workspace()
    )


    workspace_json = json.dumps(
        workspace_context,
        default=str,
        indent=2,
        ensure_ascii=False,
    )


    tool_descriptions = (
        describe_tools()
    )


    reference_context = (
        recent_context
        or "[none available]"
    )


    return (
        TOOL_PLANNER_PROMPT
        + "\n\n"
        + "REGISTERED TOOL CONTRACTS:\n\n"
        + tool_descriptions
        + "\n\n"
        + "CURRENT LIVE WORKSPACE CONTEXT:\n\n"
        + workspace_json
        + "\n\n"
        + "RECENT CONVERSATION CONTEXT:\n\n"
        + reference_context
        + "\n\n"
        + "CURRENT USER MESSAGE:\n\n"
        + user_message
    )


# ---------------------------------------------------------------------------
# Plan One Tool Action
# ---------------------------------------------------------------------------

def plan_tool_request(
    user_message: str,
):
    if not user_message:

        return ToolPlan(
            use_tool=False,
            confidence=100,
            summary=(
                "No user message was provided."
            ),
        )


    user_message = (
        user_message.strip()
    )


    if not user_message:

        return ToolPlan(
            use_tool=False,
            confidence=100,
            summary=(
                "No user message was provided."
            ),
        )


    prompt = build_planner_prompt(
        user_message
    )


    try:

        planner_client = (
            get_openai_client()
        )


        response = (
            planner_client.responses.parse(
                model="gpt-5.5",

                instructions=(
                    "Plan at most one immediate controlled "
                    "computer action. Resolve clear references "
                    "from recent conversation context. Use only "
                    "registered tool signatures."
                ),

                input=
                    prompt,

                text_format=
                    ToolPlan,
            )
        )


        plan = (
            response.output_parsed
        )


    except Exception as error:

        return ToolPlan(
            use_tool=False,
            confidence=0,
            summary=(
                "Tool planning failed: "
                f"{error}"
            ),
        )


    if plan is None:

        return ToolPlan(
            use_tool=False,
            confidence=0,
            summary=(
                "Tool planner returned "
                "no structured result."
            ),
        )


    if not plan.use_tool:

        return plan


    tool_name = (
        plan.tool_name
        .strip()
        .lower()
    )


    if (
        tool_name
        not in get_tool_names()
    ):

        return ToolPlan(
            use_tool=False,
            confidence=0,
            summary=(
                "The planned tool is "
                "not registered."
            ),
        )


    arguments = (
        parse_arguments(
            plan.arguments_json
        )
    )


    arguments = inject_workspace(
        tool_name,
        arguments,
    )


    plan.tool_name = (
        tool_name
    )


    plan.arguments_json = json.dumps(
        arguments,
        ensure_ascii=False,
    )


    return plan


# ---------------------------------------------------------------------------
# Compatibility Aliases
# ---------------------------------------------------------------------------

def plan_tool_action(
    user_message: str,
):
    return plan_tool_request(
        user_message
    )


def plan_tool(
    user_message: str,
):
    return plan_tool_request(
        user_message
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Tool Planner"
    )

    print(
        "----------------------"
    )


    print()

    sample = ToolPlan(
        use_tool=True,
        tool_name="git_status",
        arguments_json=(
            '{"workspace_path":"C:/test"}'
        ),
        confidence=100,
    )


    print(
        "Compatibility test:"
    )

    print(
        "arguments_json:",
        sample.arguments_json,
    )

    print(
        "arguments:",
        sample.arguments,
    )


    print()

    tests = (
        "What's 2 + 2?",
        "Show me my Git status.",
        (
            "Open assistant/memory/"
            "retriever.py in VS Code."
        ),
        "Open YouTube.",
        "Open it on YouTube.",
    )


    for message in tests:

        print()

        print(
            "User:",
            message,
        )


        print(
            "Should consider tools:",
            should_consider_tools(
                message
            ),
        )


        result = (
            plan_tool_request(
                message
            )
        )


        print(
            result
        )


        print(
            "Parsed arguments:",
            result.arguments,
        )