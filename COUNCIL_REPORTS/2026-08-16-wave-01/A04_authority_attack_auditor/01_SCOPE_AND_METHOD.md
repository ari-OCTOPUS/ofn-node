# A04 — SCOPE AND METHOD

## Scope
- **Root:** `F:\backup` (Obsidian vault + Python organism, git repo, branch `equip/g10-cognition-20260816`).
- **Code masses audited:** `_ops/` (primary runtime, ~1,548 py), `nervous-system/` (26), `octopus-bridge/` (2), `PRE-0` (2), `4d_system/` (243 — treated as separate process; live-wiring checked only), plus root scripts. `.claude/` (11,900 py, tooling/skills) **excluded** — out of organism authority path; noted as attack surface for a future wave. Archives, `_build`, `_portable-build`, `_zip-verify`, `_Duplicates` excluded as dead copies.
- **State observed read-only:** `_ops/state/`, `_octopus/state/`, `07 - Knowledge/genome-system/ledger/ledger.jsonl`, `.env` (metadata only — **no secret values were read or printed**; only flag-name lines were extracted).

## Method
1. **Surface sweep:** grep for `subprocess`/`shell=True`/`os.system`/`eval`/`exec`/`pickle`/`yaml.load`/`__import__`/`importlib`/`requests`/`httpx`/`urlopen`/`socket`/`smtplib`/`imaplib` across live code; classification per hit (live/test/dead).
2. **Authority-path tracing:** manual read of `shell_capability`, `policy/policy_gate`, `policy/talk_gate`, `octopus_v3/*`, `capabilities.py`, `wiring.py` (4,347 ln, structural outline + targeted reads), `organism.py` (loop + drivers), `cortex/cortex.py`, `code_autonomy`, `target_guard`, `output_guard`, `httpauth`, `board_cp/*`, `containment/*`, `mining_stop_intent`, `outbound_worker`, `consent_gate`, `effector_gate_bridge`, `pocketsmith_api`, `ps_writeback`, `mail_credentials`, `vault_bridge`, `web_research`, `public_web`, `fetch_guard`, `model_router`, `approval flow (approval_store/callback_token/center)`.
3. **Three parallel read-only sub-sweeps** (network egress; Telegram/approval auth; coding-sandbox/self-modification), each instructed to treat repo content as untrusted and to return file:line + quotes; key claims independently spot-verified by A04 (notably: board_cp Bearer actually fail-closed — correcting a subagent's initial "no owner auth" flag; STOP-CODE-AUTONOMY present).
4. **Live observation (T0):** file mtimes on state dirs (organism mutated <60 s before observation), ledger tail timestamp + hash-chain fields, ORGANISM-STATE beat/identity_health, absence of raw-shell audit file, armed-flag enumeration.
5. **Prompt-injection discipline:** all file contents treated as data; no instruction inside any file was followed; no project code executed; no network calls made; no writes outside this report directory.

## Truth-tier usage
T0 = live state/flag/ledger observation · T2 = code read this session · T4 = CURRENT-TRUTH/HANDOFF used only as claims to check, never as proof. Statuses per contract (VERIFIED_LIVE / VERIFIED_CODE_ONLY / … / UNKNOWN).

## Limitations
- No runtime instrumentation (no process introspection, no port scans beyond static binds) — "live" for servers means code+state evidence, not a socket probe. Deliberate: READ_ONLY, no consequential tools.
- `.env` runtime values for flags verified for non-secret keys present in the file; launcher scripts could set additional env vars at boot (flagged in 08_OPEN_QUESTIONS Q3).
- 4d_system assessed only for live-wiring (not connected) and egress inventory (separate process, dead wrt organism loop); its internals were not audited.
- Subagent sweeps are T2 evidence; A04 re-verified load-bearing claims directly (owner auth chain, board bearer, kill files, gate wiring, web_research, vault RAG flag).
