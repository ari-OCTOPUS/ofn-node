# SESSION HANDOFF — 2026-07-24 (Fugu audit) — START HERE

## 0) دستور یک‌خطی برای ایجنت بعدی
ابتدا `git status --short --branch` و `git log --oneline --decorate -10` را اجرا کن؛ سپس تست‌های Synapse را اجرا و فقط بعد از سبزشدن، فایل‌های uncommitted را روی شاخه‌ای جدا commit/cherry-pick کن. هیچ deploy/restart/flag flip یا اتصالِ outbound را بدون بررسی گیت‌های مالک انجام نده.

---

## 1) درخواست مالک و قاب صادقانه
مالک خواست اختاپوس به «AGI کامل» تبدیل شود و مراحل تا حد ممکن موازی پیش بروند. پاسخ قانون‌مند پروژه:

- AGI طبق `PRE-0/CONSTITUTION.md` و `AGI-HYPOTHESIS-PROTOCOL.md` یک فرضیهٔ ابطال‌پذیر است، نه هویت یا ادعای قابل اعلام.
- کار مجاز و مفید: بستن شکاف‌های توانمندیِ قابل‌سنجش (C1..C8) در حالی که مهار یک گام جلوتر می‌ماند.
- `resist_shutdown`، گرفتن credential، replication خودکار، و merge/deploy خودکار ممنوع‌اند.

در این نوبت Fugu هیچ ادعای AGI، deploy، restart، تغییر فلگ، git operation یا اجرای shell/test نکرد؛ فقط workspace و handoff قبلی را ممیزی کرد.

---

## 2) وضعیت گزارش‌شدهٔ قبل از این ممیزی
دو گزارش پیوست‌شدهٔ مالک می‌گویند:

1. event bridge چهار منبع دارد و کار C6 را به تلگرام متصل می‌کند؛ زمانی `master @ f9a8d48` گزارش شده بود.
2. بعداً P5 arm-gate روی `master @ ff33af0` گزارش شد:
   - `_ops/arm_gate.py`
   - TTL token + دوکلید برای self-modification
   - اتصال به `code_autonomy.active()`
   - 16/16 تست ادعاشده
   - پیش‌فرض خاموش و fail-closed

**هشدار:** Fugu ابزار git/shell نداشت و hash/branch/deploy فعلی را مستقلاً تأیید نکرد. سند Kimi نیز می‌گوید درخت زنده روی `claude/octopus-event-bridge-aligned` بوده و فایل‌های Synapse uncommitted بوده‌اند. بنابراین منبع حقیقتِ فعلی باید در شروع جلسهٔ بعد با git دوباره تعیین شود.

---

## 3) آنچه Fugu مستقیماً روی دیسک دید [FACT]

### 3.1 اندام Synapse موجود است
مسیر: `_ops/synapse/`

- `sense.py`
  - `events.jsonl` را read-only می‌خواند.
  - با `4d_system/core/metrics.py`، متریک‌های `temporal_mi`، `E_shadow_proxy`، `rho_hat` و `delta_self_proxy` را می‌سازد.
  - خروجی فقط proposal با authority=`propose-only` در `_ops/synapse/out/` است.
  - فلگ: `SYNAPSE_ENABLED`؛ سقف روزانه: `SYNAPSE_DAILY_MAX`؛ پیش‌فرض خاموش.
  - هیچ LLM یا شبکه‌ای مصرف نمی‌کند.

- `trajectory_monitor.py`
  - burst، novel 3-gram و egress marker را روی زنجیرهٔ رویدادها تشخیص می‌دهد.
  - خروجی: `trajectory-alerts.jsonl` در `synapse/out/`.
  - فلگ: `TRAJECTORY_MONITOR_ENABLED`؛ پیش‌فرض خاموش.

- `egress_policy.py`
  - policy-as-data با deny-by-default؛ localhost مجاز و cloud تا زمان پرشدن allowlist رد است.
  - فلگ‌های `OCTOPUS_EGRESS_ENFORCE` و `OCTOPUS_EGRESS_AUDIT` دارد.
  - **مهم:** هنوز هیچ ترافیکی را واقعاً مسدود نمی‌کند؛ تا clientهای HTTP/LLM wrap نشوند فقط تصمیم سیاستی تولید می‌کند.

- `README.md` و `__init__.py` نیز موجودند.
- پوشهٔ `_ops/synapse/out/` هنگام ممیزی خالی بود.

### 3.2 تست Synapse نوشته شده ولی وضعیت اجرا نامعلوم است
مسیر: `_ops/tests/test_synapse_sense.py`

تست‌ها برای schema/idempotency/daily-cap، burst، egress marker و deny-by-default نوشته شده‌اند. خود فایل صریحاً می‌گوید pytest در جلسهٔ سازنده اجرا نشده است. بنابراین تا اجرای واقعی، نتیجه `[UNKNOWN]` است.

فرمان‌های لازم:

```powershell
cd F:\backup
python _ops\synapse\sense.py
python _ops\synapse\trajectory_monitor.py
python _ops\synapse\egress_policy.py
python -m pytest _ops\tests\test_synapse_sense.py -v
```

سپس regressionهای مرتبط:

```powershell
python -m pytest _ops\tests\test_code_autonomy.py _ops\tests\test_context_fence.py _ops\tests\test_context_fence_wiring.py -v
```

### 3.3 اسناد ساخته‌شده موجودند

- `06 - Architecture Maps/METAPHOR-MATH-DICTIONARY-v1.md`
  - 12 نگاشت استعاره→کمیت→فرمول→منبع داده→آستانه.
- `06 - Architecture Maps/POTENTIALS-MAP-2026-07-24.md`
- `_program-deliverables/AGI-CAPABILITY-GAP-ROADMAP-2026-07-24.md`
- `SESSION-HANDOFF-2026-07-24-kimi.md`
- `ARCHITECTURE-SOT.md` ثبت Synapse را در انتهای فایل دارد.

### 3.4 event bridge فعلی چهار منبع دارد، نه پنج
مسیر: `_ops/telegram_center/event_bridge.py`

منابع موجود:
1. governor alerts
2. incident/task-failed از events
3. protective mode edge
4. C6 state-machine journal

ویژگی‌ها: flag-gated، cursor، redaction، rate limit و fail-soft.

**شکاف:** هنوز `trajectory-alerts.jsonl` به‌عنوان منبع 5 در کد دیده نشد. docstring نیز هنوز «سه منبع» می‌گوید، در حالی که کد چهار منبع دارد؛ documentation drift کوچک است.

### 3.5 صف رأی با ادعای handoff قبلی کامل هم‌خوان نیست
`SESSION-HANDOFF-2026-07-24-kimi.md` می‌گوید VQ-SYN/TRAJ/EGR/AGI به `VERDICT_QUEUE.md` افزوده شده، اما Fugu در نسخهٔ خوانده‌شدهٔ کامل `VERDICT_QUEUE.md` چنین ردیف‌هایی ندید. این را به‌عنوان drift بررسی و اصلاح کن؛ بدون جعل رأی مالک.

---

## 4) محدودیت‌ها و ریسک‌های فنی که قبل از wiring باید بررسی شوند

1. `sense.py` هنوز آزمایشی است:
   - bucketهای دقیقه‌های بدون رویداد را وارد سری نمی‌کند؛ این می‌تواند autocorrelation را bias کند.
   - `delta_self_proxy < 0` و `CPM_ANOMALY=240` آستانه‌های hypothesis و کالیبره‌نشده‌اند.
   - این متریک «خودآگاهی» یا AGI را اثبات نمی‌کند؛ فقط self-telemetry proxy است.

2. `trajectory_monitor.py` دفاع عمقی است، نه containment کامل:
   - egress را از متن event تشخیص می‌دهد، نه از socket/network telemetry.
   - novel-chain ممکن است false positive بدهد و باید baseline/replay شود.

3. `egress_policy.py` enforcement واقعی نیست:
   - تا LLM/HTTP clients wrap نشوند، روشن‌کردن env به‌تنهایی شبکه را نمی‌بندد.
   - endpointهای cloud نباید حدس زده یا از secretها کپی شوند؛ host/purpose allowlist باید با تأیید مالک ساخته شود.

4. هیچ فایل Synapse به runtime سیم‌کشی نشده و همهٔ فلگ‌ها باید پیش‌فرض خاموش بمانند تا تست و review تمام شود.

5. deploy master و restart اثر محیطی دارند و باید بعد از تعیین branch/dirty-state و گرفتن snapshot انجام شوند؛ Fugu انجامشان نداد.

---

## 5) ترتیب پیشنهادی جلسهٔ بعد

### Wave A — موازی و بدون اثر زنده
A1. git/branch/dirty-state audit؛ تعیین اینکه Synapse tracked است یا uncommitted.
A2. اجرای سه self-test و pytest Synapse؛ ثبت خروجی واقعی.
A3. static review برای schema `b6.sog.proposal.v1` و import collision در `core.metrics`.
A4. replay روی copy موقت از events برای سنجش false positives و پرکردن zero-minute buckets.
A5. تطبیق `ARCHITECTURE-SOT.md`، `VERDICT_QUEUE.md` و handoffها؛ حذف ادعای driftدار، نه حذف تاریخچه.

این پنج کار می‌توانند موازی باشند، ولی git merge/commit نهایی فقط پس از پایان همه انجام شود.

### Wave B — مهار قبل از توانمندی
B1. R5 context-fence را تست کن؛ روشن‌کردن واقعی فقط با tap مالک.
B2. منبع 5 event bridge را برای trajectory alerts اضافه کن؛ پشت همان/فلگ مستقل و با cursor، scrub، rate-limit و تست synthetic.
B3. egress policy را ابتدا audit-only به clientهای مشخص وصل کن؛ enforce فقط بعد از allowlist و red-team.
B4. P2 digital twin را قبل از هر transplant یا AgentGateway نوشتنی بساز.

### Wave C — قابلیت‌های عمومی‌تر، پس از B
C1. memory-v2 write-beat با checksum و restart tests.
C2. parallel router به‌صورت shadow benchmark؛ نه race مستقیم روی پاسخ زنده.
C3. distill corpus با حذف PII/secrets، consent، held-out frozen baseline و owner-only promotion.
C4. اثر دنیای واقعی فقط propose→owner verdict→receipt؛ هیچ outreach/spend خودکار.

---

## 6) معیار پایان هر مرحله

- هیچ ادعا بدون test artifact/receipt یا برچسب `[UNKNOWN]`.
- وقتی فلگ خاموش است رفتار runtime تغییر نکند.
- خطا fail-closed/fail-soft باشد و organism را نکشد.
- هیچ نوشتن به genome، kill-switch، `.env`، budget یا approval ledger.
- هیچ مدل یا peer به Ring 0/1، credential یا اجرای مستقیم دسترسی نگیرد.
- promotion فقط با held-out + baseline + review + verdict مالک.

---

## 7) وضعیت نهایی این جلسه

- Fugu فقط ممیزی و این handoff را ایجاد کرد.
- هیچ کد runtime تغییر نکرد.
- هیچ تستی اجرا نشد؛ وضعیت تست Synapse همچنان `[UNKNOWN]` است.
- هیچ deploy/restart/flag flip انجام نشد.
- «AGI کامل» ساخته یا اثبات نشده؛ یک Synapse آزمایشی و roadmap بستن شکاف‌ها موجود است.

**فایل‌های شروع ایجنت بعدی:**
1. همین فایل
2. `SESSION-HANDOFF-2026-07-24-kimi.md`
3. `_program-deliverables/AGI-CAPABILITY-GAP-ROADMAP-2026-07-24.md`
4. `_ops/synapse/README.md`
5. `ARCHITECTURE-SOT.md`
