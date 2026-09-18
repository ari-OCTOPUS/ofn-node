# TERRITORY-REPORT — _ops

findings: **26** · classes: OPEN_WORK 9 · SEASON_LEFTOVER 8 · DEBT_HIDDEN 3 · RULING_UNEXECUTED 2 · ABANDONED 2 · DOC_RUNTIME_DISCREPANCY 2

## top findings (rank order)

- **[OPS-1] r10.0 SEASON_LEFTOVER** STOP-FUGU circuit breaker auto-tripped 2026-09-15 05:56 and was never reset; paid/primary brain quarantined
  - `_ops/STOP-FUGU` · `line 1: auto: 3 consecutive Fugu failures (>= 3) @ 2026-09-15 (mtime Sep 15 05:56)`
- **[OPS-2] r10.0 SEASON_LEFTOVER** deep_think sessions never reached the expensive brain all season (54 paid-call-failed alerts Sep 7-15), no cards built
  - `_ops/governor/governor-alerts.md` · `line 11393: deep_think: جلسهٔ «business» به مغزِ گران نرسید (primary: paid-call-failed) — کارتی ساخته نشد`
- **[OPS-3] r10.0 SEASON_LEFTOVER** lead_email_intake IMAP failing every day of the season window (~39 alerts Sep 8-15) - lead pipeline degraded
  - `_ops/governor/governor-alerts.md` · `line 11373: lead_email_intake: IMAP خطا (error) (+N تکرارِ سرکوب‌شده)`
- **[OPS-7] r10.0 RULING_UNEXECUTED** SIG-IV independent verification still pending: owner's WAVE1 executive-order gate 1 never passed (verifier_independent=f
  - `_ops/cortex/plans/TELEGRAM-COGNITION-DEEP-DEBUG-2026-08-21.md` · `line 127: 163/163 and 202/202 are builder-run at historical HEADs; verifier_independent=false CONFIRMED... Ind`
- **[OPS-4] r6.8 SEASON_LEFTOVER** tg-center silently dying all season: ~24 WATCHDOG REVIVE relaunches Sep 6-15 incl. 3x on Sep 15
  - `_ops/governor/governor-alerts.md` · `line 11399: WATCHDOG REVIVE incident (tg-center) - centre was silent - relaunched RUN-TG-CENTER.bat`
- **[OPS-5] r6.8 SEASON_LEFTOVER** chrono.db 'database is locked' beat errors recurring in season (8 events; 2 on Sep 15) - heartbeat writes failing
  - `_ops/governor/governor-alerts.md` · `line 11384: chrono beat error: OperationalError: database is locked`
- **[OPS-19] r6.8 RULING_UNEXECUTED** Owner ruling 2026-07-30: narrow constitution fix for self-merge WITH safety net (regression vs pinned HEAD + revert tag 
  - `_ops/CROSS-SESSION-BRIEF-2026-07-30.md` · `line 37: همراهِ تورِ ایمنی (رگرسیون نسبت به HEADِ پین‌شده + تگِ برگشت + واچ‌داگِ پس‌ازmerge). ⚠️ این کار انجام`
- **[OPS-18] r6.6 SEASON_LEFTOVER** CHECKLIST-lead-arming-2026-08-01: 17 boxes never ticked; SMTP self_test proof and real-source phases unexecuted while in
  - `_ops/CHECKLIST-lead-arming-2026-08-01.md` · `line 37: - [ ] 4. self_test() ِ lead_outbound_transport را بزن → فقط به آدرسِ خودت می‌فرستد؛ لولهٔ SMTP اثبات `
- **[OPS-6] r5.0 SEASON_LEFTOVER** GITWRITE-FAILED.flag re-fired today (2026-09-15_055021, lock TIMEOUT after 40 attempts) and has been 'not cleared' since
  - `_ops/backup/GITWRITE-FAILED.flag` · `line 1: GITWRITE-FAILED 2026-09-15_055021 : git-write lock TIMEOUT after 40 attempts on F:\backup\_ops\backup\`
- **[OPS-15] r5.0 SEASON_LEFTOVER** debate SURVIVORS-QUEUE: 388 entries, 234 pending-human + 154 undecided-after-3-rounds, none ever resolved; new items sti
  - `_ops/debate/SURVIVORS-QUEUE.md` · `line 3488: ## 2026-09-15T15:09:55 — seed-1 · status: pending-human · sig:195677d0ecb1`
- **[OPS-10] r5.0 ABANDONED** action_bridge completed with 66 green tests + 8 red mutations but wired to nothing: IMPLEMENTED_NOT_INTEGRATED since 202
  - `_ops/action_bridge/HANDOFF.md` · `line 5: status: IMPLEMENTED_NOT_INTEGRATED (and 'به هیچ‌چیز وصل نیست و هیچ فلگی ندارد')`
- **[OPS-8] r4.8 DEBT_HIDDEN** T5 supervision taxonomy built and tested but never consumed: tg-center-watchdog.ps1 has zero references to health_metric
  - `_ops/cortex/plans/OCTOPUS-LOOP-CLOSURE-TELEGRAM-2026-08-21.md` · `line 99: T5 supervision taxonomy is built but not consumed — health_metrics.watchdog_truth() exists and is tes`

## coverage

- inventory files_total (md/json/txt ≤2MB): 3802
- read: 2510/5443 (agent census incl. non-text)
- method: marker+content sweep + deep reads on candidates
- excluded: 3460 .mimosa .source baselines, .pyc, .git internals, db/wal/log blobs, >2MB state DBs
