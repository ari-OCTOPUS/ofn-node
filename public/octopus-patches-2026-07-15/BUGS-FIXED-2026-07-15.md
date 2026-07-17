# باگ‌های اختاپوس — دیباگ‌شده ۲۰۲۶-۰۷-۱۵

منشأ: reality-audit «اختاپوس انگار زنده است ولی حرکت نمی‌کند». سه باگِ واقعی پیدا و **روی live درست شد + تست سبز**. هر سه در فایل‌هایی‌اند که capability-fingerprint **نیستند** → بدون revoke کردنِ درِ پول اعمال شدند. روی رستارتِ بعدیِ ارگانیسم فعال می‌شوند (کدِ فعلیِ در حالِ اجرا نسخهٔ قدیم را cache دارد).

---

## باگ ۱ — مغزِ پولی بی‌صدا می‌شکست (بحرانی) ✅
**علامت:** `synthesize/research/draft` به GLM می‌رفت؛ GLM کلید نداشت → fail → به مدلِ محلیِ $۰ می‌افتاد و **بی‌صدا**. شاهد: `state/cortex/synthesis-latest.json` → `tier="local", fallback_from="secondary: paid-call-failed", proposals:[]`. یعنی «مغزِ گران» عملاً خاموش بود و مالک نمی‌دانست.

**ریشه:**
1. `debate/client.py` فقط `ZAI_API_KEY`/`SAKANA_API_KEY` را می‌خواند، نه نامِ واقعیِ کلیدهای مالک (`GLM_API_KEY`/`FUGU_API_KEY`).
2. `cortex/model_router.py` کورکورانه به tierِ خواسته (مثلاً GLMِ بی‌کلید) می‌رفت، یک call الکی می‌سوزاند، بعد به محلی می‌افتاد — به‌جای اینکه سراغِ tierِ پولیِ **کلیددار** (Fugu) برود.

**فیکس:**
- `client.py`: `env_key_alias` اضافه شد (glm→`GLM_API_KEY`، sakana→`FUGU_API_KEY`).
- `model_router.py`: مسیریابیِ **کلید-آگاه** — فقط tierهایی که واقعاً کلید دارند امتحان می‌شوند؛ اگر GLM بی‌کلید بود مستقیم Fugu؛ اگر هیچ کلیدی نبود، بدونِ سوزاندنِ call، صادقانه محلی + `alert` قرمز.

**اثبات (زندهٔ واقعی):** `ask("synthesize",…)` → `ok:True, tier:primary, model:fugu, cost_usd:0.002185`. Fugu واقعاً جواب داد.
**تست:** `_ops/tests/test_brain_fix.py` — 3/3 PASS. **پچ:** `10-brain-fix.patch`.

---

## باگ ۲ — دکتر هیچ‌چی تست نمی‌کرد ولی «accept» می‌داد (صداقت) ✅
**علامت:** `doctor.run_cycle` → `run_sandbox` را با `suite_cmd=None` صدا می‌زد (RFCهای دکتر propose-only markdown‌اند — کدی برای اعمال/تست وجود ندارد)، پس **هیچ تستی اجرا نمی‌شد**، ولی `_critic_review` وقتی concern نبود `verdict="accept"` می‌داد. نتیجه: RFCها با برچسبِ «vetted/sandbox-tested» به مالک می‌رسیدند در حالی که **هیچ چیز اعتبارسنجی نشده بود**.

**فیکس (`doctor.py` _critic_review):** وقتی `tests is None` (هیچ suiteای اجرا نشد) → `verdict="unvalidated"` + `sandbox_validated=False` + یک concernِ صادق. «accept»ِ واقعی فقط وقتی یک suite سبز (`tests.exit==0`) اجرا شده باشد.
- خطِ Cyrillicِ سهویِ «слишком» هم به «خیلی» اصلاح شد.

**تست:** `test_doctor.py` — تستِ دروغِ قدیمی (`no suite → accept`) به دو تستِ صادق تبدیل شد: `بدونِ suite → unvalidated` + `suiteِ سبز → accept واقعی`. کلِ سوئیتِ دکتر سبز.

---

## باگ ۳a — ارگانِ مدرسه یاد می‌گرفت ولی هرگز ذخیره نمی‌کرد (سیمِ بریده) ✅
**علامت:** `wiring.py` afferent_beat → `school_bridge.learn_from(events, persist=False)`. یعنی هر ضربان، مدرسه رویدادها را «یاد می‌گرفت» ولی awareness **هرگز روی دیسک نمی‌ماند** → ارگانِ یادگیری عملاً بی‌حافظه بود.

**فیکس (`wiring.py:1365`):** `persist=False` → `persist=True`. حالا awareness واقعاً می‌ماند.
**تست:** `test_afferent_path_w2` + `test_consolidation_wiring` سبز.

---

## باگ ۳b — «حرکتِ واقعی» هنوز آن‌طرفِ مرزِ مالک است (طراحی، نه باگ)
دو سیمِ باقی‌مانده که در reality-audit پیدا شد، **باگِ کدنویسی نیستند — تصمیمِ مالک‌اند**:

- `live_loop._emit_advisory` بدنه‌اش عملاً `pass` است (advisory-theater): سیگنال در حافظه می‌رود ولی هیچ subscriberی کارِ واقعی نمی‌کند. درست‌کردنِ `pass` بدونِ یک **مصرف‌کنندهٔ واقعی** بی‌فایده است.
- هیچ leg خروجیِ کورتکس را نمی‌خواند (سیمِ مغز→اندام). زنجیرهٔ درآمدِ Lead-نقاشی (`leg_beat→draft_quote→invoice→email`) **ساخته شده** ولی پشتِ `OCTOPUS_WIRE_LEAD_DRAFT/EMAIL/INGEST` خاموش و DRY است.

**چرا نبستم:** اولین «حرکتِ واقعی» یعنی یک کنشِ **بیرونی** (ارسالِ پیش‌فاکتور به مشتریِ واقعی، پست، پرداخت). این طبقِ قانونِ اساسی همیشه **owner-gated + per-action** است. کد آماده است؛ فقط مالک با تأییدِ صریح آن را مسلح می‌کند.

---

## جمع‌بندی
| باگ | فایل | وضعیت |
|---|---|---|
| ۱ مغزِ پولیِ شکسته | client.py + model_router.py | ✅ live + اثباتِ Fugu + پچ ۱۰ |
| ۲ دکترِ ناصادق | doctor.py + test_doctor.py | ✅ live + تست سبز |
| ۳a persist مدرسه | wiring.py:1365 | ✅ live + تست سبز |
| ۳b حرکتِ بیرونی | live_loop + legs | ⏸️ آماده، DRY، منتظرِ تأییدِ مالک |

**فعال‌سازی:** رستارتِ تمیزِ ارگانیسم (دکمهٔ ♻️ در تلگرام یا `RUN-ORGANISM.bat` بعد از حذفِ `STOP-ORGANISM`) — هر سه فیکس با هم بالا می‌آیند.
