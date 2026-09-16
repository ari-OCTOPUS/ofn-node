# Parallel Integration Board — 2026-08-03

قاعده: موازی جلو می‌رویم، اما هر lane فقط D0-D2 تا وقتی contract/test/rollback روشن شود. merge مستقیم ممنوع.

| lane | branch | unique | equivalent in master | status | next |
|---|---:|---:|---:|---|---|
| P0 telegram-security | fix/tg-p1-2026-07-30 | 0 | 2 | ALREADY_DIGESTED_IN_MASTER | no merge; keep tests; mark branch as reference |
| P1-small neural | fix/neural-loop-close-310-214 | 0 | 1 | ALREADY_DIGESTED_IN_MASTER | no merge; keep shadow-only guard |
| P1-small test-hardening | claude/vigilant-grothendieck-8e8250 | 1 | 0 | CANDIDATE_SMALL_PORT | port 11-line hermetic test fix if current master lacks isolation |
| P0/P1 telegram-governance | claude/telegram-governance-integration-832984 | 12 | 0 | NEEDS_DIGEST_BY_INTENT | split into W1..W7 + Painting OS; do not merge branch |
| P1 lead-outbound-safety | phase-d | 8 | 0 | NEEDS_CONTRACT_DIFF | many modules already exist on master; compare behavior and port missing tests/contracts only |
| P2 project-f | claude/project-f-agent-build-aa512f | 5 | 0 | MUSEUM/PORT_IDEA_NOT_CODE | extract pf_know/KPI ideas only after privacy/langar policy |
| P3 c6-self-improvement | claude/c6-self-improvement-ignition-c73186 | 3 | 0 | RESEARCH_ONLY | no live wiring; use as design input for memory indexes/preregistration |
| ARCHIVE backup | backup/pre-deploy-2026-07-21 | 2 | 0 | ARCHIVE_REFERENCE_ONLY | do not merge runtime state churn |

## تصمیم‌های فوری
1. `fix/tg-p1-2026-07-30` واقعاً قبلاً در master هضم شده: هر دو commit با `git cherry` معادل‌اند و تست‌های هدفمند پاس شدند.
2. `fix/neural-loop-close-310-214` هم قبلاً در master هضم شده: merge لازم نیست؛ live wiring ممنوع/نیازمند بازبینی جدا.
3. `phase-d` ظاهراً بسیاری از ماژول‌هایش الان در master وجود دارند و تست‌های core پاس‌اند؛ اما patch-id معادل نیست، پس باید diff رفتاری/contractی انجام شود، نه merge.
4. `claude/telegram-governance-integration-832984` هنوز ۱۲ commit یکتا دارد؛ باید به work packages شکسته شود: W1 two-poller, W2 guidance ids, W3 actuator seam, W5 lead draft, W6 single TG entry, W7 UI optimization, Painting OS.
5. `claude/vigilant-grothendieck-8e8250` یک patch کوچک test-only است؛ candidate امن برای port بعد از راستی‌آزمایی current master.

## تست‌های اجراشده در این مرحله
- `test_bridge_buttons.py` 8/8
- `test_cb_token_legmiss.py` 16/16
- `test_master_halt.py` 5/5
- phase-d core: consent_gate 10/10, funnel_store 10/10, release_send_separation 7/7, speed_to_lead 9/9, lead_effect_gate 18/18
- telegram governance core present on master: approval_actuator 6/6, guidance_box 8/8, tg_api 33/33, tg_center 39/39, tg_render 16/16, telegram_poll_e2e 7/7

## ریسک‌های باز
- چند تست/ماژول از branch governance در master با نام/شکل دیگر یا missing دیده شد: `test_invoice.py`, `test_lead_quote.py`, `test_pricing.py`, `test_email_inbound.py`, `lead_draft.py`. باید به contractهای فعلی map شوند، نه copy مستقیم.
- `phase-d` patch-idها unique هستند ولی modules در master وجود دارند؛ یعنی master احتمالاً نسخهٔ تکامل‌یافته/متفاوت دارد. merge کور خطر overwrite دارد.
