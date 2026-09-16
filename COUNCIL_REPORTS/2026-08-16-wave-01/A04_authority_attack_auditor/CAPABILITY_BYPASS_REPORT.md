# A04 — CAPABILITY BYPASS REPORT

Candidate bypasses investigated; verdict for each. "Confirmed" = code path exists; "exploitable" requires the stated precondition.

## B-1 · Deny-list is not a capability boundary (shell)
**Path:** `/sh` → `shell_capability.check()` (regex, ~20 charter rules) → `subprocess.run(shell=True)` at repo root.
**Confirmed.** Not string-matched but semantically-equivalent commands pass: `python -c "<arbitrary code>"`, `pip install <pkg>`, `echo … > _ops/<any module>.py`, `git add -A; git commit -m x`. Only §0 charter items (delete/.git-internals/_code/secrets-name-match/network-egress-tools/privilege/kill-files) are denied.
**Precondition:** owner Telegram account (or anything able to forge `from.id`, which the API design makes hard). So this is *owner-scope* bypass of the charter, not an outsider bypass.
**Confusion note:** `§۰.۲ secret` rule matches the *string* `.env`/`_TOKEN` etc. in the command — reading secrets via `python -c "print(open('.env'[:0] or '.en'+'v').read())"`-style construction evades the regex. Recorded as evidence of regex-insufficiency only (STOP rule — no exploitation detail beyond this demonstrative class).

## B-2 · Sandbox allowlist prefix bypass
**Path:** `coding_sandbox/command_runner.py` — `python …` prefix allowed; `python -c "…"` = arbitrary code in worktree; `pip install` allowed (network for PyPI via pip is not stripped — only proxy env is removed).
**Confirmed** (code). **Currently inert** unless the sandbox is driven by a live task (flag-dependent) — and cwd is a worktree, blast radius = repo copy + host user privileges (no OS jail).
**Precondition:** cortex/LLM content reaching the runner without owner tap.

## B-3 · approval_id presence-only (PolicyGate)
**Path:** any future caller building `RequestContext(approval_id="x")` passes the approval check (`policy_gate.py:132-137`).
**Confirmed at gate layer; no live caller abuses it** (live callers hardcode None or never reach approval actions). Bypass becomes real the day a compose wires the gate without an external verifier (exactly what OD-A would do — hence recommendation #2).

## B-4 · `_ops/state` writes steer the organism (confused deputy)
**Path:** approved code_autonomy patch → `_ALLOW_ROOTS` includes `_ops/state` → modify state consumed by beats (knobs, pending cards, intents) → behaviour change without touching protected code.
**Confirmed as scope, unproven as exploit** (requires owner-tapped patch whose diff hides the steering). Related: STOP/ACTIVATION files live in `_ops/` (denied for shell & code_autonomy, but not provably for every state writer — Open Question Q6).

## B-5 · Callback token binding dormant
**Path:** approval callbacks verified by chat-id + single-use + destination only; `callback_token.py` HMAC machinery exists behind `OCTOPUS_WIRE_CB_TOKEN` (unset).
**Confirmed dormant.** Requires compromise *inside* the authorized chat (forwarded buttons, client bug) — low likelihood, cheap to close (OD-C).

## B-6 · Two gates / two auth stacks (divergence)
`policy/policy_gate.py` vs `agi2027_control/runtime.py:171`; `center.py` vs `approval_channel.py` auth; `fetch_guard` vs `web_research`. No live divergence-bypass found today; the structure invites future "fixed in one, forgotten in the other". Repo's own INV-4 note concurs.

## B-7 · Investigated and NOT confirmed
- **board_cp pull/ack without auth** (flagged by sweep): false alarm — Bearer required, fail-closed when unconfigured (`config.bearer_ok` → False on empty expected/got, `hmac.compare_digest`).
- **Non-owner Telegram → effects**: `handle_update` drops non-owners before any handler (deterministic).
- **Cross-origin POST to loopback servers**: httpauth Origin/Referer loopback check, default-on, fail-closed 503 if guard missing (cortex, live server).
- **SQL injection**: no SQL string-building found in telegram_center/legs state paths (JSON files; chrono.db via sqlite but no dynamic SQL from message text observed in audited paths).
- **MCP tool-name smuggling**: server exists with loopback host allowlist; runtime registration unobserved (Open Question Q1) — cannot confirm attack path.
- **`OWNER_AUTH` chat text as authorization**: record-only by design (center.py:3103-3127), consistent with CURRENT-TRUTH's "chat ≠ signature".

## Net assessment
No **unauthenticated** or **untrusted-content** bypass to a consequential effect found. All bypass candidates require owner-scope compromise (B-1, B-5) or a future wiring mistake (B-3, B-6). The systemic risk is structural: correctness depends on N independent module gates staying correct simultaneously.
