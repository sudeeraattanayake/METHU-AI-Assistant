from typing import Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm
from backend.core.state import MethuState
from backend.tools.browser.navigation import normalize_url
from backend.tools.browser.playwright_controller import (
    navigate_managed_browser,
)


class BrowserAction(BaseModel):
    action: Literal["navigate", "unknown"] = Field(
        description="Browser action to perform."
    )

    target: str | None = Field(
        default=None,
        description=(
            "Website name or complete HTTP/HTTPS URL. "
            "Examples: youtube, google, github, linkedin."
        ),
    )

    explanation: str = Field(
        description="Short explanation of what the user wants."
    )


browser_llm = llm.with_structured_output(BrowserAction)


def browser_agent_node(state: MethuState) -> dict:
    user_input = state.get("user_input", "").strip()

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

You currently support safe website navigation.

Supported action:
- navigate

Examples:

"Go to YouTube"
action = navigate
target = youtube

"Open GitHub"
action = navigate
target = github

"Go to https://www.google.com"
action = navigate
target = https://www.google.com

Do not invent browser capabilities.

If the requested browser operation is not currently supported,
return action="unknown".
""",
            ),
            ("human", user_input),
        ]
    )

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

    if decision.action == "navigate":
        if not decision.target:
            return {
                "status": "failed",
                "error": (
                    "Browser Agent did not provide a target."
                ),
            }

        url = normalize_url(decision.target)

        if not url:
            return {
                "status": "failed",
                "final_response": (
                    "I couldn't open that website because "
                    "the target is invalid or unsupported."
                ),
                "tool_name": "open_website",
                "tool_input": {
                    "target": decision.target,
                },
                "tool_result": {
                    "success": False,
                    "action": "open_website",
                    "target": decision.target,
                    "error": (
                        "Invalid or unsupported website."
                    ),
                },
                "ui_event": "methu_error",
                "ui_payload": {
                    "target": decision.target,
                },
            }

        result = navigate_managed_browser(url)

        if not result.get("success"):
            return {
                "status": "failed",
                "final_response": (
                    "I couldn't navigate the METHU browser. "
                    f"{result.get('message', 'Unknown error')}"
                ),
                "tool_name": "open_website",
                "tool_input": {
                    "target": decision.target,
                    "url": url,
                },
                "tool_result": result,
                "ui_event": "methu_error",
                "ui_payload": result,
            }

        # Standardize the result for the verifier.
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
                f"I navigated the METHU browser to "
                f"{tool_result['observed_url']}."
            ),
            "tool_name": "open_website",
            "tool_input": {
                "target": decision.target,
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

    return {
        "status": "failed",
        "error": "Unsupported Browser Agent action.",
    }
