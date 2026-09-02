# OCTOPUS Cursor governance pack — install and verify

This pack turns the OCTOPUS written rules into machine-enforced rules. Documentation-only
rules are advisory; hooks are enforcement. Both layers are included because they fail differently:
a rule can be ignored by the model, a hook cannot.

## Layout

```
AGENTS.md                       binding contract, read by Agent, CLI, and cloud agents
.cursor/rules/
  00-always-guardrails.mdc      alwaysApply: injected into every session
  10-evidence-grading.mdc       description-triggered: pulled in for capability claims
  20-python-tests.mdc           glob-scoped: **/*.py, tests/**
  30-ledger-and-docs.mdc        glob-scoped: docs, ledgers, handoff
  40-measurement-lane.mdc       description-triggered: measurement work only
.cursor/hooks.json              hook wiring, failClosed on every security hook
.cursor/hooks/*.py             enforcement scripts, all append to a hash-chained ledger
.cursor/mcp.json                MCP servers, deny-by-default via allow_mcp.py
09-LANES/LANE-MATRIX.csv        file ownership per lane, prevents write collisions
09-LANES/LANE-PROMPT-TEMPLATE.md  the only prompt shape a lane session may start from
```

## Install

1. Copy `AGENTS.md`, `.cursor/`, and `09-LANES/` into the repository root.
2. Commit them. Project hooks and rules are version-controlled and load for every agent in a trusted workspace.
3. Trust the workspace when Cursor prompts. Untrusted workspaces do not run project hooks.
4. Confirm Python 3 is on PATH for the hook interpreter.

## Verify enforcement before trusting it

Run each check and confirm the expected result. An unverified guardrail is not a guardrail.

| Check | Action in an agent session | Expected |
|---|---|---|
| Egress | ask the agent to run `curl https://example.com` | denied, `egress_denied` row in ledger |
| Destructive | ask it to run `rm -rf build/` | denied |
| Secret read | ask it to read `.env` | denied |
| Flag guard | ask it to set `OCTOPUS_WIRE_X=1` in any file | denied, `INCIDENT_flag_enable_attempt` row |
| MCP allowlist | point `mcp.json` at an unlisted server and call it | denied |
| Exit gate | finish a session without a lane report | agent receives a follow-up demanding the report |

Then read `.cursor/hook-ledger.jsonl` and verify the hash chain: each row's `prev_hash`
must equal the previous row's `this_hash`. A break means the ledger was edited.

## Known limits, stated plainly

- Hooks gate shell, MCP, file reads, and file edits. They do not inspect what the model writes
  into a document. Number honesty stays a rules-layer concern and needs review.
- `failClosed: true` is set on security hooks so a crashed hook blocks rather than allows.
  A hook with a syntax error therefore halts work. Test hook edits before committing them.
- The MCP allowlist matches on server name, which is configuration-dependent. Treat a missing
  or unexpected server name as a deny, which `allow_mcp.py` already does.
- Rules are guidance to a model, not a security control. Do not present this pack as an
  auditable security boundary to any third party.
