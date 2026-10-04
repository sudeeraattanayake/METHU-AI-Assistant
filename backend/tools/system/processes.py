import subprocess


PROCESS_NAMES = {
    "chrome": "chrome.exe",
    "vscode": "Code.exe",
    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
    "explorer": "explorer.exe",
}


def get_running_processes() -> list[str]:
    """
    Return running Windows executable names.
    """

    try:
        result = subprocess.run(
            [
                "tasklist",
                "/FO",
                "CSV",
                "/NH",
            ],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        processes = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line:
                continue

            # tasklist CSV:
            # "chrome.exe","1234","Console",...
            if line.startswith('"'):
                process_name = line.split('","', 1)[0]
                process_name = process_name.strip('"')

                processes.append(process_name.lower())

        return processes

    except Exception:
        return []


def is_process_running(process_name: str) -> bool:
    """
    Check whether a Windows process is currently running.
    """

    process_name = process_name.strip().lower()

    return process_name in get_running_processes()


def is_app_running(app_name: str) -> bool:
    """
    Convert a METHU application name into its Windows process
    name and determine whether it is running.
    """

    normalized = app_name.strip().lower()

    process_name = PROCESS_NAMES.get(normalized)

    if not process_name:
        return False

    return is_process_running(process_name)
