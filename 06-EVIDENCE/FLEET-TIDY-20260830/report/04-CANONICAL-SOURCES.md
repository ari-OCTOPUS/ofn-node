# 04 — منبع معتبر هر نود + دستور دقیق checkout

| نود | منبع معتبر کد | SHA کانونیکال | دستور |
|---|---|---|---|
| ۱۳۸ | گیت‌هاب `main` (== `backup/board138-20260830`) | `c1969bce5384f3371b916470299c991627c3d63c` | `git clone https://github.com/ari-OCTOPUS/ofn-node && cd ofn-node && git checkout main` |
| ۱۸۰ | `backup/board180-20260830` | `28209effa84af68a85ab60329c77dca81c6cea00` | `git clone https://github.com/ari-OCTOPUS/ofn-node && git checkout backup/board180-20260830` (ریشهٔ مشترک با main دارد؛ والد `76db516`) |
| ۱۸۲ | `backup/board182-20260830` | `294d51c1e01d999f55511d6b3bb038fd41ce9918` | همان clone + checkout (⚠️ تاریخچهٔ مستقل/orphan — با main پدری ندارد، عمداً) |
| لپ‌تاپ | F:\ofn-node (clone محلی، الان روی main@c1969bc) | c1969bce | `git -C F:\ofn-node pull --ff-only` |

هشدارها:
- روی برد ۱۳۸، شاخهٔ `main` **محلیِ** برد قدیمی است (2533aa3) و ملاک نیست؛ ملاک گیت‌هاب است.
- `work/truth-record-20260830@9bc05ab` = snapshot + دو سند حقیقت (CURRENT-TRUTH و PR-SPEC)؛ یک خط اصلاح باز دارد (C-055 در vault).
- هیچ شاخهٔ `backup/*` قابل بازنویسی نیست.
