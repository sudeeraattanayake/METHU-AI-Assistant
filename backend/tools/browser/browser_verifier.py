from typing import Any
from urllib.parse import urlparse, parse_qs, unquote_plus

from backend.tools.browser.playwright_controller import (
    get_active_page_info,
)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(
        value.strip().lower().split()
    )


def verify_search_goal(
    expected_query: str,
) -> dict[str, Any]:
    """
    Verify that the METHU-managed browser reached
    a search-results state for the expected query.

    Evidence can include:
    - search_query URL parameter
    - browser title

    This function is read-only.
    """

    if not expected_query.strip():
        return {
            "verified": False,
            "method": "browser_search_goal",
            "message": "Expected search query is empty.",
            "observed": {},
        }

    # -------------------------------------------------
    # 1. Observe actual managed browser
    # -------------------------------------------------

    observation = get_active_page_info()

    if not observation.get("success"):
        return {
            "verified": False,
            "method": "browser_search_goal",
            "message": observation.get(
                "message",
                "Could not observe browser.",
            ),
            "observed": observation,
        }

    actual_url = observation.get("url", "")
    actual_title = observation.get("title", "")

    expected_normalized = _normalize_text(
        expected_query
    )

    # -------------------------------------------------
    # 2. Extract search query from URL
    # -------------------------------------------------

    parsed_url = urlparse(actual_url)

    query_parameters = parse_qs(
        parsed_url.query
    )

    url_query = ""

    search_values = query_parameters.get(
        "search_query"
    )

    if search_values:
        url_query = unquote_plus(
            search_values[0]
        )

    url_query_normalized = _normalize_text(
        url_query
    )

    title_normalized = _normalize_text(
        actual_title
    )

    # -------------------------------------------------
    # 3. Compare expected goal with observed state
    # -------------------------------------------------

    url_matches = (
        bool(url_query_normalized)
        and url_query_normalized
        == expected_normalized
    )

    title_matches = (
        bool(title_normalized)
        and expected_normalized
        in title_normalized
    )

    # Strong verification:
    #
    # For YouTube-style search pages, the URL query
    # should exactly match what METHU intended.
    verified = url_matches

    return {
        "verified": verified,
        "method": "browser_search_goal",
        "message": (
            f'Search goal verified for "{expected_query}".'
            if verified
            else
            f'Search goal verification failed for '
            f'"{expected_query}".'
        ),
        "observed": {
            "expected_query": expected_query,
            "actual_url": actual_url,
            "actual_title": actual_title,
            "url_query": url_query,
            "url_matches": url_matches,
            "title_matches": title_matches,
        },
    }
