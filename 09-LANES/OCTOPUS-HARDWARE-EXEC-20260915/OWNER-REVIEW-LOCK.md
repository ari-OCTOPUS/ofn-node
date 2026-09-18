# HW HANDOFF — OWNER REVIEW LOCK (2026-09-15)

- **mode:** docs/queue only · **NO** install / service change / reboot / card write / commit
- **stamp:** 2026-09-15T03:04:00Z
- **bridge:** PC_worker (file hash + summary only)
- **HOLD customer_send:** true · **GO-B4:** deny this turn · **no live NPU install** without owner GO

## Source SoT

| artifact | path | sha256 |
|----------|------|--------|
| LANE-REPORT.md | `F:\hardware-handoff-review-20260915\09-LANES\HARDWARE-HANDOFF-REVIEW-20260915\LANE-REPORT.md` | `8922bc4e51ae054a30910f798b4518ef0720c54afc5db4d3b5a4bcc23729c600` |
| Worktree | `F:\hardware-handoff-review-20260915` | — |
| Branch | `codex/hardware-handoff-review-20260915` | HEAD observed in report: `1eb5b101…` |
| Evidence lane (cited) | `F:\backup\09-LANES\OCTOPUS-HARDWARE-ENROLLMENT-20260915\` | see report source table |

Report verdict: **REVIEW_COMPLETE**; live capacity / utilization **NOT_MEASURED** this review.

## Owner-confirmed facts

- RKNPU identified in raw dump on **all 7** boards
- Core sum **56** OK; RAM MB field sum **27370**; free disk GB field **322** OK
- Model-on-NPU **NOT proven** in reviewed evidence
- “Nobody uses NPU” = **UNKNOWN** without consumption measure
- **6 TOPS** = vendor **NOMINAL** per chip; **42 TOPS** = sum of nominal specs — **NOT** measured fleet usable power
- TOPS ≠ TFLOPS
- Rockchip cite: https://www.rock-chips.com/a/cn/news/rockchip/2022/0303/1544.html

## DENY claim language

Do **not** claim: «۴۲ TOPS آماده و بلااستفاده» — no measurement backing.

## Corrected megaprompt headline (verbatim SoT)

«در دامپ ذخیره‌شده، درایور RKNPU روی هر هفت برد شناسایی شده است. جمع ظرفیت اسمی اعلام‌شدهٔ تراشه‌ها ۴۲ TOPS است. اجرای واقعی مدل، توان پایدار قابل‌استفاده و میزان استفادهٔ فعلی هنوز اندازه‌گیری نشده‌اند. گام بعدی، اجرای مدل با خروجی معتبر و ثبت تأخیر، نرخ پردازش و شاهد اجرای NPU روی هر برد است.»

## Three required fixes (organism; HQ implement DENY for live hardware mutations)

1. **Collector incomplete:** all 7 rows `SVC` empty; `OS_CODENAME` literal `$VERSION_CODENAME` — empty ≠ zero services; `librknnrt` absence needs independent witness in raw dumps
2. **Done-definition weak:** must record per-board results for all 7; separate pilot success from fleet complete; model-server + cross-node job + monitoring in acceptance
3. **One reboot ≠ prove MAC change** across boot media; DHCP MAC reserve needs explicit SD→eMMC plan

## LANE-REPORT findings (compressed)

1. NPU enumeration ≠ usable throughput / inactivity; `tops_total_unused: 42` and “100% idle” overstate evidence
2. Collector unresolved fields (SVC / MEMINFO_SWAP / `$VERSION_CODENAME`); RUNNING_SERVICES totals alone do not prove OCTOPUS service inventory
3. Completion criteria allow incomplete mission to be called done — split PoC vs 7-row fleet matrix; power NOT_MEASURED if no sensor
4. Address persistence: one reboot same medium ≠ SD/eMMC MAC change; keep node138 no-power-off constraint

## Next bounded acceptance (from report)

Repair/re-run collector with per-node identity, UTC timestamps, boot ID, units, exit codes; pin driver/runtime/toolkit + model hashes; pilot with latency/throughput/correctness + device-execution evidence; expand only after pilot accepted. Publish per-board results separate from nominal TOPS.

## Gates

- No board contact / installs / reboot / card write / service change / commit / push this turn
- HOLD customer_send
- Machines: DESKTOP-KA9RFN5 reachable for this hash (COMMANDER had ListMachines empty earlier)

— PC_worker · bridge hash+summary · OWNER HARDWARE REVIEW LOCK 2026-09-15
