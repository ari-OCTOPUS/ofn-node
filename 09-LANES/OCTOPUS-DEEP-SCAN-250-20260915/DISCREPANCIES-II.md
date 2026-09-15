# DISCREPANCIES-II — تضادهای vault ↔ runtime ↔ archive (2026-09-15)

**23 ردیف کلاس DOC_RUNTIME_DISCREPANCY** از رجیستر ۲۵۰ (آرشیو هم این دور دامنه بود).

## [F-082] llama-8081 on 138: notes say live, probe said DOWN + binary absent (resolution: null) — and 180 now runs llama-lab: three claims, no reconciliation
- **path:** `F:/backup/09-LANES/OCTOPUS-138-WIRING-20260908/LANE-REPORT.md` — `'resolution: null, status: open'`
- **evidence:** open contradiction
- **why_complete:** local-model routing depends on knowing where llama actually serves

## [F-035] W24 chain documentation claims PB-4 NOT_RUN / corpus=6 — stale vs runtime (PB-4 IMPROVED 0.75v0.0, facts=371): open-work trackers contradict live state
- **path:** `F:/backup/09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/CURRENT-STATE.json` — `'PB-4': 'NOT_RUN' vs live 371 facts`
- **evidence:** tracker files never updated after the 09-15 closed-loop session
- **why_complete:** next agents will re-build what exists; the stale trackers are the single-source-of-forgetting this scan exists to end

## [F-036] engineering-entrypoint chain stale: AGENTS.md points at 09-04 while 0906/0907 exist and none reference the forensic-reorientation lane or ORIENTATION.md
- **path:** `F:/backup/AGENTS.md → 07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md` — `'read 07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md'`
- **evidence:** no entrypoint mentions lanes newer than 09-07; ORIENTATION.md unlinked
- **why_complete:** navigation is the first thing every agent reads; stale entrypoint = repeated rediscovery cost

## [DOC-2] F-AUTO-BRAKE (scan 2026-09-09): heart braked again — effective_period_s=900 with brake:cardiac vs biological rhythm 42.4 — contradicting F-01's 07-29 revision that declared B1 closed (period was 51.21s)
- **path:** `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-AUTO-BRAKE-قلب-ترمز-خورده.md` — `line 9: `effective_period_s=900.0` با راننده `brake:cardiac` در حالی که ریتمِ زیستی `42.42640687119285``
- **evidence:** REVISION-2026-07-29 invalidated the original braking finding ('B1 بسته شد', effective_period 51.21, n_braking=0); six weeks later the identical pathology is measured again mid-season — either the budget fix regressed or the 288→2000 cap reverted. No revision note closes this recurrence.
- **why_complete:** Could be a transient measured at scan time — but finding stands unrevised 🔴.

## [4D-31] REGISTRY.md declares 4d_system 'active-ready' while DEPRECATED.md marks the folder archive/opt-in and runtime idle since 2026-08-21
- **path:** `4d_system/REGISTRY.md` — `line 8: status: active-ready`
- **evidence:** DEPRECATED.md line 19 'ولی لانچ نمی‌شود' (softened only by C-020 errata for Aug 16); daemon_state shows no tick for 25 days; two governance docs disagree about the same directory
- **why_complete:** All three files read in full; timestamps establish the contradiction (registry verdict, errata date, last_tick)

## [ARC-7] CURRENT-TRUTH mirror drift: archived mirror-cleanup-20260902 copy differs from live 01-TRUTH/CURRENT-TRUTH.md; 7 live copies exist
- **path:** `F:/backup/99-ARCHIVE/mirror-cleanup-20260902/01-TRUTH__CURRENT-TRUTH.md` — `line 1 (diff evidence): 60 lines vs live 64 lines — DIFFER; live copies also at 00 - Inbox/, 01 - Dashboard/, 06-EVIDENCE/, 07-HANDOFF/, agent-prompts/, OCTOPUS/`
- **evidence:** The 'single source of truth' file exists in 7 live locations plus an archived mirror set (10+ files), and mirror vs live already diverge (60 vs 64 lines) — the mirror-cleanup pass was archived before convergence was achieved.
- **why_complete:** Complete when CURRENT-TRUTH is single-homed (or mirrors are generated, not copied) and the archived mirror matches its live origin byte-for-byte; diff proves residual divergence.

## [4D-6] Vault appendix provenance points to Desktop originals (4D/SOG-multiagent-handoff 2.md) that exist nowhere in F:/backup
- **path:** `4D-Vault/09-پیوست‌ها/📄 متن-کامل-handoff.md` — `line 10: خلاصه‌ی ساختاریافته‌ی `4D/SOG-multiagent-handoff 2.md` (۴۰ کیلوبایت)`
- **evidence:** Cites C:/Users/Armin/Desktop/4D/... as file of record; F:/backup/4D does not exist and 4d_system/4D contains only a README stub - chain to primary source severed
- **why_complete:** find across F:/backup for 4D reference dir and the handoff filename returns nothing outside the vault's own summary

## [DOC-3] int('متوسط') crash signature ×346: F-05 declared it fixed+closed on 2026-07-29, yet the same signature is a top 🔴 alert in scans 2026-08-13, 08-22 and still today (F-AUTO-ALERT-178 ×346, 09-15)
- **path:** `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-AUTO-ALERT-18-هشدارِ-تکراری-×346.md` — `line 9: ⚠️ wiring: doctor_digest_beat خطا: ValueError: invalid literal for int()… یک امضا، **346** بار`
- **evidence:** F-05 revision: 'کرشِ int(متوسط) هم با فیکسِ روی دیسک + ری‌استارت بسته شده است'. But alert #18 signature persists at exactly ×346 across later scans — count frozen (fix stopped NEW occurrences) yet the alert was never cleared/resolved in the wiring view, and doctor_digest_beat (the only pipe delivering findings to owner) remains the failing component in today's scan.
- **why_complete:** ×346 is cumulative historical count — but a closed finding's signature should not still headline scans.

## [RT-6] docs/DISCOVERY.md still sells the retired email channel as live frontier (sent 2026-09-01, 'first autonomous quote' pending)
- **path:** `F:/ofn-node/docs/DISCOVERY.md` — `first five real outbound emails ... 2026-09-01 13:17 UTC ... frontier: first human reply -> first autonomous quote -> first booked revenue`
- **evidence:** Email channel was retired (owner vote R2-3, 2026-09-08; outbound only via governed Telegram), yet the onboarding doc an external agent reads first still points at email-based frontier and six email timers
- **why_complete:** Doc is dated 2026-09-01 and predates the retirement — historically honest but never updated, so it misroutes new agents

## [SML-14] GAP-LEDGER count contradiction (0 rows in vault vs 64 claimed) open with resolution null
- **path:** `07-HANDOFF/GAP-VERIFY-IDENTITY-STOP-2026-09-08.md` — `table row: GAP-LEDGER.jsonl row count in F:/backup | 0 | git ls-files + path search this session | 64 | Downloads md records: 64 | null | open`
- **evidence:** L6 lane proved the claimed 64-record GAP ledger does not exist in the vault (0 rows) yet the values sit unreconciled; frontmatter still status: open, requires: owner_decision; the 29 unblocked-rows claim is equally unresolved.
- **why_complete:** Ledger may live only in Downloads by design (offline/archive rule).

## [F-055] P6 QA seal cited but its direct file unlocatable (Q1 read-only lookup never done)
- **path:** `F:/backup/09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/NEXT-ACTIONS.json` — `Q1 'READ_ONLY_LOOKUP'`
- **evidence:** CURRENT-STATE 'seal cited but direct file not found'
- **why_complete:** a QA seal that can't be produced on demand is indistinguishable from none

## [4D-5] MOC-سیستم documents physical location as C:/Users/Armin/Desktop - stale; truth moved to F:/backup per PROJECT_STATE 2026-07-16
- **path:** `4D-Vault/00-MOC/MOC-سیستم.md` — `line 62: C:/Users/Armin/Desktop/`
- **evidence:** Navigation doc tells readers the vault sits on Desktop; runtime source of truth is F:\backup\4d_system (PROJECT_STATE.md §۸.۶), Desktop copies declared منسوخ
- **why_complete:** Contradiction is internal to the repo: DEPRECATED.md/PROJECT_STATE.md explicitly rule the Desktop copy obsolete while the vault MOC still points there

## [4D-25] Channel doctor: registered 'financial_nervous' channel FAIL (layer absent from repo), 3 channels UNKNOWN; report generated against stale Desktop registry path
- **path:** `4d_system/outputs/control_plane/_reports/channel_doctor.md` — `line 29: | financial_nervous | 🔴 FAIL | ... لایه‌ی مالیِ جدا در repo وجود ندارد`
- **evidence:** registry.yaml registers a subsystem the codebase never implemented; header cites registry at C:\Users\Armin\Desktop\4d_system (pre-migration path); report never regenerated on F:
- **why_complete:** Report read in full; summary row 12 PASS / 8 WARN / 1 FAIL / 3 UNKNOWN; no newer doctor output exists

## [INB-6] Duplicate Board2 status pair in Inbox pointing to two DIFFERENT canonical paths for the same note 61
- **path:** `F:/backup/00 - Inbox/2026-08-22-Board2-M4-status-for-Obsidian.md` — `line 2: Note: F:\backup\07 - Knowledge\octopus-board2\61-BOARD2-M4-LEGS-STATUS-2026-08-22.md (twin file line 1 says: See: [[شناخت-اختاپوس/61-...]])`
- **evidence:** '2026-08-22 Board2 M4 status for Obsidian.md' (space-named) points canonical to 07 - Knowledge/شناخت-اختاپوس/61-…, hyphen-named twin points to 07 - Knowledge/octopus-board2/61-…; BOTH target files exist on disk and the two 61- files differ (57 vs 60 lines). No dedup decision recorded.
- **why_complete:** Complete when one canonical path wins, the twin pointer file is retired, and the divergent 61- copies are reconciled — none done.

## [KN-1] genome-system loop retired 2026-07-17, but plan.yaml still status:active and Knowledge index still promises 'plan-gated loop runs 3x/day'
- **path:** `F:/backup/07 - Knowledge/genome-system/plan.yaml` — `line 9: status: active`
- **evidence:** STATUS.json: status='retired', retired_note says loop dead since 2026-07-17 (zero importers, no scheduled task) — yet plan.yaml keeps status: active with 3 milestones done:false, and _Index - Knowledge.md says 'حلقهٔ plan-gated ۳بار/روز اجرا می‌شود'. Docs advertise a running system that is retired.
- **why_complete:** plan.yaml may be kept active intentionally so 'the loop idles' — but nothing runs to read it.

## [PRJ-12] Accounting ACC-V8 status contradiction: VERDICT_QUEUE says 'open' while STATUS-GAP-REPORT records 'approved by owner 2026-07-12 → executed → blocked-on-data (zero real receipts)'
- **path:** `F:/backup/03 - Projects/Accounting/VERDICT_QUEUE.md` — `line 18: | ACC-V8 | pilot 10 receipts مجاز است؟ | yes/no | open |`
- **evidence:** reports/STATUS-GAP-REPORT-2026-07-12.md:38 and drafts/receipts-pilot-2026-07-12.md:79 ('ACC-V8 = approved-but-blocked-on-data') contradict the queue; receipts-pilot awaits owner's 10 real photos per RUNBOOK §4 — never supplied. Same report flags a second contradiction: MANIFEST 'security_gate: closed (4 CRITICAL)' vs RUNBOOK 'LIFTED 2026-07-06'. Also ACC-V1/V3/V5/V7/V9/V10 all still open.
- **why_complete:** Queue may simply be stale — which is itself the discrepancy.

## [F-081] 8791 three-tenant contradiction unresolved (resolution: null)
- **path:** `F:/backup/09-LANES/D-S0-HUNT/LANE-REPORT.md` — `'`resolution: null`'`
- **evidence:** open contradiction
- **why_complete:** port/tenant ambiguity blocks any 879x-related claim

## [GEX-6] Live START-HERE names 'ofn-node @ release/p0 → docs/DISCOVERY.md' as code guide; export branch is surgery-20260830 and docs/DISCOVERY.md is absent
- **path:** `F:/backup/_github-export/ofn-node/docs` — `docs listing: discovery-138/ present, DISCOVERY.md absent at docs/ root; ofn-node branch = export/octopus-surgery-20260830 (git branch --show-current)`
- **evidence:** The 2026-09-01 discovery pointer (00 - Inbox) directs external agents to release/p0's DISCOVERY.md, but the exported tree ships a different branch without that file — the export cannot satisfy the live entry-point claim; drift between canonical repo and export.
- **why_complete:** Complete when the export carries release/p0 (or the pointer is retargeted to the exported branch + file); currently pointer and payload disagree.

## [OPS-24] wiring.py docstring claims heartstate beat is 'default OFF behind HEARTSTATE_SHADOW' while the live gate is the on-disk ACTIVATION-HEARTSTATE.flag (writes every beat)
- **path:** `_ops/wiring.py` — `line 3013: پشتِ HEARTSTATE_SHADOW (پیش‌فرض خاموش). heartstate.persist خودش هم فلگ را چک می‌کند`
- **evidence:** ACTIVATION-FLAGS.md warning section proves enabled() has a second file-exists branch (_FLAG_FILE) with the flag RAISED on disk, so runtime is ON while doc/env-based audits report OFF; docstring never corrected
- **why_complete:** docstring/audit updated to name the file branch, or env-only gate restored by owner ruling

## [PRJ-17] NBB-Control-Plane v0.2 skeleton: all four integration verdicts (NBB-V1..V4) still open; rebuilt from a conversation whose original 'هرگز دانلود نشد'
- **path:** `F:/backup/03 - Projects/NBB-Control-Plane/VERDICT_QUEUE.md` — `line 5: | NBB-V1 | نقش NBB نسبت به Architect/_ops | … | open |`
- **evidence:** README admits this is a reconstruction — 'نسخهٔ اصلی در گفتگوی claude.ai ساخته شد و هرگز دانلود نشد'; queue rows V1-V4 all open (dashboard? tenant adapters? run API?). Note OCTOPUS-TRUTH 09-OPEN-WORK claims 'NBB-V1 (حل شد)' on 2026-08-15 — the local queue was never updated (cross-doc contradiction).
- **why_complete:** NBB-V1 closed per TRUTH doc — but then the canonical queue is wrong, which is the finding.

## [F-060] DeepSeek provider exists as lab stub (3× NotImplementedError) in FUGU-BIZ-SPRINT while a different live deepseek adapter serves the chain — provenance ambiguity
- **path:** `F:/backup/06-EVIDENCE/FUGU-BIZ-SPRINT-2026-08-24/lab/gateway/brainport/providers/deepseek.py:21` — `'lab stub'`
- **evidence:** stub code on disk
- **why_complete:** two 'deepseek' implementations with opposite maturity invites wiring the wrong one

## [OPS-16] EXTERNAL_ACTIONS.json says EXTERNAL_ACTIONS=1 while the same-day counter records count=2 (send1+send2) - the two ledgers disagree
- **path:** `_ops/state/EXTERNAL_ACTIONS.json` — `line 4: "EXTERNAL_ACTIONS": 1 ... note: Set by PC_worker owner-proxy after TRAFFIC-1 SEND1 (at 2026-09-05)`
- **evidence:** state/external-actions-counter.json (date 2026-09-05) says {count: 2, cap: 10, note: backfill: TRAFFIC-1 send1 (arm A) + send2 (arm B)}; the authoritative explicit-key file was never updated for send2
- **why_complete:** both files agreeing on the same count for 2026-09-05, or a note declaring the counter authoritative

## [SML-8] SEASON.md on node 138 still titled SEASON 4 while gates file says Season 5
- **path:** `01-TRUTH/SEASON-5-2026-09-04.md` — `line 40: SEASON.md on 138 still titled SEASON 4. Gates file is Season 5 ... until SEASON.md is rewritten under owner GO.`
- **evidence:** Doc-vs-runtime discrepancy: live season file on 138 contradicts the gates file; the register defers the rewrite under owner GO and no GO/closure receipt exists here.
- **why_complete:** Rewrite intentionally owner-gated; discrepancy documented rather than hidden.

