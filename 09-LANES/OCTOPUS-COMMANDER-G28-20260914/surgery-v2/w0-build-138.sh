#!/bin/bash
# W0 bundle builder (138) — explicit allowlist only. No secrets, no state
# ledgers, no model binaries. Manifest computed ON THE HOST before tarring.
set -euo pipefail
OUT=$(mktemp -d /tmp/w0build-138-XXXX)
ROOT="$OUT/root"
FILES=(
  /home/ari/ofn/state/ops-agent/ops_agent.py
  /home/ari/ofn/state/coding-worker/coding_worker.py
  /home/ari/ofn/state/api-budget/api_budget.py
  /home/ari/ofn/state/api-budget/providers.py
  /home/ari/ofn/ofn/agents/glass_runner.py
  /home/ari/ofn/ofn/agents/go_b3_owner_bind.py
  /home/ari/ofn/state/revenue-drive/owner_reply.py
  /home/ari/ofn/ofn/agents/owner_notify.py
  /home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py
  /home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py
  /home/ari/ofn/state/coding-worker/stage/TASK-W24-BINDER-SPOOL-006/go_b3_owner_bind.py
  /home/ari/ofn/state/coding-worker/stage/G30-STAGE-GUARD-WIRING-001/coding_worker.py
  /home/ari/ofn/state/ops-agent/state/canary-requests/native-A2-G8-PRODUCER-010.json
  /home/ari/ofn/state/ops-agent/state/canary-requests/native-A3-W24-BINDER-006.json
  /home/ari/ofn/state/ops-agent/state/canary-requests/native-G30-STAGE-GUARD-WIRING-001.json
  /home/ari/ofn/state/ops-agent/state/canary-requests/native-Z-SUCCESSOR-TRIO-001.json
  /home/ari/ofn/state/ops-agent/state/dep-evidence/B8-CAPABILITY-20260914.json
  /home/ari/ofn/state/ops-agent/ops_contracts.json
  /home/ari/ofn/state/ops-agent/ops_budgets.json
  /home/ari/ofn/state/owner_dialogue/go_b3_pending_registry.json
  /home/ari/ofn/state/owner_dialogue/hold_external_sot.v1.json
)
UNITS=(
  octopus-ops-agent.service octopus-ops-agent.timer
  octopus-glass.service octopus-glass.timer
  octopus-go-b3-bind.service octopus-go-b3-bind.timer
  ofn.service
)
mkdir -p "$ROOT"
MAN="$OUT/manifest-pre.json"
echo "{" > "$MAN"
echo '  "host": "138", "observed_at_utc": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "files": [' >> "$MAN"
first=1
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "MISSING $f" >&2; exit 9; }
  mkdir -p "$ROOT$(dirname "$f")"
  cp -p "$f" "$ROOT$f"
  h=$(sha256sum "$f" | cut -d" " -f1)
  s=$(stat -c%s "$f"); m=$(stat -c%a "$f"); t=$(stat -c%y "$f" | cut -d. -f1)
  [ $first -eq 1 ] && first=0 || echo "," >> "$MAN"
  printf '    {"path": "%s", "sha256": "%s", "size": %s, "mode": "%s", "mtime_local": "%s"}' \
    "$f" "$h" "$s" "$m" "$t" >> "$MAN"
done
mkdir -p "$ROOT/etc/systemd/system"
for u in "${UNITS[@]}"; do
  src=/etc/systemd/system/$u
  [ -f "$src" ] || src=$(systemctl show -p FragmentPath $u 2>/dev/null | cut -d= -f2)
  [ -f "$src" ] || { echo "MISSING unit $u" >&2; exit 9; }
  cp -p "$src" "$ROOT/etc/systemd/system/$u"
  h=$(sha256sum "$src" | cut -d" " -f1); s=$(stat -c%s "$src")
  echo "," >> "$MAN"
  printf '    {"path": "/etc/systemd/system/%s", "sha256": "%s", "size": %s, "mode": "644", "mtime_local": "unit-file"}' \
    "$u" "$h" "$s" >> "$MAN"
done
echo "" >> "$MAN"
echo '  ],' >> "$MAN"
echo '  "python3": "'$(python3 --version 2>&1)'", "os": "'$(grep PRETTY_NAME /etc/os-release | cut -d\" -f2)'"' >> "$MAN"
echo "}" >> "$MAN"
tar -C "$OUT" -czf /tmp/w0-138.tar.gz root manifest-pre.json
cp "$MAN" /tmp/w0-138-manifest-pre.json
echo "BUNDLE OK files=$((${#FILES[@]} + ${#UNITS[@]})) sha=$(sha256sum /tmp/w0-138.tar.gz | cut -c1-16)"
