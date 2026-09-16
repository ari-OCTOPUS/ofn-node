# Integration Bridge: Octopus Body ↔ Cognitive Kernel 0.1

## پل اتصال: بدن اختاپوس ↔ کرنل شناختی ۰.۱

---

## What is this

`body_bridge` is the read-only integration layer between the octopus body (4D system) and the Cognitive Kernel 0.1. It converts kernel-internal artefacts (ADRs, verdicts, experiments) into structured JSON feeds that the body can consume safely. The kernel never writes to the body; the body never modifies the kernel.

این ماژول لایهٔ یکپارچه‌سازی بین بدن اختاپوس (سیستم ۴بعدی) و کرنل شناختی ۰.۱ است. artefactهای داخلی کرنل (ADRها، verdictها، آزمایش‌ها) را به فیدهای JSON ساختاریافته تبدیل می‌کند که بدن بتواند به‌صورت امن آن‌ها را بخواند. کرنل هرگز به بدن نمی‌نویسد؛ بدن هم هرگز کرنل را تغییر نمی‌دهد.

---

## Data Flow

```
kernel (adr/, CLAIMS_LEDGER.csv, experiments/)
    ↓
body_bridge/ modules
    ↓
body_bridge/output/*.json
    ↓
body reads via kernel_consumer.py
    ↓
body_events (SQLite / notification)
```

All data flows in one direction: **kernel → output → body**. There is no reverse channel.

---

## Modules

| Module | Description |
|--------|-------------|
| `adr_feed.py` | Parses `adr/ADR-*.md` files and emits `output/adr_feed.json`. Provides `refresh_adr_feed()`, `get_adr_by_verdict(verdict)`, and `summary()`. |
| `verdict_stream.py` | Watches `CLAIMS_LEDGER.csv` and appends new verdicts to `output/verdict_stream.jsonl`. Provides `VerdictStream` class with `refresh()`, `since_last()`, `high_priority_items()`, and `notify_digest()` (Persian). |
| `manifest_generator.py` | Scans the kernel directory and writes `output/manifest.json`. Provides `generate()` and `validate_integrity()` (tamper detection). |
| `dashboard_sync.py` | Merges manifest, ADR feed, and verdict stream into `output/kernel_dashboard.json`. Provides `sync()` and `get_metric(key)` (dot-path). Includes `persian_report` field for owner-facing summaries. |
| `kernel_consumer.py` (body-side) | Read-only consumer imported by `brain/daemon.py` or `brain/automation.py`. `KernelConsumer(kernel_path)` sets up safe read-only access to all kernel outputs. |

---

## How to run

```bash
cd "F:/backup/03 - Projects/research-spec-compiler"
python body_bridge/adr_feed.py
python body_bridge/verdict_stream.py
python body_bridge/manifest_generator.py
python body_bridge/dashboard_sync.py
```

Tests:
```bash
python -m pytest body_bridge/tests/ -v
```

---

## Sensitivity Rules (قوانین حساسیت)

- **LOW** (`validate`, `run`, `read`): بدن می‌تواند خروجی‌های کرنل را بخواند.
- **MEDIUM** (`edits with rollback note`): تغییرات با یادداشت بازگشت.
- **HIGH** (`body.write`, `daemon activation`, `owner approval required`): هرگونه اقدام HIGH نیازمند verdict صریح مالک است.

- kernel **هرگز** به بدن نمی‌نویسد.
- بدن **فقط** از فایل‌های خروجی کرنل می‌خواند.
- تمام اقدامات **HIGH** نیازمند verdict مالک هستند.

---

## Body-side consumption (مصرف در سمت بدن)

The octopus body imports `KernelConsumer` from `brain.kernel_consumer`:

```python
from brain.kernel_consumer import KernelConsumer

consumer = KernelConsumer()
manifest = consumer.read_manifest()
dashboard = consumer.read_dashboard()
health = consumer.check_kernel_health()
action = consumer.suggest_automation_action()
```

All reads are lazy and safe. If the kernel directory is missing, the consumer degrades gracefully with logged warnings.
