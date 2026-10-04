import os
import shutil
import subprocess
from typing import Any

from backend.security.command_guard import command_guard


# Applications METHU may open automatically.
APP_ALLOWLIST = {
    "chrome": {
        "executables": ["chrome.exe", "chrome"],
    },
    "vscode": {
        "executables": ["code.cmd", "code.exe", "code"],
    },
    "notepad": {
        "executables": ["notepad.exe"],
    },
    "calculator": {
        "executables": ["calc.exe"],
    },
    "explorer": {
        "executables": ["explorer.exe"],
    },
}


def _find_executable(app_name: str) -> str | None:
    config = APP_ALLOWLIST.get(app_name)

    if not config:
        return None

    for executable in config["executables"]:
        path = shutil.which(executable)

        if path:
            return path

    # Common Chrome locations on Windows
    if app_name == "chrome":
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


def open_app(
    app_name: str,
    approval_id: str | None = None,
) -> dict[str, Any]:
    """
    Safely open an allowlisted Windows application.
    """

    normalized_name = app_name.strip().lower()

    # Never allow arbitrary executable names.
    if normalized_name not in APP_ALLOWLIST:
        return {
            "success": False,
            "action": "open_app",
            "app": normalized_name,
            "error": "Application is not in the METHU allowlist.",
        }

    tool_input = {
        "app": normalized_name,
    }

    authorization = command_guard.authorize(
        action="open_app",
        tool_input=tool_input,
        approval_id=approval_id,
    )

    if not authorization["authorized"]:
        return {
            "success": False,
            "action": "open_app",
            "app": normalized_name,
            "error": authorization["reason"],
            "authorization": authorization,
        }

    executable = _find_executable(normalized_name)

    if not executable:
        return {
            "success": False,
            "action": "open_app",
            "app": normalized_name,
            "error": "Application executable could not be found.",
        }

    try:
        subprocess.Popen(
            [executable],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return {
            "success": True,
            "action": "open_app",
            "app": normalized_name,
            "executable": executable,
            "message": f"{normalized_name} launch command executed.",
        }

    except Exception as exc:
        return {
            "success": False,
            "action": "open_app",
            "app": normalized_name,
            "error": str(exc),
        }
