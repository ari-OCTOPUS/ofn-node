---
type: decision
decision_id: DEEPSEEK-AUTOMATIC-ROUTING-01
status: EXECUTED (partial — hygiene + V3 + E2E; ongoing routing auto)
created: 2026-08-19
created_by: owner (pasted ruling) — recorded by ZCode agent
supersedes: none (extends CORE-LIVE-LEARNING-01 routing)
---

# DEEPSEEK-AUTOMATIC-ROUTING-01 — DeepSeek مسیر پیش‌فرض پرداختی

## AUTHORIZE
- DeepSeek = default approved paid LLM for OCTOPUS internal cognitive work + Live-4 evaluation.
- primary paid route = DeepSeek · exact model = `deepseek-v4-flash` (superseded only by evidence-backed config).
- planner/research/synthesis/memory-analysis/hypothesis/evidence-conditioned + baseline proposals + blind judging → automatic routing.
- Live-4 arms MUST use same actual provider + exact model (enforced: driver tier="primary" both arms).
- Non-DeepSeek route requires receipt-visible reason. No silent local fallback for paid/evaluation requests.

## CREDENTIAL POLICY (hard)
- Key read only from existing secret file/env. Never print/echo/serialize/commit/transmit/copy to docs or evidence.
- Confirm only `DEEPSEEK_KEY_PRESENT = true|false`.
- Keep .gitignore + untracked-credential protections.

## AUTOMATIC USE — HARD STOPS (all must hold)
key_present · provider reachable · reservation policy permits · cost receipt completable · FX fresh (AUD) · budget hard stop not reached · no FREEZE/HALT/TCB mismatch. On failure: receipt with exact block reason; no fake success. Free/local fallback only for non-evaluation work, labelled provider_actual=local, evaluation_eligible=false, fallback_reason explicit.

## LIVE-4 JUDGE POLICY (D-B V3)
- Judge stays DeepSeek (no GLM variable now).
- Minimal structured payload: exactly `{"choice":"A"}` | `{"choice":"B"}` | `{"choice":"TIE"}`.
- Exactly one receipted re-ask after UNREADABLE; second unreadable = VOID.
- Gate: 4/4 fresh foreground E2E cases before primary scoring.

## REQUIRED TESTS
key-absent → PROVIDER_KEY_MISSING receipt, no network · key-present → route selected · provider error → failure receipt · evaluation request → no local scoring fallback · local non-eval fallback → visible receipt + ineligible · no key material in logs/receipts/test artifacts/git diff/NOW.md/Obsidian · 4/4 E2E judge gate with DeepSeek V3.

## REPORTS (this repo)
- `06-EVIDENCE/CL01-191-20260818-2233/live4/DEEPSEEK-ROUTING-CONTRACT.md`
- `06-EVIDENCE/CL01-191-20260818-2233/live4/DEEPSEEK-CREDENTIAL-HYGIENE-TEST.md`
(status/route/model/trace IDs/test results/redacted evidence only)

## SCOPE NOTES (recorder)
- این تصمیم استفادهٔ خودکارِ داخلی را باز می‌کند؛ شرط‌های Live-4 (judge_unreadable=0، FX تازه، receipt کامل، protocol V2 فریزِ مالک) پابرجا می‌مانند.
- ثبت در labels: PROVIDER_ROUTE، D_B_JUDGE_CONTRACT، LIVE4_SCORING (پس از E2E) با owner_decision_id همین سند.
