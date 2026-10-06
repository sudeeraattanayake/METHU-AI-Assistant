from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.core.llm import llm


# ============================================================
# Plan Models
# ============================================================


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


# ============================================================
# Structured Planner
# ============================================================


planner_llm = llm.with_structured_output(ExecutionPlan)


# ============================================================
# Normal Planning
# ============================================================


def create_plan(user_input: str) -> ExecutionPlan:
    """
    Create the initial structured execution plan for a
    user's request.
    """

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
- interact with supported websites
- search supported websites

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

6. Use only the available agents.

7. Keep the plan minimal and executable.


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


# ============================================================
# Recovery Planning
# ============================================================


def create_recovery_plan(
    original_goal: str,
    failed_step: dict[str, Any] | None,
    failure_evidence: dict[str, Any],
) -> ExecutionPlan:
    """
    Create a corrected execution plan after normal retries
    have failed.

    The recovery planner receives:

    - the original user goal
    - the failed plan step
    - verification / observation evidence

    It should change strategy when the previous strategy
    clearly failed rather than blindly repeating it.
    """

    failed_step = failed_step or {}

    recovery_context = {
        "original_goal": original_goal,
        "failed_step": failed_step,
        "failure_evidence": failure_evidence,
    }

    return planner_llm.invoke(
        [
            (
                "system",
                """
You are the recovery planning system inside METHU.

A previous execution plan failed independent verification
even after normal retries.

Your job is to create a corrected recovery plan.

You will receive:

1. The user's original goal.
2. The step that failed.
3. Evidence explaining what happened.


Available agents:

computer:
- open approved desktop applications

browser:
- navigate to websites
- interact with supported websites
- search supported websites

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


Recovery rules:

1. Preserve the user's original goal.

2. Study the failure evidence before creating the new plan.

3. Do not blindly repeat the exact same failed strategy when
   the evidence shows that strategy did not work.

4. Prefer a different valid strategy when one is available.

5. Do not invent tools, agents, UI elements, applications,
   websites, or capabilities.

6. Use only capabilities available to METHU.

7. Each step must contain exactly one clear executable action.

8. Keep the recovery plan as small as possible.

9. Do not claim an action succeeded. You are only creating
   a plan.

10. Do not bypass permissions, security checks, approvals,
    or verification.

11. If the browser state may have changed, the recovery plan
    may first navigate to a known safe page before attempting
    the browser action again.

12. If the failed step depends on a desktop application that
    may not be running, the recovery plan may first reopen
    that approved application.

13. Do not create endless recovery loops.

14. The returned step IDs must start at 1 and increase
    sequentially.

15. Return only actions necessary to recover and finish the
    original goal.


Example:

Original goal:
Search YouTube for Python tutorials

Failed step:
Search YouTube for Python tutorials

Evidence:
The expected search result page could not be verified.

A reasonable recovery strategy could be:

1. browser
   Navigate to YouTube

2. browser
   Search YouTube for "Python tutorials"

This changes the recovery context by first restoring the
browser to a known page before attempting the failed action
again.

Never invent unsupported actions merely to make the plan
look different.
""",
            ),
            (
                "human",
                (
                    "Create a recovery plan for the following "
                    "failed METHU task.\n\n"
                    f"Original goal:\n{original_goal}\n\n"
                    f"Failed step:\n{failed_step}\n\n"
                    "Failure evidence:\n"
                    f"{failure_evidence}\n\n"
                    "Create the smallest safe corrected plan."
                ),
            ),
        ]
    )
