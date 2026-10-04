from typing import Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm


class PlanStep(BaseModel):
    step_id: int

    agent: Literal[
        "computer",
        "browser",
        "coding",
        "research",
        "news",
        "vision",
        "memory",
        "system",
    ]

    instruction: str = Field(
        description="One clear action for this specialist agent."
    )


class ExecutionPlan(BaseModel):
    goal: str = Field(
        description="The overall goal requested by the user."
    )

    steps: list[PlanStep] = Field(
        default_factory=list,
        description="Ordered actions required to complete the goal.",
    )


planner_llm = llm.with_structured_output(ExecutionPlan)


def create_plan(user_input: str) -> ExecutionPlan:

    return planner_llm.invoke(
        [
            (
                "system",
                """
You are the planning system inside METHU.

Break a user's request into the smallest useful sequence of
specialist-agent actions.

Available agents:

computer:
- open approved desktop applications

browser:
- navigate to websites

news:
- retrieve current news

research:
- research information

coding:
- software-development tasks

vision:
- image/screen understanding

memory:
- memory operations

system:
- computer/system information


Rules:

1. Preserve execution order.

2. Each step should contain one clear action.

3. Do not invent capabilities.

4. Do not add unnecessary steps.

5. Opening an application and navigating somewhere are separate
actions when both are explicitly needed.

Example:

User:
"Methu, open Chrome and go to YouTube"

Plan:

1. computer
   "Open Google Chrome"

2. browser
   "Navigate to YouTube"

For a simple request such as:

"Methu, open Notepad"

create only one step.

For:

"Methu, show me the latest AI news"

create only one news step.
""",
            ),
            (
                "human",
                user_input,
            ),
        ]
    )
