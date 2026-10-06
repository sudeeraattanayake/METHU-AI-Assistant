from typing import Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm
from backend.core.state import MethuState

from backend.tools.browser.navigation import normalize_url
from backend.tools.browser.playwright_controller import (
    navigate_managed_browser,
)
from backend.tools.browser.browser_actions import (
    type_into_element,
    click_element,
)
from backend.tools.browser.browser_verifier import (
    verify_search_goal,
)


class BrowserAction(BaseModel):
    action: Literal[
        "navigate",
        "search",
        "unknown",
    ] = Field(
        description="Browser action to perform."
    )

    target: str | None = Field(
        default=None,
        description=(
            "Website name or complete HTTP/HTTPS URL. "
            "Examples: youtube, google, github, linkedin."
        ),
    )

    query: str | None = Field(
        default=None,
        description=(
            "The search query when action='search'. "
            "Example: LangGraph tutorials."
        ),
    )

    explanation: str = Field(
        description="Short explanation of what the user wants."
    )


browser_llm = llm.with_structured_output(BrowserAction)


def _failed(
    message: str,
    *,
    tool_name: str | None = None,
    tool_input: dict | None = None,
    tool_result: dict | None = None,
) -> dict:
    result = {
        "status": "failed",
        "final_response": message,
        "error": message,
        "ui_event": "methu_error",
        "ui_payload": tool_result or {
            "message": message,
        },
    }

    if tool_name:
        result["tool_name"] = tool_name

    if tool_input is not None:
        result["tool_input"] = tool_input

    if tool_result is not None:
        result["tool_result"] = tool_result

    return result


def _navigate(target: str) -> dict:
    url = normalize_url(target)

    if not url:
        return _failed(
            (
                "I couldn't open that website because "
                "the target is invalid or unsupported."
            ),
            tool_name="open_website",
            tool_input={
                "target": target,
            },
            tool_result={
                "success": False,
                "action": "open_website",
                "target": target,
                "error": "Invalid or unsupported website.",
            },
        )

    result = navigate_managed_browser(url)

    if not result.get("success"):
        return _failed(
            (
                "I couldn't navigate the METHU browser. "
                f"{result.get('message', 'Unknown error')}"
            ),
            tool_name="open_website",
            tool_input={
                "target": target,
                "url": url,
            },
            tool_result=result,
        )

    tool_result = {
        "success": True,
        "action": "open_website",
        "url": url,
        "observed_url": result.get("url"),
        "observed_title": result.get("title"),
        "page_count": result.get("page_count"),
        "message": result.get("message"),
    }

    return {
        "status": "completed",
        "final_response": (
            "I navigated the METHU browser to "
            f"{tool_result['observed_url']}."
        ),
        "tool_name": "open_website",
        "tool_input": {
            "target": target,
            "url": url,
        },
        "tool_result": tool_result,
        "ui_event": "browser_action_completed",
        "ui_payload": {
            "action": "navigate",
            "url": tool_result["observed_url"],
            "title": tool_result["observed_title"],
        },
    }


def _search(target: str, query: str) -> dict:
    """
    Perform a verified browser search.

    Current prototype supports YouTube search.

    Flow:
        Navigate
        -> Find textbox
        -> Type
        -> Verify typed value
        -> Find Search button
        -> Click
        -> Observe
        -> Verify final search goal
    """

    url = normalize_url(target)

    if not url:
        return _failed(
            f'Could not resolve browser target "{target}".'
        )

    # -----------------------------------------------
    # 1. Navigate to target
    # -----------------------------------------------

    navigation_result = navigate_managed_browser(url)

    if not navigation_result.get("success"):
        return _failed(
            (
                f'Could not navigate to "{target}". '
                f"{navigation_result.get('message', '')}"
            ),
            tool_name="browser_search",
            tool_input={
                "target": target,
                "query": query,
            },
            tool_result=navigation_result,
        )

    # -----------------------------------------------
    # 2. Type into search textbox
    # -----------------------------------------------

    type_result = type_into_element(
        element_query="search textbox",
        text=query,
    )

    if not type_result.get("success"):
        return _failed(
            (
                "I reached the website, but I couldn't "
                "type into the search box. "
                f"{type_result.get('message', '')}"
            ),
            tool_name="browser_search",
            tool_input={
                "target": target,
                "query": query,
            },
            tool_result={
                "stage": "type",
                "result": type_result,
            },
        )

    if not type_result.get("verified"):
        return _failed(
            "Text was entered, but METHU could not verify it.",
            tool_name="browser_search",
            tool_input={
                "target": target,
                "query": query,
            },
            tool_result={
                "stage": "type_verification",
                "result": type_result,
            },
        )

    # -----------------------------------------------
    # 3. Click Search button
    # -----------------------------------------------

    click_result = click_element(
        element_query="search button",
    )

    if not click_result.get("success"):
        return _failed(
            (
                "The search text was entered, but I "
                "couldn't click the Search button. "
                f"{click_result.get('message', '')}"
            ),
            tool_name="browser_search",
            tool_input={
                "target": target,
                "query": query,
            },
            tool_result={
                "stage": "click",
                "result": click_result,
            },
        )

    # -----------------------------------------------
    # 4. Verify actual search goal
    # -----------------------------------------------

    verification = verify_search_goal(query)

    if not verification.get("verified"):
        return _failed(
            (
                "The browser interaction completed, "
                "but METHU could not verify that the "
                "requested search actually happened."
            ),
            tool_name="browser_search",
            tool_input={
                "target": target,
                "query": query,
            },
            tool_result={
                "stage": "goal_verification",
                "navigation": navigation_result,
                "typing": type_result,
                "click": click_result,
                "verification": verification,
            },
        )

    # -----------------------------------------------
    # 5. Verified success
    # -----------------------------------------------

    tool_result = {
        "success": True,
        "verified": True,
        "action": "browser_search",
        "target": target,
        "query": query,
        "navigation": {
            "url": navigation_result.get("url"),
            "title": navigation_result.get("title"),
        },
        "typing": {
            "verified": type_result.get("verified"),
            "locator": type_result.get("locator"),
            "observed_value": type_result.get(
                "observed_value"
            ),
        },
        "click": {
            "verified": click_result.get("verified"),
            "locator": click_result.get("locator"),
            "before": click_result.get("before"),
            "after": click_result.get("after"),
        },
        "verification": verification,
    }

    observed = verification.get(
        "observed",
        {},
    )

    return {
        "status": "completed",
        "final_response": (
            f'I searched {target} for "{query}" '
            "and verified the result."
        ),
        "tool_name": "browser_search",
        "tool_input": {
            "target": target,
            "query": query,
        },
        "tool_result": tool_result,
        "verified": True,
        "verification_message": (
            f'Search goal verified for "{query}".'
        ),
        "ui_event": "browser_search_completed",
        "ui_payload": {
            "action": "search",
            "target": target,
            "query": query,
            "verified": True,
            "url": observed.get("actual_url"),
            "title": observed.get("actual_title"),
        },
    }


def browser_agent_node(state: MethuState) -> dict:
    user_input = state.get(
        "user_input",
        "",
    ).strip()

    if not user_input:
        return {
            "status": "failed",
            "error": "No browser request was provided.",
        }

    decision = browser_llm.invoke(
        [
            (
                "system",
                """
You are the Browser Agent inside METHU.

You currently support:

1. navigate
2. search

Use navigate when the user only wants to open or visit
a website.

Examples:

User:
"Go to YouTube"

action = navigate
target = youtube
query = null


User:
"Open GitHub"

action = navigate
target = github
query = null


Use search when the user wants to search for something
on a supported website.

Example:

User:
"Open YouTube and search for LangGraph tutorials"

action = search
target = youtube
query = LangGraph tutorials


User:
"Search YouTube for Python FastAPI tutorials"

action = search
target = youtube
query = Python FastAPI tutorials


IMPORTANT:

The current interactive search implementation is intended
for YouTube.

Do not invent unsupported browser capabilities.

If the request cannot be performed using navigate or the
currently supported search workflow, return:

action = unknown
""",
            ),
            (
                "human",
                user_input,
            ),
        ]
    )

    # -----------------------------------------------
    # Unknown
    # -----------------------------------------------

    if decision.action == "unknown":
        return {
            "status": "completed",
            "final_response": (
                "That browser action isn't supported yet."
            ),
            "ui_event": "browser_action_unsupported",
            "ui_payload": {
                "message": decision.explanation,
            },
        }

    # -----------------------------------------------
    # Navigate
    # -----------------------------------------------

    if decision.action == "navigate":
        if not decision.target:
            return _failed(
                "Browser Agent did not provide a target."
            )

        return _navigate(
            decision.target
        )

    # -----------------------------------------------
    # Search
    # -----------------------------------------------

    if decision.action == "search":
        if not decision.target:
            return _failed(
                "Browser Agent did not provide a search target."
            )

        if not decision.query:
            return _failed(
                "Browser Agent did not provide a search query."
            )

        return _search(
            target=decision.target,
            query=decision.query,
        )

    return {
        "status": "failed",
        "error": "Unsupported Browser Agent action.",
    }
