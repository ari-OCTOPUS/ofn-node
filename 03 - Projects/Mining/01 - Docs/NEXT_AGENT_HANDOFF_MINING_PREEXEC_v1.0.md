# NEXT AGENT HANDOFF — Mining Pre-Execution MVP v1.0

> تاریخ تهیه: 2026-07-12  
> محدوده: پروژه `Mining`  
> وضعیت فعلی: **pre-execution / INFORM-only / report-only**  
> مسیر پروژه: `F:\backup\03 - Projects\Mining`

---

## 0. هشدار حاکمیتی برای ایجنت بعدی

این پروژه هنوز وارد execution نشده است. تو اجازه نداری هیچ کاری انجام بدهی که mining واقعی، اتصال به wallet، اتصال به pool، SSH، deploy، خرید/فروش، برداشت، یا کنترل miner محسوب شود.

### ممنوع مطلق

```yaml
forbidden:
  - read_wallet_seed
  - read_private_key
  - create_or_modify_wallet
  - buy
  - sell
  - withdraw
  - ssh_to_node
  - deploy_to_node
  - start_miner
  - stop_miner
  - connect_to_pool
  - write_real_pool_target
  - expose_or_store_secret
```

### مجاز

```yaml
allowed:
  - read_project_docs
  - create_or_edit_docs
  - create_or_edit_report_only_code
  - validate_yaml
  - generate_markdown_reports
  - create_templates
  - create_tests
  - update_INDEX_DecisionLog_PhaseStatus
```

اگر چیزی به execution نزدیک شد، fail closed کن و فقط human verdict request بساز.

---

## 1. پرامپت آماده برای ایجنت بعدی

متن زیر را می‌توان مستقیم به ایجنت بعدی داد:

```text
تو ایجنت بعدی پروژه Mining هستی. پروژه در مسیر زیر است:

F:\backup\03 - Projects\Mining

وظیفه تو ادامه دادن کار pre-execution است، نه اجرای ماینینگ. پروژه طبق truth anchor فعلی در حالت:

phase: pre-execution
execution_state: ZERO mining active
autonomy_floor: INFORM-only / read-only
wallet_access: zero-agent-access
execution_allowed: false

قوانین غیرقابل عبور:
- D-10: هر buy/sell/withdraw = HARD_STOP و فقط انسان.
- D-11: ایجنت هیچ‌وقت wallet/seed/private key نمی‌بیند.
- D-20: SSH مستقیم ممنوع؛ deploy فقط در آینده با repo+deploy gate و verdict انسانی.
- برق فقط اگر <$0.05/kWh یا solar/free باشد.
- معیار abandon فقط D2 است: dev dead، chain stalled، community dead؛ نه payback.
- coin scouting فعلاً فقط report-only است.

اول این فایل‌ها را بخوان:
1. `README.md`
2. `PROJECT.md`
3. `MANIFEST.yaml`
4. `REGISTRY.md`
5. `RUNBOOK.md`
6. `VERDICT_QUEUE.md`
7. `DecisionLog.md`
8. `OpenQuestions.md`
9. `Coin Scouting Framework.md`
10. `Hardware Registry & Runbook.md`
11. `01 - Docs/Phase Status - Execution Plan & Prompt v2.0.md`
12. `01 - Docs/TENTACLE-ALPHA-MINING_Hybrid_MegaPrompt_v3.0.md`
13. `02 - Code/mining_preexec_mvp/README.md`
14. `02 - Code/mining_preexec_mvp/docs/ARCHITECTURE.md`
15. `02 - Code/mining_preexec_mvp/docs/ROADMAP.md`
16. `02 - Code/mining_preexec_mvp/docs/TODO.md`
17. `02 - Code/mining_preexec_mvp/plans/MASTER_PLAN.md`
18. `02 - Code/mining_preexec_mvp/plans/SPRINT_01.md`
19. `02 - Code/mining_preexec_mvp/plans/SPRINT_02.md`
20. `02 - Code/mining_preexec_mvp/plans/SPRINT_03.md`
21. `01 - Docs/NEXT_AGENT_HANDOFF_MINING_PREEXEC_v1.0.md`

وضعیت کاری که قبلاً انجام شده:
- مگا پرامپت v3.0 و دیاگرام‌ها قبلاً اضافه شده‌اند.
- اسکلت Python جدید در `02 - Code/mining_preexec_mvp/` ساخته شده.
- این اسکلت read-only است و هیچ SSH/deploy/wallet/miner-control ندارد.
- ماژول‌های ساخته‌شده:
  - `models.py`
  - `constants.py`
  - `governance.py`
  - `registry.py`
  - `verdicts.py`
  - `algo_classifier.py`
  - `scout.py`
  - `death_watch.py`
  - `report.py`
  - `cli.py`
- schemas ساخته شده‌اند:
  - `schemas/hardware_registry.schema.yaml`
  - `schemas/benchmark_result.schema.yaml`
  - `schemas/experiment_proposal.schema.yaml`
  - `schemas/death_watch_log.schema.yaml`
- plans ساخته شده‌اند:
  - `plans/MASTER_PLAN.md`
  - `plans/SPRINT_01.md`
  - `plans/SPRINT_02.md`
  - `plans/SPRINT_03.md`

هدف تو:
ادامه Sprint 01 و تکمیل برنامه‌ریزی عملی pre-execution، بدون execution.

اولویت‌های دقیق:
1. پوشه `02 - Code/mining_preexec_mvp/data/` را بساز.
2. از روی `Hardware Registry & Runbook.md` و اطلاعات امن موجود، یک فایل اولیه بساز:
   `02 - Code/mining_preexec_mvp/data/hardware_registry.yaml`
   نکته: اگر تعداد/وضعیت دستگاه‌ها قطعی نیست، `unknown` بگذار. حدس را به‌عنوان واقعیت ثبت نکن.
3. از روی `VERDICT_QUEUE.md` یک فایل YAML بساز:
   `02 - Code/mining_preexec_mvp/data/verdict_queue.yaml`
   اگر verdictها هنوز باز هستند، همان open بمانند.
4. CLI readiness را با این داده‌ها تست کن، اما اگر محیط اجرای Python/pytest فراهم نبود، فقط کد و دستور را آماده کن و گزارش بده.
5. اگر لازم بود، loaderهای `registry.py` و `verdicts.py` را مقاوم‌تر کن تا unknown/null را بهتر هندل کنند.
6. یک گزارش تولید/نمونه بساز:
   `02 - Code/mining_preexec_mvp/output/readiness.md`
   اگر output واقعی تولید نکردی، template آن را بساز.
7. schemaها را با داده واقعی هماهنگ کن ولی هیچ secret/IP/password/wallet وارد نکن.
8. tests اضافه کن برای:
   - load hardware registry
   - electricity gate unknown/fail/pass
   - verdict queue YAML load
   - CLI dry behavior در صورت امکان
9. docs را آپدیت کن:
   - `INDEX.md`
   - `DecisionLog.md`
   - `02 - Code/mining_preexec_mvp/docs/ROADMAP.md`
   - اگر لازم بود `OpenQuestions.md`

خروجی نهایی تو باید شامل این باشد:
- لیست فایل‌های ساخته/تغییرکرده.
- وضعیت readiness gates.
- چیزهایی که هنوز block هستند.
- دستورات قابل اجرا.
- تأیید صریح اینکه هیچ execution انجام نشده.

فرمت گزارش نهایی:

```yaml
project: Mining
mode: pre-execution / report-only
execution_performed: false
files_created: []
files_updated: []
gates:
  verdict_queue: pass/fail/unknown
  hardware_registry: pass/fail/unknown
  electricity: pass/fail/unknown
  wallet_zero_access: pass/fail/unknown
blockers: []
next_actions: []
```

یادت باشد: این پروژه باید آرام، امن و evidence-based جلو برود. هیچ عدد unverified را source-of-truth نکن. هرجا شک داری، `unknown` بگذار و OpenQuestions را آپدیت کن.
```

---

## 2. دستورالعمل به مهندس بعدی

### نقش مهندس بعدی

مهندس بعدی باید نقش **pre-execution engineer** داشته باشد، نه ops engineer. یعنی هدفش ساخت ابزار و داده‌های لازم برای تصمیم‌گیری است، نه راه‌اندازی فارم یا miner.

---

## 3. وضعیت فعلی کد

مسیر کد جدید:

```text
02 - Code/mining_preexec_mvp/
├── README.md
├── pyproject.toml
├── requirements.txt
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── TODO.md
├── examples/
│   ├── hardware_registry.example.yaml
│   ├── verdict_queue.example.yaml
│   └── coin_candidates.example.yaml
├── mining_preexec_mvp/
│   ├── __init__.py
│   ├── algo_classifier.py
│   ├── cli.py
│   ├── constants.py
│   ├── death_watch.py
│   ├── governance.py
│   ├── io.py
│   ├── models.py
│   ├── registry.py
│   ├── report.py
│   ├── scout.py
│   └── verdicts.py
├── plans/
│   ├── MASTER_PLAN.md
│   ├── SPRINT_01.md
│   ├── SPRINT_02.md
│   └── SPRINT_03.md
├── schemas/
│   ├── benchmark_result.schema.yaml
│   ├── death_watch_log.schema.yaml
│   ├── experiment_proposal.schema.yaml
│   └── hardware_registry.schema.yaml
└── tests/
    ├── test_algo_classifier.py
    ├── test_death_watch.py
    ├── test_governance.py
    └── test_scout.py
```

---

## 4. کارهای پیشنهادی برای اولین PR/commit بعدی

### PR-01 — Data Source of Truth Bootstrap

#### هدف
ساخت داده‌های YAML واقعی اولیه برای pre-execution.

#### فایل‌های جدید پیشنهادی

```text
02 - Code/mining_preexec_mvp/data/hardware_registry.yaml
02 - Code/mining_preexec_mvp/data/verdict_queue.yaml
02 - Code/mining_preexec_mvp/output/readiness.md
```

#### قوانین داده

- اگر دستگاه قطعی نیست، ثبت شود اما `status: unknown`.
- اگر برق قطعی نیست، `power_source: unknown` و `electricity_cost_usd_kwh: null`.
- IP، پسورد، hostname حساس، seed، wallet، private key، API key وارد نشود.
- یادداشت‌ها فقط در `notes_safe` و بدون secret.

#### Acceptance Criteria

```yaml
acceptance:
  - data/hardware_registry.yaml exists
  - data/verdict_queue.yaml exists
  - readiness report can be generated or command documented
  - no secrets in data files
  - no execution code added
```

---

### PR-02 — Validation Hardening

#### هدف
loaderها و validatorها را مقاوم‌تر کن.

#### تغییرات پیشنهادی

- در `registry.py`:
  - null-safe enum parsing
  - unknown fallback به‌جای crash
  - duplicate node_id detection
  - unsafe fields detector برای `seed/private_key/password/wallet`

- در `verdicts.py`:
  - markdown parser optional برای `VERDICT_QUEUE.md`
  - YAML loader strict ولی safe
  - unknown status fallback → open

- در `governance.py`:
  - gate برای duplicate nodes
  - gate برای suspected secrets
  - gate برای active mining confirmation اگر verdict MIN-V3 باز باشد

#### Acceptance Criteria

```yaml
acceptance:
  - pytest passes
  - invalid YAML produces safe failure
  - unknown values do not crash CLI
  - suspected secrets cause red gate
```

---

### PR-03 — Benchmark Planning Toolkit

#### هدف
فقط قالب‌سازی benchmark، نه اجرای benchmark.

#### فایل‌ها/کد پیشنهادی

```text
mining_preexec_mvp/benchmark.py
schemas/benchmark_result.schema.yaml  # already exists, improve if needed
examples/benchmark_result.example.yaml
```

#### قابلیت‌ها

- validate benchmark result completeness
- محاسبه H/s/W اگر `hashrate_avg` و `power_w_avg` وجود داشت
- تشخیص invalid benchmark اگر duration کم، دما زیاد، rejected shares زیاد
- تولید `Benchmark Report.md`

#### ممنوع

- اجرای miner
- خواندن miner API زنده
- SSH
- اتصال به pool

---

## 5. دستور اجرای پیشنهادی برای مهندس

اگر محیط Python آماده است:

```bash
cd "F:\backup\03 - Projects\Mining\02 - Code\mining_preexec_mvp"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
python -m mining_preexec_mvp.cli readiness --hardware examples/hardware_registry.example.yaml --verdicts examples/verdict_queue.example.yaml --wallet-zero-access --output output/readiness.example.md
python -m mining_preexec_mvp.cli scout --candidates examples/coin_candidates.example.yaml --output output/coin_scout.example.md
```

اگر محیط اجرا در دسترس نیست، فقط فایل‌ها و دستورها را آماده کن و در گزارش بنویس `not executed locally`.

---

## 6. source-of-truth hierarchy

برای جلوگیری از drift، اولویت اسناد این است:

1. `01 - Docs/Phase Status - Execution Plan & Prompt v2.0.md`
2. `MANIFEST.yaml`
3. `PROJECT.md`
4. `DecisionLog.md`
5. `VERDICT_QUEUE.md`
6. `Coin Scouting Framework.md`
7. `Hardware Registry & Runbook.md`
8. `02 - Code/mining_preexec_mvp/docs/ROADMAP.md`
9. `02 - Code/mining_preexec_mvp/plans/MASTER_PLAN.md`
10. لاگ‌های تلگرام و archive فقط context هستند، نه truth anchor.

---

## 7. مسائل باز که باید حفظ شوند

```yaml
open_blockers:
  - wallet_seed_rotation_unresolved
  - hardware_inventory_unverified
  - electricity_unknown
  - hashrate_unmeasured
  - verdict_queue_open
  - active_mining_state_needs_human_confirmation
  - secrets_cleanup_needed_in_legacy_code
```

هیچ کدام را بدون evidence انسانی نبند.

---

## 8. خروجی مدیریتی مورد انتظار از مهندس بعدی

در پایان کار، مهندس باید چنین خلاصه‌ای بدهد:

```yaml
project: Mining
current_mode: pre-execution / INFORM-only
execution_allowed: false
execution_performed: false
new_source_of_truth_files:
  - data/hardware_registry.yaml
  - data/verdict_queue.yaml
reports:
  - output/readiness.md
remaining_blockers:
  - ...
recommended_next_sprint:
  - one-node benchmark planning after human verdict
security_notes:
  - no secrets introduced
  - no SSH/deploy/miner-control added
```

---

## 9. یادآوری نهایی

هدف پروژه ساخت یک سیستم venture mining / frontier coin scouting است، نه فارم ماینینگ کلاسیک. تا وقتی inventory، برق، wallet policy و verdictها بسته نشده‌اند، بهترین contribution مهندس بعدی این است:

1. داده‌ها را تمیز کند.
2. schemaها را محکم کند.
3. reportها را قابل اتکا کند.
4. هیچ execution انجام ندهد.
