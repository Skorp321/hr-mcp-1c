import base64
from datetime import date, datetime, timezone
from typing import Optional
import uuid
from dotenv import load_dotenv
import os
from runtime.utils import logger

import requests

load_dotenv()

def generate_headers_request():
    headers = {
        "x-messageID": str(uuid.uuid4().hex[:32]),  # Уникальный ID сообщения (32 символа)
        "x-messageDT": datetime.now(timezone.utc).strftime("%Y.%m.%d %H.%M.%S"),  # Время в UTC
        "x-correlationID": str(uuid.uuid4().hex[:32]),  # Опционально, но добавим
        "x-sourceCode": "BBH1C",  # Пример: 1С:ЗУП
        "x-destinationCode": "AIST",  # Пример: АС АИСТ
        "Content-type": "application/json; charset=utf-8",
    }

    login = os.getenv("ZUP_LOGIN")
    password = os.getenv("ZUP_PASSWORD")

    auth_str = f"{login}:{password}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers["Authorization"] = f"Basic {b64_auth}"

    return headers

def get_personal_days(login: str | None = None) -> dict:
    """Получить персональные дни сотрудников по логину."""

    headers = generate_headers_request()
    payload = {
        "login": login
    }
    url = os.path.join(os.getenv("BASE_ZUP_URL", ""), "PostPersonalDays/")
    try:
        response = requests.post(
            url,
            timeout=10,
            json=payload,
            headers=headers,
            verify=False
        )

        if response.headers.get("Content-Type", "").startswith("application/json"):
            try:
                response_json = response.json()
                logger.info("Ответ (JSON):", response_json)
                return response_json
            except requests.exceptions.JSONDecodeError:
                logger.info("Не удалось распарсить JSON.")
                return {}
        else:
            logger.info("Ответ не в формате JSON.")
            return {}

    except requests.exceptions.RequestException as e:
        logger.info("Ошибка запроса:", e)
        return {}    


def get_remaining_vacation_days(login: str) -> list[dict]:
    """Получить оставшиеся дни отпуска по логину за текущий год."""
    headers = generate_headers_request()
    payload = {
        "login": login
    }
    url = os.path.join(os.getenv("BASE_ZUP_URL", ""), "PostMyVacationRemainders/")
    try:
        response = requests.post(
            url,
            timeout=10,
            json=payload,
            headers=headers,
            verify=False
        )

        if response.headers.get("Content-Type", "").startswith("application/json"):
            try:
                response_json = response.json()
                logger.info("Ответ (JSON):", response_json)
                return response_json
            except requests.exceptions.JSONDecodeError:
                logger.info("Не удалось распарсить JSON.")
                return [{}]
        else:
            logger.info("Ответ не в формате JSON.")
            return [{}]

    except requests.exceptions.RequestException as e:
        logger.info("Ошибка запроса:", e)
        return [{}]
    
def get_plan_vacation(login: Optional[str]) -> list[dict]:
    """Получить плановые отпуска по логину за текущий год."""
    headers = generate_headers_request()
    payload = {
        "login": login
    }
    url = os.path.join(os.getenv("BASE_ZUP_URL", ""), "PostPlanVacation/")
    try:
        response = requests.post(
            url,
            timeout=10,
            json=payload,
            headers=headers,
            verify=False
        )

        if response.headers.get("Content-Type", "").startswith("application/json"):
            try:
                response_json = response.json()
                logger.info("Ответ (JSON):", response_json)
                return response_json
            except requests.exceptions.JSONDecodeError:
                logger.info("Не удалось распарсить JSON.")
                return [{}]
        else:
            logger.info("Ответ не в формате JSON.")
            return [{}]

    except requests.exceptions.RequestException as e:
        logger.info("Ошибка запроса:", e)
        return [{}]
