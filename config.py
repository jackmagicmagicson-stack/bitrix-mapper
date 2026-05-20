# config.py
import os

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "input", "leads.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "leads_ready.csv")

# Лимит строк для поиска дубликатов (при превышении — пропуск с предупреждением)
MAX_DUPLICATE_CHECK = 10000

# CSV на выходе (импорт в Битрикс / Excel)
CSV_OUTPUT_DELIMITER = ";"

# CSV на входе (устарело для JSON-пайплайна; оставлено для совместимости)
CSV_DELIMITER = ";"
CSV_ENCODINGS = ["utf-8-sig", "cp1251", "windows-1251"]

# Порядок колонок как в шаблоне импорта Битрикс24 (CSV)
BITRIX_CSV_HEADERS = [
    "ID",
    "Название лида",
    "Обращение",
    "Имя",
    "Фамилия",
    "Отчество",
    "Имя, Фамилия",
    "Дата рождения",
    "Адрес",
    "Улица, номер дома",
    "Квартира, офис, комната, этаж",
    "Населенный пункт",
    "Район",
    "Регион",
    "Почтовый индекс",
    "Страна",
    "Рабочий телефон",
    "Мобильный телефон",
    "Номер факса",
    "Домашний телефон",
    "Номер пейджера",
    "Телефон для рассылок",
    "Другой телефон",
    "Корпоративный сайт",
    "Личная страница",
    "Страница Facebook",
    "Страница ВКонтакте",
    "Страница LiveJournal",
    "Микроблог Twitter",
    "Другой сайт",
    "Рабочий e-mail",
    "Частный e-mail",
    "E-mail для рассылок",
    "Другой e-mail",
    "Контакт Facebook",
    "Контакт Telegram",
    "Контакт ВКонтакте",
    "Контакт Viber",
    "Комментарии Instagram",
    "Контакт Битрикс24 Network",
    "Онлайн-чат",
    "Контакт Открытая линия",
    "Другой контакт",
    "Связанный пользователь",
    "Название компании",
    "Должность",
    "Комментарий",
    "Стадия",
    "Дополнительно о стадии",
    "Товар",
    "Цена",
    "Количество",
    "Возможная сумма",
    "Валюта",
    "Источник",
    "Дополнительно об источнике",
    "Доступен для всех",
    "Ответственный",
    "Тип услуги",
    "Новый файл",
    "Доп файл",
    "Источник телефона",
    "Причина отказа",
    "дело",
]

# Колонки из CSV (оригинальные названия) — те же ключи в JSON-объектах лида
CSV_COLUMNS = {
    "id": "ID",
    "lead_name": "Название лида",
    "salutation": "Обращение",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "middle_name": "Отчество",
    "full_name": "Имя, Фамилия",
    "birth_date": "Дата рождения",
    "address": "Адрес",
    "street": "Улица, номер дома",
    "apartment": "Квартира, офис, комната, этаж",
    "city": "Населенный пункт",
    "district": "Район",
    "region": "Регион",
    "postal_code": "Почтовый индекс",
    "country": "Страна",
    "work_phone": "Рабочий телефон",
    "mobile_phone": "Мобильный телефон",
    "fax": "Номер факса",
    "home_phone": "Домашний телефон",
    "pager": "Номер пейджера",
    "mailing_phone": "Телефон для рассылок",
    "other_phone": "Другой телефон",
    "website": "Корпоративный сайт",
    "personal_page": "Личная страница",
    "facebook": "Страница Facebook",
    "vk": "Страница ВКонтакте",
    "livejournal": "Страница LiveJournal",
    "twitter": "Микроблог Twitter",
    "other_site": "Другой сайт",
    "work_email": "Рабочий e-mail",
    "private_email": "Частный e-mail",
    "mailing_email": "E-mail для рассылок",
    "other_email": "Другой e-mail",
    "contact_facebook": "Контакт Facebook",
    "contact_telegram": "Контакт Telegram",
    "contact_vk": "Контакт ВКонтакте",
    "contact_viber": "Контакт Viber",
    "contact_instagram": "Комментарии Instagram",
    "contact_bitrix24": "Контакт Битрикс24 Network",
    "contact_online_chat": "Онлайн-чат",
    "contact_open_line": "Контакт Открытая линия",
    "other_contact": "Другой контакт",
    "linked_user": "Связанный пользователь",
    "company_name": "Название компании",
    "position": "Должность",
    "comment": "Комментарий",
    "stage": "Стадия",
    "stage_extra": "Дополнительно о стадии",
    "product": "Товар",
    "price": "Цена",
    "quantity": "Количество",
    "possible_amount": "Возможная сумма",
    "currency": "Валюта",
    "source": "Источник",
    "source_extra": "Дополнительно об источнике",
    "available_for_all": "Доступен для всех",
    "responsible": "Ответственный",
    "service_type": "Тип услуги",
    "new_file": "Новый файл",
    "extra_file": "Доп файл",
    "phone_source": "Источник телефона",
    "rejection_reason": "Причина отказа",
    "deal": "дело",
}

# Поля, которые собираем в один список "Телефоны"
PHONE_FIELDS = [
    "work_phone", "mobile_phone", "fax", "pager", "home_phone",
    "mailing_phone", "other_phone",
]

# Поля, которые собираем в один список "Email"
EMAIL_FIELDS = [
    "work_email", "private_email", "mailing_email", "other_email"
]
