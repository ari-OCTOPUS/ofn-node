---
type: mega-prompts
wave: 1
date: 2026-07-24
parent: OCTOPUS-PARALLEL-COMPLETION-PLAN-2026-07-24
note: "هر بخش یک پرامپتِ standalone برای یک ایجنتِ مستقل. موازی قابلِ اجرا (فایل‌های مختلف)."
---

# 🌊 موجِ ۱ — مگا-پرامپت‌های مستقلِ کم‌ریسک

> **قوانینِ مشترک (در همهٔ WSها صادق):** منبعِ حقیقت = کد+git · safe-patch protocol (بکاپ → `assert count==1` → `compile()` → دو `sha256` → `try/except`) · TCB دست‌نخورده (پول/کلید/genome/kill-switch) · کار در worktreeِ ایزوله · flag-off = رفتارِ قبلی · `_ops/tests/run_all.py` سبز بماند · kill-switch محترم.

---

## WS-2 — اعمالِ ۵ فیکسِ باگِ قلب

**نقش:** مهندسِ ارشدِ سیستم‌های زنده. **مأموریت:** ۵ فیکسِ راست‌آزمایی‌شدهٔ قلب را از برنچِ منبع به ارگانیسمِ زنده منتقل کن، بدونِ رگرسیون.

**منبع:** برنچ `claude/heart-vessels-debug-52687c` (commitها: `aecc256`, `57d1225`).
**فایل‌ها:** `_ops/cardiac.py`, `_ops/heart/control_law.py`, `_ops/heart/doctor_setpoint.py`, `_ops/heart/heartstate.py`, `_ops/heart/work_pump.py`, `_ops/wiring.py` + تست‌ها: `test_cardiac_allometry.py`, `test_heart_control.py`, `test_heart_loop.py`, `test_heart_work.py`, `test_phase1_envelope.py`.
**۵ باگ:** (۱) capِ مالک، (۲) cadence بعد از restart، (۳) نشتِ sys.path، (۴) ایزولاسیونِ تست، (۵) صداقتِ heartstate.

**گام‌ها:**
1. `git worktree add ../wt-ws2 claude/heart-vessels-debug-52687c` (ایزوله).
2. دیف را بخوان: `git diff master...claude/heart-vessels-debug-52687c -- _ops/heart _ops/cardiac.py _ops/wiring.py`.
3. **برای هر یک از ۵ فیکس** جدا تأیید کن که در master نیست (اگر بود، رد کن — دوباره‌کاری نکن).
4. هر فیکس را با safe-patch protocol روی درختِ زنده اعمال کن. این‌ها **تصحیحِ باگ‌اند** (نه فیچر) → معمولاً مستقیم، نه پشتِ فلگ؛ ولی «صداقتِ heartstate» و «cadence بعد از restart» را با دقتِ رفتاری بررسی کن.
5. `python _ops/tests/run_all.py` → باید کاملاً سبز بمونه + ۵ تستِ قلب pass.
6. یک هوکِ heartstate/cadence رفتارِ زنده را عوض می‌کنه؟ اگر آره، behind `OCTOPUS_WIRE_HEART_FIX=0` و تصمیمِ arm با مالک.

**پذیرش:** run_all سبز · ۵ تستِ قلب سبز · رگرسیونِ صفر با flag-off · گزارشِ «کدام فیکس تازه بود، کدام از قبل در master».

---

## WS-3 — یکسان‌سازیِ call-siteهای LLM روی model_router

**مأموریت:** فراخوان‌های مستقیمِ LLM در governor و heart-doctor را به `model_router` منتقل کن (flag-gated، additive)، تا مسیرِ مدل واحد و قابلِ‌رصد شود.

**منبع:** برنچ `claude/octopus-fugu-everywhere` (commit `976ef82`). ماژولِ router: `_ops/cortex/model_router.py` (اگر در master نیست، از برنچ `claude/fail-closed-human-guard` بیاور — همان‌جا هم هست).
**فایل‌ها:** `_ops/budget/governor_epoch.py`, `_ops/heart/doctor_setpoint.py`.

**گام‌ها:**
1. worktree ایزوله از `claude/octopus-fugu-everywhere`.
2. تأیید کن `_ops/cortex/model_router.py` در master هست؛ اگر نه، اول آن را additive اضافه کن (inert تا import).
3. دیف call-siteها را بخوان: `git diff master...claude/octopus-fugu-everywhere -- _ops/budget/governor_epoch.py _ops/heart/doctor_setpoint.py`.
4. با safe-patch، هر call-site را **پشتِ فلگِ `OCTOPUS_WIRE_MODEL_ROUTER=0`** بگذار: flag-on → router، flag-off → مسیرِ قبلی (رفتارِ دقیقاً یکسان).
5. تست: `run_all` سبز + یک تستِ کوچک که flag-off مسیرِ قبلی و flag-on router را می‌زند.

**پذیرش:** flag-off صفر تغییر · flag-on همهٔ LLMها از router رد می‌شوند (قابلِ‌رصد در governor epoch) · هزینه/مدل در یک‌جا.
**ریسکِ vendor lock-in:** model_router باید مستقل از provider بماند (DeepSeek/GLM/Ollama) — abstraction را نشکن.

---

## WS-4 — رصدِ tick-timing (instrumentation، صفر تغییرِ رفتار)

**مأموریت:** probeِ زمان‌بندیِ فاز را اضافه کن تا زمانِ هر فازِ tick قابلِ‌اندازه‌گیری شود — بدونِ هیچ تغییری در رفتار.

**منبع:** برنچ `claude/octopus-tick-decoupling` (commit `975f323`).
**فایل‌ها:** `_ops/tick_timing.py` (نو، خالص/inert)، probe در `_ops/organism.py`.

**گام‌ها:**
1. worktree ایزوله.
2. `_ops/tick_timing.py` را additive اضافه کن (stdlib خالص، بدونِ side-effect تا import).
3. probe در `organism.py` را با safe-patch **پشتِ `OCTOPUS_WIRE_TICK_TIMING=0`** بگذار — flag-off یعنی هیچ فراخوانی، صفر overhead.
4. تست: run_all سبز · flag-on یک state/تایمینگِ کوچک تولید کند، flag-off هیچ.

**پذیرش:** صفر تغییرِ رفتار (این فقط measurement است) · flag-on دادهٔ فاز-تایمینگ می‌دهد · overhead ناچیز.
**Add-on (اختیاری):** خروجی را به صفحهٔ observability/① تلگرام وصل کن (فقط‌خواندنی).

---

## WS-6 — پکِ امنیتیِ M1–M7 (now_moves، additive/flag-off)

**مأموریت:** ۷ ماژولِ امنیتیِ additive را نصب و پشتِ فلگ وصل کن. همه inert تا import، صفر تغییرِ رفتارِ زنده تا arm.

**منبع:** برنچ `claude/fail-closed-human-guard` (پکِ M1..M7).
**ماژول‌ها (`_ops/now_moves/`):** `ledger_integrity_probe` (M1), `staleness_stamp` (M2), `cortex_symmetric_revive` (M3), `unified_bus_guard` (M4), `kill_seam_closer` (M5), `module_self_manifest` (M6), `route_scorer_shadow_log` (M7). لمس‌شده: `_ops/cortex/model_router.py`, `_ops/budget/organ_gate.py`, `_ops/debate/debate_loop.py`.

**گام‌ها:**
1. worktree ایزوله از `claude/fail-closed-human-guard`.
2. برای هر ماژول: تأیید کن در master نیست → additive کپی کن → `python _ops/now_moves/<m>.py` (smoke سبز).
3. وصلِ هرکدام پشتِ فلگِ جدا (`OCTOPUS_WIRE_M1..M7=0`)، با safe-patch. flag-off = رفتارِ قبلی.
4. **verify-first add-on (cranky-chandrasekhar):** anti-replayِ پول (`approvalِ تک‌مصرف/consume اتمیک/TTL/action-id سوخته`) در `_ops/budget/approval_channel.py` + `channels/approval_store.py`. **⚠️ TCB-adjacent:** اول با master دیف بگیر؛ اگر anti-replay آنجا نیست، این یک **ارتقای امنیتیِ مهم** است — ولی چون مسیرِ پول را لمس می‌کند، **فقط پشتِ فلگ + تأییدِ صریحِ مالک**.
5. تست: run_all سبز + تست‌های هر ماژول (`test_module_self_manifest`, `test_route_scorer_shadow_log`, `test_kill_seam_closer`, ...).

**پذیرش:** ۷ ماژول نصب + تست‌سبز · همه flag-off (صفر رفتارِ زنده) · anti-replay فقط پس از تأییدِ مالک · `kill_seam_closer`/`unified_bus_guard` با kill-switchِ موجود تداخل نکنند (هماهنگ، نه رقیب).

---

*بعد از موجِ ۱: موجِ ۲ (C6 · lead-gen · infra) و زیرپروژه‌ها (Project-F · Ziman · Painting-OS).*
