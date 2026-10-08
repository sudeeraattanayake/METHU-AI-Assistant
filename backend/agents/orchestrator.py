
from typing import Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm
from backend.core.prompts import METHU_SYSTEM_PROMPT
from backend.core.state import MethuState


class OrchestratorDecision(BaseModel):
    intent: str = Field(
        description="Short description of the user's request."
    )

    language: str = Field(
        description="Primary language of the request."
    )

    selected_agent: Literal[
        "orchestrator",
        "computer",
        "coding",
        "browser",
        "research",
        "news",
        "vision",
        "memory",
        "system",
    ] = Field(
        description="The best specialist agent for the request."
    )

    requires_planning: bool = Field(
        description=(
            "True when the task requires multiple dependent "
            "actions or coordination between agents. "
            "False for a single straightforward action."
        )
    )

    requires_approval: bool = Field(
        description=(
            "True when the request may involve an action "
            "requiring explicit user approval."
        )
    )

    risk_level: Literal[
        "low",
        "medium",
        "high",
    ] = Field(
        description="Estimated risk level of the request."
    )


orchestrator_llm = llm.with_structured_output(
    OrchestratorDecision
)


def orchestrator_node(state: MethuState) -> dict:
    user_input = state.get("user_input", "").strip()

    if not user_input:
        return {
            "status": "failed",
            "error": "No user input was provided.",
        }

    decision = orchestrator_llm.invoke(
        [
            (
                "system",
                METHU_SYSTEM_PROMPT
                + """

You are METHU's Orchestrator.

Your responsibilities:
1. Understand the user's request.
2. Identify the primary language.
3. Select the appropriate specialist agent.
4. Decide whether structured planning is required.
5. Identify potential risks and approval requirements.

Do not generate execution steps.

Set requires_planning=True when:
- Multiple dependent actions are required.
- Multiple agents must coordinate.
- The user requests a multi-stage browser workflow.
- The user requests a multi-stage computer workflow.

Set requires_planning=False when:
- The user is having a simple conversation.
- Only one application needs to be opened.
- Only one website needs to be opened.
- A single straightforward specialist action is needed.

The dedicated Planner generates structured execution plans.

Your risk assessment does not authorize actions.
The security layer must independently enforce permissions.
"""
            ),
            ("human", user_input),
        ]
    )

    return {
        "intent": decision.intent,
        "language": decision.language,
        "selected_agent": decision.selected_agent,

        "requires_planning": decision.requires_planning,

        # Keep legacy field empty for compatibility.
        "plan": [],

        "current_step": 0,

        "requires_approval": decision.requires_approval,
        "approval_granted": None,
        "risk_level": decision.risk_level,

        "status": (
            "waiting_approval"
            if decision.requires_approval
            else "planning"
        ),

        "retry_count": 0,
        "error": None,

        "ui_event": "methu_planning",
        "ui_payload": {
            "agent": decision.selected_agent,
            "intent": decision.intent,
            "requires_planning": decision.requires_planning,
        },
    }
