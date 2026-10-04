from backend.core.llm import llm
from backend.core.state import MethuState
from backend.tools.web.news import news_tool


def news_agent_node(state: MethuState) -> dict:
    """
    METHU News Agent.

    Searches live news, summarizes the retrieved results,
    and prepares structured data for the holographic UI.
    """

    user_input = state.get("user_input", "").strip()

    if not user_input:
        return {
            "status": "failed",
            "error": "No news request was provided.",
        }

    # --------------------------------------------------------
    # 1. Search live news
    # --------------------------------------------------------

    try:
        articles = news_tool.search(
            query=user_input,
            max_results=6,
        )

    except Exception as exc:
        return {
            "status": "failed",
            "error": f"News search failed: {exc}",
            "final_response": (
                "I couldn't retrieve live news right now."
            ),
            "ui_event": "methu_error",
            "ui_payload": {
                "type": "news",
                "error": str(exc),
            },
        }

    if not articles:
        return {
            "status": "completed",
            "final_response": (
                "I couldn't find any current articles for that request."
            ),
            "ui_event": "show_news_panel",
            "ui_payload": {
                "type": "news",
                "title": "METHU NEWS",
                "articles": [],
            },
        }

    # --------------------------------------------------------
    # 2. Prepare retrieved context
    # --------------------------------------------------------

    news_context = ""

    for index, article in enumerate(articles, start=1):
        news_context += f"""
ARTICLE {index}
Title: {article.get("title")}
Published: {article.get("published_date")}
URL: {article.get("url")}
Content: {article.get("content")}
"""

    # --------------------------------------------------------
    # 3. Let METHU summarize ONLY retrieved information
    # --------------------------------------------------------

    response = llm.invoke(
        [
            (
                "system",
                """
You are the News Agent inside METHU.

Summarize the live news results provided to you.

Rules:
- Use only the retrieved articles.
- Do not invent headlines or facts.
- Do not claim anything that is not supported by the results.
- Prefer recent and relevant developments.
- Keep the response concise and natural.
- Mention important companies, models, products or research when relevant.
- Do not fabricate publication dates.
- If results appear old or irrelevant, say so.
""",
            ),
            (
                "human",
                f"""
User request:

{user_input}

LIVE RETRIEVED NEWS:

{news_context}

Give the user a concise current-news briefing.
""",
            ),
        ]
    )

    # --------------------------------------------------------
    # 4. Build clean holographic UI data
    # --------------------------------------------------------

    ui_articles = []

    for article in articles:
        ui_articles.append(
            {
                "title": article.get("title"),
                "url": article.get("url"),
                "published_date": article.get("published_date"),
                "source_content": article.get("content"),
            }
        )

    # --------------------------------------------------------
    # 5. Return state update
    # --------------------------------------------------------

    return {
        "status": "completed",
        "final_response": response.content,

        "tool_name": "live_news_search",
        "tool_input": {
            "query": user_input,
        },
        "tool_result": articles,

        "ui_event": "show_news_panel",
        "ui_payload": {
            "type": "news",
            "title": "METHU NEWS",
            "summary": response.content,
            "articles": ui_articles,
        },
    }
