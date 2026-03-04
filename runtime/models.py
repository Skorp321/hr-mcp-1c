from typing import Optional
from pydantic import BaseModel, Field

# --- Выходные схемы ---
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
    """Один персональный день."""

    fio: str = Field(..., description="ФИО сотрудника чьи персональные дни.")
    RemainsPersonalDays: int = Field(..., description="Остаток персональных дней")
    FuturePersonalDays: str = Field(..., description="Даты когда заплонированы персональные дни")


class EmployeePersonalDays(BaseModel):
    """Персональные дни сотрудника."""

    fio: str = Field(..., description="ФИО")
    RemainsPersonalDays: str = Field(..., description="Дата начала")
    FuturePersonalDays : str = Field(..., description="Дата окончания")


class GetPersonalDaysOutput(BaseModel):
    """Результат получения персональных дней."""

    items: list[EmployeePersonalDays] = Field(
        default_factory=list,
        description="Запланированные даты отпуска по сотрудникам",
    )


class VacationDaysRecord(BaseModel):
    """Запись об отпуске сотрудника."""
    FIO: str = Field(..., description="ФИО")
    TypeVacation: str = Field(..., description="Тип отпуска")
    RemainsVacation: float = Field(..., ge=0, description="Всего дней отпуска")

class VacationDatesRecord(BaseModel):
    """Запись об отпуске сотрудника."""
    FIO: str = Field(..., description="ФИО")
    TypeVacation: str = Field(..., description="Тип отпуска")
    StartDate: str = Field(..., description="Дата начала запланированного отпуска")
    EndDate: str = Field(..., description="Дата конца запланированного отпуска")
    

class GetRemainingVacationDaysOutput(BaseModel):
    """Результат получения оставшихся дней отпуска."""

    items: list[VacationDaysRecord] = Field(
        default_factory=list,
        description="Данные по отпуску",
    )

class GetRemainingVacationDatesOutput(BaseModel):
    """Результат получения оставшихся дней отпуска."""

    items: list[VacationDatesRecord] = Field(
        default_factory=list,
        description="Данные по отпуску",
    )

class ValidationErrorOutput(BaseModel):
    """Ошибка валидации."""

    error: str = Field("ValidationError", description="Тип ошибки")
    details: list[str] = Field(default_factory=list, description="Детали ошибок")
