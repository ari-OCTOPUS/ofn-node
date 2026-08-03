# RFC: بستنِ حلقهٔ هوش (#۳۱۰ + #۲۱۴) — shadow-first

**شاخه:** `fix/neural-loop-close-310-214`
**worktree:** `F:/backup/.wt-neural-loop/`
**تاریخ:** ۲۰۲۶-۰۷-۲۸
**وضعیت:** آمادهٔ بازبینیِ مالک — merge نشده، flagها default-off

---

## خلاصهٔ اجرایی

این RFC دو ریشه‌ای‌ترین مانعِ «هوشِ مصنوعیِ واقعی» بودنِ اختاپوس را نشانه می‌گیرد:
- **#۲۱۴** — BCM در هر سیکل خودش را پاک می‌کرد (یک لیست خالی = پاک‌کردنِ همه).
- **#۳۱۰** — لایهٔ neural از تصمیم unplugged بود (هیچ وزنِ آموخته‌شده‌ای اثر نداشت).

بعد از این فیکس، BCM شروع به یادگیری می‌کنه (جلوگیری از self-wipe) و برای اولین‌بار یک مسیرِ shadow می‌نویسه که نشان می‌ده یادگیری چه می‌گفت. مسیرِ اعمال (apply) پشتِ flag جداگانه است که مالک بعد از ۲۴-۴۸h مقایسه روشنش می‌کنه.

---

## آنچه تغییر کرد

| فایل | تغییر | ریسک |
|---|---|---|
| `_ops/neural/bcm.py:150` | guard `if known:` — لیستِ خالی دیگر وزن‌ها را پاک نمی‌کنه | صفر |
| `_ops/neural/neural_driver.py` | پارامتر اختیاری `bcm`، محاسبهٔ `learned_pressure` از وزن‌های top-3 | صفر (bcm=None → 0) |
| `_ops/wiring.py:1122` | پاسِ `bcm_signals` به evaluate | صفر |
| `_ops/wiring.py:1194` | shadow log فیلدهای `learned_*` را ثبت می‌کنه | صفر (فقط نوشتن) |
| `_ops/wiring.py:1224` | مسیرِ apply پشتِ `OCTOPUS_NEURAL_LEARNED_APPLY` (default-off) | خطرناک اگر روشن شه — به همین دلیل default-off |
| `_ops/tests/test_neural_loop_close.py` | ۱۲ تست جدید | — |

---

## تست‌ها

- **۱۲ تست جدید سبز** (۴ تا برای #۲۱۴، ۵ تا برای #۳۱۰-evaluate، ۳ تا برای #۳۱۰-apply).
- **۳۰ تستِ regression سبز**: ۱۹ bcm_forgetting + ۱۱ bcm_feed_and_verdicts + ۱۵ neural.
- هیچ regression.

---

## rollout (برای مالک)

**گام ۱ — merge (اختیاری):**
```
cd F:/backup
git merge fix/neural-loop-close-310-214   # یا cherry-pick
```

**گام ۲ — بوت با فیکسِ #۲۱۴ فعال:**
هیچ flag لازم نیست. بعد از ری‌استارت، BCM شروع به یادگیری می‌کنه. زیرا `OCTOPUS_WIRE_BCM_FEED=1` در flags.cmd فعلی روشنه، bcm_signals شروع به پر شدن می‌کنه. این **امروز** تأثیر دارد.

**گام ۳ — مشاهدهٔ shadow (۲۴-۴۸h):**
در `OCTOPUS-flags.cmd` اضافه کن:
```
set OCTOPUS_NEURAL_EFFECT_SHADOW=1
```
بعد از ری‌استارت، `effect-shadow.jsonl` شروع به ثبتِ `learned_pressure` می‌کنه. ۲۴-۴۸h صبر کن، بعد بپرس: «آیا وقتی learned_pressure بالا است، واقعاً درد/خطر هم بالا است؟» اگر بله → گام ۴. اگر نه → مسیرِ apply را روشن نکن.

**گام ۴ — اعمالِ واقعی (با احتیاط):**
اگر shadow منطقی بود:
```
set OCTOPUS_NEURAL_LEARNED_APPLY=1
```
این **اولین بار** است که یک وزنِ آموخته‌شده یک تصمیمِ واقعی را عوض می‌کنه. ضریبِ 0.5 (محافظه‌کارانه) به‌کار رفته. اگر رفتارِ بد دیدی، flag را خاموش کن.

---

## rollback

- سریع: `set OCTOPUS_NEURAL_LEARNED_APPLY=0` (مسیرِ apply را قطع می‌کنه).
- کامل: `git revert` در شاخهٔ اصلی، یا حذفِ worktree.
- #۲۱۴ قابل rollback نیست (و نباید) — جلوگیری از پاک‌کردنِ داده، همیشه خوب است.

---

## آنچه این RFC حل نمی‌کنه

- **#۲۱۵** — `organism.py:749` هنوز `acquisition_data`/`doctor_archive` پاس نمی‌دهد (consolidation همچنان فقط school_aware می‌بیند). ولی با #۲۱۴، حداقل BCM با سیگنال‌های انحرافی (bcm_signals) تغذیه می‌شه — حتی اگر consolidation هنوز گرسنه باشه.
- **#۵۱۳** — memory هنوز خوانده نمی‌شه. این RFC فقط neural-side را می‌بنده.
- **teacher_loop** (#۴۶۶) همچنان DEAD.

اینها برای RFC بعدی هستند.
