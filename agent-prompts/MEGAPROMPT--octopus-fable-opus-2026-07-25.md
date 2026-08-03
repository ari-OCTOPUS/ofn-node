# MEGAPROMPT — اختاپوس + اونلی فنز (Fable 5 / Opus 5 · UltraCode Session)
**تاریخ:** ۲۰۲۶-۰۷-۲۵ · **سازنده:** GLM (جلسهٔ راستی‌آزمایی) · **گیرنده:** Fable 5 یا Opus 5
**زمینه:** این مگاپرامپت بر اساسِ **دادهٔ واقعی روی دیسک** نوشته شده، نه حدس. همهٔ اعداد راستی‌آزمایی‌شده‌اند.

---

## ۰. یک‌خطیِ وضعیت

اختاپوس زنده‌ست (۳ پروسه)، رباتِ Center زنده‌ست و پیام می‌گیره (offset در حال حرکت)، مغزِ پولی پایدار شد (timeout ۴۵، STOP-FUGU حذف، circuit-breaker threshold=3)، انضباطِ سکوت ساخته شد (dedup امضا + سقف ۶/روز)، money-pulse به قلب وصله. اونلی فنز یکپارچه شد (spine + مغز غنی‌شده)، PII پاک‌سازی شد، GATE 0 فقط امضای C مانده.

---

## ۱. راستیِ راستی‌آزمایی‌شده (۲۰۲۶-۰۷-۲۵، سنجیده — ادعا نیست)

### اختاپوس (F:\backup\_ops)
| موضوع | واقعیت | شاهد |
|---|---|---|
| پروسه‌های زنده | `organism.py` · `cortex/cortex.py` (پورت ۸۷۷۲) · `live/server.py` (پورت ۸۷۷۳) · `center.py` (PID 16756) | Get-CimInstance |
| ربات Center | `@intergrade2725_Bot` (id 7992324219) · گروه «Organism» (chat_id `-1004475788460`) · ۳ عضا · supergroup خصوصی · `can_read_all_group_messages: True` | getMe + getChat از API |
| offset | 223882985 → 223883195 (در حال حرکت = ربات پیام می‌گیره) | center-config.json |
| commands_set | ۹ (۹ دستور در سرور تلگرام ثبت شده) | center-config.json |
| watchdog | `OCTOPUS-TG-Center-Watchdog` ثبت شد (Status: Ready، هر ۵ دقیقه) | schtasks /Query |
| مغزِ پولی | `PAID_HTTP_TIMEOUT_S=45` (از ۲۰ فیکس شد) · `STOP-FUGU` حذف شد · `consecutive_failures: 0` · `used_total: 59` | flags.cmd + state |
| circuit-breaker | `resilience.circuit_breaker` در budgets.yaml (failure_threshold=3، additive) | budgets.yaml |
| انضباطِ سکوت | event_bridge: dedup امضای محتوا (۵۰ هم‌امضا→۱) + سقفِ روزانهٔ ۶ + merged digest | event_bridge.py |

### اونلی فنز (F:\backup\03 - Projects\اونلی فنز)
| موضوع | واقعیت | شاهد |
|---|---|---|
| یکپارچه‌سازی | spine (`pf_os/spine.py`) + مغزِ غنی‌شده (`brain/cortex_augmented.py`) + وصل‌سازی orchestrator | orchestrator.py |
| پاک‌سازی PII | ارمین/صبا/محبی از کد پاک شدند · bridge/event_bus data-driven (`PF_PII_BLOCKLIST`) | bridge.py, event_bus.py |
| GATE 0 | Branch A + سیدنی تأیید (امضای A) · **فقط امضای C مانده** | DecisionLog DL-G0 |
| DL-PF-V5 | REVOKE بسته (تأیید A) | DecisionLog |
| نامِ برند | سیستمِ A/B test با ThompsonBandit (`brain/brand_naming.py`) — flag-off، seed: Anar Soles/Yalda Arch | brand_naming.py |
| کارت‌های توافق | `/agreement /agreement_for_creator /agreement_signed` در لنگر | langar_bot.py |
| سباست | اسمِ برندِ persona، نه آدم · پارتنر یک نفره (۵۰/۵۰ A+C) · صبا=C | مالک ۲۰۲۶-۰۷-۲۵ |

### تست‌ها (همگی سبز)
- اختاپوس: **۲۵۲۶+** تست سبز (۱ fail از پیش‌موجود: `test_paid_router_dark_config` که router flags در working-tree روی ۱ هست ولی تست صفر می‌خواد — رأیِ مالک، از کارِ این جلسه نیست)
- اونلی فنز: **۳۹۱** تست سبز (۱۱۹ pf_os + ۱۴۴ tests + ۱۲۸ langar/brain/studio)
- فایل‌های تستِ ساخته‌شدهٔ این جلسه: `test_budgets_resilience_config.py`، `test_telegram_silence.py`، `test_money_pulse.py`

---

## ۲. مأموریتِ تو (Fable 5 / Opus 5)

تو در یه **UltraCode Session** هستی با دسترسیِ کامل به `F:\backup`. سه هدف داری، به ترتیبِ اولویت:

### هدف ۱ — بستنِ GATE 0 (بزرگ‌ترین قفل)
GATE 0 = NO-GO. تنها چیزِ باز: **امضای مکتوبِ C (صبا)** روی توافق. این یه آدمِ واقعیه — نمی‌تونی به‌جاش امضا کنی. ولی:
- کارتِ `/agreement_for_creator` تو لنگر آماده‌ست (متنِ قابل‌کپی برای C).
- وقتی C تأیید کرد، `/agreement_signed` در DecisionLog ثبت می‌کنه (ولی **دو-مرحله‌ای‌اش کن** — یه زدنِ اشتباه ثبت نکنه. این جلسه یه‌بار اشتباهاً ثبت شد و revert شد).
- بعد از امضا: GATE-STAMP را GO کن (ولی این کارِ مالکه، نه ایجنت — فقط پیشنهاد بده).

### هدف ۲ — فعّال‌سازیِ money-pulse + پاها
money-pulse ساخته شد ولی flag-off (`OCTOPUS_WIRE_MONEY_PULSE`). وقتی مالک اجازه داد:
- flag رو روشن کن (به `_ops/OCTOPUS-flags.cmd` byte-level اضافه کن).
- ولی **الان confirmed_revenue = ۰** چون هیچ پا پولِ واقعی تولید نکرده. pulse صفره.
- برای پولِ واقعی: یه پا باید شروع به تولید کنه. کاندیدها: studio_pf (G0 لازم)، mining/crypto (اگه فعال باشن)، lead/ziman.

### هدف ۳ — وصل‌کردنِ data sources واقعی به ledger
ژنوم = زبانِ مشترک (hash-chain ledger). پول از `MONEY_ATTRIBUTION` event میاد. ولی **الان صفر ردیف**. برای پر کردن:
- scraping/reconciliation از پلتفرم‌ها (propose-only، نه auto-post).
- یا ورودیِ دستیِ مالک (claim → confirm).

---

## ۳. قوانینِ سختِ این ریپو (رعایتِ اجباری)

۱. **درختِ زنده‌ست.** ۳+ پروسه کد رو از دیسک می‌خونن. تشخیص موازی، اعمال سریالی.
۲. هر رفتارِ نو: **additive، flag-gated (پیش‌فرض خاموش)، fail-soft**. استثنا هرگز تیک را نکشه.
۳. `OCTOPUS-flags.cmd` فقط byte-level و با حفظِ CRLF ویرایش بشه (ابزارِ Edit رو روی `.cmd` به‌کار نبر — LF می‌کنه و batch خراب می‌شه).
۴. `.env` هرگز dump/echo/ویرایش نشه. فقط مالک. توکن‌ها فقط SET/EMPTY چک بشن، نه مقدار.
۵. **هرگز:** `git clean`، حذف (فقط انتقال به `_Archive`/`_Duplicates`)، `OCTOPUS_CB_SECRET` بسازی، `_ops/ACTIVATION-C6-RESEARCH.flag` بسازی.
۶. C6 ساختاراً propose-only — نشکنش.
۷. **هیچ امضای خودکار.** امضای C فقط خودِ C. امضای A فقط خودِ A. هیچ‌وقت به‌جای آدم امضا نکن.
۸. **هیچ auto-post به پلتفرم.** ToS + ban risk. فقط payload آماده + تأییدِ انسان.
۹. مرزِ #۷: هیچ PII/محتوا/پلتفرم به cortex اختاپوس نمی‌ره. prompt فقط اعداد abstract.
۱۰. سوئیت سبز قبل از هر commit: `python -X utf8 _ops\tests\run_all.py` (اختاپوس) و `python -X utf8 -m pytest pf_os/ langar/ tests/ brain/ studio/` (اونلی فنز).
۱۱. **صداقتِ فرایند:** قبل از هر ادعا، شمارِ صریحِ pass/fail یا exit code بگیر. «نبودِ ❌» یعنی سبز نیست.
۱۲. grep در Git-Bash روی این سیستم با `-i -E` ترکیبی باگ داره — از `python -c` با `re` استفاده کن.
۱۳. git روی ویندوز با کاراکتر فارسی در pathspec مشکل داره — `-c core.quotepath=false`.

---

## ۴. گوچاهایی که این جلسه هزینه داد (یاد بگیر)

- **«نبودِ ❌» یعنی سبز نیست.** یه‌بار گزارش دادم «سبز شد» در حالی که پچ اجرا نشده بود. همیشه شمار بگیر.
- **امضای تستی:** وقتی `/agreement_signed` رو تست کردم، تصادفاً امضای C رو ثبت کردم. سریع revert شد. **هر دستوری که state تغییر می‌ده، دو-مرحله‌ای باشه.**
- **`PAID_HTTP_TIMEOUT_S=20` جا افتاده بود** از یه دیباگِ قبلی. علتِ اصلیِ timeoutهای مکرر بود.
- **`STOP-FUGU` auto-trip** بعد از `FUGU_FAIL_CEILING=3` شکست. فکر می‌کردم مغز خرابه، ولی فایلِ kill بود.
- **`flags.cmd` در `.gitignore`** (خط ۴۰) — پس `git status` تمیز نشون می‌ده حتی اگه flagها محلی تغییر کنن.
- **۳ ربات متفاوت:** `TELEGRAM_BOT_TOKEN` (رباتِ اصلی `@Robo2725_bot`) ≠ `TG_CENTER_BOT_TOKEN` (`@intergrade2725_Bot`). هر کدوم تو گروهِ خودش. تداخل ندارن.
- **۴۰۹ Conflict** وقتی getUpdates موازی از یه ربات زده بشه. approval_channel داخلِ organism.py هم poll می‌کنه (با رباتِ اصلی).

---

## ۵. راستی‌آزماییِ روزانه (بعد از هر تغییر)

```powershell
# اختاپوس
python -X utf8 "F:\backup\_ops\tests\run_all.py"
Get-Content "F:\backup\_ops\state\paid-calls.jsonl" -Tail 3
Get-Content "F:\backup\07 - Knowledge\genome-system\ledger\ledger.jsonl" -Tail 3
python -X utf8 -c "import json; print(json.load(open(r'F:\backup\_ops\state\fugu-quota.json'))['consecutive_failures'])"
# اونلی فنز
cd "F:\backup\03 - Projects\اونلی فنز"
python -X utf8 -m pytest pf_os/ langar/ tests/ brain/ studio/ -q
```

---

## ۶. اولین قدمِ تو

۱. اول `python -X utf8 _ops\tests\run_all.py` بزن تا baseline ببینی (باید ۲۵۲۶+ سبز + ۱ fail از پیش‌موجود).
۲. بعد `git status` ببین کیا uncommitted هستن از این جلسه (flags.cmd غایب چون gitignored).
۳. اگه مالک G0 رو امضا زد، فعال‌سازیِ acquisition شروع می‌شه. وگرنه، روی پایداری و data sources کار کن.

---

## ۷. آنچه ساخته **نمی‌شود** (صداقت)

- **AGI معامله‌گر واقعی** — کسی نمی‌تونه. چیزی که هست: یه سیستمِ تصمیم‌یار با مغزِ پولیِ اختاپوس.
- **auto-post به پلتفرم** — طراحیِ ساختاری propose-only (ToS + ban).
- **مشتری واقعی بدونِ G0** — قانوناً و ساختاراً قفل.
- **امضای به‌جای آدم** — مطلقاً ممنوع.

---

*ساخته‌شده ۲۰۲۶-۰۷-۲۵ بر پایهٔ: getMe/getChat از API تلگرام، Get-CimInstance،
خواندنِ مستقیمِ flags.cmd/state/ledger، اجرایِ واقعیِ هر دو سوئیت.*
*هر عددی اینجا هست، سنجیده شده. هیچ حدسی در کار نیست.*
