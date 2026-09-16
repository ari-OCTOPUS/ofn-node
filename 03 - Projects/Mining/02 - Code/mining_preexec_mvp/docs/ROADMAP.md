# Roadmap — پایه کدنویسی Mining

## Phase 0 — Pre-execution scaffold ✅

- [x] Package skeleton
- [x] Governance gates
- [x] Hardware registry validator
- [x] Verdict queue loader
- [x] Algorithm classifier
- [x] Coin scout draft report
- [x] Death-watch evaluator
- [x] Markdown report renderer
- [x] CLI
- [x] Example YAML files
- [x] Unit tests
- [x] Octopus leg design attached: `docs/OCTOPUS_LEG_DESIGN.md`
- [x] Octopus requirements/edge-case matrix: `docs/OCTOPUS_LEG_REQUIREMENTS_MATRIX.md`
- [x] Octopus runtime leg scaffold: `_ops/legs/mining_leg.py`
- [x] Octopus wiring + Telegram digest added behind default-off `OCTOPUS_WIRE_MINING`

## Phase 1 — Registry + measurement, still report-only

- [x] افزودن schema رسمی `hardware_registry.schema.yaml`
- [x] افزودن schema رسمی `benchmark_result.schema.yaml`
- [x] افزودن schema رسمی `experiment_proposal.schema.yaml`
- [x] افزودن schema رسمی `death_watch_log.schema.yaml`
- [x] افزودن master plan و sprintهای 01 تا 03
- [ ] تبدیل `Hardware Registry & Runbook.md` به YAML source-of-truth یا تولید YAML از Markdown
- [ ] ثبت دستی H/s/W/temp/rejected shares/uptime
- [ ] تولید `Benchmark Report.md`
- [ ] electricity feasibility table

## Phase 2 — Coin scouting واقعی اما read-only

- [ ] adapter برای Bitcointalk ANN، فقط read/cache
- [ ] adapter برای MiningPoolStats، فقط read/cache
- [ ] adapter برای CryptoMiso/GitHub activity، فقط read/cache
- [ ] adapter برای GeckoTerminal/Rug Checker، فقط read/cache
- [ ] unify output به `CoinCandidate`
- [ ] افزودن confidence و source evidence

## Phase 3 — Dry-run orchestration

- [ ] پیشنهاد node-group فقط به صورت draft
- [ ] no execution target files
- [ ] no wallet address
- [ ] no pool connection
- [ ] تولید `Experiment Proposal.md`
- [ ] human verdict block

## Phase 4 — Execution فقط بعد از verdict

این فاز عمداً در این MVP پیاده‌سازی نمی‌شود. اگر در آینده فعال شد:

- باید repo+deploy gate داشته باشد.
- باید auth و kill-switch داشته باشد.
- باید wallet zero-access حفظ شود.
- باید هر action audit شود.
