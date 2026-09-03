# ثبت رضایت انتشار سبا — فقط مالک، روی برد

`consent_confirmed` بولین کافی نیست. `ConsentStore.record_release`
هش ۶۴کاراکتری، `document_ref` غیرخالی، scope معتبر، و `add_subject`
قبلی را اجباری می‌کند.

PDF را در Git نگذار. `OFN_ONLYFANS_HTTP_ARM` تا ردیف release وجود
ندارد unset بماند. مجموعه را از ابتدا `general` بساز؛
`advisor_gate` هیچ پارامتری برای restricted=yes ندارد.

```bash
# روی برد، بعد از امضا و اسکن
sha256sum ~/docs/saba-release-20260902.pdf
# خروجی ۶۴ کاراکتر را در دستور زیر بگذار — ایجنت مقدار را نمی‌بیند
```

```bash
python3 - <<'PY'
import time
from ofn.adapters.consent_store import ConsentStore

# مسیر واقعی دیتابیس رضایت روی برد، نه یک حدس
s = ConsentStore("<OFN_CONSENT_DB path>")
now = int(time.time())
try:
    s.add_subject("studio", "saba", "Saba", now_epoch_s=now)
except Exception as exc:
    # شناسه تکراری یعنی شخص از قبل هست — ادامه بده
    print(type(exc).__name__)

s.record_release(
    "saba-release-20260902",
    "saba",
    scope="telegram_channel bluesky",
    signed_at=int(time.mktime((2026, 9, 2, 0, 0, 0, 0, 0, 0))),
    document_ref="docs/consent/saba-release-20260902.pdf",
    document_sha256="<64 hex of the signed PDF>",
    recorded_by="owner",
    expires_at=int(time.mktime((2027, 9, 2, 0, 0, 0, 0, 0, 0))),
)
print("recorded", s.document_digest("saba-release-20260902"))
s.close()
PY
```
