import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
from playwright.sync_api import sync_playwright

from backend.tools.browser.navigation import get_chrome_path


CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
CDP_URL = f"http://{CDP_HOST}:{CDP_PORT}"

PROJECT_ROOT = Path(__file__).resolve().parents[3]

METHU_BROWSER_PROFILE = (
    PROJECT_ROOT
    / "data"
    / "browser_profile"
)


def is_cdp_ready() -> bool:
    """
    Check whether METHU's managed Chrome
    debugging endpoint is available.
    """

    try:
        response = httpx.get(
            f"{CDP_URL}/json/version",
            timeout=2.0,
        )

        return response.status_code == 200

    except Exception:
        return False


def start_managed_chrome() -> dict[str, Any]:
    """
    Start a dedicated Chrome instance for METHU.

    This Chrome uses:
    - a dedicated METHU profile
    - Chrome DevTools Protocol
    - remote debugging on port 9222
    """

    if is_cdp_ready():
        return {
            "success": True,
            "already_running": True,
            "cdp_url": CDP_URL,
            "message": (
                "METHU managed Chrome is already running."
            ),
        }

    chrome_path = get_chrome_path()

    if not chrome_path:
        return {
            "success": False,
            "message": (
                "Google Chrome executable "
                "could not be found."
            ),
        }

    METHU_BROWSER_PROFILE.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        chrome_path,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={str(METHU_BROWSER_PROFILE)}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ]

    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except Exception as exc:
        return {
            "success": False,
            "message": (
                f"Could not start managed Chrome: {exc}"
            ),
        }

    # Wait up to ~10 seconds for Chrome CDP.
    for _ in range(20):

        if is_cdp_ready():
            return {
                "success": True,
                "already_running": False,
                "cdp_url": CDP_URL,
                "message": (
                    "METHU managed Chrome started."
                ),
            }

        time.sleep(0.5)

    return {
        "success": False,
        "message": (
            "Chrome started but the CDP endpoint "
            "did not become available."
        ),
    }


def get_active_page_info() -> dict[str, Any]:
    """
    Connect to the real METHU-controlled Chrome
    instance and observe its current page.
    """

    if not is_cdp_ready():
        return {
            "success": False,
            "message": (
                "METHU managed Chrome is not running."
            ),
        }

    try:
        with sync_playwright() as playwright:

            browser = (
                playwright.chromium.connect_over_cdp(
                    CDP_URL
                )
            )

            contexts = browser.contexts

            if not contexts:
                return {
                    "success": False,
                    "message": (
                        "No Chrome browser context found."
                    ),
                }

            context = contexts[0]

            pages = context.pages

            if not pages:
                return {
                    "success": False,
                    "message": (
                        "No browser pages found."
                    ),
                }

            # For now, use the newest tab.
            page = pages[-1]

            title = page.title()

            return {
                "success": True,
                "url": page.url,
                "title": title,
                "page_count": len(pages),
                "message": (
                    "Browser page observed successfully."
                ),
            }

    except Exception as exc:
        return {
            "success": False,
            "message": (
                f"Browser observation failed: {exc}"
            ),
        }


def navigate_managed_browser(url: str) -> dict[str, Any]:
    """
    Navigate the METHU-managed Chrome tab
    and observe the resulting browser state.
    """

    if not is_cdp_ready():
        start_result = start_managed_chrome()

        if not start_result.get("success"):
            return start_result

    try:
        with sync_playwright() as playwright:

            browser = playwright.chromium.connect_over_cdp(
                CDP_URL
            )

            contexts = browser.contexts

            if not contexts:
                return {
                    "success": False,
                    "message": "No Chrome browser context found.",
                }

            context = contexts[0]
            pages = context.pages

            if pages:
                page = pages[-1]
            else:
                page = context.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            page.wait_for_timeout(1000)

            return {
                "success": True,
                "action": "navigate_managed_browser",
                "requested_url": url,
                "url": page.url,
                "title": page.title(),
                "page_count": len(context.pages),
                "message": (
                    f"METHU navigated the managed browser to {url}."
                ),
            }

    except Exception as exc:
        return {
            "success": False,
            "message": f"Browser navigation failed: {exc}",
        }
