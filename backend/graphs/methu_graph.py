from langgraph.graph import StateGraph, START, END

from backend.core.state import MethuState
from backend.core.planner import create_plan
from backend.core.executor import execute_plan

from backend.agents.orchestrator import orchestrator_node
from backend.agents.news_agent import news_agent_node
from backend.agents.computer_agent import computer_agent_node
from backend.agents.browser_agent import browser_agent_node


# ============================================================
# Temporary Specialist Agent Nodes
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
# Multi-Step Executor Node
# ============================================================


def multi_step_node(state: MethuState) -> dict:
    user_input = state.get("user_input", "").strip()
    session_id = state.get("session_id", "default")

    if not user_input:
        return {
            "status": "failed",
            "error": "No request was provided.",
        }

    try:
        # 1. Create structured execution plan
        plan = create_plan(user_input)

        if not plan.steps:
            return {
                "status": "failed",
                "error": "Planner produced no executable steps.",
            }

        # 2. Execute plan
        execution = execute_plan(
            plan=plan,
            session_id=session_id,
        )

        # 3. Handle execution failure
        if not execution["success"]:
            return {
                "status": "failed",
                "final_response": "I couldn't complete the entire task.",
                "tool_name": "multi_step_executor",
                "tool_result": execution,
                "ui_event": "methu_execution_failed",
                "ui_payload": {
                    "goal": plan.goal,
                    "results": execution.get("results", []),
                    "failed_step": execution.get("failed_step"),
                },
            }

        # 4. Completed
        return {
            "status": "completed",
            "final_response": f"I completed the task: {plan.goal}.",
            "tool_name": "multi_step_executor",
            "tool_input": {
                "goal": plan.goal,
            },
            "tool_result": execution,
            "verified": False,
            "verification_message": (
                "All planned actions completed successfully. "
                "Visual verification has not been performed."
            ),
            "ui_event": "multi_step_completed",
            "ui_payload": {
                "goal": plan.goal,
                "completed_steps": execution["completed_steps"],
                "results": execution["results"],
            },
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "final_response": (
                "I encountered an error while executing the task."
            ),
            "ui_event": "methu_error",
            "ui_payload": {
                "error": str(exc),
            },
        }


# ============================================================
# Routing
# ============================================================


def route_execution(state: MethuState) -> str:
    """
    Multi-step requests go to the planner/executor.
    Simple requests go directly to their specialist agent.
    """

    plan = state.get("plan", [])

    if len(plan) > 1:
        return "multi_step"

    return state.get("selected_agent", "orchestrator")


# ============================================================
# Build METHU Graph
# ============================================================


builder = StateGraph(MethuState)

# Core
builder.add_node("orchestrator", orchestrator_node)

# Real agents
builder.add_node("computer", computer_agent_node)
builder.add_node("browser", browser_agent_node)
builder.add_node("news", news_agent_node)

# Temporary agents
builder.add_node("coding", coding_node)
builder.add_node("research", research_node)
builder.add_node("vision", vision_node)
builder.add_node("memory", memory_node)
builder.add_node("system", system_node)
builder.add_node("conversation", conversation_node)

# Multi-step execution
builder.add_node("multi_step", multi_step_node)


# ============================================================
# Edges
# ============================================================

builder.add_edge(START, "orchestrator")

builder.add_conditional_edges(
    "orchestrator",
    route_execution,
    {
        "multi_step": "multi_step",
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

builder.add_edge("computer", END)
builder.add_edge("coding", END)
builder.add_edge("browser", END)
builder.add_edge("research", END)
builder.add_edge("news", END)
builder.add_edge("vision", END)
builder.add_edge("memory", END)
builder.add_edge("system", END)
builder.add_edge("conversation", END)
builder.add_edge("multi_step", END)


# ============================================================
# Compile
# ============================================================

methu_graph = builder.compile()
