---
type: log
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
tags: [lead-gen, decisions]
created: 2026-07-04
updated: 2026-07-04
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
