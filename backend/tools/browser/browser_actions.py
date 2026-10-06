from typing import Any

from playwright.sync_api import sync_playwright

from backend.security.command_guard import command_guard
from backend.tools.browser.element_finder import find_element
from backend.tools.browser.playwright_controller import (
    CDP_URL,
    is_cdp_ready,
)


def _resolve_locator(page, locator_hint: dict[str, Any]):
    """
    Convert METHU's semantic locator hint into
    a Playwright locator.
    """

    strategy = locator_hint.get("strategy")
    value = locator_hint.get("value")

    if strategy == "name":
        return page.locator(
            f'[name="{value}"]'
        ).first

    if strategy == "aria_label":
        return page.get_by_label(
            value,
            exact=True,
        ).first

    if strategy == "placeholder":
        return page.get_by_placeholder(
            value,
            exact=True,
        ).first

    if strategy == "id":
        return page.locator(
            f'#{value}'
        ).first

    if strategy == "text":
        return page.get_by_text(
            value,
            exact=True,
        ).first

    raise ValueError(
        f"Unsupported locator strategy: {strategy}"
    )


def type_into_element(
    element_query: str,
    text: str,
    approval_id: str | None = None,
) -> dict[str, Any]:
    """
    Find an input semantically, type text into it,
    then read the value back from the real DOM
    to verify the action.

    This does NOT submit the form.
    """

    if not element_query.strip():
        return {
            "success": False,
            "verified": False,
            "message": "Element query cannot be empty.",
        }

    if not text:
        return {
            "success": False,
            "verified": False,
            "message": "Text cannot be empty.",
        }

    # -------------------------------------------------
    # 1. Make sure METHU browser exists
    # -------------------------------------------------

    if not is_cdp_ready():
        return {
            "success": False,
            "verified": False,
            "message": (
                "METHU managed Chrome is not running."
            ),
        }

    # -------------------------------------------------
    # 2. Observe + semantically find target
    # -------------------------------------------------

    find_result = find_element(
        element_query
    )

    if not find_result.get("success"):
        return {
            "success": False,
            "verified": False,
            "message": find_result.get(
                "message",
                "Could not find target element.",
            ),
        }

    locator_hint = find_result.get(
        "locator"
    )

    if not locator_hint:
        return {
            "success": False,
            "verified": False,
            "message": (
                "Element was found but no locator "
                "could be generated."
            ),
        }

    # -------------------------------------------------
    # 3. Security authorization
    # -------------------------------------------------

    tool_input = {
        "element_query": element_query,
        "text": text,
    }

    authorization = command_guard.authorize(
        action="type_text",
        tool_input=tool_input,
        approval_id=approval_id,
    )

    if not authorization["authorized"]:
        return {
            "success": False,
            "verified": False,
            "action": "type_text",
            "message": authorization["reason"],
            "authorization": authorization,
        }

    # -------------------------------------------------
    # 4. Connect to real METHU browser
    # -------------------------------------------------

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
                    "verified": False,
                    "message": (
                        "No browser context found."
                    ),
                }

            context = contexts[0]
            pages = context.pages

            if not pages:
                return {
                    "success": False,
                    "verified": False,
                    "message": (
                        "No browser page found."
                    ),
                }

            page = pages[-1]

            # -----------------------------------------
            # 5. Resolve semantic locator
            # -----------------------------------------

            locator = _resolve_locator(
                page,
                locator_hint,
            )

            if locator.count() == 0:
                return {
                    "success": False,
                    "verified": False,
                    "message": (
                        "Target element disappeared "
                        "before typing."
                    ),
                }

            # -----------------------------------------
            # 6. Type into real DOM element
            # -----------------------------------------

            locator.fill(text)

            page.wait_for_timeout(300)

            # -----------------------------------------
            # 7. Observe actual DOM value
            # -----------------------------------------

            observed_value = locator.input_value()

            # -----------------------------------------
            # 8. Verify postcondition
            # -----------------------------------------

            verified = observed_value == text

            return {
                "success": verified,
                "verified": verified,
                "action": "type_text",
                "element_query": element_query,
                "requested_text": text,
                "observed_value": observed_value,
                "locator": locator_hint,
                "page": {
                    "url": page.url,
                    "title": page.title(),
                },
                "authorization": authorization,
                "message": (
                    "Text was typed and verified."
                    if verified
                    else
                    "Typing completed but verification failed."
                ),
            }

    except Exception as exc:
        return {
            "success": False,
            "verified": False,
            "action": "type_text",
            "message": (
                f"Browser typing failed: {exc}"
            ),
        }


def click_element(
    element_query: str,
    approval_id: str | None = None,
    wait_after_click_ms: int = 1500,
) -> dict[str, Any]:
    """
    Find an interactive element semantically,
    authorize the action,
    click it,
    then observe the resulting browser state.

    This function does not yet decide whether the
    resulting page semantically satisfies the user's
    complete goal. That verification layer comes next.
    """

    if not element_query.strip():
        return {
            "success": False,
            "verified": False,
            "message": "Element query cannot be empty.",
        }

    # -------------------------------------------------
    # 1. Ensure METHU managed Chrome exists
    # -------------------------------------------------

    if not is_cdp_ready():
        return {
            "success": False,
            "verified": False,
            "message": "METHU managed Chrome is not running.",
        }

    # -------------------------------------------------
    # 2. Observe + semantically find target
    # -------------------------------------------------

    find_result = find_element(element_query)

    if not find_result.get("success"):
        return {
            "success": False,
            "verified": False,
            "message": find_result.get(
                "message",
                "Could not find target element.",
            ),
        }

    locator_hint = find_result.get("locator")

    if not locator_hint:
        return {
            "success": False,
            "verified": False,
            "message": (
                "Element was found but no locator "
                "could be generated."
            ),
        }

    # -------------------------------------------------
    # 3. CommandGuard authorization
    # -------------------------------------------------

    tool_input = {
        "element_query": element_query,
    }

    authorization = command_guard.authorize(
        action="click_element",
        tool_input=tool_input,
        approval_id=approval_id,
    )

    if not authorization["authorized"]:
        return {
            "success": False,
            "verified": False,
            "action": "click_element",
            "message": authorization["reason"],
            "authorization": authorization,
        }

    # -------------------------------------------------
    # 4. Connect to actual managed Chrome
    # -------------------------------------------------

    try:
        with sync_playwright() as playwright:

            browser = playwright.chromium.connect_over_cdp(
                CDP_URL
            )

            contexts = browser.contexts

            if not contexts:
                return {
                    "success": False,
                    "verified": False,
                    "message": "No browser context found.",
                }

            context = contexts[0]
            pages = context.pages

            if not pages:
                return {
                    "success": False,
                    "verified": False,
                    "message": "No browser page found.",
                }

            page = pages[-1]

            # Capture state before click.
            before_url = page.url
            before_title = page.title()

            # -------------------------------------------------
            # 5. Resolve locator
            # -------------------------------------------------

            locator = _resolve_locator(
                page,
                locator_hint,
            )

            if locator.count() == 0:
                return {
                    "success": False,
                    "verified": False,
                    "message": (
                        "Target element disappeared "
                        "before clicking."
                    ),
                }

            if not locator.is_visible():
                return {
                    "success": False,
                    "verified": False,
                    "message": (
                        "Target element is not visible."
                    ),
                }

            # -------------------------------------------------
            # 6. Perform click
            # -------------------------------------------------

            locator.click(
                timeout=10000
            )

            page.wait_for_timeout(
                wait_after_click_ms
            )

            # -------------------------------------------------
            # 7. Observe actual state after click
            # -------------------------------------------------

            after_url = page.url
            after_title = page.title()

            url_changed = (
                after_url != before_url
            )

            title_changed = (
                after_title != before_title
            )

            # The click itself completed successfully.
            # We record evidence rather than pretending
            # every click must cause navigation.
            verified = True

            return {
                "success": True,
                "verified": verified,
                "action": "click_element",
                "element_query": element_query,
                "locator": locator_hint,
                "before": {
                    "url": before_url,
                    "title": before_title,
                },
                "after": {
                    "url": after_url,
                    "title": after_title,
                },
                "observed": {
                    "url_changed": url_changed,
                    "title_changed": title_changed,
                },
                "authorization": authorization,
                "message": (
                    "Element was clicked and browser "
                    "state was observed."
                ),
            }

    except Exception as exc:
        return {
            "success": False,
            "verified": False,
            "action": "click_element",
            "message": (
                f"Browser click failed: {exc}"
            ),
        }
