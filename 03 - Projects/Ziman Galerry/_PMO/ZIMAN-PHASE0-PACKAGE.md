# 🎁 ZIMAN — Phase 0 PMO Package

> معمار: PMO Specialist + Enterprise Architect  
> تاریخ: 2026-07-12  
> وضعیت: **propose-only / draft baseline**  
> اصل: IMPROVE, DON'T REWRITE. First truth, then governance, then memory.

---

## ۱. خلاصهٔ اجرایی

| فیلد | مقدار |
|---|---|
| **نقش در اکوسیستم** | Validation Leg — نخستین آزمایش درآمد کم‌ریسک |
| **ریسک** | Low (R1) |
| **کف خودمختاری** | propose-only |
| **وضعیت اجرایی** | ZERO outward execution. Code built + 21 tests green, relocated. |
| **بلاکر اصلی** | ۷ verdict مالک باز + code location unknown in workspace |
| **وابستگی به دیگران** | Accounting (FEEDS sales income + COGS) |
| **معیار موفقیت فاز** | Ziman ready for Phase 1 activation with clarity on all 7 verdicts |

---

## ۲. یافته‌های حسابرسی (Fact / Inference / Conflict / Unknown)

### Fact — تأییدشده با evidence
| # | یافته | Evidence |
|---|---|---|
| F1 | Ziman مستندات کامل دارد: MANIFEST, README, PROJECT, INDEX, DecisionLog, Strategy-DecisionLog, OpenQuestions, TODO, REGISTRY, RUNBOOK, VERDICT_QUEUE, adapter | بررسی فایل‌سیستم |
| F2 | کد control-brain + ziman-agent ساخته شده و ۲۱ تست سبز دارد | ZIMAN-SYSTEM-MAP.md + ZIMAN-BRAIN-SETUP.md |
| F3 | کد به `_code/` و `_launchpad/ziman-live/` منتقل شده؛ در workspace فعلی حضور فیزیکی ندارد | PROJECT.md Active Context + MANIFEST |
| F4 | محتوای فروش اول آماده است: ۱۰ DM، ۴ کپشن، پیام گروه، اسپرینت ۷ روزه | content/first-sale-pack.md |
| F5 | capacity guard (D4) در کد enforce می‌شود — campaign بالای ۳۰ رد می‌کند | MANIFEST + docs/ZIMAN-BRAIN-SETUP.md |
| F6 | هویت برند: Bloom rose-gold | DecisionLog.md |
| F7 | ۲۰ واحد موجودی فعلی؛ صفر فروش | Business-Zeiman.md |
| F8 | استراتژی: بازار گرم ایرانیان سیدنی، نه تبلیغ سرد | Strategy-DecisionLog.md |
| F9 | روش پرداخت: PayID | Strategy-DecisionLog.md |

### Inference — استنتاج معقول اما تأییدنشده
| # | استنتاج | Basis |
|---|---|---|
| I1 | Ziman می‌تواند بدون وابستگی به هیچ tenant دیگری فعال شود | MANIFEST ecosystem_connections: فقط Accounting |
| I2 | مسیر Revenue experiment از Lead-Painting جداست و Ziman مستقل عمل می‌کند | MANIFEST: "none (separate businesses)" |
| I3 | کد control-brain احتمالاً در `F:\backup\_code/` یا `F:\backup\_launchpad/ziman-live/` است | PROJECT.md Active Context |

### Conflict — تناقض بین اسناد
| # | Conflict | اسناد |
|---|---|---|
| C1 | **عدد ظرفیت**: PROJECT.md می‌گوید «ثبت نشده، منتظر مالک»، ولی Business-Zeiman.md می‌گوید `[Measured]` = ۳۰ واحد/هفته و ZIMAN-BRAIN-SETUP.md می‌گوید در `ziman.yaml` ست شده | PROJECT.md vs Business-Zeiman.md vs ZIMAN-BRAIN-SETUP.md |
| C2 | **نام پوشه**: `Ziman Galerry` (با دو r) — typo در نام پوشه | filesystem |

### Unknown — نیازمند verdict مالک
| # | Unknown | Verdict ID |
|---|---|---|
| U1 | عدد ظرفیت رسمی و نهایی | ZIM-V1 |
| U2 | محصول hero | ZIM-V2 |
| U3 | عکس محصول آماده؟ | ZIM-V3 |
| U4 | نام برند نهایی | ZIM-V4 |
| U5 | محدودهٔ قیمت | ZIM-V5 |
| U6 | مدل تحویل | ZIM-V6 |
| U7 | کانال اول | ZIM-V7 |

---

## ۳. تحلیل قرارداد (Contract Quality Review)

### MANIFEST.yaml — Score: ۹/۱۰ ✅
| Aspect | Status |
|---|---|
| identity + domain | ✅ کامل |
| product_lines (C1-C4) | ✅ دقیق |
| status_snapshot | ✅ صادقانه |
| hard_rules_locked | ✅ ۵ قاعدهٔ شفاف |
| blackbox_potential | ✅ ۵ organ با readiness |
| control_surface | ✅ load_order مشخص |
| kill_switches | ✅ ۳ scope |
| budget_caps | ⚠️ higgsfield_credits = `[To measure]` |
| ecosystem_connections | ✅ شفاف |

**اقدام:** budget_caps باید قبل از activation تکمیل شود.

### adapter.yaml — Score: ۱۰/۱۰ ✅
- چهار interface با schema برگشتی مشخص
- hard_gated_actions شفاف
- autonomous_allowed فعلاً خالی — درست است
- forbidden مطلق با جزئیات

### REGISTRY.md — Score: ۸/۱۰ ✅
- entity schema کامل
- hard-gated actions شفاف
- ⚠️ capacity_guard = `designed` — در واقع `built + tested`
- ⚠️ اشاره به `control-brain/` که در workspace نیست

### RUNBOOK.md — Score: ۹/۱۰ ✅
- اصول سخت ✅
- graph search protocol ✅
- مجاز/ممنوع ✅
- first-sale checklist ✅

### PROJECT.md — Score: ۶/۱۰ ⚠️
- Active Context آپدیت است (2026-07-06)
- ⚠️ Current state کهنه است (خود سند هم اعتراف کرده)
- ⚠️ «بخش Current state این نوت کهنه است» — backlogging خودآگاه
- ظرفیت هنوز `[Estimate]` نوشته در حالی که در جای دیگر `[Measured]`

---

## ۴. Dependency Map زیمان

```text
                    ┌──────────────────────────┐
                    │ Architect/_ops (L1 Boss) │
                    └────────────┬─────────────┘
                                 │ BOSS_OF
                    ┌────────────▼─────────────┐
                    │ Risk Ladder: R1/LOW       │
                    │ autonomy_floor: propose   │
                    └────────────┬─────────────┘
                                 │ GATED_BY
                    ┌────────────▼─────────────┐
                    │        ZIMAN              │
                    │   status: active          │
                    │   execution: ZERO          │
                    └──────┬──────────┬────────┘
                           │          │
              FEEDS        │          │ OWNS (8 docs)
              ┌────────────▼──┐    ┌──▼──────────────────────────┐
              │  Accounting    │    │ MANIFEST, adapter, RUNBOOK, │
              │  (income+COGS) │    │ REGISTRY, VERDICT_QUEUE,    │
              └───────────────┘    │ DecisionLog, README, PROJECT │
                                   └─────────────────────────────┘

BLOCKERS:
  ZIM-V1 (capacity) ──block──► campaign planning
  ZIM-V2 (hero) ──block──► first-sale funnel focus
  ZIM-V3 (photos) ──block──► video engine + IG posts
  ZIM-V7 (channel) ──block──► experiment design

UNBLOCKED work (can proceed now):
  - product taxonomy refinement
  - draft captions/scripts (templates exist)
  - price range worksheet draft
  - brand asset checklist completion (logo, palette, fonts)
  - capacity-aware campaign templates
  - PMO documentation hardening
```

---

## ۵. Work Breakdown — Ziman Phase 0

| ID | Task | Owner | Deliverable | Risk | Gate | Acceptance |
|---|---|---|---|---|---|---|
| ZIM-P0-01 | Audit & Contract Review | PMO | این سند | Green | — | ✅ done |
| ZIM-P0-02 | Resolve capacity conflict | Owner | عدد نهایی ظرفیت با برچسب | Yellow | ZIM-V1 | PROJECT.md و MANIFEST هم‌راستا |
| ZIM-P0-03 | Product taxonomy hardening | Revenue Steward | C1-C4 با price/delivery/margin | Green | — | هر محصول یک پروفایل کامل |
| ZIM-P0-04 | Brand asset checklist | Revenue Steward | checklist تکمیل‌شده | Green | — | logo, palette, fonts, templates |
| ZIM-P0-05 | First-sale experiment design | Revenue Steward | hypothesis, ceiling, KPI, duration, rollback | Yellow | ZIM-V7 | آمادهٔ verdict مالک برای اجرا |
| ZIM-P0-06 | Capacity guard test | Revenue Steward | test report: D4 enforce | Green | — | campaign > ceiling = rejected |
| ZIM-P0-07 | Graph enrichment | Cartographer | nodes/edges برای organها و content | Green | — | graph از ۵ node به ~۲۰ node |
| ZIM-P0-08 | Event ledger entries | PMO | runs.jsonl با schema درست | Green | — | هر action provenance دارد |
| ZIM-P0-09 | Code location verified | Owner/Steward | path دقیق control-brain + ziman-agent | Yellow | — | فایل‌ها پیدا شوند |
| ZIM-P0-10 | Phase 0 exit gate | PMO | acceptance checklist | Orange | — | همهٔ ۷ verdict بسته یا explicitly deferred |

---

## ۶. Verdict Dependency و ترتیب پیشنهادی

مالک باید به ترتیب زیر تصمیم بگیرد — هر verdict قبلی verdict بعدی را باز می‌کند:

```text
ZIM-V1 (capacity)
  │
  ├──► ZIM-V2 (hero product) ← وابسته: باید بدانیم ظرفیت چه محصولی را پشتیبانی می‌کند
  │      │
  │      ├──► ZIM-V5 (price range) ← وابسته: محصول hero قیمت anchor را تعیین می‌کند
  │      │
  │      └──► ZIM-V6 (delivery) ← وابسته: محصول hero نحوهٔ تحویل را تعیین می‌کند
  │             (perishable = local only)
  │
  ├──► ZIM-V3 (photos) ← semi-independent: هر محصولی انتخاب شود، عکس می‌خواهد
  │
  ├──► ZIM-V7 (first channel) ← وابسته: محصول و price مشخص‌کنندهٔ channel مناسب
  │
  └──► ZIM-V4 (brand name) ← independent: می‌تواند هر زمان تصمیم‌گیری شود
```

**مسیر بحرانی:** ZIM-V1 → ZIM-V2 → ZIM-V5/V6 → ZIM-V7

---

## ۷. ریسک‌های ویژهٔ Ziman

| # | ریسک | احتمال | اثر | Mitigation |
|---|---|---|---|---|
| R1 | کد control-brain/ziman-agent پیدا نشود | Medium | High: باید rebuild یا از F: mount | ZIM-P0-09: locate before activation |
| R2 | ظرفیت ۳۰ بالاتر از توان واقعی باشد | Low | Medium: overpromise, brand damage | ZIM-V1: عدد از production owner |
| R3 | عکس محصول با AI بهبودیافته دوباره استفاده شود | Medium | Medium: اعتبار برند | فقط عکس واقعی گوشی |
| R4 | کانال اشتباه انتخاب شود | Medium | Low: هزینهٔ پایین آزمایش | experiment design با hypothesis و rollback |
| R5 | فعال‌سازی زودتر از موعد (قبل از verdict) | Low | High: شکستن hard rules | RUNBOOK و RISK-LADDER enforce می‌کنند |

---

## ۸. Alignment با معماری OCTOPUS 2030

| سرویس ۹گانه | وضعیت در Ziman | شکاف |
|---|---|---|
| ۱. Trust/Policy Kernel | RISK-LADDER + hard_rules_locked | ✅ کافی برای R1 |
| ۲. Identity/Charter | MANIFEST identity + DecisionLog | ⚠️ brand name قطعی نیست |
| ۳. Event Ledger | ندارد — در سطح workspace طراحی می‌شود | ❌ Gap: tenantها ledger مستقل ندارند |
| ۴. Memory Compiler | Strategy-DecisionLog + DecisionLog | ⚠️ دستی، نه خودکار |
| ۵. Evidence Graph | Graph nodes/edges مشترک workspace | ⚠️ organ-level granularity کم است |
| ۶. Context Composer | MANIFEST.load_order + INDEX | ✅ برای propose-only کافی |
| ۷. Model Gateway | ندارد — LLM call از control-brain | ⚠️ نه در scope فاز ۰ |
| ۸. Execution Fabric | worker.py + capacity guard + drafts/ | ✅ برای propose-only کافی |
| ۹. Eval/Release | ۲۱ تست سبز | ✅ baseline test موجود |

---

## ۹. Phase 0 Exit Gate — Ziman

```yaml
gate: ZIMAN_PHASE0_EXIT
criteria:
  - ZIM-V1..V7: "all either closed or explicitly deferred with rationale"
  - code_location: "control-brain path verified or rebuild plan approved"
  - contract_quality: "MANIFEST budget_caps complete, PROJECT.md current-state updated"
  - graph_enrichment: "Ziman nodes >= 15 in graph, edges reflect organ relationships"
  - event_ledger: "Ziman events recorded with idempotency and provenance"
  - experiment_ready: "first-sale experiment designed, gated behind ZIM-V7 verdict"
  - no_external_action: "zero publish/spend/DM executed"
```

---

## ۱۰. اقدام بعدی (فقط یک مورد)

```text
ZIM-V1: عدد ظرفیت رسمی (units/week) چند است؟

گزینه‌ها:
A — ۳۰ (همان عدد Measured در Business-Zeiman)
B — عدد دیگر (مشخص کن)
C — هنوز نمی‌دانم، با production owner چک می‌کنم
```

---

## ضمیمه: وضعیت graph فعلی برای Ziman

```text
Nodes (5):
  Ziman (Project) — status: active
  Zim_MANIFEST — status: verified-exists
  Zim_ADAPTER — status: verified-exists
  Zim_RUNBOOK — status: created
  Zim_REGISTRY — status: created
  Zim_VERDICT — status: created

Edges (6):
  ArchitectOps → Ziman (BOSS_OF)
  RiskLadder → Ziman (GATED_BY, propose-only)
  Ziman → Accounting (FEEDS, sales)
  Ziman → Zim_MANIFEST (OWNS)
  Ziman → Zim_ADAPTER (OWNS)
  Ziman → Zim_RUNBOOK (OWNS)
  Ziman → Zim_REGISTRY (OWNS)
  Ziman → Zim_VERDICT (REQUIRES_VERDICT)
  Agent_RevenueSteward → Ziman (SUPPORTS)

مفقود در graph:
  - organها: control-brain, ziman-agent, video-engine, funnel-tracker, multiuser-control
  - اسناد: PROJECT.md, DecisionLog, Strategy-DecisionLog, OpenQuestions, TODO, INDEX
  - content: first-sale-pack, higgsfield-video-kit, Ziman-FirstSale-Tracker
  - اسناد سیستم: ZIMAN-SYSTEM-MAP, ZIMAN-BRAIN-SETUP, ARCHITECTURE-multiuser-admin
  - داده: Business-Zeiman, Capacity-Channels, Zeiman-KB-note
```
