from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Actions METHU can perform automatically
LOW_RISK_ACTIONS = {
    "open_app",
    "open_website",
    "web_search",
    "news_search",
    "read_file",
    "list_files",
    "create_file",
    "create_folder",
    "edit_workspace_file",
    "run_tests",
    "take_screenshot",
    "get_system_info",
    "check_battery",
    "check_network",
}


# Actions that normally require approval
MEDIUM_RISK_ACTIONS = {
    "install_dependency",
    "run_terminal_command",
    "overwrite_file",
    "move_file",
    "rename_file",
    "git_commit",
    "git_push",
    "deploy_project",
}


# Sensitive / consequential actions
HIGH_RISK_ACTIONS = {
    "delete_file",
    "delete_folder",
    "send_email",
    "send_message",
    "send_whatsapp",
    "publish_content",
    "financial_transaction",
    "enter_credentials",
    "change_system_settings",
    "install_system_software",
    "shutdown_computer",
    "restart_computer",
}


def get_risk_level(action: str) -> RiskLevel:
    """
    Determine the risk level of a METHU action.

    Unknown actions default to MEDIUM rather than LOW.
    """

    action = action.strip().lower()

    if action in LOW_RISK_ACTIONS:
        return RiskLevel.LOW

    if action in MEDIUM_RISK_ACTIONS:
        return RiskLevel.MEDIUM

    if action in HIGH_RISK_ACTIONS:
        return RiskLevel.HIGH

    # Fail safely for unknown actions.
    return RiskLevel.MEDIUM


def requires_approval(action: str) -> bool:
    """
    Determine whether an action requires explicit user approval.
    """

    risk = get_risk_level(action)

    return risk in {
        RiskLevel.MEDIUM,
        RiskLevel.HIGH,
    }


def check_permission(action: str) -> dict:
    """
    Return permission information that agents and tools can consume.
    """

    risk = get_risk_level(action)
    approval_required = requires_approval(action)

    return {
        "action": action,
        "risk_level": risk.value,
        "requires_approval": approval_required,
        "allowed": not approval_required,
    }
