from typing import Any
from urllib.parse import urlparse

import httpx

from backend.tools.system.processes import is_app_running


def verify_open_app(
    tool_result: dict[str, Any],
) -> dict[str, Any]:

    app_name = tool_result.get("app")

    if not app_name:
        return {
            "verified": False,
            "method": "process_check",
            "message": "Tool result did not contain an app name.",
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


def verify_open_website(
    tool_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Verify that the destination website is reachable.

    IMPORTANT:
    This verifies the destination itself, not yet the
    active Chrome tab. Active-tab/DOM verification will
    later use Playwright or Chrome DevTools Protocol.
    """

    url = tool_result.get("url")

    if not url:
        return {
            "verified": False,
            "method": "http_reachability",
            "message": "Tool result did not contain a URL.",
        }

    try:
        response = httpx.get(
            url,
            timeout=10.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 METHU/"
                    "BrowserVerifier"
                )
            },
        )

        reachable = response.status_code < 500

        requested_host = (
            urlparse(url).hostname or ""
        ).lower()

        final_url = str(response.url)

        final_host = (
            urlparse(final_url).hostname or ""
        ).lower()

        host_matches = (
            requested_host == final_host
            or final_host.endswith(
                "." + requested_host
            )
            or requested_host.endswith(
                "." + final_host
            )
        )

        verified = reachable and host_matches

        return {
            "verified": verified,
            "method": "http_reachability",
            "message": (
                f"{url} is reachable."
                if verified
                else (
                    f"Could not verify destination "
                    f"{url}."
                )
            ),
            "observed": {
                "requested_url": url,
                "final_url": final_url,
                "status_code": response.status_code,
                "reachable": reachable,
                "host_matches": host_matches,
            },
        }

    except Exception as exc:
        return {
            "verified": False,
            "method": "http_reachability",
            "message": (
                f"Website verification failed: {exc}"
            ),
            "observed": {
                "requested_url": url,
                "reachable": False,
            },
        }


def verify_tool_result(
    tool_name: str | None,
    tool_result: Any,
) -> dict[str, Any]:

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
            "message": "Tool result could not be verified.",
        }

    if tool_name == "open_app":
        return verify_open_app(
            tool_result
        )

    if tool_name == "open_website":
        return verify_open_website(
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
