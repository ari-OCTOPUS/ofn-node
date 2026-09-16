#!/usr/bin/env bash
# Brushline -- VPS first-time setup
# Run as root or with sudo on Ubuntu 22.04+
# Usage: bash setup.sh
set -euo pipefail

DEPLOY_DIR="/srv/brushline"
DATA_DIR="$DEPLOY_DIR/data"
CODE_DIR="$DEPLOY_DIR/code"
VENV_DIR="$DEPLOY_DIR/venv"
SERVICE_NAME="brushline"
PYTHON="python3"

echo "=== Brushline VPS Setup ==="

# 1. System dependencies
echo "[1/6] Installing system dependencies..."
apt-get update -q
apt-get install -y python3 python3-pip python3-venv git curl

# 2. Create directory structure
echo "[2/6] Creating directories..."
mkdir -p "$DATA_DIR" "$CODE_DIR"
chmod 750 "$DEPLOY_DIR" "$DATA_DIR"

# 3. Copy code (run this from the brushline/60_code directory)
echo "[3/6] Copying code..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rsync -av --exclude='.env' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.git' --exclude='data/' \
    "$SCRIPT_DIR/" "$CODE_DIR/"

# 4. Copy .env (user must have filled it in first)
if [ -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env" "$CODE_DIR/.env"
    chmod 600 "$CODE_DIR/.env"
    echo "   .env copied and secured (600)"
else
    echo "   WARNING: .env not found at $SCRIPT_DIR/.env -- copy manually before starting"
fi

# 5. Python virtual environment
echo "[4/6] Creating Python venv..."
$PYTHON -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$CODE_DIR/requirements.txt" -q
echo "   Dependencies installed"

# 6. Systemd service
echo "[5/6] Installing systemd service..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << SERVICE
[Unit]
Description=Brushline AI Painting Assistant
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=www-data
WorkingDirectory=$CODE_DIR
EnvironmentFile=$CODE_DIR/.env
ExecStart=$VENV_DIR/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=brushline

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$DATA_DIR

[Install]
WantedBy=multi-user.target
SERVICE

chown -R www-data:www-data "$DEPLOY_DIR"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
echo "   Service installed and enabled"

echo "[6/6] Verifying config..."
cd "$CODE_DIR"
"$VENV_DIR/bin/python" -c "
from src.config import config
missing = config.validate()
if missing:
    print('WARN: Missing required config:', missing)
    print('Fill in .env before starting the bot.')
else:
    print('Config OK -- all required keys present')
"

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Edit $CODE_DIR/.env with your real values (if not done)"
echo "  2. systemctl start brushline"
echo "  3. systemctl status brushline"
echo "  4. journalctl -u brushline -f   (live logs)"
