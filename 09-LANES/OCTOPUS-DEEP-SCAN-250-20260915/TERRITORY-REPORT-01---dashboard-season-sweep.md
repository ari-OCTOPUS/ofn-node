# TERRITORY-REPORT — 01 - Dashboard (season sweep)

findings: **8** · classes: SEASON_LEFTOVER 8

## top findings (rank order)

- **[SE-3] r10.0 SEASON_LEFTOVER** verified_cash still $0.00 — Ziman store live with 251+ checkout checks and zero orders
  - `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `09-15 05:15Z block: verified_cash = $0.00 — فروشگاه زیمان live ولی ۲۵۱+ چک صفر سفارش`
- **[SE-5] r7.0 SEASON_LEFTOVER** Containment rollback plan never exercised while organism self-deploys patches
  - `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `09-15 04:45Z block: containment rollback: برنامهٔ مهار آزموده نشده`
- **[SE-14] r7.0 SEASON_LEFTOVER** ziman-gift.com NXDOMAIN (expired) — owner renewal card unanswered since 09-08 while store counts traffic
  - `01 - Dashboard/UNLOCK-PLAN-2026-09-08.md` · `line 15-19: ziman-gift.com = NXDOMAIN — دامنه خریده expire شده. فقط تو می‌توانی تمدیدش کنی. ... وضعیت: ___`
- **[SE-1] r4.8 SEASON_LEFTOVER** Nodes 114/160 run via nohup — systemd units never installed (continuity risk)
  - `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `09-15 05:15Z block: 114/160 systemd unit نصب نشده (nohup کار میکنند)`
- **[SE-6] r4.8 SEASON_LEFTOVER** G27 producer ACK boundary lacks WAL/atomic temp-file — known receipt-loss window left open
  - `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `09-15 04:45Z block: G27 (producer ACK boundary): ساختار at-most-once؛ نیاز به WAL یا temp-file atomic`
- **[SE-4] r4.6 SEASON_LEFTOVER** Memory durability restart/restore: two same-day verdicts conflict (PARTIAL-untested vs PASS)
  - `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `04:45Z block: MEMORY durability: تست restart/restore (MEMORY: PARTIAL, هنوز تست نشده) vs 05:15Z block: MEMORY:`
- **[SE-15] r4.6 SEASON_LEFTOVER** UNLOCK-REGISTRY rows L04 (secret_rotation) and L11 (OWNER_KEY rewording) frozen at PROPOSED since 09-08
  - `01 - Dashboard/UNLOCK-REGISTRY-2026-09-08.md` · `row L04: L04 | secret_rotation | مالک چرخش را waive کرد (09-07) -> گیت را بگذار باز تا کد stale نشود | PROPOSE`
- **[SE-2] r2.6 SEASON_LEFTOVER** PB-1 24-hour continuity window cannot PASS before 2026-09-16T04:31Z — verdict still open
  - `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `09-15 04:45Z block: PB-1: منتظر ۲۴ ساعت (اولین PASS ممکن: 2026-09-16T04:31Z)`

## coverage

- read: n/a (carried group; per-item anchors in FORGOTTEN-250.json)
