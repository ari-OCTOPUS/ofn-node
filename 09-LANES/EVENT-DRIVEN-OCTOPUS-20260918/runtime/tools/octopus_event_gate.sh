#!/bin/bash
# octopus_event_gate.sh — fail-closed gate + shadow/live switch for event-triggered runners.
# EVENT-DRIVEN-OCTOPUS 2026-09-18.  v2: "-" dirs = direct file-watch trigger, no event files.
#
# Usage:  octopus_event_gate.sh <name> <inbox-dir>[,...]|- -- <cmd...>
#
# Behaviour
#  1. STALE BEAT  -> refuse (exit 75), receipt EVENTS_GATED_STALE_BEAT. Nothing runs.
#  2. mode=shadow -> do NOT run the runner; move event files to shadow-consumed/ and
#                    write a SHADOW_WOULD_RUN receipt naming the items it WOULD process.
#  3. mode=live   -> run the runner; rc==0 -> move event files to processed/ + receipt;
#                    rc!=0 -> leave files in place + FAILED receipt (beat-pulse
#                    re-touch sweeper retriggers them later).
#
# mode is read per-name from state/events/mode.json  {"default":"shadow","<name>":"live"}
# set OCTOPUS_GATE_MODE_OVERRIDE=live|shadow to force.
# trigger source can be named by the unit via OCTOPUS_GATE_TRIGGER=<path> (recorded).
set -u
EV=/home/ari/ofn/state/events
MODE_FILE="$EV/mode.json"
BEAT="$EV/beat.json"
RECEIPTS="$EV/gate-receipts.jsonl"
MAX_AGE="${OCTOPUS_BEAT_MAX_AGE:-150}"
TRIGGER="${OCTOPUS_GATE_TRIGGER:-}"

NAME="${1:-}"; shift || true
DIRS_CSV="${1:-}"; shift || true
[ "${1:-}" = "--" ] && shift || true
if [ -z "$NAME" ] || [ -z "$DIRS_CSV" ] || [ "$#" -eq 0 ]; then
  echo "usage: $0 <name> <dirs-csv|-> -- <cmd...>" >&2; exit 2
fi

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if [ -f "$BEAT" ]; then
  BMT=$(stat -c %Y "$BEAT"); AGE=$(( $(date +%s) - BMT ))
else
  AGE=999999
fi

rcpt() { # rcpt <kind> <extra-json-fields>
  printf '{"schema":"octopus.gate.v1","at":"%s","gate":"%s","kind":"%s","beat_age_s":%s,"trigger":"%s"%s}\n' \
    "$NOW" "$NAME" "$1" "$AGE" "$TRIGGER" "$2" >> "$RECEIPTS"
}

if [ "$AGE" -gt "$MAX_AGE" ]; then
  rcpt EVENTS_GATED_STALE_BEAT ",\"max_age_s\":$MAX_AGE,\"note\":\"fail-closed: beat stale, runner not started\""
  echo "GATED: beat stale (${AGE}s > ${MAX_AGE}s) name=$NAME" >&2
  exit 75
fi

MODE=$(OCTOPUS_MODE_FILE="$MODE_FILE" OCTOPUS_GATE_NAME="$NAME" python3 - <<'PY' 2>/dev/null
import json, os
p = os.environ["OCTOPUS_MODE_FILE"]; n = os.environ["OCTOPUS_GATE_NAME"]
try:
    d = json.load(open(p))
except Exception:
    d = {}
print(d.get(n, d.get("default", "shadow")))
PY
)
[ -n "${OCTOPUS_GATE_MODE_OVERRIDE:-}" ] && MODE="$OCTOPUS_GATE_MODE_OVERRIDE"

DIRECT=0
[ "$DIRS_CSV" = "-" ] && DIRECT=1
DIRS=()
if [ "$DIRECT" -eq 0 ]; then IFS=',' read -r -a DIRS <<< "$DIRS_CSV"; fi

collect() {
  for d in "${DIRS[@]:-}"; do [ -d "$d" ] && find "$d" -maxdepth 1 -name '*.json' -type f 2>/dev/null; done
}
FILES=$(collect)
COUNT=$(printf '%s' "$FILES" | grep -c '\.json$' || true)

if [ "$MODE" = "shadow" ]; then
  ITEMS=$(printf '%s' "$FILES" | head -20 | xargs -r -n1 basename | paste -sd, -)
  rcpt SHADOW_WOULD_RUN ",\"files\":$COUNT,\"items\":\"${ITEMS}\",\"direct\":$DIRECT"
  for f in $FILES; do
    mkdir -p "$EV/shadow-consumed/$NAME"
    mv -f "$f" "$EV/shadow-consumed/$NAME/" 2>/dev/null || true
  done
  exit 0
fi

if [ "$DIRECT" -eq 0 ] && [ "$COUNT" -eq 0 ]; then
  exit 0   # retrigger with nothing to do: silent no-op
fi

START=$(date +%s)
"$@"
RC=$?
END=$(date +%s)
ITEMS=$(printf '%s' "$FILES" | head -20 | xargs -r -n1 basename | paste -sd, -)
if [ "$RC" -eq 0 ]; then
  for f in $FILES; do
    mkdir -p "$EV/processed/$NAME"
    mv -f "$f" "$EV/processed/$NAME/" 2>/dev/null || true
  done
  rcpt EVENTS_RAN ",\"files\":$COUNT,\"items\":\"${ITEMS}\",\"duration_s\":$((END-START)),\"rc\":0,\"direct\":$DIRECT"
else
  rcpt EVENTS_RUN_FAILED ",\"files\":$COUNT,\"items\":\"${ITEMS}\",\"duration_s\":$((END-START)),\"rc\":$RC,\"direct\":$DIRECT"
fi
exit $RC
