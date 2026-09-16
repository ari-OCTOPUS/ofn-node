#!/bin/bash
# W0 bundle builder (180) — explicit allowlist only (units, scripts, model
# hash pins). No secrets, no model binary, no lab data.
set -euo pipefail
OUT=$(mktemp -d /tmp/w0build-180-XXXX)
ROOT="$OUT/root"
UNITS=(octopus-llama-lab.service octopus-organism-lab.service
       octopus-gateway.service octopus-afferent-lab.service
       octopus-soak-lab.service)
FILES=(
  /opt/octopus/runtime/model.sha256
  /opt/octopus/lab/bin/start-organism.sh
)
mkdir -p "$ROOT/etc/systemd/system" "$ROOT/opt/octopus/runtime" "$ROOT/opt/octopus/lab/bin"
MAN="$OUT/manifest-pre.json"
echo "{" > "$MAN"
echo '  "host": "180", "observed_at_utc": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "files": [' >> "$MAN"
first=1
for u in "${UNITS[@]}"; do
  src=/etc/systemd/system/$u
  [ -f "$src" ] || { echo "MISSING unit $u" >&2; exit 9; }
  cp -p "$src" "$ROOT/etc/systemd/system/$u"
  h=$(sha256sum "$src" | cut -d" " -f1); s=$(stat -c%s "$src")
  [ $first -eq 1 ] && first=0 || echo "," >> "$MAN"
  printf '    {"path": "/etc/systemd/system/%s", "sha256": "%s", "size": %s, "mode": "644"}' "$u" "$h" "$s" >> "$MAN"
done
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "MISSING $f" >&2; exit 9; }
  cp -p "$f" "$ROOT$f"
  h=$(sha256sum "$f" | cut -d" " -f1); s=$(stat -c%s "$f"); m=$(stat -c%a "$f")
  echo "," >> "$MAN"
  printf '    {"path": "%s", "sha256": "%s", "size": %s, "mode": "%s"}' "$f" "$h" "$s" "$m" >> "$MAN"
done
# model binary: hash-pin only (too big for the code bundle; restore dependency)
MH=$(sha256sum /opt/octopus/models/qwen3-0.6b-q4_0.gguf | cut -d" " -f1)
echo "," >> "$MAN"
printf '    {"path": "/opt/octopus/models/qwen3-0.6b-q4_0.gguf", "sha256": "%s", "size": %s, "mode": "644", "note": "hash-pin only; binary is a RESTORE_DEPENDENCY (from owner-approved source), not bundled"}' \
  "$MH" "$(stat -c%s /opt/octopus/models/qwen3-0.6b-q4_0.gguf)" >> "$MAN"
# the llama runner script referenced by ExecStart
RS=$(systemctl cat octopus-llama-lab.service 2>/dev/null | grep ^ExecStart= | awk "{print \$1}" | cut -d= -f2)
[ -f "$RS" ] && { mkdir -p "$ROOT$(dirname "$RS")"; cp -p "$RS" "$ROOT$RS";
  h=$(sha256sum "$RS" | cut -d" " -f1); s=$(stat -c%s "$RS");
  echo "," >> "$MAN"; printf '    {"path": "%s", "sha256": "%s", "size": %s, "mode": "755"}' "$RS" "$h" "$s" >> "$MAN"; }
echo "" >> "$MAN"
echo '  ],' >> "$MAN"
echo '  "python3": "'$(python3 --version 2>&1)'", "os": "'$(grep PRETTY_NAME /etc/os-release | cut -d\" -f2)'"' >> "$MAN"
echo "}" >> "$MAN"
tar -C "$OUT" -czf /tmp/w0-180.tar.gz root manifest-pre.json
cp "$MAN" /tmp/w0-180-manifest-pre.json
echo "BUNDLE OK sha=$(sha256sum /tmp/w0-180.tar.gz | cut -c1-16)"
