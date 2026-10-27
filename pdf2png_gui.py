#!/usr/bin/env python3
"""PDF を 1 ページずつ PNG 画像に変換するツール (GUI 版)。

    python pdf2png_gui.py
"""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import pymupdf

DPI_PRESETS = ["72", "96", "150", "200", "300", "600"]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF → PNG 変換")
        self.resizable(True, False)
        self.minsize(560, 0)

        self.pdf_var = tk.StringVar()
        self.outdir_var = tk.StringVar()
        self.prefix_var = tk.StringVar()
        self.start_var = tk.StringVar(value="1")
        self.digits_var = tk.StringVar(value="0")
        self.dpi_var = tk.StringVar(value="150")
        self.preview_var = tk.StringVar()
        self.status_var = tk.StringVar(value="PDF を選択してください")

        self.doc = None
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.worker = None

        self._build()
        for v in (self.prefix_var, self.start_var, self.digits_var):
            v.trace_add("write", lambda *_: self._update_preview())
        self._update_preview()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- 画面構築 ----------
    def _build(self):
        f = ttk.Frame(self, padding=12)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(f, text="入力 PDF").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(f, textvariable=self.pdf_var, state="readonly").grid(
            row=row, column=1, sticky="ew", padx=6)
        ttk.Button(f, text="参照…", command=self._choose_pdf).grid(row=row, column=2)

        row += 1
        ttk.Label(f, text="出力先フォルダ").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(f, textvariable=self.outdir_var).grid(row=row, column=1, sticky="ew", padx=6)
        ttk.Button(f, text="参照…", command=self._choose_outdir).grid(row=row, column=2)

        row += 1
        ttk.Separator(f).grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)

        row += 1
        ttk.Label(f, text="ファイル名の文字列").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(f, textvariable=self.prefix_var).grid(
            row=row, column=1, columnspan=2, sticky="ew", padx=(6, 0))

        row += 1
        ttk.Label(f, text="連番の開始番号").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Spinbox(f, from_=0, to=999999, textvariable=self.start_var, width=10).grid(
            row=row, column=1, sticky="w", padx=6)

        row += 1
        ttk.Label(f, text="ゼロ埋め桁数").grid(row=row, column=0, sticky="w", pady=4)
        dg = ttk.Frame(f)
        dg.grid(row=row, column=1, sticky="w", padx=6)
        ttk.Spinbox(dg, from_=0, to=10, textvariable=self.digits_var, width=10).pack(side="left")
        ttk.Label(dg, text="  (0 = 自動)", foreground="gray").pack(side="left")

        row += 1
        ttk.Label(f, text="解像度 (DPI)").grid(row=row, column=0, sticky="w", pady=4)
        dp = ttk.Frame(f)
        dp.grid(row=row, column=1, sticky="w", padx=6)
        ttk.Combobox(dp, values=DPI_PRESETS, textvariable=self.dpi_var, width=8).pack(side="left")
        ttk.Label(dp, text="  (直接入力も可)", foreground="gray").pack(side="left")

        row += 1
        ttk.Label(f, text="出力例").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Label(f, textvariable=self.preview_var, foreground="#0a58ca").grid(
            row=row, column=1, columnspan=2, sticky="w", padx=6)

        row += 1
        ttk.Separator(f).grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)

        row += 1
        self.progress = ttk.Progressbar(f, mode="determinate")
        self.progress.grid(row=row, column=0, columnspan=3, sticky="ew")

        row += 1
        ttk.Label(f, textvariable=self.status_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))
        btns = ttk.Frame(f)
        btns.grid(row=row, column=2, sticky="e", pady=(8, 0))
        self.cancel_btn = ttk.Button(btns, text="中止", command=self.cancel.set, state="disabled")
        self.cancel_btn.pack(side="left", padx=(0, 6))
        self.run_btn = ttk.Button(btns, text="変換開始", command=self._start)
        self.run_btn.pack(side="left")

    # ---------- 入力 ----------
    def _choose_pdf(self):
        path = filedialog.askopenfilename(
            title="PDF を選択", filetypes=[("PDF ファイル", "*.pdf"), ("すべて", "*.*")])
        if path:
            self._load_pdf(Path(path))

    def _load_pdf(self, path: Path):
        try:
            doc = pymupdf.open(path)
        except Exception as e:
            messagebox.showerror("エラー", f"PDF を開けませんでした。\n{e}")
            return
        protected = doc.needs_pass
        if protected and not self._authenticate(doc, path.name):
            doc.close()
            return

        if self.doc:
            self.doc.close()
        self.doc = doc
        self.pdf_var.set(str(path))
        if not self.outdir_var.get():
            self.outdir_var.set(str(path.parent))
        self.prefix_var.set(f"{path.stem}_")
        self.status_var.set(f"{doc.page_count} ページ" + (" (パスワード解除済み)" if protected else ""))
        self.progress["value"] = 0
        self._update_preview()

    def _authenticate(self, doc, name):
        for attempt in range(3):
            msg = f"「{name}」はパスワードで保護されています。\nパスワードを入力してください。"
            if attempt:
                msg = "パスワードが正しくありません。\n" + msg
            pw = simpledialog.askstring("パスワード", msg, show="*", parent=self)
            if pw is None:
                return False
            if doc.authenticate(pw):
                return True
        messagebox.showerror("エラー", "認証に失敗しました。")
        return False

    def _choose_outdir(self):
        path = filedialog.askdirectory(title="出力先フォルダを選択")
        if path:
            self.outdir_var.set(path)

    def _int(self, var, name, minimum):
        try:
            v = int(var.get())
        except ValueError:
            raise ValueError(f"{name}には整数を入力してください。")
        if v < minimum:
            raise ValueError(f"{name}は {minimum} 以上を指定してください。")
        return v

    def _digits(self, start, count):
        d = int(self.digits_var.get() or 0)
        return d if d > 0 else len(str(start + max(count, 1) - 1))

    def _update_preview(self):
        try:
            start = int(self.start_var.get())
            count = self.doc.page_count if self.doc else 1
            d = self._digits(start, count)
            first = f"{self.prefix_var.get()}{start:0{d}d}.png"
            if count > 1:
                first += f"  …  {self.prefix_var.get()}{start + count - 1:0{d}d}.png"
            self.preview_var.set(first)
        except ValueError:
            self.preview_var.set("—")

    # ---------- 変換 ----------
    def _start(self):
        if not self.doc:
            messagebox.showwarning("確認", "PDF を選択してください。")
            return
        try:
            start = self._int(self.start_var, "開始番号", 0)
            self._int(self.digits_var, "ゼロ埋め桁数", 0)
            dpi = self._int(self.dpi_var, "解像度", 1)
        except ValueError as e:
            messagebox.showerror("入力エラー", str(e))
            return
        if dpi > 2400:
            messagebox.showerror("入力エラー", "解像度は 2400 以下を指定してください。")
            return
        prefix = self.prefix_var.get()
        if any(c in prefix for c in '\\/:*?"<>|'):
            messagebox.showerror("入力エラー", 'ファイル名に \\ / : * ? " < > | は使えません。')
            return
        outdir = Path(self.outdir_var.get() or ".")
        count = self.doc.page_count
        digits = self._digits(start, count)
        names = [outdir / f"{prefix}{start + i:0{digits}d}.png" for i in range(count)]

        existing = [p for p in names if p.exists()]
        if existing and not messagebox.askyesno(
                "上書き確認", f"{len(existing)} 個のファイルが既に存在します。上書きしますか？"):
            return
        try:
            outdir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            messagebox.showerror("エラー", f"出力先フォルダを作成できませんでした。\n{e}")
            return

        self.cancel.clear()
        self.progress.configure(maximum=count, value=0)
        self._set_running(True)
        self.worker = threading.Thread(
            target=self._convert, args=(self.doc, names, dpi), daemon=True)
        self.worker.start()
        self.after(50, self._poll)

    def _convert(self, doc, names, dpi):
        """別スレッドで実行。GUI の更新は events キュー経由で行う。"""
        try:
            for i, (page, out) in enumerate(zip(doc, names)):
                if self.cancel.is_set():
                    self.events.put(("cancelled", i))
                    return
                page.get_pixmap(dpi=dpi).save(out)
                self.events.put(("progress", i + 1, len(names)))
            self.events.put(("done", names[0].parent, len(names)))
        except Exception as e:
            self.events.put(("error", e))

    def _poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                kind = ev[0]
                if kind == "progress":
                    self.progress["value"] = ev[1]
                    self.status_var.set(f"変換中… {ev[1]} / {ev[2]}")
                    continue
                self._set_running(False)
                if kind == "done":
                    self.status_var.set(f"完了: {ev[2]} ページ")
                    messagebox.showinfo("完了", f"{ev[2]} ページを出力しました。\n{ev[1]}")
                elif kind == "cancelled":
                    self.status_var.set(f"中止しました ({ev[1]} ページ出力済み)")
                else:
                    self.status_var.set("エラー")
                    messagebox.showerror("エラー", f"変換中にエラーが発生しました。\n{ev[1]}")
                return
        except queue.Empty:
            pass
        self.after(50, self._poll)

    def _set_running(self, running):
        self.run_btn.configure(state="disabled" if running else "normal")
        self.cancel_btn.configure(state="normal" if running else "disabled")

    def _on_close(self):
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno("確認", "変換中です。中止して終了しますか？"):
                return
            self.cancel.set()
            self.worker.join()
        if self.doc:
            self.doc.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
