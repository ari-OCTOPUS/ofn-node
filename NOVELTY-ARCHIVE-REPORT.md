# NOVELTY ARCHIVE REPORT — Phase 1

- **Decision:** `MEGA-LIFE-v1`
- **Observed:** 2026-08-19
- **Verdict:** `INCONCLUSIVE_FOR_BEHAVIORAL_NOVELTY`
- **Stop rule:** No Phase 2–9 implementation was performed.

## Direct answer

The requested number—“how many of 335 ideas were genuinely novel?”—cannot be honestly computed because the repository contains **no evidence-backed 335-item idea cohort** and **no 358-entry duplicate-rejection ledger**.

The strongest reproducible current result is:

| Measure | Result | Grade |
|---|---:|---|
| Canonical cohort inspected | **191** queued debate entries | OBSERVED |
| Exact unique normalized idea texts | **176** | VERIFIED by deterministic recount |
| Exact repeat records | **15** | VERIFIED by deterministic recount |
| Conservative near-duplicate candidate pairs | **3 pairs** | OBSERVED screen, not semantic verdict |
| Behaviorally novel **and** replayable ideas | **UNKNOWN** | INCONCLUSIVE |

Therefore:

```text
Of 335 ideas, genuinely novel = NOT MEASURABLE (unsupported denominator).
Of 191 queued entries, exact-text unique = 176; exact repeats = 15.
Behaviorally novel and learnable = UNKNOWN.
```

It would be false to label all 176 exact-unique texts “genuinely novel.” Different wording can describe the same behavior, and many entries are generic variations on neural networks, market prediction, genome tooling, blockchain, or 3D printing.

## 1. Claims tested

### Claim A: 335 ideas were generated

- No repository file, counter, or ledger cohort supporting 335 was found.
- Related but non-equivalent counts exist across different lifecycle layers. They must not be added together because they overlap and have different schemas.
- **Verdict:** `FAILED_ASSUMPTION`.

### Claim B: 358 duplicate rejections were recorded

- No `duplicate rejection` event type or 358-record rejection cohort was found.
- Memory admission has an idempotency duplicate decision, and the doctor/debate paths have local dedupe, but these are not a 358-record novelty archive.
- **Verdict:** `FAILED_ASSUMPTION`.

## 2. Canonical cohort selection

The report uses `_ops/debate/SURVIVORS-QUEUE.md` as the canonical available idea cohort because it records one human-facing queued idea per entry and includes the full idea text.

Observed structure:

- `191` entry headers.
- `191` `**idea:**` lines.
- `173` unique recorded content signatures among the later signed format.
- `18` early entries predate the signature format.
- The queue is append-only by contract; “survivor” means queued for human review, not approved or valuable.

Other related sources are not substituted as the denominator:

| Source | Observed count | Why it is not the canonical denominator |
|---|---:|---|
| `_ops/debate/survivors-pending.jsonl` | 64 records | Later publication subset; feature-gated and not the full queue. |
| `07 - Knowledge/genome-system/ledger/ledger.jsonl` | 63 records whose parsed type is `PROPOSAL` | Only queued survived proposals under a specific path; overlaps the queue and omits kills/undecided entries. |
| Same genome ledger, debate `EXPERIENCE` matches | 659 records | Round-level records, not ideas; one debate may use multiple rounds. |
| Same ledger, `verdict: kill` string matches | 119 | Round verdict records, not unique rejected ideas. |
| Same ledger, `verdict: pass` string matches | 86 | Round verdict records; not unique accepted ideas. |

The ledger was live while this audit ran, so counts are a timestamped observation, not a permanent constant.

## 3. Reproducible exact-duplicate method

For each of the 191 queue entries:

1. Extract the text after `- **idea:**`.
2. Apply Unicode NFKC normalization.
3. Apply case folding.
4. Replace punctuation with spaces.
5. Collapse repeated whitespace.
6. Group by the resulting exact normalized string.

Result:

```text
total records                 = 191
normalized exact unique       = 176
normalized exact repeat count = 15
```

The largest obvious repetition is the stub idea:

```text
پروکسی ارزش per-organ از APPROVALهای sent ساخته شود
```

The code explains why this repetition exists: `_ops/debate/debate_loop.py` defines that sentence in `_stub_transport`, and comments record that a production caller historically used `live=False`, causing stub output. This is direct evidence of a closed, repetitive generation path, but it does not prove that every non-exact entry is novel.

## 4. Conservative near-duplicate screen

To find obvious wording variants without pretending to perform semantic judgment, this audit computed Jaccard similarity over normalized character trigrams and flagged pairs at `>= 0.80`, excluding exact duplicates.

Three candidate pairs were found:

| Similarity | Candidate A | Candidate B |
|---:|---|---|
| 0.879 | استفاده از شبکه‌های عصبی مصنوعی برای پیش‌بینی حرکات بازار | استفاده از شبکه‌های عصبی مصنوعی برای پیش‌بینی بازار |
| 0.833 | استفاده از هوش مصنوعی برای پیش‌بینی و کاهش رویدادهای متر صفر | استفاده از هوش مصنوعی برای پیش‌بینی و کنترل رویدادهای متر صفر |
| 0.804 | استفاده از هوش مصنوعی برای پیش‌بینی معاملات سهام | استفاده از هوش مصنوعی برای پیش‌بینی سهام |

This is only a **candidate screen**:

- It misses semantic duplicates expressed in another language or with different vocabulary.
- It can flag legitimately distinct ideas with similar wording.
- It does not inspect implementation behavior, inputs, outputs, costs, failure modes, or replay.

Accordingly, subtracting these pairs from 176 would not yield a valid novelty number.

## 5. Why behavioral novelty is currently unknowable

The target acceptance rule is:

```text
admit = novel AND learnable
```

The current records lack a versioned behavior characterization containing at least:

```text
{
  problem_class,
  intended_human_or_survival_value,
  inputs_schema,
  permitted_outputs,
  state_transition,
  tools_and_models,
  resource_profile,
  risk_class,
  failure_signature,
  expected_observable_delta,
  replay_recipe,
  receipt_refs
}
```

The current queue often has an idea, rationale, kill condition, and cheapest test, but it normally has no live caller, executable candidate, behavior trace, or replay receipt. Under LAW-12, these are proposals, not verified capabilities.

## 6. Existing anti-repetition mechanisms

### Debate content signatures

`_ops/debate/debate_loop.py` computes:

```text
sha256(topic_id + "|" + idea)[:12]
```

The signature binds a wording to a topic and is used for queue idempotency and owner verdict lookup. This prevents a byte-equivalent idea on the same topic from being queued again after the newer format is active.

**Limitation:** It is exact-content dedupe, not semantic or behavioral novelty.

### Queue cooldown

The debate queue enforces a per-topic cooldown (default six hours).

**Limitation:** A cooldown reduces rate; it does not increase novelty.

### Memory admission idempotency

`_ops/memory/admission.py` rejects an already-present `idempotency_key` as `IDEMPOTENT_SKIP`.

**Limitation:** This protects canonical memory; it does not compare idea behaviors.

### Doctor open-RFC dedupe

`_ops/doctor/doctor.py` reuses an open RFC with the same bottleneck text.

**Limitation:** This is local lifecycle dedupe, not an archive-wide novelty score.

## 7. Required novelty archive contract

This report defines the contract but does not implement it.

### Characterization

Every proposed capability must receive a versioned behavior characterization before paid or high-risk execution:

```text
behavior_id
schema_version
proposal_id
lineage_ids
problem_class
input_contract_hash
output_contract_hash
state_transition_signature
tool_family
model_family
resource_bucket
risk_class
human_value_target
failure_signature
expected_observable_delta
replay_recipe_hash
receipt_refs
```

### Distance

Distance must be computed over declared fields, not only natural-language text. A versioned formula and thresholds must be frozen before evaluation. Missing fields increase uncertainty; they do not make an idea novel.

Suggested first deterministic baseline:

- exact input/output/state/tool/risk signature match: duplicate;
- same lineage and same expected observable delta: variation unless an ablation proves a new mechanism;
- k-nearest behavior distance above frozen threshold: novelty candidate;
- cross-language text is only supporting evidence, never the primary distance.

### Learnability

An entry is learnable only if:

- a candidate can be replayed from a declared recipe;
- a live or shadow caller emits a receipt;
- inputs and outputs are interpretable to an independent observer;
- a falsifier and rollback exist;
- the candidate does not judge its own success.

### Budget position

The cheap characterization and archive lookup must run before paid calls or mutation execution. A proposal with insufficient fields is `INCOMPLETE`, not “novel by default.”

## 8. Admission states

```text
INCOMPLETE
EXACT_DUPLICATE
VARIATION_CANDIDATE
NOVELTY_CANDIDATE
LEARNABLE
ADMITTED
QUARANTINED
RETIRED
```

Only `NOVELTY_CANDIDATE + LEARNABLE` can become `ADMITTED`. Admission itself does not equal promotion to a live capability.

## 9. Phase-1 gate verdict

| Gate question | Result |
|---|---|
| Was a 335-item cohort found? | **No** |
| Was a 358 duplicate-rejection ledger found? | **No** |
| Can exact repeats be measured now? | **Yes: 15 of 191 records** |
| Can exact-unique wording be measured now? | **Yes: 176 of 191 records** |
| Can genuine behavioral novelty be measured now? | **No** |
| Can learnability be measured for the cohort? | **No; replay receipts are absent** |

**Final Phase-1 verdict:** `INCONCLUSIVE_FOR_BEHAVIORAL_NOVELTY`, with a verified exact-repeat baseline of `15/191` and an exact-unique wording count of `176/191`.

This is the honest number available today. Any stronger “genuinely novel” count would exceed the evidence.
