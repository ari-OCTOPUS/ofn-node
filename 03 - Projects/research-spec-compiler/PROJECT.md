---
type: project
kind: brain
project: "[[03 - Projects/research-spec-compiler/PROJECT]]"
status: active
owner: آری
risk_level: low
autonomy_level: read-only
tags: [cognitive-kernel, research, cortex, shadow, propose-only]
created: 2026-07-14
updated: 2026-07-14
---

# پروژه: research-spec-compiler (اندام شناختیِ Ring-2 — shadow)

> 🧠 **رکنِ ساخت:** یک node در §۳ رجیستریِ اتصال (URCP)، ثبت‌شده به‌عنوان
> **brain/tool سیبلینگ، نه tenant**. اتصالِ shadow، تأییدشدهٔ مالک (Q1، اقدامِ
> نارنجی، 2026-07-14). این فایل تنها ثبتِ رجیستری است؛ هیچ اثری فعال نمی‌کند.

## Mission

کرنلِ حقیقتِ ابطال‌پذیرِ Cognitive Kernel 0.1 — هر «ایده» را به specِ ۵-گیتی
کامپایل می‌کند و verdictِ ماشینی می‌دهد (DISCARD/OPTIMIZE/INTEGRATE/REJECTED).
شکاف‌های بازِ cortexِ ارگانیسم (تثبیت، خود-پایش) را با دیسیپلینِ ابطال‌پذیر پر
می‌کند. verdictِ ماشینیِ اتصال: **OPTIMIZE (shadow-only)** — منبع پایین.

## قراردادِ اتصال (نشکن)

| بُعد | مقدار |
|---|---|
| ring | ۲ (اندام شناختی؛ نه Ring 0/1) |
| afferent | broadband، **read-only** روی `dashboard_events` (`mode=ro&immutable=1`) |
| efferent | **propose-only** — spec/verdict/proposal به‌صورتِ فایل‌نو در پوشهٔ خودِ کرنل |
| off_flag | **true** — غیرفعال؛ فعال‌سازیِ اثرِ زنده = گیتِ نارنجیِ جداگانه |
| هرگز | نوشتن به بدن (جز همین ثبت) · لمسِ TCB/genome/pulse (لنگر 0.135073) · اقدامِ بیرونی · ساختِ حساب/راز |
| scope | access/functional فقط — **هرگز phenomenal/qualia** |
| revocable | بله — حذف/انتقالِ این پوشه اندام را کاملاً بازمی‌گرداند (germline دست‌نخورده) |

## مکانِ کد و شواهد (خارج از بدن)

- کد و کلِ قرارداد: `C:\Users\Armin\Desktop\121212121212121212\research-spec-compiler\`
- قراردادِ جعبه‌سیاه: `…\research-spec-compiler\attach-proposal\` (MANIFEST/adapter/DecisionLog/OpenQuestions)
- **verdictِ اتصال:** `…\adr\ADR-008-hybrid-cortex-organism-attach.md` — OPTIMIZE،
  bottleneck_advantage 0.036 روی event streamِ واقعیِ همین بدن [FACT].
- دفترِ verdictها: `…\CLAIMS_LEDGER.csv` (۲۰ آزمایشِ REAL، ۲۱ ADR).

## Current state

- **shadow، غیرفعال، فقط-خواندنی.** بدن اکنون اندام را می‌بیند (registry_scan)،
  اما اندام هیچ اثری بیرون نمی‌گذارد.
- daemonِ پژوهشیِ 4d از 2026-07-11 متوقف است؛ snapshotِ خوانده‌شده ثابت بود.
- قدمِ بعدی (گیتِ نارنجیِ جداگانه، تصمیمِ مالک): بازفعال‌سازیِ daemon برای دادهٔ
  تازه، یا ارتقای اثر از propose به shadow-run. تا آن verdict، هیچ.

## Integration with Octopus Body (فعال)

> **Owner-commanded activation (HIGH sensitivity gate, 2026-07-14).**
> The kernel now exposes structured read-only feeds that the body consumes via
> `kernel_consumer.py`. The kernel NEVER writes to the body; the body ONLY reads.

### body_bridge modules (کرنل → خروجی)

- **`body_bridge/adr_feed.py`** — parses all `adr/ADR-*.md` files into `output/adr_feed.json`.
  - Provides `refresh_adr_feed()`, `get_adr_by_verdict(verdict)`, and `summary()`.
- **`body_bridge/verdict_stream.py`** — watches `CLAIMS_LEDGER.csv` and appends new verdicts to `output/verdict_stream.jsonl`.
  - Provides `VerdictStream` class with `refresh()`, `since_last()`, `high_priority_items()`.
  - `notify_digest()` returns a short Persian text summary for Telegram/notification.
- **`body_bridge/manifest_generator.py`** — scans the kernel directory and writes `output/manifest.json`.
  - Provides `generate()` and `validate_integrity()` (detects tampering).
- **`body_bridge/dashboard_sync.py`** — merges manifest, ADR feed, and verdict stream into `output/kernel_dashboard.json`.
  - Provides `sync()` and `get_metric(key)` (dot-separated path).
  - Includes `persian_report` field for owner-facing summaries.

### Body-side consumer (بدن → خواندن)

- **`4d_system/brain/kernel_consumer.py`** — read-only consumer imported by `daemon.py` or `automation.py`.
  - `KernelConsumer(kernel_path)` — sets up read-only access.
  - `read_manifest()`, `read_dashboard()`, `read_adr_feed()`, `read_verdict_stream(since)`.
  - `check_kernel_health()` — returns `{reachable, manifest_fresh, integrity_ok, last_sync}`.
  - `suggest_automation_action()` — suggests body action based on kernel state (e.g., `"review"` if REJECTED exists).
  - `publish_body_event(event_name, summary)` — emits body event via `brain/events.py`.

### Data flow (جریان داده)

```
kernel (adr, experiments, ledger) → body_bridge/output/*.json → body reads → body_events (SQLite)
```

- The kernel writes **only** into `body_bridge/output/`.
- The body reads **only** from those JSON files.
- All paths are absolute (`F:/backup/...`) or resolved via `pathlib.Path(__file__)`.
- Every module has error handling, logging, and degrades gracefully if dependencies are missing.

### Running the bridge (اجرای پل)

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
python -m pytest "F:/backup/4d_system/brain/tests/test_kernel_consumer.py" -v
```

> ⚠️ هیچ اثرِ بیرونی/مالی/تولیدی بدونِ verdictِ صریحِ مالک. `apply_merge` unwired.

## Integration with Octopus Body (فعال)

The kernel is now integrated with the octopus body via `body_bridge/` modules:
- `adr_feed.py` — structured ADR feed
- `verdict_stream.py` — CLAIMS_LEDGER verdict stream
- `manifest_generator.py` — machine-readable manifest
- `dashboard_sync.py` — dashboard metrics JSON
- The body consumes these via `F:/backup/4d_system/brain/kernel_consumer.py`

Data flow: kernel → body_bridge/output/*.json → body reads → body_events
All writes are kernel-internal; the body never modifies the kernel.

