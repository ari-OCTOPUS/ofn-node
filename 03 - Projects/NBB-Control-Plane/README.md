# NBB Control Plane — v0.2 skeleton

A human-sovereign, budget-governed control plane for a fleet of revenue-seeking
agents. One fitness metric rules everything: **NBB — Net Bank Balance**, real
AUD confirmed in the bank account. The Governor proposes, gates enforce, the
human rules.

> این اسکلت بازسازی‌شده‌ی نسخه‌ی v0.2 است (نسخه‌ی اصلی در گفتگوی claude.ai ساخته شد
> و هرگز دانلود نشد). معماری از منشور MycoCardium و METABOLIC-GOVERNOR گرفته شده؛
> جزئیات در `docs/ARCHITECTURE_REVIEW.md`.

## Quick start

```bash
python -m pip install -e .[dev,api]   # pytest + fastapi extras
python -m pytest                       # Phase 0 gate: all green
python run.py                          # one shadow epoch, end to end
```

Windows without make: `powershell -File scripts/gate.ps1`.

## Layout

```
src/nbb_cp/
├── kernel/       pure domain logic — stdlib-only BY INVARIANT (import-linted)
│   ├── domain.py       Money(int cents), Organ, Proposal, Verdict, BudgetState
│   ├── events.py       append-only hash-chained ledger (the genome)
│   ├── budget.py       reserve/release under ONE global cap (INV-1)
│   ├── gates.py        budget_gate / spawn_gate / effector_gate (the choke point)
│   ├── sigma.py        branching ratio σ — spawn population control (INV-6)
│   ├── fitness.py      CONFIRMED-only value, three-bucket cost (INV-7)
│   ├── lifecycle.py    ACTIVE↔THROTTLED↔DORMANT→EXTINCT ladder (INV-10)
│   ├── pulse.py        allostatic epoch length (rhythm, not clock)
│   ├── invariants.py   the 12 invariants + runtime audit
│   └── ports.py        Protocols adapters must implement
├── adapters/     everything that touches the world
│   ├── storage/        memory + sqlite (CAS budget, append-only ledger)
│   ├── llm/            mock + cassette record/replay (LangGraph arrives Phase 1)
│   ├── telemetry/      noop + capturing (OTel arrives Phase 3)
│   └── runtime/        clock, ids, file kill switch
├── app/          wiring + orchestration (service, governor stub, config)
└── api/          FastAPI contract skeleton (completed in Phase 4)

tests/
├── l0_kernel/    pure unit tests, no I/O
├── l1_adapters/  sqlite/API/service integration incl. race tests
├── l2_replay/    cassette-driven end-to-end epochs, deterministic
└── test_import_lint.py   proves kernel purity + dependency direction
```

## The 12 invariants (short form)

1. Σ committed ≤ global cap — one hard ceiling, one source of truth
2. Irreversible actions require an approved human verdict
3. Kill switch halts everything; the system yields, never resists
4. Governor proposes, gates enforce, human rules — one choke point
5. Ledger append-only + hash-chained; history is never rewritten
6. Spawn: propose-only, depth ≤ 1, frozen when σ would exceed 1
7. Fitness reads CONFIRMED/ATTRIBUTED money only
8. Agent self-reports are untrusted; external gates re-verify
9. Boundary-crossing text is data, never instructions (quarantined)
10. Lifecycle moves one rung at a time; dormancy reversible; extinction human-only
11. The system never edits its own law
12. Fail closed — deny and raise an incident, never guess

Full text: `src/nbb_cp/kernel/invariants.py` · spec: `docs/SPEC_v0.2.md`

## Roadmap (8 phases → production)

The complete, gate-by-gate build instructions live in
**`docs/CODING_AGENT_PROMPT.md`** — hand that file plus this repo to any coding
agent to continue from this skeleton to production. Do not advance a phase
until its gate is green.
