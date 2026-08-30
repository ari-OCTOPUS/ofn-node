# OCTOPUS Architecture Evolution Loop — DESIGN outline
stamp_local: 2026-08-23T08:45:38+10:00
author_contrib: Ios (laptop child) — ari synthesizes / owns merge gate
schema: octopus-arch-evolution-loop-design/0.1

## Goal (24h, SAFE)
Run a bounded **internal architecture-improvement loop** using doctor + evelab + simulation in a **lab worktree**.
Produce **proposed patches + tests**. **Human/ari merge gate** only.
Improve wiring, contracts, evidence hygiene, and dry-run fidelity — **not** "become smarter / self-aware".

## Hard NO
- NO money unlock (mining/crypto/accounting/paid)
- NO auto `git push` / force-push / history rewrite
- NO claims of becoming smarter, conscious, or self-aware
- NO WAVE0 actuator unlock / physical e-stop purchase lane
- NO unrestricted live Telegram `sendMessage` (flag unlock ≠ send; need send_exceptions)
- NO secrets in evidence

## YES / allowed substrate
- Lab worktree under F:/backup (or dedicated worktree) — reversible
- doctor uniqueness / EveLab doctor wire (cite `06-EVIDENCE/OCTOPUS-EVELAB-DOCTOR-WIRE-2026-08-23`)
- Simulation / dry-run transports (fake send_fn, fixture outbox)
- `live_telegram_gate` evaluate-only + SenderBridge dry refused path
- Epistemics **advisory metrics only** (no phenomenal claims)
- Patch proposals with pytest; evidence packs under `06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/`

## Loop cadence (24h sketch)
1. **Select** ≤3 GAPs from inventory (prefer disconnected/unfinished architecture, not business noon tasks)
2. **Simulate** in lab: doctor tick + evelab scenario + dry TelegramOrgan/SenderBridge gate
3. **Propose** minimal reversible patch + tests in worktree
4. **Evidence** RESULT.json (pass/fail, no secrets)
5. **Stop** for ari/owner merge gate — no auto merge/push
6. **Repeat** until wall clock 24h or 3 merges proposed

## Candidate first slices (from inventory)
1. A18 inbound Full Loop prove path (durable_loop CLOSED) — lab fake inbound first
2. Center poll-loop optional attach to `owner_gated_sender_bridge_run_once` still default-off + tests
3. C05 documentation/contract: durable outbox SoT vs canary sqlite non-SoT (no merge)
4. CONNECTOR-GAP GA4/GSC/Ads — registry hygiene only (no OAuth invent)
5. MiniApp: keep localhost documented; optional lab UI smoke without publishing URL

## Success metrics (architecture, not IQ)
- New tests green in lab
- Fewer OPEN high-severity architecture GAPs
- Gate invariants hold: `live_mode_allowed` may be true while `send_allowed` false without exceptions
- Zero money/WAVE0/force-git violations in loop journal

## Rollback
- Delete lab worktree branch / restore `.bak-*`
- Do not touch production center PID unless owner GO (already demonstrated reload path)

## References
- Gap inventory: `06-EVIDENCE/OCTOPUS-GAP-INVENTORY-2026-08-23/IOS-GAPS.json`
- TG wire fix: `06-EVIDENCE/OCTOPUS-TELEGRAM-WIRE-FIX-2026-08-23/RESULT.json`
- Center reload gate: `06-EVIDENCE/OCTOPUS-CENTER-RELOAD-TG-GATE-2026-08-23` (if present)
- Contradiction scan: `06-EVIDENCE/OCTOPUS-CONTRADICTION-SCAN-2026-08-23/CONTRADICTIONS.json`
- Continuous mission: `06-EVIDENCE/OCTOPUS-CONTINUOUS-MISSION-2026-08-23/STATUS.json`

## Open for ari
- Confirm lab worktree path naming
- Confirm max parallel slices (recommend 1–2)
- Owner GO before any center reload during loop
