---
tags: [changelog, architect]
---

# CHANGELOG — SYSTEM-BLUEPRINT

> Append-only. هر اجرای [[PROMPT-B-test-improve]] یک entry اضافه می‌کند.

## 2026-07-03 — v1 → v2 (اولین اجرای PROMPT-B)

**نمره:** v1 = **۵.۷/۱۰** (red-team مستقل، میانگین وزنی ۹ بخش: ۸/۶/۶/۵/۴/۶/۵/۶/۸) → v2 = منتظر red-team بعدی (خودارزیابی: ~۷+).

**ورودی‌ها:** تأیید مستقل (~۵۷ ادعا چک شد، ~۵۰ تأیید، ۴ خطای citation، ۲ ادعای بی‌منبع، ۳ ناسازگاری داخلی) + red-team (۶ محور + ۳ سناریو).

**تغییرات کلیدی v2:**

1. **مدل بودجه بازنویسی کامل شد** — تناقض کشندهٔ v1 ($3/روز→$90/ماه ≠ $60 hard-stop؛ mining $50/روز→$1500/ماه) حل شد: دو mode (Normal $2/روز-$60/ماه، Growth $10/روز-$300/ماه فقط با passphrase)، سقف‌ها هم‌تراز، alert پلکانی.
2. **Intent-Router rule-based اضافه شد (P11)** — باگ معماری S1: هیچ مسیری از متن آزاد به adapter نبود.
3. **قرارداد Tenant Adapter تعریف شد** — interface خواندنی `status/logs/report/audit` با credential جداگانهٔ read-only (enforced نه قراردادی).
4. **Step-up passphrase** برای فرمان‌های APPROVE_FIRST (دفاع session hijack/SIM-swap) + کلید age صریحاً off-box.
5. **Kill-switch در حلقهٔ خودبهبودی interpose شد** — چک در هر round و قبل از هر commit؛ + پیش‌شرط LIVE: held-out واقعی (اثبات قبلی فقط MOCK بود).
6. **Recovery عددی شد** — RPO ≤۱h جداول حیاتی (بکاپ ساعتی off-box)، RTO ≤۴h، restore drill ماهانه؛ DBOS journaling جلو کشیده شد.
7. **اصلاح ۴ citation غلط** (قیمت Haiku 4.5↔3.5 → G-23؛ Hetzner/Oracle/ufw → CHECKLIST_VPS_FA نه SERVER-ARCHITECTURE؛ rollback<5min → doc 10؛ sampling ≤20% → doc 09) + حذف ۲ عدد بی‌منبع جدول بودجه.
8. **پیاده‌سازی سوم خودبهبودی شناسایی و ثبت شد** (`self_improver.py` — تنها حلقهٔ الان-زنده) + ابهام «وزن» (G-24) + سیم‌کشی نیمه‌کارهٔ tracer (sink وصل، call-site غایب) + پل `pro_client.py` به معماری اضافه شد.
9. **دفاع‌های FM جدید:** checkpoint میانی در pipeline تحقیق (FM-1)، برچسب `<external_data>` در بازیابی نه فقط نوشتن (FM-3 persistence)، circuit-break روی retry همسان (FM-2)، judge سبک روی تحقیق روزمره (FM-4)، refresh فصلی ~۲۵٪ anchor (FM-10).
10. **صداقت وضعیت:** هر چیز طراحی‌شده-ولی-بدون-کد صریحاً برچسب خورد (`action_policy`، `stackctl`، mirror STOP در langar، MLflow/Mem0).

**ارجاع:** [[SYSTEM-BLUEPRINT-v1]] (دست‌نخورده) → [[SYSTEM-BLUEPRINT-v2]] (فعال). اقدام‌ها: [[BACKLOG]].
