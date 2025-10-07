# auto_config.py
# Handles application configuration and path detection.
import os
import sys
import tempfile
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def get_app_folder():
    """Return folder where executable or script resides."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))


APP_DIR = get_app_folder()
CONFIG_PATH = os.path.join(APP_DIR, "config.ini")

# Paths relative to APP_DIR
T32_DLL    = os.path.join(APP_DIR, "dll", "t32api64.dll")
T32_CONFIG = os.path.join(APP_DIR, "config.t32")
CANOE_CFG  = os.path.join(APP_DIR, "canoe", "Configuration1.cfg")
CLI_PATH   = os.path.join(APP_DIR, "CLI.exe")  # instead of CLI.py
# --------------------------------------------------
# Utility path helpers
# --------------------------------------------------
def try_local_file(*relative_path):
    path = os.path.join(APP_DIR, *relative_path)
    return path if os.path.isfile(path) else ""


def fast_find(filename, roots=["C:\\"], max_depth=6):
    exclude = {"Windows", "Program Files", "Program Files (x86)",
               "$Recycle.Bin", "System Volume Information", "System32"}

    def search(path, depth):
        if depth > max_depth:
            return None
        try:
            with os.scandir(path) as entries:
                dirs = []
                for entry in entries:
                    if entry.is_dir():
                        if entry.name in exclude:
                            continue
                        dirs.append(entry.path)
                    elif entry.is_file() and entry.name.lower() == filename.lower():
                        return entry.path
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


# --------------------------------------------------
# Path detection functions
# --------------------------------------------------
def get_trace32_exe():
    # 1. Try local bundled locations
    path = try_local_file("bin", "windows64", "t32marm.exe")
    if path:
        return path
    # 2. Try fast_find from common roots (C:, D:, E:, etc.)
    drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ"]
    path = fast_find("t32marm.exe", roots=drives, max_depth=6)
    if path:
        return path

    # 3. Try scanning system PATH environment variable
    for dir in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(dir, "t32marm.exe")
        if os.path.isfile(candidate):
            return candidate

    # 4. Ask user manually
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("Not Found", "TRACE32 Executable not found. Please select it manually.")
    path = filedialog.askopenfilename(
        title="Select TRACE32 Executable", filetypes=[("Executable files", "*.exe")]
    ) or ""
    root.destroy()
    return path



def get_trace32_dll():
    return try_local_file("dll", "t32api64.dll") or fast_find("t32api64.dll") or ""

def get_trace32_config():
    return try_local_file("config.t32") or fast_find("config.t32") or ""


def get_canoe_cfg():
    return os.path.join(APP_DIR, "canoe", "Configuration1.cfg")


# --------------------------------------------------
# Scrollable Frame widget
# --------------------------------------------------
class ScrollableFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


# --------------------------------------------------
# Unified Config Wizard
# --------------------------------------------------
class ConfigWizard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        style = ttk.Style(self)
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#007acc")
        style.configure("Desc.TLabel", font=("Segoe UI", 9), foreground="#555")

        ttk.Label(
            self,
            text="Configuration Wizard\nFill in or confirm fields below.",
            style="Header.TLabel", justify="center"
        ).pack(pady=(10, 15))

        # --- unified configuration fields ---
        self.items = [
            ("trace32_exe", "TRACE32 Executable:", get_trace32_exe, True, "Main TRACE32 executable."),
            ("trace32_dll", "TRACE32 DLL (t32api64.dll):", get_trace32_dll, True, "TRACE32 API DLL."),
            ("trace32_config", "TRACE32 Config (.t32):", get_trace32_config, True, "TRACE32 configuration file."),
            ("canoe_cfg", "CANoe Config (Configuration1.cfg):", get_canoe_cfg, True, "CANoe configuration file."),
            ("tmp_dir", "Temporary Directory:", tempfile.gettempdir, True, "Folder for temporary files."),
            ("cli", "CLI Server Script:", lambda: os.path.join(APP_DIR, "CLI.py"), True, "Path to the CLI server."),
            ("cli_host", "CLI Host:", lambda: "127.0.0.1", False, "IP where CLI server listens."),
            ("cli_port", "CLI Port:", lambda: "12345", False, "Port used by CLI server."),
            ("trace32_node", "TRACE32 Node:", lambda: "localhost", False, "Host/IP for TRACE32 node."),
            ("trace32_port", "TRACE32 Port:", lambda: "20000", False, "Port used by TRACE32 API."),
            ("trace32_packlen", "TRACE32 PacketLen:", lambda: "1024", False, "Packet length for TRACE32 communication."),
            ("timeout", "Script Timeout (s):", lambda: "20", False, "Max seconds to wait for script completion."),
            ("inactivity_timeout", "Inactivity Timeout (s):", lambda: "5", False, "Seconds of no messages before timeout."),
        ]

        self.vars = {}
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_ui()
        self._load_existing()
        self._fill_defaults()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Save & Exit", command=self._on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side="left")
        ttk.Button(btn_frame, text="Auto-Detect", command=self._refresh_detection).pack(side="left", padx=5)

    # --------------------------------------------------
    def _build_ui(self):
        container = self.scroll_frame.scrollable_frame
        row = 0
        for key, label, _, browse_btn, desc in self.items:
            ttk.Label(container, text=label).grid(row=row, column=0, sticky="w", pady=4)
            var = tk.StringVar()
            ttk.Entry(container, textvariable=var, width=60).grid(row=row, column=1, padx=5)
            if browse_btn:
                ttk.Button(container, text="Browse", width=7,
                           command=lambda v=var: self._browse_and_set(v)).grid(row=row, column=2, padx=5)
            ttk.Label(container, text=desc, style="Desc.TLabel").grid(
                row=row + 1, column=0, columnspan=3, sticky="w", padx=5)
            self.vars[key] = var
            row += 2

    def _browse_and_set(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _load_existing(self):
        cfg = configparser.RawConfigParser()
        if os.path.isfile(CONFIG_PATH):
            cfg.read(CONFIG_PATH)
        for key, var in self.vars.items():
            if cfg.has_option("config", key):
                val = cfg.get("config", key)
                if val:
                    var.set(val)

    def _refresh_detection(self):
        for key, _, default, _, _ in self.items:
            val = default() if callable(default) else default
            if val and os.path.exists(val):
                self.vars[key].set(val)
        messagebox.showinfo("Detection", "Auto-detection refreshed.")

    def _fill_defaults(self):
        for key, _, default, _, _ in self.items:
            if not self.vars[key].get():
                val = default() if callable(default) else default
                if val:
                    self.vars[key].set(val)

    def _on_save(self):
        cfg = configparser.RawConfigParser()
        cfg.add_section("config")
        for key, var in self.vars.items():
            cfg.set("config", key, var.get())
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            cfg.write(f)
        messagebox.showinfo("Saved", f"Configuration saved to:\n{CONFIG_PATH}")
        self.master.destroy()

    def _on_cancel(self):
        if messagebox.askokcancel("Cancel", "Cancel configuration?"):
            self.master.destroy()


# --------------------------------------------------
# Config validation
# --------------------------------------------------
def ensure_config(force=False):
    cfg = configparser.RawConfigParser()
    if not os.path.isfile(CONFIG_PATH):
        open(CONFIG_PATH, "a").close()
    cfg.read(CONFIG_PATH)

    required = [
        "trace32_exe", "trace32_dll", "trace32_config", "canoe_cfg",
        "tmp_dir", "cli", "cli_host", "cli_port", "trace32_node",
        "trace32_port", "trace32_packlen", "timeout", "inactivity_timeout"
    ]

    missing = [k for k in required if not cfg.has_option("config", k) or not cfg.get("config", k).strip()]
    if force or missing:
        root = tk.Tk()
        root.title("Configuration Wizard")
        root.geometry("600x600")
        ConfigWizard(root).pack(fill="both", expand=True)
        root.mainloop()

    cfg.read(CONFIG_PATH)
    still_missing = [k for k in required if not cfg.has_option("config", k) or not cfg.get("config", k).strip()]
    if still_missing:
        messagebox.showerror("Configuration Error",
                             f"Missing settings: {still_missing}\nPlease re-run with --reconfigure.")
        sys.exit(1)
    return cfg


if __name__ == "__main__":
    ensure_config(force=True)
