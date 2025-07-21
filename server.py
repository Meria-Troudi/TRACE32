import socket
from PyQt5.QtCore import QThread, pyqtSignal

import threading
HOST = "127.0.0.1"
PORT = 12345

class TcpServerThread(QThread):
    connected     = pyqtSignal(bool)
    run_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._srv = None
        self._running = True
        self._active_conn = None
        self._result_ready_event = threading.Event()  # Add this

    def run(self):
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
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Server] Accept error: {e}")
                break

            print(f"[Server] Client connected from {addr}")
            self.connected.emit(True)
            self._handle_connection(conn, addr)
            self.connected.emit(False)

        self._srv.close()
        print("[Server] Stopped.")

    def _handle_connection(self, conn, addr):
        buffer = b""
        try:
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    print("[Server] Client closed connection")
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    cmd_line = line.decode('utf-8').strip()
                    print(f"[Server] Received command: {cmd_line}")

                    if cmd_line == "RUN_CMM":
                        self._active_conn = conn
                        self.run_requested.emit()

                        # Wait for GUI to run script and send result
                        self._result_ready_event.clear()
                        self._result_ready_event.wait(timeout=180)  # Wait max 180 seconds
                        print("[Server] Result sent, waiting for next command...")
                    else:
                        conn.sendall(b"ERROR: UNKNOWN_COMMAND\n")
        except Exception as e:
            print(f"[Server] Connection handling error: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
            self._active_conn = None


    def send_result(self, msg: str):
        if self._active_conn:
            try:
                self._active_conn.sendall((msg + "\n__END__\n").encode("utf-8"))
            except Exception as e:
                print(f"[Server] Error sending result: {e}")
            # Don't close connection here to keep socket alive!
            self._result_ready_event.set()  # Notify _handle_connection that sending is done

    def _wait_for_result(self):
        # Wait until send_result signals it has sent the data
        self._result_ready_event.clear()
        self._result_ready_event.wait(timeout=180) 