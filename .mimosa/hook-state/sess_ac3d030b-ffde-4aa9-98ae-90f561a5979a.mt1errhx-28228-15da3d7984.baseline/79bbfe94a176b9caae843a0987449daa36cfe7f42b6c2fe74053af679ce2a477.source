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
echo "=============================================="
echo " Operation Piggy Bank 2026 - Hardening"
echo " Target board: Node ${NODE_NUM}"
echo "=============================================="
AUTH_KEYS_FILE="${HOME}/.ssh/authorized_keys"
if [[ ! -f "$AUTH_KEYS_FILE" ]]; then
    echo "[ERROR] ${AUTH_KEYS_FILE} does not exist." >&2; exit 1
fi
KEY_COUNT=$(grep -c 'ssh-' "$AUTH_KEYS_FILE" 2>/dev/null || true)
[[ "$KEY_COUNT" -lt 1 ]] && { echo "[ERROR] No SSH keys found." >&2; exit 1; }
echo "[PRE-FLIGHT] OK - Found ${KEY_COUNT} authorized key(s)."
echo "[STEP 1] Updating packages..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq ufw fail2ban curl wget jq unattended-upgrades
echo "[STEP 2] Hardening SSH..."
SSHD_CONFIG="/etc/ssh/sshd_config"
cp "${SSHD_CONFIG}" "${SSHD_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"
apply_sshd_setting() {
    local key="$1" value="$2"
    if grep -qE "^#?${key}" "$SSHD_CONFIG"; then
        sed -i "s|^#\?${key}.*|${key} ${value}|g" "$SSHD_CONFIG"
    else
        echo "${key} ${value}" >> "$SSHD_CONFIG"
    fi
}
apply_sshd_setting "Port"                   "${SSH_PORT}"
apply_sshd_setting "PermitRootLogin"        "prohibit-password"
apply_sshd_setting "PasswordAuthentication" "no"
apply_sshd_setting "PubkeyAuthentication"   "yes"
apply_sshd_setting "X11Forwarding"          "no"
apply_sshd_setting "MaxAuthTries"           "3"
apply_sshd_setting "LoginGraceTime"         "30"
apply_sshd_setting "ClientAliveInterval"    "300"
apply_sshd_setting "ClientAliveCountMax"    "2"
sshd -t || { echo "[ERROR] sshd config failed. Restoring..." >&2; exit 1; }
systemctl restart sshd
echo "[STEP 2] SSH hardened."
if [[ "$ENABLE_UFW" == "true" ]]; then
    echo "[STEP 3] Configuring UFW..."
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow from "${ALLOW_SSH_FROM}" to any port "${SSH_PORT}" proto tcp comment "SSH"
    ufw allow "${FULLNODE_P2P_PORT}/tcp" comment "Hacash P2P"
    ufw allow "${FULLNODE_API_PORT}/tcp" comment "Hacash API"
    ufw --force enable
    echo "[STEP 3] UFW configured."
fi
echo "[STEP 4] Configuring fail2ban..."
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5
[sshd]
enabled  = true
port     = ${SSH_PORT}
maxretry = 3
EOF
systemctl enable fail2ban --quiet
systemctl restart fail2ban
echo "[STEP 5] System optimizations..."
cat > /etc/security/limits.d/99-hacash.conf <<EOF
root soft nofile 65535
root hard nofile 65535
* soft nofile 65535
* hard nofile 65535
EOF
cat > /etc/sysctl.d/99-hacash.conf <<EOF
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.somaxconn = 1024
vm.swappiness = 10
EOF
sysctl --system -q
echo "[STEP 6] Creating directories..."
mkdir -p "${INSTALL_DIR}" "${DATA_DIR}" "${LOG_DIR}"
chmod 750 "${INSTALL_DIR}"
NEW_HOSTNAME="piggybank-node${NODE_NUM}"
hostnamectl set-hostname "${NEW_HOSTNAME}"
echo "127.0.1.1  ${NEW_HOSTNAME}" >> /etc/hosts
echo ""
echo "=============================================="
echo " Hardening complete - Node ${NODE_NUM}"
echo " Hostname: ${NEW_HOSTNAME}"
echo "=============================================="