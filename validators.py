# validators.py
import re
from datetime import datetime


def clean_phone(phone: str) -> str:
    """Оставляет только цифры и + в начале.
    Превращает 8... в +7..., 7... в +7..."""
    if not phone:
        return ""
    phone = re.sub(r"[^\d+]", "", phone)
    if phone.startswith("8"):
        phone = "+7" + phone[1:]
    if phone.startswith("7") and not phone.startswith("+"):
        phone = "+" + phone
    return phone


def is_valid_phone(phone: str) -> bool:
    """Для номеров с кодом 7/8 (RU): ровно 11 цифр; остальные — не короче 10 цифр."""
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return False
    if digits[0] in ("7", "8"):
        return len(digits) == 11
    return len(digits) >= 10


def is_valid_email(email: str) -> bool:
    """Базовая проверка email"""
    if not email:
        return False
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email.strip()))


def parse_date(date_str: str) -> str:
    """Приводит дату к YYYY-MM-DD; нераспознанный формат — пустая строка."""
    if not date_str or date_str.strip() == "":
        return ""
    formats = ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    s = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def parse_float(value: str) -> float:
    """Парсит цену/сумму: убирает пробелы, меняет запятую на точку"""
    if not value:
        return 0.0
    cleaned = value.replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
