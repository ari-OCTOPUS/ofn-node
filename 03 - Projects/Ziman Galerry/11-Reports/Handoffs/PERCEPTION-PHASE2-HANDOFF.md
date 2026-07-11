---
type: handoff
project: ZIMAN
status: ready
created: 2026-07-12
updated: 2026-07-12
from: Ziman Calibration/Perception-Geometry Audit Agent
to: next engineering agent
sources:
  - "[[00 - Control/PERCEPTION-GEOMETRY-AUDIT-2026-07-12]]"
  - "[[11 - Reports/Handoffs/FOUNDATION-PHASE2-HANDOFF]]"
tags: [ziman, handoff, phase2, calibration]
---

# HANDOFF — Perception/Calibration Phase-2 (2026-07-12)

> ادامهٔ [[11 - Reports/Handoffs/FOUNDATION-PHASE2-HANDOFF|FOUNDATION-PHASE2-HANDOFF]]. Phase-2 از قبل ساخته بود؛ این جلسه **کالیبراسیون + راستی‌آزمایی** انجام داد. مرجعِ کامل: [[00 - Control/PERCEPTION-GEOMETRY-AUDIT-2026-07-12|CALIBRATION-AUDIT]].

## آنچه این جلسه تثبیت شد
- ✅ **۴۰/۴۰ تستِ Ziman واقعاً اجرا و سبز** (leg 17 + phase2/wiring 23) + smoke OK → **T11 → VERIFIED (T16).** اکشنِ #۱ handoff قبلی انجام شد.
- ✅ منیفولدِ محصول (PRODUCT-CARD.v1) ۶بعدی و fail-closed است — از قبل ساخته، ولی null.
- ✅ propose-only ساختاری، C4 local-only، D4 روی null fail-closed، seam قلب/مغز یک‌طرفهٔ امن — تأیید شد.
- 🔎 ۵ conflictِ جدید ثبت شد: **CF-06..CF-10** (+ T16/T17/T18 در TRUTH-REGISTER).

## بلوکِ A — فیکس‌های propose-only (بدونِ verdict شروع کن؛ فقط draft/proposal، اجرا-تغییرِ کد پشتِ verdict)
- [ ] **A1 [CF-10]** Role Card → `suite: ZM-QUAL-PRODINV-v1` + گیتِ all-critical؛ افزودنِ ۱۲ critical و تستِ delivery-promise. (ویرایشِ سندِ agent — کم‌ریسک)
- [ ] **A2 [CF-01/CF-05]** در digest/draft، اعداد را با `evidence_class` برچسب بزن؛ تا revalidation «~۶/هفته (unverified)» — نه ۳۰ خام. (پیشنهادِ متن)
- [ ] **A3** EXP-002: stop+success+failure؛ EXP-003: stop؛ هر EXP: frontmatter+experiment_id. (ویرایشِ کارت‌های experiment)
- [ ] **A4** VERDICT_QUEUE.md frontmatter اضافه شود؛ OpenQuestions type اصلاح (schema-hygiene؛ constitution §6).

## بلوکِ B — فیکس‌های کدِ گیت‌دار (proposal + regression test بنویس؛ اجرا/merge پشتِ verdict — گیتِ ایمنی)
- [ ] **B1 [CF-06، 🔴 اصلی]** `capacity_fail_closed` را به گیتِ D4 وصل کن (هم `_ops/legs/ziman_leg.py:143 campaign_check`، هم `ziman-agent/ziman/capacity.check_campaign` via `worker.py:106`): سقفِ مؤثر = `capacity_fail_closed(yaml_ceiling, owner_revalidated=False)` = ۶ تا revalidation. + تستِ «۷/هفته رد شود». **این باگِ اصلیِ ایمنی است.**
- [ ] **B2 [CF-07]** freshness واقعی در `compute_atp`: ISO8601 parse، ردِ future، پنجرهٔ کهنگی. + تستِ stale/future/naive.
- [ ] **B3** `worker.py` docstring را با `main()` هم‌تراز کن یا ۴ subcommandِ Phase-2 را به `phase2_cli` مسیر بده (silent no-op فعلی رفع شود).

## بلوکِ C — تصمیم‌های مالک (فقط مالک؛ ایجنت انجام نمی‌دهد)
- [ ] **C1 [🔴 CF-08]** وضعیتِ `_launchpad/second-brain-live/`: آیا باتِ زندهٔ واقعیِ send-دار است؟ اگر بله → حکمرانیِ جدا + انتقالِ PII (chat-id) به `.env` + خروج از ادعای «zero outward». اگر نه → آرشیو. (ایجنت به این درخت دست نمی‌زند.)
- [ ] **C2 [CF-09]** برچسبِ provider (Anthropic vs DeepSeek) + rotation.
- [ ] **C3** تصمیمِ **A/B/C استراتژیِ پرکردنِ منیفولد** (توصیه B) → سپس ساختِ Product Cardها.
- [ ] **C4** revalidation ظرفیت (CF-01) · شمارشِ واقعی → inventory_snapshot.v1 (CF-02) · نام برند (CF-05) · ۷ verdict ZIM-V1..V7.

## مرزهای سخت (بدون تغییر)
- No publish/send/spend/deploy/price/promise؛ human gate برای هر بیرونی.
- عکس‌ها/فایل‌های legacy هرگز move/rename نشوند؛ ۴ درختِ کد هرگز auto-sync نشوند؛ `_code` منطقهٔ ممنوعِ `.agentignore`.
- Telegram = gateway؛ canonical memory فقط با curator + مالک.
- تست‌های Ziman جدا اجرا شوند (کلِ dir با pytest crash می‌کند).

## ضدِ گاف
- Phase-2 و schemaها از قبل هستند — **بازنساز**؛ فقط فیکس/برچسب. 
- ۳۰/۲۰ اعدادِ unverified‌اند (`[Estimate]`) نه `[Measured]` — به آن‌ها promise نبند.
- منیفولد ۶بعدی است؛ تصمیمِ باز «چطور پر شود» است نه «چند بعد».
