# LANE-REPORT — ARCH-ADVISOR-3REC-20260907

ORDER=owner GO («معماری کن درست کن») روی سه توصیهٔ مشاور · GOV_VERSION=V8 · LADDER=L2

## ۱) پروب زندگی معنایی — ساخته شد و مسلح شد (توصیهٔ #۱)

کشف معماری: تشخیص stall (تازگی ts + مونوتونیک بودن beat با فایل mark) **از قبل** در `watchdog.py` بود و دوقلوی production آن را صدا می‌زد — ولی شاخهٔ stall فقط alert می‌زد و هرگز نمی‌کشت؛ دو wedge امشب دقیقاً به همین دلیل تا دخالت دستی ماندند. وصلهٔ دوقلوی production (`04 - Architect System/scripts/organism-watchdog.ps1`، `87f8cc88→e3354b68`):

1. **اول stack، بعد اقدام**: در هر stall، `py-spy dump` نگهدارندهٔ wedged → `state/stall-stacks/<ts>-pid<N>.txt` (پروب زندهٔ موفقیت: stack واقعی کورتکس گرفته شد — دیگری «منتظر رخداد بعدی» نیست).
2. **kill-first مسلح**: مارکر مالک‌دار `WATCHDOG-STALL-REVIVE` ساخته شد (تنها مسیر مسلح‌سازی که به Scheduled Task می‌رسد — طبق سند خود watchdog.py) ⇒ stall ⇒ stack ⇒ kill نگهدارنده ⇒ relaunch، با **سقف ۳ در ۶ ساعت** (ضد crash-loop، الگوی دوقلوی cortex). خلع سلاح: `Remove-Item _ops/WATCHDOG-STALL-REVIVE`.
3. ارشدیت STOP/HALT-ALL دست‌نخورده (قبل از همه چک می‌شود).
شاهد زنده: `watchdog.py --json` الان `beat_age_s` را می‌دهد (553s — زیر آستانهٔ 900s، پایش می‌شود).

## ۲) بازگزارش ACD-01 — سه اصلاح آماری اعمال شد (توصیهٔ #۲)

`FAMILY-VERDICT-ACD-01-amend1-stats.json` (append-only): silent → **NOT_REFUTED** [0.093–0.280] و حکم PROMOTE → **PROMOTION_SUSPENDED** (n≈600 برای رد آستانه)؛ کد-گارد → **DETERMINISTIC_BY_CONSTRUCTION** با اثبات AST (`instrument/guarded_extract.py` + تست ساختاری **3/3 سبز**: مسیر فیلد غایب = صفر فراخوانی مدل، فقط return)؛ تودرتو 0/6 → **NOT_ESTABLISHED_AS_ZERO** (upper95=0.39). سه ادعای پابرجا: pass₅=0.75 [0.628–0.842]، calibration (0.683 داخل CI)، رد ABSTAIN (Fisher p=0.0142). **ناهم‌خوانی ثبت‌شده:** P(X≤10|p=0.20)=0.323 به‌جای 0.79 مشاور (نتیجه یکی، عدد اصلاح شد — resolution: محاسبهٔ ایجنت با فرمول باینومیال مستقیم).
INV-TOOL-GUARD به‌عنوان invariant پذیرفته و ثبت شد + قاعدهٔ سوختن held-out.

## ۳) هارنس ACD-07 — نقشه از صفر نساختیم (توصیهٔ #۳)

الگوی AgentCheck (سرور ابزار=سطح مداخله، کش replay، ۱۲ نوع خطا، امتیاز دوبخشی) به‌عنوان طرح هارنس ثبت شد؛ اجرا با حداقل ۵ اجرا/سطح = GO بعدی. انتظارات اولیه مطابق مشاور: timeout→retry (30%→100% در ادبیات)، کهنگی→validator قطعی (رفتار جواب نمی‌دهد).

MUTATIONS=دوقلوی waچ‌داگ (WRITE، production-reachable) + مارکر مسلح + ۴ فایل lane/instrument · COUNTERS: EXTERNAL_ACTIONS=0
ROLLBACK=حذف مارکر (خلع سلاح فوری) + git checkout دوقلو + حذف فایل‌های lane
