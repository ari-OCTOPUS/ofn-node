---
type: decision-entries
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: ready-to-paste (اعمال‌شده در DecisionLog.md همین تاریخ)
created: 2026-07-10
created_by: agent (Claude Fable 5 — اجرای PROMPT C / M4)
tags: [project-f, decisionlog, m4]
---

# DecisionLog Entries — M4 (2026-07-10)

> قواعد status طبق پرامپت C: هر چیز مرتبط با قاعدهٔ قفل‌شده یا اکشن outward/hard-gated → `proposal (awaiting human verdict)`؛ `adopted` فقط برای انتخاب‌های برگشت‌پذیرِ درون‌پوشه‌ایِ غیر-outward. بلاک زیر عیناً در [[DecisionLog]] هم اعمال شد.

| Date | Decision | Rationale | Alternatives considered | Accepted risks | Status | Linked docs |
|---|---|---|---|---|---|---|
| 2026-07-10 | کاتالوگ gray-area = «analyze-not-recommend» — ردیف‌های gray فقط برای آگاهی از ریسک نگه‌داری می‌شوند؛ هیچ‌کدام وارد پلن اجرایی نمی‌شوند مگر با verdict جدا | تفکیک شفاف دانش از اجرا؛ جلوگیری از خزش gray به پلن `[OPINION]` | (الف) حذف کامل grayها از اسناد — دانش ریسک از بین می‌رفت؛ (ب) اجازهٔ ورود مشروط بدون verdict — ناسازگار با منشور | هزینهٔ شناختی نگه‌داری فهرست بزرگ‌تر | **adopted** (درون‌پوشه، برگشت‌پذیر) | [[DECISION-MATRIX-M2-2026-07-10]] · [[RESEARCH-INTEGRATION-round2-2026-07-10]] §۴ |
| 2026-07-10 | Decision Matrix با وزن ban-risk ‏۰٫۳۰ = ابزار رسمی اولویت‌بندی تاکتیک‌ها در فاز validation | از دست رفتن اکانت اصلی در validation فاجعه‌بار است؛ وزن سنگین ریسک، سوگیری «حجمِ سریع» را خنثی می‌کند `[OPINION]`؛ حساسیت‌سنجی ضمیمه است | (الف) وزن برابر همهٔ ابعاد — ریسک را کم‌نمایی می‌کرد؛ (ب) وزن ۰٫۱۵ — مناسب فاز بعد از تثبیت، نه حالا | تاکتیک‌های پرحجم/پرریسک (TikTok) عمداً پایین می‌مانند؛ هزینهٔ فرصت پذیرفته شد | **adopted** (ابزار تحلیلی داخلی، برگشت‌پذیر) | [[DECISION-MATRIX-M2-2026-07-10]] |
| 2026-07-10 | پذیرش Compliant-Only Playbook ‏(M3) به‌عنوان پلن اجرایی فاز validation — ۲۴ گام، ۱۵ تاکتیک Do-Now، کیدنس هفتگی، معیارهای kill/pivot | خروجی هم‌گرای سه راند تحقیق + ماتریس M2؛ فقط تاکتیک‌های compliant؛ سازگار با ACQUISITION-ENGINE و گیت‌های G0–G2 | (الف) ادامه با ACQUISITION-ENGINE خالی — پلن گام‌به‌گام و kill-criteria صریح نداشت؛ (ب) شمول grayهای پربازده (C1/C2) — رد شد (ریسک ban در validation) | باند KPIهای هدف از منابع `[COI]` است تا دادهٔ خودی برسد | **proposal (awaiting human verdict)** — شامل اکشن‌های outward و hard-gated؛ اجرا پشت GATE 0 | [[COMPLIANT-PLAYBOOK-M3-2026-07-10]] |
| 2026-07-10 | قاعدهٔ عملیاتی «هیچ بالانسی >US$100 روی هیچ پلتفرمی نماند؛ برداشت در آستانهٔ min» | گذار مالکیتی OF ‏(فوت Radvinsky + مذاکرهٔ فروش >$3B ‏[FACT — Forbes]) + بند مصادرهٔ ۱۲ماههٔ Fanvue ‏[FACT — legal رسمی] + اختیار توقیف earnings در ToS ‏OF ‏[FACT] | (الف) برداشت ماهانهٔ ثابت — پنجرهٔ ریسک بازتر؛ (ب) برداشت روزانه — fee/friction بیهوده | کارمزد تراکنش‌های کوچک بیشتر می‌شود `[EST]` | **proposal (awaiting human verdict)** — قاعدهٔ مالی عملیاتی | [[RESEARCH-INTEGRATION-round2-2026-07-10]] §۲/§۷ ‏(R4/R11) |
| 2026-07-10 | سقف مطلق هزینهٔ مغز AI = ‏AUD 15/ماه تا اولین درآمد (جایگزین موقت ۲٪-cap) | ‏۲٪-cap با درآمد صفر = بودجهٔ صفر و بلاتکلیفی؛ هزینهٔ واقعی workload ‏≈AUD 8–12/ماه `[EST — محاسبه با قیمت رسمی]` زیر این سقف می‌ماند | (الف) ماندن روی ۲٪-cap — عملاً مغز را خاموش نگه می‌دارد؛ (ب) سقف A$25 — بافر غیرلازم در فاز صفر-درآمد | ریسک loop کنترل می‌شود با fail-closed موجود در BRAIN-SPEC | **proposal (awaiting human verdict)** — سؤال باز #۲۰ | [[RESEARCH-INTEGRATION-round2-2026-07-10]] §۵.۴ · [[PROJECT-F-BRAIN-SPEC]] |
| 2026-07-10 | بستن سؤال #۱۰ به‌نفع نردبان EXT-04 ‏(free-page + PPV اول $5–8 + custom از $25؛ بدون VIP تا روز ۹۰) | یافتهٔ فنی: فقط free-page می‌تواند پست تایم‌لاین را price-lock کند ‏[FACT-secondary] + قیمت‌های نیش ‏[COI-consensus] هر دو به EXT-04 نزدیک‌ترند | نسخهٔ MASTER-BUILD ‏(VIP ‏$35) و Playbook ‏(VIP ‏$20) — هر دو به paid-page یا VIP زودهنگام تکیه دارند | اگر unlock <۵٪ بماند، مدل paid-page ‏$4.99 تست می‌شود (شرط شکست ثبت‌شده) | **proposal (awaiting human verdict)** — تصمیم قیمت = hard-gated طبق منشور §۸ | [[RESEARCH-INTEGRATION-round2-2026-07-10]] §۳ · OpenQuestions ‏#۱۰ |
