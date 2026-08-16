---
type: knowledge
status: active
tags: [octopus, discovery, unwired, dead-path]
created: 2026-08-16
updated: 2026-08-16
created_by: agent
sources:
  - "[[06-EVIDENCE/DEEP-TEST-1H-2026-08-16]]"
  - "[[00 - Inbox/2026-08-15 DISCOVERY — Hidden Capabilities Catalog]]"
---

# DISCOVERY — Unwired & Dead Paths Catalog (کلاس ۹)

> **نقض = توقف:** فلگ روشن نشد · TCB لمس نشد · send/pay/exec نشد · حذف صفر.
> **روش:** فکت‌چک پیش‌فرض در برابر درخت زنده · `orphan_scan.py` · AST/rg نماد-محور روی `4d_system` (خارج از `nbb-cp-kre`/`src`) · تسک‌های ویندوزی · لاگ اثر ۷روزه.
> این کلاس **نهم** کاتالوگ ۰۸-۱۵ است: کد کامل با صفر فراخوان تولیدی، یا مسیر با ادعای اثر و اثر صفر.

## فکت‌چک پیش‌فرض‌ها (C-015/C-018)

| پیش‌فرض مگاپرامپت | درخت زنده 2026-08-16 ~11:3x | حکم |
|---|---|---|
| ConsolidationCycle صفر فراخوان در automation/daemon | تأیید: فقط `tests/test_consolidation_delta_r18.py` | ✅ |
| فایل تولیدی ۱ ردیف/۱ سیکل | **۳ ردیف** — سیکل ۲–۳ دیپ‌تست 10:35 (r18-degraded → delta-zero) | ⚠️ عدد کهنه شد |
| شوراها صفر فراخوان تولیدی | تأیید: فقط تست + `councils_real.py` که خودش فقط از تست صدا می‌شود | ✅ DEAD-BY-DESIGN |
| http.server روی 8765 | LISTENING pid 5780 از 14-08 12:20 · GET timeout · parent مرده | ✅ عضو اعلان‌نشده + مسیر مرده |
| ۵ عضو + دیمون 4d نسل ۳ pid تازه enforce مسلح | ۵ پایتون `_ops` + daemon 27164 + http.server 5780 | ✅ + عضو ششم ناشناس |
| C-019 آزاد | تخصیص این نشست؛ recall C-021 · errorhunt C-022 · update-debug C-023/C-024 | ✅ برخورد نام حل شد · آزاد **C-025** |
| تسک Tick بعداً ساخته شد | Ready · LastRun هرگز · LastResult 267011=HAS_NOT_RUN · Action=`py` (همان الگوی FILE_NOT_FOUND) | ⚠️ containment روی کاغذ؛ اثر هنوز صفر |
| `_ops` ConsolidationCycle هم بی‌فراخوان است | **نقض:** `wiring.py` `make_neural_stack` + ۶۲۵ سیکل در `_ops/neural/consolidation.json` | ⚠️ فورک 4d وصل نیست؛ اصل `_ops` زنده است |

ارگانیسم: beat **37781** · coherence 0.972 · halted=False · HEAD CURRENT-TRUTH `bfc673f`.

---

## جدول طبقه (خلاصه)

| طبقه | شمار (کف) | نمونه‌های برتر |
|---|---|---|
| NEVER-WIRED | ۱۲ نماد/ماژول وزن‌دار در 4d + ۱۸ ماژول weighty `_ops` (کلاس ۵ کاتالوگ ۰۸-۱۵) | `ConsolidationCycle` (4d) · `suggest_next_experiment` · `Supervisor` · `run_meta_research` (فقط UI) |
| DEAD-BY-DESIGN | ۸ نماد شورا + `telegram_bot` 4d (opt-in/۴۰۹) | `ArchitectureCouncil` · `EpistemicCouncil` · `ProtocolRunner` · `PepEndpoint` |
| ORPHANED / گیت همیشه-بسته | ۴ مسیر اثر | `git_watcher.check_and_trigger` پشت `SELF_CODE_ENABLED=0` · digest تلگرام 4d `not-configured` · poisoning-watch LastResult FILE_NOT_FOUND · http.server 8765 آویزان |
| زنده با اثر واقعی (کنترل) | ۳ | tg-send ۷روزه ۲۰۱۱ · paid-calls ۷روزه ۲۰۸۱ · `_ops` neural consolidation ۶۲۵ سیکل |

کف است نه سقف: `orphan_scan` عمداً محافظه‌کار است (هر ابهام → «وصل»).

---

## STEP 1 — استخراج (شواهد فرمان)

### ۱-۱. اسکنر ماژول `_ops` (orphan_scan.v1)

فرمان: `py -X utf8 _ops/orphan_scan.py` → `checked=667 · total=101 · weighty=18` (همان کف کاتالوگ ۰۸-۱۵ کلاس ۵؛ عدد کهنه نشده).

۱۸ weighty (کف یتیم ماژول): `hypothesis_engine/experiments/analysis.py` (422) · `epistemics/benchmark.py` (407) · `state_guard.py` (391) · `scripts/unlock_self_progress.py` (366) · `phase_gate.py` (362) · `legs/agent_gateway_http.py` (353) · `watchdog_extension.py` (257) · `seed/redteam_harness.py` (256) · `legs/budget_frustration.py` (218) · `evidence_plane/seven_day.py` (196) · `legs/books_xero.py` (184) · `outcomes/reconcile_card.py` (137) · `cortex/depth_guard.py` (107) · `budget/drawdown_guard.py` (103) · `doctor/box/primitive.py` (94) · `now_moves/unified_bus_guard.py` (83) · `now_moves/kill_seam_closer.py` (76) · `stop_probe.py` (64).

`state_guard`: تنها ارجاع تولیدی در `evidence_plane/event_log.py` یک **کامنت** است نه import — یتیم می‌ماند.

### ۱-۲. نمادهای عمومی 4d (خارج از تست / nbb-cp-kre)

| نماد | فایل | خطوط تقریب | فراخوان غیر-تست | mtime |
|---|---|---|---|---|
| `ConsolidationCycle` | `brain/consolidation.py` | ~330 | **۰** (فقط تست R18) | 2026-08-16 (ERRATA docstring) |
| `ArchitectureCouncil` / `EpistemicCouncil` | `councils/councils_phase1.py` | ~20 | ۰ تولیدی؛ `councils_real` فقط تست | 2026-08-16 |
| `ProtocolRunner` / `CouncilRouter` / `PepEndpoint` / `LeaseToken` | `councils/*` | — | ۰ تولیدی | 2026-08-16 |
| `Supervisor` | `control_plane/supervisor.py` | ~400 | فقط `__main__` + تست؛ **نه daemon، نه schtask** | — |
| `suggest_next_experiment` | `brain/auto_experiment.py` | ~119 | **فقط خودش** | — |
| `run_meta_research` / `WebResult` | `brain/meta_research.py` · `web_research.py` | — | فقط `ui/tab_meta.py` + `__main__`؛ UI در پروسه‌ها نیست | — |
| `KernelConsumer` | `brain/kernel_consumer.py` | — | **وصل:** daemon tick%30 + automation | — |
| `AutoLoopEngine` | `brain/autoloop.py` | — | **وصل:** AutomationController | — |
| `_ops.neural.ConsolidationCycle` | `_ops/neural/consolidation.py` | — | **وصل:** `wiring.make_neural_stack` · ۶۲۵ سیکل | mtime 05:30 |

### ۱-۳. تسک‌های ویندوزی → آیا به کاندیدها می‌رسند؟

| تسک | State | LastRun | LastResult | Action | به ConsolidationCycle؟ |
|---|---|---|---|---|---|
| OCTOPUS Observatory Hourly | Ready | 11:06 امروز | 0 | `python.exe` مطلق → `run_observatory.py` (Desktop) | خیر |
| OCTOPUS 4d Consolidation Tick | Ready | **هرگز** (1999) | **267011 HAS_NOT_RUN** | `py -X utf8 …\consolidation_4d_tick.py` | بله — ساختهٔ ایجنت recall ~11:5x؛ هنوز شلیک نشده |
| OCTOPUS 4d Poisoning Watch | Ready | 10:08 امروز | **2147942402 = FILE_NOT_FOUND** | `py -X utf8 …\poisoning_watch_4d.py` | خیر (پایش است نه consolidation) |
| OCTOPUS-doctor-day | Ready | 07:00 | 0 | `run_doctor_day.py` | خیر |
| germline-hourly | Ready | 10:49 | 0 | `germline-hourly.ps1` | خیر |
| ۵ watchdog (center/cortex/live/miniapp/organism) | Ready | ~11:1x | 0 | ps1 نگهبان | خیر |
| OCTOPUS-Cockpit-Brain | Ready | 11:17 | 0 | `cockpit-brain-run.ps1` | خیر |
| OCTOPUS-Observatory | **Disabled** | 15-08 22:36 | 0 | `python run_observatory.py` نسبی | C-014 contained |
| OctopusLiveDataRefresh | Ready | 10:58 | **2147942402 FILE_NOT_FOUND** | bat با مسیر فارسی mojibake | خیر |

**هیچ تسکی تا ~11:4x `brain.consolidation` را نمی‌زد.** از ~11:5x تسک Tick وجود دارد ولی **هنوز اجرا نشده** و لانچر `py` است.

---

## STEP 2 — تفکیک سه‌گانه

### NEVER-WIRED (از تولد بی‌فراخوان)

1. **`4d_system.brain.consolidation.ConsolidationCycle`** — شاهد کلاس. فورک ۰۸-۰۲ از `_ops/neural` که خودش زنده است. docstring تا امروز دروغ می‌گفت «daemon صدا می‌زند». کامیت‌ها: `25ee527` revive · `e51a491` R18 دلتا — هیچ‌کدام `daemon.py` را گره نزدند. ایجنت موازی recall تسک ویندوزی ساخت (C-019 contained روی کاغذ؛ LastRun هنوز هیچ). → [[06-EVIDENCE/UNWIRED-4d-consolidation-2026-08-16]]
2. **`brain.auto_experiment.suggest_next_experiment`** — LLM پیشنهاد آزمایش؛ rg فقط خود فایل.
3. **`control_plane.Supervisor`** — حلقهٔ ۲۴/۷ خودترمیم؛ نقطهٔ ورود `python -m control_plane.supervisor`؛ صفر schtask.
4. **`run_meta_research` / `web_research`** — فقط تب Streamlit؛ پروسهٔ UI در لیست زنده نیست.
5. ۱۸ ماژول weighty `_ops` (کلاس ۵ کاتالوگ ۰۸-۱۵) — هنوز کف یتیم.

### DEAD-BY-DESIGN (سایه/رأی‌خواه)

1. بستهٔ `councils/` — تست‌ها ۱۸+۵+۵؛ `zero_tool_access`؛ router کار ناشناخته را رد می‌کند. تریگر تولیدی عمداً نیست.
2. `4d_system/brain/telegram_bot.py` — DEPRECATED + `OCTOPUS_4D_TELEGRAM_BOT_OPT_IN`؛ خطر ۴۰۹ روی توکن مرکز. daemon آن را import نمی‌کند.

### ORPHANED / گیت همیشه-بسته (ادعای اثر، اثر صفر)

1. **`git_watcher.check_and_trigger`** — کد در daemon هست ولی پشت `SELF_CODE_ENABLED` (پیش‌فرض ۰). state می‌گوید `enabled: true` (`GIT_WATCHER_ENABLED` پیش‌فرض ۱) و `check_count: 0`. ادعا ≠ اجرا.
2. **`notify.flush_digest` → تلگرام 4d** — daemon هر ۲۰ تیک flush می‌کند؛ ۱۸/۱۸ packet = `queued (not-configured)`؛ `sent_today=0` · `queued=24`.
3. **Poisoning Watch 10:08** — تسک Ready است؛ آخرین موفقیت شواهد 05:14؛ LastResult FILE_NOT_FOUND. احتمالاً `py` در PATH نشست Task Scheduler نیست (رصدخانه با `python.exe` مطلق سبز است).
4. **http.server :8765** — از ۱۴ اوت زنده؛ GET timeout؛ parent مرده. → [[06-EVIDENCE/UNWIRED-http8765-2026-08-16]]

---

## STEP 3 — مسیرهای اثر (۷ روز)

منبع: jsonl زنده · برش ۷روزه. جزئیات: [[06-EVIDENCE/UNWIRED-effect-zero-2026-08-16]]

| کلاس اثر | نقطهٔ نهایی | ۷ روز | حکم |
|---|---|---|---|
| send (_ops) | `_ops/state/tg-send-log.jsonl` | ۲۰۱۱ ردیف · ok True 1199 / False 812 | **زنده** |
| pay/LLM (_ops) | `_ops/state/paid-calls.jsonl` | ۲۰۸۱ از ۲۷۳۰ · critic_shadow 148 | **زنده** |
| send سایه PEP | `telegram-pep-shadow.jsonl` | ۲ · `editMessageText` deny-no-lease | سایهٔ زنده (دیپ‌تست) |
| send (4d notify) | `decision_packets.jsonl` | ۱۸ کل · delivered همگی `not-configured` | **اثر صفر** — گیت همیشه-بسته |
| exec (4d self_code) | daemon `proposals_this_run` | ۰ · `SELF_CODE_ENABLED` خاموش (بنر بوت) | گیت بسته (طراحی) |
| write حافظه 4d R18 | `outputs/self_evolved/consolidation.json` | ۳ سیکل دستی؛ صفر از زمان‌بند | **کد زنده، تریگر مرده** |
| write حافظه _ops | `_ops/neural/consolidation.json` | **۶۲۵ سیکل** | **زنده** — دوگانه با 4d |

---

## رتبهٔ وصل (ارزش × بی‌خطری) — حداکثر ۵ کارت

معیار: ارزش اگر وصل می‌شد × احتمال بی‌خطر بودن وصل. TCB/فلگ/پول پایین می‌آید.

### [VOTE 1] ConsolidationCycle 4d — لانچر تسک (`py` → python.exe مطلق)
```
چیستی: ایجنت recall ~11:5x تسک «OCTOPUS 4d Consolidation Tick» ساخت (غیر TCB). LastRun هیچ‌وقت · LastResult 267011=HAS_NOT_RUN. Action هنوز `py` است.
چرا: poisoning-watch با همان `py` در ۱۰:۰۸ FILE_NOT_FOUND گرفت؛ رصدخانه با python.exe مطلق سبز است. بدون این فیکس، Tick در ۱۷:۴۹ همان شکست را تکرار می‌کند.
ریسک: فقط عوض کردن Execute به مسیر مطلق — صفر منطق.
گزینه‌ها: (الف) Action = "C:\Program Files\Python313\python.exe" -X utf8 F:\backup\_ops\audit\consolidation_4d_tick.py (+ همین برای poisoning-watch)
         (ب) یک‌بار دستی با python.exe مطلق برای اثبات
         (ج) رها — اولین شلیک احتمالاً FILE_NOT_FOUND
توصیه: الف+ب
```

### [VOTE 2] شنوندهٔ ناشناس :8765
```
چیستی: python -m http.server 8765 --bind 127.0.0.1 · pid 5780 از 14-08 12:20 · GET timeout · parent مرده.
چرا: عضو اعلان‌نشده (diagnose drift 8/5/2)؛ LISTENING ولی پاسخ نمی‌دهد = سطح حمله + نویز سلامت.
ریسک: کشتن پروسه اثر روی ۵ عضو ندارد (جداست). اگر مالکی دستی برای فایل لوکال بالا آورده، قطع می‌شود.
گزینه‌ها: (الف) شناسایی cwd/مالک سپس kill
         (ب) رها + ثبت در manifest ارگانیسم به‌عنوان undeclared
         (ج) watchdog برای پورت‌های اعلام‌نشده
توصیه: الف پس از یک نگاه cwd (الان WMI parent خالی است)
```

### [VOTE 3] Poisoning Watch — LastResult FILE_NOT_FOUND
```
چیستی: تسک Ready · 10:08 شکست 0x80070002 · شواهد آخر 05:14 موفق.
چرا: پایش R15/C-012 که شورا شرط سایه گذاشت؛ شکست خاموش = متریک مسمومیت کهنه می‌شود.
ریسک: عوض کردن Action به مسیر مطلق python.exe (الگوی Observatory Hourly) صفر تغییر منطق است.
گزینه‌ها: (الف) Action = "C:\Program Files\Python313\python.exe" -X utf8 <مسیر مطلق اسکریپت>
         (ب) رها
توصیه: الف — درس دیپ‌تست: لانچر از منبع رسمی؛ `py` در نشست Scheduled Task PATH ندارد
```

### [VOTE 4] digest تلگرام 4d — صف ۲۴، ارسال ۰
```
چیستی: daemon هر ۲۰ تیک flush_digest؛ ۱۸ packet همگی delivered=not-configured؛ telegram_bot 4d عمداً خاموش.
چرا: ۲۴ رویداد خودمختار هرگز به مالک نمی‌رسد. مرکز _ops send زنده است (۲۰۱۱/۷روز).
ریسک: احیای telegram_bot 4d = ۴۰۹ و بلعیدن دکمهٔ مالک (خود فایل می‌گوید). رله از center مثل دکتر امن‌تر است.
گزینه‌ها: (الف) رلهٔ digest به outbox مرکز (الگوی doctor_link) — رأی
         (ب) پذیرش صف‌فقط‌محلی (داشبورد Streamlit که الان بالا نیست)
         (ج) روشن کردن OCTOPUS_4D_TELEGRAM_BOT_OPT_IN — NO-GO تا تأیید «هیچ پولر دیگری نیست»
توصیه: ب یا الف؛ هرگز ج بدون رأی صریح
```

### [VOTE 5] git_watcher — enabled=true ولی check_count=0
```
چیستی: GIT_WATCHER_ENABLED پیش‌فرض ۱؛ فراخوان check_and_trigger پشت SELF_CODE_ENABLED (۰).
چرا: state دروغ می‌گوید enabled. ادعا≠اثر. جدا کردن پایش از self_code ارزش دارد ولی daemon.py = TCB.
ریسک: هر تغییر daemon.py امضای مجدد می‌خواهد.
گزینه‌ها: (الف) رها + ERRATA در state (همین گزارش)
         (ب) رأی TCB: صدا زدن watcher بدون self_code (فقط propose)
         (ج) نمایش enabled=false وقتی self_code خاموش است
توصیه: الف تا رأی TCB
```

---

## فیکس کم‌ریسک این نشست (بدون رأی، بدون فلگ، بدون TCB، بدون رفتار)

1. ERRATA C-019 روی docstring `brain/consolidation.py` — ادعا دیگر نمی‌گوید daemon صدا می‌زند.
2. بنر ERRATA C-020 روی `4d_system/DEPRECATED.md` — «لانچ نمی‌شود» کهنه است.
3. ثبت C-019 و C-020 در دفتر تناقض‌ها. آزاد بعدی (پس از C-021..C-024 موازی): **C-025**.

تست نو ساخته نشد (تغییر رفتار صفر؛ پین «باید بی‌فراخوان بماند» سیم‌کشی آینده را می‌شکند).

---

## سه پیشنهاد (نه سیم‌کشی)

1. **زمان‌بند R18 را مثل poisoning-watch بساز، نه داخل daemon.py.** فایل consolidation TCB نیست؛ daemon هست.
2. **تلگرام‌بات 4d را revive نکن.** گارد ۴۰۹ درست است؛ صدای واحد = center.
3. **Supervisor 24/7 را بدون رأی start نکن.** spawn/self-heal است؛ schtask هم ندارد.

---

## چک‌لیست مأموریت

- [x] صفر فلگ تازه · [x] صفر حذف · [x] صفر لمس TCB (daemon/automation/telegram_bot/…)
- [x] C-registry C-019 contained + C-020 open · C-021 recall · C-022 errorhunt · C-023/C-024 update-debug · آزاد **C-025**
- [x] کاتالوگ Inbox · شواهد 06-EVIDENCE · 07-HANDOFF · STATE §8
- [ ] push — پس از کامیت `agent-checkpoint`
