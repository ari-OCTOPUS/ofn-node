# RUNTIME CONFIG PROVENANCE — A02 Runtime Investigator

Question: does runtime config follow `command-line > env > config > defaults > persisted state`? **Answer: effectively yes, with two important details** — (1) the top layer is a batch file that *injects* env vars before Python starts, and (2) persisted auto-tuned state can only fill keys that are *otherwise unset* — it can never override any explicit layer.

## Live-proven precedence chain (highest wins)

1. **`F:\backup\_ops\OCTOPUS-flags.cmd`** (non-secret flag overrides), `call`ed by every launcher (`RUN-ORGANISM.bat:26`, `RUN-CORTEX.bat`, `run-live-headless.bat`, `RUN-TG-CENTER.bat`) immediately before `python …`. These `set KEY=VALUE` lines become the child's environment — highest practical layer. mtime 12:52:57, i.e. rewritten seconds before the current organism boot.
2. **Pre-existing process environment** (`os.environ` inherited from the shell/schtask) — code reads everything through `os.environ.get("KEY", default)` (e.g. `organism.py:235` `ORGANISM_PORT`; `chrono.py:56-70` `_envf`).
3. **`F:\backup\.env` secrets file** — loaded at boot by `env_loader.load_env()` (`organism.py:231-232` → `_ops/budget/env_loader.py:33-56`). Key property: **idempotent, fills only keys not already in `os.environ`** — so flags.cmd and inherited env always beat `.env`. Keys: `GLM_API_KEY`, `FUGU_API_KEY`, `DEEPSEEK_API_KEY`, `ZAI_API_KEY`, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_CHAT_ID` (names only; values not inspected).
4. **Persisted auto-tuned knobs** — `state/cortex/auto-knobs.json` restored at boot by `auto_approve.load_persisted_knobs()` (`auto_approve.py:395-408`, called `organism.py:282-289`). Restoration is doubly constrained: only if the key is **unset** in env, and only if the value lies **within the safe bounds** in `cortex/improve.py:223-225` (e.g. `HEART_SAMPLE_INTERVAL_S` ∈ [1800, 7200]). This is the boot log line "auto-tuned knobs restored: ['ts','CHRONO_NUDGE_EVERY_N_BEATS','note','HEART_SAMPLE_INTERVAL_S','CORTEX_THINK_EVERY_N','owner_apply_ts']".
5. **Hardcoded defaults** in code (`os.environ.get(NAME, DEFAULT)` pattern throughout; `chrono.py` `PERIOD_S` default 60.0 etc.).

**Command-line arguments**: none of the live services take config arguments (only `-X utf8`); CLI is therefore not an active precedence layer today.

## Live snapshot evidence

`_ops/state/flags-loaded-organism.json` (schema `flags-loaded.v1`, written at boot, pid 29028, source `F:\backup\_ops\OCTOPUS-flags.cmd`):

- `file_count: 335`, `env_count: 340`, `missing_count: 0`, `alarm: False` — every expected flag resolved.
- Secrets are **redacted by the loader itself** before persisting (`secret_names` lists 9 keys; values stored as `<redacted>`) — good hygiene, verified.
- **Practically every `OCTOPUS_WIRE_*` flag is `'1'`** (~200 wiring flags on, including `OCTOPUS_WIRE_PULSE_ARBITER`, `OCTOPUS_WIRE_COHERENCE`, `OCTOPUS_WIRE_ACTUATOR`, `OCTOPUS_WIRE_KILL_SEAM`, `OCTOPUS_WIRE_LEAD_OUTBOUND`, `OCTOPUS_WIRE_POCKETSMITH`), plus autonomy arming flags `OCTOPUS_AUTONOMY_FREE=1`, `OCTOPUS_AUTONOMY_GRANT=1`, `OCTOPUS_CODE_AUTOAPPLY_LOWRISK=1` (F-12).
- **Absent** (therefore default-off): `OCTOPUS_WIRE_DUAL_VETO` — the mutual-veto brain gate is NOT enabled (F-16).
- `OCTOPUS_PROFILE=live`, `OCTOPUS_SPEND_CAP_USD=200`, `OCTOPUS_SPEND_CAP_UNTIL=2026-08-13` (expired window, F-14), `OCTOPUS_QUIET_FROM=23`/`TO=7` (matches the quiet hours visible in telemetry cadence).

## Other config sources observed

- `board_cp/server.py` reads `OCTOPUS.env` + `OCTOPUS-flags.cmd` at startup (setdefault), env `OCTOPUS_BOARD_CP_PORT` (default 8801), `OCTOPUS_BOARD_CP_BIND` (default **0.0.0.0**), TLS dir default `_ops/state/board_cp/tls`.
- Named-tunnel config is inline (no config.yml drift — see `run-miniapp-tunnel-named.ps1` header): hostname from `OCTOPUS_MINIAPP_HOSTNAME` (`app.master-painting.com`), port from `OCTOPUS_MINIAPP_PORT` (default 8774).
- Legacy `_octopus/config/*.yaml` (bots, octopus, policy, projects — all mtime 2026-07-18) belongs to the older control-plane whose state is mostly stale (F-28); no evidence the live organism reads it.
- Kill switches are **files, not config**: `STOP-ORGANISM`, `STOP-CORTEX`, `STOP-TG-CENTER`, `HALT-ALL`, `04 - Architect System/STOP` (checked per-loop; F-19). Existing on disk now: `STOP-CODE-AUTONOMY` (active) and `STOP-FUGU.cleared-20260726` (tombstone).
