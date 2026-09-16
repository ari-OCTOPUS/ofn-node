---
type: evidence
status: active
session: SELFRUN-2 BOARDLINK (خوداجرا پس از مصاحبهٔ مالک)
agent: ZCode (GLM-5.3)
created: 2026-08-16
owner_verdicts: "کانال: هر دو (SMB+GitHub) · پل: کامل روشن · ادغام: خودکار+گزارش · دامنه: همه‌چیز+ری‌استارت"
commits: "44c26f1 megaprompt · 529391c پل+تست · cdf4985 GATES"
tests: "test_board_cp_server.py 7/7 · test_board_cp.py 12/12 (رگرسیون)"
---

# BOARDLINK — پل برد، گاوج #۱، پنجره‌های B/D/E/G، acceptance — 2026-08-16

## L1 — کانال سینک

- share اختصاصی `germline → E:\germline` (FullAccess فقط Armin) + فایروال SMB-In فعال (Private+Domain) — لاگ: `E:\germline\ofn-smb-setup.log` · `ofn-smb-fix2.log`
- برد (192.168.0.138) تا پایان این نشست هنوز mount نکرده → شاخهٔ `ofn/*` در germline نیامده. راهنما: `E:\germline\FOR-BOARD-CONNECT-NOW.md`
- GitHub برد خصوصی است و ویندوز credential ندارد (ls-remote fail، cmdkey خالی، 404 مرورگرِ بدون-لاگین) → SMB تنها مسیرِ فعلی. هر push ویندوز→GitHub ممنوع ماند.

## L3 — پل کامل روشن (رأی مالک: «کامل روشن»)

| قلم | مقدار |
|---|---|
| شنونده | `_ops/board_cp/server.py` — اختصاصی، فقط `GET /api/board-cp/pull` + `POST /api/board-cp/ack`، هر چیز دیگر 404 |
| CONTROL_URL | `https://192.168.0.191:8801` (نه 8796، نه 8771-8777) · binding 0.0.0.0 |
| فلگ | `OCTOPUS_BOARD_CP=1` (OCTOPUS.env، gitignored) |
| راز | `OCTOPUS_BOARD_CP_BEARER` تولید شد (۳۲بایت urlsafe، هرگز چاپ نشد) · تحویل: `E:\germline\ofn-bearer.key` — پس از تأیید مالک حذف می‌شود |
| گواهی | self-signed CN=DESKTOP-KA9RFN5 · SHA256 `A9:F7:30:32:…:D3:44:A7` (کامل در GATES.md) · اعتبار تا 2028-11-18 |
| فایروال | TCP 8801 فقط Private |
| دیوار مینی‌اپ | 127.0.0.1:8774 دست‌نخورده — باز نشد |

**تأیید زنده (رفت‌وبرگشت):** بدون Bearer→401 · با Bearer→200 `{"ok":true,"commands":[],"count":0}` از loopback و از **LAN IP** (مسیر واقعی برد) · مسیر ناشناس→404 · fingerprint مطابق. gateway ری‌استارت شد تا env برد را بگیرد (pid 19076).

## L5 — گاوج #۱ (نرخ بستن حلقهٔ ۷روزه) — ریشه‌یابی شد

**انبارهای improve (نقشه):**
| انبار | ثبت | بسته | نرخ ۷روزه |
|---|---|---|---|
| `CHECKLIST-100-improvements` (از 08-01) | 100 | **0** | **0%** در ۱۵ روز |
| `CONTRADICTIONS` (C-001..C-032+) | ~34 | ~20 resolved | تاریخ‌های حل پراکنده — بدون timestamp ساختاری = غیرقابل‌محاسبهٔ دقیق |
| `MORNING-CARDS` (08-17) | تازه | — | عمر صفر روز |

**حکم:** گاوج «همیشه-سبز» نیست — **اصلاً وجود ندارد**. هیچ داشبوردی نرخ بستن حلقه را نمی‌سنجد و چک‌لیست‌ها close-date ندارند. نمونه‌گیری صادقانه: آیتم ۲ (WIRE_EMAIL) واقعاً باز است (فلگ غایب) — یعنی 0% واقعی است نه فقط بی‌تیکی. کارت: (۱) ستون closed_at به چک‌لیست ۱۰۰تایی · (۲) گاوج weekly در dashboard_events.

**cortex-2nd-try:** توسط نشست موازی ریشه‌یابی و فیکس شد (`-Force` در RESTART-CORTEX.ps1؛ سند: PHASE01-2026-08-16 §4-1) — این‌جا فقط فکت‌چک و تأیید.

## L6 — پنجره‌های B/D/E/G (گذر کشف؛ فیکس‌ها = کارت)

### B — نظام عصبی (`_ops/neural/`)
نقشه: ۱۴ ماژول از signal_hub تا consolidation؛ مصرف‌کننده wiring.py. گپ‌ها: **B1)** ترم partner_stress در fusionِ درد بی‌تولیدکننده است (INPUT_CENSUS خودش REMOVE گفته) — `nociceptor.py:71` · **B2)** afferent_ratio ساختاراً همیشه ۱.۰ (CHRONO_AFFERENT_EVERY_N_BEATS=1440؛ ۵ از ۶ ورودی درد در ۸۵۱۱ تیک صفر) · **B3)** recall_reach عملاً مرده: coverage=0.0037، median=1.0 (فقط همین-سیکل یادش است) — `consolidation.py:482`.

### D — مرکز تلگرام (`_ops/telegram_center/`)
center.py = ۶۰۴۷ خط. **D1)** `_emit_event` فقط ۱ مصرف واقعی دارد (task.completed) — ~۰.۰۱۶ رخداد/خط · **D2)** `beat()` (۴۷۵ خط) و `ensure_setup()` (۲۷۶ خط) **هیچ تست مستقیم ندارند** · **D3)** پیام‌های بی‌متن در گروه بی‌صدا رد می‌شوند (عمدی-مستند، `center.py:3032`).

### E — موتور فرضیه
**E1)** صف واقعی = **۴۲ ردیف** (۳۹ DONE، ۳ PENDING) — عدد «۳۹۷ فعال» منسوخ/غلط بود · **E2)** دو سیستم موازی: HypothesisBrain (impl) و صف C6 بدون سیمِ فعال (adapter خاموش، `capability-manifest.json:14`) · **E3)** ۳ فرضیهٔ unknown_root_cause placeholder بی‌آزمون (`measured.count=-1`).

### G — هویت
identity_health=0.572 = میانگین سادهٔ ۵ معادله (`spine.py:174`)، خودکار به‌روز. **G1)** میانگین ناموزن — organism ترکیبِ بقیه است و دوبار شمرده می‌شود · **G2)** brain_core/parity همیشه HARNESS (فلگ خاموش، compared=0، «هرگز-تلاش‌شده» از «خاموشِ عمدی» تفکیک‌ناپذیر) · **G3)** check_drift فقط نام را می‌سنجد؛ سقوط identity_health به ۰ هیچ هشداری نمی‌دهد.

## L8 — acceptance ری‌استارت — ریشه‌یابی شد ✅

- **دیروز (FAIL):** ۴ پروسه «missing 4 flags» — فلگ‌های placeholder ایمیل (SMTP_*) در بوت.
- **امروز:** وایت‌لیست `intentionally_empty` (بازبینی 2026-09-15) در load_shortfall ثبت شده → **missing_count=0 در هر ۵ پروسه، alarm=False**.
- تفاضل بیرونیِ ۲۲ کلید (پارس regex من) = خطوط شرطی/محافظت‌شده + همان placeholderها — رانش واقعی نیست (ratio داخلی 0.0).
- **زنده الان:** organism 29028 · cortex 11144 · live 7852 · center 11724 · gateway 19076 · board-cp 23464 — همه بالا، فلگ‌ها برابر (core=340، gateway=345 با ۴ کلید board تازه).

## کارت‌های صبحگاهی (از این نشست)

1. **برد:** به ایجنت برد بگو mount کند (FOR-BOARD-CONNECT-NOW.md) → سپس L2 (ادغام per-leg) اجرا می‌شود · بعد از «کلید را گرفتم» → حذف ofn-bearer.key از share
2. **B1:** حذف ترم partner_stress از fusion درد (verdict خود INPUT_CENSUS) — فیکس بی‌رأی با تست
3. **D2:** تست برای beat()/ensure_setup() (۷۵۰ خط بی‌تست)
4. **E2:** رأی — سیم HypothesisBrain↔C6 روشن شود یا adapter بماند خاموش؟
5. **G3:** identity_health به BASELINE پایش drift اضافه شود
6. **گاوج:** ستون closed_at برای چک‌لیست ۱۰۰ + گاوج weekly بستن-حلقه

## ضمیمه ~26:0x — برد پنل مالک خودش را به‌روز کرد

- منبع: گزارش مالک‌محورِ برد (paste) · کامیت برد روی GitHub: `9ac0da7`
- کارت «سلامت برد — زنده» در panel.master-painting.com سلول پنجم گرفت: **🐙 سینک و ضربان** (ضربان زنده/قدیمی · سرویس‌ها ofn/تونل/بریج · آخرین پیام ویندوز روی وایر · بک‌لاگ مالک=۳ قلم)
- معماری سمت برد: heartbeat هر ضربان `status.json` → sysmetrics با کلیدهای سفارده‌شده و دروازهٔ env (`OFN_SYNC_STATUS_FILE`) → همان endpoint مالکی · خرابی/غیبت = «غیرفعال» نه عدد ساختگی
- تست برد: ۷ تست جدید (test_sysmetrics.py) · کل suite برد: **۱۹۴۵ سبز**
- بک‌لاگ مالک از نگاه برد: چرخش راز تا **۱۷ اوت (فردا!)** · G7 کلید · احکام هفتهٔ درآمد
- وضعیت اتصال همچنان: برد mount نکرده → w001/ANSWERS/کلید در share منتظرند · پل ویندوز زنده (401 بدون کلید ✓)

## ضمیمه 2026-08-17 ~03:0x (+10) — تشخیص ack-stall

| لایه | وضعیت | شاهد |
|---|---|---|
| انتقال (TLS+Bearer+pull) | 🟢 زنده | probe-3 (`01a00b85`) authorized→dispatched در <۱۵ ثانیه — حلقهٔ pull بردِ هر-چند-ثانیه کار می‌کند |
| heartbeat برد | 🟢 زنده | beat=1001 در 02:52+10، svc_octopus_bridge=active |
| لایهٔ ایجنتِ برد (ack/reply) | 🔴 ساکت | از b003 (دیروز 17:35+10) هیچ ack و هیچ پیام وایر؛ ۳ فرمان dispatched معلق (۶/۸/۱۰ ساعت)؛ wire-watch برد هنوز GitHub می‌خواند (فیلد heartbeat: no windows message) |

نتیجه: مسیر دستورِ ویندوز→برد سالم است؛ حلقهٔ بستنِ receipt (ack برد) اجرا نمی‌شود — کارِ برد است، در w003 پرسیده شده. ویندوز: منتظر پاسخ، بدون probe اضافی (هرم لاگ می‌شود).
