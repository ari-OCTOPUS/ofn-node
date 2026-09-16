---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, patch-plan, reuse]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/DO-NOT-REBUILD]]"
---

# MINIMAL-PATCH-PLAN

**هنوز پچ نزن.** اول یال را با شاهد ببند. هر گام: read-only مگر GO صریح مالک روی همان فایل.

## فاز ۰ — اثبات هویت درخت (امروز، فقط خواندن)

1. روی میزبان مجاز (۱۳۸ یا تونل به loopback ۱۳۸): `systemctl show ofn.service` → MainPID, ActiveEnterTimestamp.  
2. `git -C /home/ari/ofn rev-parse HEAD` و مقایسه با `d3fb20c` / `6070f51` / `6881337` / `c803dee`.  
3. وجود یا عدم `ofn/adapters/owner_decision.py` روی **همان worktree در حال اجرا**.  
4. یک GET به `127.0.0.1:8794/api/v2/owner/version` از خود ۱۳۸ (نه از LAN ۱۹۱). نبود پورت روی ۱۹۱ = NOT_OBSERVED نه ABSENT.  
5. ثبت receipt در evidence موجود؛ schema جدید نه.

DoD فاز ۰: یک JSON که `deployed_commit` و `files_present` و `pid_start` را به هم bind کند.  
اگر HEAD = `c803dee`: vault را با ofn.service یکی گزارش نکن — آن commit vault است.

## فاز ۱ — سه آزمایش اتصال (sandbox، اثر خارجی ۰)

ترتیب ثابت است. هیچ‌کدام framework نو نیست.

### P1 — Queue ID parity (Cockpit V2 ↔ decide) — DONE, FAIL

- hypothesis: `CockpitV2ReadModel.queue` همان `idem_key`های `owner_queue()` را نشان می‌دهد.  
- **verdict: REJECT_OR_REDESIGN (اتصال).** دو فضای ID ثابت شد. گزارش: [[P1-QUEUE-IDENTITY]].  
- metric مشاهده‌شده: ارجاع `owner_queue`/`idem_key` در read-model = ۰؛ منبع = mesh dirs.  
- پچ بعدی (اعمال‌نشده): adapter داخل `_collect_queue` یا resource `business_outbox`.  
- rollback: بی‌معنی — کدی نوشته نشد.

### P2 — F-2 claims embed (فقط فایل دیسکی)

- hypothesis: افزودن claims منجمد به payload AUTO-VERIFY، verdict خالی را از بین می‌برد.  
- reuse: همان `octopus_verify_dispatcher.py` + 182.  
- red: payload فقط ID. green: `claims` حاضر + witness `claims_verified`.  
- rollback: revert یک commit روی همان فایل.  
- **این نشست فایل را ندید؛ پچ ننویس تا کپی read-only از ۱۳۸ برسد.**

### P3 — EDGE-6 سه خط (۱۸۰، بعد از cleanup ردیف ۳)

- hypothesis: صدا زدن `persist_pending`+`transmit_pending` بعد از registry، proposal را enqueue می‌کند بدون duplicate.  
- reuse: الگوی هم‌نیا در همان handler.  
- negative: kill بین persist و ACK؛ duplicate delivery.  
- rollback: `.bak` یک فایل.  
- نیاز: GO مالک روی ۱۸۰. این سند GO نیست.

## فاز ۲ — اتصال schema موجود به مسیر فرمان (سایه)

فقط اگر فاز ۰ نشان داد `owner_decision.py` روی دیسک ۱۳۸ هست و decide هنوز ۱۲ فیلد را نمی‌سازد:

- یک تابع **ترجمه**: `owner_decide` موفق → ساخت `OwnerDecision` از payload موجود + hashها.  
- ننویس: route جدید.  
- ننویس: executor جدید؛ `fake_executor` را فقط در تست علیه این ترجمه بزن.  
- Telegram renderer بعد از این ترجمه، روی bot موجود.

DoD: یک decision_id در تست = همان outbox idem_key.  
اگر ترجمه بیش از سقف کوچک شد: بایست؛ یعنی binding ناقص است نه نیاز به bus.

## فاز ۳ — این ماه (shadow) فقط با GO جدا

- backup timer + مسیر mesh (GAP-3)  
- یک poller `__owner__` وقتی env کامل است  
- halt drill / lease issuer — خارج از این ممیزی مگر owner بخواهد

## این فصل انجام نشود

- هر مورد `DO-NOT-REBUILD.md`  
- promote `integration/138` به `main` بدون OD-SYNC-03  
- کپی به germline  
- download مدل  
- تغییر flag سیمی  
- ادعای exactly-once بدون fault-injection روی outbox موجود  

## سه اولویت اگر فقط سه کار مجاز باشد

1. **فاز ۰ receipt هویت** (E1) — بدون آن هر پچ به درخت غلط می‌خورد.  
2. **P1 parity صف** (E2) — ثابت می‌کند V2 و decide یک SoT دارند.  
3. **E4 EDGE-6 با GO** یا **P2 اگر فایل دیسکی در دست است** — هر کدام بدون هویت درخت ممنوع.

```
NEXT_CODE_LINE_ALLOWED=0
UNTIL=phase0_receipt_bound
```
