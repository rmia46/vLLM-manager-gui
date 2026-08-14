#!/bin/bash
set -e

APP_NAME="vLLM-Manager"
REPO="rmia46/vLLM-manager-gui"
INSTALL_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/scalable/apps"
OPT_DIR="/opt/vLLM-Manager"

# Check root/sudo permissions for system-wide installation
if [ "$EUID" -ne 0 ]; then
  echo "System-wide installation requires root/sudo privileges."
  echo "Re-running script with sudo..."
  exec sudo "$0" "$@"
fi

echo "=========================================================="
echo "  Installing ${APP_NAME} System-Wide (Linux x86_64)"
echo "=========================================================="

mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"
mkdir -p "$OPT_DIR"

# 1. Fetch latest release asset URL from GitHub API
echo "[1/4] Fetching latest release asset URL..."
LATEST_URL=$(curl -s "https://api.github.com/repos/${REPO}/releases/latest" | grep "browser_download_url.*Linux-x86_64.tar.gz" | cut -d '"' -f 4)

if [ -z "$LATEST_URL" ]; then
    echo "Error: Could not find Linux release binary for ${REPO}."
    exit 1
fi

TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

echo "[2/4] Downloading ${APP_NAME} binary package..."
curl -sL "$LATEST_URL" -o "$TMP_DIR/app.tar.gz"

echo "[3/4] Extracting system-wide to ${OPT_DIR}..."
rm -rf "${OPT_DIR:?}/*"
tar -xzf "$TMP_DIR/app.tar.gz" -C "$TMP_DIR"
cp -r "$TMP_DIR/vLLM-Manager-Linux-x86_64"/* "$OPT_DIR/"

# Create system-wide binary symlink in /usr/local/bin
ln -sf "$OPT_DIR/vLLM-Manager-Linux-x86_64" "$INSTALL_DIR/vllm-manager"
chmod +x "$INSTALL_DIR/vllm-manager"

# Copy icon
if [ -f "$OPT_DIR/logo.svg" ]; then
    cp "$OPT_DIR/logo.svg" "$ICON_DIR/vllm-manager.svg"
fi

# 4. Register System-Wide Desktop Entry
echo "[4/4] Creating system-wide desktop application menu entry..."
cat <<EOF > "$DESKTOP_DIR/vllm-manager.desktop"
[Desktop Entry]
Name=vLLM Manager
Comment=Manage local vLLM servers, Hugging Face models, and Open WebUI
Exec=/usr/local/bin/vllm-manager
Icon=vllm-manager
Terminal=false
Type=Application
Categories=Utility;Development;AI;
Keywords=vLLM;LLM;AI;HuggingFace;PySide6;
EOF

chmod +x "$DESKTOP_DIR/vllm-manager.desktop"

echo ""
echo "=========================================================="
echo " SUCCESS! vLLM Manager installed system-wide."
echo " - System Binary: /usr/local/bin/vllm-manager"
echo " - App Directory: /opt/vLLM-Manager"
echo " - Menu Shortcut: vLLM Manager in Application Menu"
echo "=========================================================="
