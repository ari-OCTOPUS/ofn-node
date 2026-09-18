# Hardware handoff evidence review — 2026-09-15

GOV_VERSION=V8 · LADDER=L2

Owner: Codex /root. Lane: HARDWARE-HANDOFF-REVIEW-20260915.
Scope: review of the supplied handoff and stored evidence, not execution of its six deployment tasks.
Worktree: `F:/hardware-handoff-review-20260915`.
Branch: `codex/hardware-handoff-review-20260915`.
Source repository HEAD observed: `1eb5b1010a401f9ee2b047933dc18575aa1b8e5b`.
Verdict: REVIEW_COMPLETE; live capacity and utilization NOT_MEASURED in this review.

## What was verified

The named megaprompt, metadata, evidence and two raw JSON files exist under
`F:/backup/09-LANES/OCTOPUS-HARDWARE-ENROLLMENT-20260915/`.
Local git log contains `f170c31` and `1eb5b10`. Mesh commit `2d1793bda` was not queried on node138.
Both raw arrays parse and contain seven node rows. Recomputed sums are 56 cores,
27370 in the raw RAM field labelled MB, and 322 in the raw disk-free field labelled GB.
These are stored inventory observations, not fresh live measurements or pooled resources.
All seven capability rows contain `DRIVER=RKNPU` and the RK3588 NPU device-tree compatible string.

## Findings

### 1. NPU enumeration does not establish usable throughput or inactivity

The stored raw data supports driver/device enumeration on seven named nodes at collection time.
It contains no model execution, output validation, utilization interval, latency or throughput data.
The metadata field `tops_total_unused: 42` and the prompt's `100% idle` overstate this evidence.
Treat 7 x 6 TOPS as summed vendor nominal capacity, not measured fleet throughput. TOPS means
tera-operations per second, not TFLOPS. The seven NPUs are separate devices.
`librknnrt` absence is asserted in metadata but not demonstrated by these two raw dumps or EVIDENCE.md;
even an absent library in a searched location would not prove no alternative/containerized consumer.
The key `DRM[device]` does not preserve a per-node render-device mapping; do not hardcode renderD129.

Official sources consulted:
- [Rockchip RK3588 announcement](https://www.rock-chips.com/a/cn/news/rockchip/2022/0303/1544.html): nominal 6 TOPS NPU.
- [Rockchip RKNN Toolkit2](https://github.com/airockchip/rknn-toolkit2): model conversion, board-side runtime and inference workflow.

### 2. Collector output has unresolved fields

All 7 capability rows have empty `SVC` and `MEMINFO_SWAP`; all 7 inventory rows contain the
literal `$VERSION_CODENAME`. Empty output must be UNKNOWN/collection error, not zero services,
no swap or a successful OS read. Raw RUNNING_SERVICES on 100/160/193/114 are 8/6/6/6;
these total counts neither prove nor disprove zero OCTOPUS services. A scoped service inventory
must supply names, filter definition, exit status and collection time.
The selected evidence lacks independent per-board timestamps, boot IDs and command outcomes.

### 3. Completion criteria allow incomplete mission to be called done

T2 permits enabling a subset; DoD requires only one NPU; T3 may remain unbuilt. T5 has no explicit
acceptance test, and DoD omits dispatch and T6. Split proof-of-concept acceptance from full-fleet
completion. Report a 7-row outcome matrix with failed/unknown/not-run nodes retained in denominator.
For dispatch acceptance trace one job ID through enqueue, dispatch, ACK, persisted result and readback;
exercise duplicate, expired and unreachable-worker outcomes without losing the receipt chain.
Power is in the T6 title but its acceptance only measures temperature. If no trustworthy power
sensor exists, record power NOT_MEASURED and do not infer watts from temperature.

### 4. Address persistence acceptance is narrower than the observed identity problem

One reboot tests persistence for the same boot medium. It does not test the reported MAC change
between SD and eMMC. A DHCP reservation tied to the old MAC needs an explicit media-change strategy.
Do not claim this failure mode resolved from one successful reboot. Keep node138's no-power-off
constraint explicit in any reboot acceptance procedure.

## Copy-ready replacement for the headline

در دامپ ذخیره‌شده، درایور RKNPU برای هر هفت برد شناسایی شده است. ظرفیت اسمی اعلام‌شده برای
این خانواده ۶ TOPS به‌ازای هر تراشه و جمع اسمی هفت برد ۴۲ TOPS است. اجرای واقعی مدل، ظرفیت
پایدار قابل‌استفاده و میزان استفاده فعلی هنوز در این بسته اندازه‌گیری نشده‌اند. وضعیت:
NPU_ENUMERATION_RECORDED=7/7؛ NPU_INFERENCE=NOT_MEASURED؛ NPU_UTILIZATION=UNKNOWN؛
FLEET_THROUGHPUT=NOT_MEASURED. TOPS واحد تعداد عملیات است، نه ترافلاپس.

## Next bounded acceptance

First repair/re-run the collector with per-node identity, UTC timestamps, boot ID, explicit units,
command exit codes and separated stderr. Preserve the old raw files. Reconfirm the chosen worker's
headroom before enabling a pilot. Pin driver/runtime/toolkit and model hashes; record input shape,
precision, warm-up and sample counts, output correctness, p50/p95 latency, throughput, memory and
temperature. Preserve device-execution evidence. Expand only after that pilot is accepted; publish
per-board results and measured concurrent fleet throughput separately from nominal TOPS.

## Source hashes (SHA256)

| Source basename | SHA256 |
|---|---|
| NEXT-AGENT-MEGAPROMPT.md | 897F2A5B740FB002CC101B17F1D2C86EA3A0954937FC4BB3A5DB445DF5D63875 |
| FLEET-METADATA.json | F3F73B5CB6FE3AC9DE2A86C1822E517E0EC8C60F4F2E0CC23F00F35A515D3A51 |
| raw-fleet-inventory.json | A600FDAF7291B7865D67D7EF68F942CCD815858827579B1197CDFEE2634B82CA |
| raw-fleet-capabilities.json | F880DBFE338E6680800D396F915240E6A4B7CC0DEA6804486338A0C1A125CF5A |
| EVIDENCE.md | 1CF8287A5FD60A15B59E479A0D04CA957F861CCA907B35AAE3C3A8C1B18F5AF2 |

## Changes, failures, remaining work and rollback

Created only this review report in a separate sparse worktree. Original evidence and handoff files
remain untouched. No board contact, installs, reboot, card write, service change, commit or push.
Validation: parsed raw JSON; recomputed totals; counted seven RKNPU rows, seven empty service fields
and seven unresolved OS fields; recorded source hashes. No runtime tests were run.
Remaining: collector repair and fresh census, hardware benchmarks, six implementation tasks,
and a separately scoped physical rescue-card operation if requested.
Rollback: no live rollback needed. Retain or archive this independent report/worktree; it has no
runtime consumer. Original lane ownership is preserved.
