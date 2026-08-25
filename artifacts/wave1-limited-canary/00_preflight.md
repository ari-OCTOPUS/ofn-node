# Wave 1 limited external-learning preflight

- Captured at: `2026-08-25T13:53:44Z`
- Gate: `GATE-WAVE1-LIMITED-LEARNING-CANARY`
- Decision: `APPROVED_WITH_CONDITIONS`
- Scope: `ONE_USE`
- Approval used: `false`
- Action executed: `false`

## Live continuity

- Branch: `feat/phase3-completion`
- Final repository HEAD: `c6ecac03ad9307a48e704ffee77e67a00df764a0`
- Loaded runtime source commit: `9dc8ad888a7723212e61fede3fce96664593ee22`
- Organism PID: `42687`, active/running, `NRestarts=0`
- Soak PID: `38871`, active/running, `NRestarts=0`
- Llama PID: `527`, active/running, `NRestarts=0`
- Gateway PID: `641`, active/running, `NRestarts=0`
- Existing controlled-growth result: `CONTROLLED_GROWTH_CANARY_PASS`
- Existing registry phase: `ACTIVE_LOCAL`
- Existing external-learning capability: `LOCKED`
- Existing external-action capability: `LOCKED`
- Existing Active Inference state: `SHADOW`

## Database and identity

- Identity head: sequence `266`, hash `ea809ad06e45a9f702aca1386a47703579c4e5e77ef5137bc758613621d97b1b`
- Independent identity-chain verification: `valid=true`
- Event head: node sequence `503`, event ID `12b5829ed350de488c92d1f39d325a91`, hash `cb20c45fa34908445a8df46b49df5cfe26fe3397333d349109feb8ec6e0c6b65`
- Episode count: `503`
- Memory receipt count: `718`
- Decision evidence count: `529`
- Memory future-use total: `0`
- Decision evidence rows without a matching memory receipt: `0`
- Executable evidence total: `0`
- External request counter (`wan_fetches`): `0`
- SQLite integrity: `ok`
- SQLite quick check: `ok`
- GET state delta: `0`

## Security and resources

- `OCTOPUS_GET_PURE=1`
- `OCTOPUS_REQUIRE_LAN_TOKEN=1`
- `OCTOPUS_LEARN_EXTERNAL=0`
- LAN token: present at `/etc/octopus/lan-token`, mode `0600`; content was not emitted.
- Root available: `7014727680` bytes (`6.53 GiB`)
- Root use: `89%`
- RAM available: `2274709504` bytes
- Temperature: `29615 mC`
- Unit/drop-in/start-script rollback config hash: `422bf2930c7a523732bbdb13c89113716e999a78c4d6b64567b60ed74ce896ca`
- Rollback config remains the existing systemd drop-in with external learning forced to `0`; no config change was made.

## Real provider discovery

- Provider: `DEEPSEEK`
- Exact endpoint: `https://api.deepseek.com/v1/chat/completions`
- Source allowlist: exactly `api.deepseek.com`
- Model ID: `deepseek-chat`
- Credential loader: `ofn/organism/cognition/secrets.py::load_named_secrets`
- Credential file: present, mode `0600`
- DeepSeek credential presence: `true`
- Flash-specific credential presence: `false`
- Credential values were neither printed nor persisted.
- Call sites: `learn.py::learn_topic()` via `complete_flash()`/`complete_deep()`, and `backend.py::AskCascade._ask_learn()`.
- Redirects are disabled and the host is checked before request.
- Existing response read is not explicitly size-bounded.
- Existing teacher call path does not increment the `wan_fetches` counter.
- No repository evidence establishes that this credential/account/model is no-cost for this canary.
- Paid budget authorized by this gate: `0`.

## Watcher

The earlier bounded watcher was still running and its heartbeat was fresh. Its original timeout was `3600s`; approximately `709s` remained, which is insufficient to cover a new `900s` canary. No replacement watcher was started because the provider/cost precondition already blocks activation and no request may be sent.

## Disposition

`DIRECT_OWNER_APPROVAL_REQUIRED=true`

The only real provider is a credentialed DeepSeek API endpoint. The repository contains no no-cost authorization, free-tier guarantee, billing guard, or owner-approved zero-cost account evidence. Under `PAID_BUDGET=0`, external requests are forbidden. Wave 1 was not activated, the existing registry was not changed, and `OCTOPUS_LEARN_EXTERNAL` remained `0`.

FINAL_STATUS: `BLOCKED_PRECONDITION`
