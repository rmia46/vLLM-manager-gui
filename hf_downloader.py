import re
from PySide6.QtCore import QThread, Signal
from huggingface_hub import HfApi, snapshot_download

def parse_model_params(model_id):
    """
    Parses parameter count from model ID string (e.g. 1.5B, 7B, 32B, 0.5B).
    Returns (params_in_billions, estimated_vram_gb_fp16)
    """
    match = re.search(r'(\d+(?:\.\d+)?)\s*[bB]\b', model_id)
    if match:
        params_b = float(match.group(1))
        # Rough estimate for FP16: ~2.2 GB VRAM per billion parameters + 2 GB overhead
        vram_gb = round(params_b * 2.2 + 2.0, 1)
        return params_b, vram_gb
    return None, None

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
            
            # Build search string
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

            # Determine sorting key for API call (huggingface_hub >= 1.0)
            api_sort = "downloads"
            if self.sort_by == "Likes":
                api_sort = "likes"
            elif self.sort_by == "Recently Created":
                api_sort = "created_at"

            kwargs = {
                "limit": 60,
                "sort": api_sort,
            }
            if combined_search:
                kwargs["search"] = combined_search
            if self.filter_tag == "Vision":
                kwargs["pipeline_tag"] = "image-text-to-text"
            else:
                kwargs["pipeline_tag"] = "text-generation"

            raw_models = list(api.list_models(**kwargs))

            res = []
            for m in raw_models:
                params_b, vram_gb = parse_model_params(m.modelId)
                
                # Check VRAM filter if set
                if self.max_vram is not None and vram_gb is not None:
                    if vram_gb > self.max_vram:
                        continue

                res.append({
                    "id": m.modelId,
                    "downloads": getattr(m, "downloads", 0),
                    "likes": getattr(m, "likes", 0),
                    "params_b": f"{params_b:.1f}B" if params_b else "Unknown",
                    "vram_gb": f"~{vram_gb:.1f} GB" if vram_gb else "Unknown",
                    "vram_val": vram_gb or 999.0,
                    "pipeline_tag": getattr(m, "pipeline_tag", "text-generation")
                })

            # Additional in-memory sort if requested by VRAM / Size
            if self.sort_by == "Model Size (Asc)":
                res.sort(key=lambda x: x["vram_val"])
            elif self.sort_by == "Model Size (Desc)":
                res.sort(key=lambda x: x["vram_val"], reverse=True)

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
