# OCTOPUS-HARDWARE-EXEC-20260915 — LANE-REPORT

GOV_VERSION=V8  
LADDER=L2  
FREEDOM-V2: **green** for this internal, reversible, non-TCB work  
HOLD customer_send: **true**  
Lane: `F:\backup\09-LANES\OCTOPUS-HARDWARE-EXEC-20260915\`  
Updated: 2026-09-15 (docs write after T0)

---

## Mission

Execute the hardware follow-on after enrollment and owner review: honest fleet census (T0), then T1–T6 with split DoD (pilot ≠ fleet matrix), corrected NPU language (nominal-only / NOT_MEASURED), and MAC SD↔eMMC strategy for T4. No customer_send.

---

## Source of Truth (SoT)

| artifact | path / note | sha256 |
|----------|-------------|--------|
| NEXT-AGENT-MEGAPROMPT.md (enrollment) | `F:\backup\09-LANES\OCTOPUS-HARDWARE-ENROLLMENT-20260915\NEXT-AGENT-MEGAPROMPT.md` | `897F2A5B740FB002CC101B17F1D2C86EA3A0954937FC4BB3A5DB445DF5D63875` |
| Owner review LANE-REPORT | cited in OWNER-REVIEW-LOCK / OWNER-REVIEW-LANE-REPORT | `8922bc4e51ae054a30910f798b4518ef0720c54afc5db4d3b5a4bcc23729c600` |
| fleet-inventory-v2.sh | `scripts\fleet-inventory-v2.sh` | `1c437c9cf3e3aa6d035b8b05fd112add4eac00329ec3ae858d8f8202d9ccefbc` |
| fleet-collect-t0.sh | `scripts\fleet-collect-t0.sh` | `9291a4a9ea2866524822c6866f6393f648ee017c6a83eac4591e4b321da917ec` |
| fleet-t0-aggregate.py | `scripts\fleet-t0-aggregate.py` | `bb7e67110fd7a68433f189d33ca7ee83ad54f76b1dba574d32b08c9f32fb6034` |
| T0 inventory JSON | `T0-RECEIPTS\fleet-inventory-t0.json` | see INDEX.md |
| PRE-T0 dump | `PRE-T0\` (old raws + `fleet-inventory.sh.bak`) | see INDEX.md |

---

## Mesh probe (pre-T0)

From `ari@192.168.0.138` with mesh key: **100 / 160 / 193 / 114 / 180 / 182** reachable.  
`python3` present on **100**; **NO_PYTHON3** on **160 / 193 / 114**.

---

## T0 — what / fixed / results

**Stamp:** T0 ran **2026-09-15T03:11:29Z → 03:11:42Z** from `ari@192.168.0.138`.

**What:** Fleet census via `scripts/fleet-collect-t0.sh` + `fleet-inventory-v2.sh` + `fleet-t0-aggregate.py`; receipts under `T0-RECEIPTS\`.

**Fixed (collector bugs from owner review):**
- `OS_CODENAME` now resolves to real codename (**trixie** on all 7) — no longer literal `$VERSION_CODENAME`.
- Scoped OCTOPUS service names + `LIBRKKNRT_COUNT` / paths recorded per node.
- Per-node identity: UTC collect time, boot ID, exit codes in JSON rows.
- All 7 rows: `collect_status=OK`.

**Results (verified from T0 JSON / collect.log):**
- **138:** `librknnrt=3`; OCTOPUS services present (`octopus-bridge`, `octopus-control-router`, …).
- **180:** `librknnrt=0`; `octopus-afferent-lab`, `octopus-gateway`, ….
- **182:** `librknnrt=0`; `octopus-fusiond`, `octopus-metacontrol`, ….
- **100 / 160 / 193 / 114:** `librknnrt=0`; `OCTOPUS_SVC_NAMES=NONE`.
- **OS_CODENAME=trixie** on all 7.

### Compact 7-row T0 summary

| HOST | OS_CODENAME | LIBRKKNRT_COUNT | OCTOPUS_SVC_NAMES (trunc) | TEMP_C | MEM_MB |
|------|-------------|-----------------|---------------------------|--------|--------|
| DietPi | trixie | 3 | octopus-bridge.service,octopus-control-router.s… | 37.9 | 3910 |
| octopus-continuity-180 | trixie | 0 | octopus-afferent-lab.service,octopus-gateway.se… | 33.3 | 3910 |
| sensorium-opi5pro | trixie | 0 | octopus-fusiond.service,octopus-metacontrol.ser… | 49.0 | 3910 |
| octopus-compute-100 | trixie | 0 | NONE | 32.4 | 3910 |
| octopus-compute-160 | trixie | 0 | NONE | 27.8 | 3910 |
| octopus-model-plus-193 | trixie | 0 | NONE | 28.7 | 3910 |
| octopus-pro-114 | trixie | 0 | NONE | 27.8 | 3910 |

**Also on 138 (T0 staging):** `/home/ari/hw-exec-t0/`, `/home/ari/fleet-inventory-t0.json`, and `fleet-inventory.sh.pre-t0-20260915` bak.

---

## Plan T1–T6 (successor)

| Task | Intent | Acceptance split |
|------|--------|------------------|
| **T1** | Provision idle boards (100/160/193/114): base runtime (`python3`, `git`, mesh agent needs); mesh round-trip with 138 | **Pilot:** one board heartbeat+receipt. **Fleet:** 4/4 receipts; 7-row matrix retains failed/unknown. |
| **T2** | NPU runtime + measured inference | **Pilot:** one board with valid model output, latency, throughput, NPU execution witness. **Fleet:** 7-row matrix; unmeasured = `NPU_INFERENCE=NOT_MEASURED`. |
| **T3** | `model-server` role on Plus (193) | Verified service **or** honest unbuilt; not implied by label alone. |
| **T4** | Static IPs / stable addressing | **Must include SD↔eMMC MAC strategy** beyond one same-medium reboot (MAC follows boot medium). DHCP reservation plan for media change. Never power off 138. |
| **T5** | Cross-node dispatch from 138 | Job ID through enqueue→dispatch→ACK→persisted result→readback; receipt chain. |
| **T6** | Thermal (+ power if sensor exists) | Before/after temp table under defined load; power `NOT_MEASURED` if no trustworthy sensor. |

**pilot ≠ fleet:** pilot acceptance does not mark the fleet mission complete. Publish a 7-row outcome matrix with not-run / failed / unknown retained in the denominator.

---

## Hard DENYs (LOCKED)

- DENY «۴۲ TOPS آماده و بلااستفاده»
- **42 TOPS** = nominal **7×6** only; **NPU_INFERENCE=NOT_MEASURED**
- DENY claims of “entirely unused” / “100% idle” / “NPU unused (42 TOPS)” without measured utilization
- HOLD **customer_send**
- Never print/send/copy/commit secret values; never power off board **138**; `may_authorize` stays `false`

### Corrected Persian headline (verbatim)

«در دامپ ذخیره‌شده، درایور RKNPU روی هر هفت برد شناسایی شده است. جمع ظرفیت اسمی اعلام‌شدهٔ تراشه‌ها ۴۲ TOPS است. اجرای واقعی مدل، توان پایدار قابل‌استفاده و میزان استفادهٔ فعلی هنوز اندازه‌گیری نشده‌اند. گام بعدی، اجرای مدل با خروجی معتبر و ثبت تأخیر، نرخ پردازش و شاهد اجرای NPU روی هر برد است.»

---

## Remaining

1. T1–T6 execution per corrected DoD (not started in this docs write).
2. Pilot measured inference before fleet expansion.
3. T4 media-change MAC/DHCP strategy design + proof.
4. Keep HOLD customer_send until owner lifts it.

---

## Evidence paths

| kind | path |
|------|------|
| PRE-T0 preserved | `PRE-T0\` (old raws + `fleet-inventory.sh.bak`) |
| T0 receipts | `T0-RECEIPTS\` (`fleet-inventory-t0.json`, `collect.log`, `raw-*.txt`) |
| Scripts | `scripts\` |
| This report | `LANE-REPORT.md` |
| Actions | `ACTIONS-LOG.md` |
| Successor prompt | `NEXT-AGENT-MEGAPROMPT.md` |
| Index + hashes | `INDEX.md` |
| Owner review lock (copy) | `OWNER-REVIEW-LOCK.md` |
| Owner review report (copy) | `OWNER-REVIEW-LANE-REPORT.md` |

---

## Rollback

- PRE-T0 dump preserved; old collector bak kept (`PRE-T0\fleet-inventory.sh.bak`).
- v2 collector installed **alongside** (not destructive overwrite of sole SoT).
- Docs write is additive under this lane directory.


## Honest census (supersedes bad T0-CENSUS-LIVE)

Path: `T0-CENSUS-HONEST/` · JSON sha `65a85c8f38a6fe9764e1b204694e05b7b905f6b9e41194a0a2ffceb58feae241`
- **7 distinct boot_ids** (PASS uniqueness)
- librknnrt at census: **138=3**, others **0** (193 got librknnrt later in T2)
- Idle 100/160/193/114: no OCTOPUS services — nested-ssh census that claimed octopus on 100 is INVALID
- T1 DONE: python3+git on all four idle boards (megaprompt missing-python claim STALE)

## T2 PILOT: **PASS on 193** (pilot ≠ fleet)

- Model yolov5s-640-640.rknn sha `7c6b801d…` from airockchip rknn-toolkit2 RK3588 demo
- librknnrt sha `d31fc19c…`; API 2.3.2; driver 0.9.8
- Measured: mean **19.909 ms**, p50 **20.346**, p95 **20.541**, **50.230 FPS** (warmup 3, loops 20)
- Outputs OK (3 tensors, checksum recorded); NPU Core0 12% after run
- Matrix: 193=PASS; others NOT_RUN — see `T2-PILOT/T2-NPU-INFERENCE-MATRIX.json`
- DENY invent usable-42-TOPS; HOLD customer_send; SEC 69012a24…; no durable-memory live jobs


## DOCS_LAG FIX — T1 PASS (stamped)

T1 provision+heartbeat **PASS** — 4/4 idle boards. Receipts: `T1-RECEIPTS/` (heartbeats for 100/160/193/114). Megaprompt "python3 missing" was STALE.

## WORKER CONNECT — PASS (SEC `0a634c9d…`)

Installed `octopus-worker-heartbeat.timer` on **100/160/193/114 only**.
Roles in `nodes.json` (may_authorize **false** all): 100=retrieve · 160=prep · 193=model-server · 114=eval.
Round-trip: 138 puller fetched `state/heartbeats/worker-{100,160,193,114}.json` (node_id + boot_id).
138 remains sole commander. No install on 180/182. HOLD customer_send.
Receipts: `WORKER-CONNECT/`.

## T2 NPU matrix — expanded

Matrix sha `d13f19285482a2a346b8b26979f2341c8f7a4ccef50c281967e47cabfc469df5` — **6/7 PASS**, **138 NOT_RUN** (organism optional).
DENY usable-42-TOPS / fleet-from-pilot-alone still holds; this is measured inference on six boards, not nominal TOPS claim.

| node | status | mean_ms | fps |
|---|---|---|---|
| 138 | NOT_RUN |  |  |
| 180 | PASS | 19.83 | 50.429 |
| 182 | PASS | 16.815 | 59.472 |
| 100 | PASS | 20.638 | 48.454 |
| 160 | PASS | 20.613 | 48.513 |
| 193 | PASS | 19.909 | 50.23 |
| 114 | PASS | 21.954 | 45.549 |

P0 persistent-fleet discovery already filed under `PERSISTENT-FLEET-EXEC/` / `OCTOPUS-PERSISTENT-FLEET-EXEC-20260915/` (JetStream YES on 182).
