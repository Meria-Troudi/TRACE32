# run_cmm.py
# This module provides functionality to run CMM scripts in TRACE32.
import ctypes
import time
import configparser
import os

T32_DEV = 0  
TIMEOUT = 20
INACTIVITY_TIMEOUT = 5
from auto_config import get_app_folder, CONFIG_PATH

# Load config.ini
cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH)

T32_EXE    = cfg.get("paths", "trace32_exe", fallback="")
T32_CONFIG = cfg.get("paths", "trace32_config", fallback="")
T32_DLL    = cfg.get("paths", "trace32_dll", fallback="")

NODE = "localhost"
PORT = "20000"
PACKLEN = "1024"


def init_trace32():
    api = ctypes.cdll.LoadLibrary(T32_DLL)
    for _ in range(20):
        if (
            api.T32_Config(b"NODE=", NODE.encode()) == 0 and
            api.T32_Config(b"PORT=", PORT.encode()) == 0 and
            api.T32_Config(b"PACKLEN=", PACKLEN.encode()) == 0 and
            api.T32_Init() == 0
        ):
            return api
        time.sleep(0.25)
    return None

def wait_for_script_completion(api, timeout=TIMEOUT):
    state = ctypes.c_int(-1)
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        rc = api.T32_GetPracticeState(ctypes.byref(state))
        if rc != 0:
            raise ConnectionError(f"Failed to get script state: {rc}")
        if state.value == 0:  # script finished
            return True
        time.sleep(0.1)
    return False

def run_cmm_script(api, cmm_path):
    api.T32_Cmd(b"PRINT")  # Clear previous messages
    path = cmm_path.replace("\\", "/").replace('"', "")
    return api.T32_Cmd(f'DO "{path}"'.encode()) == 0


def collect_messages_and_detect_error(api, timeout=TIMEOUT, inactivity_timeout=INACTIVITY_TIMEOUT):
    buffer = ctypes.create_string_buffer(256)
    status = ctypes.c_uint16()
    start = last_time = time.monotonic()
    error_detected = False
    messages = []
    seen_msgs = set()
    fail_keywords = ["teststepfail", "[fail]", "test failed", "aborting test", "execution failed"]

    while True:
        now = time.monotonic()
        if now - start > timeout:
            error_detected = True
            messages.append("⚠️ Timeout: script did not complete in time.")
            break

        rc = api.T32_GetMessage(buffer, ctypes.byref(status))
        msg = buffer.value.decode("utf-8", errors="ignore").strip()

        if rc == 0 and msg and msg not in seen_msgs:
            seen_msgs.add(msg)
            messages.append(msg)
            last_time = now

            # explicit checks
            if status.value in (2, 16):
                error_detected = True
                print(f"[DEBUG] status.value {status.value} indicates error")
            if any(k in msg.lower() for k in fail_keywords):
                error_detected = True

        else:
            # no new message
            time.sleep(0.05)

        if now - last_time > inactivity_timeout:
            break

    return error_detected, "\n".join(messages)


def run_cmm(cmm_path: str):
    api = init_trace32()
    if not api:
        return "FAIL: TRACE32 connection failed."

    try:
        attach_rc = api.T32_Attach(1)
        ping_rc   = api.T32_Ping()
        if attach_rc != 0 or ping_rc != 0:
            return "FAIL: Failed to attach to TRACE32."

        api.T32_Cmd(b"RESET")

        ok_script = run_cmm_script(api, cmm_path)
        if not ok_script:
            return "FAIL: Failed to run CMM script."

        done = wait_for_script_completion(api)
        if not done:
            return "FAIL: ⚠️ Script did not finish in time."

        error, messages = collect_messages_and_detect_error(api)
        if error:
            return "FAIL:\n" + messages
        else:
            return "PASS:\n" + messages

    finally:
        api.T32_Exit()