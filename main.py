#!/usr/bin/env python3
import sys, os, glob, json, datetime, time, threading, psutil
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QPushButton, QMessageBox, QFileDialog,
    QProgressBar, QAction, QTextEdit, QVBoxLayout, QDialog, QLabel
)
from PyQt5.QtCore import QTimer, pyqtSignal
from concurrent.futures import ThreadPoolExecutor

from server import TcpServerThread  # Your TCP server thread class
from run_cmm import run_cmm            # Function to run CMM scripts
from cmm import Ui_MainWindow          # Your UI form
from historyDialog import Ui_HistoryDialog  # History dialog UI


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_HistoryDialog()
        self.ui.setupUi(self)

        self.history_display = QTextEdit(readOnly=True)
        self.button_layout = QVBoxLayout()
        wrapper = QVBoxLayout()
        wrapper.addLayout(self.button_layout)
        wrapper.addWidget(QLabel("Log Preview:"))
        wrapper.addWidget(self.history_display)
        self.setLayout(wrapper)

        self.ui.closeButton.clicked.connect(self.close)
        self._load_history_buttons()

    def _load_history_buttons(self):
        folder = "history_files"
        if not os.path.isdir(folder):
            self.history_display.setPlainText("No history directory found.")
            return
        for path in sorted(glob.glob(os.path.join(folder, "*.log"))):
            name = os.path.basename(path)
            try:
                base, ts_ext = name.rsplit("_", 1)
                ts = ts_ext.split(".")[0]
                dt = datetime.datetime.fromtimestamp(int(ts))
                label = f"{base} | {dt:%Y-%m-%d %H:%M:%S}"
            except Exception:
                label = name
            btn = QPushButton(label, clicked=self._make_loader(path))
            self.button_layout.addWidget(btn)

    def _make_loader(self, path):
        def loader():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.history_display.setPlainText(f.read())
            except Exception as e:
                self.history_display.setPlainText(f"⚠️ Error reading file: {e}")
        return loader


class CmmGuiApp(QMainWindow):
    canoe_detected = pyqtSignal(bool)
    result_ready = pyqtSignal(str)
    run_requested = pyqtSignal()      # client asked for RUN_CMM


    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Widgets
        self.select_btn = self.ui.select
        self.run_btn = self.ui.run
        self.path_field = self.ui.path
        self.log_out = self.ui.textEdit
        self.progress = self.ui.progressBar
        self.radio_on = self.ui.radioButton
        self.radio_off = self.ui.radioButton_2
        self.body_label = self.ui.bodyLabel
        self.client_label = self.ui.canoeStatusLabel
        self.server_label = self.ui.serverStatusLabel
        self.ui.statusbar.addPermanentWidget(self.client_label)
        self.ui.statusbar.addPermanentWidget(self.server_label)
        # State
        self.selected_file = None
        self._start_time = None
        self.history = []
        self._dots = 0
        self._canoe_running = False

        # Initial UI state
        self.log_out.setReadOnly(True)
        self.select_btn.setEnabled(False)
        self.run_btn.setEnabled(False)
        self.path_field.setText("No file selected")
        self._hide_outputs()

        # Thread pool and timer
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.timer = QTimer(self); self.timer.timeout.connect(self._update_progress)

        # Menu
        self.ui.menuSettings.addAction(QAction("Save Log…", self, triggered=self._save_log))
        self.ui.menuHistory.addAction(QAction("Show History…", self, triggered=self._show_history))
        self.ui.actionExit.triggered.connect(self.close)

        # Connections
        self.select_btn.clicked.connect(self._select_file)
        self.run_btn.clicked.connect(self.on_run_btn_clicked)

        self.canoe_detected.connect(self._on_canoe)
        threading.Thread(target=self._detect_canoe_loop, daemon=True).start()

        # TCP‑server thread
        self.tcp = TcpServerThread()
        self.tcp.connected.connect(self._on_server_status)
        self.tcp.connected.connect(self._on_canoe_process)

        self.tcp.run_requested.connect(self._on_run_requested)
        self.result_ready.connect(self._display_result)
        self.tcp.start()
        self.tcp.run_requested.connect(self.on_server_request_cmm)
    def on_server_request_cmm(self):
        # Instead of launching the CMM directly here...
        QMessageBox.information(self, "Server Request", "Server requested to run CMM.\nPlease select the file and press Run.")
        self._allow_user_to_choose_cmm = True
        self.ui.run_btn.setEnabled(True)

    def on_run_btn_clicked(self):
        if not self._allow_user_to_choose_cmm:
            QMessageBox.warning(self, "Not Allowed", "Waiting for server trigger to run CMM.")
            return

        if not self.selected_file:
            QMessageBox.warning(self, "Missing File", "Please choose a CMM file before running.")
            return

        self._run_and_report()
        self._run_cmm(self.selected_cmm_path)
        self._allow_user_to_choose_cmm = False
        self.ui.run_btn.setEnabled(False)

    def _hide_outputs(self):
        self.progress.hide()
        self.body_label.hide()
        self.log_out.hide()

    def _show_outputs(self):
        self.progress.show()
        self.body_label.show()
        self.log_out.show()

    def _on_canoe(self, up: bool):
        self.radio_on.setChecked(up)
        self.radio_off.setChecked(not up)
        self._refresh_buttons()


    def _refresh_buttons(self):
        ok = self.radio_on.isChecked()
        self.select_btn.setEnabled(ok)
        self.run_btn.setEnabled(ok and hasattr(self, "selected_file"))


    def _detect_canoe_loop(self):
        prev = False
        while True:
            found = any("Canoe" in (p.info.get("name") or "") for p in psutil.process_iter(["name"]))
            if found != prev:
                prev = found
                self.canoe_detected.emit(found)
            time.sleep(5)

    def _on_canoe_process(self, running: bool):
        icon = "🟢" if running else "🔴"
        self.client_label.setText(f"CANoe: {icon}")
        self._update_run_button_state()

    def _on_server_status(self, connected: bool):
        icon = "🟢" if connected else "🔴"
        self.server_label.setText(f"Server: {icon}")
        self._update_run_button_state()

    def _update_run_button_state(self):
        canoe_ok = "🟢" in self.client_label.text()
        server_ok = "🟢" in self.server_label.text()
        has_file = bool(self.selected_file)
        self.select_btn.setEnabled(canoe_ok and server_ok)
        self.run_btn.setEnabled(canoe_ok and server_ok and has_file)



    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CMM Script", "", "CMM Files (*.cmm);;All Files (*)")
        if path:
            self.selected_file = path
            self.path_field.setText(path)
            self.statusBar().showMessage(f"Selected: {os.path.basename(path)}", 3000)
            self.run_btn.setEnabled(True)
            self._refresh_buttons()
    def _confirm_run(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No file", "Please select a CMM file first.")
            return
        if QMessageBox.question(self, "Confirm Run", f"Run this script?\n{self.selected_file}", QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Ok:
            self._run_and_report()

    def _on_run_requested(self):
        QMessageBox.information(self, "Client Request", "Client requested to run a CMM script.\nPlease select a file and press Run.")
        self.select_btn.setEnabled(True)
        self.run_btn.setEnabled(True)
        self._allow_user_to_choose_cmm = True
        self.select_btn.setEnabled(True)
        self.run_btn.setEnabled(bool(self.selected_file))

        def poll():
            if fut.done():
                self.timer.stop()
                res = fut.result()
                self.result_ready.emit(res)
            else:
                self._dots = (self._dots+1) % 4
                self.progress.setValue(min(self._dots*25, 100))
                QTimer.singleShot(500, poll)

        self._hide_outputs(); self._show_outputs()
        self.progress.setValue(0); self._dots=0
        self.timer.start(500)
        poll()

    def _run_and_report(self):
        self.result_ready.emit("")
        self._hide_outputs()
        self._show_outputs()
        self._start_time = time.monotonic()
        self.log_out.setPlainText("⏳ Running script…")
        self.progress.setValue(0)
        self.statusBar().showMessage("Running script…")

        def task():
            try:
                return run_cmm(self.selected_file)
            except Exception as e:
                return json.dumps({"status": "failure", "message": str(e)})

        future = self.pool.submit(task)

        def check():
            if future.done():
                try:
                    result_json = future.result()
                except Exception as e:
                    result_json = json.dumps({"status": "failure", "message": str(e)})
                self.result_ready.emit(result_json)
                self.timer.stop()
            else:
                elapsed = time.monotonic() - self._start_time
                if elapsed > 30:
                    future.cancel()
                    self.result_ready.emit(json.dumps({"status": "failure", "message": "Timeout"}))
                    self.timer.stop()
                else:
                    pct = min(int((elapsed / 30) * 95), 95)
                    self.progress.setValue(pct)
                    self._dots = (self._dots + 1) % 4
                    self.statusBar().showMessage("Running script" + "." * self._dots)
                    QTimer.singleShot(500, check)

        check()

    def _update_progress(self):
        if not self._start_time:
            return
        elapsed = time.monotonic() - self._start_time
        pct = min(int((elapsed / 10) * 99), 99)
        self.progress.setValue(pct)
        self._dots = (self._dots + 1) % 4
        self.statusBar().showMessage("Running script" + "." * self._dots)

    def _display_result(self, result_json):
        self.timer.stop()
        elapsed = time.monotonic() - (self._start_time or time.monotonic())
        self.progress.setValue(100)
        self.statusBar().showMessage(f"Completed in {elapsed:.1f}s", 4000)

        try:
            parsed = json.loads(result_json)
            status = parsed.get("status", "unknown")
            message = parsed.get("message", "")
            logf = parsed.get("logFile", "")
        except Exception:
            status, message, logf = "error", result_json, ""

        ts = str(int(datetime.datetime.now().timestamp()))
        name = os.path.basename(self.selected_file or "run")
        fn = f"{name}_{ts}.log"
        os.makedirs("history_files", exist_ok=True)
        with open(os.path.join("history_files", fn), "w", encoding="utf-8") as f:
            f.write(f"{message}\nStatus: {status}\nLog File: {logf}")

        self.history.append((ts, status, message))
        self.log_out.setPlainText(f"{message}\nStatus: {status}\nLog File: {logf}")

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Log As…", "cmm_log.txt", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_out.toPlainText())
            self.statusBar().showMessage(f"Log saved to {path}", 3000)

    def _show_history(self):
        dlg = HistoryDialog(self)
        dlg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CmmGuiApp()
    w.show()
    sys.exit(app.exec_())
