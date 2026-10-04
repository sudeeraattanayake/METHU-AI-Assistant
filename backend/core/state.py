from typing import Annotated, Any, Literal
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


AgentName = Literal[
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

ExecutionStatus = Literal[
    "idle",
    "understanding",
    "planning",
    "waiting_approval",
    "executing",
    "verifying",
    "replanning",
    "completed",
    "failed",
]


class MethuState(TypedDict, total=False):

    # ---------------------------------------------------------
    # Conversation
    # ---------------------------------------------------------

    messages: Annotated[list[BaseMessage], add_messages]

    user_input: str
    final_response: str

    # ---------------------------------------------------------
    # Understanding
    # ---------------------------------------------------------

    intent: str
    language: str

    # ---------------------------------------------------------
    # Planning
    # ---------------------------------------------------------

    plan: list[str]
    current_step: int

    # ---------------------------------------------------------
    # Agent Routing
    # ---------------------------------------------------------

    selected_agent: AgentName

    # ---------------------------------------------------------
    # Tool / MCP Execution
    # ---------------------------------------------------------

    tool_name: str | None
    tool_input: dict[str, Any]
    tool_result: Any

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    status: ExecutionStatus
    error: str | None

    # ---------------------------------------------------------
    # Verification / Repair
    # ---------------------------------------------------------

    verified: bool
    verification_message: str

    retry_count: int

    # ---------------------------------------------------------
    # Security / Approval
    # ---------------------------------------------------------

    requires_approval: bool
    approval_granted: bool | None
    risk_level: Literal["low", "medium", "high"]

    # ---------------------------------------------------------
    # Memory
    # ---------------------------------------------------------

    memory_context: list[str]

    # ---------------------------------------------------------
    # Vision
    # ---------------------------------------------------------

    image_paths: list[str]
    screenshot_path: str | None

    # ---------------------------------------------------------
    # Holographic UI
    # ---------------------------------------------------------

    ui_event: str | None
    ui_payload: dict[str, Any]

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    session_id: str
