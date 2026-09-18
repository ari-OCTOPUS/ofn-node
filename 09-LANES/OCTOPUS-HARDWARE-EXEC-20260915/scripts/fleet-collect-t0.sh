#!/bin/bash
# fleet-collect-t0.sh — orchestrate inventory-v2 across mesh from 138
set -u
KEY="${HOME}/.ssh/octopus_mesh_ed25519"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INV="${SCRIPT_DIR}/fleet-inventory-v2.sh"
AGG="${SCRIPT_DIR}/fleet-t0-aggregate.py"
OUTDIR="${1:-/tmp/t0-receipts}"
mkdir -p "$OUTDIR"
NODES=(138 180 182 100 160 193 114)

echo "T0_START $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "$OUTDIR/collect.log"
for ip in "${NODES[@]}"; do
  echo "=== node $ip ===" | tee -a "$OUTDIR/collect.log"
  raw="$OUTDIR/raw-$ip.txt"
  ec=0
  if [ "$ip" = "138" ]; then
    if sudo -n true 2>/dev/null; then
      sudo -n bash "$INV" >"$raw" 2>"$OUTDIR/raw-$ip.err" || ec=$?
    else
      bash "$INV" >"$raw" 2>"$OUTDIR/raw-$ip.err" || ec=$?
    fi
  else
    ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=12 -o StrictHostKeyChecking=no \
      root@192.168.0."$ip" "bash -s" <"$INV" >"$raw" 2>"$OUTDIR/raw-$ip.err" || ec=$?
  fi
  echo "SSH_OR_LOCAL_EXIT=$ec" >>"$raw"
  echo "node=$ip exit=$ec" | tee -a "$OUTDIR/collect.log"
done

python3 "$AGG" "$OUTDIR" | tee -a "$OUTDIR/collect.log"
cp -f "$OUTDIR/fleet-inventory-t0.json" /home/ari/fleet-inventory-t0.json 2>/dev/null || true
# bak old inventory script; install v2 alongside (do not silently overwrite until hashed)
if [ -f /home/ari/fleet-inventory.sh ] && [ ! -f /home/ari/fleet-inventory.sh.pre-t0-20260915 ]; then
  cp -f /home/ari/fleet-inventory.sh /home/ari/fleet-inventory.sh.pre-t0-20260915
fi
cp -f "$INV" /home/ari/fleet-inventory-v2.sh
cp -f "$AGG" /home/ari/fleet-t0-aggregate.py
cp -f "$SCRIPT_DIR/fleet-collect-t0.sh" /home/ari/fleet-collect-t0.sh
chmod +x /home/ari/fleet-inventory-v2.sh /home/ari/fleet-collect-t0.sh
echo "T0_END $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$OUTDIR/collect.log"
