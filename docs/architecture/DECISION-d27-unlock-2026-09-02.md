# DecisionRecord — D-27 آزادسازی مجوز، نه سقف

**تاریخ: ۲۰۲۶-۰۹-۰۲ · حکم مالک + ایجنت ارشد · اجرا با سقف و ترمز**

## منبع

فایل `D-27-UNLOCK-DIRECTIVE.md`. این حکم فقط فیلدهای مجوز D-26 را عوض
می‌کند. شکاف بدن کانونی، سه معنای «واقعی»، و
`partner_voices_independently_observed = false` سر جایشان می‌مانند.

```yaml
speaker: owner
co_owner: senior-agent
implementation_authorized: true
merge_authorized: true
deploy_authorized: true
wire_authorized: true
external_effect_authorized: true
board_access_authorized: true
money_authorized: true
auto_advance_waves: true
parallel_execution: true
propose_only_mode: false
owner_attests_all_signed: true
partner_voices_independently_observed: false
```

## سقف

```text
daily_send_cap: 25
daily_spend_cap_aud: 50
per_board_budget_default: 0
kill_switch: OFN_EXTRA_CLOSED_GATES
rollback_window_hours: 24
```

آزاد = مجاز + سقف‌دار + قابل‌بازگشت. خطا یک مسیر را یک پله عقب می‌برد،
نه هر پنج مسیر را.

## چهار چیزی که با امضا true نمی‌شود

1. مشاهدهٔ مستقل صدای ملیحه / عباس / سبا
2. رکورد رضایت انتشار سبا (flag کافی نیست)
3. rotate واقعی رازها — `OFN_KEEP_GATES_OPEN=1` بدون rotate فقط هشدار را خفه می‌کند
4. قوانین Shopify / Telegram / درگاه پرداخت

## کلیدهای واقعی این مخزن

`_flag()` فقط رشتهٔ `"1"` را روشن می‌گیرد. این حکم پیش‌فرض
`OFN_WIRE_OUTBOUND` و `OFN_KEEP_GATES_OPEN` را در `ofn/config.py`
عوض نمی‌کند. سهمیهٔ مالک از قبل `7000` است؛ نثر دستورالعمل که پیش‌فرض را
صفر گفته بود با کد نمی‌خواند.

`GATE_OPEN_UNTIL_UTC = 2026-08-17` منقضی است. `secret_rotation` و
`partner_precondition` تا rotate واقعی بسته می‌مانند.

## لبه

`board_events` همان قرارداد لبه است. برد فقط proposal می‌دهد. نوع
`MESSAGE_SENT` / `REVENUE_RECORDED` / `BOOKING_CONFIRMED` روی این
قرارداد وجود ندارد. خانوادهٔ envelope دوم روی ofn-node ساخته نمی‌شود.

## معیار هفته

یک رسید پرداخت واقعی روی `PAINT-L5-001`. این پرونده آن رسید را جعل نمی‌کند.

## merge به main

PR #65 از Draft خارج شد و CI سبز است. push مستقیم به `main` از این
vantage رد شد: ریویو اجباری + ممنوعیت merge-commit. ادغام squashed را
انسان با write access می‌زند.
