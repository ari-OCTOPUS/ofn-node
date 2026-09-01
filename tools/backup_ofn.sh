#!/bin/bash
# backup_ofn.sh — بکاپِ شبانهٔ انبارهای بورد (Lane I3، رأی Q7)
# هر شب: sqlite3 .backup برای سه انبار + sha256 manifest؛ نگه‌داری ۱۴ روز.
set -u
DEST="$HOME/backups/ofn-daily"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$DEST/$STAMP"
rc=0
for db in "$HOME/.local/share/ofn/painting.sqlite" \
          "$HOME/.local/share/ofn/outbox.sqlite" \
          "$HOME/ofn/ofn/agi2027_runtime/outbound-effects.sqlite3"; do
  name="$(basename "$db")"
  if [ -f "$db" ]; then
    sqlite3 "$db" ".backup '$DEST/$STAMP/$name'" || rc=1
  fi
done
# state های حیاتی هم همراه
cp -r "$HOME/ofn/data/state" "$DEST/$STAMP/state" 2>/dev/null || true
( cd "$DEST/$STAMP" && sha256sum * > SHA256SUMS 2>/dev/null; \
  find state -type f -exec sha256sum {} + >> SHA256SUMS 2>/dev/null ) || true
# چرخش: فقط ۱۴ آخر
ls -1dt "$DEST"/20* 2>/dev/null | tail -n +15 | xargs -r rm -rf
echo "backup done rc=$rc dest=$DEST/$STAMP"
exit $rc
