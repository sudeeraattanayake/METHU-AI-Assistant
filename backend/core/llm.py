from langchain_openai import ChatOpenAI

from backend.core.config import settings


def create_llm(
    model: str | None = None,
    temperature: float = 0.2,
) -> ChatOpenAI:
    """
    Create an OpenAI chat model for METHU.

    A different model can be supplied by individual agents later.
    """

    return ChatOpenAI(
        model=model or settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=temperature,
    )


# Default METHU model
llm = create_llm()
