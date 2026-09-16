# CLOCK AND TIMESTAMP AUDIT — A02 Runtime Investigator

## Time source / timezone

- Host timezone: **AUS Eastern Standard Time, UTC+10:00** (no DST in effect during observation). System clock `2026-08-16T23:46:31+10:00`; PowerShell agrees (`23:46:33.079+10:00`). NTP sync state not queried (w32tm needs admin; out of read-only scope) — UNKNOWN.
- All human-readable logs (`HEARTBEAT.md`, most `state/*.json` `ts` fields) use **naive local time** via `opslib.now_iso()` = `datetime.now().isoformat()` (`_ops/budget/opslib.py:175`) — no timezone marker.

## Monotonic clock usage

- **`time.monotonic()` is used NOWHERE** in the live codebase (`grep` across `_ops`, `chrono.py`, `organism.py` — 0 hits) (F-24).
- Beat scheduling (`organism.py:540` `now = time.time()`; `:1335` hourly gate; `:1434` `time.sleep`), HLC physical time (`chrono.py:93-94` `_utc_ms = time.time()*1000`), freshness checks (`opslib` lines 92/249/308/475/530), and heart sampling (`heart/producers.py:365-376`) are all **wall-clock**.
- Consequence: a system clock step (NTP correction, manual change, DST boundary) can stretch/compress beats, trip freshness checks, or double-fire hourly gates. The HLC implementation (CockroachDB-style, `chrono.py:98-114`) tolerates physical-time regressions logically, but nothing else does.

## Timestamp convention per artifact (observed values)

| Artifact | Convention | Example observed | Correct? |
|---|---|---|---|
| `_memory/HEARTBEAT.md` | naive local, no marker | `2026-08-16T23:06:44` | ⚠️ ambiguous outside host TZ |
| `state/ORGANISM-STATE.json` ts | naive local | `2026-08-16T23:53:31` | ⚠️ ambiguous |
| `state/pulse/arbiter-latest.json` ts | naive local | `2026-08-16T23:53:25` | ⚠️ ambiguous |
| `state/pulse/math-control-latest.json` ts | local time **with `Z` suffix** | `2026-08-16T13:53:26Z` while actual local was 23:53 | ❌ **BUG — local time mislabeled as UTC, 10 h skew** (F-24) |
| `state/board-status.txt` | local **with explicit +10:00** | `2026-08-16T23:00:52+10:00` | ✅ |
| `state/telegram/miniapp-url.json` started/stopped | UTC `Z` | `2026-08-15T20:58:11Z` = 06:58:11+10 — matches cloudflared process start | ✅ |
| `state/state_guard-receipts.jsonl` ts | UTC `Z` | `2026-08-16T02:35:34Z` = 12:35:34+10 — matches file mtimes | ✅ |
| `chrono.db` / HLC | epoch ms UTC | hlc `[1786888354115, 0]` = 23:52:34+10 | ✅ machine-consistent |
| `_octopus/logs/audit.log` | local with +1000 | `2026-08-16T12:35:57+1000` | ✅ (nonstandard offset format but explicit) |

## Consistency incidents

1. **math-control `Z` mislabel (confirmed bug)**: `pulse/math-control-latest.json` `ts` carries local time with a UTC designator. Any consumer sorting/correlating by that field sees a 10-hour illusion (e.g. "3 hours stale" when fresh, or "fresh" when 10 h stale). Cross-checked: its sibling values (`beat 38509`) align with the local-time beat sequence, not UTC.
2. **Three conventions coexist** (naive local / explicit-offset / UTC-Z) plus one hybrid file per writer family. Cross-artifact correlation requires knowing each writer's convention; a future DST transition (AEDT +11) will silently shift every naive-local artifact by an hour relative to fixed-offset consumers.
3. **Beat timestamps are internally consistent**: sampled beat advances (23:53→23:55→23:57) align with file mtimes and the arbiter's 125.02 s effective period — no clock skew within the organism this window.
