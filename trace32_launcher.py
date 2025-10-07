# trace32_launcher.py
import os, subprocess, time, ctypes, configparser
from auto_config import  CONFIG_PATH, get_app_folder

cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH)
# Use values from config, fallback to files next to exe (_MEIPASS)
APP_DIR = get_app_folder()

T32_EXE    = cfg.get("paths", "trace32_exe", fallback=os.path.join(APP_DIR, "bin", "t32marm.exe"))
T32_CONFIG = cfg.get("paths", "trace32_config", fallback=os.path.join(APP_DIR, "dll", "config.t32"))
T32_DLL    = cfg.get("paths", "trace32_dll", fallback=os.path.join(APP_DIR, "dll", "t32api64.dll"))
NODE               = cfg.get("runtime", "trace32_node", fallback="localhost")
PORT               = cfg.get("runtime", "trace32_port", fallback="20000")
PACKLEN            = cfg.get("runtime", "trace32_packlen", fallback="1024")


import locale

def is_running():
    try:
        cp = locale.getpreferredencoding(False)
        output = subprocess.check_output(
            "tasklist",
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode(cp, errors="ignore")
        return any(name in output.lower() for name in ("t32marm.exe", "t32start.exe"))
    except Exception as e:
        print(f"[TRACE32] Error checking running processes: {e}")
        return False


def kill_existing():
    targets = ["t32marm.exe", "t32start.exe"]
    for exe in targets:
        try:
            subprocess.run(["taskkill", "/F", "/IM", exe],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"[TRACE32] Failed to kill {exe}: {e}")

def launch_trace32():
    if is_running():
        print("[TRACE32] Already running.")
        return None
    kill_existing()
    cmd = [T32_EXE, "-c", T32_CONFIG]
    print(f"[TRACE32] Launching: {' '.join(cmd)}")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    if p.poll() is not None:
        out, err = p.communicate(timeout=5)
        raise RuntimeError(f"TRACE32 exited: {err.decode(errors='ignore')}")
    print("[TRACE32] Launched.")
    return p

def init_api():
    print(f"[TRACE32] Loading DLL: {T32_DLL}")
    api = ctypes.cdll.LoadLibrary(T32_DLL)
    api.T32_Config(b"NODE=",    NODE)
    api.T32_Config(b"PORT=",    PORT)
    api.T32_Config(b"PACKLEN=", PACKLEN)
    api.T32_Init()
    api.T32_Attach(1)
    api.T32_Ping()
 
    return api

