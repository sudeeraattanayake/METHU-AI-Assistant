from typing import Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm
from backend.core.state import MethuState
from backend.tools.computer.app_control import open_app


class ComputerAction(BaseModel):
    action: Literal["open_app", "unknown"] = Field(
        description="Computer action that should be performed."
    )

    app_name: str | None = Field(
        default=None,
        description=(
            "Normalized application name. "
            "Use chrome, vscode, notepad, calculator, or explorer."
        ),
    )

    explanation: str = Field(
        description="Short explanation of the requested action."
    )


computer_llm = llm.with_structured_output(ComputerAction)


def computer_agent_node(state: MethuState) -> dict:
    user_input = state.get("user_input", "").strip()

    if not user_input:
        return {
            "status": "failed",
            "error": "No computer-control request was provided.",
        }

    decision = computer_llm.invoke(
        [
            (
                "system",
                """
You are the Computer Agent inside METHU.

Your job is to translate the user's request into a safe computer action.

Currently supported action:

open_app

Currently supported applications:

chrome
vscode
notepad
calculator
explorer

Normalization examples:

Google Chrome -> chrome
Chrome -> chrome

Visual Studio Code -> vscode
VS Code -> vscode
Code -> vscode

Notepad -> notepad

Calculator -> calculator

File Explorer -> explorer
Windows Explorer -> explorer

If the user requests something that isn't currently supported,
return action="unknown".

Never pretend an action succeeded.
Only select actions actually supported by the Computer Agent.
""",
            ),
            (
                "human",
                user_input,
            ),
        ]
    )

    # ----------------------------------------
    # Unsupported request
    # ----------------------------------------

    if decision.action == "unknown":
        return {
            "status": "completed",
            "final_response": (
                "That computer action isn't supported yet."
            ),
            "tool_name": None,
            "tool_result": None,
            "ui_event": "computer_action_unsupported",
            "ui_payload": {
                "message": decision.explanation,
            },
        }

    # ----------------------------------------
    # Open application
    # ----------------------------------------

    if decision.action == "open_app":
        if not decision.app_name:
            return {
                "status": "failed",
                "error": "Computer Agent did not provide an application name.",
            }

        result = open_app(decision.app_name)

        if not result["success"]:
            return {
                "status": "failed",
                "final_response": (
                    f"I couldn't open {decision.app_name}. "
                    f"{result.get('error', 'Unknown error')}"
                ),
                "tool_name": "open_app",
                "tool_input": {
                    "app": decision.app_name,
                },
                "tool_result": result,
                "ui_event": "methu_error",
                "ui_payload": result,
            }

        return {
            "status": "completed",
            "final_response": f"I opened {decision.app_name}.",
            "tool_name": "open_app",
            "tool_input": {
                "app": decision.app_name,
            },
            "tool_result": result,
            "verified": True,
            "verification_message": (
                f"{decision.app_name} launch command completed."
            ),
            "ui_event": "computer_action_completed",
            "ui_payload": {
                "action": "open_app",
                "app": decision.app_name,
                "message": f"Opened {decision.app_name}",
            },
        }

    return {
        "status": "failed",
        "error": "Unsupported Computer Agent action.",
    }
