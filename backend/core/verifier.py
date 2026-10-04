from typing import Any

from backend.tools.system.processes import is_app_running


def verify_open_app(
    tool_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Verify that an application requested through open_app
    has a corresponding running Windows process.
    """

    app_name = tool_result.get("app")

    if not app_name:
        return {
            "verified": False,
            "method": "process_check",
            "message": (
                "Verification failed because the tool result "
                "did not contain an application name."
            ),
        }

    running = is_app_running(app_name)

    if running:
        return {
            "verified": True,
            "method": "process_check",
            "message": (
                f"{app_name} process is running."
            ),
            "observed": {
                "app": app_name,
                "running": True,
            },
        }

    return {
        "verified": False,
        "method": "process_check",
        "message": (
            f"{app_name} process was not found."
        ),
        "observed": {
            "app": app_name,
            "running": False,
        },
    }


def verify_tool_result(
    tool_name: str | None,
    tool_result: Any,
) -> dict[str, Any]:
    """
    Main verification router.

    More verification methods will be added here later.
    """

    if not tool_name:
        return {
            "verified": False,
            "method": "none",
            "message": "No tool was available for verification.",
        }

    if not isinstance(tool_result, dict):
        return {
            "verified": False,
            "method": "none",
            "message": (
                "Tool result could not be independently verified."
            ),
        }

    if tool_name == "open_app":
        return verify_open_app(tool_result)

    return {
        "verified": False,
        "method": "unsupported",
        "message": (
            f"Independent verification for '{tool_name}' "
            "has not been implemented yet."
        ),
    }
