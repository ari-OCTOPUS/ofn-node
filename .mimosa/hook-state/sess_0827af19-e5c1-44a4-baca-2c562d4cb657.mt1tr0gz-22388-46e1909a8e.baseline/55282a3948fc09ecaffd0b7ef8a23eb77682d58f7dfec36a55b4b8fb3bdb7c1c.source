# OWNER-GATE CARD — M2.1 FUGU-EVERYWHERE

**What you are approving (propose-only draft; nothing is applied):**
Make the shared brain reachable from every intelligent organ through one door
(`model_router.ask`). Concretely: (1) add explicit `TASK_TIERS` entries so
`chord.extract` / `tg_intent` / governor / heart / debate work-types route by intent
instead of silently falling to local; (2) add two OPTIONAL args to the door (`organ=`,
`role=`) that default to today's exact behavior — a strict superset, no existing caller
changes; (3) migrate the governor's metabolic-allocation call off a hardcoded
DeepSeek-econ client onto the door, so it can use YOUR Fugu/GLM subscription when armed.

**Safety envelope (unchanged by this change):**
- Local brain always allowed, $0. Paid strictly behind `ACTIVATION-CORTEX-PAID` — and
  the governor ADDITIONALLY still requires its own `ACTIVATION-GOVERNOR-LLM.flag`, so
  spend needs BOTH open. Authority narrows, never widens.
- Paid never bypasses organ_gate/budget_gate; reserve→settle still happens (now inside
  the door, same `ARCHITECT_SYS` budget line).
- `halted()`/`master_halted()`/`frozen()` checked at the top of every brain path.
- Logs still record only tier/model/cost/latency — never prompt/content.
- Touches none of `SELF_IMPROVEMENT_FORBIDDEN` (no merge/deploy/replicate/edit-verifier).

**What stays OFF until you decide separately:**
- `CORTEX_ROUTE_SCORER` for real routing — only after a held-out eval proves the scorer
  agrees with your labels and never unsafely over-escalates (harness proposed, not built).
- Heart (`doctor_setpoint`) and debate (`debate_loop`) migrations — same pattern, left
  for you to land after the governor migration proves out.

**Rollback:** revert `fugu-everywhere.patch` (3 files:
`cortex/model_router.py`, `budget/governor_epoch.py`,
`tests/test_llm_call_inventory.py`). The door changes are additive-default, so reverting
is clean; governor reverts to the DeepSeek-econ path verbatim. No state migration, no
data change, nothing armed.

**Before apply — run:** `_ops/tests/test_llm_call_inventory.py`,
`test_cortex.py`, `test_brain_fix.py`, `test_brain_cortisol.py`,
`test_context_fence_wiring.py`, `test_d3_provider_effect_halt.py` (green = door contract
+ fence + halt semantics intact).
