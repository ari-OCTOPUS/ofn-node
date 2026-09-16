#!/bin/bash
set -euo pipefail
EV=/home/ari/ofn/06-EVIDENCE/runtime-provenance-20260828T230743Z
cd /home/ari/ofn
export PYTHONPATH=/home/ari/ofn
set +e
python3 -m unittest \
  tests.test_owner_decision_fake \
  tests.test_executor_fake \
  tests.test_witness_mint \
  tests.test_business_source_export \
  -q > "$EV/e8-unittest.out" 2> "$EV/e8-unittest.err"
echo $? | tee "$EV/e8-unittest.exit"
set -e
tail -n 30 "$EV/e8-unittest.err"
sqlite3 -readonly /home/ari/.local/share/ofn/outbox.sqlite \
  'SELECT status, count(*) FROM outbox GROUP BY status;' \
  | tee "$EV/outbox-status-counts.txt"
