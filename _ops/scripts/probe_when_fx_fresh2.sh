#!/usr/bin/env bash
# نگهبان v2.1 — طبق طبقه‌بندی دستور: فقط حکم‌های پایانی توقف می‌کنند؛
# FX_STALE و HTTP_FAILED (شبکه) و BLOCKED_LEASE = retryable با backoff.
cd /f/backup
TERMINAL="PROBE_PASS|PROBE_RESPONSE_INVALID|PROBE_BLOCKED_SIGNATURE|PROBE_BLOCKED_SOURCE_CONFLICT|PROBE_BLOCKED_LEASE|PROBE_BLOCKED_FX_STALE_AFTER_2H"
for i in $(seq 1 12); do
  echo "=== probe-watch try $i/12 $(date +%H:%M) ==="
  python -X utf8 research/event_time_probe/pipeline.py 2>&1 | tail -14
  V=$(python -X utf8 -c "import json; print(json.load(open('06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json',encoding='utf-8')).get('verdict',''))" 2>/dev/null)
  echo "verdict: $V"
  case "$V" in
    PROBE_PASS|PROBE_RESPONSE_INVALID|PROBE_BLOCKED_SIGNATURE|PROBE_BLOCKED_SOURCE_CONFLICT)
      echo "TERMINAL:$V"; exit 0 ;;
    PROBE_BLOCKED_LEASE)
      echo "lease-held-by-session — retry (transient)"; sleep 60 ;;
    *)
      echo "retryable ($V) — 10 min backoff" ;;
  esac
  [ $i -lt 12 ] && sleep 600
done
echo "STILL-BLOCKED after 12 tries (~2h)"
