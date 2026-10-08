from langgraph.graph import StateGraph, START, END
from backend.core.state import MethuState
from backend.core.planner import create_plan, create_recovery_plan
from backend.core.verifier import verify_tool_result
from backend.agents.orchestrator import orchestrator_node
from backend.agents.news_agent import news_agent_node
from backend.agents.computer_agent import computer_agent_node
from backend.agents.browser_agent import browser_agent_node
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_REPLANS = 1


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
        "final_response": (
            "METHU Orchestrator selected for conversation."
        ),
        "ui_event": "methu_speaking",
        "ui_payload": {"agent": "orchestrator"},
    }


def planning_node(state: MethuState) -> dict:
    """
    Create the initial authoritative structured execution plan.
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
            "max_replans": DEFAULT_MAX_REPLANS,
            "verified": False,
        }
    try:
        plan = create_plan(user_input)
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
            "replan_count": 0,
            "max_replans": DEFAULT_MAX_REPLANS,
            "verified": False,
            "ui_event": "methu_error",
            "ui_payload": {"error": str(exc)},
        }
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
            "max_replans": DEFAULT_MAX_REPLANS,
            "verified": False,
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
        "retry_count": 0,
        "max_retries": state.get(
            "max_retries",
            DEFAULT_MAX_RETRIES,
        ),
        "retry_reason": None,
        "replan_count": 0,
        "max_replans": state.get(
            "max_replans",
            DEFAULT_MAX_REPLANS,
        ),
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
            "max_replans": state.get(
                "max_replans",
                DEFAULT_MAX_REPLANS,
            ),
        },
    }


def load_step_node(state: MethuState) -> dict:
    """
    Load the current structured plan step.
    """
    plan = state.get(
        "structured_plan",
        [],
    )
    current_step = state.get(
        "current_step",
        0,
    )
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
            "replan_count": state.get(
                "replan_count",
                0,
            ),
            "max_replans": state.get(
                "max_replans",
                DEFAULT_MAX_REPLANS,
            ),
        },
    }


def execute_step_node(state: MethuState) -> dict:
    """
    Execute exactly one structured plan step.
    """
    step = state.get("current_plan_step")
    if not step:
        return {
            "status": "failed",
            "error": "No current plan step was loaded.",
            "verified": False,
        }
    agent = step.get("agent")
    instruction = step.get(
        "instruction",
        "",
    )
    session_id = state.get(
        "session_id",
        "default",
    )
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
            "verified": False,
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
            "verified": False,
        }
    execution_results = list(
        state.get(
            "execution_results",
            [],
        )
    )
    attempt_number = (
        state.get(
            "retry_count",
            0,
        )
        + 1
    )
    step_result = {
        "step_id": step["step_id"],
        "agent": agent,
        "instruction": instruction,
        "status": result.get(
            "status",
        ),
        "response": result.get(
            "final_response",
        ),
        "tool_name": result.get(
            "tool_name",
        ),
        "tool_result": result.get(
            "tool_result",
        ),
        "ui_event": result.get(
            "ui_event",
        ),
        "ui_payload": result.get(
            "ui_payload",
            {},
        ),
        "attempt": attempt_number,
        "verified": False,
        "verification": None,
    }
    execution_results.append(
        step_result
    )
    # --------------------------------------------------------
    # Execution failed before independent verification
    # --------------------------------------------------------
    if result.get("status") != "completed":
        failure_reason = (
            result.get("error")
            or f"Step {step['step_id']} failed."
        )
        return {
            "status": "failed",
            "execution_results": execution_results,
            "error": failure_reason,
            "verified": False,
            "verification_message": (
                "Execution failed before verification."
            ),
            "retry_reason": failure_reason,
            "ui_event": "methu_step_failed",
            "ui_payload": {
                "step": step,
                "result": step_result,
            },
        }
    # --------------------------------------------------------
    # Execution succeeded
    # --------------------------------------------------------
    next_step_index = (
        state.get(
            "current_step",
            0,
        )
        + 1
    )
    return {
        "status": "executing",
        # Important:
        # pointer advances before verification.
        "current_step": next_step_index,
        "execution_results": execution_results,
        # Evidence used by independent verifier.
        "tool_name": result.get(
            "tool_name",
        ),
        "tool_input": result.get(
            "tool_input",
            {},
        ),
        "tool_result": result.get(
            "tool_result",
        ),
        "verified": False,
        "verification_message": (
            "Execution succeeded. Waiting for "
            "independent verification."
        ),
        "error": None,
        "ui_event": "methu_step_completed",
        "ui_payload": {
            "step_id": step["step_id"],
            "agent": agent,
            "instruction": instruction,
            "attempt": attempt_number,
            "result": step_result,
        },
    }


def verify_step_node(state: MethuState) -> dict:
    """
    Independently verify the most recently executed step.
    """
    tool_name = state.get(
        "tool_name",
    )
    tool_result = state.get(
        "tool_result",
    )
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
    if execution_results:
        latest_result = execution_results[-1]
        execution_results[-1] = {
            **latest_result,
            "verified": verified,
            "verification": verification,
        }
    # --------------------------------------------------------
    # Verification success
    # --------------------------------------------------------
    if verified:
        return {
            "status": "verifying",
            "verified": True,
            "verification_message": (
                verification.get(
                    "message",
                    "",
                )
            ),
            "execution_results": execution_results,
            # New successfully verified step gets a fresh
            # retry budget.
            "retry_count": 0,
            "retry_reason": None,
            "error": None,
            "ui_event": "methu_step_verified",
            "ui_payload": {
                "verified": True,
                "verification": verification,
            },
        }
    # --------------------------------------------------------
    # Verification failure
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
        "error": None,
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


def retry_step_node(state: MethuState) -> dict:
    """
    Prepare the most recently failed verification step
    for another execution attempt.
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
    # execute_step_node advanced current_step before verification.
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
        failed_step = plan[
            failed_step_index
        ]
    execution_results = list(
        state.get(
            "execution_results",
            [],
        )
    )
    # Remove the failed attempt from final-plan result tracking.
    #
    # Later we can add a separate attempt_history for permanent
    # execution/recovery auditing.
    if execution_results:
        execution_results.pop()
    new_retry_count = (
        retry_count + 1
    )
    return {
        "status": "observing",
        # Return pointer to the failed step.
        "current_step": failed_step_index,
        "current_plan_step": None,
        "execution_results": execution_results,
        "retry_count": new_retry_count,
        "max_retries": max_retries,
        "retry_reason": retry_reason,
        "verified": False,
        "verification_message": (
            f"Verification failed. "
            f"Retrying step "
            f"{failed_step_index + 1}. "
            f"Retry "
            f"{new_retry_count}/{max_retries}."
        ),
        # Clear stale tool evidence before executing again.
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


def reobserve_node(state: MethuState) -> dict:
    """
    Collect failure evidence after the current step has
    exhausted its retry budget.
    V1 collects existing execution and verification evidence.
    Future versions can add:
    - fresh DOM observation
    - screenshots
    - vision analysis
    - active-window observation
    - accessibility tree
    """
    plan = state.get(
        "structured_plan",
        [],
    )
    current_step = state.get(
        "current_step",
        0,
    )
    failed_step_index = max(
        current_step - 1,
        0,
    )
    failed_step = None
    if failed_step_index < len(plan):
        failed_step = plan[
            failed_step_index
        ]
    verification_message = state.get(
        "verification_message",
        "Verification failed.",
    )
    retry_reason = state.get(
        "retry_reason",
        verification_message,
    )
    observation = {
        "failed_step_index": failed_step_index,
        "failed_step": failed_step,
        "retry_count": state.get(
            "retry_count",
            0,
        ),
        "max_retries": state.get(
            "max_retries",
            DEFAULT_MAX_RETRIES,
        ),
        "retry_reason": retry_reason,
        "verification_message": (
            verification_message
        ),
        "tool_name": state.get(
            "tool_name",
        ),
        "tool_input": state.get(
            "tool_input",
            {},
        ),
        "tool_result": state.get(
            "tool_result",
        ),
    }
    return {
        "status": "observing",
        "verified": False,
        "retry_reason": retry_reason,
        "error": None,
        "ui_event": "methu_reobserving",
        "ui_payload": {
            "message": (
                "Retry limit reached. "
                "METHU is collecting fresh "
                "failure evidence before replanning."
            ),
            "observation": observation,
        },
    }


def replan_node(state: MethuState) -> dict:
    """
    Create a corrected execution strategy after retries
    have been exhausted.
    """
    replan_count = state.get(
        "replan_count",
        0,
    )
    max_replans = state.get(
        "max_replans",
        DEFAULT_MAX_REPLANS,
    )
    # --------------------------------------------------------
    # Replan safety boundary
    # --------------------------------------------------------
    if replan_count >= max_replans:
        return {
            "status": "failed",
            "verified": False,
            "error": (
                "Maximum recovery replans reached."
            ),
            "verification_message": (
                "METHU could not recover the task "
                "within the allowed replan limit."
            ),
            "ui_event": (
                "methu_replan_limit_reached"
            ),
            "ui_payload": {
                "replan_count": replan_count,
                "max_replans": max_replans,
            },
        }
    # --------------------------------------------------------
    # Original user goal
    # --------------------------------------------------------
    original_goal = state.get(
        "user_input",
        "",
    ).strip()
    if not original_goal:
        return {
            "status": "failed",
            "verified": False,
            "error": (
                "Original user goal is missing."
            ),
            "verification_message": (
                "Recovery planning could not continue "
                "because the original goal was unavailable."
            ),
            "ui_event": "methu_replan_failed",
            "ui_payload": {
                "reason": "Missing original goal.",
            },
        }
    # --------------------------------------------------------
    # Determine failed step
    # --------------------------------------------------------
    plan = state.get(
        "structured_plan",
        [],
    )
    current_step = state.get(
        "current_step",
        0,
    )
    # current_step was advanced before verification.
    failed_step_index = max(
        current_step - 1,
        0,
    )
    failed_step = None
    if failed_step_index < len(plan):
        failed_step = plan[
            failed_step_index
        ]
    # --------------------------------------------------------
    # Recovery evidence
    # --------------------------------------------------------
    failure_evidence = {
        "retry_count": state.get(
            "retry_count",
            0,
        ),
        "max_retries": state.get(
            "max_retries",
            DEFAULT_MAX_RETRIES,
        ),
        "retry_reason": state.get(
            "retry_reason",
        ),
        "verification_message": state.get(
            "verification_message",
        ),
        "tool_name": state.get(
            "tool_name",
        ),
        "tool_input": state.get(
            "tool_input",
            {},
        ),
        "tool_result": state.get(
            "tool_result",
        ),
        # V1 re-observation evidence currently lives here.
        "reobservation": state.get(
            "ui_payload",
            {},
        ),
    }
    # --------------------------------------------------------
    # Ask recovery planner for a corrected strategy
    # --------------------------------------------------------
    try:
        recovery_plan = create_recovery_plan(
            original_goal=original_goal,
            failed_step=failed_step,
            failure_evidence=failure_evidence,
        )
    except Exception as exc:
        return {
            "status": "failed",
            "verified": False,
            "error": str(exc),
            "verification_message": (
                "Recovery planner failed."
            ),
            "ui_event": "methu_replan_failed",
            "ui_payload": {
                "error": str(exc),
            },
        }
    # --------------------------------------------------------
    # Validate recovery plan
    # --------------------------------------------------------
    if not recovery_plan.steps:
        return {
            "status": "failed",
            "verified": False,
            "error": (
                "Recovery planner produced "
                "no executable steps."
            ),
            "verification_message": (
                "METHU could not create "
                "a recovery plan."
            ),
            "ui_event": "methu_replan_failed",
            "ui_payload": {
                "reason": (
                    "Recovery plan contained "
                    "no steps."
                ),
            },
        }
    structured_recovery_plan = [
        step.model_dump()
        for step in recovery_plan.steps
    ]
    new_replan_count = (
        replan_count + 1
    )
    # --------------------------------------------------------
    # Activate recovery plan
    # --------------------------------------------------------
    return {
        "status": "replanning",
        "structured_plan": (
            structured_recovery_plan
        ),
        # Start new recovery plan at its first step.
        "current_step": 0,
        "current_plan_step": None,
        # Recovery plan has its own final verification results.
        "execution_results": [],
        # Reset retry budget for recovery execution.
        "retry_count": 0,
        "max_retries": state.get(
            "max_retries",
            DEFAULT_MAX_RETRIES,
        ),
        "retry_reason": None,
        # Consume one recovery replan.
        "replan_count": new_replan_count,
        "max_replans": max_replans,
        "verified": False,
        "verification_message": "",
        # Clear stale execution evidence.
        "tool_name": None,
        "tool_input": {},
        "tool_result": None,
        "error": None,
        "ui_event": "methu_replanned",
        "ui_payload": {
            "original_goal": original_goal,
            "failed_step": failed_step,
            "failure_evidence": failure_evidence,
            "replan_count": new_replan_count,
            "max_replans": max_replans,
            "recovery_goal": recovery_plan.goal,
            "recovery_plan": (
                structured_recovery_plan
            ),
        },
    }


def complete_task_node(state: MethuState) -> dict:
    """
    Complete only when every step in the currently active
    plan has an independently verified result.
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
            "All planned steps executed and "
            "were independently verified."
        )
        if state.get("replan_count", 0) > 0:
            final_response = (
                f"I recovered from the failed strategy "
                f"and completed and verified all "
                f"{len(results)} recovery steps."
            )
        else:
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
        "error": None,
        "ui_event": "multi_step_completed",
        "ui_payload": {
            "completed_steps": len(
                results
            ),
            "total_steps": len(
                plan
            ),
            "verified": all_verified,
            "replan_count": state.get(
                "replan_count",
                0,
            ),
            "max_replans": state.get(
                "max_replans",
                DEFAULT_MAX_REPLANS,
            ),
            "results": results,
        },
    }


def failed_task_node(state: MethuState) -> dict:
    """
    Final bounded safe failure.
    """
    error = state.get(
        "error",
    )
    retry_reason = state.get(
        "retry_reason",
    )
    if not error:
        error = (
            retry_reason
            or "Unknown execution error."
        )
    return {
        "status": "failed",
        "verified": False,
        "verification_message": state.get(
            "verification_message",
            "Task execution failed.",
        ),
        "final_response": (
            "I couldn't safely verify and "
            "complete the entire task."
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
            "replan_count": state.get(
                "replan_count",
                0,
            ),
            "max_replans": state.get(
                "max_replans",
                DEFAULT_MAX_REPLANS,
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


def route_after_orchestrator(
    state: MethuState,
) -> str:
    """
    Route requests safely.
    Failed requests and requests awaiting approval
    must not reach an execution agent.
    Multi-step tasks use the dedicated planner.
    Simple tasks use their specialist agent.
    """
    if state.get("status") == "failed":
        return "failed"
    if (
        state.get("status") == "waiting_approval"
        or state.get("requires_approval", False)
    ):
        return "approval_required"
    if state.get("requires_planning", False):
        return "planner"
    return state.get(
        "selected_agent",
        "orchestrator",
    )


def approval_required_node(state: MethuState) -> dict:
    return {
        "status": "waiting_approval",
        "requires_approval": True,
        "approval_granted": False,
        "final_response": "This request requires your approval. No action was performed.",
        "ui_event": "methu_approval_required",
        "ui_payload": {
            "intent": state.get("intent", ""),
            "risk_level": state.get("risk_level", "medium"),
            "requires_approval": True,
        },
    }


def route_after_planning(
    state: MethuState,
) -> str:
    """
    Planner -> first execution step.
    """
    if state.get("status") == "failed":
        return "failed"
    if not state.get(
        "structured_plan"
    ):
        return "failed"
    return "load_step"


def route_after_execution(
    state: MethuState,
) -> str:
    """
    Successful execution must go through independent
    verification.
    """
    if state.get("status") == "failed":
        return "failed"
    return "verify"


def route_after_verification(
    state: MethuState,
) -> str:
    """
    Route after independent verification.
    The latest execution result is the authoritative
    source for step verification.
    """
    if state.get("status") == "failed":
        return "failed"
    structured_plan = state.get(
        "structured_plan",
        [],
    )
    current_step = state.get(
        "current_step",
        0,
    )
    # ========================================================
    # Determine authoritative verification result
    # ========================================================
    execution_results = state.get(
        "execution_results",
        [],
    )
    verified = False
    if execution_results:
        latest_result = execution_results[-1]
        verified = latest_result.get(
            "verified",
            False,
        )
    else:
        verified = state.get(
            "verified",
            False,
        )
    # ========================================================
    # Verification succeeded
    # ========================================================
    if verified:
        # There are more steps in the active plan.
        if current_step < len(structured_plan):
            return "next_step"
        # Entire active plan has finished.
        return "complete"
    # ========================================================
    # Verification failed
    # ========================================================
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
    # ========================================================
    # Retry budget exhausted
    # ========================================================
    replan_count = state.get(
        "replan_count",
        0,
    )
    max_replans = state.get(
        "max_replans",
        DEFAULT_MAX_REPLANS,
    )
    if replan_count < max_replans:
        return "reobserve"
    return "failed"
    # --------------------------------------------------------
    # Verification success
    # --------------------------------------------------------
    if verified:
        if current_step < len(
            structured_plan
        ):
            return "next_step"
        return "complete"
    # --------------------------------------------------------
    # Verification failure
    # --------------------------------------------------------
    retry_count = state.get(
        "retry_count",
        0,
    )
    max_retries = state.get(
        "max_retries",
        DEFAULT_MAX_RETRIES,
    )
    # First use normal retry budget.
    if retry_count < max_retries:
        return "retry"
    # --------------------------------------------------------
    # Retry budget exhausted
    # --------------------------------------------------------
    replan_count = state.get(
        "replan_count",
        0,
    )
    max_replans = state.get(
        "max_replans",
        DEFAULT_MAX_REPLANS,
    )
    # Recovery strategy still available.
    if replan_count < max_replans:
        return "reobserve"
    # No more recovery budget.
    return "failed"


def route_after_replan(
    state: MethuState,
) -> str:
    """
    Valid recovery plan -> execute it.
    Failed/empty recovery plan -> stop safely.
    """
    if state.get("status") == "failed":
        return "failed"
    recovery_plan = state.get(
        "structured_plan",
        [],
    )
    if not recovery_plan:
        return "failed"
    return "load_step"


builder = StateGraph(MethuState)
builder.add_node("approval_required", approval_required_node)
builder.add_node(
    "orchestrator",
    orchestrator_node,
)
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
    "reobserve",
    reobserve_node,
)
builder.add_node(
    "replan",
    replan_node,
)
builder.add_node(
    "complete",
    complete_task_node,
)
builder.add_node(
    "failed",
    failed_task_node,
)
builder.add_edge(
    START,
    "orchestrator",
)
builder.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {
        "planner": "planner",
        "failed": "failed",
        "approval_required": "approval_required",
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
builder.add_conditional_edges(
    "planner",
    route_after_planning,
    {
        "load_step": "load_step",
        "failed": "failed",
    },
)
builder.add_edge(
    "load_step",
    "execute_step",
)
builder.add_conditional_edges(
    "execute_step",
    route_after_execution,
    {
        "verify": "verify_step",
        "failed": "failed",
    },
)
builder.add_conditional_edges(
    "verify_step",
    route_after_verification,
    {
        "next_step": "load_step",
        "retry": "retry_step",
        "reobserve": "reobserve",
        "complete": "complete",
        "failed": "failed",
    },
)
builder.add_edge(
    "retry_step",
    "load_step",
)
builder.add_edge(
    "reobserve",
    "replan",
)
builder.add_conditional_edges(
    "replan",
    route_after_replan,
    {
        "load_step": "load_step",
        "failed": "failed",
    },
)
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
builder.add_edge(
    "complete",
    END,
)
builder.add_edge(
    "failed",
    END,
)
builder.add_edge("approval_required", END)


methu_graph = builder.compile()
