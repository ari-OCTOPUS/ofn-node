# LANE REPORT — OCTOPUS-FLEET-AUDIT-20260918

GOV_VERSION=V8 · LADDER=L2 · read-only probes on all boards + three surgical fixes

## Owner question this lane answers
«الان همه‌چیز با اختاپوس یکپارچه و روی ۷ برد هماهنگ و دیباگه — مطمئنی یا حدس می‌زنی؟»
Answer given: measured, not guessed — and the measurement changed two beliefs (see "Corrections").

## Measured fleet state (two independent sources per layer)

| layer | result | evidence |
|---|---|---|
| NATS transport | **7/7 leaves live** (114,138,180,182,193,100,160) | hub `/leafz`: 7 leafs, 5 subscriptions each |
| Telemetry | **7/7 nodes pulsing < 1 min** | `06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md` |
| Cross-board work | real job `model_infer` commander=138 → worker=193, state **CLOSED** | `state/fleet-jobs/fleet_jobs.jsonl` |
| Capability registry | fresh (23:37Z): 138=coordinator, 193=model_infer(:8193), 100=knowledge_retrieve | `state/fleet-scheduler/node-capabilities.json` |
| Per-node health | 0 failed units on 114/193/180/100/160; 138 = 1 (smartmontools), 182 = 0 after cleanup | ssh to each board |

## Fixes executed
1. **Telemetry key contract (`leaf=None` forever)** — root cause: 138's pulse script published `leaf`, while `fleet-vault-consumer.py` reads `nats_leaf_active` (the key every OTHER node already sends, with a real socket probe). Patched 138's `/usr/local/bin/octopus-138-pulse.sh` (backup `.bak-leafkey-20260917T234628Z`), frame 140→160 B, real leaf probe. **Verified live:** `23:47:29Z 138 load1=2.41 leaf=True`.
2. **182's two failed units cleared** — `octopus-miniscientist-daily` reproduced clean by hand (exit 0 → historical transient); `octopus-gap001-boot-probe` had been OOM-killed 2026-09-15 (mem peak 2 G) and 182 now carries a 2 G swapfile with 1 G headroom. `systemctl reset-failed` both → `FAILED_COUNT_NOW=0`. Honest limit: the boot probe will only be re-tested at the next boot of 182.
3. **`systemd-logind` masking = by design, not a defect** — `/etc/systemd/system/systemd-logind.service -> /dev/null` exists on **138, 182, 114, 193** with the same provisioning date (Mar 31). Corrected my earlier "defect" wording. Consequence to remember: `systemctl reboot` prints `Failed to set wall message … Call to Reboot failed` and still reboots (seen in A7). Use `systemctl --force reboot` in future drills to avoid the confusing message.
4. **W1 verdict automation built** (owner-supplied collector prompt; client-side scheduling was unavailable in this session, so it is wired into our own infrastructure):
   - `138:/home/ari/ofn/tools/w1_verdict_collector.py` + `octopus-w1-verdict.{service,timer}` — fires **once at 2026-09-18 09:20:00Z**, probes 182 read-only over SSH, applies the charter's PASS/FAIL rule (frozen start timestamps 07:18:32/41 UTC, NRestarts=0, no `apply_signed_inbound`, gaps ≤ 900 s, coverage to the planned end), writes the JSON to 138 state **and** to the germline SMB share.
   - laptop: `finalize_w1_verdict.py` + Windows Scheduled Task `OCTOPUS-W1-VERDICT-FINALIZE` (next run 2026-09-18 19:25 local = 09:25Z) copies the verdict into `09-LANES/S2-MATURITY-EXEC-20260917/evidence/W1-VERDICT-20260918.json`, appends the report section, commits.
   - dry-run validated on real data (175 obs samples, 184 frozen-window samples, max gap 301 s, zero unit violations) **and** two collector bugs were caught by that dry run: a `pgrep` self-match that produced a false FAIL, and a muddled coverage comparison. Both fixed before arming.
   - FAIL consequence recorded in the collector and the finalizer: **S1-GAP-02A reverts to FAIL-OPEN-DEBUG** per charter, no partial credit.

## Corrections to earlier statements (honesty log)
- I had recorded 100 and 160 as "blocked behind a credential wall" — **wrong today**: both are live leaves; I reached both over SSH with the piggybank key.
- I reported "JetStream has 0 consumers" — that was about the **fleet-job bus**; the telemetry stream has a durable consumer `vault-pulse` (`fleet-vault-consumer.py`). The job bus remains `SHADOW_LOCAL_JSONL`.

## Still open
- Fleet-job bus durability: `state/fleet-jobs` writes `bus: SHADOW_LOCAL_JSONL` and its own note says "not JetStream durable (0 consumers)" — dispatch is not replayable if the hub dies. Not fixed in this lane (needs a durable consumer + producer switch).
- 138 `smartmontools.service` failed (pre-existing).

## Rollback
Each fix has a backup (`*.bak-leafkey-*` on 138) or is a reversible state reset (`reset-failed`). The new timer/task can be removed with `systemctl disable --now octopus-w1-verdict.timer` and `schtasks /Delete /TN OCTOPUS-W1-VERDICT-FINALIZE`.
