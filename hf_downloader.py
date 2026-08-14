import re
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
    
    # 1. If HfApi returned model.siblings (file info with size)
    if hasattr(model_info, 'siblings') and model_info.siblings:
        total_bytes = sum(getattr(f, 'size', 0) or 0 for f in model_info.siblings)
        if total_bytes > 0:
            size_gb = total_bytes / (1024 ** 3)
            return round(size_gb, 1)

    # 2. Heuristic fallback based on quant/format in repo ID
    params_b = parse_model_params(model_id)
    if params_b is None:
        return None

    model_id_upper = model_id.upper()
    if "GGUF" in model_id_upper or "Q4" in model_id_upper:
        multiplier = 0.6  # ~4-bit quantization (~0.6 GB per B params)
    elif "Q8" in model_id_upper:
        multiplier = 1.05 # ~8-bit quantization (~1.05 GB per B params)
    elif "AWQ" in model_id_upper or "GPTQ" in model_id_upper or "FP8" in model_id_upper:
        multiplier = 0.7  # ~4-8 bit GPU quants
    else:
        multiplier = 2.0  # FP16 / BF16 default (~2.0 GB per B params)

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
                
                # Check VRAM / Size filter if set
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

            # Additional in-memory sort if requested by Model Size / Download Size
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
            self.log_signal.emit(f"Error downloading {self.repo_id}: {str(e)}\n")
            self.finished_signal.emit(False, str(e))
