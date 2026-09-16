---
type: evidence
session: ERRORHUNT-RAW
created: 2026-08-16
window: 2026-08-09 .. 2026-08-16
mode: read-only harvest
---

# ERRORHUNT RAW — 2026-08-16

- harvested_at: 2026-08-16T11:24:48 local
- window_start: 2026-08-09
- event_rows: 1173
- cluster_keys: 55

## Notes / coverage

- DBs opened uri mode=ro + PRAGMA query_only
- secrets redacted from samples (token prefixes only)
- daemon-launch*.err.log exist only for 2026-08-16 boots (gen1/2/3)
- _flaky: files whose mtime is inside window, not necessarily new flakes
- **pass-2 corrections (do not use first-regex counts for REVIVE or readback-fail):**
  - `REVIVE` regex also matched `no revive` on STOP-CORTEX lines (73 → real **5** REVIVE in window)
  - `یافت نشد` over-matched non-readback lines; sqlite: pre-fix 11 fail / post-05:00 **67/67 ok, 0 fail**
  - dashboard column is `summary` not `message` (first pass skipped events; pass-2 used correct schema)
  - pass-2 script: `_errorhunt_pass2.py`

## Clusters (source::kind)

| count | first | last | key | sample |
|---:|---|---|---|---|
| 451 | 2026-08-09T00:15:55 | 2026-08-16T05:32:57 | `governor-alerts.md::governor-alert` | - ⚠️ circuit OPEN for orchestr (fail_count=5) HTTPError: HTTP Error 429: Too Many Requests |
| 85 | 2026-08-16 05:02:14 | 2026-08-16 10:32:00 | `daemon-launch2.err.log::task-blocked` | 2026-08-16 05:02:14,130 INFO brain.events: event task.blocked [blocked] ⛔ تغییر رد شد (رد شد — تازگیِ کمتر (0.0 < 0.0))  |
| 73 | 2026-08-09T08:44:05 | 2026-08-16T04:34:03 | `watchdog-log.txt::cortex-revive` | 2026-08-09T08:44:05 cortex: REVIVE (2 consecutive misses) |
| 68 | 2026-08-11T21:18:56 | 2026-08-15T20:34:49 | `_flaky::flaky-file` | S1-05_test_ap_binding.py.txt |
| 57 | 2026-08-16 05:00:47 | 2026-08-16 10:33:08 | `daemon-launch2.err.log::readback-ok` | 2026-08-16 05:00:47,726 INFO brain.events: event memory.readback [ok ] read-back فرضیه #1098 — تأیید شد(r16-view:dedup) |
| 50 | 2026-08-12T18:48:03 | 2026-08-12T22:53:02 | `live-watchdog-log.txt::live-halt-no-revive` | 2026-08-12T18:48:03 global HALT-ALL/architect-STOP present - not reviving 8773 |
| 50 | 2026-08-12T18:47:02 | 2026-08-12T22:52:01 | `tg-center-watchdog-log.txt::center-halt-no-revive` | 2026-08-12T18:47:02 global HALT-ALL/architect-STOP present - not reviving centre |
| 46 | 2026-08-09T00:16:00 | 2026-08-16T06:01:26 | `paid-timeout-alerts::paid-timeout-alert` | {"ts": "2026-08-09T00:16:00", "role": "glm", "max_tokens": 1200, "need_s": 79.5, "cap_s": 54.0, "why": "سقفِ سوکت زیرِ ن |
| 43 | 2026-08-16 05:05:31 | 2026-08-16 10:26:55 | `daemon-launch2.err.log::daemon-warning` | 2026-08-16 05:05:31,949 INFO brain.events: event task.completed [warning] کرنل: ADR=10I/7O/3R · high=3 · action=review · |
| 42 | 2026-08-16 05:08:25 | 2026-08-16 10:29:33 | `daemon-launch2.err.log::readback-fail` | 2026-08-16 05:08:25,520 INFO brain.events: event task.completed [ok ] 🛡️ لنگرها سالم · بدونِ ویرایشِ کد · نوشتن فقط در ن |
| 29 | 2026-08-16 03:57:09 | 2026-08-16 04:56:22 | `daemon-launch.err.log::readback-fail` | 2026-08-16 03:57:09,524 INFO brain.events: event memory.readback [error ] read-back فرضیه #1087 — یافت نشد! |
| 16 | 2026-08-16 03:58:42 | 2026-08-16 04:59:08 | `daemon-launch.err.log::task-blocked` | 2026-08-16 03:58:42,504 INFO brain.events: event task.blocked [blocked] ⛔ تغییر رد شد (رد شد — تازگیِ کمتر (0.0 < 0.0))  |
| 16 | 2026-08-11T19:27:16 | 2026-08-16T00:53:16 | `organ-gate-log::organ-denied` | {"ts": "2026-08-11T19:27:16", "op": "reserve", "organ": "ZIMAN", "est_usd": 0.001, "task": "seam-noimport", "allow": fal |
| 12 | 2026-08-09 02:58:03 | 2026-08-16 06:58:04 | `miniapp-watchdog-log.txt::tunnel-restart` | 2026-08-09 02:58:03 tunnel state: alive=False urlFresh=False - restarting tunnel script. |
| 11 | 2026-08-16 10:36:29 | 2026-08-16 11:17:22 | `daemon-launch3.err.log::task-blocked` | 2026-08-16 10:36:29,508 INFO brain.events: event task.blocked [blocked] ⛔ تغییر رد شد (رد شد — تازگیِ کمتر (0.0 < 0.0))  |
| 10 | 2026-08-09T08:39:05 | 2026-08-14T11:44:04 | `watchdog-log.txt::cortex-dead-miss` | 2026-08-09T08:39:05 cortex: dead (miss 1/2) |
| 9 |  |  | `daemon-launch2.err.log::rag-score-warn` | F:\backup\4d_system\memory\vectorstore.py:318: UserWarning: Relevance scores must be between 0 and 1, got [(Document(id= |
| 8 | 2026-08-16 04:01:57 | 2026-08-16 04:57:59 | `daemon-launch.err.log::daemon-warning` | 2026-08-16 04:01:57,043 INFO brain.events: event task.completed [warning] کرنل: ADR=10I/7O/3R · high=3 · action=review · |
| 8 | 2026-08-16 10:35:15 | 2026-08-16 11:19:20 | `daemon-launch3.err.log::readback-ok` | 2026-08-16 10:35:15,105 INFO brain.events: event memory.readback [ok ] read-back فرضیه #1155 — تأیید شد(r16-view:dedup) |
| 8 | 2026-08-09T08:42:04 | 2026-08-15T14:52:17 | `tg-center-watchdog-log.txt::center-down-launch` | 2026-08-09T08:42:04 centre down (silent 17545s) - launching RUN-TG-CENTER.bat |
| 6 | 2026-08-16 04:00:41 | 2026-08-16 04:00:45 | `daemon-launch.err.log::hf-404` | 2026-08-16 04:00:41,729 INFO httpx: HTTP Request: HEAD https://huggingface.co/sentence-transformers/paraphrase-multiling |
| 6 | 2026-08-16 05:04:06 | 2026-08-16 05:04:09 | `daemon-launch2.err.log::hf-404` | 2026-08-16 05:04:06,067 INFO httpx: HTTP Request: HEAD https://huggingface.co/sentence-transformers/paraphrase-multiling |
| 6 | 2026-08-16 10:38:47 | 2026-08-16 10:38:51 | `daemon-launch3.err.log::hf-404` | 2026-08-16 10:38:47,325 INFO httpx: HTTP Request: HEAD https://huggingface.co/sentence-transformers/paraphrase-multiling |
| 6 | 2026-08-16 10:40:00 | 2026-08-16 11:21:33 | `daemon-launch3.err.log::daemon-warning` | 2026-08-16 10:40:00,590 INFO brain.events: event task.completed [warning] کرنل: ADR=10I/7O/3R · high=3 · action=review · |
| 6 | 2026-08-09T08:43:02 | 2026-08-14T11:43:04 | `live-watchdog-log.txt::live-down-launch` | 2026-08-09T08:43:02 8773 down - launching run-live-headless.bat |
| 5 | 2026-08-16 10:42:37 | 2026-08-16 11:14:07 | `daemon-launch3.err.log::readback-fail` | 2026-08-16 10:42:37,582 INFO brain.events: event task.completed [ok ] 🛡️ لنگرها سالم · بدونِ ویرایشِ کد · نوشتن فقط در ن |
| 5 | 2026-08-09T08:44:06 | 2026-08-14T11:44:04 | `watchdog-log.txt::cortex-launch` | 2026-08-09T08:44:06 cortex: launched RUN-CORTEX.bat |
| 5 | 2026-08-09 08:52:03 | 2026-08-14 11:52:04 | `watchdog.log::organism-watchdog-event` | ﻿2026-07-07 23:37:03 revived organism (port 8771 was dead, no STOP flags) |
| 2 | 2026-08-16 04:00:39 | 2026-08-16 04:00:39 | `daemon-launch.err.log::hf-unauth-warn` | Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and  |
| 2 |  |  | `daemon-launch.err.log::rag-score-warn` | F:\backup\4d_system\memory\vectorstore.py:318: UserWarning: Relevance scores must be between 0 and 1, got [(Document(id= |
| 2 | 2026-08-16 05:04:04 | 2026-08-16 05:04:04 | `daemon-launch2.err.log::hf-unauth-warn` | Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and  |
| 2 | 2026-08-16 10:38:45 | 2026-08-16 10:38:45 | `daemon-launch3.err.log::hf-unauth-warn` | Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and  |
| 2 |  |  | `daemon-launch3.err.log::rag-score-warn` | F:\backup\4d_system\memory\vectorstore.py:318: UserWarning: Relevance scores must be between 0 and 1, got [(Document(id= |
| 2 | 2026-08-12T08:07:04 | 2026-08-16T00:27:03 | `tg-center-watchdog-log.txt::stop-tg-center` | 2026-08-12T08:07:04 STOP-TG-CENTER present - not reviving centre |
| 2 | 2026-08-13T20:03:25 | 2026-08-15T14:52:06 | `tg-center-watchdog-log.txt::center-hung` | 2026-08-13T20:03:25 centre HUNG (alive, silent 411s) - killing pid 24028 then relaunching |
| 2 | 2026-08-16T05:32:55 | 2026-08-16T05:43:40 | `telegram-pep-shadow::pep-deny` | {"ts": "2026-08-16T05:32:55", "sender": "tg_api._call_post", "action": "editMessageText", "params_sha": "04733cd66d9fc1a |
| 2 | 2026-08-15T17:58:05+00:00 | 2026-08-15T19:14:25+00:00 | `POISONING-WATCH::poisoning-ok` | 🟢 سالم 2026-08-15T17:58:05+00:00 - telemetry(windowed): jobs/read/ratio/readback = 32 32 1.0 2 1 - semantic: کل=238 نو-پ |
| 1 | 2026-08-16 03:56:27 | 2026-08-16 03:56:27 | `daemon-launch.err.log::reference-dir-warn` | 2026-08-16 03:56:27,835 WARNING config.settings: settings: REFERENCE_DIR='./' به ریشهٔ پروژه resolve شد — مرزِ نامعتبر ( |
| 1 | 2026-08-16 03:56:36 | 2026-08-16 03:56:36 | `daemon-launch.err.log::notify-not-configured` | 2026-08-16 03:56:36,409 INFO brain.notify: decision packet [summary] → queued (not-configured): milestone مرزِ دانش |
| 1 | 2026-08-16 05:00:08 | 2026-08-16 05:00:08 | `daemon-launch2.err.log::reference-dir-warn` | 2026-08-16 05:00:08,924 WARNING config.settings: settings: REFERENCE_DIR='./' به ریشهٔ پروژه resolve شد — مرزِ نامعتبر ( |
| 1 | 2026-08-16 05:00:14 | 2026-08-16 05:00:14 | `daemon-launch2.err.log::notify-not-configured` | 2026-08-16 05:00:14,285 INFO brain.notify: decision packet [summary] → queued (not-configured): milestone مرزِ دانش |
| 1 | 2026-08-16 10:34:38 | 2026-08-16 10:34:38 | `daemon-launch3.err.log::reference-dir-warn` | 2026-08-16 10:34:38,139 WARNING config.settings: settings: REFERENCE_DIR='./' به ریشهٔ پروژه resolve شد — مرزِ نامعتبر ( |
| 1 | 2026-08-16 10:34:42 | 2026-08-16 10:34:42 | `daemon-launch3.err.log::notify-not-configured` | 2026-08-16 10:34:42,197 INFO brain.notify: decision packet [summary] → queued (not-configured): milestone مرزِ دانش |
| 1 | 2026-08-13T20:03:33 | 2026-08-13T20:03:33 | `tg-center-watchdog-log.txt::center-orphan-reap` | 2026-08-13T20:03:33 reaping 1 orphan centre process(es) |
| 1 |  |  | `dashboard_events::schema-mismatch` | ['id', 'timestamp', 'trace_id', 'agent_id', 'event_name', 'status', 'summary', 'duration_ms', 'next_action', 'approval_s |
| 1 | 2026-08-16T11:24:48 | 2026-08-16T11:24:48 | `4d_experiments.db::db-summary` | sqlite summary |
| 1 | 2026-08-16T11:24:48 | 2026-08-16T11:24:48 | `_flaky::flaky-summary` | total_files=127 in_window=68 |
| 1 |  |  | `doctor-vitals::vitals` | {"ts": 1786827602.3839598, "schema": "doctor-vitals.v1", "missions_total": {"value": 1, "provenance": "درون‌زاد"}, "miss |
| 1 | 2026-08-16T11:14:14 | 2026-08-16T11:14:14 | `cortex-watchdog.json::snapshot` | {"status": "alive", "attempts": [], "last_check": 1786842854} |
| 1 | 2026-08-16T11:25:10 | 2026-08-16T11:25:10 | `daemon_state.json::snapshot` | {"pid": 27164, "errors_this_run": 0, "paused": false, "generation": 9, "kernel": {"reachable": true, "manifest_fresh": t |
| 1 | 2026-08-14T11:52:04 | 2026-08-14T11:52:04 | `watchdog.log::mtime` | size=4647 |
| 1 | 2026-08-14T11:43:04 | 2026-08-14T11:43:04 | `live-watchdog-log.txt::mtime` | size=5170 |
| 1 | 2026-08-16T11:18:27 | 2026-08-16T11:18:27 | `miniapp-watchdog-log.txt::mtime` | size=90680 |
| 1 | 2026-08-16T00:27:03 | 2026-08-16T00:27:03 | `tg-center-watchdog-log.txt::mtime` | size=6404 |
| 1 | 2026-08-16T11:24:18 | 2026-08-16T11:24:18 | `watchdog-log.txt::mtime` | size=206810 |

## JSON

Companion: `ERRORHUNT-RAW-2026-08-16.json` (full rows, redacted samples).
