---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# PASS 1 — Security Reviewer: IGK Kernel

Role: adversarial security reviewer of the Immutable Grounding Kernel. Scope: kill-switch
reachability, permit-logic bypass, secrets handling, prompt-injection surface reaching an LLM,
and the kernel↔agent separation boundary. Repo root abbreviated as `.../fusion-mvp`.

## Architecture as built (evidence)

- Kernel logic lives in `igk/kernel.py` (`class Kernel`). It is hosted as a **separate OS
  subprocess** by `igk/daemon.py` (spawned in `igk/client.py:14-20` via `subprocess.Popen`).
  The signing key exists only inside that process (`igk/kernel.py:43-54`).
- The ecology side holds only `KernelClient` (`igk/client.py:12-41`) and `ActuationGate`
  (`igk/client.py:48-61`). It talks to the kernel over a line-delimited JSON stdin/stdout
  protocol; it does **not** hold the key. This is a genuine process-level trust boundary. [Certain]
- Governed agents (`src/agents.py`) do **not** import `igk` at all; only `src/orchestrator.py`
  imports the client (`src/orchestrator.py:26-31, 44-45`). Agents cannot reach the kernel
  directly. [Certain]
- The kernel protocol has a fixed verb allow-list (`igk/daemon.py:13`
  `VERBS = {"audit","verify","permit","consume","ground","canon","ping","status"}`). There is
  no verb to set the key or mutate an invariant; red-team test #4 confirms this
  (`igk/test_redteam.py:55-59`, ran green). [Certain]

## Findings

### P1-01 [High] IGK silently degrades to cooperative mode on any spawn error (fail-OPEN)
`src/orchestrator.py:42-49`:
```
if self.use_igk:
    try:
        from igk.client import KernelClient, ActuationGate
        self.kernel = KernelClient(...); self.gate = ActuationGate(...)
    except Exception as e:
        print(f"  ⚠️ IGK در دسترس نیست، بازگشت به cooperative: {e}")
        self.use_igk = False
```
A broad `except Exception` converts **any** kernel-spawn failure (bad interpreter path, corrupt
`daemon.py`, OS process-limit exhaustion, import error) into a silent downgrade. Once
`self.use_igk = False`, the final actuation gate is skipped entirely
(`src/orchestrator.py:130` `if self.use_igk and self.gate is not None:`) and so is the grounding
call (`:114`). The system's headline property — "external, mechanical, fail-closed enforcement"
(`igk/README.md:6-9`) — is lost with only a console warning. The in-process `KillSwitch` and the
HITL gate remain as backstops, so this is High rather than Critical, but it is a silent security
downgrade of the primary control. Existence of the code path: [Certain]. Attacker-inducibility of
the spawn failure from inside the process: [Probable].

### P1-02 [High] Audit integrity depends on key *continuity*; deleting the key enables a clean forge
`igk/kernel.py:43-54` `_load_or_make_key()` **creates a fresh random key** if `.kernel_key` is
absent. `verify()` (`igk/kernel.py:86-100`) checks each record against the *current* key. An
attacker with filesystem access who deletes `.kernel_key`, then writes a brand-new audit chain and
lets the kernel regenerate a key, produces a chain that `verify()` reports as fully valid — because
it is self-consistent under the new key. There is no external key attestation, no key fingerprint
recorded off-box, and no rotation record. Red-team test #1 only proves that forging a single line
*without* the key fails (`igk/test_redteam.py:29-36`); it does not cover key deletion + full
rewrite. [Probable] (single-machine, same-user threat model). Note: the real `.kernel_key` was
moved out today (`logs/igk_state/MOVED - .kernel_key.md`), so the next run will regenerate a key
and the existing `logs/igk_state/audit.jsonl` (7 records) will no longer verify — expected, cited
as context, not a finding.

### P1-03 [Medium/High] Key isolation is process-level only (self-admitted, but it is the crux)
`igk/kernel.py:41-42` and `igk/README.md:17-18` state plainly that on one OS user any process with
raw file access can read `.kernel_key`; real isolation needs OS-user separation / TEE. Today no
governed agent has a filesystem tool (`src/tools.py:24-26` registers only `web_search_mock`), so
the boundary is not *currently* reachable by an agent. The risk is latent: the moment any file /
shell / code-exec tool is added to `TOOLS`, an in-process agent can read the key and forge both
permits and audit records, routing around the entire kernel. [Certain] that the boundary is
process-level; [Guess] on future tool additions.

### P1-04 [Medium] Grounding gate is advisory by default and mis-wired to the wrong text/domain
`config.py:59` sets `GROUNDING_REQUIRED = False`, so `src/orchestrator.py:118` never blocks
finalize in the default configuration — grounding ratio is printed only. Worse, when enabled it
validates `findings.splitlines()` (raw Researcher output, `src/orchestrator.py:115`) against a
held-out set of geography/science facts (`igk/held_out.json`). Normal Researcher output (topic
summaries, and in MOCK the fixed lines in `src/llm.py:56-62`) shares no subject with those facts,
so every claim scores `unverifiable` and the ratio is ~0.0 — confirmed by the persisted record
`logs/igk_state/audit.jsonl` seq 1 (`ratio: 0.0`). Consequence: turning the gate on would halt
essentially every real run, which is why it ships disabled. The grounding control is therefore
effectively inert. [Certain]

### P1-05 [Medium] Two kill-switch mechanisms are not unified; programmatic trip is invisible to the orchestrator guard
`src/orchestrator.py:73-79` `_kguard()` consults only `kernel.status()` (external STOP **file**)
when IGK is active and does **not** call `self.ks.check()` in that branch. The in-process
`KillSwitch.trip()` (`src/killswitch.py:26-28`), which `src/killswitch.py:5` and `README` say
`supervisor`/`budget` may use, is thus ignored at the orchestrator step boundary under IGK. It is
still honored inside `Agent._think` (`src/agents.py:41`) and `Judge.vote` (`src/panel.py:45`), and
no production code currently calls `trip()`, so the impact is latent — but the two stop paths
(in-memory flag vs. external file) are not coherent. [Certain]

### P1-06 [Low/Medium] STOP is honored at checkpoints, not "instantly"
README claims immediate stop ("آنی", `README.md:13,49`). In practice STOP is polled at each
`_kguard`, `ks.check`, `permit`, and `consume`. A long synchronous LLM call (`src/llm.py:40-45`,
blocking) cannot be interrupted mid-flight; STOP takes effect at the next boundary. Bounded latency,
not unbounded, but the "instant" claim is overstated. [Certain]

### P1-07 [Medium] `config` is a mutable module used as live kernel configuration
Kernel state location is read from `config.IGK_STATE_DIR` / `config.STOP_FILE` at Orchestrator
construction (`src/orchestrator.py:36,45`). Tests reassign these at runtime
(`test_igk_integration.py:20-23`). Any in-process code that can set `config.IGK_STATE_DIR` before a
new Orchestrator is built can relocate the kernel to an attacker-owned state dir (attacker
`held_out.json`, `audit.jsonl`, and a self-owned `.kernel_key`). The running kernel's `stop_path`
is fixed at spawn, so this does not disable STOP for an already-running kernel, but it poisons
grounding and audit for the next run. [Probable]

### P1-08 Prompt-injection surface reaching an LLM
Data flow into LLM calls (LIVE mode, `src/llm.py:37-52`): user `topic` → Researcher system+prompt
→ tool `web_search_mock` (returns fixed text, ignores content, `src/tools.py:17-21`) → Analyst →
Panel judges. Key observation: **the panel's approve/reject decision does not use the LLM output at
all** — `Judge.vote` calls the provider (`src/panel.py:48-49`) but discards `res.text` and decides
via Python string heuristics `_decide()` (`src/panel.py:33-42`). Likewise the Supervisor's
LLM-derived verdict (`src/agents.py:78-86`) is dead code (orchestrator uses the panel, not
`supervisor.review`). Net: injected text cannot flip control flow through the panel/supervisor
(robust, good), but it *can* poison the delivered `findings`/`analysis` content, which only passes a
keyword guardrail (`src/guardrails.py:11-21`). Control-flow injection risk: Low. Content-integrity
injection risk: Medium. [Certain] on the discard/dead-code; [Probable] on content poisoning impact.

## Kill-switch reachability summary
External STOP file: reached by kernel `permit` (`igk/kernel.py:107`), kernel `consume`
(`igk/kernel.py:129`), orchestrator `_kguard` (`:76`), agent `ks.check` (`src/agents.py:41`), judge
`ks.check` (`src/panel.py:45`). Coverage of the external file is good and fail-closed. The gaps are
P1-05 (in-memory trip) and P1-06 (checkpoint latency).

## Gaps I could not verify
- LIVE-mode kernel behavior end-to-end (no API key; sandbox offline). The real-provider branch is
  unexercised.
- OS-level key isolation (single-machine assumption; not testable here).
- Contents of `.kernel_key` / `.env` — intentionally not read (moved out today).
