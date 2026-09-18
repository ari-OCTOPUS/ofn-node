---
merge_domain: live-state
merge_key: lane-report:OCTOPUS-LIVE-STATE-20260917
lane: OCTOPUS-LIVE-STATE-20260917
GOV_VERSION: V8
LADDER: L2
mode: READ_ONLY
mutations_performed: 0
status: complete
snapshot_at_utc: 2026-09-17T01:29:08Z
report_written_at_utc: 2026-09-17T01:40:00Z
---

# LANE-REPORT — OCTOPUS-LIVE-STATE-20260917

`GOV_VERSION=V8` · `LADDER=L2` · mode `READ_ONLY` · `mutations_performed=0`

Mission: answer "Is Octopus alive right now, and which parts are breathing?" with a
machine-readable, snapshot-dated, conflict-free artifact set that merges into the single
graph alongside the parallel UNIFIED-RECON lane.

---

## 1. What was done

All six phases executed end to end.

| Phase | Status | Output |
|---|---|---|
| PHASE 0 PREFLIGHT | DONE | UTC/AEST time, vault + ofn-node git baselines, board inventory (7 boards) |
| PHASE 1 HOST LIVENESS | DONE (rev 2) | 7 of 7 registered nodes ALIVE; 182 DEGRADED; 0 unreachable. Rev 1 of this row said "4 ALIVE, 3 UNREACHABLE" and was wrong — see §3.1 |
| PHASE 2 SERVICE & TIMER INVENTORY | DONE | 81 timers across 4 boards, 26 services classified |
| PHASE 3 OPS-AGENT & CONTROL STATE | DONE | queues, 4603 receipts, budget use, 6 breakers, 8 HALT probes |
| PHASE 4 BUSINESS LIVENESS | DONE | funnel, revenue timers, WAL, send authority, owner cards |
| PHASE 5 MESH COHERENCE | DONE | clock drift, deployed versions, daemon reconciliation |
| PHASE 6 OUTPUTS | DONE | 4 artifacts + this report |

### Headline result

**The organism is alive; its money leg is not.** Control plane on 138 is fully awake
(5 long-running daemons active, 42 timers ticking, ops-agent ticking every ~5.5 min, all
breakers closed, budgets at 1/20). But the revenue loop breaks at its **send** stage, and
because that stage is an `ExecStartPost`, its failure also cancels `owner_ask` and
`owner_reply` in the same tick — so the owner receives no revenue card and the owner's
Telegram answers are not read.

Three primary findings, all with closed causal chains:

1. **GAP-01 (CRITICAL)** — `send_queue.py:61` writes `/home/ari/ofn/tools/leads_master.json`;
   the unit has `ProtectHome=read-only` with `ReadWritePaths` that excludes `tools/` ⇒ `EROFS`.
   Ruled out as disk fault: root FS is `ext4 rw`, file is `-rw-r--r-- ari ari`.
   Masked historically behind `if synced:`; now fires every tick because 68 ledger businesses
   vs 66 synced = 2 pending.
2. **GAP-02 (HIGH)** — board 182 runs a `PathExists` fire-loop: `apply-registry` ~13/min,
   `apply-checkpoint` ~4/min, two children at ~100% CPU, started 2026-09-17T01:05:27Z.
3. **GAP-05 (HIGH)** — outbound-effect WAL frozen at 2026-09-02T02:00:10Z (6 rows) while
   `sent-log.jsonl` records 39 sends to 2026-09-16T06:15:59Z.

### Deliverables

- `LIVE-STATE-SNAPSHOT.json` — valid JSON, all 11 required top-level keys present
- `LIVE-STATE-REPORT.md` — Persian, health table for 7 boards
- `LIVE-STATE-COMMANDS.log` — every board command in order with key output
- `OPEN-QUESTIONS.md` — 10 items, each needing mutation or owner decision
- `LANE-REPORT.md` — this file

---

## 2. What remains

Nothing in scope. All phases DONE, no `BLOCKED_WITH_REASON` phases.

Out-of-scope by design, handed to others:

| Item | Owner |
|---|---|
| GAP-01 fix (drop-in or code path) | owner decision — Q-01 |
| GAP-02 fix (`PathExists` → `PathChanged`) | owner decision — Q-02 |
| GAP-05 ledger reconciliation | owner decision — Q-03 |
| GAP-06 swap on 138 | owner decision — Q-04 |
| GAP-03 / GAP-04 / GAP-08 | lower priority — Q-06, Q-07, Q-08 |
| Vault census | UNIFIED-RECON lane (declared `VAULT_CENSUS=IN_PROGRESS_BY_OTHER_LANE`) |

---

## 3. What failed (in my own work, reported honestly)

1. **Breaker mis-read, self-corrected.** My first replication of `budget_allows()` printed
   `B8 => OPEN`. Cause: I omitted the function's legacy `{B8: "RY"}` signature-key mapping.
   After applying it, `B8 => closed`. Published value is `closed`; the error is recorded in
   the snapshot limitations, the command log, and OPEN-QUESTIONS Q-09 so it cannot
   propagate as a false positive into the merged graph.
2. **Shell quoting.** An early compound `ssh … 'python3 -c "…"'` call broke on nested
   parentheses. Switched to piping a script over stdin (`ssh host 'python3 -' < file.py`),
   which is also more auditable.
3. **Output truncation.** The HALT probe and the quote-packet count were cut off in a first
   batched call and had to be re-run.
4. **`python3` absent on the laptop**, only `/c/Program Files/Python313/python`. Switched
   invocation; no effect on results.
5. **Apparent "stuck" units were not stuck.** 182's apply units first read as
   `activating` and looked hung; the journal showed finish→immediate-refire, i.e. a loop.
   Recording this because the first reading was wrong and the second is what matters.
6. **THE BOARD TABLE WAS WRONG — the most serious error in this lane.** Revision 1 reported
   "4 ALIVE, 3 UNREACHABLE" and this reached the owner, who asked why boards that were fine
   yesterday were now unreachable. All three entries were wrong:

   - **CORR-01** — node `.114` (`octopus-pro-114`) was missing entirely. The board list had been
     assembled by hand from hardware-discovery JSONs, `~/.ssh/config` and project memory,
     instead of from the organism's own registry at
     `/home/ari/ofn/state/fleet-nodes/registry.jsonl`. That file lists exactly 7 nodes and was
     only opened near the end of the session.
   - **CORR-02** — `.100` and `.160` were labelled UNREACHABLE. They were reachable all along with
     `~/.ssh/piggybank_id_ed25519`, a key that was *printed in the preflight `ls ~/.ssh/` output and
     never tested*. `Permission denied (publickey)` is an auth rejection on an open port 22 — that
     is not unreachability, and labelling it so was a category error.
   - **CORR-03** — `.191` was listed as a board. It is the Wi-Fi address of this very laptop
     (hostname `DESKTOP-KA9RFN5`); it appears in no fleet registry. A refused port 22 on it is
     expected, not a fault.

   Now corrected in all five artifacts: **all 7 registered nodes ALIVE, 0 unreachable, 182 the only
   DEGRADED one**, with `.114` probed, `.100`/`.160` fully inventoried, and `.191` reclassified as
   `SELF_VANTAGE`. Root-cause lesson for future lanes: **start from the organism's own registry, and
   test every available key before declaring a host unreachable.**

7. **Compounded by trusting memory over evidence.** Project memory said ".100/.160 de-mined
   (never reflash)", which primed me to expect those hosts to be dead. They are alive and running
   Debian 13. The memory note was about their *role* being retired (compute/mining), not about the
   machines being gone. Verify a remembered fact against the live host before letting it shape a
   conclusion.

Nothing on any board failed *because of* this lane — no board state was touched.

---

## 4. Evidence paths

**On the laptop (this lane):**
- `F:\backup\09-LANES\OCTOPUS-LIVE-STATE-20260917\LIVE-STATE-SNAPSHOT.json`
- `F:\backup\09-LANES\OCTOPUS-LIVE-STATE-20260917\LIVE-STATE-REPORT.md`
- `F:\backup\09-LANES\OCTOPUS-LIVE-STATE-20260917\LIVE-STATE-COMMANDS.log`
- `F:\backup\09-LANES\OCTOPUS-LIVE-STATE-20260917\OPEN-QUESTIONS.md`

**On board 138 (`ari@192.168.0.138`):**
- journal: `sudo -n journalctl -u octopus-revenue-drive.service` → `EROFS` at 2026-09-17T00:00:51Z
- unit: `/etc/systemd/system/octopus-revenue-drive.service` + drop-ins
  `20-octopus-wire-env.conf`, `i7-auto-stage.conf`
- source: `/home/ari/ofn/state/revenue-drive/send_queue.py` (sha256 `d05820359f2ecde645dddcbe738fd3a40baa7a9b7c468e4178609364a7440365`)
- funnel: `…/revenue-drive/season-meter.json`, `lead-emails.jsonl`, `sent-log.jsonl`,
  `channel-authorization.json`, `i7-runtime.json`, `owner-review.json`
- WAL: `/home/ari/ofn/ofn/agi2027_runtime/outbound-effects.sqlite3` (12288 B, 6 rows)
- WAL empty: `/home/ari/ofn/state/revenue-drive/outbound-effects.sqlite3` (0 B)
- receipts: `…/ops-agent/state/ops-receipts.jsonl` (4603 rows)
- deployed bytes: `…/ops-agent/ops_agent.py` sha256 `b2d48553458bb920d33611df1cfbd6808ed7a86e2ba64ea80e4f8c4ab902208e`
  = byte-identical to `…/coding-worker/stage/B5-SCOPE-GUARD-20260916/ops_agent.py`

**On board 182 (`root@192.168.0.182`):**
- `journalctl -u octopus-apply-registry.service` / `octopus-apply-checkpoint.service`
- `/etc/systemd/system/octopus-apply-checkpoint.path` (`PathExists=`)
- `/var/lib/octopus/inbound/SIGNED-CHECKPOINT-BUNDLE/checkpoint.json.sig` (mtime Aug 22 11:54)
- `ps -eo pcpu,rss,args` → `octopus_sensorium.app` RSS 1921168 KiB

---

## 5. Rollback steps

**This lane requires no rollback: `mutations_performed = 0`.** No service was
started/stopped/restarted/enabled; no flag, HALT, budget, `gates.json` or ledger was written;
no file on any board was created, deleted, moved, renamed or overwritten.

To undo the lane's only footprint (four new files inside its own directory, plus one new
directory), delete or archive the directory:

```
F:\backup\09-LANES\OCTOPUS-LIVE-STATE-20260917\
```

Per AGENTS.md §7, prefer moving it to `99-ARCHIVE/` with an `archive_` prefix over
`rm -rf`. No other path was written, so nothing else needs restoring.

Board-side: **nothing to roll back.** If a future session acts on Q-01/Q-02, the rollback
for those changes is that respective session's responsibility — Q-01 already has a
pre-image on disk (`leads_master.json.pre-email-sync-20260915`), and Q-02 should take a
pre-image of both `.path`/`.service` units before editing.

---

## 6. Compliance statement

- **Truth hierarchy (§1):** every claim is level 1 (runtime output: live journal, systemctl,
  `ps`, sqlite reads) or level 2 (repository/ledger files). Nothing rests on chat summaries
  or agent memory. Where a number could not be measured it is marked as a limitation.
- **Number discipline (§3):** no synthetic data; every figure has a source path or a named
  measurement command. The 182 memory figure that moved between reads (875 MiB → 1526 MiB)
  is reported as both values rather than silently picking one.
- **Output boundaries (§4):** no `OCTOPUS_WIRE_*` / `OFN_WIRE_*` flag was touched in either
  direction; no email was sent; no blocked gate was opened.
- **Self-elevation ban (§5):** nothing was elevated or edited.
- **Owner decisions (§6):** nothing was decided on the owner's behalf; all open items are in
  `OPEN-QUESTIONS.md` with `status: open, requires: owner_decision`.
- **Deletion and naming (§7):** no `rm -rf`, no renames.
- **Secrets:** no secret value was printed, transmitted, copied or committed — only paths,
  sizes, row counts, states and hashes.
- **Coexistence (§2 of mission):** the only writes were inside this lane's directory; the
  commit (if made) stages only `09-LANES/OCTOPUS-LIVE-STATE-20260917`.
- **Merge rule:** every artifact carries `merge_domain: live-state` and a unique `merge_key`.
  Where the parallel lane's statement differed (the WAL size), the report records both as
  true of different files under `AS_OF_NOW` rather than asserting the other lane was wrong.

---

## 7. Twelve-line Persian summary

1. Octopus زنده است: هر هفت نودِ ثبت‌شده (۱۳۸، ۱۸۰، ۱۸۲، ۱۰۰، ۱۶۰، ۱۹۳، ۱۱۴) زنده‌اند و لایهٔ کنترل ۱۳۸ کامل بیدار است.
2. هر هفت نودِ ثبت‌شده (۱۳۸، ۱۸۰، ۱۸۲، ۱۰۰، ۱۶۰، ۱۹۳، ۱۱۴) زنده و در دسترس‌اند؛ صفر نود در دسترس‌نیافته. (نسخهٔ ۱ اینجا غلط بود.)
3. ۸۱ تایمر روی چهار برد در چرخه‌اند؛ هیچ دیمنی که سند زنده بداندش پیدا نشد نباشد، وجود ندارد.
4. `ops-agent` هر ~۵.۵ دقیقه تیک می‌زند و همهٔ بریکرها (B1..B8) بسته‌اند؛ بودجه ۱ از ۲۰ مصرف شده.
5. هیچ فایل توقف (HALT/STOP-AUTONOMY/CHANNEL-REVOKED) وجود ندارد — سیستم متوقف نیست.
6. **اما حلقهٔ درآمد ۱۳۸ از نیمه‌شب در مرحلهٔ ارسال می‌شکند** (`Errno 30 Read-only file system`).
7. علتش خرابی دیسک نیست — سندباکس خود systemd مسیر `tools/` را فقط‌خواندنی کرده است.
8. چون این مرحله `ExecStartPost` است، `owner_ask` و `owner_reply` هم کنسل می‌شوند: کارت درآمد نرفت و پاسخ مالک خوانده نشد.
9. **برد ۱۸۲ در یک حلقهٔ داغ دو هسته می‌سوزاند** — از ساعت ۰۱:۰۵:۲۷Z امروز، ~۱۳ اجرا در دقیقه فقط برای registry.
10. دفتر WAL از ۲ سپتامبر یخ زده (۶ ردیف) در حالی که دفتر ارسال ۳۹ ارسال تا ۱۶ سپتامبر دارد — این دو نمی‌خوانند.
11. ۱۳۸ هیچ swap ندارد، در حالی که پرکارترین برد است و نگهبانان مرز قرمز پول روی آن اجرا می‌شوند.
12. **درآمد تأییدشده صفر است** (`verified_cash = 0.0`) و ۴۳۳ بررسی پیاپی سفارش صفر — گلوگاه تقاضاست، نه تحویل.
