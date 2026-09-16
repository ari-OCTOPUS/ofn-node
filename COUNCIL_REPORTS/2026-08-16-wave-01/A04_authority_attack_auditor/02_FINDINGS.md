# A04 — FINDINGS (Authority & Attack-Surface Audit)

Agent: A04_authority_attack_auditor · Mode: READ_ONLY · Date: 2026-08-16
Every finding cites evidence rows in `03_EVIDENCE.jsonl` (E-###).

## Finding index

| ID | Short claim | Status | Tier | Sev | Contradiction |
|----|-------------|--------|------|-----|---------------|
| F-001 | Raw shell capability exists, armed, reachable from Telegram `/sh` | VERIFIED_CODE_ONLY (+T0 armed, never executed) | T2+T0 | HIGH | none |
| F-002 | Shell deny-list is regex-on-command; `python -c`, `pip`, arbitrary file writes not covered | VERIFIED_CODE_ONLY | T2 | HIGH | none |
| F-003 | octopus_v3 P0ExecutionGate (kill/taint/budget/lease/INTENT-ledger choke) is WIRED=False — not in live path | VERIFIED_CODE_ONLY (dead) | T2 | HIGH | C-3 |
| F-004 | containment/ G8 package (risk_gate, approval_binder, agent_circuit, audit_chain, kill_coordinator) has no live consumers | DOCUMENTED_NOT_IMPLEMENTED (as enforcement) | T2 | MEDIUM | C-3 |
| F-005 | PolicyGate checks approval_id for presence only, not validity | VERIFIED_CODE_ONLY | T2 | MEDIUM | none |
| F-006 | PolicyGate live coverage is narrow: protective_halt + collaborator draft path only | VERIFIED_CODE_ONLY | T2 | HIGH | C-3 |
| F-007 | code_autonomy: 8 gates + resolve/containment target guard; currently killed by STOP file; allow-roots include `_ops/state` | VERIFIED_CODE_ONLY (+T0 kill file) | T2+T0 | MEDIUM | none |
| F-008 | coding_sandbox command_runner: prefix allowlist + shell=True; `python -c <code>` passes; no OS-level jail | VERIFIED_CODE_ONLY | T2 | MEDIUM | none |
| F-009 | web_research fetches search-result URLs with no allowlist/SSRF/size checks; fetched content enters improve() context unfenced | VERIFIED_CODE_ONLY (flag default off) | T2 | MEDIUM | C-5 |
| F-010 | Vault RAG is ON in live .env; evidence snippets reach brain context with no untrusted labelling | VERIFIED_LIVE (config) | T0+T2 | MEDIUM | none |
| F-011 | Telegram owner auth = deterministic `from.id == TELEGRAM_OWNER_CHAT_ID` env; fail-closed; non-owners silently dropped | VERIFIED_CODE_ONLY | T2 | INFO | none |
| F-012 | MiniApp gateway (127.0.0.1:8774) initData HMAC + owner id; `/api/actions` can execute OpsActionEngine DB/flag writes (owner-gated) | VERIFIED_CODE_ONLY | T2 | LOW | none |
| F-013 | cortex HTTP (127.0.0.1:8772) POST /ask guarded by httpauth CSRF/Origin, default-on, fail-closed | VERIFIED_CODE_ONLY | T2 | LOW | none |
| F-014 | `.env` gitignored & untracked; plaintext backup `.env.bak-20260810` sits at repo root | VERIFIED_LIVE (observation) | T0 | MEDIUM | none |
| F-015 | All 15 activation flags armed simultaneously (incl. RAW-SHELL, CODE-AUTONOMY, SELF-IMPROVE-AUTO, REPLICATION, GO-LIVE) | VERIFIED_LIVE | T0 | HIGH | none |
| F-016 | Effect legs are propose/intent-only or default-off: mining=stop-intent file only; outbound SMTP behind OCTOPUS_WIRE_LEAD_OUTBOUND+consent+staleness; PocketSmith/PS-writeback default-off | VERIFIED_CODE_ONLY (+.env flags off) | T2+T0 | INFO | supports "propose-only" claim |
| F-017 | Genome ledger live, append-only, hash-chained; **no bitemporal fields** (0 valid_from/valid_to) | VERIFIED_LIVE / partially CONTRADICTED | T0 | INFO | C-4 |
| F-018 | identity_health computed live (0.542 in ORGANISM-STATE.json, beat 38516) | VERIFIED_LIVE | T0 | INFO | none |
| F-019 | Recovery/fallback paths degrade authority (fugu→glm→local→None); auto-freeze on canary red; no authority-expanding recovery found | VERIFIED_CODE_ONLY | T2 | INFO | none |
| F-020 | output_guard enforces inert-artifact policy (autorun names, executable exts, shell patterns, TCB prefixes) | VERIFIED_CODE_ONLY | T2 | INFO | none |
| F-021 | Chat-sourced owner authorization is recorded, never executed ("chat ≠ Ed25519 signature") | VERIFIED_CODE_ONLY + T4 | T2 | INFO | none |
| F-022 | Organism is live at audit time (state files mutated within 60 s; beat 38516) | VERIFIED_LIVE | T0 | INFO | none |
| F-023 | Approvals: server-minted atomic single-use; HMAC callback-token binding exists but flag default OFF | VERIFIED_CODE_ONLY (+live file use today) | T2+T0 | MEDIUM | none |
| F-024 | Local .bat relaunch surfaces exist (live/server.py, cortex_symmetric_revive) — duplicate-safe, cap+incident on loops | VERIFIED_CODE_ONLY | T2 | LOW | none |
| F-025 | Two independent PolicyGate implementations (policy/policy_gate.py vs agi2027_control/runtime.py) + two Telegram clients — acknowledged INV-4 divergence risk | VERIFIED_CODE_ONLY | T2 | MEDIUM | none |
| F-026 | 4d_system brain is NOT connected to live organism (CURRENT-TRUTH + wiring) | VERIFIED_CODE_ONLY / STALE claim basis | T4+T2 | INFO | C-7 |
| F-027 | MCP server surface exists (git/file subprocess tools; loopback host allowlist) | VERIFIED_CODE_ONLY (runtime registration UNKNOWN) | T2 | LOW | none |
| F-028 | board_cp is the only 0.0.0.0 bind (:8801), TLS fail-closed, 2 endpoints, Bearer-gated; all other servers loopback | VERIFIED_CODE_ONLY | T2 | MEDIUM | none |
| F-029 | Generic outbound-HTTPS client structurally NOT_WIRED; agi2027 external call triple-gated (READY_NOT_CALLED default) | VERIFIED_CODE_ONLY | T2 | INFO | none |
| F-030 | Telegram egress host-pinned to api.telegram.org; probe tool method-allowlisted (getMe/getWebhookInfo) | VERIFIED_CODE_ONLY | T2 | INFO | none |
| F-031 | "Mutual veto" governance could not be located as code-enforced mechanism | UNKNOWN | — | — | C-8 |

## Detail — selected findings

### F-001/F-002 Raw shell (HIGH)
`_ops/shell_capability.py` runs `subprocess.run(cmd, shell=True)` at the **repo root** behind: owner activation file, three kill files, a ~20-rule regex deny-list, 120 s/20 KB caps, audit-before-execute. It is reachable from Telegram `/sh <cmd>` (`center.py:648-695`) after `_is_owner`. The deny-list encodes the owner's charter (no deletes, no .git/_code/secret access, no network egress, no privilege escalation) but does not deny `python -c`, `pip install`, or redirection into source files — i.e. it is a charter-filter, not a capability sandbox. Zero executions recorded (audit file absent) → armed but unused. Deny-list inspection only; no exploitation testing performed (STOP rule respected).

### F-003/F-006 The strongest gate is dead code (HIGH — governance)
`_ops/octopus_v3/gate.py` (P0ExecutionGate: kill → hard_no_go → taint→network=none → owner approval → budget reserve → lease consume → INTENT ledger → execute) is explicitly `WIRED=False` (`octopus_v3/__init__.py:12`) with zero consumers outside its package. `containment/` (G8) is equally dormant. The live ADR-033 PolicyGate enforces only `request_protective_halt` (wiring.py:2053) and the collaborator draft path (talk_gate). All other live executors (shell, code-apply, outbound senders, OpsActionEngine) rely on **module-local** gates. Conclusion for Task 10: gating is **structural but federated** — each executor has deterministic checks, but there is **no single enforced choke point** matching the documented architecture.

### F-005 approval_id semantics (MEDIUM)
`policy_gate.py:132-137` treats `approval_id` as truthy/non-null. Any caller constructing a RequestContext with a fabricated non-empty string passes this layer; binding to a real owner approval must be proven by the caller. Live callers (protective_halt, talk draft) hardcode `approval_id=None` or never reach approval actions, so no live exploit path — but the gate cannot be composed safely without an external approval-verifier.

### F-007 code_autonomy (MEDIUM, currently inert)
Eight sequential gates (activation, heart≠freeze, owner tap-approval, allowed_target, shadow-green, refractory, non-empty, auto-approval-risk). Path containment uses resolve-then-containment (target_guard.py:78-147) rejecting absolute/UNC/drive-letter/nul-byte. Deny-list protects its own TCB (code_autonomy, kill, capability_gate, budget/, money, germline, organism, .env, .git). Residual: `_ALLOW_ROOTS` includes `_ops/state` — writable state can steer organism behaviour without touching code. Live status now: `STOP-CODE-AUTONOMY` present → `active()` False.

### F-009 web_research injection chain (MEDIUM)
`cortex/web_research.py` (flag `OCTOPUS_WIRE_WEB_RESEARCH`, default off; exposed via wiring.py:941, work_pump every 12 h): DDG/Wikipedia/arXiv fetch with scheme check + rate limit only — no host allowlist, no private-IP rejection, no size cap. Results land in `state/pulse/research-latest.json`, consumed by `improve.gather_signals()` (improve.py:328) and `synthesis.py:61` **without an UNTRUSTED fence**. This contradicts the repo's own hardened patterns (`world_discovery/public_web.py` UNTRUSTED_EXTERNAL_CONTENT fence; `observatory/fetch_guard.py` ADR-041 allowlist). End effects remain propose-only (patches need owner tap + shadow-green), so this is an injection-into-reasoning risk, not an unauthenticated effect path.

### F-010 memory→reasoning unlabelled (MEDIUM)
`.env` sets `OCTOPUS_WIRE_VAULT_RAG=1`. `memory/vault_bridge.py` is read-only/evidence-only (documented narrowing-only), but `retrieval_router.py` carries no trust/taint markers: vault-note snippets and memory gists enter brain prompts (`cortex.think` rich mode appends last reflection; improve consumes synthesis) indistinguishable from trusted state. Model output is downstream of unlabelled untrusted text — the invariant "model output is untrusted input" holds on the effect side, but provenance labelling on the input side is absent.

### F-015 armed posture (HIGH)
Fifteen activation flags present (RAW-SHELL, CODE-AUTONOMY, SELF-IMPROVE-AUTO, REPLICATION, GO-LIVE, PULSE(+ARBITER), HEART-DOCTOR, HEARTSTATE, GOVERNOR-LLM, WORK-LLM, CORTEX-PAID, DEBATE, RESEARCH-EARLY, C6-RESEARCH). The kill-side counterweight currently present is only `STOP-CODE-AUTONOMY`. This is an owner-chosen posture, not a bug — but it maximises the consequence of any single authentication failure (Telegram account takeover = raw shell at repo root next to live `.env`).

### F-017/F-018 ledger & identity (INFO)
Ledger append observed 11 min before audit with prev-hash chaining → live. Bitemporality (valid-time/transaction-time) NOT implemented — single `ts` per row. `identity_health=0.542` present in live ORGANISM-STATE.json, produced per beat by `math_control/spine.py:157`.

### F-023 approvals (MEDIUM)
`approval_store` mints `job_<type>_<ts>` ids (sanitised), atomic single-use transitions under file lock; verification order HMAC → expiry (clock-guard fail-closed) → destination binding. But `OCTOPUS_WIRE_CB_TOKEN` is unset → the cryptographic binding layer is dormant; protection rests on owner chat-id + single-use + destination checks.
