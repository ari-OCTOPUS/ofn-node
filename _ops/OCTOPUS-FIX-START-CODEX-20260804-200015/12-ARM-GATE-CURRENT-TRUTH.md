# 12 — arm_gate: current truth

## The headline finding of this run

**The arm_gate P0 is code-complete and tested, but structurally unenforced.** Commit
`2a99aa3` (2026-08-04, already on `master` before this session started) made the
`arm_gate.py` module *capable* of closing blindspot #30, and shipped 28 passing tests for it
— but **nothing in the production codebase calls it**. Flipping `OCTOPUS_ARM_SENSITIVE_
DEFAULT=1` (which the owner already did, in `OCTOPUS-flags.cmd`) currently has **zero
behavioral effect**, because the function it controls, `arm_gate.guard()`, has no caller.

This is the exact gap the master instruction itself anticipated ("arm_gate هنوز فقط
proposal بود، fix واقعی نشد") — confirmed still true even after the newer commit that made
the module itself better.

## Evidence

1. `_ops/state/ORGANISM-STATE.json:76` — `"arm_gate_enforcing": false` — live, file mtime
   ~3 min before this check (organism actively running).
2. `_ops/arm_gate.py` fully implements `enforced()` (reads `OCTOPUS_REQUIRE_ARM`),
   `sensitive_enforced()` (reads `OCTOPUS_ARM_SENSITIVE_DEFAULT`, new in `2a99aa3`), and
   `guard(capability, **kw)` which is the intended single call-site helper
   (`arm_gate.py:147-161`).
3. Full-tree grep for `arm_gate` outside `arm_gate.py` and `tests/`:
   ```
   _ops/action_bridge/scope_guard.py:36   — string in an allowlist, not a call
   _ops/orphan_scan.py:241                — a comment about arm_gate being orphan-scanned
   _ops/outcomes/thesis_queue.py:68       — a comment referencing "arm_gate.py — double-apply test"
   _ops/wiring.py:738-744                 — SELF-DOCUMENTING ADMISSION (see below)
   ```
   **No `import arm_gate`, no `arm_gate.guard(`, no `arm_gate.arm_open(` anywhere in
   production code.**
4. `_ops/wiring.py:738-744` (existing comment, not written by this run):
   > "arm_gate تزئینی است تا وقتی OCTOPUS_REQUIRE_ARM ست نشود (arm_gate.py:51 —
   > (cortex_paid) در arm_gate.DANGEROUS فهرست است ولی سایتِ فراخوانش چک نمی‌کند"
   >
   > Translation: "arm_gate is decorative until OCTOPUS_REQUIRE_ARM is set — cortex_paid is
   > in arm_gate.DANGEROUS but its call site does not check it." A previous agent already
   > found and documented this exact gap; it was not closed by `2a99aa3`.

## What IS true (do not overstate the gap either)

- `code_autonomy`'s actual write path (`self_patch.py`'s `_offer_patch_to_owner`, see
  `14-ARM-GATE-PATCH-REPORT.md`) is **not undefended** — it already sits behind its own
  7-gate chain (ACTIVATION flag, heart mood, `_owner_approved`, `allowed_target`,
  `shadow_green`, non-empty content, 48h staleness ceiling) plus an explicit owner
  button-tap. `arm_gate` was designed as *additional* defense-in-depth on top of that chain,
  not the only gate — its docstring says so explicitly ("P5 defense-in-depth... ADDS a
  strictly-tightening precondition... never relaxes anything").
- So the practical risk is narrower than "wide open": it is "the intended second gate for
  code_autonomy/self_improve_auto/replicate does not yet run," not "these capabilities have
  no gate at all." Still, closing it is exactly what blindspot #30 asked for, and it remains
  open.

## Status

**PARTIAL — module fixed, tested, and safe to leave as-is (default-off, strictly-
tightening); NOT enforced in production; needs a wiring decision from the owner before it
does anything.** See `13-ARM-GATE-DESIGN-RECORD.md` and `14-ARM-GATE-PATCH-REPORT.md`.
