import subprocess
import requests

CONTAINER_NAME = "open-webui"

def check_open_webui_status():
    """
    Returns a dict with:
    - container_running: bool
    - http_ok: bool
    - container_id/status_text: str
    """
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=3
        )
        status_text = res.stdout.strip()
        is_running = bool(status_text)
    except Exception as e:
        status_text = str(e)
        is_running = False

    http_ok = False
    if is_running:
        try:
            r = requests.get("http://localhost:8080", timeout=2)
            http_ok = r.status_code == 200
        except Exception:
            http_ok = False

    return {
        "container_running": is_running,
        "http_ok": http_ok,
        "status_text": status_text if is_running else "Stopped / Not Found"
    }

def start_open_webui():
    """Attempts to start the container."""
    try:
        # Check if exists
        res = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        if CONTAINER_NAME in res.stdout.splitlines():
            subprocess.run(["docker", "start", CONTAINER_NAME], check=True)
        else:
            subprocess.run([
                "docker", "run", "-d", "--network", "host",
                "--name", CONTAINER_NAME, "--restart", "always",
                "ghcr.io/open-webui/open-webui:main"
            ], check=True)
        return True, "Container started"
    except Exception as e:
        return False, str(e)

def stop_open_webui():
    try:
        subprocess.run(["docker", "stop", CONTAINER_NAME], check=True)
        return True, "Container stopped"
    except Exception as e:
        return False, str(e)
