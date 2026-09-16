---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, chatbox, unified-context, memory, equations, explainer, session, adr-036, handoff, senior-agent]
created: 2026-08-12
updated: 2026-08-12
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/04-FINAL]]"
  - "[[00 - Inbox/2026-08-12 RECONCILIATION-REPORT — Math Atlas Runtime Truth]]"
  - "[[03 - Projects/research-spec-compiler/adr/ADR-036-math-control-spine]]"
---

# ۴۲ — اتصال کامل Chat Box به مغز، حافظه، معادلات و معماری (2026-08-12)

> برای ایجنت بعدی: وضعیتِ فعلی + فایل‌های نو + قواعد. همه‌چیز از فایل/runtime تأیید شده، نه چت.

## ۱. موج‌های امروز (خلاصهٔ ترتیب)

| موج | کار | نتیجه |
|-----|-----|--------|
| **۱** | Math Atlas Reconciliation (۲۰ معادله ↔ runtime) | APPLY=ADR-035/ARMED · CR-B0 زنده · σ نسخه‌دار · verifier + evidence aggregator |
| **۲** | Awareness/Memory/Ask B→H (ایجنت موازی) + فاز I تأیید | owner_recall · data.facts · vault_empty · selfmap · همه ادعاها VERIFIED |
| **۳** | J→N (رأی مالک «کمترین محدودیت» = انتخاب ۳) | equation_advice · shadow_influence · shadow_evaluation · limited_effect (proposal-only) |
| **۴** | Chat Box اتصال O→U (این مگاپرامپت) | unified_context · explainerها · session · UI · ADR-036 · M9 localStorage |

Evidence pack: `_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/`
(00-DISCOVERY · 01-ARCHITECTURE · 02-TEST · 03-VERIFY · 04-FINAL · 07/08/09/10/11).

## ۲. فایل‌های نو (همه additive — هیچ orchestrator جایگزین نشد)

| فایل | نقش |
|------|------|
| `_ops/memory/unified_context.py` | assembler واحد (فاز P): self_context + shadow + effects + architecture + facts؛ schema unified-context.v1 |
| `_ops/memory/equation_explainer.py` | ۱۳ معادله، ۵ سطح (فرمول/معنی/ورودی/status واقعی/شاهد)؛ برچسب advice-only |
| `_ops/memory/architecture_explainer.py` | ۱۱ جزء با path/caller/gates/effects؛ دو حالت ساده+فنی |
| `_ops/memory/session_memory.py` | session موقت (preview-only) + «یادت بماند» → MEMORY_CANDIDATE (نه commit) |
| `_ops/tests/test_chatbox_unified.py` | 13 تست (P×3, Q×4, S×3, intent×3) |
| `03 - Projects/…/adr/ADR-036-math-control-spine.md` | بستن C2 — math spine تصمیم ثبت‌شده (ACCEPTED، رأی مالک) |

**گسترش‌یافته:** `conversation.py` (+۶ intent: equation/architecture/evidence/business/effect/memory-proposal) ·
`collaborator.py` (+data.equation_advice, data.unified_context, session) ·
`collab_model_adapter.py` (+session block در `_self_context`) ·
`miniapp/app.js` (پنل «📎 Sources / شواهد · معادلات · وضعیت» + vault paths + localStorage `octopus.asklog.v1`).

## ۳. وضعیت‌های حاکمیتی (تا الان — هم‌راستا)

| موضوع | ارزش | شاهد |
|-------|------|------|
| APPLY | **1 / ARMED** (ADR-035) | ۶ منبع هم‌راستا (flags/capability/verdict/ADR/registry/runtime) |
| limited_effect_phase_n | **3** (اثر محدود — فقط proposal) | owner-verdicts.yaml + limited_effect.enabled() |
| math_control_spine | **1** (ADR-036 — soft effects فقط) | owner-verdicts + spine.py |
| chrono-rhythm CR-B0 | TESTED/SHADOW (معتبر — validator ok) | signals-registry |
| may_authorize | **همیشه false** در adapterهای گفت‌وگویی | test_chatbox_unified P2 |

## ۴. قواعد برای ایجنت بعدی (شکستن = رد)

1. **Memory/Equation/Chat هیچ‌وقت authorize نمی‌کند** — `may_authorize=false`؛ semantic write فقط با رأی مالک.
2. **effect request در چت فقط proposal** — `ALLOWED_AS_PROPOSAL`؛ PolicyGate مرجع؛ `applied=false` همیشه.
3. **فایل‌های قفل‌شده دست‌نخورده:** flags.cmd · signals-registry · capabilities-registry · run_all.py · ADR-033..037 · pulse_arbiter · rhythm · ledger · policy_gate. تغییر = STOP + رأی.
4. **Improve don't rewrite.** اگر عضوی هست (مثل Collaborator/gateway) reuse کن؛ سیستم موازی نساز.
5. **Truth over appearance.** معادلهٔ بدون implementation هرگز ACTIVE معرفی نشود؛ 4d همیشه «وصل نیست».
6. **Evidence قبل از ادعا.** هر ادعا → fact با source_path/locator؛ نبود → «تأیید نشده».
7. **WORKLOCK:** `run_all.py`/`wiring.py`/`center.py`/`orphan_scan.py` — ثبت تست را گزارش کن، خودت ثبت گسترده نکن.
8. **بدون commit مگر دستور مالک.** بدون secret در لاگ/فیکسچر/report.

## ۵. Conflictهای امروز (همه بسته)

| id | شرح | حل |
|----|------|-----|
| C1 | chrono-rhythm TESTED/SHADOW (ممیزی نردبان را معکوس دیده بود) | validator ok — ادعا ≤ شواهد |
| C2 | ADR-036 ارجاع‌شده ولی فایل نداشت | رأی مالک → فایل ساخته شد |

## ۶. تست‌های کلیدی (سبز در 2026-08-12 شب)

```
test_chatbox_unified 13/13 · test_phase_jn 13/13 · test_awareness_ask_bridge 6/6
test_memory_ask_recall 6/6 · test_miniapp_gateway 49/49 · test_owner_verdicts 15/15
test_cognitive_unify PASS · pytest (verify_math_atlas + neural_apply_evidence) 163 passed
node --check app.js OK · compile 27 ماژول OK · registry validator ok
```

## ۷. هنوز باز (برای موج بعد — نیاز به رأی/زمان)

- Shadow Influence پنجرهٔ ۷ روزه (تا 100 نمونه) → فاز L verdict.
- CR-B1 کوراموتو runtime وصل نیست (فقط pure helper).
- v2 σ (connectivity_ratio) فقط shadow؛ canonical شدن نیازمند AUC + رأی.
- session backend فقط preview کوتاه (کامل‌تر = موج بعد).
- ask_vault RAG بُعدی روشن است ولی semantic write arm نشده (عمدی).

## ۸. برای مالک — دیدن اثر

مینی‌اپ ببند/باز → تب «پرسش» → همکار (پیش‌فرض):
- «از چی تشکیل شدی؟» → دو مغز + شاهد runtime
- «معادله BCM چیه؟» → فرمول + status + شاهد فایل
- «Pulse Arbiter به چی وصله؟» → معماری با path
- «این تصمیم من را یادت بماند» → «پیشنهاد حافظه ساختم؛ هنوز ننوشتم»
- «سرعت رو کم کن» → «پیشنهاد اثر ساخته شد؛ PolicyGate مرجع»
- پنل «📎 Sources / شواهد · معادلات · وضعیت» زیر پاسخ همکار؛ چت بعد از تعویض تب می‌ماند.

## مرتبط

- [[01 - Dashboard/HANDOFF]] (وضع لحظه‌ای جمع‌شده — چهار موج)
- [[_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/README]]
- [[_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/12-TIDY-VERIFY]]
- [[00 - Inbox/2026-08-12 RECONCILIATION-REPORT — Math Atlas Runtime Truth]]
- [[03 - Projects/research-spec-compiler/adr/ADR-036-math-control-spine]]
- [[03 - Projects/research-spec-compiler/adr/ADR-035-neural-learned-apply-rearm]]
- [[_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/00-DISCOVERY-REPORT]]
- [[_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/04-FINAL]]
