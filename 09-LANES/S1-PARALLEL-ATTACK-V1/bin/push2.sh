#!/bin/bash
# OCTOPUS money-state mirror push v2 (node 138 -> witness 182). Runs as ari on 138.
# S1-PARALLEL-ATTACK-V1 lane L-A. Push-based, append-only, monotonic sequence.
# Sender ledger: state/sender-ledger.json (advanced ONLY after receiver accepts).
set -euo pipefail

M=/home/ari/octopus-mirror
SRC=/home/ari/ofn/state
DEST_HOST=192.168.0.182
DEST_USER=mirror138
LEDGER="$M/state/sender-ledger.json"

STAGE=$(mktemp -d "$M/staging/push2-XXXXXX")
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/payload/api-budget/config" "$STAGE/payload/revenue-drive" "$M/logs" "$M/staging" "$M/state"

cp -p "$SRC/api-budget/budget-ledger.jsonl" "$STAGE/payload/api-budget/" 2>/dev/null || true
cp -p "$SRC/api-budget/config/"*.json "$STAGE/payload/api-budget/config/" 2>/dev/null || true
cp -p "$SRC/api-budget/config/"*.jsonl "$STAGE/payload/api-budget/config/" 2>/dev/null || true
cp -p "$SRC/revenue-drive/season-meter.json" "$STAGE/payload/revenue-drive/" 2>/dev/null || true

SEQ_JSON=$(python3 - "$STAGE" "$LEDGER" <<'PY'
import hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

stage, ledger_path = sys.argv[1], sys.argv[2]
payload = Path(stage) / "payload"

POLICY_SPEC_JSON = (
    '{"allow":["api-budget/budget-ledger.jsonl","api-budget/config/<name>.json",'
    '"api-budget/config/<name>.jsonl","revenue-drive/season-meter.json"],'
    '"max_age_seconds":172800,"max_file_bytes":52428800,"max_files":64,'
    '"max_future_skew_seconds":900,"max_total_bytes":209715200,'
    '"mirror_id":"S1-MONEY-138-182","namespace":"octopus-mirror-manifest",'
    '"policy_version":"mirror-policy-v2-20260917","quarantine_cap_entries":100,'
    '"receipt_policy":"RECEIVED+HASH-MATCH ONLY; REPLAY-VALID NOT CLAIMED (S1-GAP-02C)",'
    '"replay_bridge":"FORBIDDEN"}'
)

ledger = {"epoch": 1, "sequence": 0, "last_manifest_sha256": "GENESIS"}
if os.path.isfile(ledger_path):
    with open(ledger_path, encoding="utf-8") as fh:
        ledger = json.load(fh)

files = []
for p in sorted(payload.rglob("*")):
    if p.is_file():
        data = p.read_bytes()
        files.append({"path": str(p.relative_to(payload)), "sha256": hashlib.sha256(data).hexdigest(),
                      "bytes": len(data)})
if not files:
    print(json.dumps({"error": "empty payload"}))
    sys.exit(1)

canonical = "".join("{} {}\n".format(f["path"], f["sha256"])
                    for f in sorted(files, key=lambda x: x["path"]))
manifest = {
    "schema": "octopus-mirror-manifest.v1",
    "mirror_id": "S1-MONEY-138-182",
    "namespace": "octopus-mirror-manifest",
    "epoch": int(ledger["epoch"]),
    "sequence": int(ledger["sequence"]) + 1,
    "prev_manifest_sha256": ledger["last_manifest_sha256"],
    "sent_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "sender": "node-138",
    "receiver": "node-182-witness",
    "scope_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    "files_count": len(files),
    "policy_version": "mirror-policy-v2-20260917",
    "policy_sha256": hashlib.sha256(POLICY_SPEC_JSON.encode()).hexdigest(),
    "files": files,
}
with open(Path(stage) / "manifest.json", "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2)
    fh.write("\n")
print(json.dumps({"epoch": manifest["epoch"], "sequence": manifest["sequence"]}))
PY
)

echo "$SEQ_JSON" | grep -q '"sequence"' || { echo "PUSH_FAILED: manifest build failed: $SEQ_JSON"; exit 1; }

ssh-keygen -Y sign -q -f "$M/mirror-sign" -n octopus-mirror-manifest "$STAGE/manifest.json"

OUT=$(ssh -i "$M/mirror-push" \
        -o UserKnownHostsFile="$M/known_hosts" \
        -o BatchMode=yes -o StrictHostKeyChecking=yes \
        -o ConnectTimeout=15 \
        "$DEST_USER@$DEST_HOST" < <(tar -C "$STAGE" -cf - payload manifest.json manifest.json.sig))

TS=$(date -u +%Y%m%dT%H%M%SZ)
printf '%s\n' "$OUT" | tee "$M/logs/push-$TS.json"
if grep -q '"RECEIVED+HASH-MATCH"' <<<"$OUT"; then
    printf '%s' "$OUT" > "$STAGE/receipt.json"
    python3 - "$LEDGER" "$STAGE/receipt.json" <<'PY'
import json, os, sys
ledger_path, receipt_path = sys.argv[1], sys.argv[2]
with open(receipt_path, encoding="utf-8") as fh:
    r = json.load(fh)
ledger = {"epoch": 1, "sequence": 0, "last_manifest_sha256": "GENESIS"}
if os.path.isfile(ledger_path):
    with open(ledger_path, encoding="utf-8") as fh:
        ledger = json.load(fh)
# advance ONLY on a receiver-accepted receipt that chains onto our ledger
if (r.get("status") == "RECEIVED+HASH-MATCH"
        and r.get("epoch") == ledger.get("epoch")
        and r.get("sequence") == ledger.get("sequence", 0) + 1):
    ledger = {"epoch": r["epoch"], "sequence": r["sequence"],
              "last_manifest_sha256": r["manifest_sha256"],
              "accepted_at_utc": r.get("received_at_utc")}
    tmp = ledger_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)
        fh.write("\n")
        fh.flush()
    os.replace(tmp, ledger_path)
PY
    echo "PUSH_OK $TS $SEQ_JSON"
else
    echo "PUSH_FAILED $TS"
    exit 1
fi
