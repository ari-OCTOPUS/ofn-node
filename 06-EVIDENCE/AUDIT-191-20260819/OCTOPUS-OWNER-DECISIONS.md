# OCTOPUS-OWNER-DECISIONS — only items truly unsolvable without the owner

Principle applied: if an agent can do it under existing decisions (CORE-AUTO-DEBUG scope, non-TCB, tests+rollback), it is **not** listed here. Audit close 2026-08-19T02:07Z.

## Immediate (hours)

### OD-1 — FX re-pin before 06:00Z today
- **What**: manually fetch RBA AUD_USD (2026-08-19), pin it (new FX-RECORD.json + fx_hash + new pin ID like FX-PIN-20260819-02).
- **Why only owner**: FX pinning is an owner act by design (auto-fetch forbidden / PROPOSE_ONLY boundary).
- **If not decided**: from 06:00Z every Live-4 paid evaluation returns `expired(>24h) → paid_fallback=BLOCKED`. The whole day's scoring window dies on this one administrative act.
- **Irreversibility**: none (re-pin anytime).

### OD-2 — Ratify LIVE4_PROTOCOL_VERSION V2 freeze (before first primary pair)
- **What**: declare the taxonomy/judge-contract/eligibility set frozen; attach a freeze timestamp + hash (non-null evidence_hash on the label).
- **Why only owner**: preregistration is an owner guarantee; an agent freezing its own scoring rules before grading itself would be self-sealing.
- **If not decided**: any primary pairs collected now are formally unfrozen-protocol pairs — contestable later.

### OD-3 — Reservation re-arm (only if the 90-min window lapses before scoring)
- **What**: a fresh `start_override` (like LEARNING-FIRST-BUDGET-EXPANSION-01) if the current window expires before batches 1-2 complete.
- **Why only owner**: override activation is an owner-budget act; also note `start_override` **resets all counters** (G11) — decide whether counter-reset is acceptable.

## Today (otherwise the machine can proceed alone)

### OD-4 — Judge-provider policy if the next D-B iteration still fails 4/4
- **What**: pre-authorize (or forbid) switching the judge to a different provider family than the arms (current: same family, `judge_independence_limited=True` hard-coded).
- **Why only owner**: changes scoring semantics + possibly spend pattern; also resolves the duplicate-rationale-hash smell.
- **Recommendation**: allow one different-family judge for the E2E gate only, keep VOID policy unchanged.

### OD-5 — Accept / schedule D3 git-history cleanup (or explicitly accept the risk)
- **What**: history rewrite to purge old `mail_credentials.py` versions — currently **forbidden** by standing rule.
- **Why only owner**: highest irreversible-risk action in the repo (rewrite breaks clone/verify chains).
- **Safe default**: keep risk OPEN, rotate any credentials the old file contained, decide rewrite never/in-a-window.

## Not now (do NOT authorize in this window)

- Any board/SSH contact (.138/.180/.182), .180 activation, ESP32 pilot or hardware purchases — no verified inventory even exists (K1–K8).
- Budget cap changes beyond 30/24/1 AUD.
- TCB edits (incl. wiring changes inside the manifest's 15 files) outside owner ceremony.
- Automatic FX fetching.
- Splitting/rewriting label-history (append-only rule).

## Explicitly NOT owner-blocked (agent-executable under standing decisions)

- D-B code fix + fresh 4-case E2E (blocker #1) — technical, within CORE-AUTO-DEBUG.
- E2E fixture gate assertions, NOW.md regeneration script, receipt-budget bug fix, paid_blocked/FX-expiry wiring, Admission+radar wiring, F3 auto-debug, missing decision-file write-ups (with owner sign-off after the fact).

---

**One-line summary for the owner**: امروز فقط سه کار مالک‌محور فوری داری — (۱) پین FX را قبل از ۰۶:۰۰Z تازه کن، (۲) فریز V2 پروتکل را تصویب کن، (۳) اگر پنجرهٔ رزرو گذشت دوباره مسلحش کن؛ همهٔ ماندهٔ سیستم فنی است و بزرگ‌ترینش همان ۱-from-4 قضاوتِ غیرقابل‌خواندن در گیت E2E.
