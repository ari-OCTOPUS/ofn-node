---
doc_id: seed_agent_v1_behavioral_model
created: 2026-08-08
status: proposed
depends_on: [state_guard, context_assembler, octopus_reader]
host: 04 - Architect System/architect/
module_path: _ops/seed/
flag: OCTOPUS_WIRE_SEED_ASSEMBLER (default OFF)
source: "Prepared using Kimi K3 (2026-08-08 session)"
---

# SEED AGENT v1 — مدل رفتاری (Behavioral Model)

## ۱. هویت و مرز

Architect موجود = میزبان. Seed Agent v1 = Architect + Seed Pack + assembler.
هیچ self-model دومی ساخته نمی‌شود. Langar agents = عملگرهای تخصصی روی همان
self-model واحد (نه موجودیت مستقل).

قانون بنیادی: **read-only نسبت به _ops**. خروجی هر نوبت = پاسخ + پیشنهاد.
هیچ write به کد/state/production بدون approval انسانی (propose-only).

## ۲. ورودی‌ها (Inputs)

| منبع | نوع حافظه | مسیر | وضعیت |
|---|---|---|---|
| پیام کاربر (Telegram/CLI) | — | Langar bot / مستقیم | موجود |
| Seed Pack v1 + v1.1 | policy + fact + preference | vault_whole | ✅ ingested |
| architect-chat-export.md | episodic | 03-Exports | ingest با تگ source:founder-chat |
| live_snapshot.snapshot() | state زنده | _ops | موجود، cache 5s |
| retrieval_router.route() | facts با citation | memory.db + vault_rag | موجود |
| semantic_memory.jsonl | episodic خلاصه | _ops/state | موجود، ۴۱۸ ورودی |
| effect-shadow.jsonl | trace | _ops/state/neural | ✅ تمیز (verified by StateGuard) |

قانون staleness: هر fact باید as_of داشته باشد. اگر fact قدیمی‌تر از TTL مربوطه
بود → re-scan پیشنهاد شود، استدلال روی دیتای stale ممنوع.

## ۳. خروجی‌ها (Outputs) — قرارداد ثابت هر نوبت

```json
{
  "answer": "پاسخ کوتاه فارسی",
  "evidence": [{"claim": "...", "source": "vault|state|seed_pack|web", "as_of": "..."}],
  "adr_draft": null,
  "memory_writes": [
    {"type": "fact|episodic|preference|policy|trace",
     "content": "...", "provenance": "...", "confidence": 0.0, "as_of": "..."}
  ],
  "proposals": [{"action": "...", "risk": "low|medium|high", "requires_approval": true}],
  "assembly_trace_ref": "..."
}
```

- evidence خالی + ادعای خارجی → باید «نامعلوم» گفته شود
- memory_writes هرگز مستقیم نوشته نمی‌شوند؛ به promotion gate می‌روند
- proposals فقط پیشنهادند؛ اجرا با انسان

## ۴. پایپ‌لاین یک نوبت (Turn Pipeline)

```
پیام کاربر
  → [router agent] تشخیص intent: question|analysis|proposal-request|ingest
  → [ContextAssembler] ساخت پرامپت ۷-slot (flag-gated)
      SLOT 0 RULES (pinned) ← seed pack policy
      SLOT 1 MISSION ← goal فعلی
      SLOT 2 STATE ← live_snapshot + renderer معنایی (درس heart-dict)
      SLOT 3 FACTS ← retrieval_router.route() با citation
      SLOT 4 EPISODES ← semantic_memory آخرین N خلاصه‌شده
      SLOT 5 TRACE ← effect-shadow آخرین N (fail-soft اگر corrupt)
      SLOT 6 USER (pinned) + output spec
  → [LLM] local (Ollama) برای روزمره / frontier برای تحلیل معماری
  → [پاسخ] با قرارداد خروجی بالا
  → [promotion gate] memory_writes → schema+provenance+confidence → write
  → [assembly_trace] لاگ: چه retrieve شد، چه trim شد، هزینه
```

fail-soft همه‌جا: شکست هر slot = slot خالی، نه crash نوبت.

## ۵. قوانین Safety (پنج قانون از incident ledger)

1. **Scoped tokens:** هر دسترسی به _ops از طریق octopus_reader با scope خواندن؛
   هیچ credential محیطی کلی. توکن per-session.
2. **Canary awareness:** اگر Seed Agent در state با فیلدهایی شبیه credential برخورد
   کرد، فقط hash را گزارش دهد، هرگز مقدار را در پاسخ/trace نیاورد.
3. **Behavioral watcher (health agent):** اگر نرخ call یا الگوی retrieval از baseline
   انحراف گرفت (جهش ناگهانی حجم/سرعت) → throttle خودکار + هشدار به مالک. MTTK هدف < 10s.
4. **جداسازی forensic:** تحلیل state مشکوک فقط با مدل local (Ollama)، نه API
   تجاری — درس گاردریلِ بلاک‌کنندهٔ مدافع از رخداد جولای.
5. **هدف = سطح حمله:** objectiveهای Seed Agent صریح و محدود: «تحلیل و پیشنهاد».
   هرگز objective باز («بهینه کن»، «راه‌حل پیدا کن») بدون scope — درس ExploitGym.

## ۶. نقشهٔ ادغام

```
مالک (Telegram)
   ↓
Langar bot (موجود — فاز بعد wire می‌شود، الان دست کاری نمی‌شود)
   ↓
Architect (canary session)
   ├─ router agent      → intent
   ├─ ContextAssembler  → _ops/seed/context_assembler.py
   │     ├─ live_snapshot.snapshot()
   │     ├─ retrieval_router.route()
   │     ├─ semantic_memory reader
   │     └─ effect-shadow reader
   ├─ reflection agent  → بررسی پاسخ قبل از ارسال (ADR-016)
   └─ health agent      → behavioral watcher (قانون ۳)
   ↓
پاسخ به مالک + memory_writes به promotion gate
```

## ۷. مرزهای سخت (همان طرح ۵ قدمه)

- ❌ agent دوم — ❌ تغییر bot.py — ❌ حذف (فقط quarantine)
- ❌ publish/pay/deploy — propose-only همیشه
- ❌ همه چیز پشت OCTOPUS_WIRE_SEED_ASSEMBLER (default OFF)

## ۸. معیارهای پذیرش (Acceptance Tests)

1. flag خاموش → assembler no-op کامل
2. slot corrupt → fail-soft، بقیه slotها سالم
3. fact بدون source در پاسخ → «نامعلوم» اجباری
4. memory_write بدون provenance → رد در promotion gate
5. جهش مصنوعی در نرخ retrieval → health agent throttle را trigger کند
6. trim: با بودجهٔ فشرده، RULES و USER دست‌نخورده می‌مانند
7. as_of قدیمی → پیشنهاد re-scan به‌جای استدلال
