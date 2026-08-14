import sys
import os
import subprocess
from PySide6.QtCore import QThread, Signal
from huggingface_hub import HfApi, snapshot_download

VENV_PYTHON = "/data/rspace/codespace/libs/python_env/3.12/.venv/bin/python"

class HFSearchWorker(QThread):
    results_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            api = HfApi()
            models = api.list_models(
                search=self.query,
                limit=20,
                sort="downloads",
                direction=-1
            )
            res = []
            for m in models:
                res.append({
                    "id": m.modelId,
                    "downloads": getattr(m, "downloads", 0),
                    "likes": getattr(m, "likes", 0),
                    "pipeline_tag": getattr(m, "pipeline_tag", "text-generation")
                })
            self.results_ready.emit(res)
        except Exception as e:
            self.error_occurred.emit(str(e))

class HFDownloadWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, repo_id, hf_cache_dir):
        super().__init__()
        self.repo_id = repo_id
        self.hf_cache_dir = hf_cache_dir

    def run(self):
        self.log_signal.emit(f"Starting download for '{self.repo_id}' into '{self.hf_cache_dir}'...\n")
        try:
            snapshot_download(
                repo_id=self.repo_id,
                cache_dir=self.hf_cache_dir,
                resume_download=True
            )
            self.log_signal.emit(f"Successfully downloaded {self.repo_id}!\n")
            self.finished_signal.emit(True, self.repo_id)
        except Exception as e:
            self.log_signal.emit(f"Download Error: {str(e)}\n")
            self.finished_signal.emit(False, str(e))
