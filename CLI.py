import socket
import threading
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

                    output_accum = []
                    for i in range(count):
                        print(f"[PYTHON] Running {path} ({i+1}/{count})")
                        try:
                            result = run_cmm(path)
                            output_accum.append(f"[{i+1}] {result}")
                            print(f"[PYTHON] Result {i+1}: {result}")   
                        except Exception as e:
                            output_accum.append(f"[{i+1}] ERROR: {e}")

                    final_response = "\n".join(output_accum)
                        
                    conn.sendall(final_response.encode())

                else:
                    conn.sendall(b"ERROR: Unknown command\n")

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
