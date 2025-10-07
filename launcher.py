# launcher.py
# Orchestrates configuration and launches TRACE32 and CANoe.

import os
import sys
import time
import configparser
import tkinter as tk
from tkinter import messagebox
from auto_config import ConfigWizard, CONFIG_PATH, get_app_folder
import trace32_launcher


CONFIG_DONE_FLAG = os.path.join(get_app_folder(), ".config_done")

REQUIRED_PATHS = [
    ("paths", "trace32_exe"),
    ("paths", "trace32_dll"),
    ("paths", "trace32_config"),
    ("paths", "canoe_cfg"),
    ("paths", "tmp_dir"),
]


def show_error(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()


def is_config_valid(cfg):
    for section, key in REQUIRED_PATHS:
        if not cfg.has_option(section, key):
            return False
        value = cfg.get(section, key)
        if key.endswith("_dir") and not os.path.isdir(value):
            return False
        if not key.endswith("_dir") and not os.path.isfile(value):
            return False
    return True


def ensure_config():
    cfg = configparser.ConfigParser()
    if not os.path.isfile(CONFIG_PATH):
        open(CONFIG_PATH, "a").close()

    cfg.read(CONFIG_PATH)

    if os.path.isfile(CONFIG_DONE_FLAG) and is_config_valid(cfg):
        return True

    # show small waiting window
    wait = tk.Tk()
    wait.title("Preparing Configuration Wizard")
    tk.Label(wait, text="Preparing configuration wizard, please wait...").pack(padx=20, pady=20)
    wait.update()
    time.sleep(1)
    wait.destroy()

    # launch wizard
    root = tk.Tk()
    root.title("Configuration Wizard")
    root.geometry("700x500")
    ConfigWizard(root).pack(fill="both", expand=True)
    root.mainloop()

    cfg.read(CONFIG_PATH)
    if is_config_valid(cfg):
        with open(CONFIG_DONE_FLAG, "w") as f:
            f.write("done")
        return True

    show_error("Configuration Incomplete", "Required paths missing or invalid.")
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
        print("[Launcher] Configuration incomplete. Exiting.")
        return

    print("[Launcher] Configuration valid. Launching CANoe.")
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
