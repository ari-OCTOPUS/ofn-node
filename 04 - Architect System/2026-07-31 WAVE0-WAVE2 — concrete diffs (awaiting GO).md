# 2026-07-31 · WAVE 0.2 + WAVE 2 — CONCRETE DIFFS (AWAITING GO)
**Status:** READY TO APPLY — owner must say "GO" (D4). Nothing changed yet.
**Scope:** my domain only (NO telegram). Two independent edits + tests.

---

## CHANGE 1 — W0.2: Restore hardened LockedJson.write (VQ-STATE-WRITE-001)
**File:** `_ops/budget/opslib.py` lines 270-297
**Why:** Current HEAD has the WEAKER 6-retry version. Commit `0a303af` (in history) has a
BETTER version (fsync + failure receipt + snapshot integration) that was lost in merge `681907f`.
Restoring it = bringing back a known-good, already-reviewed fix.
**Risk:** LOW — restoring a reviewed commit, not inventing new logic. Central writer, so tested carefully.
**Rollback:** `git checkout 681907f -- _ops/budget/opslib.py` (or revert this edit).

### The diff (apply exactly — replace current write() body):
- BEFORE: 6 attempts, `tmp.write_text`, NO fsync, breadcrumb-only `.replace-failed.json`
- AFTER (0a303af): `open()`+`fh.flush()`+`os.fsync()`, 5 attempts with `0.05*(2**attempt)` backoff,
  `_write_failure_receipt()` → `STATE_DIR/write-failures.jsonl` (real receipt, consumed by snapshot)
- Add module-level `WRITE_FAILURES = STATE_DIR / "write-failures.jsonl"` + `_write_failure_receipt()` fn.

---

## CHANGE 2 — W2: Hebbian instrumentation = the EFE bridge
**File:** `_ops/wiring.py` — two edits:
  (a) inside `_hebbian_eventclock_beat` after `observed = True` (~L1292)
  (b) lazy import of `emit_event` (no top-level import to avoid circular)
**Why:** Hebbian associations currently ONLY go to `hebbian.json` (flat file, dead end). Logging
each observation to spine.db via `emit_event` makes the REAL learning layer observable/queryable —
the honest prerequisite for any future EFE. NOT building EFE.
**Risk:** LOW — purely additive, behind new flag `OCTOPUS_HEBBIAN_LEDGER` (default OFF = zero I/O).
Fail-soft (emit_event never raises). No change to learning math.
**Rollback:** unset flag / delete the ~6 added lines.

### The diff:
- New flag gate: `if flag("OCTOPUS_HEBBIAN_LEDGER"):`
- Lazy import: `from spine import spine_adapters` (inside the gate)
- emit: `spine_adapters.emit_event(event_type="hebb.observation", domain="neural",
  correlation_id=f"hebb-win-{n}", producer="wiring.hebbian", trust="ADVISORY",
  payload={"window_n": n, "union_signals": union, "n_pairs": len(union)*(len(union)-1)//2,
  "top_strength": max((heb.strength_of(u, v) for ...), default=0.0)})`

---

## VERIFICATION (D13 — per change)
- **Test:** run the existing Hebbian test suite (`_ops/tests/test_hebbian*.py` or equivalent)
  + LockedJson tests. Add one assertion that emit fires when flag on, zero I/O when off.
- **Check:** organism stays alive (beat advancing). `write-failures.jsonl` only grows on real fail.
- **Green bar:** all suites green; no new .tmp stranding.

## EXECUTION
These two are independent (different files) — I'll do them serially (me = single agent),
test after each, report, then Wave 0.3 (budget) next.

SAY GO to apply Change 1, or amend.
