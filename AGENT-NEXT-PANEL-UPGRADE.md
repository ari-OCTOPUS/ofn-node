---
tags: [ofn, megaprompt, panels, ui, agent]
aliases: [دستورالعمل ارتقای کنترل‌پنل‌ها, Agent Next Panel Upgrade]
updated: 2026-08-10
status: باز — منتظر اجرای عامل
---

# دستورالعمل ایجنت بعدی — اسکن، ادغام و ارتقای چهار کنترل‌پنل

> این سند self-contained است. هدف: تمام قابلیت‌های تازهٔ بک‌اند (و شکاف‌های UI)
> را به چهار کنترل‌پنل **اضافه یا ادغام** کنی — **هیچ بخش کارآمدی را حذف نکن**.
>
> اول اسکن زنده بگیر، بعد مرحله‌به‌مرحله هر پنل را تمام کن، بعد برو سراغ بعدی.

**پیوندها:** [[docs/handoffs/panel-scans-2026-08-10/INVENTORY|اسکن پایه]] ·
[[INDEX]] · [[HANDOFF]] · [[CLAUDE]] · [[DECISIONS]] · [[DESIGN-DIRECTIVE]] ·
[[MEGAPROMPT-MARKETING-PLATFORM-INTEGRATION]] · [[LESSONS-ZIMAN]] · [[LESSONS-STUDIO]]

---

## ۰) مأموریت در یک جمله

چهار کنترل‌پنل زنده را اسکن کن، بعد هر کدام را طوری ارتقا بده که حقیقتِ
اندازه‌گیری‌شدهٔ نود را نشان بدهد و قابلیت‌های جدید (inbox، observability،
سلامت، empty-state، متن گرم) **به UI اضافه شوند** — بدون پاک‌کردن میز کار
فعلی شریک/مالک.

```
حذف ممنوع · ادغام یا اضافه مجاز · حقیقت > زیبایی · فارسی گرم · D-22
```

---

## ۱) چهار کنترل‌پنل — فقط این‌ها

| ترتیب اجرا | پنل | فایل | پورت | دامنه | کاربر |
|---|---|---|---:|---|---|
| ۱ | مالک | `web/panel.html` | ۸۷۹۴ | panel.master-painting.com | آری |
| ۲ | لید | `web/lead.html` | ۸۷۹۲ | lead.master-painting.com | عباس |
| ۳ | استودیو | `web/studio.html` | ۸۷۹۳ | studio… + `/sabaapp` | سبا |
| ۴ | زیمان | `web/ziman.html` | ۸۷۹۱ | ziman.master-painting.com | ملیحه |

ترتیب عمدی است: اول کوک‌پیت مالک (بیشترین شکاف observability)، بعد پارتنرهایی
که CRM/آرشیو دارند، آخر زیمان (پایدارتر و حساس به فرم قطعه).

`hypno` خارج از این مأموریت است مگر آری بگوید.

---

## ۲) قوانین سخت

```
❌ هیچ بخش موجودِ کارآمد را پاک نکن (فرم، تب، kill، CRM، آرشیو، چت، …)
❌ راز نخوان / echo نکن
❌ WIRE_* روشن نکن · گیت بسته باز نکن · outbox خالی نکن · ارسال واقعی نزن
❌ sender loop / mark_sent برای publish واقعی نساز
❌ متن فنی در UI (RAG, API, schema, token, backend, webhook jargon خام)
❌ اسم شریک قبل از auth
❌ عدد ساختگی وقتی endpoint شکست خورده
❌ commit فایل .bak-*
❌ rm -rf خارج /tmp
```

```
✅ اضافه کردن کارت/بخش/تب جدید کنار موجود
✅ ادغام دادهٔ تازه در کارت موجود
✅ اصلاح باگ و متن و empty-state
✅ endpoint خواندنی owner جدید اگر لازم است (بدون outbound)
✅ تست reachability / shell / UI contract
✅ screenshot قبل و بعد
```

اصل: اگر شکی داری چیزی را حذف کنی — **حذف نکن، بپرس**.

---

## ۳) حقیقت روی زمین — اول بسنج

```bash
cd ~/ofn
python3 tools/repo_baseline.py --tests
python3 -m pytest -q --tb=line
systemctl is-active ofn hypno-fugu-mini cloudflared
git status -sb && git log -3 --oneline

for pair in "8794:panel" "8791:ziman" "8792:lead" "8793:studio"; do
  port=${pair%%:*}; name=${pair##*:}
  curl -s -m5 -o /dev/null -w "$name %{http_code} %{size_download}\n" \
    -H "Host: ${name}.master-painting.com" "http://127.0.0.1:${port}/"
done
curl -s -m5 -o /dev/null -w "sabaapp %{http_code}\n" \
  -H "Host: studio.master-painting.com" "http://127.0.0.1:8793/sabaapp"
```

بک‌اند مرتبطی که UI هنوز کامل نشانش نمی‌دهد (از کامیت `d140756` و اسناد):

```
ofn/adapters/marketing_inbox.py
ofn/adapters/correlation.py
ofn/adapters/inbound_rate.py
ofn/adapters/webhook_verify.py
ofn/adapters/connector_contract.py
ofn/adapters/connector_metrics.py
POST /api/v1/webhooks/…  (قبل از auth)
```

اسکن پایهٔ قبلی: [[docs/handoffs/panel-scans-2026-08-10/INVENTORY]].

---

## ۴) آیین اسکن — برای هر پنل، قبل از هر ویرایش

دایرکتوری خروجی:

```
docs/handoffs/panel-scans-<YYYY-MM-DD>/
  INVENTORY.md          # ماتریس موجود/شکاف
  01-panel-before.png
  02-lead-before.png
  03-studio-before.png
  04-ziman-before.png
  …-after.png           # بعد از ارتقا
```

برای هر پنل این پنج کار را انجام بده و در INVENTORY بنویس:

### ۴-۱) Screenshot

- HTTPS همان دامنه را در مرورگر باز کن.
- حالت بدون auth را بگیر (حقیقتِ پیش‌نمایش).
- اگر راهی برای auth تستی بدون خواندن راز نداری، همان پیش‌نمایش + HTML کافی است؛
  حدس نزن که پشت auth چه شکلی است — از کد `web/*.html` و endpointها بخوان.

### ۴-۲) HTML سرو‌شده

```bash
curl -s -H "Host: NAME.master-painting.com" \
  http://127.0.0.1:PORT/ | tee /tmp/NAME.served.html | wc -c
# برای استودیو علاوه بر /، /sabaapp را هم بگیر
```

### ۴-۳) Inventory خودکار از HTML

استخراج کن:

- `<title>` و headings
- `id=`های مهم
- همهٔ مسیرهای `/api/v1/…`
- دکمه‌های خطرناک (حذف، ارسال، kill)
- المان‌های `hidden` و بازکننده‌شان در `boot()`/`refresh()`

### ۴-۴) ماتریس سه‌ستونه

| بخش UI | وضعیت | اقدام |
|---|---|---|
| … | موجود و سالم | دست نزن / فقط polish |
| … | موجود ولی ناقص | ادغام دادهٔ تازه |
| … | غایب ولی بک‌اند هست | اضافه کن |
| … | غایب و بک‌اند نیست | یا endpoint خواندنی بساز یا «اندازه‌گیری نمی‌شود» |

### ۴-۵) لیست ممنوع‌حذف آن پنل

حداقل ۵ چیز که اگر حذف شوند مأموریت شکست است. مثال مالک: kill، صف تصمیم،
میز نقاشی، outbox، metrics.

**دروازهٔ اسکن:** بدون INVENTORY تازه برای هر چهار پنل، وارد ویرایش نشو.

---

## ۵) قرارداد مشترک همهٔ پنل‌ها

بعد از هر تغییر UI این‌ها برقرار بماند:

1. `lang=fa` `dir=rtl` charset utf-8
2. D-22: بدون jargon فنی قابل‌مشاهده
3. اسم شریک فقط بعد از auth از دادهٔ امضاشده
4. هر async در boot/handler → `.catch`
5. `tg` با تابع خوانده شود نه بایند زودهنگام
6. empty-state بن‌بست نباشد (D-19)
7. عدد ساختگی وقتی fetch شکست می‌خورد نشان داده نشود
8. المان `hidden` بازکننده‌اش از boot قابل‌دسترس باشد (`test_shell_reachability`)
9. بعد از ویرایش: `systemctl restart ofn` + curl بایت عوض‌شده
10. تست مرتبط سبز

---

## ۶) فازها — اجرا به ترتیب؛ از فازی رد نشو

### فاز ۰ — آماده‌سازی

```
[ ] §۳ را زنده اجرا کن
[ ] CLAUDE / DECISIONS D-22 D-19 D-25 / HANDOFF را بخوان
[ ] اسکن پایهٔ قبلی را بخوان ولی دوباره اسکن کن
[ ] دایرکتوری panel-scans-<امروز> بساز
```

**دروازه:** suite سبز یا فقط failهای از قبل شناخته‌شده گزارش شده.

### فاز ۱ — اسکن کامل چهار پنل

برای panel → lead → studio → ziman:

```
[ ] screenshot قبل
[ ] HTML سرو‌شده
[ ] inventory + ماتریس + ممنوع‌حذف
```

خروجی: `docs/handoffs/panel-scans-…/INVENTORY.md` کامل.

**دروازه:** چهار ردیف اسکن در INVENTORY؛ هیچ ویرایش UI هنوز.

### فاز ۲ — بک‌اند خواندنی لازم برای UI (اگر غایب است)

فقط آنچه UI مالک برای **دیدن حقیقت** لازم دارد. پیشنهاد حداقلی:

```
GET /api/v1/owner/observability
  → inbox counts per tenant/status
  → connector_metrics snapshot
  → correlation: فقط اگر query با ID محدود داده شد (بدون PII)
  → webhook route present: true/false
  → measured vs not_measured صریح
```

قواعد:

- owner-only · auth اجباری · ۴۰۱ بدون session
- هیچ secret، raw webhook body، یا PII در پاسخ
- اگر مقداری خوانده نمی‌شود: کلید را حذف کن یا `null` + پرچم not_measured
- تست واحد/API برای شکل پاسخ و tenancy

**دروازه:** تست API سبز؛ هنوز UI نزن مگر endpoint آماده است.

### فاز ۳ — ارتقای `panel.html` (مالک) — تمامش کن

**حذف ممنوع:** kill، میز نقاشی و همهٔ تب‌هایش، صف تصمیم، قلب، بوت، metrics،
عصبی، دریچه‌ها، outbox، لجر، سطوح.

**اضافه / ادغام کن:**

1. کارت تازهٔ «ورودی کانال‌ها / صندوق ورودی» (زبان گرم، نه webhook jargon)
   - تعداد accepted / held / failed per tenant (ziman/lead/studio)
   - hypno فقط برچسب inventory اگر لازم است
2. کارت «سلامت اتصال‌ها»
   - capability ≠ permission ≠ health (سه ستون یا سه chip)
   - اگر connector واقعی نیست: صادقانه «هنوز وصل نشده / اندازه‌گیری نمی‌شود»
3. در بخش outbox: اگر inbox held رشد کرده، کنار outbox held دیده شود
4. correlation: یک فیلد جست‌وجوی اختیاری با ID — اگر پیدا نشد بگو پیدا نشد؛
   جزئیات خام نشان نده
5. هر fetch تازه `.catch` + empty/error فارسی
6. polish متن‌های سرد بدون عوض‌کردن معنا

تست‌ها:

- reachability المان‌های جدید از boot/refresh
- نبود کلمات ممنوع D-22
- unauthorized API

بعد:

```bash
sudo systemctl restart ofn
curl -s -H "Host: panel.master-painting.com" http://127.0.0.1:8794/ \
  | grep -n "صندوق\|ورودی\|observ\|inbox" | head
# screenshot بعد
```

**دروازهٔ فاز ۳:** screenshot بعد + INVENTORY به‌روز + تست‌های panel سبز.

### فاز ۴ — ارتقای `lead.html` — تمامش کن

**حذف ممنوع:** CRM boot، جستجو/فیلتر، جواب/قیمت، ثبت لید، سؤال‌ها.

**اضافه / ادغام:**

1. در کارت لید: امتیاز/اولویت اگر از API می‌آید — با برچسب انسانی
   («اولویت بالا/متوسط/…») نه JSON خام
2. empty-state وقتی لیست خالی است + دکمهٔ ثبت روی همان صفحه
3. اگر خطای reply/quote آمد، پیام گرم؛ دکمهٔ جعلی «ایمیل رفت» نساز
4. هدر آمار: اگر dashboard fail شد، عدد ساختگی نشان نده
5. polish متن عباس: کوتاه، عملی، غیرفنی

تست reachability + هر قرارداد UI موجود حفظ شود.

**دروازه:** screenshot بعد + CRM هنوز از boot باز می‌شود.

### فاز ۵ — ارتقای `studio.html` — تمامش کن

**حذف ممنوع:** آرشیو، گالری، چت دستیار، آپلود، حذف تک‌عکس، marketing خواندنی،
shell/boot.

**اضافه / ادغام:**

1. اگر `tg().setHeaderColor` / `setBackgroundColor` هنوز نیست — اضافه کن
2. خلاصهٔ وضعیت انتشار/صف به زبان گرم از board/marketing/status
   (قفل بودن را صادقانه بگو؛ دور نزن)
3. empty-stateها را گرم‌تر کن بدون حذف دکمهٔ موجود
4. هر async بدون catch را ببند
5. D-22 و ممنوعیت نشت اسم قبل از auth

**دروازه:** `/` و `/sabaapp` هر دو ۲۰۰؛ curl بایت؛ screenshot بعد.

### فاز ۶ — ارتقای `ziman.html` — تمامش کن

**حذف ممنوع:** فرم قطعه، قفسه، سؤال‌ها، عکس، toLatinDigits.

**اضافه / ادغام:**

1. قبل از auth: متن خنثی بدون اسم ملیحه (اگر هنوز هاردکد است — اصلاح ادغامی)
2. بعد از auth: سلام از first_name
3. قفسه خالی: کنش روی همان صفحه
4. `time_counted` / «بیشتر از خرج مواد» اگر هنوز گمراه‌کننده است — ادعا را درست کن
   نه عدد را پنهان
5. ارقام فارسی مسیر API را دوباره بسنج

**دروازه:** screenshot بعد؛ فرم ثبت قطعه هنوز کامل راه می‌رود (تست UI/API).

### فاز ۷ — رگرسیون مشترک و رگرسیون کل

```bash
cd ~/ofn
python3 -m pytest -q \
  tests/test_web_serving.py \
  tests/test_shell_reachability.py \
  tests/test_studio_shell.py \
  tests/test_connector_infra.py
python3 -m pytest -q
python3 tools/repo_baseline.py --tests

sudo systemctl restart ofn
for pair in "8794:panel" "8792:lead" "8793:studio" "8791:ziman"; do
  port=${pair%%:*}; name=${pair##*:}
  curl -s -m5 -o /dev/null -w "$name %{http_code}\n" \
    -H "Host: ${name}.master-painting.com" "http://127.0.0.1:${port}/"
done
```

Screenshot نهایی هر چهار پنل را در همان پوشهٔ scans بگذار (`*-after.png`).

**دروازه:** صفر fail جدید · HTTPS/loopback ۲۰۰ · outbox ارسال نشده.

### فاز ۸ — Obsidian / HANDOFF

```
[ ] INDEX: لینک این مأموریت + وضعیت پنل‌ها
[ ] HANDOFF: چه اضافه شد، چه عمداً حذف نشد، چه ماند
[ ] INVENTORY اسکن: before/after کامل
[ ] هیچ راز/PII در اسناد
```

Commit فقط اگر آری بگوید. پیام پیشنهادی:

```
agent-checkpoint: panel upgrade — merge observability into four shells
```

---

## ۷) چه چیزی را به هر پنل اضافه کنی — چک‌لیست محصول

### مالک (panel)

- [ ] صندوق ورودی / وضعیت کانال‌ها
- [ ] سلامت اتصال‌ها (measured/not measured)
- [ ] پیوند بصری inbox held ↔ outbox held
- [ ] جست‌وجوی correlation ID محدود
- [ ] همهٔ بخش‌های قبلی سر جایشان

### لید (lead)

- [ ] اولویت انسانی روی کارت
- [ ] empty-state + ثبت
- [ ] هدر بدون عدد دروغ
- [ ] CRM و جواب/قیمت سالم

### استودیو (studio)

- [ ] رنگ هدر تلگرام
- [ ] وضعیت انتشار صادقانه
- [ ] empty-state گرم
- [ ] آرشیو/چت/آپلود سالم

### زیمان (ziman)

- [ ] بدون اسم قبل از auth
- [ ] empty-state قفسه
- [ ] ادعای پول درست (time_counted)
- [ ] فرم قطعه سالم

---

## ۸) الگوی ادغام امن در HTML

وقتی بخش جدید می‌سازی:

```
۱. بلوک HTML جدید با id یکتا کنار بخش مرتبط — نه جایگزین کل panel
۲. renderer جدا (drawInbox, drawConnectorHealth, …)
۳. از refresh()/boot() صدا بزن؛ خطای آن بقیه را نکشد (.catch جدا)
۴. اگر داده نبود: empty فارسی، نه صفر جعلی
۵. تست: id در فایل هست + از boot/reachable است
```

اگر بخشی قدیمی و جدید هم‌پوشانی دارند:

- داده را در کارت قدیمی تزریق کن
- یا تب جدید داخل همان desktop بساز
- کارت موازیِ تکراری نساز مگر برچسب متفاوت دارند

---

## ۹) چیزهایی که عمداً تمام‌شدن را بلوکه نمی‌کنند

```
• نبود vendor واقعی / MCP / GHL
• بسته‌بودن secret_rotation و partner_precondition
• نبود publish drain (عمدی)
• پیش‌نمایش بدون Telegram (طبیعی است)
• hypno WebApp
```

---

## ۱۰) قالب گزارش پایان

```
## اسکن
- مسیر screenshots قبل/بعد
- جدول موجود/شکاف هر پنل

## بک‌اند اضافه‌شده (اگر بود)
- endpoint · تست

## UI
- panel: چه اضافه/ادغام شد
- lead: …
- studio: …
- ziman: …

## حذف‌نشده‌ها (تأیید)
- لیست ممنوع‌حذف هر پنل هنوز هست

## صحت
- pytest
- restart + curl
- outbox count قبل/بعد
- WIRE/gates دست‌نخورده

## مانده برای آری
- …
```

---

## ۱۱) دستور شروع سریع

```
۱. این فایل را کامل بخوان
۲. فاز ۰ و ۱ — فقط اسکن
۳. فاز ۲ اگر observability API لازم است
۴. فاز ۳ panel را کامل تمام کن قبل از lead
۵. فاز ۴ lead → ۵ studio → ۶ ziman
۶. فاز ۷ رگرسیون → ۸ HANDOFF
۷. اگر وسط راه خواستی چیزی حذف کنی: نکن، بپرس
```

> کنترل‌پنل جای حقیقت اندازه‌گیری‌شده است، نه جای داشبورد تزئینی.
> چیزی را که شریک یا مالک امروز با آن کار می‌کند، برای قشنگ‌تر شدن نشکن.
