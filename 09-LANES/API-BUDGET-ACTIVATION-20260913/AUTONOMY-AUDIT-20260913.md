---
title: AUTONOMY-AUDIT-20260913
lane: API-BUDGET-ACTIVATION-20260913
date: 2026-09-13
owner_order: "همه خطراتو می‌پزیرم اختاپوس رو چک کن کامل خودمختار باشه"
verdict: AUTONOMOUS_OPERATIONAL_WITH_3_NAMED_GAPS
method: read-only audit + in-sandbox runtime proof
secrets_exposed: none
---

# Autonomy audit — is OCTOPUS fully autonomous?

**Verdict: yes for its control loops — it plans, acts, verifies, repairs, budgets, spends and
reports without the PC.** Three gaps remain, and none of them is "the organism stops if the PC
is off". They are: code *publication* to GitHub, an unproven Class B execution path, and one
missing self-measurement source.

Re-runnable at any time: `python3 <lane>/package/autonomy_audit.py` on node 138
(13 checks; last full run 2026-09-13T04:07:05Z).

## 1. What was verified

| Check | Result | Evidence |
|---|---|---|
| Kill-switch absent (autonomy permitted) | PASS | `state/autonomy/STOP-AUTONOMY` absent; `/etc/octopus-ops-halt` absent |
| Timers scheduled | PASS | **26** octopus/ofn timers with next-run times |
| Core timers enabled at boot | PASS | `octopus-autonomy-supervisor.timer`, `octopus-ops-agent.timer`, `octopus-coding-worker.timer` all `enabled`; host booted 2026-09-13 02:42 |
| Supervisor ticking | PASS | receipts 423 rows; last tick 04:02:16Z, `TICK_COMPLETE`, ledger verification inside the tick |
| Queue / predictions / witness ledgers | PASS | queue 10, predictions 6 (`predictions_ok: true`), witness-consumption 1 |
| No `GLOBAL_AUTONOMY_PAUSE` | PASS | 0 occurrences in 423 receipts |
| ops-agent armed | PASS | `armed.json` = B2,B3,B4,B5,B6,B8 all `true` |
| coding-worker ticking | PASS | last `TICK_COMPLETE` 04:07:03Z `NATIVE_CODING_IDLE_HEALTHY` |
| **Core oneshots really succeed** | PASS | `ExecMainStatus=0 / Result=success` for supervisor, ops-agent, coding-worker, witness, shadow-verify, scheduler, brainwake |
| Owner contact path live | PASS | `octopus-bridge.service` active |
| No PC-path dependency in runtime files | PASS | no `F:\`, `C:\`, `/mnt/*`, or PC-IP references in service/unit/runtime sources |
| Witness node reachable | PASS | 182 answers over the mesh key |
| Storage / memory | PASS | `/` 29% used (40G free), 2.9G RAM available |

The only failed systemd unit on the host is `smartmontools.service` — host-level SMART daemon
(no SMART-capable device on this SBC). Unrelated to OCTOPUS autonomy.

## 2. The decisive test — can the worker actually *use* paid cognition in production?

A service that cannot read its own credential is not autonomous, and `ProtectHome=read-only`
plus `PrivateTmp=true` made that a real question. So the probe was run **inside the exact
sandbox** of `octopus-coding-worker.service` (`systemd-run` with the same properties, `--uid=ari`):

```text
uid=1001 user=ari
credential_file_readable: True (16245 bytes)
registry_import: True
candidates: ['deepseek', 'gemini', 'openai', 'anthropic']
health: local-llamacpp-180 LIVE | deepseek LIVE | openai LIVE | anthropic LIVE | gemini LIVE
        sakana-fugu ACCOUNT_LIMIT_REACHED
deepseek models endpoint: ok=True http=200 count=2
gemini   models endpoint: ok=True http=200 count=50
broker_import: True     budget: window=window1 cap=20.0 spent=0.084512
writable: /home/ari/ofn/state/coding-worker/state True | /tmp True
credential_dir_writable: False (OSError)  <-- correct
```

Reads the credential, resolves four live providers, reaches the network, reads the shared
budget — and **cannot write** into the credential directory. The paid rung wired earlier is
therefore genuinely available in production, not just in a shell.

## 3. The three real gaps (named, with owners)

**G-1 — The organism cannot publish its own code (owner-side, external).**
Repo `ari-OCTOPUS/ofn-node` has **deploy keys disabled**, so `autonomy/*` branches cannot be
pushed from the node. Everything else about the git workflow is local and autonomous; this one
step needs an owner toggle (enable deploy keys) or a fine-grained PAT. Until then the organism
commits locally and stops at publication.

**G-2 — Class B has never executed (`CLASS_B_EXECUTED=0`).**
The Class B path is armed, witness-gated (16-field verdict, single-use consumption, node-182
mandatory) and dry-run tested — but it has **zero production executions**. Its E-grade is
therefore low until a genuine Class B event occurs. Manufacturing one to "prove" it is
forbidden, so this stays open honestly.

**G-3 — One self-measurement source is missing (frozen-artifact change, needs owner visibility).**
The frozen prediction `load1_138_p95_poststagger_window` reconciled as `EXPIRED_UNOBSERVED`
because the reconcile extractor only recognises `cpu_headroom` targets
(`supervisor.py:296-317`). The value *is* measured — the telemetry store carries
`cpu_headroom.raw = "load1=1.33 nproc=8"` — but it is not exposed as a structured `load1` metric
(`eti/node_telemetry_collector.py:48,137` is where it would be added).

**Why this was not fixed here:** it means editing the **frozen** reconcile/rubric source, and
AGENTS.md §5 forbids changing a scoring formula mid-cycle. Recorded as a scoped proposal, not
applied silently. Proposed shape: emit a structured `load1` metric from the already-measured
value (additive, no new formula), then define the p95 window explicitly before any extractor
change, so no post-hoc tuning is possible.

## 4. Not gaps (explicitly checked, so nobody re-opens them)

* **Reboot survival** — verified in the CONTINUITY lane with a real reboot; core timers are
  enabled at boot and today's 02:42 boot was followed by normal ticks.
* **Owner stop is absolute** — the kill-switch path was proven honored earlier (every tick after
  2026-09-12T19:34Z wrote `KILL_SWITCH_STOP` and did nothing else).
* **No silent provider failover** — providers that are not LIVE are skipped by name and recorded;
  every selection writes a receipt.
* **Secrets boundary** — WILD has no local user, `/home/ari/.config` is `700`, the credential file
  is `600`, node 182 has no reference to it, and a 758-file scan found no value in receipts,
  ledger or state.

## 5. Standing owner item (restated once)

A Claude API key was posted in a chat transcript on 2026-09-13
(`apikey_01HYoiWGnN2BiBxvDMiy8FD3`). The owner has stated they accept the risk; it remains
**unused and unstored** by OCTOPUS, and deleting it in the console is still the clean close-out.
Nothing about autonomy depends on it — Anthropic went live on the credential already in the
secure file.

## 6. Status

**AUTONOMOUS_OPERATIONAL_WITH_3_NAMED_GAPS** — the organism runs its own loop end-to-end on
node 138 + 180 + 182 with four live paid providers and a free local rung, under an unchanged
owner-approved budget. The remaining three items are one owner toggle (G-1), one unproven
production path (G-2), and one frozen-artifact proposal (G-3).
