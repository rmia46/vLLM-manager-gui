import re
import os
import sys
import subprocess
from PySide6.QtCore import QThread, Signal
from huggingface_hub import HfApi, hf_hub_download

def parse_model_params(model_id):
    match = re.search(r'(\d+(?:\.\d+)?)\s*[bB]\b', model_id)
    if match:
        return float(match.group(1))
    return None

def estimate_model_download_size(model_info):
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

    def __init__(self, repo_id, hf_cache_dir, selected_filename=None, hf_token=None):
        super().__init__()
        self.repo_id = repo_id
        self.hf_cache_dir = hf_cache_dir
        self.selected_filename = selected_filename
        self.hf_token = hf_token
        self.process = None
        self.is_cancelled = False

    def run(self):
        self.log_signal.emit(f"Starting download for '{self.repo_id}' into '{self.hf_cache_dir}'...\n")
        self.progress_signal.emit(0, f"Downloading {self.repo_id}...")

        token_str = f"'{self.hf_token}'" if self.hf_token else "None"

        if self.selected_filename:
            py_code = (
                "import os, sys\n"
                "os.environ['PYTHONUNBUFFERED'] = '1'\n"
                "from huggingface_hub import hf_hub_download\n"
                f"hf_hub_download(repo_id='{self.repo_id}', filename='{self.selected_filename}', cache_dir='{self.hf_cache_dir}', token={token_str})\n"
            )
        else:
            py_code = (
                "import os, sys\n"
                "os.environ['PYTHONUNBUFFERED'] = '1'\n"
                "from huggingface_hub import snapshot_download\n"
                f"snapshot_download(repo_id='{self.repo_id}', cache_dir='{self.hf_cache_dir}', token={token_str})\n"
            )

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        if self.hf_token:
            env["HF_TOKEN"] = self.hf_token
            env["HUGGING_FACE_HUB_TOKEN"] = self.hf_token

        try:
            self.process = subprocess.Popen(
                [sys.executable, "-u", "-c", py_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )

            last_percent = 0
            buf = ""

            # Read both stdout and stderr dynamically line by line / character by character
            while True:
                if self.is_cancelled:
                    if self.process and self.process.poll() is None:
                        self.process.kill()
                    break

                # Non-blocking check for subprocess stdout / stderr text
                chunk = self.process.stderr.read(128)
                if not chunk:
                    if self.process.poll() is not None:
                        break
                    continue

                buf += chunk
                while '\r' in buf or '\n' in buf:
                    # Pick earliest delimiter
                    r_pos = buf.find('\r')
                    n_pos = buf.find('\n')

                    if r_pos != -1 and (n_pos == -1 or r_pos < n_pos):
                        line, buf = buf[:r_pos], buf[r_pos+1:]
                    else:
                        line, buf = buf[:n_pos], buf[n_pos+1:]

                    clean_line = line.strip()
                    if clean_line:
                        self.log_signal.emit(clean_line + "\n")

                        p_match = re.search(r'(\d+)%', clean_line)
                        if p_match:
                            last_percent = int(p_match.group(1))

                        ratio_match = re.search(r'(\d+/\d+|[\d\.]+[kMGT]?B?/[\d\.]+[kMGT]?B?)', clean_line)
                        speed_match = re.search(r'([\d\.]+[kMGT]?B/s)', clean_line)

                        info_parts = []
                        if ratio_match:
                            info_parts.append(ratio_match.group(0))
                        if speed_match:
                            info_parts.append(speed_match.group(0))

                        speed_str = " | ".join(info_parts) if info_parts else "Downloading..."
                        self.progress_signal.emit(last_percent, f"Downloading {self.repo_id} ({last_percent}%) [{speed_str}]")

            return_code = self.process.wait() if self.process else 0

            if self.is_cancelled:
                self.progress_signal.emit(0, "Download Cancelled")
                self.log_signal.emit(f"\n[CANCEL] Download killed by user for {self.repo_id}.\n")
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
            self.log_signal.emit("\n[CANCEL] Killing download subprocess immediately...\n")
            self.process.kill()
