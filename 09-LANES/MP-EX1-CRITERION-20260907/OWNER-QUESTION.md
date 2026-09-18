---
type: owner-decision
status: answered_in_chat
requires: none_for_ex1_layers
resolution: three_layer_register_not_abcd
kind: owner_chat_answer
may_authorize: false
updated: 2026-09-07
---

# جواب ثبت شد — منوی A/B/C/D انتخاب نشد

متن عین: `OWNER-ANSWER.md`. سه لایه: `THREE-RESULTS.json`. EX1 v3.0 = NOT_PASSED. EX3 شروع نشد.

منوی زیر همان سؤال اولیه است؛ بایگانی می‌ماند، تکرار نمی‌شود.

# یک سؤال — معیار EX1 برای دو رکورد تاریخی (بایگانی سؤال)

برای seqهای **۱۹۴۲۹۸** و **۱۹۴۳۲۹** فیلدهای provenance داخل خود رکورد غایب‌اند و بازنویسی تاریخ ممنوع است. خود v3 دو حکم متعارض دارد: §0 می‌گوید `owner_decision` بنویس و ادامه بده؛ EX-1 `on_fail` می‌گوید کل lane بایستد.

کدام را تصویب می‌کنی؟

1. **A — توقف سخت.** expect اصلی می‌ماند. EX3 شروع نشود.
2. **B — شکاف معیار.** EX1-H = فقط مجموعهٔ قابل‌اثبات همین دو رکورد (`ORIGINAL_EXPECT_NOT_MET`). EX1-F = provenance اجباری روی هر تصمیم جدید. EX3 فقط بعد از این تصویب و فقط روی همان knowable set، بدون جعل زمان/تبار.
3. **C — waiver.** فیلدهای رسید خواننده و seq-monotonic جای expect اصلی بنشینند. برچسب باید `WAIVER` باشد، نه `PASS`.
4. **D — جفت baseline تازه.** EX1 به دو رکورد **جدید** که همان فیلدهای اجباری را دارند وصل شود؛ ۱۹۴۲۹۸/۱۹۴۳۲۹ فقط شاهد جزئی تاریخی بمانند.

پیش‌نویس موازی در `07-HANDOFF/EX1-CRITERION-OWNER-QUESTION-2026-09-07.md` گزینهٔ سوم را «new baseline pair» نامیده بود. آن معنی اینجا **D** است، نه C. دو برچسب را یکی نکن.

پیشنهاد مشاور: **B**. این متن حکم نیست. جواب خالی = EX3 شروع نمی‌شود.
