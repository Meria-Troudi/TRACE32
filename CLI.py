import socket
import threading
import os
import json
from run_cmm import run_cmm

HOST, PORT = "127.0.0.1", 12345

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
                print(f"[PYTHON] Received from {addr}: {msg!r}")

                if msg.startswith("RUN_CMM|"):
                    parts = msg.split("|", 1)
                    if len(parts) != 2 or not parts[1]:
                        response = json.dumps({"status": "error", "message": "Missing file path."})
                        conn.sendall(response.encode())
                        continue

                    path = parts[1]
                    print(f"[PYTHON] Running CMM script: {path}")

                    try:
                        result = run_cmm(path)
                        response = json.dumps({"status": "success", "output": result})
                    except Exception as e:
                        response = json.dumps({"status": "error", "message": str(e)})

                    conn.sendall(response.encode())

                else:
                    response = json.dumps({"status": "error", "message": "Unknown command."})
                    conn.sendall(response.encode())

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
            try:
                conn, addr = srv.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except KeyboardInterrupt:
                print("\n[PYTHON] Server shutting down.")
                break
            except Exception as e:
                print(f"[PYTHON] Server error: {e}")

if __name__ == "__main__":
    start_server()

"""
import socket
import threading
import os
from run_cmm import run_cmm

HOST, PORT = "127.0.0.1", 12345

def handle_client(conn, addr):
    print(f"[PYTHON] Connected by {addr!r}")
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                print("[PYTHON] Client disconnected")
                break

            msg = data.decode(errors="ignore").strip()
            print(f"[PYTHON] Received: {msg!r}")

            if msg.startswith("RUN_CMM|"):
                _, path = msg.split("|", 1)
                print(f"[PYTHON] Running CMM script: {path}")
                try:
                    result = run_cmm(path)
                except Exception as e:
                    result = f" Python exception: {str(e)}"

                final_msg = f"RESULT:\n{result}\n"
                conn.sendall(final_msg.encode("utf-8"))
                print("[PYTHON] Result sent")
            else:
                conn.sendall(b" Unknown command\n")

print("[PYTHON] Server starting…")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"[PYTHON] Listening on {HOST}:{PORT}")

    conn, addr = srv.accept()
    handle_client(conn, addr)
"""