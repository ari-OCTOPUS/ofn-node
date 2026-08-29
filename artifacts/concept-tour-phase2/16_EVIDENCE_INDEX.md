# نمایهٔ شواهد و فایل‌های خروجی

## گزارش‌های فاز ۲ — ۲۰ فایل

1. [00_OWNER_ANSWER_FA.md](00_OWNER_ANSWER_FA.md)
2. [01_EXECUTIVE_MAP_FA.md](01_EXECUTIVE_MAP_FA.md)
3. [02_LIVE_SYSTEM_TOUR_FA.md](02_LIVE_SYSTEM_TOUR_FA.md)
4. [03_EVENT_AND_MEMORY_TOUR_FA.md](03_EVENT_AND_MEMORY_TOUR_FA.md)
5. [04_IDENTITY_AND_CONTINUITY_FA.md](04_IDENTITY_AND_CONTINUITY_FA.md)
6. [05_HOMEOSTASIS_AND_SENSES_FA.md](05_HOMEOSTASIS_AND_SENSES_FA.md)
7. [06_COGNITION_AND_MODELS_FA.md](06_COGNITION_AND_MODELS_FA.md)
8. [07_OFN_L4_FUTURE_FA.md](07_OFN_L4_FUTURE_FA.md)
9. [08_WBE_CONCEPT_FA.md](08_WBE_CONCEPT_FA.md)
10. [09_ACTIVE_INFERENCE_CONCEPT_FA.md](09_ACTIVE_INFERENCE_CONCEPT_FA.md)
11. [10_VLLM_PREFIX_CACHE_FA.md](10_VLLM_PREFIX_CACHE_FA.md)
12. [11_VLLM_BLOCK_SIZE_FA.md](11_VLLM_BLOCK_SIZE_FA.md)
13. [12_HYBRID_MAMBA_CACHE_FA.md](12_HYBRID_MAMBA_CACHE_FA.md)
14. [13_LOCAL_PRESENCE_MATRIX.csv](13_LOCAL_PRESENCE_MATRIX.csv)
15. [14_RUNTIME_VS_CONCEPT.md](14_RUNTIME_VS_CONCEPT.md)
16. [15_RISKS_AND_GAPS_FA.md](15_RISKS_AND_GAPS_FA.md)
17. [16_EVIDENCE_INDEX.md](16_EVIDENCE_INDEX.md)
18. [17_GLOSSARY_FA.md](17_GLOSSARY_FA.md)
19. [18_NEXT_CONCEPTUAL_LESSONS_FA.md](18_NEXT_CONCEPTUAL_LESSONS_FA.md)
20. [19_SCAN_DELTA_FROM_PHASE1.md](19_SCAN_DELTA_FROM_PHASE1.md)

Canvas مستقل: `/root/.cursor/projects/root/canvases/octopus-board-deep-tour-phase2.canvas.tsx`.

## معنی labelها

- `[LOCAL-LIVE]`: فایل محلی + evidence فعال runtime
- `[LOCAL-CODE]`: implementation روی دیسک؛ activation نتیجه نمی‌شود
- `[LOCAL-SCAFFOLD]`: قطعهٔ آینده بدون orchestration
- `[LOCAL-OFFLINE-LAB]`: artifact/test آفلاین
- `[DOCUMENTED]`: دانش یا design فقط در سند
- `[RUNTIME-VERIFIED]`: process/service/listener/filesystem/DB metadata محلی
- `[INFERRED]`: نتیجهٔ منطقی با مرز صریح
- `[CONFLICT]`: دو منبع محلی ناسازگار
- `[BLOCKED]`: prerequisite قطعی غایب
- `[UNKNOWN]`: evidence کافی نیست

## روش اسکن

- scope فایل: `/opt/octopus`
- hardware/OS: procfs، device-tree، os-release، free/df/lsblk
- process/service: systemd metadata و listener table؛ بدون environment و بدون بازنشر process command line
- DB: SQLite URI `mode=ro` و `PRAGMA query_only=ON`؛ هیچ migration، checkpoint یا write
- source: ReadFile/recursive inventory/search
- Git coverage: `GIT_OPTIONAL_LOCKS=0` و شمارش read-only tracked/untracked/commit
- runtime API: **هیچ HTTP call انجام نشد**
- network/external API: **هیچ تماس انجام نشد**
- benchmark/test: **هیچ benchmark یا test جدید در این mission اجرا نشد**؛ فقط artifact و execution record موجود خوانده شد

## snapshot فیزیکی

- model: Orange Pi 5 Pro
- OS: Debian 13
- kernel/arch: 6.1.115-vendor-rk35xx / aarch64
- RAM: 4,100,845,568 bytes
- root: 61,326,831,616 bytes؛ 51,771,301,888 used؛ 7,026,900,992 available؛ 89%
- `/opt/octopus`: 815M allocated؛ 829,572,399 apparent bytes
- files/dirs: 8081 / 1237 excluding root

`[RUNTIME-VERIFIED] local metadata snapshot`.

## snapshot service/listener

- active/running: gateway، llama، organism، afferent، soak
- active/exited: first-stage proof
- inactive/dead at instant: heartbeat and mirror one-shot units
- listeners: gateway 8780، local cortex 8081 loopback، organism 8090 loopback+board identity؛ no 8091/4222
- restart count active services checked: zero

`[RUNTIME-VERIFIED] systemctl show/list-units؛ ss -ltn`.

## snapshot DB

- query-only: 1
- journal: WAL
- synchronous: 2/FULL
- integrity/quick: ok/ok
- FK violations: 0
- event hash mismatch: 0
- event sequence contiguous: true
- episode orphan/type mismatch/duplicate: 0/0/0
- outbox: 319 done، 0 pending
- `wan_fetches`: absent

row countهای کامل در [03_EVENT_AND_MEMORY_TOUR_FA.md](03_EVENT_AND_MEMORY_TOUR_FA.md).

## evidence کلیدی source

- v1 event: `/opt/octopus/lab/ofn/organism/contracts/events.py:5-45`
- EventKernel: `/opt/octopus/lab/ofn/organism/event_kernel/kernel.py:6-104`
- DB schema: `/opt/octopus/lab/ofn/organism/persistence/db.py:8-209`
- identity: `/opt/octopus/lab/ofn/organism/identity/ledger.py:13-308`
- episodic memory: `/opt/octopus/lab/ofn/organism/memory/episodic.py:5-80`
- body/state: `/opt/octopus/lab/ofn/organism/homeostasis/core.py:5-119`
- runtime heartbeat: `/opt/octopus/lab/ofn/organism/runtime/app.py:558-609`
- life cycle: `/opt/octopus/lab/ofn/organism/runtime/life_cycle.py:49-410`
- language cascade: `/opt/octopus/lab/ofn/organism/cognition/backend.py:38-467`
- afferent: `/opt/octopus/lab/ofn/organism/runtime/{afferent.py,lan_watch.py}`
- OFN-L4: `/opt/octopus/ofn-l4`، ۱۰ فایل
- WBE/Active Inference: `/opt/octopus/ofn-l4/docs/SCALE-AND-ACTIVE-INFERENCE.md`
- APC: `/opt/octopus/lab/ofn/adapters/vllm_prefix_cache.py`
- block harness: `/opt/octopus/lab/ofn/{benchmarks,adapters/vllm_metrics.py}`

## evidence تست/آفلاین

- sha256 APC report: `/opt/octopus/lab/artifacts/prefix-cache/benchmark-report.{md,json}`
- block preflight/results/Pareto: `/opt/octopus/lab/artifacts/vllm-block-size/`
- 51-test execution record: `/root/.cursor/projects/root/agent-transcripts/ccec7392-b4a7-42f7-97c0-b400b637236e/subagents/2477326a-b3ed-4651-8a24-ec821041cb69.jsonl:73-78`
- proto WBE test claim: `/opt/octopus/research-intake/lab/proto-organism/README.md:1-8`

## exclusions حفاظتی

محتوای secretها، private letterها، raw promptها، utteranceهای خصوصی، process environment، active process command line، tokenها، binary model و vendor/venv internals وارد report/canvas نشد. فقط aggregate/status/schema/path evidence استفاده شد.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
