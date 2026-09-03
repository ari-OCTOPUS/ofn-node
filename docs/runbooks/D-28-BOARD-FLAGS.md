# D-28 — flag ها روی برد، نه در پیش‌فرض مخزن

ایجنت راز را نمی‌خواند. این دستور را مالک روی Orange Pi می‌زند.

```bash
# اختیاری بعد از ثبت DECISION-open-gates و انقضای 2026-09-16
export OFN_KEEP_GATES_OPEN=1
export OFN_WIRE_OUTBOUND=1
export OFN_COMMERCE_ROUTES=1
export OFN_SHOPIFY_WIRE=1   # یک محصول، بعد مقیاس

# عمداً نزده شود تا ردیف record_release سبا وجود داشته باشد:
# export OFN_ONLYFANS_HTTP_ARM=1

# سهمیهٔ مالک در کد از قبل 7000 است. اگر env صفر است:
export OFN_CONTROL_QUOTA_TOKENS=7000
```

چرخش حداقل دو راز — مقدار را به ایجنت نشان نده:

```bash
nano ~/.config/ofn/secrets.env     # OFN_SESSION_SECRET, OFN_BOT_TOKEN_OWNER
chmod 600 ~/.config/ofn/secrets.env
sudo systemctl restart ofn
python3 -m ofn.preflight | grep boot
```

اگر بدون چرخش `OFN_KEEP_GATES_OPEN=1` زدی، رسید باید
`risk_accepted_unrotated` بگوید. این میزبان آن را همین‌طور ثبت کرد.
