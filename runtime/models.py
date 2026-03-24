from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field


class RagDocumentResult(BaseModel):
    """Один документ в результатах RAG-поиска."""

    text: str = Field(..., description="Текст документа")
    relevance: float = Field(..., ge=0, le=1, description="Релевантность (0-1)")
    topic: str = Field(..., description="Тема документа")


class HrRagSearchOutput(BaseModel):
    """Результат RAG-поиска по HR-документам."""

    query: str = Field(..., description="Исходный запрос")
    results: list[RagDocumentResult] = Field(
        default_factory=list,
        description="Найденные документы",
    )


class PersonalDayItem(BaseModel):
    """Информация о персональных днях сотрудника."""

    fio: str = Field(..., description="ФИО сотрудника")
    RemainsPersonalDays: int = Field(..., description="Остаток персональных дней")
    FuturePersonalDays: str = Field(..., description="Запланированные персональные дни")


class VacationDaysRecord(BaseModel):
    """Запись об остатках отпуска сотрудника."""

    FIO: str = Field(..., description="ФИО")
    TypeVacation: str = Field(..., description="Тип отпуска")
    RemainsVacation: float = Field(..., ge=0, description="Остаток дней отпуска")


class VacationDatesRecord(BaseModel):
    """Запись о запланированном отпуске сотрудника."""

    FIO: str = Field(..., description="ФИО")
    TypeVacation: str = Field(..., description="Тип отпуска")
    StartDate: str = Field(..., description="Дата начала запланированного отпуска")
    EndDate: str = Field(..., description="Дата окончания запланированного отпуска")


T = TypeVar("T")


class ToolResponse(BaseModel, Generic[T]):
    """Унифицированный ответ MCP-инструмента."""

    status: str = Field(
        ...,
        description="Статус результата: ok, not_found, no_data или system_error",
    )
    message: str = Field(..., description="Краткое пояснение результата")
    data: Optional[T] = Field(
        default=None,
        description="Полезная нагрузка инструмента, если она есть",
    )


class ValidationErrorOutput(BaseModel):
    """Ошибка валидации."""

    error: str = Field("ValidationError", description="Тип ошибки")
    details: list[str] = Field(default_factory=list, description="Детали ошибок")
