# SYSTEM-MAP

source: live_disk on 180 + ssh 138/182 + GitHub ls-remote 2026-08-27T23:03Z  
node_id writing: 180 · asserted_ip: 192.168.0.180 · claim_type: observation unless marked inference  
GitHub is source of record for ofn-node. Disk is runtime truth. Mesh trees are not git.

## Nodes and roles (runtime, not wish)

| node | IP | hostname | runtime role on disk | GitHub |
|---|---|---|---|---|
| 138 | 192.168.0.138 | DietPi | commander: ofn.service, router, scheduler timer, executor file, verify-dispatcher, cycle-settler | origin ari322/ofn-node HEAD d3fb20c = branch octopus/reconcile-138-20260827 |
| 180 | 192.168.0.180 | octopus-continuity-180 | quality-brain / cognitive core: organism-lab, llama:8081, cognitive-worker timer, mesh no-git | lab HEAD 76db516 **not on GitHub**; ofn-l4 08f9155 no remote |
| 182 | 192.168.0.182 | sensorium-opi5pro | lab-witness worker timer + separate sensorium stack (nats, fusiond, world-model) | mesh no git |
| PC | 192.168.0.191 | UNKNOWN | ICMP up; F:\backup not pulled | n/a |
| PC_worker | UNKNOWN | UNKNOWN | not observed on 180/138/182 | n/a |

Transport roles in signed `octopus-mesh/config/nodes.json` (sha256 prefix `cefbd5cafe689382`, same on 180 and 182): 138 commander-router-ledger-owner, 180 quality-brain, 182 lab-witness.

## Data path observation → effect (intended vs live)

```
sensors/LAN  → 180 organism.db + vault
138 scheduler timer → 180 cognitive_wake → octopus_business_cycle (painting|ziman|studio)
  → artifact + telegram_decision + witness_packet
  → proposal to 138 (ACK inbox only)
  → 138 SHOULD mint witness_request to 182
  → 182 witness worker PASS|DISPUTED|UNRESOLVED
  → 138 Telegram owner decision
  → owner APPROVE exact payload
  → 138 octopus_executor.py one-shot
  → receipt on 138 ledger (180 must not write revenue/SENT/booking)
```

Live break points:

1. Last 180 run `bizop-20260827T111625Z`: three artifacts PROPOSAL_READY, `external_effects=0`, `witness_verdict=PENDING_138_RELAY`, `owner_approval_pending=PENDING_OWNER_TELEGRAM`.
2. `octopus-telegram-bridge.service` on 138 is **inactive**. Running Telegram process is `hypno-fugu-mini.service` (different product).
3. 180 `forbidden_receive_types` includes `witness_request`; 180 cannot mint.
4. Business cycle last run used **shadow fixtures**, `model_receipt=null`.
5. `painting_shadow_only: true` in cognitive_policy.json.
6. ofn-l4 `L4-GATE.json`: listen/run/systemd false, phase shadow_only.

## Cognitive brain (180)

- Worker: `/root/octopus-mesh/bin/octopus_cognitive_worker.py` sha256 `7b6b387f00d8223f…` ExecStart `--once` via timer.
- Library: `octopus_business_cycle.py` sha256 `dc8f58a79bc4d113…`
- Local model: llama-server `0.0.0.0:8081` (pre-existing bind) model `qwen3-0.6b-q4_0.gguf`, `/health` HTTP 200.
- Organism: `octopus-organism-lab.service` → `start-organism.sh`; HTTP 8090 dual-bind LAN+loopback.
- Memory: `organism.db` episodes=2825 inner_speech=768 learned_topics=4 identity_ledger=945; mesh `state/cognition/business_memory/{episodic,semantic,procedural,negative}`.
- Obsidian: `/opt/octopus/lab/vault/board-life-001` generated, untracked. Not the 138 ofn vault.

## Owner gateway (138)

- `python3 -m ofn.run` active.
- Packs on disk: `lead.yaml` `ziman.yaml` `studio.yaml` `hypno.yaml`.
- Mesh bin includes scheduler, router, executor, telegram_bridge, verify_dispatcher.
- Processed mesh 6192; inbox 5; outbox 9.
- GitHub heartbeat unit `ofn-heartbeat.service` pushes to `ofn/heartbeat` (new remote branches fetched this scan).

## Witness (182)

- `octopus_witness_worker.py --once` timer; last rc=0 claimed=1 mixed `generic_rejected` / `completed_acked`.
- Inbox 2200 / outbox 577 — backlog.
- `policy.json` sha256 **differs** from 180/138 (`eee2812d…` vs `e0ffea18…`). `nodes.json` matches.

## Accelerator (laptop)

- ICMP 191 UP. Mirror last_sync_result=blocked. No F:\backup body on 180.

## Three businesses

| lane | GitHub | 138 ofn pack | 180 live |
|---|---|---|---|
| Painting | ari322/Armin = 2 files, 37KiB, not a lead engine | packs/lead.yaml + web/lead.html | shadow fixture leads; QUALITY-DRAFTS-PAINTING.md untracked |
| Ziman | not a dedicated repo | packs/ziman.yaml | fixture products; price_aud null if unknown |
| Studio | notes in ofn-node | packs/studio.yaml + studio.html | fixture album-general-1; restricted assets BLOCKED_HONEST |

## Models

- Local Qwen 0.6B on 180:8081.
- DeepSeek: secret key name `DEEPSEEK_API_KEY` on 180; organism `external_api=DISABLED`; topics LEARNED_FROM_MODEL=4.
- Laptop DeepSeek optional; laptop_required=false.

## Ledgers / memory

- 180 must not write revenue. Authoritative money ledger is 138 (not re-read this session as numbers).
- 180 identity_ledger hash chain in SQLite.
- 182 has ledger-verify timers (sensorium), separate from mesh witness.

## Transport

- octomesh SSH JSON envelopes. 180 send to 138 works (bizop proposal ACK fe60cb26).
- Mesh not a git repo on 180 or 138 or 182. Drift is file-copy not commit.

## Failure points (live)

- Owner Telegram path for OFN decisions inactive.
- Witness mint not executed for bizop packets.
- Ping flood in 180 inbox (~385/400 sampled).
- Disk 90% on 180.
- GitHub private ofn-node reachable only via 138 credentials.
- 180 anatomy commit 76db516 never pushed.
- Parallel stacks: organism-lab, mesh cognitive, ofn-l4 shadow, 182 sensorium+NATS, hypno-fugu.

## Dead / duplicate paths

See DEAD-CODE.md and DUPLICATES.md.
