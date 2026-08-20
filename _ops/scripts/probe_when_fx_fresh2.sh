#!/usr/bin/env bash
# نگهبان v2 — پیپ‌لاین کاملِ سازگار با دستور 15:45 (parser+receipt+probe).
# BLOCKED_FX_STALE یعنی «بعداً دوباره»؛ هر حکم دیگر = پایانی، حلقه متوقف.
cd /f/backup
for i in $(seq 1 12); do
  echo "=== probe-watch try $i/12 $(date +%H:%M) ==="
  python -X utf8 research/event_time_probe/pipeline.py 2>&1 | tail -20
  V=$(python -X utf8 -c "import json; print(json.load(open('06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json',encoding='utf-8')).get('verdict',''))" 2>/dev/null)
  echo "verdict: $V"
  if [ "$V" != "PROBE_BLOCKED_FX_STALE" ] && [ -n "$V" ]; then
    echo "TERMINAL-VERDICT:$V"; exit 0
  fi
  [ $i -lt 12 ] && sleep 600
done
echo "STILL-BLOCKED-FX after 12 tries (~2h)"
