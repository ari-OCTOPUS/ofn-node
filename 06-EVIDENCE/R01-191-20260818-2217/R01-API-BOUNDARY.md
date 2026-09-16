# R01-API-BOUNDARY — نقشهٔ ورودی‌ها و مسیرهای اثر (INITIAL)

run: R01-191-20260818-2217 · عمق این سند: نگاشت سطح-ورودی از شواهد F1 + کد؛ ممیزی خط‌به‌خط هر endpoint = F4/R02 (در هر ردیف صریح شده).

## ۱. ورودی‌های شبکه (Ingress)

| Entry | آدرس | Auth | Side-effect | گیت | وضعیت کنترل |
|---|---|---|---|---|---|
| Telegram cockpit (`telegram_center/center.py`) | 127.0.0.1:8776 + دریافت از Telegram (long-poll — پروسهٔ زنده) | `_is_owner` allowlist، fail-closed (center.py:2657، فراخوانی:2678) | اجرای دستورهای /ش، ارسال پیام، خواندن state | allowlist + per-capability (مثل shell_capability) | **PRESENT** — enforcement دومرحله‌ای برای /sh: **ABSENT** (D2 ناسازگار) |
| `/sh` خام | از داخل center | ACTIVATION-RAW-SHELL.flag (موجود=ARMED) + deny-list §۰ + timeout 120s + audit (لاگ دیده نشد) | shell محدود به F:\backup | fail-closed در ماژول | PRESENT اما **ARMED برخلاف D2** |
| board_cp (`_ops/board_cp/server.py`) | **0.0.0.0:8801** (TLS — cert.pem در state) | UNVERIFIED (این پاس بازبینی نشد) | فرمان به بردها (commands.sqlite) | UNVERIFIED | **GAP: bind همهٔ اینترفیس‌ها** — با بازگشت LAN سطح exposure عوض می‌شود |
| miniapp_gateway | 127.0.0.1:8774 | UNVERIFIED | رابط mini-app تلگرام | UNVERIFIED | عمق: F4 |
| organism / cortex / live | 127.0.0.1:8771/8772/8773 | UNVERIFIED | حلقه‌های داخلی | UNVERIFIED | عمق: F4 |
| cloudflared `octopus-cp` (named tunnel) | عمومی → local (config: `C:\Users\Armin\.cloudflared\octopus-cp-config.yml`) | Cloudflare | ingress عمومی | خارج از vault — **مرور نشد (راز-محور)** | **UNVERIFIED — تصمیم مالک: آیا tunnel عمومی فعلاً لازم است؟** |
| cloudflared quick tunnel `octopus-miniapp` | عمومی → 127.0.0.1:8774 | بدون identity (quick tunnel) | ingress عمومی موقت | — | **GAP: quick-tunnel بدون احراز هویت دائمی** |

## ۲. ماژول‌های خروجی (Egress — شناسایی‌شده، ممیزی‌نشده)

`_ops/integrations/outbound_https.py` · `_ops/budget/approval_channel.py` · `_ops/legs/email_inbound.py` · `_ops/legs/books_xero.py` · `_ops/cortex/web_research.py` · `_ops/cortex/local_llm.py` · `_ops/cortex/code_brain.py` · `_ops/debate/client.py` · `_ops/agi2027_control/runtime.py` · `_ops/tg_receive_probe.py`

کنترل‌های مورد انتظار مالک برای هرکدام: auth source · timeout · retry · budget · receipt.
وضعیت فعلی: **UNVERIFIED مورد‌به‌مورد** — در این پاس فقط شناسایی شدند. بودجهٔ مرکزی موجود است (`_ops/budget/` + cardiac-budget.json + FREEZE.flag Errno22) یعنی لایهٔ budget پیاده شده؛ اتصال per-endpoint اثبات نشد.

## ۳. مسیرهای غیرشبکه‌ای اثر

- زمان‌بند: ۱۲ تسک (F1 §2) — همه به فایل واقعی؛ watchdogها پروسه‌ها را ری‌استارت می‌کنند (auto-heal پیش‌موجود؛ با WAVE0 ناسازگار نیست چون owner-era است، ولی باید در F4 فهرست کامل شود).
- git: پرچم `GITWRITE-FAILED` + قفل gitwrite.lock (متن پرچم: TIMEOUT پس از ۴۰ تلاش) — مسیر git-write دارای گیت قفل است؛ پاک‌کردنش فقط با تصمیم مالک.
- فایل: shell_capability deny-list §۰ (حذف/git/راز/شبکه/scheduler ممنوع در /sh) — PRESENT در کد.

## ۴. کنترل‌های غایب (فهرست F4)

1. گیت دومرحله‌ای برای /sh (D2).
2. احراز هویت board_cp + تغییر bind به loopback.
3. سیاست tunnel عمومی (named + quick) — تصمیم مالک.
4. قرارداد receipt یکنواخت برای همهٔ egress (امضا/هش مثل envelope).
5. observability خطا/retry/timeout در سطح endpoint (لاگ متمرکز قابل audit).
