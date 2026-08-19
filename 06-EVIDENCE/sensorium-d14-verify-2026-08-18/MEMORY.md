# MEMORY — Sensorium board agent persistent memory (owner: Armin)
Rewritten 2026-08-17T12:50Z after full F:\backup read. Sources: primary files only.

## ECOSYSTEM — THREE NODES, ONE OWNER (all ZCode/GLM-5.3)
1. **Laptop .191 (brain/vault)** — F:\backup = canonical vault (owner vote 2026-08-15)
   AND a live git repo. Organism ALIVE (auto-block 12:29Z: coherence 0.872, beat
   39816, halted False, 11 members, HEAD 8df4bf5; ports 8771/8774 loopback).
   E:\germline = OFN sync share. board-cp TLS :8801. hourly vault backup alive,
   pushes failing (err empty, fallback throttled). 
2. **Legs board (body)** — NBB-V5, octopus-bridge.service, ofn-heartbeat, ofn/*
   git branches, WIRE.md protocol (w…=windows, b…=board). SILENT: wire b003
   2026-08-16 17:35+10, heartbeat 2026-08-17 08:47+10. Revive recipe:
   germline:FOR-BOARD-ACTION-NEEDED.md. 3 unacked cmds: 01a0096d 01a009d1 01a00b85
   (ack via POST :8801/api/board-cp/ack). Its beat counter (1681) ≠ organism beat.
3. **Sensorium Pi .182 (me)** — observability node; my 2026-08-17 work all receipted.

## VAULT GOVERNANCE (F:\backup — I MUST FOLLOW WHEN EDITING)
- Constitution: agent-prompts/_PROJECT_INSTRUCTIONS.md (read-only for agents).
  Rules: never delete (move to _Archive/_Duplicates) · never touch .git/_code/
  secrets · *.env and secrets-export/ unreadable · Inbox-first (new notes →
  00 - Inbox) · >5 files ⇒ commit "agent-checkpoint:" · blocked rule ⇒ stop,
  ask in 00 - Inbox/AGENT_QUESTIONS.md
- CLAUDE.md: session start = 01 - Dashboard/HANDOFF.md + 00 - Inbox; session end
  = refresh HANDOFF (wikilinks only, no content copies, no secrets)
- WORKLOCK section in HANDOFF: parallel-lane coordination; always-reserved:
  _ops/tests/run_all.py, _ops/wiring.py, telegram_center/center.py,
  orphan_scan.py. Safe parallel: new docs in 06/07/00.
- TCB ceremony (apply→regen manifest→sign→restart) required for organism code
  patches; pending patches in Inbox: PATCH-EQUIP-G2-*, PATCH-JOB-RESEARCH-*;
  laptop agent root-caused a TCB-guard self-halt (digest mismatch during
  C-026/DARE window) — verify current daemon state before assuming.
- Truth layer: OCTOPUS/CURRENT-TRUTH.md = runtime-written canonical (don't edit
  auto-block); 01-TRUTH/* = verified mirrors + CONTRADICTIONS (C-001…C-034; only
  owner resolves) + GATES (secret_rotation/partner_precondition/miner_isolation
  blocked-level-B, origin outside vault; board_cp gate OPENED by owner 08-16).
- Decisions: architect/01-Project/DECISIONS.md D-01…D-37 + O-01…O-04 (append-only).
  Owner interview votes 2026-08-16: channel=both · bridge=fully-on ·
  merge=auto+report · scope=full.
- Agents: 05 - Agents/AGENT_REGISTRY.md (phase-4 agents, propose-only until
  Security Gate CRITICALs closed). Three node-agents NOT yet registered →
  proposed in my alignment note §5.

## MY ALIGNMENT EDITS IN F:\backup (2026-08-17, 3 files, no commit needed <5)
1. NEW  "00 - Inbox/2026-08-17 SENSORIUM-NODE-ALIGNMENT.md" (topology, my day's
   receipts + one-line verify commands, C-034 ref, security hygiene, 5 proposals)
2. APPEND C-034 (resolved, owner-verified) to 01-TRUTH/CONTRADICTIONS.md
3. PIN in 01 - Dashboard/HANDOFF.md وضعِ لحظه‌ای (link to 1+2)
Laptop agent may commit these per its protocol.

## STANDING SECURITY NOTES
- SMB creds from owner in chat → /root/.smbcred (600) on .182; advise rotation
- ofn-bearer.key / secrets-export/ / *.env NEVER read (either side)
- my mounts: .182←.191 germline=RO, octopus-main=RW (alignment edits only)

## OPEN ITEMS
- [ ] Owner/architect ratify: register 3 node agents; add my note to
      NEXT-AGENT-HANDOFF reading list; archive the Inbox note properly
- [ ] Revive legs board (+3 acks) — recipe ready
- [x] ARCHITECTURE-REFERENCE built (OCTOPUS-ARCHITECTURE-REFERENCE.md + REFERENCE/ library, 15 docs, MANIFEST hashes) — always board-resident for cross-agent work
- [ ] Laptop hourly push-fail investigation
- [ ] Board queue: I2 core/evidence · next signed checkpoint: GAP-001 closure
      (POWER_LOSS_UNTESTED rider) + CHG-019 certificate (drafts ready)
- [ ] HANDOFF.md is 875 lines vs its own <200 rule — needs an archive overflow
      pass by the vault agent (observation only, I didn't touch)

### 2026-08-18 (~01:35+10) — laptop restore round-2: VERIFIED
- Laptop agent report fully verified from .182 (level A): equip tip d10887c exact match on octopus.git; hourly-latest.bundle byte-exact (1,339,973,214 B, 01:03:22+10); hourly row "01:22:11 OK bundle-fallback" confirms the 74-min in-progress run; gitwrite.lock released; GITWRITE-FAILED.flag deliberately retained (correct — anti-fake-green).
- My diagnostic: vault.git CLEAN (213 refs, zero bad refs) → scheduled `--all` push failure is NOT remote corruption. Suspects sent to laptop agent: (1) --quiet hides real error — remove it first; (2) task-account ACL/credentials on E:\germline; (3) --all batch aborts on one rejected ref (manual single-branch push succeeded). Plus lock-vs-flag coupling (74min lock vs 80s timeout).
- RESTORE_DONE = AUTO hourly push green (task account, --all, no fallback) → then flag removal. Agreed both sides.
- Open: cmd 01a00d3d (4th) still dispatched — owner decision; TCB ceremony 2 patches (EQUIP-G2, JOB-RESEARCH) pending; 3 acks unknown_outcome done by laptop agent 23:57+10 (level B).
- SMB write gotcha on .182: fresh file may ls as 0 bytes via attribute cache — verify size after sleep, or cp from local + sync.

### 2026-08-18 (~01:55+10) — D13 autonomy mandate deployed
- D13 (owner blanket): boards (.138/.182) = always-on backbone; laptop intermittent; NO flow may require laptop online; queue on boards, flush on return.
- .182: octopus-agent-sentinel (5min timer) — laptop off/on transitions, legs SSH health, auto gap-note in vault Inbox on laptop return, CIFS self-heal. State: /var/lib/octopus-agent/sentinel/. Hardened unit; oneshot semantics: "inactive" after success is normal.
- .138: ofn-bridge-watchdog (2min, root) — restart octopus-bridge if dead; log /var/log/ofn-bridge-watchdog.log. Deployed via SSH key; sudo for install only.
- P-ACK-1 (auto-ack expired>12h → unknown_outcome) NOT deployed: needs laptop read API or bridge code change (trust boundary). Proposal in D13 doctrine note.
- Stale failed units on .182 (apply-registry/checkpoint start-limit-hit, 11:33Z era) reset-failed — final applies had succeeded.
- Pending owner: cmd 01a00d3d (dispatched), TCB ceremony 2 patches, password rotation (SMB + .138 sudo).

### 2026-08-18 (~02:05+10) — D14 verification doctrine adopted
- Owner's three-megaprompt design (Verifier Pattern / Evidence Envelope / structural gates) is now ecosystem doctrine. Activation order: laptop → sensorium → legs. My charter v2 STAGED in PENDING-CHARTER-V2.md (gate: laptop envelope verified).
- Exchange envelope v1.1 live: claim/raw_evidence/reproduction/uncertainty/escalation/initiating_owner (validator X12, tests 17/17, backward compatible). Every EVIDENCE message carries them + readiness gauge (NATS + sensorium independent + boot-report gates; ACTIVE ≠ VERIFIED, never conflated).
- P-ACK-1 auto-ack WITHDRAWN (I proposed it; doctrine says only owner closes unknown_outcome — detection-only now). 01a00d3d stays owner-pending.
- pytest lives at /opt/octopus/venv/bin/pytest (system python3 has none).

### 2026-08-18 (~02:25+10) — Charter v2 ACTIVE (owner-delivered, D15)
- New node: board .180 (continuity.* NATS). Rules: sensorium.* prefix, no direct exchange with .180 (laptop mirror only). Audit: zero refs, no NATS interconnect — independent.
- NATS subjects currently octopus.* (disjoint from continuity.*); sensorium.* rename queued for next signed TCB ceremony (code + nats-server.conf are TCB-protected).
- senses_gauge() live in every EVIDENCE packet: board_id + registry v6 + quarantine_status. First reading: 10 health records, 0 quarantined, OCT-SENSE-099 degraded (not Wave-0-enabled; surfaced only).
- CURRENT-PHASE.yaml is owner-gated (never agent-edited, per its own header) — mission doc carries the charter instead.
