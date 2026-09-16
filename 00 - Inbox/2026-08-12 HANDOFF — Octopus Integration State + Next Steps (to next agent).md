---
type: handoff
status: active
updated: 2026-08-12
tags: [octopus, handoff, integration, git, restart]
---

# HANDOFF به ایجنت بعدی — وضعیت ادغام اختاپوس + مراحل بعدی (2026-08-12)

> این سند توسط ایجنتِ کشف/ادغام نوشته شده تا ایجنت بعدی (موازی یا آینده) بدون
> از دست دادن زمینه، ادامه دهد. **قبل از هر ریاستارت/کامیت این را کامل بخوان.**

---

## ۱) چیزی که تا الان انجام شده (تاریخچهٔ کامیتها روی master)

| کامیت | موضوع |
|---|---|
| `a428326` | feat(memory): ۱۲ ماژول حافظه/آگاهی/بازیابی + وایرینگ (brain_pulse, owner_recall, session_memory, shadow_evaluation, shadow_influence, unified_context, retrieval_router, self_loop_ingest و…) |
| `165c3db` | feat(cortex): قفل apply + گیت low-risk خودکار (ADR-035 dual-mode) + runner_apply_gate + pain_assessment |
| `9bc7b91` | feat(organism): سیمهای DW — seed_beat + kernel_bridge_reader + sleep clamp (ADR-036) |
| `55720f7` | feat(owner-console): collab روی DeepSeek + discovery UI + رفع timeout های collab |
| `6f97ac2` | feat(legs/doctor): leg_feed + spectral v2 + criticality + اسکریپتهای verify |
| `272a67b` | docs: ۱۷۳ فایل شواهد/vault (adr-033 reports, SESSION ها, ADR-033..036) |
| `73d50f0` | chore: state های tracked بهروز + .gitignore جدید + غریبهها (_ops/cognitive و…) |
| `dc21485` | merge(collab): ادغام branch همکار با `-X ours` — ۱۵ فایل یکتا آمد (BETA-ALLOWLIST, ONBOARDING, telemetry code…) |
| `c53bee8` | fix(ops): پاکسازی فلگ کهنهٔ GITWRITE-FAILED (قفل gitwrite.lock از قبل آزاد بود) |

### وضعیت فعلی git (نکات مهم)
- **HEAD = `c53bee8`**؛ اما `.gitignore` هنوز `M` است (ویرایشِ حذفِ `_ops/telemetry/` از ignore — چون کد OTel واقعی است) + **۳ فایل untracked telemetry** که باید کامیت شوند:
  - `_ops/telemetry/alloy_sog.alloy.example`
  - `_ops/telemetry/neural_apply_evidence.py`
  - `_ops/telemetry/sog_metrics_v2.py`
- `out2.txt` / `out_utf8.txt` (ریشهٔ repo): **عمداً untracked** رها شدند (خروجی debug) — کامیت نکن.
- `_ops/seed_beat.py` با `git add -f` کامیت شد — الگوی امنیتی قدیمی `*seed*` در .gitignore با آن تداخل دارد؛ فایلهای seed-دار جدید نیاز به `-f` دارند.
- **قاعدهٔ طلایی: فقط یک ایجنت در لحظه عملیات git انجام دهد** — همان بیماری index.lock که GITWRITE-FAILED میساخت. اگر `F:\backup\.git\index.lock` گیر کرد و پروسهٔ git زندهای نبود، حذفش کن.

### .gitignore جدید چه میکند
- runtime های untracked زیر `_ops/state/` (session/, cockpit_brain/, seed/, telemetry/state, instant-*, ORGANISM-STATE.*, adr-033/events|evidence|proposals|quarantine|replay, epochs/…) + فلگهای `STOP-*`/`HALT-ALL`/`RESTART-*` + `*.sqlite3-wal/shm` + `*.lock` → دیگر در status ظاهر نمیشوند.
- طبق رأی مالک: **فایلهای state که از قبل tracked اند، tracked میمانند** (۲۹۴ فایل) — تغییراتشان در کامیتها میآید.

---

## ۲) وضعیت runtime (خیلی مهم)

### پروسهها
- **همهچیز متوقف است** (organism, cortex, center, live) — با فلگهای:
  `_ops/STOP-ORGANISM`, `_ops/STOP-CORTEX`, `_ops/STOP-TG-CENTER`, `_ops/STOP-CODE-AUTONOMY`, `_ops/HALT-ALL`
- **فقط** اینها زندهاند:
  - `miniapp_gateway.py` (PID متغیر — واتداگِ داخل `_ops/telegram_center/run-miniapp-tunnel-named.ps1` مدام ریاسپاونش میکند؛ **فلگهای STOP را دور میزند چون مستقیم spawn میکند**)
  - تانل cloudflared (همان ps1)
- واتداگهای جداگانه هم هستند: `_ops/live-watchdog.ps1`, `_ops/tg-center-watchdog.ps1` → اگر خواستی کامل متوقف کنی، خودِ این ps1 ها را هم باید بکشی (نه فقط پایتونها).

### ⚠️ معمای باز (اولویت بررسی)
بعد از merge، ~۱۲ فایل `M` ظاهر شد که معلوم نیست **چه کسی نوشتهشان** (بررسی mtime من ناتمام ماند):
- `_ops/telegram_center/miniapp_state.py` (فیکس SoT: `agent-prompts/_PROJECT_INSTRUCTIONS.md` + فیکس مسیر CURRENT-TRUTH)
- `_ops/state/owner-goal.json` (رأی مالک ۰۸-۱۲: «سقف خرج فعلاً متغیر» — do_not_change_flags)
- SESSION های `00 - Inbox`, `06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md`, `_memory/HEARTBEAT.md`, `_ops/GOALS-OCTOPUS.md`, `_ops/state/reach/{ledger,probes}.jsonl`, لاگهای watchdog
- محتوایشان واقعی و مستدل است (کامنتهای تاریخدار). **نویسنده را پیدا کن** (mtime فایلها + پروسههای زندهٔ gateway/تانل) و بعد تصمیم: کامیتشان کن یا اگر پروسهای زنده دارد مینویسد، اول متوقفش کن.

### سهمیهٔ LLM پولی
- امروز **تمام شده**: `quota_daily-cap` با `quota_used=64` — همهٔ تماسهای paid از ~۱۶:۲۰ بلاکاند (فایل `_ops/state/paid-calls.jsonl`).
- deep-think های امروز به local fallback افتادهاند (`fallback_from: paid-call-failed`).
- **تا ریست نیمهشب، مغز ارگانیسم local-only است** — انتظار واقعبینانه داشته باش.

---

## ۳) مراحل بعدی (به ترتیب)

1. **کامیت باقیماندهها** (یک کامیت کوچک): `.gitignore` (حذف `_ops/telemetry/` از ignore — کد واقعی OTel) + ۳ فایل untracked telemetry. پیام: `fix(ops): unignore _ops/telemetry (real OTel code) + commit telemetry modules`
2. **حل معمای M فایلها** (مطابق بخش ۲): mtime → نویسنده → کامیت یا توقف نویسنده.
3. **اجرای تستها قبل از ریاستارت** — حداقل سوئیتهای کلیدی:
   `python _ops/tests/run_all.py` یا دستی: `test_chatbox_unified`, `test_adr033_control_plane`, `test_adr035_neural_rearm`, `test_phantom_guards`, `test_collab_components`, `test_phase_jn`
   (شواهد: `_ops/state/adr-033/reports/INTEGRATION-WAVE-2026-08-11/` سبک قبلی)
4. **ریاستارت کامل** به این ترتیب:
   - پاک کردن فلگها: `rm _ops/STOP-ORGANISM _ops/STOP-CORTEX _ops/STOP-TG-CENTER _ops/STOP-CODE-AUTONOMY _ops/HALT-ALL`
   - اجرا (از `F:\backup\_ops`): `RUN-ORGANISM.bat` (پورت 8771) → `RUN-CORTEX.bat` (8772) → `telegram_center\RUN-TG-CENTER.bat` → `run-live-headless.bat` → `telegram_center\run-miniapp-tunnel-named.ps1`
   - **تأیید:** پورتها 8771/8772/8774/8790 بالا؛ beat جدید در `_ops/state/pulse/beat-state.json`؛ فلگهای rearm در `_ops/state/flags-loaded-cortex.json` (AUTONOMY_FREE=1, CODE_AUTOAPPLY_LOWRISK=1, IMPROVE_REFRACTORY_H=0)؛ ماژولهای جدید فعال: `_ops/state/seed/beat-latest.json` (هر ۱۷/۲۳ beat)، `_ops/state/kernel-bridge-reader-report.json` (هر ۱۱ beat)، brain_pulse در `_ops/state/cockpit_brain/latest.json` و telemetry های چت
5. **پس از ریاستارت:** تأیید حافظه (memory-consolidate هر ~۱۰ دقیقه → `_ops/state/semantic_memory.jsonl` رشد میکند)، discovery digest، و اینکه **چکپوینت خودکار دوباره کار میکند** (کامیت بعدی خودش زده شود — GITWRITE الان سالم است؛ اگر دوباره `GITWRITE-FAILED.flag` ساخت، یعنی قفل واقعی است: چک کن کدام پروسه git زنده است)
6. **(اختیاری) ریشهٔ فلگ ۰۸-۱۱:** germline-hourly.ps1 ساعت ۰۳:۳۱ قفل را ۴۰ بار نتواست بگیرد — احتمالاً رقابت با پروسهٔ زنده در آن ساعت. بعد از ریاستارت، یک دور `04 - Architect System/scripts/germline-backup.ps1` بزن و نتیجه را ببین.

---

## ۴) نقشهٔ مختصر معماری (برای پیمایش سریع)
- `_ops/organism.py` — قلب (beat ~۸ دقیقه؛ wire های DW-02/03/05)
- `_ops/cortex/` — مغز (cortex.py :8772, code_brain, code_autonomy, improve)
- `_ops/memory/` — حافظهٔ جدید (brain_pulse, owner_recall, session_memory, unified_context, retrieval_router)
- `_ops/telegram_center/` — چت/پنل (center.py, miniapp_gateway.py, ask_brain.py, miniapp/)
- `_ops/state/` — runtime (pulse/, c6/, doctor/, adr-033/reports = شواهد)
- `_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/` — تصمیمهای مالک امروز (disarm → rearm)
- `04 - Architect System/scripts/` — germline/gitwrite/health-check
