#!/bin/bash
# OCTOPUS money-state mirror push (node 138 -> witness 182). Runs as ari on 138.
# Push-based, append-only. Receiver verifies signed manifest; receipts limited to RECEIVED+HASH-MATCH.
set -euo pipefail

M=/home/ari/octopus-mirror
SRC=/home/ari/ofn/state
DEST_HOST=192.168.0.182
DEST_USER=mirror138

STAGE=$(mktemp -d "$M/staging/push-XXXXXX")
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/payload/api-budget/config" "$STAGE/payload/revenue-drive" "$M/logs" "$M/staging"

cp -p "$SRC/api-budget/budget-ledger.jsonl" "$STAGE/payload/api-budget/" 2>/dev/null || true
cp -p "$SRC/api-budget/config/"*.json "$STAGE/payload/api-budget/config/" 2>/dev/null || true
cp -p "$SRC/api-budget/config/"*.jsonl "$STAGE/payload/api-budget/config/" 2>/dev/null || true
cp -p "$SRC/revenue-drive/season-meter.json" "$STAGE/payload/revenue-drive/" 2>/dev/null || true

( cd "$STAGE/payload" && find . -type f -printf '%P\n' | LC_ALL=C sort | while IFS= read -r f; do
    printf '%s  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$f"
  done ) > "$STAGE/manifest.sha256"

[ -s "$STAGE/manifest.sha256" ] || { echo "PUSH_FAILED: empty manifest"; exit 1; }

ssh-keygen -Y sign -q -f "$M/mirror-sign" -n octopus-mirror-manifest "$STAGE/manifest.sha256"

OUT=$(ssh -i "$M/mirror-push" \
        -o UserKnownHostsFile="$M/known_hosts" \
        -o BatchMode=yes -o StrictHostKeyChecking=yes \
        -o ConnectTimeout=15 \
        "$DEST_USER@$DEST_HOST" < <(tar -C "$STAGE" -cf - payload manifest.sha256 manifest.sha256.sig))

TS=$(date -u +%Y%m%dT%H%M%SZ)
printf '%s\n' "$OUT" | tee "$M/logs/push-$TS.json"
if grep -q '"RECEIVED+HASH-MATCH"' <<<"$OUT"; then
    echo "PUSH_OK $TS"
else
    echo "PUSH_FAILED $TS"
    exit 1
fi
