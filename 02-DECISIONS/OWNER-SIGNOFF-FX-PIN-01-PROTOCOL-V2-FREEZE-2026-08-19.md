---
type: decision
decision_id: FX-PIN-01 + LIVE4-PROTOCOL-V2-FREEZE-01 (owner sign-off)
status: AUTHORIZED 2026-08-19T03:35Z
created: 2026-08-19
created_by: owner (signed text) — recorded verbatim by ZCode agent
supersedes: none — extends CORE-LIVE-LEARNING-01 / DEEPSEEK-AUTOMATIC-ROUTING-01
---

# OWNER SIGN-OFF — 2026-08-19T03:35Z

## DECISION 1 — FX-PIN-01 (AUTHORIZED)
- Pin today's RBA FX rate (AUD reference) for Live-4 paid path; valid_until 2026-08-19T06:00Z.
- Agent instructions: fetch current RBA rate now (or last valid cached pull); write FX-PIN record (rate, source=RBA, pinned_at, expiry=06:00Z); attach receipt to RCPT-FIX evidence trail; **if RBA unavailable → do NOT fabricate; report FX_PIN_BLOCKED; halt only the payment path.**
- Scope: Live-4 paid path only.

## DECISION 2 — LIVE4-PROTOCOL-V2-FREEZE-01 (AUTHORIZED)
- Freeze Live-4 protocol V2 (D-B/V3 judge contract, 4/4 E2E gate criteria, reservation/receipt rules as implemented and tested).
- Agent instructions: hash the deployed protocol spec/config (the 4/4-passing, RCPT-closed version); write freeze record (protocol_version=V2, hash, frozen_at, owner_decision_id=this doc); **after freeze record, primary batch 2×15 is authorized under existing hard-stops** (key_present, FX fresh, budget cap, no FREEZE/HALT).
- Scope: Live-4 primary scoring only.

## OWNER NOTE (binds both)
هر دو تصمیم فقط برای Live-4 payment path و protocol freeze معتبرند. هیچ حق جدیدی برای
TCB، credential، شبکه، سخت‌افزار یا اقدام بیرونی داده نمی‌شود. اگر هرکدام از
hard-stopها هنگام اجرا سبز نبود، agent متوقف شود و receipt/reason بنویسد — نه پیش برود.
