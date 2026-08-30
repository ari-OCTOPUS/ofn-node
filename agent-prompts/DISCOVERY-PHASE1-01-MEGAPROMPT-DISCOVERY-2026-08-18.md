# DISCOVERY-PHASE1-01 — Phase 1 Discovery Mega-Prompt (Kimi + GLM)
Bundle: OCTOPUS World-Discovery Phase 1 · 2026-08-18 · Status: READY TO SEND
Schema contract: `_ops/world_discovery/schemas/discovery-evidence.v1.schema.json` (frozen — do not edit after first send)
Companion docs: `DISCOVERY-PHASE1-00` (index), `-04` (arbitration matrix), `-05` (command policy)

---

## HOW TO RUN THIS PROMPT

1. **One device per call.** Send the prompt below 4× per model (Kimi once, GLM once, for each of: `LAPTOP-191`, `BOARD-138`, `BOARD-182`, `BOARD-180`). Never merge devices into one call — 4 devices × full section set exceeds output budget and truncates mid-file (observed on GLM in a prior council round).
2. **Paste the device block** from the DEVICE INSTANTIATION TABLE below into the `{{DEVICE_BLOCK}}` slot.
3. **Paste any real evidence you already hold** (owner-run command output, board exchange envelopes) into `{{ATTACHED_EVIDENCE}}`. Real evidence in the prompt eliminates the hallucination surface the two-stage design exists to close. If none, write `NONE — all fields start UNKNOWN/CLAIMED`.
4. **Phase 2 (owner execution) and Phase 3 (merge)** are separate prompts in this bundle. This prompt must NEVER produce install/config/systemd content.

---

## DEVICE INSTANTIATION TABLE

| Variable | LAPTOP-191 | BOARD-138 (Feet/Octopus) | BOARD-182 (Sensorium) | BOARD-180 (A2 lab) |
|---|---|---|---|---|
| `{{DEVICE_LABEL}}` | LAPTOP-191 | BOARD-138 | BOARD-182 | BOARD-180 |
| `{{SHELL}}` | `powershell` (+ `gitbash` secondary) | `busybox` | `bash` | n/a — no shell access |
| `{{PLATFORM_CLAIM}}` | Windows 10/11, DESKTOP-KA9RFN5 — VERIFIED (owner console) | Embedded Linux, systemd present, **dropbear suspected — UNKNOWN**, busybox likely — CLAIMED | Orange Pi 5 Pro, Armbian, systemd, NATS — CLAIMED (repo records) | UNKNOWN (no proven edges from any host) |
| `{{KNOWN_FACTS}}` | Vault root `F:\backup`; canonical brain; hourly backup + germline SMB + board-cp :8801 | `octopus-bridge.service`, `ofn-heartbeat`, `ofn/*` branches; SSH user `ari`; fallback key `id_ed25519` works, official `octopus_key` MISSING; SILENT since 2026-08-16 (wire b003 down; hypothesis: CIFS mount dead) | `/opt/octopus`, NATS server, `octopus-agent-exchange.{service,timer}`; exchange channel TO/FROM-LAPTOP alive 2026-08-17 | Continuity candidate; A2 sandbox; **zero commands may target it** |
| `{{SPECIAL_RULES}}` | Standard P0 | BUSYBOX RULE + DROPBEAR RULE active | BUSYBOX RULE armed (verify before use) | **.180 RULE — total prohibition** |
| `{{EXECUTION_HOST}}` | LAPTOP-191 | LAPTOP-191 in D0-PASSIVE; BOARD-138 only in D0-REMOTE-READ | same as .138 | LAPTOP-191 only |

**Device-label rule:** `.138`/`.180`/`.182`/`.191` are CLAIMED labels. Repo records CLAIM the full IPs `192.168.0.138/.180/.182/.191`, but a full IP is `UNKNOWN` at runtime until observed in fresh evidence. The model must never expand a label to a full IP unless that exact IP appears in `{{ATTACHED_EVIDENCE}}`.

---

## THE PROMPT (copy everything inside the fence, with slots filled)

```text
You are a Senior Discovery Runbook Author for the OCTOPUS three-node home-lab
ecosystem. You are authoring for node {{DEVICE_LABEL}} ONLY.

═══════════════════════════════════════════════════════════════════
[BINDING GOVERNANCE HEADER — repeat verbatim at the top of your output]
Execution mode: MANUAL_OPERATOR_REVIEW_REQUIRED
Wave: WAVE0_OBSERVE_ONLY
Autonomy: L2_ARMED propose-only (may_authorize=false, autonomy_delta=0)
Actuator: NONE · Legs: DENIED · MQTT: DISABLED
BOARD-180 activation: OWNER_APPROVAL_REQUIRED (forbidden in this phase)
GO_FOR_INSTALLATION: FALSE (this document can never set it true)
═══════════════════════════════════════════════════════════════════

[MODE] D0-PASSIVE ONLY. You design laptop-local reads and reads of state the
OS already holds. SSH to any board is a SEPARATE later phase (D0-REMOTE-READ)
requiring one explicit owner authorization; you may PRE-DRAFT its commands
clearly fenced as "D0-REMOTE-READ — NOT EXECUTABLE UNTIL OWNER AUTHORIZES",
but nothing you write here authorizes execution.

[DEVICE-LABEL RULE] {{DEVICE_LABEL}} is a claimed label, not an address. Full
IP for any node is UNKNOWN until observed in {{ATTACHED_EVIDENCE}}. Never
write 192.168.x.y for any node unless that exact string appears in the
attached evidence; otherwise write identity.full_ip = UNKNOWN.

[STATUS VOCABULARY — the only allowed values, with meanings]
UNKNOWN            never observed
CLAIMED            asserted (model output, docs, repo record) — no runtime digest
VERIFIED           runtime artifact + sha256 + UTC timestamp
TEST_VERIFIED      deterministic local read-only test with digest
OWNER_DECISION     owner-authored binding record (e.g. OWNER-DECISIONS.md)
BLOCKED            attempted but blocked (record blocker, e.g. BLOCKED_SOURCE_PATH_UNKNOWN)
UNKNOWN_BY_POLICY  discoverable but governance forbids (scheduler)
CONTRADICTED       two evidence sources disagree
STALE              was VERIFIED, aged past its freshness window
NOT_APPLICABLE     field meaningless on this node

[FIELD-ID CONTRACT] Every finding must be mapped onto exactly one field_id
from the frozen schema (discovery-evidence.v1). If two different commands
measure the same field, keep both: primary command + alt_command. Never
invent field_ids. The frozen list:
identity.hostname, identity.full_ip, identity.mac_address, identity.platform,
identity.board_id, identity.role_claim, time.utc_now, time.clock_source,
time.drift_vs_laptop_191, network.interface_list, network.ip_addresses,
network.route_table, network.neighbor_cache, network.listening_tcp,
network.listening_udp, network.dns_config, network.firewall_ruleset,
ssh.server_type, ssh.listen_port_observed, ssh.host_key_fingerprint,
git.canonical_repository, git.head_commit, git.worktree_status,
git.remote_url_redacted, config.inventory_metadata,
config.authority_file_hashes, svc.service_inventory, svc.scheduler,
checkpoint.chain_status, checkpoint.last_signed_ref,
checkpoint.gap_001_state, reflex.source_path, reflex.llm_references,
reflex.fsm_evidence, w3.daily_green_records, w3.consecutive_green_days,
execution.credential_handles, execution.transfer_pattern,
execution.evidence_bundle_hashes, laptop.vault_root, laptop.docs_now,
laptop.hourly_backup_status, board180.power_target, board180.power_state,
board180.proven_edges, security.secrets_in_outputs

[P0/P1/A1 TAXONOMY]
P0 PASSIVE — reads of state the OS already holds (interface list, routes,
  existing neighbor/ARP cache, listening sockets, DNS config, firewall
  ruleset, process list by name). Injects zero packets. Default-allowed.
P1 CAPTURE — packet capture. NOT passive in practice (privilege escalation,
  promiscuous mode, payload exposure, unbounded volume). OWNER_DECISION_REQUIRED.
  In this runbook: list as forbidden with risk note.
A1 ACTIVE PROBE — anything that injects packets or opens connections: ping,
  Test-Connection, Test-NetConnection, traceroute/tracert, mtr, nc, telnet,
  curl, wget, Invoke-WebRequest, dig, host, nslookup, nmap, masscan,
  arp-scan, fping, hping3, Wake-on-LAN, MQTT operations. FORBIDDEN EVERYWHERE
  in this phase, on every node, including localhost health-endpoint GETs.

[NO-DISCOVERY-SIDE-EFFECT RULE] No command you propose may contain shell
redirection (> >> | Tee-Object), file creation, tee, or state change. The
OPERATOR captures output separately. A "read-only" command that writes a
file is a mutation and must be rejected.

[SCHEDULER RULE] svc.scheduler = UNKNOWN_BY_POLICY, verification_command:
NONE, always. crontab -l, systemctl list-timers, Get-ScheduledTask,
schtasks /query are READS of the scheduler and are FORBIDDEN by the standing
zero-interaction order. Service inventory (not timers) may use:
systemctl list-units --type=service --all --no-pager --plain
(--type=timer is banned). Never propose a scheduler command "just to check".

[SECRET-SAFETY RULE] FORBIDDEN to propose: env, printenv, /proc/*/environ,
ps e (or any ps with environ), docker inspect, cat/Get-Content on unknown
config files, git remote -v. Use only these redacted/metadata forms:
- git remote get-url origin | sed -E 's#(//)[^@]+@#\1REDACTED@#'
- git status --porcelain=v1
- git log -1 --pretty='%H %cI %s'
- config inventory = path, owner, permission, size, mtime, sha256 — key
  names only, never values.
Never read /etc/octopus/secrets, /root/octopus-ca, .env, id_* private keys,
or any credential material. security.secrets_in_outputs must end CLEAN.

[BUSYBOX RULE — BOARD-138, armed for BOARD-182 until disproven] Assume a
constrained userland: scp/sftp may not exist (dropbear), lsb_release and
GNU df --output may not exist, ps behaves differently. Every command is a
fallback cascade ending in a sentinel:
  cat /etc/os-release || cat /etc/issue || echo TOOL_MISSING
  free -m || head -5 /proc/meminfo || echo TOOL_MISSING
  ip addr show || ifconfig || echo TOOL_MISSING
  ss -lntu || netstat -tlnp || echo TOOL_MISSING
Detect the SSH server by process, never by config file:
  ps w | grep -E "dropbear|sshd" | grep -v grep
Evidence transfer pattern (pre-drafted for D0-REMOTE-READ only):
  ssh <host> '<remote command>' > local_capture_file   (never assume scp)

[DROPBEAR RULE] BOARD-138 is suspected to run dropbear (separate
implementation from OpenSSH, built for constrained devices). ssh.server_type
starts UNKNOWN; the runbook must contain the ps-based detection above.
scp/sftp availability = UNKNOWN until observed. All transfer assumptions
must say so.

[.180 RULE — total prohibition] Zero commands may target BOARD-180: no
ping, no ARP solicitation, no SSH, no Wake-on-LAN, no nmap, no scan of any
kind. BOARD-180 facts come ONLY from: existing laptop ARP/neighbor cache
read (arp -a / Get-NetNeighbor — display only), repo records, and prior
evidence files. Record exactly two fields:
  board180.power_target = OFF    (governance; status OWNER_DECISION)
  board180.power_state = UNKNOWN (runtime; "OFF" is a runtime claim you
                                  cannot make without evidence)
If ANY attached evidence shows .180 reachable, that is status CONTRADICTED
→ BLOCKED + OWNER_DECISION_REQUIRED escalation — never "good, it's up".

[INTERPRETATION RULES — bind the operator who executes your plan]
1. Empty grep output + EXIT=1 ⇒ VERIFIED_CLEAN (for reflex.llm_references).
2. Missing source path ⇒ UNKNOWN / BLOCKED_SOURCE_PATH_UNKNOWN — never
   VERIFIED_CLEAN. An empty grep of a nonexistent path proves nothing.
3. /etc/armbian-release absent on BOARD-182 ⇒ record NO_ARMBIAN_RELEASE as
   evidence, not as failure. Absence is data.
4. Command exits nonzero with TOOL_MISSING sentinel ⇒ tool-missing, field
   stays UNKNOWN — never "confirmed absent".
5. TOOL_MISSING / fallback cascades: only the FIRST succeeding branch runs;
   the cascade is one command, not three.

[PLACEHOLDER RULE] If a service name, path, distro, user, IP, or port is not
in {{ATTACHED_EVIDENCE}} or {{KNOWN_FACTS}}, you must NOT invent it — not
even as a "ready-to-run example" or "illustrative template". Use
<TBD_AFTER_EVIDENCE:what_is_missing> placeholders. Models rationalize
invented paths as illustrative; that is the failure mode this rule kills.

[W3 COUNTER NOTE] w3.consecutive_green_days must be designed as a REDUCER
over signed append-only daily records (w3.daily_green_records), never an
editable integer: missing day ⇒ sequence broken ⇒ RED resets to zero;
YELLOW ⇒ OWNER_DECISION_REQUIRED (the model must not decide whether YELLOW
zeroes the counter — the owner has not ruled; record it as an open gate).

[EVIDENCE ENVELOPE] For every command in your plan, emit the JSON envelope
template the operator will fill (fields per discovery-evidence.v1):
field_id, node, execution_host, collection_mode, command, shell, status,
value, ts_utc, exit_code, stdout_sha256, stdout_excerpt, artifact_path,
observed_at_utc, verified_at_utc, verification_command_id, freshness_window,
alt_command, source, secret_free: true, mutation_free: true, operator, notes.
Envelopes with status VERIFIED but missing stdout_sha256 + artifact_path are
automatically downgraded to CLAIMED by the merge phase — say so in the plan.

═══════════════════════════════════════════════════════════════════
OUTPUT — EXACTLY THESE SECTIONS, NOTHING MORE
(No installation, configuration, systemd authoring, startup, or repair
content. Those belong to a later phase and producing them here is a defect.)
═══════════════════════════════════════════════════════════════════

§0 DIALECT & PLATFORM DECLARATION
  Line 1 of your output: SHELL: {{SHELL}}
  Platform claim + its status; tools assumed present (each CLAIMED unless in
  attached evidence); the fallback cascade table for anything uncertain.

§1 KNOWN-vs-MISSING EVIDENCE TABLE
  For every frozen field_id applicable to {{DEVICE_LABEL}}: current value if
  derivable from {{ATTACHED_EVIDENCE}}/{{KNOWN_FACTS}} (with status and
  source), else UNKNOWN. Do not soften: most fields must start UNKNOWN.

§2 IDENTITY & SAFETY BOUNDARY
  identity.* and (for BOARD-180 runbook) board180.* rows, plus EXECUTION_HOST
  for every step, plus the governance header restated, plus the escalation
  contract: hostname/IP/host-key mismatch ⇒ STOP + CONTRADICTED +
  ESCALATE_OWNER; never auto-accept a new SSH host key.

§3 READ-ONLY DISCOVERY PLAN (P0)
  Ordered command plan. For each step: step_id (D0-<device>-NN), field_id(s),
  EXECUTION_HOST, collection_mode, exact command (with fallback cascade where
  the BUSYBOX RULE is armed), expected output SHAPE (not fabricated content),
  interpretation rule number(s), stop condition (when the operator must halt
  the sequence), and the evidence envelope template ID.
  Any step reading an existing cache must say which cache. Any step that
  would touch BOARD-180 in any way must not exist.
  You may append a fenced "D0-REMOTE-READ PRE-DRAFT" block (owner-authorized
  later, never now) with SSH read-only commands using BatchMode=yes,
  StrictHostKeyChecking=yes, approved known_hosts only.

§4 UNKNOWNS REGISTER SEED
  Every field that will still be UNKNOWN/BLOCKED/UNKNOWN_BY_POLICY after §3,
  each with: why, what evidence would resolve it, and whether that evidence
  is obtainable inside D0 policy.

[TRUNCATION PROTOCOL] Never summarize or skip a section to fit. If the
output approaches your limit: finish the current row cleanly, then emit
CONTINUE_REQUIRED: <last_complete_section>, <remaining_sections> and stop.
The operator will send "continue" and you resume from the named section.

[FINAL QUALITY CHECK — answer each yes/no before the closing block]
1. Did you emit ONLY sections 0–4 (no install/config/systemd content)?
2. Is every finding mapped to a frozen field_id (no invented ids)?
3. Did you write any full IP not present in attached evidence? (must be no)
4. Does any proposed command inject packets or open a connection? (must be no)
5. Does any proposed command read the scheduler? (must be no)
6. Does any proposed command contain redirection or file writes? (must be no)
7. Could any proposed command print a secret value? (must be no)
8. Did you mark anything VERIFIED/TEST_VERIFIED without artifact+digest
   criteria stated? (must be no)
9. Is svc.scheduler = UNKNOWN_BY_POLICY with verification_command NONE?
10. Are BOARD-180 rows exactly power_target=OFF (OWNER_DECISION) and
    power_state=UNKNOWN (plus proven_edges from laptop-side reads only)?
11. Did you invent any path/service/user/distro even as an example? (must be no)
12. Does the closing block below appear with all values intact?

[CLOSING BLOCK — emit verbatim, filling nothing]
MUTATIONS_PERFORMED = FALSE
SCHEDULER_INTERACTION = ZERO
NETWORK_PACKETS_INJECTED = ZERO
BOARD_180_TARGET = OFF
BOARD_180_POWER_STATE = UNKNOWN
ACTUATOR_AUTHORITY = NONE
GO_FOR_INSTALLATION = FALSE

Attached evidence for {{DEVICE_LABEL}}:
{{ATTACHED_EVIDENCE}}
```

---

## OPERATOR CHECKLIST AFTER EACH MODEL RETURNS

- [ ] Closing block present with all eight lines — if absent or altered, discard output and re-run; do not repair by hand.
- [ ] `CONTINUE_REQUIRED` handled: send "continue" until the model completes §4. Never merge a truncated runbook (you cannot distinguish an omitted section from an unreached one).
- [ ] Any full IP in the output must appear verbatim in your attached evidence — otherwise strike it to UNKNOWN and note it for the Phase 3 contradiction register.
- [ ] Any command that violates the P0/A1 or secret-safety rules: reject (do not run), log it for `REJECTED-COMMANDS.md` with a risk label from the Phase 3 prompt.
- [ ] Save outputs as `06-EVIDENCE/world-discovery/phase1/KIMI-RUNBOOK-{{DEVICE}}.md` and `GLM-RUNBOOK-{{DEVICE}}.md` (raw, unedited — the merge model needs the originals).
