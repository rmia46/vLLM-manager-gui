#!/bin/bash
set -e

APP_NAME="vLLM-Manager"
REPO="rmia46/vLLM-manager-gui"
INSTALL_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

echo "=========================================================="
echo "  Installing ${APP_NAME} (Linux x86_64)"
echo "=========================================================="

mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# 1. Fetch latest release archive URL from GitHub API
echo "[1/4] Fetching latest release asset URL..."
LATEST_URL=$(curl -s "https://api.github.com/repos/${REPO}/releases/latest" | grep "browser_download_url.*Linux-x86_64.tar.gz" | cut -d '"' -f 4)

if [ -z "$LATEST_URL" ]; then
    echo "Error: Could not find Linux release binary for ${REPO}."
    exit 1
fi

TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

echo "[2/4] Downloading ${APP_NAME} archive..."
curl -sL "$LATEST_URL" -o "$TMP_DIR/app.tar.gz"

echo "[3/4] Extracting and installing to $INSTALL_DIR..."
tar -xzf "$TMP_DIR/app.tar.gz" -C "$TMP_DIR"

# Move executable bundle directory
rm -rf "$HOME/.local/opt/vLLM-Manager"
mkdir -p "$HOME/.local/opt"
mv "$TMP_DIR/vLLM-Manager-Linux-x86_64" "$HOME/.local/opt/vLLM-Manager"

# Create symlink in ~/.local/bin
ln -sf "$HOME/.local/opt/vLLM-Manager/vLLM-Manager-Linux-x86_64" "$INSTALL_DIR/vllm-manager"

# Install logo icon
if [ -f "$HOME/.local/opt/vLLM-Manager/logo.svg" ]; then
    cp "$HOME/.local/opt/vLLM-Manager/logo.svg" "$ICON_DIR/vllm-manager.svg"
fi

# 4. Create Desktop Entry in Applications Menu
echo "[4/4] Creating Desktop Entry shortcut..."
cat <<EOF > "$DESKTOP_DIR/vllm-manager.desktop"
[Desktop Entry]
Name=vLLM Manager
Comment=Manage local vLLM servers, Hugging Face models, and Open WebUI
Exec=$HOME/.local/bin/vllm-manager
Icon=vllm-manager
Terminal=false
Type=Application
Categories=Utility;Development;AI;
Keywords=vLLM;LLM;AI;HuggingFace;PySide6;
EOF

chmod +x "$DESKTOP_DIR/vllm-manager.desktop"

echo ""
echo "=========================================================="
echo " SUCCESS! vLLM Manager installed successfully."
echo " - Binary Symlink: $INSTALL_DIR/vllm-manager"
echo " - Desktop Entry:  vLLM Manager in Application Menu"
echo "=========================================================="
