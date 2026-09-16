# 00-DISCOVERY-REPORT — اتصال Chat Box (فاز O) — 2026-08-12

> قبل از هر patch. همهٔ ادعاها از فایل/runtime تأیید شدند — نه از چت.
> مگاپرامپت: «وصل به دایرکتوری، به خلاصه اعتماد نکن.»

---

## ۱. ادعاهای baseline — وضعیت

### گروه A (B→H) — همه VERIFIED

| ادعا | فایل | وضعیت |
|------|------|--------|
| `recall_for_owner_ask` + `topic_wants_recall` | `_ops/memory/owner_recall.py:30,23` | **VERIFIED** |
| `may_authorize==False` همه‌جا | owner_recall.py:77,110,138 + hard-overwrite 147-148 | **VERIFIED** |
| `_self_context` = cortex+business_brain+4d note | `collab_model_adapter.py:143-144` | **VERIFIED** |
| `data.facts` + خط «شاهد:» | `collaborator.py:242,247-256` | **VERIFIED** |
| `vault_empty`/`vault_flag` در /api/ask | `miniapp_gateway.py:644-648` | **VERIFIED** |
| selfmap intent | `conversation.py:42-46` | **VERIFIED** |
| tests awareness 6/6 · memory_recall 6/6 | هر دو فایل | **VERIFIED** (6 تابع هرکدام) |
| miniapp_gateway 49/49 | `test_miniapp_gateway.py` | **VERIFIED** (قبلاً اجرا شد) |

### گروه B (J→N) — همه VERIFIED

| ادعا | فایل | وضعیت |
|------|------|--------|
| `equation_advice.py` برچسب‌ها | :173-175 (advice_only/decision_effect/apply_effect) | **VERIFIED** |
| `shadow_influence.py` applied=false | :90-91 | **VERIFIED** |
| `shadow_evaluation.py` verdictها | :84,110,113,116 | **VERIFIED** |
| `limited_effect.py` رأی‌خوان + ۵ فیلد + ALLOWED_AS_PROPOSAL | :57-67,37-44,131 | **VERIFIED** |
| رأی `limited_effect_phase_n=3` | `owner-verdicts.yaml:112` | **VERIFIED** |
| test_phase_jn 13 تابع | `test_phase_jn.py` | **VERIFIED** |

### گروه C (اسناد) — VERIFIED

`AWARENESS-MEMORY-ASK-2026-08-12/` = 7 فایل (00, 07, 08, 09, 10, 11, FINAL) — همه موجود.
**توجه:** فایل‌های 04/05/06 در مگاپرامت جدید ادعا نشده‌اند — عدم وجودشان gap نیست.

### فایل‌های قفل‌شده — بدون تغییر غیرمجاز ✅

flags.cmd (ignored) · signals-registry.yaml · capabilities-registry.yaml · run_all.py ·
pulse_arbiter.py · chrono_rhythm/rhythm.py · ledger.py · policy_gate.py → همه CLEAN.
`EVIDENCE-LADDER.md`/`ROUTE-POLICY.md` تغییرات مطابق commit `1d28067` (awareness checkpoint) — سازگار.

---

## ۲. CONFLICTها (Class-1)

### C1 — chrono-rhythm-cr-b0: TESTED/SHADOW (Q3)
- `signals-registry.yaml:178-201` و `capabilities/chrono-rhythm-cr-b0.json:5-6`: truth_status=TESTED، evidence_level=SHADOW.
- **ارزیابی:** طبق نردبان خودِ validator (`SPEC→STRUCTURAL→TESTED→SHADOW→ARMED→LOCKED`)،
  TESTED(3) < SHADOW(4) → ادعا ≤ شواهد → **معتبر است** (ممیزی ترتیب نردبان را معکوس فرض کرده).
  → با `validate_signals_registry.py` راستی‌آزمایی می‌شود (فاز بعد).
- اگر validator رد کند → ثبت به‌عنوان CONFLICT واقعی و STOP (قفل).

### C2 — ADR-036 فایل ندارد (Q4)
- `owner-verdicts.yaml:94,106` · `organism.py:680` · `cortex/improve.py:354,486,534` ·
  `math_control/__init__.py:3` — به ADR-036 ارجاع می‌دهند؛ فایل `ADR-036*` وجود نداشت.
- **تصمیم (به‌روزرسانی 2026-08-12):** مالک «با همه موافقه» → رأی صریح → **ADR-036 ساخته شد**:
  `03 - Projects/research-spec-compiler/adr/ADR-036-math-control-spine.md` (ACCEPTED).
  شکاف C2 **بسته شد**. محتوا منعکس‌کنندهٔ spine.py واقعی + flags + رأی‌هاست؛ صفر تغییر کد.

---

## ۳. Call graph واقعی (خلاصه)

```
MiniApp (app.js renderAsk)
  ├─ collab (پیش‌فرض) POST /api/collab
  │    → collaborator.handle()
  │        → quarantine/draft gate (ADR-033)
  │        → conversation.handle() — 17 regex intent
  │        → [COLLAB_USE_MODEL=1] collab_model_adapter.complete()
  │            → _self_context (organism+truth+brains+owner_recall)
  │            → model_router.ask
  │        → owner_recall.recall_for_owner_ask → data.facts + «شاهد:»
  │        → equation_advice.equation_advice_snapshot() → data.equation_advice
  │        → collab_memory.append (content-free sha256)
  │    ← {schema:reply.v1, kind, text, keyboard, data{facts,equation_advice,...},
  │       model_source, external_effect:false, send_attempted:false}
  ├─ ask POST /api/ask
  │    → ask_vault.query (flag=1, hit→source=vault+sources[]+vault_empty)
  │    → ask_brain.ask (flag=1) → collab-fallback
  └─ mirror POST /api/mirror → mirror_room.ask
```

**امنیت (Q6):** هر ۴ مسیر پاسخ defense-in-depth؛ `_redact` دولایه در gateway؛
`external_effect=false` ساختاری؛ **صفر نشتی secret**. ✅

---

## ۴. شکاف‌های پیاده‌سازی (۱۳ مورد از call graph)

| # | شکاف | اثر |
|---|------|-----|
| M1 | **No session memory** — هر سؤال ایزوله؛ DOM-only log | مالک نمی‌تواند مکالمهٔ چندنوبته داشته باشد |
| M2 | **No equation explainer** — سؤال معادله → clarify | «BCM چیست؟» جواب معماری نمی‌گیرد |
| M3 | **No architecture explainer** | «Pulse Arbiter به چی وصله؟» → clarify |
| M4 | **equation_advice محاسبه ولی رندر نمی‌شود** | UI فقط facts/limitations را می‌خواند (app.js:2080-2099) |
| M5 | policy_version/evidence_plane/authorization_truth نامرئی | شواهد کنترل‌پلین در UI دیده نمی‌شود |
| M6 | data.rationale نامرئی | دلیل پاسخ همکار دیده نمی‌شود |
| M7 | vault sources فقط count در Ask mode | مسیر نوت‌ها دیده نمی‌شود |
| M8 | keyboard از collab رها می‌شود | پیشنهادهای inline دکمه‌ای نمی‌آیند |
| M9 | askLog در tab switch از بین می‌رود | گفت‌وگو با تعویض تب گم می‌شود |
| M10 | mirror source جزئیات ندارد | بدون provenance |
| M11 | shadow/effect وضعیت در پاسخ نیست | «آخرین shadow چه بود؟» جواب ندارد |
| M12 | intentهای business/evidence/improve/effect_request ناقص | ۱۰ intent هدف مگاپرامپت → ~۷ موجود |
| M13 | fact بدون source قابل نمایش | اعتبار ادعا بدون locator |

---

## ۵. طبقه‌بندی runtime معادلات (برای equation explainer — از کد، نه نام فایل)

| معادله | status واقعی | شاهد |
|--------|-------------|------|
| BCM | TESTED (advisory) | registry TESTED · wiring:1475 |
| Hebbian | TESTED | registry · wiring:1178-1397 |
| Pain/Nociceptor | TESTED (APPLY=1 → protective) | registry · brain_worker |
| Latent cosine | PROPOSAL_ONLY | بدون تست/registry/caller |
| Identity L/E/G/K/O | LOCKED/ACTIVE | registry LOCKED · spine:157-181 |
| SOG/DARE | LOCKED | registry · MC lock · spine:184-195 |
| Living-Beat control | TESTED/ACTIVE | organism:577 arbiter · test_heart_math |
| Allometry | SHADOW (flag OFF default) | cardiac.py · test |
| Phi-accrual | DIAGNOSTIC | chrono.py:130 · equation_advice |
| Spectral σ legacy | TESTED/ACTIVE (spine rank_bias) | spine:104-120 |
| connectivity_ratio_v2 | TESTED/DIAGNOSTIC | spectral_definitions |
| Chrono CR-B0 | TESTED/SHADOW (C1 pending) | rhythm.py advisory |
| CR-B1 Kuramoto | TESTED (pure) | test_rhythm |
| Decay-Reinforcement | BUILT/ADVISORY | coherence.py · partial test |
| Fusion φ_t | SHADOW | registry SHADOW · test_box |
| rho(J)/z | TESTED/DIAGNOSTIC | sensors.py · warden |
| rho_max warden | TESTED/ACTIVE (safety cap) | warden.py:60 |
| Kalman shadow | SHADOW | kalman_shadow_pipeline |
| Criticality v2 | SHADOW | registry |
| Spectral definitions | TESTED | test_spectral_definitions |

---

## ۶. تصمیم معماری (فاز P→U)

**بدون orchestrator جدید.** Collaborator موجود نقش unified router/assembler را دارد:
1. **P:** `_ops/memory/unified_context.py` — assembler واحد (owner_recall + brains + vault + equation_advice + runtime + shadow) → خروجی قرارداد واحد؛ اتصال در collaborator.
2. **Q:** `equation_explainer.py` (از جدول §۵) + `architecture_explainer.py` (read model از فایل/registry) + intentهای جدید در conversation.py.
3. **R:** app.js — رندر equation_advice/evidence/shadow/effect + vault paths + keyboard.
4. **S:** session memory سبک (localStorage frontend + اختیاری session_id backend) + «یادت بماند» → memory candidate.
5. **T:** shadow/effect visibility در پاسخ (شمارش records، آخرین divergence، proposal status).
6. **U:** تست‌ها + 4 گزارش (01-04).

**فایل‌های ممنوع/قفل:** لیست §۲ مگاپرامت — دست نمی‌خورند مگر رأی (C2 ثبت شد، ساخت نشد).
