# 02-TEST-REPORT — اتصال Chat Box (فاز U) — 2026-08-12

## تست‌های نو (فاز P→U)

### `test_chatbox_unified.py` — 13/13 ✅

| # | تست | پوشش |
|---|-----|-------|
| P1 | دو مغز حاضر + 4D صادق | self_context.cortex/business_brain live · four_d_connected=false |
| P2 | never authorizes | may_authorize=false در unified/equations/effects/shadow |
| P3 | missing state fail-soft | STATE_DIR گم → schema سالم، بدون crash |
| Q1 | BCM توضیح با status | matched · equation_id=bcm · status ∈ STATUSES · شاهد bcm.py |
| Q2 | sigma اثر صادق | spectral-sigma-legacy · status واقعی نه جعلی |
| Q3 | معادلهٔ ناشناخته | matched=false · equation=None · no claim |
| Q4 | معماری با path | pulse_arbiter · path در detail |
| S1 | session roundtrip + isolation | 2 نوبت · roles درست · may_authorize=false |
| S2 | memory proposal نه commit | MEMORY_CANDIDATE · candidate_not_committed |
| S3 | session clear | بعد از clear خالی |
| Q5 | equation intent | kind=equation · advice_only · no effect |
| Q6 | effect proposal-only | kind=effect · applied=false · external_effect=false |
| Q7 | evidence honest | kind=evidence · may_authorize=false |

## Regression — همه سبز ✅

| suite | نتیجه |
|-------|-------|
| test_awareness_ask_bridge | 6/6 ✅ |
| test_memory_ask_recall | 6/6 ✅ |
| test_miniapp_gateway | 49/49 ✅ |
| test_phase_jn | 13/13 ✅ |
| test_owner_verdicts | 15/15 ✅ |
| test_rhythm | ✅ |
| test_pulse_arbiter | ✅ |
| node --check app.js | ✅ |

## Smoke زنده

- `equation_explainer "BCM چیست؟"` → matched · ۵ سطح + شاهد
- `architecture_explainer "Pulse Arbiter به چی وصله؟"` → path + caller
- `unified_context "از چی تشکیل شدی؟"` → shadow_records=2 · effects NOT_REQUESTED · may_authorize=false
- conversation intents: equation/architecture/evidence/effect/memory-proposal/business → همه kind درست

## سه لایه (مگاپرامت)

| لایه | وضعیت |
|------|--------|
| Unit (router/assembler/explainer/contract) | ✅ test_chatbox_unified 13/13 |
| Integration (/api/ask + collab + recall + facts + shadow) | ✅ regression gateway 49/49 + phase_jn 13/13 |
| Regression (awareness/recall/gateway/J-N/verdicts) | ✅ همه سبز |

هیچ تستی برای سبزشدن حذف/ضعیف نشد — فقط افزوده شد.
