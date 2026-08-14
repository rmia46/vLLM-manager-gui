# vLLM Manager GUI (`vLLM-manager-gui`)

![vLLM Manager Logo](logo.svg)

A modern, high-density desktop GUI application built in **Python (PySide6)** to manage local **vLLM** inference servers, browse & download Hugging Face models based on VRAM requirements, and orchestrate **Open WebUI** integration.

Designed following the **Obsidian Crimson** theme specs for power users requiring high information density and seamless local AI workflow execution.

---

## 🌟 Key Features

- **🚀 Server Manager**:
  - Launch & stop local vLLM OpenAI-compatible servers.
  - GUI parameters control: Port assignment, Quantization mode (`awq`, `gptq`, `fp8`), GPU memory utilization, max model length, and tool parsers (`qwen3_xml`, etc.).
  - Interactive **Flags Info** reference dialog explaining all vLLM CLI parameters.
  - Integrated live CPU Usage % and RAM Usage progress gauges.

- **🤗 Hugging Face Model Browser & Downloader**:
  - Filter models by family (`Qwen`, `Llama`, `DeepSeek`, `Mistral`, `Phi`, `Gemma`).
  - Filter by task/category (`Coder`, `Reasoning / Thinking`, `Vision`, `AWQ / Quantized`).
  - **Max GPU VRAM Calculator**: Enter your available GPU VRAM (e.g. 16GB) to automatically hide models that won't fit.
  - One-click downloader directly into your custom Hugging Face cache folder.

- **🌐 Open WebUI Integration**:
  - Automatic container status monitoring for `open-webui`.
  - Quick toggle to start/stop the Docker container.
  - Direct browser launch to `http://localhost:8080`.

- **🖥 Live Log Console**:
  - Real-time continuous output log stream of vLLM startup events and API calls.

---

## 📦 Installation & Quickstart

### Prerequisites
- Python 3.12+
- `uv` package manager (or standard python venv)
- Docker (for optional Open WebUI integration)

### Running the App

```bash
# Clone the repository
git clone https://github.com/rmia46/vLLM-manager-gui.git
cd vLLM-manager-gui

# Launch via auto-venv script
./run.sh
```

---

## 🎨 Design System
Built using the **Obsidian Crimson** palette:
- **Base Background**: `#0A0A0A`
- **Surface Panels**: `#121212` & `#1A1A1A`
- **Crimson Primary Accent**: `#DC143C`
- **Typography**: Plus Jakarta Sans (Branding), Inter (UI), JetBrains Mono (Terminal & Data)
