# 15 — arm_gate test results

Both test files run directly this session with `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`
(see `04-TEST-RESULTS.md` for why that flag is needed on Windows).

## `test_arm_gate.py` — 16/16 pass (unittest, verbose)

Covers: flag-absent deny, flag-present-no-token deny, single-key fresh-token open, stale
token deny, future token deny, wrong-capability token deny, HMAC valid open / forged deny /
required-when-secret-and-bad deny, two-key both-open / one-missing-deny /
second-stale-deny, unknown-capability deny, `guard()` pass-through-when-not-enforced,
`guard()` deny-without-token-when-enforced, `arm_status()` reports all 5 caps unarmed by
default.

## `test_arm_gate_p0.py` — 12/12 pass (blindspot #30 specific)

Covers: default-off pass-through, sensitive-capability-no-arm → deny (only when
`sensitive_enforced()`), sensitive-capability-valid-arm → allow, stale-arm → deny,
non-sensitive capability still passes through under `sensitive_enforced()` alone (i.e. the
new flag does NOT silently widen scope to `cortex_paid`/`governor_llm`), full-enforce mode
still works unchanged, unknown-capability deny, `arm_status()` shape checks, `replicate`
flag-absent → deny, and an explicit "no network/http/socket in this module" AST-style check.

## Honest caveat

These are **unit tests of the module in isolation** — every one of them calls
`arm_gate.guard(...)` or `arm_gate.arm_open(...)` directly. None of them exercise a real
call site inside `self_patch.py` or anywhere else, because — per `12-ARM-GATE-CURRENT-
TRUTH.md` — no such call site exists yet. A green 28/28 here proves the gate itself is
correct; it does not prove the gate is consulted by anything that matters yet.
