#!/usr/bin/env python3
import socket, threading, time

HOST, PORT = "127.0.0.1", 12345
HB = 10  # heartbeat every 10s

def heartbeat(sock):
    while True:
        time.sleep(HB)
        try:
            sock.sendall(b"PING\n")
            print("[Client] → PING")
        except:
            break

def main():
    while True:
        try:
            print("[Client] Connecting…")
            s = socket.create_connection((HOST, PORT))
            print("[Client] Connected.")
            threading.Thread(target=heartbeat, args=(s,), daemon=True).start()

            while True:
                data = s.recv(1024)
                if data:
                    print("[Client] ←", data.decode().strip())
                cmd = input("Enter RUN_CMM to start or quit: ").strip()
                if cmd=="quit":
                    s.close(); return
                s.sendall((cmd + "\n").encode())
        except Exception as e:
            print("Error:", e, "retrying in 5s")
            time.sleep(5)

if __name__=="__main__":
    main()
