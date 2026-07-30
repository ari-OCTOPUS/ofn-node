---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: done
# status پیشین: complete (deliverables) — تصمیم‌ها proposal
created: 2026-07-10
updated: 2026-07-29
created_by: agent (Claude Fable 5 — اجرای PROMPT D)
related: "[[RESEARCH-INTEGRATION-round2-2026-07-10]] · [[DECISION-MATRIX-M2-2026-07-10]] · [[COMPLIANT-PLAYBOOK-M3-2026-07-10]] · [[architecture-blueprint-2026-07-04]] · CLAUDE.md"
tags: [project-f, thread-closure, prompt-d, t1-t8]
aliases: ["Thread Closure", "PROMPT D", "T1-T8"]
---

# THREAD-CLOSURE — PROMPT D ‏(2026-07-10)

## §۰ — خلاصهٔ وضعیت (۱۰ خط)
۱. ترتیب لود منشور اجرا شد (memory → STATE-REPORT → CLAUDE → PROJECT + منابع کاری و دادهٔ خام). همهٔ فایل‌های ارجاعی موجود بودند؛ فقط ماژول‌های `_ops/` بیرون از پوشه در دسترس این session نیستند `[OPEN — بدون اثر بر deliverableها]`.
۲. **GATE 0 همچنان باز و بلاکر مطلق است** — T1 کارت تصمیم + پیام آماده داد؛ جواب را نساختم.
۳. چهار verdict معلق → T2: هر چهار مورد تحلیل + پیشنهاد + ریسک؛ همگی `proposal`.
۴. پنج draft امن ساخته شد (T3) در `drafts-awaiting-gate/`: hub-copy · x-profile · tracking-links · ppv-ladder · kpi-spec.
۵. چک‌لیست OpSec با owner ساخته شد (T4) — ۲۴ آیتم تیک‌خور، پیش‌شرط بازشدن Security Gate.
۶. لیست ۱۲-سؤالی مشاور AU آماده شد (T5) — فقط سؤال/ریسک، بدون مشاوره.
۷. T6: ‏B2 ‏re-score شد (‏8.25→7.65، خروج از Top-5)؛ D3 با ۳ قید طراحی تأیید ماند؛ «ACC» برای بار سوم رد شد.
۸. T7: هر سه تناقض reconcile-پیشنهادی شد: برند=Anar Soles ‏(رزرو Yalda Arch) · نردبان=EXT-04 · Fansly=«mirror با تنظیم discovery-first» — هر سه flag برای verdict دونفره/آری.
۹. ساعت صبا طبق پیام امروز آری «~۳h/هفته» بسته تلقی و ثبت شد (سؤال #۴ → closed).
۱۰. بلوک‌های state ‏(T8) در PROJECT/DecisionLog/OpenQuestions/INDEX/memory اعمال شد (همه additive و proposal-tagged)؛ فهرست یکجای «منتظر verdict تو» در §۹.

---

## §۱ — T1: ‏GATE 0 (تصمیم انسانی — ساخته نشد، آماده‌سازی شد)

**دادهٔ لازم برای بستن (حداقلی):** یک جملهٔ صریح از صبا دربارهٔ **کشور اقامت فعلی** (self-report کافی است؛ سند لازم نیست) + تاریخ ثبت. همین.
**پیامد شاخه‌ها (عین بلوپرینت §۱ `[FACT — سند]`):**
- **Branch A (خارج از ایران):** کل مسیر (توافق §۴.۱ → Day-Zero → warm-up → پلن M3) مستقیماً اجرایی؛ KYC عادی؛ تقسیم درآمد داخل چارچوب Track B.
- **Branch B (داخل ایران):** ‏Track A **متوقف**؛ KYC/payout عملاً ناممکن (sanctions) `[EST — بلوپرینت]`؛ انتقال پول = ریسک حقوقی جدی → فقط مشاور licensed؛ ریسک شخصی صبا = همان downside برگشت‌ناپذیری که survival-filter پروژه رد می‌کند؛ گزینه‌ها: انجماد تا تغییر اقامت / بازطراحی کامل. هیچ دورزدنی پیشنهاد نمی‌شود.
**سؤال آمادهٔ ارسال (الحاق به پیام §۴.۲ بلوپرینت، لحن همان):**
> «یه سؤال مهم هم برای محکم‌کاری قانونی لازم دارم و بدون جوابش هیچ قدمی برنمی‌دارم: **الان محل زندگیت کدوم کشوره؟** این فقط برای اینه که مطمئن شم همه‌چیز از مسیر قانونی و امن برای خودت پیش می‌ره — هیچ جوابی همکاری رو خراب نمی‌کنه، فقط مسیرش رو عوض می‌کنه.»
**فرمت ثبت (یک خط در PROJECT.md):** `محل اقامت پارتنر: ___ · تاریخ: ___ · پیامد: Branch A/B` — تا این خط پر نشود، همهٔ اکشن‌های outward قفل‌اند (از جمله فعال‌سازی تلگرامی Langar برای هر چیز فراتر از گزارش داخلی).

## §۲ — T2: چهار verdict معلق (تحلیل → پیشنهاد → ریسک → آنچه انسان تأیید می‌کند)

| # | موضوع | تحلیل فشرده | Verdict پیشنهادی | ریسک پذیرفته | انسان چه چیزی را تأیید کند |
|---|---|---|---|---|---|
| V1 | پذیرش Playbook ‏M3 | ۲۴ گام فقط-compliant؛ هم‌گرا با ACQUISITION-ENGINE و گیت‌های عددی بلوپرینت §۳؛ با «صبا ~۳h» (بستهٔ امروز) سازگار است — گام ۸ (شوت ۴–۶h) باید به **دو جلسهٔ ≤۲.۵h در دو هفته** بشکند (اصلاحیهٔ M3-a) | **تصویب مشروط** به اصلاحیهٔ M3-a | KPI-targetهای اولیه ‏`[COI]`اند تا دادهٔ خودی | کلیت پلن + اصلاحیهٔ شوت + تاریخ شروع (پس از G0) |
| V2 | «بالانس >$100 نماند» | سه پایهٔ [FACT]: اختیار توقیف/تعلیق ToS ‏OF · گذار مالکیتی (فروش ~۱۶٪ به Architect Capital با ‏$3.15B ‏[FACT — fresh-scan]) · بند مصادرهٔ Fanvue | **تصویب** | کارمزد تراکنش‌های خرد `[EST]`؛ در Paxum کمتر | عدد آستانه ($100 یا min+ε) و روش برداشت |
| V3 | سقف مغز AUD 15/ماه تا اولین درآمد | هزینهٔ واقعی workload ‏≈AUD 8–12 ‏`[EST — محاسبهٔ round2 §۵.۴]`؛ ۲٪-cap با درآمد صفر = صفر؛ fail-closed موجود | **تصویب** + بازبینی ماهانه در حلقهٔ جمعه | ریسک loop → با hard-cap per-run مهار | عدد سقف + اینکه Langar هم زیر همین سقف باشد |
| V4 | بستن #۱۰ به‌نفع EXT-04 | استناد خام: ‏EXT-04 §۵ (پله‌های ‏$3–5/‏$8–15/‏$15–30/custom ‏$25+، بدون VIP ‏۹۰ روز؛ ماه اول بدون promo §۹۴) `[سند: external-research/04]` ↔ ‏MASTER-BUILD خط ۱۰۹ (‏VIP ‏$35) و §۴۳۶ (PPV ‏$6–18، custom از $30) ↔ Playbook ‏(VIP ‏$20) ‏[STATE-REPORT §۶]. شواهد round2 (فقط free-page ‏price-lock + باند نیش) به EXT-04 نزدیک‌تر است؛ VIP ‏$35 با «مُد=صفر» ماه‌های اول ناسازگار `[OPINION]` | **تصویب EXT-04**؛ ‏VIP منجمد (نه حذف) تا G2؛ draft اجرایی: [[drafts-awaiting-gate/ppv-ladder]] | اگر unlock<۵٪ پایدار → تست paid ‏$4.99 (شرط شکست ثبت‌شده) | قیمت دقیق پله‌ها + تاریخ بازبینی VIP |

Entryهای آمادهٔ DecisionLog (فرمت M4، همه `proposal — awaiting human verdict`) در [[DECISIONLOG-ENTRIES-M4-2026-07-10]] موجود بود؛ ورودی امروز فقط V1-اصلاحیه و بستن #۴ را اضافه کرد (در خود DecisionLog اعمال شد).

## §۳ — T3: درفت‌های امن (نوشته شد، نه توضیح)
`drafts-awaiting-gate/`: ‏[[drafts-awaiting-gate/link-hub-copy|کپی hub + گیت 18+]] · [[drafts-awaiting-gate/x-profile|پروفایل X با sensitive-media ON + پین + ۳ پست اول]] · [[drafts-awaiting-gate/tracking-link-design|نقشهٔ ۸ لینک بدون PII/cloaking]] · [[drafts-awaiting-gate/ppv-ladder|نردبان reconciled]] · [[drafts-awaiting-gate/kpi-dashboard-spec|اسپک داشبورد + آستانه‌های قرمز]] — همگی تگ `draft-awaiting-gate`.

## §۴ — T4: چک‌لیست OpSec / Security Gate (تیک‌خور، با owner)

**الف) رسانه/metadata — owner: آری (pipeline) + صبا (منبع)**
- [ ] EXIF/GPS strip خودکار در گام 02_READY (اسکریپت P9) — تست با exiftool روی ۳ فایل نمونه
- [ ] عکس‌های آمده از تلگرام: re-encode (تلگرام متادیتا را می‌شکند اما ری‌اینکد قطعی‌اش می‌کند) `[EST]`
- [ ] WM/NOWM دو نسخه (مصوب)؛ NOWM هرگز خارج از پلتفرم پولی
- [ ] پس‌زمینهٔ هر فریم: چک نشانهٔ مکانی/پریز/پنجره/فرش قابل‌جستجو — چک‌لیست بصری قبل از publish
- [ ] نام‌گذاری فایل بدون نام/دستگاه/مکان (قالب PF-2026Wxx — بلوپرینت §۷.۱)
**ب) ضد-شناسایی تصویری — owner: آری**
- [ ] reverse-image-search ماهانه (Google Lens/Yandex) روی ۳ عکس پرتوزیع — لاگ در Fable5
- [ ] verification-postهای Reddit با متن **چاپی** نه دست‌خط (T6-round2)
- [ ] تست cross-contamination ماهانه (مصوب 07-05): جستجوی handleها کنار نام واقعی/شهر
**ج) هویت/اکانت — owner: آری**
- [ ] ایمیل alias جدا برای هر پلتفرم (X/Reddit/OF/Fansly/GAML/SendX) — بدون نام واقعی در آدرس
- [ ] 2FA ‏TOTP همه‌جا (نه SMS)؛ recovery codes چاپ/آفلاین؛ password manager
- [ ] شمارهٔ تلفن شخصی به هیچ اکانت عمومی وصل نشود (الزام KYC ‏OF مستثناست — محرمانه سمت پلتفرم)
- [ ] پروفایل‌ها: صفر geo-fact حد شهر؛ location خالی/«Down Under»
**د) پرداخت/بانک — owner: آری (سؤالات نهایی → مشاور T5)**
- [ ] حساب بانکی/Paxum جدا از حساب شخصی روزمره؛ صفر تراکنش شخصی
- [ ] payout در آستانهٔ min برداشت (V2)؛ لاگ برداشت‌ها در Fable5
- [ ] هیچ جزئیات بانکی/هویتی در هیچ سند خارج از این پوشه/پیام تلگرام
**ه) دیوایس/شبکه — owner: هر دو**
- [ ] مرورگر پروفایل جدا (profile مجزا) برای همهٔ اکانت‌های برند؛ بدون افزونهٔ ناشناس
- [ ] بدون login اکانت‌های برند روی دیوایس مشترک/عمومی؛ قفل دیوایس
- [ ] cloud-sync گالری برای پوشهٔ RAW خاموش؛ آرشیو رمزگذاری‌شده (V4-#۱۵ ‏C2PA باز)
**و) پروتکل leak/DMCA — owner: آری (پلن مصوب 07-05 + این تکمله)**
- [ ] الگوی DMCA notice آماده در Fable5؛ ثبت timestamp+hash هر ست (اثبات مالکیت)
- [ ] در صورت لیک: (۱) ثبت URL+اسکرین، (۲) takedown مستقیم، (۳) اگر >۳ mirror → سرویس takedown پولی (فقط post-درآمد)، (۴) صفر تعامل عمومی
- [ ] در صورت سؤال هویتی در DM: پاسخ استاندارد privacy-forward + توقف ۴۸h پست (kill-switch M3 §۴)
**ز) تلگرام/ایجنت‌ها — owner: آری**
- [ ] توکن‌های bot جدا (صبا/لنگر)، فقط env، هرگز داخل فایل commit-شده
- [ ] صفر رسانه/PII در هر دو bot (گارد کد + بازبینی ماهانه ترنسکریپت)
**شرط بازشدن Security Gate ‏(PROJECT.md):** تیک کامل بندهای الف تا ز + ثبت در DecisionLog.

## §۵ — T5: سؤالات مشاور حقوقی/مالی AU (فقط سؤال/ریسک)
دوازده سؤال = ده‌گانهٔ round2 §۷.۲ (ABN timing · GST/export آستانهٔ ‏$75k · hobby-vs-business · ساختار sole-trader/partnership/company و پرداخت سهم شریک خارجی · گزارش ارزی USD→AUD · super/بیمه · قرارداد cross-border · نگهداری سوابق consent · **پیامد Branch B/sanctions** · IP برند) **+ دو سؤال بانکی/پردازنده:** ‏(۱۱) کدام بانک‌های AU با درآمد adult-adjacent مشکل حساب/بستن دارند؛ معیار انتخاب حساب چیست؟ (۱۲) دریافت payout از Fenix/Paxum از نظر AML/گزارش‌دهی چه الزامی برای فرد دارد؟ — هیچ‌کدام پاسخ قطعی از سمت ما ندارد؛ خروجی جلسه در DecisionLog ثبت شود.

## §۶ — T6: نتیجهٔ re-verify (اعمال‌شده در ماتریس)
‏B2 ‏→ ‏7.65 و خروج از Top-5 (جایگزین A7)؛ D3 تأیید با ۳ قید؛ جزئیات + تعارض «ACC» در [[DECISION-MATRIX-M2-2026-07-10]] §۶ ‏Changelog. سرچ روزِ این پرامپت دوباره همان الگو را نشان داد: نتایج برتر content-farm بودند و صفحهٔ رسمی حاکم است `[FACT — help.x.com]`؛ conservatively re-scored طبق دستور D.

## §۷ — T7: ‏reconcile سه تناقض (پیشنهاد + استناد؛ verdict انسانی)
| تناقض | شواهد دو طرف | پیشنهاد نهایی + منطق | flag |
|---|---|---|---|
| برند | MASTER-BUILD §۳: ‏Anar Soles/House Red/Yalda Arch ↔ Playbook §۳.۳: ‏Arch & Amber ‏[STATE-REPORT §۶ ردیف برند] · ‏12-prelaunch: ‏**Anar Soles صفر collision**، Yalda Arch آزاد، Arch & Amber همسایهٔ amberarch.com | **Anar Soles** (کاندید #۱) + رزرو Yalda Arch؛ چک نهایی handle لحظهٔ ساخت + جستجوی دستی IP Australia (سؤال #۶) | تصمیم دونفره (برند = هویت مشترک) |
| نردبان قیمت | سه نسخه (STATE-REPORT §۶) — تحلیل کامل در §۲/V4 | **EXT-04**؛ ‏VIP منجمد تا G2 | verdict آری (قیمت = hard-gated) |
| نقش Fansly | Playbook: mirror ↔ MONETIZATION: هم‌وزن روز اول · شواهد جدید: ‏FYP/discovery مزیت ساختاری برای faceless ‏[FACT-secondary — round2 §۲.۲] + fresh-scan #۵: «Fansly پلتفرم دوم قطعی» + محدودیت AI فوتورئال ۲۰۲۵ = رقابت discovery کمتر | **«mirror با تنظیم discovery-first»**: تولید یک‌بار (هزینهٔ mirror)، اما زمان‌بندی Fansly مستقل و native-first برای FYP؛ بازوزن‌دهی با دادهٔ G1 — عملاً میانهٔ دو موضع با هزینهٔ mirror و upside هم‌وزن `[OPINION]` | verdict آری (سؤال #۸) |
| ~~ساعت صبا~~ | — | **بسته با پیام امروز آری: ~۳h/هفته** → M3 با همین فرض معتبر؛ اصلاحیهٔ شوت M3-a | ثبت شد (adopted — ورودی انسانی) |

## §۸ — T8: بهداشت state
بلوک‌ها **اعمال شد** (همه additive): ‏DecisionLog (بند PROMPT D + بستن #۴) · OpenQuestions ‏(#۴ → بسته؛ به‌روزرسانی #۶/#۸/#۱۰/#۱۹) · PROJECT.md ‏(Active Context + Next actions) · INDEX ‏(ارجاع این سند + drafts + Langar) · memory (یک بند). متن دقیق در خود فایل‌هاست؛ چیزی overwrite نشد.

## §۹ — منتظر verdict تو (فهرست یکجا)
1. **GATE 0** — ارسال پیام §۱ + ثبت Branch A/B ‏(P0، بلاکر همه).
2. ‏V1: تصویب Playbook ‏M3 + اصلاحیهٔ M3-a (شوت دو-جلسه‌ای).
3. ‏V2: قاعدهٔ بالانس ‏(>$100 نماند) — عدد نهایی.
4. ‏V3: سقف مغز/لنگر AUD 15/ماه.
5. ‏V4: نردبان EXT-04 + انجماد VIP تا G2.
6. برند: ‏Anar Soles ‏(دونفره، با صبا).
7. ‏Fansly: تصویب «mirror با discovery-first».
8. حالت labeling ‏X: تنظیم اکانت sensitive-media ‏ON (محافظه‌کار، پیش‌فرض draft) یا دو-وضعیتی per-post.
9. ‏#۱۹: بلاک AU در OF — پیشنهاد بلوپرینت: فعلاً نه.
10. **فعال‌سازی Langar**: ساخت bot در BotFather (اکشن بیرونی = دست خودت) + یک هفته shadow-mode طبق قاعدهٔ منشور «اتوماسیون جدید بعد از یک هفته اجرای دستی موفق».
11. انجماد رسمی «expansion به body» (بلوپرینت §۴.۳-۴ — قدیمی، هنوز باز).

## §۱۰ — Sources (فایل‌های استنادشده)
`_memory/onlyfans-project-memory-2026-07-05.md` · `STATE-REPORT-2026-07-05.md` ‏(§۶) · `CLAUDE.md` · `PROJECT.md` · `architecture-blueprint-2026-07-04.md` ‏(§۱، §۲-دلتاها، §۳، §۴) · `ACQUISITION-ENGINE-2026-07-05.md` · `OpenQuestions.md` · `DecisionLog.md` · `external-research-2026-07-05/04-onlyfans-funnel.md` ‏(§۵، §۹۴) · `MASTER-BUILD-2026-07-04.md` ‏(خطوط ۱۰۹/۳۱۵–۳۱۷/۴۳۶) · `RESEARCH-INTEGRATION-round2-2026-07-10.md` · `DECISION-MATRIX-M2-2026-07-10.md` · `COMPLIANT-PLAYBOOK-M3-2026-07-10.md` · `PROJECT-F-BRAIN-SPEC.md` · `orchestrator.py` / `brain/dual_brain_v3.py` / `studio/studio_telegram_v3.py` · وب: ‏help.x.com/adult-content ‏(fetch ‏07-10).

## §۱۱ — Open Questions / شکاف‌ها
بدون سؤال بازِ جدید؛ تغییرها: #۴ بسته (ورودی انسانی) · #۶/#۸/#۱۰ حالا proposal-آماده و فقط verdict می‌خواهند · #۱۸/#۱۹ بدون تغییر · شکاف فنی: ماژول‌های `_ops/neural` بیرون از mount این session → تست‌های Langar بدون آن‌ها طراحی شد (fallback مستقل) `[OPEN — کم‌اثر]`.

---
*Verification pass: هر T با فایل منبع cross-check شد؛ هیچ قاعدهٔ قفل‌شده لمس نشد؛ هیچ hard-gated ‏adopted نشد؛ تنها ورودی «adopted» = ساعت صبا (تصمیم صریح انسانی در پیام امروز).*
