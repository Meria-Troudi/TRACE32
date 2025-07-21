#!/usr/bin/env python3
import socket

HOST, PORT = "127.0.0.1", 12345
def main():
    while True:
        try:
            print("[Client] Connecting…")
            with socket.create_connection((HOST, PORT)) as s:
                print("[Client] Connected.")
              

                while True:
                    cmd = input("Enter RUN_CMM to start or quit: ").strip()
                    if cmd.lower() == "quit":
                        print("[Client] Quitting.")
                        return
                    s.sendall((cmd + "\n").encode())
                    data = s.recv(4096)
                    print("[Client] ←", data.decode().strip())

        except Exception as e:
            print("Error:", e, "retrying in 5s")
            import time; time.sleep(5)

if __name__ == "__main__":
    main()
