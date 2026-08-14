import sys
import os
import subprocess
from PySide6.QtCore import QThread, Signal

VENV_VLLM = "/data/rspace/codespace/libs/python_env/3.12/.venv/bin/vllm"

class VLLMProcessWorker(QThread):
    log_received = Signal(str)
    status_changed = Signal(str)

    def __init__(self, cmd_args, hf_cache_path):
        super().__init__()
        self.cmd_args = cmd_args
        self.hf_cache_path = hf_cache_path
        self.process = None
        self._is_stopping = False

    def run(self):
        self.status_changed.emit("STARTING")
        env = os.environ.copy()
        env["HF_HOME"] = self.hf_cache_path

        cmd = [VENV_VLLM, "serve"] + self.cmd_args
        self.log_received.emit(f"[vLLM Manager] HF_HOME={self.hf_cache_path}\n")
        self.log_received.emit(f"[vLLM Manager] Executing command: {' '.join(cmd)}\n")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1
            )

            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_received.emit(line)
                    if "Uvicorn running on" in line or "Application startup complete" in line:
                        self.status_changed.emit("RUNNING")

            self.process.wait()
            if not self._is_stopping:
                self.status_changed.emit("STOPPED")
                self.log_received.emit("[vLLM Manager] Process exited.\n")

        except Exception as e:
            self.status_changed.emit("ERROR")
            self.log_received.emit(f"[vLLM Manager Error] {str(e)}\n")

    def stop_server(self):
        self._is_stopping = True
        if self.process and self.process.poll() is None:
            self.log_received.emit("[vLLM Manager] Sending SIGTERM to vLLM...\n")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.status_changed.emit("STOPPED")
