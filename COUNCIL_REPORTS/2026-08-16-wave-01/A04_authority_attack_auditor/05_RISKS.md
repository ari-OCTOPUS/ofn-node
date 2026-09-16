# A04 — RISKS

Risk = threat × exposure × existing barriers. Barriers cited are real code, not documents.

## R-1 · Owner-account compromise → full machine control (SEVERITY: HIGH, LIKELIHOOD: LOW)
Telegram `from.id` is the root of all command authority; `/sh` runs arbitrary shell at repo root (where live `.env` with provider/mail/Telegram credentials sits). With all flags armed, a hijacked Telegram session or a stolen bot token (api.telegram.org polling) yields shell + secrets + git-tree writes (deny-list permits `git add/commit`, file redirection; blocks push/.git internals).
Barriers today: env chat-id allowlist (deterministic), deny-list (charter rules), audit-first, kill files, loopback-only servers. Missing: second factor on `/sh`, HMAC callback tokens (flag off), secret隔离 from shell cwd.
Note: bot-token theft alone does NOT pass `_is_owner` (updates from non-owner ids are dropped) — but a hijacked *owner account* does. (F-001, F-002, F-011, F-015)

## R-2 · Injection into reasoning via unfenced web content (SEVERITY: MEDIUM)
`web_research` result pages (flag-gated) and vault/memory snippets (RAG live) enter `improve()`/synthesis/think context with no UNTRUSTED fence. Malicious page/note content can steer proposals shown to the owner and self-patch targets. Buffered by: propose-only effects, owner tap, shadow-green tests, target allow-lists. Residual: owner-fatigue rubber-stamping; `_ops/state` inside allow-roots.
(F-009, F-010, F-007)

## R-3 · Federated-gate drift (SEVERITY: MEDIUM-HIGH over time)
No central choke; each executor re-implements allow/deny/kill semantics. Already-diverged duplicates: two PolicyGate classes, two Telegram auth implementations, two web-fetch stacks (fetch_guard vs web_research). Each new module is a fresh chance to forget a gate; dead central gates (v3, G8) rot while documents describe them.
(F-003, F-004, F-006, F-025)

## R-4 · Regex deny/allow lists as capability boundaries (SEVERITY: MEDIUM)
shell_capability deny-list and coding_sandbox prefix allowlist are string-pattern checks on commands that then run via `shell=True`. `python -c`, `pip install`, indirect file writes pass. Deterministic — but the policy they enforce is narrower than the intent ("don't do dangerous things") suggests.
(F-002, F-008)

## R-5 · LAN exposure of board control plane (SEVERITY: LOW-MEDIUM)
`board_cp/server.py` binds `0.0.0.0:8801` (only non-loopback listener). TLS fail-closed (no certs → exit), Bearer fail-closed, 2 read/ack endpoints, `is_armed()` gate. On a hostile LAN with valid certs present and bearer leaked, pull/ack of owner command queue becomes reachable. 
(F-028)

## R-6 · Plaintext secret backup at repo root (SEVERITY: MEDIUM hygiene)
`.env.bak-20260810` — full secret snapshot, gitignored but world-readable to any process running as the user (including the raw shell and sandbox runners by design of cwd).
(F-014)

## R-7 · Approval-token binding dormant (SEVERITY: MEDIUM)
`OCTOPUS_WIRE_CB_TOKEN` unset → callback approvals rely on transport (owner chat-id) + single-use store, without the cryptographic binding already implemented in `callback_token.py`. Forwarding/spoofing a callback inside an authorized chat is the residual vector.
(F-023)

## R-8 · state-writing autonomy (SEVERITY: MEDIUM)
`code_autonomy._ALLOW_ROOTS` includes `_ops/state` — approved patches can rewrite runtime state (knobs, pending cards, mining intents) that steers the organism without touching protected code paths.
(F-007)

## R-9 · Dead-but-armed combinations (SEVERITY: posture)
ACTIVATION-CODE-AUTONOMY armed with only a STOP file standing between; STOP files are single files whose creation/deletion is owner-side convention. A state-writer (R-8) that learns the STOP path could re-enable code-apply. Deny-list forbids the shell from touching STOP/ACTIVATION names — but `_ops/state` writes are not so constrained.
(F-007, F-015, R-8)
