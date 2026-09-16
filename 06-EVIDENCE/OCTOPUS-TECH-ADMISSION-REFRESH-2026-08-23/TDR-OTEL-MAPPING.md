# TDR: OpenTelemetry GenAI semantic-convention mapping

Scope: **mapping only.** No collector, no backend, no `opentelemetry-*` package.
The moment an SDK is installed this record no longer covers the change — that needs its
own TDR with the full Dependency Admission Gate (pin + sha256, T-EXIT, rollback).

## 1. The naming trap — read this before touching anything

`OWNER-REPORT.md` refers to the mapping target as `[TYPED EVENT CONTRACT]`. There is a
file in this repo that looks exactly like that target and **is not it**:

> `04-SYSTEMS/TYPED-EVENTS.md` — frontmatter `status: phantom-name`.
> Body: *"این نام در گفتگو تولید شد، نه در مخزن. هیچ معادلی تعیین نمی‌شود (رأی مالک NEW-1، 2026-08-15)"*
> — this name was produced in conversation, not in the repo; **no equivalent is to be assigned**,
> by owner vote NEW-1 of 2026-08-15.

That file goes on to warn that the repo's real hash-chain ledger
(`src/nbb_cp/kernel/events.py`) must **not** be registered as the equivalent either,
because doing so would manufacture evidence.

**The real target is `_ops/cognitive/event_stream.py`.** Anyone mapping to
`04-SYSTEMS/TYPED-EVENTS.md` or to the `nbb_cp` ledger is violating a standing owner vote.
This paragraph exists so the next agent does not re-walk into it.

## 2. Measured problem

There is no measured problem. Nothing today is failing for want of OTel attribute names.

The honest framing: this is **speculative alignment** — making local event names resemble an
industry vocabulary so a future observability backend would be cheap to attach. That is a
legitimate goal, but under the Technology Admission Gate ("measured problem" is required),
it does **not** clear the bar for anything beyond a zero-cost rename layer.

## 3. What actually exists — and the coverage problem

`_ops/cognitive/event_stream.py:25-34` declares **25** event types.

Production emits **6**. Verified by tracing every non-test caller
(`git grep` over tracked `*.py`; only three files import `event_stream` at all — itself,
one producer, one consumer):

| Emitted in production | Where | Payload actually carried |
|---|---|---|
| `RUN_CREATED` | `run_store.create_run` via `start_run` | `metadata.text_digest` |
| `USER_MESSAGE_ACCEPTED` | `event_stream.start_run:69` | `text_digest`, `text_len` |
| `INTENT_DETECTED` | `collaborator.py:279` | `{"kind": ...}` + `intent` field |
| `MODEL_FINISHED` | `collaborator.py:290` and `:299` | `{"model_source": ...}` |
| `RESPONSE_COMPLETED` | `complete_run` via `collaborator.py:478` | `{"response_digest": ...}` |
| `RUN_COMPLETED` | `complete_run` via `collaborator.py:478` | — |

**Declared but never emitted in production (19):** `MODEL_STARTED`, `MODEL_TOKEN`,
`TOOL_REQUESTED`, `TOOL_STARTED`, `TOOL_RESULT`, `CLAIM_CREATED`, `CLAIM_VERIFIED`,
`PROPOSAL_CREATED`, `POLICY_DECISION`, `EXECUTION_RECEIPT`, `CONTEXT_RETRIEVAL_STARTED`,
`CONTEXT_RETRIEVED`, `MEMORY_FOUND`, `MEMORY_CANDIDATE_CREATED`, `RESPONSE_STARTED`,
`RUN_PAUSED`, `RUN_RESUMED`, `RUN_CANCELLED`, `RUN_FAILED`.

`MODEL_STARTED` and `RUN_FAILED` appear **only inside `_ops/tests/test_cognitive_events.py`**.
`fail_run()` has zero production callers — a failed run is never recorded as failed.

This is the vault's own recorded failure mode, twice over:
`feedback-tested-module-zero-callers` and `feedback-reason-from-what-production-loads`.
Reading `EVENT_TYPES` and mapping all 25 would produce a telemetry surface that is ~76% dead.

## 4. Consequences for the mapping

### (a) The highest-value OTel signal cannot be produced

OTel GenAI's core value is **model call duration** and token usage. Both are unobtainable here:

- **Duration** needs a start and an end. `MODEL_STARTED` never fires in production, so there
  is no start timestamp. `MODEL_FINISHED` alone is a point, not an interval.
- **Tokens** — `gen_ai.usage.input_tokens` / `output_tokens` are the report's named
  attributes. `MODEL_FINISHED`'s entire payload is `{"model_source": "..."}`. No token
  counts. (`context_engine.py` reportedly computes a tiktoken budget per
  `01 - Dashboard/HANDOFF.md` 2026-08-12, but that number is **not** carried into the event.)

So a faithful `gen_ai.*` mapping today emits spans with no duration and no usage — the two
fields that justify the convention.

### (b) There is no span identity

OTel is a **span** model: hierarchical, with `span_id` / `parent_span_id`, each covering an
interval. `run_store` records are **flat point-in-time rows**: `event_id`, `sequence`,
`run_id`, `trace_id`, `occurred_at`.

`trace_id` already exists and is genuinely useful — that part aligns. But there is no
`span_id`, no parent linkage, and no duration field. A real mapping therefore requires a
**schema change** to `run_store.append_event`, not a lookup table. That is materially more
than the report's "just add a mapping layer."

### (c) What aligns well — and it is not nothing

The privacy posture matches almost exactly. OTel GenAI captures prompt/completion content
as **span events, off by default**. This system **structurally cannot** carry raw content:
`run_store.append_event:99-104` strips `text`/`prompt`/`dm`/`content`/`raw`/`api_key`/
`token`/`secret` from every payload, and `test_cognitive_events.py::t_no_raw_text_persisted`
asserts it. The vault's redaction invariant is *stricter* than the OTel default and needs
no reconciliation. Worth recording: if OTel is ever adopted, content capture must stay off
permanently — not as a config default but as an invariant, since enabling it would silently
break `t_no_raw_text_persisted`.

### (d) The convention is beta

`OWNER-REPORT.md` itself notes GenAI conventions are still beta with experimental
attributes. Mapping to a moving target has a maintenance cost and no rollback urgency —
an argument for the cheapest possible version, not the complete one.

## 5. Honest mapping table (only what can actually be populated)

| Local event | OTel span / attribute | Populatable today? |
|---|---|---|
| `RUN_CREATED` + `USER_MESSAGE_ACCEPTED` | `invoke_agent` span start | Partially — start only, no end-to-end duration until terminal event is joined |
| `INTENT_DETECTED` | span attribute (no standard GenAI key) | Yes — custom attr, not `gen_ai.*` |
| `MODEL_FINISHED` | model-call span | **No** — no start, so no span; degenerate zero-duration point |
| `MODEL_FINISHED.model_source` | `gen_ai.system` (approx.) | Yes, loosely — `model_source` is a route label (`secondary:deepseek-v4-flash`), not a clean provider id |
| — | `gen_ai.usage.input_tokens` / `output_tokens` | **No** — not carried |
| — | `gen_ai.response.finish_reasons` | **No** — not carried |
| `TOOL_*` | `execute_tool` span | **No** — never emitted |
| `RESPONSE_COMPLETED` + `RUN_COMPLETED` | `invoke_agent` span end | Yes |
| `trace_id` | `trace_id` | Yes — already present, genuine alignment |

Net: of the report's three named attributes (`gen_ai.system`, `gen_ai.usage.input_tokens`,
`gen_ai.response.finish_reasons`), **one** is approximable and two are unavailable.

## 6. Why current is insufficient

It is not, for observability — nobody is currently unable to answer a question.

The real gap this investigation exposed is **not** naming. It is that instrumentation was
declared (25 types) and never wired (6). Renaming 6 events to `gen_ai.*` does not fix that;
it decorates it. **Fixing instrumentation coverage is the higher-value work and is
independent of OTel entirely.**

## 7. Options

| # | Option | Cost | Verdict |
|---|---|---|---|
| A | Do nothing now. Record the vocabulary intent; revisit when a backend is actually wanted | 0 | Defensible — no measured problem exists |
| B | Emit `MODEL_STARTED` + carry token counts into `MODEL_FINISHED`; **no OTel naming at all** | ~15 lines in `collaborator.py` + payload widening | **Highest value.** Buys real model latency + usage. Prerequisite for any future OTel work, and useful standalone |
| C | Add a pure translation function `to_otel_attrs(event) -> dict`, unused by default | ~40 lines, zero deps | Cheap, but maps mostly-absent data — decorates the gap in §6 |
| D | Install `opentelemetry-sdk` + collector | dependency + service | **Out of scope.** Requires its own TDR + full Admission Gate. Explicitly not recommended; report itself advises against |

## 8. Trial threshold

For **option B** (the recommendation): after wiring, a real owner-chat turn produces a run
whose events allow computing model wall-clock duration and non-null token counts, verified
by reading a live `state/cognitive/runs/<run_id>.jsonl` — **not** a fixture. Per
`feedback-probe-with-a-generous-fake-hides-the-silence`, the check must fail loudly when
the field is absent rather than defaulting to zero.

For option C, if taken: threshold is that `to_otel_attrs` has at least one production
caller. A translation function with zero callers is the exact anti-pattern in §3.

## 9. Rollback

Option B: revert one commit in `collaborator.py` + `run_store` payload allowlist.
Instrumentation is already wrapped in `try/except … pass` (`collaborator.py:283, 293, 303`)
so a failure degrades to silence rather than breaking chat. No state migration — existing
run JSONL files simply lack the new fields, and readers use `.get()` throughout.

Option C: delete the function; nothing calls it.

## 10. Recommendation

**Reject the mapping as framed; take option B instead.**

The owner report asks for a `gen_ai.*` mapping layer. Built today it would be a translation
of six events, two of whose three headline attributes cannot be populated, into a beta
vocabulary, for a backend nobody has installed. That is motion, not progress.

The finding underneath it is worth more: **19 of 25 declared event types never fire, and
model latency is unmeasurable because `MODEL_STARTED` is test-only.** Fix that first. It is
~15 lines, has a real measured payoff, needs no dependency and no vocabulary decision — and
if OTel is ever genuinely wanted, it is the unavoidable prerequisite.

---

```yaml
candidate: OpenTelemetry GenAI semantic-convention mapping (mapping layer only, no SDK)
observed_problem: "none for observability naming. REAL problem found underneath: 19 of 25 declared event types have zero production emitters; model latency unmeasurable (MODEL_STARTED is test-only); token counts not carried"
baseline_evidence:
  - "_ops/cognitive/event_stream.py:25-34 -- 25 EVENT_TYPES declared"
  - "_ops/owner_console/collaborator.py:279,290,299,478 -- the ONLY production emitter; emits INTENT_DETECTED, MODEL_FINISHED x2, complete_run"
  - "git grep: only 3 files import event_stream (itself, collaborator.py producer, miniapp_gateway.py consumer)"
  - "fail_run() has zero production callers -- RUN_FAILED never recorded in prod"
  - "MODEL_FINISHED payload is {model_source} only -- no tokens, no finish_reason, no start timestamp"
  - "_ops/cognitive/run_store.py:99-104 -- redaction strips text/prompt/content/raw/api_key/token/secret"
naming_trap:
  target_is: "_ops/cognitive/event_stream.py"
  target_is_NOT: "04-SYSTEMS/TYPED-EVENTS.md (status: phantom-name; owner vote NEW-1 2026-08-15 forbids assigning any equivalent)"
  also_NOT: "src/nbb_cp/kernel/events.py (unrelated financial-kernel hash-chain ledger; that file's own note warns against the conflation)"
new_dependency: none (mapping-only). Installing opentelemetry-sdk would require a SEPARATE TDR + full Dependency Admission Gate
technology_admission_gate: "not triggered as scoped; WOULD trigger for option D"
trial_threshold: "option B: a live owner-chat turn yields a run whose JSONL permits computing model wall-clock duration and non-null token counts, read from real state/cognitive/runs/<run_id>.jsonl, not a fixture; check must fail loudly on absent field rather than defaulting to 0"
rollback: "option B = revert 1 commit; instrumentation already try/except-wrapped (collaborator.py:283,293,303) so failure degrades to silence; no state migration, readers use .get()"
decision: REJECT_AS_FRAMED
counter_proposal: "option B -- wire MODEL_STARTED and carry token counts into MODEL_FINISHED. ~15 lines, no dependency, no vocabulary commitment. Real measured payoff and an unavoidable prerequisite for any future OTel adoption."
evidence_refs:
  - "_ops/cognitive/event_stream.py:25-34,60-71,98-104"
  - "_ops/cognitive/run_store.py:87-130"
  - "_ops/owner_console/collaborator.py:268-305,478"
  - "_ops/tests/test_cognitive_events.py:43-55,113-119"
  - "04-SYSTEMS/TYPED-EVENTS.md (phantom-name warning)"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/AUDIT.json"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/OWNER-REPORT.md"
status: DRAFT — awaiting owner/ari review. Not committed, not pushed.
date: 2026-08-23
```
