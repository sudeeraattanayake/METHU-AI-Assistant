import os
import subprocess
from urllib.parse import urlparse

from backend.security.command_guard import command_guard


KNOWN_SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "linkedin": "https://www.linkedin.com",
}


def normalize_url(target: str) -> str | None:
    target = target.strip().lower()

    # Known friendly names
    if target in KNOWN_SITES:
        return KNOWN_SITES[target]

    # Only allow HTTP/HTTPS URLs
    if target.startswith(("https://", "http://")):
        parsed = urlparse(target)

        if parsed.scheme not in {"http", "https"}:
            return None

        if not parsed.netloc:
            return None

        return target

    return None


def get_chrome_path() -> str | None:
    possible_paths = [
        os.path.expandvars(
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
        ),
        os.path.expandvars(
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
        ),
        os.path.expandvars(
            r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
        ),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def navigate_to(target: str) -> dict:
    url = normalize_url(target)

    if not url:
        return {
            "success": False,
            "action": "open_website",
            "target": target,
            "error": "Invalid or unsupported website.",
        }

    tool_input = {
        "url": url,
    }

    authorization = command_guard.authorize(
        action="open_website",
        tool_input=tool_input,
    )

    if not authorization["authorized"]:
        return {
            "success": False,
            "action": "open_website",
            "url": url,
            "error": authorization["reason"],
        }

    chrome = get_chrome_path()

    if not chrome:
        return {
            "success": False,
            "action": "open_website",
            "url": url,
            "error": "Google Chrome could not be found.",
        }

    try:
        subprocess.Popen(
            [chrome, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return {
            "success": True,
            "action": "open_website",
            "url": url,
            "message": f"Opened {url} in Chrome.",
        }

    except Exception as exc:
        return {
            "success": False,
            "action": "open_website",
            "url": url,
            "error": str(exc),
        }
