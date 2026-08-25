#!/usr/bin/env bash
set -euo pipefail

BASE=/opt/octopus/lab
DB="$BASE/lab-data/organism.db"
PID_FILE="$BASE/receipts/organism.pid"
LOCK_FILE="$BASE/receipts/organism.start.lock"

umask 077
mkdir -p "$BASE/receipts"

exec 9>"$LOCK_FILE"
if ! /usr/bin/flock -n 9; then
  printf 'organism_start_locked\n' >&2
  exit 75
fi
export OCTOPUS_ORGANISM_LOCK_FD=9

if [[ -r "$PID_FILE" ]]; then
  read -r recorded_pid < "$PID_FILE" || recorded_pid=""
  if [[ "$recorded_pid" =~ ^[0-9]+$ ]] && [[ -d "/proc/$recorded_pid" ]]; then
    cmdline=""
    if [[ -r "/proc/$recorded_pid/cmdline" ]]; then
      cmdline="$(tr '\0' ' ' < "/proc/$recorded_pid/cmdline" 2>/dev/null || true)"
    fi
    expected_prefix="/usr/bin/python3 -m ofn.organism.runtime.app "
    if [[ "$cmdline" == "$expected_prefix"* ]]; then
      printf 'organism_already_running pid=%s\n' "$recorded_pid" >&2
      exit 73
    fi
  fi
  rm -f "$PID_FILE"
fi

cd "$BASE"
export PYTHONPATH="$BASE"

exec /usr/bin/python3 -m ofn.organism.runtime.app \
  --db "$DB" \
  --host 127.0.0.1 \
  --port 8090 \
  --heartbeat-interval 180 \
  --pid-file "$PID_FILE"
