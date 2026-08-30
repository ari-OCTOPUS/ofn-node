#!/usr/bin/env bash
# watch_hour.sh — نگهبان یک‌ساعتهٔ OCTOPUS (رأی چت مالک 2026-08-20) — فقط خواندن + append لاگ
cd /f/backup
LOG="06-EVIDENCE/OCTOPUS-WATCH-2026-08-20.md"
for i in $(seq 1 12); do
  TS=$(date +%H:%M)
  PID=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'organism.py' }).ProcessId" 2>/dev/null | tr -d '\r' | head -1)
  PORT=$(powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue) {'LISTENING'} else {'dead'}" 2>/dev/null | tr -d '\r')
  READ=$(python -X utf8 -c "
import json,os,time,sqlite3
try:
    d=json.load(open('_ops/state/ORGANISM-STATE.json',encoding='utf-8')); m=json.load(open('_ops/state/pulse/memory-read-latest.json',encoding='utf-8'))
    age=round(time.time()-os.path.getmtime('_ops/state/pulse/memory-read-latest.json'),0)
    con=sqlite3.connect(r'file:_ops/state/spine/spine.db?mode=ro',uri=True)
    t48=con.execute('SELECT COUNT(*) FROM events WHERE legacy_no_event_time=0').fetchone()[0]; con.close()
    mr=f\"{m.get('status')}/r{m.get('memory_reads_per_cycle')}/{m.get('readback')}/age{age}s\"
    print(f\"{d.get('beat')}|{mr}|{t48}\")
except Exception as e:
    print(f'ERR|{type(e).__name__}|0')
" 2>/dev/null)
  BEAT=$(echo "$READ" | cut -d'|' -f1); MR=$(echo "$READ" | cut -d'|' -f2); T48=$(echo "$READ" | cut -d'|' -f3)
  if [ -z "$PID" ] || [ "$PORT" != "LISTENING" ]; then VERDICT="ANOMALY: organism-down (pid='$PID' port=$PORT) — بازیافت دست مالک"; else VERDICT="OK"; fi
  ROW="| $TS | ${PID:-none} | $PORT | $BEAT | $MR | $T48 | $VERDICT |"
  echo "$ROW" >> "$LOG"
  echo "scan $i/12 $ROW"
  [ $i -lt 12 ] && sleep 300
done
echo "WATCH-COMPLETE: 12 scans done"
