#!/usr/bin/env bash
# پل ۵ دقیقه‌ای OCTOPUS↔مالک (دستور مالک 2026-08-20 شب) — تا توقف، هر ۳۰۰ ثانیه.
cd /f/backup
while true; do
  python -X utf8 -u _ops/scripts/tg_bridge_once.py 2>&1
  sleep 300
done
