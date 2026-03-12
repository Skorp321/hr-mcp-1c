"""
ReAct агент (LangChain + LangGraph) с инструментами из hr-mcp-1c через fastmcp.

Инструменты запрашиваются из MCP-сервера динамически через list_tools().
LLM выбирает КАКОЙ инструмент вызвать, но "служебные" параметры
(login, n_results и т.д.) подставляются ПРОГРАММНО в момент вызова.
"""

import asyncio
import json
from typing import Any, Callable

from fastmcp import Client
from pydantic import BaseModel, Field, create_model
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# ── Конфигурация ──────────────────────────────────────────────────────────────

MCP_SERVER_URL = "http://localhost:8000/mcp"

# Контекст текущего пользователя — задаётся программно (из сессии / токена)
CURRENT_USER_CONTEXT = {
    "login": "ivanov",
}

# Параметры, которые НИКОГДА не идут от LLM — подставляются здесь
# Ключ — имя параметра в схеме MCP-инструмента
# Значение — callable, вызываемый в момент передачи вызова на сервер
PARAM_INJECTORS: dict[str, Callable[[], Any]] = {
    "login":     lambda: CURRENT_USER_CONTEXT["login"],
    "n_results": lambda: str(5),
}


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _run(coro: Any) -> Any:
    """Запускает корутину синхронно из синхронного контекста."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _call_mcp(tool_name: str, arguments: dict[str, Any]) -> str:
    """Открывает соединение с MCP-сервером и вызывает инструмент."""
    async with Client(MCP_SERVER_URL) as client:
        result = await client.call_tool(tool_name, arguments)
    parts = []
    for block in result:
        if hasattr(block, "text"):
            parts.append(block.text)
        elif hasattr(block, "model_dump"):
            parts.append(json.dumps(block.model_dump(), ensure_ascii=False))
        else:
            parts.append(str(block))
    return "\n".join(parts)


# ── Динамическое создание инструментов из MCP ────────────────────────────────

_JSON_TYPE_MAP: dict[str, type] = {
    "string":  str,
    "integer": int,
    "number":  float,
    "boolean": bool,
    "array":   list,
    "object":  dict,
}


def _build_args_model(tool_name: str, input_schema: dict) -> type[BaseModel]:
    """
    Строит Pydantic-модель аргументов из JSON Schema инструмента,
    исключая параметры из PARAM_INJECTORS (они не должны видеть LLM).
    """
    properties: dict = input_schema.get("properties", {})
    required: list[str] = input_schema.get("required", [])

    fields: dict[str, Any] = {}
    for param_name, param_schema in properties.items():
        if param_name in PARAM_INJECTORS:
            continue  # этот параметр подставим сами

        python_type = _JSON_TYPE_MAP.get(param_schema.get("type", "string"), str)
        description = param_schema.get("description", "")

        if param_name in required:
            fields[param_name] = (python_type, Field(..., description=description))
        else:
            fields[param_name] = (python_type, Field(None, description=description))

    if not fields:
        # Инструмент не требует аргументов от LLM
        fields["_no_args"] = (str, Field(default="", exclude=True))

    return create_model(f"{tool_name}_args", **fields)


def _make_langchain_tool(mcp_tool: Any) -> StructuredTool:
    """
    Оборачивает MCP-инструмент в LangChain StructuredTool:
    - из схемы убираются параметры из PARAM_INJECTORS
    - при вызове инжектируемые параметры подставляются программно
    """
    tool_name: str = mcp_tool.name
    description: str = mcp_tool.description or ""
    input_schema: dict = mcp_tool.inputSchema or {}

    # Имена параметров, которые реально есть в этом инструменте и подлежат инъекции
    injectable = {
        k for k in PARAM_INJECTORS if k in input_schema.get("properties", {})
    }

    args_model = _build_args_model(tool_name, input_schema)

    def tool_func(**kwargs) -> str:
        # Убираем служебное поле-заглушку, если оно есть
        kwargs.pop("_no_args", None)

        # Добавляем инжектируемые параметры — ПРОГРАММНО, не от LLM
        for param_name in injectable:
            kwargs[param_name] = PARAM_INJECTORS[param_name]()

        return _run(_call_mcp(tool_name, kwargs))

    return StructuredTool.from_function(
        func=tool_func,
        name=tool_name,
        description=description,
        args_schema=args_model,
    )


async def _discover_tools() -> list[StructuredTool]:
    """Запрашивает список инструментов из MCP-сервера и создаёт LangChain-обёртки."""
    async with Client(MCP_SERVER_URL) as client:
        mcp_tools = await client.list_tools()

    lc_tools = [_make_langchain_tool(t) for t in mcp_tools]
    print(f"[MCP] Обнаружено инструментов: {len(lc_tools)}")
    for t in lc_tools:
        print(f"  • {t.name}")
    return lc_tools


# ── Агент ─────────────────────────────────────────────────────────────────────

# Инструменты запрашиваются из MCP один раз при запуске
TOOLS: list[StructuredTool] = _run(_discover_tools())

LLM = ChatAnthropic(
    model="claude-opus-4-6",
    temperature=0,
)

SYSTEM_PROMPT = """Ты — HR-ассистент компании. Отвечай на русском языке.

У тебя есть доступ к инструментам для получения информации о текущем сотруднике:
- поиск по HR-документам и политикам
- персональные дни
- оставшиеся дни отпуска
- план-график отпусков

Используй инструменты, чтобы давать точные, актуальные ответы.
"""

agent = create_react_agent(
    model=LLM,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
)


# ── Публичный API ─────────────────────────────────────────────────────────────

def ask(question: str, user_login: str = "ivanov") -> str:
    """
    Задать вопрос HR-агенту от имени указанного пользователя.

    Args:
        question:   Вопрос на естественном языке.
        user_login: Логин пользователя — подставляется в MCP-вызовы программно.
    """
    CURRENT_USER_CONTEXT["login"] = user_login
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content


if __name__ == "__main__":
    questions = [
        "Сколько дней отпуска у меня осталось?",
        "Когда у меня запланированы отпуска в этом году?",
        "Какие у меня есть персональные дни?",
        "Какова политика компании по больничным?",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"Вопрос: {q}")
        print(f"{'='*60}")
        print(f"Ответ:\n{ask(q, user_login='ivanov')}")
