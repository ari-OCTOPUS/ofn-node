# TERRITORY-REPORT — 03 - Projects

findings: **13** · classes: SEASON_LEFTOVER 4 · DEBT_HIDDEN 3 · OPEN_WORK 3 · DOC_RUNTIME_DISCREPANCY 2 · RULING_UNEXECUTED 1

## top findings (rank order)

- **[PRJ-8] r7.0 DEBT_HIDDEN** Project-F miniapp: 8 read-only API routes (/api/state,/api/legs,…) served with NO initData auth on a public tunnel — own
  - `F:/backup/03 - Projects/اونلی فنز/PROJECT.md` · `line 76: رأی: هشت مسیر read-only ِ مینی‌اپ… بدون احراز initData سرو می‌شوند — روی تونل عمومی قابل‌دیدن‌اند`
- **[PRJ-9] r7.0 OPEN_WORK** Project-F: 11 owner verdicts + GATE 0 + 3 human signatures A pending since 2026-07-20; R9/R10 backlog (PII in tracked fi
  - `F:/backup/03 - Projects/اونلی فنز/PROJECT.md` · `line 80: **۱۱ verdict منتظر تو** (THREAD-CLOSURE §۹): G0 · Playbook+M3-a · …`
- **[PRJ-16] r7.0 RULING_UNEXECUTED** Control-plane approvals queue backlog: forensic report found 3 approvals stuck since 2026-07-25 (one risk:high) — live f
  - `F:/backup/03 - Projects/_OCTOPUS-PMO/FORENSIC-REPORT-2026-08-03.md` · `table row ۶: ۳ مأموریتِ pending در `_octopus/state/approvals.json` از ۲۰۲۶-۰۷-۲۵ گیر کرده — شاملِ یکی با `risk`
- **[PRJ-1] r6.8 SEASON_LEFTOVER** Ziman customer domain ziman-gift.com dead (NXDOMAIN) — owner's 2-minute Shopify fix still pending since 09-07
  - `F:/backup/03 - Projects/Ziman Galerry/PROJECT.md` · `line 50: قدم باقی: خود مالک، ۲ دقیقه — Shopify admin → Settings → Domains → حذف ziman-gift.com`
- **[PRJ-4] r6.8 SEASON_LEFTOVER** TOP-5 outreach GO'd 2026-09-07 (Whelan #1, 7/7 QUALIFIED) — pack prepared but no evidence the human calls were ever made
  - `F:/backup/03 - Projects/Lead-نقاشی/PROJECT.md` · `line 37: 📞 TOP-5 OUTREACH — مجاز و آماده (2026-09-07)… تماس تلفنی = فقط انسان (مالک)`
- **[PRJ-2] r6.6 SEASON_LEFTOVER** Ziman msg38 season deadline 2026-09-08T12:10Z passed with state carrier unreadable from laptop — no closure recorded
  - `F:/backup/03 - Projects/Ziman Galerry/PROJECT.md` · `line 56: msg38 ددلاین 2026-09-08T12:10Z (حامل state روی mesh؛ از laptop قابل خواندن نیست)`
- **[PRJ-5] r5.0 OPEN_WORK** Lead pipeline: SMTP transport written+tested but dark; owner vote on OCTOPUS_SMTP_* / WIRE_LEAD_OUTBOUND never given; ba
  - `F:/backup/03 - Projects/Lead-نقاشی/PROJECT.md` · `line 80: رأیِ مالک روی `OCTOPUS_SMTP_*` + `OCTOPUS_WIRE_LEAD_OUTBOUND` · پر کردنِ bank details (بلاکرِ فاکتورِ`
- **[PRJ-3] r4.8 DEBT_HIDDEN** Ziman branding engine built but never called: branding:null for 3+ weeks, drafts_count=0, capacity/inventory numbers unc
  - `F:/backup/03 - Projects/Ziman Galerry/PROJECT.md` · `line 67: `branding: null` یعنی موتورِ برندینگِ ساخته‌شده سه هفته است هیچ خروجی نداده — کدِ زنده‌ای که هرگز صدا`
- **[PRJ-14] r4.8 DEBT_HIDDEN** OWNER BOARD budget engine expired: 'Sakana Max ends Aug 27' / 'Budget engine to 2026-08-27' — no renewal or post-expiry 
  - `F:/backup/03 - Projects/Lead-نقاشی/06-Board/OCTOPUS-OWNER-BOARD/BOARD.md` · `line 20: ## Budget engine to 2026-08-27`
- **[PRJ-13] r4.6 SEASON_LEFTOVER** Accounting telemetry escalate conflict + budget guard 'in deep debug' logged 2026-09-07 with no resolution entry
  - `F:/backup/03 - Projects/Accounting/PROJECT.md` · `line 85: گارد بودجه سبز در دیباگ عمیق؛ تعارض تلمتری escalate شد.`
- **[PRJ-12] r3.0 DOC_RUNTIME_DISCREPANCY** Accounting ACC-V8 status contradiction: VERDICT_QUEUE says 'open' while STATUS-GAP-REPORT records 'approved by owner 202
  - `F:/backup/03 - Projects/Accounting/VERDICT_QUEUE.md` · `line 18: | ACC-V8 | pilot 10 receipts مجاز است؟ | yes/no | open |`
- **[PRJ-7] r2.8 OPEN_WORK** WLOS v0.1.1 (135/135 green) never had its first live run; restore drill acceptance #15 still open; cortex bridge flag-of
  - `F:/backup/03 - Projects/WLOS - Weight Loss OS/PROJECT.md` · `line 42: acceptance #15 (restore drill) هنوز ⚠️`

## coverage

- inventory files_total (md/json/txt ≤2MB): 1106
- read: ~62/862
- method: PROJECT/ROADMAP/VERDICT deep reads + marker grep
- excluded: chat-log bulk, media, sub-code trees listed not read
