import re
import os
import sys
import subprocess
from PySide6.QtCore import QThread, Signal
from huggingface_hub import HfApi, snapshot_download

def parse_model_params(model_id):
    """
    Parses parameter count from model ID string (e.g. 1.5B, 7B, 32B, 0.5B, 4b).
    Returns params_in_billions or None.
    """
    match = re.search(r'(\d+(?:\.\d+)?)\s*[bB]\b', model_id)
    if match:
        return float(match.group(1))
    return None

def estimate_model_download_size(model_info):
    """
    Estimates actual repo download / storage size in GB using model_info files if available,
    or quantized precision heuristic (GGUF Q4 ~0.6GB/B, AWQ/GPTQ Q4 ~0.7GB/B, FP16 ~2.0GB/B).
    """
    model_id = model_info.modelId
    
    if hasattr(model_info, 'siblings') and model_info.siblings:
        total_bytes = sum(getattr(f, 'size', 0) or 0 for f in model_info.siblings)
        if total_bytes > 0:
            size_gb = total_bytes / (1024 ** 3)
            return round(size_gb, 1)

    params_b = parse_model_params(model_id)
    if params_b is None:
        return None

    model_id_upper = model_id.upper()
    if "GGUF" in model_id_upper or "Q4" in model_id_upper:
        multiplier = 0.6
    elif "Q8" in model_id_upper:
        multiplier = 1.05
    elif "AWQ" in model_id_upper or "GPTQ" in model_id_upper or "FP8" in model_id_upper:
        multiplier = 0.7
    else:
        multiplier = 2.0

    return round(params_b * multiplier, 1)

class HFBrowserWorker(QThread):
    results_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, family="All", filter_tag="All", sort_by="downloads", query="", max_vram=None):
        super().__init__()
        self.family = family
        self.filter_tag = filter_tag
        self.sort_by = sort_by
        self.query = query
        self.max_vram = max_vram

    def run(self):
        try:
            api = HfApi()
            
            search_terms = []
            if self.family != "All":
                search_terms.append(self.family)
            if self.filter_tag == "Coder":
                search_terms.append("coder")
            elif self.filter_tag == "Reasoning / Thinking":
                search_terms.append("reasoning")
            elif self.filter_tag == "Vision":
                search_terms.append("vision")
            elif self.filter_tag == "AWQ / Quantized":
                search_terms.append("AWQ")
            
            if self.query.strip():
                search_terms.append(self.query.strip())
                
            combined_search = " ".join(search_terms) if search_terms else None

            api_sort = "downloads"
            if self.sort_by == "Likes":
                api_sort = "likes"
            elif self.sort_by == "Recently Created":
                api_sort = "created_at"

            kwargs = {
                "limit": 100,
                "sort": api_sort,
            }
            if combined_search:
                kwargs["search"] = combined_search

            if self.filter_tag == "Vision":
                kwargs["pipeline_tag"] = "image-text-to-text"
            elif not combined_search and self.family == "All" and self.filter_tag == "All":
                kwargs["pipeline_tag"] = "text-generation"

            raw_models = list(api.list_models(**kwargs))

            res = []
            for m in raw_models:
                params_b = parse_model_params(m.modelId)
                size_gb = estimate_model_download_size(m)
                
                if self.max_vram is not None and size_gb is not None:
                    if size_gb > self.max_vram:
                        continue

                res.append({
                    "id": m.modelId,
                    "downloads": getattr(m, "downloads", 0),
                    "likes": getattr(m, "likes", 0),
                    "params_b": f"{params_b:.1f}B" if params_b else "Unknown",
                    "vram_gb": f"~{size_gb:.1f} GB" if size_gb else "Unknown",
                    "vram_val": size_gb or 999.0,
                    "pipeline_tag": getattr(m, "pipeline_tag", "text-generation")
                })

            if self.sort_by == "Model Size (Asc)":
                res.sort(key=lambda x: x["vram_val"])
            elif self.sort_by == "Model Size (Desc)":
                res.sort(key=lambda x: x["vram_val"], reverse=True)

            self.results_ready.emit(res)
        except Exception as e:
            self.error_occurred.emit(str(e))

class HFDownloadWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int, str)  # percent, status_text
    finished_signal = Signal(bool, str)

    def __init__(self, repo_id, hf_cache_dir):
        super().__init__()
        self.repo_id = repo_id
        self.hf_cache_dir = hf_cache_dir
        self.process = None
        self.is_cancelled = False

    def run(self):
        self.log_signal.emit(f"Starting download for '{self.repo_id}' into '{self.hf_cache_dir}'...\n")
        self.progress_signal.emit(0, f"Downloading {self.repo_id}...")

        python_script = (
            "import os, sys\n"
            "os.environ['PYTHONUNBUFFERED'] = '1'\n"
            "from huggingface_hub import snapshot_download\n"
            "try:\n"
            f"    snapshot_download(repo_id='{self.repo_id}', cache_dir='{self.hf_cache_dir}')\n"
            "    print('SUCCESS_HF_DOWNLOAD')\n"
            "except Exception as e:\n"
            "    print('ERROR_HF_DOWNLOAD:', str(e), file=sys.stderr)\n"
            "    sys.exit(1)\n"
        )

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        try:
            self.process = subprocess.Popen(
                [sys.executable, "-u", "-c", python_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )

            # Read stderr line-by-line where tqdm progress bars (speed, ETA, MB/s, %) are emitted by huggingface_hub
            percent = 0
            speed_str = "Downloading..."

            for line in iter(self.process.stderr.readline, ''):
                if not line or self.is_cancelled:
                    break
                
                self.log_signal.emit(line)

                # Parse tqdm progress line: e.g. " 45%|████▌     | 1.2G/2.5G [00:12<00:15, 85.2MB/s]"
                # Match percentage
                p_match = re.search(r'(\d+)%', line)
                if p_match:
                    percent = int(p_match.group(1))

                # Match tqdm speed & downloaded size info [00:12<00:15, 85.2MB/s] or 1.2G/2.5G
                size_match = re.search(r'([\d\.]+[kMG]B?/s|[\d\.]+[kMG]B?/s)', line)
                ratio_match = re.search(r'([\d\.]+[kMGT]?B/|\d+/\d+)', line)
                
                info_parts = []
                if ratio_match:
                    info_parts.append(ratio_match.group(0))
                if size_match:
                    info_parts.append(size_match.group(0))

                if info_parts:
                    speed_str = " | ".join(info_parts)

                status_msg = f"Downloading {self.repo_id} ({percent}%) [{speed_str}]"
                self.progress_signal.emit(percent, status_msg)

            self.process.stderr.close()
            return_code = self.process.wait()

            if self.is_cancelled:
                self.progress_signal.emit(0, "Download Cancelled")
                self.log_signal.emit(f"\n[CANCEL] Download cancelled by user for {self.repo_id}.\n")
                self.finished_signal.emit(False, "Cancelled by user")
            elif return_code == 0:
                self.progress_signal.emit(100, "Download Complete!")
                self.log_signal.emit(f"\nSuccessfully downloaded {self.repo_id}!\n")
                self.finished_signal.emit(True, self.repo_id)
            else:
                self.progress_signal.emit(0, "Download Failed")
                self.log_signal.emit(f"\nDownload failed for {self.repo_id}.\n")
                self.finished_signal.emit(False, f"Process exited with code {return_code}")
        except Exception as e:
            self.log_signal.emit(f"Error downloading {self.repo_id}: {str(e)}\n")
            self.finished_signal.emit(False, str(e))

    def cancel_download(self):
        self.is_cancelled = True
        if self.process and self.process.poll() is None:
            self.log_signal.emit("\n[CANCEL] Terminating download process...\n")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
