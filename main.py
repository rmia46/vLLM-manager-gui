import sys
import os
import requests
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QDoubleSpinBox, QSpinBox,
    QPushButton, QTextEdit, QGroupBox, QFrame, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from model_scanner import get_cached_models
from docker_checker import check_open_webui_status, start_open_webui, stop_open_webui
from vllm_runner import VLLMProcessWorker

DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    font-family: 'Segoe UI', Inter, sans-serif;
    font-size: 13px;
    color: #cdd6f4;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cdd6f4;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #89b4fa;
}
QPushButton {
    background-color: #89b4fa;
    color: #11111b;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #7f849c;
}
QPushButton#stopBtn {
    background-color: #f38ba8;
    color: #11111b;
}
QPushButton#stopBtn:hover {
    background-color: #eba0ac;
}
QPushButton#dockerBtn {
    background-color: #a6e3a1;
    color: #11111b;
}
QTextEdit {
    background-color: #11111b;
    border: 1px solid #313244;
    border-radius: 6px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: #a6adc8;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""

class VLLMManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("vLLM Manager & Open WebUI Control Center")
        self.resize(1000, 750)
        self.setStyleSheet(DARK_STYLESHEET)

        self.worker = None

        self.init_ui()

        # Timer for Open WebUI status refresh
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_docker_status)
        self.status_timer.start(5000)
        self.update_docker_status()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Top Header Bar
        header = QLabel("🚀 vLLM Desktop Manager")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #cba6f7; margin-bottom: 5px;")
        main_layout.addWidget(header)

        # Splitter between Settings and Logs
        splitter = QSplitter(Qt.Vertical)

        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Left Column: vLLM Config & Controls
        vllm_box = QGroupBox("vLLM Server Configuration")
        vllm_layout = QVBoxLayout(vllm_box)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.refresh_models()
        model_layout.addWidget(self.model_combo, 1)
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Rescan HF cache")
        refresh_btn.setFixedWidth(36)
        refresh_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(refresh_btn)
        vllm_layout.addLayout(model_layout)

        # Port & Quantization
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Port:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(8000)
        row1.addWidget(self.port_spin)

        row1.addWidget(QLabel("Quantization:"))
        self.quant_combo = QComboBox()
        self.quant_combo.addItems(["none", "awq", "gptq", "fp8", "squeezellm"])
        row1.addWidget(self.quant_combo)
        vllm_layout.addLayout(row1)

        # GPU Memory & Max Model Len
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("GPU Mem Util (0.1 - 1.0):"))
        self.gpu_spin = QDoubleSpinBox()
        self.gpu_spin.setRange(0.10, 1.00)
        self.gpu_spin.setSingleStep(0.05)
        self.gpu_spin.setValue(0.90)
        row2.addWidget(self.gpu_spin)

        row2.addWidget(QLabel("Max Model Len:"))
        self.max_len_spin = QSpinBox()
        self.max_len_spin.setRange(512, 131072)
        self.max_len_spin.setSingleStep(512)
        self.max_len_spin.setValue(4096)
        row2.addWidget(self.max_len_spin)
        vllm_layout.addLayout(row2)

        # Checkboxes & Tool Parser
        row3 = QHBoxLayout()
        self.tool_choice_cb = QCheckBox("Enable Auto Tool Choice (--enable-auto-tool-choice)")
        self.tool_choice_cb.setChecked(True)
        row3.addWidget(self.tool_choice_cb)

        row3.addWidget(QLabel("Tool Parser:"))
        self.tool_parser_combo = QComboBox()
        self.tool_parser_combo.addItems(["none", "qwen3_xml", "llama3_json", "mistral", "hermes"])
        self.tool_parser_combo.setCurrentText("qwen3_xml")
        row3.addWidget(self.tool_parser_combo)
        vllm_layout.addLayout(row3)

        # Additional Extra Arguments
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Extra Flags:"))
        self.extra_flags_edit = QLineEdit()
        self.extra_flags_edit.setPlaceholderText("e.g. --trust-remote-code --dtype float16")
        row4.addWidget(self.extra_flags_edit)
        vllm_layout.addLayout(row4)

        # Launch / Stop Buttons & Status
        btn_layout = QHBoxLayout()
        self.start_vllm_btn = QPushButton("▶ Launch vLLM Server")
        self.start_vllm_btn.clicked.connect(self.start_vllm)
        btn_layout.addWidget(self.start_vllm_btn)

        self.stop_vllm_btn = QPushButton("⏹ Stop vLLM Server")
        self.stop_vllm_btn.setObjectName("stopBtn")
        self.stop_vllm_btn.setEnabled(False)
        self.stop_vllm_btn.clicked.connect(self.stop_vllm)
        btn_layout.addWidget(self.stop_vllm_btn)

        self.vllm_status_lbl = QLabel("STATUS: IDLE")
        self.vllm_status_lbl.setStyleSheet("font-weight: bold; color: #f9e2af; padding-left: 10px;")
        btn_layout.addWidget(self.vllm_status_lbl)

        vllm_layout.addLayout(btn_layout)
        top_layout.addWidget(vllm_box, 2)

        # Right Column: Open WebUI Status Widget
        webui_box = QGroupBox("Open WebUI Status Monitor")
        webui_layout = QVBoxLayout(webui_box)

        self.docker_status_lbl = QLabel("Container Status: Checking...")
        self.docker_status_lbl.setWordWrap(True)
        webui_layout.addWidget(self.docker_status_lbl)

        self.http_status_lbl = QLabel("Web UI URL: http://localhost:8080")
        webui_layout.addWidget(self.http_status_lbl)

        self.open_browser_btn = QPushButton("🌐 Open in Browser")
        self.open_browser_btn.setObjectName("dockerBtn")
        self.open_browser_btn.clicked.connect(lambda: webbrowser.open("http://localhost:8080"))
        webui_layout.addWidget(self.open_browser_btn)

        self.toggle_docker_btn = QPushButton("⚡ Start Container")
        self.toggle_docker_btn.clicked.connect(self.toggle_docker)
        webui_layout.addWidget(self.toggle_docker_btn)

        webui_layout.addStretch()
        top_layout.addWidget(webui_box, 1)

        splitter.addWidget(top_container)

        # Bottom Area: Live Log Viewer
        log_box = QGroupBox("Live vLLM Output Logs")
        log_layout = QVBoxLayout(log_box)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("Clear Logs")
        clear_log_btn.setFixedWidth(100)
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn, alignment=Qt.AlignRight)

        splitter.addWidget(log_box)

        main_layout.addWidget(splitter)

    def refresh_models(self):
        self.model_combo.clear()
        models = get_cached_models()
        if models:
            self.model_combo.addItems(models)
        else:
            self.model_combo.addItem("Qwen/Qwen2.5-1.5B-Instruct")

    def build_vllm_args(self):
        model_name = self.model_combo.currentText().strip()
        args = [model_name, "--port", str(self.port_spin.value())]

        quant = self.quant_combo.currentText()
        if quant != "none":
            args.extend(["--quantization", quant])

        args.extend(["--gpu-memory-utilization", str(self.gpu_spin.value())])
        args.extend(["--max-model-len", str(self.max_len_spin.value())])

        if self.tool_choice_cb.isChecked():
            args.append("--enable-auto-tool-choice")

        tool_parser = self.tool_parser_combo.currentText()
        if tool_parser != "none":
            args.extend(["--tool-call-parser", tool_parser])

        extra = self.extra_flags_edit.text().strip()
        if extra:
            args.extend(extra.split())

        return args

    def start_vllm(self):
        model_name = self.model_combo.currentText().strip()
        if not model_name:
            QMessageBox.warning(self, "Missing Model", "Please select or type a model name.")
            return

        cmd_args = self.build_vllm_args()

        self.start_vllm_btn.setEnabled(False)
        self.stop_vllm_btn.setEnabled(True)

        self.worker = VLLMProcessWorker(cmd_args)
        self.worker.log_received.connect(self.append_log)
        self.worker.status_changed.connect(self.on_vllm_status_change)
        self.worker.start()

    def stop_vllm(self):
        if self.worker:
            self.worker.stop_server()

    def on_vllm_status_change(self, status):
        self.vllm_status_lbl.setText(f"STATUS: {status}")
        if status == "RUNNING":
            self.vllm_status_lbl.setStyleSheet("font-weight: bold; color: #a6e3a1;")
        elif status == "STARTING":
            self.vllm_status_lbl.setStyleSheet("font-weight: bold; color: #f9e2af;")
        elif status in ["STOPPED", "IDLE"]:
            self.vllm_status_lbl.setStyleSheet("font-weight: bold; color: #fab387;")
            self.start_vllm_btn.setEnabled(True)
            self.stop_vllm_btn.setEnabled(False)
        elif status == "ERROR":
            self.vllm_status_lbl.setStyleSheet("font-weight: bold; color: #f38ba8;")
            self.start_vllm_btn.setEnabled(True)
            self.stop_vllm_btn.setEnabled(False)

    def append_log(self, text):
        self.log_text.append(text.rstrip())

    def update_docker_status(self):
        status = check_open_webui_status()
        if status["container_running"]:
            self.docker_status_lbl.setText(f"Container: RUNNING\n({status['status_text']})")
            self.docker_status_lbl.setStyleSheet("color: #a6e3a1;")
            self.toggle_docker_btn.setText("⏹ Stop Container")
        else:
            self.docker_status_lbl.setText(f"Container: STOPPED")
            self.docker_status_lbl.setStyleSheet("color: #f38ba8;")
            self.toggle_docker_btn.setText("⚡ Start Container")

    def toggle_docker(self):
        status = check_open_webui_status()
        if status["container_running"]:
            ok, msg = stop_open_webui()
        else:
            ok, msg = start_open_webui()
        self.update_docker_status()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VLLMManagerGUI()
    window.show()
    sys.exit(app.exec())
