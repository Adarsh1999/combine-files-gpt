# Combine-Files-GPT

Combine-Files-GPT is a tiny desktop utility (Tkinter GUI) that lets you pick **any mix of files and/or folders** and instantly export their human-readable contents into **one UTF-8 `.txt` file**.  
It is ideal for quickly sharing snippets, archiving configuration files, or pasting multi-file examples into chat apps without having to zip everything up first.

---

## Features

* **Drag-and-drop style navigator** – browse the file-system, double-click folders, press <kbd>Backspace</kbd> to go up.
* **Recursive folder support** – add an entire directory and all sub-files are included.
* **Extension filter** – type e.g. `py,tf,yaml` to only capture specific file-types.
* **Binary-file detection** – prevents garbled output by automatically skipping binaries.
* **One-click export** – generates `combined_<timestamp>.txt` inside the `combined_files/` folder next to the script.

A typical header inside the export looks like this:

```text
/home/user/project/app/main.py
========================================
<file contents here>
```

---

## Quick start

```bash
# 1. Clone or download the repo
$ git clone https://github.com/your-handle/combine-files-gpt.git
$ cd combine-files-gpt

# 2. (Optional but recommended) create an isolated environment
$ python3 -m venv venv
$ source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install runtime requirements (currently none outside the standard library)
$ pip install -r requirements.txt

# 4. Run the app
$ python combine_files_to_txt.py
```

A window will appear.  Navigate to the desired directory, select files/folders, then click **“Generate TXT”**.  The resulting file opens automatically and is also written to the `combined_files/` directory.

---

## Script outline

The application lives entirely in [`combine_files_to_txt.py`](combine_files_to_txt.py) (≈250 LOC) and contains two main components:

1. `FileNavigator` – a `ttk.Frame` subclass that implements the dual-pane **navigator / cart** interface.
2. `create_txt()` – streams selected paths to the output file, adding a neat header before each file’s contents.

No external GUI libraries are required; everything is powered by Python’s built-in **Tkinter**.

---

## Testing

Because the tool is GUI-centric, there is no formal test-suite.  However you can quickly validate functionality by:

1. Running the script, selecting a few files and generating a TXT export.
2. Opening the generated file and confirming each source file appears with the correct header.

---

## Contributing

Contributions are welcome!  Feel free to open issues or submit pull-requests for bugs, feature requests, or improvements (e.g. dark mode, CLI batch-mode, PDF export, etc.).

---

## License

This project is released under the MIT License.  See [LICENSE](LICENSE) for details.
