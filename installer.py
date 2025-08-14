import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import webbrowser

from auto_config import ConfigWizard, CONFIG_PATH, get_app_folder

def check_system_python_version():
    try:
        output = subprocess.check_output(["python", "--version"], stderr=subprocess.STDOUT)
        version_str = output.decode().strip().split()[1]
        major, minor, *_ = map(int, version_str.split('.'))
        return (major > 3 or (major == 3 and minor >= 7)), version_str
    except Exception:
        return False, "Not found"

class WizardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Setup Wizard")
        self.geometry("600x600")
        self.resizable(False, False)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (WelcomePage, PythonCheckPage, ConfigWizardPage):
            page = F(parent=container, controller=self)
            self.frames[F] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_frame(WelcomePage)

    def show_frame(self, page_class):
        frame = self.frames[page_class]
        frame.tkraise()

    def launch_canoe(self):
        cfg = configparser.ConfigParser()
        if not os.path.isfile(CONFIG_PATH):
            messagebox.showerror("Error", "Config file not found. Please run configuration wizard first.")
            return False

        cfg.read(CONFIG_PATH)
        canoe_cfg = cfg.get("paths", "canoe_cfg", fallback=os.path.join(get_app_folder(), "canoe", "Configuration1.cfg"))

        if not os.path.isfile(canoe_cfg):
            messagebox.showerror("Error", f"CANoe config not found:\n{canoe_cfg}")
            return False

        try:
            os.startfile(canoe_cfg)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open CANoe config:\n{e}")
            return False

class CenteredFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, width=600, height=600)
        self.pack_propagate(False)
        self.place(relx=0.5, rely=0.5, anchor='center')

class WelcomePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        container = ttk.Frame(self)
        container.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Label(container, text="Welcome to the Project Setup!", font=("Segoe UI", 20)).pack(pady=20)
        ttk.Label(container, text="This wizard will guide you through configuration.", font=("Segoe UI", 12)).pack(pady=10)
        ttk.Button(container, text="Next", command=lambda: controller.show_frame(PythonCheckPage)).pack(pady=20)

class PythonCheckPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        container = ttk.Frame(self)
        container.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Label(container, text="Checking System Python Version", font=("Segoe UI", 16)).pack(pady=15)

        self.version_label = ttk.Label(container, text="", font=("Segoe UI", 12))
        self.version_label.pack(pady=10)

        self.warning_label = ttk.Label(container, text="", font=("Segoe UI", 10), foreground="red")
        self.warning_label.pack(pady=5)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(pady=20)

        self.retry_button = ttk.Button(btn_frame, text="Retry", command=self.check_python)
        self.retry_button.grid(row=0, column=0, padx=10)

        self.download_button = ttk.Button(btn_frame, text="Download Python",
                                          command=lambda: webbrowser.open("https://www.python.org/downloads/"))
        self.download_button.grid(row=0, column=1, padx=10)

        self.next_button = ttk.Button(btn_frame, text="Next", command=self.go_next)
        self.next_button.grid(row=0, column=2, padx=10)
        self.next_button.state(['disabled'])  # Disabled until Python check passes

        self.check_python()

    def check_python(self):
        ok, version = check_system_python_version()
        if ok:
            self.version_label.config(text=f"Python detected: Version {version}")
            self.warning_label.config(text="")
            self.next_button.state(['!disabled'])
        else:
            self.version_label.config(text="Python not detected or version too old.")
            self.warning_label.config(text="You must install Python 3.7 or newer.")
            self.next_button.state(['disabled'])

    def go_next(self):
        self.controller.show_frame(ConfigWizardPage)

class ConfigWizardPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.config_wizard = ConfigWizard(self, controller)
        self.config_wizard.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        launch_btn = ttk.Button(btn_frame, text="Launch CANoe", command=self.launch_canoe)
        launch_btn.pack(side="right")

    def launch_canoe(self):
        self.master.master.launch_canoe()

if __name__ == "__main__":
    app = WizardApp()
    app.mainloop()
