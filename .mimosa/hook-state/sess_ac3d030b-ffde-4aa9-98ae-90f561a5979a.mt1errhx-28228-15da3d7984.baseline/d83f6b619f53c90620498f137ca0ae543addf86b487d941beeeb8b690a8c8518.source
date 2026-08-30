#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.env"
NODE_NUM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --node) NODE_NUM="$2"; shift 2 ;;
        *) echo "[ERROR] Unknown argument: $1" >&2; exit 1 ;;
    esac
done
[[ -z "$NODE_NUM" ]] && { echo "[ERROR] --node required." >&2; exit 1; }
[[ $EUID -ne 0 ]] && { echo "[ERROR] Run as root." >&2; exit 1; }
echo "=============================================="
echo " Operation Piggy Bank 2026 - Miner Setup"
echo " Node ${NODE_NUM} | Fullnode: ${NODE_1_IP}:${FULLNODE_API_PORT}"
echo "=============================================="
echo "[STEP 1] Downloading poworker ${HACASH_VERSION}..."
DOWNLOAD_URL="${GITHUB_RELEASE_BASE}/${POWORKER_BINARY}"
DEST_BIN="${INSTALL_DIR}/hacash_poworker"
curl -fsSL --retry 3 --retry-delay 5 -o "${DEST_BIN}" "${DOWNLOAD_URL}" || {
    echo "[ERROR] Download failed." >&2; exit 1
}
chmod +x "${DEST_BIN}"
echo "[STEP 2] Writing poworker.config.ini..."
cat > "${POWORKER_INI}" <<EOF
[config]
connect = ${NODE_1_IP}:${FULLNODE_API_PORT}
supervene = ${MINER_THREADS}
EOF
echo "[STEP 3] Creating systemd service..."
cat > "/etc/systemd/system/${SYSTEMD_MINER_UNIT}.service" <<EOF
[Unit]
Description=Hacash Miner (poworker) - Node ${NODE_NUM}
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${DEST_BIN} ${POWORKER_INI}
Restart=always
RestartSec=15
StartLimitBurst=0
StandardOutput=append:${LOG_DIR}/miner.log
StandardError=append:${LOG_DIR}/miner.err
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable "${SYSTEMD_MINER_UNIT}" --quiet
systemctl start  "${SYSTEMD_MINER_UNIT}"
sleep 3
systemctl is-active --quiet "${SYSTEMD_MINER_UNIT}" && \
    echo "[OK] ${SYSTEMD_MINER_UNIT} is running on Node ${NODE_NUM}." || \
    echo "[WARNING] Check: journalctl -u ${SYSTEMD_MINER_UNIT} -n 20"
echo ""
echo "=============================================="
echo " Miner setup complete - Node ${NODE_NUM}"
echo " Threads: ${MINER_THREADS} | Fullnode: ${NODE_1_IP}:${FULLNODE_API_PORT}"
echo " Logs: ${LOG_DIR}/miner.log"
echo "=============================================="