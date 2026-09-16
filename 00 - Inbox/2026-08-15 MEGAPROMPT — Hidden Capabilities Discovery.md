---
type: knowledge
kind: megaprompt
status: active
created: 2026-08-15
updated: 2026-08-15
created_by: agent
audience: next-agent
tags: [octopus, megaprompt, dark-capabilities, hidden, discovery, propose-only]
sources:
  - "[[00 - Inbox/2026-08-15 SELF-CONTAINED — Architecture Deep-Scan for External Agents]]"
  - "[[00 - Inbox/2026-08-11 OWNER — Focus AI Core Hidden Capabilities]]"
  - "[[00 - Inbox/2026-08-11 DISCOVERY — AI Core Hidden Capabilities Report]]"
  - "[[_ops/dark_capabilities]]"
  - "[[_ops/orphan_scan]]"
  - "[[_ops/effector_registry]]"
  - "[[_ops/capability_registry]]"
---

# MEGAPROMPT — کشف قابلیت‌های پنهان اختاپوس (2026-08-15)

> **مالک:** کل این فایل را به ایجنت بده. حدس نزند؛ اسکنرهای موجود را اجرا کند.
> **ایجنت:** تو کاشف هستی، نه مسلح‌کننده. خروجی = کاتالوگ + حداکثر ۵ کارت رأی.
> تاریخ نوشتن: 2026-08-15 ~23:05 Sydney. HEAD تقریبی `576c7fb`. اعداد کهنه را باور نکن.

```text
نقش: Senior Capability Forensic — OCTOPUS
ماموریت: بگو چه چیزی ساخته شده و مالک نمی‌بیند / نمی‌دود / دو نسخه است.
ممنوع: مسلح‌کردن فلگ · send · pay · git-apply · merge · restart زنده · بازنویسی
خط حقیقت: octopus-ai-core + hidden-capability-discovery
       != money-legs-live != AGI-claim != «همه را روشن کن»
```

---

## ۰. نقش و تعریف «پنهان»

«پنهان» در این سیستم **یک چیز نیست.** اسکنر `dark_capabilities.py` فقط کلاس ۱ را می‌پوشاند. تو باید **هشت کلاس** را جداگانه شکار کنی. قاطی‌کردنشان = گزارش دروغ.

| کلاس | معنی | ابزارِ موجود |
|---|---|---|
| **۱ DARK flag** | کد فلگ را می‌خواند؛ در `OCTOPUS-flags.cmd` مسلح نیست؛ در PAPER_FULL_FLAGS هم نیست؛ در هیچ پروسهٔ زنده ON نیست | `dark_capabilities.scan()` |
| **۲ PARTIAL** | در بعضی پروسه‌ها ON، در بعضی نه — بدترین حالت (نیمِ سیستم خیال می‌کند قابلیت هست) | همان + `flag_drift.probe_all()` |
| **۳ orphan_armed** | در فایل فلگ =1 ولی **هیچ ذکر تولیدی** ندارد (تایپو / کد حذف‌شده / runner_apply historically) | `dark_capabilities` → `orphan_armed` |
| **۴ TUNING** | `getenv` با پیش‌فرض دارد و با `"1"` مقایسه نمی‌شود ⇒ **به هر حال می‌دود**؛ دروازه نیست | `state=TUNING` |
| **۵ یتیمِ کد** | ماژول کامل + تست، صفر importer، بیرون از `card()` SCAN_DIRS | `orphan_scan.py` (عمداً کم‌گزارش؛ کف است نه سقف) |
| **۶ DEAD-OUTPUT / display-only** | حس تولید می‌شود؛ تصمیم نمی‌سازد | `effector_registry.EFFECTORS` — **verify با rg، رجیستری ۰۸-۰۸/۱۲ کهنه می‌شود** |
| **۷ نامرئیِ سطح** | `card()` دارد ولی پوشه‌اش در `capability_registry.SCAN_DIRS` نیست ⇒ تلگرام نمی‌بیند | مقایسه SCAN_DIRS با درخت `_ops/` |
| **۸ دو-نسخه / IMPLEMENTED_NOT_*** | قابلیت دوم که شبیه اول است یا STATUS صریح unwired | `__init__.py` STATUS + ADR-040/042 + `agi2027_control` |

کلاس ۸ قابلیت برای «روشن کردن» نیست — بوی معماری است. در کاتالوگ جداگانه با برچسب `DO-NOT-ARM — dual-stack` بیاور.

---

## ۱. قواعد سخت — نقض = توقف

1. **شواهد نه ادعا.** هر ردیف: مسیر فایل + فلگ + state اسکنر + `rg` یک‌خطی. سطح A (همین جلسه اجرا کردم) / B (ایجنت دیگر) / C (فقط سند).
2. **هیچ مقدار فلگ/secret چاپ نشود.** فقط نام. `.env` را باز نکن. الگوی TOKEN/KEY/SECRET را از `flag_drift.is_secret_name` قرض بگیر — تعریف دوم نساز.
3. **فلگ روشن نکن.** حتی «کم‌ریسک». کارت رأی بنویس. `OCTOPUS-flags.cmd` را ننویس.
4. **restart / send / pay / git-apply / merge / push ممنوع.**
5. **Improve, don't rewrite.** اسکنر نو نساز مگر یک کلاس بالا اصلاً ابزار ندارد — اول همان هشت ابزار را اجرا کن.
6. **`.claude/worktrees` و `_Archive` را نپیما.** `dark_capabilities` عمداً skip می‌کند (۵.۵GB، ۹۶٪ رونوشت). اسکن از ریشهٔ vault = خواباندن لپ‌تاپ.
7. **import نکن ۲۵۰ ماژول را.** کشف نحوی است. `import wiring` = اجرای `apply_profile` روی env همین پروسه.
8. **تست را شاهد زنده‌بودن نگیر.** تستی که فلگ را set می‌کند مصرف‌کنندهٔ تولیدی نیست — اسکنر تست‌ها را skip می‌کند؛ تو هم.
9. **نبودِ snapshot ≠ همه خاموش.** اگر `live_source != "live"` بگو «نمی‌دانمِ قوی» نه «DARK مطلق». درس قفل‌شده: اولین اجرا ۲۵۷/۲۵۷ تاریک دروغ گفت چون `ORGANISM-STATE.json` کلید `flags` ندارد. حقیقت زنده = `state/flags-loaded-*.json` per-process.
10. **WORKLOCK:** `run_all.py` · `wiring.py` · `center.py` · `orphan_scan.py` — اگر تست نو نوشتی، نام را گزارش کن؛ خودت در `run_all` ثبت نکن.
11. **شورای دوم NO-GO** برای اجرای خودمختار/پیامددار برقرار است. کشف ≠ مجوز اثر.
12. **Honesty:** بدون ادعای AGI / آگاهی. `claimed ≠ درآمد`.
13. **شناسه تناقض آزاد: C-016.** قبل از تخصیص هر دو مخزن را grep کن.
14. **Meta Rule of Two:** در یک جلسه همزمان untrusted input + داده حساس + اثر خارجی نداشته باش. این مأموریت اثر خارجی ندارد.

---

## ۲. اعداد کهنه — این‌ها را در گزارشت ننویس مگر با برچسب STALE

| ادعا | تاریخ | چرا مرده |
|---|---|---|
| ۱۲۸ dark از ۳۲۶ | نوت ۲۶ / ~۰۸-۰۷ | مستقل ۰۸-۰۸: ۶۴ از ۳۴۷ |
| ۶۴ dark از ۳۴۷ | ۰۸-۰۸ | قبل از batch-arm ۶۳ فلگ (۰۸-۰۹) |
| ۲۲ dark از ۳۶۸ | گزارش کشف ۰۸-۱۱ | بعدش Talk Discovery / Hub / Hypothesis / Epistemic / APPLY مسلح شدند |
| «COLLAB_USE_MODEL تاریک» | گزارش ۰۸-۱۱ §C | همان شب ARMED شد |
| «CORTEX_CONSOLIDATE ست نشده» | نوت‌های ۰۸-۰۶ | **غلط** — پروسه زنده با آن می‌دوید |
| ORGANISM-SPEC «یک پروسه» | ۰۷-۰۷ | زنده = پنج proسه |
| `capability_registry` SCAN_DIRS کامل است | کد | conversation_hub / epistemics / hypothesis_engine / math_control / memory / … داخلش نیستند |

گزارش ۰۸-۱۱ **روش** است نه موجودی. روش را نگه دار؛ موجودی را از نو بساز.

---

## ۳. Ground truth — از اینجا شروع کن (حدس نزن)

### ۳.۱ اسکنرهای موجود (به ترتیب اجرا)

```text
# از F:\backup — فقط نام فلگ، هرگز مقدار
python -X utf8 _ops/dark_capabilities.py
python -X utf8 _ops/dark_capabilities.py --json   > 00 - Inbox/_scratch-dark.json
python -X utf8 _ops/flag_drift.py
python -X utf8 _ops/orphan_scan.py
```

بعد، بدون ساختن ابزار نو:

| چیست | کجا |
|---|---|
| دروازهٔ تاریک | `_ops/dark_capabilities.py` · تست: `_ops/tests/test_dark_capabilities.py` |
| رانش مسلح↔لودشده | `_ops/flag_drift.py` · snapshotها: `_ops/state/flags-loaded-*.json` |
| یتیمِ ماژول | `_ops/orphan_scan.py` |
| حس بدون اکچوئیتور | `_ops/effector_registry.py` — verify با `rg` |
| کارت تلگرام | `_ops/capability_registry.py` → `SCAN_DIRS` (ناقص) |
| نردبان شواهد ADR-033 | `_ops/capabilities/*.json` (۷ فایل) |
| پل حکم→کد | `_ops/capabilities.py` |
| فهرست AST `card()` | همان registry؛ `SCAN_DIRS` را با `os.listdir(_ops)` تفاضل بگیر |
| STATUS unwired | `_ops/action_bridge/__init__.py` · `unified_control/` · `owner_console/__init__.py` (STATUS ممکن است کهنه باشد — collaborator **wired** است) |
| PolicyGate دوم | `_ops/agi2027_control/` |
| Hub در برابر collab | `_ops/conversation_hub/` vs `owner_console/collaborator.py` |
| Observability vs اجرا | `_ops/epistemics/` (`may_execute=False`) · `hypothesis_engine/` |
| 4d | `_ops/cortex/fourd_health.py` observe-only · `4d_system` را attach نکن |

### ۳.۲ فلگ‌های زندهٔ امشب (last-wins در `OCTOPUS-flags.cmd` ~1470–1482) — برای تضاد، نه برای اعتماد

`OCTOPUS_UNIFIED_CHAT=1` · `CORTEX_HYPOTHESIS=1` · `EPISTEMIC_TESTS=1` · `OCTOPUS_WIRE_VAULT_RAG=1` · `OCTOPUS_WIRE_DOCTOR_TG=1` · `OCTOPUS_NEURAL_LEARNED_APPLY=1` · `OCTOPUS_OBSERVE_4D=1` · `OCTOPUS_WIRE_KILL_SEAM=1` · `FUGU_VIA_CENTRAL_GATE=0` · `STUDIO_LLM_CLOUD_VIA_ROUTER=0`

**[TENSION]** شورا: `CORTEX_HYPOTHESIS` باید ۰ بماند. زنده = ۱ (رأی مالک ۰۸-۱۵). این را «کشفِ قابلِ آرم» ننویس — از قبل روشن است. در کاتالوگ: `ALREADY-ON / council-conflict`.

### ۳.۳ هرگز به‌عنوان «پنهانِ ارزشمند برای آرم» پیشنهاد نکن

- `OCTOPUS_INITIATIVE_UNCAPPED`
- مسیر پول: `OCTOPUS_ENFORCE_MONEY_FSM` / `OCTOPUS_WIRE_VALUE_LEDGER` / `LIVE-ENABLED` / harvest / lead outbound — مگر مالک صریح بگوید (الان خط حقیقت این فاز نیست)
- `STUDIO_LLM_CLOUD_VIA_ROUTER` — کسب‌وکار زنده
- `brain_core` promote و `4d` attach — **هرگز هم‌زمان**؛ هیچ‌کدام در این مأموریت
- `FUGU_VIA_CENTRAL_GATE` بدون رأی جدا (4d DEPRECATED)
- هر چیزی با `external_send` / `payment` / SMTP
- ساخت اسکنر موازی به‌جای خواندن خروجی همین‌ها

### ۳.۴ پنج پروسه

organism :8771 · cortex :8772 · live :8773 · gateway :8774 · center lock :8776. PARTIAL یعنی بین این‌ها شکاف است. `flags-loaded-*.json` را بخوان — ORGANISM-STATE را برای فلگ نه.

---

## ۴. فازها (ترتیب اجباری)

### فاز A — تصویر زنده (۴۵–۹۰ دقیقه، فقط‌خواندنی)

1. `CURRENT-TRUTH.md` beat/halted/HEAD.
2. هر سه CLI بالا. اگر `live_source != live` → در گزارش بنویس و **حکم DARK را تضعیف کن**؛ پیشنهاد restart نده مگر مالک بخواهد (خارج از این مأموریت).
3. جدول خلاصه: `n_flags / n_dark / n_partial / n_tuning / n_orphan_armed / live_source / process names`.
4. `flag_drift`: کدام پروسه کد کهنه دارد (فایل عوض شده، ری‌استارت نشده).
5. `orphan_scan`: فقط `weighty` را در کاتالوگ اصلی بیاور (۲۰ اول CLI کافی نیست — JSON کامل).

DoD A: یک جدول اعداد **با فرمان منبع‌دار** + فایل JSON اسکرچ (secret-free). اگر عدد با نوت ۰۸-۱۱ فرق داشت، نوت را «باطل برای موجودی» اعلام کن نه «اسکنر خراب است».

### فاز B — طبقه‌بندی هر DARK / PARTIAL / orphan_armed

برای **هر** ردیف DARK و PARTIAL (نه فقط ۶ تای صدر `card()`):

| فیلد | محتوا |
|---|---|
| flag | نام |
| class | 1–8 |
| readers | مسیرها از اسکنر |
| bucket | `ai-core` / `memory` / `ops-surface` / `money-lead` / `dangerous` / `dead-name` / `dual-stack` |
| ladder | STRUCTURAL / TESTED / SHADOW / ARMED (از کد+تست+capabilities JSON — حدس نه) |
| arm_risk | none / owner-chat-ok / needs-vote / never |
| note | یک جمله: اگر روشن شود چه **رفتاری** عوض می‌شود |

PARTIAL را بالاتر از DARK مرتب کن. orphan_armed را جدا: احتمالاً تایپو — پیشنهاد rename/document نه «روشن‌ترش کن».

Bucket `dangerous` پیش‌فرض: money, uncapped, outbound HTTPS, SMTP, code-apply production, runner-apply اگر واقعاً apply می‌شود (آخرین حقیقت: `armed_inert` / `apply_module_present: False` — **verify**).

### فاز C — کلاس‌های ۵–۸ (اسکنر فلگ نمی‌بیند)

حداقل این تفاضل‌ها را روی دیسک انجام بده:

1. `SCAN_DIRS` در `capability_registry.py` در برابر پوشه‌های `_ops/*/`. هر پکیج با `card()` یا `__init__.py` که در SCAN_DIRS نیست = کلاس ۷.
2. `rg -n "STATUS = " _ops --glob __init__.py`. هر `IMPLEMENTED_NOT_*` را باز کن و با import واقعی بسنج (owner_console STATUS ممکن است دروغ باشد چون collaborator wired است — الگوی C-015).
3. `effector_registry.EFFECTORS`: برای هر `dead-output` / `display-only` یک `rg` روی نام فیلد. اگر مصرف‌کنندهٔ تصمیم پیدا شد، رجیستری را در گزارش «کهنه» علامت بزن — فایل رجیستری را بدون رأی بازنویس نکن.
4. `_ops/capabilities/*.json`: `enabled` / `production_caller` / flag را با اسکنر زنده تطبیق بده. نمونهٔ شناخته‌شده: `criticality-v2.json` enabled:false در برابر فلگ OTLP later=1؛ `bayes-engine.json` `production_caller: NOT_FOUND`.
5. Dual: PolicyGate دوم، دو کلاینت تلگرام، Hub vs `/api/collab`. این‌ها را در بخش «پنهانِ خطرناک» بیاور نه «پتانسیل آرم».

DoD C: فهرست کلاس ۷ (نامرئی تلگرام) + فهرست STATUS دروغین/درست + حداقل ۵ DEAD-OUTPUT راستی‌آزمایی‌شده.

### فاز D — ارزش برای مالک (AI-core فقط)

از bucket `ai-core` حداکثر **۸** نامزد بساز، مرتب بر `(ارزش تصمیم مالک × کم‌ریسکی × تعداد خواننده)`.

برای هر نامزد یک بلوک:

```text
NAME: <flag or module>
WHY_HIDDEN: class 1–8
WHAT_IT_DOES: یک پاراگراف از کد (نقل مسیر:خط)
LADDER_NOW: STRUCTURAL|TESTED|SHADOW
IF_ARMED: چه رفتار قابل‌مشاهده‌ای در MiniApp/تلگرام عوض می‌شود
PROOF_WITHOUT_MONEY: نام تست موجود یا طرح تست نو (فایل یکتا در _ops/tests/)
RISK: اثر خارجی؟ پول؟ ارسال؟ خودتغییری TCB؟
RECOMMEND: leave-dark | shadow-only | owner-vote-to-arm | never
COUNCIL: آیا با NO-GO / PEP / evaluator تضاد دارد؟
```

پیش‌فرض‌های عقل سلیم (باطل کن اگر کد خلاف گفت):

- خودپایشی / route_scorer / semantic_trace / collab_memory → غالباً `owner-vote-to-arm` یا `shadow-only`
- Hypothesis Engine → `ALREADY-ON / council-conflict` نه کشف
- Epistemics → cabin؛ `may_execute` را دست نزن
- Action Bridge / unified_control → `leave-dark` تا PEP (R20a)؛ «وصلش کن» = دور زدن شورا
- Runner apply → verify inert؛ اگر inert است `dead-name`

### فاز E — کارت رأی برای مالک (حداکثر ۵)

مالک از گوشی رأی می‌دهد. هر کارت ≤ ۱۲ خط:

```text
[VOTE n] <نام یک‌خطی>
الان: <DARK|PARTIAL|invisible|dead-output>
پیشنهاد: leave / shadow / arm
اگر arm: فقط این فلگ: <NAME>
ریسک: <یک جمله>
اثبات بعد: <یک فرمان تست>
نه: <چه چیزی را قاطی نکنیم>
```

بیش از ۵ کارت = مالک هیچ‌کدام را نمی‌خواند. بقیه در پیوست کاتالوگ بمانند.

### فاز F — تحویل

یک نوت:

`00 - Inbox/2026-08-15 DISCOVERY — Hidden Capabilities Catalog.md`

بخش‌ها: خلاصهٔ اجرایی (جدول اعداد زنده) · کاتالوگ کلاس ۱–۴ · کلاس ۵–۸ · ۸ نامزد AI-core · ۵ کارت رأی · چیزهایی که عمداً تاریک ماندند · اعداد STALE که باطل کردی · کار بعدی (نه DEBT-SWEEP، نه اتصال 4d).

اگر >۵ فایل لمس شد: از مالک بپرس برای `agent-checkpoint:` — خودت commit نکن مگر بگوید.

HANDOFF: فقط یک پین wikilink، کپی محتوا نه.

---

## ۵. تله‌های شناخته‌شده (اگر افتادی، گزارش خراب است)

1. `PAPER_FULL_FLAGS`: غیاب در فایل برای اعضای این tuple یعنی **روشنِ ضمنی** بعد از `apply_profile`. اسکنر این را `profile_on` می‌داند. تو «در flags.cmd نیست پس تاریک» نگو.
2. Last-wins در `OCTOPUS-flags.cmd` (۱۴۸۲ خط). فلگ را در چند جا set می‌کند؛ حکم = آخرین. `rg` همه‌اش را نشان بده.
3. `flag()` در `wiring.py` شکل غالب خواندن است. اسکنر `getenv`/`get`/`flag` را می‌بیند. اسکن دستی فقط `os.environ` = از دست دادن ~نیمی از سطح (درس خودِ ماژول).
4. `OCTOPUS_STATE_DIR` دروازه نیست؛ مسیر است. TUNING/noise.
5. `card()` در `dark_capabilities` فقط ۶ تاریکِ پرخواننده را نشان می‌دهد. تو همه را در JSON ببین.
6. Collaborator wired است؛ `owner_console/__init__.py` ممکن است هنوز `IMPLEMENTED_NOT_WIRED` بگوید.
7. C-015: اسناد (COUNCIL-MESH) هنوز می‌گویند حافظه 4d write-only — کد ۰۸-۱۵ وصل شد. سند را موجودی نگیر.
8. Worktree `.claude` را اسکن کردن = ۹۶٪ رونوشت.
9. `run_all.py` از ریشه pytest نیست؛ تست‌های `_ops` اغلب اسکریپت خوداعتبارسنج‌اند.
10. سبز بودن تست ≠ ARMED. نردبان: STRUCTURAL < TESTED < SHADOW(≈۷روز) < ARMED.

---

## ۶. نردبان شواهد (قبل از «داریم»)

از ADR-033 / HONESTY:

- **STRUCTURAL** — فایل وجود دارد
- **TESTED** — تست سبز روی رفتار (نه فقط import)
- **SHADOW** — روی زنده می‌نویسد/می‌خواند بدون اثر خارجی، با provenance
- **ARMED** — فلگ ON در **همه** پروسه‌های مربوط + رفتار قابل مشاهده

جملهٔ ممنوع: «کد کامل است پس کار می‌کند.» همین جمله علت وجود `dark_capabilities` است.

---

## ۷. خروجی ممنوع / خروجی واجب

**واجب:** کاتالوگ Inbox · جدول اعداد با فرمان · حداکثر ۵ کارت رأی · باطل کردن اعداد STALE · جدا کردن dual-stack از dark-flag.

**ممنوع:** روشن کردن فلگ · «همه را آرم کن» · وصل کردن Action Bridge به عنوان کشف · promote brain_core · attach 4d · ادعای AGI · چاپ مقدار env · اسکن `.claude` · ویرایش WORKLOCK files · ساختن داشبورد Grafana/Redis/LangGraph · بازنویسی `wiring.py`.

---

## ۸. Opener کپی‌پیست (اولین پیام به ایجنت)

```
تو کاشف قابلیت‌های پنهان اختاپوس هستی، نه مسلح‌کننده.
کل مگاپرامپت «کشف قابلیت‌های پنهان اختاپوس (2026-08-15)» را اجرا کن.
فاز A→F به ترتیب. اسکنرهای موجود را اجرا کن؛ ابزار موازی نساز.
اعداد نوت‌های ۰۸-۰۷/۰۸/۱۱ را STALE فرض کن.
هشت کلاس پنهان را جدا نگه دار. Dual-stack را آرم نکن.
خروجی: 00 - Inbox/2026-08-15 DISCOVERY — Hidden Capabilities Catalog.md
+ حداکثر ۵ کارت رأی برای مالک.
فلگ روشن نکن. send/pay/restart/git-apply نکن.
```

---

## Sources

`_ops/dark_capabilities.py` · `_ops/flag_drift.py` · `_ops/orphan_scan.py` · `_ops/effector_registry.py` · `_ops/capability_registry.py` · `_ops/capabilities/*.json` · گزارش کشف 2026-08-11 (روش، نه موجودی) · Architecture Deep-Scan 2026-08-15 · شورای دوم NO-GO · `OCTOPUS-flags.cmd` last-wins
