# LANE-REPORT — OCTOPUS-COMMANDER-W24-20260913

**GOV_VERSION=V8 · LADDER=L2 · DEFAULT=PROCEED (internal, non-TCB, reversible)**
**HOLD_EXTERNAL=true · customer_send=false · GO-B4=false · APPROVE_PAT not widened**
**PC side:** `F:\backup` @ `e247f3164d169898cdc35e597c531af8a23468c8` (branch `rescue/octopus-live-tree-20260821`)
**Runtime side:** `/home/ari/ofn` on DietPi `192.168.0.138` @ `63938eb01141030f6c9c56f8e1c51ec76e46458c` (branch `main`)
**Evidence bundle:** `00-SEASON/ziman-full-repair-20260910/OCTOPUS-COMMANDER-20260913/W24-CHAIN-FORENSIC.json`

---

## 1. What actually closed, and with which receipt

### CLOSED — FIX-1: the free-form self-repair path was 100% dead (import defect)

`coding_worker.process_patch_task()` called `import api_budget` with no `sys.path`
entry, while `api_budget.py` lives in the hyphenated directory `state/api-budget`
(not importable as a package). `paid_fallback()` carried the `sys.path` guard; the
free-form path did not. Every free-form patch task therefore died with
`ModuleNotFoundError` before reaching cognition — i.e. **GOV-FREEDOM-V2 §3, the
organism's ability to author and land its own fixes, had never run once.**

- sha256 before `82cce47aa2498ec9…` → after `f8c90b7ba48843cb9a12f37fe5a6cf667abb398a5daa789219803aa76a3b1f18`
- pre-image: `/home/ari/ofn/state/coding-worker/coding_worker.py.pre-import-repair-20260913`
- verified: `ast.parse` clean, guard precedes import, `import api_budget` resolves
- receipt: worker tick 09:33:18Z — the failure **advanced** from `ModuleNotFoundError`
  to the next real blocker, which is the proof the import now works.

### CLOSED — FIX-2: the coding worker could never spend, so the paid rung silently degraded

`octopus-coding-worker.service` had `ProtectHome=read-only` with
`ReadWritePaths=…coding-worker …canary-requests /tmp` — **omitting `state/api-budget`**.
`api_budget` could not append `budget-ledger.jsonl`, so every paid call raised
`EROFS`. Because `paid_fallback()` swallows exceptions and returns `None`, this
degraded to "no paid fallback" and was never reported anywhere.

- unit sha256 before `92ef105cd292aa05…`; pre-image `/etc/systemd/system/octopus-coding-worker.service.pre-rwpaths-20260913`
- `systemctl daemon-reload` applied; `ReadWritePaths` now includes `/home/ari/ofn/state/api-budget`
- **budget guard untouched:** `api_budget` enforces its own caps; a path-list entry grants no budget.
- receipt: worker tick **09:38:23Z → 09:38:25Z** produced
  `PATCH_REJECTED {provider: "deepseek"}` — a **real billed provider call**, then
  `TICK_COMPLETE`. That is end-to-end proof that cognition + provider + budget ledger now work.

### CLOSED — the inbound path is now measurable (GREEN telemetry)

`/home/ari/ofn/state/owner_dialogue/inbound_liveness.py` — read-only. Never confirms
a Telegram update, never moves an offset, never drains a queue. Emits
`state/owner_dialogue/inbound-liveness.json`. First measurement:

```json
{"verdict": "INBOUND_STALE", "glass_offset": "732409709",
 "glass_offset_last_moved": "2026-09-10T21:20:01Z", "glass_offset_age_s": 216621,
 "telegram": {"ok": true, "pending_update_count": 0, "webhook_url_set": false}}
```

**60.2 hours of silence that every other surface reported as healthy.** This is the
specific blindness that let the owner's replies vanish unnoticed.

### STAGED, NOT DEPLOYED — FIX-3: the W24 binder was a second Telegram poller

`go_b3_owner_bind.py` called `getUpdates` itself. `glass_runner.py` is the sole poller
and confirms every update, so the binder received **nothing, by construction**:
journal `{"spooled": 0, "offset": 0}`, `go_b3_tg_spool.jsonl` absent,
`owner_decision.v1.jsonl` absent, all 6 registry requests still `pending`.

Rewritten to consume the glass spool through its own durable cursor:
no `getUpdates` at all; durable-first (B3 spool fsync before the cursor moves);
idempotent (`source_text_sha256` dedupe against the decisions ledger);
fail-closed dispositions `REJECT_WRONG_SENDER / REJECT_MALFORMED / REJECT_REPLAY /
REJECT_EXPIRED / REJECT_AMBIGUOUS`. Dedicated B3 spool preserved.
`owner_reply.py` and `APPROVE_PAT` untouched (`ffa43a90…`).

- **16/16 stage tests green** (`stage/TASK-W24-BINDER-SPOOL-006/`, incl. an AST assertion
  that the module contains no `getUpdates` string and no `api.telegram.org` URL)
- sha256 `00dd4ef36204941a…` → `48be3f6193ab083ebd4f7896f0cc456249a85a0fa53677d7d08586691cc62edd`
- canary request `state/ops-agent/state/canary-requests/native-TASK-W24-BINDER-SPOOL-006.json`
  (deliberately **without** a `backup` key — see G2)
- pre-image `state/owner_dialogue/preimage/go_b3_owner_bind.py.00dd4ef36204941a.orig`
- **deploy gate: B8 is `BUDGET_NODE_24H` blocked** (`per_node_24h=2`, both slots spent
  01:49:08Z and 02:24:54Z). First free slot **2026-09-14T01:49:08Z**, with two requests queued ahead.

### RECONCILED, NOT RE-APPLIED — W25 and W27

Verified from the apply receipt **and** independent read-back, per the owner's
instruction not to re-apply without a provable cause. No cause was found. Nothing re-applied.

| artifact | expected sha256 | read-back |
|---|---|---|
| `state/owner_dialogue/hold_external_sot.v1.json` (W25) | `13a1e79fc56da0bd…` | **MATCH** on 138 |
| `state/self-model/OCTOPUS-SELF-DRIVE-20260913/W27-AGENTS-ALLOWLIST.json` (W27) | `86a1eb991030866b…` | **MATCH** on 138 |
| `F:\backup\AGENTS.md` | `577fdef0b8f8ed76…` | **MATCH** on PC |
| `state/revenue-drive/owner_reply.py` | `ffa43a90b8a99a3f…` | **MATCH**, unchanged |

One documentation imprecision, not a functional failure: the W27 apply receipt records
the bare filename `W27-AGENTS-ALLOWLIST.json` with no directory, so a naive
`state/self-model/W27-AGENTS-ALLOWLIST.json` read-back reports absent. The file is at
`state/self-model/OCTOPUS-SELF-DRIVE-20260913/`. W25/W27 status: **APPLIED**.

---

## 2. What was open, why, and who owns it

| id | item | why open | owner |
|----|------|----------|-------|
| **INBOUND** | Telegram delivers **zero** updates to `@Robo2725_bot` | no webhook set; `getWebhookInfo.pending_update_count = 0`; no cron, no hidden poller (the mesh bridge is a *fake* adapter, the watchdogs only manage the mount and the bridge unit). The update stream is simply empty. | **owner**: one fresh message is the only way to distinguish "owner has not written" from "Telegram is not delivering". |
| **FIX-3 deploy** | binder spool-consumer | canary budget serialised | organism (auto-deploys at `2026-09-14T01:49:08Z`+) |
| **G2** | B8 deploys the **pre-image** | `backup = req.get("backup") or req.get("patched")` | organism — `TASK-OPS-B8-CANARY-SRC-007` queued |
| **G1** | the coding worker cannot patch `ofn/agents/**` | `PATCH_ALLOW_ROOTS` = ops-agent, coding-worker, eti | **architecture decision** (widening a write scope is a gate change, so not self-granted) |
| **G3** | canary queue has no priority; sorted by filename | contract gap | contract change |
| **G4** | `check_awaited_canaries` verifies `OPS/target_file` | wrong for non-OPS targets | coding worker |
| **G5** | `per_node_24h=2` ⇒ ~1 class-B deploy/day | budget contract, never tuned to permit execution | **do not touch** |
| **G6** | `owner-decisions.jsonl` holds injectable test entries next to real decisions | hygiene | money lane |

### G2 is imminent and cheap to state precisely

The queued `native-B5-MEASURED-RECOVERY-001.json` carries
`backup = stage/B5-MEASURED-RECOVERY-001/ops_agent.py.bak` whose sha256 is
`71b8f0ad16aad893…` — **the live original** — and `target_sha256 = 77b809958d8562a8…`
— **the patched artifact**. Because B8 prefers `backup`, at 01:49:08Z it will
`cp` the original over the target and then fail sha256 verification. **The first
budget slot of the day will be spent on a no-op.**

---

## 3. What failed

- `TASK-OPS-B8-CANARY-SRC-006` — the organism worker picked it up on its own timer
  (09:27:48Z, 09:33:18Z, 09:38:23Z) and **rejected** it: the model returned text with no
  parseable JSON document (`PATCH_REJECTED provider=deepseek reason=NO_JSON_DOC`).
  The free-patch prompt is `json.dumps(context)` with no statement of the required
  `octopus.patch.v1` shape — the model is not told what to emit. Re-queued as
  `TASK-OPS-B8-CANARY-SRC-007` with an explicit `REQUIRED_OUTPUT_JSON_SCHEMA` and rules.
  This is a corrected task, **not** a blind retry.
- The owner's 17:53 and 18:22 AEST confirms: **`FAIL_NOT_SEEN`, unrecoverable.**
  Telegram holds no pending update, and a confirmed update is deleted server-side.
- The `E2E-TEST فقط تست` line in `tg-inbox.jsonl` (05:16:36Z) is **synthetic**:
  glass logged `answered=0 ignored=0` at that minute and its offset file still carries
  a 2026-09-10 mtime. It must never be counted as a delivered owner message again.

---

## 4. Evidence paths

- `00-SEASON/ziman-full-repair-20260910/OCTOPUS-COMMANDER-20260913/W24-CHAIN-FORENSIC.json` (full forensic, hashes, rollbacks)
- `00-SEASON/ziman-full-repair-20260910/GO-W24-BINDER-20260913/` (prior pass: RECEIPT, SEC post-deploy, LIVE-INGEST-PROVE)
- `00-SEASON/ziman-full-repair-20260910/OCTOPUS-SELF-DRIVE-20260913/` (W-numbering source: MISS-SCAN, ORGANISM-QUEUE, GO-W25-W27-APPLY)
- 138: `state/coding-worker/state/coding-receipts.jsonl` (hash-chained worker receipts)
- 138: `state/owner_dialogue/inbound-liveness.json`, `state/owner_dialogue/preimage/`
- 138: `state/coding-worker/stage/TASK-W24-BINDER-SPOOL-006/` (patched module + 16 tests)

## 5. Rollback steps

```bash
# FIX-1
cp /home/ari/ofn/state/coding-worker/coding_worker.py.pre-import-repair-20260913 \
   /home/ari/ofn/state/coding-worker/coding_worker.py
# FIX-2
sudo cp /etc/systemd/system/octopus-coding-worker.service.pre-rwpaths-20260913 \
        /etc/systemd/system/octopus-coding-worker.service && sudo systemctl daemon-reload
# FIX-3 (if it ever deploys)
cp /home/ari/ofn/state/owner_dialogue/preimage/go_b3_owner_bind.py.00dd4ef36204941a.orig \
   /home/ari/ofn/ofn/agents/go_b3_owner_bind.py
```

## 6. Autonomy loop — what the organism did by itself

Every one of these was the **organism's own timer**, never a manual trigger:

| time (UTC) | what the organism did on its own |
|---|---|
| 09:27:48 | picked up the author-supplied task from its queue and started it |
| 09:33:18 | retried, and its failure **located** the sandbox defect (`EROFS` on the budget ledger) |
| 09:38:23 | ran again and **made a real billed provider call** (`deepseek`) |

The queue itself was **empty** before this session — the worker was ticking
`NATIVE_CODING_IDLE_HEALTHY` every ~5.5 min with nothing to do. A healthy worker with
an unfeedable queue is not autonomy; feeding that queue is now demonstrably the
highest-leverage action available.

## 7. Honesty notes

- No test was deleted, renamed, skipped or xfailed. No live-ledger entry was written for a controlled test.
- Code+tests, deployment, runtime effect and capability grade are reported separately, never merged.
- Grades: FIX-1 **E2**, FIX-2 **E2**, FIX-3 **E2 on stage tests / E0 in production**.
  No E4/E5 is claimed anywhere.
- `hold_external=true`, `customer_send=false`, no GO-B4, no retroactive bind, no APPROVE_PAT widening.
- The binder fix is **not** reported as deployed, and the owner's replies are **not** reported as received.

---

## 8. Round 2 — the two owner decisions, executed

### DECISION 1 — open the worker's write scope (`باز کن به ofn/agents`) — EXECUTED

`PATCH_ALLOW_ROOTS` now includes `/home/ari/ofn/ofn/agents`, **and in the same change**
`PATCH_DENY_MARKERS` gained `recovery-contract`, `witness_verifier`, `supervisor.py`.
Widening the root without tightening the deny list would have opened the TCB by the side
door, because the free-form path never consulted `_TCB_TARGETS` (only the enum path did).

- `f8c90b7ba48843cb…` → `f9d8794d89dcd13e…`
- pre-image `state/coding-worker/coding_worker.py.pre-agent-scope-20260913`
- **10/10 path cases verified:** `ofn/agents/go_b3_owner_bind.py` and `ofn/agents/glass_runner.py`
  ALLOWED; `supervisor.py`, `witness_verifier.py`, `witness-pins.json`, `tcb-manifest.json`,
  `recovery-contract.json`, `state/autonomy/supervisor.py`, `state/api-budget/api_budget.py`
  and a `../` traversal all still **DENIED**.

### DECISION 2 — put the B8 repair first (`تعمیر B8 را اول بگذار`) — EXECUTED

The repair: `backup = req.get("backup") or req.get("patched")` → `backup = req.get("patched") or req.get("backup")`.
Exactly **one line**: 2 diff lines, byte size unchanged (35777), and all **774 CRLF endings preserved**
(staged with `read_bytes`/`replace`/`write_bytes` — see G10 below, this mattered).

Queue order now:

```
native-A-B8-DEPLOY-SOURCE-008.json      <- deploys Sep 14 01:49:08Z
native-A2-W24-BINDER-SPOOL-006.json     <- deploys Sep 14 ~02:25Z
native-B5-MEASURED-RECOVERY-001.json
native-TASK-OPS-BUDGET-CATSCOPE-005.json
```

**Disclosure:** promoting the W24 binder to second place pushes B5 and CATSCOPE each **one day**
later. Said out loud rather than done quietly.

### G10 — a systemic staging defect found while doing this

`ops_agent.py` is **mixed-CRLF**: 774 CRLF lines, and its raw byte sha256 (`71b8f0ad…`) differs
from the sha256 of its text-mode re-encoding (`481b1393…`). Any artifact staged through text IO
therefore **normalises every line ending**, turning a small semantic change into a whole-file
rewrite. Measured across the three staged `ops_agent.py` artifacts, **two of three** had
`crlf=0` against a live file with 774:

| artifact | crlf before | crlf after | semantic diff vs live |
|---|---|---|---|
| B5-MEASURED-RECOVERY-001 | 0 | 800 (=774+26) | 28 lines |
| TASK-OPS-BUDGET-CATSCOPE-005 | 0 | 778 (=774+4) | 10 lines |
| TASK-OPS-B8-CANARY-SRC-008 (mine, byte-staged) | 774 | 774 | 2 lines |

All three were **re-based in byte mode**, with the semantic line list verified byte-identical
to the original staging, and each canary request updated with its new `target_sha256`.
The `backup` key was also removed from the B5 request so it deploys the patch rather than the
pre-image even if the handler fix were delayed. All four queue entries now parse `PARSE_OK`.

**This is the same CRLF trap already recorded in memory for deploy-byte hashes — it is not
hypothetical, it had already corrupted two of four queued deploys.**

### G9 — the ops-agent manifest is not enforced

`state/ops-agent/ops-manifest.json` pins sha256 for `ops_agent.py`, `ops_budgets.json` and
`ops_contracts.json`, but **no code in the tree reads it** (grep for `ops-manifest` /
`OPS_MANIFEST` finds no consumer). The pin is documentation, not enforcement.

---

## 9. Round 3 — G8 isolation, queue composability, and the real cause of G7

Evidence: `00-SEASON/ziman-full-repair-20260910/OCTOPUS-COMMANDER-20260913/ROUND2-G8-QUEUE-FORENSIC.json`

### B — G8 CLOSED IN DESIGN AND PROOF (not deployed: class-B quota)

The producer wrote every allow-listed owner message into one spool that fed **two** consumers
with different semantics. The fix routes on the **validated identity of the request** — a hash
resolving to a known B3 card — never on vocabulary, because the sender chooses the words.
Card-confirm-shaped messages with an unresolvable hash also go to the B3 lane, fail-closed.
`owner_reply.py` (`ffa43a90…`) and `APPROVE_PAT` are untouched.

**Acceptance (`g8-accept.py` on 138): `G8_ACCEPTANCE: PASS`**

- 13/13 B3-shaped inputs routed to the B3 lane — including `بفرست <full hash>` and
  `ارسال <full hash>`, the two cases that could previously reach `execute_money_batch`
- **money lane received 0 messages**
- **counters: `execute_money_batch` 0, `prepare_channel_assets` 0, `record_rate_card` 0**
- control: a plain `بفرست` still routes to MONEY and is still seen by the money consumer

My own test caught a real hole: the first router version decided on conflict-language
vocabulary, so `بفرست <hash>` still went to money. Identity-first is the correction.

Two other defects surfaced while building this:

- **G13:** `glass_runner` used `pathlib.Path(...)` while importing only `Path`, inside a blanket
  `except Exception: pass`. **The owner-message spool write has never once executed.** Fixed in
  the same change, and the silent swallow now emits a receipt instead.
- **G14/G15/G16** — see §E.

### C — DEPLOY QUEUE: a real composability defect, fixed and proven

B5 and CATSCOPE still carried the pre-fix `req.get("backup")` line, so **each would have reverted
the B8 fix** and put the pipeline back to "deploy the pre-image". Both were also text-mode staged
(`crlf=0` against a live file with 774).

Chain rebuilt from the live bytes in byte mode, each element based on the preceding output:

```
live 71b8f0ad -> B8 5940ed32 -> B5 4d4b6e95 -> CATSCOPE ec01f551   (ops_agent.py)
live 00dd4ef3 -> W24 binder c0941968                                (go_b3_owner_bind.py, independent)
```

- **COMPOSITE: PASS** — base, artifact sha and post sha all match at every step; B8, B5 and
  CATSCOPE changes all survive in the final artifact; it parses
- **B8 handler logic: 9/9 PASS** — patched+backup deploys *patched*; stale base gives
  `OPS_B_STALE_BASE`, takes no action and stays queued; absent artifact no-ops; TCB target
  becomes an owner task; budget block no-ops; the pre-image is never the candidate
- The B8 fix now also **verifies `base_sha256` before overwriting**, so a stale candidate can no
  longer overwrite a newer accepted change

### E — G11 first, and it settled G7

G11 records model, provider, `resp_len`, `resp_sha256`, `finish_reason`, `truncated`, parser,
stage and a **redacted** 240-char excerpt. Fixture test PASS (10/10 redaction cases).

**On its first real run it returned `resp_len: 0` — the paid reply was empty.**

**G7 is therefore REFUTED, append-only.** The earlier claim was "the free path has no prompt
contract". Task 007 already carried an explicit schema and still produced nothing; there was
never any text to parse. The prompt contract was never the binding constraint.

Running it exposed three further defects, each fixed and then exercised by the real worker:

| id | defect | status |
|----|--------|--------|
| **G14** | `paid_call` settles an empty reply as `insufficient-or-empty` with `response_sha256 = sha256(b"")` **and still returns `ok: True`**, so the caller never falls back | fixed **at the caller**, leaving the money broker untouched |
| **G15** | `cognition_request` read `task["output_contract"]` with no default, so the fallback raised `KeyError` and killed the tick | fixed |
| **G16** | **the root cause.** The node-180 broker returns `{ok, proposal, model, tokens, cost_usd, receipt, …}` — **there is no `text` key.** The free path does `resp.get("text","")`, so it always gets `""`. The free-form patch path has never had a working cognition source. | **open** |

Proof of G16, by direct broker probe (free, local): `proposal={'method':'split','confidence':0.9}`,
`tokens=17`, `cost_usd=0.0`, no `text` key at all.

End-to-end evidence from the organism's own timer:

```
10:16:34 TASK_STARTED   TASK-OPS-QUEUE-PRIORITY-009
10:17:18 COGNITION_RESPONSE  model='qwen3-0.6b-q4_0 (local llama.cpp, node 180)' tokens=658
10:17:18 PATCH_REJECTED      provider='local-llamacpp-180' reason='EMPTY_COGNITION_REPLY'
```

The wiring is repaired and the diagnostics work. **What remains is that no cognition route
returns free-form text.**

### D — the sandbox boundary was wider than intended, and is now narrowed

The previous round added `ReadWritePaths=/home/ari/ofn/state/api-budget`. A sandbox probe with the
real UID under the real directives returned **`CODE_WRITABLE`** — the worker could rewrite the
broker's **code**, not just its ledger. That is exactly the "a patch deny-list is not a real
access restriction" risk.

Narrowed to the ledger file and the config directory, pre-image
`octopus-coding-worker.service.pre-narrow-20260913`, `daemon-reload` applied. Re-probe:

```
CODE_DENIED   LEDGER_OK   CONFIG_OK
```

`G9` remains open as a finding: the ops-agent manifest pins hashes that nothing reads.
`G4` (`check_awaited_canaries` verifies `OPS/target_file`, wrong for any non-OPS target) is
recorded and prepared but not fixed.

### F — how far the end-to-end path got

Durable queue → worker (the organism's own timer, no manual trigger) → cognition → diagnostics →
disposition, all traversed. The path stops at "patch valid" because **G16** means no route
returns free-form text. Deployment could not be reached: class-B quota reopens
`2026-09-14T01:49:08Z`.

### Still open, with owners

| item | why | owner |
|------|-----|-------|
| **G16** | 180 broker answers in `proposal`, never `text` | **owner decision** (below) |
| **G8 deploy** | class-B quota | organism, from `2026-09-14T01:49:08Z` |
| **W24 + B8 + B5 + CATSCOPE deploy** | same quota, 5 queued | organism |
| **INBOUND** | Telegram delivers nothing; offset frozen since 2026-09-10T21:20:01Z | owner: one fresh message, **after** G8 lands |
| **G4 / G9 / G12** | verifier path, unenforced manifest, one file per budget slot | organism / contract |
| **G14 broker half** | paid broker reports a known-bad reply as `ok: True` | owner decision |

---

## 10. Round 4 — evidence hygiene, G16 contract, and where it actually stops

Evidence: `OCTOPUS-COMMANDER-20260913/ROUND3-G16-CONTRACT-FORENSIC.json`

### §1 — the bundle is now machine-readable

`ROUND2-G8-QUEUE-FORENSIC.json` was **invalid JSON**: it used Python implicit string
concatenation inside a tuple at line 41. No consumer could parse it. Six such blocks were
joined and the tuple parens dropped by a line-based state machine, then re-serialised with
`json.dump`. The original is **preserved byte-for-byte** (`f5baf2e5…`); the corrected
`…-v2.json` (`ac722814…`) carries a `supersedes` block with both hashes. Validated
independently by `json.tool`, `node JSON.parse` and `json.loads`; content spot checks all pass.
A `.json` extension was never evidence — parsing it is.

### §2 — G16 is a contract gap, not "no cognition ever worked"

Extracted contract of the node-180 broker: input requires all five of `schema/task_id/purpose/
prompt_context/output_contract`; the envelope returns `proposal` and **no `text`**; the scan is
`re.finditer(r"\{[^{}]*\}")` — **flat only**, so a nested patch document can never match; and
`llm_complete` hard-codes `stop:["\n"]`, making multi-line output impossible by construction.

That is a **missing mode, not a missing capability** — the broker already had prompt assembly,
sanitisation, budgets, receipts and a single-job lock. No `json.dumps(proposal)` adapter was
written. The enum path and `autonomy_battery` both use the proposal contract daily, so the
"nothing ever worked" generalisation is **withdrawn**.

**Change (opt-in, default preserved):** `mode: "proposal" | "patch"`; `stop` becomes a
parameter; a balanced `first_json_object()` is used only in patch mode; the envelope gains
`mode`, `transport_ok`, `usable_output`, `empty`, `truncated` and — in patch mode — `text`.
Output remains a **proposal** with `executable: false`.

- `dbd3a50e…` → `970e49ca…`, pre-image `cognition_broker.py.pre-mode-20260913`
- **`BROKER_CONTRACT_PROBE: PASS` (5/5)** — default mode keeps all 9 historical keys and leaks
  no `text`; patch mode returns 8279 chars of usable text; `UNSUPPORTED_MODE` and the two
  `SCHEMA_INVALID` regressions all still fail closed

### §3 — the paid option stayed separate, and spend stayed bounded

The caller still refuses to count an unusable paid reply as success (G14). This round the paid
fallback was refused with `PAID_DUPLICATE_PROMPT`, so a failed local route did **not** become
unbounded paid calls. The paid-empty cause remains **separate and unproven** — the settle row
shows `response_sha256 == sha256(b"")`, `retained=false`, `insufficient-or-empty`,
`billed_tokens=2183`, but the provider envelope was never instrumented, so no claim is made and
no retry was spent.

### §8 — how far the organism actually got, and exactly why it stopped

```
10:39:48  TASK_STARTED            TASK-OPS-QUEUE-PRIORITY-009   (organism's own timer)
10:41:48  COGNITION_FAIL_CLOSED   rc=2  MODEL_UNAVAILABLE: "timed out"
10:41:48  PAID_FALLBACK_REJECTED  PAID_DUPLICATE_PROMPT
```

**G18 (new):** patch mode removes the newline stop, so `qwen3-0.6b` generates past the broker's
120 s `inference_timeout_seconds` and the call times out. The contract works; generation does not
finish. Recommended bounded fix: ask for one **compact single-line JSON** and keep
`stop:["\n"]` — smallest change, keeps the historical stop semantics, verifiable with the same
probe suite. No text, no `tokens>0` and no HTTP success is counted as patch-authoring ability.

### Carried forward, NOT closed

§4 (G8/W24 activation matrix and the `G4` verifier fix), §5 (extended ambiguous-input
acceptance), §6 (Telegram ack ordering under injected write failure) and §7 (naming the writable
config paths precisely, rather than the blanket `CONFIG_OK`) are **open**. They are listed here
as outstanding work, not as done.



