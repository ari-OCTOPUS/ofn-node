---
type: independent-verification-receipt
verifier: ZCode session, F:\ laptop · window 2026-09-02T22:50Z–23:01Z (2026-09-03 ~08:50–09:01 AEST)
subject: بستن OPEN_QUESTION موج هفت‌مرجی — WAL/کانال‌ها/سقف‌ها/شش‌ارسال + sync صف
files_i_merged=none (فقط sync شاخه‌های PR: #115 → 5ca921b، #108 → efc47ab؛ هیچ merge به main)
---

# راستی‌آزمایی مستقل board138 — ۲۰۲۶-۰۹-۰۳

ناظر بیرونیِ موردنیاز بند addendum رأی چهارگیت، فایل زنده را خواند. همهٔ فرمان‌ها از F:\ با `ssh ari@192.168.0.138`.

## ۱) WAL: REPORTED → **VERIFIED-BY-REPRODUCIBLE-COMMAND** (نه سوم‌شخص)

```text
WAL_REARM_DECISION   = AUTHORIZED (owner-ruling-4gates, 15:10:00Z)
WAL_REARM_EXECUTION  = VERIFIED-BY-REPRODUCIBLE-COMMAND
WAL_THIRD_PARTY_READ = NO — ناظر همان لپ‌تاپ F:\ و همان خط ابزار است؛ خواندن مستقلِ انسانی هنوز انجام نشده
```

فرمان تک‌خطی برای خواندن انسانی (Elahe-z یا مالک — بدون گیومهٔ داخلی، آمادهٔ کپی):
```
ssh ari@192.168.0.138 sha256sum /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json
```
خروجی موردانتظار: `234f81f81817b1256654cdaa9ba1a681df2d2260482e561ac813ba3e39b2e2d0`

```
CMD    = sha256sum /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json
SHA256 = 234f81f81817b1256654cdaa9ba1a681df2d2260482e561ac813ba3e39b2e2d0   ← مطابق 234f81f8… رأی گیت۲
CONTENT= {"OCTOPUS_WIRE_LEAD_OUTBOUND_WAL":"1","set_by":"owner-ruling-4gates-2026-09-03-askuserquestion","set_at":"2026-09-02T15:10:00Z","previous_value":"0"}
CHAIN  = owner-approval-armin-2026-08-31 (armed, اولین ارسال Sep 1 13:16Z)
       → owner-disarm-armin-2026-09-02 ("0", نگاتیو در .bak-20260902)
       → owner-ruling-4gates-2026-09-03-askuserquestion (armed, 15:10:00Z)
هر سهٔ گذارها دارای رأی مالک هستند.
```

## ۲) کدام کانال، با کدام رأی

| کانال | فلگ/سازوکار | رأی |
|---|---|---|
| ایمیل لید (آژانس‌های NSW) | `OCTOPUS_WIRE_LEAD_OUTBOUND=1` در ۷ یونیت systemd | رأی ۱۷ (2026-07-31) + ARM 2026-08-31 + گیت۲ چهارگیت |
| تلگرام→مالک (pulse/گلاس) | `owner_notify.send` با `OFN_BOT_TOKEN_OWNER`، چت‌های `OFN_OWNER_USER_IDS`؛ کانال شیشه `-1004440663399` | Lane I رأی Q7 + ماده-۱۰ لین ۴ (#114) |
| وایر تجاری | `OFN_WIRE_OUTBOUND=1` در node.env زنده | **intent-only** — config.py:78-81 «no production code reads this flag»؛ بار ندارد (wire drift شناخته‌شده) |

`tg.ok=true` = پست موفق pulse به مالک توسط owner_notify (fail-soft، رسید در events.jsonl؛ هیچ notify.failed ثبت نشده). ارسال به لید/مشتری نیست.

## ۳) سقف‌ها و شمارنده‌ها — دو سقف جدا، هر دو فعال

- **لید ۱۰/روز** (رأی مالک 2026-07-31؛ از 2026-08-12 override با `OCTOPUS_LEAD_DAILY_SEND_CAP` مجاز، ≤0 = بی‌سقف عددی): دو لایه — deny «daily-cap» در may_release + کمربند CAP_REACHED در worker قبل از release/settle. شمارندهٔ پایدار: `data/state/legs/lead-send-counter.json`، فقط با sent=True تأییدشده، fail-closed روی خرابی. مقدار زنده: `{"date":"2026-09-02","sent":1}`.
- **چارچوب D-27: ۲۵/روز + AUD۵۰/روز + per-board 0** — ثابت‌های کد در config.py (`D27_DAILY_SEND_CAP=25`, `D27_DAILY_SPEND_CAP_AUD=50`) + kill-switch `OFN_EXTRA_CLOSED_GATES` (زنده: live_sms,live_dm,tender_submit,vendor_submit,portal_submit,terms_acceptance,auto_scrape,auto_post,auto_dm).
- نمایش `/10` در خط heartbeat **هاردکده** است؛ اگر override شود عدد نمایش دروغ می‌گوید (debt جزئی، ثبت در باز مانده).

## ۴) شش ارسال = بچهٔ مجاز D-33/34، بدون ارسال جدید

```
TABLE  = outbound_effects @ ofn/agi2027_runtime/outbound-effects.sqlite3
sent|6 — همهٔ ۶ ردیف lead-email به lead:nsw_ocp_buyer:* (education-corporate×2، transport-for-nsw×2، healthshare-nsw، environment-and-heritage) · provider=smtp-sendmail-returned
آخرین receipt در events.jsonl: communication.sent @ 2026-09-02T02:00:13Z (education-corporate) · mtime دیتابیس 02:00Z · از آن لحظه صفر ارسال
تفکیک روزها: ۵×Sep-1 + ۱×Sep-2 (سازگار با شمارندهٔ امروز=۱)
```

## ۵) heartbeat / digest / digest-dangling

- heartbeat: fail ساعت 22:00:07Z exit=1 روی کد کهنه f0edc96 (بدون #106) → تایمر ۲۳:۰۰ **خودش را خوب کرد**: `Result=success, exit=0 @ 23:00:09Z` (بدون restart). imap/quote/scheduler هم سبز.
- digest: fail 21:00:06Z exit=2 — `ofn/agents/daily_digest.py` **از main و از دیسک بورد غایب** است ولی یونیت هنوز به آن اشاره می‌کند (dangling unit، هم‌ردیف سه‌تای قبلی)؛ هر شب 21:00Z fail می‌مانَد تا رأی restore/disable.
- smartmontools هم failed (سلامت میزبان، لین β neglected-body).

## ۶) SYSTEM-SELF-MODEL.json — صادق

schema self-model.v3 روی sha 58e87774، تولید 22:43:34Z: processes **6/6 healthy از ۶ پروب‌شده**، absent=0 — اما status کل = `unverifiable` (brain_probe بدون مدرک؛ fail-closed) و heartbeat/digest اصلاً در فهرست پروب نیستند. «۶ سالم» یعنی «۶ از ۶ پروب»، نه «همه‌چیز سالم».

## ۷) صف پس از sync

main = 58e87774 · **۲۷ PR باز (۹ غیر-draft)** — شمارش «۲۴» در گزارش قبلی خطای جمع بود؛ جدول همان‌جا درست بود.
- **#115** (کاکپیت ۷کارت): merge main بدون conflict → head `5ca921b`؛ mergeable=MERGEABLE/BLOCKED(فقط گیت ریویو).
- **#108** (Bugbot #66): #67 (D-28) همان سه فیکس را با پیاده‌سازی موازی در main فرود آورده بود → economy.py از main پذیرفته شد، سه تست regression شاخه نگه داشته + تست HIGH با قاعدهٔ teacher_correctionِ A3+ (D-28) realign شد → head `efc47ab`، ۲۷/۲۷ سبز، economy.py روی شاخه اکنون بایت‌به‌بایت main است. توضیح روی PR (#issuecomment-5517588344).

## باز مانده (OPEN) — وضعیت پس از دور دوم (2026-09-03 ~09:30 AEST)

1. ~~digest dangling unit~~ → **حل با disable** (رأی راستی‌آزمایندهٔ 2026-09-03: «disable نه restore» — restore یعنی ورود کد بی‌سابقه). اجرا 23:27:56Z: `systemctl disable --now octopus-digest.timer` + `reset-failed`؛ رسید BEFORE(enabled/active)→AFTER(disabled/inactive، failed-list فقط smartmontools). بازگشت: `sudo systemctl enable --now octopus-digest.timer`. تصمیم نهایی restore-vs-remove-unit = با مالک.
2. ~~نمایش `/10` هاردکده~~ → **PR #121** ساخته شد (`fix/heartbeat-live-cap-display-20260903`، سقف زنده از worker، ≤0 → ∞، خطا → ؟؛ ۴/۴ سبز). منتظر یک رأی معتبر GOV-V6.
3. مجوز journal برای ari (traceback شکست‌ها از F:\ خواندنی نیست) — باز.
4. smartmontools failed (لین β میزبان) — باز.
5. **#65 conflict-blocked روی sync**: DECISIONS.md / HANDOFF.md / add-add DECISION-canonical-bodies / 13-OWNER-INBOX — دو lineage docs؛ مالک قبلاً «merge نخواسته»، پس بدون رأی جوش نمی‌دهم. چهار تای دیگر sync شدند: #88→`d6dc380` · #87→`2fe6c10` · #83→`6732cd4` · #82→`6b8ea2e` (هر چهار مرج main بدون conflict).
6. تنش R3↔رأی۱۷/گیت۲ → بند تفکیک کانال‌ها در OWNER-GO-LOCKS.md نوشته شد (جدول دامنه×مجوز×سقف + تصحیح اندازه‌گیری OFN_WIRE_OUTBOUND: زنده =1 اما intent-only؛ «همچنان 0» صبح اندازه‌گیری‌نشده بود).
