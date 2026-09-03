---
tags: [ofn, ziman, architecture, harvester, W7, tender]
date: 2026-09-03
status: PROPOSED — pending owner GO on target URL
FILES_I_MERGED: none
---

# ZIMAN BROWSER HARVESTER — Architecture Doc

## هدف

board138 (همان board کسب‌وکار) با Chromium headless صید مناقصه‌ها را مستقیماً از سایت هدف می‌خواند
(خواندنی-فقط) و در پایگاه داده محلی ذخیره می‌کند.

## عبورگاههای امنیتی سه‌لایه

```
لایه ۱ — gate:    owner_approval=True + OFN_WIRE_HARVEST=1
لایه ۲ — ask-first: آدرس URL را به مالک نشان بده، منتظر باش
لایه ۳ — read-only: هیچ POST، هیچ login، هیچ فرم
```

## جریان داده

```
board138 Chromium → سایت هدف (خواندنی-فقط)
    ↓
 TenderRow[] (در RAM)
    ↓
 painting.sqlite → ziman_tender_leads (INSERT OR IGNORE)
    ↓
 state/legs/ziman-tender-harvest-claim.json → شاهد بیرونی (#130)
    ↓
 مالک Cockpit V2 در panel.master-painting.com می‌بیند
```

## محدودیت‌ها (fail-closed)

- حداکثر `MAX_ROWS = 50` در هر اجرا
- Chromium: `--single-process` — 4 GB RAM حساس
- خطای stub selector تا مالک URL + DOM shape را تأیید کند
- خطای exception → `HARVEST_FAILED` log، هیچ نیمه‌نویسته‌ای commit نمی‌شود

## نصب بر board138 (Claude Code — ۳ قدم)

```bash
# قدم ۱: نصب وابستگی‌ها
sudo apt-get install -y chromium-browser chromium-chromedriver python3-selenium

# قدم ۲: از مالک بپرس
echo "آدرس سایتی که باید ازش صید کنیم چیست؟"
# منتظر بمان تا مالک جواب دهد

# قدم ۳: پس از تأیید مالک
export OFN_WIRE_HARVEST=1
python3 -c "
from ofn.agents.ziman_tender_harvest import run
result = run(owner_approval=True, target_url='<URL تأییدشده>')
print(result)
"
```

## تست‌ها (CI سبز بدون browser)

```bash
cd ~/ofn && python3 -m pytest tests/test_ziman_tender_harvest.py -v
```

## باز مانده — نیاز به تأیید مالک

1. **URL:** مالک بگوید کدام سایت منبع ۳۷تایی است (buy.nsw.gov.au؟ دیگری؟)
2. **DOM shape:** پس از باز کردن سایت، selector CSS را تأیید کن
3. **OFN_WIRE_HARVEST=1:** فقط روی node.env برد board138 بزن (نه اینجا)

`FILES_I_MERGED = none`
