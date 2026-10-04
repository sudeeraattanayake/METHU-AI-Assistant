from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # AI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5-mini"

    # LangSmith
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_TRACING: bool = True
    LANGSMITH_PROJECT: str = "METHU"

    # Web Search
    TAVILY_API_KEY: str | None = None

    # Application
    METHU_ENV: str = "development"
    METHU_DEBUG: bool = True

    # Server
    METHU_HOST: str = "127.0.0.1"
    METHU_PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./data/memory/methu.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
