# vLLM Manager GUI (`vLLM-manager-gui`)

A sleek Python Qt (PySide6) desktop GUI to manage vLLM server instances, configure launch parameters via GUI controls, and monitor Open WebUI container status.

## Features
- **Local Model Manager**: Automatically scans Hugging Face cache (`/data/rspace/codespace/libs/hf_cache/hub`).
- **GUI Parameter Configurator**:
  - Model selection dropdown
  - Port assignment (default: `8000`)
  - Quantization mode (`awq`, `gptq`, `fp8`, etc.)
  - GPU Memory utilization & Max model length controls
  - Tool choice and parser toggles (`--enable-auto-tool-choice`, `--tool-call-parser qwen3_xml`)
  - Custom extra flag input box
- **Open WebUI Control**:
  - Live container status monitor
  - Start/Stop container actions
  - Direct browser launch button (`http://localhost:8080`)
- **Live Console Logs**: Real-time streaming output of vLLM startup logs and API activity.

## How to Run

```bash
cd /data/rspace/codespace/projects/vLLM-manager-gui
./run.sh
```
