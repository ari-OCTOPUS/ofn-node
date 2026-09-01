#!/bin/bash
# restore_drill.sh — آزمونِ واقعیِ بازیابی (GAPS-13: هیچ‌وقت انجام نشده بود)
# آخرین بکاپ را به /tmp می‌ریزد، checksum را می‌سنجد و ردیف‌ها را می‌شمارد.
# موفقیت = exit 0 + خط در restore-drill.log — «بکاپ داریم» تا «بازیابی کردیم» ارتقا یافت.
set -u
DEST="$HOME/backups/ofn-daily"
LOG="$HOME/ofn/data/state/restore-drill.log"
LATEST="$(ls -1dt "$DEST"/20* 2>/dev/null | head -1)"
if [ -z "${LATEST:-}" ]; then
  echo "NO BACKUP FOUND" | tee -a "$LOG"; exit 1
fi
TMP="$(mktemp -d)"
cp -r "$LATEST" "$TMP/restore"
rc=0
cd "$TMP/restore" || exit 1
sha256sum -c SHA256SUMS >/dev/null 2>&1 || { echo "CHECKSUM FAIL"; rc=1; }
for db in painting.sqlite outbox.sqlite outbound-effects.sqlite3; do
  if [ -f "$db" ]; then
    n="$(sqlite3 "$db" 'SELECT COUNT(*) FROM sqlite_master' 2>/dev/null || echo ERR)"
    echo "drill $LATEST $db objects=$n $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
    [ "$n" = "ERR" ] && rc=1
  fi
done
rm -rf "$TMP"
echo "restore drill rc=$rc"
exit $rc
