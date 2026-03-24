import logging
import os
from typing import Any

import uvicorn
from mcp.server.fastmcp import FastMCP

from runtime.models import (
    HrRagSearchOutput,
    PersonalDayItem,
    RagDocumentResult,
    ToolResponse,
    VacationDatesRecord,
    VacationDaysRecord,
)
from tools.rag import rag_search
from tools.zup_1c import (
    get_personal_days,
    get_plan_vacation,
    get_remaining_vacation_days,
)

logger = logging.getLogger(__name__)

MCP_PORT = int(os.getenv("MCP_PORT", "8050"))

mcp = FastMCP(
    name="HR MCP Server",
    json_response=True,
    host="0.0.0.0",
    port=MCP_PORT,
)


def _extract_error_message(raw: Any) -> str | None:
    """Попытаться вытащить бизнес-ошибку из ответа внешней системы."""
    if isinstance(raw, dict):
        for key in ("message", "error", "detail", "details", "description"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(raw, list) and raw:
        first = raw[0]
        if isinstance(first, dict):
            return _extract_error_message(first)
    return None


def _classify_empty_result(message: str | None) -> tuple[str, str]:
    """Определить статус пустого результата по сообщению внешней системы."""
    normalized = (message or "").strip().lower()
    if any(token in normalized for token in ("не найден", "not found", "unknown login")):
        return "not_found", message or "Пользователь не найден."
    if any(
        token in normalized
        for token in ("нет подчин", "no subordinates", "не является руководителем")
    ):
        return "no_data", message or "У пользователя нет подчинённых."
    if message:
        return "no_data", message
    return "no_data", "Данные не найдены."


def _normalize_personal_days(raw: Any) -> ToolResponse[PersonalDayItem]:
    if isinstance(raw, dict) and {"fio", "RemainsPersonalDays", "FuturePersonalDays"} <= raw.keys():
        return ToolResponse(
            status="ok",
            message="Персональные дни успешно получены.",
            data=PersonalDayItem(**raw),
        )

    error_message = _extract_error_message(raw)
    status, message = _classify_empty_result(error_message)
    return ToolResponse(status=status, message=message, data=None)


def _normalize_collection_result(
    raw: Any,
    model: type[VacationDaysRecord] | type[VacationDatesRecord],
    success_message: str,
) -> ToolResponse[list[Any]]:
    if isinstance(raw, list):
        valid_items = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                valid_items.append(model(**item))
            except Exception:
                continue
        if valid_items:
            return ToolResponse(status="ok", message=success_message, data=valid_items)

    error_message = _extract_error_message(raw)
    status, message = _classify_empty_result(error_message)
    return ToolResponse(status=status, message=message, data=[])


@mcp.tool()
def hr_rag_search(query: str, n_results: str) -> HrRagSearchOutput:
    """
    Поиск по HR-документам и политикам с помощью RAG (Retrieval Augmented Generation).
    """
    results = rag_search(query=query, n_results=int(n_results))
    return HrRagSearchOutput(
        query=query,
        results=[RagDocumentResult(**r) for r in results],
    )


@mcp.tool()
def get_personal_days_tool(login: str) -> ToolResponse[PersonalDayItem]:
    """
    Получить персональные дни сотрудника.
    """
    try:
        data = get_personal_days(login=login)
        return _normalize_personal_days(data)
    except Exception as exc:
        logger.exception("Ошибка при получении персональных дней для login=%s", login)
        return ToolResponse(
            status="system_error",
            message=f"Не удалось получить персональные дни: {exc}",
            data=None,
        )


@mcp.tool()
def get_remaining_vacation_days_tool(login: str) -> ToolResponse[list[VacationDaysRecord]]:
    """
    Получить оставшиеся дни отпуска сотрудника за текущий год.
    """
    try:
        data = get_remaining_vacation_days(login=login)
        return _normalize_collection_result(
            raw=data,
            model=VacationDaysRecord,
            success_message="Данные по остаткам отпуска успешно получены.",
        )
    except Exception as exc:
        logger.exception("Ошибка при получении остатков отпуска для login=%s", login)
        return ToolResponse(
            status="system_error",
            message=f"Не удалось получить данные по отпуску: {exc}",
            data=[],
        )


@mcp.tool()
def get_plan_vacation_tool(login: str) -> ToolResponse[list[VacationDatesRecord]]:
    """
    Получить план-график отпусков сотрудника за текущий год.
    """
    try:
        data = get_plan_vacation(login=login)
        return _normalize_collection_result(
            raw=data,
            model=VacationDatesRecord,
            success_message="План отпусков успешно получен.",
        )
    except Exception as exc:
        logger.exception("Ошибка при получении плана отпусков для login=%s", login)
        return ToolResponse(
            status="system_error",
            message=f"Не удалось получить план отпусков: {exc}",
            data=[],
        )


def main():
    """Точка входа для запуска сервера."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest

    class TraceContextMiddleware(BaseHTTPMiddleware):
        """Прокидывает traceparent из входящего MCP-запроса в текущий контекст."""

        async def dispatch(self, request: StarletteRequest, call_next):
            try:
                from opentelemetry import context as otel_context
                from opentelemetry.propagate import extract

                ctx = extract(dict(request.headers))
                token = otel_context.attach(ctx)
                try:
                    return await call_next(request)
                finally:
                    otel_context.detach(token)
            except Exception:
                return await call_next(request)

    app = mcp.streamable_http_app()
    app.add_middleware(TraceContextMiddleware)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=MCP_PORT,
        ws="none",
        log_level="info",
    )


if __name__ == "__main__":
    main()
