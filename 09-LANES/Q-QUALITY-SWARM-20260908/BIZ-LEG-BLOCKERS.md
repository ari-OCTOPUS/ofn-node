---
type: report
lane: Q-QUALITY-SWARM-20260908
created: 2026-09-08
gov: V8
ladder: L2
---

# BIZ-LEG-BLOCKERS — one unit blocker per leg

Rule: one blocker per leg. Class A/A2 only if a single code action (no owner vote) would remove it. If the unit blocker needs an owner vote, mark **OWNER_DECISION**, not TODO. No guesses.

Legs named in the prompt: **ziman**, **painting**, **studio**.

## painting → class A2

| Field | Value |
|---|---|
| Blocker | Public `/Contacts/` form is **not** an organism store: `website_form` / `OCTOPUS_LEAD_FORM_SENDERS` default empty, so the consented-inbound path is unreachable. A store-only intake that records a lead with `baseline_action=0` is missing on the organism side. |
| Class | **A2** (local store, no send, no pay) |
| Why not Z | Wiring a localhost/store path does not require an owner vote. TLS renew / GBP remain separate owner items and are **not** this row. |
| Evidence | `03 - Projects/Lead-نقاشی/WHY-NO-REAL-LEADS-2026-08-01.md` #7 (HTTP GET `/Contacts/`: 1 form, 7 inputs, not connected; `OCTOPUS_LEAD_FORM_SENDERS` default `""`). `03 - Projects/Lead-نقاشی/PROJECT.md` Progress still lists «فرم وب‌سایت». |
| Contradiction (open) | Same WHY-NO-REAL-LEADS file says the **site already has a form**; PROJECT.md (updated 2026-09-07) still lists the form as remaining. Both kept. `resolution: null`, `status: open`. A2 here = **organism store-only intake**, not a claim that `/Contacts/` HTML is absent. |
| A2 action | `painting_lead_form/` in this lane: persist one realtime lead, `baseline_action=0`. |

## ziman → OWNER_DECISION

| Field | Value |
|---|---|
| Unit blocker | First paid order / `CASH_first_order` (market + owner checkout). No single class A/A2 action in this vault opens VERIFIED_CASH. |
| Class | **OWNER_DECISION** (not TODO) |
| Why not A | Domain renew is owner. Capacity units/week is owner (`Ziman Galerry/PROJECT.md` Open blockers). `shelf1_readiness_probe.py` is an evidenced **missing file** (`07-HANDOFF/BIZ-LEGS-PLAN-2026-09-05.md`; glob this session = 0 files) but a probe does not complete the money path. Treating it as *the* unit blocker would be a guess. |
| Domain note | `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` §1 still lists `ziman-gift.com` NXDOMAIN; later blocks on the same day say `.com.au` is live vs local-cache 404. Both values recorded in `WIKI-DRIFT-REPORT.md`. Not used as an A fix. |

## studio → OWNER_DECISION

| Field | Value |
|---|---|
| Unit blocker | GATE 0 open: partner residence / branch A/B not closed; `gate_stamp_go: false`. Organism: `studio_pf.live=false`, `outward_execution=false`. |
| Class | **OWNER_DECISION** (GATE 0 / GATE-STAMP) |
| Why not A | `_ops/state/ORGANISM-STATE.json` `business_legs.studio_pf`: «عمداً قفل — GATE 0 باز است و مهرِ انسانیِ GATE-STAMP-GO روی دیسک نیست». `03 - Projects/اونلی فنز/PROJECT.md` Open blockers: GATE 0. |
| Not this row | PROJECT.md Next actions lists LearningBridge default as «بی‌نیاز به گیت». That is class A **work**, not the unit blocker of the leg. |

## Summary

| Leg | Unit blocker | Class | A/A2 PR in this lane? |
|---|---|---|---|
| painting | store-only lead intake unconnected | A2 | yes |
| ziman | first paid order / cash gate | OWNER_DECISION | no |
| studio | GATE 0 / GATE-STAMP-GO | OWNER_DECISION | no |
