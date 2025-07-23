#!/usr/bin/env python3
import socket
import sys

HOST = "127.0.0.1"
PORT = 12345

def capl_like_client(path_to_cmm: str, repeat_count: int = 1):
    try:
        print(f"[CLIENT] Connecting to {HOST}:{PORT}…")
        with socket.create_connection((HOST, PORT), timeout=5) as sock:
            sock.settimeout(5)
            print("[CLIENT] Connected.")

            def send_line(line: str):
                print(f"[CLIENT] → {line.strip()}")
                sock.sendall(line.encode())

            def recv_line(maxbytes=4096) -> str:
                data = sock.recv(maxbytes)
                if not data:
                    raise ConnectionError("Server closed connection")
                text = data.decode(errors="ignore").strip()
                print(f"[CLIENT] ← {text}")
                return text

            # 1) PING → expect PONG
            send_line("PING\n")
            pong = recv_line()
            if not pong.startswith("PONG"):
                print("❌ Expected PONG, got:", pong)
                return

            # 2) Send RUN_CMM|path|count
            cmd = f"RUN_CMM|{path_to_cmm}|{repeat_count}\n"
            send_line(cmd)

            # 3) Read full result until the server closes or timeout
            print("[CLIENT] Waiting for script results…")
            sock.settimeout(30)  # allow lengthy CMM runs
            full = []
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    full.append(chunk.decode(errors="ignore"))
                except socket.timeout:
                    break

            result = "".join(full).strip()
            print("✅ Final Result:\n" + result)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python capl_like_client.py <path_to_cmm> [count]")
        sys.exit(1)

    path = sys.argv[1]
    cnt = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    capl_like_client(path, cnt)
