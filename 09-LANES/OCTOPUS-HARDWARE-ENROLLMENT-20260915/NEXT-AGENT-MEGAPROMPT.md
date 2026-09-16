# MEGAPROMPT — OCTOPUS FLEET: WIRE IT UP AND USE THE WHOLE MACHINE
**Lane:** OCTOPUS-HARDWARE-ENROLLMENT-20260915 → successor lane
**Written:** 2026-09-15 · **For:** the next agent (Grok bots / any agent)
**Repository:** `F:\backup` · **Primary contract:** `F:\backup\AGENTS.md`

> **خلاصهٔ فارسی:** هفت برد Orange Pi الان زندهاند، همه روی eMMC، همه در مِش ثبت شدهاند و
> هیچ کارتی جایی نیست. سه برد سرویسهای اختاپوس را اجرا میکنند؛ **چهار برد کاملاً بیکارند**
> و **NPU هر هفت برد (جمعاً ۴۲ TOPS) دستنخورده است**. کار تو: آن چهار برد را واقعاً وارد
> ارگانیسم کن و از تمام توان سختافزار — بهخصوص NPU — استفاده کن. همهچیز باید با اندازهگیری
> روی برد زنده اثبات شود، نه با استنتاج.

---

## 0. READ FIRST (in this order)

1. `09-LANES/OCTOPUS-HARDWARE-ENROLLMENT-20260915/LANE-REPORT.md` — what this lane did, with rollback
2. `09-LANES/OCTOPUS-HARDWARE-ENROLLMENT-20260915/EVIDENCE.md` — raw command output for every claim below
3. `09-LANES/OCTOPUS-HARDWARE-ENROLLMENT-20260915/FLEET-METADATA.json` — machine-readable fleet state
4. `09-LANES/OCTOPUS-HARDWARE-ENROLLMENT-20260915/ACTIONS-LOG.md` — every change made + how to undo it
5. `07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md` — the vault's routing doc

**Truth hierarchy (AGENTS.md §1):** runtime output > repository file > fresh handoff > old notes.
Chat summaries and agent memory are FORBIDDEN as evidence. If you cannot confirm from level 1 or 2,
write `status: unverified`. **Never write an inference as a fact** — that exact mistake was made in
this lane (see §6, "the hardware-fault error") and cost time.

---

## 1. THE MISSION

The fleet is assembled and reachable but **most of it does nothing**. Your job is to:

**A. Make all seven boards real OCTOPUS nodes** (four of them currently run zero services).
**B. Use the full hardware capacity — above all the seven NPUs, which are 100% idle.**

This is an owner directive: *«بیان تموم ارتباطات لازم اختاپوس رو بسازن و کامل از تموم توان این
سختافزار های جدید استفاده کنن»* — build every OCTOPUS connection needed and use the full
capability of this new hardware.

---

## 2. FLEET STATE — VERIFIED 2026-09-15 (not inferred)

| node | hostname | model | IP | cores | RAM | disk free | temp | boot | role |
|---|---|---|---|---|---|---|---|---|---|
| 138 | DietPi | OPi 5 Pro | .138 | 8 | 3910 MB | 39/58 GB | 38.8 °C | eMMC | commander-router-ledger-owner |
| 180 | octopus-continuity-180 | OPi 5 Pro | .180 | 8 | 3910 MB | 43/58 GB | 32.4 °C | eMMC | quality-brain |
| 182 | sensorium-opi5pro | OPi 5 Pro | .182 | 8 | 3910 MB | 31/58 GB | 48.1 °C | eMMC | lab-witness |
| 100 | octopus-compute-100 | OPi 5 Pro | .100 | 8 | 3910 MB | 48/58 GB | 32.4 °C | eMMC | compute-node |
| 160 | octopus-compute-160 | OPi 5 Pro | .160 | 8 | 3910 MB | 53/58 GB | 27.8 °C | eMMC | compute-node |
| 193 | octopus-model-plus-193 | **OPi 5 Plus** | .193 | 8 | 3910 MB | 54/58 GB | 28.7 °C | eMMC | model-server |
| 114 | octopus-pro-114 | OPi 5 Pro | .114 | 8 | 3910 MB | 54/58 GB | 28.7 °C | eMMC | compute-node |

All: Debian 13 **trixie**, kernel `6.1.115-vendor-rk35xx`, `SD present = 0` on every board.
**Fleet goal achieved: 6 Pro + 1 Plus, all on eMMC, no SD cards anywhere.**

**Aggregate capacity:** 56 CPU cores (4×A76 + 4×A55 per board) · 27.4 GB RAM · 322 GB free disk ·
7× Mali-G610 MP4 GPU · **7× RK3588 NPU @ 6 TOPS = 42 TOPS, entirely unused.**

---

## 3. ACCESS

- **Key auth only. No passwords are stored anywhere, and none are written in this repo.**
- From your machine: `ssh board138`. From 138 the mesh key reaches **all seven**:
  ```bash
  ssh -i ~/.ssh/octopus_mesh_ed25519 root@192.168.0.<ip>
  ```
- **Trap:** run as the user that owns the key. `config/nodes.json`'s `identity` field is the key path
  *on that node* (`/root/.ssh/...`), which user `ari` cannot read. From 138 always use
  `~/.ssh/octopus_mesh_ed25519`.
- **Registry:** `/home/ari/octopus-mesh/config/nodes.json` on 138 (git repo, last commit `2d1793bda`).
  Consumed by `octomesh_*.py`. `may_authorize` is `false` on every node — **leave it that way**.
- **Never remove a node entry** — `octomesh_agent_bridge transmit()` raises KeyError. Use `retired: true`.

---

## 4. WHAT IS ALREADY BUILT

- All 7 nodes enrolled, roles assigned, reachability verified **7/7** from 138.
- Mesh SSH key on every node; CRLF stripped from every `authorized_keys`.
- Every board boots from eMMC; zero SD cards in the fleet.
- 182's OOM crash-loop **fixed and measured** (2 GB swapfile; `NRestarts` was 98, now 0; the sensorium
  reaches `readiness=READY bus=CONNECTED`).
- 138 / 180 / 182 run the OCTOPUS service stack. 180 additionally serves **llama.cpp on :8081**.
- Tooling already staged on 138: `~/bootmedia/flash.py`, `write-pro-card.sh`, `enroll-board.sh`,
  `fleet-inventory.sh`, `rockusb-probe.sh` (read-only MASKROM probe via `rkdeveloptool`).

## 5. WHAT IS **NOT** BUILT (this is your work)

1. **100 / 160 / 193 / 114 run ZERO OCTOPUS services** — four idle 8-core boards, ~13.4 GB free RAM.
2. **The NPU on all 7 boards is unused (42 TOPS).**
3. The Plus (193) is labelled `model-server` but nothing runs on it.
4. No cross-node workload dispatch; the registry is a contact list, not a scheduler.
5. No static IPs — and the **MAC follows the boot medium**, so DHCP leases can shift and silently
   break the registry.
6. `python3` is missing on **160 / 193 / 114**; `docker` exists only on 180.

---

## 6. TRAPS — learned the hard way today. Do not repeat them.

| Trap | What actually happens | Do this |
|---|---|---|
| **The hardware-fault error** | This lane concluded "eMMC is dead" from "the device tree is byte-identical to a working board". Wrong: the eMMC was fine, the *SD boot path* was the problem. | Vary the **boot medium** before concluding hardware. Never infer a physical fault from software sameness. |
| **MAC follows the boot medium** | 193 and 114 each showed a *different* MAC after booting from eMMC vs SD. | Never key anything off the MAC as a stable board identity. |
| **`hostnamectl` fails over SSH** | dbus is broken → `Failed to connect to system scope bus`. | Write `/etc/hostname` directly + `hostname <name>`. |
| **No SFTP on DietPi** | `scp` dies with `/usr/lib/sftp-server: No such file or directory`. | Stream: `ssh host 'cat > /path' < localfile`. |
| **`xz` / `python3` often absent** | A flash **silently wrote 0 bytes** because `xz` was missing. | Check first; `apt-get install -y xz-utils`, or use python3's `lzma`. Always assert the written byte count. |
| **"Never hot-plug SD"** | Overstated. 138 and the Plus hot-plugged cleanly. 182's crashes were a **faulty card** wedging the controller. | Power off when you can — but never power off **138**. |
| **`ssh` eats stdin** | A python script that shells out to ssh consumed its own heredoc, producing silent empty results. | `stdin=subprocess.DEVNULL`. |
| **Quoting in `ssh host '...'`** | A single quote inside terminates the remote command. | Use `ssh host "…"` with `<<'EOF'` inside, or push the script as a file. |
| **CRLF** | Corrupts `authorized_keys` and scripts. | `sed -i 's/\r$//'`. |
| **182 is memory-tight** | 3.9 GB RAM, warmest board (48 °C). It was OOM-looping before the swapfile. | Do not pile heavy services on 182 without checking headroom. |

---

## 7. BUILD TASKS — concrete, ordered, each with an acceptance test

### T1 — Provision the four idle boards (unblocks everything else)
On **100, 160, 193, 114**: install the base runtime (`python3`, `git`, and whatever the mesh agent needs).
Confirm each board can run a trivial mesh round-trip with 138.
**Accept:** all four report a heartbeat/status back to 138; a receipt exists per board.

### T2 — Bring the NPU online (highest value, biggest untapped capacity)
The NPU is **already exposed** as a DRM accel device:
```
DRIVER=RKNPU   OF_FULLNAME=/npu@fdab0000   compatible=rockchip,rk3588-rknpu
```
There is **no** `/dev/rknpu*` node and **`librknnrt` is not installed**. Install the RKNN runtime
(`librknnrt` / `rknn-toolkit-lite2`, matching the `6.1.115-vendor-rk35xx` kernel) and prove it with a
real measured benchmark — a model actually executed on the NPU, with throughput and latency recorded.
**Accept:** a receipt showing a real inference ran on the NPU **on each of the boards you enable**, with
measured numbers. If a board cannot run it, record that honestly as `status: unverified` rather than
claiming the fleet can.

### T3 — Implement the `model-server` role on the Plus (193)
193 is the only **RK3588** (not RK3588S) and has the most free disk. It is labelled `model-server`
but runs nothing. Decide with the owner whether it hosts a model server (like 180's llama.cpp) or an
NPU-accelerated inference endpoint, then build and verify it.

### T4 — Give the fleet static IPs
The MAC changes with the boot medium, so DHCP is a latent failure mode that would silently break the
registry. Set static addresses (or DHCP reservations) and update `nodes.json` to match.
**Accept:** a reboot of at least one board followed by a successful mesh round-trip proves the address
is stable.

### T5 — Build cross-node dispatch (the actual "connections")
The registry is a contact list. Turn it into a router: let 138 hand a job to a specific node by role
and collect a receipt. Start with the compute-nodes, then include the NPU workers from T2.

### T6 — Thermal + power watch
182 sits at 48 °C and is the memory-tightest board. Before loading the fleet, add a measured
temperature/load baseline per board so regressions are detectable.
**Accept:** a before/after table of temp per node under a defined load.

---

## 8. GOVERNANCE — non-negotiable (from `F:\backup\AGENTS.md`)

- `GOV_VERSION=V8`, `LADDER=L2`. Write both at the top of your lane report.
- **Red boundaries:** never print/send/copy/commit a secret value (key **names** only); never delete or
  rewrite a receipt-chain entry; never declare PASS or LIVE without a same-scope receipt.
- **Never power off board 138** — it is the executor; the organism dies with it.
- **`may_authorize` stays `false` on every node.** Do not raise your own authority, gates or quotas
  (AGENTS.md §5). Self-elevation is an incident.
- **Lane discipline:** one lane, one worktree, declared at session start. End with
  `09-LANES/<LANE>/LANE-REPORT.md` containing what was done, what remains, what failed, evidence
  paths and rollback steps. **No report, no completion.**
- Owner decisions are listed as `status: open, requires: owner_decision` — never decided on the
  owner's behalf.
- Internal, reversible, non-TCB work: **PROCEED** (GOV-FREEDOM-V2). Ask only at the red boundaries.

## 9. DEFINITION OF DONE

1. Four previously-idle boards run a verified OCTOPUS service and round-trip with 138.
2. NPU inference is **measured** on at least one board (ideally all seven), with real numbers.
3. `model-server` on 193 either runs something verified, or is honestly recorded as unbuilt.
4. Static addressing proven stable across a reboot.
5. `LANE-REPORT.md` committed, with evidence paths and rollback for every change.
6. **Zero** unverified claims. Where something failed, say so with the output.

## 10. MACHINE-READABLE STATE

Everything above, plus per-board inventory, is in
`09-LANES/OCTOPUS-HARDWARE-ENROLLMENT-20260915/FLEET-METADATA.json`.
On the live board 138: `/home/ari/fleet-inventory.json`, `/home/ari/fleet-capabilities.json`,
`/home/ari/fleet-capabilities2.json`.
