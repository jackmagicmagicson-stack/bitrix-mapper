import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Добавляем путь к проекту для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_EXCEL
from mapper import process_leads


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработчик лидов Битрикс 24")
        self.root.geometry("520x380")
        self.root.resizable(False, False)

        self.csv_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Готов к работе")
        self.stats_text = tk.StringVar(value="")

        self.build_ui()

    def build_ui(self):
        # Заголовок
        ttk.Label(
            self.root,
            text="📞 Обработчик лидов Битрикс 24",
            font=("Arial", 14, "bold"),
        ).pack(pady=(15, 10))

        ttk.Label(self.root, text="Выберите CSV-файл для обработки:").pack()

        # Выбор файла
        frame = ttk.Frame(self.root)
        frame.pack(pady=5)
        entry = ttk.Entry(frame, textvariable=self.csv_path, width=45)
        entry.pack(side=tk.LEFT, padx=(0, 5))
        entry.bind("<Button-1>", lambda e: entry.focus_set())
        entry.bind("<Command-v>", lambda e: entry.event_generate("<<Paste>>"))
        entry.bind("<Control-v>", lambda e: entry.event_generate("<<Paste>>"))
        ttk.Button(frame, text="Обзор...", command=self.browse_file).pack(side=tk.LEFT)

        # Кнопка Обработать
        self.btn_process = ttk.Button(
            self.root, text="⚡ Обработать", command=self.start_processing
        )
        self.btn_process.pack(pady=15)

        # Прогресс-бар (режим indeterminate — просто крутится)
        self.progress = ttk.Progressbar(
            self.root, mode="indeterminate", length=400
        )
        self.progress.pack(pady=5)

        # Статус
        ttk.Label(
            self.root, textvariable=self.status_text, font=("Arial", 10)
        ).pack(pady=5)

        # Статистика
        ttk.Label(
            self.root, textvariable=self.stats_text, font=("Arial", 11, "bold")
        ).pack(pady=5)

        # Кнопка Открыть Excel
        self.btn_open = ttk.Button(
            self.root,
            text="📂 Открыть Excel",
            command=self.open_excel,
            state=tk.DISABLED,
        )
        self.btn_open.pack(pady=10)

        # Подпись
        ttk.Label(self.root, text="v1.0 • MITA", foreground="gray").pack(
            side=tk.BOTTOM, pady=5
        )

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Выберите CSV-файл",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
        )
        if path:
            self.csv_path.set(path)

    def start_processing(self):
        csv_path = self.csv_path.get().strip()
        if not csv_path:
            messagebox.showwarning("Нет файла", "Выберите CSV-файл!")
            return

        if not os.path.exists(csv_path):
            messagebox.showerror("Ошибка", f"Файл не найден:\n{csv_path}")
            return

        # Блокируем кнопки
        self.btn_process.config(state=tk.DISABLED)
        self.btn_open.config(state=tk.DISABLED)
        self.status_text.set("Обработка...")
        self.stats_text.set("")
        self.progress.start(10)

        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.run_processing, args=(csv_path,))
        thread.daemon = True
        thread.start()

    def run_processing(self, csv_path):
        try:
            summary = process_leads(input_path=csv_path)
            self.root.after(0, self.on_finished, summary, None)
        except Exception as e:
            self.root.after(0, self.on_finished, None, str(e))

    def on_finished(self, summary, error):
        self.progress.stop()
        self.btn_process.config(state=tk.NORMAL)

        if error:
            self.status_text.set("Ошибка!")
            self.stats_text.set(f"❌ {error}")
            messagebox.showerror("Ошибка обработки", error)
            return

        processed = summary.get("processed", 0)
        errors = summary.get("errors", 0)
        duplicates = summary.get("duplicates_count", 0)

        self.status_text.set("✅ Обработка завершена")
        self.stats_text.set(
            f"Лидов: {processed} | Ошибок: {errors} | Групп дубликатов: {duplicates}"
        )
        self.btn_open.config(state=tk.NORMAL)

    def open_excel(self):
        if os.path.exists(OUTPUT_EXCEL):
            if sys.platform == "win32":
                os.startfile(OUTPUT_EXCEL)
            elif sys.platform == "darwin":
                subprocess.run(["open", OUTPUT_EXCEL], check=False)
            else:
                subprocess.run(["xdg-open", OUTPUT_EXCEL], check=False)
        else:
            messagebox.showwarning(
                "Файл не найден",
                "Excel-файл ещё не создан.\nСначала нажмите «Обработать».",
            )


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
