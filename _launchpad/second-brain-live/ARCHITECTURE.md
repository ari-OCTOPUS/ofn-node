# ARCHITECTURE — مغز دوم v2 (فاز ۱)

> نسخه 1.0 · 2026-07-06 · مبنا: INVENTORY.md فاز ۰ + verdictهای آری (کانال: تلگرام+واتساپ · بیزنس‌ها: زیمان/نقاشی/حسابداری · بودجه: DeepSeek ~$2-3/روز + Fugu سقف $40/ماه)

## ۱. نمای کلی — چهار لایه روی دایرکتوری‌های واقعی

```
لایه ۰  ربات ادمین ─────── control-brain/adapters/telegram_bot.py  (ارتقا: صف تأیید + /status)
لایه ۱  Core ────────────── control-brain/core/  (+ gateway.py + memory.py جدید)
لایه ۲  آداپترها ─────────── ziman-agent/ · painting-bot/ · accounting-bot/ · projectf-agent/
                              هر کدام + rokn_a.py (تحقیق) + rokn_b.py (تعامل) طبق core/contracts.py
لایه ۳  مغز تکاملی ───────── evolution/  (فاز ۴؛ دیزاین ratified در vault)
```

## ۲. جریان اصلی داده (حلقه‌ی دو رکن)

```
[زمان‌بند روزانه] → رکن A بیزنس X: gather_context (دیتای پروژه + feedback قبلی + وب/Tavily)
   → DeepSeek → Brief(فرصت/چرا/اقدام/منبع)
   → Memory (briefs + knowledge مشترک)
   → ربات ادمین: کارت بریف + دکمه‌های [👍مفید | 👎بی‌فایده]  ← حلقه یادگیری
رکن B همان بیزنس: compose(Brief) → OutboxMessage(برای صاحب بیزنس)
   → صف تأیید ادمین: [✅ Approve | ✏️ Edit | ❌ Reject]
   → پس از تأیید → Channel (تلگرام؛ واتساپ بعداً) → صاحب بیزنس
   → همه‌چیز در outbox + audit لاگ می‌شود
```

حالت خودکار per-business: فیلد `auto_send: false` در projects.yaml — فقط آری true می‌کند.

## ۳. Memory Layer — یک sqlite مشترک: `control-brain/core.db`

| جدول | ستون‌های کلیدی | نقش |
|---|---|---|
| `briefs` | id, business, title, opportunity, why, action, source, created | خروجی رکن A |
| `feedback` | brief_id, useful(0/1), note, ts | حلقه یادگیری — به prompt تحقیق بعدی تزریق می‌شود |
| `outbox` | id, business, channel, to_id, text, status(draft/pending/approved/rejected/sent), brief_id, ts | صف رکن B |
| `knowledge` | id, business(nullable=مشترک), tag, text, source, ts | پایگاه دانش مشترک یافته‌ها |
| `usage` | day, provider, tokens_in, tokens_out, cost_est | شمارنده بودجه (سقف Fugu) |

حافظه‌ی اختصاصی هر بیزنس = ردیف‌های فیلترشده با `business` + فایل‌های خود آداپتر (مثل ziman.yaml). Backup: core.db در git نیست (`*.db` ignore) → snapshot روزانه به `_Duplicates/db-backups/` توسط survival-heartbeat (فاز ۲).

## ۴. API Gateway — `control-brain/core/gateway.py`

یک کلاس واحد؛ همه‌ی آداپترها فقط از این رد می‌شوند (هیچ call مستقیم):

- `llm(prompt, tier="cheap"|"escalate")` → ‏cheap = DeepSeek ‏(`deepseek-v4-flash`، ‏OpenAI-compatible) · escalate = Fugu ‏(`api.sakana.ai/v1`، فقط با بودجه‌ی باقی‌مانده در جدول usage؛ توکن‌های orchestration هم شمرده می‌شوند)
- `search(query)` → Tavily (کلید موجود)
- `tg(token_ref).send(...)` → تلگرام با rate-limit مرکزی (۲۰ پیام/دقیقه، backoff)
- cache: پاسخ‌های تحقیق ۲۴ساعته در `knowledge` (کلید = hash پرامپت)
- هر call یک ردیف `usage` می‌نویسد؛ سقف رد شد → استثنای BudgetExceeded → کارت هشدار به ربات ادمین

## ۵. قرارداد دو رکن — `control-brain/core/contracts.py` (همین فاز نوشته شد)

هر آداپتر موظف است `ResearchEngine` و `OwnerInteractionEngine` را implement کند — امضاها در خود فایل، با dataclassهای `Brief` / `OutboxMessage` / `Feedback` و `Channel` انتزاعی (تلگرام فاز ۳، واتساپ آداپتور بعدی روی همان interface).

## ۶. مدل‌ها و هزینه (استاندارد سند: مدل/دلیل/برآورد/کش)

| مصرف | مدل | دلیل | برآورد ماهانه |
|---|---|---|---|
| رکن A (۳-۴ تحقیق/روز) + رکن B (compose) | `deepseek-v4-flash` | ارزان، ‏OpenAI/Anthropic-compatible، کیفیت کافی برای بریف | ~US$3-8 (خیلی زیر سقف $2-3/روز) |
| escalation مسائل سخت (مغز تکاملی/تحلیل عمیق) | Fugu / Fugu Ultra | پلن **Standard ‏$20/ماه** (شامل هر دو مدل؛ زیر سقف $40؛ ماه دوم رایگان تا ۳۱ جولای) | $20 ثابت |
| کش | جدول knowledge + cached-input Fugu ($0.5/M) | تحقیق تکراری نزنیم | — |

## ۷. تصمیم‌های معماری (ADR)

- **ADR-001 — یک ربات ادمین واحد:** ‏control-brain موجود ارتقا می‌یابد (authz/inline/halt دارد). ربات‌های بیزنس جدا می‌مانند (ایزوله‌سازی توکن و ریسک). ❌ رد شد: ربات ادمین جدید از صفر (نقض قانون طلایی ۱).
- **ADR-002 — polling نه webhook:** لپ‌تاپ پشت NAT، بدون دامنه/SSL؛ کد موجود polling است. اگر روزی VPS آمد بازبینی می‌شود.
- **ADR-003 — sqlite واحد (core.db) نه فایل‌های پراکنده:** ‏transaction، ‏query بین‌بیزنسی برای مغز تکاملی، backup تک‌فایلی. ❌ رد شد: Postgres (overkill روی لپ‌تاپ).
- **ADR-004 — DeepSeek اصلی / Fugu پشت budget-gate:** verdict آری (بدون Anthropic مستقیم). مسیر anthropic-compat ‏DeepSeek برای کد قدیمی حفظ می‌شود.
- **ADR-005 — abstraction کانال در رکن B:** interface واحد `Channel`؛ تلگرام اول، واتساپ (WhatsApp Cloud API — نیازمند شماره/Meta Business، هزینه per-conversation) به‌عنوان آداپتور دوم بدون تغییر رکن B.
- **ADR-006 — approve-first پیش‌فرض:** هیچ پیام رکن B بدون تأیید ادمین نمی‌رود؛ ‏auto per-business فقط با verdict. Timeout تأیید = رد (fail-closed، هم‌راستا با D-13 منشور vault).

## ۸. امنیت و پایداری

توکن‌ها فقط `.env` (gitignored) · whitelist ادمین + authz نقش‌ها (تست‌شده) · rate-limit مرکزی تلگرام · لاگ ساخت‌یافته `logs/*.jsonl` ‏append-only · health-check: ‏`/status` ادمین + survival-heartbeat موجود · هر فاز commit قبل/بعد · rollback = git + branchهای مغز تکاملی.

## ۹. نقشه فاز ۲ (بعد از تأیید آری)

1. `core/memory.py` (جدول‌ها + migration idempotent) → 2. `core/gateway.py` (+ شمارنده بودجه) → 3. ارتقای ربات ادمین: `/status` تجمیعی، کارت بریف با 👍/👎، صف Approve/Edit/Reject از `outbox` → 4. تست + گزارش غیرفنی + توقف.
