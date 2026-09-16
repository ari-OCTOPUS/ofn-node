---
type: mega-prompts
wave: 2
date: 2026-07-24
parent: OCTOPUS-PARALLEL-COMPLETION-PLAN-2026-07-24
note: "موجِ ۲ — متوسط‌ریسک، بعد از سبزشدنِ موجِ ۱. هر بخش standalone برای یک ایجنت."
---

# 🌊 موجِ ۲ — C6 خودبهبودی · lead-gen · control-plane infra

> **قوانینِ مشترک:** منبعِ حقیقت = کد+git · safe-patch (بکاپ → `assert count==1` → `compile()` → دو `sha256` → `try/except`) · TCB دست‌نخورده · worktreeِ ایزوله · flag-off = رفتارِ قبلی · `run_all.py` سبز · kill-switch محترم · **قبل از اجرا: `REAL_VAULT=<worktree>` را پین کن** (وگرنه `opslib.ORG_ROOT` به `F:\backup`ِ زنده می‌رود و به state زنده دست می‌زند — ارگانیسم روی 8771/8772 زنده است).

---

## WS-1 — وصلِ حلقهٔ خودبهبودیِ C6 به ارگانیسمِ زنده  ⚠️ پرمخاطره‌ترین

**نقش:** مهندسِ سیستم‌های خودتغییردهنده + مهندسِ ایمنی. **مأموریت:** مکانیزمِ C6 را طوری به ارگانیسم وصل کن که **پیشنهاد بدهد، هرگز خودکار کدِ زنده را عوض نکند** بدونِ گیتِ مالک.

**منبع:**
- `claude/octopus-reproduction-c6` → `_ops/c6_trigger.py` (نو) + هوکِ `_ops/organism.py` (flag-gated، propose-only).
- `claude/c6-self-improvement-ignition-c73186` → `_sandbox/evolution_v3/proposed_v3_final.patch` (بهبودِ **governed-accepted**: ایندکس‌های ثانویهٔ `memory get()/insert-dedupe`) + `_sandbox/evolution_v4/` (چرخهٔ ۳: pre-registrationِ پیش‌بینی، U=0.85).

**اصلِ ایمنیِ سخت (بالاتر از همه):** یک سیستمِ خودبهبود **هرگز نباید بدونِ تأییدِ صریحِ مالک کدِ زندهٔ خودش را بنویسد**. C6 فقط: (۱) آزمایش در `_sandbox` (ایزوله)، (۲) پیش‌ثبتِ پیش‌بینی، (۳) verifyِ خصمانه، (۴) تولیدِ **پچِ پیشنهادی** + verdict با آستانهٔ U، (۵) **صف برای رأیِ مالک**. هیچ auto-apply.

**گام‌ها:**
1. worktree ایزوله از `octopus-reproduction-c6`.
2. دیف بخوان: `git diff master...claude/octopus-reproduction-c6 -- _ops/c6_trigger.py _ops/organism.py`. تأیید کن هوکِ organism **پشتِ `OCTOPUS_WIRE_C6=0`** و **propose-only** است (فقط پیشنهاد در `state/`، نه apply).
3. `c6_trigger.py` را additive بیاور؛ هوکِ organism را با safe-patch پشتِ فلگ بگذار. flag-off = tickِ دقیقاً قبلی.
4. پچِ `proposed_v3_final.patch` (memory-index) را **جدا** بررسی کن: اگر `_ops/`‌ی که هدفش است در master بهبودِ ایندکس ندارد، آن را **پشتِ فلگِ جدا + با تستِ before/after (سرعتِ get/insert)** اعمال کن؛ اثباتِ بهبود لازم است، نه ادعا.
5. تست: `run_all` سبز + تستِ propose-only (flag-on فقط پیشنهاد تولید کند، صفر تغییرِ کدِ زنده).

**پذیرش:** flag-off صفر تغییر · flag-on فقط پیشنهادِ صف‌شده (نه apply) · پچِ memory-index با بنچمارکِ عددی اثبات شود · TCB و genome دست‌نخورده · زنجیرهٔ governance (pre-register → verify → U-threshold → owner) کامل.
**هزینه/مدل:** اگر C6 از LLM استفاده می‌کند، از `model_router` (WS-3) برود؛ بودجه پشتِ `governor`.

---

## WS-5 — تکمیلِ پایپ‌لاینِ lead-gen (Phase-D)

**مأموریت:** پایپ‌لاینِ تولیدِ سرنخِ کسب‌وکار را از منبع بیاور و flag-off وصل کن — **هیچ ارسالِ مشتری بدونِ arm مالک** (R2 حفظ).

**منبع:** برنچ `phase-d` (D3–D7، ۹۴ تست).
**فایل‌ها (`_ops/legs/`):** `harvest_austender.py` (D5 خوراکِ AusTender)، `email_inbound.py` (D5 خوراکِ ایمیل)، `funnel_store.py` (D3 قیف، append-only/replay-safe)، `speed_to_lead.py` (D4 پیش‌نویسِ پاسخِ اول)، `lead_effect_gate.py` (D6 جداسازیِ release/send)، `outbound_worker.py` (D7 اعلانِ **مالک**، نه مشتری) + تست‌ها.

**گام‌ها:**
1. worktree ایزوله از `phase-d`. `git diff master...phase-d --stat` را بخوان.
2. زنجیره را به‌ترتیب بیاور: harvest/email → `submit_candidate` → funnel → speed_to_lead → effect_gate → outbound_worker. همه additive/flag-off.
3. **مرزِ پول/ارسال:** `outbound_worker` فقط به **مالک** پیام می‌دهد (نه مشتری)؛ هر مسیرِ ارسالِ واقعی پشتِ فلگِ خاموش + دوکلیدِ مالک بماند. `NOT_ARMED` را نگه‌دار.
4. تست: `run_all` + ۹۴ تستِ lead سبز.

**پذیرش:** flag-off صفر ارسال · قیف append-only/replay-safe · اعلان فقط به مالک · هیچ داده‌ی مشتری به بیرون بدونِ arm.
**ابزار/هزینه:** AusTender = منبعِ عمومیِ رایگان؛ ایمیلِ IMAP با App-Password (env-only، هرگز در کد). enrichmentِ LLM (اگر هست) از `model_router` + محلی‌اول (Ollama) برای صفرکردنِ هزینه.

---

## WS-10 — control-plane infra (verify-first، سنگین)

**مأموریت:** زیرساختِ control-plane و ۱۸ رفعِ blind-spot را بیاور — **اما چون منبع 07-14 است و ارگانیسم از آن‌موقع تکامل یافته، اول با master دیف بگیر و فقط آنچه واقعاً تازه و ناموجود است را بیاور** (کارِ تازه‌ترِ master را revert نکن).

**منبع:** برنچ `claude/obsidian-vault-org-swarm-796424` (۹ commit، ۱۳۷ تست).
**فایل‌ها:** `_ops/octopus_logger.py`، `_ops/cortex/improve.py`، `_ops/cortex/self_model.py`، `_ops/live/server.py`، `_ops/dashboard/server.py`، `_ops/organism.py` + control-plane (پنیک، رصدپذیری، restart-aware، پلِ استکِ دوم، FLAG-REGISTRY) + تست‌ها (`test_self_claims`, `test_improve_refractory`, `test_octopus_logger_wire`, `test_deadwrite_readers`).

**گام‌ها:**
1. worktree ایزوله. **برای هر فایل:** `git diff master...<branch> -- <file>` → تشخیص بده کدام hunk در master هست (رد) و کدام تازه است (بیاور).
2. FLAG-REGISTRY و octopus_logger احتمالاً بیشترین ارزش را دارند (رصدپذیری). هر وصل flag-gated.
3. اگر بخشی با کارِ فعلیِ organism/cortex تداخل دارد → **به‌نفعِ master**، فقط additiveهای غیرمتداخل.
4. تست: `run_all` سبز + تست‌های آورده‌شده.

**پذیرش:** صفر رگرسیون/صفر revertِ کارِ تازه‌ترِ master · فقط additiveهای تازه · flag-off = رفتارِ قبلی. اگر معلوم شد **همه‌اش در master هست** → این WS «هیچ» می‌شود و برنچ به لیستِ حذف می‌رود (گزارش بده).
