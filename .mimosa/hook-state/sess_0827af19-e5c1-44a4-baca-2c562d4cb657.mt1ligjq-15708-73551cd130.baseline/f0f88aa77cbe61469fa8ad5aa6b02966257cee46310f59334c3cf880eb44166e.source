#!/bin/bash
# =============================================================================
# deploy/setup_worker.sh — Orange Pi 5 Pro worker nodes (×9)
# =============================================================================
# Run on EACH OPi5 Pro. Sets up:
#   - XMRig (CPU miner for RandomX/CryptoNight)
#   - cpuminer-multi (Yespower/Ghostrider/other algos)
#   - fleet/worker_agent.py
#   - systemd auto-start
#
# Usage (run as root on each worker):
#   WORKER_ID=w01 MANAGER_URL=http://192.168.1.100:7700 \
#   WALLET_ADDR=YOUR_WALLET bash deploy/setup_worker.sh
#
# Variables:
#   WORKER_ID     e.g. w01 .. w09  (REQUIRED — unique per node)
#   MANAGER_URL   http://192.168.1.100:7700
#   WALLET_ADDR   Your mining wallet address
#   STATIC_IP     e.g. 192.168.1.101 (optional — if you want static IP)
# =============================================================================

set -euo pipefail

WORKER_ID="${WORKER_ID:-w01}"
MANAGER_URL="${MANAGER_URL:-http://192.168.1.100:7700}"
WALLET_ADDR="${WALLET_ADDR:-}"
STATIC_IP="${STATIC_IP:-}"
GATEWAY="192.168.1.1"

BOT_USER="pi"
BOT_HOME="/home/$BOT_USER"
BOT_DIR="$BOT_HOME/ai-bots"
VENV="$BOT_DIR/.venv"

echo "=== [1/6] System packages ==="
apt-get update -qq
apt-get install -y -qq \
    python3.11 python3.11-venv python3-pip \
    git wget curl htop build-essential \
    libssl-dev libhwloc-dev libuv1-dev cmake

id "$BOT_USER" 2>/dev/null || useradd -m -s /bin/bash "$BOT_USER"

echo "=== [2/6] XMRig (RandomX / CryptoNight) ==="
if [ ! -f /usr/local/bin/xmrig ]; then
    XMRIG_VER="6.21.3"
    ARCH="linux-static-aarch64"
    URL="https://github.com/xmrig/xmrig/releases/download/v${XMRIG_VER}/xmrig-${XMRIG_VER}-${ARCH}.tar.gz"
    echo "  Downloading XMRig v$XMRIG_VER..."
    wget -q "$URL" -O /tmp/xmrig.tar.gz
    tar xf /tmp/xmrig.tar.gz -C /tmp/
    cp /tmp/xmrig-*/xmrig /usr/local/bin/xmrig
    chmod +x /usr/local/bin/xmrig
    rm -rf /tmp/xmrig*
    echo "  XMRig installed at /usr/local/bin/xmrig"

    # Enable huge pages for RandomX (3× hashrate boost)
    echo "vm.nr_hugepages=1280" >> /etc/sysctl.conf
    sysctl -p >/dev/null 2>&1 || true
fi

echo "=== [3/6] cpuminer-multi (Yespower / Ghostrider / other) ==="
if [ ! -f /usr/local/bin/cpuminer ]; then
    echo "  Building cpuminer-multi from source..."
    git clone --depth=1 https://github.com/tpruvot/cpuminer-multi /tmp/cpuminer-multi
    cd /tmp/cpuminer-multi
    ./autogen.sh
    CFLAGS="-O3 -march=native" ./configure --with-crypto --with-curl
    make -j$(nproc)
    cp cpuminer /usr/local/bin/cpuminer
    chmod +x /usr/local/bin/cpuminer
    cd /
    rm -rf /tmp/cpuminer-multi
    echo "  cpuminer installed at /usr/local/bin/cpuminer"
fi

echo "=== [4/6] Python worker agent ==="
mkdir -p "$BOT_DIR"
chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"

# Create minimal Python env (only requests needed)
sudo -u "$BOT_USER" python3.11 -m venv "$VENV"
sudo -u "$BOT_USER" "$VENV/bin/pip" install requests flask --quiet

echo "=== [5/6] Environment config ==="
ENV_FILE="/etc/worker-agent.env"
cat > "$ENV_FILE" << EOF
MANAGER_URL=$MANAGER_URL
WORKER_ID=$WORKER_ID
WALLET_ADDR=$WALLET_ADDR
POLL_INTERVAL=30
XMRIG_PATH=/usr/local/bin/xmrig
CPUMINER_PATH=/usr/local/bin/cpuminer
WORKER_LOG=/var/log/worker-${WORKER_ID}.log
EOF
chmod 600 "$ENV_FILE"
echo "  Worker config: $ENV_FILE"

echo "=== [6/6] Static IP (optional) ==="
if [ -n "$STATIC_IP" ]; then
    cat > /etc/netplan/01-static.yaml << EOF
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
        addresses: [8.8.8.8, 1.1.1.1]
EOF
    chmod 600 /etc/netplan/01-static.yaml
    echo "  Static IP configured: $STATIC_IP"
fi

echo "=== systemd worker service ==="
cat > /etc/systemd/system/worker-agent.service << EOF
[Unit]
Description=Fleet Worker Agent ($WORKER_ID)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
EnvironmentFile=/etc/worker-agent.env
ExecStart=$VENV/bin/python -m fleet.worker_agent
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable worker-agent.service

echo ""
echo "=============================================="
echo " Worker $WORKER_ID setup complete!"
echo " Next steps:"
echo "  1. Copy ai-bots/fleet/ from main to $BOT_DIR/fleet/"
echo "  2. Edit /etc/worker-agent.env — add WALLET_ADDR"
echo "  3. sudo systemctl start worker-agent"
echo "  4. Watch: journalctl -fu worker-agent"
echo "=============================================="
