# 🌸 ایجنتِ مارکتینگِ زیمان (ziman-agent)

ورکرِ اجراشدنیِ پروژهٔ زیمان که **مغزِ کنترل** روشن/خاموش/تستش می‌کند. کارَش:
تولیدِ **پیش‌نویسِ (draft)** محتوای مارکتینگ برای کسب‌وکارِ هدایای دست‌سازِ سیدنی —
**همیشه زیرِ سقفِ ظرفیت (قیدِ D4)** و **بدونِ هیچ انتشار/خرجِ خودکار**.

## اصولِ ایمنی (هم‌راستا با منشورِ زیمان)
- `autonomy: read-only` — فقط فایلِ draft محلی در `drafts/` می‌نویسد. نه پست می‌کند، نه خرج.
- **گاردِ D4:** هر هدفِ کمپینی بالاتر از سقفِ ظرفیت **رد** می‌شود، با دلیل (`ziman/capacity.py`).
- انتشارِ هر draft فقط با **تأییدِ انسانی**.

## حالت‌های اجرا
```
python worker.py              # حالتِ زنده (loop): مغزِ کنترل این را «start» می‌کند
python worker.py --once       # یک draft بساز و خارج شو
python worker.py --selftest   # خودآزمایی (مغزِ کنترل این را «test» می‌کند)
python worker.py --status     # وضعیتِ کوتاه (JSON)
python worker.py --campaign 100   # امتحانِ گاردِ D4 روی هدفِ ۱۰۰ واحد → رد می‌شود
```

## دو حالتِ تولید
- **offline (پیش‌فرض):** بدونِ کلیدِ API، یک draftِ قالبیِ امن می‌سازد — برای تست و راه‌اندازیِ اول.
- **live (Claude):** اگر `ANTHROPIC_API_KEY` در محیط باشد (مغزِ کنترل از KeePassXC تزریق می‌کند)،
  با Claude یک کپشنِ واقعیِ فارسی می‌سازد. مدل در `ziman.yaml` قابلِ تغییر است.
  اگر تماس ناموفق شود، **امن** به offline برمی‌گردد.

## ساختار
```
ziman-agent/
├─ worker.py            # نقطهٔ ورود + حالت‌ها + loop
├─ ziman.yaml           # پیکربندی (تنها منبعِ اعداد/قواعد)
├─ ziman/
│  ├─ config.py         # بارگذاری و اعتبارسنجیِ پیکربندی
│  ├─ capacity.py       # گاردِ D4 (تابعِ خالص، تست‌پذیر)
│  ├─ content.py        # تولیدِ draft (offline + Claude)
│  └─ brief.py          # خواندنِ read-only از vault
└─ drafts/              # خروجی‌ها (در گیت نادیده گرفته می‌شوند)
```

## Phase 2 — Product & Inventory Intelligence (local drafts only)

`phase2_cli.py` فقط آرتیفکت‌های محلیِ غیرکانونیکال می‌سازد؛ هیچ پیام، پست، پرداخت، قیمت عمومی یا اتصال Telegram را فعال نمی‌کند.

```bat
:: تست‌های بدون شبکه
python phase2_cli.py --selftest
python -m pytest tests\test_product.py -q

:: کارت محصولِ draft؛ خانواده و عنوان باید از شمارش/طبقه‌بندی مالک بیاید
python phase2_cli.py --product-card C3 "Shadow box — title pending" --qty 1

:: snapshot شمارش؛ ظرفیت عمداً null می‌ماند مگر مالک صریحاً بازاعتبارسنجی کند
python phase2_cli.py --inventory-snapshot physical_count --C1 0 --C2 0 --C3 0 --C4 0

:: preview پاسخ Telegram؛ فقط format می‌کند، ارسال نمی‌کند
python phase2_cli.py --telegram-dry /ziman_status
```

- `--price` عمداً رد می‌شود: قیمت عمومی فقط بعد از گیت جداگانهٔ تأیید مالک وارد می‌شود.
- `--owner-revalidated --capacity N` فقط زمانی استفاده شود که مالک سقف را بازاعتبارسنجی کرده باشد.
- `--photo-index` فقط روی یک پوشهٔ صریح اجرا می‌شود، اصلِ عکس را جابه‌جا/تغییر نمی‌دهد و هیچ Product ID نمی‌سازد.

## پیش‌نیاز
`PyYAML` (خودِ مغزِ کنترل هم لازمش دارد). برای حالتِ live هیچ کتابخانهٔ اضافه‌ای لازم نیست (urllib استاندارد).
