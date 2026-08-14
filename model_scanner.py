import os
from pathlib import Path

DEFAULT_HF_CACHE_DIR = "/data/rspace/codespace/libs/hf_cache"

def get_cached_models(cache_dir_path=DEFAULT_HF_CACHE_DIR):
    """Scans the specified HF cache directory and returns a list of model IDs."""
    models = []
    path = Path(cache_dir_path)
    hub_path = path / "hub" if (path / "hub").exists() else path

    if not hub_path.exists():
        return models

    for folder in hub_path.iterdir():
        if folder.is_dir() and folder.name.startswith("models--"):
            parts = folder.name[len("models--"):].split("--")
            if len(parts) >= 2:
                model_id = f"{parts[0]}/{'--'.join(parts[1:])}"
                models.append(model_id)
            elif len(parts) == 1:
                models.append(parts[0])
    return sorted(models)
