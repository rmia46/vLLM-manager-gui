import os
from pathlib import Path

HF_CACHE_DIR = Path("/data/rspace/codespace/libs/hf_cache/hub")

def get_cached_models():
    """Scans the local HF cache directory and returns a list of repo IDs."""
    models = []
    if not HF_CACHE_DIR.exists():
        return models

    for folder in HF_CACHE_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith("models--"):
            parts = folder.name[len("models--"):].split("--")
            if len(parts) >= 2:
                model_id = f"{parts[0]}/{'--'.join(parts[1:])}"
                models.append(model_id)
            elif len(parts) == 1:
                models.append(parts[0])
    return sorted(models)
