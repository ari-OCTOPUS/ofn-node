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
[[ -z "$NODE_NUM" ]] && { echo "[ERROR] --node required" >&2; exit 1; }
[[ $EUID -ne 0 ]] && { echo "[ERROR] Run as root" >&2; exit 1; }
ROLE_VAR="NODE_${NODE_NUM}_ROLE"
ROLE="${!ROLE_VAR:-miner}"
[[ "$ROLE" == "fullnode" ]] && PRIMARY_UNIT="${SYSTEMD_FULLNODE_UNIT}" || PRIMARY_UNIT="${SYSTEMD_MINER_UNIT}"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}[v]${NC} $*"; }
fail() { echo -e "  ${RED}[x]${NC} $*"; CHECKS_FAILED=$((CHECKS_FAILED+1)); }
warn() { echo -e "  ${YELLOW}[!]${NC} $*"; }
CHECKS_FAILED=0
echo ""
echo "================================================"
echo " Operation Piggy Bank 2026 - Auto-Start Setup"
echo " Node ${NODE_NUM} | Role: ${ROLE}"
echo "================================================"
echo ""
echo "[STEP 1] Systemd service auto-start"
if systemctl is-enabled --quiet "${PRIMARY_UNIT}" 2>/dev/null; then
    ok "${PRIMARY_UNIT} is enabled"
else
    warn "Enabling ${PRIMARY_UNIT}..."
    systemctl enable "${PRIMARY_UNIT}" --quiet
    ok "${PRIMARY_UNIT} enabled."
fi
if systemctl is-active --quiet "${PRIMARY_UNIT}" 2>/dev/null; then
    ok "${PRIMARY_UNIT} is running"
else
    warn "Starting ${PRIMARY_UNIT}..."
    systemctl start "${PRIMARY_UNIT}"
    sleep 3
    systemctl is-active --quiet "${PRIMARY_UNIT}" && ok "Started." || fail "Failed to start."
fi
echo ""
echo "[STEP 2] Log rotation"
cat > /etc/logrotate.d/hacash-piggybank <<EOF
/opt/hacash/logs/*.log /opt/hacash/logs/*.err {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
ok "logrotate configured (7 days)"
echo ""
FINAL_ENABLED=$(systemctl is-enabled "${PRIMARY_UNIT}" 2>/dev/null || echo "disabled")
FINAL_ACTIVE=$(systemctl is-active  "${PRIMARY_UNIT}" 2>/dev/null || echo "inactive")
echo "================================================"
echo " Boot Guarantee Checklist - Node ${NODE_NUM}"
echo "================================================"
echo "  Service : ${PRIMARY_UNIT}"
echo "  Enabled : ${FINAL_ENABLED}"
echo "  Status  : ${FINAL_ACTIVE}"
echo "  Restart : always (no limit)"
echo ""
if [[ $CHECKS_FAILED -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}[OK] This board will auto-start on every boot.${NC}"
else
    echo -e "  ${RED}${BOLD}[FAIL] ${CHECKS_FAILED} check(s) failed - review above.${NC}"
fi
echo ""