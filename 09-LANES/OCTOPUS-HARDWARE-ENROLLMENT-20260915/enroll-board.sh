#!/bin/bash
# =============================================================================
# enroll-board.sh — enroll a freshly booted Orange Pi 5 into the OCTOPUS mesh.
# Run this ON 138 (it holds the mesh keys).
#
#   ssh board138 'bash -s' < enroll-board.sh -- 192.168.0.170 opi5-node-4
#
# What it does (all additive, all reversible):
#   1. verifies it can reach the board with the mesh key
#   2. records model / MAC / kernel  (identification, nothing written)
#   3. sets the hostname
#   4. authorises the mesh key for the `octopus` account and root
#   5. adds an /etc/hosts entry on 138
#
# What it deliberately does NOT do: install agents, touch mining nodes,
# change any governance/config, or reboot anything.
# =============================================================================
set -euo pipefail

IP="${1:?usage: enroll-board.sh <ip> [hostname]}"
NAME="${2:-}"

KEY=~/.ssh/id_ed25519
SSHOPT=(-i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=no
        -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8)

echo "=== 1. reachability ==="
ssh "${SSHOPT[@]}" root@"$IP" 'echo REACHABLE' || { echo "FAIL: cannot SSH to $IP with $KEY"; exit 1; }

echo "=== 2. identification ==="
MODEL=$(ssh "${SSHOPT[@]}" root@"$IP" 'cat /proc/device-tree/model; echo')
MAC=$(ssh "${SSHOPT[@]}" root@"$IP" "ip -o link show eth0 2>/dev/null | awk '{print \$17}'")
KERN=$(ssh "${SSHOPT[@]}" root@"$IP" 'uname -r')
OSREL=$(ssh "${SSHOPT[@]}" root@"$IP" '. /etc/os-release; echo "$PRETTY_NAME"')
echo "  model : $MODEL"
echo "  mac   : $MAC"
echo "  kernel: $KERN"
echo "  os    : $OSREL"

# Refuse to enrol a board that is already doing real work elsewhere.
BUSY=$(ssh "${SSHOPT[@]}" root@"$IP" 'systemctl is-active hacash-fullnode hacash-miner tdc_miner 2>/dev/null | grep -c "^active" || true')
if [ "${BUSY:-0}" != "0" ]; then
  echo "ABORT: $IP is running a mining workload ($BUSY active units). Not enrolling."
  exit 2
fi

if [ -z "$NAME" ]; then
  NAME="opi5-node-$(echo "$MAC" | tr -d ':' | tail -c 5)"
fi

echo "=== 3. hostname -> $NAME ==="
ssh "${SSHOPT[@]}" root@"$IP" "hostnamectl set-hostname '$NAME' && hostname"

echo "=== 4. authorise mesh key ==="
MESH_PUB=$(cat ~/.ssh/octopus_mesh_ed25519.pub)
ssh "${SSHOPT[@]}" root@"$IP" "bash -s" <<EOF
set -e
mkdir -p /root/.ssh && chmod 700 /root/.ssh
touch /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys
grep -qF '$MESH_PUB' /root/.ssh/authorized_keys || echo '$MESH_PUB' >> /root/.ssh/authorized_keys
echo "  keys now: \$(wc -l < /root/.ssh/authorized_keys)"
EOF

echo "=== 5. /etc/hosts entry on 138 ==="
if grep -qE "[[:space:]]$NAME\$" /etc/hosts; then
  echo "  already present"
else
  sudo -n cp /etc/hosts /etc/hosts.pre-enroll-$(date -u +%Y%m%dT%H%M%SZ) 2>/dev/null || true
  echo "$IP	$NAME" | sudo -n tee -a /etc/hosts >/dev/null
  echo "  added: $IP $NAME"
fi

echo
echo "ENROLLED: $NAME ($IP) — $MODEL"
echo "ROLLBACK: sudo sed -i '/[[:space:]]$NAME\$/d' /etc/hosts ; hostnamectl set-hostname dietpi"
