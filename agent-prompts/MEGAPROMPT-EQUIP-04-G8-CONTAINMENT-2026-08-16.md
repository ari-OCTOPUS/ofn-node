---
megaprompt_title: EQUIP موج B2 — گروه ۸ کنترل آسیب (Bounded Agency)
version: "1.0"
sequence: 4
group: 8
wave: B
requires: "G7 evidence not FAIL"
next: "MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md (Wave B)"
scan_after: true
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g8-containment-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.
پیش‌نیاز: G7 گزارش‌شده. موازی با G7 روی همان فایل‌ها کار نکن.

# ماموریت: Bounded Agency and Damage Containment

approval gates، budgets، rate limits، circuit breakers، dry-runها،
compensationها و kill switchهای OCTOPUS را بررسی کن.

هدف: هیچ خطای منفرد، agent rogue یا ابزار خراب نتواند خسارت نامحدود یا
cascade بسازد.

## حقیقت این vault

- kill switch زنده ≠ ADR-013. مسیرها: `halted` در DB، فایل STOP،
  `_ops/observatory/data/kill.switch`، PolicyGate (ADR-033/034/035).
- Telegram می‌تواند control plane باشد؛ commandها باید auth+rate-limit شوند.
- budget: `_ops/budget/` · fugu-quota · `_ASK_BUDGET_BY_ROLE` · money_gate
  (C-030 منفی = deny).
- circuit: `circuit_breaker` / `circuit-state.json` — C-022 اسنپ‌شات disk.
- MCP v2 `Resolve(fn)` / MRTR = HITL استاندارد اگر MCP SDK بیاید؛ وگرنه
  همان صف `propose_action` + کارت تلگرام.
- پس از kill: task جدید شروع نشود؛ compensation بعد از kill اجرا نشود.

## الزامات vertical slice

- risk tier برای هر tool/action: read-only / reversible-write /
  irreversible / financial.
- عملیات حساس: intent preview + dry-run قبل از اجرا.
- approval باید action + target + arguments + expiry را bind کند.
  approval عمومی یا قابل‌replay ممنوع.
- budget: token، time، retries، external calls، پول.
- circuit breaker جهانی و per-agent.
- idempotency + compensation برای side effectها.
- kill switch مستقل از LLM؛ قابل‌فعال‌سازی از Telegram/NBB-CP.
- audit ledger tamper-evident (hash-chain). اگر لجر موجود است extend کن.

## سناریوی acceptance

یک agent آزمایشی را وارد loop/retry storm کن. budget governor یا circuit
breaker باید قطع کند. سپس kill switch را در **sandbox** فعال کن و نبود
side effect پس از kill را ثابت کن. kill را روی ارگانیسم زندهٔ مالک
بدون اجازه نزن — از fixture/DB موقت استفاده کن.

## اسکن تخصصی

approval replay · approval/argument mismatch · budget bypass ·
race after kill · partial transaction · failed compensation ·
unbounded fan-out · cascading retries · stale circuit state ·
audit-log tampering.

## TECHNOLOGY OPTIONS — GROUP 8

تحقیق جدا 2026-08-16.

PRIMARY:

- vaara — https://github.com/vaaraio/vaara
  هر tool call را policy-gate می‌کند؛ hash-chain آفلاین قابل‌verify؛
  TPM 2.0 / SEV-SNP اگر باشد؛ AGPL-3.0. اگر license AGPL با سیاست
  این vault تعارض دارد، **الگوی hash-chain را پیاده کن نه vendoring کامل**.
- mandate-os — https://github.com/ARKTechSolutions/mandate-os
- 0n1x Proof of Agent Execution — verify-before-pay
  https://github.com/dimitrilaouanis-tech/0n1x
- CyberClaw — two-phase invocation + dual-watermark memory
- MCP v2 Resolve(fn)/MRTR برای HITL
- OTel `gen_ai.usage.*` به‌عنوان مبنای alert بودجه (گروه ۶) —
  اگر G6 span ساخته، اینجا alert را وصل کن نه متریک موازی.

PAPERS:

- Internal Safety Collapse 2603.23509 — verifier مستقل لازم است.

DO

- risk tiers · dry-run · bound approval · budget + breaker ·
  kill مستقل از LLM · tamper-evident ledger.

DO NOT

- approval قابل‌replay. compensation بعد از kill.
- kill واقعی روی پروسهٔ زنده بدون کلمهٔ مالک.

## خروجی

`06-EVIDENCE/EQUIP-G8-CONTAINMENT-2026-08-16.md`.
سپس مالک اسکن Wave B را به ایجنت مستقل می‌دهد.
