import sys
import os
import requests
import webbrowser
import psutil
import subprocess
import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QDoubleSpinBox, QSpinBox,
    QPushButton, QTextEdit, QGroupBox, QSplitter, QMessageBox,
    QFileDialog, QStackedWidget, QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QGridLayout, QProgressBar, QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
from huggingface_hub import HfApi

from model_scanner import get_cached_models, get_cached_models_details, delete_cached_model, DEFAULT_HF_CACHE_DIR
from docker_checker import check_open_webui_status, start_open_webui, stop_open_webui
from vllm_runner import VLLMProcessWorker
from hf_downloader import HFBrowserWorker, HFDownloadWorker
from vllm_flags_info import VLLM_FLAGS_HELP
from stitch_theme import STITCH_DARK_STYLESHEET

VENV_VLLM = "/data/rspace/codespace/libs/python_env/3.12/.venv/bin/vllm"

def get_gpu_info():
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = [p.strip() for p in res.stdout.strip().split(",")]
            if len(parts) >= 4:
                return parts[0], float(parts[1]), float(parts[2]), float(parts[3])
    except Exception:
        pass
    return None

class SolidCard(QFrame):
    def __init__(self, title_text, icon_name=None):
        super().__init__()
        self.setObjectName("panelCard")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = QLabel()
        self.header.setObjectName("cardHeader")
        if icon_name:
            self.header.setText(f"   {title_text.upper()}")
        else:
            self.header.setText(title_text.upper())
        
        self.layout.addWidget(self.header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(12, 12, 12, 12)
        self.body_layout.setSpacing(10)
        self.layout.addWidget(self.body)

class FlagsHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("vLLM Command Line Flags Help")
        self.resize(720, 500)
        self.setStyleSheet(STITCH_DARK_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        table = QTableWidget(len(VLLM_FLAGS_HELP), 2)
        table.setHorizontalHeaderLabels(["FLAG", "DESCRIPTION"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        for row, (flag, desc) in enumerate(VLLM_FLAGS_HELP.items()):
            table.setItem(row, 0, QTableWidgetItem(flag))
            table.setItem(row, 1, QTableWidgetItem(desc))

        layout.addWidget(table)

class VLLMManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("vLLM Manager")
        self.resize(1380, 850)
        self.setStyleSheet(STITCH_DARK_STYLESHEET)

        logo_path = os.path.join(os.path.dirname(__file__), "logo.svg")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self.current_cache_dir = DEFAULT_HF_CACHE_DIR
        self.vllm_worker = None
        self.download_worker = None
        self.browser_worker = None

        self.init_ui()

        # Timers
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_docker_status)
        self.status_timer.start(5000)
        self.update_docker_status()

        self.sys_timer = QTimer(self)
        self.sys_timer.timeout.connect(self.update_system_stats)
        self.sys_timer.start(2000)
        self.update_system_stats()

        self.browse_hf_models()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------------------------------------------------------------
        # COLUMN A: Left Sidebar (Fixed 240px)
        # -------------------------------------------------------------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(8)

        # Branding Header
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(8)
        logo_path = os.path.join(os.path.dirname(__file__), "logo.svg")
        if os.path.exists(logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            brand_layout.addWidget(logo_lbl)

        brand_label = QLabel("vLLM Manager")
        brand_label.setFont(QFont("Plus Jakarta Sans", 16, QFont.Bold))
        brand_label.setStyleSheet("color: #ffb3b3; margin-bottom: 0px;")
        brand_layout.addWidget(brand_label, 1)

        sidebar_layout.addLayout(brand_layout)
        sidebar_layout.addSpacing(16)

        # Navigation items
        self.nav_server_btn = QPushButton("  Server Manager")
        self.nav_server_btn.setIcon(qta.icon('fa5s.server', color='#ac8888'))
        self.nav_server_btn.setObjectName("navBtn")
        self.nav_server_btn.setCheckable(True)
        self.nav_server_btn.setChecked(True)
        self.nav_server_btn.clicked.connect(lambda: self.switch_tab(0))
        sidebar_layout.addWidget(self.nav_server_btn)

        self.nav_browser_btn = QPushButton("  Model Browser")
        self.nav_browser_btn.setIcon(qta.icon('fa5s.cubes', color='#ac8888'))
        self.nav_browser_btn.setObjectName("navBtn")
        self.nav_browser_btn.setCheckable(True)
        self.nav_browser_btn.clicked.connect(lambda: self.switch_tab(1))
        sidebar_layout.addWidget(self.nav_browser_btn)

        self.nav_manage_btn = QPushButton("  Local Storage Manager")
        self.nav_manage_btn.setIcon(qta.icon('fa5s.hdd', color='#ac8888'))
        self.nav_manage_btn.setObjectName("navBtn")
        self.nav_manage_btn.setCheckable(True)
        self.nav_manage_btn.clicked.connect(lambda: self.switch_tab(2))
        sidebar_layout.addWidget(self.nav_manage_btn)

        sidebar_layout.addStretch()

        # Engine Status Card
        status_card = SolidCard("Engine Status")
        self.vllm_status_lbl = QLabel("STATUS: IDLE")
        self.vllm_status_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-weight: bold; font-size: 11px; color: #ffb4a5;")
        status_card.body_layout.addWidget(self.vllm_status_lbl)

        restart_btn = QPushButton("  Restart Engine")
        restart_btn.setIcon(qta.icon('fa5s.redo-alt', color='#ffb3b3'))
        restart_btn.setObjectName("secondaryBtn")
        restart_btn.clicked.connect(self.stop_vllm)
        status_card.body_layout.addWidget(restart_btn)

        sidebar_layout.addWidget(status_card)
        main_layout.addWidget(sidebar)

        # -------------------------------------------------------------
        # COLUMN B: Center Workspace
        # -------------------------------------------------------------
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        # Top Header Bar
        header_bar = QHBoxLayout()
        header_bar.setSpacing(10)
        header_title = QLabel("vLLM Manager")
        header_title.setFont(QFont("Plus Jakarta Sans", 16, QFont.Bold))
        header_title.setStyleSheet("color: #e5e2e1;")
        header_bar.addWidget(header_title)

        header_bar.addStretch()

        cache_label = QLabel("HF Cache:")
        cache_label.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 700; color: #ac8888;")
        header_bar.addWidget(cache_label)

        self.cache_dir_edit = QLineEdit(self.current_cache_dir)
        self.cache_dir_edit.setFixedWidth(200)
        header_bar.addWidget(self.cache_dir_edit)

        browse_dir_btn = QPushButton("Browse")
        browse_dir_btn.setIcon(qta.icon('fa5s.folder-open', color='#ffb3b3'))
        browse_dir_btn.setObjectName("secondaryBtn")
        browse_dir_btn.clicked.connect(self.select_cache_directory)
        header_bar.addWidget(browse_dir_btn)

        token_label = QLabel("HF Token:")
        token_label.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 700; color: #ac8888;")
        header_bar.addWidget(token_label)

        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setEchoMode(QLineEdit.Password)
        self.hf_token_edit.setPlaceholderText("hf_xxxxxxxxxxxx")
        self.hf_token_edit.setFixedWidth(160)
        # Pre-fill HF_TOKEN environment variable if available
        if "HF_TOKEN" in os.environ:
            self.hf_token_edit.setText(os.environ["HF_TOKEN"])
        header_bar.addWidget(self.hf_token_edit)

        content_layout.addLayout(header_bar)

        # Stacked Views Widget
        self.stack = QStackedWidget()

        # VIEW 1: Server Manager
        server_view = QWidget()
        server_layout = QVBoxLayout(server_view)
        server_layout.setContentsMargins(0, 0, 0, 0)
        server_layout.setSpacing(12)

        # Primary Action & GPU System Monitor Card
        hero_card = SolidCard("Primary Action & GPU System Monitor")
        
        hero_top = QHBoxLayout()
        hero_top.setSpacing(10)

        hero_top.addWidget(QLabel("Select Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.currentIndexChanged.connect(self.update_selected_model_info)
        self.model_combo.editTextChanged.connect(self.update_selected_model_info)

        # Selected Model Metadata Horizontal Pill Row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        self.meta_family_lbl = QLabel("FAMILY: --")
        self.meta_family_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb3b3; background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 4px; padding: 2px 8px; max-height: 14px;")

        self.meta_params_lbl = QLabel("PARAMS: --")
        self.meta_params_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb3b3; background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 4px; padding: 2px 8px; max-height: 14px;")

        self.meta_size_lbl = QLabel("DISK SIZE: --")
        self.meta_size_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb3b3; background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 4px; padding: 2px 8px; max-height: 14px;")

        self.meta_status_lbl = QLabel("STATE: CACHED")
        self.meta_status_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ac8888; background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 4px; padding: 2px 8px; max-height: 14px;")

        meta_row.addWidget(self.meta_family_lbl)
        meta_row.addWidget(self.meta_params_lbl)
        meta_row.addWidget(self.meta_size_lbl)
        meta_row.addWidget(self.meta_status_lbl)
        meta_row.addStretch()

        self.refresh_models()
        hero_top.addWidget(self.model_combo, 1)

        refresh_btn = QPushButton("  Rescan")
        refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='#ffb3b3'))
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.setToolTip("Rescan local models")
        refresh_btn.clicked.connect(self.refresh_models)
        hero_top.addWidget(refresh_btn)

        self.start_vllm_btn = QPushButton("  Launch Server")
        self.start_vllm_btn.setIcon(qta.icon('fa5s.play', color='#ffffff'))
        self.start_vllm_btn.setObjectName("primaryBtn")
        self.start_vllm_btn.clicked.connect(self.start_vllm)
        hero_top.addWidget(self.start_vllm_btn)

        self.stop_vllm_btn = QPushButton("  Stop Server")
        self.stop_vllm_btn.setIcon(qta.icon('fa5s.stop', color='#ffffff'))
        self.stop_vllm_btn.setObjectName("stopBtn")
        self.stop_vllm_btn.setEnabled(False)
        self.stop_vllm_btn.clicked.connect(self.stop_vllm)
        hero_top.addWidget(self.stop_vllm_btn)

        hero_card.body_layout.addLayout(hero_top)
        hero_card.body_layout.addLayout(meta_row)

        # System & Dedicated GPU Gauges Grid
        env_grid = QGridLayout()
        env_grid.setSpacing(10)

        gpu_col = QVBoxLayout()
        gpu_col.setSpacing(2)
        self.gpu_name_label = QLabel("GPU VRAM: DETECTING...")
        self.gpu_name_label.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb3b3;")
        self.gpu_bar = QProgressBar()
        self.gpu_bar.setValue(0)
        gpu_col.addWidget(self.gpu_name_label)
        gpu_col.addWidget(self.gpu_bar)
        env_grid.addLayout(gpu_col, 0, 0)

        gpu_util_col = QVBoxLayout()
        gpu_util_col.setSpacing(2)
        self.gpu_util_label = QLabel("GPU CORE UTILIZATION: 0%")
        self.gpu_util_label.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb3b3;")
        self.gpu_util_bar = QProgressBar()
        self.gpu_util_bar.setValue(0)
        gpu_util_col.addWidget(self.gpu_util_label)
        gpu_util_col.addWidget(self.gpu_util_bar)
        env_grid.addLayout(gpu_util_col, 0, 1)

        cpu_col = QVBoxLayout()
        cpu_col.setSpacing(2)
        self.cpu_label = QLabel("CPU USAGE: 0%")
        self.cpu_label.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ac8888;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setValue(0)
        cpu_col.addWidget(self.cpu_label)
        cpu_col.addWidget(self.cpu_bar)
        env_grid.addLayout(cpu_col, 1, 0)

        ram_col = QVBoxLayout()
        ram_col.setSpacing(2)
        self.ram_label = QLabel("RAM USAGE: 0 GB / 0 GB")
        self.ram_label.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ac8888;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setValue(0)
        ram_col.addWidget(self.ram_label)
        ram_col.addWidget(self.ram_bar)
        env_grid.addLayout(ram_col, 1, 1)

        vllm_installed = os.path.exists(VENV_VLLM)
        self.vllm_env_lbl = QLabel(f"vLLM Engine: {' INSTALLED' if vllm_installed else ' NOT FOUND'}")
        self.vllm_env_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: {'#ffb3b3' if vllm_installed else '#ffb4ab'};")

        self.webui_env_lbl = QLabel("Open WebUI: CHECKING...")
        self.webui_env_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ac8888;")

        env_status_row = QHBoxLayout()
        env_status_row.setSpacing(14)
        env_status_row.addWidget(self.vllm_env_lbl)
        env_status_row.addWidget(self.webui_env_lbl)
        env_status_row.addStretch()

        env_grid.addLayout(env_status_row, 2, 0, 1, 2)
        hero_card.body_layout.addLayout(env_grid)

        server_layout.addWidget(hero_card)

        # Compact Symmetric Grid Config Panel
        vllm_card = SolidCard("Server Configuration Parameters")
        grid = QGridLayout()
        grid.setSpacing(8)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(8000)

        self.quant_combo = QComboBox()
        self.quant_combo.addItems(["none", "awq", "gptq", "fp8", "squeezellm"])

        grid.addWidget(QLabel("Port:"), 0, 0)
        grid.addWidget(self.port_spin, 1, 0)
        grid.addWidget(QLabel("Quantization:"), 0, 1)
        grid.addWidget(self.quant_combo, 1, 1)

        self.gpu_spin = QDoubleSpinBox()
        self.gpu_spin.setRange(0.10, 1.00)
        self.gpu_spin.setSingleStep(0.05)
        self.gpu_spin.setValue(0.90)

        self.max_len_spin = QSpinBox()
        self.max_len_spin.setRange(512, 131072)
        self.max_len_spin.setSingleStep(512)
        self.max_len_spin.setValue(4096)

        grid.addWidget(QLabel("GPU Mem Util (0.10 - 1.00):"), 2, 0)
        grid.addWidget(self.gpu_spin, 3, 0)
        grid.addWidget(QLabel("Max Model Length:"), 2, 1)
        grid.addWidget(self.max_len_spin, 3, 1)

        self.tool_choice_cb = QCheckBox("Enable Auto Tool Choice")
        self.tool_choice_cb.setChecked(True)

        self.tool_parser_combo = QComboBox()
        self.tool_parser_combo.addItems(["none", "qwen3_xml", "llama3_json", "mistral", "hermes"])
        self.tool_parser_combo.setCurrentText("qwen3_xml")

        grid.addWidget(self.tool_choice_cb, 5, 0)
        grid.addWidget(QLabel("Tool Parser:"), 4, 1)
        grid.addWidget(self.tool_parser_combo, 5, 1)

        extra_container = QWidget()
        e_layout = QHBoxLayout(extra_container)
        e_layout.setContentsMargins(0, 0, 0, 0)
        e_layout.setSpacing(6)
        self.extra_flags_edit = QLineEdit()
        self.extra_flags_edit.setPlaceholderText("e.g. --trust-remote-code --dtype float16")
        e_layout.addWidget(self.extra_flags_edit, 1)
        flags_help_btn = QPushButton(" Flags Info")
        flags_help_btn.setIcon(qta.icon('fa5s.question-circle', color='#ffb3b3'))
        flags_help_btn.setObjectName("secondaryBtn")
        flags_help_btn.clicked.connect(self.show_flags_help)
        e_layout.addWidget(flags_help_btn)

        grid.addWidget(QLabel("Extra Command Line Flags:"), 6, 0, 1, 2)
        grid.addWidget(extra_container, 7, 0, 1, 2)

        vllm_card.body_layout.addLayout(grid)
        server_layout.addWidget(vllm_card)
        self.stack.addWidget(server_view)

        # VIEW 2: Model Browser
        browser_view = QWidget()
        browser_layout = QVBoxLayout(browser_view)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(10)

        filter_card = SolidCard("Browse & Filter Models")
        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(8)

        frow1 = QHBoxLayout()
        frow1.setSpacing(10)
        frow1.addWidget(QLabel("Family:"))
        self.family_combo = QComboBox()
        self.family_combo.addItems(["All", "Qwen", "Llama", "DeepSeek", "Mistral", "Phi", "Gemma"])
        self.family_combo.currentIndexChanged.connect(self.browse_hf_models)
        frow1.addWidget(self.family_combo, 1)

        frow1.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Coder", "Reasoning / Thinking", "Vision", "AWQ / Quantized"])
        self.category_combo.currentIndexChanged.connect(self.browse_hf_models)
        frow1.addWidget(self.category_combo, 1)

        frow1.addWidget(QLabel("Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Most Downloads", "Likes", "Model Size (Asc)", "Model Size (Desc)", "Recently Created"])
        self.sort_combo.currentIndexChanged.connect(self.browse_hf_models)
        frow1.addWidget(self.sort_combo, 1)
        filter_layout.addLayout(frow1)

        frow2 = QHBoxLayout()
        frow2.setSpacing(10)
        self.vram_filter_cb = QCheckBox("Filter Max GPU VRAM (GB):")
        self.vram_filter_cb.stateChanged.connect(self.browse_hf_models)
        frow2.addWidget(self.vram_filter_cb)

        self.vram_spin = QSpinBox()
        self.vram_spin.setRange(1, 128)
        self.vram_spin.setValue(16)
        self.vram_spin.valueChanged.connect(self.browse_hf_models)
        frow2.addWidget(self.vram_spin)

        frow2.addWidget(QLabel("Keyword:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search keyword...")
        self.search_edit.returnPressed.connect(self.browse_hf_models)
        frow2.addWidget(self.search_edit, 1)

        apply_btn = QPushButton("  Apply")
        apply_btn.setIcon(qta.icon('fa5s.search', color='#ffb3b3'))
        apply_btn.setObjectName("secondaryBtn")
        apply_btn.clicked.connect(self.browse_hf_models)
        frow2.addWidget(apply_btn)
        filter_layout.addLayout(frow2)

        filter_card.body_layout.addLayout(filter_layout)
        browser_layout.addWidget(filter_card)

        self.hf_results_table = QTableWidget(0, 5)
        self.hf_results_table.setHorizontalHeaderLabels(["MODEL REPO ID", "PARAMS", "EST. DOWNLOAD SIZE", "DOWNLOADS", "LIKES"])
        self.hf_results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.hf_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.hf_results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        browser_layout.addWidget(self.hf_results_table)

        dl_row = QHBoxLayout()
        dl_row.setSpacing(10)
        
        self.dl_btn = QPushButton("  Download Selected Model to Cache")
        self.dl_btn.setIcon(qta.icon('fa5s.download', color='#ffffff'))
        self.dl_btn.setObjectName("primaryBtn")
        self.dl_btn.clicked.connect(self.download_selected_model)
        dl_row.addWidget(self.dl_btn, 1)

        self.cancel_dl_btn = QPushButton("  Cancel Download")
        self.cancel_dl_btn.setIcon(qta.icon('fa5s.times-circle', color='#ffffff'))
        self.cancel_dl_btn.setObjectName("stopBtn")
        self.cancel_dl_btn.setEnabled(False)
        self.cancel_dl_btn.clicked.connect(self.cancel_download)
        dl_row.addWidget(self.cancel_dl_btn)

        browser_layout.addLayout(dl_row)

        self.dl_status_lbl = QLabel("Download Status: Idle")
        self.dl_status_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ac8888;")
        browser_layout.addWidget(self.dl_status_lbl)

        self.dl_progress_bar = QProgressBar()
        self.dl_progress_bar.setValue(0)
        self.dl_progress_bar.setVisible(False)
        browser_layout.addWidget(self.dl_progress_bar)

        self.stack.addWidget(browser_view)

        # VIEW 3: Local Storage Model Manager
        manage_view = QWidget()
        manage_layout = QVBoxLayout(manage_view)
        manage_layout.setContentsMargins(0, 0, 0, 0)
        manage_layout.setSpacing(10)

        manage_card = SolidCard("Local Storage Model Manager")
        
        m_top = QHBoxLayout()
        m_top.setSpacing(10)

        self.storage_info_lbl = QLabel("Storage Usage: Calculating...")
        self.storage_info_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-weight: bold; font-size: 11px; color: #ffb3b3;")
        m_top.addWidget(self.storage_info_lbl, 1)

        refresh_storage_btn = QPushButton("  Refresh Storage")
        refresh_storage_btn.setIcon(qta.icon('fa5s.sync-alt', color='#ffb3b3'))
        refresh_storage_btn.setObjectName("secondaryBtn")
        refresh_storage_btn.clicked.connect(self.refresh_storage_manager)
        m_top.addWidget(refresh_storage_btn)

        delete_selected_btn = QPushButton("  Delete Selected Model")
        delete_selected_btn.setIcon(qta.icon('fa5s.trash-alt', color='#ffffff'))
        delete_selected_btn.setObjectName("stopBtn")
        delete_selected_btn.clicked.connect(self.delete_selected_local_model)
        m_top.addWidget(delete_selected_btn)

        manage_card.body_layout.addLayout(m_top)
        manage_layout.addWidget(manage_card)

        self.local_models_table = QTableWidget(0, 3)
        self.local_models_table.setHorizontalHeaderLabels(["MODEL ID", "DISK STORAGE SIZE", "CACHE DIRECTORY PATH"])
        self.local_models_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.local_models_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.local_models_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        manage_layout.addWidget(self.local_models_table)

        self.stack.addWidget(manage_view)

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_area, 1)

        # -------------------------------------------------------------
        # COLUMN C: Right Control Dock
        # -------------------------------------------------------------
        right_dock = QFrame()
        right_dock.setFixedWidth(340)
        right_dock.setStyleSheet("background-color: #121212; border-left: 1px solid #2A2A2A;")
        right_layout = QVBoxLayout(right_dock)
        right_layout.setContentsMargins(12, 16, 12, 16)
        right_layout.setSpacing(10)

        webui_card = SolidCard("Open WebUI Integration")
        self.docker_status_lbl = QLabel("Container Status: Checking...")
        self.docker_status_lbl.setWordWrap(True)
        webui_card.body_layout.addWidget(self.docker_status_lbl)

        open_browser_btn = QPushButton("  Open WebUI (localhost:8080)")
        open_browser_btn.setIcon(qta.icon('fa5s.external-link-alt', color='#ffffff'))
        open_browser_btn.setObjectName("primaryBtn")
        open_browser_btn.clicked.connect(lambda: webbrowser.open("http://localhost:8080"))
        webui_card.body_layout.addWidget(open_browser_btn)

        self.toggle_docker_btn = QPushButton("  Start Container")
        self.toggle_docker_btn.setIcon(qta.icon('fa5s.bolt', color='#ffb3b3'))
        self.toggle_docker_btn.setObjectName("secondaryBtn")
        self.toggle_docker_btn.clicked.connect(self.toggle_docker)
        webui_card.body_layout.addWidget(self.toggle_docker_btn)

        right_layout.addWidget(webui_card)

        log_card = SolidCard("Live Log Stream")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_card.body_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("Clear Logs")
        clear_log_btn.setObjectName("secondaryBtn")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_card.body_layout.addWidget(clear_log_btn, alignment=Qt.AlignRight)

        right_layout.addWidget(log_card, 1)

        main_layout.addWidget(right_dock)

        self.refresh_storage_manager()

    def update_system_stats(self):
        try:
            cpu = psutil.cpu_percent()
            self.cpu_bar.setValue(int(cpu))
            self.cpu_label.setText(f"CPU USAGE: {cpu:.1f}%")

            ram = psutil.virtual_memory()
            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)
            self.ram_bar.setValue(int(ram.percent))
            self.ram_label.setText(f"RAM USAGE: {ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB")

            gpu_info = get_gpu_info()
            if gpu_info:
                gpu_name, used_mb, total_mb, util_pct = gpu_info
                used_gb = used_mb / 1024.0
                total_gb = total_mb / 1024.0
                vram_pct = (used_mb / total_mb) * 100.0 if total_mb > 0 else 0

                self.gpu_name_label.setText(f"GPU VRAM ({gpu_name}): {used_gb:.2f} GB / {total_gb:.2f} GB")
                self.gpu_bar.setValue(int(vram_pct))

                self.gpu_util_label.setText(f"GPU CORE UTILIZATION: {util_pct:.0f}%")
                self.gpu_util_bar.setValue(int(util_pct))
            else:
                self.gpu_name_label.setText("GPU VRAM: NO NVIDIA GPU DETECTED")
                self.gpu_bar.setValue(0)
                self.gpu_util_label.setText("GPU CORE UTILIZATION: N/A")
                self.gpu_util_bar.setValue(0)
        except Exception:
            pass

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        self.nav_server_btn.setChecked(index == 0)
        self.nav_browser_btn.setChecked(index == 1)
        self.nav_manage_btn.setChecked(index == 2)

        self.nav_server_btn.setIcon(qta.icon('fa5s.server', color='#ffb3b3' if index == 0 else '#ac8888'))
        self.nav_browser_btn.setIcon(qta.icon('fa5s.cubes', color='#ffb3b3' if index == 1 else '#ac8888'))
        self.nav_manage_btn.setIcon(qta.icon('fa5s.hdd', color='#ffb3b3' if index == 2 else '#ac8888'))

        if index == 2:
            self.refresh_storage_manager()

    def select_cache_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select HF Cache Directory", self.current_cache_dir)
        if dir_path:
            self.current_cache_dir = dir_path
            self.cache_dir_edit.setText(dir_path)
            self.refresh_models()
            self.refresh_storage_manager()

    def refresh_models(self):
        curr = self.model_combo.currentText().strip()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        cache_path = self.cache_dir_edit.text().strip() if hasattr(self, 'cache_dir_edit') else self.current_cache_dir
        models = get_cached_models(cache_path)
        if models:
            self.model_combo.addItems(models)
            if curr and curr in models:
                self.model_combo.setCurrentText(curr)
        else:
            self.model_combo.addItem("Qwen/Qwen2.5-1.5B-Instruct")
        self.model_combo.blockSignals(False)
        self.update_selected_model_info()

    def update_selected_model_info(self):
        model_name = self.model_combo.currentText().strip()
        if not model_name:
            self.meta_family_lbl.setText("FAMILY: --")
            self.meta_params_lbl.setText("PARAMS: --")
            self.meta_size_lbl.setText("DISK SIZE: --")
            self.meta_status_lbl.setText("STATE: NONE")
            return

        cache_path = self.cache_dir_edit.text().strip() if hasattr(self, 'cache_dir_edit') else self.current_cache_dir
        details = get_cached_models_details(cache_path)

        match_detail = next((d for d in details if d["id"] == model_name), None)

        if match_detail:
            self.meta_family_lbl.setText(f"FAMILY: {match_detail['family'].upper()}")
            self.meta_params_lbl.setText(f"PARAMS: {match_detail['params']}")
            self.meta_size_lbl.setText(f"DISK SIZE: {match_detail['size_gb']:.2f} GB")
            self.meta_status_lbl.setText("STATE: LOCAL CACHE")
            self.meta_status_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb3b3; background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 4px; padding: 2px 8px; max-height: 14px;")
        else:
            from model_scanner import detect_model_family
            family_str = detect_model_family(model_name)
            p_match = re.search(r'(\d+(?:\.\d+)?)\s*[bB]\b', model_name)
            params_str = f"{p_match.group(1)}B" if p_match else "Unknown"

            self.meta_family_lbl.setText(f"FAMILY: {family_str.upper()}")
            self.meta_params_lbl.setText(f"PARAMS: {params_str}")
            self.meta_size_lbl.setText("DISK SIZE: UNCACHED")
            self.meta_status_lbl.setText("STATE: REMOTE HF REPO")
            self.meta_status_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ac8888; background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 4px; padding: 2px 8px; max-height: 14px;")

    def refresh_storage_manager(self):
        cache_path = self.cache_dir_edit.text().strip() if hasattr(self, 'cache_dir_edit') else self.current_cache_dir
        details = get_cached_models_details(cache_path)

        self.local_models_table.setRowCount(0)
        total_disk_gb = 0.0

        for d in details:
            row = self.local_models_table.rowCount()
            self.local_models_table.insertRow(row)

            item_id = QTableWidgetItem(d["id"])
            item_id.setData(Qt.UserRole, d["folder_path"])

            item_size = QTableWidgetItem(f"{d['size_gb']:.2f} GB")
            item_path = QTableWidgetItem(d["folder_path"])

            self.local_models_table.setItem(row, 0, item_id)
            self.local_models_table.setItem(row, 1, item_size)
            self.local_models_table.setItem(row, 2, item_path)

            total_disk_gb += d["size_gb"]

        self.storage_info_lbl.setText(f"Total Local Model Storage: {total_disk_gb:.2f} GB ({len(details)} Models)")

    def delete_selected_local_model(self):
        selected_rows = self.local_models_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a model row to delete.")
            return

        row = selected_rows[0].row()
        model_id = self.local_models_table.item(row, 0).text()
        folder_path = self.local_models_table.item(row, 0).data(Qt.UserRole)
        size_str = self.local_models_table.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirm Model Deletion",
            f"Are you sure you want to delete model '{model_id}' ({size_str}) from disk?\n\nFolder: {folder_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            success = delete_cached_model(folder_path)
            if success:
                QMessageBox.information(self, "Model Deleted", f"Model '{model_id}' was successfully deleted.")
                self.refresh_storage_manager()
                self.refresh_models()
            else:
                QMessageBox.critical(self, "Deletion Failed", f"Failed to delete directory: {folder_path}")

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
        hf_token = self.hf_token_edit.text().strip()

        self.start_vllm_btn.setEnabled(False)
        self.stop_vllm_btn.setEnabled(True)

        self.vllm_worker = VLLMProcessWorker(cmd_args, cache_path, hf_token=hf_token)
        self.vllm_worker.log_received.connect(self.append_log)
        self.vllm_worker.status_changed.connect(self.on_vllm_status_change)
        self.vllm_worker.start()

    def stop_vllm(self):
        if self.vllm_worker:
            self.vllm_worker.stop_server()

    def on_vllm_status_change(self, status):
        self.vllm_status_lbl.setText(f"STATUS: {status}")
        if status == "RUNNING":
            self.vllm_status_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-weight: bold; font-size: 11px; color: #ffb3b3;")
        elif status in ["STOPPED", "IDLE", "ERROR"]:
            self.vllm_status_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 11px; color: #ffb4ab;")
            self.start_vllm_btn.setEnabled(True)
            self.stop_vllm_btn.setEnabled(False)

    def append_log(self, text):
        self.log_text.append(text.rstrip())

    def update_docker_status(self):
        status = check_open_webui_status()
        if status["container_running"]:
            self.docker_status_lbl.setText(f"Container: RUNNING\n({status['status_text']})")
            self.docker_status_lbl.setStyleSheet("color: #ffb3b3; font-weight: 600;")
            self.webui_env_lbl.setText("Open WebUI: READY (Docker Active)")
            self.webui_env_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb3b3;")
            self.toggle_docker_btn.setText("  Stop Container")
            self.toggle_docker_btn.setIcon(qta.icon('fa5s.stop-circle', color='#ffb3b3'))
        else:
            self.docker_status_lbl.setText(f"Container: STOPPED")
            self.docker_status_lbl.setStyleSheet("color: #ffb4ab; font-weight: 600;")
            self.webui_env_lbl.setText("Open WebUI: CONTAINER STOPPED")
            self.webui_env_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; color: #ffb4ab;")
            self.toggle_docker_btn.setText("  Start Container")
            self.toggle_docker_btn.setIcon(qta.icon('fa5s.bolt', color='#ffb3b3'))

    def toggle_docker(self):
        status = check_open_webui_status()
        if status["container_running"]:
            stop_open_webui()
        else:
            start_open_webui()
        self.update_docker_status()

    def browse_hf_models(self):
        family = self.family_combo.currentText()
        category = self.category_combo.currentText()
        sort_by = self.sort_combo.currentText()
        query = self.search_edit.text().strip()
        max_vram = self.vram_spin.value() if self.vram_filter_cb.isChecked() else None

        self.browser_worker = HFBrowserWorker(
            family=family, filter_tag=category, sort_by=sort_by, query=query, max_vram=max_vram
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

        # If model repository contains GGUF files, prompt user to select specific quant file
        selected_filename = None
        if "GGUF" in repo_id.upper():
            try:
                api = HfApi()
                info = api.model_info(repo_id, files_metadata=True)
                file_map = {}
                file_options = []
                for f in info.siblings:
                    if f.rfilename.endswith(".gguf"):
                        size_gb = (getattr(f, "size", 0) or 0) / (1024 ** 3)
                        display_str = f"{f.rfilename} ({size_gb:.2f} GB)"
                        file_map[display_str] = f.rfilename
                        file_options.append(display_str)
                
                if file_options:
                    item, ok = QInputDialog.getItem(
                        self,
                        "Select GGUF Quant File",
                        f"Found {len(file_options)} GGUF quant file(s) in '{repo_id}'.\nSelect specific quant file to download:",
                        file_options,
                        0,
                        False
                    )
                    if ok and item and item in file_map:
                        selected_filename = file_map[item]
                    elif not ok:
                        return
            except Exception as e:
                self.append_log(f"Warning: Could not fetch GGUF file list: {str(e)}\n")

        self.dl_btn.setEnabled(False)
        self.cancel_dl_btn.setEnabled(True)
        self.dl_progress_bar.setVisible(True)
        self.dl_progress_bar.setValue(0)
        target_name = selected_filename or repo_id
        self.dl_status_lbl.setText(f"Download Status: Starting download for {target_name}...")

        hf_token = self.hf_token_edit.text().strip()
        self.download_worker = HFDownloadWorker(repo_id, cache_dir, selected_filename=selected_filename, hf_token=hf_token)
        self.download_worker.log_signal.connect(self.append_log)
        self.download_worker.progress_signal.connect(self.on_download_progress)
        self.download_worker.finished_signal.connect(self.on_download_finished)
        self.download_worker.start()

    def on_download_progress(self, percent, text):
        self.dl_progress_bar.setValue(percent)
        self.dl_status_lbl.setText(f"Download Status: {text}")

    def cancel_download(self):
        if self.download_worker:
            self.download_worker.cancel_download()
            self.cancel_dl_btn.setEnabled(False)

    def on_download_finished(self, success, model_or_err):
        self.dl_btn.setEnabled(True)
        self.cancel_dl_btn.setEnabled(False)
        if success:
            self.dl_progress_bar.setValue(100)
            self.dl_status_lbl.setText("Download Status: Download Completed Successfully!")
            QMessageBox.information(self, "Download Complete", f"Model '{model_or_err}' successfully downloaded into cache!")
            self.refresh_models()
            self.refresh_storage_manager()
        else:
            self.dl_progress_bar.setValue(0)
            self.dl_status_lbl.setText("Download Status: Stopped / Error")
            QMessageBox.critical(self, "Download Result", f"Status: {model_or_err}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VLLMManagerGUI()
    window.show()
    sys.exit(app.exec())
