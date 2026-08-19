# LIVE-4 PRIMARY V2 RUN REPORT — 2026-08-19 (frozen protocol V2, composite d6e02f770ac2aaab)

Executed under owner sign-off FX-PIN-01 + LIVE4-PROTOCOL-V2-FREEZE-01, 03:43Z–05:35Z, both batches completed **before FX hard expiry (06:00Z)**. Foreground mode, reservation receipted (RESERVATION_RESET ×2 — the G11 fix's first production receipts).

## Verdict: FROZEN CRITERION **NOT MET** — valid 22/30 · conditioned wins 13/20

| batch | n | valid | cond wins | voids (all judge) | positions |
|---|---|---|---|---|---|
| 1 | 15 | 11 | 7 | 4 | A:7 B:4 |
| 2 | 15 | 11 | 6 | 4 | A:7 B:4 |
| **total** | **30** | **22** | **13** | **8** | A:14 B:8 |

## Full reporting contract (per frozen protocol §6)

- **valid pairs**: 22 (all under judge-choice-v3/1; unique pids; complete receipts)
- **VOID count+reasons**: 8 — 100% `judge` (UNREADABLE after the one allowed receipted re-ask); **zero** provider failures, **zero** baseline-arm failures, zero exceptions
- **provider availability**: 100% (45/45 base+cond calls ok, deepseek-v4-flash tier=primary both arms)
- **baseline-arm reliability**: 100% (D-A fix held at scale)
- **judge readability**: 22/30 = 73.3% (E2E gate was 4/4; readability degrades at batch volume — the run's central finding)
- **metadata completeness**: 100% (retrieved evidence mem-ids recorded per valid pair)
- **Brier (this run, n=22, conf 0.55)**: (13×0.2025 + 9×0.3025)/22 = **0.2434**
- **costs**: ≈ $0.0045 AUD total run → ≈ $0.0002/valid pair · ≈ $0.00035/conditioned win (receipt basis: remaining-budget, all non-negative — RCPT-1 held through 90+ receipts)
- **evidence-conditioned vs baseline**: 13W–9L (59.1% of valid; chance=50%; n too small to claim)
- **limitations**: same-family judge (independence limited, disclosed); 8 readability voids; single-day single-FX-window

## Falsification check (protocol §7)

- wins < 20/30 → **falsified for this run** (as a pass)
- judge readability < 100% of *counted* pairs — counted pairs are the 22 valid (readable by construction), but the 30-case sample could not be fully counted → the deeper failure is readability, not conditioning
- `MEMORY_LIVE_LEARNING_UNVERIFIED` **stands** — this run's evidence weighs against upgrade

## Honest reading

اجرا از نظر عملیاتی موفق بود (صفر خطای provider، صفر شکست baseline، رسیدهای سالم، هر دو batch داخل پنجرهٔ FX) — اما قابلیتِ خواناییِ داور در مقیاس batch (۷۳٪) گلویی است که E2E چهارتایی آن را پنهان می‌کرد. نرخ برد شرط‌دار ۵۹٪ در n=22 نشانهٔ مثبتی است ولی معیارِ منجمد ۳۰/۲۰ است و تغییرش ممنوع.

## Next options (owner-gated — no inference)

1. **D-B/V4 judge robustness** (e.g., two-stage parse, different-family judge, or lower-entropy prompt engineering) → then a NEW frozen protocol version + fresh primary. A different-family judge needs an explicit owner decision (DEEPSEEK-AUTOMATIC-ROUTING-01 currently pins DeepSeek-only).
2. **Void-top-up rule**: predeclare that batches may extend beyond 15 cases until 15 *valid* per batch accrue (censored sampling) — this CHANGES the frozen protocol ⇒ needs owner + new freeze record.
3. Stop here: the falsified run is itself valid scientific output (negative knowledge preserved).

Artifacts: live4-pairs.jsonl rows 63–92 · primary-v2-score.json · primary-v2-b1-run.log (partial, crashed shell) · API-RECEIPTS.jsonl · cost-receipts (RCPT-1 basis) · reservation-receipts.jsonl (RESET×2).
