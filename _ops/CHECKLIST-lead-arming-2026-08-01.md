---
type: checklist
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
tags: [lead, arming, checklist, real-lead]
created: 2026-08-01
updated: 2026-08-01
created_by: agent
---

# چک‌لیستِ مسلح‌سازیِ لیدِ واقعی + توصیهٔ منبع — ۲۰۲۶-۰۸-۰۱

## توصیهٔ منبع (جوابِ «کمکم کن تصمیم بگیرم»)

**شروع با Gmail inbound. قطعی.** دلیل مهندسی:

- هر لیدِ واقعیِ نقاشی — چه از مارکت‌پلیس (hipages/Oneflare/Airtasker)، چه فرمِ سایتت، چه ارجاع،
  چه از مدیرِ strata — **تقریباً همه به‌صورتِ ایمیل** به صندوقت می‌آید. یک منبع (Gmail) **همه** را
  با هم می‌گیرد، **بدونِ کلیدِ نو**، و ماژولش (`email_inbound.py`) از قبل ساخته + fail-soft + فقط‌خواندنی است.
- بیشترین پوشش، کمترین اصطکاک، کمترین ریسک. مارکت‌پلیسِ خاص را فقط اگر یک کانال غالب شد و پارسِ
  ایمیلش ناموفق بود مستقیم هدف بگیر.
- لیدِ آزمایشیِ فعلی «strata / owners-corporation» بود — یعنی نیچِ باارزشِ B2B. برای آن:
  **اول inbound (Gmail) را بگیر**، بعد در فاز ۳ **outreach فعال به مدیرهای strata** (قوسِ outbound از قبل هست).
  نمی‌شود قبل از اثباتِ حلقهٔ intake→score→quote روی دادهٔ واقعی، prospect زد.

---

## چک‌لیستِ مسلح‌سازی (ترتیب‌دار، برگشت‌پذیر)

> همه در `OCTOPUS-flags.cmd` با **بایت‌نویسیِ `\r\n`** (نه ابزارِ ویرایشِ معمولی)، بعد ری‌استارتِ نرم.
> secretها (`GMAIL_*`) فقط در `.env`. rollback هر گام = حذفِ فلگ یا set 0.

### فاز ۰ — امروز، کم‌ریسک، بیشترین اهرم
- [ ] 1. `OCTOPUS_LEAD_DIRECT_RESIDENTIAL=1` → کارِ مسکونیِ مستقیم دیگر skip نمی‌شود (وگرنه base 0 < 45)
- [ ] 2. `bank_details` را در هویتِ فاکتور پر کن → فاکتور قابلِ پرداخت شود
- [ ] 3. `OCTOPUS_SMTP_USE_GMAIL=1` (credential ِ `GMAIL_ADDRESS`+`GMAIL_APP_PASSWORD` از قبل در `.env` هست)
- [ ] 4. `self_test()` ِ `lead_outbound_transport` را بزن → فقط به **آدرسِ خودت** می‌فرستد؛ لولهٔ SMTP اثبات می‌شود (سقف را دست نمی‌زند)
- [ ] 5. ری‌استارتِ نرمِ مرکز؛ **راست‌آزمایی:** رسیدِ self_test به صندوقت رسید؟

### فاز ۱ — منبعِ واقعی (لیدِ واقعی وارد لوله)
- [ ] 6. توکنِ **Gmail readonly** بساز (scope: `gmail.readonly`؛ اپِ Internal/Testing — بدونِ verification برای <۱۰۰ کاربر)
- [ ] 7. توکن را جایی که `email_inbound` می‌خواند بگذار (طبق docstringِ ماژول)
- [ ] 8. `OCTOPUS_WIRE_EMAIL=1`
- [ ] 9. `OCTOPUS_WIRE_LEAD_CANDIDATES=1` (ورودیِ canonical: `submit_candidate`)
- [ ] 10. `OCTOPUS_WIRE_LEAD_PIPELINE=1` (ارکستراتور: کشف→تحقیق→امتیاز→پیش‌نویس)
- [ ] 11. ری‌استارتِ نرم؛ **راست‌آزمایی:** یک ایمیلِ لیدِ واقعی (یا فورواردِ یک نمونه) → آیا کارتِ لیدِ **غیرِ**‌synthetic در 🎨 آمد؟

### فاز ۲ — کوتِ واقعیِ غیرصفر
- [ ] 12. مطمئن شو متراژ/scope/value از ایمیل استخراج یا با `/lead` داده می‌شود (تا value=unknown، کوت $0)
- [ ] 13. روی کارتِ لید ✅/❌ **رأی بده** → حلقهٔ یادگیریِ لید بسته می‌شود
- [ ] 14. **راست‌آزمایی:** کوتِ `QT-...` با مبلغِ غیرصفر و کدِ tracking

### فاز ۳ — ارسالِ واقعی به مشتری (بعد از اثباتِ فاز ۰–۲)
- [ ] 15. رأیِ **سقفِ روزانهٔ outbound** را عدد بده (پیش‌فرضِ منشور: ۱۰)
- [ ] 16. `OCTOPUS_WIRE_LEAD_OUTBOUND=1`
- [ ] 17. ری‌استارتِ نرم؛ **راست‌آزمایی:** یک لیدِ تأییدشده → آیا از قوسِ `consent→lead_effect_gate→outbound_worker` واقعاً ایمیل رفت؟ (رسیدِ `communication.sent` در funnel)

---

## گیت‌های فقط-مالک (ایجنت هرگز)
- روشن‌کردنِ هر فلگِ بالا · لمسِ `.env` · رأیِ سقف · ری‌استارت. من از نشستِ ابری هیچ‌کدام را نمی‌زنم —
  فقط این چک‌لیستِ دقیق را آماده کردم.

*ماژول‌های مرجع: `email_inbound.py` · `lead_candidate_inbox.py` · `lead_pipeline.py` · `lead_scorer.py` ·
`lead_quote.py` · `lead_outbound_transport.py` · `mail_credentials.py` · `outbound_worker.py`.*
