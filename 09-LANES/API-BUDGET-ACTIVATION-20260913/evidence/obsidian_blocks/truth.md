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
ROUTE_CHAIN   = deterministic -> local-llamacpp-180 -> deepseek -> gemini -> openai -> anthropic -> WAITING_COGNITION
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

### حکم خودمختاری — ۲۰۲۶-۰۹-۱۳ ~04:10Z (AUTONOMOUS_OPERATIONAL_WITH_3_NAMED_GAPS)
```text
AUDIT         = 13-check autonomy audit on 138 + an in-sandbox runtime proof; re-runnable via
                09-LANES/API-BUDGET-ACTIVATION-20260913/package/autonomy_audit.py
LOOPS         = 26 timers; the three core timers are enabled at boot; supervisor 423 receipts (last tick
                04:02:16Z), ops-agent armed B2-B8, coding-worker last tick 04:07:03Z; every core oneshot
                ExecMainStatus=0 / Result=success; 0 GLOBAL_AUTONOMY_PAUSE; owner bridge active; no PC path
                referenced by any runtime file. (Only failed host unit: smartmontools, unrelated.)
SANDBOX_PROOF = the probe ran INSIDE octopus-coding-worker.service's own sandbox (ProtectHome=read-only,
                PrivateTmp=true, User=ari): credential file read (16245 bytes), broker imported, 4 live
                providers resolved, models endpoints 200 from inside, budget readable — and writing into
                the credential directory FAILED (OSError). Paid cognition is available in production.
GAP_G1        = code publication: ari-OCTOPUS/ofn-node has DEPLOY KEYS DISABLED, so autonomy/* cannot be
                pushed. Owner-side toggle. Everything else in the git path is local and autonomous.
GAP_G2        = CLASS_B_EXECUTED=0: armed, witness-gated, dry-run tested, never executed in production.
                Manufacturing an event to "prove" it is forbidden, so it stays honestly open.
GAP_G3        = one self-measurement source missing: load1_138_p95_poststagger_window reconciled as
                EXPIRED_UNOBSERVED because the reconcile extractor recognises only cpu_headroom targets
                (supervisor.py:296-317); the value IS measured but only inside cpu_headroom.raw
                (eti/node_telemetry_collector.py:48,137). Editing the FROZEN reconcile/rubric source would
                change a scoring formula mid-cycle, which AGENTS.md section 5 forbids — recorded as a
                scoped proposal, NOT applied.
VERDICT       = the organism plans, acts, verifies, repairs, budgets, spends and reports without the PC.
```
