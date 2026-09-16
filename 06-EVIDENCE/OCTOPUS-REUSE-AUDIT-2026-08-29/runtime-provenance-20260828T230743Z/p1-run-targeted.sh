#!/bin/bash
set -u
cd /home/ari/ofn
export PYTHONPATH=/home/ari/ofn
export OCTOPUS_DEBUG_ENDPOINT=http://127.0.0.1:7901/ingest/bed063e6-fc1e-4087-81ba-9bee01576aa1
export OCTOPUS_DEBUG_RUN_ID="${1:-p1-targeted}"
export OCTOPUS_DEBUG_LOG="06-EVIDENCE/runtime-provenance-20260828T230743Z/debug-bbea48-${OCTOPUS_DEBUG_RUN_ID}.log"
output="06-EVIDENCE/runtime-provenance-20260828T230743Z/${OCTOPUS_DEBUG_RUN_ID}.out"
exit_file="06-EVIDENCE/runtime-provenance-20260828T230743Z/${OCTOPUS_DEBUG_RUN_ID}.exit"
python3 -m unittest tests.test_cockpit_v2_owner_queue -v > "$output" 2>&1
rc=$?
printf '%s\n' "$rc" > "$exit_file"
python3 - "$output" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))
PY
printf 'TEST_EXIT=%s\n' "$rc"
exit 0
