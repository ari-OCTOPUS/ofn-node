# R01-GOVERNANCE-GAPS — مسیرهای activation، scheduler، راز، شبکه، و نقض fail-closed

run: R01-191-20260818-2217

## ۱. مسیرهای activation (چیزهایی که «وضعیت» را عوض می‌کنند)

| مسیر | وضعیت | ناسازگاری/شکاف |
|---|---|---|
| `_ops/ACTIVATION-RAW-SHELL.flag` | موجود → /sh مسلح | **نقض سیاست D2** تا ceremony حذف؛ ایجاد/حذف پرچم باید مالکی باشد — سازوکار two-stage موجود نیست |
| `_ops/budget/FREEZE.flag` | موجود (Errno 22، Aug 16) | مسیر settle خراب؛ پرچم مانده و budget halted=false — یعنی FREEZE **تزئینی** برای ARCHITECT_SYS (حکم ENFORCED/DECORATIVE = F4، شاهد اول اینجا) |
| `GITWRITE-FAILED.flag` | موجود (TIMEOUT قفل، امروز 03:50) | مسیر git-write قفل است؛ پاک‌کردنش فقط با تصمیم مالک (رعایت شد) |
| STOP-ORGANISM / HALT-ALL | منطق تقدم در opslib:357–367 موجود | enforcement در «هر حلقه/کانکتور» CLAIMED — تست نشد (F4) |

## ۲. مسیرهای scheduler

- ۱۲ تسک ویندوزی فعال (F1 §2) — همهٔ اکشن‌ها به فایل واقعی در vault؛ watchdogها پروسه‌ها را **خودکار ری‌استارت** می‌کنند (auto-heal). این pre-existing و owner-era است، ولی: هیچ تسکی نباید بدون OwnerDecision اضافه/حذف شود (R01_FORBIDDEN رعایت شد — صفر تغییر).
- نکتهٔ F4: فهرست کامل trigger هر ۱۲ تسک (زمان/رویداد) هنوز استخراج نشده.

## ۳. ریسک‌های راز

1. **B1**: `mail_credentials.py` tracked در git + آینهٔ E: (HIGH).
2. `.octopus-signing/` کلید خصوصی مالک — gitignored (خوب)؛ backup policy آن UNVERIFIED (F4).
3. `.env` ×6 — روت و 4d_system ignored؛ بقیه (`_build/…`، QuantumAlphaBot) وضعیت ignore **UNVERIFIED** (چک نشد — عمق F4).
4. در این run: صفر نمایش/کپی/commit راز؛ یک redaction در F1؛ فایل خام حذف شد.

## ۴. مسیرهای شبکه

- Ingress عمومی: دو tunnel فعال cloudflared (named + **quick-tunnel بدون identity**) — policy فعلی برای هیچ‌کدام مکتوب نیست → تصمیم مالک.
- board_cp روی 0.0.0.0 (B8).
- Egress: ۱۰+ ماژول شناسایی؛ قرارداد receipt/budget per-endpoint UNVERIFIED (API-BOUNDARY §2).
- طبق D6: صفر تماس با بردها در این run — رعایت شد.

## ۵. نقض‌های fail-closed مشاهده‌شده

- **fail-closed درست کار می‌کند در:** `_is_owner` (allowlist، خطا=False) · shell_capability.active() (هر خطا=False) · classifier A2=BLOCK (تست ۲۴/۲۴).
- **شکاف‌های fail-closed:** FREEZE تزئینی برای ARCHITECT_SYS (§۱)؛ ingest حافظه بدون گیت admission (MEMORY-AUDIT §۲)؛ quick-tunnel بی‌identity.

## ۶. حکم کلی GOVERNANCE برای مالک

ساختار گیت‌ها در کد واقعی و اغلب fail-closed است — تصویر «همه‌چیز WIRED=False» اسناد شورا **رد شد**؛ اما سه مسیر مسلح/باز (پرچم /sh، FREEZE بی‌اثر، tunnel بی‌identity) دقیقاً همان جاهایی‌اند که F4 باید ENFORCED/DECORATIVE را نهایی کند. هیچ‌کدام در این run دست نخورد.
