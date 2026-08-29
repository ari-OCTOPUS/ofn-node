#!/bin/bash
# OPTIONAL observation-only autoheal: restart sensorium if live bus=ISOLATED.
# Never ARM/PWM. Rate-limited. Read snapshots only.
set -euo pipefail
STATE=/var/lib/octopus/state
LOCK=/var/lib/octopus/state/observation_autoheal.last
EVID=/var/lib/octopus/evidence/session-edge-next-20260823/m2-obs-harden
mkdir -p "$EVID"
SNAP=$(ls -1t "$STATE/snapshots"/snapshot-*.json 2>/dev/null | head -1 || true)
if [[ -z "$SNAP" ]]; then
  echo "no_snapshot" | tee "$EVID/autoheal.last.txt"
  exit 0
fi
BUS=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('bus_state',''))" "$SNAP")
ACTIVE=$(systemctl is-active octopus-sensorium.service || true)
NOW=$(date -u +%s)
if [[ -f "$LOCK" ]]; then
  LAST=$(cat "$LOCK" || echo 0)
else
  LAST=0
fi
# 10 minute rate limit
if (( NOW - LAST < 600 )); then
  echo "rate_limited bus=$BUS active=$ACTIVE" | tee "$EVID/autoheal.last.txt"
  exit 0
fi
if [[ "$ACTIVE" == "active" && "$BUS" == "ISOLATED" ]]; then
  echo "$NOW" > "$LOCK"
  echo "restarting_sensorium_for_isolated $(date -u -Iseconds)" | tee "$EVID/autoheal.last.txt"
  systemctl restart octopus-sensorium.service
  echo "restarted" >> "$EVID/autoheal.last.txt"
else
  echo "noop bus=$BUS active=$ACTIVE $(date -u -Iseconds)" | tee "$EVID/autoheal.last.txt"
fi
