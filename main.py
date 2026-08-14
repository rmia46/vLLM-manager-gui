import sys
import os
import requests
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QDoubleSpinBox, QSpinBox,
    QPushButton, QTextEdit, QGroupBox, QSplitter, QMessageBox,
    QFileDialog, QTabWidget, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from model_scanner import get_cached_models, DEFAULT_HF_CACHE_DIR
from docker_checker import check_open_webui_status, start_open_webui, stop_open_webui
from vllm_runner import VLLMProcessWorker
from hf_downloader import HFBrowserWorker, HFDownloadWorker
from vllm_flags_info import VLLM_FLAGS_HELP

DARK_STYLESHEET = """
QMainWindow { background-color: #1e1e2e; color: #cdd6f4; }
QWidget { font-family: 'Segoe UI', Inter, sans-serif; font-size: 13px; color: #cdd6f4; }
QTabWidget::pane { border: 1px solid #45475a; border-radius: 6px; background-color: #1e1e2e; }
QTabBar::tab { background-color: #313244; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background-color: #89b4fa; color: #11111b; font-weight: bold; }
QGroupBox { border: 1px solid #45475a; border-radius: 8px; margin-top: 12px; padding-top: 12px; font-weight: bold; color: #89b4fa; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 6px 10px; color: #cdd6f4; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #89b4fa; }
QPushButton { background-color: #89b4fa; color: #11111b; border-radius: 6px; padding: 8px 14px; font-weight: bold; }
QPushButton:hover { background-color: #b4befe; }
QPushButton:disabled { background-color: #45475a; color: #7f849c; }
QPushButton#stopBtn { background-color: #f38ba8; color: #11111b; }
QPushButton#stopBtn:hover { background-color: #eba0ac; }
QPushButton#dockerBtn { background-color: #a6e3a1; color: #11111b; }
QTextEdit, QTableWidget { background-color: #11111b; border: 1px solid #313244; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 12px; color: #a6adc8; }
QHeaderView::section { background-color: #313244; color: #cdd6f4; padding: 4px; border: 1px solid #45475a; }
"""

class FlagsHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("vLLM Command Line Flags Help")
        self.resize(700, 500)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QVBoxLayout(self)
        table = QTableWidget(len(VLLM_FLAGS_HELP), 2)
        table.setHorizontalHeaderLabels(["Flag", "Description"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        for row, (flag, desc) in enumerate(VLLM_FLAGS_HELP.items()):
            table.setItem(row, 0, QTableWidgetItem(flag))
            table.setItem(row, 1, QTableWidgetItem(desc))

        layout.addWidget(table)

class VLLMManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("vLLM Manager & Open WebUI Control Center")
        self.resize(1150, 820)
        self.setStyleSheet(DARK_STYLESHEET)

        self.current_cache_dir = DEFAULT_HF_CACHE_DIR
        self.vllm_worker = None
        self.download_worker = None
        self.browser_worker = None

        self.init_ui()

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_docker_status)
        self.status_timer.start(5000)
        self.update_docker_status()

        # Initial popular models load
        self.browse_hf_models()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Cache Directory Selector Header
        cache_row = QHBoxLayout()
        cache_row.addWidget(QLabel("📂 HF Cache Path:"))
        self.cache_dir_edit = QLineEdit(self.current_cache_dir)
        cache_row.addWidget(self.cache_dir_edit, 1)
        browse_dir_btn = QPushButton("Browse Folder")
        browse_dir_btn.clicked.connect(self.select_cache_directory)
        cache_row.addWidget(browse_dir_btn)
        main_layout.addLayout(cache_row)

        tabs = QTabWidget()
        
        # TAB 1: vLLM Server & Open WebUI Launcher
        server_tab = QWidget()
        server_layout = QVBoxLayout(server_tab)

        splitter = QSplitter(Qt.Vertical)
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # vLLM Config Box
        vllm_box = QGroupBox("vLLM Parameters")
        vllm_layout = QVBoxLayout(vllm_box)

        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.refresh_models()
        model_layout.addWidget(self.model_combo, 1)
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(36)
        refresh_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(refresh_btn)
        vllm_layout.addLayout(model_layout)

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

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("GPU Mem Util:"))
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

        row3 = QHBoxLayout()
        self.tool_choice_cb = QCheckBox("Enable Auto Tool Choice")
        self.tool_choice_cb.setChecked(True)
        row3.addWidget(self.tool_choice_cb)

        row3.addWidget(QLabel("Tool Parser:"))
        self.tool_parser_combo = QComboBox()
        self.tool_parser_combo.addItems(["none", "qwen3_xml", "llama3_json", "mistral", "hermes"])
        self.tool_parser_combo.setCurrentText("qwen3_xml")
        row3.addWidget(self.tool_parser_combo)
        vllm_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Extra Flags:"))
        self.extra_flags_edit = QLineEdit()
        self.extra_flags_edit.setPlaceholderText("e.g. --trust-remote-code --dtype float16")
        row4.addWidget(self.extra_flags_edit)
        flags_help_btn = QPushButton("❓ Flags Info")
        flags_help_btn.clicked.connect(self.show_flags_help)
        row4.addWidget(flags_help_btn)
        vllm_layout.addLayout(row4)

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

        # WebUI Box
        webui_box = QGroupBox("Open WebUI Monitor")
        webui_layout = QVBoxLayout(webui_box)
        self.docker_status_lbl = QLabel("Container Status: Checking...")
        self.docker_status_lbl.setWordWrap(True)
        webui_layout.addWidget(self.docker_status_lbl)

        open_browser_btn = QPushButton("🌐 Open WebUI")
        open_browser_btn.setObjectName("dockerBtn")
        open_browser_btn.clicked.connect(lambda: webbrowser.open("http://localhost:8080"))
        webui_layout.addWidget(open_browser_btn)

        self.toggle_docker_btn = QPushButton("⚡ Start Container")
        self.toggle_docker_btn.clicked.connect(self.toggle_docker)
        webui_layout.addWidget(self.toggle_docker_btn)
        webui_layout.addStretch()
        top_layout.addWidget(webui_box, 1)

        splitter.addWidget(top_container)

        # Log Console
        log_box = QGroupBox("Console Output Logs")
        log_layout = QVBoxLayout(log_box)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        splitter.addWidget(log_box)

        server_layout.addWidget(splitter)
        tabs.addTab(server_tab, "🚀 Server & Control Center")

        # TAB 2: Advanced Hugging Face Browser & Downloader
        hf_tab = QWidget()
        hf_layout = QVBoxLayout(hf_tab)

        # Filter Control Panel
        filter_box = QGroupBox("Browse & Filter Models")
        filter_layout = QVBoxLayout(filter_box)

        frow1 = QHBoxLayout()
        frow1.addWidget(QLabel("Family:"))
        self.family_combo = QComboBox()
        self.family_combo.addItems(["All", "Qwen", "Llama", "DeepSeek", "Mistral", "Phi", "Gemma"])
        self.family_combo.currentIndexChanged.connect(self.browse_hf_models)
        frow1.addWidget(self.family_combo)

        frow1.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Coder", "Reasoning / Thinking", "Vision", "AWQ / Quantized"])
        self.category_combo.currentIndexChanged.connect(self.browse_hf_models)
        frow1.addWidget(self.category_combo)

        frow1.addWidget(QLabel("Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Most Downloads", "Likes", "Model Size (Asc)", "Model Size (Desc)", "Recently Created"])
        self.sort_combo.currentIndexChanged.connect(self.browse_hf_models)
        frow1.addWidget(self.sort_combo)
        filter_layout.addLayout(frow1)

        frow2 = QHBoxLayout()
        self.vram_filter_cb = QCheckBox("Filter by Max GPU VRAM (GB):")
        self.vram_filter_cb.stateChanged.connect(self.browse_hf_models)
        frow2.addWidget(self.vram_filter_cb)

        self.vram_spin = QSpinBox()
        self.vram_spin.setRange(1, 128)
        self.vram_spin.setValue(16)
        self.vram_spin.valueChanged.connect(self.browse_hf_models)
        frow2.addWidget(self.vram_spin)

        frow2.addWidget(QLabel("Search Keyword:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search optional keyword...")
        self.search_edit.returnPressed.connect(self.browse_hf_models)
        frow2.addWidget(self.search_edit, 1)

        apply_btn = QPushButton("🔎 Apply Filters")
        apply_btn.clicked.connect(self.browse_hf_models)
        frow2.addWidget(apply_btn)
        filter_layout.addLayout(frow2)

        hf_layout.addWidget(filter_box)

        # Table showing models with parameters & estimated VRAM
        self.hf_results_table = QTableWidget(0, 5)
        self.hf_results_table.setHorizontalHeaderLabels(["Model Repo ID", "Params", "Est. VRAM (FP16)", "Downloads", "Likes"])
        self.hf_results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.hf_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.hf_results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hf_layout.addWidget(self.hf_results_table)

        dl_row = QHBoxLayout()
        self.dl_btn = QPushButton("⬇ Download Selected Model to HF Cache")
        self.dl_btn.clicked.connect(self.download_selected_model)
        dl_row.addWidget(self.dl_btn)
        hf_layout.addLayout(dl_row)

        tabs.addTab(hf_tab, "🤗 Hugging Face Model Browser & Downloader")

        main_layout.addWidget(tabs)

    def select_cache_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select HF Cache Directory", self.current_cache_dir)
        if dir_path:
            self.current_cache_dir = dir_path
            self.cache_dir_edit.setText(dir_path)
            self.refresh_models()

    def refresh_models(self):
        self.model_combo.clear()
        cache_path = self.cache_dir_edit.text().strip() if hasattr(self, 'cache_dir_edit') else self.current_cache_dir
        models = get_cached_models(cache_path)
        if models:
            self.model_combo.addItems(models)
        else:
            self.model_combo.addItem("Qwen/Qwen2.5-1.5B-Instruct")

    def show_flags_help(self):
        dialog = FlagsHelpDialog(self)
        dialog.exec()

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
        cache_path = self.cache_dir_edit.text().strip()

        self.start_vllm_btn.setEnabled(False)
        self.stop_vllm_btn.setEnabled(True)

        self.vllm_worker = VLLMProcessWorker(cmd_args, cache_path)
        self.vllm_worker.log_received.connect(self.append_log)
        self.vllm_worker.status_changed.connect(self.on_vllm_status_change)
        self.vllm_worker.start()

    def stop_vllm(self):
        if self.vllm_worker:
            self.vllm_worker.stop_server()

    def on_vllm_status_change(self, status):
        self.vllm_status_lbl.setText(f"STATUS: {status}")
        if status == "RUNNING":
            self.vllm_status_lbl.setStyleSheet("font-weight: bold; color: #a6e3a1;")
        elif status in ["STOPPED", "IDLE", "ERROR"]:
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
            stop_open_webui()
        else:
            start_open_webui()
        self.update_docker_status()

    # HuggingFace Browser methods
    def browse_hf_models(self):
        family = self.family_combo.currentText()
        category = self.category_combo.currentText()
        sort_by = self.sort_combo.currentText()
        query = self.search_edit.text().strip()

        max_vram = self.vram_spin.value() if self.vram_filter_cb.isChecked() else None

        self.browser_worker = HFBrowserWorker(
            family=family,
            filter_tag=category,
            sort_by=sort_by,
            query=query,
            max_vram=max_vram
        )
        self.browser_worker.results_ready.connect(self.populate_hf_results)
        self.browser_worker.error_occurred.connect(lambda err: QMessageBox.critical(self, "Browse Error", err))
        self.browser_worker.start()

    def populate_hf_results(self, results):
        self.hf_results_table.setRowCount(0)
        for r in results:
            row = self.hf_results_table.rowCount()
            self.hf_results_table.insertRow(row)
            self.hf_results_table.setItem(row, 0, QTableWidgetItem(r["id"]))
            self.hf_results_table.setItem(row, 1, QTableWidgetItem(r["params_b"]))
            self.hf_results_table.setItem(row, 2, QTableWidgetItem(r["vram_gb"]))
            self.hf_results_table.setItem(row, 3, QTableWidgetItem(str(r["downloads"])))
            self.hf_results_table.setItem(row, 4, QTableWidgetItem(str(r["likes"])))

    def download_selected_model(self):
        selected_rows = self.hf_results_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a model from the table.")
            return

        repo_id = self.hf_results_table.item(selected_rows[0].row(), 0).text()
        cache_dir = self.cache_dir_edit.text().strip()

        self.dl_btn.setEnabled(False)
        self.download_worker = HFDownloadWorker(repo_id, cache_dir)
        self.download_worker.log_signal.connect(self.append_log)
        self.download_worker.finished_signal.connect(self.on_download_finished)
        self.download_worker.start()

    def on_download_finished(self, success, model_or_err):
        self.dl_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Download Complete", f"Model '{model_or_err}' successfully downloaded into cache!")
            self.refresh_models()
        else:
            QMessageBox.critical(self, "Download Failed", f"Failed to download: {model_or_err}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VLLMManagerGUI()
    window.show()
    sys.exit(app.exec())
