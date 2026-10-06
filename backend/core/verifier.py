from typing import Any
from urllib.parse import urlparse

from backend.tools.system.processes import is_app_running
from backend.tools.browser.playwright_controller import (
    get_active_page_info,
)
from backend.tools.browser.browser_verifier import (
    verify_search_goal,
)


def verify_open_app(
    tool_result: dict[str, Any],
) -> dict[str, Any]:

    app_name = tool_result.get("app")

    if not app_name:
        return {
            "verified": False,
            "method": "process_check",
            "message": (
                "Tool result did not contain an app name."
            ),
        }

    running = is_app_running(app_name)

    return {
        "verified": running,
        "method": "process_check",
        "message": (
            f"{app_name} process is running."
            if running
            else f"{app_name} process was not found."
        ),
        "observed": {
            "app": app_name,
            "running": running,
        },
    }


def hosts_match(
    expected_url: str,
    observed_url: str,
) -> bool:

    expected_host = (
        urlparse(expected_url).hostname or ""
    ).lower()

    observed_host = (
        urlparse(observed_url).hostname or ""
    ).lower()

    if not expected_host or not observed_host:
        return False

    return (
        expected_host == observed_host
        or observed_host.endswith(
            "." + expected_host
        )
        or expected_host.endswith(
            "." + observed_host
        )
    )


def verify_open_website(
    tool_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Verify website navigation by inspecting the
    actual METHU-managed Chrome tab through CDP.
    """

    expected_url = tool_result.get("url")

    if not expected_url:
        return {
            "verified": False,
            "method": "cdp_page_state",
            "message": (
                "Tool result did not contain "
                "an expected URL."
            ),
        }

    observation = get_active_page_info()

    if not observation.get("success"):
        return {
            "verified": False,
            "method": "cdp_page_state",
            "message": (
                "Could not observe the METHU "
                "browser tab."
            ),
            "observed": observation,
        }

    observed_url = observation.get("url", "")
    observed_title = observation.get("title", "")

    host_matches = hosts_match(
        expected_url,
        observed_url,
    )

    verified = host_matches

    return {
        "verified": verified,
        "method": "cdp_page_state",
        "message": (
            f"Browser tab verified at {observed_url}."
            if verified
            else (
                "Browser tab did not match the "
                f"expected destination {expected_url}."
            )
        ),
        "observed": {
            "expected_url": expected_url,
            "actual_url": observed_url,
            "title": observed_title,
            "page_count": observation.get(
                "page_count"
            ),
            "host_matches": host_matches,
        },
    }


def verify_browser_search(
    tool_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Independently verify that a browser search reached
    the expected search-result state.

    The Browser Agent may already have verified the
    operation, but the main METHU graph does not trust
    that flag alone. It observes the browser again.
    """

    expected_query = tool_result.get("query")

    if not expected_query:
        return {
            "verified": False,
            "method": "browser_search_goal",
            "message": (
                "Browser search result did not contain "
                "the expected search query."
            ),
        }

    verification = verify_search_goal(
        expected_query
    )

    return {
        "verified": verification.get(
            "verified",
            False,
        ),
        "method": verification.get(
            "method",
            "browser_search_goal",
        ),
        "message": verification.get(
            "message",
            "Browser search verification failed.",
        ),
        "observed": verification.get(
            "observed",
            {},
        ),
    }


def verify_tool_result(
    tool_name: str | None,
    tool_result: Any,
) -> dict[str, Any]:

    if not tool_name:
        return {
            "verified": False,
            "method": "none",
            "message": (
                "No tool was available for verification."
            ),
        }

    if not isinstance(tool_result, dict):
        return {
            "verified": False,
            "method": "none",
            "message": (
                "Tool result could not be verified."
            ),
        }

    if tool_name == "open_app":
        return verify_open_app(
            tool_result
        )

    if tool_name == "open_website":
        return verify_open_website(
            tool_result
        )

    if tool_name == "browser_search":
        return verify_browser_search(
            tool_result
        )

    return {
        "verified": False,
        "method": "unsupported",
        "message": (
            f"Verification for '{tool_name}' "
            "is not implemented."
        ),
    }
