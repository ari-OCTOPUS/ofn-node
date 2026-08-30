#!/usr/bin/env bash
# =============================================================================
# 03_monitor.sh — Operation Piggy Bank 2026
# Purpose : Quick health-check and hashrate view across all active nodes
# Run on  : Control machine (your laptop)
# Usage   : bash 03_monitor.sh [--watch] [--nodes 1 2 3 4]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.env"

WATCH_MODE=false
MONITOR_NODES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --watch) WATCH_MODE=true; shift ;;
        --nodes) shift
            while [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; do
                MONITOR_NODES+=("$1"); shift
            done ;;
        *) shift ;;
    esac
done

if [[ ${#MONITOR_NODES[@]} -eq 0 ]]; then
    read -ra MONITOR_NODES <<< "$ACTIVE_NODES"
fi

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

remote_exec() {
    local node="$1"; shift
    local ip_var="NODE_${node}_IP"
    local ip="${!ip_var}"
    ssh -i "${SSH_KEY_PATH}" -o BatchMode=yes -o ConnectTimeout=8 \
        -p "${SSH_PORT}" "${SSH_USER}@${ip}" "$@" 2>/dev/null || echo "SSH_FAIL"
}

check_node() {
    local node="$1"
    local ip_var="NODE_${node}_IP"
    local ip="${!ip_var}"
    local role_var="NODE_${node}_ROLE"
    local role="${!role_var:-miner}"

    echo -e "${BOLD}--- Node ${node} (${ip}) [${role}] ---${NC}"

    # Uptime
    local uptime
    uptime=$(remote_exec "$node" "uptime -p")
    echo "  Uptime   : ${uptime}"

    # CPU temp (Orange Pi 5 thermal)
    local temp
    temp=$(remote_exec "$node" "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1f°C\", \$1/1000}' || echo 'N/A'")
    echo "  CPU Temp : ${temp}"

    # Service status
    if [[ "$role" == "fullnode" ]]; then
        local unit="${SYSTEMD_FULLNODE_UNIT}"
        local logfile="${LOG_DIR}/fullnode.log"
    else
        local unit="${SYSTEMD_MINER_UNIT}"
        local logfile="${LOG_DIR}/miner.log"
    fi

    local svc_status
    svc_status=$(remote_exec "$node" "systemctl is-active ${unit} 2>/dev/null || echo 'inactive'")
    if [[ "$svc_status" == "active" ]]; then
        echo -e "  Service  : ${GREEN}${svc_status}${NC}"
    else
        echo -e "  Service  : ${RED}${svc_status}${NC}"
    fi

    # Last log lines (hashrate / mining success)
    echo "  Last log :"
    remote_exec "$node" "tail -5 ${logfile} 2>/dev/null || echo '  (no log yet)'" | \
        sed 's/^/    /'
    echo ""
}

run_check() {
    clear
    echo -e "${BOLD}========================================"
    echo " Operation Piggy Bank 2026 — Monitor"
    echo " $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo -e "========================================${NC}"
    echo ""
    for n in "${MONITOR_NODES[@]}"; do
        check_node "$n"
    done
    echo "Fullnode API check (block height):"
    local height
    height=$(curl -sf --max-time 5 \
        "http://${NODE_1_IP}:${FULLNODE_API_PORT}/query/latest/block" \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print('Block:', d.get('height','?'))" \
        2>/dev/null || echo "API not responding yet")
    echo "  ${height}"
}

if [[ "$WATCH_MODE" == "true" ]]; then
    while true; do
        run_check
        echo ""
        echo "(Refreshing every 30s — Ctrl+C to stop)"
        sleep 30
    done
else
    run_check
fi
