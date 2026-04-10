# CLI.py
import socket
import threading
import configparser
from registry import TOOL_REGISTRY
from auto_config import CONFIG_PATH

cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH)

HOST = cfg.get("runtime", "cli_host", fallback="127.0.0.1")
PORT = cfg.getint("runtime", "cli_port", fallback=12345)

def handle_client(conn, addr):
    print(f"[PYTHON] Client connected: {addr}")
    try:
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    print(f"[PYTHON] Client {addr} disconnected.")
                    break

                msg = data.decode(errors="ignore").strip()
                print(f"[PYTHON] Received: {msg!r}")

                if msg == "PING":
                    conn.sendall(b"PONG")
                    continue

                # Expected format: RUN|PATH|INDEX
                parts = msg.split("|")
                if len(parts) < 2:
                    conn.sendall(b"ERROR: Invalid command\n")
                    continue

                command = parts[0].upper()
                path = parts[1]
                count_index = 1
                if len(parts) >= 3:
                    try:
                        count_index = int(parts[2])
                    except Exception:
                        conn.sendall(b"ERROR: Invalid count/index\n")
                        continue

                if command != "RUN":
                    conn.sendall(b"ERROR: Unsupported command\n")
                    continue

                # Dynamic tool detection based on path
                tool = None
                path_lower = path.lower()
                if path_lower.endswith(".cmm"):
                    tool = "CMM"
                elif "flash" in path_lower:
                    tool = "CFLASH"
                elif path_lower.endswith(".hex"):
                    tool = "HEX_TOOL"
                elif "vn89" in path_lower or "vnxx" in path_lower:
                    tool = "VN89XX"
                else:
                    tool = "DEFAULT_TOOL"

                if tool not in TOOL_REGISTRY:
                    conn.sendall(b"ERROR: Unknown or unsupported tool\n")
                    continue

                # Run single execution per request
                try:
                    runner = TOOL_REGISTRY[tool]["runner"]
                    print(f"[PYTHON] Running {tool} on {path} (index={count_index})")
                    result = runner(path)  # "PASS: ..." or "FAIL: ..."
                    payload = f"[{count_index}] {result.rstrip()}\n\n<<EOT>>\n"
                    conn.sendall(payload.encode(errors="ignore"))
                    print(f"[PYTHON] Sent result for index {count_index}, size={len(payload)}")
                except Exception as e:
                    err = f"FAIL|{str(e)}\n<<EOT>>\n"
                    conn.sendall(err.encode())
                    print(f"[PYTHON] Error running tool {tool}: {e}")

    except Exception as e:
        print(f"[PYTHON] Exception with client {addr}: {e}")


def start_server():
    print("[PYTHON] Server starting...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)
        print(f"[PYTHON] Listening on {HOST}:{PORT}")

        while True:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    start_server()