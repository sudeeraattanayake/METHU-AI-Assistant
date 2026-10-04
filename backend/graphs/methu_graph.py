from langgraph.graph import StateGraph, START, END

from backend.core.state import MethuState
from backend.core.planner import create_plan

from backend.agents.orchestrator import orchestrator_node
from backend.agents.news_agent import news_agent_node
from backend.agents.computer_agent import computer_agent_node
from backend.agents.browser_agent import browser_agent_node


# ============================================================
# Temporary Specialist Agents
# ============================================================


def coding_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Coding Agent selected.",
        "ui_event": "coding_agent_active",
        "ui_payload": {"agent": "coding"},
    }


def research_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Research Agent selected.",
        "ui_event": "research_agent_active",
        "ui_payload": {"agent": "research"},
    }


def vision_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Vision Agent selected.",
        "ui_event": "vision_agent_active",
        "ui_payload": {"agent": "vision"},
    }


def memory_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "Memory Agent selected.",
        "ui_event": "memory_agent_active",
        "ui_payload": {"agent": "memory"},
    }


def system_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "System Agent selected.",
        "ui_event": "system_agent_active",
        "ui_payload": {"agent": "system"},
    }


def conversation_node(state: MethuState) -> dict:
    return {
        "status": "completed",
        "final_response": "METHU Orchestrator selected for conversation.",
        "ui_event": "methu_speaking",
        "ui_payload": {"agent": "orchestrator"},
    }


# ============================================================
# Multi-Step Planning
# ============================================================


def planning_node(state: MethuState) -> dict:
    """
    Create ONE authoritative structured execution plan.
    """

    user_input = state.get("user_input", "").strip()

    if not user_input:
        return {
            "status": "failed",
            "error": "No request was provided.",
            "structured_plan": [],
            "execution_results": [],
            "current_step": 0,
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
            "verified": False,
            "verification_message": "",
            "error": None,
            "ui_event": "methu_plan_created",
            "ui_payload": {
                "goal": plan.goal,
                "steps": structured_plan,
            },
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "structured_plan": [],
            "execution_results": [],
            "current_step": 0,
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
    Load the next plan step into current_plan_step.
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
        "ui_event": "methu_step_started",
        "ui_payload": {
            "step_id": step["step_id"],
            "agent": step["agent"],
            "instruction": step["instruction"],
        },
    }


# ============================================================
# Execute ONE Step
# ============================================================


def execute_step_node(state: MethuState) -> dict:
    """
    Execute exactly ONE plan step.

    LangGraph controls the loop rather than execute_plan().
    """

    step = state.get("current_plan_step")

    if not step:
        return {
            "status": "failed",
            "error": "No current plan step was loaded.",
        }

    agent = step.get("agent")
    instruction = step.get("instruction", "")

    session_id = state.get("session_id", "default")

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
        state.get("execution_results", [])
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
        "ui_payload": result.get("ui_payload", {}),
    }

    execution_results.append(step_result)

    # Tool execution failed
    if result.get("status") != "completed":
        return {
            "status": "failed",
            "execution_results": execution_results,
            "error": (
                result.get("error")
                or f"Step {step['step_id']} failed."
            ),
            "verified": False,
            "ui_event": "methu_step_failed",
            "ui_payload": {
                "step": step,
                "result": step_result,
            },
        }

    # IMPORTANT:
    # current_step here represents how many plan steps
    # have successfully completed.
    completed_count = state.get("current_step", 0) + 1

    return {
        "status": "executing",
        "current_step": completed_count,
        "execution_results": execution_results,
        "tool_name": result.get("tool_name"),
        "tool_result": result.get("tool_result"),
        "verified": False,
        "verification_message": (
            "Step execution succeeded but has not yet "
            "been independently verified."
        ),
        "ui_event": "methu_step_completed",
        "ui_payload": {
            "step_id": step["step_id"],
            "agent": agent,
            "instruction": instruction,
            "result": step_result,
        },
        "error": None,
    }


# ============================================================
# Complete Multi-Step Task
# ============================================================


def complete_task_node(state: MethuState) -> dict:
    plan = state.get("structured_plan", [])
    results = state.get("execution_results", [])

    return {
        "status": "completed",
        "current_plan_step": None,
        "verified": False,
        "verification_message": (
            "All planned steps executed successfully, but "
            "independent observation and verification have "
            "not yet been implemented."
        ),
        "final_response": (
            f"I completed all {len(results)} planned steps."
        ),
        "ui_event": "multi_step_completed",
        "ui_payload": {
            "completed_steps": len(results),
            "total_steps": len(plan),
            "results": results,
        },
        "error": None,
    }


# ============================================================
# Failed Multi-Step Task
# ============================================================


def failed_task_node(state: MethuState) -> dict:
    return {
        "status": "failed",
        "verified": False,
        "final_response": (
            "I couldn't complete the entire task."
        ),
        "ui_event": "methu_execution_failed",
        "ui_payload": {
            "error": state.get("error"),
            "current_step": state.get("current_step", 0),
            "results": state.get("execution_results", []),
        },
    }


# ============================================================
# Routing
# ============================================================


def route_after_orchestrator(state: MethuState) -> str:
    """
    The orchestrator understands/routs the request.

    Multi-action requests go to the authoritative planner.
    Simple requests continue directly to specialist agents.
    """

    initial_plan = state.get("plan", [])

    if len(initial_plan) > 1:
        return "planner"

    return state.get(
        "selected_agent",
        "orchestrator",
    )


def route_after_planning(state: MethuState) -> str:
    if state.get("status") == "failed":
        return "failed"

    if not state.get("structured_plan"):
        return "failed"

    return "load_step"


def route_after_execution(state: MethuState) -> str:
    """
    After executing one step:

    failed      -> failed node
    more steps  -> load next step
    no steps    -> complete
    """

    if state.get("status") == "failed":
        return "failed"

    plan = state.get("structured_plan", [])
    current_step = state.get("current_step", 0)

    if current_step < len(plan):
        return "next_step"

    return "complete"


# ============================================================
# Build Graph
# ============================================================


builder = StateGraph(MethuState)


# ------------------------------------------------------------
# Core
# ------------------------------------------------------------

builder.add_node(
    "orchestrator",
    orchestrator_node,
)


# ------------------------------------------------------------
# Direct specialist agents
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Agentic execution loop
# ------------------------------------------------------------

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
    "complete",
    complete_task_node,
)

builder.add_node(
    "failed",
    failed_task_node,
)


# ============================================================
# Entry
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
        "coding": "coding",
        "browser": "browser",
        "research": "research",
        "news": "news",
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
# Load Step -> Execute
# ============================================================

builder.add_edge(
    "load_step",
    "execute_step",
)


# ============================================================
# Execute -> Next / Complete / Failed
# ============================================================

builder.add_conditional_edges(
    "execute_step",
    route_after_execution,
    {
        "next_step": "load_step",
        "complete": "complete",
        "failed": "failed",
    },
)


# ============================================================
# Direct Agent Endpoints
# ============================================================

builder.add_edge("computer", END)
builder.add_edge("browser", END)
builder.add_edge("news", END)

builder.add_edge("coding", END)
builder.add_edge("research", END)
builder.add_edge("vision", END)
builder.add_edge("memory", END)
builder.add_edge("system", END)
builder.add_edge("conversation", END)


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
# Compile
# ============================================================

methu_graph = builder.compile()
