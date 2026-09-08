cd ~/ofn || { echo 'CD_FAIL'; exit 9; }
export PYTHONDONTWRITEBYTECODE=1
echo '=====ROW GAP-002'
o=$(timeout 60 bash -c 'python -m tools.mesh_audit --node 180 --json | jq '''[.outbox[]|select(.ttl==null)]|length'''' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-004'
o=$(timeout 60 bash -c 'python -m tools.dual_outbox_verify --json | jq -r .status' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-005'
o=$(timeout 60 bash -c 'python -m tools.skip_table --explain --json | jq '''(.entries|length)>0 and (all(.entries[]; .reason!=null))'''' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-006'
o=$(timeout 60 bash -c 'python -m tools.queue_audit --batch 18 --json | jq -r .deployed' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-008'
o=$(timeout 60 bash -c 'python -m pytest tests/test_drain_semantics.py -q -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-009'
o=$(timeout 60 bash -c 'python -m tools.pulse --dry-run | rg -c "دکتر:"' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-010'
o=$(timeout 60 bash -c 'rg -c "OWNER-QUEUE" tools/ ofn/ --glob "!tests/**"' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-011'
o=$(timeout 60 bash -c 'rg -c "SILENT_FLIP" tools/pulse.py ofn/adapters/' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-012'
o=$(timeout 60 bash -c 'python -m tools.learning_feeder --dry-run --json | jq -r .runs_written' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-013'
o=$(timeout 60 bash -c 'python -m pytest tests/test_telegram_glass_runner.py -q -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-015'
o=$(timeout 60 bash -c 'rg -c "board_events" ofn/ tools/ --glob "!tests/**"' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-017'
o=$(timeout 60 bash -c 'python -m tools.doctor --json | jq '''[.units[]|select(.type=="oneshot" and .status=="UNKNOWN")]|length'''' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-018'
o=$(timeout 60 bash -c 'python -m tools.doctor --check imap --json | jq -r .status' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-019'
o=$(timeout 60 bash -c 'journalctl -u octopus-doctor -n 1 --no-pager' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-022'
o=$(timeout 60 bash -c 'python -m tools.homeostat --json | jq '''[.signals[]|select(.source==null and .zone!="WISHLIST")]|length'''' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-032'
o=$(timeout 60 bash -c 'python -m pytest tests/test_budget_idempotency.py -q -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-033'
o=$(timeout 60 bash -c 'python -m tools.verify_chain --from-zero --json | jq -r .status' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-037'
o=$(timeout 60 bash -c 'python -m pytest tests/test_authority_ladder.py -q -k a2_blocked -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-038'
o=$(timeout 60 bash -c 'python -m pytest tests/test_no_llm_import_in_reflex.py -q -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-039'
o=$(timeout 60 bash -c 'python -m pytest tests/test_no_executor_handle_in_cognition.py -q -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-040'
o=$(timeout 60 bash -c 'python -m tools.counters --json | jq -r '''[.EXTERNAL_ACTIONS,.NEW_LAN_LISTENERS,.MAY_AUTHORIZE]|@csv'''' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-041'
o=$(timeout 60 bash -c 'stat -c %s state/memory/memory.db' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-049'
o=$(timeout 60 bash -c 'python -m pytest tests/test_no_budget_without_owner_number.py -q -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-050'
o=$(timeout 60 bash -c 'python -m tools.queue_audit --ids 1515,1516,1517 --json | jq '''[.[]|select(.root_cause==null)]|length'''' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-053'
o=$(timeout 60 bash -c 'python -m tools.runway --json | jq -r '''[.runway_days,.source]|@csv'''' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-054'
o=$(timeout 60 bash -c 'python -m tools.treasury --json | jq -r .ato_reserve_ratio' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-055'
o=$(timeout 60 bash -c 'python -m pytest tests/test_strategy_not_persistence_copy.py -q -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-056'
o=$(timeout 60 bash -c 'python -m tools.gate_check --gate 4 --json | jq -r .status' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
echo '=====ROW GAP-060'
o=$(timeout 60 bash -c 'python -m pytest --collect-only -q 2>/dev/null | tail -1 -p no:cacheprovider' 2>&1); rc=$?
echo "RC=$rc"
echo "OUT=$o"
