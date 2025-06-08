#!/usr/bin/env python3
"""
Select files from many folders, add them to a cart, and export them
(all with full paths) into a single PDF stored in ./combined_files/.
Handles Unicode (emoji, non-Latin) via fpdf2 + DejaVuSansMono.ttf.
"""

import os
import pathlib
from datetime import datetime

# ── Tkinter imports
import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as mb

# ── PDF lib (fpdf2)
from fpdf import FPDF   # pip install fpdf2

# ─────────────────────────  CONFIG  ─────────────────────────
TK_SCALING       = 2.1                      # UI scale factor
PDF_FONT_SIZE    = 10
PDF_LINE_HEIGHT  = 6
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

# ─────────────────────  FILE NAVIGATOR UI  ──────────────────
class FileNavigator(tk.Toplevel):
    """Dual-pane: left = file browser, right = cart."""
    def __init__(self, master, start_dir=None):
        super().__init__(master)
        self.title("Select Files for PDF")
        self.geometry("1000x600")

        self.current_dir   = pathlib.Path(start_dir or pathlib.Path.home())
        self.cart_files: list[pathlib.Path] = []

        self._build_widgets()
        self._refresh()

        # shortcuts
        self.nav_list.bind("<Double-1>", self._enter_dir)
        self.nav_list.bind("<Return>",   self._enter_dir)
        self.bind("<BackSpace>", lambda e: self._go_up())

    # ----- UI -------------------------------------------------------------
    def _build_widgets(self):
        self.columnconfigure(0, weight=1)          # nav pane
        self.columnconfigure(2, weight=1)          # cart pane
        self.rowconfigure(2, weight=1)

        self.path_var = tk.StringVar()
        tk.Label(self, textvariable=self.path_var, anchor="w",
                 relief="sunken").grid(row=0, column=0, columnspan=3,
                                       sticky="ew", padx=6, pady=(6,2))

        bar = tk.Frame(self)
        bar.grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=(0,6))
        tk.Button(bar, text="⬅ Back",  command=self._go_up).pack(side="left")
        tk.Button(bar, text="🏠 Home", command=self._go_home)\
            .pack(side="left", padx=(4,0))

        mono = tkfont.Font(family="Courier", size=10)

        # left list = navigator
        self.nav_list = tk.Listbox(self, selectmode="extended",
                                   activestyle="none", font=mono)
        nav_sb = tk.Scrollbar(self, command=self.nav_list.yview)
        self.nav_list.config(yscrollcommand=nav_sb.set)
        self.nav_list.grid(row=2, column=0, sticky="nsew", padx=(6,0))
        nav_sb.grid(row=2, column=1, sticky="ns")

        # right list = cart
        self.cart_list = tk.Listbox(self, activestyle="none", font=mono)
        cart_sb = tk.Scrollbar(self, command=self.cart_list.yview)
        self.cart_list.config(yscrollcommand=cart_sb.set)
        self.cart_list.grid(row=2, column=2, sticky="nsew", padx=(6,6))
        cart_sb.grid(row=2, column=3, sticky="ns", padx=(0,6))

        # middle add / remove buttons
        mid = tk.Frame(self)
        mid.grid(row=2, column=1, sticky="n")
        tk.Button(mid, text="➕", width=3, command=self._add_selected)\
            .pack(pady=(50,5))
        tk.Button(mid, text="➖", width=3, command=self._remove_selected)\
            .pack()

        # bottom buttons
        bottom = tk.Frame(self)
        bottom.grid(row=3, column=0, columnspan=4, sticky="ew", padx=6, pady=6)
        bottom.columnconfigure(0, weight=1)
        tk.Button(bottom, text="Cancel", command=self._cancel)\
            .grid(row=0, column=0, sticky="w")
        tk.Button(bottom, text="Generate PDF", command=self._accept)\
            .grid(row=0, column=1, sticky="e")

    # ----- directory navigation ------------------------------------------
    def _refresh(self):
        self.nav_list.delete(0, tk.END)
        self.path_var.set(str(self.current_dir))

        try:
            entries = sorted(os.listdir(self.current_dir), key=str.lower)
        except PermissionError:
            mb.showerror("Error", f"No permission for {self.current_dir}")
            self._go_up(); return

        # folders then files
        for n in entries:
            p = self.current_dir / n
            if p.is_dir():
                self.nav_list.insert(tk.END, f"[DIR] {n}")
        for n in entries:
            p = self.current_dir / n
            if p.is_file():
                self.nav_list.insert(tk.END, n)

    def _enter_dir(self, *_):
        sel = self.nav_list.curselection()
        if not sel: return
        text = self.nav_list.get(sel[0])
        if text.startswith("[DIR] "):
            self.current_dir /= text[6:]
            self._refresh()

    def _go_up(self):
        if self.current_dir.parent != self.current_dir:
            self.current_dir = self.current_dir.parent
            self._refresh()

    def _go_home(self):
        self.current_dir = pathlib.Path.home()
        self._refresh()

    # ----- cart operations -----------------------------------------------
    def _add_selected(self):
        for idx in self.nav_list.curselection():
            name = self.nav_list.get(idx)
            if name.startswith("[DIR] "): continue
            path = self.current_dir / name
            if path not in self.cart_files:
                self.cart_files.append(path)
                self.cart_list.insert(tk.END, str(path))

    def _remove_selected(self):
        for idx in reversed(self.cart_list.curselection()):
            path = pathlib.Path(self.cart_list.get(idx))
            self.cart_files.remove(path)
            self.cart_list.delete(idx)

    # ----- dialog finish --------------------------------------------------
    def _accept(self):
        if not self.cart_files:
            mb.showwarning("Nothing selected",
                           "Add at least one file to the list.")
            return
        self.selected_files = self.cart_files
        self.destroy()

    def _cancel(self):
        self.selected_files = []
        self.destroy()

# ─────────────────────  PDF CREATOR (Unicode)  ───────────────────────────────
def create_pdf(paths, out_pdf):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True) 
    pdf.set_font("DejaVu", size=PDF_FONT_SIZE)

    for p in paths:
        pdf.set_font("DejaVu", style="B", size=PDF_FONT_SIZE + 1)
        pdf.multi_cell(0, PDF_LINE_HEIGHT + 2, str(p))
        pdf.ln(1)

        pdf.set_font("DejaVu", size=PDF_FONT_SIZE)
        try:
            txt = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            txt = p.read_bytes().decode("latin-1")
        pdf.multi_cell(0, PDF_LINE_HEIGHT, txt)
        pdf.ln(2)

    pdf.output(str(out_pdf))
    print(f"✅  PDF created: {out_pdf}")

# ───────────────────────────  MAIN  ─────────────────────────────────────────-
if __name__ == "__main__":
    root = tk.Tk()
    root.tk.call("tk", "scaling", TK_SCALING)
    root.withdraw()

    picker = FileNavigator(root)
    root.wait_window(picker)

    if not picker.selected_files:
        print("No files selected; exiting.")
        exit(0)

    out_dir = pathlib.Path.cwd() / "combined_files"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"combined_files_{ts}.pdf"

    try:
        create_pdf(picker.selected_files, out_file)
        mb.showinfo("Done", f"PDF saved to:\n{out_file}")
    except Exception as e:
        mb.showerror("Error", f"Failed:\n{e}")
