# Owner Console — نتیجه قابل لمس برای انسان

وضعیت: `IMPLEMENTED_NOT_WIRED`

این بسته پاسخ مستقیم به مشکل «صدها تغییر انجام شد ولی تلگرام چیزی نشان نمی‌دهد» است.
به‌جای سیم‌کشی دستی هر قابلیت، یک facade واحد برای Outer DM می‌دهد:

- خانه و منوی انسانی
- کاتالوگ manifest + کارت‌های قدیمی
- تفاوت صریح CODE / WIRED / SANDBOX / LIVE / INVALID
- هدف فعلی و سنجه
- حقیقت runtime قلب/خودمدل/عصب‌کشی
- blockerها
- World Discovery
- proposal فقط‌خواندنی
- درخواست حساس → BLOCKED_BY_OWNER
- ناشناخته → clarify

## مرز امنیتی

- بدون transport و poller
- بدون send/spend/restart/arm/merge/deploy
- بدون state write
- discovery با metadata است، نه import قابلیت‌ها
- manifest خراب پنهان نمی‌شود ولی LIVE هم نمی‌شود
- registration مجوز نیست
- callback ناشناخته block می‌شود

## اتصال مورد انتظار

بعد از اینکه `input_surface_policy` تصمیم زیر را داد:

```python
{"allow": True, "mode": "core_conversation", ...}
```

مرکز فقط این seam را صدا می‌زند:

```python
from owner_console.telegram_adapter import handle_message, handle_callback
r = handle_message(text, surface_decision=decision)
```

اگر `handled=True`، caller فقط reply را از transport موجود ارسال می‌کند. adapter مالک، chat،
token یا surface را دوباره حدس نمی‌زند.

## تعریف Done

این بسته زمانی نتیجه انسانی می‌دهد که:

1. تست‌های خودش سبز شوند.
2. mutationهای handoff قرمز شوند.
3. یک handler در Outer DM وصل شود.
4. tg-center ری‌استارت شود.
5. ۱۲ سؤال Acceptance Runbook پاسخ درست بگیرند.
6. delivery receipt واقعی برای پاسخ‌ها ثبت شود.

تا آن زمان وضعیت درست `IMPLEMENTED_NOT_WIRED` است.
