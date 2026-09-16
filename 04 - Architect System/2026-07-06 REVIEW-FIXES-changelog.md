---
type: changelog
status: review+fixes
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «بازنگری و رفع ایراد» 2026-07-06"
method: "اجرا و تستِ واقعیِ کد در سندباکسِ Linux؛ PowerShell فقط بازبینیِ چشمی (بدونِ Windows)"
tags: [changelog, review, bugfix, tested, propose-only]
---

# بازنگری و رفع ایراد — changelog (با شاهدِ تست)

> این‌بار کد **واقعاً اجرا و تست شد**، نه فقط بازخوانی. ۷ ایراد پیدا و رفع شد؛ ۵ فایلِ پیشنهادی به‌روز شدند. همه هنوز propose-only.

---

## یافته‌ها و رفع‌ها
| # | فایل | ایراد | شدت | رفع | شاهدِ تست |
|---|---|---|---|---|---|
| ۱ | BUILD-05 `budget_gate` | **race دو-رزرو:** `reserve` چک می‌کرد ولی رزرو را persist نمی‌کرد → دو ایجنتِ همزمان هر دو مجاز، over-spend | **بالا** | `reserve` حالا رزرو را زیرِ قفل persist می‌کند + `settle(actual)` + `release()` برای refund | ✅ ۲۰ پروسهٔ موازی → دقیقاً ۱۰ مجاز، سقف $۲.۰۰، صفر over-spend |
| ۲ | BUILD-05 `budget_gate` | **fail-open:** روی state خراب crash می‌کرد (به‌جای deny) | متوسط | `try/except` → deny `state-unreadable` (fail-closed) | ✅ T4: روی JSON خراب → deny |
| ۳ | BUILD-05 `budget_gate` | **deadlock قفل:** `.lock` رهاشدهٔ پروسهٔ crash‌کرده تا ابد بلوکه می‌کرد | متوسط | steal کردنِ قفلِ کهنه‌تر از ۳۰ ثانیه | بازبینی‌شده (منطقِ ساده) |
| ۴ | BUILD-03 `governor_shadow` | **خطای خاموش:** خطای اجرای دکتر/گارد به‌عنوان «سالم» (score=۱۰۰) بلعیده می‌شد — نقضِ منشور §۴ | **بالا** | هر `_error` runner → alertِ صریح («doctor/guard FAILED to run») | ✅ تستِ منطق: خطای دکتر → alert، نه سکوت |
| ۵ | BUILD-02 `genome_guard` | مسیرِ Windows هاردکد (غیرقابلِ تست/حمل) + قفلِ خراب crash | پایین | `VAULT_ROOT` env override + `try/except` روی خواندنِ lock | ✅ init/tamper(CRITICAL,exit=1)/restore(ok) |
| ۶ | BUILD-01 `backup-offbox.ps1` | **خطای خاموش:** اگر rclone نصب نبود، throw قبل از نوشتنِ `FAILED.flag` → شکستِ بی‌صدا | متوسط | `try/catch` → `FAILED.flag` در هر حالتِ شکست نوشته می‌شود | بازبینی‌شده (PowerShell، بدونِ Windows اجرا نشد) |
| ۷ | PHASE1 charter | **شکافِ R1:** مرزِ MUSE↔learning-loop در منشور رمزگذاری نشده بود | متوسط (طراحی) | افزودنِ §۱.۳: دامنه‌ها متعامد (MUSE=cross-project، loop=خودجهش)، هر دو در یک قیفِ verdict | — |
| ۸ | BUILD-03 `governor_shadow` | **حفرهٔ ضدِ خطای‌خاموش (لایهٔ دوم):** کرشِ دکتر با stdout خالی → `run_json` آن را `{}` می‌گرفت (نه `_error`) → «سالم» پنداشته می‌شد | **بالا** | `run_json`: خروجیِ خالی/نامعتبر = `_error` → alert | ✅ integration-test سناریو C: کرشِ دکتر → «doctor FAILED» |

## آنچه تغییر کرد (۵ فایل)
`BUILD-01` (try/catch) · `BUILD-02` (portable + lock-safe) · `BUILD-03` (anti-silent-failure) · `BUILD-05` (reserve/settle/release + fail-closed + stale-lock) · `PHASE1` (§۱.۳ مرزِ R1).

## صداقتِ روش
- **تست‌شده در سندباکس:** `budget_gate` (race/concurrency/rollover/fail-closed) و `genome_guard` (init/tamper/restore) و منطقِ alertِ governor — همه پاس، `py_compile` پاک.
- **بازبینیِ چشمی (اجرا نشد):** اسکریپت‌های PowerShell (بدونِ Windows/rclone در سندباکس). قبل از اتکا، همان QA checklistِ هر runbook را سمتِ Windows اجرا کن.
- ریسکِ R3 (ایزولاسیونِ نرم تا پروسهٔ مستقل) هنوز پابرجاست — این یک واقعیتِ معماری است، نه باگِ کد؛ در فاز ۵ بسته می‌شود.

## ردیف‌های ledger پیشنهادی
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | fix | بازنگری | ۷ رفعِ ایراد در BUILD-01/02/03/05 + PHASE1 (با تستِ سندباکس) | آماده |

---

*propose-only. اصلاحات فقط روی فایل‌های پیشنهادیِ خودم بود؛ هیچ ژنوم/کدِ زنده تغییر نکرد.*
