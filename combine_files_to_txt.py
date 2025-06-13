#!/usr/bin/env python3
"""
Modern file-stitcher (text export)
─────────────────────────────────
• Pick individual files *or* entire folders (recursively).
• Optional extension filter (`py,tf,yaml` …).
• Binary files skipped automatically.
• Outputs one UTF-8 `.txt` in ./combined_files/.
• Includes per-directory search filter.

Emoji are avoided so the interface renders even on minimal fonts.
"""

from __future__ import annotations
import os
import pathlib
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb
from typing import Iterable

# ────────────── CONFIG ──────────────
TK_SCALING = 2.1
HEADER_RULE = 80                   # ===== length
BINARY_SAMPLE = 2048               # bytes to sniff
NON_PRINTABLE_THRESHOLD = 0.30     # >30 % non‑printables → binary
FOLDER_PREFIX = "DIR▶ "            # navigator prefix for folders

# ────────────── GUI CLASS ───────────
class FileNavigator(ttk.Frame):
    """Navigator (left) + Cart (right)"""

    def __init__(self, master: tk.Tk, start_dir: str | pathlib.Path | None = None):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        master.title("Select Files / Folders for TXT Export")
        master.geometry("1120x700")
        master.tk.call("tk", "scaling", TK_SCALING)

        # state
        self.current_dir = pathlib.Path(start_dir or pathlib.Path.home())
        self.cart_files: list[pathlib.Path] = []
        self.ext_filter = tk.StringVar()
        self.name_filter = tk.StringVar()

        self._build_ui()
        self._refresh()

        self.nav.bind("<Double-1>", self._enter_dir)
        self.nav.bind("<Return>", self._enter_dir)
        master.bind("<BackSpace>", lambda _: self._go_up())

    # ---------- UI BUILD ----------
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

        # path label
        self.path_var = tk.StringVar()
        ttk.Label(self, textvariable=self.path_var, anchor="w", relief="sunken")\
            .grid(row=0, column=0, columnspan=4, sticky="ew", padx=6, pady=(6, 2))

        # toolbar (ext filter)
        bar = ttk.Frame(self)
        bar.grid(row=1, column=0, columnspan=4, sticky="ew", padx=6, pady=(0, 4))
        ttk.Button(bar, text="← Back", command=self._go_up).pack(side="left")
        ttk.Button(bar, text="Home", command=self._go_home).pack(side="left", padx=(4, 8))
        ttk.Label(bar, text="Ext filter:").pack(side="left")
        ttk.Entry(bar, textvariable=self.ext_filter, width=20).pack(side="left")
        ttk.Label(bar, text="  (comma-sep, blank = all)").pack(side="left")

        # search bar (file/folder name)
        searchbar = ttk.Frame(self)
        searchbar.grid(row=2, column=0, columnspan=4, sticky="ew", padx=6, pady=(0, 4))
        ttk.Label(searchbar, text="Search in folder:").pack(side="left")
        search_entry = ttk.Entry(searchbar, textvariable=self.name_filter, width=30)
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", lambda _: self._refresh())

        mono = ("Courier New", 10)

        # navigator list
        self.nav = tk.Listbox(self, selectmode="extended", activestyle="none", font=mono)
        nav_sb = ttk.Scrollbar(self, command=self.nav.yview)
        self.nav.config(yscrollcommand=nav_sb.set)
        self.nav.grid(row=3, column=0, sticky="nsew", padx=(6, 0))
        nav_sb.grid(row=3, column=1, sticky="ns")

        # cart list
        self.cart = tk.Listbox(self, activestyle="none", font=mono)
        cart_sb = ttk.Scrollbar(self, command=self.cart.yview)
        self.cart.config(yscrollcommand=cart_sb.set)
        self.cart.grid(row=3, column=2, sticky="nsew", padx=(6, 6))
        cart_sb.grid(row=3, column=3, sticky="ns", padx=(0, 6))

        # mid buttons
        mid = ttk.Frame(self); mid.grid(row=3, column=1, sticky="n")
        ttk.Button(mid, text="Add", width=6, command=self._add_selected).pack(pady=(50, 5))
        ttk.Button(mid, text="Remove", width=6, command=self._remove_selected).pack()

        # bottom buttons
        bottom = ttk.Frame(self)
        bottom.grid(row=4, column=0, columnspan=4, sticky="ew", padx=6, pady=6)
        bottom.columnconfigure(0, weight=1)
        ttk.Button(bottom, text="Cancel", command=self._cancel).grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text="Generate TXT", command=self._accept).grid(row=0, column=1, sticky="e")

    # ---------- NAVIGATION ----------
    def _refresh(self):
        self.nav.delete(0, tk.END)
        self.path_var.set(str(self.current_dir))
        try:
            entries = sorted(os.listdir(self.current_dir), key=str.lower)
        except PermissionError:
            mb.showerror("Error", f"No permission for {self.current_dir}")
            self._go_up(); return

        search = self.name_filter.get().strip().lower()
        for name in entries:
            if search and search not in name.lower():
                continue
            p = self.current_dir / name
            if p.is_dir():
                self.nav.insert(tk.END, f"{FOLDER_PREFIX}{name}/")
        for name in entries:
            if search and search not in name.lower():
                continue
            if (self.current_dir / name).is_file():
                self.nav.insert(tk.END, name)

    def _enter_dir(self, _=None):
        sel = self.nav.curselection()
        if not sel:
            return
        entry = self.nav.get(sel[0])
        if entry.startswith(FOLDER_PREFIX):
            folder = entry[len(FOLDER_PREFIX):].rstrip("/")
            self.current_dir = self.current_dir / folder
            self.name_filter.set("")
            self._refresh()

    def _go_up(self):
        if self.current_dir.parent != self.current_dir:
            self.current_dir = self.current_dir.parent
            self.name_filter.set("")
            self._refresh()

    def _go_home(self):
        self.current_dir = pathlib.Path.home()
        self.name_filter.set("")
        self._refresh()

    def _allowed_ext(self, path: pathlib.Path) -> bool:
        raw = self.ext_filter.get().strip()
        if not raw:
            return True
        allowed = {f".{e.strip().lstrip('.').lower()}" for e in raw.split(',') if e.strip()}
        return path.suffix.lower() in allowed

    def _is_binary(self, path: pathlib.Path) -> bool:
        try:
            chunk = path.read_bytes()[:BINARY_SAMPLE]
        except Exception:
            return True
        if b"\x00" in chunk:
            return True
        non_print = sum(b < 32 and b not in (9, 10, 13) or b == 127 for b in chunk)
        return len(chunk) > 0 and (non_print / len(chunk)) > NON_PRINTABLE_THRESHOLD

    def _should_include(self, path: pathlib.Path) -> bool:
        return self._allowed_ext(path) and not self._is_binary(path)

    def _add_selected(self):
        for idx in self.nav.curselection():
            entry = self.nav.get(idx)
            if entry.startswith(FOLDER_PREFIX):
                folder = self.current_dir / entry[len(FOLDER_PREFIX):].rstrip("/")
                self._add_folder(folder)
            else:
                fp = self.current_dir / entry
                if fp.is_file() and self._should_include(fp):
                    self._add_to_cart(fp)

    def _add_folder(self, folder: pathlib.Path):
        for f in _iter_files_recursive(folder):
            if self._should_include(f):
                self._add_to_cart(f)

    def _add_to_cart(self, path: pathlib.Path):
        if path not in self.cart_files:
            self.cart_files.append(path)
            self.cart.insert(tk.END, str(path))

    def _remove_selected(self):
        for idx in reversed(self.cart.curselection()):
            path = pathlib.Path(self.cart.get(idx))
            self.cart_files.remove(path)
            self.cart.delete(idx)

    def _accept(self):
        if not self.cart_files:
            mb.showwarning("Nothing selected", "Cart is empty.")
            return
        self.master.selected_files = self.cart_files
        self.master.destroy()

    def _cancel(self):
        self.master.selected_files = []
        self.master.destroy()


def _iter_files_recursive(folder: pathlib.Path) -> Iterable[pathlib.Path]:
    for root, _dirs, files in os.walk(folder):
        for fname in files:
            yield pathlib.Path(root) / fname


def create_txt(paths: Iterable[pathlib.Path], out: pathlib.Path):
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for p in paths:
            header = str(p)
            fh.write(f"\n{header}\n{'=' * min(HEADER_RULE, len(header))}\n\n")
            try:
                fh.write(p.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                fh.write(p.read_bytes().decode("latin-1"))
            fh.write("\n")
    print("✓ Exported:", out)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileNavigator(root)
    root.mainloop()

    if getattr(root, "selected_files", None):
        dest_dir = pathlib.Path.cwd() / "combined_files"
        dest_dir.mkdir(exist_ok=True)
        dest_file = dest_dir / f"combined_{datetime.now():%Y-%m-%d_%H-%M-%S}.txt"
        try:
            create_txt(root.selected_files, dest_file)
            mb.showinfo("Done", f"Saved:\n{dest_file}")
        except Exception as exc:
            mb.showerror("Error", str(exc))
    else:
        print("No files selected.")
