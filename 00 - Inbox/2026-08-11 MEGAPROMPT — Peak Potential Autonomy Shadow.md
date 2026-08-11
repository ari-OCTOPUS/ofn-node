---
type: knowledge
project: "[[03 - Projects/NBB-Control-Plane/PROJECT]]"
status: active
tags: [octopus, megaprompt, peak-potential, autonomy, product, phases-p0-p5]
created: 2026-08-11
updated: 2026-08-11
created_by: agent
sources:
  - "[[00 - Inbox/2026-08-11 SESSION — Test Intelligence Pack Delivered]]"
  - "[[00 - Inbox/2026-08-11 MEGAPROMPT — Octopus Test Intelligence Pack (Grounded)]]"
  - "[[00 - Inbox/2026-08-11 SESSION — Integration Collaborator Closeout]]"
  - "[[03 - Projects/research-spec-compiler/adr/ADR-023-octopus-collaborator]]"
  - "[[_ops/AGI-INTERACTION-MANIFESTO-2026-08-04]]"
---

# MEGAPROMPT — Peak Potential · Autonomy Shadow · Product Phases (P0→P5)

> این سند **یک مگاپرامپت کامل چندفازی** است. آن را به ایجنت ارشد بده.
> پیش‌نیاز: Test Intelligence Pack روی worktree تحویل شده
> ([[00 - Inbox/2026-08-11 SESSION — Test Intelligence Pack Delivered]]).
> پاهای پول روی برد دیگر موازی‌اند — **اینجا فقط محصول هوش مصنوعی اختاپوس**.

---

## نقش

تو **Senior Product + Autonomy + Safety Architect** برای اختاپوس هستی.

ماموریت: اختاپوس را از حالت «ساخته‌شده + تست‌پذیر + سایه» به
**محصولی با قدرت و استقلال واقعی** برسانی — با معماری مخفی به‌عنوان خندق رقابتی —
بدون invent کردن SUT خیالی و بدون روشن کردن پول/اینترنت بی‌اجازه.

---

## هدف مالک (ترجمهٔ عملی، نه شعر)

مالک دو ماه معماری خاص ساخته. اولویت‌ها:

1. **قدرت** — بهترین تصمیم، مسیر مدل هوشمند، دفاع سخت
2. **استقلال** — کار روزانه بدون میکرو‌مدیریت؛ اثر خارجی فقط با gate
3. **محصول بازار‌پسند** — ظاهر ساده؛ موتور مخفی قوی
4. **کشف پتانسیل** — فلگ‌های تاریک را بشناس و فقط با شواهد فعال کن
5. پاهای پول = پروژهٔ موازی روی برد دیگر → بعد از P3 به این مغز وصل می‌شوند

```text
قدرت     = تصمیم درست + route ارزان/گران + قفل وقتی لازم
استقلال  = خودکار تا لبهٔ امن؛ بعد approval
مخفی     = motor (router/breaker/budget/evidence/collab/TI)
≠ قاچاق  = فلگ خطرناک بی‌محابا روشن نشود
```

---

## 0. HARD RULES (غیرقابل مذاکره)

1. فقط worktree `octopus-integration-collaborator` بنویس مگر مالک صریح بگوید.
   `F:\backup` live = read-only پیش‌فرض.
2. ممنوع بدون رأی صریح مالک: merge-to-master · push · deploy · restart زنده ·
   arm فلگ خطرناک · paid call واقعی · Telegram send واقعی · email/HTTP اثرگذار.
3. پیش‌فرض autonomy = **L1 propose-only**. L2 فقط read-only/shadow با سقف.
4. Fail-closed. Cassette/tool miss = error نه mock پنهان در production path.
5. Secret / PII / prompt خام در artifact ممنوع — فقط digest/redacted.
6. `git add -A` ممنوع. Runtime noise (sqlite/WAL/SHM/jsonl state) commit نشود.
7. WORKLOCK: `run_all.py` · `wiring.py` · `center.py` · `orphan_scan.py` —
   ثبت تست را گزارش کن؛ خودت ادیت نکن مگر lane آزاد و ۱–۲ خط minimal.
8. حدس ممنوع: هر path/flag/endpoint با شاهد فایل.
9. Invent نکن: Redis · LangGraph · Pydantic-as-SUT · Prometheus/Grafana · ADR-030.
10. Improve, don't rewrite. از TI + Collaborator + model_router موجود استفاده کن.
11. ادعا ممنوع: «AGI» · «اینترنت را گرفت» · «کامل‌ترین مدل دنیا» —
    فقط KPI قابل‌اندازه‌گیری.
12. Meta Rule of Two: session هرگز هم‌زمان untrusted input + sensitive data +
    external effect نداشته باشد.

---

## 1. GROUND TRUTH (از اینجا شروع کن — حدس نزن)

### EXISTS (SUT)

| حوزه | مسیر |
|---|---|
| Router | `_ops/cortex/model_router.py` |
| Local / Fugu / DeepSeek | `local_llm.py` · `fugu_quota.py` · `debate/client.py` |
| Breaker | `_ops/budget/circuit_breaker.py` (JSON، نه Redis) |
| Kill / organ / budget | `opslib.py` · `organ_gate.py` · `token_meter.py` · `budgets.yaml` |
| Context / control | `context_bundle.py` · `control_contracts.py` |
| MiniApp + collab | `telegram_center/miniapp_gateway.py` · `owner_console/collaborator.py` |
| Approval / outbound | `approval_store.py` · `approval_channel.py` · `integrations/outbound_https.py` |
| Dark / capability | `dark_capabilities.py` · `capability_registry.py` · `capability_classifier.py` (WT) |
| Test Intelligence | `_ops/test_intelligence/` + `_ops/tests/test_ti_*.py` |
| Harness | `_ops/tests/harness.py` · `run_all.py` |

### MISSING (نساز به‌عنوان «از قبل بوده»)

Redis breaker · Prom/Grafana · LangGraph در `_ops` · ADR-030 ·
`paid_router.py` جدا · Pydantic به‌جای dataclass اصلی

### وضعیت ورود (2026-08-11)

```text
test-intelligence-built + mocked + evidence-backed + collab-webapp-shadow
!= committed? != master-merged != armed != live != AGI != money-legs
```

اگر TI هنوز uncommitted است → **اول P0**؛ وارد P1 نشو.

---

## 2. نقشهٔ فازها (اجباری به ترتیب)

```text
P0 Pack    →  P1 Owner Shadow  →  P2 Power Motor
     →  P3 Product Beta  →  P4 Money-Legs Bridge  →  P5 Scale Moat
```

هر فاز **Gate** دارد. بدون Gate سبز، فاز بعد ممنوع.
هر فاز گزارش اجباری دارد (قالب پایین).

---

# P0 — بسته‌بندی تحویل (۱ نشست، بدون arm)

## هدف
کار TI را قابل‌نگهداری و قابل‌رأی مالک کن.

## کارها

1. Inventory: `git status` / `git diff --stat` روی worktree؛ runtime noise را جدا کن.
2. Digest جفت‌سازی: `verification-summary.json` ↔ آخرین خروجی `run_all` (sha256).
3. Commit محدود **فقط با رأی مالک** با پیام شبیه:
   `test(ti): grounded test-intelligence pack + close security gaps`
   شامل: production fixes + `_ops/test_intelligence/` + `test_ti_*` + evidence.
   **حذف از stage:** sqlite/WAL/SHM/`state/*.jsonl`/logs.
4. نام فایل‌های `test_ti_*.py` را برای ثبت در `run_all.py` **گزارش** کن (ثبت نکن مگر آزاد).
5. بنویس `_ops/PRODUCT-V1.md` (یا `01 - Docs/PRODUCT-V1.md` در worktree):

```markdown
# Octopus Product v1
## سه کار اصلی روزانه
1. ...
2. ...
3. ...
## غیرهدف‌ها (عمداً نه)
- ...
## KPI هفت‌روزه مالک
- ...
## معماری مخفی (کاربر نمی‌بیند)
- router / breaker / budget / evidence / collab gates
## خط حقیقت
octopus-product-defined != launched != AGI
```

## Gate P0

- [ ] Commit تمیز (اگر مالک گفت) یا patch review آماده
- [ ] TI tests روی HEAD سبز
- [ ] `PRODUCT-V1.md` موجود
- [ ] صفر runtime noise در commit
- [ ] WORKLOCK فایل‌ها دست‌نخورده مگر گزارش‌شده

## خروجی P0

`REPORT-P0.md`: فایل‌های commit‌شده · digest · PRODUCT-V1 خلاصه · blockers

---

# P1 — استقلال سایه برای مالک (۳–۷ روز واقعی)

## هدف
مالک هر روز با اختاپوس کار کند؛ محصول حس «مستقل ولی مطیع» بدهد.

## Arm plan (فقط با رأی صریح، یکی‌یکی)

| ترتیب | Flag / knob | پیش‌شرط | سقف | Rollback |
|---|---|---|---|---|
| 1 | `OCTOPUS_WIRE_COLLAB` | HMAC + owner allowlist | فقط owner | flag=0 + restart path |
| 2 | `OCTOPUS_WIRE_COLLAB_MEMORY` | P1-1 پایدار ۲۴س | state داخل `OCTOPUS_STATE_DIR` | flag=0 + wipe scoped memory |
| 3 | `OCTOPUS_WIRE_COLLAB_DIGEST` | P1-2 | digest-only، بدون raw | flag=0 |
| 4 | `OCTOPUS_COLLAB_USE_MODEL` اختیاری | بودجه روزانهٔ خیلی پایین نوشته شود | USD/تومان سقف در `budgets.yaml` یا معادل | flag=0 + STOP-FUGU اگر لازم |

### خاموش بمانند در کل P1

```text
OCTOPUS_WIRE_OUTBOUND_HTTPS (اثرگذار)
money FSM / uncapped initiative / lead-auto-reply
harvest / value-ledger money paths
OCTOPUS_WIRE_KILL_SEAM مگر drill کنترل‌شدهٔ مالک
هر send واقعی به غیر-owner
```

## معیار استقلال روزانه (KPI)

هر روز مالک ثبت می‌کند (حتی ۳ خط):

| KPI | هدف |
|---|---|
| کارهای واقعی از MiniApp/Collaborator | ≥۵ / روز |
| دخالت دستی در کد برای همان کارها | ۰ |
| external effect ناخواسته | ۰ |
| پیشنهاد خطرناک → approval (نه اجرا) | ۱۰۰٪ |
| هزینهٔ مدل | ≤ سقف ازپیش‌نوشته |
| TI red-team regression | ۰ |

## کار ایجنت در P1

1. جدول Arm plan بالا را با مسیر فایل واقعی کامل کن (شاهد grep).
2. `DAILY-INDEPENDENCE-CHECKLIST.md` برای مالک بساز.
3. اسکریپت/دستور read-only برای خلاصهٔ هزینهٔ روز (از `paid-calls.jsonl` / organ_gate) — بدون ارسال.
4. بعد از هر arm: `dark_capabilities.py` با snapshot بوت؛ نتیجه را در evidence بنویس.
5. هیچ «بهبود بزرگ» UI مگر مانع استفادهٔ روزانه باشد (minimal).

## Gate P1

- [ ] ۷ روز shadow بدون حادثهٔ امنیتی/پولی
- [ ] مالک تأیید کند: «بدون تو هم کار روزانه می‌چرخد»
- [ ] صفر اثر خارجی ناخواسته
- [ ] لاگ‌ها digest-only

## خروجی P1

`REPORT-P1.md` + checklist پرشدهٔ ۷روز + جدول flag states بعد از restart

خط حقیقت هدف:

```text
octopus-product-shadow + owner-daily-use + bounded-autonomy
!= market-launched != money-legs-live != AGI
```

---

# P2 — موتور قدرت (خندق مخفی، بدون بازار عمومی)

## هدف
قدرت رقابتی را در موتور بساز — کاربر فقط سرعت/کیفیت/اعتماد را حس کند.

## کارها (additive روی SUT واقعی)

### P2.a — Routing & cost intelligence

- Snapshot policy برای `model_router.ask`: local / secondary / primary
- سند کوتاه `ROUTE-POLICY.md`: چه وظیفه‌ای کدام لایه؛ سقف هزینه
- تست: `test_ti_router_snapshot` نباید بشکند؛ موارد نو فقط additive
- متریک ساده (stdlib/jsonl): شمارش route + هزینهٔ تقریبی per day

### P2.b — Resilience muscle

- تمرین کنترل‌شدهٔ chaos از `_ops/test_intelligence/chaos_proxy.py` روی adapters
- سناریوها: timeout primary → fallback · breaker OPEN · budget deny · STOP-FUGU
- **هنوز** live-chaos روی production network ممنوع مگر مالک «chaos day staging» بگوید
- ثبت: fault × outcome matrix (الهام ReliabilityBench: consistency / robustness / fault-tolerance)

### P2.c — Evidence & trust ladder

- اتصال عملی `capability_classifier` / evidence ladder به پاسخ‌های Collaborator
  (اگر هنوز فقط WT است: وضعیت را صادقانه بنویس)
- هر ادعای «می‌توانم X» باید سطح شاهد داشته باشد: STRUCTURAL / TESTED / SHADOW / ARMED
- ممنوع ارتقای ادعا بدون شاهد

### P2.d — Golden traces

- از sessionهای واقعی shadow (redacted): ۵ بهترین + ۵ بدترین
- ذخیره در `_ops/test_intelligence/fixtures/golden_traces/` (digest + route + outcome)
- تست regression: replay با mock provider — path پایدار

### P2.e — Discovery loop

- هفته‌ای یک‌بار: `discovery.py` با seeds ثابت روی held-out tasks
- قابلیت فقط اگر Novel ∧ Repeatable(≥3/5) ∧ Useful ∧ Policy-Compliant
- خروجی: `CAPABILITY-CANDIDATES.md` (نه arm خودکار)

## Gate P2

- [ ] صفر regression در TI red-team (۲۵/۲۵)
- [ ] ROUTE-POLICY + هزینهٔ روزانه قابل‌خواندن
- [ ] ≥۱۰ golden traces redacted
- [ ] matrix chaos (حتی mock) کامل
- [ ] هیچ فلگ پول/outbound جدید بدون رأی

## خروجی P2

`REPORT-P2.md` · `ROUTE-POLICY.md` · `CAPABILITY-CANDIDATES.md` · matrix json

خط حقیقت هدف:

```text
power-motor-hardened + evidence-ladder-live + golden-regression
!= public-beta != money-live != AGI
```

---

# P3 — محصول بتا (قابل‌نمایش / قابل‌فروش اولیه)

## هدف
محصولی که بشود به ۲ معتمد یا ۱۰–۲۰ کاربر نشان داد — بدون شرم معماری، بدون حادثه.

## تعریف محصول (اجباری قبل از کد)

از `PRODUCT-V1.md` قفل کن:

- یک سطح ورود: MiniApp Collaborator (یا مسیر واحدی که مالک انتخاب می‌کند)
- یک وعده: «کمک روزانهٔ قابل‌اعتماد با تأیید برای کارهای خطرناک»
- غیروعده: اتوماسیون پول · ارسال انبوه · AGI

## کارها

1. UX مینیمال: ۳ کار اصلی از P0 در UI پیدا و روان باشند (chip همکار از قبل هست — گسترش حساب‌شده).
2. Per-user / per-day budget + rate limit (روی سازوکار موجود؛ invent سیستم billing کامل نکن).
3. Onboarding یک‌صفحه‌ای: چه می‌کند / چه نمی‌کند / چطور قطع می‌شود.
4. Kill / stop مسیر برای مالک واضح باشد (دکمه/دستور موجود را document کن؛ bypass نساز).
5. بستهٔ دمو: اسکریپت ۵ دقیقه‌ای نمایش برای مالک.
6. امنیت بتا: allowlist کاربران؛ پیش‌فرض deny؛ TI collab_security همچنان سبز.

## KPI بتا (۷ روز)

| KPI | هدف حداقلی |
|---|---|
| فعال‌سازی روزانهٔ کاربر بتا | ≥۴ روز از ۷ |
| کار مفید تکمیل‌شده بدون کمک مالک | ≥۳ / کاربر / هفته |
| حادثهٔ امنیتی / اثر خارجی ناخواسته | ۰ |
| رضایت مالک «می‌شود نشان داد» | بله/خیر صریح |

## Gate P3

- [ ] دمو ۵دقیقه‌ای بدون عذرخواهی معماری
- [ ] KPI بالا یا مالک کتباً استثنا بدهد
- [ ] red-team collab همچنان pass
- [ ] merge-to-master فقط اگر مالک بگوید (پیش‌فرض: هنوز worktree/سایه)

## خروجی P3

`REPORT-P3.md` · `DEMO-SCRIPT.md` · `BETA-ALLOWLIST.md` (بدون PII خام؛ شناسه‌های hash)

خط حقیقت هدف:

```text
octopus-product-beta + demoable + bounded-users
!= mass-market != money-legs-live != AGI
```

---

# P4 — پل پاهای پول (برد دیگر → مغز اختاپوس)

## هدف
پاهای پول (لید/CRM، Mining، Project-F، …) که مالک جدا می‌سازد،
اختاپوس را به‌عنوان **مغز + دروازه** صدا بزنند — نه اینکه پول داخل هسته قاطی شود.

## قوانین پل

1. هر پا = client جدا با capability allowlist خودش.
2. پول / ارسال / برداشت = همیشه از ApprovalPort / control_contracts عبور کند.
3. پیش‌فرض: propose-only از پا → تأیید مالک → execute.
4. ContextBundle typed برای handoff؛ schema غلط = reject (TI قرارداد).
5. هیچ پا حق دور زدن organ_gate / breaker / kill را ندارد.
6. Project-F: Hard Rules منشور (geo-block، ToS، فقط‌پا، …) نقض نشود — در صورت تضاد بایست.

## کارها

1. `BRIDGE-CONTRACT.md`: API/events که پاها می‌توانند صدا بزنند (واقعی از کد، نه خیالی).
2. برای هر پا: جدول `effects allowed | needs approval | forbidden`.
3. یک پا را به‌عنوان pilot انتخاب کن — **فقط با رأی مالک** کدام پا.
4. تست قرارداد + یک red-team مخصوص bridge (تزریق از یادداشت لید / tool payload).
5.dry-run end-to-end با fixture؛ صفر اثر واقعی تا رأی.

## Gate P4

- [ ] pilot پا dry-run سبز
- [ ] صفر اثر پولی واقعی در تست
- [ ] bridge red-team pass
- [ ] مالک صریح: «این پا می‌تواند به سایه/live برود»

## خروجی P4

`REPORT-P4.md` · `BRIDGE-CONTRACT.md` · انتخاب pilot + rollback

خط حقیقت هدف:

```text
money-legs-bridged-shadow + approval-bound
!= uncapped-money != auto-send != AGI
```

---

# P5 — مقیاس و خندق (بعد از بتا پایدار)

## هدف
آمادگی رشد بدون فروپاشی استقلال/امنیت.

## کارها (فقط بعد از Gate P3؛ ترجیحاً بعد از P4 pilot)

1. **Chaos day ماهانه (staging):** timeout / rate-limit / disk / provider down —
   با TI harness؛ گزارش fault matrix.
2. **Red-team ماهانه:** گسترش cases از ۲۵ به ۴۰ با الگوی ASI جدید؛ oracle اثر‌محور بماند.
3. **Eval held-out فصلی:** کشف قابلیت؛ candidates وارد registry شوند نه arm خاموش.
4. **هزینه و کیفیت:** داشبورد سادهٔ محلی (json/md) — Prom invent نکن مگر مالک زیرساخت بخواهد.
5. **استقلال L2 محدود:** لیست کارهای read-only که بدون approval تمام می‌شوند؛
   هر چیز write/external = L1.
6. **Packaging:** یک دستور نصب/اجرای محصول برای ماشین تمیز (README-RUN سطح محصول).

## Gate P5

- [ ] یک chaos day بدون حادثهٔ خارج از staging
- [ ] L2 list مکتوب و تست‌شده
- [ ] هزینهٔ واحد کار بتا پایدار یا نزولی
- [ ] مالک: «خندق رقابتی را می‌فهمم و می‌توانم توضیح دهم»

خط حقیقت هدف:

```text
scale-ready-moat + measured-autonomy-L2 + monthly-safety-loop
!= unbounded-autonomy != AGI-claimed
```

---

## 3. ماتریس تصمیم مالک (قبل از هر arm/merge)

| تصمیم | پیش‌فرض | کی بپرس |
|---|---|---|
| Commit TI | بپرس | شروع P0 |
| Merge به master | OFF | بعد از P1 یا P3 به‌انتخاب مالک |
| Arm collab | OFF | شروع P1 |
| Arm model در collab | OFF | وسط P1 اگر بودجه معلوم |
| Arm outbound | OFF | فقط P4 با پایلوت |
| Chaos day زنده | OFF | P5 / رأی |
| اتصال پای پول | OFF | P4 |

---

## 4. چیزهایی که عمداً نمی‌سازیم (ضد-لیست)

- شبیه‌ساز موازی به‌جای Gateway واقعی
- Redis/LangGraph فقط چون «باحال است»
- روشن کردن ۲۷۱ فلگ تاریک یکجا
- «استقلال» به‌معنای حذف approval برای پول/ارسال
- بازنویسی MiniApp از صفر
- ادعای بازاری بدون ۷ روز shadow

---

## 5. قالب گزارش هر فاز (اجباری)

```text
# REPORT-P{N}

## خط حقیقت
...

## Done
- ...

## Evidence (paths + commands)
- ...

## Flags touched (before → after)
- ...

## Gates
- [ ] ...

## NOT done / blocked
- ...

## Owner decisions needed
1. ...

## Next phase entry criteria
- ...
```

---

## 6. ترتیب اجرا برای ایجنت (همین الان)

1. بخوان: SESSION TI + این مگاپرامپت + ADR-023 + `PRODUCT` اگر هست.
2. Inventory worktree: committed؟ TI سبز؟ dark live_source؟
3. اگر uncommitted → فقط P0 (و برای commit رأی بگیر).
4. اگر P0 سبز و مالک گفت shadow → P1 فقط با جدول arm.
5. P2 را می‌توانی بخشی موازی با اواخر P1 به‌صورت **کد/سند بدون arm** پیش ببری.
6. P3+ را شروع نکن تا Gate P1 سبز یا مالک کتباً استثنا بدهد.
7. در پایان هر نشست: HANDOFF wikilink + REPORT-P{N}؛ secret ننویس.

---

## 7. پیام کپی‌برای‌ایجنت (کوتاه)

```text
نقش: Senior Product + Autonomy + Safety Architect برای Octopus.
سند حاکم: این مگاپرامپت P0→P5.
پیش‌نیاز: Test Intelligence تحویل‌شده روی worktree.
هدف: قدرت + استقلال + محصول؛ پاهای پول فقط از P4 با پل approval-bound.
قید: fail-closed؛ بدون merge/arm/send/paid مگر رأی مالک؛ invent نکن Redis/LangGraph/Prom.
الان: Inventory → P0 (pack + PRODUCT-V1) → منتظر رأی برای commit/arm → P1.
خروجی: REPORT-P{N} با خط حقیقت و gates تیک‌خورده.
```

---

## 8. خط حقیقت نهاییِ مسیر (افق)

```text
P0 packed → P1 owner-shadow → P2 power-motor → P3 demoable-beta
→ P4 money-bridge-shadow → P5 scale-moat
!= AGI-proven != unbounded-autonomy != silent-money
```
