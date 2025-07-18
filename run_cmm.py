import ctypes
import os
import time
import json
from typing import List

T32_DLL = r"C:\Users\meria\Desktop\T32_Ranger\T32_r\demo\api\python\t32api64.dll"
TIMEOUT = 180
INACTIVITY_TIMEOUT = 5

def init_trace32():
    trace32_api = ctypes.cdll.LoadLibrary(T32_DLL)
    for _ in range(20):
        if (
            trace32_api.T32_Config(b"NODE=", b"localhost") == 0 and
            trace32_api.T32_Config(b"PORT=", b"40000") == 0 and
            trace32_api.T32_Config(b"PACKLEN=", b"1024") == 0 and
            trace32_api.T32_Init() == 0
        ):
            return trace32_api
        time.sleep(0.25)
    return None

def run_cmm_script(trace32_api, cmm_path):
    trace32_api.T32_Cmd(b"PRINT")
    path = cmm_path.replace("\\", "/").replace('"', "")
    return trace32_api.T32_Cmd(f'DO "{path}"'.encode()) == 0

def collect_messages(trace32_api, timeout=TIMEOUT, inactivity_timeout=INACTIVITY_TIMEOUT) -> List[str]:
    buffer = ctypes.create_string_buffer(256)
    status = ctypes.c_uint16()
    messages, seen = [], set()
    start = last = time.monotonic()

    while True:
        now = time.monotonic()
        if now - start > timeout:
            messages.append("⚠️ Timeout: script did not complete in time.")
            break
        if trace32_api.T32_GetMessage(buffer, ctypes.byref(status)) == 0 and buffer.value:
            msg = buffer.value.decode("utf-8", errors="ignore").strip()
            if msg and msg not in seen:
                messages.append(msg)
                seen.add(msg)
                print(f"> {msg}")
                last = now
        else:
            time.sleep(0.05)

    return messages

def run_cmm(cmm_path: str) -> str:
    api = init_trace32()
    if not api:
        return json.dumps({
            "status": "failure",
            "message": "❌ TRACE32 connection failed. Ensure it's running with Remote API enabled."
        })

    if api.T32_Attach(1) != 0:
        return json.dumps({"status": "failure", "message": "❌ Attach to TRACE32 failed."})

    if not run_cmm_script(api, cmm_path):
        return json.dumps({"status": "failure", "message": "❌ Failed to run the CMM script."})

    messages = collect_messages(api)
    log_file = "trace32_log.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(messages))

    return json.dumps({
        "status": "success",
        "message": "✅ Script executed successfully.",
        "logFile": log_file,
        "rawOutput": messages
    })
   

