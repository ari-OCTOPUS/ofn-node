---
type: prompt
project: "[[03 - Projects/Accounting/PROJECT]]"
status: ready
created: 2026-07-17
updated: 2026-07-29
created_by: deep-scan agent (ZCode)
tags: [accounting, pocketsmith, execution-prompt, resync, self-run]
aliases: ["پرامپت اجرایی سینک دوباره PocketSmith", "Resync Execution Prompt"]
# purpose: "پرامپت اجراییِ گام‌به‌گام برای اجرای بعدی: به‌روزرسانی PocketSmith + فعال‌سازی امنِ pipeline. خودِ ایجنت این را اجرا می‌کند."
# audience: "the next ZCode session (self)"
---

# ▶️ پرامپت اجرایی — به‌روزرسانی PocketSmith + فعال‌سازی امنِ Accounting

> **تو (= ایجنت بعدی):** این پرامپت را اجرا کن. پیش‌نیاز: `DEEP-SCAN-2026-07-17-POCKETSMITH-STATUS.md` را اول بخوان.
> **هدف:** داده‌های PocketSmith را تا امروز sync کن، بدون شکستنِ دکترینِ propose-only و بدون روشن‌کردنِ فلگ‌های سطحِ HIGH بدون رأیِ مالک.

---

## ۰. قوانین طلایی (نقض نکن — از MEGAPROMPT + charter)

1. **پول = سنتِ صحیح (integer cents)** — هیچ‌گاه float. (موتورِ `money.py` از قبل اجرا می‌کند.)
2. **Propose-only.** هیچ تراکنش/entry بدونِ تأییدِ انسان به `posted` نمی‌رود. صفر حرکت خودکار پول.
3. **کلیدها فقط در `F:/backup/.env` (gitignored).** هرگز در کد/چت/commit.
4. **read-only پیش‌فرض.** writeback پشتِ فلگ و پشتِ رأی.
5. **هرگز حذف نکن — فقط انتقال** به `_Archive`.
6. **تست‌ها قبل و بعد سبز بمانند.**
7. **فلگ‌های سطح HIGH (= اثرِ live، write به دنیای بیرون) را خودت روشن نکن** — کارت پیشنهاد + diff بده، منتظر رأی بمان. فقط فلگ‌های خواندنی/درون‌پوشه‌ای را فعال کن.

---

## ۱. مرتب‌سازی اولیه (قبل از هر کاری) — ردهٔ 🟢 آزاد

### ۱.۱ راستی‌آزمایی محیط
```bash
cd "F:/backup"
# کلید موجود است؟
grep -q "POCKETSMITH_API_KEY" .env && echo "KEY present" || echo "KEY MISSING — stop"
# پایتون + مسیر _ops روی sys.path
python -c "import sys; sys.path.insert(0,'_ops'); from legs import pocketsmith_api; print('import OK')"
```

### ۱.۲ backup state فعلی (هرگز حذف، فقط snapshot)
```bash
cd "F:/backup/03 - Projects/Accounting"
mkdir -p _Archive/state-2026-07-17
cp personal/txn-store.json _Archive/state-2026-07-17/txn-store-pre-resync.json
cp personal/ledger.json     _Archive/state-2026-07-17/ledger-pre-resync.json 2>/dev/null || true
```

### ۱.۳ اجرای تست‌های baseline (باید سبز بمانند)
```bash
cd "F:/backup" && python _ops/tests/run_all.py 2>&1 | tail -20
# یا حداقل:
python -m pytest _ops/tests/test_pocketsmith_api.py _ops/tests/test_ps_writeback.py _ops/tests/test_journal_bridge.py -q
```
اگر شکست خورد → **متوقف شو**، گزارش بده، دست نزن.

---

## ۲. مأموریت اصلی: sync دوباره تا امروز — ردهٔ 🟢 آزاد (read-only)

> این کار **read-only** است: فقط GET از PocketSmith و بازنویسیِ `txn-store.json` (gitignored). هیچ write به PocketSmith نیست. فلگِ `OCTOPUS_WIRE_POCKETSMITH` را **فقط برای طولِ این فراخوانی** در پراسس فعال کن (نه در `.env` دائمی) — مگر اینکه مالک `.env` دائمی را تأیید کرده باشد.

### ۲.۱ تعیین بازهٔ sync
- قدیمی‌ترین تراکنش در store: `2024-07-28`
- جدیدترین: `2026-04-20` (stale)
- **بازهٔ sync:** `2024-07-01` تا `امروز (2026-07-17)` — کامل، تا هیچ شکاف‌ای نماند.

### ۲.۲ اجرای sync (روشِ امن، flag در پراسس)
```python
# F:/backup/_ops/tmp_resync.py  (موقت، بعداً پاک کن)
import os, sys, json
sys.path.insert(0, r"F:/backup/_ops")
# فقط برای این پراسس روشن کن — هرگز os.environ را در .env ننویس بدون رأی
os.environ["OCTOPUS_WIRE_POCKETSMITH"] = "1"
from legs import pocketsmith_api, accountant, txn_store

# ۱) fetch + map + merge از API
print("syncing PocketSmith 2024-07-01 → today ...")
result = pocketsmith_api.sync("2024-07-01", "2026-07-17")
print("sync result:", result)
```
**اجرای مستقیم در ترمینال به‌جای اسکریپت موقت، اگر ترجیح داری:** کدِ `accountant.build_network()` همین کار را می‌کند. اما `sync()` سبک‌تر است.

⚠️ **نکتهٔ مهم dedup:** تابعِ `pocketsmith_api.sync()` تراکنش‌های API را با `id` (PS numeric) dedup می‌کند و با ردیف‌های موجود merge می‌کند. تراکنش‌های CSV دست‌نخورده باقی می‌مانند. اگر بعد از sync، شمارش تراکنش‌ها به‌طور غیرعادی بالا رفت (مثلاً >۳۰٪ رشد)، **متوقف شو** — احتمالاً باگِ دو-هش باعث duplicate شده.

### ۲.۳ راستی‌آزماییِ بعد از sync
```python
import json
d = json.load(open(r"F:/backup/03 - Projects/Accounting/personal/txn-store.json", encoding="utf-8"))
txns = d["txns"]
from collections import Counter
print("count:", len(txns))
print("max date:", max(t.get("date","") for t in txns))   # باید ≈ امروز باشد
print("by source:", dict(Counter(t["source"] for t in txns)))
# بررسی duplicate احتمالی: id یکتا؟
ids = [t.get("id") for t in txns]
print("unique ids:", len(set(ids)), "of", len(ids))       # باید برابر باشند
```
**معیار قبولی:**
- `max date` ≥ `2026-07-10` (هفتهٔ گذشته).
- `unique ids == len(txns)` (صفر duplicate).
- تست‌های baseline هنوز سبز.

اگر خراب شد → restore از `_Archive/state-2026-07-17/txn-store-pre-resync.json`.

---

## ۳. گزارشِ تازه (اختیاری، 🟢 آزاد) — با دادهٔ به‌روز

اسکریپتِ تولیدِ گزارش را با دادهٔ جدید اجرا کن (همان که `personal/REPORT-2026-07-16.md` را ساخت):
```python
import sys; sys.path.insert(0, r"F:/backup/_ops")
from legs import accountant
card = accountant.run(persist=False)   # یا تابعِ گزارشِ مخصوص
print(json.dumps(card, ensure_ascii=False, indent=2))
```
خروجی را در `personal/REPORT-2026-07-17.md` بنویس (gitignored). **هرگز** مبلغ/نامِ مشتری را به هیچ LLM ابری نفرست.

---

## ۴. کارت‌های پیشنهاد برای مالک (ردهٔ 🔴 مهم — فقط بنویس، اجرا نکن)

این موارد را به‌صورت **پیشنهاد + دیف + اثر** به مالک بده، **بدونِ روشن‌کردنِ فلگ**:

### ۴.۱ کارت پیشنهاد: فعال‌سازیِ دائمیِ sync (فلگ در `.env`)
```
پیشنهاد: افزودن  OCTOPUS_WIRE_POCKETSMITH=1  به F:/backup/.env
اثر: sync خودکارِ روزانه از طریق acct_beat (اگر ACCT_BEAT_SYNC=1 هم باشد)
ریسک: read-only است؛ هیچ write به PocketSmith. فقط fetch.
تصمیم لازم: yes/no
```

### ۴.۲ کارت پیشنهاد: فعال‌سازیِ writeback برچسب‌ها
```
پیشنهاد: OCTOPUS_WIRE_PS_WRITEBACK=1  (بعلاوه OCTOPUS_WIRE_POCKETSMITH=1)
اثر: تأییدهای /review به‌صورت برچسبِ oct-مالک-* / oct-نوع-* روی همان تراکنش در PocketSmith نوشته می‌شوند.
مرز: فقط PUT labels به /transactions/{id}. هیچ تغییرِ مبلغ/تاریخ/پرداخت.
این اولین (و تنها) استثنای دکترینِ صفر-نوشتن است (RD-004، رأیِ قبلیِ مالک برای «پاکت‌اسمیتم سینک باشه»).
تصمیم لازم: yes/no
```

### ۴.۳ کارت پیشنهاد: شروعِ double-entry واقعی (ledger_core)
```
پیشنهاد: اجرای journal_bridge.rebuild() برای ساختِ صفِ پروپوزال از تراکنش‌های confirmed،
سپس مرورِ مالک و post به ledger_core.
پیش‌نیاز: تکمیلِ policy-profile.json (legal_name + ABN — مالک) و گسترشِ COA.
هیچ چیزی بدون /books approve منتشر نمی‌شود.
تصمیم لازم: آیا COA گستردهٔ MEGAPROMPT (۲۵ حساب، تفکیکِ پیمانکاران) پذیرفته است؟
```

---

## ۵. گام‌های عمیق‌تر (پشتِ رأی — برای جلسهٔ بعد)

اگر مالک گفت «حسابداریِ واقعی» (MEGAPROMPT)، این‌ها را **پشتِ worktree + flag-off + پیشنهاد** بساز:

| گام | کار | خروجیِ قابل تست |
|---|---|---|
| G1 | گسترشِ `ledger_core.DEFAULT_COA` به ۲۵ حساب (MEGAPROMPT §COA) از طریقِ `policy-profile.chart_of_accounts` | لیست لود می‌شود، تابعِ `coa()` override را مرج می‌دهد |
| G2 | رفعِ باگِ دو-هش: یکسان‌کردنِ `txn_store._hash` و `accountant._content_hash` (یا مهاجرت کامل به external_ref) | تست: همان تراکنش از API و CSV → یک id |
| G3 | مدلِ REA: جداسازیِ `account_holder` از `beneficial_owner` در schema | migration + تست |
| G4 | سیم‌کردنِ `recon.py` به‌صورتِ ماهانه (bank ↔ app cross-check) | گزارشِ recon |
| G5 | فعال‌سازیِ Xero (ریل A): خرید + کلیدها + `OCTOPUS_WIRE_COMPANY_BOOKS=1` — **کاملاً مالک** | کارتِ /finance بخشِ شرکت |

---

## ۶. به‌روزرسانیِ state (پایانِ جلسه) — 🟢 آزاد

- [ ] `PROJECT.md` (Accounting) → Active Context: «sync دوباره تا ۲۰۲۶-۰۷-۱۷ انجام شد؛ N تراکنش جدید؛ M نیازبه‌مرور».
- [ ] `VERDICT_QUEUE.md` → وضعیتِ ACC-V2/V4 را به «partial — رأیِ مالک ۲۰۲۶-۰۷-۱۶ Pty Ltd+GST در policy-profile» به‌روز کن.
- [ ] `personal/REPORT-2026-07-17.md` (gitignored).
- [ ] اگر >۵ فایل تغییر کرد → `git commit -- <files>` با pathspec (هرگز بدون pathspec — tree dirty از _ops).
- [ ] تست‌های baseline دوباره سبز.

---

## ۷. ضدالگوها (این‌ها را نکن)

1. **فلگِ HIGH را خودت روشن نکن** (writeback، write به خارج). فقط prepos.
2. **`OCTOPUS_WIRE_POCKETSMITH` را در `.env` دائمی ننویس بدون رأی** — برای sync یک‌باره در پراسس OK است.
3. **به گزارشِ stale (۲۰۲۶-۰۴-۲۰) اعتماد نکن** — اول sync.
4. **double-entry را از صفر بازسازی نکن** — `ledger_core.py` از قبل کامل است.
5. **commit بدون pathspec ممنوع** — ۳۰۵ فایل dirty از _ops را جارو می‌کند.
6. **هیچ مبلغ/نامِ مشتری به LLM ابری نرود** — `txn_categorize.scrub_pii` محترم.
7. **حذف ممنوع** — snapshot به `_Archive`.

---

## ۸. خطِ شروع (چک‌لیستِ سریع)

```
[ ] DEEP-SCAN را خواندی
[ ] .env → POCKETSMITH_API_KEY موجود
[ ] backup state فعلی به _Archive/state-2026-07-17/
[ ] تست‌های baseline سبز
[ ] sync 2024-07-01 → 2026-07-17 (flag در پراسس)
[ ] راستی‌آزمایی: max date + unique ids
[ ] گزارش تازه در personal/REPORT-2026-07-17.md
[ ] کارت‌های پیشنهاد (۳ تا) به مالک
[ ] PROJECT.md + VERDICT_QUEUE به‌روز
[ ] commit با pathspec
```

> **یک‌خطی:** داده‌ها ۳ ماه stale‌اند و فلگ‌ها خاموش‌اند. یک sync خواندنیِ امن (flag در پراسس، نه دائمی) داده‌ها را تا امروز می‌آورد؛ بقیه کارها پشتِ رأیِ مالک.
