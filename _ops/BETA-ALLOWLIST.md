# BETA-ALLOWLIST — کاربران مجاز برای بتا

> تاریخ: ۲۰۲۶-۰۸-۱۱ · بدون PII خام — فقط شناسه‌های hash

## مکانیزم allowlist

دسترسی به MiniApp از طریق `validate_init_data()` کنترل می‌شود (`miniapp_gateway.py:188`):
- فقط `user.id == TELEGRAM_OWNER_CHAT_ID` مجاز است
- HMAC با `TG_CENTER_BOT_TOKEN` بررسی می‌شود
- age ≤ ۳۰۰ ثانیه (ضد replay)

برای بتا، allowlist باید گسترش یابد. دو روش:

### روش ۱: لیست chat_id در env

```cmd
set OCTOPUS_MINIAPP_BETA_ALLOWLIST=chatid1,chatid2,chatid3
```

(نیاز به تغییر کد در `validate_init_data` — propose-only)

### روش ۲: allowlist هش‌شده

برای حریم خصوصی، chat_id‌ها hash می‌شوند:

```python
import hashlib
allowed_hashes = {
    hashlib.sha256(str(chat_id).encode()).hexdigest()[:16]
    for chat_id in [111111, 222222, 333333]
}
```

## کاربران بتای فعلی

| نقش | شناسهٔ hash | وضعیت |
|---|---|---|
| مالک | `sha256(owner_chat_id)[:16]` | ✅ فعال |
| معتمد ۱ | (اضافه کن) | pending |
| معتمد ۲ | (اضافه کن) | pending |

## قواعد بتا

۱. پیش‌فرض deny — هیچ کاربری بدون allowlist دسترسی ندارد
۲. هر کاربر بتا rate-limited است: ۶ درخواست در ۳۰ ثانیه
۳. کار خطرناک = کارت تأیید (نه اجرای خودکار)
۴. هزینهٔ مدل محدود به سقفِ `budgets.yaml`
5. TI collab_security باید سبز بماند
