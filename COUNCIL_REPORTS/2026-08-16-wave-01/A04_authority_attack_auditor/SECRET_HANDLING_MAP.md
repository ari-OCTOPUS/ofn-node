# A04 — SECRET HANDLING MAP

**No secret values were read, printed, or copied during this audit.** All evidence is structural (file existence, git status, code paths).

## Inventory (location → handling)

| Secret class | Location | Load path | Exposure assessment |
|---|---|---|---|
| Bot tokens (center + approval), provider keys (FUGU/GLM/ANTHROPIC), mail creds, owner chat-id | `.env` (20 keys) at repo root | python-dotenv-style loads per module (`_ensure_env_loaded` in mail_credentials; opslib env conventions) | **Gitignored + untracked** (verified `git check-ignore` + `git ls-files`). Readable by any process of the same user — including, by design, the raw shell and sandbox runners (cwd = repo root) |
| Full historical secret snapshot | `.env.bak-20260810` (repo root) | none (dormant copy) | Same exposure as `.env`; **no consumer**; contains 2026-08-10-era secrets — delete (recommendation #4) |
| Mail password | env → `mail_credentials.resolve()` | `os.environ` only; dict returned **without** the password; masked addresses in logs/receipts (module docstring + code) | Good practice, verified |
| Callback HMAC secret | `OCTOPUS_CB_SECRET` env | `callback_token._secret()` | Machinery present; **feature flag off** (see OD-C) |
| Board CP bearer | `OCTOPUS_BOARD_CP_BEARER` env | `bearer_ok` fail-closed, `hmac.compare_digest`, never logged | Good |
| MiniApp auth | bot token → initData HMAC key (WebAppData derivation) | validate_init_data; token never in URL/logs | Good |
| Xero OAuth | `XERO_CLIENT_ID/SECRET` env | client_credentials flow to hardcoded hosts | OK; draft-only writes |
| TLS certs (board_cp) | cert/key files required at boot | fail-closed exit if absent | Good |
| Human-append guard secret | per-boot generated (organism heartbeat: "per-boot secret") | in-memory/env | Not examined further (no need) |

## Redaction / leak-prevention mechanisms observed
- `_scrub()` on all Telegram-bound text (center.py) — banned-string filter before egress.
- cortex `_redact()` on error bodies returned by HTTP handlers.
- shell_capability deny-list §0.2 blocks commands *naming* secret files (regex — see B-1 caveat).
- output_guard FORBIDDEN_PREFIXES blocks artifacts targeting `.env`, `secrets/`, `config/keys/`.
- code_autonomy deny tokens: `.env`, `secret`, `budget/`, `money`.
- public_web `_KEY_RE` strips API-key-like strings from fetched web content before storage.

## Gaps
1. `.env.bak-20260810` (delete).
2. Regex-based secret-name matching is bypassable at the shell layer (B-1) — secrets remain one owner-scope mistake from exfiltration via non-`curl` channels (e.g. `python -c` + SMTP/requests). Charter says network tools denied; library-level egress is not.
3. Secrets share a filesystem namespace with an armed shell — structural, accepted by owner vote 2026-08-04 (documented in shell_capability docstring); re-confirm as part of OD-B.
