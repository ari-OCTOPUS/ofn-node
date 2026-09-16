---
type: report
status: draft
created_by: agent (Cowork session)
project: "[[03 - Projects/Accounting/PROJECT]]"
tags: [accounting, subledger, associates, div7a, draft]
created: 2026-07-12
updated: 2026-07-12
---

# Sub-ledger پیش‌نویس Associates — پنجرهٔ AUG→NOV 2024

> ⚠️ **[Unverified — accountant to confirm]** — همهٔ دسته‌بندی‌ها و برداشت‌های مالیاتی draft هستند. هیچ ثبت نهایی انجام نشده.
> 🔒 PII (نام/مبلغ) فقط داخل همین پوشه؛ طبق verdict مالک 2026-07-12 استخراج شد.
> 📎 منبع: ۶ فایل `data/حساب کتاب/*.xlsx` — ۵ فایل «PS Export» (خروجی فیلترشدهٔ ANZ، ۱۶۰ تراکنش) + ۱ شیت خلاصهٔ دستی.
> ⏳ **این snapshot تاریخی FY2024-25 است (AUG–NOV 2024)** — دفاتر جاری FY2025-26 نیست.

## ۱) تطبیق شیت خلاصهٔ دستی ↔ تراکنش‌های PS Export

شیت `حساب و کتاب.xlsx` ادعا می‌کند: ورودی AUG→NOV = **86,075** و تخصیص‌ها + مانده = 73,137 + 12,938. `[FACT: 73,137+12,938=86,075 ✓ — حساب داخلی شیت می‌خواند]`

| شخص/دسته | شیت دستی | جمع PS Export (کل) | جمع در پنجرهٔ AUG–NOV | Δ نسبت به شیت | توضیح |
|---|---:|---:|---:|---:|---|
| Armin (حقوق) | 11,020 | 11,020.00 (6 تراکنش) | 11,020.00 (6 تراکنش) | +0.00 | تطابق دقیق |
| Rent (اجاره) | 14,940 | 17,138.00 (13 تراکنش) | 14,940.00 (11 تراکنش) | +0.00 | دو ردیف جولای (−710 و −1,488) خارج از پنجره‌اند؛ داخل پنجره دقیقاً برابر |
| Behzad (حقوق) | 10,250 | 10,250.00 (20 تراکنش) | 10,250.00 (20 تراکنش) | +0.00 | تطابق دقیق |
| Maliheh (خردی‌ها انتقال‌ها اسنپ‌ها و …) | 8,850 | 8,856.94 (72 تراکنش) | 8,856.94 (72 تراکنش) | +6.94 | اختلاف 6.94 — احتمالاً رُندکردن دستی `[EST]` |
| Sume asadi (حواله‌های ایران و ارسال‌ها و خریدهای بیزنس از کارت و متفرقه) | 28,077 | 28,077.99 (49 تراکنش) | 28,077.99 (49 تراکنش) | +0.99 | اختلاف 0.99 — رُندکردن `[EST]` |
| **جمع** | **73,137** | **75,342.93** | **73,144.93** | **+7.93** | |

`[FACT]` نتیجهٔ تطبیق: شیت دستی با دقت ~۸ دلار (رُندکردن) با تراکنش‌های بانکی سازگار است؛ **ورودی 86,075 از این فایل‌ها قابل‌راستی‌آزمایی نیست** (این ۵ فایل فقط سمت هزینه را پوشش می‌دهند) `[OPEN — نیازمند export کامل درآمدها]`.

## ۲) جزئیات هر شخص/دسته

### Armin — 11,020.00 AUD / 6 تراکنش (2024-09-30 تا 2024-11-26)

| ماه | جمع (AUD) |  | حساب مبدأ | جمع (AUD) |
|---|---:|---|---|---:|
| 2024-09 | 2,220.00 |  | ANZ Plus | 10,620.00 |
| 2024-10 | 5,500.00 |  | COMPLETE FREEDOM | 400.00 |
| 2024-11 | 3,300.00 |  |  |  |

| تاریخ | شرح (Merchant) | مبلغ | حساب | Bank ID |
|---|---|---:|---|---|
| 2024-09-30 | SEP | -2,220.00 | ANZ Plus | 1130806096 |
| 2024-10-31 | OCT | -2,800.00 | ANZ Plus | 1130805184 |
| 2024-10-31 | AUG | -2,700.00 | ANZ Plus | 1130805007 |
| 2024-11-26 | اضافه کاری یک روز کامل خودت در افیس | -300.00 | ANZ Plus | 1130808067 |
| 2024-11-26 | NOV | -2,600.00 | ANZ Plus | 1130804605 |
| 2024-11-26 | کار کامل رضا | -400.00 | COMPLETE FREEDOM | 1130807374 |

### Rent — 17,138.00 AUD / 13 تراکنش (2024-07-28 تا 2024-11-18)

| ماه | جمع (AUD) |  | حساب مبدأ | جمع (AUD) |
|---|---:|---|---|---:|
| 2024-07 | 2,198.00 |  | COMPLETE FREEDOM | 17,138.00 |
| 2024-08 | 2,976.00 |  |  |  |
| 2024-09 | 4,524.00 |  |  |  |
| 2024-10 | 2,976.00 |  |  |  |
| 2024-11 | 4,464.00 |  |  |  |

| تاریخ | شرح (Merchant) | مبلغ | حساب | Bank ID |
|---|---|---:|---|---|
| 2024-07-28 | additional lease payment | -710.00 | COMPLETE FREEDOM | 1130354665 |
| 2024-07-31 | rocovered Rent | -1,488.00 | COMPLETE FREEDOM | 1130354668 |
| 2024-08-13 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130354671 |
| 2024-08-27 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130354674 |
| 2024-09-02 | water | -60.00 | COMPLETE FREEDOM | 1130354677 |
| 2024-09-10 | rocovered Rent | -1,488.00 | COMPLETE FREEDOM | 1130354680 |
| 2024-09-16 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130357059 |
| 2024-09-20 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130354683 |
| 2024-10-01 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130354686 |
| 2024-10-04 | recovered | -1,488.00 | COMPLETE FREEDOM | 1130354689 |
| 2024-11-01 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130355940 |
| 2024-11-15 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130355943 |
| 2024-11-18 | Rent | -1,488.00 | COMPLETE FREEDOM | 1130355937 |

### Behzad — 10,250.00 AUD / 20 تراکنش (2024-08-23 تا 2024-11-24)

| ماه | جمع (AUD) |  | حساب مبدأ | جمع (AUD) |
|---|---:|---|---|---:|
| 2024-08 | 1,350.00 |  | ANZ Plus | 9,250.00 |
| 2024-09 | 3,900.00 |  | Smart Access | 1,000.00 |
| 2024-10 | 2,000.00 |  |  |  |
| 2024-11 | 3,000.00 |  |  |  |

| تاریخ | شرح (Merchant) | مبلغ | حساب | Bank ID |
|---|---|---:|---|---|
| 2024-08-23 | Payment to Armin Mohebiafzal #131986 | -500.00 | ANZ Plus | 1120778158 |
| 2024-08-25 | Payment to Armin Mohebiafzal #348300 | -350.00 | ANZ Plus | 1120778185 |
| 2024-08-31 | Payment to Armin Mohebiafzal #579974 | -500.00 | ANZ Plus | 1120778362 |
| 2024-09-07 | Payment to Armin Mohebiafzal #134320 | -500.00 | ANZ Plus | 1120778503 |
| 2024-09-08 | Payment to Armin Mohebiafzal #115726 | -500.00 | ANZ Plus | 1120778542 |
| 2024-09-13 | Payment to Armin Mohebiafzal #069966 | -500.00 | ANZ Plus | 1120778665 |
| 2024-09-14 | Payment to Armin Mohebiafzal #729106 | -500.00 | ANZ Plus | 1120778797 |
| 2024-09-21 | Payment to Armin Mohebiafzal #373211 | -500.00 | ANZ Plus | 1120778905 |
| 2024-09-24 | Payment to Armin Mohebiafzal #133475 | -500.00 | ANZ Plus | 1120778968 |
| 2024-09-28 | Payment to Armin Mohebiafzal #605488 | -400.00 | ANZ Plus | 1120779064 |
| 2024-09-30 | Payment to Armin Mohebiafzal #835465 | -500.00 | ANZ Plus | 1120779094 |
| 2024-10-13 | Payment to Armin Mohebiafzal #783143 | -500.00 | ANZ Plus | 1120779322 |
| 2024-10-15 | Payment to Armin Mohebiafzal #719886 | -500.00 | ANZ Plus | 1120779442 |
| 2024-10-17 | Payment to Armin Mohebiafzal #424286 | -500.00 | ANZ Plus | 1120779457 |
| 2024-10-22 | Payment to Armin Mohebiafzal #987168 | -500.00 | ANZ Plus | 1120779634 |
| 2024-11-02 | Payment to Armin Mohebiafzal #297716 | -500.00 | ANZ Plus | 1120780054 |
| 2024-11-07 | Payment to Armin Mohebiafzal #527264 | -500.00 | ANZ Plus | 1120780201 |
| 2024-11-14 | Payment to Armin Mohebiafzal #832494 | -500.00 | ANZ Plus | 1120780453 |
| 2024-11-15 | Payment to Armin Mohebiafzal #996396 | -500.00 | ANZ Plus | 1120780504 |
| 2024-11-24 | behzad | -1,000.00 | Smart Access | 1130372182 |

### Maliheh — 8,856.94 AUD / 72 تراکنش (2024-08-10 تا 2024-11-23)

| ماه | جمع (AUD) |  | حساب مبدأ | جمع (AUD) |
|---|---:|---|---|---:|
| 2024-08 | 1,223.01 |  | ANZ Plus | 8,688.34 |
| 2024-09 | 2,946.87 |  | Smart Access | 168.60 |
| 2024-10 | 1,852.20 |  |  |  |
| 2024-11 | 2,834.86 |  |  |  |

| تاریخ | شرح (Merchant) | مبلغ | حساب | Bank ID |
|---|---|---:|---|---|
| 2024-08-10 | Payment to Colour Printers #623334 | -75.00 | ANZ Plus | 1120777918 |
| 2024-08-15 | Visa Debit purchase card 5673 bunnings group ltd hawthorn ea | -72.01 | ANZ Plus | 1120777993 |
| 2024-08-17 | Visa Debit purchase card 5673 apple.com/bill sydney | -14.99 | ANZ Plus | 1120778047 |
| 2024-08-21 | Visa Debit purchase card 5673 nobabyblisters charity www.nob | -10.86 | ANZ Plus | 1120778086 |
| 2024-08-25 | TerryWhite Chemmart - Visa Debit purchase card 5673 terry wh | -16.49 | ANZ Plus | 1120778215 |
| 2024-08-25 | Visa Debit purchase card 5673 apple.com/bill sydney | -22.99 | ANZ Plus | 1120778209 |
| 2024-08-25 | Payment to Maliheh Khalajijou #000408 | -1,000.00 | ANZ Plus | 1120778176 |
| 2024-08-30 | Visa Debit purchase card 5673 sq *lucaccino pymble | -10.67 | ANZ Plus | 1120778359 |
| 2024-09-03 | Visa Debit purchase card 5673 paypal *aldimobile ald 4029357 | -29.00 | ANZ Plus | 1120778410 |
| 2024-09-04 | Visa Debit purchase card 5673 coles 0702 stanhope gdns | -76.19 | ANZ Plus | 1120778455 |
| 2024-09-07 | Visa Debit purchase card 5673 uber *trip sydney | -29.19 | ANZ Plus | 1120778521 |
| 2024-09-08 | Visa Debit purchase card 5673 uber *trip sydney | -26.66 | ANZ Plus | 1120778551 |
| 2024-09-09 | Visa Debit purchase card 5673 rouse hill towncenter rouse hi | -37.35 | ANZ Plus | 1120778593 |
| 2024-09-09 | Visa Debit purchase card 5673 kmart 1380 rouse hill | -67.50 | ANZ Plus | 1120778584 |
| 2024-09-09 | Visa Debit purchase card 5673 sq *oliver brown rouse hi rous | -22.75 | ANZ Plus | 1120778581 |
| 2024-09-14 | Visa Debit purchase card 5673 big w/windsor rd & commer rous | -57.85 | ANZ Plus | 1120778788 |
| 2024-09-14 | Visa Debit purchase card 5673 big w/windsor rd & commer rous | -819.00 | ANZ Plus | 1120778779 |
| 2024-09-14 | Visa Debit purchase card 5673 nobabyblisters charity www.nob | -10.86 | ANZ Plus | 1120778728 |
| 2024-09-18 | Payment to Maliheh Khalajijou #979610 | -500.00 | ANZ Plus | 1120778857 |
| 2024-09-18 | Payment to Maliheh Khalajijou #675606 | -500.00 | ANZ Plus | 1120778848 |
| 2024-09-28 | Eftpos cleartowork\ | -20.52 | ANZ Plus | 1120779058 |
| 2024-09-29 | Payment to Maliheh Khalajijou #072892 | -700.00 | ANZ Plus | 1120779073 |
| 2024-09-30 | Payment to Armin Mohebiafzal #738378 | -50.00 | ANZ Plus | 1120779100 |
| 2024-10-04 | Visa Debit purchase card 5673 afterpay afterpay.com | -34.69 | ANZ Plus | 1120779154 |
| 2024-10-04 | PAYPAL *ALDIMOBILE ALDIMOSydney AU | -29.00 | Smart Access | 1120775437 |
| 2024-10-08 | Visa Debit purchase card 5673 paypal * bpaustra s092 1800073 | -15.00 | ANZ Plus | 1120779202 |
| 2024-10-08 | Visa Debit purchase card 5673 paypal * bpaustra s092 1800073 | -10.50 | ANZ Plus | 1120779199 |
| 2024-10-08 | Check Out 7 - Visa Debit purchase card 5673 2co.com hp inc.  | -12.99 | ANZ Plus | 1120779190 |
| 2024-10-09 | APPLE.COM/BILL SYDNEY NS AUS, Card xx4178, Value date: 09/10 | -16.99 | Smart Access | 1120775458 |
| 2024-10-10 | UBER *TRIP Sydney AU AUS, Card xx4178, Value date: 10/10/202 | -26.03 | Smart Access | 1120775467 |
| 2024-10-11 | Visa Debit purchase card 5673 woolworths/cnr epping & b mars | -22.06 | ANZ Plus | 1120779283 |
| 2024-10-12 | Visa Debit purchase card 5673 good value chemist blacktown | -9.99 | ANZ Plus | 1120779316 |
| 2024-10-12 | Visa Debit purchase card 5673 ls the shed cafe stanh stanhop | -28.64 | ANZ Plus | 1120779307 |
| 2024-10-13 | Visa Debit purchase card 5673 amazon marketplace AU sydney s | -65.01 | ANZ Plus | 1120779367 |
| 2024-10-13 | Visa Debit purchase card 5673 sushi shed stanhope stanhope g | -16.76 | ANZ Plus | 1120779346 |
| 2024-10-14 | Visa Debit purchase card 5673 apple.com/bill sydney | -4.49 | ANZ Plus | 1120779418 |
| 2024-10-14 | Visa Debit purchase card 5673 nobabyblisters charity www.nob | -10.86 | ANZ Plus | 1120779388 |
| 2024-10-16 | Visa Debit purchase card 5673 amazon marketplace AU sydney s | -112.50 | ANZ Plus | 1120779508 |
| 2024-10-17 | Visa Debit purchase card 5673 uber* trip sydney | -28.45 | ANZ Plus | 1120779553 |
| 2024-10-17 | Payment to Maliheh Khalajijou #318864 | -500.00 | ANZ Plus | 1120779541 |
| 2024-10-17 | Payment to Maliheh Khalajijou #300177 | -500.00 | ANZ Plus | 1120779523 |
| 2024-10-17 | APPLE.COM/BILL SYDNEY AU AUS, Card xx4178, Value date: 17/10 | -14.99 | Smart Access | 1120775500 |
| 2024-10-19 | WOOLWORTHS 1163 KIAMA NS AUS, Card xx4178, Value date: 19/10 | -22.60 | Smart Access | 1120775512 |
| 2024-10-22 | Visa Debit purchase card 5673 paypal *ostado b v 4029357733 | -18.63 | ANZ Plus | 1120779652 |
| 2024-10-23 | Visa Debit purchase card 5673 uber *trip sydney | -27.10 | ANZ Plus | 1120779757 |
| 2024-10-23 | Visa Debit purchase card 5673 chemist warehouse castle hill | -43.98 | ANZ Plus | 1120779748 |
| 2024-10-23 | Visa Debit purchase card 5673 mcdonalds castle twr2 castle h | -8.00 | ANZ Plus | 1120779742 |
| 2024-10-23 | Visa Debit purchase card 5673 sushi hub castle hil castle hi | -18.90 | ANZ Plus | 1120779727 |
| 2024-10-23 | Visa Debit purchase card 5673 carefirst pharmacy castle hill | -11.99 | ANZ Plus | 1120779712 |
| 2024-10-23 | Visa Debit purchase card 5673 uber* trip www.uber.coma | -31.70 | ANZ Plus | 1120779700 |
| 2024-10-23 | Visa Debit purchase card 5673 sp ray kazzi casula | -45.25 | ANZ Plus | 1120779691 |
| 2024-10-25 | Visa Debit purchase card 5673 uber *trip sydney | -36.64 | ANZ Plus | 1120779820 |
| 2024-10-25 | APPLE.COM/BILL SYDNEY NS AUS, Card xx4178, Value date: 25/10 | -29.99 | Smart Access | 1120775542 |
| 2024-10-31 | Visa Debit purchase card 5673 tk maxx castle hill castle hil | -3.13 | ANZ Plus | 1120780000 |
| 2024-10-31 | Visa Debit purchase card 5673 portmans castle hill | -44.93 | ANZ Plus | 1120779988 |
| 2024-10-31 | Visa Debit purchase card 5673 bellaccino espresso ba castle  | -23.65 | ANZ Plus | 1120779976 |
| 2024-10-31 | Visa Debit purchase card 5673 uber *trip sydney | -26.76 | ANZ Plus | 1120779970 |
| 2024-11-01 | Visa Debit purchase card 5673 paypal *temu com 4029357733 | -224.94 | ANZ Plus | 1120780027 |
| 2024-11-01 | Visa Debit purchase card 5673 big w/stanhope gardens stanhop | -26.50 | ANZ Plus | 1120780021 |
| 2024-11-04 | Payment to Maliheh Khalajijou #474140 | -400.00 | ANZ Plus | 1120780105 |
| 2024-11-04 | Payment to Maliheh Khalajijou #765425 | -400.00 | ANZ Plus | 1120780093 |
| 2024-11-04 | PAYPAL *ALDIMOBILE ALDIMOSydney AU | -29.00 | Smart Access | 1120775551 |
| 2024-11-06 | Payment to Maliheh Khalajijou #589658 | -500.00 | ANZ Plus | 1120780168 |
| 2024-11-07 | Check Out 7 - Visa Debit purchase card 5673 2co.com hp inc.  | -12.99 | ANZ Plus | 1120780219 |
| 2024-11-14 | Visa Debit purchase card 5673 nobabyblisters charity www.nob | -10.86 | ANZ Plus | 1120780459 |
| 2024-11-14 | Payment to Maliheh Khalajijou #447759 | -400.00 | ANZ Plus | 1120780435 |
| 2024-11-15 | Payment to Maliheh Khalajijou #979009 | -500.00 | ANZ Plus | 1120780522 |
| 2024-11-20 | Visa Debit purchase card 5673 uber* trip sydney | -26.83 | ANZ Plus | 1122502309 |
| 2024-11-23 | Amazon marketplace AU sydney south | -57.35 | ANZ Plus | 1125907969 |
| 2024-11-23 | Amazon marketplace AU +618662161072au POS authorisation | -144.49 | ANZ Plus | 1125907966 |
| 2024-11-23 | Visa Debit purchase card 5673 amazon marketplace AU sydney s | -59.00 | ANZ Plus | 1125404317 |
| 2024-11-23 | Amazon marketplace AU +618662161072au POS authorisation | -42.90 | ANZ Plus | 1125404305 |

### Sume asadi — 28,077.99 AUD / 49 تراکنش (2024-08-09 تا 2024-11-26)

| ماه | جمع (AUD) |  | حساب مبدأ | جمع (AUD) |
|---|---:|---|---|---:|
| 2024-08 | 1,987.48 |  | ANZ Plus | 18,907.81 |
| 2024-09 | 10,715.16 |  | ANZ Business Essentials | 9,066.00 |
| 2024-10 | 3,675.11 |  | COMPLETE FREEDOM | 98.18 |
| 2024-11 | 11,700.24 |  | ANZ Save | 6.00 |

| تاریخ | شرح (Merchant) | مبلغ | حساب | Bank ID |
|---|---|---:|---|---|
| 2024-08-09 | EFTPOS DEBIT 09AUG21:21 MCDONALDS STANHOPE STANHOPE GARDNSWA | -2.50 | COMPLETE FREEDOM | 1120775056 |
| 2024-08-09 | EFTPOS DEBIT 09AUG21:13 PS FOODS PTY LTD STANHOPE GARDNSWAU | -8.75 | COMPLETE FREEDOM | 1120775053 |
| 2024-08-10 | Payment to Pb Holidays #436605 | -1,280.00 | ANZ Plus | 1120777909 |
| 2024-08-11 | Visa Debit purchase card 5673 myob Australia burwood east | -31.00 | ANZ Plus | 1120777945 |
| 2024-08-13 | Payment to Low Price Windscreens #64385 0 | -290.00 | ANZ Plus | 1120777963 |
| 2024-08-18 | Visa Debit purchase card 5673 netflix.com melbourne | -7.99 | ANZ Plus | 1120778062 |
| 2024-08-18 | Payment to Sume Asadi #694344 | -100.00 | ANZ Plus | 1120778053 |
| 2024-08-22 | Payment to Sume Asadi #689877 | -250.00 | ANZ Plus | 1120778098 |
| 2024-08-25 | Visa Debit purchase card 5673 mcdonalds stanhope stanhope ga | -2.00 | ANZ Plus | 1120778221 |
| 2024-08-28 | Visa Debit purchase card 5673 northside burgers pymble | -4.57 | ANZ Plus | 1120778290 |
| 2024-08-29 | Visa Debit purchase card 5673 sq *lucaccino pymble | -10.67 | ANZ Plus | 1120778323 |
| 2024-09-01 | Payment to Kourosh Mahmoodi #127459 | -1,676.00 | ANZ Plus | 1130199826 |
| 2024-09-03 | Payment to Sydney Tehran Group #130007 | -1,661.60 | ANZ Plus | 1120778401 |
| 2024-09-06 | Visa Debit purchase card 5673 smp*lion rock pty ltd rouse hi | -86.06 | ANZ Plus | 1120778485 |
| 2024-09-07 | Payment to Sume Asadi #953108 | -500.00 | ANZ Plus | 1120778512 |
| 2024-09-12 | Payment to Pb Holidays #880849 | -1,000.00 | ANZ Plus | 1120778653 |
| 2024-09-17 | EFTPOS DEBIT 17SEP19:01 COLES 0702 STANHOPE GDNS AU | -1.54 | COMPLETE FREEDOM | 1120775092 |
| 2024-09-18 | Visa Debit purchase card 5673 netflix.com melbourne | -7.99 | ANZ Plus | 1120778872 |
| 2024-09-18 | Payment to Sume Asadi #263887 | -500.00 | ANZ Plus | 1120778866 |
| 2024-09-25 | Payment to Ehsan Davari #363191 | -3,885.00 | ANZ Plus | 1120779013 |
| 2024-09-26 | EFTPOS DEBIT 25SEP22:13 COLES EXPRESS 1710 PARKLEA AU | -16.25 | COMPLETE FREEDOM | 1120775116 |
| 2024-09-29 | Visa Debit purchase card 5673 the grange buffet blacktown | -316.99 | ANZ Plus | 1120779088 |
| 2024-09-29 | Payment to Armin Mohebiafzal #046458 | -1,000.00 | ANZ Plus | 1120779079 |
| 2024-09-30 | EFTPOS DEBIT 30SEP17:45 PLATINUM FOOD HOLDINGSRouse Hill AU | -47.95 | COMPLETE FREEDOM | 1120775140 |
| 2024-09-30 | EFTPOS DEBIT 30SEP15:38 SQ *OLIVER BROWN ROUSERouse Hill NSW | -15.78 | COMPLETE FREEDOM | 1120775134 |
| 2024-10-12 | Visa Debit purchase card 5673 kabul butchery pty ltd blackto | -46.00 | ANZ Plus | 1120779295 |
| 2024-10-15 | Visa Debit purchase card 5673 call dynamics pty lt south yar | -115.51 | ANZ Plus | 1120779448 |
| 2024-10-17 | Visa Debit purchase card 5673 bp lane cove 2212 lane cove | -24.20 | ANZ Plus | 1120779562 |
| 2024-10-17 | Visa Debit purchase card 5673 east sydney hotel woolloomoolo | -65.40 | ANZ Plus | 1120779556 |
| 2024-10-18 | Visa Debit purchase card 5673 netflix Australia pty ltd melb | -7.99 | ANZ Plus | 1120779577 |
| 2024-10-26 | Payment to Sume Asadi #092935 | -1,500.00 | ANZ Plus | 1120779838 |
| 2024-10-29 | Payment to S Niazmand #607211 | -910.00 | ANZ Plus | 1120779889 |
| 2024-10-31 | Resident withhold tax on interest paid | -6.00 | ANZ Save | 1120777696 |
| 2024-10-31 | Payment to Sume Asadi #105183 | -1,000.00 | ANZ Plus | 1120779964 |
| 2024-10-31 | DEBIT INTEREST | -0.01 | COMPLETE FREEDOM | 1120775218 |
| 2024-11-12 | Payment to Sume Asadi #389103 | -500.00 | ANZ Plus | 1120780402 |
| 2024-11-15 | Visa Debit purchase card 5673 call dynamics pty lt south yar | -16.50 | ANZ Plus | 1120780525 |
| 2024-11-17 | 000000000532846 CIRCUM VENDING MENTONE | -5.40 | COMPLETE FREEDOM | 1120775242 |
| 2024-11-18 | Visa Debit purchase card 5673 netflix.com melbourne | -7.99 | ANZ Plus | 1120780648 |
| 2024-11-19 | Visa Debit purchase card 5673 sp montu group pty ltd east me | -142.50 | ANZ Plus | 1130248747 |
| 2024-11-22 | Payment to Sume Asadi #432161 | -500.00 | ANZ Plus | 1124513824 |
| 2024-11-24 | Payment to Ehsan Zamani #599386 | -1,430.00 | ANZ Plus | 1126633624 |
| 2024-11-26 | Allianz Insurance | -312.00 | ANZ Business Essentials | 1129869661 |
| 2024-11-26 | google ad یک ماه و نیمی که وصل بود اوایل اگوست درحالی که سای | -186.00 | ANZ Business Essentials | 1129869646 |
| 2024-11-26 | 8 * 35 xero باید نصف بر میداشتن باید زنگ بزنم | -280.00 | ANZ Business Essentials | 1129869640 |
| 2024-11-26 | ezidebit | -388.00 | ANZ Business Essentials | 1129869637 |
| 2024-11-26 | بنزین | -3,300.00 | ANZ Business Essentials | 1129862905 |
| 2024-11-26 | برداشت مستیم از کارت بیزنس | -4,600.00 | ANZ Business Essentials | 1129862518 |
| 2024-11-26 | Hmr hcm 8188809021 ca POS authorisation | -31.85 | ANZ Plus | 1130150212 |

## ۳) نکات و ناهنجاری‌های نیازمند verdict مالک/حسابدار

1. **پرداخت‌های Behzad از مسیر Armin** — ۱۹ از ۲۰ تراکنشِ «behzad cashout» در واقع `Payment to Armin Mohebiafzal` است `[FACT]`. اگر حقوق بهزاد از طریق حساب آرمین پرداخت شده، ردّ حسابرسی مبهم می‌شود و سؤال worker-status (employee/contractor) و PAYG را حادتر می‌کند `[OPEN — مالک توضیح دهد]`.
2. **حقوق‌ها از حساب‌های غیربیزنس** — پرداخت‌های Armin (حقوق ماهانه: AUG 2,700 · SEP 2,220 · OCT 2,800 · NOV 2,600 + اضافه‌کاری) از `ANZ Plus` رفته نه `ANZ Business Essentials` `[FACT]` → مخلوط‌شدن شخصی/بیزنس، همان «بزرگ‌ترین red flag حسابرسی» در MANIFEST `[OPEN]`.
3. **ماهیت Rent** — 1,488 هر دو هفته از `COMPLETE FREEDOM`. تجاری (GST-claimable) یا مسکونی؟ + معنی ردیف‌های «recovered» `[OPEN — config importer هم منتظر همین است]`.
4. **دستهٔ Sume asadi مخلوط است** — هزینه‌های بیزنس (Allianz، Google Ads، Xero، Ezidebit، بنزین 3,300، برداشت 4,600) + شخصی (Netflix، غذا) + حواله‌های ایران (Sydney Tehran Group، Kourosh Mahmoodi، Pb Holidays، Ehsan Davari/Zamani، S Niazmand) همه زیر یک برچسب `[FACT]`. یادداشتِ «۸×۳۵ xero باید نصف برمی‌داشتن» نشانهٔ توافق تقسیم هزینه است `[EST]` → آیا Sume Asadi شریک تجاری است؟ سهم‌ها چگونه تسویه می‌شود؟ `[OPEN]`
5. **GST روی برداشت نقدی** — importer برای «برداشت مستقیم از کارت بیزنس» (4,600) GST=418.18 محاسبه کرد؛ برداشت/انتقال GST ندارد → به backlog importer اضافه شد `[FACT — gap شناسایی‌شده]`.
6. **گیرنده‌های ناشناس برای Div 7A** — Ehsan Zamani (در ASSOCIATES config هست)، Ehsan Davari، S Niazmand، Kourosh Mahmoodi، Pb Holidays، Sydney Tehran Group: کدام associate و کدام طرف تجاری‌اند؟ `[OPEN]`

## ۴) یادداشت Div 7A `[Unverified — accountant to confirm]`

اگر در این بازه Pty Ltd فعال بوده و این پرداخت‌ها از منابع شرکت به associates باشد، هر برداشت/قرضِ بدون سند حقوق یا قرارداد قرضِ منطبق، بالقوه مشمول Div 7A است (dividend فرضی). اما `[EST]` بر اساس نام حساب‌ها (ANZ Plus / COMPLETE FREEDOM / Smart Access) این‌ها حساب شخصی به نظر می‌رسند و شاید دورهٔ sole-trader بوده — در آن صورت Div 7A موضوعیت ندارد و موضوع صرفاً drawings شخصی است. تشخیص نهایی فقط با حسابدار.

## ۵) برای تبدیل به sub-ledger رسمی چه لازم است

- export کامل و فیلترنشدهٔ ANZ (همهٔ حساب‌ها، FY2024-25 و FY2025-26) — reconciliation فقط روی export کامل معنا دارد
- پاسخ ۶ سؤال بخش ۳ + تعیین worker-status
- تأیید حسابدار روی طبقه‌بندی حقوق vs برداشت vs قرض

---
*Sources: data/حساب کتاب/*.xlsx (۶ فایل) · drafts/ledger-extract/*.csv (استخراج 2026-07-12) · drafts/importer-run/*.json*
