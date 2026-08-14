import os
import shutil
from pathlib import Path

DEFAULT_HF_CACHE_DIR = "/data/rspace/codespace/libs/hf_cache"

def get_cached_models_details(cache_dir_path=DEFAULT_HF_CACHE_DIR):
    """
    Scans HF cache directory and returns detailed info:
    list of dicts containing: id, folder_name, folder_path, size_gb
    """
    results = []
    path = Path(cache_dir_path)
    hub_path = path / "hub" if (path / "hub").exists() else path

    if not hub_path.exists():
        return results

    for folder in hub_path.iterdir():
        if folder.is_dir() and folder.name.startswith("models--"):
            parts = folder.name[len("models--"):].split("--")
            if len(parts) >= 2:
                model_id = f"{parts[0]}/{'--'.join(parts[1:])}"
            elif len(parts) == 1:
                model_id = parts[0]
            else:
                model_id = folder.name

            # Calculate total folder size
            total_bytes = sum(f.stat().st_size for f in folder.glob('**/*') if f.is_file())
            size_gb = round(total_bytes / (1024 ** 3), 2)

            results.append({
                "id": model_id,
                "folder_name": folder.name,
                "folder_path": str(folder),
                "size_gb": size_gb
            })
    return sorted(results, key=lambda x: x["id"])

def get_cached_models(cache_dir_path=DEFAULT_HF_CACHE_DIR):
    """Scans the specified HF cache directory and returns a list of model IDs."""
    details = get_cached_models_details(cache_dir_path)
    return [d["id"] for d in details]

def delete_cached_model(folder_path):
    """Deletes a model directory from HF cache."""
    path = Path(folder_path)
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        return True
    return False
