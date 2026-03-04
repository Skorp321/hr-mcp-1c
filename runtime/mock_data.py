# Моковые данные о персональных днях сотрудников
# Персональный день - это дополнительный выходной (день рождения, годовщина и т.д.)
PERSONAL_DAYS_MOCK = [
    {
        "employee_id": "EMP001",
        "login": "ivanov",
        "employee_name": "Иванов Иван Иванович",
        "personal_days": [
            {"date": "2025-02-14", "reason": "День рождения", "used": False},
            {"date": "2025-06-15", "reason": "Годовщина в компании", "used": False},
        ],
        "total_available": 2,
    },
    {
        "employee_id": "EMP002",
        "login": "petrova",
        "employee_name": "Петрова Мария Сергеевна",
        "personal_days": [
            {"date": "2025-03-08", "reason": "Международный женский день", "used": False},
            {"date": "2025-05-15", "reason": "День рождения", "used": True},
        ],
        "total_available": 2,
        "used_count": 1,
    },
    {
        "employee_id": "EMP003",
        "login": "sidorov",
        "employee_name": "Сидоров Алексей Петрович",
        "personal_days": [
            {"date": "2025-01-10", "reason": "День рождения", "used": True},
        ],
        "total_available": 1,
        "used_count": 1,
    },
]

# Моковые данные об отпусках
VACATION_DAYS_MOCK = [
    {
        "employee_id": "EMP001",
        "login": "ivanov",
        "employee_name": "Иванов Иван Иванович",
        "year": 2025,
        "total_days": 28,
        "used_days": 5,
        "remaining_days": 23,
        "planned_days": 14,
        "carry_over_from_prev_year": 0,
    },
    {
        "employee_id": "EMP002",
        "login": "petrova",
        "employee_name": "Петрова Мария Сергеевна",
        "year": 2025,
        "total_days": 28,
        "used_days": 14,
        "remaining_days": 14,
        "planned_days": 7,
        "carry_over_from_prev_year": 3,
    },
    {
        "employee_id": "EMP003",
        "login": "sidorov",
        "employee_name": "Сидоров Алексей Петрович",
        "year": 2025,
        "total_days": 28,
        "used_days": 21,
        "remaining_days": 7,
        "planned_days": 0,
        "carry_over_from_prev_year": 0,
    },
]
