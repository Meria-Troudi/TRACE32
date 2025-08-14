import os, subprocess, time, ctypes, configparser
from auto_config import get_app_folder, CONFIG_PATH

# Load config.ini
cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH)

T32_EXE    = cfg.get("paths", "trace32_exe", fallback="")
T32_CONFIG = cfg.get("paths", "trace32_config", fallback="")
T32_DLL    = cfg.get("paths", "trace32_dll", fallback="")

NODE         = "localhost"
PORT         = "20000"
PACKLEN      = "1024"

def is_running():
    try:
        output = subprocess.check_output("tasklist", creationflags=subprocess.CREATE_NO_WINDOW).decode()
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
    print("[TRACE32] API ready.")
    return api
