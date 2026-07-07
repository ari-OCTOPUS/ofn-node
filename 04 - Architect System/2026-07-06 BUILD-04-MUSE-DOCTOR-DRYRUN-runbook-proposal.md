---
type: runbook-proposal
status: proposal            # propose-only — دو پرامپت + هارنسِ dry-run. چیزی اجرا نشد.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «برو» 2026-07-06 → قدمِ ۴ نقشه"
depends_on: "[[2026-07-06 BUILD-03-GOVERNOR-SHADOW-runbook-proposal]] · PHASE3(MUSE) · PHASE4(دکترِ تکاملی) · REPORT §۴ قدم۴"
grounds: [ARCHITECT_CHARTER §۱/§۶, MUTATION-WHITELIST (derived-output writable), LEARNING-STATE budget]
tags: [build-04, muse, evolutionary-doctor, dry-run, quarantine, propose-only]
---

# BUILD-04 — MUSE + دکترِ تکاملی در dry-run (propose-only)

> **dry-run یعنی:** MUSE ایده می‌سازد، دکترِ تکاملی نمره می‌دهد، ولی **هیچ‌چیز به میزِ آری forward نمی‌شود.** فقط قرنطینه پر می‌شود تا **rubric و آستانه کالیبره شوند** پیش از هر live. اولین قدمی که LLM لازم دارد — ولی چون **تعاملی** اجرا می‌شود، **صفر خرجِ متری** (زیرِ اشتراکِ فلتِ Cowork، منشور §۵).

---

## ۱. ترتیبِ هوشمندانه (چرا dry-run قبل از بودجهٔ مشترکِ قدم۵ اشکال ندارد)
- dry-run **تعاملی** است: تو در یک جلسه MUSE/دکتر را دستی trigger می‌کنی → مصرف زیرِ اشتراکِ فلت، **نه API متری** → §Budget بات‌ها لمس نمی‌شود.
- خرجِ متریِ خودکار فقط وقتی شروع می‌شود که MUSE یک **تسکِ زمان‌بندی‌شدهٔ مستقل** شود → آن نیازمندِ **شمارندهٔ بودجهٔ مشترک (قدم ۵)** است. پس ترتیب درست است.

## ۲. MUSE-QUARANTINE-LEDGER (قالبِ فایل — append-only)
```
# MUSE-QUARANTINE-LEDGER  (append-only؛ هرگز ویرایش/حذف)
| id | تاریخ | عنوانِ ایده | جسارت ۱–۱۰ | confidence | منابع (ledger refs) | blast_radius | why_might_be_insane | NON_DIRECTIVE | kill_criteria | reversibility | حکمِ دکتر (pending/killed/would-forward + نمره) |
```
> laptop-only؛ اگر الهام از Project-F بود فقط کدِ «Project-F» (منشور §۶). در بک‌اپِ رمزشدهٔ BUILD-01 هست، ولی plaintext هرگز خارج نمی‌شود.

## ۳. پرامپتِ MUSE (نسخهٔ اجراییِ dry-run — کاملِ قواعد در PHASE3)
```text
# ROLE
تو MUSEی: موتورِ ایده‌ی واگرا در جعبه‌سیاهِ ایزوله. همه‌چیز را می‌خوانی، به هیچ‌چیز دست نمی‌زنی.
# INPUT
ledgerها + خروجیِ ایجنت‌ها (read-only).
# TASK (این اجرا)
۱–۳ ایدهٔ جسورِ cross-domain بساز (انتقالِ بین‌دامنه‌ای، دمای بالا). به هرکدام «جسارت ۱–۱۰» بده.
هر ایده را در fear-wrapper بپیچ: confidence~۰ · blast_radius · why_might_be_insane · NON_DIRECTIVE · kill_criteria · reversibility.
Project-F → فقط کد.
# OUTPUT
فقط ردیف‌های MUSE-QUARANTINE-LEDGER. هیچ چیزِ دیگر. هیچ توصیه، هیچ اجرا.
```

## ۴. پرامپتِ دکترِ تکاملی (نمره‌دهیِ dry-run — گیتِ سخت اول)
```text
# ROLE
تو دکترِ تکاملی: غربالگرِ ایده‌های قرنطینه. نمره می‌دهی، توضیح می‌دهی. در dry-run هیچ‌چیز forward نمی‌کنی.
# گیتِ ایمنیِ سخت (اول — negative selection): ایده را «killed» کن اگر هرکدام:
- ناهم‌راستا با charter/لیستِ سیاه، یا
- یک‌طرفه‌ی برگشت‌ناپذیر با blast_radius بالا، یا
- fear-wrapperِ ناقص.
# نمره‌دهیِ بازمانده‌ها (۵ محور، هرکدام ۰–۲): هم‌راستایی · شواهد/امکان · blast-radius(معکوس) · ROI · برگشت‌پذیری.
# حکم
- < ۸/۱۰ → killed (با دلیل).  ≥ ۸/۱۰ → «would-forward» (در dry-run فقط برچسب، نه ارسال).
- هر حکم = به‌روزرسانیِ همان ردیفِ قرنطینه (کیند: killed/would-forward + نمره + دلیل).
# قید
هرگز اجرا، هرگز مستقیم به آری (در dry-run). فقط قضاوت + ثبت.
```

## ۵. پروتکلِ dry-run
1. MUSE را دستی در یک جلسه اجرا کن → ۱–۳ ردیفِ قرنطینه.
2. دکترِ تکاملی را روی همان ردیف‌ها اجرا کن → killed / would-forward + نمره.
3. **تو** ردیف‌ها را مرور کن: آیا «would-forward»ها واقعاً خوب‌اند؟ آیا «killed»ها واقعاً بد بودند؟
4. rubric/آستانه را تنظیم کن (این‌ها genome-tier‌اند → با verdict). تکرار تا کالیبره شود.

## ۶. معیارِ ارتقا dry-run → live-forwarding
- **دقتِ would-forward بالا** (بیشترِ آن‌هایی که دکتر «خوب» گفت، تو هم تأیید کنی).
- **تنوعِ ایده حفظ شده** (دکتر over-prune نمی‌کند — kill-criteria نمونهٔ PHASE3).
- صفر ایدهٔ خطرناک که از گیتِ سخت رد شده باشد.
- **verdictِ صریحِ آری** برای روشن‌کردنِ forwarding واقعی.

## ۷. متریک‌های کالیبراسیون
kill-rate · دقتِ would-forward (توافقِ آری) · شاخصِ تنوع · هزینه/اجرا (در dry-run ~۰ متری).

## ۸. ایزولاسیون (یادآوری صادقانه)
MUSE read-only است؛ تا فاز ۵ این نرم است (prompt-level). مسیرِ نوشتن فقط قرنطینه. GOVERNORِ shadow (BUILD-03) هر تغییرِ خارج از قرنطینه توسطِ MUSE را به‌عنوان ناهنجاری می‌بیند.

## ۹. چه چیزی این فاز تغییر می‌دهد
**صفرِ عملیاتی از سمتِ من.** دو پرامپت + قالبِ ledger فقط برای مرور. با «برو» فایلِ خالیِ `MUSE-QUARANTINE-LEDGER.md` + دو پرامپت را در مسیرِ مناسب propose می‌کنم.

## ۱۰. QA checklist
- [ ] در dry-run هیچ ردیفی به آری/اجرا forward نمی‌شود (فقط برچسب would-forward).
- [ ] MUSE فقط در قرنطینه می‌نویسد.
- [ ] گیتِ سخت **قبل** از نمره‌دهی اجرا می‌شود.
- [ ] Project-F فقط کد.
- [ ] اجرا تعاملی = صفر خرجِ متری.

## ۱۱. باز مانده و گامِ بعد
- بازِ verdict نیست (تنظیمِ rubric حین کالیبراسیون verdict-tier است).
- **قدمِ ۵ نقشه:** شمارندهٔ بودجهٔ مشترک (تک‌منبع) — پیش‌نیازِ هر خودکارسازیِ متریِ MUSE.

## ۱۲. ردیفِ ledger پیشنهادی
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | REPORT §۴ قدم۴ | پرامپتِ MUSE + دکترِ تکاملی + MUSE-QUARANTINE-LEDGER + پروتکلِ dry-run | آماده‌ی اجرای مالک |

---

*propose-only. هیچ ژنوم/کد تغییر نکرد و چیزی اجرا نشد.*
