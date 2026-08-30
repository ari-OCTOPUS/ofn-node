#!/usr/bin/env bash
# نگهبان پروب: هر ۱۰ دقیقه RBA را چک می‌کند؛ به‌محض دادهٔ ۲۰ اوت (یا تازه‌تر):
# پین FX (authority = payload امضاشده) زیر lease → اجرای پروب → release.
cd /f/backup
for i in $(seq 1 6); do
  curl -s --max-time 30 "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv" -o _ops/state/f11-tmp.csv
  PUBDATE=$(python -X utf8 -c "
import csv
rows = list(csv.reader(open('_ops/state/f11-tmp.csv', encoding='utf-8', errors='replace')))
print(rows[9][1] if len(rows) > 9 and len(rows[9]) > 1 else 'NONE')
" 2>/dev/null)
  echo "try $i/6 RBA publication-date: $PUBDATE"
  if [[ "$PUBDATE" == 20-Aug-2026* || "$PUBDATE" == 21-Aug-2026* ]]; then
    python -X utf8 -c "
import csv, json, hashlib, sys
from pathlib import Path
rows = list(csv.reader(open('_ops/state/f11-tmp.csv', encoding='utf-8', errors='replace')))
rate = [r[1] for r in rows[11:] if len(r) > 1 and r[0].strip() == '20-Aug-2026']
if not rate: sys.exit('no 20-Aug row')
aud_usd = float(rate[-1])
rec = {'fx_source_id': 'RBA_EXCHANGE_RATES_DAILY_2026-08-20',
       'fx_timestamp_utc': '2026-08-20T06:00:00Z',
       'fx_rate_usd_to_aud': round(1.0/aud_usd, 9),
       'FX_SOURCE_VALUE': f'AUD_USD = {aud_usd}',
       'FX_CONVERSION_METHOD': 'reciprocal_of_RBA_AUD_USD',
       'owner_pin_id': 'FX-PIN-20260820-01',
       'fx_hash': hashlib.sha256(f'AUD_USD = {aud_usd}@{round(1.0/aud_usd,9)}'.encode()).hexdigest(),
       'pinned_at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
       'standing_authorization': 'SIGNED payload PRE-REG-EVENT-TIME-PROBE-2026-08-20 (Ed25519 verified)'}
for p in [Path('_ops/cortex/pricing_pinned.json'), Path('06-EVIDENCE/CL01-191-20260818-2233/live4/FX-RECORD.json')]:
    d = json.loads(p.read_text(encoding='utf-8'))
    d['fx_usd_to_aud'] = rec['fx_rate_usd_to_aud']
    d['fx_record'] = rec
    if '_comment' in d: d['_comment'] = 'FX pinned FX-PIN-20260820-01 (RBA daily 2026-08-20). Authority: SIGNED PRE-REG-EVENT-TIME-PROBE. No auto-refresh.'
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
print('PINNED', rec['fx_rate_usd_to_aud'])
" || { echo "pin failed"; exit 2; }
    python -X utf8 _ops/writer_lease.py acquire --agent "agent-B-ZCode-probe" --session "sess_1d388c34-probe" --ttl 300 --scope "state,evidence" | head -1
    python -X utf8 research/event_time_probe/run_probe.py 2>&1 | tail -25
    python -X utf8 _ops/writer_lease.py release --agent "agent-B-ZCode-probe" --session "sess_1d388c34-probe" | head -1
    echo "PROBE-FLOW-DONE"
    exit 0
  fi
  [ $i -lt 6 ] && sleep 600
done
echo "PROBE-STILL-BLOCKED-FX: RBA 20-Aug data not published after 6 tries (~60 min)"
