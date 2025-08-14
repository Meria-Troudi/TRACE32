import os
import sys
import tempfile
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
def ensure_config(force: bool = False) -> configparser.ConfigParser:
    """
    Guarantee that CONFIG_PATH exists and contains all required fields.
    If `force` is True, or if any required field is missing/empty,
    launches the ConfigWizard to let the user fill them in.
    Returns the loaded ConfigParser.
    """
    cfg = configparser.RawConfigParser()
    # create empty file if missing
    if not os.path.isfile(CONFIG_PATH):
        open(CONFIG_PATH, "a").close()

    cfg.read(CONFIG_PATH)

    # list of (section, key) pairs you know your wizard writes
    required = [
        ("paths", "trace32_exe"),
        ("paths", "trace32_dll"),
        ("paths", "trace32_config"),
        ("paths", "canoe_cfg"),
        ("paths", "tmp_dir"),
        ("paths", "cli"),
    ]

    missing = []
    for section, key in required:
        if not (cfg.has_section(section) and cfg.has_option(section, key) and cfg.get(section, key).strip()):
            missing.append((section, key))

    if force or missing:
        # launch wizard
        root = tk.Tk()
        root.title("Configuration Wizard")
        root.geometry("600x600")
        ConfigWizard(root).pack(fill="both", expand=True)
        root.mainloop()

        # reload after wizard
        cfg = configparser.RawConfigParser()
        cfg.read(CONFIG_PATH)
        # re-check
        still_missing = []
        for section, key in required:
            if not (cfg.has_section(section) and cfg.has_option(section, key) and cfg.get(section, key).strip()):
                still_missing.append((section, key))
        if still_missing:
            messagebox.showerror(
                "Configuration Error",
                f"The following settings are still missing: {still_missing}\n"
                "Please re-run with --reconfigure and fill them."
            )
            sys.exit(1)

    return cfg

def get_app_folder():
    """
    Returns the folder where the EXE is located (not the PyInstaller temp folder).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

# Path to config.ini (always next to our exe or script)
APP_DIR = get_app_folder()
CONFIG_PATH = os.path.join(APP_DIR, "config.ini")

def try_local_file(*relative_path):
    """
    Look for a file relative to the EXE/script location.
    """
    path = os.path.join(get_app_folder(), *relative_path)
    return path if os.path.isfile(path) else ""

def fast_find(filename, roots=["C:\\"], max_depth=10):
    exclude = {"Windows", "Program Files", "Program Files (x86)",
               "$Recycle.Bin", "System Volume Information", "System32"}

    def search(path, depth):
        if depth > max_depth:
            return None
        try:
            with os.scandir(path) as entries:
                dirs = []
                for entry in entries:
                    if entry.name in exclude and entry.is_dir():
                        continue
                    if entry.is_file() and entry.name.lower() == filename.lower():
                        return entry.path
                    if entry.is_dir():
                        dirs.append(entry.path)
                for d in dirs:
                    res = search(d, depth + 1)
                    if res:
                        return res
        except (PermissionError, FileNotFoundError):
            pass
        return None

    for root in roots:
        found = search(root, 0)
        if found:
            return found
    return None

def get_trace32_exe():
    exe_path = try_local_file("bin", "windows64", "t32marm.exe") or fast_find("t32marm.exe")
    if not exe_path:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Not Found", "TRACE32 Executable not found automatically.\nPlease select it manually.")
        exe_path = filedialog.askopenfilename(title="Select TRACE32 Executable", filetypes=[("Executable files", "*.exe")]) or ""
        root.destroy()
    return exe_path or ""

def get_trace32_dll():
    return try_local_file("dll", "t32api64.dll") or fast_find("t32api64.dll") or ""

def get_trace32_config():
    return try_local_file("config.t32") or fast_find("T32_1000005.t32") or ""

def get_canoe_cfg():
    return os.path.join(get_app_folder(), "canoe", "Configuration1.cfg")
class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class ConfigWizard(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller

        style = ttk.Style(self)
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"), foreground="#007acc")
        style.configure("Desc.TLabel", font=("Segoe UI", 9), foreground="#555555")

        intro_text = (
            "Welcome to the Project Configuration Wizard.\n"
            "Fill in or confirm the fields below to set up the project."
        )
        intro = ttk.Label(self, text=intro_text, style="Desc.TLabel", justify="center")
        intro.pack(pady=(10, 15), padx=15)

        self.items = [
            ("paths", "trace32_exe",    "TRACE32 Executable:",    get_trace32_exe,    True,  "Main executable for TRACE32."),
            ("paths", "trace32_dll",    "TRACE32 DLL (t32api64.dll):", get_trace32_dll,    True,  "DLL file required by TRACE32 API."),
            ("paths", "trace32_config","TRACE32 Config (.t32):", get_trace32_config, True,  "Configuration file for TRACE32."),
            ("paths", "canoe_cfg",      "CANoe Config (Configuration1.cfg):", get_canoe_cfg, True, "Configuration file for CANoe."),
            ("paths", "tmp_dir",        "Temp Directory:",         tempfile.gettempdir, True, "Directory for temporary files."),
            ("paths", "cli",            "CLI Server Script:",      lambda: os.path.join(get_app_folder(), "CLI.py"), True, "Path to the Python CLI server script."),
        ]

        self.vars = {}
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self._build_ui()
        self._load_existing()   # <-- now uses only valid saved paths, else detected
        self._fill_defaults()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Save & Exit", command=self._on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel",    command=self._on_cancel).pack(side="left")
        ttk.Button(btn_frame, text="Refresh Detection", command=self._refresh_detection).pack(side="left", padx=5)

    def _load_existing(self):
        cfg = configparser.RawConfigParser()
        saved_values = {}
        if os.path.isfile(CONFIG_PATH):
            cfg.read(CONFIG_PATH)
            for key in self.vars:
                sec, k = key.split('.', 1)
                if cfg.has_option(sec, k):
                    saved_values[key] = cfg.get(sec, k)

        detected_values = {}
        for sec, key, _, default, _, _ in self.items:
            key_full = f"{sec}.{key}"
            val = default() if callable(default) else default
            detected_values[key_full] = val or ""

        for key, var in self.vars.items():
            sec, k = key.split('.', 1)
            saved = saved_values.get(key, "").strip()
            detected = detected_values.get(key, "")
            # only accept saved if it still exists
            if saved:
                if (k.endswith("_dir") and os.path.isdir(saved)) or (not k.endswith("_dir") and os.path.isfile(saved)):
                    var.set(saved)
                    continue
            # otherwise use detection
            var.set(detected)
    def _build_ui(self):
        container = self.scroll_frame.scrollable_frame
        sections_seen = set()
        row = 0
        for sec, key, label, default, browse_btn, desc in self.items:
            if sec not in sections_seen:
                header = ttk.Label(container, text=sec.upper(), style="Section.TLabel")
                header.grid(row=row, column=0, sticky="w", pady=(10, 5), padx=3, columnspan=3)
                sections_seen.add(sec)
                row += 1

            ttk.Label(container, text=label).grid(row=row, column=0, sticky="w", pady=6, padx=3)

            var = tk.StringVar()
            entry = ttk.Entry(container, textvariable=var, width=58)
            entry.grid(row=row, column=1, padx=5)

            if browse_btn:
                btn = ttk.Button(container, text="Browse", width=7,
                                 command=lambda v=var, fn=filedialog.askopenfilename: self._browse_and_set(v, fn))
                btn.grid(row=row, column=2, padx=(0, 10))

            desc_label = ttk.Label(container, text=desc, style="Desc.TLabel")
            desc_label.grid(row=row + 1, column=0, columnspan=3, sticky="w", padx=5, pady=(0, 6))

            self.vars[f"{sec}.{key}"] = var
            row += 2

    def _browse_and_set(self, var, browse_fn):
        selected = browse_fn()
        if selected:
            var.set(selected)



    def _refresh_detection(self):
        updated_any = False
        for sec, key, _, default, _, _ in self.items:
            key_full = f"{sec}.{key}"
            if callable(default):
                val = default()
                if val and self.vars[key_full].get() != val:
                    self.vars[key_full].set(val)
                    updated_any = True
        if updated_any:
            messagebox.showinfo("Detection Refreshed", "Paths have been updated with detected values.")
        else:
            messagebox.showinfo("Detection", "No new detected paths found.")

    def _fill_defaults(self):
        for sec, key, _, default, _, _ in self.items:
            key_full = f"{sec}.{key}"
            if key_full in self.vars and not self.vars[key_full].get():
                val = default() if callable(default) else default
                self.vars[key_full].set(val or "")

    def _on_save(self):
        cfg = configparser.RawConfigParser()
        for key in self.vars:
            sec, k = key.split('.', 1)
            if not cfg.has_section(sec):
                cfg.add_section(sec)
            cfg.set(sec, k, self.vars[key].get())
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            cfg.write(f)
        print("[ConfigWizard] Saved values:")
        for key in self.vars:
            print(f"  {key} = {self.vars[key].get()}")
        messagebox.showinfo("Saved", f"Configuration saved to:\n{CONFIG_PATH}")
        self.master.destroy()  # Close the wizard window

    def _on_cancel(self):
        if messagebox.askokcancel("Cancel", "Are you sure you want to cancel configuration?"):
            self.master.destroy()

if __name__ == "__main__":
    open(CONFIG_PATH, "a").close()
    root = tk.Tk()
    root.title("Configuration Wizard")
    root.geometry("600x600")
    ConfigWizard(root).pack(fill="both", expand=True)
    root.mainloop()
