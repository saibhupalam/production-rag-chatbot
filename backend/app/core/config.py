from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional

# Search for .env in current working dir, parent dirs, or backend dir
ENV_PATHS = [
    Path(".env"),
    Path("backend/.env"),
    Path(__file__).resolve().parent.parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent.parent / ".env"
]
chosen_env_file = next((str(p) for p in ENV_PATHS if p.exists()), ".env")


class Settings(BaseSettings):
    PROJECT_NAME: str = "ContextIQ"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Relational Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "rag_chatbot"

    # Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "documents"

    # LLM Settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Security & JWT
    SECRET_KEY: str = "dev_secret_key_change_in_production_32bytes_min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Ingestion & Document Processing limits
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".txt"]

    # Advanced RAG Feature Toggles
    RAG_RETRIEVAL_LIMIT: int = 4
    RERANKING_ENABLED: bool = True
    SEMANTIC_CHUNKING_ENABLED: bool = True
    QUERY_REWRITE_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=chosen_env_file,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        encoded_password = quote_plus(str(self.POSTGRES_PASSWORD))
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{encoded_password}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()