#!/bin/bash
set -u
cd /home/ari/ofn
export PYTHONPATH=/home/ari/ofn
run_id="${1:?run id required}"
mode="${2:?mode required}"
export OCTOPUS_DEBUG_RUN_ID="$run_id"
export OCTOPUS_DEBUG_LOG="06-EVIDENCE/runtime-provenance-20260828T230743Z/debug-bbea48-${run_id}.log"
output="06-EVIDENCE/runtime-provenance-20260828T230743Z/${run_id}.out"
exit_file="06-EVIDENCE/runtime-provenance-20260828T230743Z/${run_id}.exit"

start="$(python3 -c 'import time; print(time.time())')"
if test "$mode" = targeted; then
  python3 -m unittest \
    tests.test_cockpit_v2_owner_queue \
    tests.test_cockpit_v2_purity \
    tests.test_cockpit_v2_http \
    tests.test_cockpit_v2_read_model \
    tests.test_cockpit_v2_business_truth \
    tests.test_cockpit_v2_frontend \
    -v > "$output" 2>&1
  rc=$?
elif test "$mode" = full; then
  python3 -m unittest discover -s tests -p 'test_*.py' \
    > "$output" 2>&1
  rc=$?
else
  printf 'unknown mode %s\n' "$mode" >&2
  exit 2
fi
end="$(python3 -c 'import time; print(time.time())')"
printf '%s\n' "$rc" > "$exit_file"
python3 - "$output" "$start" "$end" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
print(text)
print(f"WALL_SECONDS={float(sys.argv[3]) - float(sys.argv[2]):.3f}")
PY
printf 'TEST_EXIT=%s\n' "$rc"
exit 0
