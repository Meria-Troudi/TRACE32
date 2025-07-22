# server.py
import socket
from PyQt5.QtCore import QThread, pyqtSignal
from run_cmm import run_cmm

HOST = "127.0.0.1"
PORT = 12345

class TcpServerThread(QThread):
    connected = pyqtSignal(bool)

    def __init__(self, get_file_path_callable):
        super().__init__()
        self.get_file_path = get_file_path_callable
        self._running = True

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(1)
        srv.settimeout(1.0)
        self.connected.emit(False)

        while self._running:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            self.connected.emit(True)
            print(f"[Server] Connected from {addr}")

            try:
                buf = b""
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buf += data
                    if b"\n" not in buf:
                        continue
                    line, buf = buf.split(b"\n", 1)
                    cmd = line.decode().strip()
                    print(f"[Server] ← {cmd}")

                    if cmd == "RUN_CMM":
                        path = self.get_file_path()
                        if not path:
                            conn.sendall(b"ERROR:NO_FILE_SELECTED\n")
                            continue

                        # 1️⃣ Block here until run_cmm() returns
                        print("[Server] Running CMM…")
                        result = run_cmm(path)
                        payload = result.replace("\n", "\\n")  # escape newlines if you like
                        conn.sendall(f"RESULT:{payload}\n".encode())

                    else:
                        conn.sendall(b"ERROR:UNKNOWN_COMMAND\n")

            except Exception as e:
                print(f"[Server] Error handling client: {e}")
            finally:
                conn.close()
                print(f"[Server] Disconnected {addr}")
                self.connected.emit(False)

        srv.close()
        print("[Server] Stopped.")
