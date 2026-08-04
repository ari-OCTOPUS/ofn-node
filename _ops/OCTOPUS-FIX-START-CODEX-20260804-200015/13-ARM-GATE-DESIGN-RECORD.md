# 13 — arm_gate design record

Source: `_ops/arm_gate.py` docstring + code (read in full this session).

## Intent

Defense-in-depth against "ambient capability": the ~12 `ACTIVATION-*.flag` files sit on
disk, so a bare restart re-arms paid/self-mod paths without any fresh owner action. arm_gate
adds a strictly-tightening precondition — a dangerous capability opens only if, **in
addition** to its ACTIVATION flag, a fresh (TTL-bounded) owner arm-token exists, and for the
highest-risk self-modification capabilities, **two** independent tokens (two-key).

## Fail-closed everywhere

Unknown capability, missing/stale/future/unreadable token, wrong-capability token, or (when
an owner secret is configured) a bad HMAC → deny. `arm_open()` never raises — any internal
exception is caught and turned into a deny (`failsafe-deny:<ExceptionType>`).

## Two independent knobs, both default-off, both strictly-tightening

| Knob | Env var | Scope when on |
|---|---|---|
| `enforced()` | `OCTOPUS_REQUIRE_ARM` | ALL five `DANGEROUS` capabilities require arm_open() |
| `sensitive_enforced()` (new in `2a99aa3`, #30 fix) | `OCTOPUS_ARM_SENSITIVE_DEFAULT` | Only `code_autonomy`, `self_improve_auto`, `replicate` (the three D5/D6-highest-risk ones) require arm_open(), even when `enforced()` is False |

When both are off (today's live process state, and today's on-di<REDACTED-OPENAI-KEY>
state before `2a99aa3`'s flag would take effect), `guard()` returns `(True,
"arm-gate-not-enforced")` for everything — byte-identical to pre-arm_gate behavior. This is
deliberate and documented as the compatibility guarantee.

## The five capabilities and their ACTIVATION flags

| capability | flag file | two-key? |
|---|---|---|
| `cortex_paid` | `ACTIVATION-CORTEX-PAID.flag` | no |
| `governor_llm` | `ACTIVATION-GOVERNOR-LLM.flag` | no |
| `code_autonomy` | `ACTIVATION-CODE-AUTONOMY.flag` | **yes** |
| `self_improve_auto` | `ACTIVATION-SELF-IMPROVE-AUTO.flag` | **yes** |
| `replicate` | `ACTIVATION-REPLICATION.flag` | **yes** |

## The one thing the design doc does not cover

Nowhere in `arm_gate.py` or its docstring is a caller specified — the module is a complete,
tested library with no consumer wired in. That is the gap this run found and is proposing
(not applying) a fix for.
