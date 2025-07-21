#main.py
import sys, os, glob, json, datetime, time, threading, psutil
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QPushButton, QMessageBox, QFileDialog,
    QProgressBar, QAction, QTextEdit, QVBoxLayout, QDialog, QLabel
)
from PyQt5.QtCore import QTimer, pyqtSignal, QMetaObject, Qt
from concurrent.futures import ThreadPoolExecutor
from server import TcpServerThread
from run_cmm import run_cmm
from cmm import Ui_MainWindow
from historyDialog import Ui_HistoryDialog
class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_HistoryDialog()
        self.ui.setupUi(self)
        self.history_display = QTextEdit(readOnly=True)
        self.btnhistory = self.ui.buttonLayout
        self.ui.addWidget(QLabel("Log Preview:"))
        self.ui.addWidget(self.history_display)
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
    update_result_signal = pyqtSignal(str)  # Declare here

    def __init__(self):
        self._result_container = None
        self._event_loop = None
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.select_btn = self.ui.select
        self.run_btn = self.ui.run
        self.path_field = self.ui.path
        self.result = self.ui.res
        self.progresslabel = self.ui.progLabel
        self.canstatus = self.ui.canStatusLabel
        self.serverstatus = self.ui.serverStatusLabel
        self.progress = self.ui.progressBar
        self.statusBar().addPermanentWidget(self.ui.canStatusLabel)
        self.statusBar().addPermanentWidget(self.ui.serverStatusLabel)

        self.selected_file = None
        self._start_time = None
        self.history = []
        self._dots = 0

        self.result.setReadOnly(True)
        self.path_field.setText("No file selected")
        self._hide_outputs()
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)

        self.ui.menuSettings.addAction(QAction("Save Log…", self, triggered=self._save_log))
        self.ui.menuHistory.addAction(QAction("Show History…", self, triggered=self._show_history))
        self.ui.actionExit.triggered.connect(self.close)

        self.select_btn.clicked.connect(self._select_file)
        self.run_btn.clicked.connect(lambda: self._run_and_report(local=True))
        
        self.tcp = TcpServerThread()
        self.tcp.connected.connect(self._on_server_status)
        self.tcp.run_requested.connect(self._on_run_requested)
        self.update_result_signal.connect(self._update_result_in_gui)

        self.tcp.start()

        threading.Thread(target=self._detect_canoe_loop, daemon=True).start()

    def _hide_outputs(self):
        self.progress.hide()
        self.result.hide()

    def _show_outputs(self):
        self.progress.show()
        self.result.show()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CMM Script", "", "CMM Files (*.cmm);;All Files (*)")
        if path:
            self.selected_file = path
            self.path_field.setText(path)
            self.statusBar().showMessage(f"Selected: {os.path.basename(path)}", 3000)

    def _on_result_ready(self, res):
        self.result.setPlainText(res)
        self.statusBar().showMessage("Result received from CAPL command")


    def _run_and_report(self, local):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected",
                                "Please select a CMM script file first.")
            return

        self._show_outputs()
        self._start_time = time.monotonic()
        self.result.setPlainText("⏳ Running script…")
        self.progress.setValue(0)
        self.statusBar().showMessage("Running script…")

        def task():
                print("[Task] Starting run_cmm")
                res = run_cmm(self.selected_file)
                self.update_result_signal.emit(res)  # ✔ Correct: emit to main thread

                print("[Task] run_cmm finished")
                return res


        future = self.pool.submit(task)

        def monitor():
            print("[Monitor] Monitoring future...")
            while not future.done():
                time.sleep(0.2)
            res = future.result()
            print("[Monitor] Future done, sending result...")
            self.tcp.send_result(res)  # Directly send result back via server thread
    
        threading.Thread(target=monitor, daemon=True).start()
        

        
    def _update_result_in_gui(self, text):
        self.progress.setValue(100)
        self.result.setPlainText(text)

        self.statusBar().showMessage("Result received from script.")
        
    def _on_run_requested(self):
         QMessageBox.information(self, "Run CMM Request",
            "Server requested to run a CMM script.\n"
            "Please select a file and click Run manually.")
         
    def _detect_canoe_loop(self):
        prev = True
        while True:
            found = any("Canoe" in (p.info.get("name") or "") for p in psutil.process_iter(["name"]))
            if found != prev:
                prev = found
                self._on_canoe_status(found)
            time.sleep(5)

    def _on_canoe_status(self, running: bool):
        icon = "🟢" if running else "🔴"
        self.ui.canStatusLabel.setText(f"CANoe: {icon}")
    def _on_server_status(self, connected: bool):
        icon = "🟢" if connected else "🔴"
        self.ui.serverStatusLabel.setText(f"Server: {icon}")
    def _update_progress(self):
        if not self._start_time:
            return
        elapsed = time.monotonic() - self._start_time
        pct = min(int((elapsed / 10) * 99), 99)
        self.progress.setValue(pct)
        self._dots = (self._dots + 1) % 4
        self.statusBar().showMessage("Running script" + "." * self._dots)

    
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
