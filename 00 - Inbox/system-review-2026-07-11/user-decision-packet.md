---
type: proposal
status: draft
tags: [decision, human-in-the-loop, approval, handoff]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[00 - Inbox/system-review-2026-07-11/implementation-backlog]]"
  - "[[00 - Inbox/system-review-2026-07-11/risk-register]]"
---

# User Decision Packet — READ-ONLY (2026-07-11)

> 5 high-leverage decisions only. Each in your Telegram packet format. Nothing proceeds without your explicit answer — I stay propose-only until you say "go" per item.

## D1 — Fail-closed HumanAppendGuard (R1 / your own #1)
- **[TYPE]** approve
- **[CONTEXT]** `is_human=1` is forgeable when the guard is unconfigured (`human_append_guard.py:78-80` → passthrough); a forged human verdict advances the genome mortal age-tick.
- **[WHY NOW]** it's the only *live exploitable* security gap, and it's already your #1 — just never green-lit.
- **[OPTIONS]** 1) build strict mode + turn on · 2) build strict + ship **shadow-alert only** first · 3) reject · 4) more analysis · 5) defer
- **[RECOMMENDATION]** **Option 2** — additive `strict` flag, ship in shadow-alert (log "would-deny") one cycle, then flip. Zero behavior change until you flip; reuses as the template for D2.
- **[CONSEQUENCE if no answer]** gap stays open; any code path can keep forging human verdicts.

## D2 — Live money kill-switch, shadow-first (R2 / your #4)
- **[TYPE]** approve
- **[CONTEXT]** the drawdown breaker (`spike_pct=25`) is only asserted in tests; nothing halts live.
- **[WHY NOW]** it guards *money*; a test-only breaker is a breaker that never fires.
- **[OPTIONS]** 1) build enforcer, shadow-count first · 2) build + enable now · 3) reject · 4) defer
- **[RECOMMENDATION]** **Option 1** — enforcer logs would-halt behind `HH_DRAWDOWN_ENFORCE=off`; you watch shadow, then flip.
- **[CONSEQUENCE if no answer]** no autonomous drawdown protection near live money.

## D3 — Clear git locks + run live hygiene (R3) — YOUR HANDS
- **[TYPE]** blocked (owner-only)
- **[CONTEXT]** stale AV `.git/*.lock` files intermittently wedge git; ~113 uncommitted live entries; `RUN-CLEANUP` never run on live.
- **[WHY NOW]** your control plane's own backup/push path is unreliable — a durability risk I *cannot* fix (correctly denied `.git` + live-business writes).
- **[OPTIONS]** 1) you clear locks + run cleanup now · 2) you do it later (accept risk) · 3) tell me exactly what you want staged so it's one click
- **[RECOMMENDATION]** **Option 1** — `Remove-Item F:\backup\.git\*.lock` then `_ops/maintenance/RUN-CLEANUP-2026-07-11.bat`; verify a clean push.
- **[CONSEQUENCE if no answer]** backups may stay silently broken; one disk event = real loss.

## D4 — Promote which "built-but-shadow" capabilities? (R11)
- **[TYPE]** approve (per item)
- **[CONTEXT]** several capabilities are built + tested but shadow/flag-gated: HeartState telemetry (`HEARTSTATE_SHADOW`), heart precision-weighting (`HEART_PRECISION_WEIGHT`), soft-WTA ignition (`IGNITION_SOFT_WTA_LIVE`), incident/#13 wiring.
- **[WHY NOW]** capability debt: "built" ≠ "live"; each needs a deliberate promote.
- **[OPTIONS]** 1) promote telemetry-only (HeartState) — safest · 2) promote a specific one (name it) · 3) keep all shadow · 4) defer
- **[RECOMMENDATION]** **Option 1** — `HEARTSTATE_SHADOW=1` is telemetry (regulator, never commander); promote it first, keep behavior-affecting ones (precision-weight, soft-WTA-live) shadow until you decide.
- **[CONSEQUENCE if no answer]** capabilities stay dark; no harm, but no value realized.

## D5 — Web-grounded 2027 benchmark pass?
- **[TYPE]** notify
- **[CONTEXT]** this review's competitive/2027 comparison is `INFER` from my training knowledge (cutoff Jan 2026), not fresh web data. Your `2027 Standards Base & Backlog` already did a real 6-pillar audit.
- **[WHY NOW]** to ground the routing/UI/observability dimensions against current 2026-2027 vendor patterns before you invest in B5/B6.
- **[OPTIONS]** 1) yes, run a scoped web-research pass (RESEARCH mode) extending your 6-pillar audit · 2) no, my knowledge-based review is enough · 3) later
- **[RECOMMENDATION]** **Option 3 (later)** — do it right before B5/B6, not now; it's not blocking B0–B4.
- **[CONSEQUENCE if no answer]** B5/B6 proceed on `INFER`-level anchors (still fine, just less externally validated).

---
**My single most important ask:** answer **D3** first (durability), then **D1** (security). Everything else can wait.
