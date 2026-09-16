# R01-REALITY-MANIFEST — هر مسیر ادعایی: PRESENT / ABSENT / UNVERIFIED

run: R01-191-20260818-2217 · 2026-08-18 ~22:17–22:4x +10:00 · node .191
مبنا: artifactهای F1 (verified 27/27) + بازرسی تازهٔ همین run. برچسب‌ها عیناً.

## مسیرهای ادعاشده در اسناد شورا/اسپرینت

| مسیر / شیء ادعایی | وضعیت | شاهد |
|---|---|---|
| `tools/now.py` | **ABSENT** | جستجوی کل درخت (پوشهٔ tools وجود ندارد) |
| `docs/NOW.md` | **ABSENT** | همان |
| `validate_vault` | **ABSENT** | همان |
| `SELF-MODEL-REALITY.json` | **ABSENT** | همان — cite شده در سند شورای ۲ و ۴؛ «ارجاع بی‌مرجع» |
| `OCTOPUS-200-CHECKLIST-2026-08-15.md` | **ABSENT** (روی لپ‌تاپ) | دو جستجوی مستقل؛ workspace پروژهٔ خارجی: CLAIMED مالک |
| `OBSIDIAN-REBUILD-MEGAPROMPT-2026-08-15.md` | **ABSENT** | همان |
| `docs/gaps/GAP-001.md` | **ABSENT** (GAP-001 فقط مفهوم در اسناد) | grep کل درخت |
| `octopus-research-sprint/` | **PRESENT — FROZEN (D5)** | ۳۷ فایل placeholder، ساخته 21:20–21:22، فقط inventory شد |

## زیرساخت واقعی (OBSERVED)

| مسیر / شیء | وضعیت | شاهد |
|---|---|---|
| Vault canonical `F:\backup` | PRESENT (حکم پیشین مالک) | repo HEAD 1db8894، dirty=411 |
| آینهٔ germline `E:/germline/octopus.git` | PRESENT | bare، آخرین دست‌خوردگی Aug 17 |
| ۵ worktree ثبت‌شده `.claude/worktrees/*` | PRESENT | dirty: fugu=10، hybrid=14، بقیه ۰؛ امروز صفر تغییر |
| ششمین دایرکتوری `telegram-operational-control-de7666` | **PRESENT-ORPHAN** (بدون .git، ثبت‌نشده در worktree list) | ls/verify این run |
| ۲ stub-git (AI-sume، genome-system) | PRESENT — init ناتمام، `config.lock` رهاشده، HEAD→master بی-commit | محتوای دایرکتوری |
| ۷ باندل `nbb-control-plane-history.bundle` | PRESENT — **هر ۷ بیت‌به‌بیت یکسان** (sha256=0b656431d4a4fafa…، 96,075B) → ۶ کپی دقیق | sha256sum این run |
| `~/.octopus-signing/` (کلید ed25519 مالک) | PRESENT — gitignored؛ فقط متادیتا | F1 §3 |
| `_ops/state/memory/memory.db` | PRESENT — 884,736B، ۴۸۳ سطر + FTS، فعال | F1 07c |
| `_ops/state/memory.db` | PRESENT — صفربایتی یتیم (mtime 2026-08-07)، بدون ارجاع کدی | F1 03b/07e |
| `_ops/state/chrono.db` | PRESENT — heartbeat 40,713 · checkpoint 40,712 · experience_meter 40,266 · anticipation ۶ · gated_effect **۰** | F1 07c |
| events.jsonl | PRESENT — ۴٬۶۷۵ شناسهٔ یکتا، **۰ تکراری** | 03-code-map (h) |
| NATS روی لپ‌تاپ | **ABSENT** (listener 4222=false، پروسه نیست) | پاکت service-inventory + F1 §1 |
| `/sh` handler + زنجیرهٔ گیت | PRESENT — center.py:3213 · `_is_owner`:2657 · shell_capability fail-closed | F1 §7 |
| `_ops/ACTIVATION-RAW-SHELL.flag` | **PRESENT → ARMED** (ناسازگار با D2 تا ceremony disarm) | F1 07e |
| `STOP-RAW-SHELL` / `STOP-ORGANISM` / `HALT-ALL` | ABSENT (فعال نیست) — منطق تقدم در `_ops/budget/opslib.py:357–367` موجود (HALT-ALL > STOP) | 03-code-map (g) |
| raw-shell audit log | ABSENT — هیچ استفادهٔ ثبت‌شده‌ای از /sh دیده نشد | F1 §7 |
| `_ops/tests/run_all.py` | PRESENT (runner سفارشی؛ الگوی `t_*` را اجرا می‌کند — نه pytest استاندارد) | 02-test-matrix |
| تست‌های pytest-قابل-collect | PRESENT — hypothesis_policy R16 (۱۱) · math-atlas (۴۱) — هر دو exit=0 | 02-test-matrix |
| تست‌های الگوی `t_*` | PRESENT — classifier ۲۴/۲۴ پاس · envelope ۵/۵+۱ fixture — **pytest آن‌ها را collect نمی‌کند** | 02-test-matrix |

## جمع‌بندی

هفت ارجاع کلیدی اسناد خارجی **ABSENT** (فانتوم/خارج از این ماشین)؛ زیرساخت واقعی موجود و فعال است اما نام‌گذاری/اسناد بیرونی با آن هم‌خوان نیست. هر سند آینده باید از ستون «شاهد» همین جدول ارجاع بدهد، نه از ادعای چت.
