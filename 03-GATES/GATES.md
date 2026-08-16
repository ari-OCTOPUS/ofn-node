---
type: gates-note
created: 2026-08-15
status: unverified
rule: "گیت بسته یعنی باز نشده؛ این یادداشت فقط ثبت می‌کند، باز نمی‌کند"
---

# GATES — گیت‌های بسته

## گیت‌های نامبرده در مگاپرامپت مالک (2026-08-15)

| گیت | موضوع | وضعیت راستی‌آزمایی |
|-----|-------|---------------------|
| `secret_rotation` | چرخش کلیدها/رازها | **تأیید به‌عنوان آیتم مسدود** (سطح B): گزارش نشست رصدخانه §10 آن را در فهرست «همچنان مسدود — نیاز به اقدام بیرونی» دارد؛ نامش در md های F:\backup نیست (مبدأ: پروژهٔ رصدخانه/Perplexity) |
| `partner_precondition` | پیش‌شرط شریک | همان وضعیت — مسدود، اقدام بیرونی لازم |
| `miner_isolation` | ایزوله‌بودن ماینینگ | همان وضعیت — مسدود؛ مفهوم مرتبط در F:\backup: D-10 (اجرای مالی هرگز) + D-23 (gVisor) |

```yaml
verified_at: 2026-08-15
verification_source: "گزارش نشست ۱۵ اوت (Downloads) §10 + PHASE-1-DECISIONS.md — خوانده‌شده مستقیم"
status: confirmed_blocked_items (سطح B) — منبع اولیهٔ نام‌ها همچنان بیرون از F:\backup
likely_origin: "CHECKPOINT.md نود میدانی (غایب در vault) / اسناد پروژهٔ رصدخانه"
```

## گیت‌های مستندِ موجود (برای کامل بودن ثبت شد)

- `halted` flag در DB = منبع حقیقت kill-switch (D-06) + فایل STOP mirror
- فاز ۴-۵ NBB-CP گیت‌شده (NBB-V2/V4 باز)
- `OCTOPUS_UNIFIED_CHAT=0` (ADR-040، خاموش)
- ADR-034/035: neural APPLY dual-mode ARMED (CURRENT-TRUTH 2026-08-12)
- `D7_EXECUTION_AUTHORIZED=FALSE` · `INDEPENDENT_THIRD_PARTY_PASS=FALSE` (CURRENT-TRUTH 2026-08-15)

## کار لازم

- [ ] از مالک: منبع اصلی سه گیت نامبرده (CHECKPOINT برد؟ سند غایب؟) → NEW در OPEN-VERDICTS


## به‌روزرسانی 2026-08-16 (مصاحبهٔ GOVERNANCE-GATES)
- **GATE 0 (Project-F):** مسیر امن ساخته شد (`_ops/state/owner-private/` — gitignored)؛ اطلاعات محل اقامت پارتنر پس از گذاشتنِ مالک ثبت می‌شود؛ **گیت تا آن لحظه بسته**.
- **سه گیت مبهم (secret_rotation/partner_precondition/miner_isolation):** منشأ همچنان خارج از F:ackup (سطح B) — جستجوی عمیق‌تر موکول شد؛ هم‌زمان کشف هماهنگیِ کامیت دوقلو ثبت شد (INTERVIEW-LOG-GOVERNANCE-2026-08-16 §کشف).

## به‌روزرسانی 2026-08-16 (نشست SELFRUN-2 BOARDLINK) — گیت board_cp باز شد

**رأی مالک (مصاحبهٔ ۲۰۲۶-۰۸-۱۶ ~24:0x):** «کامل روشن» — CONTROL_URL + کلید Bearer + فلگ‌ها برای octopus-bridge. این رأی قانونِ «هیچ فلگ WIRE تازه‌ای روشن نشود» را **فقط برای همین کانالِ بردِ داخل LAN** با تأیید مالک اِسر می‌کند؛ هیچ کانال خروجی دیگری باز نشده.

```yaml
gate: board_cp_control_channel
opened_at: 2026-08-16 16:43 (+10)
authority: "owner verdict — interview SELFRUN-2, answer #2"
implementation:
  listener: "_ops/board_cp/server.py (TLS اختصاصی، فقط pull/ack، fail-closed)"
  endpoint: "https://192.168.0.191:8801 — نه 8796، نه پورت‌های ارگانیزم"
  flag: "OCTOPUS_BOARD_CP=1 (در _ops/OCTOPUS.env، gitignored)"
  secret: "OCTOPUS_BOARD_CP_BEARER — تحویل به برد از E:\germline\ofn-bearer.key (بعد از تأیید مالک حذف می‌شود)"
  cert_fingerprint_sha256: "A9:F7:30:32:AE:2C:53:D4:0B:DF:BD:19:E8:A8:8A:FE:67:01:3A:34:BC:19:27:6B:A0:E2:60:85:93:D3:44:A7"
  firewall: "TCP 8801 inbound، فقط پروفایل Private"
  miniapp_firewall: "127.0.0.1:8774 دست‌نخورده — دیوار مینی‌اپ باز نشد"
verification:
  - "بدون Bearer → 401 (loopback و LAN)"
  - "با Bearer → 200، صف خالی، count=0"
  - "مسیر ناشناس → 404"
  - "تست‌ها: test_board_cp_server.py 7/7 + test_board_cp.py 12/12"
first_command_policy: "طبق سند شناخت ۴۶ فاز ۳: اولین فرمان زنده فقط ask یا status — نه task"
```
