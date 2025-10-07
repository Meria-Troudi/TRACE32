# CLI.py
import socket
import threading
from run_cmm import run_cmm

import configparser, os
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
                
                if msg.startswith("RUN_CMM|"):
                    parts = msg.split("|", 2)
                    if len(parts) != 3:
                        conn.sendall(b"ERROR: Invalid RUN_CMM command\n")
                        continue
                    path = parts[1]
                    try:
                        count = int(parts[2])
                    except:
                        conn.sendall(b"ERROR: Invalid count\n")
                        continue

                       # Minimal change: run exactly one CMM run per request (CAPL drives loop)
                    print(f"[PYTHON] Running single run for {path} (index={count})")
                    res = run_cmm(path)  # returns "PASS:...\n..." or "FAIL:...\n..."
                    payload = f"[{count}] {res.rstrip()}\n\n<<EOT>>\n"
                    try:
                        conn.sendall(payload.encode(errors="ignore"))
                        print(f"[PYTHON] Sent result for index {count}, size={len(payload)}")
                    except Exception as e:
                        print(f"[PYTHON] send error: {e}")

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
        start_server()  # now start listening for clients
