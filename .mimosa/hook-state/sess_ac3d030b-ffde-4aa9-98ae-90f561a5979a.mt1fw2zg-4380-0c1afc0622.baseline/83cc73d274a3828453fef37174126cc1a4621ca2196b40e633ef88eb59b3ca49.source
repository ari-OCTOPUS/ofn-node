#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.env"
[[ $EUID -ne 0 ]] && { echo "[ERROR] Run as root." >&2; exit 1; }
echo "=============================================="
echo " Operation Piggy Bank 2026 - Full Node Setup"
echo "=============================================="
echo "[STEP 1] Downloading fullnode ${HACASH_VERSION}..."
DOWNLOAD_URL="${GITHUB_RELEASE_BASE}/${FULLNODE_BINARY}"
DEST_BIN="${INSTALL_DIR}/hacash_fullnode"
curl -fsSL --retry 3 --retry-delay 5 -o "${DEST_BIN}" "${DOWNLOAD_URL}" || {
    echo "[ERROR] Download failed. Check: https://github.com/hacash/fullnode/releases" >&2; exit 1
}
chmod +x "${DEST_BIN}"
echo "[STEP 2] Writing hacash.config.ini..."
cat > "${CONFIG_INI}" <<EOF
[node]
data_dir = ${DATA_DIR}
listen_port = ${FULLNODE_P2P_PORT}
boot_nodes = 182.92.163.225:3337,47.244.26.14:3337
[server]
listen_port = ${FULLNODE_API_PORT}
[miner]
enable = true
reward = ${HAC_REWARD_ADDRESS}
EOF
echo "[STEP 3] Creating systemd service..."
cat > "/etc/systemd/system/${SYSTEMD_FULLNODE_UNIT}.service" <<EOF
[Unit]
Description=Hacash Full Node - Operation Piggy Bank 2026
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${DEST_BIN} ${CONFIG_INI}
Restart=always
RestartSec=10
StartLimitBurst=0
StandardOutput=append:${LOG_DIR}/fullnode.log
StandardError=append:${LOG_DIR}/fullnode.err
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable "${SYSTEMD_FULLNODE_UNIT}" --quiet
systemctl start  "${SYSTEMD_FULLNODE_UNIT}"
sleep 3
systemctl is-active --quiet "${SYSTEMD_FULLNODE_UNIT}" && \
    echo "[OK] ${SYSTEMD_FULLNODE_UNIT} is running." || \
    echo "[WARNING] Service may not have started. Check: journalctl -u ${SYSTEMD_FULLNODE_UNIT} -n 20"
echo ""
echo "=============================================="
echo " Full Node setup complete!"
echo " API port: ${FULLNODE_API_PORT} | P2P: ${FULLNODE_P2P_PORT}"
echo " Logs: ${LOG_DIR}/fullnode.log"
echo "=============================================="