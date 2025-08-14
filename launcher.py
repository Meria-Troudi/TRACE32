import os
import sys
import subprocess
import configparser
import tkinter as tk
from tkinter import messagebox
from auto_config import ConfigWizard, CONFIG_PATH, get_app_folder
import trace32_launcher  # Make sure this module exists and is importable

CONFIG_DONE_FLAG = os.path.join(get_app_folder(), ".config_done")

def show_error(title: str, message: str):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message, parent=root)
    root.destroy()

def is_config_valid(cfg: configparser.ConfigParser, required: list) -> bool:
    for section, key in required:
        if not cfg.has_option(section, key):
            return False
        path = cfg.get(section, key)
        if key.endswith("_dir"):
            if not os.path.isdir(path):
                return False
        else:
            if not os.path.isfile(path):
                return False
    return True

def ensure_config() -> bool:
    """
    Runs ConfigWizard only if configuration is incomplete or missing.
    Returns True if config is valid, False otherwise.
    """
    cfg = configparser.ConfigParser()
    if not os.path.isfile(CONFIG_PATH):
        open(CONFIG_PATH, "a").close()

    cfg.read(CONFIG_PATH)

    required = [
        ("paths", "trace32_exe"),
        ("paths", "trace32_dll"),
        ("paths", "trace32_config"),
        ("paths", "canoe_cfg"),
        ("paths", "tmp_dir"),
    ]

    # Short-circuit if config was previously marked as complete
    if os.path.isfile(CONFIG_DONE_FLAG) and is_config_valid(cfg, required):
        return True

    # Otherwise, check validity and launch wizard if needed
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Configuration Required",
        "Some required paths are missing or invalid.\nPlease complete the configuration.",
        parent=root
    )
    root.destroy()

    wizard_root = tk.Tk()
    wizard_root.title("Configuration Wizard")
    wizard_root.geometry("600x600")
    ConfigWizard(wizard_root).pack(fill="both", expand=True)
    wizard_root.grab_set()
    wizard_root.mainloop()

    # Re-check config
    cfg.read(CONFIG_PATH)
    if is_config_valid(cfg, required):
        # Mark as completed
        with open(CONFIG_DONE_FLAG, "w") as f:
            f.write("done")
        return True

    show_error("Configuration Incomplete", "Configuration is still missing or invalid. Exiting.")
    return False

def launch_canoe():
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_PATH)
    canoe_cfg = cfg.get("paths", "canoe_cfg", fallback="")

    if not canoe_cfg or not os.path.isfile(canoe_cfg):
        show_error("Missing CANoe Config", f"Cannot find CANoe config at:\n{canoe_cfg}")
        return False

    try:
        print(f"[Launcher] Launching CANoe config: {canoe_cfg}")
        os.startfile(canoe_cfg)
        return True
    except Exception as e:
        show_error("Launch Error", f"Failed to open CANoe config:\n{e}")
        return False

def main():
    if not ensure_config():
        print("[Launcher] Configuration invalid or incomplete. Exiting.")
        return

    print("[Launcher] Configuration OK. Launching CANoe.")
    launch_canoe()

    try:
        print("[Launcher] Launching TRACE32...")
        t32_proc = trace32_launcher.launch_trace32()
        trace32_launcher.init_api()
        print("[Launcher] TRACE32 launched successfully.")
    except Exception as e:
        show_error("TRACE32 Error", f"Failed to start TRACE32:\n{e}")

if __name__ == "__main__":
    main()
