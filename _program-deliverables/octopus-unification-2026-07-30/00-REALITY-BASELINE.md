# 00 — REALITY BASELINE · مأموریتِ یکپارچه‌سازی

تاریخ: ۲۰۲۶-۰۷-۳۰ (شب) · برنچ: `fix/tg-p2-2026-07-30` · HEAD: `8d76618`
روش: خواندنِ سورس + AST + state ِ ران‌تایم؛ هیچ ادعای بی‌شاهد. «تستِ سبز ≠ زنده».

## ۰. قانونِ خوانده‌شده (پیش از هر کار)

- `PRE-0/CONSTITUTION.md` (۱۸ خط) — precedence ِ ۸لایه، hard constraints ⇒ −∞،
  self-improvement فقط measure/propose/test، AGI فرضیه، **merge_or_deploy ممنوع**.
- `PRE-0/SELF-IMPROVEMENT-BOUNDARY.md` — allow/forbid ماشین‌خوان؛ ناشناخته = رد.
- `PRE-0/GOVERNANCE-MAINTENANCE-LANE.md` — قانون/verifier فقط از lane ِ مالک.
- `ARCHITECTURE-SOT.md` (۲۶۹ خط) — `_ops` تنها بدنِ زنده؛ dormantها فهرست‌شده؛
  قاعدهٔ «canonical ِ نو باید همین‌جا ثبت شود».
- `_ops/SGC-14-PROTOCOL.md` — شکافِ اصلی با نامِ صریح: «پلِ اقدام (Goal Action
  Bridge) فازِ بعد است» + ۱۵ تهدید که دو تایش باز است (#۱۲ صفِ خالی، #۱۴
  نوشتنِ بی‌صدا-شکسته = VQ-STATE-WRITE-001).

## ۱. Git inventory (پیش از هر ویرایش)

```text
F:\backup            → fix/tg-p2-2026-07-30 @ 8d76618   (بدنِ زنده)
worktreeها           → ۴ ایجنتی (کهنه‌تر از HEAD؛ لمس نمی‌شوند)
dirty                → 185 M + 442 ??  (اکثراً ران‌تایم/والت؛ ۲ فایلِ پرریسک:)
  _ops/telegram_center/center.py        ← ۲ هانکِ بیگانه (بلوکِ tr، جلسهٔ موازی)
  _ops/budget/approval_channel.py       ← ۸ هانکِ بیگانه (tr/tool_request + consult)
organism.py · wiring.py · run_all.py    ← تمیز
```

قاعدهٔ عملی این جلسه (اثبات‌شده در ۴ کامیتِ جراحی قبلی): ویرایشِ این دو فایل
فقط با هانکِ جدا + `git apply --cached` ِ پچِ فیلترشده؛ دیفِ کامل قبل از هر
staging در scratchpad ذخیره می‌شود (بیمه‌نامهٔ بازسازی).

## ۲. Baseline tests — پیش از هر تغییر

`01-BASELINE-TESTS.{md,json}` — **۴۶۳/۴۶۳ شمارش‌پذیر + ۳ سوییتِ PASS-فرمت،
صفر قرمز، ۴۲ سوییت.** `run_all.py` ِ کامل BLOCKED (سابقهٔ ساختنِ
STOP-ORGANISM روی درختِ زنده؛ فقط در worktree با pin ِ ORG_ROOT — فازِ E2E).
۱۲ سوییت شمارش چاپ نمی‌کنند («OK N»/«PASS») — tail شان به‌عنوانِ شاهدِ اجرای
assert ثبت شد؛ گزارشِ خام در JSON.

## ۳. وضعیتِ ران‌تایمِ الان (شاهدِ زنده، نه سند)

| پروسه | PID | بوت | شاهد |
|---|---|---|---|
| organism | 24760 | ۱۹:۱۸:۲۸ | HEARTBEAT ۱۹:۲۰:۱۴ `organism=ok` |
| tg-center | 29020 | ۱۹:۴۳:۲۱ | لانچرِ حلقه‌ای + واچ‌داگِ ۵دقیقه‌ای Ready |
| cortex | 29180 | ۱۴:۱۲ | — |
| live server | 3476 | دیشب ۲۰:۳۰ | — |

دلتای امروز که **در پروسهٔ زنده بار شده** (کامیت‌های `2718921..8d76618`):
مسیریابیِ خروجیِ مرکز (resolve وصل، فلگ SPLIT_V1 مسلح، شاهد: `center-pulse →
DM` ۳۳ ثانیه بعدِ بوت) · ماشینِ حالتِ hold_policy (TG-HOLD-POLICY-LIVE) ·
مامور/owner_console وصل به Outer DM (پروبِ ۱۲سؤالی 12/12 آفلاین) · مدلِ Task ِ
پاها (leg_tasks، بارشده در بوتِ ۱۹:۴۳).

## ۴. جدولِ وضعیتِ اجزا (واژگانِ مصوب)

| component | status | شاهد |
|---|---|---|
| SGC-14 (goal→prereg→observe→verdict→pivot) | LIVE_PROVEN | چرخهٔ `2026-07-30#1`؛ فلگ‌ها مسلح؛ organism بوتِ ۱۹:۱۸ |
| Goal→**Action** (پلِ اقدام) | ABSENT | SGC-14 §بالا: «فازِ بعد» — هدفِ P0 ِ همین مأموریت |
| action_bridge | TESTED_NOT_WIRED | ۶۶/۶۶ baseline؛ `integration.py::STATUS="IMPLEMENTED_NOT_INTEGRATED"`؛ صداکنندهٔ تولیدی: ۰ (کاوشِ B) |
| unified_control | TESTED_NOT_WIRED | ۲۷ چک baseline؛ صداکنندهٔ تولیدی ۰ به‌جز owner_console/status.py (read-only) |
| owner_console | WIRED_NOT_LOADED→LOADED | وصل در `0025064`؛ مرکز بوتِ ۱۹:۴۳ با آن؛ LIVE ِ کامل منتظرِ گیت ۵ مالک |
| world_discovery | TESTED_NOT_WIRED | NO_VALID_DISCOVERY = خروجیِ معتبر؛ manifest ندارد (MANIFEST_MISSING) |
| telegram routing (خروجی) | LIVE_PROVEN | `4c36362` — رسیدِ ران‌تایم |
| hold_policy | LIVE_PROVEN (fake-proofs+boot) | `35acdef`؛ رسیدِ بحرانی/دایجستِ واقعی منتظرِ رخدادِ طبیعی |
| leg_tasks | WIRED_NOT_LOADED→LOADED | بوتِ ۱۹:۴۳؛ اولین استفادهٔ مالک هنوز نه |
| self-model freshness | CONFLICTED | `.tmp` تازه، فایلِ اصلی کهنه (WinError 5)؛ VQ-STATE-WRITE-001 |
| ORGANISM-STATE freshness | CONFLICTED | همان الگو؛ تهدید #۱۴ ِ SGC-14 |
| heart (سه‌گانه) | LIVE_PROVEN (shadow) | consensus/GREEN هر tick؛ `wire_open=false`؛ داور flag-off عمداً |
| memory read-path در تصمیم | (کاوشِ C) | پیش‌فرضِ سند: write-heavy/read-poor — منتظرِ شاهدِ AST |

## ۵. یافته‌های کاوشگرها

→ `02-CALL-GRAPH.md` (پنج کاوشِ موازیِ read-only: ستونِ مأموریت، مسیرِ اقدام،
حافظه، سلامتِ state، trace).
