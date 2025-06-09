#!/usr/bin/env python3
"""
Select files – or entire folders – from many locations, add them to a cart, and
export every chosen file (with its full path) into one UTF‑8 text document
stored in ./combined_files/.

➤ NEW FEATURE (June 2025)
   • If you highlight a folder in the navigator and click ➕ **Add**, the script
     adds *every* regular file immediately inside that folder to the cart.
   • You can still browse into a folder (double‑click / Enter) when you really
     need to cherry‑pick specific files.
   • Cart shows a flat list of absolute paths. Remove any entry with the ➖
     button before exporting.

No external libraries required.
"""

import os
import pathlib
from datetime import datetime
import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as mb

# ─────────────────────────  CONFIG  ─────────────────────────
TK_SCALING      = 2.1   # UI scale factor for Hi‑DPI / WSL
HEADER_RULE_LEN = 80    # width of ===== rule under each header line

# ─────────────────────  FILE NAVIGATOR UI  ──────────────────
class FileNavigator(tk.Toplevel):
    """Dual‑pane selector: left = navigator / right = cart."""

    def __init__(self, master, start_dir=None):
        super().__init__(master)
        self.title("Select Files or Folders for TXT Export")
        self.geometry("1000x600")

        # State
        self.current_dir = pathlib.Path(start_dir or pathlib.Path.home())
        self.cart_files: list[pathlib.Path] = []

        # UI setup
        self._build_widgets()
        self._refresh()

        # Keyboard shortcuts
        self.nav_list.bind("<Double-1>", self._enter_dir)
        self.nav_list.bind("<Return>",   self._enter_dir)
        self.bind("<BackSpace>", lambda _e: self._go_up())

    # ── UI LAYOUT ────────────────────────────────────────────
    def _build_widgets(self):
        self.columnconfigure(0, weight=1)      # navigator column
        self.columnconfigure(2, weight=1)      # cart column
        self.rowconfigure(2, weight=1)         # lists stretch vertically

        # Current path label
        self.path_var = tk.StringVar()
        tk.Label(self, textvariable=self.path_var, anchor="w", relief="sunken")\
            .grid(row=0, column=0, columnspan=3, sticky="ew", padx=6, pady=(6, 2))

        # Toolbar (Back / Home)
        bar = tk.Frame(self)
        bar.grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 6))
        tk.Button(bar, text="⬅ Back",  command=self._go_up).pack(side="left")
        tk.Button(bar, text="🏠 Home", command=self._go_home).pack(side="left", padx=(4, 0))

        mono = tkfont.Font(family="Courier", size=10)

        # Navigator list (left)
        self.nav_list = tk.Listbox(self, selectmode="extended", font=mono, activestyle="none")
        nav_sb = tk.Scrollbar(self, command=self.nav_list.yview)
        self.nav_list.config(yscrollcommand=nav_sb.set)
        self.nav_list.grid(row=2, column=0, sticky="nsew", padx=(6, 0))
        nav_sb.grid(row=2, column=1, sticky="ns")

        # Cart list (right)
        self.cart_list = tk.Listbox(self, font=mono, activestyle="none")
        cart_sb = tk.Scrollbar(self, command=self.cart_list.yview)
        self.cart_list.config(yscrollcommand=cart_sb.set)
        self.cart_list.grid(row=2, column=2, sticky="nsew", padx=(6, 6))
        cart_sb.grid(row=2, column=3, sticky="ns", padx=(0, 6))

        # Add / Remove buttons between lists
        mid = tk.Frame(self)
        mid.grid(row=2, column=1, sticky="n")
        tk.Button(mid, text="➕", width=3, command=self._add_selected).pack(pady=(50, 5))
        tk.Button(mid, text="➖", width=3, command=self._remove_selected).pack()

        # Bottom action buttons
        bottom = tk.Frame(self)
        bottom.grid(row=3, column=0, columnspan=4, sticky="ew", padx=6, pady=6)
        bottom.columnconfigure(0, weight=1)
        tk.Button(bottom, text="Cancel", command=self._cancel).grid(row=0, column=0, sticky="w")
        tk.Button(bottom, text="Generate TXT", command=self._accept).grid(row=0, column=1, sticky="e")

    # ── DIRECTORY NAVIGATION ─────────────────────────────────
    def _refresh(self):
        """Populate navigator list with dirs first, then files."""
        self.nav_list.delete(0, tk.END)
        self.path_var.set(str(self.current_dir))

        try:
            entries = sorted(os.listdir(self.current_dir), key=str.lower)
        except PermissionError:
            mb.showerror("Error", f"No permission for {self.current_dir}")
            self._go_up(); return

        for name in entries:
            p = self.current_dir / name
            if p.is_dir():
                self.nav_list.insert(tk.END, f"[DIR] {name}")
        for name in entries:
            p = self.current_dir / name
            if p.is_file():
                self.nav_list.insert(tk.END, name)

    def _enter_dir(self, _event=None):
        sel = self.nav_list.curselection()
        if not sel:
            return
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

    # ── CART MANAGEMENT ──────────────────────────────────────
    def _add_selected(self):
        """Add highlighted items to the cart.
        • Regular files → added directly.
        • Folders      → every direct file inside the folder is added.
        """
        for idx in self.nav_list.curselection():
            entry = self.nav_list.get(idx)
            if entry.startswith("[DIR] "):
                # Folder – add each *file* immediately inside (non‑recursive)
                folder_path = self.current_dir / entry[6:]
                for child in sorted(folder_path.iterdir()):
                    if child.is_file() and child not in self.cart_files:
                        self.cart_files.append(child)
                        self.cart_list.insert(tk.END, str(child))
            else:
                # Single file
                file_path = self.current_dir / entry
                if file_path not in self.cart_files:
                    self.cart_files.append(file_path)
                    self.cart_list.insert(tk.END, str(file_path))

    def _remove_selected(self):
        for idx in reversed(self.cart_list.curselection()):
            path = pathlib.Path(self.cart_list.get(idx))
            self.cart_files.remove(path)
            self.cart_list.delete(idx)

    # ── FINISH / CANCEL ─────────────────────────────────────
    def _accept(self):
        if not self.cart_files:
            mb.showwarning("Nothing selected", "Add at least one file.")
            return
        self.selected_files = self.cart_files
        self.destroy()

    def _cancel(self):
        self.selected_files = []
        self.destroy()

# ────────────────────  TXT EXPORTER  ────────────────────────

def export_to_txt(paths: list[pathlib.Path], out_txt: pathlib.Path):
    """Write every file to a single UTF‑8 text document."""
    with out_txt.open("w", encoding="utf-8", newline="\n") as fh:
        for path in paths:
            header = str(path)
            rule = "=" * min(HEADER_RULE_LEN, len(header))
            fh.write(f"{header}\n{rule}\n\n")
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_bytes().decode("latin-1")
            fh.write(text.rstrip() + "\n\n")
    print(f"✅  TXT file created: {out_txt}")

# ───────────────────────────  MAIN  ─────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.tk.call("tk", "scaling", TK_SCALING)
    root.withdraw()

    picker = FileNavigator(root)
    root.wait_window(picker)

    if not picker.selected_files:
        print("No files selected; exiting.")
        exit()

    out_dir = pathlib.Path.cwd() / "combined_files"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_txt = out_dir / f"combined_files_{ts}.txt"

    try:
        export_to_txt(picker.selected_files, out_txt)
        mb.showinfo("Done", f"TXT saved to:\n{out_txt}")
    except Exception as exc:
        mb.showerror("Error", f"Failed:\n{exc}")
