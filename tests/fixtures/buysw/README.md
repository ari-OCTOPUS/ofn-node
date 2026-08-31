# buy.nsw eTendering — Test Fixtures

## داریم
- `schema_example.json` — نمونهٔ رسمی از GitHub NSW-eTendering-API (template، نه داده واقعی)
- `synthetic_tenders.json` — تندرهای ساختگی برای تست mapping و ساختار

## نداریم (blocker: API key)
- `golden_response.json` — پاسخ واقعی API — تا رسیدن API key موجود نیست

## قانون (از README اصلی fixtures)
> هر چیزی که ورودی تست خودش را تولید کند، دارد خودش را تأیید می‌کند.

تست‌های mapping با schema_example سبز هستند.
تست‌های filter تا رسیدن golden_response با پیام صریح skip می‌شوند.
