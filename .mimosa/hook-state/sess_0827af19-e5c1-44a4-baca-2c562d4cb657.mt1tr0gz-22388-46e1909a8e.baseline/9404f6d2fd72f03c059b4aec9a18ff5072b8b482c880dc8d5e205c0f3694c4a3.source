#!/bin/bash
# =============================================================================
# deploy/setup_rpi.sh — Raspberry Pi 3B  (watchdog / backup monitor)
# =============================================================================
# Minimal setup — only the watchdog service runs here.
# RPi3B has 1GB RAM — do NOT run the full bot on it.
#
# Usage (run as root on RPi3B):
#   MAIN_URL=http://192.168.1.100:7700 \
#   TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=xxx \
#   bash deploy/setup_rpi.sh
# =============================================================================

set -euo pipefail

MAIN_URL="${MAIN_URL:-http://192.168.1.100:7700}"
COORD_HOST="${COORD_HOST:-192.168.1.100}"
COORD_USER="${COORD_USER:-pi}"
TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
STATIC_IP="${STATIC_IP:-192.168.1.110}"
GATEWAY="192.168.1.1"

BOT_USER="pi"
BOT_DIR="/home/$BOT_USER/ai-bots"
VENV="$BOT_DIR/.venv"

echo "=== [1/4] System packages ==="
apt-get update -qq
apt-get install -y -qq \
    python3 python3-venv python3-pip \
    openssh-client git curl wget

echo "=== [2/4] Python env ==="
mkdir -p "$BOT_DIR"
chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"
sudo -u "$BOT_USER" python3 -m venv "$VENV"
sudo -u "$BOT_USER" "$VENV/bin/pip" install requests --quiet

echo "=== [3/4] Environment config ==="
cat > /etc/watchdog-agent.env << EOF
MAIN_URL=$MAIN_URL
COORDINATOR_HOST=$COORD_HOST
COORDINATOR_USER=$COORD_USER
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
CHECK_INTERVAL=60
ALERT_AFTER_FAILS=3
SSH_RESTART=false
WATCHDOG_LOG=/var/log/fleet-watchdog.log
EOF
chmod 600 /etc/watchdog-agent.env

echo "=== [4/4] systemd watchdog service ==="
cat > /etc/systemd/system/watchdog.service << EOF
[Unit]
Description=Fleet Watchdog (RPi3B)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
EnvironmentFile=/etc/watchdog-agent.env
ExecStart=$VENV/bin/python -m fleet.watchdog
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable watchdog.service

# Static IP
if [ -n "$STATIC_IP" ]; then
    cat > /etc/dhcpcd.conf.static << EOF
interface eth0
static ip_address=$STATIC_IP/24
static routers=$GATEWAY
static domain_name_servers=8.8.8.8 1.1.1.1
EOF
    # Append to dhcpcd.conf (RPi OS style)
    cat /etc/dhcpcd.conf.static >> /etc/dhcpcd.conf
fi

echo ""
echo "=============================================="
echo " RPi3B watchdog setup complete!"
echo " Next steps:"
echo "  1. Copy ai-bots/fleet/watchdog.py to $BOT_DIR/fleet/"
echo "  2. Edit /etc/watchdog-agent.env — add TELEGRAM keys"
echo "  3. sudo systemctl start watchdog"
echo "  4. Watch: journalctl -fu watchdog"
echo "=============================================="
