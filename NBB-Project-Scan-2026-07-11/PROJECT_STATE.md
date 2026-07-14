# PROJECT STATE & HANDOFF — read me first

> For the next agent. A verified snapshot (built from a 7-agent parallel survey of the
> live code + a hard-fact scan) of **what exists, what stage it's at, and the traps**.
> Authoritative rules live in [`CLAUDE.md`](../CLAUDE.md); this file is the *map*.
>
> **Snapshot:** HEAD `2919c69` · **207 tests green** (~1.5s, offline) · 2551 LOC source ·
> 8 commits since the reconstructed baseline.

---

## 1. What this is

**NBB Control Plane (NBB-CP)** — a human-sovereign, budget-governed, event-sourced
control plane for multiple AI "organs" (ventures). It is **component B6** ("AgentOps /
the guardian") of a larger **Second Brain Super-Governor** (8 domain brains B1–B8 over an
Obsidian vault). NBB-CP is built and hardened; the wider Second Brain is mostly plan +
Phase-1 docs.

Mental model — **the kernel decides, the app acts, the human rules**:

```
api (FastAPI, optional)      ── HTTP surface, contract-first
  └─ app  (ControlPlaneService = the ONE execution choke point, INV-4)
       └─ adapters  (storage / llm / vault / runtime / telemetry — everything that touches the world)
            └─ kernel  (stdlib-only, pure: 12 invariants, gates, ledger, domain types)
```

Dependency direction is strict and machine-enforced: **`kernel ← adapters ← app ← api`**
([`tests/test_import_lint.py`](../tests/test_import_lint.py) AST-checks it every run).

## 2. Current state

| Layer / phase | What | Status |
|---|---|---|
| **NBB-CP kernel + adapters + app + api** | the control plane (B6) | ✅ built + hardened (9 confirmed review bugs fixed) |
| **12 invariants** INV-1..12 | acceptance backbone | ✅ in `kernel/invariants.py` (audit checks 7; rest structural) |
| **Second Brain Phase 1** | 9 brain prompts + `agents.yaml` + 7 templates | ✅ docs only (`second-brain/`) |
| **Phase 2** vault scanner | read-only, resolve-based exclusion | ✅ tool built + tested — **needs the vault path to run for real** |
| **Phase 3** Fugu brain | Sakana, OpenAI-compatible, **live-verified** | ✅ end-to-end (real epoch: 3 grants, 0 violations) |
| **Phase 4–5** (vault policies, memory promotion, dashboard) + **brains B1–B8 runtime** | — | 📋 planned, not built |

Commits (newest first): `2919c69` review fixes · `6e0829e` Phase 2+3 · `219e7dc` .env/live-gate/CI/breaker ·
`3cabca9` Phase 1 · `02561ea` build plan · `48b9211` approval-TTL+evidence · `0cdaa6f` idempotency+saga · `d216a1e` skeleton hardening.

## 3. Subsystem map (verified)

### kernel/ (pure, stdlib-only — never does I/O, never reads a clock/env)
- `invariants.py` — the 12-invariant registry + `SystemView` + `audit()`. **audit covers only the 7 state-checkable invariants (INV-1,2,3,4,5,6,7)**; INV-8/9/10/11/12 are enforced structurally at their definition sites. Any non-empty audit result is *always* an incident. Two INV-1 checks: `_check_cap` (ceiling) and `_check_budget_reconciliation` (committed == Σ GRANT events).
- `domain.py` — frozen dataclasses, fail-closed in `__post_init__`: `Money` (integer cents; rejects float/bool/negative), `Proposal`, `Verdict` (carries `epoch` for TTL), `EvidencePack` (optional HITL pack), `BudgetState` (CAS `version`), `Mode`, `ProposalKind`, `RevenueState` (5 states; only CONFIRMED/ATTRIBUTED feed fitness), `GateDecision`.
- `gates.py` — the 3 pure decision fns. **`effector_gate` order is load-bearing: kill → verdict → mode.**
- `budget.py` — `reserve`/`release`/`headroom`; every derived state bumps `version` (optimistic-lock CAS). "load-bearing, do not simplify away."
- `events.py` — append-only hash-chained ledger (the "genome"). `compute_hash` body `seq|ts|kind|json|prev_hash` is a **wire contract** (changing it invalidates every chain); `canonical_json` uses `ensure_ascii=False` (Persian/unicode survives); `next_event` is pure (caller supplies ts).
- `sigma.py` — branching-ratio (INV-6). **Use `prospective_sigma_from_events` (post-one-more-spawn) for gating, not `sigma_from_events`**, or population overshoots by one. `SIGMA_LIMIT=1.0`.
- `fitness.py`, `pulse.py`, `lifecycle.py`, `ports.py` (the Protocols — the only doorway out), `errors.py` (each error carries `.invariant`).

### adapters/ (implement the ports; wired only in `app/bootstrap.py`)
- `storage/` `memory.py` + `sqlite.py` — CAS budget + append-only ledger. **sqlite's stored payload TEXT is not the hashed representation** (it json.dumps with spaces; the hash uses compact `canonical_json`).
- `llm/` `mock.py`, `cassette.py` (`RecordingLLM` wraps live + records, `ReplayLLM` fails closed on a miss), **`fugu.py`** — Sakana OpenAI-compatible, stdlib `urllib`, **`_NoRedirect` opener (key-exfil guard: urllib re-sends `Authorization` on 3xx with no same-host check)**, whole 200-body parse in one fail-closed guard.
- `vault/scanner.py` — **read-only** markdown scanner; exclusion is **resolve-based** (a symlink/junction into a restricted folder is still excluded). `runtime/system.py` (clock/idgen/`FileKillSwitch`), `telemetry/noop.py`. Test doubles (`FixedClock`, `ManualKillSwitch`, `CapturingTelemetry`) live *inside* the production adapter modules by design.

### app/ (the heart)
- `service.py` (596 LOC) — **`ControlPlaneService.execute` is the single runtime choke point.** It calls pure `effector_gate` then does all impure work: `RLock`, CAS retries, **idempotency** (`self._executed`, rebuilt from the genome), **approval-TTL** staleness refusal, **saga compensation** on GRANT-append failure, `run_audit`, `rebuild_projections` (soma is disposable), `trip_breaker_if_unsafe` (opt-in circuit breaker). Keep this orchestration OUT of the kernel.
- `governor.py` — `StubGovernor` + `run_demo_epoch` (the deterministic-in-shadow demo loop). `bootstrap.py` — `build_service`/`build_llm`. `config.py` — `from_env`, `.env` loader (utf-8-sig, BOM-safe), M5 live-gate.

### api/ (`http.py`, optional `[api]` extra)
Contract-first FastAPI: health/state/audit/proposals/verdict/execute/kill/resume. **No server entrypoint yet** (`api/__init__.py` empty; no module-level `app`; uvicorn declared but unused) — you cannot `uvicorn nbb_cp...` today. `FailClosedError` maps to 422 on create but 404 on verdict/execute (route-specific). Read surface is minimal (`/state`, `/audit`).

## 4. The 12 invariants (never delete/weaken — INV-11)

1 cap ceiling · 2 human verdict for irreversible/spawn · 3 kill halts all · 4 one choke point ·
5 append-only hash-chained ledger · 6 spawn depth≤1 & σ≤1 · 7 fitness = CONFIRMED/ATTRIBUTED money only ·
8 self-reports untrusted · 9 external text is quarantined data · 10 lifecycle one-rung, extinction human-only ·
11 system never edits its own law · 12 fail closed. Full text in `kernel/invariants.py`.

## 5. How to run

```bash
python -m pytest                 # 207 green (83 l0 + 102 l1 + 5 l2 + 17 import-lint); ~196 without the api extra
python run.py                    # shadow demo (no keys, no network, in-memory)
NBB_LLM_MODE=fugu python -c ...   # live Fugu brain (key from .env); run_demo_epoch runs a governor epoch in shadow
python scripts/scan_vault.py "<obsidian vault path>"   # read-only scan; restricted folders excluded by default
```
Env: `NBB_MODE` (live needs `NBB_ALLOW_LIVE=1`), `NBB_LLM_MODE` (mock|cassette|fugu), `FUGU_API_KEY` (in gitignored `.env`), `NBB_GLOBAL_CAP_CENTS`. Backups: `F:\Black Box` + Desktop.

## 6. Governance the next agent MUST follow

- **IMPROVE-DON'T-REWRITE** ([doctrine](SELF_IMPROVEMENT_DOCTRINE.md)): additive only; preserve old versions; don't change interfaces; **any change >30% of a module, any interface change, or any old-version removal = "rewrite" → ask first**, showing **Current / Delta / Preserved / Rollback**.
- **CLAUDE.md STRICT RULES**: invariants are sacred (INV-11); kernel stays stdlib-only; one choke point; fail closed; money = integer cents; **secrets never enter repo/ledger/cassette** (the Fugu key lives in gitignored `.env`); if a decision isn't derived from spec+invariants, **stop and ask**; suite always green (new behavior ships with its test; a bug gets its regression test first).

## 7. Gotchas the survey flagged (non-obvious)

- **Two "live" concepts, easy to conflate:** `llm_mode="live"` is just an *alias for "fugu"* (builds the real brain, ungated); `Mode.LIVE` (execution) is separate and gated by `NBB_ALLOW_LIVE=1`.
- **Budget reservation is REAL in shadow mode** — `_execute_grant` commits via CAS in both modes; only the outward *effect* is simulated.
- **`execute` is idempotent** (replay → 409 / INCIDENT `replay_refused`), but **`POST /proposals` is NOT** — a client retry double-ledgers a PROPOSAL (Phase-4 item).
- Tests reach into privates on purpose (`service._proposals[...].evidence`); the `view()` helper defaults `committed=0` because it must reconcile with GRANT events; the symlink exclusion test self-skips where symlinks aren't permitted (Windows w/o privilege) — a "pass" there may be a skip.
- Regression tests double as documentation — **read their docstrings before touching code.**

## 8. Known drift & open items (fix/decide before trusting the older docs)

- **DOC DRIFT — the descriptive docs lag the code.** `CODING_AGENT_PROMPT.md`, `SPEC_v0.2.md`, `SKELETON_HARDENING.md` say **"LangGraph"** and **"150/171 tests"**; the code actually ships the **Fugu/Sakana** adapter and **207 tests**. Two unreconciled roadmaps exist (the 8-phase `CODING_AGENT_PROMPT` vs `SECOND-BRAIN-BUILD-PLAN`); the build followed the latter. **Trust the code + this file over the older prose.**
- **Blocked on the owner:** the **Obsidian vault path** (to run Phase 2 for real) and per-phase approval for anything touching private People/Crypto-eToro/Telegram data.
- **Open build items:** Phase 4 (vault policies §14 + memory-promotion pipeline), Phase 5 (dashboard), the B1–B8 runtime, `POST /proposals` idempotency, and an actual API server entrypoint.

## 9. Onboarding order for the next agent

1. This file → 2. [`CLAUDE.md`](../CLAUDE.md) (rules) → 3. `kernel/invariants.py` (the law) →
4. `app/service.py` (the choke point) → 5. `tests/` (executable spec; run `pytest`) →
6. [`SECOND-BRAIN-BUILD-PLAN.md`](SECOND-BRAIN-BUILD-PLAN.md) (where it's going).
Then: improve, don't rewrite; keep it green; ask before the big/irreversible.
