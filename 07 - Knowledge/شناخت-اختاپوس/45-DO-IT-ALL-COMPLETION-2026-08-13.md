---
type: session-note
date: 2026-08-13
status: COMPLETE (except subprocess isolation — documented)
suites: 170+ tests green across all epistemic + hub + gateway suites
restarts: gateway PID 5704→21580, cortex restarted (fresh code live)
---

# 45 — «انجام بده همرو»: تکمیلِ کاملِ تمامِ خواسته‌های این چت

> مالک: «انجام بده همرو». این نوت ثبت می‌کند چه چیزی واقعاً شد، چه چیزی live است،
> و تنها قطعهٔ باقی‌مانده چیست.

## ✅ چه چیزی LIVE شد (با restart gateway + cortex)

کامیت‌های این نشست روی پروسهٔ زنده لود شدند. gateway PID 5704→21580، cortex تازه.

| چیزی | وضعیت | چطور ببینیش |
|---|---|---|
| مغزِ واقعیِ چت (DeepSeek) | ✅ live | مینی‌اپ → سؤال → جوابِ طبیعی (نه stub) |
| template→model (۱۴ intent) | ✅ live | «وضعیت/هدف/موانع/معادله/معماری/...» → جوابِ مدل |
| پنلِ `/api/epistemic` | ✅ live | تب System (یا chipِ جدید بعد از باز‌بازکردن مینی‌اپ) |
| chipِ 🐙 درگاه (Phase ۵) | ✅ live بعد از باز‌بازکردن مینی‌اپ | app.js جدید در cache |
| `epistemic_tick` (C5) | ⏸ shadow، default OFF | `EPISTEMIC_TESTS=1` + restart cortex |

## ✅ چه چیزی ساخته شد (کد commit‌شده، flag-gated)

### Conversation Hub (ADR-040) — کامل
- Phase ۱: schemas/router/service (`8aef770`)
- Phase ۲-lite + Phase ۲ کامل: همهٔ ۱۰ route واقعی — ask/runtime/memory/guide/epistemic/mcp/propose (`01d63b0`/`864f7d2`)
- Phase ۳: `POST /api/octopus/chat` + `GET /api/octopus/runs` + `/api/octopus/receipts` (`864f7d2`/`0390007`)
- Phase ۵: app.js chipِ «🐙 درگاه» + renderِ ChatReply (`a0225e5`)
- Phase ۶: shadow_rollout (dual-read Hub vs collab) (`1dd7ef1`)

### Epistemic TCB (ADR-039) — کامل (C1-C7)
- C1/C2: schemas + canonical + receipt chain (قبلاً)
- Phase ۲.۵: WorldMode/ExecutionScope + ۱۰ invariant + ۸-part (`cf769e9`)
- C4: bayes.py + DiscoveryBlock + score-band (`a7649d0`)
- Phase ۲.۶: experiment_selector + benchmark_metrics (`e65457d`)
- C3: sandbox_runner + test_planner (`5ee5753`)
- C5: cortex epistemic_tick shadow (`1c08eeb`)
- C6: `/api/epistemic` read-only panel (`c0fb34b`)
- C7: shadow_run harness + digest (`c0fb34b`)
- post-Go: dual-channel composer + cortex claim-builder (`1dd7ef1`)

### Benchmark آفلاین — ۲۰ موردِ grounded
- REAL_CASES روی فرضیه‌های واقعیِ Octopus (`34bed3b`)
- نتیجه: 🛑 NO-GO صادقانه (delta=0.0) ولی safety criteria همگی pass + UFBR C=1.0
- Go واقعی نیازِ اجرای واقعیِ آزمون‌ها دارد (نه fixture metric)

## 🔓 دروازه — owner override
مالک «بیا دروازه رو باز کنیم». نیمهٔ ایمنی pass بود؛ نیمهٔ کارایی روی synthetic/grounded
NO-GO. مالک با آگاهی override کرد — صادقانه در پنل ثبت شد (نه جعلِ Go). C6/C7 = سطوحِ
observability، `may_execute` همیشه False.

## ⏳ تنها قطعهٔ باقی‌مانده (صادقانه: خطرناک است بسازیمش زود)

**subprocess + rlimits isolation برای sandbox_runner.** الان sandbox_runner یک bounded-
wrapper است (HALT/budget/time/output-path را enforce می‌کند) ولی true process/network
isolation نیست. ساختِ real sandbox روی win32 نیازِ کارِ platform-specific دارد — improvise
کردنش خطرناک‌تر از نکردنش است. document شد، نساخته شد.

## 🚀 چطور همه‌چیز را real کنی (الان)

۱. **مینی‌اپ را ببند و باز کن** (از تلگرام) → chipِ «🐙 درگاه» ظاهر می‌شود + app.js جدید.
۲. **چتِ واقعی**: بپرس «وضعیت چیست؟» → جوابِ DeepSeek.
۳. **درگاهِ واحد (وقتی خواستی)**: `set OCTOPUS_UNIFIED_CHAT=1` در flags.cmd + restart gateway
   → chipِ 🐙 فعال → intent routing خودکار.
۴. **C5 epistemic tick**: `set EPISTEMIC_TESTS=1` + restart cortex → shadow health-check.
۵. **Go واقعی**: datasetِ واقعیِ ۲۰-۴۰ مورد با thresholdِ predeclare → run benchmark → Go.

## شواهد تست — ۱۷۰+ سبز

epistemic: schemas 45 + receipt_chain 20 + invariants 19 + bayes 14 + selector_metrics 24
+ runner 11 + benchmark 6 + compose_build 8 = 147
hub: conversation_hub 11 + octopus_chat_endpoint 5 + shadow_rollout 4 = 20
gateway: miniapp_state 9 + miniapp_gateway 49 + collab_model_evidence 9 + talk_discovery 14
+ route_scorer_wire 6 + api_collab 17
