---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, self-awareness, roadmap, memory]
created: 2026-08-06
updated: 2026-08-06
created_by: agent
sources:
  - "self-awareness-roadmap agent (workflow w3r6q78oe), re-verified against live _ops code, 2026-08-06"
---

# نقشهٔ راهِ عمیق‌کردنِ خودآگاهی — ۲۰۲۶-۰۸-۰۶

> «لایه‌های آگاهیش را پیدا کند، هر روشی که می‌شود آموزشش داد.» این نقشه فقط
> مکانیزم‌های **موجود** را توسعه می‌دهد؛ ایجنتش کدِ زنده را دوباره خواند و چند
> ادعای کاتالوگ (سندِ ۲۱) را تصحیح کرد. Stage 0 ارزان‌ترین قدمِ امن است.
> کاتالوگِ کامل: [[21-PURPOSEFULNESS-AUDIT-CATALOG-2026-08-06]].

*Grounding note: every claim below was checked against the live code in this session (`F:\backup\_ops`, worktree copy) before writing — not just taken from the audit. Several audit findings turned out to be slightly more optimistic or more pessimistic than the code shows; corrections are flagged inline as **[refines audit]**.*

## 0. Correction to the audit's framing: two silos, not five

The audit's top finding frames this as five disconnected producers. Direct inspection shows a partial reducer **already exists and works**:

- `state/cortex/self-claims.jsonl` is a real shared append-only stream. Confirmed writers: `cortex/self_model.py` (`emit_self_claims`), `cortex/goal_directed.py` (`up-*` claims), `doctor/self_accuracy.py` (`selfknow.*` claims). Confirmed reader/grader: `cortex/calibration_probe.py:44` (`CLAIMS = STATE/"cortex"/"self-claims.jsonl"`), which pairs claims against truth ledgers and writes `calibration-latest.json`.
- `self_model.py`'s own code (lines ~130-155) is *already* honest about `self_awareness_pct` being ungradeable — it emits `"gradeable": False` and a comment naming `goal_directed` and `self_accuracy` as the two producers that carry real graded pairs. **[refines audit finding #4]**: this isn't a module unaware of its own unfalsifiability; it's a module that correctly declined to fake gradeability and pointed at the real mechanism. The rename/replace suggestion still stands, but "structurally unfalsifiable" undersells that the code already fenced it off.
- `doctor/self_accuracy.py` (lines 36-46) has an explicit **anti-self-grading invariant**: "`confidence` never enters the computation of `y`; `y` only comes from comparing the report against `ORGANISM-STATE.json`/`fitness-latest.json`." This matters for teaching-method design below — any fix that feeds accuracy *back into* confidence is safe (forward in time, external truth stays external); a fix that let confidence influence *how accuracy is measured* would violate this, and none of the proposals below do that.
- `calibration-latest.json` is **not** zero-consumer as literally stated. **[refines audit finding #3]**: `budget/cockpit_readmodel.py`, `dashboard/server.py`, and `live/server.py` all read it. But `live/server.py:70,571` labels it explicitly, in its own source comment, as part of a "shadow artifacts — read-only" (`آرتیفکتِ سایه`) card whose stated purpose is to show the owner things that are "written but not read" (`نوشته‌می‌شد، خوانده‌نمی‌شد`). So the code has **already built a detector that names this exact pathology** — the audit's "zero consumers that matter" is right in spirit (nothing *decision-relevant* reads it), just imprecise in the literal grep.

**The real gap** is therefore two-sided, not "build a new reducer":
1. Two producers never joined the existing stream: `doctor/self_knowledge.py`'s "understanding" claims (confidence field, currently a rule-engine constant per its own header comment: *"15 heuristic records out of 47, every one confidence = exactly 0.4, hardcoded"* — direct corroboration of audit finding #2's pattern, though the specific 0.85 example in the audit wasn't independently reproduced this session) and `self_audit.py`'s maturity checklist never emit into `self-claims.jsonl`.
2. The one channel that proactively pushes to the owner — `cockpit_brain.py`'s `_TIERS` (line 194) and its `_ALWAYS = ("halted", "germline_alert", "approvals_status")` bypass-the-diff-threshold list (line 329) — reads none of it. `_TIERS` is wired only to `dark_capabilities`, `orphan_scan`, `self_scan` (code archaeology, subprocess-isolated, cost-tiered at 4.5s/7.8s/46.2s per the module's own measured-cost comment). It has never been extended to read `calibration-latest.json` or `self-knowledge-latest.json`, despite the module's own docstring (lines 180-187) framing its purpose as "connecting the disconnected senses."

### Consolidation plan
- **Step A** — onboard `self_knowledge` and `self_audit` into `self-claims.jsonl`, following the exact pattern `self_model.emit_self_claims()`/`goal_directed` already use: flag-gated, default-off = byte-identical, one claim per gradeable field. *Uncertainty I have not resolved*: whether `self_audit`'s always-True probes (`_probe_named_owner`, `_probe_trace_independent`) would poison `calibration_probe`'s pairing if naively added — those need to be excluded or split into the "coverage vs. live" tiers the audit itself proposes (finding #10) *before* wiring them into the shared stream, or they'll silently inflate the calibration score with unfalsifiable claims that always grade "correct."
- **Step B** — extend `cockpit_brain._TIERS`/`_ALWAYS` to read `calibration-latest.json`'s `verdict` field and `self-knowledge-latest.json`'s pathology signals, using the identical subprocess-dispatch-plus-diff pattern already built for the code-archaeology tools. This is the audit's own proposed fix for finding #3 and #7, and it is cheap: both files are already computed (`CORTEX_SELF_MONITOR=1` and `OCTOPUS_WIRE_DOCTOR_SELFKNOW=1` are already armed in `OCTOPUS-flags.cmd:1063,319`), so this is a *read-side* wire, not a new producer.
- **Step C — make it feed decisions, not just displays.** Concrete existing consumer to target: `cortex/improve.py:gather_signals()` (line 267) already reads `self_audit` and `self_model` (`state/cortex/self-model.json`) but not `calibration-latest.json` or `self-knowledge-latest.json` — directly confirmed by reading the function body. Adding those two reads to `gather_signals()`'s return dict is the one change that would make the RFC-generation pipeline (`doctor/doctor.py`, downstream of `improve.py`) actually prioritize by measured self-knowledge health instead of only code-hygiene signals. **Success criterion that's independently checkable**: after Step B lands, re-run whatever produces `live/server.py`'s shadow-artifact list — `calibration` should either drop off it (now read by cockpit_brain) or the card's own definition of "read" needs to be widened to count a push-loop consumer, not just an HTTP-pull one.

## 1. Teaching methods — each tied to a named existing mechanism

| # | Method | Builds on (verified) | New wiring needed |
|---|---|---|---|
| 1 | **Confidence clamped by measured accuracy** | `doctor/self_accuracy.py` already computes Brier per cycle into `state/doctor/self-accuracy.jsonl`; `_prior_confidence()` (line 183) already reads back "confidence stated in the *previous* round." The plumbing to read history back is already there. | `doctor/self_knowledge.py`'s snapshot writer needs one new line: before emitting the "understanding" record's `confidence` field, compute an EMA of the last N rows of `self-accuracy.jsonl`'s Brier/accuracy and set `confidence = min(stated_default, ema)`. Forward-only (last cycle's grade → next cycle's stated confidence), so it does not touch the anti-self-grading invariant. No new flag — reuses the already-armed `OCTOPUS_SELFKNOW_ACCURACY`. |
| 2 | **Push the calibration verdict, don't just store it** | `cockpit_brain._ALWAYS` (line 329) is a proven pattern for "some signals bypass the normal diff threshold and always notify." `calibration_probe.probe()` already computes `verdict` every time it's called. | Add `"calib": ("calibration_probe_card", 21600.0)` (6h — pure computation over an already-existing file, no LLM call, cheap) to `_TIERS`, and add a check inside cockpit_brain's diff loop: if `verdict` flips to `"worse"` or crosses an ungraded-ratio threshold, treat it like `halted`/`germline_alert` — bypass the tier-cadence and push immediately. |
| 3 | **Give the sophisticated-but-unrun module its first production caller** | `self_insight.py`'s `predicted_observation`/`score_previous()` loop is fully built per its own docstring (causal linking + falsifiable predictions + self-grading of past predictions) but `state/self-insight.jsonl` doesn't exist on disk — it has literally never completed a cycle. `cockpit_brain._TIERS` already has a "daily, expensive" slot (`self_scan`, 46.2s) that proves the subprocess-dispatch pattern scales to costlier tools. | Add `self_insight` as a weekly tier in `_TIERS` (cadence above `self_scan`'s daily, since it depends on `self_scan`/`dark`/`orphan` output existing first to link into hypotheses). **Unverified by me**: whether `self_insight.card()` calls out to `model_router` for synthesis or is pure static analysis like `self_scan` — this needs a read of `self_insight.py`'s body before wiring, since if it makes LLM calls it needs quota-guard consideration (see #4). |
| 4 | **Local-LLM triage before paid-LLM escalation for self-awareness events** | `cortex/model_router.py` already implements exactly this discipline for other work: three tiers (`local` = ollama qwen2.5:1.5b, "$0, always allowed"; `secondary` = GLM; `primary` = Fugu), and `cortex/fugu_quota.py` already fail-closes to local on quota exhaustion or repeated failure (`STOP-FUGU` auto-trip). | When cockpit_brain (per #2) needs to turn a raw "verdict flipped to worse" number into an owner-readable explanation, route the *classification* of "is this actually notable" through `model_router.ask("classify", ..., tier="local")` first, and only escalate to `secondary`/`primary` for the rare case that needs real synthesis — mirroring the existing cost discipline instead of introducing a new one. |
| 5 | **Owner-correction staleness as a first-class, gated signal** | `doctor/self_knowledge.py` (lines ~298-317, confirmed) *already* opens `state/doctor/owner-corrections.jsonl` every cycle and quotes the last correction verbatim. `memory/gate.py` *already* has a hard rule (its own docstring): "`self_knowledge` is always ADVISORY — raw LLM output is never stored/fed back as authoritative (end of the self-reinforcement loop)." | (a) Cheap, stdlib-only: compute `age_days` of the newest row in `owner-corrections.jsonl` inside the same read block and surface it (`"no owner correction in 10 days — focus may be stale"`) — this is literally the audit's proposed fix and touches ~3 lines. (b) Route that staleness flag through `memory/gate.py`'s `propose` verb (not `commit`) so a future `memory_store.search()` call can surface "this context may be stale" to any decision path that queries memory before acting — this **must** stay advisory per the gate's own already-declared invariant; do not add a bypass. |
| 6 | **Fix the one real live-wire lane in the RFC/genome system before building anything new on top of it** | `doctor/doctor.py:apply_merge()` (line 670) is the one part of the entire genome/RFC machinery that is structurally wired for real effect: flag-gated (`OCTOPUS_WIRE_MERGE_APPLIES_KNOB`, already armed at `OCTOPUS-flags.cmd:413`), whitelisted (`cortex/improve.py:AUTO_KNOBS`, currently one knob: `CHRONO_NUDGE_EVERY_N_BEATS`), calling a real bounded/reversible setter (`cortex/auto_approve.py:apply_knob`, line 280). Yet `knob_applied` is `null` on all 47 ledger rows, and `state/cortex/auto-knobs.json` (the file this is supposed to produce) does not exist anywhere in `state/`. | This is diagnosis, not a feature — do **not** write code before checking two things directly: (i) whether the 47 merged RFCs actually have `change_level=='tune'` and `knob=='CHRONO_NUDGE_EVERY_N_BEATS'`, or whether they're all `change_level=='code'` (which `apply_merge`'s own logic skips by design, per its comment at line ~1055); (ii) whether `OCTOPUS_WIRE_MERGE_APPLIES_KNOB` is present in the actual `os.environ` of the process that runs `apply_merge`, not just in the `.cmd` file — this vault has hit the "flag armed on disk, not loaded into the live process" failure mode before. Only once the root cause is identified does this become a code fix. |

**A cross-cutting opportunity not in the original audit list**: the `flags-overall-purpose` findings show a recurring pattern of flag comments contradicting their own values (`OCTOPUS_WIRE_BUDGET_JUDGE`'s "DISARMED" comment beside `set ...=1`; `OCTOPUS_WIRE_ROMAJAN_PROBES` same pattern; `OCTOPUS_WIRE_LEAD_OUTBOUND`'s stale "stays 0" comment). This is itself a self-awareness gap — the organism has no probe that checks "does my own configuration narrate itself correctly." `self_audit.py`'s checklist (already grep/exists-based, already admits to being "coverage not audit" per the audit's own finding #10) is the natural home for a new, genuinely falsifiable probe: parse `OCTOPUS-flags.cmd`, pair each `set OCTOPUS_*` line with its nearest preceding comment block, and flag disagreement between stated intent words ("off", "disarmed", "stays 0") and the actual value. This is cheap (pure text parsing, no LLM, no live-state read) and directly extends a module that already exists for exactly this kind of check.

## 2. Staged plan

```
Stage 0 (hours, zero new flags, pure Python, no LLM calls)
  ├─ #1  self_knowledge confidence ← EMA(self_accuracy)
  └─ #5a owner-correction staleness surfaced in self_knowledge.snapshot()
        │
        ▼
Stage 1 (cheap, reuses cockpit_brain's existing subprocess+diff pattern)
  └─ #2  cockpit_brain._TIERS/_ALWAYS reads calibration-latest.json +
         self-knowledge-latest.json
        (more valuable once Stage 0 lands — the confidence number being
         pushed is now the corrected one, not the stale constant)
        │
        ▼
Stage 2 (first production run of a previously-dead module)
  └─ #3  self_insight.py added as a weekly tier
        (needs Stage 1's extended _TIERS dispatcher to already exist;
         needs a read of self_insight.py's body first to confirm whether
         it calls model_router — currently unverified)
        │
        ▼
Stage 3 (new LLM-call path, touches the paid brain even if gated)
  └─ #4  local-tier triage before paid-tier escalation for notable events
        (depends on #2 existing — there must be a "notable event" signal
         to triage in the first place)

Parallel track, independent of the above (read-only diagnosis, no dependency):
  └─ #6  diagnose knob_applied:null root cause — do this any time, it only
         costs a targeted read of RFC files + env at the live process

Stage 4 (largest scope, needs explicit owner sign-off — this is a
governance decision per the vault's own VQ pattern, not just a code change)
  ├─ Silo Step A — onboard self_knowledge + self_audit into self-claims.jsonl
  │   (blocked on excluding self_audit's always-True probes first, or on
  │    building the coverage/live split the audit's finding #10 proposes)
  ├─ Silo Step C — wire cortex/improve.gather_signals() to read
  │   calibration-latest.json + self-knowledge-latest.json
  └─ #5b — route staleness signal through memory/gate.py as PROPOSED
        (must respect the gate's own advisory-only invariant for
         self_knowledge output; do not add a commit-bypass)
```

**Cheapest genuinely-first step**: Stage 0. Both items are pure-Python edits to files that already run every cycle (`OCTOPUS_WIRE_DOCTOR_SELFKNOW=1` is already armed), touch no new flags, make zero new LLM calls, and are individually revertible without affecting anything else in the pipeline. Neither requires understanding `self-claims.jsonl`'s pairing semantics or the calibration grading logic in depth — they're local fixes to `self_knowledge.py`'s own output.

**Highest-leverage step**: Stage 1 (#2). It is the one change that turns the *already-working* claims/calibration loop from a pull-only dead end into something that reaches the owner the same way `halted`/`germline_alert` do — without inventing any new self-observation machinery, purely by finishing a wire the codebase's own docstring says was the point of `cockpit_brain.py` in the first place.

**Where I'm least certain**: (a) whether `self_insight.py`'s cost profile is closer to `self_scan`'s 46s or something cheaper — I did not benchmark it, only read its docstring; (b) whether adding `self_audit`'s checklist wholesale into `self-claims.jsonl` would corrupt `calibration_probe`'s Brier score with unfalsifiable always-True claims — this needs to be checked against `calibration_probe.py`'s pairing logic before Stage 4 Step A, not assumed safe; (c) the exact numeric example in audit finding #2 (0.85 vs 0.667) — I confirmed the *pattern* (hardcoded confidence disconnected from measured accuracy) independently via `self_knowledge.py`'s own header comment about "15 of 47 records at exactly 0.4," but did not reproduce the specific 0.85 figure this session, so treat that one number as unverified-by-me even though the underlying defect is real and corroborated from a second angle.
