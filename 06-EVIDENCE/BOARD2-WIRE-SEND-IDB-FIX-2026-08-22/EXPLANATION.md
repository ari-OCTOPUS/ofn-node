# BOARD2 wire-send id:b numbering fix — 2026-08-22

## Path patched
- **DietPi (live):** `ari@192.168.0.138:/home/ari/.local/bin/ofn-wire-send.sh`
- **Pre-fix backup:** `/home/ari/.local/bin/ofn-wire-send.sh.bak-idfix-20260822`
- **Windows copy:** NOT present under `F:\octopus-wire` or `F:\ofn-node` (send helper is board-side only).

## Bug
1. `LAST_B=$(... | sed 's/id://')` left the letter, e.g. `b003`.
2. `N=$((10#${LAST_B:-0} + 1))` became `$((10#b003))` → bash error: `value too great for base`.
3. With `set -u`, `N`/`NEW_ID` broke → empty headers (`##  - date`).
4. Secondary: many historical blocks are `## b003 —` without `id:b003`, so id:-only grep could miss max and re-issue low ids.

## Minimal patch applied
- Change `sed 's/id://'` → `sed 's/id:b//'`.
- If empty, fall back to `^## b[0-9]+` / `sed 's/^## b//'`.
- Leave `N=$((10#${LAST_B:-0} + 1))` and `printf 'b%03d'` unchanged.
- **Did not** enable Phase-3 / CONTROL_URL / OUTBOUND.
- **Did not** mint GitHub tokens.
- **Did not** git-commit (script lives outside the ofn/wire repo under `~/.local/bin`).

## Verification (captured)
See `REPRO-ARITH.txt` and `VERIFY.txt`.
- BEFORE: `LAST_B='b003'` → `10#b003: value too great for base`.
- AFTER: `LAST_B='003'` → `N=4 NEW_ID=b004`.
- Live against board `WIRE.md` (last `id:b003`): next id would be **b004**.

## How marketing can re-apply / confirm
See `PATCH-FOR-MARKETING.txt`.