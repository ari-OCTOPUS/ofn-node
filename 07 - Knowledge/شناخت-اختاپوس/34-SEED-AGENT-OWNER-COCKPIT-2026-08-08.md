---
type: cognition-note
status: active
tags: [seed-agent, owner-cockpit, state-guard, fugu-proxy, otel, audit, hmac]
created: 2026-08-08
updated: 2026-08-08
created_by: agent
depends_on:
  - "[[32-INDEPENDENT-VERIFICATION-2026-08-08]]"
  - "[[33-DEEP-SCAN-TRIPLE-FIX-2026-08-08]]"
---

# ۳۴ — Seed Agent v1 + Owner-Cockpit Stack + StateGuard (۲۰۲۶-۰۸-۰۸)

> سه فازِ بزرگ در یک session — از دیتای خراب تا پراکسیِ Fugu و پنلِ مالک.

## روش

این session با دیپ‌اسکنِ وب‌اپ شروع شد (نوت ۳۳ + این session)، بعد به سه مسیرِ
مستقل تقسیم شد: (الف) StateGuard برای دیتای سالم، (ب) Seed Agent v1 برای تحلیلِ
هوشمند، (ج) Owner-Cockpit برای کنترلِ مالک از تلگرام.

## فازِ الف — StateGuard (۵ commit)

### مسئله
۶ فایلِ JSONL در `state/` corrupt بودند — هر کدام یک خطِ null-only (امضای
crash وسطِ نوشتن). ریشه: `opslib.append_jsonl()` بدون fsync.

### فیکس
۱. `_ops/state_guard.py` — scan + repair با arm gate + maintenance lock
۲. repair روی allowlistِ ۶ فایل: null stripped، invalid quarantined، atomic rewrite
۳. `opslib.append_jsonl` harden شد با `fh.flush()` + `os.fsync()`
۴. ۲ نویسندهٔ raw (tick_timing, reach_probe) به append_jsonl migrate شدند

### نتیجه
- ۵۴۴۶۲ رکوردِ معتبر حفظ شد (صفر داده از دست‌رفته)
- ۶ معیار موفقیت PASS (null=0, invalid=0, valid preserved, quarantine+meta, receipt, post-restart)
- rescan: ۰ null در allowlist targets

## فازِ ب — Seed Agent v1

### معماری (تصمیمِ کلیدی: یک ایجنت، نه دو تا)
Architect موجود ارتقا یافت — نه ایجنتِ دوم. دلیل: جلوگیری از self-model موازی
چهارم (درس: ۳ self-model فعلی reconcile نمی‌شدند).

### فایل‌های ساخته‌شده
- `_ops/seed/context_assembler.py` — ۷-slot prompt assembler (RULES/MISSION/STATE/
  FACTS/EPISODES/TRACE/USER). trim هوشمند، fail-soft، stale-fetch guard.
- `_ops/seed/octopus_reader.py` — bridge read-only (snapshot/retrieval/semantic/trace)
- `_ops/seed/evolution_gate.py` — safe self-improvement با evaluator مستقل (ADR-014)
- `_ops/seed/redteam_harness.py` — sandbox escape simulation (ADR-012/013)
- `_ops/seed/canary.py` — CLI تستِ زنده

### Seed Pack
- v1: ۹ memory unit (policy/fact/preference/trace) — ingested در Architect vault
- v1.1 delta: تصمیمِ یک-ایجنتی + StateGuard results
- v1.2 delta: Owner-Cockpit completion

### تستِ زنده (canary)
۷ slot همگی با داده‌ی واقعی پر شدند:
`beat=28792 | flags=215/244 | dark_gates=65`, ۵ episodes, ۵ traces.

## فازِ ج — Owner-Cockpit Stack (۸ WP)

### فایل‌های ساخته‌شده
| فایل | نقش | پورت/فلگ |
|---|---|---|
| `fugu_proxy.py` | پراکسیِ محلی Fugu + usage normalizer | :8787 / `OCTOPUS_WIRE_FUGU_PROXY` |
| `otel_setup.py` | OTel spans (JSON-lines) | `OCTOPUS_WIRE_OTEL` |
| `db.py` | SQLite ۴ جدول + hash-chained audit | `OCTOPUS_WIRE_OWNER_DB` |
| `owner_api.py` | HTTP API + HMAC auth + approval | :8788 / `OCTOPUS_WIRE_OWNER_API` |
| `miniapp/index.html` | Mini App ۵ تب RTL تم تیره | — |

### امنیت (۷ لایه)
۱. HMAC initData (الگوریتم رسمی Telegram)
۲. Session جدا (۳۰ دقیقه، hash در DB)
۳. Owner allowlist
۴. Consume-once در confirm
۵. CORS محدود به web.telegram.org
۶. Rate limit ۳۰/دقیقه
۷. Freeze بدون approval ولی در audit ledger

### قیمت‌گذاریِ Fugu (verify‌شده ۲۰۲۶-۰۸-۰۸)
- $5/1M input, $30/1M output, $0.50/1M cached (standard)
- $10/$45/$1.00 (context >272K)
- Orchestration tokens جداگانه track می‌شوند
- منبع: console.sakana.ai/pricing

### ADR: fugu_quota vs provider_usage
`fugu_quota` = circuit breaker (attempt-based, gate قبل از call).
`provider_usage` = financial tracking (token/cost, ledger بعد از response).
مکمل، نه متضاد.

## درس‌های کلیدی

۱. **دیتای سالم قبل از تحلیل** — StateGuard اول، بعد assembler. اگر assembler
   روی دیتای خراب اجرا شود، trace envelope آلوده می‌شود.
۲. **یک ایجنت، نه دو تا** — ساختنِ ایجنتِ دوم = self-model موازی. Architect
   ارتقا یافت، نه جایگزین.
۳. **همه پشت فلگ default-OFF** — StateGuard، Seed Agent، Owner-Cockpit همه
   پشت فلگ‌های جدا. بدون arm صفر اثر.
۴. **fsync روی Windows** — `append_jsonl` بدون fsync = corruption. یک خط
   تغییر (`fh.flush()` + `os.fsync()`) ۶ نویسنده را immunize کرد.

## توصیه به ایجنت بعدی

۱. **Go-live Owner-Cockpit**: `FUGU_API_KEY` + `TELEGRAM_BOT_TOKEN` +
   `OWNER_TELEGRAM_IDS` در env، سپس owner_api روی :8788، cloudflared tunnel.
۲. **approval_items wiring**: جدول در db.py هست ولی model_router هنوز به آن
   وصل نیست. این کارِ WP بعدی است.
۳. **saba-bridge.jsonl**: ۱۲ خطِ invalid (comment format) — مستثنی شد از
   scan. اگر فرمتِ عمدی است، نوت کن.
۴. **live $0.10 call**: آخرین آیتمِ چک‌لیست verify — نیاز به کلیدِ واقعی.
