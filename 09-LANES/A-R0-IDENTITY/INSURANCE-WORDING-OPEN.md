---
type: contradiction-record
lane: A-R0-IDENTITY
as_of: 2026-09-03T19:54+10
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
vantage: this_host_only
scope: this_host_only
claim_type: file_verified
may_authorize: false
hold_external: true
send: none
winner: none
resolution: owner_on_request
status: decided_by_owner
applies_to: future_DET_letter_wording_only
requires: none
superseded_open_pass: 2026-09-03T19:49+10
ruling_path: 09-LANES/A-R0-IDENTITY/INSURANCE-OWNER-RULING-2026-09-03.md
---

# حکم بیمه — تناقض تاریخی باز؛ خروجی آینده = on request

حکم مالک این نشست: **ک) بیمه = «on request» — رقم آلینز را در نامه نگذار.**

متن کامل حکم: [`INSURANCE-OWNER-RULING-2026-09-03.md`](INSURANCE-OWNER-RULING-2026-09-03.md)

`resolution: owner_on_request` و `status: decided_by_owner` فقط برای **متن آیندهٔ DET/نامه** است. فایل‌های تاریخی پاک یا بازنویسی نشدند.

```
node_id: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191   # prior A session Get-NetIPAddress Wi-Fi
vantage: this_host_only
scope: this_host_only
claim_type: file_verified
```

شماره‌های هویت (ABN / شماره پالیس) در فایل‌های مبدأ می‌مانند. اینجا فقط حضور + مسیر + هش.

## 1 — value_A (on request)

منبع: `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md`  
sha256 این نشست: `b5bd72e4f360392f148ecc830d1aa12ed9375b43ccf21c4786e21272f0eeb67a`

نقل کوتاه §۲:

> در پاسخ: certificates on request — **هیچ عدد بیمه‌ای ساخته نشد**

نقل کوتاه پیش‌نویس DET §۳:

> Insurance: Public Liability and Workers Compensation certificates  
> available on request

**Owner ruling (outgoing):** همین فرم. رقم آلینز در نامه نرود.

## 2 — value_B (استناد به PDF / رقم آلینز)

این ادعا فقط «PDF را ببین» نیست. چند نوت بعدی رقم PL و شناسه پالیس را از ایندکس/گواهی در متن DET می‌گذارند. خود ارقام اینجا کپی نمی‌شوند؛ مسیر منبع است.

| path | wording (short; numbers stay in source) | this-session sha256 |
|---|---|---|
| `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` | «متن نهایی پاسخ DET آماده (بیمه $20M Allianz)» — رقم در همان فایل | `33313f6e0855e050f3dcbcf44d7883e2b5eb89b456f7b8c114351e20655a5c3f` |
| `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/LANE-A-R0-BUSINESS-IDENTITY-2026-09-03.md` | «بیمه ✓ $20M Allianz» + شناسه پالیس در همان خط | `9f09a906a6c14f71fa7c5421685c66cf574a38f5a634e647fa03eaca621f5bf2` |
| `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/R0-CLOSE-EXECUTION-20260902T1340Z-RECEIPT.md` | «خط بیمه در پاسخ DET \| عدد واقعی $20M Allianz ذکر شود» | `e652a0d4cabbdd05976cb3cccf3cfa1b07463c84bf62e6984256b71b91856fbf` |
| `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-PACK-R0-CLOSE-2026-09-02.md` | پیش‌نویس DET: Public Liability با رقم per occurrence + Allianz + شناسه پالیس + «certificate available on request» | `4402689ddc4ac75d8a69e6ddd07863c8cb7850d70b60542b59434a4babb0a9e5` |
| `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/SEASON-LOG.md` | «DET reply can now cite "$20M Public Liability (Allianz)" — offered to owner» | not hashed this pass (`unverified` hash) |
| `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/company-docs/COMPANY-DOCS-INDEX.md` | ایندکس گواهی PL آلینز (رقم + شناسه پالیس + دوره) — منبع استخراج ادعا، نه حکم ارسال | `d713283e05b3a4c6b5b0f6f0b8e169d0657645310a33c381a61a1441159cc057` |

`$20M` / `$20,000,000` در نوت‌های بالا آمده‌اند؛ منبع ادعای رقم در ایندکس: `COMPANY-DOCS-INDEX.md` §۱. لین A صحت رقم داخل بایت PDF را باز نکرد (باینری/PII). محتوای صفحه PDF = `unverified` به‌جز هویت فایل در برابر ایندکس.

این ادعاهای تاریخی **پاک نشدند**. حکم مالک آن‌ها را از نامهٔ آینده حذف می‌کند، نه از دیسک.

## 3 — حضور PDF و هش در برابر ایندکس

| item | value | source |
|---|---|---|
| path | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/company-docs/2026-PUBLIC-LIABILITY-ALLIANZ.pdf` | Test-Path prior A pass = True |
| bytes | 221248 | Get-Item prior A pass |
| file sha256 | `53048a13a693d2364f771679a7fcaaf5c3c074e8321667687901c7635a138007` | Get-FileHash SHA256 prior A pass |
| index row 1 sha256 | `53048a13a693d2364f771679a7fcaaf5c3c074e8321667687901c7635a138007` | `COMPANY-DOCS-INDEX.md` row 1 |
| hash vs index | match | same two strings prior A pass |
| index vs file disagree? | no | — |

سه فایل ایندکس روی دیسک این والت: Allianz + SWMS + subcontract. ردیف workers-comp در ایندکس نیست.

## 4 — گواهی workers-comp / پروانه نقاش (فقط حضور)

فهرست زنده `company-docs/` گذر قبلی (۴ نام):

- `2026-PUBLIC-LIABILITY-ALLIANZ.pdf`
- `2026-SWMS-PAINT-001-REV1.pdf`
- `2026-SUBCONTRACT-INTERNAL-PAINTING-SIGNED.pdf`
- `COMPANY-DOCS-INDEX.md`

| file class | Test-Path / list | status |
|---|---|---|
| workers compensation certificate PDF | no matching filename in `company-docs/`; named probes false | MISSING on this vault |
| NSW painter licence PDF | no matching filename under owner-board depth 2 (`licen\|worker\|workcover\|icare\|painter` → no HIT) | MISSING / unverified on this vault |

ساخته نشد. جستجو فقط نام فایل.

## 5 — تناقض (خروجی آینده تصمیم‌گرفته؛ تاریخچه باز)

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| DET insurance wording (outgoing) | certificates on request; no insurance number invented | `PRICE-RULING-AND-DET-REPLY-20260902T1305Z.md` §۲–§۳ | cite Allianz PL figure (and policy id in some drafts) in DET text | `CURRENT-TRUTH.md` + `LANE-A-R0-BUSINESS-IDENTITY-2026-09-03.md` + `R0-CLOSE-EXECUTION-20260902T1340Z-RECEIPT.md` + `OWNER-PACK-R0-CLOSE-2026-09-02.md` | owner_on_request | decided_by_owner |
| same claims inside historical files | unchanged on disk | those files | unchanged on disk | those files | n/a — do not erase | FILE_VERIFIED historical |

```
resolution: owner_on_request
status: decided_by_owner
applies_to: future_DET_letter_wording_only
requires: none
winner: none
A_chose: false
owner_chose: on_request
send: none
```

آیندهٔ DET باید بگوید certificates available on request. آیندهٔ DET نباید رقم آلینز را در نامه بگذارد. `CURRENT-TRUTH` و PRICE-RULING و رسیدهای R0-CLOSE دست نخورده‌اند.

## 6 — خارج از این حکم

- ارسال DET، پر کردن `[NAME]`، رقم $306.90، QT sqlite: اینجا حل نشدند.
- نامهٔ پرشدهٔ جدید ساخته نشد؛ فقط اشاره: پیش‌نویس‌های آینده باید on-request باشند.
- `09-LANES/LANE-MATRIX.csv` در خواندن قبلی فقط L0–L9 دارد؛ پوشهٔ A از `SCOPE.md` همین لین است. ردیف ماتریس اختراع نشد.
- فایل‌های لین C دست نخورده‌اند. فقط `VOTE-SLIP-FOR-C.md` این پوشه به‌روز شد.
