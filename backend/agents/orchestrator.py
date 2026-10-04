from typing import Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm
from backend.core.prompts import METHU_SYSTEM_PROMPT
from backend.core.state import MethuState


class OrchestratorDecision(BaseModel):
    intent: str = Field(
        description="Short description of what the user wants."
    )

    language: str = Field(
        description="Primary language used by the user."
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
    ]

    plan: list[str] = Field(
        default_factory=list,
        description="Concise steps required to complete the request."
    )

    requires_approval: bool = Field(
        description="Whether execution should wait for explicit user approval."
    )

    risk_level: Literal[
        "low",
        "medium",
        "high",
    ]


orchestrator_llm = llm.with_structured_output(OrchestratorDecision)


def orchestrator_node(state: MethuState) -> dict:
    user_input = state.get("user_input", "").strip()

    if not user_input:
        return {
            "status": "failed",
            "error": "No user input was provided.",
        }

    decision = orchestrator_llm.invoke(
        [
            ("system", METHU_SYSTEM_PROMPT),
            ("human", user_input),
        ]
    )

    return {
        "intent": decision.intent,
        "language": decision.language,
        "selected_agent": decision.selected_agent,
        "plan": decision.plan,
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

        # Tell the future holographic UI what METHU is doing.
        "ui_event": "methu_planning",
        "ui_payload": {
            "agent": decision.selected_agent,
            "intent": decision.intent,
        },
    }
