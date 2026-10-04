from typing import Any

from tavily import TavilyClient

from backend.core.config import settings


class MethuNewsTool:
    """
    Live web/news search tool for METHU.
    """

    def __init__(self):
        if not settings.TAVILY_API_KEY:
            raise ValueError(
                "TAVILY_API_KEY is missing. Add it to your .env file."
            )

        self.client = TavilyClient(
            api_key=settings.TAVILY_API_KEY
        )

    def search(
        self,
        query: str,
        max_results: int = 6,
    ) -> list[dict[str, Any]]:

        response = self.client.search(
            query=query,
            topic="news",
            search_depth="advanced",
            max_results=max_results,
        )

        articles = []

        for result in response.get("results", []):
            articles.append(
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": result.get("content"),
                    "score": result.get("score"),
                    "published_date": result.get("published_date"),
                }
            )

        return articles


news_tool = MethuNewsTool()
