---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: idea
tags: [painting, lead, trust-engine, blueprint, p0, handoff]
created: 2026-07-21
updated: 2026-07-21
---

# Trust Engine v1.1 — بستهٔ طراحیِ P0 (ورودیِ ایجنتِ Opusِ بعدی)

> **این کدِ اجرایی نیست — بستهٔ طراحی/اسپکِ خارجی است** که مالک آورد (2026-07-21). یک ایجنتِ
> architectِ قوی (Opus) قرار است آن را در سه فاز بسازد: **A** ممیزیِ read-onlyِ runtime →
> **B** قراردادها/state-machineها → **C** پیاده‌سازیِ ایزوله در worktree. **هیچ کد/فلگ/برنچ تا
> تحویلِ `00_RUNTIME_TRUTH.md` و تأییدِ مالک تغییر نمی‌کند** (قاعدهٔ خودِ بسته).

## این بسته چیست
یک **Trust & Network Engine** برای بیزنسِ نقاشی/نگهداریِ سیدنی — نه marketplace/directory. هستهٔ P0
= کوچک‌ترین حلقهٔ auditable: لید → صلاحیت → پاسخ/پیش‌فاکتور → کارتِ تصمیمِ تلگرام → اثرِ بیرونیِ
گیت‌خورده → انتساب نتیجه → یادگیری. برد روی **اعتماد و سرعت، نه قیمت**. زیرِ ناوردی‌های I1–I10 + TINV-7.

## فایل‌ها
- [[00_MASTER_BLUEPRINT|00_MASTER_BLUEPRINT.md]] — سندِ حاکم (stack ruling، ۳ مسیرِ ورودی، P0، rollout).
- [[OPUS_MISSION_PROMPT|OPUS_MISSION_PROMPT.md]] — مأموریتِ ایجنتِ Opus (فاز A/B/C، ناوردی‌ها، تست‌ها، DoD).
- [[01_VERIFICATION_REPORT|01_VERIFICATION_REPORT.md]] — واقعیت‌های بازارِ سورس‌دار (Oneflare رفت، LSA در AU نیست، ACMA SMS، مجوزِ NSW).
- `lead_inbox/LEAD_INBOX_SPEC.md` — قراردادِ canonicalِ لید + قرارداد رویداد (v1.1).
- `legs/LEG_P0-1..4` — اسپکِ چهار جزء (speed-to-lead، quote-draft، review، case-study).
- `module1_b2b_infiltrator/` — پلاگینِ B2B (کشف Domain → کارت → ارسالِ Octopus) + دو ورک‌فلوِ n8n (WF2 حذف‌شده: n8n هیچ دسترسیِ gate/approval/outbound ندارد).

## قاعدهٔ معماریِ سختِ بسته (هم‌راستا با ناوردی‌های فعلیِ اختاپوس)
n8n/Make/Apify فقط **candidate جمع می‌کنند** و به مرزِ امضاشدهٔ `POST /api/v1/lead-candidates`
POST می‌کنند. **هرگز** approve/LANGAR/release/settle/outbound. تنها یک مسیرِ ارسال = Octopus.

## وضعیتِ تطبیق با واقعیتِ فعلی (خلاصه — کاملش در نوتِ خواهر)
تطبیقِ کاملِ بلوپرینت↔سورسِ کانونی: [[RUNTIME-TRUTH-RECONCILE-2026-07-21]] (فاز A، از قبل انجام‌شده).
- **موجود (پشتِ فلگِ خاموش):** legهای lead (inbox/scorer/quote/sense)، Proposal Router + verdict→outcome، LANGAR، EffectorGate، budget_gate، STOP.
- **MISSING (کارِ واقعیِ P0):** endpointِ امضاشدهٔ `/api/v1/lead-candidates`، **firewallِ رضایت** (taxonomyِ consented_inbound/public_b2b/market_signal + outreach_allowed در کد صفر است)، و **workerِ outboundِ Octopus** (مسیرِ واقعیِ ارسال).
