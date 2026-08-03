# Octopus — نقاط کورِ جدید (DELTA-4: ۴۶۴–۵۴۰)

> اسکنِ نهاییِ ساختاری، ۲۰۲۶-۰۷-۲۷. مکملِ ۱۰۰ + DELTA + DELTA-2 + DELTA-3.
> چهار ایجنتِ موازی مناطقِ زیراسکن‌نرفته را پوشش دادند:
> (۱) ۴۷ فایلِ top-levelِ `_ops/`، (۲) ۱۴ subdirِ `_ops/`، (۳) ۲۵ دایرکتوریِ top-levelِ vault، (۴) duplicates/Persian/secret-hygiene.
>
> **دو کشفِ بحرانیِ این دور:**
> ۱. **`_octopus/` زنده است** (نه مرده) — `approval_store.py` فعالانه می‌نویسدش. false-negative از اسکن‌های قبلی.
> ۲. **`OWNER-PROFILE.json` با PII در git tracked شده** — تأییدِ قطعیِ CRITICAL.

---

## بخش ۰ — تصحیحِ حیاتیِ این دور

| # | آنچه قبلاً گفته شد | واقعیت | منبع |
|---|---|---|---|
| C12 | `_octopus/` (در ریشه، متمایز از `_ops/`) احتمالاً مرده | ❌ **زنده**. `approval_store.py:54-56` فعالانه `_octopus/state/approvals.json` (۳۹KB، ~۴۵ job pending) و `logs/audit.log` (آخرین ورودی: امروز ۲۰۲۶-۰۷-۲۸) را می‌نویسد. اگر حذف شه صف تأیید می‌شکنه. | `_ops/telegram_center/approval_store.py:54-56` |
| C13 | OWNER-PROFILE.json «PII risk» (DELTA-3 #۴۴۶، severity فرضی) | ✅ **تأییدِ قطعیِ CRITICAL**: فایل واقعاً در git tracked شده (commit `76f58ca`). شامل نام واقعی، پروفایلِ روان‌شناختی، ترومای کودکی، الگوهای رابطه، روان‌شناسی مالی. در تاریخچهٔ git برای همیشه. | `git ls-files` تأیید کرد |
| C14 | «پنج اختاپوس» (`_ops`، `octopus_core`، `_octopus`، `OCTOPUS-PRIME`، `OCTOPUS`) رقیب‌اند | ❌ پنج نقشِ متفاوت: `_ops/`=زنده، `octopus_core/`=مرده(#۳۲۸)، `_octopus/`=state-layer زنده، `OCTOPUS-PRIME/`=session packet مرده، `OCTOPUS/`=HTML gallery مرده. هیچ رقیبِ کدی. | grep |

---

## بخش ۱ — فایل‌های top-levelِ `_ops/` (۴۶۴–۴۷۵)

**یافتهٔ کلیدی:** از ۴۷ ماژول، **۸ تا DEAD** (output_critic، teacher_loop، octopus_logger، stop_probe، orphan_scan، watchdog_extension، vault_updater_apply، vault_updater_gate). از آن‌ها، ۴ تا safety/quality-critical هستن ولی وصله‌اند.

| # | Sev | فایل | نقطهٔ کور | فیکس |
|---|---|---|---|---|
| ۴۶۴ | 🟠 MED | `output_guard.py` | فقط پشت flag که در PAPER_FULL نیست، فقط در tradequote_bridge | اضافه به flags یا gate سراسری |
| ۴۶۵ | 🟠 MED | `output_critic.py` | **کاملاً DEAD** — خود‌انتقادی ۴‌بعدی، هیچ productionای import نمی‌کند | wire یا حذف |
| ۴۶۶ | 🔴 HIGH | `teacher_loop.py` | **کاملاً DEAD** — مسیرِ «یادگیری از معلم» C6، قطع شده | wire یا حذف از capability_registry |
| ۴۶۷ | 🟠 MED | `epistemics/readers.py` | ۳ از ۵ metric TODO stub، composite بی‌معنی | پیاده‌سازی یا gating |
| ۴۶۸ | 🟠 MED | `octopus_logger.py` | **کاملاً DEAD** — structured logger که observability لازمش داره، ولی fragmented ad-hoc logging جایگزینش | wire به opslib.alert |
| ۴۶۹ | 🟡 LOW | `trajectory_log.py` | فقط auto_approve + teacher_loop(dead) صدا می‌زنن، C6/governor/doctor غایب | wire در high-stakes |
| ۴۷۰ | 🔴 HIGH | `stop_probe.py` | **کاملاً DEAD** — oracle برای «should supervisor yield؟»، هیچ PS1ای صدا نمی‌زنه | wire به organism-watchdog.ps1 |
| ۴۷۱ | 🟠 MED | `orphan_scan.py` | **کاملاً DEAD** — اسکنرِ ماژول‌های orphan، خودش orphan | wire به self_scan |
| ۴۷۲ | 🔴 HIGH | `watchdog_extension.py` | **کاملاً DEAD** — WatchdogMonitor برای metrics، organism loop هیچ‌وقت صدا نمی‌زنه. dashboard به status watchdog کوره. | wire به organism.py |
| ۴۷۳ | 🟠 MED | `vault_updater_apply.py` | **کاملاً DEAD** با وجود dual-flag gating — EffectorGate برای AUTO vault patches، ۷-layer validation | wire به doctor/code_autonomy |
| ۴۷۴ | 🟡 LOW | `vault_updater_gate.py` | transitively dead (وابسته به #۴۷۳) | live میشه وقتی #۴۷۳ wire بشه |
| ۴۷۵ | 🟠 MED | `export_status.py:127` | `subprocess.run` از ماژولی که باید read-only باشه + substring forbidden-names | import مستقیم + suffix list |

## بخش ۲ — subdirهای `_ops/` (۴۷۶–۴۸۸)

**یافته‌های کلیدی:** spine flag-OFF (۶ call-site بی‌صدا no-op)، synapse کاملاً shadow (صفر production)، observability کامل مرده، memory gate flag-OFF (همهٔ learning writes drop می‌شه).

| # | Sev | فایل | نقطهٔ کور | فیکس |
|---|---|---|---|---|
| ۴۷۶ | 🟠 MED | `now_moves/staleness_stamp.py` (M2) | صفر call-site، FM-1/FM-2 که مستند کرده بی‌فیکس می‌مونه | wire یا حذف |
| ۴۷۷ | 🟠 MED | `now_moves/cortex_symmetric_revive.py` (M3) | صفر call-site — cortex هنوز ۳۶h بدون detect می‌میره | register scheduled task |
| ۴۷۸ | 🟡 LOW | `now_moves/unified_bus_guard.py` (M4) | صفر call-site — defense-in-depth فقط | wire یا حذف |
| ۴۷۹ | 🟡 LOW | `now_moves/module_self_manifest.py` (M6) | صفر call-site — diagnostic | wire یا حذف |
| ۴۸۰ | 🟠 MED | `spine/spine_adapters.py:90-91` | flag-OFF، ۶ call-site بی‌صدا no-op — تأیید #۴۵۲ | arm flag یا حذف imports مرده |
| ۴۸۱ | 🟠 MED | `synapse/` (sense/trajectory/egress) | کلِ subsystem SHADOW، صفر production wiring، egress_policy کاملاً خالی | wire یا archive |
| ۴۸۲ | 🟡 LOW | `epistemics/readers.py` | wiring هر ۷۲۰ beat ولی upstreamها None برمی‌گردونن | pre-check یا حذف wiring |
| ۴۸۳ | 🟡 LOW | `epistemics/emit.py:13` | hardcoded relative path | Path(__file__) |
| ۴۸۴ | 🟡 LOW | `observability/tracer.py` | tracer کامل ۴۵۵ خط با @trace، صفر production | adopt یا archive |
| ۴۸۵ | 🟠 MED | `observability/` ۴ monitor | flag-drift/budget-drift/germline-lag detect می‌کنن ولی هیچ‌کس run نمی‌کنه | wire health_check به beat |
| ۴۸۶ | 🟠 MED | `memory/gate.py:100-101` | `_verify_external_grade` همیشه False چون validator None — self-knowledge همیشه ADVISORY می‌مونه | validator پیاده‌سازی |
| ۴۸۷ | 🟠 MED | `eval/run_adversarial.py:316` | gate-verdict policy صفر runtime enforcer | boot check در wiring |
| ۴۸۸ | 🟠 MED | `backup/GITWRITE-FAILED.flag` | germline git write شکست خورده، health_check detect می‌کنه ولی run نمی‌شه | investigate + alert |

## بخش ۳ — دایرکتوری‌های top-levelِ vault (۴۸۹–۴۹۵)

**یافتهٔ بازنویسی‌کننده:** `_octopus/` زنده است. survival-gateway ۷۳MB PostgreSQL در repo.

| # | Sev | فایل/دایرکتوری | نقطهٔ کور | فیکس |
|---|---|---|---|---|
| ۴۸۹ | 🔴 CRIT | `_octopus/state/approvals.json` | **زنده ولی احتمالاً مرده فرض شده** — approval_store.py فعالانه می‌نویسدش، ۴۵ job pending | مستندسازی ALIVE؛ مهاجرت به _ops/state |
| ۴۹۰ | 🔴 HIGH | `approval_store.py:85-111` | dual-write approval queue (phase-1 monolithic + phase-2 per-file)، silent divergence | single store یا reconciliation |
| ۴۹۱ | 🔴 HIGH | `owner_views.py:706,723` | `pend[:5]` hardcode — ۴۵ job pending ولی مالک فقط ۵ تا می‌بینه، ۴۰ تا invisible wall | pagination |
| ۴۹۲ | 🟠 MED | `survival-gateway/data/postgres/` | **۷۳MB PostgreSQL raw data در git repo** | gitignore + حذف |
| ۴۹۳ | 🟠 MED | `debate/client.py:278` vs `survival-gateway/DEPRECATED.md:15` | DEPRECATED می‌گوید هیچ ارجاعی ولی client.py ارجاع می‌دهد | update doc یا حذف reference |
| ۴۹۴ | 🟠 MED | `CHRONOS-FABLE-OS/` | زنده (read by _ops) ولی بدون schema-version check | hash validation |
| ۴۹۵ | 🟡 LOW | `_worktree-rescue-2026-07-24/` | ۴۹۵MB rescue data که هدفش را انجام داده | archive/حذف |

## بخش ۴ — duplicates/Persian/secret-hygiene (۴۹۶–۵۱۲)

| # | Sev | فایل/دایرکتوری | نقطهٔ کور | فیکس |
|---|---|---|---|---|
| ۴۹۶ | 🔴 CRIT | `_ops/state/OWNER-PROFILE.json` | **PII در git tracked شده** (commit 76f58ca) — نام، تروما، رابطه، مالی | gitignore + git rm --cached + filter-branch |
| ۴۹۷ | 🔴 CRIT | `_ops/state/OWNER-PROFILE-LOG.md` | همPII، هم tracked | مثل #۴۹۶ |
| ۴۹۸ | 🔴 HIGH | `.gitignore:7` | `*key*` بیش از حد broad — فایل‌های legit را بی‌صدا ignore می‌کنه | narrow patterns |
| ۴۹۹ | 🟠 MED | `03-Projects/` (بدون فاصله) | duplicateِ staleِ `03 - Projects/`، خالی | حذف |
| ۵۰۰ | 🟠 MED | `00/` + `Inbox/` | دو inbox خالی رقیبِ `00 - Inbox/` | حذف |
| ۵۰۱ | 🟠 MED | `Projects/` (bare) | duplicateِ stale، خالی | حذف |
| ۵۰۲ | 🟠 MED | `-/` | دایرکتوری خالی با نامِ `-` (shell typo) | حذف |
| ۵۰۳ | 🟡 LOW | `09 - Archive/` | خالی (فقط `superseded-code/`)، رقیبِ `_Archive/` | populate یا حذف |
| ۵۰۴ | 🟠 MED | `شناخت اختاپوس/` | ۱۲ markdown دانشِ نهادی، untracked — می‌تونه گم شه | track یا move به 07-Knowledge |
| ۵۰۵ | 🟠 MED | `نقشه اختاپوس/vault_scanner.py` | ابزار Python 28KB untracked | track یا archive |
| ۵۰۶ | 🟠 MED | `09 - People/_Index - People.md` | placeholder `status: paused`، با `09 - Archive` numbering collision | renumber |
| ۵۰۷ | 🟡 LOW | ۴۲ .md پراکنده در ریشه | noisy — ۸ session-handoff، ۶ scan، ۵ megaprompt | consolidate به dir |
| ۵۰۸ | 🟡 LOW | `MycoCardium-Architecture-Analysis-v1.docx` | ۲۵۴KB binary در git | LFS یا extract به md |
| ۵۰۹ | 🔴 HIGH | ۱۱۱ modified + ۲۷۷ untracked | **VQ-COMMIT-002** — ۲۴K insertions/۱۲.۵K deletions uncommitted، ریسکِ loss | commit code changes |
| ۵۱۰ | 🟡 LOW | `OCTOPUS/ARCHITECTURE-BIBLE.md` | به `4d_system/` مرده ارجاع می‌ده (#۳۸۰s) | DEPRECATED header |
| ۵۱۱ | 🟡 LOW | `OCTOPUS/_legacy-2026-07-24/` | ۷ HTML duplicate | حذف |
| ۵۱۲ | 🟡 LOW | `_octopus/queue/` | ۴ subdir خالی، design رهاشده | حذف |

---

## بخش ۵ — یافته‌های ساختاریِ بزرگ

### ۵.الف — «پنج اختاپوس» حل شد
پنج دایرکتوری با «octopus» در نام، پنج نقشِ متفاوت:
- `_ops/` = ارگانیسمِ زنده (CANONICAL)
- `octopus_core/` = prototype مرده (#۳۲۸)
- `_octopus/` = state-layer زنده (#۴۸۹) — **false-negative از اسکن‌های قبلی**
- `OCTOPUS-PRIME/` = session packet مرده
- `OCTOPUS/` = HTML gallery مرده
**هیچ رقیبِ کدی وجود ندارد.**

### ۵.ب — «سه inbox» حل شد
فقط `00 - Inbox/` زنده است (۲۵۸ فایل). `00/` و `Inbox/` shell-typo/early-layout artifacts خالی‌اند.

### ۵.ج — deadcode وزنی
- `_worktree-rescue-2026-07-24/` = ۴۹۵MB
- `survival-gateway/` = ۷۴MB (۷۳MB Postgres)
- `_code/` = ۷.۴MB (personal projects)
- `nervous-system/` = ۱.۵MB (dead extractors)
- `octopus_core/` = ۱.۸MB (#۳۲۸)
مجموعاً ~۵۸۰MB deadweight.

### ۵.د — ماژول‌های DEADِ safety-critical
چهار ماژول safety/quality-critical ولی DEAD:
- **stop_probe** (#۴۷۰) — halt detection unreachable
- **watchdog_extension** (#۴۷۲) — watchdog health telemetry never published
- **teacher_loop** (#۴۶۶) — «learn from teacher» C6 pathway disconnected
- **octopus_logger** (#۴۶۸) — structured logger dead، ad-hoc logging جایگزین

---

## بخش ۶ — ۵ کارِ امروز (P0 به‌روزرسانی‌شده)

۱. **gitignore + git rm --cached OWNER-PROFILE*.json/md** (#۴۹۶/#۴۹۷) — CRITICAL PII. یک دستور.
۲. **فیکس BCM sync-delete** (#۲۱۴) — یک خط `if known:`.
۳. **فیکس redact() fail-open** (#۱۳۱ DELTA-2) — یک خط.
۴. **pagination در owner_views** (#۴۹۱) — ۴۰ job invisible wall.
۵. **gitignore survival-gateway/data/** (#۴۹۲) — ۷۳MB Postgres.

## بخش ۷ — جمعِ نقاط کور تا کنون

| سند | محدوده | تعداد |
|---|---|---|
| `OCTOPUS-BLINDSPOTS-100.md` | ۱–۱۰۰ | ۱۰۰ |
| `OCTOPUS-BLINDSPOTS-DELTA.md` | ۱۰۱–۱۳۰ | ۳۰ |
| `OCTOPUS-BLINDSPOTS-DELTA-2.md` | ۱۳۱–۱۹۶ | ۶۶ |
| `OCTOPUS-BLINDSPOTS-DELTA-3.md` | ۱۹۷–۳۲۷ | ۱۳۱ |
| `OCTOPUS-BLINDSPOTS-MASTER-BACKUP.md` | ۳۲۸–۴۶۳ | ۱۳۶ |
| `OCTOPUS-BLINDSPOTS-DELTA-4.md` (این) | ۴۶۴–۵۱۲ | ۴۹ |
| **جمع** | | **۵۱۲ نقطهٔ کور + ۱۴ تصحیح** |

**پوشش اسکن:** حالا شامل ۴۷ فایلِ top-levelِ `_ops/`، ۱۴ subdir، ۲۵ دایرکتوریِ vault، duplicates، Persian docs، secret hygiene. اسکن ساختاریِ تمام‌عیار.
