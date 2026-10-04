from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.security.permissions import check_permission


@dataclass
class ApprovalRequest:
    approval_id: str
    action: str
    description: str
    risk_level: str
    tool_input: dict[str, Any]
    status: str
    created_at: str


class ApprovalManager:
    """
    Manages pending METHU approval requests.

    This is currently in-memory.
    Later we can persist approvals in SQLite.
    """

    def __init__(self):
        self.pending: dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        action: str,
        description: str,
        tool_input: dict[str, Any] | None = None,
    ) -> dict:

        permission = check_permission(action)

        request = ApprovalRequest(
            approval_id=str(uuid4()),
            action=action,
            description=description,
            risk_level=permission["risk_level"],
            tool_input=tool_input or {},
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self.pending[request.approval_id] = request

        return asdict(request)

    def approve(self, approval_id: str) -> dict | None:
        request = self.pending.get(approval_id)

        if request is None:
            return None

        request.status = "approved"

        return asdict(request)

    def reject(self, approval_id: str) -> dict | None:
        request = self.pending.get(approval_id)

        if request is None:
            return None

        request.status = "rejected"

        return asdict(request)

    def get(self, approval_id: str) -> dict | None:
        request = self.pending.get(approval_id)

        if request is None:
            return None

        return asdict(request)


approval_manager = ApprovalManager()
