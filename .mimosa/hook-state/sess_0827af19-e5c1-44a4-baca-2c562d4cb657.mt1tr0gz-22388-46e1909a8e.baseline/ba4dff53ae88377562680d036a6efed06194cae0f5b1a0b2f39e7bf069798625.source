#!/bin/bash
# ============================================================
# SENTINEL — deploy.sh
# Stage B: Deploy to Orange Pi 5 OR Raspberry Pi 3B
# مرحله B: استقرار روی Orange Pi 5 یا Raspberry Pi 3B
#
# Usage / نحوه استفاده:
#   bash deploy.sh              # interactive
#   bash deploy.sh --dry-run    # print steps only / فقط نمایش مراحل
# ============================================================

set -e
DRY_RUN=false
[[ "$1" == "--dry-run" ]] && DRY_RUN=true

SENTINEL_USER="sentinel"
SENTINEL_DIR="/home/${SENTINEL_USER}/sentinel"
VENV_DIR="${SENTINEL_DIR}/venv"
SERVICE_NAME="sentinel"

run() {
    if $DRY_RUN; then
        echo "[DRY-RUN] $*"
    else
        eval "$@"
    fi
}

echo "======================================================"
echo "  SENTINEL — Stage B Deployment"
echo "  استقرار SENTINEL روی Orange Pi 5 / Pi 3B"
echo "======================================================"

# ─── Detect hardware ───
if grep -q "Orange Pi" /proc/cpuinfo 2>/dev/null || \
   grep -q "RK3588" /proc/cpuinfo 2>/dev/null; then
    HW="Orange Pi 5"
elif grep -q "Raspberry" /proc/cpuinfo 2>/dev/null; then
    HW="Raspberry Pi 3B"
else
    HW="Unknown SBC (treating as Pi-compatible)"
fi
echo ""
echo "[0/9] Hardware detected: $HW"

# ─── Step 1: System packages ───
echo ""
echo "[1/9] Installing system packages..."
run sudo apt-get update -qq
run sudo apt-get install -y -qq python3 python3-pip python3-venv git sqlite3

# ─── Step 2: Isolated user ───
echo ""
echo "[2/9] Creating isolated user '${SENTINEL_USER}'..."
if id "$SENTINEL_USER" &>/dev/null; then
    echo "  User '${SENTINEL_USER}' already exists — skipping"
else
    run sudo useradd -m -s /bin/bash "$SENTINEL_USER"
    echo "  ✅ User created"
fi

# ─── Step 3: Copy project files ───
echo ""
echo "[3/9] Copying project files to ${SENTINEL_DIR}..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
run sudo mkdir -p "$SENTINEL_DIR"
run sudo rsync -a --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='backtest_cache' \
    "${SCRIPT_DIR}/" "${SENTINEL_DIR}/"
run sudo chown -R "${SENTINEL_USER}:${SENTINEL_USER}" "$SENTINEL_DIR"
echo "  ✅ Files copied"

# ─── Step 4: Virtual environment ───
echo ""
echo "[4/9] Setting up Python virtual environment..."
run sudo -u "$SENTINEL_USER" python3 -m venv "$VENV_DIR"
run sudo -u "$SENTINEL_USER" "${VENV_DIR}/bin/pip" install --upgrade pip -q
run sudo -u "$SENTINEL_USER" "${VENV_DIR}/bin/pip" install \
    -r "${SENTINEL_DIR}/requirements.txt" -q
echo "  ✅ Virtual environment ready"

# ─── Step 5: .env file ───
echo ""
echo "[5/9] Setting up .env..."
if [ ! -f "${SENTINEL_DIR}/.env" ]; then
    run sudo -u "$SENTINEL_USER" cp \
        "${SENTINEL_DIR}/.env.example" "${SENTINEL_DIR}/.env"
    echo ""
    echo "  ⚠️  .env was created from template. Edit it now:"
    echo "      sudo -u ${SENTINEL_USER} nano ${SENTINEL_DIR}/.env"
    echo ""
    if ! $DRY_RUN; then
        read -p "  Press ENTER after editing .env to continue..." -r
    fi
fi
run sudo chmod 600 "${SENTINEL_DIR}/.env"
run sudo chown "${SENTINEL_USER}:${SENTINEL_USER}" "${SENTINEL_DIR}/.env"
echo "  ✅ .env secured (permissions: 600)"

# ─── Step 6: systemd timer ───
echo ""
echo "[6/9] Installing systemd timer..."

TIMER_UNIT="/etc/systemd/system/${SERVICE_NAME}.timer"
SERVICE_UNIT="/etc/systemd/system/${SERVICE_NAME}.service"

run sudo tee "$SERVICE_UNIT" > /dev/null << EOF
[Unit]
Description=SENTINEL crypto signal robot
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=${SENTINEL_USER}
WorkingDirectory=${SENTINEL_DIR}
ExecStart=${VENV_DIR}/bin/python3 ${SENTINEL_DIR}/main.py --once
StandardOutput=append:${SENTINEL_DIR}/sentinel.log
StandardError=append:${SENTINEL_DIR}/sentinel.log
# Resource limits — Pi 3B safe / محدودیت منابع
MemoryMax=120M
CPUQuota=30%

[Install]
WantedBy=multi-user.target
EOF

run sudo tee "$TIMER_UNIT" > /dev/null << EOF
[Unit]
Description=SENTINEL timer — runs every 15 minutes
Requires=${SERVICE_NAME}.service

[Timer]
OnBootSec=60
OnUnitActiveSec=15min
AccuracySec=30

[Install]
WantedBy=timers.target
EOF

run sudo systemctl daemon-reload
run sudo systemctl enable "${SERVICE_NAME}.timer"
run sudo systemctl start "${SERVICE_NAME}.timer"
echo "  ✅ systemd timer enabled (every 15 minutes)"

# ─── Step 7: Mock self-test ───
echo ""
echo "[7/9] Running mock self-test..."
if $DRY_RUN; then
    echo "[DRY-RUN] Would run: SENTINEL_MOCK_MODE=1 python3 main.py --once"
else
    sudo -u "$SENTINEL_USER" bash -c \
        "cd ${SENTINEL_DIR} && SENTINEL_MOCK_MODE=1 ${VENV_DIR}/bin/python3 main.py --once" \
        && echo "  ✅ Mock self-test passed" \
        || echo "  ❌ Mock self-test failed — check ${SENTINEL_DIR}/sentinel.log"
fi

# ─── Step 8: Resource check ───
echo ""
echo "[8/9] Resource usage check..."
FREE_MEM=$(free -m | awk '/^Mem:/ {print $7}')
CPU_CORES=$(nproc)
echo "  Available RAM:  ${FREE_MEM} MB"
echo "  CPU cores:      ${CPU_CORES}"
if [ "$FREE_MEM" -lt 80 ]; then
    echo "  ⚠️  Low memory warning: < 80 MB free"
else
    echo "  ✅ Memory: OK"
fi

# ─── Step 9: Rollback instructions ───
echo ""
echo "[9/9] Rollback instructions / دستورالعمل بازگشت:"
cat << 'ROLLBACK'
  If something goes wrong / اگر مشکلی پیش آمد:
    sudo systemctl stop sentinel.timer sentinel.service
    sudo systemctl disable sentinel.timer
    sudo rm /etc/systemd/system/sentinel.*
    sudo systemctl daemon-reload
    # Then re-run deploy.sh with the previous version
ROLLBACK

echo ""
echo "======================================================"
echo "  ✅ Deployment complete! / استقرار کامل شد!"
echo "======================================================"
echo ""
echo "Useful commands / دستورات مفید:"
echo "  Status:         systemctl status sentinel.timer"
echo "  Live log:       journalctl -u sentinel.service -f"
echo "  Manual run:     sudo -u ${SENTINEL_USER} bash -c 'cd ${SENTINEL_DIR} && ${VENV_DIR}/bin/python3 main.py --once'"
echo "  Disable:        sudo systemctl stop sentinel.timer && sudo systemctl disable sentinel.timer"
echo ""
if ! $DRY_RUN; then
    echo "  👉  Next: watch the first real Telegram signal arrive."
    echo "  👉  بعدی: منتظر اولین سیگنال واقعی تلگرام بمان."
fi
