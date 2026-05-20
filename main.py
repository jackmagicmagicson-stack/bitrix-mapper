# main.py
import sys
import time

from mapper import process_leads
from config import INPUT_JSON, OUTPUT_CSV


def main():
    t0 = time.perf_counter()
    print("=" * 60)
    print("📞 ОБРАБОТЧИК ЛИДОВ ДЛЯ БИТРИКС 24")
    print("=" * 60)
    print("Положи JSON в папку input/ (файл leads.json)")
    print("CSV будет в папке output/ (файл leads_ready.csv)")
    print("=" * 60)
    print(f"📂 Вход: {INPUT_JSON}")
    print(f"📂 Выход: {OUTPUT_CSV}")
    print("=" * 60)

    try:
        summary = process_leads()
        print(
            f"\n✅ Обработано: {summary['processed']}, "
            f"Ошибок: {summary['errors']}, "
            f"Групп дубликатов: {summary['duplicates_count']}"
        )
        print(f"📄 CSV сохранён в: {OUTPUT_CSV}")
        if summary["errors"] > 0:
            print("⚠️ ВНИМАНИЕ: есть ошибки в строках!")
            sys.exit(1)
        elapsed = time.perf_counter() - t0
        print(f"Выполнено за {elapsed:.1f} сек")
    except FileNotFoundError:
        print(f"\n❌ Файл не найден: {INPUT_JSON}")
        print("💡 Положи JSON в папку input/ и назови leads.json")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
