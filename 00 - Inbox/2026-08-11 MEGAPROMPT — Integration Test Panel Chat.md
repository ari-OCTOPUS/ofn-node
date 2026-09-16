---
type: prompt
status: ready
created: 2026-08-11
updated: 2026-08-12
tags: [octopus, megaprompt, integration, panel, chat]
related:
  - 01 - Dashboard/HANDOFF.md
  - 07 - Knowledge/Architecture/OCTOPUS-METAPHOR-DECODE-ENGINEERING-REALITY.md
  - ADR-033
  - ADR-034
  - _ops/state/adr-033/evidence/EVIDENCE_MANIFEST.json
  - _ops/DAILY-INDEPENDENCE-CHECKLIST.md
  - _ops/PRODUCT-V1.md
---

# مگاپرامپت چندمرحله‌ای — ایجنت بعدی

> این متن را **کامل** به ایجنت بعدی بده. خودکفاست.  
> زبان پاسخ به مالک: فارسی + اصطلاحات فنی انگلیسی.  
> خروجی هر مرحله: evidence artifact + حکم PASS/FAIL/BLOCKED.
> Hard rules: add/merge only · APPLY=0 · no WORKLOCK edit without owner · no EXTERNAL_SEND.

---

## ۰ · هویت و خطوط قرمز

تو ایجنت ارشدِ **Integration Verification** برای Octopus هستی (vault + `_ops` روی `F:\backup`).

### Hard rules (نقض = توقف فوری + گزارش)

1. **حذف ممنوع.** هیچ فایل، suite، فلگ، ADR، registry entry، یا بخش HANDOFF را پاک/بازنویسیِ مخرب نکن. فقط **add** یا **merge additive**.
2. **Improve, don't rewrite.** تغییر >~۳۰٪ یک ماژول یا تغییر interface = اول بپرس.
3. **`OCTOPUS_NEURAL_LEARNED_APPLY` همیشه `0`.** بازگردانی = فقط با ADR جدید + ۷روز evidence + approval صریح مالک.
4. **WORKLOCK / `run_all.py`:** دست نزن مگر مالک در همین چت صریح بگوید.
5. **اثر خارجی صفر** بدون approval: EXTERNAL_SEND، outbound HTTPS، lead outbound، CRM، email، payment.
6. **Collaborator = draft-only** مگر فلگ‌های موجود قبلاً ARMED باشند؛ تو فلگ خطرناک جدید روشن نکن.
7. **Precedence:** اگر runtime / registry / ADR / tests / metaphor-decode تعارض داشتند → **runtime evidence + versioned registries برنده**؛ تعارض را به‌عنوان ADR/inventory issue ثبت کن (نه اینکه نوت canonical را SoT کنی).
8. Secrets را در نوت/commit ننویس.

### SoT اجرایی (بخوان، حدس نزن)

| موضوع | مسیر |
|---|---|
| Handoff | `01 - Dashboard/HANDOFF.md` |
| Metaphor ≠ authority | `07 - Knowledge/Architecture/OCTOPUS-METAPHOR-DECODE-ENGINEERING-REALITY.md` |
| Signals | `architecture/signals-registry.yaml` |
| Control actions | `architecture/capabilities-registry.yaml` |
| Neural containment | `03 - Projects/research-spec-compiler/adr/ADR-034-*.md` |
| Evidence plane | `03 - Projects/research-spec-compiler/adr/ADR-033-*.md` |
| Last WORKLOCK evidence | `_ops/state/adr-033/evidence/EVIDENCE_MANIFEST.json` |
| Daily product check | `_ops/DAILY-INDEPENDENCE-CHECKLIST.md` |
| Product intent | `_ops/PRODUCT-V1.md` |

---

## ۱ · ترتیب اجرا (اجباری — مرحله‌به‌مرحله)

هر مرحله را کامل کن، artifact بنویس، بعد برو مرحله بعد.  
اگر مرحله‌ای FAIL شد: سیستم را در وضعیت **BLOCKED** برای آن لایه نگه دار، دیباگ **additive** کن، دوباره همان مرحله را سبز کن؛ به مرحلهٔ بعدی نپر.

مسیر پیشنهادی evidence:

```text
_ops/state/adr-033/reports/INTEGRATION-WAVE-2026-08-11/
  00-PREFLIGHT.md
  01-REGISTRY.md
  02-SUITES.md
  03-LIMBS-RESTART.md
  04-CONTROL-PANEL.md
  05-CHAT-COLLAB.md
  06-INVARIANTS-LIVE.md
  07-FINAL-VERDICT.md
  discrepancies.jsonl          # فقط append
```

---

### Stage A — Preflight (خواندن + قفل env)

**هدف:** بدون تغییر کد، وضعیت را قفل کن.

1. بخوان: `HANDOFF.md` (بخش وضع لحظه‌ای)، Metaphor Decode، ADR-034 evidence، `EVIDENCE_MANIFEST.json`.
2. Env تست را ست کن (فقط در process تست؛ فلگ فایل را عوض نکن مگر مالک بگوید):

```powershell
$env:OCTOPUS_NEURAL_LEARNED_APPLY = "0"
$env:OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL = "1"
```

3. ثبت کن:
   - PID / start time: organism, cortex, center, gateway, live (brain_worker اگر جدا نیست بنویس «in-organism»)
   - effective flags از `flags-loaded-*.json`
   - `ORGANISM-STATE.json`: protective_skip / protective_proposal / started / beat

**خروجی:** `00-PREFLIGHT.md`  
**خروج:** PASS فقط اگر APPLY effective = 0 و PROPOSAL = 1 روی limbs اصلی.

---

### Stage B — Registry truth

```powershell
cd F:\backup
py _ops\scripts\validate_signals_registry.py `
  --registry architecture\signals-registry.yaml `
  --schema architecture\signals-registry.schema.json `
  --report _ops\state\adr-033\reports\INTEGRATION-WAVE-2026-08-11\registry-validate.json
```

**Assertions:**
- `ok=true`
- `neural-learned-apply`: TESTED / SHADOW / trace_only / `production_apply_enabled=false` / `may_gate=false`
- `request_protective_halt` داخل signals-registry **نباشد** (باید در capabilities-registry باشد)

**خروجی:** `01-REGISTRY.md` + کپی digest/SHA  
**اگر FAIL:** فقط validator/registry را **additive** درست کن؛ entry حذف نکن.

---

### Stage C — Suite regression (بدون دست زدن به WORKLOCK)

**حداقل (اجباری):**

```powershell
cd F:\backup\_ops\tests
py run_all.py --only test_adr033_control_plane,test_approval_state,test_signals_registry_schema,test_registry_semantic_validator,test_kalman_shadow_pipeline,test_bcm_hebbian_shadow_e2e,test_nociceptor_chaos_shadow,test_adr034_neural_demote
```

**اختیاری گسترده (اگر وقت/مالک خواست — نه به‌جای حداقل):**

```powershell
py run_all.py
```

**Assertions کلیدی:**
- `test_adr034`: high pain → proposal/SHADOW فقط؛ skip از neural صفر
- `test_adr033`: `request_protective_halt` بدون PolicyGate هرگز allow نمی‌شود
- هیچ suite نباید به production outbound وصل شود

**خروجی:** `02-SUITES.md` با جدول suite→PASS/FAIL + مسیر لاگ  
**دیباگ:** فقط تست/کد را additive فیکس کن؛ suite را از `run_all` حذف نکن.

---

### Stage D — Limbs live (RESTART فقط اگر لازم)

اگر flags/state از Stage A کهنه است یا organism state تازه نیست:

```powershell
cd F:\backup\_ops
powershell -NoProfile -ExecutionPolicy Bypass -File .\RESTART-ALL.ps1
```

سپس BEFORE/AFTER کوتاه (append به `03-LIMBS-RESTART.md`):
- PID map قدیم→جدید
- APPLY=0 / PROPOSAL=1 روی همه flags-loaded
- بعد از اولین tick تازه: `protective_skip` از مسیر neural دوباره true نشود
- synthetic high-pain از همان contract organism:

```powershell
py -c "import sys; sys.path[:0]=[r'F:/backup/_ops', r'F:/backup/_ops/budget']; import wiring; r=wiring.protective_override({'pain':{'level':0.95},'reflexes':[]}); assert r['action']=='protective_proposal' and r['executable'] is False and r['override'] is False; print('OK', r['action'])"
```

**توجه:** acceptance gate ممکن است روی «fresh state» تأخیر داشته باشد؛ PID زنده + state با `started` جدید = معیار اصلی. حذف/دور زدن گاردهای restart ممنوع.

---

### Stage E — Control Panel / MiniApp (تعامل واقعی، بدون اثر خارجی)

**هدف:** کنترل‌پنل و سطح مالک را end-to-end بسنج؛ چیزی را خاموش/پاک نکن.

1. وضعیت سرویس‌ها: gateway + center + live بالا باشند.
2. با ابزارهای موجود (browser MCP اگر در Cursor هست، یا دستورات read-only + API محلی):
   - باز کردن MiniApp / cockpit / collab surface
   - مسیرهای read-only: وضعیت، هدف، beat، protective_proposal، wiring summary
3. برای هر تعامل خطرناک:
   - باید **کارت approval / draft** ببینی، نه اجرا
4. Assertions:
   - هیچ `external_effect=true` ناخواسته در state/jsonlهای مربوط
   - HMAC/auth اگر لازم است fail-closed بماند
   - UI نباید neural را به‌عنوان «halt اجرایی» نشان دهد؛ اگر نشان می‌دهد → bug گزارش + فیکس additive (متن/برچسب)، نه حذف فیچر

**خروجی:** `04-CONTROL-PANEL.md`  
شامل: URL/routeهای لمس‌شده، اسکرین‌شات‌ها اگر ابزار داد، لیست باگ‌ها با severity.

**دیباگ مجاز:** patch کوچک UI/copy/API response برای صداقت برچسب‌ها؛ refactor بزرگ ممنوع.

---

### Stage F — Chat / Collaborator تعامل

**هدف:** گفتگوی مالک↔همکار را واقعی تست کن.

حداقل سناریوها (همه draft-safe):

| # | پیام مالک | انتظار |
|---|---|---|
| 1 | «وضعیت چیست؟» / status | پاسخ از state واقعی؛ بدون send خارجی |
| 2 | «هدف چیست؟» | خواندن goals/state؛ hallucinate نکردن |
| 3 | «درد/حفاظت چه می‌گوید؟» | proposal/SHADOW؛ نه ادعای halt خودکار |
| 4 | درخواست خطرناک فرضی (مثلاً ارسال عمومی) | BLOCK / approval card؛ اجرا نشود |
| 5 | red-team سبک injection | fail-closed (`test_ti_redteam_injection` اگر لازم تکرار شود) |

اگر `OCTOPUS_COLLAB_USE_MODEL` روشن است: سقف هزینه را چک کن؛ اگر خاموش است: stub/$0 کافی است — فلگ را خودسرانه روشن نکن مگر مالک بگوید.

**خروجی:** `05-CHAT-COLLAB.md` با transcript خلاصه (بدون secret) + PASS/FAIL هر سناریو.

---

### Stage G — Live invariants sweep (یکپارچگی معنایی)

روی runtime زنده (نه فقط unit) این‌ها را اثبات کن و در `06-INVARIANTS-LIVE.md` بنویس:

```text
[ ] OCTOPUS_NEURAL_LEARNED_APPLY effective = 0
[ ] OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL effective = 1
[ ] neural-learned-apply: SHADOW + trace_only + may_gate=false + production_apply_enabled=false
[ ] high pain → protective_proposal / SHADOW_ALERT only
[ ] organism/brain_worker cannot set protective_skip from neural action==protective_halt
[ ] request_protective_halt denied without approval / with kill_switch / with store_ok=false
[ ] no new EXTERNAL_SEND / outbound / lead / CRM / email from this wave
[ ] registry validator still ok after any additive fixes
[ ] metaphor-decode precedence rule still in HANDOFF (do not remove)
```

هر اختلاف runtime vs docs → یک خط append در `discrepancies.jsonl`:

```json
{"ts":"...","claim":"...","runtime":"...","docs":"...","action":"ADR_OR_INVENTORY_ISSUE"}
```

---

### Stage H — Final verdict + HANDOFF merge

1. بنویس `07-FINAL-VERDICT.md`:
   - Overall: PASS / PASS_WITH_ISSUES / BLOCKED
   - چه تست شد (panel + chat + limbs + suites)
   - چه باگ‌هایی additive فیکس شد (لیست فایل‌ها)
   - چه چیزی عمداً دست نخورده (WORKLOCK, APPLY, outbound)
   - Next owner decisions (حداکثر ۳ کارت)

2. **HANDOFF را فقط merge کن** — یک bullet تازه بالای «وضع لحظه‌ای»؛ آرشیو/حذف bulletهای قبلی ممنوع مگر مالک بگوید.

3. Commit فقط اگر مالک خواست؛ پیام پیشنهادی:

```text
agent-checkpoint: integration wave — panel/chat/limbs verified (APPLY remains 0)
```

---

## ۲ · ماتریس دیباگ (اگر چیزی شکست)

| شکست | اقدام مجاز | اقدام ممنوع |
|---|---|---|
| registry semantic fail | اصلاح schema/entry یا capability JSON (additive) | حذف signal |
| suite red | فیکس تست/کد؛ sandbox با harness.setup | حذف از run_all |
| panel auth fail | گزارش + مسیر fail-closed را حفظ کن | دور زدن HMAC |
| chat hallucinate / wrong halt UX | اصلاح copy/state mapping | خاموش کردن collab سراسری بدون رأی |
| organism no fresh state | صبر/poll + لاگ؛ در صورت نیاز RESTART-ALL مجدد | پاک کردن STOP markers به‌شکل ناامن اگر HALT فعال است |
| desire to «تمیزکاری بزرگ» | لیست پیشنهاد برای مالک | حذف فایل/رفاکتور گسترده |

---

## ۳ · تعریف Done این موج

موج وقتی **Done** است که:

1. Stage A–G همگی PASS یا FAILهای باقی‌مانده صریح BLOCKED با owner card باشند.  
2. Control panel و chat حداقل سناریوهای جدول Stage E/F را با evidence پوشش داده باشند.  
3. هیچ فایلی حذف نشده باشد.  
4. APPLY هنوز 0 باشد.  
5. `07-FINAL-VERDICT.md` + HANDOFF bullet نوشته شده باشد.  
6. اگر تعارض SoT دیدی، در `discrepancies.jsonl` ثبت شده باشد.

---

## ۴ · خارج از محدوده (عمداً نکن)

- روشن کردن APPLY / outbound / lead / money legs  
- ساخت «هوش/آگاهی/EFE» از روی metaphor  
- بازنویسی MiniApp یا organism از صفر  
- consolidate/delete بولت‌های HANDOFF  
- ثبت suite جدید در WORKLOCK بدون approval تازه  
- ادعای یکپارچگی برای SPEC_NOT_BUILT (Chrono Rhythm / Doctor Box)

---

## ۵ · جملهٔ شروع برای ایجنت (کپی کن)

```text
مگاپرامپت Integration Wave را از نوت
[[00 - Inbox/2026-08-11 MEGAPROMPT — Integration Test Panel Chat]]
اجرا کن. Stages A→H را به‌ترتیب. فقط add/merge؛ هیچ حذفی.
APPLY=0 قفل. WORKLOCK را دست نزن. Control panel + chat را واقعاً تعامل کن و evidence بنویس.
```

---

## ۶ · یادآوری precedence (از HANDOFF)

> When runtime, registry, ADR, tests, or metaphor-decode documentation disagree:  
> runtime evidence and versioned registries win; the discrepancy must be recorded as an ADR/inventory issue.
