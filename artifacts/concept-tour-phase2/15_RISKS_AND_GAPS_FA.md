# ریسک‌ها و بدهی‌ها

هر مورد پنج بخش دارد: چرا مهم، failure، نشانه، mitigation آینده و تأیید مالک.

## R1 — فشار دیسک / eMMC

- چرا: root برابر 89% و فقط 6.54 GiB آزاد است؛ WAL، log، evidence و vault رشد می‌کنند.
- failure: disk-full، write failure، DB/WAL trouble و از دست‌رفتن receipt.
- نشانه: `df /`، رشد WAL، `DISK_FREE_DANGER`.
- mitigation: retention، budget، archive/backup و پاک‌سازی انتخابی پس از inventory.
- owner approval: **لازم** برای هر حذف/جابجایی.
- evidence: `[RUNTIME-VERIFIED] df؛ homeostasis/core.py:57-85`.

## R2 — backup/mirror غیرقابل اتکا

- چرا: mirror empty و state `blocked`/`mirror_healthy=false`.
- failure: خرابی eMMC بدون copy قابل بازیابی.
- نشانه: sync age نامعلوم و no successful pull.
- mitigation: مقصد backup مستقل، restore drill، checksum و retention.
- owner approval: **لازم** برای credential/transport/destination.
- evidence: `[LOCAL-LIVE] /opt/octopus/state/sync.json؛ mirror-pull.sh:64-78,126-178`.

## R3 — Git reproducibility ضعیف

- چرا: 40 tracked در برابر 491 untracked و فقط 2 commit.
- failure: rebuild از Git بخش عمدهٔ سامانه/units/artifacts را بازتولید نمی‌کند.
- نشانه: read-only `git ls-files` count snapshot.
- mitigation: secret-safe inventory، commit plan، generated/state ignore policy و release manifest.
- owner approval: **لازم** برای add/commit/remote؛ این مأموریت Git را تغییر نداد.
- evidence: `[RUNTIME-VERIFIED] GIT_OPTIONAL_LOCKS=0 metadata count`.

## R4 — unitهای عملیاتی بیرون Git

- چرا: unitهای فعال در `/etc/systemd/system` هستند و tracked set پروژه آن‌ها را تضمین نمی‌کند.
- failure: reinstall با source درست ولی service config متفاوت.
- نشانه: five active unit files در `/etc` و copies پراکنده در lab.
- mitigation: canonical unit templates، checksum manifest و deployment recipe.
- owner approval: **لازم** برای systemd یا install.
- evidence: `[LOCAL-LIVE] /etc/systemd/system/octopus-*.service`.

## R5 — DB sidecarهای 0644

- چرا: DB، WAL و SHM همگی world-readable محلی‌اند و payloadهای event/memory می‌توانند خصوصی باشند.
- failure: disclosure به user/process محلی غیرمجاز.
- نشانه: mode `0644 root:root`.
- mitigation: threat model، dedicated user/group، restrictive umask/mode و permission tests.
- owner approval: **لازم**؛ permission change ممنوع بود.
- evidence: `[RUNTIME-VERIFIED] stat organism.db{,-wal,-shm}`.

## R6 — listener LAN بدون auth آشکار

- چرا: `192.168.0.180:8090` listen می‌کند و Handler auth middleware/check ندارد.
- failure: خواندن state، ask workload یا side-effectful GET توسط LAN peer.
- نشانه: listener فعال؛ `do_GET/do_POST` مستقیماً route می‌کنند.
- mitigation: bind policy، mutual/auth token، firewall و rate limit با secret-safe design.
- owner approval: **لازم** برای network/auth rollout.
- evidence: `[LOCAL-CODE] runtime/app.py:228-503,706-723`.

## R7 — systemd hardening ضعیف

- چرا: همهٔ سرویس‌های بررسی‌شده root هستند و sandbox محدود است.
- failure: compromise یک process سطح اثر root دارد.
- نشانه: `systemd-analyze security`: gateway 9.6 UNSAFE؛ llama/organism/afferent/soak هرکدام 9.0 UNSAFE.
- mitigation: DynamicUser/dedicated users، ProtectSystem، ProtectHome، capability drop، syscall/device restrictions.
- owner approval: **لازم** و نیازمند canary/rollback.
- evidence: `[RUNTIME-VERIFIED] security exposure snapshot؛ unit files`.

## R8 — source/runtime drift

- چرا: process قبل از آخرین `db.py`/`wan.py` شروع شده و live schema `wan_fetches` ندارد.
- failure: operator source را behavior زنده فرض می‌کند؛ restart بعدی migration/behavior غیرمنتظره می‌آورد.
- نشانه: timestamp ordering و schema mismatch.
- mitigation: build/version receipt، source hash در process_started، migration dry-run و controlled restart plan.
- owner approval: **لازم** برای restart/migration.
- evidence: `[CONFLICT] service/file metadata؛ persistence/db.py:143-165`.

## R9 — GETهای side-effectful

- چرا: چند GET `organism_snapshot()`، seed/apply/write public state یا eval/attestation را اجرا می‌کنند؛ gateway health نیز ping می‌کند.
- failure: monitor ساده state/DB/network را تغییر می‌دهد.
- نشانه: route call graph.
- mitigation: pure read snapshot، explicit POST/admin action برای refresh/eval، idempotency test.
- owner approval: **لازم** برای API contract change.
- evidence: `[LOCAL-CODE] runtime/app.py:251-455؛ gateway/app.py:145-157`.

## R10 — سه codebase ارگانیسم

- چرا: live v1، L4 scaffold و proto research naming مشترک دارند.
- failure: اجرای اشتباه scaffold یا انتقال assumption/test بین schemaها.
- نشانه: سه root مستقل و version/contract متفاوت.
- mitigation: authoritative manifest، package names، ADR و archive/quarantine labels.
- owner approval: **لازم** برای consolidation.
- evidence: `[LOCAL-CODE] /opt/octopus/lab/ofn/organism؛ /opt/octopus/ofn-l4؛ /opt/octopus/research-intake/lab/proto-organism`.

## R11 — soak نامحدود

- چرا: loop پایان زمانی ندارد و sample/local inference ادامه می‌دهد.
- failure: disk/log growth یا load دائمی.
- نشانه: `while abort is None`، `cap=NONE_HOUR`.
- mitigation: duration cap، evidence retention، budget و owner stop policy.
- owner approval: **لازم** برای تغییر یا stop service.
- evidence: `[LOCAL-LIVE] runtime/soak.py:90-123؛ SOAK-RESULTS.json:2-13`.

## R12 — identity بدون external anchor

- چرا: internal chain tail expectation بیرون DB ندارد.
- failure: tail truncation سازگار ممکن است کشف نشود.
- نشانه: `external_anchor=None` و `tail_truncation_detectable=False`.
- mitigation: signed/checkpoint anchor روی مقصد مستقل، rotation و restore verification.
- owner approval: **لازم** برای key/remote witness.
- evidence: `[LOCAL-CODE] identity/ledger.py:164-174`.

## R13 — retrieval gap

- چرا: recall wired است ولی minimum reads/metric/fail-closed contract وجود ندارد.
- failure: refactor ممکن است memory grounding را بی‌صدا حذف کند.
- نشانه: `memory_reads_per_cycle` در code/meta absent.
- mitigation: counter، required read receipt، test و safe fallback.
- owner approval: برای source/DB change **لازم**.
- evidence: `[LOCAL-CODE] life_cycle.py:57-105؛ SQLite meta`.

## R14 — L4 bridge غایب

- چرا: v1/v2 hash material، time، schema، identity و transaction متفاوت‌اند.
- failure: double truth، broken provenance یا chain ادعایی جعلی.
- نشانه: no bridge file/test/mapping table.
- mitigation: immutable mapping، terminal v1 anchor، shadow projection، parity tests و rollback.
- owner approval: **لازم** قبل از هر writer/daemon L4.
- evidence: `[CONFLICT] live contracts/events.py:5-45؛ ofnl4/contracts.py:13-125`.

## R15 — GPU/vLLM absent

- چرا: benchmark/tuning empirical بدون accelerator/runtime ممکن نیست.
- failure: انتخاب block-size از estimator و deployment اشتباه.
- نشانه: no vLLM package/tool، no CUDA/ROCm device، results header-only.
- mitigation: GPU host جدا، same-version evidence، W1–W5، metrics و canary.
- owner approval: **الزامی** برای canary/deployment.
- evidence: `[BLOCKED] vllm-block-size/preflight.json؛ pareto-report.md:1-14`.

## اولویت مالک

1. backup قابل restore و manifest reproducible.
2. disk/retention.
3. DB permission و LAN auth.
4. source/runtime reconciliation.
5. pure-read API separation.
6. L4 bridge/tests.
7. GPU canary فقط روی میزبان مناسب.

هیچ‌یک در این مأموریت اجرا نشد.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
