from typing import Any

from backend.tools.browser.dom_observer import observe_dom


def _normalize(value: Any) -> str:
    """
    Convert a DOM value into normalized lowercase text
    for semantic matching.
    """

    if value is None:
        return ""

    return str(value).strip().lower()


def _score_element(
    element: dict[str, Any],
    query: str,
) -> int:
    """
    Score how closely an interactive DOM element
    matches a natural-language query.
    """

    query = _normalize(query)

    if not query:
        return 0

    score = 0

    tag = _normalize(element.get("tag"))
    role = _normalize(element.get("role"))
    element_type = _normalize(element.get("type"))
    text = _normalize(element.get("text"))
    aria_label = _normalize(element.get("aria_label"))
    placeholder = _normalize(element.get("placeholder"))
    name = _normalize(element.get("name"))
    element_id = _normalize(element.get("id"))

    # ---------------------------------------------
    # Strong exact semantic matches
    # ---------------------------------------------

    if query == aria_label:
        score += 100

    if query == placeholder:
        score += 95

    if query == text:
        score += 90

    if query == name:
        score += 85

    if query == element_id:
        score += 80

    # ---------------------------------------------
    # Partial matches
    # ---------------------------------------------

    if query in aria_label and aria_label:
        score += 50

    if query in placeholder and placeholder:
        score += 45

    if query in text and text:
        score += 40

    if query in name and name:
        score += 35

    if query in element_id and element_id:
        score += 30

    # ---------------------------------------------
    # Token matching
    # Example:
    # "search textbox"
    # ---------------------------------------------

    query_tokens = set(query.split())

    searchable_text = " ".join(
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

    for token in query_tokens:
        if token and token in searchable_text:
            score += 10

    # ---------------------------------------------
    # Semantic aliases
    # ---------------------------------------------

    textbox_words = {
        "textbox",
        "input",
        "field",
        "box",
    }

    button_words = {
        "button",
        "submit",
    }

    link_words = {
        "link",
    }

    if query_tokens & textbox_words:
        if tag in {"input", "textarea"}:
            score += 35

        if role in {
            "textbox",
            "searchbox",
            "combobox",
        }:
            score += 35

    if query_tokens & button_words:
        if tag == "button":
            score += 35

        if role == "button":
            score += 35

    if query_tokens & link_words:
        if tag == "a":
            score += 35

        if role == "link":
            score += 35

    # Search-specific bonus
    if "search" in query_tokens:
        if "search" in placeholder:
            score += 40

        if "search" in aria_label:
            score += 40

        if "search" in name:
            score += 30

    return score


def _build_locator_hint(
    element: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a stable locator hint.

    Priority:
    name -> aria-label -> placeholder -> id -> text

    We intentionally do not rely primarily on DOM index.
    """

    name = element.get("name")

    if name:
        return {
            "strategy": "name",
            "value": name,
        }

    aria_label = element.get("aria_label")

    if aria_label:
        return {
            "strategy": "aria_label",
            "value": aria_label,
        }

    placeholder = element.get("placeholder")

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
    """
    Find the interactive DOM element that best matches
    a natural-language description.

    Examples:

        find_element("search textbox")

        find_element("search button")

        find_element("sign in link")
    """

    if not query or not query.strip():
        return {
            "success": False,
            "message": "Element query cannot be empty.",
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
                "No visible interactive elements found."
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
                f'No interactive element matched "{query}".'
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
            f'Found an element matching "{query}".'
        ),
    }
