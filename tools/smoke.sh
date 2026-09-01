#!/bin/bash
# smoke.sh — دروازهٔ دودِ دیپلوی (GAPS-74/75): هر ایجنت قبل از هر ادعایی این را اجرا کند
set -u
cd /home/ari/ofn
fail=0
step() { printf "%-46s" "$1:"; }

step "pytest lane battery"
if python3 -m pytest tests/test_lane_e_q.py -q >/tmp/smoke_pytest 2>&1; then echo PASS; else echo FAIL; tail -5 /tmp/smoke_pytest; fail=1; fi

step "imports (transport/worker/writer/listener/quote)"
if python3 - <<'EOF' >/dev/null 2>&1
import sys
sys.path.insert(0, "ofn/agents"); sys.path.insert(0, "ofn/budget")
import lead_outbound_transport, outbound_worker, lead_email_writer
import imap_listener, followup_worker, quote_engine, quote_pipeline
import owner_notify, heartbeat, daily_digest, rotate_logs
EOF
then echo PASS; else echo FAIL; fail=1; fi

step "reconcile 6 invariants"
if python3 tools/reconcile.py >/dev/null 2>&1; then echo PASS; else echo FAIL; fail=1; fi

step "timers armed (7 octopus timers)"
n=$(systemctl list-timers --no-pager | grep -c "octopus-\(imap\|heartbeat\|digest\|followup\|backup\|drill\|quote\)\.timer")
if [ "$n" -eq 7 ]; then echo "PASS ($n/7)"; else echo "FAIL ($n/7)"; fail=1; fi

step "clock synchronized (NTP)"
if timedatectl | grep -q "synchronized: yes"; then echo PASS; else echo FAIL; fail=1; fi

step "last backup exists"
if ls -1t ~/backups/ofn-daily/20* >/dev/null 2>&1; then echo "PASS ($(ls -1t ~/backups/ofn-daily/ | head -1))"; else echo FAIL; fail=1; fi

step "halt oracle clear (HALT-ALL absent)"
if [ ! -f ~/ofn/HALT-ALL ]; then echo PASS; else echo "HALTED — intentional?"; fi

step "rate card lock intact"
if python3 -c "import json,sys; d=json.load(open('/home/ari/.local/share/ofn/painting_rate_card.json')); sys.exit(0 if d.get('approved_by_owner') is False else 1)" 2>/dev/null; then echo "PASS (locked)"; else echo "NOTE: approved-or-missing"; fi

echo "SMOKE $([ $fail -eq 0 ] && echo ALL-PASS || echo HAS-FAILURES)"
exit $fail
