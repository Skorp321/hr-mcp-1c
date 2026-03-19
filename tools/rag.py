"""RAG (Retrieval Augmented Generation) модуль для HR-документов."""

import os
import logging

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_HR_AGENT_URL: str = os.getenv("HR_AGENT_URL", "http://localhost:8000")


def rag_search(query: str, n_results: int = 5) -> list[dict]:
    """
    Поиск по HR-документам через /api/similarity endpoint hr-agent.

    Args:
        query: Поисковый запрос
        n_results: Количество возвращаемых документов (по умолчанию 5)

    Returns:
        Список найденных документов: [{"text", "relevance", "topic"}, ...]
    """
    try:
        url = f"{_HR_AGENT_URL}/api/similarity"
        payload = {"query": query, "top_k": n_results}
        # Пробрасываем W3C traceparent из текущего OTel контекста (установленного
        # TraceContextMiddleware) в заголовки запроса — без создания лишних spans.
        headers: dict[str, str] = {}
        try:
            from opentelemetry.propagate import inject as otel_inject
            otel_inject(headers)
        except Exception:
            pass
        response = requests.post(url, json=payload, timeout=30, headers=headers)
        response.raise_for_status()
        data = response.json()
        return [
            {
                "text": source["content"],
                "relevance": source["score"],
                "topic": source["title"],
            }
            for source in data.get("results", [])
        ]
    except Exception as e:
        logger.error(f"Ошибка при поиске через hr-agent /api/similarity: {e}")
        return []
