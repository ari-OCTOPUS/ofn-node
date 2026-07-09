---
type: build-prompt
status: ready-for-handoff
created_by: agent
created: 2026-07-09
tags: [octopus, epistemics, build-prompt, non-destructive, shadow-theory]
source_theory: "[[07 - Knowledge/SHADOW-THEORY-5principles-v1]]"
source_audit: "[[00 - Inbox/2026-07-09 COHERENCE-AUDIT — intelligence layer wiring + walls (read-only)]]"
---

# PROMPT — لایهٔ Epistemics اختاپوس (پنج‌اصلِ SHADOW-THEORY)، ساختِ بدونِ‌تخریب

> این پرامپت را یک‌جا به سازنده (GLM/coder) بده. **همه‌چیز با هم**: فاز A (آف‌لوپ) + فاز B (وایرینگِ پشتِ فلگ) + اسپکِ ۵ متریک + گاردریل‌ها. مبنای نظری در `SHADOW-THEORY-5principles-v1` §۱ و §۹–§۱۳ است.

---

## ۰. نقش و هدف
تو سازندهٔ یک ماژولِ نوِ **read-only/advisory** به‌نامِ `epistemics` هستی که پنج متریکِ نظریه (شناسایی/کانال/سطح/خودارجاع/روش) را روی **داده‌های موجودِ** اختاپوس محاسبه می‌کند و به‌صورتِ **append-only** ثبت می‌کند. هدف: افزودنِ «هوشِ اندازه‌گیری» **بدونِ** تغییرِ رفتار، بدونِ تخریبِ داده، بدونِ تصادم با کدِ زندهٔ GLM.

---

## ۱. context سخت (قبل از هر کار بخوان)
- **لِجر append-only و hash-chain است:** `07 - Knowledge/genome-system/ledger/ledger.jsonl`. هر رکورد: `{id, ts, type, actor, payload, meta, prev, hash}` با زنجیرهٔ `prev`→`hash`. **هر بازنویسی = شکستنِ زنجیره = فساد.** (ناوردیِ I1)
- **سیستم module-rich/wiring-poor است و GLM هر ۳–۶ دقیقه `organism.py`/`wiring.py` را commit می‌کند** (طبقِ COHERENCE-AUDIT). **ویرایشِ موازیِ این فایل‌ها ممنوع** — بازنویسی/تصادم می‌شود.
- تنها enforcerِ سیستم `budget_gate` است (I2). این لایه **enforcer نیست**.
- ناوردی‌های حاکم: I1 append-only · I2 تک‌enforcer · I3 fail-closed · I7 پذیرشِ انسانی · walls (money-lock/live/secret/PII).

---

## ۲. قیدهای مطلق (DO / DON'T)
**DO**
- فقط **بخوان** از لِجر و `_ops/state/*`.
- خروجی را فقط با **type جدیدِ لِجر** `EPI_METRIC` **append** کن (از همان API/نویسندهٔ رسمیِ لِجر که hash-chain را حفظ می‌کند — ننویس مستقیم به فایل).
- state خودت را فقط در `_ops/state/epi-*.json` بنویس.
- همه‌چیز **paper/$0 · advisory · پشتِ flag · reversible**.

**DON'T**
- لِجر را mutate/بازنویسی نکن؛ رکوردِ موجود را دست نزن.
- `organism.py`/`wiring.py`/`unified_bus.py` را **موازی** ویرایش نکن (فاز B فقط هماهنگ با GLM).
- gate/block/enforce نکن؛ هیچ تصمیمِ سیستم را عوض نکن.
- به money/live/secret/PII/walls دست نزن.
- schemaی لِجر را تغییر نده (نه فیلدِ جدیدِ top-level، نه migration).

---

## ۳. چیدمانِ فایل (namespaceِ ایزوله)
```
_ops/epistemics/
  __init__.py
  contracts.py        # ثابت‌ها: LEDGER_TYPE="EPI_METRIC"، نسخهٔ schemaی payload
  readers.py          # فقط‌خواندن: ledger + state، بدونِ side-effect
  metrics/
    identifiability.py  # اصل ۱
    channel.py          # اصل ۲
    levels.py           # اصل ۳
    self_reference.py   # اصل ۴ (SOG)
    method.py           # اصل ۵ (conditional S⇒L)
  emit.py             # فقط append EPI_METRIC از طریقِ نویسندهٔ رسمیِ لِجر
  run_offloop.py      # فاز A: entrypointِ مستقل
  wire.py             # فاز B: wire_epistemics(organism) پشتِ flag — تا هماهنگی با GLM فراخوانی نشود
  test_epistemics.py
_ops/state/epi-latest.json   # خروجیِ خواندنیِ آخرین دور (نه لِجر)
```

---

## ۴. قراردادِ EPI_METRIC (append-only، بدونِ تغییرِ schema)
هر مشاهده یک رکوردِ لِجر با همان schema، فقط `type` و `payload` مالِ ما:
```json
{
  "type": "EPI_METRIC",
  "actor": "epistemics",
  "payload": {
    "epi_schema": "v1",
    "metric": "identifiability|channel|levels|self_reference|method",
    "value": { "...": "فیلدهای مخصوصِ هر متریک (§۵)" },
    "inputs_ref": ["debate/…","fitness-history",""],
    "advisory": "یک‌خط تفسیرِ advisory — هرگز دستور/گیت",
    "flag_state": "offloop|wired",
    "epi_run_id": "uuid"
  },
  "meta": { "paper": true }
}
```
`prev`/`hash`/`id`/`ts` را **نویسندهٔ رسمیِ لِجر** پر می‌کند (تو دستی hash نساز).

---

## ۵. اسپکِ پنج متریک (نگاشت به سیگنال‌های موجود — بدونِ سنسورِ نو)
> مرجعِ ریاضی: `SHADOW-THEORY-5principles-v1` §۲–§۶. اینجا فقط فرمِ عملیاتی.

**۱) identifiability** — ورودی: `_ops/debate/*` (فرضیه‌های رقیب)، `_ops/state/fitness-history.json`.
- محاسبه: روی مجموعهٔ فرضیه‌های رقیبِ یک تصمیم، $N_{\text{eff}}=e^{H(\text{posterior})}$ (perplexity)؛ $\Lambda=p(\text{best})/p(\text{null})$ که null=وضعِ‌موجود؛ با جریمهٔ MDL (هزینه per قاعده/پارامترِ اضافه).
- `value`: `{n_eff, lambda, n_candidates, mdl_penalty, decision_ref}` · advisory: «$N_{\text{eff}}$ بالا = تصمیم under-determined → دادهٔ بیشتر/انسان».

**۲) channel (DPI)** — ورودی: `telemetry-latest.json`+`telemetry/`، `_ops/reconcile/*`، `fitness-latest.json`.
- محاسبه: کیفیتِ بازساخت اثرِ قصد‌شده (H) از نتیجهٔ مشاهده‌شده (Ĥ): proxyِ $I(H;\hat H)$ و خطای بازسازی؛ برآوردِ سقفِ $C$ با سنسورهای فعلی.
- `value`: `{i_h_hhat, c_estimate, reconstruction_err}` · advisory: «$C$ پایین = observability gap».

**۳) levels ($L_G$)** — ورودی: توپولوژیِ `unified_bus.py`/`wiring.py` + فعالیتِ نودها از `_ops/state/*`.
- محاسبه: لاپلاسینِ گراف $L_G$؛ طیف؛ k مُدِ کُند (λ کوچک)=سطوحِ robust؛ zero-mode=مختصهٔ پایسته.
- `value`: `{slow_modes:[{lambda, top_nodes}], zero_mode_coord, k}` · advisory: «کدام aggregate واقعی است».

**۴) self_reference (SOG)** — ورودی: `_ops/doctor/*` (self-model) + baselineِ twin.
- محاسبه: $SOG=\text{err}^{\text{self}}-\text{err}^{\text{other}}$ با **twin-control** + **architecture-control** (با/بدونِ self-loop) + **capacity-scaling**.
- `value`: `{err_self, err_other, sog, kappa, arch_control:{with_loop, without_loop}, verdict:"capacity_artifact|candidate_barrier|underpowered"}`.
- **قید:** هرگز ادعای «تعالی» نکن؛ فقط verdictِ افقِ **کارکردی**. kill-condition طبقِ §۵.۱.

**۵) method (S⇒L)** — فقط گزارهٔ **شرطی**: «اگر ساختارِ S در داده دیده شد، قانونِ L مورد انتظار است». هرگز ادعای غیرشرطی/متافیزیکی.
- `value`: `{s_detected, l_expected, confidence}`.

---

## ۶. فاز A — آف‌لوپ (اول این؛ بدونِ تماس با فایلِ داغ)
- `run_offloop.py`: لِجر+state را می‌خواند، پنج متریک را حساب می‌کند، `EPI_METRIC` append می‌کند، `epi-latest.json` را می‌نویسد. **به تیکِ organism وصل نیست.**
- اجرا: دستی یا یک scheduled beat جدا. صفر تماس با `organism.py`/`wiring.py` → صفر ریسکِ تصادم.
- **DoD فاز A:** اجرا سبز؛ N رکوردِ `EPI_METRIC` در لِجر با زنجیرهٔ سالم (verify کن `prev/hash` نشکسته)؛ هیچ رکوردِ موجود تغییر نکرده؛ `epi-latest.json` نوشته شد؛ روی یک testbedِ کوچک با H معلوم، متریک‌ها با ground-truth کالیبره شدند (§Aی نظریه).

---

## ۷. فاز B — وایرینگِ پشتِ فلگ (فقط هماهنگ با GLM)
- `wire.py: wire_epistemics(organism)` یک قلابِ سبک در تیک، **پشتِ** `OCTOPUS_WIRE_EPISTEMICS` (پیش‌فرض **off**)، به‌سبکِ الگوی موجودِ `wire_doctor`/`doctor_beat`.
- **این تنها نقطهٔ تماس با فایلِ داغِ مشترک است** → در **یک پاسِ واحدِ هماهنگ با GLM** اعمال شود، نه موازی. اگر GLM زنده روی `organism.py` کار می‌کند، صبر کن/هماهنگ کن.
- **DoD فاز B:** با flag روشن، هر دور در تیک fire می‌شود، paper/$0، advisory (هیچ گیت/بلاک)، walls دست‌نخورده؛ با flag خاموش، عیناً مثلِ نبودنِ ماژول.

---

## ۸. تست و گیتِ capability
- `test_epistemics.py` بنویس (خواندنِ mock، تولیدِ EPI_METRIC، عدمِ mutate، رفتارِ flag on/off).
- **آن را به `run_all` اضافه کن** تا markerِ capability پوششش دهد (گَپِ neural که در audit آمد را تکرار نکن).
- یک تستِ صریح: بعد از اجرا، **hash-chainِ لِجر معتبر می‌ماند** و **تعدادِ رکوردهای غیر-EPI بدون تغییر** است.

---

## ۹. Definition of Done (کل)
1. namespaceِ `_ops/epistemics/` مستقل؛ صفر ویرایشِ موازیِ `organism.py`/`wiring.py`.
2. فقط `EPI_METRIC` append؛ zero schema-change؛ hash-chain سالم (تستِ اثبات).
3. advisory محض؛ non-enforcer؛ paper/$0؛ walls سالم.
4. فاز A سبز و کالیبره؛ فاز B فقط پشتِ flagِ off و آمادهٔ پاسِ هماهنگ.
5. `test_epistemics` در `run_all`، سوئیت سبز.
6. reversible: حذفِ پوشه یا flag=off → سیستم عیناً مثلِ قبل.

---

## ۱۰. فرمتِ گزارشِ پایان (چه چیزی به مالک برگردان)
- چه فایل‌هایی ساخته شد (فقط داخلِ namespace).
- تعدادِ `EPI_METRIC`های append‌شده + اثباتِ سلامتِ زنجیره.
- خروجیِ نمونهٔ هر متریک از `epi-latest.json`.
- تأیید: صفر تماس با فایلِ داغِ GLM، صفر mutate، flag=off.
- سؤال‌های باز / نقاطِ نیازمندِ هماهنگی با GLM (به‌ویژه فاز B).

> اگر هر مرحله با یک ناوردی یا wall در تضاد افتاد: **اجرا نکن**، تضاد را با منبع flag کن، جایگزینِ امن پیشنهاد بده.
