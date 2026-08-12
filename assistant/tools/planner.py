"""
E.V.I.E. - Single Tool Planner

Created: August 9, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Converts simple natural-language computer requests into one
    controlled Phase 6 tool action.

Capabilities:
    - single-action tool planning
    - exact registered tool signatures
    - active-workspace grounding
    - recent-conversation referent grounding
    - Phase 8 managed-browser routing
    - live browser-state routing
    - live web-search routing
    - follow-up references such as "it", "that", and "the one you found"
    - compatibility with existing brain.py tool-routing logic
    - lazy OpenAI client initialization
    - safe argument parsing
    - no direct execution

Important:
    This planner handles ONE immediate computer action only.

    Multi-step, adaptive, iterative, debugging, research, and
    retry-until-success requests belong to Phase 7.

Most Recent Change:
    Added Phase 8 managed-browser intent detection and routing so
    browser state, page reading, and live web-search requests use
    real browser tools instead of stale conversational context.
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

from assistant.intelligence.integration_runtime import (
    prepare_integration_arguments,
)

from assistant.intelligence.context import (
    format_planner_conversation_context,
    looks_like_contextual_followup,
)

from assistant.intelligence.resolver import (
    resolve_contextual_request,
)

from assistant.intelligence.normalize import (
    normalize_user_input,
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
    Creates the planner client only when planning is actually needed.

    This prevents module import from failing solely because credentials
    are unavailable during startup/import.
    """

    return OpenAI()


# ---------------------------------------------------------------------------
# Structured Planner Output
# ---------------------------------------------------------------------------

class ToolPlan(BaseModel):
    """
    Structured result returned by the Phase 6 tool planner.

    arguments_json:
        Raw JSON string generated through structured model output.

    arguments:
        Compatibility property expected by brain.py.
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
        Returns arguments_json as a Python dictionary.

        Maintains compatibility with existing brain.py code that uses:

            plan.arguments
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
research-oriented, or asks E.V.I.E. to continue working based on future
results:

    use_tool = false

Those requests belong to Phase 7.


GENERAL RULES

1. Use ONLY registered tools.

2. Never invent tool names.

3. Use exact parameter names from the registered Python signatures.

4. Never claim that a tool executed.

5. Never invent file paths.

6. Never invent URLs.

7. Never invent application names.

8. Never invent workspace paths.

9. Prefer dedicated tools over run_command.

10. Plan no more than ONE computer action.

11. Do not turn ordinary questions into tool actions.

12. Preserve specific objects and destinations mentioned in recent
    conversation.

13. Never replace a specific previously identified object with a more
    generic destination.

14. If a conversational reference is ambiguous, do not guess.

15. Live tool state is stronger evidence than stale conversational
    assumptions.

16. Questions asking about current managed-browser state should use
    browser inspection tools rather than being answered from memory.

17. Questions asking E.V.I.E. to search the live web should use the
    managed browser search tool.

18. Requests involving multiple dependent browser actions belong to
    Phase 7.

PHASE 10 SHORT-TERM CONTEXT

You may receive ACTIVE PHASE 10 SHORT-TERM CONTEXT.

This contains structured context from the most recent successfully
verified tool action.

It may contain:

    last_provider
    last_capability
    last_account_id
    last_arguments
    active_document
    active_section
    active_repo
    active_location
    active_symbol

Use this context ONLY when the current message is clearly a follow-up.

Examples:

Earlier successful action:
    weather.current
    location = Honolulu

Current:
    What about tomorrow?

Interpret as:
    integration_execute

    capability = weather.forecast
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {
        "location": "Honolulu",
        "days": 2
    }


Earlier successful action:
    notion.read_document
    page_title = E.V.I.E. Assistant

Current:
    What about Phase 9?

Interpret as:
    integration_execute

    capability = notion.read_document
    provider = notion
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "page_title": "E.V.I.E. Assistant",
        "section": "Phase 9"
    }


Earlier successful action:
    github.commits
    repo = E.V.-Assistant

Current:
    What about the open issues?

Interpret as:
    integration_execute

    capability = github.issues
    provider = github
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "repo": "E.V.-Assistant"
    }


RULES

1. The CURRENT user message always has priority.

2. Inherit only arguments that remain logically relevant.

3. Explicit new arguments replace inherited arguments.

4. Never inherit approval state.

5. Never inherit destructive intent.

6. Never invent an entity when short-term context does not contain one.

7. Never use stale short-term context for an unrelated new request.

8. Short-term context does not change capability permissions.

9. If the reference is ambiguous, do not guess.

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
    "Read it."
    "Click that."

Use RECENT CONVERSATION CONTEXT to resolve these references.

The most recent relevant explicit object has priority.


YOUTUBE EXAMPLE

Earlier:

User:
    Hacksmith on YouTube

E.V.I.E.:
    Opened YouTube search results for Hacksmith.

Current user:
    Open it.

If the recent conversation contains the specific URL that was opened,
preserve that exact URL.

Do not replace a specific prior destination with:

    https://www.youtube.com


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


APPLICATION EXAMPLE

Earlier:

E.V.I.E.:
    Chrome is currently open.

Current user:
    Focus it.

Correct:

    focus_application(
        name="chrome"
    )


AMBIGUITY

Use recent context only when the reference is reasonably clear.

If multiple equally plausible referents exist:

    use_tool = false

Do not guess.


URL RULES

If recent conversation contains a specific HTTP or HTTPS URL and the
user clearly refers to it:

    preserve the exact specific URL.

Do NOT simplify a specific page/channel/video into a generic domain.


WORKSPACE RULES

For tools supporting workspace_path:

- use an explicitly named workspace when available
- otherwise use the current active workspace
- never invent a workspace


TERSE NAVIGATION REQUESTS

Users may omit verbs in natural speech.

A phrase combining a subject with a destination may still represent
navigation intent.

Examples:

    "Hacksmith on YouTube"
    "OpenAI on GitHub"
    "Python docs in browser"

For a subject plus YouTube request without a known exact destination,
opening a YouTube search URL is acceptable.

Example:

User:
    Hacksmith on YouTube

Correct:

    open_url(
        url="https://www.youtube.com/results?search_query=Hacksmith"
    )

Do not invent a specific channel or video URL unless that exact URL
already exists in recent context.


PHASE 8 MANAGED BROWSER ROUTING

E.V.I.E. has a dedicated Playwright-managed Chromium browser.

The managed browser is separate from the user's normal Chrome window.

Questions about the managed browser are computer-tool requests.


BROWSER STATE

User:
    "What browser tabs do you have open?"

Use:

    browser_get_state


User:
    "Show me my browser tabs."

Use:

    browser_get_state


User:
    "What is the active browser tab?"

Use:

    browser_get_state


User:
    "What page is open in the managed browser?"

Use:

    browser_get_state


Do NOT answer these from conversation history if browser_get_state can
retrieve the real current state.


PAGE READING

User:
    "Read the current webpage."

Use:

    browser_read_page


User:
    "Tell me what this webpage contains."

Use:

    browser_read_page


User:
    "What does the current page say?"

Use:

    browser_read_page


User:
    "Summarize this browser page."

Use:

    browser_read_page


PAGE STRUCTURE

User:
    "What links and buttons are on this page?"

Use:

    browser_get_page_context


User:
    "What inputs are on this page?"

Use:

    browser_get_page_context


User:
    "Inspect the current webpage."

Use:

    browser_get_page_context


WEB SEARCH

User:
    "Search the web for Playwright Python."

Use:

    browser_search_web


User:
    "Search online for FPGA acceleration."

Use:

    browser_search_web


User:
    "Look up current browser automation libraries online."

Use:

    browser_search_web


For a single search request, use browser_search_web.

Do not merely provide a remembered URL when the user explicitly asks
for a live web search.


NEW TAB

User:
    "Open Python.org in a new browser tab."

Use:

    browser_new_tab


If a URL can be confidently resolved from the current message or recent
context, pass it through the url argument.


NAVIGATION

User:
    "Go to Python.org in the managed browser."

Use:

    browser_navigate


User:
    "Navigate this browser to Playwright.dev."

Use:

    browser_navigate


If the request clearly concerns the managed browser, prefer
browser_navigate over legacy open_url.


HISTORY

User:
    "Go back."

When recent context clearly concerns the managed browser:

    browser_back


User:
    "Go forward."

Use:

    browser_forward


User:
    "Reload this page."

Use:

    browser_reload


User:
    "Refresh this page."

Use:

    browser_reload


TAB CONTROL

User:
    "Close this browser tab."

Use:

    browser_close_tab


User:
    "Switch to tab 2."

Use:

    browser_activate_tab


SCROLLING

User:
    "Scroll down."

When recent context clearly concerns the managed browser:

    browser_scroll


User:
    "Scroll up."

Use:

    browser_scroll


CLICKING

User:
    "Click the Downloads link."

If this is ONE immediate browser interaction, use the most appropriate
registered click tool.

Possible tools:

    browser_click_text
    browser_click_role

These tools may require approval because clicking can trigger page
actions.


FORM INPUT

User:
    "Type hello into the Search field."

If this is ONE immediate browser interaction, use the appropriate
registered fill tool.

Possible tools:

    browser_fill_label
    browser_fill_placeholder

These are medium-risk and may require approval.


KEYBOARD

User:
    "Press Enter."

When recent context clearly concerns the managed browser:

    browser_press


LIVE BROWSER STATE PRIORITY

Current managed-browser state should be retrieved with browser tools.

Example:

User:
    "What browser tabs do you have open?"

Incorrect:
    infer tabs from recent assistant messages

Correct:
    browser_get_state


Example:

User:
    "What does the current webpage contain?"

Incorrect:
    infer it from the Windows active-window title

Correct:
    browser_read_page


Example:

User:
    "Search the web for Playwright Python browser automation."

Incorrect:
    provide remembered links without performing a search

Correct:
    browser_search_web


MULTI-STEP BROWSER REQUESTS

Requests involving multiple dependent browser operations belong to
Phase 7.

Examples:

    "Start the browser and open Python.org."

    "Search for Playwright, open the first useful result, and summarize it."

    "Search the web, open three sources, compare them, and tell me what
    you learned."

    "Research FPGA acceleration and keep searching until you understand
    the major approaches."

    "Open Python.org, click Downloads, then tell me what page loaded."

For these:

    use_tool = false

Phase 7 should generate and execute the multi-step plan.


DEEP RESEARCH

Deep research belongs to Phase 7.

Phase 6 provides primitives such as:

    browser_search_web
    browser_get_state
    browser_read_page
    browser_get_page_context
    browser_navigate
    browser_new_tab
    browser_activate_tab

Phase 7 can combine them into:

    search
    inspect
    select source
    open source
    read source
    search follow-up question
    open another source
    read another source
    compare
    synthesize

Do not try to compress a multi-source research task into one Phase 6
tool call.


PHASE 9 CONNECTED-SERVICE ROUTING

Connected-service questions are real tool requests.

Use integration_execute whenever the user asks for live data or an
action from a connected service.

Examples:

User:
    What Google tasks do I have?

Use:
    integration_execute

Arguments:
    capability = tasks.read
    provider = google


User:
    What's on my Google Calendar?

Use:
    integration_execute

Arguments:
    capability = calendar.read
    provider = google


User:
    Search my Gmail for paperwork.

Use:
    integration_execute

Arguments:
    capability = email.search
    provider = google


User:
    What am I listening to on Spotify?

Use:
    integration_execute

Arguments:
    capability = media.read
    provider = spotify


User:
    Create a Google task called Finish report.

Use:
    integration_execute

Arguments:
    capability = tasks.create
    provider = google
    arguments = {"title": "Finish report"}

SCHWAB / FINANCE ROUTING

E.V.I.E. has live read-only Charles Schwab access.

User:
    What stocks do I own?

Use:
    integration_execute

Arguments:
    capability = finance.positions
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    What are my holdings?

Use:
    integration_execute

Arguments:
    capability = finance.positions
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    Show me my portfolio.

Use:
    integration_execute

Arguments:
    capability = finance.positions
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    What's my Schwab balance?

Use:
    integration_execute

Arguments:
    capability = finance.balances
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    Show my Schwab accounts.

Use:
    integration_execute

Arguments:
    capability = finance.accounts
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    What is NVDA trading at?

Use:
    integration_execute

Arguments:
    capability = market.quote
    provider = schwab
    account_id = primary
    routing_mode = explicit_account
    arguments = {"symbol": "NVDA"}


User:
    What's Tesla trading at?

Use:
    integration_execute

Arguments:
    capability = market.quote
    provider = schwab
    account_id = primary
    routing_mode = explicit_account
    arguments = {"symbol": "TSLA"}


User:
    Get quotes for NVDA and AAPL.

Use:
    integration_execute

Arguments:
    capability = market.quotes
    provider = schwab
    account_id = primary
    routing_mode = explicit_account
    arguments = {"symbols": ["NVDA", "AAPL"]}


User:
    Show my recent Schwab transactions.

Use:
    integration_execute

Arguments:
    capability = finance.transactions
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    Show my Schwab orders.

Use:
    integration_execute

Arguments:
    capability = finance.orders
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


PORTFOLIO PERFORMANCE

User:
    How much is my portfolio up today?

Use:
    integration_execute

Arguments:
    capability = finance.performance
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    How much am I up today?

When recent context clearly concerns the connected Schwab portfolio, use:
    integration_execute

Arguments:
    capability = finance.performance
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    What's my portfolio's day gain?

Use:
    integration_execute

Arguments:
    capability = finance.performance
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


User:
    How is my portfolio doing today?

Use:
    integration_execute

Arguments:
    capability = finance.performance
    provider = schwab
    account_id = primary
    routing_mode = explicit_account


FINANCIAL ROUTING RULES

1. Questions about what stocks, securities, shares, positions, holdings,
   investments, or assets the user owns should use:

       finance.positions

2. Questions about brokerage balances, cash, buying power, or account
   value should use:

       finance.balances

3. Questions about brokerage accounts should use:

       finance.accounts

4. Questions about recent brokerage activity or trades should use:

       finance.transactions

5. Questions about existing or open brokerage orders should use:

       finance.orders

6. Questions about the current market price, share price, live quote,
   or what a stock/company is "trading at" should use:

       market.quote

   If the user gives a well-known, unambiguous company name instead of a
   ticker, convert it to the correct ticker symbol.

   Examples:
       Tesla -> TSLA
       Apple -> AAPL
       Nvidia -> NVDA
       Amazon -> AMZN

   If the company name is ambiguous, do not guess.

7. Questions about current prices for multiple tickers should use:

       market.quotes

8. Historical price requests should use:

       market.history

9. Questions about live portfolio performance, including today's gain/loss,
   day gain, daily return, or "how much am I up today", should use:

       finance.performance

10. The current Schwab integration is READ ONLY.

11. NEVER invent, plan, or imply support for:
        finance.trade
        orders.create
        orders.replace
        orders.cancel

12. When the request clearly refers to the connected Schwab brokerage
    account, use:
        provider = schwab
        account_id = primary
        routing_mode = explicit_account

13. Never answer current portfolio, balance, position, transaction,
    order, performance, or market-state questions from conversational memory
    when integration_execute can retrieve live data.

GITHUB ROUTING

E.V.I.E. has a connected read-only GitHub integration.

Provider:
    github

Account:
    primary

Routing:
    explicit_account


IMPORTANT CAPABILITY NAMES

Use ONLY these registered GitHub capabilities:

    github.profile
    github.repos
    github.repo
    github.commits
    github.issues
    github.pulls
    github.notifications
    github.workflows
    github.actions

NEVER invent aliases such as:

    repos.read
    repo.read
    commits.read
    issues.read
    pulls.read
    actions.read
    github.read
    github.repositories


User:
    What GitHub repositories do I have?

Use:
    integration_execute

Arguments:
    capability = github.repos
    provider = github
    account_id = primary
    routing_mode = explicit_account


User:
    Show me my GitHub profile.

Use:
    integration_execute

Arguments:
    capability = github.profile
    provider = github
    account_id = primary
    routing_mode = explicit_account


User:
    What were my latest commits to E.V.-Assistant?

Use:
    integration_execute

Arguments:
    capability = github.commits
    provider = github
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "repo": "E.V.-Assistant"
    }


User:
    Are there any open issues on E.V.-Assistant?

Use:
    integration_execute

Arguments:
    capability = github.issues
    provider = github
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "repo": "E.V.-Assistant"
    }


User:
    Are there any open pull requests on E.V.-Assistant?

Use:
    integration_execute

Arguments:
    capability = github.pulls
    provider = github
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "repo": "E.V.-Assistant"
    }


User:
    Did any GitHub Actions run on E.V.-Assistant?

Use:
    integration_execute

Arguments:
    capability = github.actions
    provider = github
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "repo": "E.V.-Assistant"
    }


User:
    What workflows are configured on E.V.-Assistant?

Use:
    integration_execute

Arguments:
    capability = github.workflows
    provider = github
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "repo": "E.V.-Assistant"
    }


GITHUB ROUTING RULES

1. Repository listing uses:
       github.repos

2. One repository uses:
       github.repo

3. Commit history uses:
       github.commits

4. Issues use:
       github.issues

5. Pull requests use:
       github.pulls

6. Notifications use:
       github.notifications

7. Actions workflow runs use:
       github.actions

8. Workflow definitions use:
       github.workflows

9. Profile information uses:
       github.profile

10. GitHub read operations are low risk and do not require approval.

11. Always use:
       provider = github
       account_id = primary
       routing_mode = explicit_account

12. NEVER invent a GitHub capability name.

WEATHER ROUTING

E.V.I.E. has a public read-only weather provider.

Provider:
    weather

Account:
    public

Routing:
    explicit_account


User:
    What's the weather in Honolulu?

Use:
    integration_execute

Arguments:
    capability = weather.current
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {"location": "Honolulu"}


User:
    What is the current weather in Corvallis?

Use:
    integration_execute

Arguments:
    capability = weather.current
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {"location": "Corvallis"}


User:
    What's the forecast for Corvallis this week?

Use:
    integration_execute

Arguments:
    capability = weather.forecast
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {"location": "Corvallis", "days": 7}


User:
    What's the forecast for Honolulu for the next 3 days?

Use:
    integration_execute

Arguments:
    capability = weather.forecast
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {"location": "Honolulu", "days": 3}


User:
    What's the hourly forecast in Honolulu?

Use:
    integration_execute

Arguments:
    capability = weather.hourly
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {"location": "Honolulu"}


User:
    What's the hourly weather in Seattle?

Use:
    integration_execute

Arguments:
    capability = weather.hourly
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {"location": "Seattle"}


User:
    Will it rain in Seattle tomorrow?

Use:
    integration_execute

Arguments:
    capability = weather.forecast
    provider = weather
    account_id = public
    routing_mode = explicit_account
    arguments = {"location": "Seattle", "days": 2}


NOTION ROUTING

E.V.I.E. has a connected Notion integration.

Provider:
    notion

Account:
    primary

Routing:
    explicit_account


REGISTERED NOTION CAPABILITIES

Use ONLY:

    notion.search
    notion.page
    notion.page_content
    notion.block_children
    notion.data_source
    notion.data_source_query
    notion.read_document
    notion.document
    notion.block_update
    notion.block_delete


NEVER invent aliases such as:

    notion.read
    notion.write
    document.read
    document.write
    page.read
    page.write
    notes.read
    notes.write


User:
    Search my Notion for FPGA research

Use:
    integration_execute

Arguments:
    capability = notion.search
    provider = notion
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "query": "FPGA research"
    }


User:
    What did I write in my Documentation page?

Use:
    integration_execute

Arguments:
    capability = notion.read_document
    provider = notion
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "page_title": "Documentation"
    }


User:
    Read the Phase 9 section of my E.V.I.E. Assistant page.

Use:
    integration_execute

Arguments:
    capability = notion.read_document
    provider = notion
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "page_title": "E.V.I.E. Assistant",
        "section": "Phase 9"
    }


User:
    Document that GitHub integration passed under Phase 9 in my E.V.I.E. Assistant page.

Use:
    integration_execute

Arguments:
    capability = notion.document
    provider = notion
    account_id = primary
    routing_mode = explicit_account
    arguments = {
        "page_title": "E.V.I.E. Assistant",
        "section": "Phase 9",
        "content": "GitHub integration passed."
    }


NOTION ROUTING RULES

1. Search/finding pages by title or topic:
       notion.search

2. Read actual page content by page title:
       notion.read_document

3. Read a named subsection:
       notion.read_document
   with:
       page_title
       section

4. Append/document information:
       notion.document

5. Notion writes are medium risk and require approval.

6. Block deletion is high risk and requires approval.

7. Always use:
       provider = notion
       account_id = primary
       routing_mode = explicit_account

8. NEVER answer "what did I write" from notion.search metadata alone.
   Use notion.read_document when actual content is requested.

9. NEVER invent capability names.

WEATHER ROUTING RULES

1. Current conditions, current temperature, current humidity, current wind,
   or "what's the weather" should use:

       weather.current

2. Multi-day, daily, tomorrow, weekend, or "this week" forecast requests
   should use:

       weather.forecast

3. Hourly weather or hourly forecast requests MUST use:

       weather.hourly

4. Location-resolution-only requests may use:

       weather.location

5. NEVER pass invented arguments such as:

       type
       forecast_type
       mode

   The capability name determines whether the request is current,
   daily forecast, or hourly forecast.

6. weather.current accepts:
       location
       latitude
       longitude

7. weather.forecast accepts:
       location
       latitude
       longitude
       days

8. weather.hourly accepts:
       location
       latitude
       longitude
       days

9. When the user gives a location name, preserve it in:
       arguments.location

10. For "tomorrow", request enough forecast days to include tomorrow.
    Normally use days = 2.

11. For "this week", normally use days = 7.

12. Weather is public and read-only. It never requires approval.

13. Do not answer live/current/future weather from conversational memory
    when integration_execute can retrieve fresh data.

14. Do not guess the user's physical location for requests such as
    "weather near me" unless an approved location source is available.

RULES FOR CONNECTED SERVICES

1. Never answer a live connected-service state question from
   conversation history when integration_execute can retrieve it.

2. Do not claim an integration is unavailable merely because the
   information is absent from conversation history.

3. For integration_execute, NEVER provide or infer the approved
   argument. Approval state belongs exclusively to E.V.I.E.'s executor.

4. Do not invent an account_id when the user did not specify an account.

5. If the user explicitly names an account or email address, preserve
   that exact account_id.

6. Use normalized lowercase provider identifiers such as:
       google
       spotify
       github
       notion
       discord
       weather

7. For read capabilities, approval is not required unless the registered
   permission policy says otherwise.

8. If multiple accounts are available and the user did not select one,
   leave account_id unset. The integration routing layer will resolve or
   request account selection.

9. A connected-service read such as tasks.read, calendar.read,
   email.search, contacts.search, media.read, finance.read, or weather
   retrieval is an immediate Phase 6 tool action when it requires only
   one integration call.

10. Multi-step connected-service workflows that depend on intermediate
    results belong to Phase 7.


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
    Open YouTube.

Result:
    use_tool = true
    tool_name = open_url


User:
    Open assistant/main.py in VS Code.

Result:
    use_tool = true
    tool_name = open_file_in_vscode


User:
    What browser tabs do you have open?

Result:
    use_tool = true
    tool_name = browser_get_state


User:
    Read the current webpage.

Result:
    use_tool = true
    tool_name = browser_read_page


User:
    Search the web for Playwright Python browser automation.

Result:
    use_tool = true
    tool_name = browser_search_web


NO TOOL EXAMPLE

User:
    What's 2 + 2?

Result:
    use_tool = false


PROJECT KNOWLEDGE QUESTIONS

Do NOT use computer tools merely because a question concerns code or a
project.

Examples that normally remain normal reasoning / project knowledge:

    "Where is memory retrieval implemented?"
    "What does the memory system do?"
    "Where is the Phase 7 planner?"
    "Explain E.V.I.E.'s vision architecture."

Explicitly requesting a real file inspection may use read_file.

Example:

    "Read assistant/tools/terminal.py and explain it."


PHASE 7 EXAMPLE

User:
    Run the tests and fix whatever fails.

Result:
    use_tool = false


ANOTHER PHASE 7 EXAMPLE

User:
    Create a Python script, run it, fix any errors, and keep trying
    until it works.

Result:
    use_tool = false


BROWSER PHASE 7 EXAMPLE

User:
    Search the web for Playwright Python browser automation, open the
    first useful result, read it, and summarize what it says.

Result:
    use_tool = false
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
    """
    Returns all registered Phase 6 tool names.
    """

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
    """
    Returns current Phase 3 workspace context when available.
    """

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
    """
    Retrieves the first useful value from a conversation record.
    """

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
# Tuple Conversation Fallback
# ---------------------------------------------------------------------------

def extract_tuple_conversation(
    conversation,
):
    """
    Best-effort extraction for tuple/list conversation records.
    """

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


    values = []


    for item in conversation:

        if isinstance(
            item,
            str,
        ):

            values.append(
                item
            )


    if len(values) >= 2:

        return (
            values[-2],
            values[-1],
        )


    if len(values) == 1:

        return (
            values[0],
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
    """
    Retrieves recent persisted conversation context for immediate
    referent resolution.

    This is not a replacement for long-term semantic memory.
    """

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
    Fast compatibility gate used by brain.py.

    This function does NOT choose a tool.

    It determines whether a message plausibly requests inspection or
    control of the real computer/browser environment OR live access to
    a Phase 9 connected service.

    The semantic planner makes the final tool decision.
    """

    if not user_message:

        return False


    normalized_message = (
        normalize_user_input(
            str(
                user_message
            )
        )
    )


    text = (
        normalized_message
        .strip()
        .lower()
    )


    if not text:

        return False

    # -----------------------------------------------------------------------
    # Phase 10B Contextual Follow-Up
    # -----------------------------------------------------------------------

    if looks_like_contextual_followup(
        normalized_message
    ):

        return True

    # -----------------------------------------------------------------------
    # Conversational Follow-Up Actions
    # -----------------------------------------------------------------------

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
        "read it",
        "read that",
        "read this",
        "click it",
        "click that",
        "click this",
        "search it",
        "search that",
        "scroll it",
        "refresh it",
        "reload it",
    )


    if any(
        phrase in text
        for phrase
        in referent_actions
    ):

        return True


    # -----------------------------------------------------------------------
    # Phase 8 Browser State / Intelligence
    # -----------------------------------------------------------------------

    browser_state_terms = (
        "browser",
        "managed browser",
        "browser tab",
        "browser tabs",
        "tabs open",
        "tab open",
        "current tab",
        "active tab",
        "active browser tab",
        "webpage",
        "web page",
        "current webpage",
        "current web page",
        "current page",
        "page content",
        "page contents",
        "read the webpage",
        "read webpage",
        "read the web page",
        "read web page",
        "read the page",
        "read page",
        "read this page",
        "read current page",
        "read the current page",
        "read the current webpage",
        "what is on this page",
        "what's on this page",
        "what is on the page",
        "what's on the page",
        "what does this page say",
        "what does the current page say",
        "what does the webpage say",
        "what does the web page say",
        "tell me what this page contains",
        "tell me what the webpage contains",
        "tell me what the web page contains",
        "links on this page",
        "buttons on this page",
        "inputs on this page",
        "inspect this page",
        "inspect the page",
    )


    if any(
        term in text
        for term
        in browser_state_terms
    ):

        return True


    # -----------------------------------------------------------------------
    # Phase 8 Web Search
    # -----------------------------------------------------------------------

    web_search_terms = (
        "search the web",
        "search web",
        "web search",
        "search online",
        "look up online",
        "look it up online",
        "find online",
        "research online",
        "search bing",
        "search google",
        "search duckduckgo",
        "search the internet",
        "search internet",
    )


    if any(
        term in text
        for term
        in web_search_terms
    ):

        return True


    # -----------------------------------------------------------------------
    # Phase 8 Browser Navigation / Interaction
    # -----------------------------------------------------------------------

    browser_action_terms = (
        "new browser tab",
        "new tab",
        "open tab",
        "close tab",
        "switch tab",
        "activate tab",
        "go back",
        "go forward",
        "reload",
        "refresh",
        "scroll down",
        "scroll up",
        "click ",
        "fill ",
        "type into",
        "enter into",
        "press enter",
        "navigate to",
    )


    if any(
        term in text
        for term
        in browser_action_terms
    ):

        return True


    # -----------------------------------------------------------------------
    # Phase 9 Connected Services
    # -----------------------------------------------------------------------
    #
    # This gate does not choose integration_execute itself. It only makes
    # sure live connected-service questions reach the semantic tool planner.
    # -----------------------------------------------------------------------

    integration_service_terms = (
        # Google / communication
        "gmail",
        "email",
        "emails",
        "mailbox",
        "inbox",

        # Calendar
        "calendar",
        "calendars",
        "event",
        "events",
        "schedule",
        "scheduled",

        # Tasks
        "google task",
        "google tasks",
        "task",
        "tasks",
        "to-do",
        "todo",

        # Contacts
        "contact",
        "contacts",

        # Spotify / media
        "spotify",
        "playing",
        "currently playing",
        "listening to",
        "playback",
        "spotify devices",

        # Finance / Schwab
        "portfolio",
        "positions",
        "position",
        "holdings",
        "holding",
        "schwab",
        "brokerage",
        "investment",
        "investments",
        "stock",
        "stocks",
        "shares",
        "shares of",
        "own",
        "owned",
        "balance",
        "balances",
        "cash balance",
        "buying power",
        "account value",
        "portfolio value",
        "net liquidation",
        "portfolio performance",
        "performance",
        "day gain",
        "day gain/loss",
        "daily gain",
        "daily return",
        "today's gain",
        "todays gain",
        "up today",
        "down today",
        "gain today",
        "loss today",
        "transactions",
        "transaction",
        "trades",
        "trade history",
        "orders",
        "open orders",
        "market price",
        "stock price",
        "share price",
        "current price",
        "live price",
        "live quote",
        "market quote",
        "trading at",
        "price of",
        "quote",
        "ticker",

        # Weather
        "weather",
        "forecast",
        "weather forecast",
        "hourly forecast",
        "hourly weather",
        "temperature",
        "humidity",
        "wind",
        "rain",
        "raining",
        "precipitation",

        # GitHub
        "github",
        "repository",
        "repositories",
        "repo",
        "repos",
        "commit",
        "commits",
        "issue",
        "issues",
        "pull request",
        "pull requests",
        "pulls",
        "github actions",
        "actions",
        "workflow",
        "workflows",
        "notifications",

        # Notion
        "notion",
        "notion page",
        "notion pages",
        "notion database",
        "notion data source",
        "notion notes",
        "notion document",
        "notion documents",
        "documentation",
        "document",
        "document this",
        "write this",
        "add this",
        "page",
        "section",

        # Phase 9 providers / future connected services
        "discord",
    )


    integration_query_terms = (
        "what ",
        "what's ",
        "whats ",
        "which ",
        "who ",
        "when ",
        "where ",
        "show ",
        "show me ",
        "list ",
        "read ",
        "search ",
        "find ",
        "check ",
        "get ",
        "tell me ",
        "do i have",
        "do we have",
        "how many ",
        "how much ",
        "how did ",
        "how is ",
        "will ",
        "is it ",
        "are we ",
    )


    integration_action_terms = (
        "create ",
        "add ",
        "send ",
        "complete ",
        "mark ",
        "schedule ",
        "play ",
        "pause ",
        "resume ",
        "skip ",
        "next ",
        "previous ",
    )


    mentions_integration = any(
        term in text
        for term
        in integration_service_terms
    )


    asks_integration_query = any(
        term in text
        for term
        in integration_query_terms
    )


    asks_integration_action = any(
        term in text
        for term
        in integration_action_terms
    )


    if (
        mentions_integration
        and (
            asks_integration_query
            or asks_integration_action
        )
    ):

        return True


    # -----------------------------------------------------------------------
    # Existing General Computer Actions
    # -----------------------------------------------------------------------

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
                # Phase 9 contextual media controls
        "skip ",
        "skip the song",
        "skip this song",
        "next song",
        "next track",
        "pause ",
        "pause the song",
        "pause music",
        "resume ",
        "resume music",
        "unpause ",
        "go back",
        "previous song",
        "previous track",
        "play ",
        "queue ",
        "add to queue",
        "shuffle ",
        "repeat ",
        "volume ",
        "turn it up",
        "turn it down",
    )


    if any(
        term in text
        for term
        in action_terms
    ):

        return True


    return False


# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------

def parse_arguments(
    arguments_json: str,
):
    """
    Safely converts structured planner JSON into a dictionary.
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
    """
    Injects the active workspace only when:

        - the target tool accepts workspace_path
        - the planner did not already provide one
    """

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
# Build Planner Prompt
# ---------------------------------------------------------------------------

def build_planner_prompt(
    user_message: str,
):
    """
    Builds the Phase 6 planner prompt.
    """

    recent_context = (
        get_reference_context()
    )

    phase10_context = (
        format_planner_conversation_context()
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
        + "ACTIVE PHASE 10 SHORT-TERM CONTEXT:\n\n"
        + phase10_context
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
    """
    Converts a simple user request into at most one Phase 6 tool action.

    Returns:
        ToolPlan
    """

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


    # -----------------------------------------------------------------------
    # Phase 10D - Normalize User Input
    # -----------------------------------------------------------------------

    normalized_user_message = (
        normalize_user_input(
            user_message
        )
    )


    prompt = build_planner_prompt(
        normalized_user_message
    )


    try:

        planner_client = (
            get_openai_client()
        )


        response = (
            planner_client.responses.parse(
                model=
                    "gpt-5.5",

                instructions=(
                    "Plan at most one immediate "
                    "controlled computer action. "
                    "Resolve clear conversational "
                    "references from recent context. "
                    "Prefer live browser inspection "
                    "tools for current managed-browser "
                    "state. Use only registered tool "
                    "signatures."
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


    # -----------------------------------------------------------------------
    # No Tool Needed
    # -----------------------------------------------------------------------

    if not plan.use_tool:

        return plan


    # -----------------------------------------------------------------------
    # Validate Tool Name
    # -----------------------------------------------------------------------

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


    # -----------------------------------------------------------------------
    # Parse Arguments
    # -----------------------------------------------------------------------

    arguments = (
        parse_arguments(
            plan.arguments_json
        )
    )

    # -----------------------------------------------------------------------
    # Phase 10C - Contextual Reference Resolution
    # -----------------------------------------------------------------------

    if (
        tool_name
        == "integration_execute"
        and looks_like_contextual_followup(
            normalized_user_message
        )
    ):

        resolved = (
            resolve_contextual_request(
                normalized_user_message
            )
        )


        if resolved is not None:

            # For a clearly contextual follow-up, the deterministic
            # resolver is authoritative.
            #
            # It begins from the last successfully verified tool state
            # and applies only explicit changes found in the current
            # follow-up request.
            #
            # Do not allow independently generated planner arguments
            # to overwrite inherited entities such as the active
            # Notion page, GitHub repository, location, or symbol.

            arguments = resolved

    # -----------------------------------------------------------------------
    # Phase 10A / 10E - Prepare Integration Arguments
    # -----------------------------------------------------------------------

    if (
        tool_name
        == "integration_execute"
    ):

        arguments = (
            prepare_integration_arguments(
                arguments
            )
        )
        
    # -----------------------------------------------------------------------
    # Inject Workspace
    # -----------------------------------------------------------------------

    arguments = inject_workspace(
        tool_name,
        arguments,
    )


    # -----------------------------------------------------------------------
    # Final Result
    # -----------------------------------------------------------------------

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
    """
    Compatibility alias used by earlier Phase 6 integrations.
    """

    return plan_tool_request(
        user_message
    )


def plan_tool(
    user_message: str,
):
    """
    Compatibility alias used by earlier Phase 6 integrations.
    """

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


    gate_tests = (
        "What browser tabs do you have open?",
        "What stocks do I own?",
        "How much is my portfolio up today?",
        "What's the weather in Honolulu?",
        "What's the forecast for Corvallis this week?",
        "What's the hourly forecast in Honolulu?",
        (
            "Read the current webpage and "
            "tell me what it contains."
        ),
        (
            "Search the web for Playwright "
            "Python browser automation."
        ),
        "What is 2 + 2?",
    )


    print(
        "Tool consideration tests:"
    )


    for message in gate_tests:

        print(
            (
                f"{message!r} -> "
                f"{should_consider_tools(message)}"
            )
        )


    print()


    compatibility = ToolPlan(
        use_tool=True,
        tool_name="browser_get_state",
        arguments_json="{}",
        confidence=100,
    )


    print(
        "ToolPlan compatibility:"
    )


    print(
        "arguments_json:",
        compatibility.arguments_json,
    )


    print(
        "arguments:",
        compatibility.arguments,
    )


    print()


    planner_tests = (
        "What's 2 + 2?",
        "Show me my Git status.",
        "What browser tabs do you have open?",
        "What stocks do I own?",
        "How much is my portfolio up today?",
        "What's the weather in Honolulu?",
        "What's the forecast for Corvallis this week?",
        "What's the hourly forecast in Honolulu?",
        "Read the current webpage.",
        (
            "Search the web for Playwright "
            "Python browser automation."
        ),
        (
            "Open assistant/memory/"
            "retriever.py in VS Code."
        ),
    )


    for message in planner_tests:

        print()

        print(
            "User:",
            message,
        )


        result = (
            plan_tool_request(
                message
            )
        )


        print(
            "Use tool:",
            result.use_tool,
        )


        print(
            "Tool:",
            result.tool_name,
        )


        print(
            "Arguments:",
            result.arguments,
        )


        print(
            "Confidence:",
            result.confidence,
        )


        print(
            "Summary:",
            result.summary,
        )