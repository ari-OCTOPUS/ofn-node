---
type: log
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
tags: [lead-gen, decisions]
created: 2026-07-04
updated: 2026-08-01
---

# DecisionLog — Lead-نقاشی

> seed اولیه از [[03 - Projects/Lead-نقاشی/PROJECT|PROJECT]] — 2026-07-04.

**D5 — آزمایش #۱ = SEGMENT-DISCOVERY، pre-registered.** یک آزمایش در هر زمان؛ معیار موفقیت لید واقعی، نه کلیک. tenant #2 (D-26).
**Canonical زیرساخت = `AiFarm-Lead/`.** brushline مغز کامل مستقل خودش را دارد (governance/KB)؛ این پروژه مصرف‌کنندهٔ آن است.
**قید قانونی هر outreach.** طبق [[03 - Projects/Lead-نقاشی/Outreach Compliance|Outreach Compliance]] (Spam Act 2003 + DNCR Act 2006)؛ ارسال فقط با verdict انسانی.
**2026-07-03 — بازسازی ربات کاریابی فازهای ۰-۴.** کلیدها فقط .env + fail-fast؛ حلقهٔ تأیید تلگرام؛ ۳۳ تست سبز؛ خاموش تا rotation.
**2026-07-04 — یافتهٔ کانال:** Google LSA در AU موجود نیست → مسیر GBP + Ads ([[03 - Projects/Lead-نقاشی/Report - Lead-نقاشی - Sydney Lead Channels 2026|گزارش]]).
**2026-07-21 — Trust Engine فاز B (طراحی، متخاصم-verify).** ۱۰ سندِ propose-only در `Trust-Engine-v1.1/PHASE-B-CONTRACTS/`؛ ۲ باگِ blocking در برابرِ کد اصلاح شد (sweep_stale_effects روی releasable؛ سوراخِ consent در handoff).
**2026-07-21 — رأیِ تامِ مالک «FULL AUTHORITY + MANDATORY COMPLETION».** همهٔ HOLDهای قبلیِ این workstream لغو؛ فقط R1–R5 ممنوع (فایلِ STOP، ارسالِ واقعیِ غیر-synthetic، پول/LIVE سراسری، تضعیفِ consent firewall، green دروغین). اجازهٔ صریح: unhold ماژول‌های heart (find-or-hermetic)، پیاده‌سازیِ فاز C (C0–C2 synthetic)، مرزِ HMAC، گاردِ staleness، commit/ff/push بدونِ پرسشِ مجدد.
**2026-07-21 — فاز C پیاده شد (کدِ flag-off، تست‌شده، صفر ارسال).** consent_firewall + lead_candidate_inbox (synthetic E2E) + lead_boundary_http (HMAC 127.0.0.1:8774) + effector_gate_bridge (staleness) + llm_intent wiring + دو ماژولِ heart. فعال‌سازیِ لوله owner-gated (رأی روی قراردادها + secretها + restart). funnel/workerِ outboundِ واقعی = فاز D، رأیِ جدا.
**2026-07-21 — LEAD-SAFETY-C1 + سیم‌کشی + دمو (رأی مالک، ratified).** footgunِ batch-release بسته (allowlist + release_one)؛ lead_effect_gate (per-effect، fail-closed)؛ outbound_worker = NOT_ARMED؛ inbox convergence + freezeِ lead_leg_inbox؛ دموِ dry-run ۹/۹. راستی‌آزماییِ متخاصم چند باگ گرفت و همه فیکس شد (denylist→allowlist، synthetic-normalize، audit-honesty، idempotency، may_outreach).
**2026-07-21 — لِینِ لید = COMPLETE-UNARMED.** قوسِ لید کامل، متصل، تست‌شده (۱۸/۱۸ گیت + دمو ۹/۹)، adversarial-verify؛ **مسلح نیست** (transport NOT_ARMED، هیچ ارسالِ واقعی). `on_lead_verdict` نقطهٔ اتصالِ verdict→effect ساخته شد. **arming = رأیِ آیندهٔ صریحِ مالک** (وصلِ دکمهٔ کارت + مسلح‌کردنِ transport). راهنما: `OWNER-RUNBOOK-LEAD.md`. ماژول‌های parkـشده (نه لازمِ مسیر): consent_store(suppression)/funnel_store/first-response-draft/producer-absorption + جداسازیِ release/send برای staleness (فاز D).
**2026-08-01 — تشخیص: حلقهٔ ارزش در سرچشمه گرسنه است، نه خراب.** صفر پیشنهادِ تحویل‌شده در کلِ عمرِ سیستم. درِ ورودی باز (`OCTOPUS_WIRE_LEAD_CANDIDATES` روشن، ۴ خواننده) و درِ خروجی تاریک (`OCTOPUS_WIRE_LEAD_OUTBOUND`، ۵ خواننده، منتظرِ رأی) — ولی **هیچ تولیدکننده‌ای وجود ندارد**: هر نویسندهٔ `lead-inbox` انسان صدایش زده و هیچ فلگی قفلش نکرده. همان «جذبِ producerها» که از ۰۷-۲۱ در Progress مانده بود، حالا با سنجهٔ زنده تأیید شد. تصمیم: لولهٔ ایمیل اولویتِ یک است چون سایت ده ماه است ساکت است (SSL منقضی + صفر فرم).
**2026-08-01 — قیدِ پاسخِ اولِ خودکار (رأیِ مالک).** پاسخ در چند دقیقه، ولی **هیچ عددی**: نه قیمت، نه بازه، نه تعهدِ تاریخ. فقط تصدیق + ۲-۳ سؤالِ صلاحیت + پیشنهادِ بازدید. و **هرگز خودش نمی‌فرستد** — تولیدِ متن از ارسال جداست و ارسال تصمیمِ گیت‌شدهٔ مالک می‌ماند. مبنای قانونی: پاسخ به inbound طبقِ [[03 - Projects/Lead-نقاشی/Outreach Compliance|Outreach Compliance]]؛ کاندیدی که `consented_inbound` نباشد اصلاً پاسخی تولید نمی‌کند.
**2026-08-01 — دسترسیِ پهن، پردازشِ باریک.** مالک IMAP ِ کلِ صندوق را انتخاب کرد نه برچسبِ فیلترشده. قید: ایمیلِ غیرکاری خوانده و **بی‌هیچ ردی** دور ریخته می‌شود — نه لاگ، نه فایلِ حالت، نه حتی یک خطِ موضوع.
**2026-08-01 — جزئیاتِ بانک: خواننده اصلاح شد، نه دادهٔ مالک.** مالک `bank_details` را زیرِ `bank_accounts[0]` گذاشت که جای درست‌تری است (پرداخت به یک حسابِ مشخص تعلق دارد). به‌جای درخواستِ جابه‌جایی، `invoice._bank_from_accounts` با تقدمِ ریشه اضافه شد. فاکتور دیگر «پرداخت‌ناپذیر» نیست.
