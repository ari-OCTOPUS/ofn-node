### چند-ارائه‌دهندهٔ هوش فعال — ۲۰۲۶-۰۹-۱۳ ~03:45Z (الحاقی؛ MULTI_PROVIDER_COGNITION_ACTIVE)
```text
MULTIPROVIDER = ACTIVE. Credential file /home/ari/.config/ofn/external-models.env installed by this lane
                (owner-supplied; ari:ari, mode 600; 187 vars; CRLF stripped). It did NOT exist before.
                Owner ruling: keep these tokens permanently; nothing deleted, nothing rotated.
LIVE_PAID     = deepseek (deepseek-flash) | gemini (gemini-3.8-flash) | openai (gpt-5.6-terra) |
                anthropic (claude-sonnet-5)
LIVE_FREE     = local-llamacpp-180 (qwen3-0.6b, $0, always first rung; from 138 reachable at 192.168.0.180:8081)
BLOCKED       = sakana-fugu   ACCOUNT_LIMIT_REACHED   (credential valid: models list 200 with 8 models, calls 429;
                              account-level limit — a new IP or a new key cannot reopen it)
ANTHROPIC_FIX = unblocked 2026-09-13 by adding ANTHROPIC_WORKSPACE_ID (a workspace IDENTIFIER, not a credential)
                to the secure file; the credential used is the one already stored there. Canary served
                claude-sonnet-5 ($0.00052); models list 200 with 11 models.
CHAT_KEY_WARN = a Claude key was posted in a chat transcript on 2026-09-13. It was NOT read, stored or used by
                OCTOPUS (it is not in the secure file). A credential whose only copy is a chat/log is classified
                CREDENTIAL_EXPOSURE_REQUIRES_ROTATION — the owner should DELETE it in the Anthropic console
                (key id apikey_01HYoiWGnN2BiBxvDMiy8FD3) rather than reuse it.
ROUTE_CHAIN   = deterministic -> local-llamacpp-180 -> deepseek -> gemini -> openai -> WAITING_COGNITION
                (frozen in config/provider-routes.json). A non-LIVE provider is skipped BY NAME; there is no
                silent failover and every route selection writes a ledger receipt.
OWNER_DECISION= 2026-09-13: default provider for ordinary work = deepseek (was cheapest-healthy = gemini);
                budget caps UNCHANGED. Proof: task owner-default-proof-20260913 served by deepseek-flash.
BROKER_FIX    = explicit provider->variable mapping replaces the first-match load_key scan (defect F-2: a stale
                key above a fresh one silently won); the credential is handed to the child over STDIN, never
                argv (the previous argv form was readable from the process table).
DISCOVERY     = configured deepseek names did not exist -> resolved to deepseek-flash / deepseek-v4-pro from the
                provider's own list (config/discovered-models.json); the owner's credential file was not rewritten.
BUDGET        = shared global contract UNCHANGED (owner re-confirmed 2026-09-13): window1 $20 / window2 $20 /
                steady $10 per 24h / month $100 / per task $2 / 3 calls per task / concurrency 1 / no rollover /
                no borrowing.
SPEND         = $0.084512 of window1 (37 ledger rows). Per-provider canary cap $0.25 enforced in code.
                Self-reported breach reconciled: two small out-of-band OpenAI diagnostic calls recorded as
                explicit reserve+settle pairs.
EXPOSURE      = none: 758-file scan clean (values compared in memory, booleans only); no key in receipts /
                ledger / state / generated code / worktrees; node 182 has no reference; WILD cannot reach the
                file (no separate local user; /home/ari/.config is mode 700).
EVIDENCE      = commit 6346d03; 09-LANES/API-BUDGET-ACTIVATION-20260913/MULTIPROVIDER-ACTIVATION-EVIDENCE.md
RULE          = never print, copy, prompt, or commit a credential value; paid calls only through
                api_budget.paid_call(); never create a new key; do NOT add external-models.env to ofn.service
                (its empty FUGU_API_KEY / OFN_REMOTE_API_KEY would shadow secrets.env and break the legacy
                RemoteBrain path).
```
