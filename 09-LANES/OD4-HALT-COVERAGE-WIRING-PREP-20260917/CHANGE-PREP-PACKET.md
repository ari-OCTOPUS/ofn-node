---
type: proposal
status: draft
tags: [octopus, od-4, halt-oracle, change-prep, no-patch-applied, blocking-question]
updated: 2026-09-17
project: "[[OCTOPUS]]"
---

# CHANGE-PREP PACKET — OD-4 Option B (narrow halt-coverage wiring)

`GOV_VERSION=V8 · LADDER=L2 · mode: SPEC + PREP ONLY`
`authority: owner ruling OD-4, 2026-09-17 (Option B)`
`STATUS: NOT APPLIED · no diff has been written to any file · implementation BLOCKED on BQ-1`

> **Nothing in this packet has been applied.** Every code block below is a *plan*,
> written for review. No file under `F:\ofn-node` was modified; no service restarted;
> no flag edited; no HALT file touched; no node contacted.

---

## 0. STATUS — targets APPROVED by owner card 2026-09-17 (BQ-1 / BQ-2 CLOSED)

The owner card approved the corrected targets and **rejected `callbudget.py`**, matching
the trace. Recorded verbatim at
`06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-CARD-OD4-2026-09-17.md`.

| Effect | Approved site | Approved oracle |
|---|---|---|
| **A — Telegram send** | `ofn/node.py`, `publish_to_telegram` / `ReleaseContext` construction (`:3607`) | existing `opslib.master_halted()` — **not** a second HALT path |
| **B — model spend** | site 1: `ofn/adapters/router.py` model admission point · site 2: `ofn/assistant_update.py:32` direct call | existing `opslib.master_halted()` |
| **REJECTED** | `ofn/kernel/callbudget.py` | — |

**BQ-1 CLOSED** — corrected target approved as traced.
**BQ-2 CLOSED** — owner chose the **halt check at the direct call site** for
`assistant_update.py:32` (the packet's recommendation).
**No rework is required**: the patches in §1 and §2.2 are already exactly the approved
shape. `callbudget.py` is formally **out of OD-4 scope**.

### Owner's non-negotiable order (binding on this lane)

1. Build doctor first. 2. Run doctor once offline. 3. Produce machine-readable pre/post
receipts for coverage. 4. **Only then** apply the narrow wiring.

This lane performs **none of 1–4 as implementation**; it delivers the spec, the prep
packet, and the coverage proof. The wiring is step 4 and is **not authorized yet**.

### Why the originally-named target was wrong (audit trail — kept, not deleted)

The owner named **`callbudget.py`** as "the text model budget path". The trace says
otherwise — the same failure class this lane series documents, applied to the
instruction itself.

**`callbudget.CallBudget` gates neither of the two live model-egress consumers.**

| `call_budget` use site (`grep -n call_budget ofn/node.py`) | What it gates |
|---|---|
| `:326-327` | diagnostics `report()` |
| `:422` | owner-ask **submit** path |
| `:1707`, `:1719-1720` | `request_studio_reading` (studio advisor) |
| `:3587-3588`, `:3643-3646` | the **Telegram publish** rate-limit slot |

And the two things that actually spend model money:

| Consumer | Gate it really has | Is `callbudget` on it? |
|---|---|---|
| **B-1** `ModelRouter.ask` (`router.py:130`) — the live worker thread (`run.py:587,626` → `worker.py:223`), plus `node.py:1277`, `node.py:1721` | `NodeQuota.check` (`router.py:214`, injected at `run.py:548`) | **No.** `router.py` does not import callbudget; `worker.py` has no budget reference at all. |
| **B-2** `ofn/assistant_update.py:32` — `RemoteBrain.answer(...)` called **directly**, bypassing the router | **none found** — no quota, no budget, no halt | **No** |

Wiring the halt oracle into `callbudget.py` would therefore produce a change that
**passes its own tests, reads as compliant with the instruction, and stops nothing** —
a textbook `DECLARED ≠ WIRED` fix. Per the owner's evidence rule ("stop before partial
implementation"), **this lane stops here and asks** rather than implementing the wrong
site.

Full trace with commands: `CONSUMER-MAP.json` (this directory).

### Resolution of the owner's stop condition

The card says: *"If any consumer path is still UNVERIFIED, stop and report instead of
guessing."* Precision matters here, so it is stated explicitly:

| Question | Verdict |
|---|---|
| Is the **consumer set** of effect A resolved? | **YES** — one consumer, traced to a single production call line |
| Is the **consumer set** of effect B resolved? | **YES** — two consumers, both traced to their egress sites |
| Is any **consumer path** UNVERIFIED? | **NO** — all three consumer paths are `WIRED` and proven by command + output |
| Is anything about these effects still UNVERIFIED? | **YES, but not the consumer paths** — three *environmental* items (below) |

**The three UNVERIFIED items are runtime/environmental, not structural:**

1. **U-1** — which exact path each running service resolves at runtime, and the on-node
   file state (`absent`/`present`/`malformed`/`unreadable`/`symlink`). *Forbidden to
   observe in this lane.*
2. **U-2** — deployed env values (`OFN_KEEP_GATES_OPEN`, `OFN_EXTRA_CLOSED_GATES`,
   presence of `remote_api_key`). Effect B is only reachable if a remote key is present
   (`build_brains` wires hosted rungs only then). *Not read, not contacted.*
3. **U-3** — whether an out-of-repo `octopus-*` unit invokes a model or send path.
   *Outside this repo.*

**Therefore the stop condition does NOT fire**, and it is exactly why the owner's order
puts the doctor before the wiring: U-1 and U-2 are what the doctor's Half B captures.
No guessing is required anywhere in this packet — the structural claims are all verified,
and the environmental unknowns are named as unknowns.

---

## 0.5 COVERAGE PROOF (owner success definition: *prove coverage, not just path correctness*)

Path correctness answers "does execution get from the caller to the egress?".
Coverage answers "does the canonical halt oracle actually **stop** it?" These are
different questions, and only the second is what OD-4 is for.

Labels are restricted to the four the owner authorized: `WIRED` / `TESTED_ONLY` /
`DOC_ONLY` / `UNVERIFIED`.

### 0.5.1 Current coverage — the "pre" state (expected doctor output)

| Effect | Consumer | Path correctness | **Halt-oracle COVERAGE today** | Any budget gate? | Basis |
|---|---|---|---|---|---|
| **A** | `node.py:3607` (`ReleaseContext.kill_switch_active`) | **WIRED** | **DOC_ONLY** | `CallBudget` (rate-limit slot) | the in-process `self.killed` is `WIRED`; the **file oracle is not consulted on this path**, though `AGENTS.md` GOV-V7 documents it as the safeguard. Verified: `node.py:3600-3616` reads `kill_switch_active=self.killed` only |
| **B-1** | `router.py:130` `ModelRouter.ask` (live worker + `node.py:1277` + `node.py:1721`) | **WIRED** | **DOC_ONLY** | `NodeQuota` (`router.py:214`) | `master_halted()` is not called; `callbudget.py:80` states *"HALT is not consulted"*. The oracle is documented as the node-wide stop and is absent from this path |
| **B-2** | `assistant_update.py:32` (direct `RemoteBrain.answer`) | **WIRED** | **DOC_ONLY** | **none — verified absent** | no quota, no budget, no halt on this path; live daily via `ofn-assistant-update.timer` (04:10) |

**Verdict summary for the pre state: 3 consumers, 0 of 3 covered by the canonical
oracle.** All three path-correct, all three coverage-`DOC_ONLY`.

> **Vocabulary gap, reported honestly.** The four authorized labels have no value for
> "verified absent, and not even documented as applying here" — which is the literal
> state of B-2's budget gate. `DOC_ONLY` is used because the oracle *is* documented as a
> node-wide safeguard, but the label undersells a consumer with **no gate of any kind**.
> Flagged rather than silently stretched; if the owner wants a fifth label (e.g.
> `ABSENT`), that is a vocabulary decision, not this lane's to make.

### 0.5.2 Target coverage — the "post" state (what a successful wiring must produce)

| Effect | Consumer | Halt-oracle coverage after wiring | How it is proven |
|---|---|---|---|
| **A** | `node.py:3607` | **WIRED** | test T2: refusal with the **exact** rule `release:kill-switch-active`; T5 wiring test |
| **B-1** | `router.py` admission | **WIRED** | test T4: `refused_code == "route:halt"` **and** zero calls to `RemoteBrain.answer` |
| **B-2** | `assistant_update.py:32` | **WIRED** | test T6: `RemoteBrain` constructor never called when halted |

**Success is a coverage transition, not a green test suite:** `DOC_ONLY → WIRED` for
exactly these three consumers, and **no other consumer's label may change**. A diff that
alters any other consumer's coverage has left OD-4 scope (see §4.3).

### 0.5.3 Pre/post receipt contract (owner order step 3)

The wiring may not be applied until both receipts exist and are machine-readable. The
doctor emits them; this packet defines the shape so step 3 is auditable.

```json
{
  "schema": "octopus.halt-coverage-receipt.v1",
  "phase": "PRE | POST",
  "captured_at_utc": "<ISO8601>",
  "runtime_identity": {"commit": "<sha of F:/ofn-node HEAD>", "host": "<declared>"},
  "canonical_oracle": {"resolved_path": "<path>", "state": "absent|present|malformed|unreadable|symlink",
                       "predicate": "RUNNING|HALTED|UNKNOWN"},
  "consumers": [
    {"effect_id": "E-A-telegram-send", "consumer": "ofn/node.py:3607",
     "coverage": "DOC_ONLY", "evidence": "<command or test id>", "unchanged_since_pre": null},
    {"effect_id": "E-B-text-model-spend", "consumer": "ofn/adapters/router.py:130",
     "coverage": "DOC_ONLY", "evidence": "<command or test id>", "unchanged_since_pre": null},
    {"effect_id": "E-B-text-model-spend", "consumer": "ofn/assistant_update.py:32",
     "coverage": "DOC_ONLY", "evidence": "<command or test id>", "unchanged_since_pre": null}
  ],
  "out_of_scope_consumers": {"checked": true, "any_label_changed": false},
  "mutations_performed": 0
}
```

Rules: exactly three consumer rows (T-rows beyond three mean scope creep); `phase: PRE`
must exist **before** any wiring lands; `phase: POST` must show all three at `WIRED` and
`out_of_scope_consumers.any_label_changed == false`; `mutations_performed` is always `0`.

---

---

## 1. Effect A — Telegram send path (clean; 1 consumer)

**Consumer:** `Node.publish_to_telegram` → `ReleaseContext.kill_switch_active`
(`ofn/node.py:3607`). Verified single: `grep -rn "\.publish("` over `ofn/ tools/ ops/
scripts/` returns exactly one production line, `ofn/node.py:3637`. `pilot_daily.py`
uses the **read-only** adapter, not a send path.

### Exact diff plan (site A-1)

`ofn/node.py`, in `publish_to_telegram`, at the `ReleaseContext(...)` construction
(currently line 3607):

```python
# BEFORE (current)
            kill_switch_active=self.killed,

# AFTER (planned — not applied)
            kill_switch_active=self.killed or _halt_oracle_active(),
```

with **one** module-level addition in `ofn/node.py`:

```python
# PLANNED — not applied. Deliberately reads the EXISTING oracle rather than
# re-deriving a path: a second path literal here would recreate the D-3 defect.
from .budget import opslib as _opslib


def _halt_oracle_active() -> bool:
    """True when the canonical halt oracle is engaged. Fail-closed."""
    try:
        return _opslib.master_halted() is not None
    except Exception:
        return True          # cannot verify the switch ⇒ treat as engaged
```

**Why `opslib.master_halted()` and not `halt_flag_active(<path>)`:** `opslib.py:20` is the
existing single source of truth for *both* the path (`~/ofn/HALT-ALL`) and the
`HALT_SURVIVAL_LOOP=1` override. Supplying the path from a second place would
re-introduce exactly the fragmentation OD-1 exists to fix. `halt_flag_active()` remains
the reader it uses internally.

**Why not dependency injection here:** the Node already injects `quota`, `router`,
`ledger`, `call_budget` as optional attributes set at wiring time. Injection would be
more testable but introduces an "injected but never wired" state — i.e. a new
`DECLARED ≠ WIRED` surface. Direct-and-fail-closed has no such state, and is smaller.
*(Trade-off stated; injection is the fallback if testability outweighs that risk.)*

**No change to `ofn/kernel/release_switch.py`.** The gate already handles
`kill_switch_active` first and unconditionally (`release_switch.py:79-82`,
`RULE_KILL = "release:kill-switch-active"`). We only feed it a more truthful input.
This is required by the owner's constraint "do not change … release gate".

**Blast radius:** one expression + one import + one 4-line helper in a single file.
Behaviour changes only when the file oracle is actually engaged.

---

## 2. Effect B — text-model spend

### 2.1 Variant b1 — the named target (`callbudget.py`) — **REJECTED**

Rejected because it stops neither live consumer (§0). Recorded here so the rejection is
auditable rather than silent. Also: doing it would contradict the module's own stated
doctrine — `callbudget.py:28` "HALT is not a parameter. Layer 3 stops STARTS; an
in-flight record still …" and `:80` "Structurally False. HALT is not consulted — this is
not a start gate." A change there would have to reverse a deliberate design note in
addition to being ineffective.

### 2.2 Variant b2 — the corrected target — **RECOMMENDED (BQ-1)**

**B-1 — `ofn/adapters/router.py`.** One admission check at the top of `ask()`, before
the rung loop. The router already takes an injected `quota`, `on_event` etc., so the
oracle is injected the same way:

```python
# PLANNED — not applied.  ofn/adapters/router.py
# constructor gains: halt_oracle: Callable[[], str | None] | None = None  -> self._halt_oracle

# in ask(), immediately after `cleaned = scrub(prompt)`:
        if self._halt_oracle is not None:
            try:
                if self._halt_oracle() is not None:
                    return RouterResult("", None, refused="halt engaged",
                                        refused_code="route:halt")
            except Exception:
                return RouterResult("", None, refused="halt engaged",
                                    refused_code="route:halt-unverifiable")
```

plus the wiring at `ofn/run.py:548`:

```python
# BEFORE:  router = ModelRouter(build_brains(cfg), node.quota, on_event=...)
# AFTER:
    from .budget import opslib as _opslib
    router = ModelRouter(build_brains(cfg), node.quota, on_event=...,
                         halt_oracle=_opslib.master_halted)
```

**This is the single choke point for effect B-1**: all three callers
(`worker.py:223`, `node.py:1277`, `node.py:1721`) go through `ask()`. It touches no
quota cap, no rung policy, no `_charge` accounting.

**Injection here is acceptable (unlike effect A) because the "unwired" state is caught
by test T5** — see §3. The test is what makes the injected form safe; without it, this
variant would carry the half-landed risk.

**B-2 — `ofn/assistant_update.py:32`.** Script entry point; direct call, no DI needed:

```python
# PLANNED — not applied.  ofn/assistant_update.py, before `rb = RemoteBrain(...)`
    from .budget import opslib as _opslib
    if _opslib.master_halted() is not None:
        print("assistant update: skipped (halt engaged)")
        return 0
```

Verified context: `ofn-assistant-update.timer` → `OnCalendar=*-*-* 04:10:00`,
`ExecStart=/usr/bin/python3 -m ofn.assistant_update` — a **live daily** path that
currently constructs `fugu-ultra` with `timeout_s=900` and calls it with no gate.

---

## 3. Test cases (exact assertions)

All offline; none may contact a network, a node, or a live path. The halt oracle is
substituted via the injected parameter / env var so tests never touch `~/ofn`.

| # | Test | Assertion |
|---|---|---|
| **T1** | A regression: halt **not** engaged | `publish_to_telegram` behaves exactly as today; existing `tests/test_sender_dryrun.py` and `tests/test_studio_marketing_actions.py` stay green |
| **T2** | A: halt engaged, publish attempted | refusal with `rule == "release:kill-switch-active"` (`RULE_KILL`, `release_switch.py:63`), `ok is False`, and **no** adapter call — assert `TelegramChannelAdapter.publish` was never invoked |
| **T3** | A: oracle raises | treated as engaged (fail-closed) — same refusal as T2 |
| **T4** | B-1: halt engaged, each of the 3 callers | `RouterResult.refused_code == "route:halt"`; assert `RemoteBrain.answer` was **never** called (patch it and assert zero calls) |
| **T5** | **Wiring test** (the anti-half-landing test) | after `build_worker(...)`/router construction, assert `router._halt_oracle is not None`; and after `build_node(...)` assert the effect-A oracle is reachable. **This is the test that prevents this lane's fix from itself becoming `DECLARED ≠ WIRED`.** |
| **T6** | B-2: halt engaged | `assistant_update.main()` returns 0 and `RemoteBrain` is never constructed (assert constructor not called) |
| **T7** | Predicate fixtures | the 9 file states in `HALT-ORACLE-DOCTOR-SPEC.md` §8.3 behave fail-closed |
| **T8** | Dry-run neutrality preserved | a `dry_run=True` publish still does not consume a budget slot (`node.py:3643`, `if not dry_run`) |
| **T9** | **No-scope-leak test** | sha256 of the forbidden files (§4) is byte-identical before and after the change |

Test assertions T2 reference the **exact** rule string. `RULE_OK = "release:ok"`,
`RULE_KILL = "release:kill-switch-active"`, `RULE_LEDGER = "ledger:not-ready"` — verified
at `release_switch.py:63-73`. A test asserting a paraphrase of these would be wrong.

---

## 4. Proof that no unintended scope is leaking in

### 4.1 Files the plan touches (exhaustive)

| File | Lines | Nature |
|---|---|---|
| `ofn/node.py` | +1 import, +1 helper (~4 lines), 1 expression at `:3607` | construct the release context |
| `ofn/adapters/router.py` | +1 constructor param, +1 attribute, ~7 lines in `ask()` | admission check |
| `ofn/run.py` | +1 import, +1 kwarg at `:548` | wiring |
| `ofn/assistant_update.py` | +3 lines at the top of `main()` | admission check |

**4 files. No new file. No new module. No new gate class. No new daemon, timer, or flag.**

### 4.2 Files that MUST remain byte-identical (verified by hash in T9)

`ofn/kernel/callbudget.py` · `ofn/kernel/quota.py` · `ofn/kernel/release_switch.py` ·
`ofn/adapters/ledger.py` · `ofn/kernel/hash_chain.py` · `ofn/agents/consent_gate.py` ·
`ofn/agents/consent_store.py` · `data/gates.json` · `BUDGET.json` ·
`tools/install_systemd.sh` · every `deploy/systemd/*` unit · every `HALT*` path ·
every `OCTOPUS_WIRE_*` / `OFN_WIRE_*` occurrence.

This list maps 1:1 onto the owner's prohibitions: "Do not change LEDGER, consent,
release gate, budget thresholds, or outbound flags" and "Do not touch HALT files,
systemd, timers, or any live node."

### 4.3 Anti-scope-creep assertions

- The change adds **no** general/global egress guard — the owner explicitly excluded
  one. Each check is local to one consumer boundary.
- The change adds **no** architectural refactor. No module is split, renamed, or moved.
- The change does **not** alter when anything is *allowed* today; it can only make
  something *refused* that is currently permitted **while the halt oracle is engaged**.
  With the oracle disengaged, behaviour is bit-identical — this is the property T1 pins.
- Nothing here consumes or writes receipts; nothing reads a secret; no new import of a
  network or database module is introduced (`opslib` is stdlib + pathlib only).

---

## 5. Rollback path

Because the change is four small local edits with no persisted state, rollback is exact
and one-command:

1. **Pre-image (must be taken before applying):** `git -C F:/ofn-node rev-parse HEAD`
   → record sha; plus sha256 of the four target files.
2. **Standard revert:** `git -C F:/ofn-node revert <change-sha>` — or, if the change is
   uncommitted, `git -C F:/ofn-node checkout -- ofn/node.py ofn/adapters/router.py
   ofn/run.py ofn/assistant_update.py`.
3. **No state to unwind:** no flag was flipped, no file was created, no migration ran,
   no receipt was written, no service was restarted. The halt oracle itself is untouched.
4. **Verification after rollback:** T1 (regression) must be green and the four file
   hashes must equal the pre-image.
5. **Anything that produces an external effect requires a receipt or a rollback**
   (GOV-V7 safeguard). This change produces none on its own — it can only *prevent*.

Note: the effect-A/effect-B changes are independent and separately revertable; A can be
landed and rolled back without touching B.

---

## 6. Lane attestation — zero live changes

| Attestation | Value |
|---|---|
| Files modified under `F:\ofn-node` | **0** |
| Files modified in ledger / consent / release gate / budget thresholds / outbound flags | **0** |
| Services restarted | **0** |
| Flags edited (any direction) | **0** |
| HALT files created / deleted / armed | **0** |
| systemd units or timers touched | **0** |
| Live nodes contacted | **0** |
| Network requests made by this lane | **0** |
| Automatic side-effects | **0** |
| Output | reports + one machine-readable map, nothing else |

---

## 7. What must happen before this becomes implementable

BQ-1 and BQ-2 are **closed** (§0). The remaining gates are the owner's own numbered
order, which is binding:

| Owner order step | State | Note |
|---|---|---|
| 1. Build doctor first | **not done** | authorized read-only (OD-1 clause 3 + this card); spec + fixture harness complete at `HALT-ORACLE-DOCTOR-SPEC.md` §1–§8 |
| 2. Run doctor once **offline** | **not done** | must be offline; no live-node execution is authorized |
| 3. Machine-readable pre/post receipts for coverage | **contract defined** (§0.5.3) | the `PRE` receipt must exist before any wiring lands |
| 4. **Only then** apply the narrow wiring | **NOT AUTHORIZED** | blocked on 1–3 |

Additional gates:

- **Class B rules apply to deployment.** The four-file edit is code-in-repo, but
  *deploying* it to a live node is Class B and requires the independent witness. This
  lane does neither.
- **Scope lock.** The implementation must map to exactly the three consumer rows in
  §0.5.2. Any change that alters coverage for any other consumer, or that introduces a
  shared/global guard, is outside OD-4 and must be re-carded — the owner's
  "no scope expansion into generalized guard architecture" and "nothing else counts as
  OD-4 scope".
- **No live ablation.** Testing this must never involve arming a real halt flag on a live
  node; the fixture harness and the injected/substituted oracle are how it is tested.

**Stop point for this lane.** The card says *"No implementation in this lane."* This lane
therefore stops here having produced: the approved-target confirmation, the coverage
proof (§0.5), the pre/post receipt contract, the exact diff plans, the test set, the
rollback path, and the zero-live-change attestation. **No wiring code has been written.**
