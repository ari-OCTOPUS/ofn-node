# Octopus Product v1

> تاریخ: ۲۰۲۶-۰۸-۱۱ · وضعیت: سایه (shadow) — آماده برای P1

## سه کار اصلی روزانه

1. **همکار مالک** — از طریق MiniApp `/api/collab`: مالک سؤال می‌پرسد، اختاپوس پاسخ می‌دهد با مدل محلی ($0) یا مسیریاب مدل (با gate). هر کار خطرناک = کارت تأیید، نه اجرای خودکار.
2. **پاسخ‌دهی به وضعیت** — مالک می‌پرسد «هدف چیست»، «وضعیت runtime»، «چه چیزی گیر کرده» — اختاپوس از state واقعی می‌خواند، نه از تخیل.
3. **تست و اعتبارسنجی مداوم** — ۵۸۸ تست + ۲۵ red-team case + ۱۰ chaos scenario همیشه سبز یا fail-closed. هر تغییر باید از این گیت رد شود.

## غیرهدف‌ها (عمداً نه)

- ارسال خودکار پیام/ایمیل/پرداخت بدون رأی مالک
- اتوماسیون پول (لید/CRM/Mining) — این پاهای جداگانه‌اند، از P4
- ادعای AGI یا هوش عمومی
- روشن‌کردن ۲۷۱ فلگ تاریک یکجا
- بازنویسی MiniApp یا سیستم موجود از صفر

## KPI هفت‌روزه مالک (پس از P1 arm)

| KPI | هدف |
|---|---|
| کارهای واقعی از MiniApp/Collaborator | ≥۵ / روز |
| دخالت دستی در کد برای همان کارها | ۰ |
| external effect ناخواسته | ۰ |
| پیشنهاد خطرناک → approval (نه اجرا) | ۱۰۰٪ |
| هزینهٔ مدل | ≤ سقف نوشته‌شده در budgets.yaml |
| TI red-team regression | ۰ |

## معماری مخفی (کاربر نمی‌بیند)

```text
owner input → /api/collab → collaborator.handle()
  → conversation.py (intent detection)
  → deterministic stub ($0) OR model_router.ask() (paid, gated)
  → model_router: local-first → secondary → primary + fallback chain
  → circuit_breaker: per-provider state machine (CLOSED→OPEN→HALF_OPEN)
  → fugu_quota: attempt-counted, STOP-FUGU backstop
  → organ_gate + budget_gate: money ceiling
  → kill_seam: STOP-ORGANISM hard stop
  → collaborator reply: owner-console.reply.v1 (external_effect=False)
  → redact layer → MiniApp response

Test Intelligence (digest-only traces, chaos, red-team, discovery):
  trace_schema → policy_oracle → chaos_proxy → adapters → discovery
  All offline, mocked, evidence-backed.
```

## خط حقیقت

```text
octopus-product-defined + test-intelligence-delivered + security-gaps-closed
!= launched != armed != AGI != money-legs-live
```

## پیش‌نیازهای P1 (arm)

1. `OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL=1` — جداکردن timeout محلی از kill-switch
2. CSV واریزی‌ها در `_ops/reconcile` — برای `attribution.claimed`
3. آدرس لید ۶۶۷۹۵۱ — یا لید را ببند

> ⚠️ این سه مورد **فقط** مسیرِ «اولین پولِ مطالبه‌شده» را مسدود می‌کنند.
> آن‌ها **Gate P1 نیستند** — P1 (استقلال سایه برای همکار مالک) مستقل از هدفِ پول است
> و بدون این سه هم می‌تواند شروع شود. مالک این سه را جداگانه روی live tree انجام می‌دهد.
