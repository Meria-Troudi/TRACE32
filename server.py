# canoepy.py
import socket
import threading
import json
from PyQt5.QtCore import QThread, pyqtSignal, QEventLoop, QTimer

HOST = "127.0.0.1"
PORT = 12345
HEARTBEAT_TIMEOUT = 30  # seconds

class TcpServerThread(QThread):
    connected     = pyqtSignal(bool)
    run_requested = pyqtSignal()
    result_ready  = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self._srv = None

    def run(self):
        print("[Server] Starting TCP server…")
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((HOST, PORT))
        self._srv.listen(1)
        self._srv.settimeout(1.0)
        self.connected.emit(False)
        print(f"[Server] Listening on {HOST}:{PORT}")

        while self._running:
            try:
                conn, addr = self._srv.accept()
                print(f"[Server] Client connected from {addr}")
                self.connected.emit(True)
                threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Server] Accept error: {e}")
                break

        if self._srv:
            self._srv.close()
        self.connected.emit(False)
        print("[Server] Stopped.")

    def _handle_client(self, conn, addr):
        last_hb = __import__("time").time()
        conn.settimeout(1.0)
        try:
            while True:
                try:
                    data = conn.recv(1024).decode().strip()
                    if not data:
                        break
                    self.command_received.emit(data)
                except socket.timeout:
                    # check for heartbeat timeout
                    if __import__("time").time() - last_hb > HEARTBEAT_TIMEOUT:
                        print("[Server] Heartbeat timed out.")
                        break
                    continue

                if not data:
                    break

                text = data.decode(errors="ignore").strip()
                print(f"[Server] ← {text}")

                if text == "PING":
                    conn.sendall(b"PONG\n")
                    last_hb = __import__("time").time()

                elif text == "RUN_CMM":
                    # wait until GUI calls `result_ready.emit(...)`
                    loop = QEventLoop()
                    result = {}
                    def on_res(r): result["data"] = r; loop.quit()
                    self.result_ready.connect(on_res)
                    self.run_requested.emit()
                    # safety timer
                    t = QTimer()
                    t.setSingleShot(True)
                    t.timeout.connect(loop.quit)
                    t.start(35000)
                    loop.exec_()
                    self.result_ready.disconnect(on_res)

                    if "data" not in result:
                        resp = "RESULT:FAIL\n"
                    else:
                        parsed = json.loads(result["data"])
                        resp = "RESULT:OK\n" if parsed.get("status")=="success" else "RESULT:FAIL\n"
                    conn.sendall(resp.encode())
                    print(f"[Server] → {resp.strip()}")

                else:
                    conn.sendall(b"RESULT:UNKNOWN\n")

        except Exception as e:
            print("[Server] Handler error:", e)
        finally:
            conn.close()
            self.connected.emit(False)
            print("[Server] Disconnected", addr)