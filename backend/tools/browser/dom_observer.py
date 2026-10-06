from typing import Any

from playwright.sync_api import sync_playwright

from backend.tools.browser.playwright_controller import (
    CDP_URL,
    is_cdp_ready,
)


def observe_dom(
    max_elements: int = 100,
) -> dict[str, Any]:
    """
    Observe interactive DOM elements in METHU's managed browser.

    This function is READ-ONLY.

    It does not:
    - click
    - type
    - submit forms
    - modify the page

    It extracts useful information about interactive elements
    so METHU can understand the current webpage.
    """

    if not is_cdp_ready():
        return {
            "success": False,
            "message": "METHU managed Chrome is not running.",
            "page": None,
            "elements": [],
        }

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(
                CDP_URL
            )

            contexts = browser.contexts

            if not contexts:
                return {
                    "success": False,
                    "message": "No browser context found.",
                    "page": None,
                    "elements": [],
                }

            context = contexts[0]
            pages = context.pages

            if not pages:
                return {
                    "success": False,
                    "message": "No browser page found.",
                    "page": None,
                    "elements": [],
                }

            # For now METHU observes the newest managed page.
            page = pages[-1]

            raw_elements = page.locator(
                """
                a,
                button,
                input,
                textarea,
                select,
                [role="button"],
                [role="link"],
                [role="textbox"],
                [role="searchbox"],
                [role="combobox"],
                [contenteditable="true"]
                """
            )

            count = raw_elements.count()

            elements: list[dict[str, Any]] = []

            limit = min(count, max_elements)

            for index in range(limit):
                element = raw_elements.nth(index)

                try:
                    if not element.is_visible():
                        continue

                    tag = element.evaluate(
                        "(el) => el.tagName.toLowerCase()"
                    )

                    role = element.get_attribute("role")

                    element_type = element.get_attribute("type")

                    placeholder = element.get_attribute(
                        "placeholder"
                    )

                    aria_label = element.get_attribute(
                        "aria-label"
                    )

                    name = element.get_attribute("name")

                    element_id = element.get_attribute("id")

                    href = element.get_attribute("href")

                    text = ""

                    try:
                        text = element.inner_text(
                            timeout=1000
                        ).strip()
                    except Exception:
                        pass

                    # Prevent huge text blocks.
                    if len(text) > 200:
                        text = text[:200]

                    elements.append(
                        {
                            "index": index,
                            "tag": tag,
                            "role": role,
                            "type": element_type,
                            "text": text,
                            "aria_label": aria_label,
                            "placeholder": placeholder,
                            "name": name,
                            "id": element_id,
                            "href": href,
                        }
                    )

                except Exception:
                    # DOMs can change while being observed.
                    # Skip elements that disappear during inspection.
                    continue

            return {
                "success": True,
                "page": {
                    "url": page.url,
                    "title": page.title(),
                },
                "element_count": len(elements),
                "elements": elements,
                "message": (
                    f"Observed {len(elements)} visible "
                    f"interactive elements."
                ),
            }

    except Exception as exc:
        return {
            "success": False,
            "message": f"DOM observation failed: {exc}",
            "page": None,
            "elements": [],
        }
