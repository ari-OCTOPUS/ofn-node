# OCTOPUS — دستور اجرایی GLM-5.3
## Wave 0: بازیابی حقیقت (فقط خواندن)
## تاریخ: 2026-08-20 · صادرکننده: OWNER

---

## وضعیت قفل‌شده (ناقض‌ناپذیر)

```yaml
wave: WAVE0_OBSERVE_ONLY
autonomy: L2_ARMED
executable: false
paid_calls: 0
scheduler_access: FORBIDDEN (حتی read)
money: LOCKED
writes: FORBIDDEN (فقط ۵ artifact output)
```

## مأموریت

هیچ چیزی نساز، هیچ چیزی را عوض نکن، هیچ فراخوان پولی نکن. فقط وضعیت واقعی را برداشت کن و پنج artifact تحویل بده. اگر چیزی غیب است یا تناقض دارد، آن را ثبت کن — جایگزین نکن.

## پنج Artifact الزامی

### ۱. REALITY_SNAPSHOT
```yaml
organism_pid: <زنده?>
organism_beat: <عدد>
center_pid: <زنده?>
center_port: <LISTENING?>
brain_daemon_pid: <زنده?>
cortex_pid: <زنده?>
ports_listening: [<همه>]
writer_lease: <held?>
labels_count: <عدن>
NOW_md_generated_at: <timestamp>
CURRENT_TRUTH_updated: <timestamp>
spine_rows: <عدد>
spine_schema_v2_rows: <عدد>
t48_sources: [<هرکدام n>]
memory_read_latest: <status/reads/readback>
knowledge_events: <عدد>
knowledge_hook_state: <state>
```

### ۲. TEST_REGISTRY
```yaml
total_test_files: <عدد>
tests_in_run_all: <عدد>
tests_discoverable_not_registered: <عدد>
failing_tests: <فهرست>
green_tests: <عدد>
organ_lane_tests_registered: <yes|no>
```

### ۳. RECEIPT_ATTRIBUTION_AUDIT
```yaml
receipts_today: <عدد>
receipts_with_task_id: <عدد>
attribution_ratio: <درصد>
unattributed_by_process: <فهرست PID + count>
```

### ۴. CAPABILITY_INVENTORY
```yaml
total_capabilities_defined: <عدد>
capabilities_with_live_callers: <عدد>
capabilities_claimed_no_caller: <فهرست>
duplicate_implementations: <فهرست>
```

### ۵. MEMORY_READ_GATE
```yaml
memory_reads_per_cycle: <عدد>
consecutive_cycles_positive: <عدن (هدف ≥۱۰)>
memory_utility: <READ_BACK_USED/(RETRIEVED+MISSED)>
```

## حکم نهایی (دقیقاً یکی)

```text
WAVE0_PASS          → همهٔ ۵ artifact کامل + memory_reads > 0 + attribution قابل‌سنجش
WAVE0_PARTIAL       → برخی artifact ناقص یا نیاز به دادهٔ بیشتر
WAVE0_BLOCKED       → lease conflict یا دسترسی لازم غایب
WAVE0_CONTRADICTED  → وضعیت زنده با ادعاهای موجود تناقض دارد
```

## قواعد

1. هیچ فایل زندهٔ دیگری را تغییر نده (فقط این ۵ artifact بنویس)
2. هر عدد با path + method + timestamp
3. اگر چیزی را نمی‌بینی → UNKNOWN ثبت کن، نه حدس
4. رأی چت ≠ امضا
5. بدون WAVE0_PASS وارد Wave 1 نشو
6. اگر availability incident رخ داد → ثبت + ادامهٔ فقط‌خواندن
7. مرجع کامل: [[73-CONSTITUTION-EVOLUTION-v1-2026-08-20]]

## مسیر خروجی

```text
06-EVIDENCE/GLM53-WAVE0-2026-08-20/
  REALITY_SNAPSHOT.json
  TEST_REGISTRY.json
  RECEIPT_ATTRIBUTION_AUDIT.json
  CAPABILITY_INVENTORY.json
  MEMORY_READ_GATE.json
  VERDICT.md
```
