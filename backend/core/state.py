
from typing import Annotated, Any, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

AgentName = Literal[
    "orchestrator", "computer", "coding", "browser",
    "research", "news", "vision", "memory", "system"
]

ExecutionStatus = Literal[
    "idle", "understanding", "planning", "waiting_approval",
    "executing", "observing", "verifying", "replanning",
    "completed", "failed"
]


class MethuState(TypedDict, total=False):
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str
    final_response: str

    # Understanding
    intent: str
    language: str

    # Planning
    requires_planning: bool
    plan: list[str]
    structured_plan: list[dict[str, Any]]
    current_step: int
    current_plan_step: dict[str, Any] | None
    execution_results: list[dict[str, Any]]

    # Agent routing
    selected_agent: AgentName

    # Tool execution
    tool_name: str | None
    tool_input: dict[str, Any]
    tool_result: Any

    # Execution
    status: ExecutionStatus
    error: str | None
    retry_count: int
    max_retries: int
    retry_reason: str | None
    replan_count: int
    max_replans: int

    # Verification
    verified: bool
    verification_message: str

    # Security
    requires_approval: bool
    approval_granted: bool | None
    risk_level: Literal["low", "medium", "high"]

    # Memory
    memory_context: list[str]

    # Vision
    image_paths: list[str]
    screenshot_path: str | None

    # UI
    ui_event: str | None
    ui_payload: dict[str, Any]

    # Session
    session_id: str
