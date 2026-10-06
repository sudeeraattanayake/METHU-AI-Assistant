from langgraph.graph import StateGraph, START, END

from backend.core.state import MethuState
from backend.core.planner import create_plan
from backend.core.verifier import verify_tool_result

from backend.agents.orchestrator import orchestrator_node
from backend.agents.news_agent import news_agent_node
from backend.agents.computer_agent import computer_agent_node
from backend.agents.browser_agent import browser_agent_node


# ============================================================
# Recovery Configuration
# ============================================================

DEFAULT_MAX_RETRIES = 2


# ============================================================
# Temporary Specialist Agents
# ============================================================


def coding_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Coding Agent selected.",
        "ui_event": "coding_agent_active",
        "ui_payload": {
            "agent": "coding",
        },
    }


def research_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Research Agent selected.",
        "ui_event": "research_agent_active",
        "ui_payload": {
            "agent": "research",
        },
    }


def vision_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Vision Agent selected.",
        "ui_event": "vision_agent_active",
        "ui_payload": {
            "agent": "vision",
        },
    }


def memory_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Memory Agent selected.",
        "ui_event": "memory_agent_active",
        "ui_payload": {
            "agent": "memory",
        },
    }


def system_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "System Agent selected.",
        "ui_event": "system_agent_active",
        "ui_payload": {
            "agent": "system",
        },
    }


def conversation_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": (
            "METHU Orchestrator selected for conversation."
        ),
        "ui_event": "methu_speaking",
        "ui_payload": {
            "agent": "orchestrator",
        },
    }


# ============================================================
# Planning Node
# ============================================================


def planning_node(state: MethuState) -> dict:
    """
    Create one authoritative structured execution plan.
    """

    user_input = state.get("user_input", "").strip()

    if not user_input:
        return {
            "status": "failed",
            "error": "No request was provided.",
            "structured_plan": [],
            "execution_results": [],
            "current_step": 0,
            "retry_count": 0,
            "max_retries": DEFAULT_MAX_RETRIES,
            "retry_reason": None,
            "replan_count": 0,
        }

    try:
        plan = create_plan(user_input)

        if not plan.steps:
            return {
                "status": "failed",
                "error": "Planner produced no executable steps.",
                "structured_plan": [],
                "execution_results": [],
                "current_step": 0,
                "retry_count": 0,
                "max_retries": DEFAULT_MAX_RETRIES,
                "retry_reason": None,
                "replan_count": 0,
            }

        structured_plan = [
            step.model_dump()
            for step in plan.steps
        ]

        return {
            "status": "planning",
            "structured_plan": structured_plan,
            "execution_results": [],
            "current_step": 0,
            "current_plan_step": None,

            # Recovery state
            "retry_count": 0,
            "max_retries": state.get(
                "max_retries",
                DEFAULT_MAX_RETRIES,
            ),
            "retry_reason": None,
            "replan_count": state.get(
                "replan_count",
                0,
            ),

            # Verification state
            "verified": False,
            "verification_message": "",

            "error": None,

            "ui_event": "methu_plan_created",
            "ui_payload": {
                "goal": plan.goal,
                "steps": structured_plan,
                "max_retries": state.get(
                    "max_retries",
                    DEFAULT_MAX_RETRIES,
                ),
            },
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "structured_plan": [],
            "execution_results": [],
            "current_step": 0,
            "retry_count": 0,
            "max_retries": DEFAULT_MAX_RETRIES,
            "retry_reason": None,
            "verified": False,
            "ui_event": "methu_error",
            "ui_payload": {
                "error": str(exc),
            },
        }


# ============================================================
# Load Current Step
# ============================================================


def load_step_node(state: MethuState) -> dict:
    """
    Load the next structured plan step.

    During a retry, current_step is moved back to the failed
    step before this node is entered.
    """

    plan = state.get("structured_plan", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(plan):
        return {
            "current_plan_step": None,
        }

    step = plan[current_step]

    return {
        "current_plan_step": step,
        "selected_agent": step["agent"],
        "status": "executing",
        "verified": False,
        "verification_message": "",
        "error": None,

        "ui_event": (
            "methu_step_retry_started"
            if state.get("retry_count", 0) > 0
            else "methu_step_started"
        ),

        "ui_payload": {
            "step_id": step["step_id"],
            "agent": step["agent"],
            "instruction": step["instruction"],
            "retry_count": state.get(
                "retry_count",
                0,
            ),
            "max_retries": state.get(
                "max_retries",
                DEFAULT_MAX_RETRIES,
            ),
        },
    }


# ============================================================
# Execute ONE Step
# ============================================================


def execute_step_node(state: MethuState) -> dict:
    """
    Execute exactly one structured plan step.

    LangGraph controls the execution loop.
    """

    step = state.get("current_plan_step")

    if not step:
        return {
            "status": "failed",
            "error": "No current plan step was loaded.",
        }

    agent = step.get("agent")
    instruction = step.get("instruction", "")

    session_id = state.get(
        "session_id",
        "default",
    )

    # Only these agents currently have real multi-step
    # execution support.
    executors = {
        "computer": computer_agent_node,
        "browser": browser_agent_node,
    }

    executor = executors.get(agent)

    if executor is None:
        return {
            "status": "failed",
            "error": (
                f"Agent '{agent}' is not connected "
                "to multi-step execution yet."
            ),
        }

    step_state = {
        "user_input": instruction,
        "session_id": session_id,
        "status": "executing",
        "current_step": step["step_id"],
        "selected_agent": agent,
    }

    try:
        result = executor(step_state)

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }

    execution_results = list(
        state.get(
            "execution_results",
            [],
        )
    )

    step_result = {
        "step_id": step["step_id"],
        "agent": agent,
        "instruction": instruction,
        "status": result.get("status"),
        "response": result.get("final_response"),
        "tool_name": result.get("tool_name"),
        "tool_result": result.get("tool_result"),
        "ui_event": result.get("ui_event"),
        "ui_payload": result.get(
            "ui_payload",
            {},
        ),

        # Track which execution attempt produced this result.
        "attempt": state.get(
            "retry_count",
            0,
        ) + 1,

        # Verification happens in the next graph node.
        "verified": False,
        "verification": None,
    }

    execution_results.append(step_result)

    # --------------------------------------------------------
    # Execution failed before verification
    # --------------------------------------------------------

    if result.get("status") != "completed":
        return {
            "status": "failed",
            "execution_results": execution_results,
            "error": (
                result.get("error")
                or f"Step {step['step_id']} failed."
            ),
            "verified": False,
            "verification_message": (
                "Execution failed before verification."
            ),
            "retry_reason": (
                result.get("error")
                or "Execution failed before verification."
            ),
            "ui_event": "methu_step_failed",
            "ui_payload": {
                "step": step,
                "result": step_result,
            },
        }

    # --------------------------------------------------------
    # Execution succeeded
    # --------------------------------------------------------

    completed_count = (
        state.get("current_step", 0) + 1
    )

    return {
        "status": "executing",
        "current_step": completed_count,
        "execution_results": execution_results,

        # Store the most recent tool information so the
        # verifier can independently inspect the result.
        "tool_name": result.get("tool_name"),
        "tool_input": result.get(
            "tool_input",
            {},
        ),
        "tool_result": result.get("tool_result"),

        "verified": False,
        "verification_message": (
            "Execution succeeded. Waiting for "
            "independent verification."
        ),

        "ui_event": "methu_step_completed",
        "ui_payload": {
            "step_id": step["step_id"],
            "agent": agent,
            "instruction": instruction,
            "attempt": state.get(
                "retry_count",
                0,
            ) + 1,
            "result": step_result,
        },

        "error": None,
    }


# ============================================================
# Verify ONE Step
# ============================================================


def verify_step_node(state: MethuState) -> dict:
    """
    Independently verify the most recently executed step.

    Supported verification is delegated to
    backend.core.verifier.verify_tool_result().
    """

    tool_name = state.get("tool_name")
    tool_result = state.get("tool_result")

    try:
        verification = verify_tool_result(
            tool_name=tool_name,
            tool_result=tool_result,
        )

    except Exception as exc:
        verification = {
            "verified": False,
            "method": "verification_error",
            "message": str(exc),
        }

    verified = verification.get(
        "verified",
        False,
    )

    execution_results = list(
        state.get(
            "execution_results",
            [],
        )
    )

    # --------------------------------------------------------
    # Attach verification evidence to latest attempt
    # --------------------------------------------------------

    if execution_results:
        latest_result = execution_results[-1]

        execution_results[-1] = {
            **latest_result,
            "verified": verified,
            "verification": verification,
        }

    # --------------------------------------------------------
    # Verification succeeded
    # --------------------------------------------------------

    if verified:
        return {
            "status": "verifying",
            "verified": True,
            "verification_message": verification.get(
                "message",
                "",
            ),
            "execution_results": execution_results,

            # Successful step resets per-step retry state.
            "retry_count": 0,
            "retry_reason": None,

            "ui_event": "methu_step_verified",

            "ui_payload": {
                "verified": True,
                "verification": verification,
            },
        }

    # --------------------------------------------------------
    # Verification failed
    # --------------------------------------------------------

    failure_reason = verification.get(
        "message",
        "Step could not be independently verified.",
    )

    return {
        "status": "verifying",
        "verified": False,
        "verification_message": failure_reason,
        "execution_results": execution_results,

        "retry_reason": failure_reason,

        "ui_event": "methu_step_unverified",

        "ui_payload": {
            "verified": False,
            "verification": verification,
            "retry_count": state.get(
                "retry_count",
                0,
            ),
            "max_retries": state.get(
                "max_retries",
                DEFAULT_MAX_RETRIES,
            ),
        },
    }


# ============================================================
# Retry Failed Step
# ============================================================


def retry_step_node(state: MethuState) -> dict:
    """
    Prepare the most recently failed verification step
    for another execution attempt.

    execute_step_node increments current_step before
    verification, therefore retry must move the pointer
    back by one.

    The failed attempt is removed from execution_results
    before retrying so final task verification represents
    the final result of each plan step rather than counting
    obsolete failed attempts as completed steps.
    """

    current_step = state.get(
        "current_step",
        0,
    )

    retry_count = state.get(
        "retry_count",
        0,
    )

    max_retries = state.get(
        "max_retries",
        DEFAULT_MAX_RETRIES,
    )

    retry_reason = state.get(
        "retry_reason",
        "Verification failed.",
    )

    # Move back to the failed step.
    failed_step_index = max(
        current_step - 1,
        0,
    )

    plan = state.get(
        "structured_plan",
        [],
    )

    failed_step = None

    if failed_step_index < len(plan):
        failed_step = plan[failed_step_index]

    # Remove the failed attempt from final step results.
    # We keep the retry information in state/UI for now.
    execution_results = list(
        state.get(
            "execution_results",
            [],
        )
    )

    if execution_results:
        execution_results.pop()

    new_retry_count = retry_count + 1

    return {
        "status": "observing",

        # Point back to the failed plan step.
        "current_step": failed_step_index,
        "current_plan_step": None,

        "execution_results": execution_results,

        "retry_count": new_retry_count,
        "max_retries": max_retries,
        "retry_reason": retry_reason,

        "verified": False,

        "verification_message": (
            f"Verification failed. Retrying step "
            f"{failed_step_index + 1}. "
            f"Retry {new_retry_count}/{max_retries}."
        ),

        # Clear previous tool state so the next execution
        # produces fresh evidence.
        "tool_name": None,
        "tool_input": {},
        "tool_result": None,

        "error": None,

        "ui_event": "methu_step_retrying",

        "ui_payload": {
            "step": failed_step,
            "retry_count": new_retry_count,
            "max_retries": max_retries,
            "reason": retry_reason,
        },
    }


# ============================================================
# Complete Task
# ============================================================


def complete_task_node(state: MethuState) -> dict:
    """
    Finish execution after all plan steps have run.

    The whole task is verified only when every final
    individual step result has independent verification.
    """

    plan = state.get(
        "structured_plan",
        [],
    )

    results = state.get(
        "execution_results",
        [],
    )

    all_verified = (
        len(results) == len(plan)
        and len(results) > 0
        and all(
            result.get(
                "verified",
                False,
            )
            for result in results
        )
    )

    if all_verified:
        verification_message = (
            "All planned steps executed and were "
            "independently verified."
        )

        final_response = (
            f"I completed and verified all "
            f"{len(results)} planned steps."
        )

    else:
        verification_message = (
            "Task execution finished, but one or more "
            "planned steps could not be independently verified."
        )

        final_response = (
            f"I executed {len(results)} of {len(plan)} "
            "final planned step results, but I could not "
            "independently verify the entire task."
        )

    return {
        "status": "completed",
        "current_plan_step": None,

        "verified": all_verified,

        "verification_message": (
            verification_message
        ),

        "final_response": final_response,

        "retry_count": 0,
        "retry_reason": None,

        "ui_event": "multi_step_completed",

        "ui_payload": {
            "completed_steps": len(results),
            "total_steps": len(plan),
            "verified": all_verified,
            "results": results,
        },

        "error": None,
    }


# ============================================================
# Failed Task
# ============================================================


def failed_task_node(state: MethuState) -> dict:
    """
    Final failure node.

    This node is reached when execution fails or when a
    step remains unverified after the maximum retry limit.
    """

    error = state.get(
        "error",
        "Unknown execution error.",
    )

    retry_reason = state.get(
        "retry_reason",
    )

    if retry_reason and not error:
        error = retry_reason

    return {
        "status": "failed",
        "verified": False,

        "verification_message": (
            state.get(
                "verification_message",
                "Task execution failed.",
            )
        ),

        "final_response": (
            "I couldn't safely verify and complete "
            "the entire task."
        ),

        "ui_event": "methu_execution_failed",

        "ui_payload": {
            "error": error,
            "retry_reason": retry_reason,
            "retry_count": state.get(
                "retry_count",
                0,
            ),
            "max_retries": state.get(
                "max_retries",
                DEFAULT_MAX_RETRIES,
            ),
            "current_step": state.get(
                "current_step",
                0,
            ),
            "results": state.get(
                "execution_results",
                [],
            ),
        },
    }


# ============================================================
# Routing
# ============================================================


def route_after_orchestrator(
    state: MethuState,
) -> str:
    """
    Multi-action requests use the structured planner.

    Simple requests continue directly to their specialist
    agent for now.
    """

    initial_plan = state.get(
        "plan",
        [],
    )

    if len(initial_plan) > 1:
        return "planner"

    return state.get(
        "selected_agent",
        "orchestrator",
    )


def route_after_planning(
    state: MethuState,
) -> str:
    """
    Planner -> first execution step.
    """

    if state.get("status") == "failed":
        return "failed"

    if not state.get("structured_plan"):
        return "failed"

    return "load_step"


def route_after_execution(
    state: MethuState,
) -> str:
    """
    Successful execution always goes through verification.

    Execution failures currently terminate immediately.
    Recovery from verification failure is handled separately.
    """

    if state.get("status") == "failed":
        return "failed"

    return "verify"


def route_after_verification(
    state: MethuState,
) -> str:
    """
    Route based on independent verification.

    Verified:
        -> next step
        -> or complete

    Unverified:
        -> retry same step while retry budget remains
        -> fail after retry limit

    Replanning will be added after this retry layer is
    independently tested.
    """

    if state.get("status") == "failed":
        return "failed"

    verified = state.get(
        "verified",
        False,
    )

    plan = state.get(
        "structured_plan",
        [],
    )

    current_step = state.get(
        "current_step",
        0,
    )

    # --------------------------------------------------------
    # Verification succeeded
    # --------------------------------------------------------

    if verified:
        if current_step < len(plan):
            return "next_step"

        return "complete"

    # --------------------------------------------------------
    # Verification failed
    # --------------------------------------------------------

    retry_count = state.get(
        "retry_count",
        0,
    )

    max_retries = state.get(
        "max_retries",
        DEFAULT_MAX_RETRIES,
    )

    if retry_count < max_retries:
        return "retry"

    return "failed"


# ============================================================
# Build LangGraph
# ============================================================


builder = StateGraph(MethuState)


# ============================================================
# Core Nodes
# ============================================================


builder.add_node(
    "orchestrator",
    orchestrator_node,
)


# ============================================================
# Direct Specialist Agents
# ============================================================


builder.add_node(
    "computer",
    computer_agent_node,
)

builder.add_node(
    "browser",
    browser_agent_node,
)

builder.add_node(
    "news",
    news_agent_node,
)

builder.add_node(
    "coding",
    coding_node,
)

builder.add_node(
    "research",
    research_node,
)

builder.add_node(
    "vision",
    vision_node,
)

builder.add_node(
    "memory",
    memory_node,
)

builder.add_node(
    "system",
    system_node,
)

builder.add_node(
    "conversation",
    conversation_node,
)


# ============================================================
# Agentic Execution Nodes
# ============================================================


builder.add_node(
    "planner",
    planning_node,
)

builder.add_node(
    "load_step",
    load_step_node,
)

builder.add_node(
    "execute_step",
    execute_step_node,
)

builder.add_node(
    "verify_step",
    verify_step_node,
)

builder.add_node(
    "retry_step",
    retry_step_node,
)

builder.add_node(
    "complete",
    complete_task_node,
)

builder.add_node(
    "failed",
    failed_task_node,
)


# ============================================================
# Graph Entry
# ============================================================


builder.add_edge(
    START,
    "orchestrator",
)


# ============================================================
# Orchestrator Routing
# ============================================================


builder.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {
        "planner": "planner",

        "computer": "computer",
        "browser": "browser",
        "news": "news",

        "coding": "coding",
        "research": "research",
        "vision": "vision",
        "memory": "memory",
        "system": "system",

        "orchestrator": "conversation",
    },
)


# ============================================================
# Planner Routing
# ============================================================


builder.add_conditional_edges(
    "planner",
    route_after_planning,
    {
        "load_step": "load_step",
        "failed": "failed",
    },
)


# ============================================================
# Load Step -> Execute Step
# ============================================================


builder.add_edge(
    "load_step",
    "execute_step",
)


# ============================================================
# Execute Step -> Verify Step
# ============================================================


builder.add_conditional_edges(
    "execute_step",
    route_after_execution,
    {
        "verify": "verify_step",
        "failed": "failed",
    },
)


# ============================================================
# Verify -> Next / Retry / Complete / Failed
# ============================================================


builder.add_conditional_edges(
    "verify_step",
    route_after_verification,
    {
        "next_step": "load_step",
        "retry": "retry_step",
        "complete": "complete",
        "failed": "failed",
    },
)


# ============================================================
# Retry -> Load Same Step
# ============================================================


builder.add_edge(
    "retry_step",
    "load_step",
)


# ============================================================
# Direct Agent Endpoints
# ============================================================


builder.add_edge(
    "computer",
    END,
)

builder.add_edge(
    "browser",
    END,
)

builder.add_edge(
    "news",
    END,
)

builder.add_edge(
    "coding",
    END,
)

builder.add_edge(
    "research",
    END,
)

builder.add_edge(
    "vision",
    END,
)

builder.add_edge(
    "memory",
    END,
)

builder.add_edge(
    "system",
    END,
)

builder.add_edge(
    "conversation",
    END,
)


# ============================================================
# Execution Endpoints
# ============================================================


builder.add_edge(
    "complete",
    END,
)

builder.add_edge(
    "failed",
    END,
)


# ============================================================
# Compile METHU
# ============================================================


methu_graph = builder.compile()
