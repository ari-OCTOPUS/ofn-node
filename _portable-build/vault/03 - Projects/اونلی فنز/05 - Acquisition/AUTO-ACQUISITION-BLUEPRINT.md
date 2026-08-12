---
type: strategy
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[ACQUISITION-ENGINE-2026-07-05]]"
  - "[[01 - Strategy/Identity/BRAND-CHARTER]]"
  - "[[CLAUDE]]"
tags: [project-f, acquisition, automation, dual-ui, foundation]
aliases: ["Auto-Acquisition Blueprint", "پایهٔ بازاریابی خودکار"]
---

# AUTO-ACQUISITION + DUAL-UI — بلوپرینتِ پایه (propose-only)

> رأی مالک: «بازاریابی خودکار، مشتری پیدا کن، به pageهای واقعی وصل شو، مشتری هدایت کن، پست بذار؛ من از تلگرامِ خلوت (اختاپوس، ادمین) هدایت کنم؛ خالق یک UIِ خوشگلِ جدا داشته باشد. همه پایه‌ها.»
> این سند **پایه‌ها را می‌گذارد** بدونِ عبور از هیچ گیت. موتور روی داشته‌های موجود بنا می‌شود (بازنساخته نمی‌شود).

## ۰. «خودکار» یعنی چی اینجا (صادقانه)
تا **بستنِ GATE 0 + ساختِ اکانت‌های واقعی توسطِ مالک + verdict**، این‌ها **قفل‌اند** (قواعدِ قفل‌شدهٔ خودت + ToS پلتفرم‌ها + قواعدِ عاملِ من): publish/پستِ عمومی · DM · اتصال/لاگین به pageهای واقعی · ساختِ اکانت · spend. عامل هیچ‌کدام را نمی‌تواند «خودکار» روشن کند.
**بیشترین خودکاریِ امن = «one-tap-to-live»:** موتور مدام **auto-draft + auto-schedule + auto-queue** می‌کند (قیف همیشه پر و آماده)؛ تنها لمسِ انسانی = یک ✅ در تلگرام؛ سپس منتشر می‌شود. سوییچِ «کاملاً hands-off» **مالِ توست** پس از GATE 0.

## ۱. خطِ لوله (state machine) — چی auto، چی gated
```
[AUTO] plan_week (brain/acquisition) ─▶ [AUTO] draft content/caption/hook (dual_brain_v3)
   ─▶ [AUTO] schedule + enqueue (per-channel cadence: Reddit ۶۰٪ · X ۳۰٪ · SFW ماه۳)
   ─▶ 🟡 [ONE-TAP] owner approve در تلگرامِ اختاپوس (ok/no/later:<id>)
   ─▶ 🔴 [GATED] publish/DM  ← افکتور خاموش تا GATE 0 + اکانت + verdict + ۱ هفته shadow
   ─▶ [AUTO] KPI ingest (کلیک/free/paid/درآمد) ─▶ [AUTO] feedback_loop → یادگیریِ tag/زمان
```
- **AUTO (همین حالا مجاز، $0، offline):** plan_week · draft · schedule · queue · KPI-loop · learning. (brain/acquisition + dual_brain_v3 موجود.)
- **ONE-TAP (انسانی، سبک):** approve/reject در تلگرام — تنها نقطهٔ تصمیم.
- **GATED (فقط بعد از GATE 0):** publishِ واقعی · DM · اتصالِ page · spend. افکتورها built-but-OFF.

## ۲. نگاشت به داشته‌های موجود (بازاستفاده، نه بازنویسی)
| نیاز | داشتهٔ موجود |
|---|---|
| مغزِ اکتساب (plan/analyze/learn) | `brain/acquisition.py` (AcquisitionBrain: analyze/plan_week/feedback_loop/suggest_next_action) |
| draftِ محتوا/کپشن/هوک | `brain/dual_brain_v3.py` + بانکِ ۳۰ هوک ([[research-results/P4-persona-hooks]]) |
| قیفِ ۵لایه + استک + KPI | [[ACQUISITION-ENGINE-2026-07-05]] |
| UIِ ادمین (اپراتور A) | `langar/langar_bot.py` (/status /gates /verdicts /drafts /kpi /report /kill …) |
| UIِ خالق (C) | `studio/saba_studio.py` (s:new/drafts/cal/ppv/stats/cap … · /halt) |
| درفت‌های آمادهٔ گیت | `drafts-awaiting-gate/` (x-profile, link-hub-copy, ppv-ladder, tracking-link) |
| هویتِ برند/claims | [[01 - Strategy/Identity/_INDEX|Identity pack]] |
**گافِ واقعی = چسبِ integration** (queue + approve + KPI-loop) + پرداختنِ دو UI + مدلِ افکتورِ گیت‌دار. کد از صفر لازم نیست.

## ۳. دو رابطِ کاربری
### ۳.۱ ادمین (تو / A) — تلگرامِ مرکزیِ اختاپوس، خلوت، content-free
از طریقِ `telegram_center` (کلیدِ `studio_pf`، aliasِ «استودیو» — containment). فقط تصمیم و دید:
`/pf_status` (قیف یک‌نگاه) · `/pf_queue` (صفِ درفت، هر کدام ok/no/later) · `/pf_kpi` · `/pf_verdicts` · `/pf_go_live` (گیت‌دار) · `/halt_pf`. **هیچ هویت/رسانه؛ کدِ «Project-F».** یک‌تاپ = approve.
### ۳.۲ خالق (C) — باتِ جدا، ایزوله، خوشگل و انگیزه‌بخش
توکن/chat-id **جدا**؛ metadata-only؛ **هیچ رسانهٔ خام؛ هرگز روی اختاپوسِ مرکزی**. تجربه: گرم، تحسین‌گر، کارش را جشن می‌گیرد و او را ستارهٔ کار می‌کند — «streak»، «today's spotlight»، «تو این هفته X ست ساختی 🌟»، پیش‌نمایشِ زیبا، تشکرِ شخصی. (طراحی برای انگیزه و حسِ ارزش — بدونِ هیچ برچسبِ شخصیتی در هیچ فایل.) مرزِ صبا (فقط پا) و /halt همیشه حاکم.

## ۴. مدلِ افکتورِ گیت‌دار (built-OFF)
هر افکتورِ بیرونی پشتِ فلگِ خاموش + گیت (مثلِ الگوی لیمب):
`PF_LIVE_PUBLISH` · `PF_LIVE_DM` — پیش‌فرض ۰. تا ۱ نشوند، publish/DM فقط شبیه‌سازی/صف است.
**پیش‌شرطِ فعال‌سازی:** GATE 0 بسته (Branch A) + اکانت‌های واقعی (مالک می‌سازد) + tokenها در KeePass (نه repo) + verdict + ۱ هفته shadow. عامل هرگز خودش این‌ها را ست نمی‌کند.

## ۵. گاردها
- **ToS:** بدونِ mass-DM/auto-reply در OF/Reddit/X (بن‌آور)؛ تنها اتوماسیونِ DMِ مجاز = Welcome-flowِ رسمیِ OF (ACQUISITION-ENGINE §۴). AI درفت می‌زند، انسان می‌فرستد.
- **Containment:** رسانه/هویتِ C هرگز به اختاپوسِ مرکزی/گراف/cross-domain؛ استودیوی خالق ایزوله.
- **Consent/brand:** claims فقط از [[01 - Strategy/Identity/CLAIMS-REGISTER]]؛ بدونِ متنِ فارسی/شهر؛ فقط پا.
- **Budget:** سقفِ ابزار/API طبق charter؛ spend گیت‌دار.
- **Kill:** `/halt_pf` (ادمین) · `studio/HALT` (خالق، مرز حاکم) · هر اخطارِ پلتفرم → توقفِ فوری + DecisionLog.

## ۶. چک‌لیستِ ساختِ پایه (propose-only، بدونِ گیت)
- [ ] ماژولِ pipeline/queue (`05 - Acquisition/` یا `brain/`): draft→queue→approve state machine؛ publish = افکتورِ گیت‌دارِ خاموش (stub).
- [ ] KPI-loop: ingestِ شیت/دستی → `AcquisitionBrain.feedback_loop`.
- [ ] UIِ ادمین: دستورهای `/pf_*` روی langar + سطحِ content-freeِ `studio_pf` در telegram_center.
- [ ] UIِ خالق: پرداختِ `saba_studio` به تجربهٔ تحسین‌گر (spotlight/streak/preview) — ایزوله.
- [ ] افکتورِ گیت‌دار + فلگ‌ها + چک‌لیستِ فعال‌سازی.
- [ ] تست‌های propose-only (draft/queue/approve/no-live-publish) + shadow.

## ۷. یک تصمیمِ انسانی (بعد از این پایه)
> رفتنِ زنده = فقط تو: بستنِ **GATE 0 (محل اقامتِ C + Branch A/B)** → سپس اکانت‌ها + verdict + فلگ‌ها. تا آن، موتور draft/queue می‌کند و منتظرِ یک‌تاپِ توست.
