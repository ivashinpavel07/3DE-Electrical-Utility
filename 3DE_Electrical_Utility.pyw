# -*- coding: utf-8 -*-
"""
3DE Electrical Utility
GUI-обертка для автоматической обработки DXF электрических логических схем
из CATIA 3DEXPERIENCE.

Выход:
- *_layers_Arial.dxf
- *_mapping.csv
- *_interactive.html
- *_layers_searchable.pdf
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import traceback
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from electrical_automation_core import transform_dxf, generate_html, generate_pdf


APP_TITLE = "3DE Electrical Utility"
APP_VERSION = "5.0"


def unique_output_dir(source: Path, custom_dir: Path | None) -> Path:
    if custom_dir:
        return custom_dir
    return source.parent / "3DE_Electrical_Output"


def process_one(
    source: Path,
    output_dir: Path,
    make_dxf: bool = True,
    make_csv: bool = True,
    make_html: bool = True,
    make_pdf: bool = True,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = source.stem
    target_dxf = output_dir / f"{stem}_layers_Arial.dxf"
    target_csv = output_dir / f"{stem}_mapping.csv"
    target_html = output_dir / f"{stem}_interactive.html"
    target_pdf = output_dir / f"{stem}_layers_searchable.pdf"

    # transform_dxf одновременно выполняет анализ, слои, ByLayer и Arial.
    # Даже если пользователь не хочет сохранять DXF, временный DXF нам не нужен:
    # для HTML используется исходный файл, а CSV можно сформировать transform_dxf.
    # Поэтому при DXF/CSV запускаем transform один раз.
    lines = 0
    texts = 0

    actual_dxf = None
    if make_dxf or make_csv or make_pdf:
        actual_dxf = target_dxf if make_dxf else output_dir / f".{stem}_temp_layers_Arial.dxf"
        csv_arg = target_csv if make_csv else None

        lines, texts, _ = transform_dxf(source, actual_dxf, csv_arg)

    pdf_layers = 0
    pdf_text = 0
    if make_pdf:
        pdf_layers, pdf_text = generate_pdf(actual_dxf, target_pdf)

    if actual_dxf is not None and not make_dxf and actual_dxf.exists():
        actual_dxf.unlink()

    if make_html:
        html_lines = generate_html(source, target_html)
        if not lines:
            lines = html_lines

    return {
        "source": source,
        "output_dir": output_dir,
        "dxf": target_dxf if make_dxf else None,
        "csv": target_csv if make_csv else None,
        "html": target_html if make_html else None,
        "pdf": target_pdf if make_pdf else None,
        "pdf_layers": pdf_layers,
        "pdf_text": pdf_text,
        "lines": lines,
        "texts": texts,
    }


class UtilityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} {APP_VERSION}")
        self.geometry("930x650")
        self.minsize(820, 560)

        self.files: list[Path] = []
        self.custom_output = tk.StringVar(value="")
        self.use_custom_output = tk.BooleanVar(value=False)

        self.make_dxf = tk.BooleanVar(value=True)
        self.make_csv = tk.BooleanVar(value=True)
        self.make_html = tk.BooleanVar(value=True)
        self.make_pdf = tk.BooleanVar(value=True)
        self.open_folder_after = tk.BooleanVar(value=True)

        self.processing = False
        self.last_output_dir: Path | None = None

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        title = ttk.Label(
            root,
            text="3DE Electrical Utility",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root,
            text=(
                "Автоматическая подготовка DXF электрических схем из 3DEXPERIENCE: "
                "слои по обозначениям линий • ByLayer • Arial • CSV • HTML • PDF со слоями и поиском"
            ),
            wraplength=880,
        )
        subtitle.pack(anchor="w", pady=(2, 12))

        files_box = ttk.LabelFrame(root, text="1. Исходные DXF", padding=10)
        files_box.pack(fill="both", expand=True)

        list_frame = ttk.Frame(files_box)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=("Consolas", 10),
            height=9,
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scroll.set)

        btns = ttk.Frame(files_box)
        btns.pack(fill="x", pady=(8, 0))

        ttk.Button(btns, text="Добавить DXF…", command=self.add_files).pack(side="left")
        ttk.Button(btns, text="Удалить выбранные", command=self.remove_selected).pack(
            side="left", padx=6
        )
        ttk.Button(btns, text="Очистить", command=self.clear_files).pack(side="left")

        output_box = ttk.LabelFrame(root, text="2. Папка результата", padding=10)
        output_box.pack(fill="x", pady=(10, 0))

        line = ttk.Frame(output_box)
        line.pack(fill="x")

        ttk.Checkbutton(
            line,
            text="Использовать выбранную папку",
            variable=self.use_custom_output,
            command=self.toggle_output,
        ).pack(side="left")

        self.output_entry = ttk.Entry(line, textvariable=self.custom_output, state="disabled")
        self.output_entry.pack(side="left", fill="x", expand=True, padx=8)

        self.output_button = ttk.Button(
            line, text="Выбрать…", command=self.choose_output, state="disabled"
        )
        self.output_button.pack(side="left")

        ttk.Label(
            output_box,
            text="По умолчанию рядом с каждым исходным DXF создается папка 3DE_Electrical_Output.",
        ).pack(anchor="w", pady=(5, 0))

        options = ttk.LabelFrame(root, text="3. Что сформировать", padding=10)
        options.pack(fill="x", pady=(10, 0))

        ttk.Checkbutton(
            options, text="DXF — слои + ByLayer + Arial", variable=self.make_dxf
        ).grid(row=0, column=0, sticky="w", padx=(0, 18))
        ttk.Checkbutton(options, text="CSV — отчет", variable=self.make_csv).grid(
            row=0, column=1, sticky="w", padx=(0, 18)
        )
        ttk.Checkbutton(
            options, text="HTML/SVG — интерактивная схема", variable=self.make_html
        ).grid(row=1, column=0, sticky="w", pady=(7, 0), padx=(0, 18))
        ttk.Checkbutton(
            options, text="PDF — слои + текстовый поиск", variable=self.make_pdf
        ).grid(row=1, column=1, sticky="w", pady=(7, 0))

        action = ttk.Frame(root)
        action.pack(fill="x", pady=(12, 0))

        self.run_button = ttk.Button(
            action, text="▶ ОБРАБОТАТЬ", command=self.start_processing
        )
        self.run_button.pack(side="left")

        ttk.Checkbutton(
            action,
            text="Открыть папку после завершения",
            variable=self.open_folder_after,
        ).pack(side="left", padx=14)

        ttk.Button(action, text="Открыть последнюю папку", command=self.open_last_folder).pack(
            side="right"
        )

        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x", pady=(10, 4))

        log_box = ttk.LabelFrame(root, text="Журнал", padding=8)
        log_box.pack(fill="both", expand=True, pady=(6, 0))

        self.log = tk.Text(
            log_box,
            height=9,
            wrap="word",
            font=("Consolas", 9),
            state="disabled",
        )
        self.log.pack(fill="both", expand=True)

        ttk.Label(
            root,
            text=(
                "Исходный DXF не изменяется. Для промышленного применения рекомендуется "
                "предварительно проверить алгоритм на серии схем."
            ),
            foreground="#666666",
        ).pack(anchor="w", pady=(7, 0))

    def log_line(self, text: str):
        self.after(0, self._append_log, text)

    def _append_log(self, text: str):
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def add_files(self):
        selected = filedialog.askopenfilenames(
            title="Выберите DXF",
            filetypes=[("DXF files", "*.dxf"), ("Все файлы", "*.*")],
        )
        existing = {str(p).lower() for p in self.files}
        for name in selected:
            p = Path(name)
            if str(p).lower() not in existing:
                self.files.append(p)
                existing.add(str(p).lower())
        self.refresh_list()

    def remove_selected(self):
        indexes = set(self.listbox.curselection())
        self.files = [p for i, p in enumerate(self.files) if i not in indexes]
        self.refresh_list()

    def clear_files(self):
        self.files.clear()
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for p in self.files:
            self.listbox.insert("end", str(p))

    def toggle_output(self):
        enabled = self.use_custom_output.get()
        state = "normal" if enabled else "disabled"
        self.output_entry.configure(state=state)
        self.output_button.configure(state=state)

    def choose_output(self):
        folder = filedialog.askdirectory(title="Папка результата")
        if folder:
            self.custom_output.set(folder)

    def validate(self):
        if not self.files:
            messagebox.showwarning(APP_TITLE, "Добавьте хотя бы один DXF-файл.")
            return False

        if not any((self.make_dxf.get(), self.make_csv.get(), self.make_html.get(), self.make_pdf.get())):
            messagebox.showwarning(APP_TITLE, "Выберите хотя бы один выходной формат.")
            return False

        for p in self.files:
            if not p.exists():
                messagebox.showerror(APP_TITLE, f"Файл не найден:\n{p}")
                return False

        if self.use_custom_output.get() and not self.custom_output.get().strip():
            messagebox.showwarning(APP_TITLE, "Выберите папку результата.")
            return False

        return True

    def start_processing(self):
        if self.processing or not self.validate():
            return

        self.processing = True
        self.run_button.configure(state="disabled")
        self.progress["maximum"] = len(self.files)
        self.progress["value"] = 0

        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        thread = threading.Thread(target=self.worker, daemon=True)
        thread.start()

    def worker(self):
        completed = 0
        errors = 0
        first_output = None

        try:
            custom = (
                Path(self.custom_output.get().strip())
                if self.use_custom_output.get()
                else None
            )

            for i, source in enumerate(self.files, start=1):
                try:
                    output_dir = unique_output_dir(source, custom)
                    if first_output is None:
                        first_output = output_dir

                    self.log_line(f"[{i}/{len(self.files)}] {source.name}")
                    result = process_one(
                        source,
                        output_dir,
                        make_dxf=self.make_dxf.get(),
                        make_csv=self.make_csv.get(),
                        make_html=self.make_html.get(),
                        make_pdf=self.make_pdf.get(),
                    )

                    self.log_line(
                        f"  ✓ электрических линий: {result['lines']}; "
                        f"текстовых объектов Arial: {result['texts']}"
                    )
                    if result.get('pdf'):
                        self.log_line(
                            f"  ✓ PDF: слоев {result['pdf_layers']}; "
                            f"извлечено символов текста {result['pdf_text']}"
                        )
                    self.log_line(f"  → {output_dir}")

                    completed += 1
                except Exception as exc:
                    errors += 1
                    self.log_line(f"  ✗ ОШИБКА: {exc}")
                    self.log_line(traceback.format_exc())

                self.after(0, self._set_progress, i)

            self.last_output_dir = first_output

            self.after(
                0,
                self.finish_processing,
                completed,
                errors,
                first_output,
            )

        except Exception as exc:
            self.log_line(traceback.format_exc())
            self.after(0, self.fatal_error, str(exc))

    def _set_progress(self, value):
        self.progress["value"] = value

    def finish_processing(self, completed, errors, first_output):
        self.processing = False
        self.run_button.configure(state="normal")

        message = f"Готово.\nОбработано: {completed}"
        if errors:
            message += f"\nОшибок: {errors}"

        if errors:
            messagebox.showwarning(APP_TITLE, message)
        else:
            messagebox.showinfo(APP_TITLE, message)

        if (
            self.open_folder_after.get()
            and first_output
            and completed
        ):
            self.open_folder(first_output)

    def fatal_error(self, error):
        self.processing = False
        self.run_button.configure(state="normal")
        messagebox.showerror(APP_TITLE, error)

    def open_last_folder(self):
        if self.last_output_dir:
            self.open_folder(self.last_output_dir)
        else:
            messagebox.showinfo(APP_TITLE, "Пока нет созданной папки результата.")

    @staticmethod
    def open_folder(path: Path):
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(path)])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(path)])


def cli_self_test(source: Path, output: Path):
    result = process_one(source, output, True, True, True, True)
    print(f"OK: lines={result['lines']}, texts={result['texts']}")
    print(output)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--self-test", type=Path)
    parser.add_argument("--output", type=Path)
    args, _ = parser.parse_known_args()

    if args.self_test:
        target = args.output or args.self_test.parent / "3DE_Electrical_Output_TEST"
        cli_self_test(args.self_test, target)
        return

    app = UtilityApp()
    app.mainloop()


if __name__ == "__main__":
    main()
