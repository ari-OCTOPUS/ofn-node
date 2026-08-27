# ORGANISM-INTELLIGENCE — سنجش هوشمندی با شاهد (۰ تا ۵)

> Branch: `audit/zcode-20260828` · Date: 2026-08-28 · Scorer: ZCode (PC)
> قاعدهٔ مالک: هوشمندی با تعداد فایل/مدل/حجم کد سنجیده نمی‌شود؛ هر امتیاز شاهد فایل/لاگ/receipt دارد.

```yaml
ORGANISM_INTELLIGENCE_LEVEL:
  perception: 3
  memory: 3
  reasoning: 2
  decision_quality: 3
  verification: 2
  autonomy: 3
  recovery: 4
  economic_effect: 1
  safety: 4
  overall_honest_verdict: >
    ارگانیسمی با سیستم عصبیِ خوب‌محافظ‌شده: زنده می‌ماند، خودش را حسابرسی می‌کند،
    از کرش برمی‌گردد و اثر بیرونی بدون مجوز ندارد — اما هنوز درآمد تسویه‌شدهٔ صفر دارد
    و حلقهٔ استدلالِ بسته (داده→گزینه→ارسال→پاسخ→درس) کامل نیست. میانگین وزنی ~2.8/5.
```

## ۱. Perception = 3/5
- ✅ داده واقعی می‌بیند: تلگرام زنده (یک poller با lease، offset byte-exact در ری‌استارت کنترل‌شده 2026-08-21)؛ سنسوریوم 182 روی NATS JetStream واقعی؛ vitals بردها هر ۳۰ ثانیه (ofn-heartbeat). [FACT: ss/systemctl probes 2026-08-28]
- ✅ پاهای 138 دیتابیس واقعی دارند: painting.sqlite 176KB (8 ردیف پایلوت)، products 200KB (35 محصول Ziman)، studio 116KB.
- ❌ بخش بزرگی از آزمون‌های شناختی روی fixture اجرا می‌شوند (megaprompt-2/3: «ارسال زنده ۰»، «n=1 فقط fake sender»)؛ 109 پیام محیطی در روز HELD می‌شدند تا قفل‌های ارسال 08-23. [FACT: HANDOFF.md 2026-08-20..23]
- ❌ world_model در langar: هواشناسی stub، git-commits اختیاری — درک محیطش ناقص است.

## ۲. Memory = 3/5
- ✅ 12,736 ردیف حافظه، 3 خواندن در هر سیکل با readback=read_ok؛ recall_reach=91 رویداد؛ genome ledger 14,168 رکورد hash-chained؛ حافظهٔ دوبی‌تمپورال facts در OFN (as_of/history). [FACT: ORGANISM-STATE.json 2026-08-27T21:27]
- ❌ C-046: نگهداری شواهد per-beat وجود ندارد (latest.json بازنویسی می‌شود) — تجربهٔ هر تیک قابل بازیابی نیست.
- ❌ حافظهٔ معنایی langar (HybridRetriever BM25+TFIDF) کامل ساخته شده ولی هرگز در مسیر تولید فراخوانی نمی‌شود؛ حافظهٔ episodic/negative/procedural تفکیک نشده.
- ❌ C-028: حذف آخرین رکورد لجر توسط verify() تشخیص داده نمی‌شود.

## ۳. Reasoning = 2/5
- ✅ collab_chat با DeepSeek پاسخ ساختاریافته با شواهد می‌دهد (پروب 13.6s، فارسی روان، model_source ثابت)؛ RulesBrain قطعی در OFN.
- ❌ brain_core SHADOW matched=0 (مدلِ جایگزین هیچ‌وقت با مسیر زنده هم‌رأی نشد → «فهم» تولید نمی‌کند).
- ❌ شبیه‌ساز خلاف‌واقع/انتخاب ارزش اطلاعات (VOI) وجود ندارد؛ researcherها source_quality دارند ولی contradiction resolution و saturation detection ندارند.
- ❌ بیشتر خروجی‌های «تصمیم» draft/template هستند (ziman copy-drafts، studio captions) — پر کردن قالب، نه انتخاب بین گزینه‌ها.

## ۴. Decision quality = 3/5
- ✅ رویدادهای typed (7 نوع + Envelope)، صف verdict مالک، دروازه‌های ریسک یک‌طرفه (ratchet)، سؤال‌های مشتق‌شده از شکاف فکت‌ها (questions.py با leverage ordering).
- ❌ D6 judge: سوگیری SECOND_POSITION_BIAS اثبات شده (C-038، Fisher p=4.11e-05) — داوری داخلی هنوز کالیبره نیست.
- ❌ UNKNOWN در کارت‌های اجرایی (تست T14-T18 دستور 2026-08-20: فیلدهای ناشناخته در کارت)؛ C-044 دلیل خالی در گذارهای رنگ.

## ۵. Verification = 2/5
- ✅ برچسب صادق داریم: IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING به‌جای PASS جعلی؛ receipt های SHA-دارد.
- ❌ تقریباً هر راستی‌آزمایی `verifier_independent=false` بوده (SIG-IV هنوز AWAITING_INDEPENDENT_VERIFIER) — سیستم عمدتاً خودش را تأیید کرده.
- ❌ ادعای 1229 تست OFN روی برد هرگز مستقل تأیید نشده [UNKNOWN]؛ تست از ریشهٔ ریپو با INTERNALERROR قلاب می‌شود (تلهٔ شمارش).

## ۶. Autonomy = 3/5
- ✅ 52,218 ضربان بدون prompt انسان؛ تسک‌های زمان‌بندی‌شده (Observatory hourly، poisoning-watch، consolidation، keep-warm) خودکار سبز؛ self-healing و doctor از 08-22 continuous.
- ❌ هر «قدم بعدی» تاریخی نیازمند سشن ایجنت خارجی بوده (مگاپرامپت‌های زنجیره‌ای)؛ تنها از 08-22+ مأموریت‌های پیوسته wire شدند. وابستگی به Grok/Claude/GLM برای هر موج = خودمختاری ناقص.

## ۷. Recovery = 4/5
- ✅ قوی‌ترین بعد: تست power-cut/survival/persistence در OFN؛ outbox HELD (نه ارسال دوباره)؛ WAL+synchronous=FULL؛ watchdog با tolerance؛ beat-lease fencing token؛ ری‌استارت کنترل‌شدهٔ center با rollback snapshot (PASS، صفر 409). بردها 2-10 روز uptime پایدار.
- ❌ ofn-backup.service روی 138 غیرفعال → بدون بکاپ تأییدشده؛ germline lag 2.46h؛ germline-hourly خطاهای push ثبت‌شده (exit_code/stderr در jsonl).

## ۸. Economic effect = 1/5
- ❌ paid_order_count = 0 (Ziman) · checkout هرگز E2E smoke نشده · Painting: quote فقط تا outbox دستی (8 ردیف پایلوت، invoice های 0100-A/0101-B امضانشده) · Studio: KYC_BLOCKED 0/9 آپلود، OF بدون پست · Mining/Crypto/Accounting: اجرا = صفر.
- ✅ صداقت پولی ممتاز است: claimed≠confirmed اجرا می‌شود، خرج واقعی ماه AU$1.07. ولی «هیچ چیز غلط ادعا نشده» جای «چیزی درست فروخته شده» را نمی‌گیرد.
- جمع‌بندی: ارگانیسم هنوز **هیچ دلار تسویه‌شده‌ای** تولید نکرده است. [FACT: CURRENT-TRUTH 2026-08-24 + MONEY-CLAIM-VS-CONFIRM]

## ۹. Safety = 4/5
- ✅ kill-switch سه‌لایه (فایل STOP-*، /halt، لانچر) · TCB پانزده‌فایله Ed25519 با enforce=1 (ویرایش = halt واقعی، 2026-08-16 آزموده شد) · scrub PII قبل از هر فراخوانی مدل · quota fail-closed · initData HMAC ضد replay · send-lock تا سطح مالک.
- ❌ **llama-server روی 180 به 0.0.0.0:8081 bind شده** — تنها سرویسِ LAN-exposed کل شبکه (بقیه loopback-only). [FACT: ss -lntp 2026-08-28]
- ❌ C-016 (architect escape hatch) باز است؛ ادعای «partner_precondition بسته است» در کد base_closed_gates نیست (فقط در تست hardcode شده) — ادعای ایمنیِ تأییدنشده.
