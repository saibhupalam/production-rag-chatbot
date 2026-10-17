from typing import Any
from langchain_groq import ChatGroq
from app.core.config import settings


def get_llm() -> ChatGroq:
    """Return a configured ChatGroq client instance."""
    api_key = settings.GROQ_API_KEY if settings.GROQ_API_KEY else "gsk_placeholder_for_offline_dev"
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=api_key
    )


class _LazyLLM:
    """Lazy LLM proxy to avoid network or credential initialization overhead at module import."""
    _instance: Any = None

    def _get_inner(self):
        if self._instance is None:
            self._instance = get_llm()
        return self._instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_inner(), name)

    def invoke(self, *args, **kwargs):
        return self._get_inner().invoke(*args, **kwargs)


llm = _LazyLLM()