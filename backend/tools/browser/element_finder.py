from typing import Any

from backend.tools.browser.dom_observer import observe_dom


def _normalize(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in _normalize(value).split()
        if token
    }


def _score_element(
    element: dict[str, Any],
    query: str,
) -> int:
    """
    Score an interactive DOM element against a
    natural-language description.

    The scoring strongly rewards exact semantic matches
    and penalizes conflicting labels such as:

        query: "search button"
        element: aria-label="Clear search query"
    """

    query = _normalize(query)

    if not query:
        return 0

    query_tokens = _tokenize(query)

    tag = _normalize(element.get("tag"))
    role = _normalize(element.get("role"))
    element_type = _normalize(element.get("type"))
    text = _normalize(element.get("text"))
    aria_label = _normalize(element.get("aria_label"))
    placeholder = _normalize(element.get("placeholder"))
    name = _normalize(element.get("name"))
    element_id = _normalize(element.get("id"))

    score = 0

    # -------------------------------------------------
    # Exact matches
    # -------------------------------------------------

    if query == aria_label:
        score += 150

    if query == placeholder:
        score += 140

    if query == text:
        score += 130

    if query == name:
        score += 120

    if query == element_id:
        score += 110

    # -------------------------------------------------
    # Query concepts
    # -------------------------------------------------

    wants_button = "button" in query_tokens

    wants_textbox = bool(
        query_tokens
        & {
            "textbox",
            "input",
            "field",
            "box",
        }
    )

    wants_link = "link" in query_tokens

    wants_search = "search" in query_tokens

    # -------------------------------------------------
    # Element type matching
    # -------------------------------------------------

    if wants_button:
        if tag == "button":
            score += 70

        if role == "button":
            score += 70

        # Penalize inputs when explicitly asking
        # for a button.
        if tag in {"input", "textarea"}:
            score -= 60

    if wants_textbox:
        if tag in {"input", "textarea"}:
            score += 70

        if role in {
            "textbox",
            "searchbox",
            "combobox",
        }:
            score += 70

        if tag == "button":
            score -= 60

    if wants_link:
        if tag == "a":
            score += 70

        if role == "link":
            score += 70

    # -------------------------------------------------
    # Search semantics
    # -------------------------------------------------

    if wants_search:
        if aria_label == "search":
            score += 120

        elif "search" in aria_label:
            score += 35

        if placeholder == "search":
            score += 100

        elif "search" in placeholder:
            score += 30

        if name == "search_query":
            score += 90

        elif "search" in name:
            score += 30

        if text == "search":
            score += 100

    # -------------------------------------------------
    # Conflict penalties
    # -------------------------------------------------

    # YouTube example:
    # aria-label="Clear search query"
    #
    # This contains "search", but it is NOT the
    # requested Search button.
    conflict_words = {
        "clear",
        "close",
        "cancel",
        "delete",
        "remove",
        "reset",
    }

    element_tokens = _tokenize(
        " ".join(
            [
                text,
                aria_label,
                placeholder,
                name,
                element_id,
            ]
        )
    )

    conflicts = (
        conflict_words
        & element_tokens
    )

    if conflicts and not (
        conflicts & query_tokens
    ):
        score -= 150

    # -------------------------------------------------
    # Generic token overlap
    # -------------------------------------------------

    searchable_tokens = _tokenize(
        " ".join(
            [
                tag,
                role,
                element_type,
                text,
                aria_label,
                placeholder,
                name,
                element_id,
            ]
        )
    )

    overlap = (
        query_tokens
        & searchable_tokens
    )

    score += len(overlap) * 15

    return score


def _build_locator_hint(
    element: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a stable locator hint.

    Prefer semantic attributes rather than DOM index.
    """

    name = element.get("name")

    if name:
        return {
            "strategy": "name",
            "value": name,
        }

    aria_label = element.get(
        "aria_label"
    )

    if aria_label:
        return {
            "strategy": "aria_label",
            "value": aria_label,
        }

    placeholder = element.get(
        "placeholder"
    )

    if placeholder:
        return {
            "strategy": "placeholder",
            "value": placeholder,
        }

    element_id = element.get("id")

    if element_id:
        return {
            "strategy": "id",
            "value": element_id,
        }

    text = element.get("text")

    if text:
        return {
            "strategy": "text",
            "value": text,
        }

    return {
        "strategy": "index",
        "value": element.get("index"),
    }


def find_element(
    query: str,
    max_elements: int = 100,
) -> dict[str, Any]:

    if not query or not query.strip():
        return {
            "success": False,
            "message": (
                "Element query cannot be empty."
            ),
            "element": None,
            "locator": None,
        }

    observation = observe_dom(
        max_elements=max_elements
    )

    if not observation.get("success"):
        return {
            "success": False,
            "message": observation.get(
                "message",
                "DOM observation failed.",
            ),
            "element": None,
            "locator": None,
        }

    elements = observation.get(
        "elements",
        [],
    )

    if not elements:
        return {
            "success": False,
            "message": (
                "No visible interactive "
                "elements found."
            ),
            "element": None,
            "locator": None,
        }

    scored_elements = []

    for element in elements:

        score = _score_element(
            element,
            query,
        )

        if score > 0:
            scored_elements.append(
                {
                    "score": score,
                    "element": element,
                }
            )

    if not scored_elements:
        return {
            "success": False,
            "message": (
                f'No interactive element matched '
                f'"{query}".'
            ),
            "element": None,
            "locator": None,
        }

    scored_elements.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    best_match = scored_elements[0]

    element = best_match["element"]

    locator = _build_locator_hint(
        element
    )

    return {
        "success": True,
        "query": query,
        "score": best_match["score"],
        "page": observation.get("page"),
        "element": element,
        "locator": locator,
        "message": (
            f'Found an element matching '
            f'"{query}".'
        ),
    }
