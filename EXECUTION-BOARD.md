# 🐙 Octopus Execution Board — تکمیل دونه‌دونه

> تاریخ شروع: 2026-07-11  
> اصل حاکم: **هیچ secret/PII داخل چت یا فایل عمومی نوشته نشود.** فقط وضعیت، تصمیم و pointer امن.

---

## روش کار

هر پروژه با همین چرخه تکمیل می‌شود:

1. **Audit** — بررسی README/MANIFEST/adapter/OpenQuestions/DecisionLog.
2. **Owner inputs** — سؤال‌های کمینه از مالک.
3. **Contract hardening** — تکمیل MANIFEST/adapter بدون دست‌زدن به کد حساس.
4. **Registry fill** — پر کردن رجیستری‌های لازم با دادهٔ sanitised.
5. **Runbook** — ساخت دستور اجرای امن / shadow-mode.
6. **Gate decision** — تعیین اینکه read-only بماند یا وارد propose/shadow شود.
7. **Handoff** — ثبت تصمیم در DecisionLog و Next Actions.

---

## ترتیب اجرا طبق نقشهٔ قلب مشترک + لایهٔ رئیس اختاپوس

### P0 — هم‌راستاسازی با Architect/_ops
- [x] Context رئیس اختاپوس لحاظ شد: `ARCHITECT-ORGANISM-CONTEXT.md`.
- [x] Security Gate طبق Brain/HANDOFF جدید: **LIFTED 2026-07-06**؛ باقی rotationها backlog هستند، نه گیت.
- [ ] Registry / risk ladder: هر پروژه باید با جهان‌بینی Architect/_ops و URCP registry هم‌راستا شود.
- [ ] Accounting: انتخاب حسابدار / ساختار Pty Ltd.
- [ ] Project-F: GATE 0 فقط با دادهٔ حداقلی و privacy-safe.
- [ ] NBB-CP: تصمیم مالک برای تبدیل شدن به حاکم مرکزی portable یا همکارِ Architect/_ops.

### P1 — قلب مالی
- [ ] Accounting — تکمیل compliance register، جریان‌های درآمدی، tax touchpoints، runbook.

### P2 — درآمد اصلی
- [ ] Lead-نقاشی — تکمیل pipeline، portfolio taxonomy، segment، campaign shadow-mode.

### P3 — validation کسب‌وکار هدیه
- [ ] Ziman — ظرفیت، قیمت، عکس محصول، first-sale funnel، video-engine readiness.

### P4 — creator validation / Project-F
- [ ] Project-F — فقط privacy-safe و non-explicit؛ resolve G0، verdict queue، tests/runbook.

### P5 — sensing / research
- [ ] Crypto-eToro — portfolio registry، exit_rules، alerts، EdgeClassifier bug ticket.
- [ ] Mining — hardware registry، electricity rule، fleet status، coin scouting runbook.

### P6 — مغزها و ابزار
- [ ] app/NBB-CP — audit docs drift، owner commands، API entrypoint plan.
- [ ] 4d_system — decide run/no-run، Telegram setup، autonomous-run checklist.
- [ ] نقشه اختاپوس — retarget scan to current workspace; generate fresh inventory.

---

## وضعیت فعلی سریع

| بخش | وضعیت | اقدام بعدی |
|---|---|---|
| README ریشه | موجود | تبدیل به operating map |
| MANIFESTها | موجود برای همهٔ tenantها/مغزها | hardening بعد از inputs |
| adapters | برای tenantها موجود | sync با NBB-CP schema |
| Project-F manifest | golden contract موجود | استفاده به‌عنوان الگو |
| Architect/_ops context | اضافه شد | boss-layer در همهٔ تصمیم‌ها لحاظ شود |
| Security Gate | LIFTED طبق HANDOFF/Brain جدید | secret هرگز گرفته/ذخیره نشود؛ HIGH/MED rotation = backlog |

---

## قانون ثبت اطلاعات

- Secrets/API keys/seed/private keys: **هرگز اینجا نوشته نشود.** فقط `rotated: yes/no`.
- PII: فقط hash/code/summary؛ اگر لازم شد داخل فایل‌های پروژه بماند، cross-domain echo نشود.
- مالیات/قانون: تا تأیید حسابدار/مشاور، برچسب `[Unverified — advisor to confirm]`.
- اکشن بیرونی: publish/send/spend/trade/lodge/pay/create account همگی hard-gated.
