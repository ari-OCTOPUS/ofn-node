---
type: megaprompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, legs, sync, fix, phased]
created: 2026-08-02
updated: 2026-08-02
---

# مگاپرامپت — همگامیِ پاها: استودیو + نقشه‌کش + لید (۳ جعبهٔ سیاه)

> این سند برای **ایجنتِ سازنده** نوشته شده. سه پا ساخته شده‌اند ولی وصل
> نیستند: **studio_pf** (کارت دارد ولی ماژول ندارد)، **cartographer** (ماژول دارد
> ولی تابع status ندارد)، و **lead** (وصل است ولی ماشینِ کاملِ لید نیمه‌ساز است).
> این مگاپرامپت هر سه را کامل و همگام می‌کند.

---

## ۰ · این ماشین هنگ می‌کند — قواعدِ مطلق

دو آنتی‌ویروس روی `F:\backup` فعال‌اند. هر فایل ۳-۶ms. یک workflow با ۱۱ ایجنت
لپ‌تاپ را خواباند.

1. **هرگز** `find`/`du`/`rglob`/`os.walk` از `F:\backup`. از `_ops/` یا یک پوشهٔ
   پروژه شروع کن. از `Grep`/`Glob` (ripgrep) استفاده کن.
2. **هرگز** `.claude`/`.git`/`_Archive`/`_Duplicates`/`04 - Architect System` را نپیما.
3. هر فرمان زیر ۶۰ ثانیه. حداکثر ۴ ایجنتِ همزمان.
4. **هرگز فلگ را عوض نکن** (مگر با `OWNER_AUTH: ARM FLAG <name>`). **هرگز پروسه را
   ری‌استارت نکن.** **هرگز git commit نکن** (مگر با `OWNER_AUTH: COMMIT <paths>`).
5. CRLF: فایل‌های `_ops/*.py` معمولاً **CRLF**‌اند. بعد از هر ویرایش پایان‌خط را
   بشمار. پایتونِ `newline=''` می‌تواند CRLF را بشکند — تلهٔ ثبت‌شده.
6. **جهش‌آزمایی اجباری**: هر سبزی که نتوانستی با یک جهش قرمزش کنی را باور نکن.
   بین جهش‌ها `__pycache__` را پاک کن.

---

## ۱ · نقشهٔ حقیقت — سه منبع که باید همگام شوند

| منبع | فایل | تعداد پا |
|---|---|---|
| `CONTRACT_LEGS` | `input_surface_policy.py` | ۸ پا |
| `_BUSINESS_LEGS_SPEC` | `wiring.py` (سمبل: `_BUSINESS_LEGS_SPEC`) | ۵ پا |
| کارت‌های Task | `_ops/state/telegram/legs/<name>-tasks.json` | ۳ پا (lead, knowledge, studio_pf) |

**عدم‌همگامی‌های امروز:**

| پا | در CONTRACT_LEGS | در SPEC | ماژول status | کارت Task | تاپیک |
|---|---|---|---|---|---|
| lead | ✅ | ✅ | ✅ `lead_status` | ✅ | ۲۲ |
| ziman | ✅ | ❌ (الگوی متفاوت) | ⚠️ کلاس دارد، تابع سطح‌بالا نه | ❌ | ۲۳ |
| mining | ✅ | ✅ | ✅ `mining_status` | ❌ | ۲۴ |
| crypto | ✅ | ✅ | ✅ `crypto_status` | ❌ | ۲۵ |
| accounting | ✅ | ✅ | ✅ `accounting_status` | ❌ | ۲۶ |
| **studio_pf** | ✅ | **❌** | **❌ اصلاً فایل نیست** | ✅ | ۲۷ |
| knowledge | ✅ | ✅ | ✅ `knowledge_status` | ✅ | ۲۹ |
| **cartographer** | ✅ | **❌** | ⚠️ کلاس دارد، تابع نه | ❌ | ۶۵ |

---

## ۲ · سه فاز (به ترتیبِ اولویتِ مالک)

### فاز ۱ — studio_pf: از جعبهٔ سیاه به پا

این کامل‌ترین جعبهٔ سیاه است: کارتِ Task دارد (`studio_pf-tasks.json`)، فایلِ
feedback دارد (`studio_pf-feedback.jsonl`)، تاپیک ۲۷ دارد، ولی **هیچ ماژول
`studio_pf_leg.py` وجود ندارد**.

**کار:**
1. فایلِ `03 - Projects/اونلی فنز/PROJECT.md` را بخوان تا بدانی این پا چه می‌کند.
2. `studio_pf_status()` را در `_ops/legs/studio_pf_leg.py` بساز — الگوی دقیقِ
   `lead_leg.py::lead_status()` (خروجی: `{"leg","live","signal","note"}`). از رویِ
   PROJECT.md یک skeleton صادقانه بساز: `live=False`, `signal="skeleton"`.
3. آن را به `_BUSINESS_LEGS_SPEC` در `wiring.py` اضافه کن:
   `("studio_pf", "studio_pf_leg", "studio_pf_status")`.
4. تست بساز (الگوی `test_mining_age_fix.py`): تأیید `live=False`, `signal="skeleton"`,
   `note` صادقانه. جهش‌آزمایی: `live=True` را بشکن → قرمز.
5. اثباتِ observable: `business_legs_beat` را صدا بزن و تأیید کن `studio_pf` در
   خروجی ظاهر می‌شود.

### فاز ۲ — cartographer: تابعِ statusِ غایب

ماژولِ `cartographer_leg.py` وجود دارد و کلاس دارد با `status_snapshot`، ولی تابعِ
سطح‌بالا `cartographer_status()` ندارد. پس در `_BUSINESS_LEGS_SPEC` نیست.

**کار:**
1. `cartographer_leg.py` را بخوان. `status_snapshot` چه برمی‌گرداند؟
2. یک تابعِ سطحِ ماژول `cartographer_status()` بساز که همان قرارداد
   (`{"leg","live","signal","note"}`) را برمی‌گرداند — می‌تواند `status_snapshot`
   را wrap کند.
3. آن را به `_BUSINESS_LEGS_SPEC` اضافه کن.
4. تست + جهش‌آزمایی + اثباتِ observable.

### فاز ۳ — lead: ماشینِ کامل را تمام کن

lead وصل است ولی ماشینِ لید نیمه‌ساز است. کارهای باز (از راستی‌آزماییِ مستقل):

| زیرسیستم | وضعیت | کار |
|---|---|---|
| `lead_effect_gate.authorize()` | 🔴 سیم‌نشده | `center.py` دکمهٔ ✅ را به `authorize(eid,lid,token)` وصل کند. **اولین کار** — چون transport مسلح است و تأییدِ تو بی‌اثر است. |
| `lead_card` (دکمهٔ draft) | دکمهٔ مرده | handler در `center.py` اضافه شود یا دکمه حذف شود. |
| `lead_first_reply` draft | روی دیسک، بی‌خواننده | روی کارتِ لید نشان داده شود. |
| قاتلِ متراژ | ✅ فیکس شد (`1fea349`) | — |
| قفلِ STOP | ✅ فیکس شد (`cd6eebf`) | — |

⚠️ **transport مسلح است** (`OUTBOUND=1`, `SMTP=1` در هر ۴ پروسه). اول قفلِ STOP را
تأیید کن، بعد `authorize` را وصل کن. لحظهٔ وصل، ایمیلِ واقعی می‌رود.

---

## ۳ · معیارِ «تحویل‌شده»

برای هر پا، سه شاهد:
1. **اثرِ observable:** `business_legs_beat` خروجی شامل پاست.
2. **جهش‌آزمایی:** فیکس را برگردان → تست قرمز.
3. **صداقت:** اگر live نیست، صادقانه `live=False` بگو. هرگز عدد جعل نکن.

---

## ۴ · مرزهای سخت

- **D-10/D-11:** هر swap/withdraw = HARD_STOP، فقط انسان.
- **هرگز ایمیل نفرست.** transport مسلح است.
- **هرگز حذف نکن، فقط منتقل کن.**
- **حریمِ خصوصی:** `"08 - Partner (PII)"` · `Identity/*` · `OWNER-PROFILE*` را باز
  نکن. آن ونچر فقط «the venture».
- **راز:** هیچ کلید/توکن/شماره چاپ نشود.
- به نوتِ انسانی فقط append کن. هرگز بازنویسیِ مخرب.

---

## ۵ · خروجیِ مورد انتظار

برای هر فاز: «تمام / نیمه / باز» + اثبات. در پایان:
- `Active Context` و `Progress` پروژهٔ لمس‌شده را تازه کن.
- یک ورودی در `01 - Dashboard/HANDOFF.md` (فقط wikilink، زیر ۲۰۰ خط).
- اگر تصمیمِ تازه‌ای گرفته شد، یک ورودی در DecisionLog.
