from typing import Any

from backend.security.permissions import check_permission
from backend.security.approvals import approval_manager


class CommandGuard:
    """
    Security gate between METHU agents and executable tools.

    Agents propose actions.
    CommandGuard decides whether those actions may execute.
    """

    def authorize(
        self,
        action: str,
        tool_input: dict[str, Any] | None = None,
        approval_id: str | None = None,
    ) -> dict:
        tool_input = tool_input or {}

        # ----------------------------------------------------
        # 1. Check permission policy
        # ----------------------------------------------------

        permission = check_permission(action)

        # ----------------------------------------------------
        # 2. Low-risk actions can execute automatically
        # ----------------------------------------------------

        if not permission["requires_approval"]:
            return {
                "authorized": True,
                "action": action,
                "risk_level": permission["risk_level"],
                "reason": "Low-risk action.",
                "approval_id": None,
            }

        # ----------------------------------------------------
        # 3. Protected action without approval
        # ----------------------------------------------------

        if not approval_id:
            return {
                "authorized": False,
                "action": action,
                "risk_level": permission["risk_level"],
                "reason": "User approval required.",
                "approval_id": None,
            }

        # ----------------------------------------------------
        # 4. Validate approval exists
        # ----------------------------------------------------

        approval = approval_manager.get(approval_id)

        if approval is None:
            return {
                "authorized": False,
                "action": action,
                "risk_level": permission["risk_level"],
                "reason": "Approval request not found.",
                "approval_id": approval_id,
            }

        # ----------------------------------------------------
        # 5. Approval must actually be approved
        # ----------------------------------------------------

        if approval["status"] != "approved":
            return {
                "authorized": False,
                "action": action,
                "risk_level": permission["risk_level"],
                "reason": (
                    f"Approval status is "
                    f"{approval['status']}."
                ),
                "approval_id": approval_id,
            }

        # ----------------------------------------------------
        # 6. Approval must match exact action
        # ----------------------------------------------------

        if approval["action"] != action:
            return {
                "authorized": False,
                "action": action,
                "risk_level": permission["risk_level"],
                "reason": (
                    "Approval does not match "
                    "requested action."
                ),
                "approval_id": approval_id,
            }

        # ----------------------------------------------------
        # 7. Approval must match exact tool arguments
        # ----------------------------------------------------

        if approval["tool_input"] != tool_input:
            return {
                "authorized": False,
                "action": action,
                "risk_level": permission["risk_level"],
                "reason": (
                    "Approval does not match "
                    "requested tool input."
                ),
                "approval_id": approval_id,
            }

        # ----------------------------------------------------
        # 8. Authorized
        # ----------------------------------------------------

        return {
            "authorized": True,
            "action": action,
            "risk_level": permission["risk_level"],
            "reason": "Valid user approval.",
            "approval_id": approval_id,
        }


# Global CommandGuard instance used by METHU tools.
command_guard = CommandGuard()
