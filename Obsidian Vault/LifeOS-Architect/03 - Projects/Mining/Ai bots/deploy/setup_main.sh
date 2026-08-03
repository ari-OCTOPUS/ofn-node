#!/bin/bash
# =============================================================================
# deploy/setup_main.sh — Orange Pi 5 Plus  (main brain)
# =============================================================================
# Sets up the FULL bot stack on the OPi5+:
#   - System packages (Python 3.11, git, ssh, ntp)
#   - Python virtual environment + all dependencies
#   - QuantumAlphaBot + Sentinel + Coordinator + Fleet Manager
#   - .env file configuration
#   - systemd auto-start services
#   - Static IP assignment (192.168.1.100)
#
# Prerequisites:
#   - Ubuntu 22.04 / Armbian on OPi5+
#   - Run as root or with sudo
#   - Internet access
#
# Usage:
#   sudo bash deploy/setup_main.sh
# =============================================================================

set -euo pipefail

BOT_USER="pi"
BOT_HOME="/home/$BOT_USER"
BOT_DIR="$BOT_HOME/ai-bots"
STATIC_IP="192.168.1.100"
GATEWAY="192.168.1.1"
DNS="8.8.8.8"
VENV="$BOT_DIR/.venv"

echo "=== [1/8] System packages ==="
apt-get update -qq
apt-get install -y -qq \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    git wget curl htop tmux \
    openssh-server ntp \
    build-essential libssl-dev libffi-dev \
    libjpeg-dev zlib1g-dev

systemctl enable ntp && systemctl start ntp

echo "=== [2/8] Create bot user (if needed) ==="
id "$BOT_USER" 2>/dev/null || useradd -m -s /bin/bash "$BOT_USER"

echo "=== [3/8] Copy bot files ==="
# Assumes this script is run from the project root on a machine that already
# has the files. For fresh OPi5+ installs, rsync from dev machine:
#   rsync -av --exclude='.venv' --exclude='__pycache__' \
#         "Ai bots/" pi@192.168.1.100:~/ai-bots/
if [ ! -d "$BOT_DIR" ]; then
    mkdir -p "$BOT_DIR"
    echo "  Created $BOT_DIR — copy your bot files here then re-run."
fi
chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"

echo "=== [4/8] Python virtual environment ==="
sudo -u "$BOT_USER" python3.11 -m venv "$VENV"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"

sudo -u "$BOT_USER" $PIP install --upgrade pip --quiet

# Install each component's requirements
for req in \
    "$BOT_DIR/QuantumAlphaBot/requirements.txt" \
    "$BOT_DIR/sentinel/requirements.txt"; do
    if [ -f "$req" ]; then
        echo "  Installing $req..."
        sudo -u "$BOT_USER" $PIP install -r "$req" --quiet
    fi
done

# Fleet manager extra deps
sudo -u "$BOT_USER" $PIP install flask requests psutil --quiet

echo "=== [5/8] .env configuration ==="
ENV_FILE="$BOT_DIR/QuantumAlphaBot/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# Fill in your actual keys below
ANTHROPIC_API_KEY=YOUR_KEY_HERE
CRYPTOQUANT_API=ogmfC4gzi0F3yJPCUVNJ3VfPhmkCHNIBCn1unrboNOlVOdf9Xx
COINALYZE_API=bae6732b-a2da-4f6f-a7d3-1cfed8572d4f
LUNARCRUSH_API=nab3su4ybmnj8o7fma5b4kj55mpealuh9w1l5f0a
QUANTUM_BOT_TOKEN=<REDACTED-TELEGRAM-TOKEN>
QUANTUM_CHAT_ID=6150431610
EOF
    echo "  Created $ENV_FILE — verify API keys inside."
fi

SENTINEL_ENV="$BOT_DIR/sentinel/.env"
if [ ! -f "$SENTINEL_ENV" ] && [ -f "$BOT_DIR/sentinel/.env.template" ]; then
    cp "$BOT_DIR/sentinel/.env.template" "$SENTINEL_ENV"
    echo "  Created $SENTINEL_ENV from template — fill in keys."
fi

echo "=== [6/8] Static IP ==="
NETPLAN="/etc/netplan/01-static.yaml"
cat > "$NETPLAN" << EOF
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses: [$STATIC_IP/24]
      routes:
        - to: default
          via: $GATEWAY
      nameservers:
        addresses: [$DNS, 1.1.1.1]
EOF
chmod 600 "$NETPLAN"
echo "  Static IP configured: $STATIC_IP (apply with: netplan apply)"

echo "=== [7/8] systemd services ==="
SYSTEMD_DIR="$BOT_DIR/deploy/systemd"
for svc in quantumalpha coordinator fleet-manager; do
    if [ -f "$SYSTEMD_DIR/$svc.service" ]; then
        cp "$SYSTEMD_DIR/$svc.service" "/etc/systemd/system/"
        systemctl enable "$svc.service"
        echo "  Enabled: $svc.service"
    fi
done
systemctl daemon-reload

echo "=== [8/8] Fleet data directory ==="
mkdir -p "$BOT_DIR/fleet/data"
mkdir -p "$BOT_DIR/coordinator/data"
chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR/fleet" "$BOT_DIR/coordinator"

echo ""
echo "=============================================="
echo " OPi5+ setup complete!"
echo " Next steps:"
echo "  1. Edit $ENV_FILE — add your ANTHROPIC_API_KEY"
echo "  2. sudo netplan apply  (apply static IP)"
echo "  3. sudo systemctl start fleet-manager coordinator"
echo "  4. Watch logs: journalctl -fu coordinator"
echo "=============================================="
