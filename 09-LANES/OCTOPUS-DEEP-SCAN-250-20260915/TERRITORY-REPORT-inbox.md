# TERRITORY-REPORT — 00 - Inbox

findings: **10** · classes: OPEN_WORK 6 · RULING_UNEXECUTED 2 · SEASON_LEFTOVER 1 · DOC_RUNTIME_DISCREPANCY 1

## top findings (rank order)

- **[INB-1] r7.0 OPEN_WORK** OWNER-PENDING master checklist: 15+ unchecked owner votes (VOTE1-4 hard-test, P0 PEP wire, telegram PEP, PAT rotation)
  - `F:/backup/00 - Inbox/2026-08-16 OWNER-PENDING — All Open Items (Master Checklist).md` · `line 46: - [ ] **P0 overlay v3 سیم به یک PEP** — کد هست (_ops/octopus_v3/, WIRED=False, ۱۸/۱۸). تا رأی`
- **[INB-2] r7.0 RULING_UNEXECUTED** Owner-approved A2-001 merge/push/.180/ofn-bridge never executed despite explicit 'owner-approved' title
  - `F:/backup/00 - Inbox/2026-08-18 NOTE — A2-001 development_canonical owner-approved.md` · `line 15: تأیید تو برای F:\backup\octopus-bridge اعمال شد. verifier اضافه شد؛ stubهای OFN دست نخوردند. ۱۰/۱۰ تس`
- **[INB-3] r7.0 OPEN_WORK** OCTOPUS-Cortex ONLOGON schtask never registered; cortex dies on next Windows reboot (owner vote pending)
  - `F:/backup/00 - Inbox/AGENT_QUESTIONS.md` · `line 235: هیچ تسکِ OCTOPUS-Cortex ثبت نشده ... با اولین ری‌استارتِ ویندوز کورتکس می‌رود ... رأی: ثبت کنم؟`
- **[INB-4] r4.8 OPEN_WORK** Telegram live-activation blocked solely on BotFather token rotation — 'تنها قدم باقی‌مانده'
  - `F:/backup/00 - Inbox/AGENT_QUESTIONS.md` · `line 185: یادآوری تنها قدم باقی‌مانده برای زنده‌شدن تلگرام: چرخش توکن از @BotFather → _ops/OCTOPUS.env → resta`
- **[INB-13] r4.8 OPEN_WORK** Quote engine LOCKED pending owner approval of OCP rate card (live revenue path frozen since 2026-09-01)
  - `F:/backup/00 - Inbox/2026-09-01 START-HERE external-agent discovery pointer.md` · `line 10: listener (15-min, autoreply-proof), follow-up executor, quote engine (LOCKED until`
- **[INB-5] r3.8 SEASON_LEFTOVER** Season sentinels: octopus-gap001-boot-probe + octopus-miniscientist-daily systemd units FAILED on .182 during 2026-09-12
  - `F:/backup/00 - Inbox/2026-09-15 SENTINEL — LAPTOP-BACK 2026-09-15T084837Z.md` · `line 18: .182 failed units: ['octopus-gap001-boot-probe.service loaded failed failed ...', 'octopus-miniscient`
- **[INB-6] r3.0 DOC_RUNTIME_DISCREPANCY** Duplicate Board2 status pair in Inbox pointing to two DIFFERENT canonical paths for the same note 61
  - `F:/backup/00 - Inbox/2026-08-22-Board2-M4-status-for-Obsidian.md` · `line 2: Note: F:\backup\07 - Knowledge\octopus-board2\61-BOARD2-M4-LEGS-STATUS-2026-08-22.md (twin file line 1`
- **[INB-9] r2.8 OPEN_WORK** Open Q-git ruling (60+241 files) plus unfinished 100-step discovery tech queue (INTENTS/UI, doctor dedupe, budget_judge)
  - `F:/backup/00 - Inbox/2026-08-12 HANDOFF — Session Evening for Next Agent.md` · `line 67: **Q-git:** با ۶۰+۲۴۱ فایل چه کنیم؟ (header above it: 'فوری — از مالک بپرس (هنوز باز)')`
- **[INB-10] r2.8 RULING_UNEXECUTED** Arming-order 2026-07-29: flag groups 0/4/5/8 waiting on owner AUTH; two referenced flags absent from flags.cmd
  - `F:/backup/00 - Inbox/Prompt - مگاپرامپت تعمیر شکاف‌های اختاپوس (2026-07-29).md` · `line 94: **در انتظار مالک (طبق _ops/ARMING-ORDER-2026-07-29.md ...):** گروه ۰ کامل ... ردیف ۴ OCTOPUS_WIRE_DEB`
- **[INB-15] r2.8 OPEN_WORK** Morning-cards: live-rate activation explicitly deferred (موکول) and 4d shadow→live left at approve-gate
  - `F:/backup/00 - Inbox/2026-08-17 MORNING-CARDS.md` · `line 28: ## ✅ کارت ۴ — نرخ 1.0 (بی‌اثر) بماند تا دادهٔ هفتگی باشد — مکانیزم فعال، فعال‌سازی نرخ موکول.`

## coverage

- inventory files_total (md/json/txt ≤2MB): 391
- read: 46 content-examined + 211/211 frontmatter-probed
- method: frontmatter census + deep reads on open-item candidates
- excluded: older log-style notes read at marker level only
