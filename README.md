# vLLM Manager GUI (`vLLM-manager-gui`)

![vLLM Manager Logo](logo.svg)

A modern, high-density desktop GUI application built in **Python (PySide6)** to manage local **vLLM** inference servers, browse & download Hugging Face models based on VRAM requirements, and orchestrate **Open WebUI** integration.

Designed following the **Obsidian Crimson** theme specs for power users requiring high information density and seamless local AI workflow execution.

---

## 🚀 System-Wide Installation (Linux x86_64)

Run the single curl command below to automatically download the latest binary from GitHub Releases, install it system-wide to `/usr/local/bin/vllm-manager`, and register **vLLM Manager** in your system Application Menu with custom icons:

```bash
curl -fsSL https://raw.githubusercontent.com/rmia46/vLLM-manager-gui/main/install.sh | sudo bash
```

Once installed, launch the app directly from your terminal or Application Menu:
```bash
vllm-manager
```

---

## 📦 Run Locally (Development Setup)

If you prefer running from source or customizing the codebase:

```bash
# Clone the repository
git clone https://github.com/rmia46/vLLM-manager-gui.git
cd vLLM-manager-gui

# Launch via auto-venv script
./run.sh
```

---

## 🌟 Key Features

- **🚀 Server Manager**:
  - Launch & stop local vLLM OpenAI-compatible servers.
  - GUI parameters control: Port assignment, Quantization mode (`awq`, `gptq`, `fp8`), GPU memory utilization, max model length, and tool parsers (`qwen3_xml`, etc.).
  - Interactive **Flags Info** reference dialog explaining all vLLM CLI parameters.
  - Integrated live **Dedicated GPU VRAM**, **GPU Core Utilization %**, CPU, and RAM progress gauges.

- **🤗 Hugging Face Model Browser & Downloader**:
  - Filter models by family (`Qwen`, `Llama`, `DeepSeek`, `Mistral`, `Phi`, `Gemma`).
  - Filter by task/category (`Coder`, `Reasoning / Thinking`, `Vision`, `AWQ / Quantized`).
  - **Single Quant File Selector**: For GGUF repositories, pick specific `.gguf` quant files (e.g. `2.49 GB Q4_K_M`) to avoid downloading unnecessary multi-quant 20GB files.
  - Live progress bar, download speed (`MB/s`), and **Instant Cancel Download** button.

- **💾 Local Storage Model Manager**:
  - Detailed disk breakdown of cached models (`Model ID`, `Disk Size`, `Path`).
  - Delete old or unused local models with 1-click confirmation dialog.

- **🌐 Open WebUI Integration**:
  - Automatic container status monitoring for `open-webui`.
  - Quick toggle to start/stop the Docker container.
  - Direct browser launch to `http://localhost:8080`.

- **🖥 Real-Time Live Log Console**:
  - Unbuffered continuous stdout log stream of vLLM startup events and API calls.

---

## 🎨 Design System
Built using the **Obsidian Crimson** palette:
- **Base Background**: `#0A0A0A`
- **Surface Panels**: `#121212` & `#1A1A1A`
- **Crimson Primary Accent**: `#DC143C`
- **Typography**: Plus Jakarta Sans (Branding), Inter (UI), JetBrains Mono (Terminal & Data)
