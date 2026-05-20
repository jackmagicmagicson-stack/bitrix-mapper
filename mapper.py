# mapper.py
import csv
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse

from config import (
    INPUT_JSON,
    OUTPUT_CSV,
    BITRIX_CSV_HEADERS,
    CSV_COLUMNS,
    CSV_OUTPUT_DELIMITER,
    PHONE_FIELDS,
    EMAIL_FIELDS,
    MAX_DUPLICATE_CHECK,
)
from validators import (
    clean_phone,
    is_valid_phone,
    is_valid_email,
    parse_date,
    parse_float,
)

REQUIRED_HEADERS = (
    CSV_COLUMNS["id"],
    CSV_COLUMNS["lead_name"],
    CSV_COLUMNS["mobile_phone"],
    CSV_COLUMNS["work_email"],
)

PROGRESS_EVERY = 500

_COMPANY_LEGAL = re.compile(
    r"\b(ооо|ип|зао)\b",
    re.IGNORECASE,
)

PHONE_HEADERS = frozenset(
    {
        "Рабочий телефон",
        "Мобильный телефон",
        "Номер факса",
        "Домашний телефон",
        "Номер пейджера",
        "Телефон для рассылок",
        "Другой телефон",
    }
)

EMAIL_HEADERS = frozenset(
    {
        "Рабочий e-mail",
        "Частный e-mail",
        "E-mail для рассылок",
        "Другой e-mail",
    }
)

NUM_HEADERS = frozenset({"Цена", "Количество", "Возможная сумма"})

# ----------------------------------------------------------------
# ОПРЕДЕЛЕНИЕ ФОРМАТА
# ----------------------------------------------------------------

YANDEX_KEYS = {"indexNumber", "parsedAt", "phone_1", "title", "url"}


def _is_yandex_format(data: list[dict]) -> bool:
    """Если хотя бы у одного объекта есть характерные ключи Яндекса — формат Яндекс.Карт"""
    if not data:
        return False
    first_keys = set(data[0].keys())
    return bool(first_keys & YANDEX_KEYS)


# ----------------------------------------------------------------
# МАППИНГ ЯНДЕКС → БИТРИКС (строки CSV)
# ----------------------------------------------------------------

def _parse_address_yandex(address: str) -> dict:
    """Парсит адрес Яндекса: 'Тула, проспект Ленина, 102А' → город, улица"""
    if not address:
        return {"city": "", "street": ""}
    parts = [p.strip() for p in address.split(",", 1)]
    city = parts[0] if parts else ""
    street = parts[1] if len(parts) > 1 else ""
    return {"city": city, "street": street}


def _clean_url(url: str) -> str:
    """Оставляет только домен: https://adv71.ru/?yclid=... → https://adv71.ru"""
    if not url:
        return ""
    url = url.strip()
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _yandex_row_to_bitrix(raw: dict, json_filename: str = "") -> list[str]:
    """Из объекта Яндекса → готовая строка CSV (64 колонки)"""
    title = (raw.get("title") or "").strip()
    category_0 = (raw.get("Category 0") or "").strip()

    # Название лида = Категория - Название
    lead_name = f"{category_0} - {title}" if category_0 else title

    address_raw = (raw.get("address") or "").strip()
    addr = _parse_address_yandex(address_raw)

    # Только два телефона: phone_1 и phone_2
    phone_1 = clean_phone(raw.get("phone_1", ""))
    if not is_valid_phone(phone_1):
        phone_1 = ""
    phone_2 = clean_phone(raw.get("phone_2", ""))
    if not is_valid_phone(phone_2):
        phone_2 = ""

    # Сайт — только домен
    site = _clean_url(raw.get("companyUrl", ""))

    # Собираем строку по порядку BITRIX_CSV_HEADERS
    row = []
    for h in BITRIX_CSV_HEADERS:
        if h == "ID":
            row.append("")
        elif h == "Название лида":
            row.append(lead_name)
        elif h == "Название компании":
            row.append(title)
        elif h == "Адрес":
            row.append(address_raw)
        elif h == "Населенный пункт":
            row.append(addr["city"])
        elif h == "Улица, номер дома":
            row.append(addr["street"])
        elif h == "Мобильный телефон":
            row.append(phone_1)
        elif h == "Рабочий телефон":
            row.append(phone_2)
        elif h == "Другой телефон":
            row.append("")
        elif h == "Корпоративный сайт":
            row.append(site)
        elif h == "Контакт Telegram":
            row.append("")
        elif h == "Контакт ВКонтакте":
            row.append("")
        elif h == "Контакт Viber":
            row.append("")
        elif h == "Другой контакт":
            row.append("")
        elif h == "Комментарий":
            row.append("")
        elif h == "Источник":
            row.append("Холодный звонок")
        elif h == "Дополнительно об источнике":
            row.append("")
        elif h == "Источник телефона":
            row.append(json_filename)
        elif h == "Тип услуги":
            row.append("ГЦК")
        elif h == "Стадия":
            row.append("")
        elif h == "Доступен для всех":
            row.append("")
        else:
            row.append("")
    return row

# ----------------------------------------------------------------
# ОРИГИНАЛЬНЫЙ МАППИНГ (Битрикс)
# ----------------------------------------------------------------

def _cell(raw: dict, key: str) -> str:
    v = raw.get(CSV_COLUMNS[key], "")
    return v.strip() if isinstance(v, str) else str(v or "").strip()


def normalize_company(name: str) -> str:
    if not name or not str(name).strip():
        return ""
    s = str(name).strip().lower()
    s = s.replace('"', "").replace("'", "")
    s = _COMPANY_LEGAL.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _raw_get(raw: dict, header: str) -> str:
    v = raw.get(header, "")
    return v.strip() if isinstance(v, str) else str(v or "").strip()


def _iso_to_ddmmyyyy(iso: str) -> str:
    if not iso:
        return ""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return ""


def _format_ru_decimal(n: float) -> str:
    return f"{n:.2f}".replace(".", ",")


def _bitrix_cell_for_csv(header: str, raw: dict) -> str:
    if header == "Название компании":
        val = _raw_get(raw, "Название компании") or _raw_get(raw, "Компания")
    else:
        val = _raw_get(raw, header)
    if not val:
        return ""
    if header in PHONE_HEADERS:
        return clean_phone(val)
    if header in EMAIL_HEADERS:
        return val.replace(" ", "").lower()
    if header == "Дата рождения":
        return _iso_to_ddmmyyyy(parse_date(val))
    if header in NUM_HEADERS:
        parsed = parse_float(val)
        st = val.strip()
        if parsed == 0.0 and st and st != "0":
            return val
        return _format_ru_decimal(parsed)
    return val


def _bitrix_row_from_raw(raw: dict) -> list[str]:
    return [_bitrix_cell_for_csv(h, raw) for h in BITRIX_CSV_HEADERS]


# ----------------------------------------------------------------
# ЧТЕНИЕ JSON
# ----------------------------------------------------------------

def read_json(file_path: str, is_yandex: bool = False) -> list[dict]:
    """Читает JSON-массив. Для Битрикса проверяет обязательные поля."""
    with open(file_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON должен быть массивом объектов")
    if is_yandex:
        # Яндекс: минимальная проверка
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Элемент #{i + 1}: ожидается объект, не {type(item).__name__}"
                )
        return data

    # Битрикс: строгая проверка
    leads: list[dict] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(
                f"Элемент #{i + 1}: ожидается объект, не {type(item).__name__}"
            )
        row = {(k or "").strip(): v for k, v in item.items()}
        missing = [h for h in REQUIRED_HEADERS if h not in row]
        if missing:
            raise ValueError(
                f"Объект #{i + 1}: отсутствуют обязательные поля: "
                + ", ".join(missing)
            )
        leads.append(row)
    return leads


# ----------------------------------------------------------------
# ДУБЛИКАТЫ (используется только для Битрикс-формата)
# ----------------------------------------------------------------

def map_lead(raw: dict) -> dict:
    """Мапит одну строку CSV в структурированный словарь (только Битрикс)"""
    birth_raw = _cell(raw, "birth_date")

    _co = raw.get("Компания", "")
    _co = _co.strip() if isinstance(_co, str) else str(_co or "").strip()
    company_name = _co or _cell(raw, "company_name")

    mapped = {
        "id": _cell(raw, "id"),
        "lead_name": _cell(raw, "lead_name"),
        "full_name": _cell(raw, "full_name"),
        "first_name": _cell(raw, "first_name"),
        "last_name": _cell(raw, "last_name"),
        "middle_name": _cell(raw, "middle_name"),
        "salutation": _cell(raw, "salutation"),
        "birth_date_raw": birth_raw,
        "birth_date": parse_date(birth_raw),
        "company_name": company_name,
        "position": _cell(raw, "position"),
        "comment": _cell(raw, "comment"),
        "stage": _cell(raw, "stage"),
        "stage_extra": _cell(raw, "stage_extra"),
        "source": _cell(raw, "source"),
        "source_extra": _cell(raw, "source_extra"),
        "responsible": _cell(raw, "responsible"),
        "service_type": _cell(raw, "service_type"),
        "rejection_reason": _cell(raw, "rejection_reason"),
        "available_for_all": _cell(raw, "available_for_all"),
        "linked_user": _cell(raw, "linked_user"),
        "deal": _cell(raw, "deal"),
    }

    mapped["address"] = {
        "full": _cell(raw, "address"),
        "street": _cell(raw, "street"),
        "apartment": _cell(raw, "apartment"),
        "city": _cell(raw, "city"),
        "district": _cell(raw, "district"),
        "region": _cell(raw, "region"),
        "postal_code": _cell(raw, "postal_code"),
        "country": _cell(raw, "country"),
    }

    phones = []
    for field in PHONE_FIELDS:
        raw_phone = _cell(raw, field)
        if raw_phone:
            cleaned = clean_phone(raw_phone)
            if cleaned and cleaned not in phones:
                phones.append(cleaned)
    mapped["phones"] = phones
    mapped["primary_phone"] = next(
        (p for p in phones if is_valid_phone(p)),
        phones[0] if phones else "",
    )

    emails = []
    for field in EMAIL_FIELDS:
        raw_email = _cell(raw, field)
        if raw_email:
            cleaned = raw_email.replace(" ", "").lower()
            if cleaned and cleaned not in emails:
                emails.append(cleaned)
    mapped["emails"] = emails
    mapped["primary_email"] = next(
        (e for e in emails if is_valid_email(e)),
        emails[0] if emails else "",
    )

    mapped["messengers"] = {
        "telegram": _cell(raw, "contact_telegram"),
        "viber": _cell(raw, "contact_viber"),
        "whatsapp": _cell(raw, "other_contact"),
    }
    mapped["social"] = {
        "vk": _cell(raw, "vk"),
        "facebook": _cell(raw, "facebook"),
        "twitter": _cell(raw, "twitter"),
        "livejournal": _cell(raw, "livejournal"),
        "instagram": _cell(raw, "contact_instagram"),
    }
    mapped["sites"] = {
        "corporate": _cell(raw, "website"),
        "personal": _cell(raw, "personal_page"),
        "other": _cell(raw, "other_site"),
    }

    mapped["product"] = {
        "name": _cell(raw, "product"),
        "price": parse_float(_cell(raw, "price")),
        "quantity": parse_float(_cell(raw, "quantity")),
        "possible_amount": parse_float(_cell(raw, "possible_amount")),
        "currency": _cell(raw, "currency"),
    }

    mapped["files"] = {
        "new_file": _cell(raw, "new_file"),
        "extra_file": _cell(raw, "extra_file"),
    }

    mapped["extra"] = {
        "fax": _cell(raw, "fax"),
        "pager": _cell(raw, "pager"),
        "phone_source": _cell(raw, "phone_source"),
        "contact_bitrix24": _cell(raw, "contact_bitrix24"),
        "contact_online_chat": _cell(raw, "contact_online_chat"),
        "contact_open_line": _cell(raw, "contact_open_line"),
    }

    return mapped


def _build_duplicates(mapped_leads: list[dict]) -> dict:
    phone_to_ids: dict[str, set[str]] = {}
    email_to_ids: dict[str, set[str]] = {}
    company_to_ids: dict[str, set[str]] = {}

    for lead in mapped_leads:
        lid = (lead.get("id") or "").strip()
        if not lid:
            lid = f"row_{lead.get('_csv_row', 0)}"
        for p in lead.get("phones") or []:
            phone_to_ids.setdefault(p, set()).add(lid)
        for e in lead.get("emails") or []:
            email_to_ids.setdefault(e.lower(), set()).add(lid)
        cn = lead.get("company_name") or ""
        key = normalize_company(cn)
        if key:
            company_to_ids.setdefault(key, set()).add(lid)

    def only_multi(d: dict[str, set[str]]) -> dict[str, list[str]]:
        out = {}
        for k, ids in d.items():
            if len(ids) > 1:
                out[k] = sorted(ids)
        return out

    return {
        "phones": only_multi(phone_to_ids),
        "emails": only_multi(email_to_ids),
        "companies": only_multi(company_to_ids),
    }


def _duplicate_groups_count(dup: dict) -> int:
    return (
        len(dup.get("phones") or {})
        + len(dup.get("emails") or {})
        + len(dup.get("companies") or {})
    )


def _lead_ids_in_duplicates(duplicates: dict) -> set[str]:
    ids: set[str] = set()
    for key in ("phones", "emails", "companies"):
        block = duplicates.get(key) or {}
        if not isinstance(block, dict):
            continue
        for _k, id_list in block.items():
            ids.update(id_list)
    return ids


def _error_row_values(raw: dict) -> list[str]:
    row = []
    for h in BITRIX_CSV_HEADERS:
        if h == "Название компании":
            row.append(
                _raw_get(raw, "Название компании") or _raw_get(raw, "Компания")
            )
        else:
            row.append(_raw_get(raw, h))
    return row


# ----------------------------------------------------------------
# ЗАПИСЬ CSV
# ----------------------------------------------------------------

def write_csv(
    leads: list[list[str]],
    errors: list[dict],
    output_path: str,
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ncol = len(BITRIX_CSV_HEADERS)
    marker_pad = [""] * (ncol - 1) if ncol > 1 else []

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=CSV_OUTPUT_DELIMITER, quoting=csv.QUOTE_MINIMAL)
        w.writerow(BITRIX_CSV_HEADERS)
        for row in leads:
            w.writerow(row)

        if errors:
            w.writerow(["=== ОШИБКИ ==="] + marker_pad)
            err_h = list(BITRIX_CSV_HEADERS) + ["Ошибка"]
            w.writerow(err_h)
            for err in errors:
                raw = err.get("data") or {}
                line = _error_row_values(raw)
                line.append(str(err.get("error", "")))
                w.writerow(line)

# ----------------------------------------------------------------
# ГЛАВНАЯ ФУНКЦИЯ ОБРАБОТКИ
# ----------------------------------------------------------------

def process_leads(
    input_path: str = INPUT_JSON,
    output_path: str = OUTPUT_CSV,
) -> dict:
    """Читает JSON (Битрикс или Яндекс), сохраняет CSV. Возвращает сводку."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    # Читаем сырые данные для определения формата
    with open(input_path, "r", encoding="utf-8-sig") as f:
        raw_data = json.load(f)

    is_yandex = _is_yandex_format(raw_data)
    fmt_label = "Яндекс.Карты" if is_yandex else "Битрикс 24"
    print(f"📋 Определён формат: {fmt_label}")

    if is_yandex:
        # --- Режим Яндекс.Карты ---
        raw_leads = read_json(input_path, is_yandex=True)
        leads_rows: list[list[str]] = []
        seen: set[tuple] = set()
        errors: list[dict] = []

        for i, raw in enumerate(raw_leads, start=1):
            if i % PROGRESS_EVERY == 0:
                print(f"… обработано записей: {i} / {len(raw_leads)}", flush=True)
            try:
                row = _yandex_row_to_bitrix(raw, os.path.basename(input_path))
                # Уникальность по (название лида, телефон1, телефон2)
                key = (row[1], row[16], row[17])
                if key not in seen:
                    seen.add(key)
                    leads_rows.append(row)
            except Exception as e:
                errors.append({"row": i, "error": str(e), "data": raw})

        dup_count = 0

    else:
        # --- Режим Битрикс 24 (старая логика) ---
        raw_leads = read_json(input_path, is_yandex=False)
        mapped_leads: list[dict] = []
        errors: list[dict] = []
        leads_rows: list[list[str]] = []

        for i, raw in enumerate(raw_leads, start=1):
            if i % PROGRESS_EVERY == 0:
                print(f"… обработано записей: {i} / {len(raw_leads)}", flush=True)
            try:
                mapped = map_lead(raw)
                mapped["_csv_row"] = i
                mapped_leads.append(mapped)
                leads_rows.append(_bitrix_row_from_raw(raw))
            except Exception as e:
                errors.append({"row": i, "error": str(e), "data": raw})

        n_rows = len(raw_leads)
        if n_rows > MAX_DUPLICATE_CHECK:
            print(
                f"⚠️ Записей в JSON больше {MAX_DUPLICATE_CHECK}, "
                "проверка дубликатов отключена",
                flush=True,
            )
            duplicates = {
                "phones": {},
                "emails": {},
                "companies": {},
                "skipped": True,
            }
            dup_count = 0
            dup_ids: set[str] = set()
            dup_check_skipped = True
        else:
            duplicates = _build_duplicates(mapped_leads)
            duplicates["skipped"] = False
            dup_count = _duplicate_groups_count(duplicates)
            dup_ids = _lead_ids_in_duplicates(duplicates)
            dup_check_skipped = False

        dup_row_indices: set[int] = set()
        for idx, mapped in enumerate(mapped_leads):
            lid = (mapped.get("id") or "").strip()
            if not lid:
                lid = f"row_{mapped.get('_csv_row', 0)}"
            if lid in dup_ids:
                dup_row_indices.add(idx)

        dup_rows_out = [leads_rows[i] for i in sorted(dup_row_indices)]
        duplicates["rows"] = dup_rows_out
        duplicates["skipped"] = dup_check_skipped

    write_csv(leads_rows, errors, output_path)

    return {
        "processed": len(leads_rows),
        "errors": len(errors),
        "duplicates_count": dup_count if not is_yandex else 0,
    }


if __name__ == "__main__":
    summary = process_leads()
    print(
        f"Обработано: {summary['processed']}, "
        f"ошибок: {summary['errors']}, "
        f"групп дубликатов: {summary['duplicates_count']}"
    )