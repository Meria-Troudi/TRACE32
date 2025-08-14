# CLI.py
import socket
import threading
import os
import csv
from datetime import datetime
from run_cmm import run_cmm
import auto_config

HOST       =  "127.0.0.1"
PORT       = 12345

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

                    all_out = []
                    for i in range(count):
                        print(f"[PYTHON] Running [{i+1}/{count}] {path}")
                      
                        res = run_cmm(path)
                    

                        all_out.append(f"[{i+1}] {res} \n")
                        print(f"[PYTHON] Collected output: {len(all_out)} messages")
                    final = "\n".join(all_out) + "\n<<<EOT>>>\n"
                    conn.sendall(final.encode())

                else:
                    conn.sendall(f"ERROR: Unknown command '{msg}'\n".encode())

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
