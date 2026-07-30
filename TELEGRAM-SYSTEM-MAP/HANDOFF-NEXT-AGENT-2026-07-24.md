# HANDOFF → ایجنت بعدی — جلسهٔ 2026-07-24 (ارگانیسم اختاپوس)

> نویسنده: GLM-5.2 (این جلسه) · هماهنگ با: Opus 4.8 (مافوق، موازی).
> منبعِ واحدِ حقیقت: `master @ c3ffff4`.
> تاریخ: 2026-07-24 ~16:00.

---

## ۰. مهم‌ترین چیز اول — وضعیتِ موازی‌بودن

**دو ایجنت هم‌زمان روی همین repo کار کردیم.** Opus 4.8 (مافوق) زیرساختِ AGI را روی
`claude/c7-continuity` → `master` ساخت. من روی شاخه‌های جدا کار می‌کردم. آخرین توافق:
**master @ c3ffff4 منبعِ حقیقت است؛ فقط یک نویسنده در لحظه master را حرکت دهد.**

قواعدِ سخت برای تو:
- `main` وجود ندارد — از `git checkout main` استفاده نکن (fail می‌شود). از `master` استفاده کن.
- قبل از هر تغییر: `git log --oneline -1 master` بزن تا ببینی HEAD کجاست (شاید جلو رفته باشد).
- کارت را روی **شاخهٔ جدا** بزن، نه مستقیم روی master، مگر اینکه مطمئن شوی کسی دیگر نمی‌نویسد.

---

## ۱. آنچه Opus (مافوق) ساخته — روی master @ c3ffff4

این زیرساخت، مبنای حقیقت است. **کارِ من مکملِ این است، نه جایگزین.**

| ماژول | نقش | وضعیت |
|---|---|---|
| `_ops/brain_worker.py` (۶۲۰ خط) | tick-decoupling: poolِ workerهای event-driven، WorkQueue، StateLatch، ۳-لایه crash isolation + per-thread circuit breaker | روی master، **dormant** (فعلاً به organism.py وصل نیست) |
| `_ops/c6_state_machine.py` | lifecycle یکپارچهٔ reproduction: PROPOSED→RUNNING→VERIFIED→PENDING_ADMISSION→**ADMITTED→TRANSPLANTED** + leaves. transition journal در `state/c6/state-machine.jsonl` + DecisionReceipt per edge. fail-closed edge table. `test_c6_state_machine 8/8` | روی master |
| `_ops/c6_trigger.py` (۳۰۰ خط) | runtime trigger روزانهٔ C6 (recover شده از کارِ من b633efb + lifecycle). فرضیه از صف → آزمایش → RFC card propose-only | روی master |
| `_ops/legs/agent_gateway_http.py` + `agent_bearer.py` | AgentGateway v1: loopback، owner-issued bearer (expiry + anti-replay)، schema بسته، peer=UNTRUSTED_DATA، v1 فقط read-only discovery/share. `test_agent_gateway_redteam 11/11` | روی master |
| `model_router.py` TASK_TIERS گسترش‌یافته | ۶ organ work-type به router اضافه شد | روی master |

---

## ۲. آنچه من ساختم — unique contribution (هنوز روی master نیست)

### 🌟 اصلی‌ترین: `event_bridge.py` — مسیرِ push تلگرام
شاخه: `claude/octopus-event-bridge-aligned @ 5fb7397`. **هنوز روی master نیست (cherry-pick/rebase لازم).**

**مسئله:** `center.py` فقط pull-based است (`run_once` poll + `beat` که فقط status/digest edit می‌کند).
هر رویدادِ بحرانی در فایل می‌خوابد و مالک فقط با `/start` می‌بیندش.

**راه‌حل:** `_ops/telegram_center/event_bridge.py` — ۴ منبع را هر beat می‌خواند و به مالک push می‌کند:

| # | منبع | فیلتر | هماهنگی با Opus |
|---|---|---|---|
| ۱ | `governor-alerts.md` | واژگانِ بحرانی (circuit/protective/fail/...) | brain_worker.py:194,205 همین‌جا می‌نویسد → **worker panicها خودکار flow می‌کنند** |
| ۲ | `events.jsonl` | incident.opened/contained + task.failed | مستقل |
| ۳ | `ORGANISM-STATE.json` protective_mode | edge-triggered (فعال‌سازی + بازیابی) | مستقل |
| ۴ | `c6/state-machine.jsonl` | ADMITTED/TRANSPLANTED/QUARANTINED/DENIED/REJECTED | **مستقیم به c6_state_machine.py:56 او وصل** — تولدِ نسلی push می‌شود |

**امنیت:** dedup با byte-offset cursor (restart-safe)، rate-limit سخت (۱۰/ساعت)، `_scrub` redaction، fail-soft (§۴). پشتِ `OCTOPUS_WIRE_EVENT_BRIDGE` (پیش‌فرض خاموش).
**center.py:** متد `push_alert(text)` + hook در `beat()` (~L493).
**تست:** functional (۴ منبع، ۵ push، dedup، edge-detect) سبز. تلگرام تست‌ها سبز. held-out: فقط ۲ pre-existing failure (heartstate).

### سایر شاخه‌های من (کارِ قدیمی‌تر، بعضی‌شان supersede شده‌اند توسط Opus):
- `claude/octopus-fugu-everywhere @ 976ef82` — governor+heart-doctor به router. **Opus این را کامل‌تر زد** (TASK_TIERS روی master).
- `claude/octopus-tick-decoupling @ 975f323` — probe instrumentation. **Opus brain_worker.py کامل‌تر زد.**
- `claude/octopus-beat-parallel @ 349ffd3` — organ parallelism.
- `claude/octopus-reproduction-c6 @ b633efb` — C6 trigger. **Opus recover + lifecycle زد** (c6_trigger + c6_state_machine روی master).

**پس:** شاخه‌های fugu/tick/C6 من توسط Opus **supersede** شده‌اند. فقط **event_bridge** unique است.

### سند: `TELEGRAM-SYSTEM-MAP/`
- `E-state-config-tokens.md` — اسکنِ فنیِ پیکربندیِ تلگرام (فقط‌خواندنی، دقیق).
- `01-INTEGRATION-CHECKLIST.md` — چک‌لیست ۱۶ نقطهٔ گسست + ۴ فاز + شبه‌کد event_bridge. **با منبع ۴ (c6) به‌روز نشده** — بعد از merge کامل کن.
- `HANDOFF-NEXT-AGENT-2026-07-24.md` — همین فایل.

---

## ۳. حقایقِ مهمِ تصحیح‌شده (صادقانه)

1. **یادگیری از ۲۳ جولای روشن بود** — flagهای `OCTOPUS_WIRE_MEMORY_GATE=1` + `OCTOPUS_WIRE_VERDICT_OUTCOME=1` در `OCTOPUS-flags.cmd`. proof-of-life ثابت کرد حلقه کار می‌کند.
2. **«ترمزِ ۳۰۰s» دقیق نبود** — کفِ tick زنده ۶۰s است (cardiac-allometry). فقط یک beat در paper-full LLM می‌زند (ziman، propose-only).
3. **lead-naghshi ۶۰ رویداد** selfheal امروز دارد (نه ۴ — تصحیحِ خلاصهٔ قبلی). fail-storm واقعی.
4. **DEEPSEEK_API_KEY غیرفعال است ولی مغز کر نیست** — model_router از Fugu/GLM استفاده می‌کند، هر دو کلید حاضرند.
5. **اولین baseline من subset بود** — کلِ run_all = ۲ failure از قبل موجود (heartstate، اثبات‌شده روی clean parent).

---

## ۴. گام‌های بعدیِ پیشنهادی (به ترتیبِ ارزش)

1. **event_bridge را به master بیاور.** cherry-pick `5fb7397` روی master، یا rebase شاخه‌ام روی master.
   فقط `_ops/telegram_center/event_bridge.py` (جدید) + `_ops/telegram_center/center.py` (۲ نقطه: push_alert + hook). conflict بعید.
2. **فعال‌سازیِ probe + event_bridge** (هر دو flag-off پیش‌فرض): `OCTOPUS_TICK_TIMING=1` + `OCTOPUS_WIRE_EVENT_BRIDGE=1` در `OCTOPUS-flags.cmd` + restart. سپس دادهٔ واقعی جمع کن.
3. **wire کردنِ brain_worker به organism.py** — Opus گفته "deferred to debug". این بزرگ‌ترین گامِ سرعت است. نیاز به پرچم `OCTOPUS_WIRE_TICK_WORKERS`.
4. **چک‌لیست را با منبع ۴ به‌روز کن** (`01-INTEGRATION-CHECKLIST.md` هنوز ۳ منبعه).
5. **تولیدِ incident واقعی** — `incident.opened/contained` صفر caller تولیدی دارد. باید producer ساخته شود (نقاط ۳/۴ چک‌لیست).

---

## ۵. قواعدِ سخت (برای همهٔ کارها)

1. ارگانیسم زنده را restart نکن مگر با رأیِ صریحِ مالک. genome/ledger/.env/budget/kill-switch هرگز دست نخورده.
2. هر تغییری پشتِ flag، additive، با held-out. برگشت = flag=0.
3. یک نویسنده در لحظه روی master. کارت را روی شاخهٔ جدا بزن.
4. صفر secret در کد/log/patch. `.env` فقط نام کلید.
5. fail-soft: شکستِ هر organ → alert + ادامه.
6. گیت‌های پولی (`ACTIVATION-*.flag` + organ_gate) هرگز دور زده نشوند.

---

## خلاصهٔ یک‌خطی
Opus زیرساختِ AGI (brain_worker، C6 lifecycle، agent_gateway) را روی master ساخت؛
من **event_bridge** (مسیرِ push تلگرام، ۴ منبع شامل تولدِ نسلی C6) را ساختم که unique است
و منتظرِ merge به master است. همه‌چیز پشتِ flag، additive، با held-out سبز.
