---
type: decision
decision_id: D3-CLOSURE-ROTATE-ACCEPT-2026-08-19T0940Z
status: SIGNED (ed25519 delegated key — sig beside)
created: 2026-08-19T09:40Z
created_by: owner (interactive) — recorded by ZCode agent
supersedes: D3_GIT_HISTORY_RISK=OPEN
---

# بستن D3 — چرخش + پذیرش

حکم مالک: اعتبارنامه‌های قدیمیِ موجود در تاریخ git باقی می‌مانند (بازنویسی تاریخ ممنوع‌مانده و انجام نمی‌شود)؛ ریسک پذیرفته می‌شود؛ کلیدهای فعال **چرخش** می‌شوند تا هر مقدار تاریخی از امروز به بعد بی‌ارزش باشد.

## چک‌لیست چرخش (مالک — در پنل هر سرویس)
- [ ] GLM_API_KEY (bigmodel) — کلید نو؛ آدرس آینه هم هنگام تنظیم GLM_BASE_URL ثبت شود
- [ ] DEEPSEEK_API_KEY — کلید نو
- [ ] TELEGRAM_BOT_TOKEN (اگر هنوز فعال است)
- [ ] هر سرویس دیگر با کلید در تاریخ قدیمی (اسکن قبلی: فقط موارد بالا)

بعد از هر چرخش، مقدار نو در `.env` (فقط محلی) جایگزین می‌شود — ایجنت هرگز مقدار را نمی‌بیند/ثبت نمی‌کند؛ فقط `KEY_ROTATED=true/false` تأیید می‌کند.

## اثر رجیستری
لیبل D3_GIT_HISTORY_RISK: ‏OPEN → CLOSED_ROTATED_ACCEPTED (پس از تأیید چرخش واقعی مالک).
