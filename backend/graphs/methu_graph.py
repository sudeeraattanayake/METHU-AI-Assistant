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
# Multi-Step Execution Node
# ============================================================


def multi_step_node(state: MethuState) -> dict:
    """
    Execute a multi-step METHU request.

    Current architecture:

        User request
            ↓
        Structured Planner
            ↓
        Sequential Executor
            ↓
        Computer / Browser Agents
            ↓
        Tool execution

    Observation and independent verification will be added
    in the next architecture stage.
    """

    user_input = state.get(
        "user_input",
        "",
    ).strip()

    session_id = state.get(
        "session_id",
        "default",
    )

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not user_input:
        return {
            "status": "failed",
            "error": "No request was provided.",
            "verified": False,
            "final_response": (
                "I couldn't execute the task because no request "
                "was provided."
            ),
            "ui_event": "methu_error",
            "ui_payload": {
                "error": "No request was provided.",
            },
        }

    try:

        # ====================================================
        # 1. PLAN
        # ====================================================

        plan = create_plan(user_input)

        if not plan.steps:
            return {
                "status": "failed",
                "error": (
                    "Planner produced no executable steps."
                ),
                "verified": False,
                "final_response": (
                    "I couldn't create an executable plan "
                    "for that request."
                ),
                "ui_event": "methu_error",
                "ui_payload": {
                    "error": (
                        "Planner produced no executable steps."
                    ),
                },
            }

        # Convert Pydantic PlanStep objects into dictionaries
        # that can safely live inside LangGraph state.

        structured_plan = [
            step.model_dump()
            for step in plan.steps
        ]

        # ====================================================
        # 2. EXECUTE
        # ====================================================

        execution = execute_plan(
            plan=plan,
            session_id=session_id,
        )

        # ====================================================
        # 3. HANDLE EXECUTION FAILURE
        # ====================================================

        if not execution.get("success", False):

            results = execution.get(
                "results",
                [],
            )

            failed_step = execution.get(
                "failed_step",
            )

            return {
                "status": "failed",

                "structured_plan": structured_plan,

                "execution_results": results,

                "current_step": (
                    failed_step
                    if failed_step is not None
                    else len(results)
                ),

                "current_plan_step": None,

                "final_response": (
                    "I couldn't complete the entire task."
                ),

                "tool_name": "multi_step_executor",

                "tool_input": {
                    "goal": plan.goal,
                },

                "tool_result": execution,

                "verified": False,

                "verification_message": (
                    "Execution failed before independent "
                    "verification could be performed."
                ),

                "error": execution.get(
                    "error",
                    "Multi-step execution failed.",
                ),

                "ui_event": "methu_execution_failed",

                "ui_payload": {
                    "goal": plan.goal,
                    "results": results,
                    "failed_step": failed_step,
                },
            }

        # ====================================================
        # 4. EXECUTION COMPLETED
        # ====================================================

        results = execution.get(
            "results",
            [],
        )

        completed_steps = execution.get(
            "completed_steps",
            len(results),
        )

        return {
            "status": "completed",

            # Structured plan
            "structured_plan": structured_plan,

            # Execution progress
            "current_step": completed_steps,

            "current_plan_step": None,

            # Results of every executed step
            "execution_results": results,

            # User response
            "final_response": (
                f"I completed the task: {plan.goal}."
            ),

            # Tool information
            "tool_name": "multi_step_executor",

            "tool_input": {
                "goal": plan.goal,
            },

            "tool_result": execution,

            # IMPORTANT:
            #
            # The tools reported successful execution.
            # We have NOT independently observed the screen
            # or external application state yet.
            #
            # Therefore this MUST remain False.
            "verified": False,

            "verification_message": (
                "Execution completed, but external state "
                "has not yet been independently verified."
            ),

            # UI
            "ui_event": "multi_step_completed",

            "ui_payload": {
                "goal": plan.goal,
                "completed_steps": completed_steps,
                "results": results,
            },

            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",

            "error": str(exc),

            "verified": False,

            "verification_message": (
                "Execution stopped because an exception occurred."
            ),

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
    Decide whether the request should use direct specialist
    execution or METHU's multi-step execution pipeline.

    For now the orchestrator still creates the initial text plan.

    If that plan contains more than one step, route the request
    through the structured planner + executor.
    """

    plan = state.get(
        "plan",
        [],
    )

    if len(plan) > 1:
        return "multi_step"

    return state.get(
        "selected_agent",
        "orchestrator",
    )


# ============================================================
# Build METHU Graph
# ============================================================


builder = StateGraph(
    MethuState
)


# ============================================================
# Core Nodes
# ============================================================


builder.add_node(
    "orchestrator",
    orchestrator_node,
)


# ============================================================
# Real Specialist Agents
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


# ============================================================
# Temporary Specialist Agents
# ============================================================


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
# Multi-Step Executor
# ============================================================


builder.add_node(
    "multi_step",
    multi_step_node,
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


# ============================================================
# Specialist Agents -> END
# ============================================================


builder.add_edge(
    "computer",
    END,
)

builder.add_edge(
    "coding",
    END,
)

builder.add_edge(
    "browser",
    END,
)

builder.add_edge(
    "research",
    END,
)

builder.add_edge(
    "news",
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
# Multi-Step -> END
# ============================================================


builder.add_edge(
    "multi_step",
    END,
)


# ============================================================
# Compile METHU
# ============================================================


methu_graph = builder.compile()
