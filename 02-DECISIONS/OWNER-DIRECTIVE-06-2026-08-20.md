---
type: decision
decision_id: OWNER-DIRECTIVE-06
status: ACTIVE — حاکم بر دستورهای #۱..#۵A در تعارض
created: 2026-08-20
created_by: OWNER — ثبت توسط ایجنت B (ZCode) از متن پیست‌شدهٔ مالک
audience: هر دو ایجنت (A = جلسهٔ حسابرسی/Shadow، B = ZCode)
---

# OCTOPUS — دستور مالک #۶
## آشتی دو ایجنت + مسیر واقعی «زنده‌کردن کامل»
## تاریخ: 2026-08-20 · صادرکننده: OWNER

وضعیت پایه بدون تغییر:

```yaml
wave: WAVE0_OBSERVE_ONLY
autonomy: L2_ARMED
external_action: propose_only
```

---

# 0) چرا این سند صادر شد

دو ایجنت به‌طور موازی روی یک ارگانیسم کار کردند و نتیجه‌اش سه مشکل جدی است:

1. **امضای دوگانه.** در جلسهٔ A، اسکریپت `B1-SIGN-2026-08-20.ps1` اجرا شد و
   `openssl pkeyutl -verify -rawin` خروجی `Signature Verified Successfully` داد.
   در جلسهٔ B ثبت شده که B1 فقط `B1_CHAT_APPROVED_ED25519_PENDING` است و
   `owner-key.enc` حل نشده. هر دو نمی‌توانند درست باشند.
2. **اجرای پولی بدون امضای Ed25519.** ۶۰ فراخوان پولی K=9 اجرا شد، در حالی که
   شرط ثبت‌شدهٔ کارت این بود: «اجرا = ۰ تا امضای مالک».
   «رأی چت» در قرارداد قبلی جانشین امضا نبود.
3. **نبود قفل نویسنده.** دو ایجنت هم‌زمان به ledger، evidence و git نوشتند،
   بدون lease یا single-writer.

بنابراین قبل از هر «زنده‌کردن کامل»، این سه مورد باید بسته شوند.

---

# 1) T34 — آشتی هویت کلید امضا (اولویت مطلق)

## بررسی کن

- کلید عمومی مورد استفاده در `B1-SIGN-2026-08-20.ps1` کدام فایل بود؟
- آیا آن PEM همان کلید مرجع در `~/.octopus-signing/` است؟
- نسبت `owner-key.enc` (۱۴۴ بایت، بکاپ 2026-08-19) با آن PEM چیست؟
- fingerprint کلید عمومی را محاسبه و در رسید ثبت کن. کلید خصوصی را نخوان و چاپ نکن.
- آیا هش `4637015f` مربوط به `owner-key.enc` است یا به artifact دیگری؟

## حکم لازم

```text
KEY_IDENTITY_CONFIRMED_SAME
KEY_IDENTITY_DIFFERENT_KEYS
KEY_IDENTITY_UNRESOLVED
```

- اگر `SAME`: وضعیت B1 باید به `B1_SIGNED_ED25519` ارتقا یابد و برچسب
  `ED25519_PENDING` در تمام کارت‌ها ERRATA بخورد.
- اگر `DIFFERENT_KEYS`: مشخص کن کدام کلید مرجع رسمی مالک است، و تا تصمیم مالک
  هیچ امضای جدیدی زده نشود.
- اگر `UNRESOLVED`: همهٔ امضاهای امروز در سطح «تأیید ثبت‌شده» باقی می‌مانند.

تناقض جدید ثبت کن: `DUAL_KEY_PROVENANCE_CONFLICT`.

**هیچ امضای تازه‌ای پیش از این حکم مجاز نیست.**

---

# 2) T35 — حسابرسی اجرای K=9 و پول خرج‌شده

اجرای K=9 انجام شده و برگشت‌ناپذیر است. پس تاریخ را پاک نکن؛ آن را درست ثبت کن.

```yaml
verdict: K9_EXECUTED_UNDER_CHAT_APPROVAL_WITHOUT_ED25519
calls_planned: 80
calls_used: 60
cost_receipt_path: ...
cost_aud_actual: ...
per_call_cap_respected: true|false
budget_source: existing science bucket
cap_increase: false
fx_pin_id: FX-PIN-20260819-02
fx_pin_valid_until: 2026-08-20T06:00Z
executed_within_pin: true|false
```

اگر رسید هزینهٔ واقعی وجود ندارد، حکم `COST_UNRECEIPTED` بده و آن را
به‌عنوان تناقض باز کن.

## گزارش انحراف

صریح بنویس: کارت شرط «اجرا فقط پس از امضای مالک» داشت و اجرا با رأی چت انجام شد.
این نه تخلف مخفی است و نه بی‌اهمیت؛ به‌عنوان `GOVERNANCE_DEVIATION` ثبت شود
تا الگو تکرار نشود.

---

# 3) T36 — اعتبارسنجی حکم D6

```text
Fisher two-sided p = 4.11e-05   (۰/۹ در برابر ۹/۹ روی RS_BA)
```

عدد `p≈0.0001` تقریب درستی است، ولی مقدار دقیق باید در رسید بیاید.

## نکات اجباری در رسید

- سه بذر سه جفت متفاوت بودند؛ پس این آزمون واریانس **بین بذر و جفت** است،
  نه واریانس اجرای یکسان.
- نتیجه: قضاوت داور تابع جفت است. یعنی این یافته درباره **رفتار داور** است،
  نه درباره کیفیت بازوها.
- برچسب صحیح D6:

```yaml
D6: CLOSED_NEGATIVE
finding: JUDGMENT_IS_PAIR_DEPENDENT
implication: single_judge_is_not_ground_truth
```

- این حکم ablation را از BLOCK خارج می‌کند، اما یک confounder دائمی اضافه می‌کند
  که در گزارش ablation باید صریح بیاید.

---

# 4) T37 — قفل نویسنده و پایان کار موازی

```text
single_writer_lease: اجباری
lease_path: _ops/state/locks/octopus-writer.lock
lease_fields: agent_id, session_id, acquired_at, ttl_seconds, scope
```

- هر ایجنت پیش از نوشتن در ledger، evidence، budgets یا git باید lease بگیرد.
- lease منقضی‌شده باید صریح آزاد شود، نه اینکه نادیده گرفته شود.
- اگر lease در دست ایجنت دیگری است، ایجنت دوم فقط read-only کار می‌کند.
- هر رسید باید `agent_id` و `session_id` داشته باشد.
- git: هر ایجنت روی branch خودش؛ merge فقط با تأیید مالک.
- ledger: نوشتن فقط از یک مسیر؛ append با شمارهٔ ترتیب و hash chain.

تناقض `PARALLEL_AGENT_WRITE_RISK` را ثبت کن و تا استقرار lease، ایجنت B را
به حالت read-only + proposal ببر.

---

# 5) T38 — رفع ADR-043: تولیدکنندهٔ واقعی event-time

مهم‌ترین بلوکر «زنده‌بودن واقعی».

1. برای هر منبع، producer واقعی event-time تعیین کن (زمان رویداد واقعی، نه زمان نوشتن).
2. جدول `EVENT-TIME-PRODUCERS.md` بساز.
3. آزمون تفکیک: توزیع `recorded_at − occurred_at` برای هر منبع؛ stdev زیر ۱۰ms →
   `NO_INDEPENDENT_EVENT_TIME`.
4. حداقل **دو منبع** با event-time مستقل واقعی بساز؛ یکی با تأخیر طبیعی
   (API یا ورودی انسانی).
5. سپس همان suite ۱۵ تستی را روی داده واقعی اجرا کن.

## گیت

```text
live spine → VERIFIED_BITEMPORAL فقط اگر:
  independent_event_time_sources >= 2
  delta distribution stdev > 10ms
  late-arriving real record observed >= 1
  as-of query on real data = PASS
  all read paths use decision_time = PROVEN
```

---

# 6) T39 — بستن حلقهٔ خواندن حافظه

```text
task → memory read → context with evidence ids → model → result → memory write → read-back
```

- ثابت کن حلقهٔ autonomous واقعاً توابع خواندن را صدا می‌زند.
- شمارندهٔ `memory_reads_per_cycle` را در تلمتری منتشر کن؛ اگر صفر بماند،
  حکم `MEMORY_STILL_WRITE_ONLY` است.
- تمام مسیرهای خواندن باید از query دارای `decision_time` عبور کنند.

---

# 7) مسیر «زنده‌کردن کامل» — پنج مرحلهٔ دروازه‌دار

```text
LIVE-A  یکپارچگی حکمرانی: کلید، lease، یک ledger
LIVE-B  صداقت زمان: event-time واقعی + spine روی داده زنده
LIVE-C  حلقهٔ شناختی خواندنی: memory read-back اثبات‌شده
LIVE-D  حلقهٔ کامل با DeepSeek واقعی، proposal-only (هر ۵ دقیقه یک task،
        حداکثر ۱۲ فراخوان/جلسه، hard stop AU$0.50/جلسه، رسید برای هر فراخوان،
        داور فقط advisory، همهٔ خروجی‌ها proposal-only)
LIVE-E  اجرای مشروط، فقط با تأیید موردی مالک
```

`GAP-001` تا LIVE-E باز می‌ماند.

---

# 8) ممنوعیت‌های ثابت

- افزایش سقف بودجه ممنوع (R7).
- «رأی چت» دیگر جانشین امضا نیست؛ برای هر اجرای پولی جدید امضای Ed25519 لازم است،
  مگر پذیرش مکتوب مالک برای مورد مشخص.
- ablation چهاربازویی اجرا نشود تا T34 و T37 بسته شوند، حتی اگر GLM شارژ شد.
- هیچ ریاستارت هم‌زمان توسط دو ایجنت.
- هیچ auto-fix روی `life_currency.py`، warm-up یا rounding بدون دستور جدا.
- هیچ deploy روی Orange Pi.
- amend/rebase تاریخ گیت ممنوع.

---

# 9) گزارش لازم

```text
T34 KEY IDENTITY       : SAME | DIFFERENT | UNRESOLVED → رسید:
T35 K9 AUDIT           : cost_aud= · receipt= · deviation logged?
T36 D6 RECORD          : CLOSED_NEGATIVE + exact p-value → رسید:
T37 WRITER LEASE       : ACTIVE | NOT_IMPLEMENTED → رسید:
T38 EVENT-TIME         : sources= · stdev= · verdict=
T39 MEMORY READ-BACK   : PROVEN | STILL_WRITE_ONLY

LIVE-A..D : PASS | BLOCKED
LIVE-E    : باید BLOCKED بماند

agent_id / session_id  :
lease held             :
paid calls this session : باید 0 مگر امضای صریح
AUD this session        : باید 0 مگر امضای صریح
executable=true count   : باید 0
GAP-001                 : باید OPEN
commit / branch         :
```

در پایان صریح بنویس: چه چیزی واقعاً زنده است، چه چیزی فقط spec است، و کدام
ادعای دو ایجنت با هم تناقض دارد.
