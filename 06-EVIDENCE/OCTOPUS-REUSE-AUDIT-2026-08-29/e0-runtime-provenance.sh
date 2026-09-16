#!/bin/bash
set -euo pipefail

RUN="runtime-provenance-$(date -u +%Y%m%dT%H%M%SZ)"
EV="$HOME/ofn/06-EVIDENCE/$RUN"
mkdir -p "$EV"
printf '%s\n' "$EV" > /tmp/e0-evidence-dir.txt

systemctl show ofn.service \
  -p MainPID \
  -p ExecStart \
  -p WorkingDirectory \
  -p FragmentPath \
  -p ActiveState \
  -p SubState \
  -p ActiveEnterTimestamp \
  > "$EV/systemd-show.txt"

PID="$(systemctl show ofn.service -p MainPID --value)"
test -n "$PID"
test "$PID" != "0"
printf '%s\n' "$PID" | tee "$EV/process-pid.txt"

readlink -f "/proc/$PID/cwd" | tee "$EV/process-cwd.txt"
readlink -f "/proc/$PID/exe" | tee "$EV/process-exe.txt"
tr '\0' ' ' < "/proc/$PID/cmdline" | tee "$EV/process-cmdline.txt"

CWD="$(readlink -f "/proc/$PID/cwd")"
EXE="$(readlink -f "/proc/$PID/exe")"

git -C "$CWD" rev-parse HEAD | tee "$EV/runtime-tree-head.txt"
git -C "$CWD" branch --show-current | tee "$EV/runtime-tree-branch.txt"
git -C "$CWD" status --porcelain=v1 | tee "$EV/runtime-tree-status.txt"
git -C "$CWD" remote -v | tee "$EV/runtime-tree-remotes.txt"

"$EXE" - > "$EV/import-origins.txt" <<'PY'
import hashlib
import importlib
import pathlib

modules = [
    "ofn.run",
    "ofn.adapters.http_api",
    "ofn.adapters.cockpit_v2_read_model",
    "ofn.adapters.ledger",
    "ofn.adapters.outbox",
]

for name in modules:
    try:
        m = importlib.import_module(name)
        p = pathlib.Path(m.__file__).resolve()
        data = p.read_bytes()
        print(
            name,
            f"path={p}",
            f"bytes={len(data)}",
            f"sha256={hashlib.sha256(data).hexdigest()}",
        )
    except Exception as exc:
        print(name, f"UNAVAILABLE:{type(exc).__name__}:{exc}")
PY

{
  sha256sum \
    "$CWD/ofn/run.py" \
    "$CWD/ofn/adapters/http_api.py" \
    "$CWD/ofn/adapters/ledger.py" \
    "$CWD/ofn/adapters/outbox.py"
  if test -f "$CWD/ofn/adapters/cockpit_v2_read_model.py"; then
    sha256sum "$CWD/ofn/adapters/cockpit_v2_read_model.py"
  else
    echo "MISSING $CWD/ofn/adapters/cockpit_v2_read_model.py"
  fi
  for extra in \
    "$CWD/ofn/adapters/owner_decision.py" \
    "$CWD/ofn/adapters/witness_mint.py" \
    "$CWD/ofn/adapters/fake_executor.py"
  do
    if test -f "$extra"; then
      sha256sum "$extra"
    else
      echo "MISSING $extra"
    fi
  done
} > "$EV/source-sha256.txt"

systemctl show ofn.service -p ActiveEnterTimestamp --value | tee "$EV/process-start.txt"

{
  echo "ActiveEnterTimestamp=$(systemctl show ofn.service -p ActiveEnterTimestamp --value)"
  for f in \
    "$CWD/ofn/run.py" \
    "$CWD/ofn/adapters/http_api.py" \
    "$CWD/ofn/adapters/ledger.py" \
    "$CWD/ofn/adapters/outbox.py" \
    "$CWD/ofn/adapters/cockpit_v2_read_model.py" \
    "$CWD/ofn/adapters/owner_decision.py" \
    "$CWD/ofn/adapters/witness_mint.py" \
    "$CWD/ofn/adapters/fake_executor.py"
  do
    if test -f "$f"; then
      stat -c '%y %n' "$f"
    fi
  done
} > "$EV/source-mtime-compare.txt"

git -C "$CWD" diff --check | tee "$EV/git-diff-check.txt" || true
git -C "$CWD" status --porcelain=v1 | tee "$EV/git-status-final.txt"

ls -1 "$CWD/ofn/adapters"/*.bak-* 2>/dev/null | tee "$EV/tracked-bak-files.txt" || true

printf 'EV=%s\nPID=%s\nCWD=%s\nEXE=%s\n' "$EV" "$PID" "$CWD" "$EXE"
