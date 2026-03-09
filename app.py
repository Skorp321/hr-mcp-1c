import os
import uvicorn
from mcp.server.fastmcp import FastMCP

from tools.zup_1c import (
    get_personal_days, 
    get_remaining_vacation_days,
    get_plan_vacation
)
from tools.rag import rag_search
from runtime.models import (
    PersonalDayItem,
    VacationDatesRecord,
    GetRemainingVacationDatesOutput,
    GetRemainingVacationDaysOutput,
    HrRagSearchOutput,
    RagDocumentResult,
    VacationDaysRecord,
)

mcp = FastMCP(
    name="HR MCP Server",
    json_response=True,
)


@mcp.tool()
def hr_rag_search(query: str, n_results: str) -> HrRagSearchOutput:
    """
    Поиск по HR-документам и политикам с помощью RAG (Retrieval Augmented Generation).
    
    Использует семантический поиск по базе HR-документов: политики отпусков,
    персональных дней, больничных, удалённой работы, приёма на работу,
    командировки и льготы.
    
    Args:
        query: Поисковый запрос на естественном языке (например: "сколько дней отпуска", "как оформить больничный")
        n_results: Максимальное количество документов в ответе (по умолчанию 5)
    
    Returns:
        Релевантные фрагменты документов с указанием степени релевантности
    """
    results = rag_search(query=query, n_results=int(n_results))
    return HrRagSearchOutput(
        query=query,
        results=[RagDocumentResult(**r) for r in results],
    )
    

@mcp.tool()
def get_personal_days_tool(login: str) -> PersonalDayItem:
    """
    Получить персональные дни сотрудника или всех сотрудников.
    
    Персональные дни - дополнительные выходные (день рождения, годовщина в компании и т.д.)
    
    Args:
        login: Логин пользователя (ivanov, petrova, sidorov) или None для всех сотрудников
    
    Returns:
        Список персональных дней с датами, причинами и статусом использования
    """
    data = get_personal_days(login="ivanov")
    items = PersonalDayItem(**data)
    return items

@mcp.tool()
def get_remaining_vacation_days_tool(login: str) -> GetRemainingVacationDaysOutput:
    """
    Получить оставшиеся дни отпуска сотрудника за текущий год.
    
    Args:
        login: Логин пользователя
    
    Returns:
        Информация об отпуске: всего дней, использовано, осталось, запланировано
    """
    data = get_remaining_vacation_days(login="ivanov")
    items = [VacationDaysRecord(**item) for item in data]
    return GetRemainingVacationDaysOutput(items=items)

@mcp.tool()
def get_plan_vacation_tool(login: str) -> GetRemainingVacationDatesOutput:
    """
    Получить плана-графика отпусков сотрудника за текущий год.
    
    Args:
        login: Логин пользователя
    
    Returns:
        Информация об отпуске: график запланированных отпусков
    """
    data = get_plan_vacation(login="ivanov")
    items = [VacationDatesRecord(**item) for item in data]
    return GetRemainingVacationDatesOutput(items=items)

def main():
    """Точка входа для запуска сервера."""    

    app = mcp.streamable_http_app()
    mcp_port = os.getenv("MCP_PORT", 8050)
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(mcp_port),
        ws="none",  # только HTTP
        log_level="info",
    )


if __name__ == "__main__":
    main()
