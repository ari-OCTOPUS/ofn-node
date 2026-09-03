# CHIEF-ENGINEER BRIEF — the hidden half of OCTOPUS you cannot see from GitHub

id: `CHIEF-ENGINEER-BRIEF-2026-09-03`
written: 2026-09-03 (AEST) · written-by: the resident ops agent (laptop vantage)
reader: **an external chief-engineer agent with GitHub-only access**
mission split: **you design the blueprint, we implement.** You never merge,
never deploy, never touch flags. Your output = architecture documents as PRs.

Every claim below is labeled:
- `GH` = verifiable in this repo right now (go read it)
- `GH-PR` = verifiable in an open PR branch
- `RELAYED` = exists ONLY outside GitHub (laptop vault / boards / live state); you cannot verify it — treat as owner-relayed ground truth, cite it as such in your docs
- amounts/secrets/tokens are deliberately absent (house policy: financial documents and credentials never enter this public repo)

---

## 0) Your ground rules (non-negotiable, already ratified on main)

1. **GOV-V6**: one valid human approval (Elahe-z or aram-ui) merges a PR. Never the author, never any `[bot]`. Your PRs will sit in queue until a human votes — by design. See `tests/test_gov_v6_gate.py` (the executable spec) and `.github/workflows/independent-review-gate.yml`.
2. `FILES_I_MERGED = none` — always state it.
3. Propose-only: you may not design a change that flips a wire/flag/gate as a side effect (lesson F-15: a "dependency restore" once smuggled a live send path).
4. Negative tests first: a capability without a test that can fail is a claim, not a metric (F-13).
5. The revenue chain ends at `campaign_envelope_ready`; anything that sends to a customer is owner-manual (R3). Design within that.

---

## 1) What OCTOPUS actually is (RELAYED — the part GitHub hides)

**The octopus was born on the laptop, not the boards.** A full organism runs on the owner's laptop: a private vault (git, ~1854 commits, `_ops/` with 387 entries — heart/, neural/, cortex/, a live `ORGANISM-STATE.json` self-advancing at ~60k beats, heart_v2 RUNNING, arbiter GREEN, one live business leg). This laptop organism is the ORIGINAL. The three boards were grafted later and only thinly connected.

### The four physical nodes (all measured live 2026-09-03)

| Node | Hostname (self-declared) | Role | LIVE services that matter to your design |
|---|---|---|---|
| 192.168.0.138 | DietPi | **BUSINESS / feet** (this repo runs here) | ONE process `python3 -m ofn.run` serving ALL four loopback ports 8791-8794 (NOT four services); `octopus-bridge` on 127.0.0.1:8796 (pull-protocol client to a control-plane HTTPS domain); heartbeat/imap/quote/scheduler timers; 6 "mesh" daemons (see MEMBER_UNITS below) |
| 192.168.0.180 | `octopus-continuity-180` | **BRAIN / continuity candidate** | docker+containerd, **chrony (only clock-synced node)**, octopus-gateway, afferent-lab, **llama-lab (local LLM)**, organism-lab dual-bound on 192.168.0.180:8090 + model route 0.0.0.0:8081 + 8780; `/opt/octopus/lab` git repo (no git credentials — 138 pushes for it); `/root/octopus-mesh` |
| 192.168.0.182 | `sensorium-opi5b`→`sensorium-opi5pro` | **SENSORIUM / witness** | **nats-server LIVE, client port 4222 EXPOSED ON LAN**; mosquitto (MQTT 1883); octopus-sensorium / world-model / reflex / fusiond / metacontrol / stability; `/root/octopus-mesh`. In August it served as the independent WITNESS (hash-verification of 138's runs) |
| 192.168.0.191 | DESKTOP-KA9RFN5 | **LAPTOP / controller + vault** | the original organism (above); NO listening service on 8801 (old docs claiming that are dead) |

All four are on one LAN; board MACs share one hardware batch. **The graft is thin:** laptop↔boards communication happens through GitHub and through an ops agent's ssh — there is no direct laptop-organism↔board wire. That gap is your central design problem.

### The three-board contract vs the identity split (GH)
- `ofn/adapters/board_events.py:30` — `BOARDS = frozenset(("board-138","board-180","board-182"))` + a SQL CHECK on source/target + HMAC-SHA256 contract, 5 event types, 5 statuses. **The contract is built; the transport does not exist anywhere.**
- `ofn/adapters/telegram_glass.py:71` — `NODE_IDS = ("BUSINESS","SENSORIUM","LAPTOP")` — only 3 identities; board-180 is NOT in it because it never speaks on the telegram glass. Your TO-BE identity model must reconcile 4 hosts vs 3 identities vs 3 board-slots.

### Live channels & caps (RELAYED + GH for code constants)
- Lead email wire (agencies): armed, cap **10/day, two enforcement layers** (`ofn/agents/outbound_worker.py`: gate deny + worker belt; counter `state/legs/lead-send-counter.json`; fail-closed on corruption).
- Framework caps: **25 sends/day + AUD 50/day** code constants `ofn/config.py` D27 block; kill-switch `OFN_EXTRA_CLOSED_GATES` (9 hard-closed classes incl. live_sms, tender_submit, auto_*).
- Owner telegram pulse/glass: authorized (one channel).
- Bridge → control-plane domain: authorized 2026-08-22 (owner unlock session).
- Revenue truth (counts only, by policy): **5 bank-verified payments business-wide; campaign PAINT-L5-001 = 0.** Manly is the anchor client. Do not design anything that treats revenue as proven for the NEW pipeline.
- Conservation Mode: in open PR-4 (`#131`) — during owner absence or doctor silence, zero sends even within cap. Design must not route around it.

---

## 2) The wiring audit (measured 2026-09-03 — the "nerves without axons")

These are the gaps between BUILT and YIELD. Each is a design target:

| # | Nerve | Built (GH) | Missing (the gap) |
|---|---|---|---|
| W1 | **Model-API path is fugu-shaped** | `ofn/helpers/brainport.py` — docstring admits *"provider swappable (fugu now, deepseek later)"*; `BRAIN_PROVIDER` defaults `fugu`; only fugu/deepseek branches; three API-key families exist in env (sakana/fugu/deepseek-style) | provider abstraction is a stub; **the real caller never consults `ofn/kernel/callbudget.py` (DEFAULT_CAPS)** — token ceilings live in kernel + `docs/octopus-os/06-TOKEN-BUDGETS.yaml` + tests, but bypass the actual call site. Also: shared 3-layer memory lives under a fugu path (`ofn/config.py:133` memory_path → `fugu_core`) — shared organism infrastructure inside one leg's namespace |
| W2 | **Event spine** | board_events contract (above) | zero transport; nothing publishes/subscribes; **NATS is already running on 182 with zero clients in this repo** (RELAYED) — the cheapest possible spine is dark |
| W3 | **Laptop↔board channel** | bridge (138→control-plane, one-way pull) | no laptop-organism↔138 wire; mesh (`octopus-mesh`) exists on all three boards with an `octomesh_send.py` ssh-json protocol (RELAYED — not in this repo) but the repo has no mesh client and the laptop is not a node |
| W4 | **Self-model coverage** | `ofn/adapters/self_model_producer.py` MEMBER_UNITS = 6 always-on services (GH) | timers/oneshots (heartbeat/imap/quote/…) deliberately excluded → the F-12 blind spot (six green while two units failed). The board doctor (open PR `#128`) closes it with 4-state verdicts; your TO-BE should unify self-model + doctor taxonomies |
| W5 | **Memory hierarchy** | local sqlite per node; `memory_chain.py` (hash-chained CRM); fugu_core shared memory on 138 (GH) | no inter-node memory (L2 episodic shared log, L3 semantic) — every node is an island |
| W6 | **Split-brain / clock** | chrony on 180 only (RELAYED) | no quorum, no conflict quarantine, clock drift unmeasured on 138/182 |
| W7 | **Business bot tokens** | loaded in `ofn/config.py:259-262` (ziman/lead/studio/studio_partner) | consumption is partial; the glass uses the owner token only — the per-leg bot surfaces are unwired |

---

## 3) Where everything is (repo map — your reading list)

**Core kernel (38 modules)** `ofn/kernel/`: self_model (5-state SensorStatus — note: doctor's 4-state adds UNPROBED), gates, consent, advisor_gate, callbudget (DEFAULT_CAPS per Rung), token_ceiling (SEND_STATES = forbidden-mention list — the ready≠send wall), events (typed spine, FORBIDDEN_EFFECT_KINDS), envelope, halt, routing (Rung ladder), source_health, probe, quota, release_switch, settlement, edge…

**Agents (18)** `ofn/agents/`: heartbeat (hourly pulse), owner_notify (telegram to owner, fail-soft), outbound_worker (the capped send worker), imap_listener, quote_engine/quote_pipeline/quote_fingerprint, lead_email_writer, mail_credentials, consent_store, memory_chain, h1/h3 harvesters (some marked DEAD-SOURCE), external_witness (GH-PR #130), owner_absence (GH-PR #131), doctor (GH-PR #128).

**Adapters (50+)** `ofn/adapters/`: board_events (contract), telegram_glass (NODE_IDS + read-only command surface), self_model_producer (MEMBER_UNITS), remote_brain, cockpit_v2_read_model, run_store/run_gate, halt_flag, rate_limit + inbound_rate (wired into ofn.run/node), shopify_connector, board-side bits.

**Families**: `ofn/doctor/` (Lane-LB vault doctor: ReceiptLog, DestinyEngine — different from board doctor), `ofn/learning/` (economic learning lane), `octopus_observation/` (12 files), `octopus_survival/` (economy.py rungs A0–A6, telegram_bridge.py file-only, loop.py), `octopus_recovery/` (restore_drill + its CI workflow).

**Governance & docs**: `DECISIONS.md` (D1–D28 ruling chain — read at least D26/D27/D28), `CLAUDE.md`/`AGENTS.md`, `docs/octopus-os/` (00-OWNER-ABSENCE-PLAN, 02-AGENT-CONTRACTS.yaml, 06-TOKEN-BUDGETS.yaml, 07-INCIDENTS.md = the honest ops log, 08-GOV-V6-CANARY GH-PR #129), `docs/runbooks/` (+ FLAG-CLAIMS.json GH-PR #129 — the measured_at registry), `docs/agent-context/prompts/` (season megaprompts incl. MEGAPROMPT-BOARD-CHARTER), `09-LANES/`.

**CI**: 5 workflows (`.github/workflows/`): full-suite (ubuntu+windows, live excluded), independent-review-gate (GOV-V6 + require-fresh-base GH-PR #129), observation-contract, observatory-fixture, restore-drill. Branch protection: 4 required checks, strict=true. Required docs-as-tests exist (`tests/test_gov_v6_gate.py`, `test_incidents_log_policy.py`, `test_d26/d27/d28_*`, docs-contract tests reading the yaml/md).

**Open PRs that are yours to build upon (do not duplicate)**: #128 board doctor · #129 gov-pack (fresh-base/concurrency/FLAG-CLAIMS/canary) · #130 external witness · #131 OWNER_ABSENT+conservation hook · #132 vault witness · #133 inert-flag deletion · #87 receipt-digest (approved, one fresh vote pending) · #115 cockpit seven-card. Queue is ~30 open / 8 non-draft.

---

## 4) What we need from you (deliverables, as PRs to `docs/architecture/`)

1. **AS-IS connection matrix** — every real edge (producer→consumer, protocol, port/path, durability, auth, failure behavior) using §1–§3 evidence; mark each edge `GH` / `GH-PR` / `RELAYED`.
2. **TO-BE nerve plan** — priority-ordered specs for W1..W7 (yield-per-risk), each with: files to touch, the negative tests that must exist BEFORE the positive ones, rollback, and which existing module it must reuse (e.g. W2 must reuse board_events' contract verbatim; W1 must route through callbudget).
3. **Identity & truth model** — reconcile 4 hosts / 3 NODE_IDS / 3 BOARDS; define where canonical state lives per data class and what a node may cache.
4. **Technology admission TDRs** (adopt/trial/defer/reject with rollback) ONLY where a gap demands new tech (e.g. NATS JetStream vs plain NATS core for W2; mesh-ssh vs NATS for W3).
5. **Failure tabletop** — for each nerve: what happens at 1min/1h/24h disconnect; data loss vs duplicate vs lying-green.
6. **90-day sequencing** — what to wire first so each merge produces measurable yield (the owner's metric language: sends-possible → sends-with-receipts → revenue-verified).

**Non-goals:** do not design send-primitives (parked #113 awaits a D-26/D-27 compatibility ruling), governance changes, payment handling, or anything that writes to the private vault.

**Format:** markdown, one doc per deliverable, each PR body carrying a «what enters that isn't in the title» section and `FILES_I_MERGED=none`. Persian or English both fine; decisions cite ruling ids.

---

## 5) One-paragraph summary you can keep in your context

OCTOPUS = a laptop-born organism (private vault, live) with three grafted Orange-Pi organs (business-138 running this repo, brain-180 with docker+llama, sensorium-182 with a live unwired NATS), thin graft (GitHub + one ssh-operating agent), a strict two-human-vote merge law (GOV-V6), a capped-and-ruled outbound economy (10/day lead, 25/$50 framework, conservation mode coming), five bank-verified payments historically but zero on the new campaign, and six open autonomy PRs (doctor/witness/absence/gov/vault-witness/flag-cleanup). The built-but-unwired list is measured and waiting for your blueprint: model-API path (fugu-locked, ceiling-bypassing), event spine (contract w/o transport, dark NATS), laptop↔board channel, self-model blind spots, inter-node memory, split-brain/clock, per-leg bot surfaces. Design the nerves; we will solder them.
