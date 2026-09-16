# ofn-wire-send.sh ID counter bug — Board2 DietPi 192.168.0.138

Observed 2026-08-22 by marketing (Board2 M4).

## Broken lines (~16-17)
```bash
LAST_B=$(grep -oE 'id:b[0-9]+' WIRE.md 2>/dev/null | tail -1 | sed 's/id://')
N=$((10#${LAST_B:-0} + 1))
NEW_ID=$(printf 'b%03d' "$N")
```

## Why it fails
1. `sed 's/id://'` leaves `b003` (letter still present).
2. Bash `$((10#b003))` errors: `value too great for base` (token `10#b003`).
3. With `set -u`, `N` becomes unbound → empty `NEW_ID` → headers like `##  — 2026-08-22…`.
4. Secondary: historical WIRE.md blocks often use `## b003 —` without `id:b003`, so grep misses them and counter can also collide (re-issued b001).

## Proposed patch (minimal)
```bash
LAST_B=$(grep -oE 'id:b[0-9]+' WIRE.md 2>/dev/null | tail -1 | sed 's/id:b//')
# also accept legacy headers without id: prefix
if [ -z "$LAST_B" ]; then
  LAST_B=$(grep -oE '^## b[0-9]+' WIRE.md 2>/dev/null | tail -1 | sed 's/^## b//')
fi
N=$((10#${LAST_B:-0} + 1))
NEW_ID=$(printf 'b%03d' "$N")
# emit both human header and machine id
# "## $NEW_ID — …" AND ensure body/searchable `id:$NEW_ID`
```

## Out of scope / deferred
- Do not apply on board until owner opens tiny CHG (per ari).
- GitHub HTTPS creds on DietPi still empty (owner deferred) — separate track.
- Phase-3 CONTROL_URL/OUTBOUND stays OFF.

## APPLIED on DietPi 2026-08-22 ~18:52 AEST
- Canonical script: /home/ari/.local/bin/ofn-wire-send.sh
- Backup: ofn-wire-send.sh.bak-idfix-20260822
- Fix: sed 's/id:b//' + fallback '^## b[0-9]+' → digits; $((10#${LAST_B:-0}+1))
- Dry-run next id: b004 (last_b=003)
