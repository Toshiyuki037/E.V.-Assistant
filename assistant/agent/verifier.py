"""
E.V.I.E. - Agent Verifier

Created: August 9, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Provides Phase 7 execution verification, failure recovery,
    dynamic continuation planning, and final goal verification.

Capabilities:
    - deterministic Phase 6 result verification
    - stdout / stderr inspection
    - exact tool-signature awareness
    - failed-step recovery
    - dynamic continuation after successful investigative steps
    - Phase 8 browser-result preservation
    - Phase 8 research continuation
    - final goal completion verification
    - final result synthesis from verified task evidence

Important:
    This module NEVER executes tools.

    It only interprets real execution results and determines
    what the agent should do next.

Architecture:
    Phase 7 remains the reasoning / orchestration layer.

    Every real computer action continues through the existing
    Phase 6 executor, registry, permission system, and deterministic
    verification layer.

Most Recent Change:
    Added Phase 8 browser evidence to task-history reasoning and fixed
    research completion so the final verifier generates the user-facing
    research summary rather than requiring that summary to have already
    been delivered before verification.
"""

import inspect
import json

from dotenv import load_dotenv
from openai import OpenAI

from pydantic import (
    BaseModel,
    Field,
)

from assistant.tools.registry import (
    list_tools,
    load_default_tools,
)

from assistant.tools.verifier import (
    verify_tool_result as
    verify_phase6_tool_result,
)

from .models import (
    AgentStep,
    AgentTask,
)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# Structured Models
# ---------------------------------------------------------------------------

class PlannedAgentStep(BaseModel):
    description: str

    tool_name: str

    arguments_json: str = "{}"


class RecoveryDecision(BaseModel):
    action: str

    reason: str = ""

    next_steps: list[
        PlannedAgentStep
    ] = Field(
        default_factory=list
    )


class ContinuationDecision(BaseModel):
    complete: bool

    reason: str = ""

    next_steps: list[
        PlannedAgentStep
    ] = Field(
        default_factory=list
    )


class CompletionDecision(BaseModel):
    complete: bool

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    summary: str = ""

    missing: list[str] = Field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# Registered Tool Contracts
# ---------------------------------------------------------------------------

def describe_agent_tools():
    """
    Gives recovery and continuation reasoning access to the exact
    currently registered Phase 6 tool signatures.
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

def get_registered_tool_names():
    load_default_tools()

    return {
        tool.name
        for tool
        in list_tools()
    }


# ---------------------------------------------------------------------------
# Deterministic Phase 6 Verification
# ---------------------------------------------------------------------------

def verify_step_result(
    execution,
):
    """
    Uses the existing Phase 6 deterministic verifier.
    """

    return (
        verify_phase6_tool_result(
            execution
        )
    )


# ---------------------------------------------------------------------------
# Compact Browser Search Results
# ---------------------------------------------------------------------------

def compact_browser_results(
    results,
    limit: int = 15,
):
    """
    Preserves structured browser-search results without allowing a
    very large result list to flood Phase 7 reasoning context.

    Search titles and canonical URLs remain unchanged.
    """

    if not isinstance(
        results,
        list,
    ):

        return results


    compacted = []


    for item in results[
        :limit
    ]:

        if isinstance(
            item,
            dict,
        ):

            compacted.append(
                {
                    "title":
                        item.get(
                            "title"
                        ),

                    "url":
                        item.get(
                            "url"
                        ),
                }
            )

        else:

            compacted.append(
                item
            )


    return compacted


# ---------------------------------------------------------------------------
# Compact Browser Links
# ---------------------------------------------------------------------------

def compact_browser_links(
    links,
    limit: int = 40,
):
    """
    Preserves useful page links while bounding agent context.
    """

    if not isinstance(
        links,
        list,
    ):

        return links


    compacted = []


    for item in links[
        :limit
    ]:

        if isinstance(
            item,
            dict,
        ):

            compacted.append(
                {
                    "text":
                        item.get(
                            "text"
                        ),

                    "url":
                        (
                            item.get(
                                "url"
                            )
                            or item.get(
                                "href"
                            )
                        ),
                }
            )

        else:

            compacted.append(
                item
            )


    return compacted


# ---------------------------------------------------------------------------
# Compact Browser Tabs
# ---------------------------------------------------------------------------

def compact_browser_tabs(
    tabs,
    limit: int = 25,
):
    """
    Preserves managed-browser tab state for Phase 7 reasoning.
    """

    if not isinstance(
        tabs,
        list,
    ):

        return tabs


    compacted = []


    for item in tabs[
        :limit
    ]:

        if isinstance(
            item,
            dict,
        ):

            compacted.append(
                {
                    "index":
                        item.get(
                            "index"
                        ),

                    "active":
                        item.get(
                            "active"
                        ),

                    "title":
                        item.get(
                            "title"
                        ),

                    "url":
                        item.get(
                            "url"
                        ),
                }
            )

        else:

            compacted.append(
                item
            )


    return compacted


# ---------------------------------------------------------------------------
# Compact Browser Text
# ---------------------------------------------------------------------------

def compact_browser_text(
    text,
    limit: int = 30000,
):
    """
    Preserves enough retrieved source text for meaningful research
    reasoning while bounding continuation / verifier prompt size.
    """

    if not isinstance(
        text,
        str,
    ):

        return text


    if len(text) <= limit:

        return text


    return (
        text[
            :limit
        ]
        + "\n\n"
        + (
            "[Browser text truncated "
            "for agent reasoning]"
        )
    )


# ---------------------------------------------------------------------------
# Compact Tool Results
# ---------------------------------------------------------------------------

def extract_execution_details(
    execution,
):
    """
    Preserves the execution information most useful for Phase 7
    reasoning.

    Existing Phase 6 / Phase 7 fields remain available.

    Phase 8 browser fields are also preserved so continuation and
    completion reasoning can consume real search results, URLs,
    page text, links, tabs, and navigation state rather than trying
    to rediscover them.

    Raw AgentStep.result remains unchanged elsewhere. This function
    only creates a compact LLM-facing representation.
    """

    if not isinstance(
        execution,
        dict,
    ):

        return execution


    details = {
        "success":
            execution.get(
                "success"
            ),

        "executed":
            execution.get(
                "executed"
            ),

        "tool":
            execution.get(
                "tool"
            ),

        "risk":
            execution.get(
                "risk"
            ),

        "requires_approval":
            execution.get(
                "requires_approval"
            ),

        "error":
            execution.get(
                "error"
            ),

        "reason":
            execution.get(
                "reason"
            ),
    }


    result = execution.get(
        "result"
    )


    if isinstance(
        result,
        dict,
    ):

        details["result"] = {
            # ---------------------------------------------------------------
            # Existing Workspace / Terminal Evidence
            # ---------------------------------------------------------------

            "workspace":
                result.get(
                    "workspace"
                ),

            "cwd":
                result.get(
                    "cwd"
                ),

            "command":
                result.get(
                    "command"
                ),

            "command_text":
                result.get(
                    "command_text"
                ),

            "exit_code":
                result.get(
                    "exit_code"
                ),

            "stdout":
                result.get(
                    "stdout"
                ),

            "stderr":
                result.get(
                    "stderr"
                ),

            "timed_out":
                result.get(
                    "timed_out"
                ),

            # ---------------------------------------------------------------
            # Existing Filesystem Evidence
            # ---------------------------------------------------------------

            "file":
                result.get(
                    "file"
                ),

            "directory":
                result.get(
                    "directory"
                ),

            "entries":
                result.get(
                    "entries"
                ),

            "content":
                result.get(
                    "content"
                ),

            # ---------------------------------------------------------------
            # Existing Application / VS Code Evidence
            # ---------------------------------------------------------------

            "opened":
                result.get(
                    "opened"
                ),

            "new_window":
                result.get(
                    "new_window"
                ),

            "focused":
                result.get(
                    "focused"
                ),

            "window_title":
                result.get(
                    "window_title"
                ),

            "pid":
                result.get(
                    "pid"
                ),

            # ---------------------------------------------------------------
            # Phase 8 Browser Lifecycle / Navigation
            # ---------------------------------------------------------------

            "connected":
                result.get(
                    "connected"
                ),

            "closed":
                result.get(
                    "closed"
                ),

            "remaining_tabs":
                result.get(
                    "remaining_tabs"
                ),

            "status":
                result.get(
                    "status"
                ),

            "url":
                result.get(
                    "url"
                ),

            "title":
                result.get(
                    "title"
                ),

            # ---------------------------------------------------------------
            # Phase 8 Browser State
            # ---------------------------------------------------------------

            "tab_count":
                result.get(
                    "tab_count"
                ),

            "active_tab":
                result.get(
                    "active_tab"
                ),

            "active_title":
                result.get(
                    "active_title"
                ),

            "active_url":
                result.get(
                    "active_url"
                ),

            "tabs":
                compact_browser_tabs(
                    result.get(
                        "tabs"
                    )
                ),

            # ---------------------------------------------------------------
            # Phase 8 Search Evidence
            # ---------------------------------------------------------------

            "query":
                result.get(
                    "query"
                ),

            "provider":
                result.get(
                    "provider"
                ),

            "search_url":
                result.get(
                    "search_url"
                ),

            "results":
                compact_browser_results(
                    result.get(
                        "results"
                    )
                ),

            "attempts":
                result.get(
                    "attempts"
                ),

            # ---------------------------------------------------------------
            # Phase 8 Page Intelligence
            # ---------------------------------------------------------------

            "text":
                compact_browser_text(
                    result.get(
                        "text"
                    )
                ),

            "visible_text":
                compact_browser_text(
                    result.get(
                        "visible_text"
                    )
                ),

            "links":
                compact_browser_links(
                    result.get(
                        "links"
                    )
                ),

            "buttons":
                result.get(
                    "buttons"
                ),

            "inputs":
                result.get(
                    "inputs"
                ),

            # ---------------------------------------------------------------
            # Phase 8 Interaction Evidence
            # ---------------------------------------------------------------

            "filled":
                result.get(
                    "filled"
                ),
        }

    else:

        details["result"] = (
            result
        )


    return details


# ---------------------------------------------------------------------------
# Task History
# ---------------------------------------------------------------------------

def build_history(
    task: AgentTask,
):
    """
    Converts the entire current task into compact reasoning context.
    """

    history = []


    for step in task.steps:

        history.append(
            {
                "step_number":
                    step.step_number,

                "description":
                    step.description,

                "tool_name":
                    step.tool_name,

                "arguments":
                    step.arguments,

                "status":
                    step.status,

                "attempts":
                    step.attempts,

                "result":
                    extract_execution_details(
                        step.result
                    ),

                "error":
                    step.error,
            }
        )


    return history


# ---------------------------------------------------------------------------
# Parse Tool Arguments
# ---------------------------------------------------------------------------

def parse_arguments(
    arguments_json: str,
):
    if not arguments_json:

        return {}


    try:

        arguments = json.loads(
            arguments_json
        )

    except json.JSONDecodeError:

        return {}


    if not isinstance(
        arguments,
        dict,
    ):

        return {}


    return arguments


# ---------------------------------------------------------------------------
# Convert Planned Steps
# ---------------------------------------------------------------------------

def convert_planned_steps(
    planned_steps,
    starting_number: int,
):
    """
    Converts model-generated next steps into AgentStep objects.

    Invalid / hallucinated tool names are discarded.
    """

    registered = (
        get_registered_tool_names()
    )

    converted = []


    for planned in planned_steps:

        tool_name = (
            planned.tool_name
            .strip()
            .lower()
        )


        if tool_name not in registered:

            continue


        converted.append(
            AgentStep(
                step_number=(
                    starting_number
                    + len(
                        converted
                    )
                ),

                description=
                    planned.description,

                tool_name=
                    tool_name,

                arguments=
                    parse_arguments(
                        planned.arguments_json
                    ),
            )
        )


    return converted


# ---------------------------------------------------------------------------
# Failure Recovery
# ---------------------------------------------------------------------------

def decide_recovery(
    task: AgentTask,
    failed_step: AgentStep,
):
    """
    Determines what to do after a real failed action.
    """

    payload = {
        "goal":
            task.goal,

        "failed_step": {
            "step_number":
                failed_step.step_number,

            "description":
                failed_step.description,

            "tool_name":
                failed_step.tool_name,

            "arguments":
                failed_step.arguments,

            "attempts":
                failed_step.attempts,

            "error":
                failed_step.error,

            "execution":
                extract_execution_details(
                    failed_step.result
                ),
        },

        "task_history":
            build_history(
                task
            ),

        "available_tools":
            describe_agent_tools(),
    }


    response = (
        client.responses.parse(
            model="gpt-5.5",

            instructions="""
You are E.V.I.E.'s Phase 7 failure recovery controller.

A REAL computer action failed.

You have:
- the original user goal
- the exact failed tool
- the exact arguments used
- actual stdout
- actual stderr
- actual exit code
- the full task history
- exact registered tool signatures

Determine the safest useful next action.


VALID ACTIONS:

retry

    Retry the failed step unchanged.

    Use only for genuinely temporary failures.


replace

    Replace the failed step and remaining work with a corrected
    sequence of tool actions.


continue

    Skip the failed step only when it is genuinely optional to
    the user's original goal.


fail

    Stop only when the goal cannot reasonably or safely continue.


RULES:

1. Read actual stdout and stderr.

2. A non-zero exit code does NOT automatically mean the task
   should stop.

3. Programming errors are normally recoverable.

4. File-not-found errors are normally recoverable if the requested
   file can be located using available tools.

5. Incorrect tool arguments are normally recoverable.

6. When a source-code problem must be fixed:

       inspect the relevant source when necessary
       modify it with write_file
       rerun the program or test

7. write_file and other modifying tools will still pass through
   Phase 6 permissions. Do not avoid them merely because approval
   will be required.

8. Use the exact registered tool signatures.

9. Never invent argument names.

10. Never invent file paths.

11. Never repeat the same known-bad action indefinitely.

12. Return the smallest corrective sequence.

13. Return at most four next steps.

14. If an action discovers information needed for later work,
    include the action that actually uses that information when
    possible.

15. Browser failures follow the same evidence rules.

16. If browser_search_web already produced structured search
    results in task history, those exact returned URLs are real
    observed evidence.

17. Never invent a browser research URL when an unused real search
    result is available.

18. If one research source fails but other relevant real search
    results are available, using another returned result may be
    appropriate.


Example:

Goal:
Run typewriter.py and debug it until successful.

Failure:
typewriter.py was not found.

A search then needs to locate the file.

A useful corrected sequence could be:

1. search/list to locate the requested file
2. run the discovered path

If the exact discovered path is not known yet, it is acceptable
for the corrective sequence to contain only the search step.
The continuation controller will use the real search result afterward.


Example:

Failure:
run_python returned:

SyntaxError: expected ':'

Good recovery:

1. read_file the source
2. write_file corrected source
3. run_python again


Example:

Failure:
run_python() got unexpected keyword argument 'path'

Registered signature:

run_python(arguments=None, cwd=".", workspace_path=None, timeout=60)

Correct action:

replace

Next step:

run_python(
    arguments=["actual_script.py"]
)
""".strip(),

            input=json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ),

            text_format=
                RecoveryDecision,
        )
    )


    return (
        response.output_parsed
    )


# ---------------------------------------------------------------------------
# Continuation Planning
# ---------------------------------------------------------------------------

def decide_continuation(
    task: AgentTask,
):
    """
    Runs when every CURRENTLY PLANNED step has completed.

    This prevents investigative actions from incorrectly ending the
    entire task.

    Phase 8:
        Structured browser_search_web results are preserved in history
        and should be consumed directly rather than rediscovered through
        redundant search-page inspection.
    """

    payload = {
        "goal":
            task.goal,

        "task_history":
            build_history(
                task
            ),

        "available_tools":
            describe_agent_tools(),
    }


    response = (
        client.responses.parse(
            model="gpt-5.5",

            instructions="""
You are E.V.I.E.'s Phase 7 continuation controller.

Every CURRENTLY PLANNED action has finished.

Your job is to determine whether the ORIGINAL USER GOAL is actually
finished.

This is different from asking whether the current plan ended.

A successful investigative action may reveal information that must
be used in another action.


GENERAL EXAMPLE:

Goal:

Run typewriter.py and fix errors until successful.

History:

1. run_python("typewriter.py")
   failed because the file was not found.

2. workspace search
   succeeded and found:
   TypewriterTest/typewriter.py

The task is NOT complete.

Correct next action:

run_python(
    arguments=[
        "TypewriterTest/typewriter.py"
    ]
)


ANOTHER GENERAL EXAMPLE:

Goal:

Debug script until successful.

History:

1. run_python
   SyntaxError

2. read_file
   source was successfully read

The task is NOT complete.

Correct next actions may be:

1. write_file corrected source
2. run_python again


PHASE 8 STRUCTURED BROWSER EVIDENCE

browser_search_web returns structured, real search evidence.

A successful result may contain:

{
    "query": "...",
    "provider": "bing",
    "results": [
        {
            "title": "...",
            "url": "https://..."
        }
    ]
}

These URLs were observed by the real Phase 8 browser-search tool.

They are stronger evidence than model memory, guesses, or assumptions.


WHEN SEARCH RESULTS EXIST:

- consume the returned result objects directly
- use the exact returned URLs
- never invent a source URL
- do not repeat browser_search_web with the same query merely because
  the current plan ended
- do not repeatedly inspect the search-results page merely to
  rediscover URLs already present in structured results
- do not call browser_get_state merely to rediscover the same search
  page
- do not call browser_get_page_context merely to rediscover search
  result links already returned by browser_search_web
- do not browser_read_page the search-results page merely to rediscover
  those same URLs

If the original goal requires opening and reading sources, the normal
next action after a successful search is:

    browser_navigate(
        url=<exact returned result URL>
    )

followed by:

    browser_read_page


RESEARCH WORKFLOW

For a goal such as:

    Research X.
    Search the web.
    Open and read at least three useful sources.
    Compare them.
    Give me a concise summary.

A useful adaptive pattern is:

    browser_search_web
        ↓
    consume real results[]
        ↓
    browser_navigate(source 1)
        ↓
    browser_read_page
        ↓
    browser_navigate(source 2)
        ↓
    browser_read_page
        ↓
    browser_navigate(source 3)
        ↓
    browser_read_page
        ↓
    completion verification / synthesis

Do not perform redundant Bing/search-page inspections between source
reads.


SOURCE SELECTION

1. Select sources from the real browser_search_web results.

2. Prefer relevant and authoritative results when appropriate.

3. Prefer primary sources where they directly answer the user's
   question.

4. Never invent URLs.

5. Avoid reopening a URL already successfully read unless there is
   a real reason to revisit it.

6. Respect the requested number of sources.

7. If the user requested at least three sources, three distinct
   successfully read relevant sources normally satisfy the source
   count.

8. Search again only when:
       existing results are insufficient
       existing results are irrelevant
       existing results are unusable
       another query is genuinely needed


SOURCE READING

Successful browser_navigate proves navigation occurred.

It does NOT prove the source was actually read.

If the original goal requires understanding, comparing, or
summarizing a source, follow navigation with:

    browser_read_page

Use the returned real page text as research evidence.


RULES:

1. Judge the ORIGINAL GOAL, not merely the current plan.

2. Use actual execution results only.

3. Never invent discovered paths.

4. Never invent stdout or stderr.

5. Never invent browser URLs.

6. Use exact registered tool signatures.

7. If history reveals a file path needed for the next action,
   use that real path.

8. If browser_search_web reveals result URLs needed for subsequent
   work, use those exact returned URLs.

9. If the user requested:
       debug until successful
       fix errors
       keep trying
       rerun until it works
       verify the result

   then keep working until evidence supports completion.

10. If the user requested research from multiple sources, continue
    until the requested source-reading requirement is supported by
    real history.

11. Never bypass permissions.

12. Do not add unnecessary steps.

13. Do not repeatedly rediscover information that is already present
    in structured tool output.

14. Return at most four next steps.

15. Preserve adaptive execution. Do not hard-code imaginary future
    facts.

16. If future decisions depend on reading the next source, returning:

        browser_navigate
        browser_read_page

    and then reconsidering afterward is appropriate.

17. If several unused real source URLs are already known and opening
    them does not depend on an intermediate result, multiple
    navigate/read steps may be returned up to the four-step limit.

18. If the original goal is already supported by real history:

        complete = true
        next_steps = []

19. If more work remains:

        complete = false
        next_steps = concrete actions
""".strip(),

            input=json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ),

            text_format=
                ContinuationDecision,
        )
    )


    return (
        response.output_parsed
    )


# ---------------------------------------------------------------------------
# Final Goal Verification
# ---------------------------------------------------------------------------

def verify_goal_completion(
    task: AgentTask,
):
    """
    Performs final strict verification of the original user goal.

    Important lifecycle rule:

        completion.summary becomes task.final_summary in runner.py.

        runner.py then places task.final_summary into AgentResult.message.

        format_agent_result() subsequently delivers that message to the
        user.

    Therefore the verifier must NOT require evidence that its own final
    natural-language response was already delivered before declaring
    the underlying task complete.
    """

    payload = {
        "goal":
            task.goal,

        "task_history":
            build_history(
                task
            ),
    }


    response = (
        client.responses.parse(
            model="gpt-5.5",

            instructions="""
You are E.V.I.E.'s final Phase 7 completion verifier AND final
task-summary generator.

Determine whether the ORIGINAL USER GOAL is actually complete.

Judge from REAL execution evidence.


CRITICAL ARCHITECTURE RULE

Your `summary` field becomes the final AgentResult message returned by
runner.py.

runner.py delivers that message to the user AFTER this verification.

Therefore:

DO NOT require evidence that the final natural-language summary has
already been delivered to the user.

That would create a circular requirement.

Instead:

1. verify whether all underlying requested work is complete

2. if the work is complete, generate the requested final user-facing
   answer in `summary`

3. set:

       complete = true

4. assign confidence based on the real evidence

The runner will deliver your summary afterward.


USE ONLY REAL EXECUTION EVIDENCE.

Useful evidence includes:

- exit codes
- stdout
- stderr
- filesystem results
- file contents
- Git output
- VS Code open results
- new_window metadata
- application focus results
- managed-browser state
- browser navigation results
- browser search results
- browser page titles
- browser URLs
- browser page text
- browser links
- other deterministic tool results


GENERAL RULES:

1. Never assume a planned action happened.

2. Never mark success merely because all currently planned steps
   finished.

3. Never invent missing evidence.

4. Judge whether the UNDERLYING WORK requested by the original user
   goal has been completed.

5. The final natural-language answer does NOT need to appear earlier
   in task history.

6. YOUR `summary` field is the final natural-language answer that
   runner.py will deliver.

7. If the underlying work is complete:

       complete = true

   and write the appropriate final response in:

       summary

8. If important underlying work is still missing:

       complete = false

   and describe what remains in:

       missing


PROGRAMMING TASKS:

9. For programming tasks:

       exit code 0 is evidence that the program executed successfully.

       expected stdout is evidence that the program produced the
       requested result.

10. For debugging tasks:

        the final successful run must occur AFTER the relevant
        correction.

11. If the user explicitly requested a new VS Code window:

        new_window=True

    in the actual VS Code tool result is sufficient evidence that the
    new-window launch was requested successfully.


PHASE 8 BROWSER EVIDENCE:

12. A successful browser_search_web result proves that a live search
    occurred and that its returned result URLs were observed.

13. Search results alone do NOT prove those sources were read.

14. Successful browser_navigate proves navigation to that page occurred.

15. Successful browser_read_page proves the page content was actually
    retrieved and available for reasoning.

16. If the user requested at least N sources, require evidence that at
    least N distinct relevant sources were actually read.

17. Do not count repeatedly reading a search-results page as multiple
    sources.

18. Do not count repeated reads of the same URL as independent sources
    unless the original user specifically requested revisiting it.

19. If the goal requires comparing sources, require evidence from
    multiple distinct relevant source reads.

20. Never treat model knowledge or remembered webpages as if they were
    retrieved in the current task.

21. Use actual URLs, titles, search results, and retrieved page text
    preserved in task history.


RESEARCH SUMMARY GENERATION:

22. When the evidence proves the requested research work is complete,
    synthesize the findings into `summary`.

23. The summary must answer the original research question rather than
    merely saying:

        "Research completed successfully."

24. Use actual retrieved source text from task history.

25. Compare the sources when comparison was requested.

26. Explain meaningful agreement, differences, and complementary
    information when supported by the evidence.

27. Do not invent claims absent from retrieved evidence.

28. Do not claim that a source was read unless task history contains
    successful browser-read evidence for it.

29. Keep the answer concise when the user requested a concise summary.

30. Include useful source names or URLs when they are supported by the
    real task history.

31. If the user requested research but did NOT ask to modify anything,
    the absence of file mutations is normal and does not make the task
    incomplete.


EXAMPLE

Original goal:

    Research Playwright's current Python browser automation
    capabilities.

    Search the web, open and read at least three useful sources,
    compare navigation, page interaction, and locators, and give me
    a concise research summary.

History proves:

    browser_search_web succeeded

    source 1:
        browser_navigate succeeded
        browser_read_page succeeded

    source 2:
        browser_navigate succeeded
        browser_read_page succeeded

    source 3:
        browser_navigate succeeded
        browser_read_page succeeded


CORRECT:

    complete = true

    confidence = high

    summary = a concise synthesis of what the three retrieved sources
              say about navigation, interaction, and locators


INCORRECT:

    complete = false

    reason:
        "The research summary has not already been delivered."


Why incorrect:

YOUR summary is what runner.py delivers after this verification.


FINAL DECISION

If all required real-world actions and evidence gathering are complete,
mark the task complete and generate the requested final answer.

Only mark the task incomplete when an underlying action, evidence,
source count, verification requirement, or requested real-world
operation is actually missing.
""".strip(),

            input=json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ),

            text_format=
                CompletionDecision,
        )
    )


    return (
        response.output_parsed
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Agent Verifier"
    )

    print(
        "------------------------"
    )


    print()


    print(
        "Phase 7 deterministic verification test:"
    )


    sample = {
        "success":
            False,

        "executed":
            True,

        "tool":
            "run_python",

        "risk":
            "low",

        "result": {
            "exit_code":
                1,

            "stdout":
                "",

            "stderr":
                (
                    "SyntaxError: "
                    "expected ':'"
                ),

            "timed_out":
                False,
        },
    }


    print(
        verify_step_result(
            sample
        )
    )


    print()


    print(
        "Phase 8 browser result preservation test:"
    )


    browser_sample = {
        "success":
            True,

        "executed":
            True,

        "tool":
            "browser_search_web",

        "risk":
            "low",

        "result": {
            "query":
                (
                    "Playwright Python "
                    "browser automation"
                ),

            "provider":
                "bing",

            "search_url":
                (
                    "https://www.bing.com/"
                    "search?q=Playwright"
                ),

            "results": [
                {
                    "title":
                        (
                            "Playwright Python "
                            "Official Documentation"
                        ),

                    "url":
                        (
                            "https://"
                            "playwright.dev/python/"
                        ),
                },

                {
                    "title":
                        (
                            "Getting started - "
                            "Library"
                        ),

                    "url":
                        (
                            "https://playwright.dev/"
                            "python/docs/library"
                        ),
                },
            ],
        },
    }


    print(
        json.dumps(
            extract_execution_details(
                browser_sample
            ),
            indent=2,
            ensure_ascii=False,
        )
    )