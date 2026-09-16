# TDR: DBOS-style durable Run Store

`OWNER-REPORT.md` recommends: *"a small DBOS-style TRIAL on existing Postgres"* for the
Run Store, as the lighter alternative to Temporal.

**The premise is false. There is no Postgres in this stack.** And the durable-execution
capability the trial would buy is already implemented — three times, in three namespaces.

## 1. The false premise

`git ls-files | grep -iE "postgres|psycopg"` over the whole tree returns **two** files, both
archived n8n/Flowise tool definitions under `_archive-binaries/`:

```
_archive-binaries/04 - Architect System/architect/local-ai-packaged1/flowise/get_postgres_tables-CustomTool.json
_archive-binaries/04 - Architect System/architect/local-ai-packaged1/n8n-tool-workflows/Get_Postgres_Tables.json
```

No driver, no connection string, no schema, no service. Per the vault constitution
`_Archive` is a transfer destination only.

DBOS Transact's entire value proposition is that it stores workflow state in **your existing
Postgres, in the same transaction as your business writes**. With no Postgres, "DBOS-style
on existing Postgres" is not a light trial — it is *adopt Postgres, then adopt DBOS*: a new
service, a new dependency, a new backup/rotation surface, on a single-operator Windows
laptop whose recorded bottleneck is a mechanical disk
(`feedback-recursive-scan-hangs-this-laptop`).

That is strictly heavier than the Temporal option the report rejects for being heavy.

## 2. Durable execution already exists — three times

`TDR-TEMPORAL.md` (2026-08-12) justified REJECT with:
*"DBOS/journal/checkpoint/replay exists in evidence_plane/event_log + policy_gate."*

**That citation is wrong**, and I am correcting it rather than inheriting it.
`evidence_plane/event_log.py` has no checkpoint and no replay — it has `append_event` and
`read_events`, plus `checkpoint_id` as an *optional field you pass in*. `policy_gate.py` is
a pure decision function with no persistence at all.

The REJECT verdict was right. The stated evidence was not. The real implementations are
elsewhere:

| # | Module | What it durably answers | Storage | Live? |
|---|---|---|---|---|
| 1 | `_ops/durable_journal.py` | *"where do I resume from?"* — `record(run_id, step, status)`, `resume_point()`, `incomplete_runs()` | `state/journal/run-journal.jsonl` | **Yes** — producers `doctor.doctor._journal` (propose/sandbox/submit) + consumer `journal_recovery.boot_recovery`, both wired since 2026-07-23 |
| 2 | `_ops/checkpoint.py` | *"what did state look like at beat N?"* — `checkpoint()`, `replay()`, `replay_state_at()` | genome ledger + `chrono.db` | Partly — `checkpoint()` returns `False` when `db is None` (the default), so it is a fail-soft no-op unless a db is injected |
| 3 | `_ops/cognitive/run_store.py` | *"what happened during chat run X?"* — `create_run`, `append_event`, `list_events` | `state/cognitive/runs/<run_id>.jsonl` | **Yes** — one producer (`collaborator.py`), one consumer (`miniapp_gateway.py`) |
| 4 | `_ops/evidence_plane/event_log.py` | forensic audit trail (ADR-033) | `state/adr-033/events/<day>.jsonl` | Yes |

`durable_journal.py`'s own docstring already makes the distinction the report is reaching for,
and cites the same 2026 research lineage (Inngest, MS Durable Task, Diagrid, Temporal):

> `checkpoint` = *"state کجاست"* (where state is)
> `durable/run-journal` = *"چه‌طور امن جلو برویم / از کجا دوباره شروع کنیم"* (how to move forward safely / where to resume)

**Adopting DBOS would make this the fifth overlapping mechanism.** The problem is not
absence of durable execution. It is that four partial implementations sit in four
namespaces with no unifying contract — and `run_id` does not even mean the same thing
across them (`durable_journal` run_ids are doctor RFC steps; `run_store` run_ids are
`run_<hex12>` chat turns).

## 3. The one real, measured defect — and it is not what the report asked about

`_ops/cognitive/run_store.py:87-130`, `append_event`:

```python
events = _read_jsonl(_run_path(run_id))          # read ENTIRE run file
max_seq = max((e.get("sequence", 0) for e in events), default=-1)
seq = max_seq + 1                                 # compute next
...
_append_jsonl(_run_path(run_id), rec)             # append
```

Two independent defects:

**(a) Read-modify-write race, unguarded.** No lock — not a file lock, not even an in-process
one. Two concurrent appends to the same `run_id` compute the same `max_seq` and both write
`seq = N`. Sequence uniqueness is silently violated. The module's own header is candid:
`DURABILITY = "PROCESS_DURABLE"  # فایل روی دیسک ولی no cross-process guarantee`.
This is the same class as the recorded incident in
`feedback-inprocess-lock-doesnt-stop-a-second-process` (approvals.json clobbered) — except
here there is no lock at all.

**(b) O(n) per append.** Every single event re-reads and re-parses the whole run file.

**Both are currently latent, and I want to be precise rather than alarming:** run files are
per-`run_id`, and a single chat turn appends sequentially from one thread, so today nothing
triggers either. Concurrent turns write to *different* files.

They stop being latent the moment any concurrent or high-frequency producer writes to one
`run_id`. Two concrete near-term features would do exactly that:
- real SSE streaming (`TDR-SSE-O-E4.md` option B) — a background thread emitting while the
  main thread appends;
- `MODEL_TOKEN` per-token events (declared in `EVENT_TYPES`, never emitted) — a 500-token
  response becomes 500 appends, each re-parsing a growing file: ~125,000 line-parses for one
  reply.

The test suite cannot see this. `test_cognitive_events.py::t_sequence_monotonic` and
`t_duplicate_run_id_idempotent` both assert sequence integrity **single-threaded only**.
No concurrent-append test exists — `feedback-suite-can-pin-the-very-bug`.

**Neither defect is fixed by DBOS, and neither needs it.** (a) is a file lock or an
`O_APPEND` + monotonic counter; (b) is caching `max_seq` in memory or tracking it in a
sidecar. Both are tens of lines, zero dependencies.

## 4. Why current is insufficient — honestly scoped

For the chat Run Store's actual job (record a turn, let the owner replay its timeline):
**it is sufficient**, with the two latent defects above.

It is genuinely insufficient for:
- crash-mid-turn resume — `run_store` has no `resume_point` equivalent. But
  `durable_journal.py` already implements exactly that and is simply not wired to chat runs.
  That is an integration gap, not a missing technology.
- cross-process concurrent writes — see §3, fixable locally.

## 5. Options

| # | Option | Cost | Verdict |
|---|---|---|---|
| A | Adopt Postgres + DBOS as the report proposes | New service + new dependency + backup/rotation surface, on a mechanical-disk laptop | **REJECT.** False premise; strictly heavier than the Temporal option the report itself rejects |
| B | Fix the two real defects in `run_store` (lock + cached `max_seq`) | ~20-30 lines, stdlib, no deps | **Recommended.** Addresses the only measured problem found |
| C | Wire `durable_journal.record/resume_point` into chat runs for crash-resume | ~15 lines; module is live and proven | **Recommended if** crash-mid-turn resume is actually wanted. Reuses existing, already-wired machinery |
| D | Unify the four mechanisms behind one contract | Large; touches doctor, chrono, cognitive, evidence_plane | **DEFER.** Real long-term debt, but needs its own design pass and a measured trigger — not this record |
| E | Do nothing | 0 | Acceptable — nothing is failing today |

## 6. Trial threshold

No trial is authorized, because no technology is being admitted. If the owner nonetheless
wants option A explored, the gate must be cleared *before* any install, and the first
question is not a benchmark but: **why does this stack need Postgres at all?**

For option B (the recommendation), the acceptance bar is a *failing-first* test:
spawn ≥2 threads (and ideally ≥2 processes, per the recorded lesson that threads alone do
not reproduce it) appending to one `run_id`; assert zero duplicate sequences. That test must
**fail against today's code** before the fix lands — otherwise it is pinning the bug rather
than catching it (`feedback-green-mutation-means-unwatched`).

## 7. Rollback

- Option B: revert one commit. Storage format is unchanged (still append-only JSONL);
  existing run files stay readable either way. No migration.
- Option C: revert one commit; `durable_journal.record` is absolute fail-soft
  (`except: pass`, lines 65-66) so removing callers cannot break chat.
- Option A: not rollback-able cheaply — that is itself an argument against it.

## 8. Recommendation

**REJECT the DBOS trial.** The premise (existing Postgres) is false; the capability
(durable resume) already exists in `durable_journal.py` and is merely unwired to chat runs;
and the report's framing would add a fifth overlapping durability mechanism to a stack whose
actual problem is that it has four.

Take **option B** — it fixes the only measured defect this investigation found. Take
**option C** as well *if* crash-mid-turn resume is a real requirement rather than a
theoretical one; ask the owner before assuming it is.

Log **option D** as acknowledged architectural debt with no action today.

---

```yaml
candidate: DBOS-style durable Run Store (on Postgres), as alternative to Temporal
observed_problem: "NOT the one asked about. Real measured defects found in _ops/cognitive/run_store.py: (a) unguarded read-modify-write race on sequence assignment, (b) O(n) full-file re-parse per append. Neither is solved by DBOS."
premise_check: FAILED
premise_failure: "Report assumes 'existing Postgres'. git ls-files finds zero Postgres/psycopg anywhere except 2 archived n8n/flowise JSON tool-defs under _archive-binaries/. No driver, no conn string, no schema, no service. DBOS-on-existing-Postgres therefore means adopt-Postgres-then-adopt-DBOS -- heavier than the Temporal option the same report rejects for weight."
baseline_evidence:
  - "_ops/durable_journal.py -- resume-not-restart journal, LIVE since 2026-07-23; producers doctor.doctor._journal, consumer journal_recovery.boot_recovery; cites Inngest/MS Durable Task/Diagrid/Temporal lineage"
  - "_ops/checkpoint.py -- checkpoint()/replay()/replay_state_at() over genome ledger + chrono.db; checkpoint() is a no-op when db is None (the default)"
  - "_ops/cognitive/run_store.py:27 -- DURABILITY = PROCESS_DURABLE, self-declared 'no cross-process guarantee'"
  - "_ops/evidence_plane/event_log.py -- append/read only; NO checkpoint fn, NO replay fn"
  - "_ops/tests/test_cognitive_events.py:43-55,122-129 -- sequence integrity asserted SINGLE-THREADED only; zero concurrent-append coverage"
corrects_prior_record:
  file: "_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/technology-decisions/TDR-TEMPORAL.md"
  its_claim: "'DBOS/journal/checkpoint/replay exists in evidence_plane/event_log + policy_gate'"
  correction: "event_log.py has no checkpoint/replay function (only append_event/read_events + a checkpoint_id passthrough field); policy_gate.py has no persistence at all. The real implementations are _ops/durable_journal.py and _ops/checkpoint.py. TDR-TEMPORAL's REJECT verdict stands; its cited evidence does not."
latent_not_live:
  note: "Both run_store defects are structurally present but not currently triggered -- run files are per-run_id and one turn appends sequentially from one thread."
  triggers: ["real SSE streaming (TDR-SSE-O-E4 option B): background thread emits while main thread appends", "MODEL_TOKEN per-token events (declared in EVENT_TYPES, never emitted): 500-token reply = 500 appends, ~125k line-parses"]
new_dependency: "option A would add BOTH Postgres (service) and dbos (package) -> full Dependency Admission Gate, not a light trial. Options B/C add nothing."
trial_threshold: "No trial authorized -- nothing admitted. For option B: a failing-first concurrency test (>=2 threads, ideally >=2 processes) appending to one run_id asserting zero duplicate sequences, which MUST fail against today's code before the fix lands."
rollback: "option B = revert 1 commit, storage format unchanged, no migration; option C = revert 1 commit, durable_journal.record is absolute fail-soft (durable_journal.py:65-66); option A = not cheaply reversible, itself an argument against"
decision: REJECT
counter_proposal: "option B (lock + cached max_seq in run_store, ~20-30 lines stdlib) -- fixes the only measured defect. Plus option C (wire durable_journal into chat runs, ~15 lines) IF crash-mid-turn resume is a real requirement -- confirm with owner, do not assume. Log option D (unify 4 durability mechanisms) as acknowledged debt, no action today."
evidence_refs:
  - "_ops/cognitive/run_store.py:87-130 (race + O(n) append)"
  - "_ops/durable_journal.py:13-31,52-66,87-95,107-121"
  - "_ops/checkpoint.py:25-41,44-61"
  - "_ops/evidence_plane/event_log.py:30-89,92-106"
  - "_ops/policy/policy_gate.py:22-51"
  - "_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/technology-decisions/TDR-TEMPORAL.md"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/AUDIT.json"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/OWNER-REPORT.md"
status: DRAFT — awaiting owner/ari review. Not committed, not pushed.
date: 2026-08-23
```
