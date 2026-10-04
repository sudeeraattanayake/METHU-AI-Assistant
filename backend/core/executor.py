from typing import Any

from backend.core.planner import ExecutionPlan
from backend.agents.computer_agent import computer_agent_node
from backend.agents.browser_agent import browser_agent_node


AGENT_EXECUTORS = {
    "computer": computer_agent_node,
    "browser": browser_agent_node,
}


def execute_plan(plan: ExecutionPlan, session_id: str = "default") -> dict[str, Any]:
    """
    Execute a METHU plan sequentially.

    Stops immediately if a step fails.
    """

    results = []

    for step in plan.steps:
        agent_function = AGENT_EXECUTORS.get(step.agent)

        # Agent isn't executable yet
        if agent_function is None:
            return {
                "success": False,
                "status": "failed",
                "failed_step": step.step_id,
                "error": f"Agent '{step.agent}' is not connected to the executor yet.",
                "results": results,
            }

        step_state = {
            "user_input": step.instruction,
            "session_id": session_id,
            "status": "executing",
            "current_step": step.step_id,
            "selected_agent": step.agent,
        }

        try:
            result = agent_function(step_state)

        except Exception as exc:
            return {
                "success": False,
                "status": "failed",
                "failed_step": step.step_id,
                "error": str(exc),
                "results": results,
            }

        step_result = {
            "step_id": step.step_id,
            "agent": step.agent,
            "instruction": step.instruction,
            "status": result.get("status"),
            "response": result.get("final_response"),
            "tool_name": result.get("tool_name"),
            "tool_result": result.get("tool_result"),
            "ui_event": result.get("ui_event"),
            "ui_payload": result.get("ui_payload", {}),
        }

        results.append(step_result)

        # Stop the plan if this step didn't complete.
        if result.get("status") != "completed":
            return {
                "success": False,
                "status": "failed",
                "failed_step": step.step_id,
                "results": results,
            }

    return {
        "success": True,
        "status": "completed",
        "goal": plan.goal,
        "completed_steps": len(results),
        "results": results,
    }
