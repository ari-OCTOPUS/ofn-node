# OCTOPUS ECOSYSTEM — ARCHITECTURE REFERENCE (board-resident, for any agent)
Maintained by: Sensorium board agent · Snapshot basis: 2026-08-17 · Living doc.
Deep details: REFERENCE/ARCHITECTURE-BIBLE.md (laptop canonical knowledge export,
26 sections, epistemic tags FACT/DERIVED/ASSUMPTION). This file = cross-node map.

## 1. THREE NODES (one owner: Armin; all agents ZCode/GLM-5.3)

| Node | IP | Role | Status 2026-08-17 |
|---|---|---|---|
| Laptop (Windows, user Armin) | 192.168.0.191 | BRAIN: canonical vault `F:\backup` (git repo), organism `_ops`, Doctor, Architect, Council, TCB ceremonies, board-cp API | alive (organism auto-truth updating; hourly vault backup running, pushes failing) |
| OCTOPUS legs board | LAN (IP TBD) | BODY: legs NBB-V5 (leg-code authority), `octopus-bridge.service`, `ofn-heartbeat` (~10 min), `ofn/*` git branches over germline | SILENT since wire b003 2026-08-16 17:35+10 / heartbeat 2026-08-17 08:47+10 (stale CIFS hypothesis; revive recipe: REFERENCE/FOR-BOARD-ACTION-NEEDED.md; 3 unacked cmds 01a0096d 01a009d1 01a00b85) |
| Sensorium Pi (this board) | 192.168.0.182 | OBSERVATORY: sensor telemetry, evidence store, WAVE0_OBSERVE_ONLY | alive (8 octopus services + NATS; my agent pack /opt/octopus-agent) |

## 2. LAPTOP BRAIN — internals
- **F:\backup** = canonical vault AND live tree (git; agent protocol: CLAUDE.md +
  agent-prompts/_PROJECT_INSTRUCTIONS.md — Inbox-first, never delete, `.agentignore`
  = .git/_code/_Archive/_Duplicates/secrets-export/*.env; >5 files ⇒ `agent-checkpoint:`
  commit; session start = 01-Dashboard/HANDOFF.md; WORKLOCK lanes vs collisions).
- **Two trees (BIBLE §1):** boss = organism `_ops` (cortex/heart/budget/epistemics/
  organism.py/innervation pacemaker) governs "legs"; leg = `4d_system` «ایده‌یاب»
  (SOG math core + Brain-OS cognition testbed; agents W0-W3; anchors immutable,
  e.g. ½·log(σ_z²/S)=0.135073).
- **Organism runtime:** daemon.py tick 30 s, `_MODE_CYCLE` (explore/real/synthesize/
  evolve/conclude/guard), guardrails + invariant anchors (err<1e-4 → safe halt),
  self_code proposals (AST-only, owner-gated), ~40 wired loops (doctor, telegram,
  unified, lead, neural, school, legs tick, actuator-fenced, mining, ziman, …).
  Ports: 8771 organism, 8774 miniapp gateway (loopback), 8801 board-cp TLS
  (LAN; Bearer; cert pin A9:F7:30:…:44:A7; GET /api/board-cp/pull, POST .../ack).
- **TCB (Trusted Code Base):** critical files digest-verified; patches only via
  owner ceremony apply→regen manifest→sign→restart; guard self-halts on mismatch
  (2026-08-17 15:39 halt during C-026/DARE window — root-caused by laptop agent;
  pending patches: EQUIP-G2, JOB-RESEARCH).
- **E:\germline** = OFN sync share (SMB, Armin-only): octopus.git (ofn/* branches:
  wire, heartbeat, board-snapshot, bridge), message files (FOR-BOARD-*, ANSWERS,
  WIRE.md), hourly bundles. Direction rule: board→windows push only; windows never
  overwrites board; leg code on board wins (NBB-V5).
- **Governance layers:** 01-TRUTH (runtime-written CURRENT-TRUTH + verified mirrors +
  CONTRADICTIONS C-001…C-034, only owner resolves) · 03-GATES (secret_rotation/
  partner_precondition/miner_isolation blocked-lvl-B; board_cp OPENED 08-16) ·
  DECISIONS D-01…D-37 + O-01…O-04 (append-only, architect canonical) ·
  05-Agents/AGENT_REGISTRY (phase-4 propose-only agents) · COUNCIL_REPORTS ·
  06-EVIDENCE · 4D-Vault/4d_system · OCTOPUS-DOCTOR (فارسی: قوانین/معادلات/
  اندام‌ها/اسکن‌ها/نسخه‌ها).

## 3. LEGS BOARD — protocol
- WIRE.md (branch ofn/wire): append-only two-agent messaging, ids w### (windows) /
  b### (board), no secrets, business verdicts → BACKLOG-FOR-OWNER.
- bridge pulls commands from :8801 (first command must be `ask`|`status`, doc 46
  phase 3); acks each message_id honestly (succeeded|unknown_outcome).
- heartbeat branch push ~10 min; board registry exposes owner-console ops
  (ofn.snapshot.read, ofn.status.read, ofn.status.owner, ofn.task.start(owner_required)).

## 4. SENSORIUM (this board) — internals
- Runtime: /opt/octopus (release tree `current` w/ SHA256SUMS; venv; releases/*),
  8 systemd services (sensorium, fusiond, metacontrol, reflex, skill-tracker,
  stability :9101, world-model) + nats-server (JetStream; 4222 LAN / 8222 mon).
  State: /var/lib/octopus (append-only evidence + hash-chained ledgers +
  snapshots + inbound). Authority: WAVE0_OBSERVE_ONLY / actuator NONE / legs
  DENIED / mqtt DISABLED — changes only via owner-signed bundles
  (TO-LAPTOP unsigned export → Windows sign (root-v2 fp sha256:a20d836d…) →
  SIGNED-*-BUNDLE drop → path-unit verify/apply).
- Evidence store (validated 2026-08-17, 94.1% write reduction): observations.jsonl
  + 6 JSON indexes + pending.jsonl journal (crash-safe), flush every 200 obs/300 s.
- My agent pack /opt/octopus-agent: AGENT-MISSION, OWNER-DECISIONS D1–D12,
  phases P0–P7 + ROADMAP (Track A scientist / B unification I1–I5 / X exchange),
  hash-chained CHANGELOG.jsonl, RECEIPTS, this REFERENCE library, MEMORY.md.
- Exchange channel (D12): TO-LAPTOP/exchange + FROM-LAPTOP/exchange, types
  EVIDENCE/PROPOSAL/REPORT/QUERY/ACK, envelope {msg_id,run_id,from,to,type,ts_utc,
  boot_id,evidence_refs,payload_hash,prev_msg_hash,may_authorize:false}, invalid→
  quarantine, command/credential/authority payloads→BLOCKED_NEEDS_OWNER; timer 5 min.

## 5. CROSS-NODE RULES (learned 2026-08-17, hard-won)
1. Any cross-node claim ships WITH a one-line verify command (else it is level C).
2. Every quoted number carries timestamp + hostname (two different "beat" counters
   exist: organism beat ≈39816 on laptop vs heartbeat-branch beat ≈1681 on legs board).
3. Frames differ: laptop agent sees only F:\backup+germline; legs board sees wire;
   Sensorium sees /opt/octopus. None may claim the others' state without verification.
4. Secrets never cross nodes (bearer key hand-off pattern: share → receiver stores →
   sender deletes; *.env/secrets-export/keys unreadable everywhere).

## 6. GLOSSARY (quick)
SOG=Self-Other Gradient math core · DARE=matrix eq (closed-form root, Kalman S) ·
TCB=trusted code base + ceremony · OFN=octopus field network (germline sync family) ·
NBB-CP/V5=legs control-plane, version 5 (board authority) · germline=SMB sync share
+ git · wire=append-only agent messaging · board-cp=:8801 cmd API · beat=loop
counter (context-dependent!) · coherence=organism health metric · WAVE0=observe-only
era (Sensorium) · D-xx=owner decisions (vault) · D1–D12=my board authorizations ·
C-xxx=contradictions ledger · GAP-001/002=Sensorium audit gaps · CHG-xxx=change ids ·
levels A/B/C=direct-run/other-agent/unverifiable evidence.

## 7. VERIFY COMMANDS (per node, from anywhere with creds)
- Laptop→Sensorium: `ssh root@192.168.0.182 "ls /var/lib/octopus/inbound/TO-LAPTOP/exchange/; tail -4 /opt/octopus-agent/exchange/exchange-ledger.jsonl"`
- Sensorium→laptop vault: SMB //192.168.0.191/octopus-main (F:\backup) or /germline
- Legs board: via germline WIRE.md or :8801 pull (Bearer) — TBD after revival
