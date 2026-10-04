from typing import Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm
from backend.core.state import MethuState
from backend.tools.browser.navigation import navigate_to


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
            "final_response": "That browser action isn't supported yet.",
            "ui_event": "browser_action_unsupported",
            "ui_payload": {
                "message": decision.explanation,
            },
        }

    if decision.action == "navigate":
        if not decision.target:
            return {
                "status": "failed",
                "error": "Browser Agent did not provide a target.",
            }

        result = navigate_to(decision.target)

        if not result["success"]:
            return {
                "status": "failed",
                "final_response": (
                    "I couldn't open that website. "
                    f"{result.get('error', 'Unknown error')}"
                ),
                "tool_name": "open_website",
                "tool_input": {
                    "target": decision.target,
                },
                "tool_result": result,
                "ui_event": "methu_error",
                "ui_payload": result,
            }

        return {
            "status": "completed",
            "final_response": f"I opened {result['url']}.",
            "tool_name": "open_website",
            "tool_input": {
                "target": decision.target,
            },
            "tool_result": result,
            "ui_event": "browser_action_completed",
            "ui_payload": {
                "action": "navigate",
                "url": result["url"],
            },
        }

    return {
        "status": "failed",
        "error": "Unsupported Browser Agent action.",
    }
