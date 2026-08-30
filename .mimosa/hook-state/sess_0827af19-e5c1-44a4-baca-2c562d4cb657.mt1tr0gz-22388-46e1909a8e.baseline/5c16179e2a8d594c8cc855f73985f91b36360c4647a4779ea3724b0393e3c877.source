# DESIGN — FUGU-EVERYWHERE (M2.1)

One brain, reachable from every intelligent organ-beat, through **one door**:
`cortex.model_router.ask`. Propose-only. No merge, no flag-toggle, no arming.

Ground truth: all line refs read from `F:\backup` on 2026-07-24 (see CALLER-MAP.md).

---

## 0. Problem, in one paragraph

`model_router.ask` is already the fenced, budget-gated, local-first door
(`model_router.py:168-296`). But (a) two organ work-types (`chord.extract`,
`tg_intent`) route through it yet always resolve to **local** because they are absent
from `TASK_TIERS` (`model_router.py:41-46`, resolved at `:202`); (b) three heavy
organs — governor (`governor_epoch.py:289`), heart-doctor
(`doctor_setpoint.py:176`), debate (`debate_loop.py:86`) — call `DeepSeekClient`
**directly**, so they can never reach the owner's Fugu/GLM subscription and they
duplicate the reserve/settle/gate logic; (c) several beats that produce qualitative
output (cartographer, cultivation, business-legs) have **no** brain path at all. The
fix is one migration pattern plus a small extension to the door, all behind flags.

---

## 1. The unified pattern (the only pattern)

Every intelligent organ-beat routes through `model_router.ask` and obeys this contract:

```python
# at the top of any brain path — non-negotiable (already enforced in _ask_impl:180)
if opslib.STOP_ORGANISM.exists() or opslib.halted():   # + master_halted() for beats
    return <fail-soft default>            # never crash the tick

from cortex import model_router
r = model_router.ask(
        task,                 # a TASK_TIERS key — chooses default tier
        prompt,               # data only; fence screens it (model_router.py:186-198)
        system=<role prompt>,
        max_tokens=<n>,
        tier=None,            # let TASK_TIERS/route_scorer decide (or pin for privacy)
        organ=<ORGAN>,        # NEW: which organ_gate budget line to charge
        role=None,            # NEW: provider-role override (econ/reason) if owner wants
        quality=<callable?>)  # optional stricter local-first gate (as synthesis uses)
if not r.get("ok"):
    <deterministic / heuristic fallback>  # brain-off or FREEZE ⇒ organ still works
```

Rules baked into this contract (all already true in the door, preserved verbatim):
1. **Local always allowed, $0** — `local_llm.ask` (`local_llm.py:62`) needs no gate,
   only rate-limit + kill-switch (`local_llm.py:66-71`).
2. **Paid strictly behind `ACTIVATION-CORTEX-PAID`** — `_ask_paid` calls `paid_gate()`
   first (`model_router.py:115-116`); the double-lock is date + flag
   (`model_router.py:100-108`).
3. **Paid never bypasses organ_gate/budget_gate** — every paid call reserves→settles
   (`model_router.py:127-138`); `organ_gate.reserve` fails closed under
   `halted`/`frozen` (`organ_gate.py:62-68`) and `budget_gate` is the sole enforcer
   (`organ_gate.py:96`).
4. **Fail-soft** — paid closed/failed ⇒ local (`model_router.py:237-260`); local off
   ⇒ `{"ok": False, "reason": …}` (`:266-269`). The **caller** must have a
   deterministic fallback so the organ never dies when the brain is silent.
5. **Zero secrets in logs** — only `tier/model/cost/latency` recorded
   (`model_router.py:291-293`); prompts/content never logged. Preserved.

---

## 2. Extending the door: `organ` + `role` (additive, byte-identical default)

Today `_ask_paid` hardcodes `organ="ARCHITECT_SYS"` and derives role only from
`_TIER_ROLE` (`model_router.py:117,127,136`). To let a migrated organ keep its own
budget line (e.g. `DEBATE_LOOP`) and, if the owner chooses, its own provider role
(`econ`/`reason`), add two **optional** parameters that default to today's behavior:

- `organ: str = _DEFAULT_ORGAN` (`"ARCHITECT_SYS"`) — threaded to
  `organ_gate.reserve/settle/release`.
- `role: str | None = None` — `role = role or _TIER_ROLE.get(tier)`; unknown ⇒ None ⇒
  paid path declines and falls to local (unchanged failure mode).

Because both default to the current constants, **every existing caller is
byte-identical** — this is a strict superset. (See `fugu-everywhere.patch`, hunk 1.)

### 2a. `TASK_TIERS` extension — no more silent-local
Add explicit entries so organ work-types route by intent, not by accident:

| task | tier | why |
|---|---|---|
| `chord.extract` | `local` | structured JSON extraction; cheap, on-device fine — but now *explicit* |
| `tg_intent` | `secondary` | understanding arbitrary owner free-text deserves GLM when armed |
| `governor` | `secondary` | metabolic allocation reasoning (was DeepSeek-econ) |
| `heart_setpoint` | `secondary` | viable-band proposal (was DeepSeek-econ) |
| `debate_muse` | `secondary` | idea generation |
| `debate_architect` | `primary` | kill-condition / cheapest-test rigor → Fugu |

All still gated: `secondary`/`primary` only fire when `paid_gate()` is open AND a key
is present (`model_router.py:226-236`); otherwise local. No new spend authority.

---

## 3. Migrating the three bespoke callers

The migration replaces the direct `DeepSeekClient.complete` block with one
`model_router.ask(...)` call, **keeping each caller's own activation flag as an extra
precondition**. This is deliberately *more* conservative than removing those flags:
to spend, BOTH the caller's own flag (`ACT_GOV_LLM` / `ACT_HEART_DOCTOR` /
`ACT_DEBATE`) AND `ACTIVATION-CORTEX-PAID` must be open. The design never widens spend
authority; it only makes Fugu/GLM *reachable* where DeepSeek was pinned.

### A. `governor_epoch.allocate_llm` (reference migration — in the patch)
- Keep `live_gate_open(ACT_GOV_LLM)` guard (`governor_epoch.py:261-263`) as the
  "should I even try paid?" precondition.
- Keep `fence_adapter.screen_llm_input` (`:284-287`) — belt-and-suspenders; the door
  fences again (`model_router.py:186-198`).
- Replace the `DeepSeekClient`/`organ_gate` block (`:288-304`) with:
  ```python
  r = model_router.ask("governor", user, system=system, max_tokens=1200,
                       tier="secondary", organ="ARCHITECT_SYS")
  if not r.get("ok"):
      return None   # fail-closed to dry (unchanged behavior)
  return {"llm_allocation": client.extract_json(r["text"]),
          "model": r.get("model"), "cost_usd": r.get("cost_usd", 0.0)}
  ```
- Net: governor can now use Fugu/GLM when armed; reserve/settle still happen (inside
  the door, same `ARCHITECT_SYS` line); DeepSeek remains available via `role="deepseek"`
  override if the owner prefers.

### B. `heart/doctor_setpoint.llm_refine` — same shape
`ask("heart_setpoint", user, system=<band prompt>, max_tokens=400, tier="secondary",
organ="ARCHITECT_SYS")`, keep `ACT_HEART_DOCTOR` precondition + the deterministic
policy fallback on `not ok` (`doctor_setpoint.py:189-196`).

### C. `debate/debate_loop` — two-role, described (not patched; larger surface)
`_gated_call` (`debate_loop.py:67-91`) becomes a thin wrapper over
`model_router.ask(role_task, user, organ="DEBATE_LOOP", tier=<per-role>)` where
`role_task` is `debate_muse` / `debate_architect`. Keep `ORGAN="DEBATE_LOOP"`
(`:37`) as the `organ=` argument so the debate budget line is unchanged. The stub
transport path (`_stub_transport`, offline tests) stays for `live=False`. This one is
left for the owner to land after A/B prove the pattern, because debate threads the
client through `_rounds` (`debate_loop.py:149`) and needs role-prompt plumbing.

### Inventory bookkeeping (must accompany the patch)
`test_llm_call_inventory.py:39-64` is the machine-check. After migration, move
`budget/governor_epoch.py` (and later heart/debate) from `ADAPTER_FENCED` to
`ROUTER_FENCED`, or the test fails (`t_b_inventory_not_stale`,
`t_c_adapter_fenced_actually_wired`). The patch includes this edit for governor.

---

## 4. route_scorer activation behind `CORTEX_ROUTE_SCORER` + held-out

**Verified reality:** `route_scorer` is **already wired** — `_scored_tier`
(`model_router.py:147-165`) is consulted from `_ask_impl` when
`os.environ.get("CORTEX_ROUTE_SCORER")` is set and no explicit tier was given
(`model_router.py:200-201`), fully fail-soft to `TASK_TIERS`. The write-side is also
flagged (`route_scorer.py:36,255`). So "activation behind the flag" exists.

**The real remaining gap is trust, not wiring:** there is no held-out set proving the
scorer's tier suggestions match the static map (or owner judgment) before we let it
override routing in production. Proposal (design-only; harness sketch, not in patch):

1. **Held-out corpus** `_ops/eval/route_holdout.jsonl` — ~40 labelled `{task, ctx,
   expected_tier}` rows drawn from the real task strings in CALLER-MAP §1 plus the new
   organ tasks (§2a). Labels are the owner's, checked in read-only.
2. **Shadow scorer harness** `_ops/eval/route_scorer_eval.py` — pure, $0, offline
   (imports only `route_scorer` + stdlib, mirroring `route_scorer.py`'s standalone
   purity). Computes agreement %, confusion by tier, and the "escalation-safety" rate
   (how often it proposes a *cheaper* tier than the label — the only economically
   risky direction is *over*-escalation, so track both).
3. **Gate on evidence:** owner flips `CORTEX_ROUTE_SCORER` for real routing only after
   the harness shows ≥ target agreement on held-out AND zero unsafe over-escalations
   on the privacy/risk rows (scorer already forces local when `privacy ≥ 0.60`,
   `route_scorer.py:197-200` — the held-out must include sensitive rows to prove it).
4. Until then, keep the flag off (default) ⇒ byte-identical static `TASK_TIERS`
   routing (`model_router.py:200,202`).

This keeps the scorer honest: it advises today (flag on = observe), and only earns
routing authority after held-out evidence — no self-grading, no
`expose_heldout_answers` (the held-out labels are owner data, never fed back into the
scorer at runtime; governance `PRE-0/governance.py:60`).

---

## 5. Fail-soft matrix (what each organ does when the brain is silent)

| Condition | Door returns | Organ fallback (caller's responsibility) |
|---|---|---|
| `halted()` / `STOP_ORGANISM` | `{"ok":False,"reason":"kill-switch"}` (`model_router.py:180-181`) | skip the brain step; tick continues |
| `frozen()` (I3) | paid declines in `organ_gate.reserve` (`organ_gate.py:66-68`) ⇒ falls to local | local answer, or deterministic path |
| paid closed (no `ACTIVATION-CORTEX-PAID`) | local (`model_router.py:237-239`) | local answer |
| no paid key | local + alert (`model_router.py:240-245`) | local answer |
| local brain off (ollama down) | `{"ok":False,"reason":"local-llm-unavailable"}` (`:266-269`) | **deterministic heuristic** (e.g. governor→dry, heart→deterministic band, cartographer→raw drift count) |

Every migrated caller MUST branch on `r.get("ok")` and have a non-LLM path. Verified
this is already how the bespoke callers behave on `None`
(`governor_epoch.py:305-313`, `doctor_setpoint.py:189-196`), so the migration
preserves their fallback semantics.

---

## 6. Flags (all default OFF; owner arms; nothing armed here)

| Flag | Role | Default |
|---|---|---|
| `ACTIVATION-CORTEX-PAID.flag` | the only paid authority for the door | owner-only |
| `CORTEX_LOCAL_FIRST=1` | secondary asks local first, quality-gated (`model_router.py:210`) | as-is |
| `CORTEX_ROUTE_SCORER` | scorer advises/routes (`model_router.py:200`) | off until held-out passes §4 |
| `ACT_GOV_LLM` / `ACT_HEART_DOCTOR` / `ACT_DEBATE` | per-organ preconditions, kept | as-is |
| `OCTOPUS_WIRE_LEAD_LLM` | lead_discovery brain note (`wiring.py:1899`) | off |
| `OCTOPUS_ZIMAN_BRANDING` | ziman brand draft via router (`wiring.py:2436`) | off |
| *(proposed)* `OCTOPUS_WIRE_CARTOGRAPHER_LLM` | let cartographer summarize drift | off (new, propose-only) |

---

## 7. What this design explicitly does NOT do (governance guardrails)

- No auto-apply, merge, deploy, or flag-toggle (`SELF_IMPROVEMENT_FORBIDDEN`,
  `PRE-0/governance.py:59-63`). The patch is a draft the owner reviews.
- Does not remove the per-organ activation flags — spend authority only narrows.
- Does not change `budget_gate`/`organ_gate` semantics, only which organ line is
  charged (via the new `organ=` arg, defaulting to the current constant).
- Does not log any prompt/content; observability unchanged (`model_router.py:291-293`).
- Numeric beats (epistemics/heart/neural/consolidation) stay brainless by design.
