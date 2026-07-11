# PLAN-T4 — مینی‌اپِ تلگرام (web_app) برای کابینِ /ops — فقط طرح، بدون کد

- تاریخ: 2026-07-11 · وضعیت: **پیش‌نویس — بدونِ GO جداگانهٔ مالک هیچ کدی ساخته نمی‌شود** · $0 · additive/flag-گیت
- مرجع فنی: `_ops/live/server.py` روی `127.0.0.1:8773` — صفحهٔ `/ops` (RTL، poll هر ۵ ثانیه)، `GET /api/ops`، `GET /api/live` (هر دو از پاسِ `_redact`)، و اکشن‌ها `POST /api/action` + `POST /api/ask`.
- هدف T4: همان کابینِ /ops داخلِ تلگرام با دکمهٔ `web_app` — **فقط‌خواندنی**؛ هر «اقدام» همچنان فقط از دکمه‌های Bot API (cockpit v2 با allowlist بسته در `approval_channel.py`) انجام می‌شود.

## ۰. اصلِ معماری — دیوار قبل از داده
تونل **هرگز** مستقیم به 8773 وصل نمی‌شود. یک gateway جدا (`_ops/telegram_center/miniapp_gateway.py`، bind فقط `127.0.0.1:8774`) تنها مقصدِ تونل است:
- اول اعتبارسنجیِ initData (بخش ۲)، بعد حتی یک بایت داده.
- فقط دو مسیرِ خواندنی را از 8773 (loopback) proxy می‌کند: `GET /api/ops` و `GET /api/live` + یک شِلِ HTML بدونِ داده.
- **هیچ POSTی ندارد** — مسیرهای `/api/action` و `/api/ask` روی تونل اصلاً وجود ندارند. 8773 مثل امروز loopback می‌ماند.
- خروجیِ gateway دوباره از `_redact` رد می‌شود (دفاعِ دولایه؛ 8773 خودش هم redaction دارد).

## ۱. گزینه‌های تونل (HTTPS تا 8774)
| گزینه | هزینه | پایداریِ URL | راه‌اندازی | نکتهٔ کلیدی |
|---|---|---|---|---|
| **cloudflared quick tunnel** (پیشنهادی، فاز ۱) | $0، بدون حساب | هر بار URL تازهٔ `*.trycloudflare.com` | یک باینری، بدون config | URL ناپایدار **مزیت است**: هر جلسه دکمهٔ web_app با URL تازه ارسال می‌شود؛ URL کهنه خودبه‌خود می‌میرد |
| cloudflared named tunnel | $0 + نیازمند دامنه در Cloudflare | ثابت | حساب + credential-file (secret روی دیسک) | فاز ۲ اگر دکمهٔ منوی دائمی خواستیم؛ credential زیر قاعدهٔ secrets §۱۰ |
| tailscale funnel | $0 (پلن شخصی) | ثابت `*.ts.net` | نیازمند tailscaled دائمی | URL پایدار ولی حدس‌پذیرتر؛ وابستگی به یک دیمنِ همیشه‌روشنِ دیگر |

**الگوی start/stop (رأی این طرح):** tunnel-on-demand. فرمانِ مالک `/panel` در کانالِ تلگرامِ موجود → gateway بالا می‌آید → cloudflared quick tunnel اجرا و URL از خروجی‌اش پارس می‌شود → دکمهٔ `web_app` با همان URL برای مالک ارسال می‌شود → **TTL پیش‌فرض ۳۰ دقیقه** یا فرمان `/panel_off` → پروسهٔ تونل kill و gateway خاموش. هیچ‌چیز دائمی روشن نمی‌ماند.

## ۲. دیوارِ سختِ احراز — قبل از سرو کردنِ هرچیز
1. کلاینت (JS داخل شِل): `window.Telegram.WebApp.initData` را روی **هر** fetch در هدر `X-Tg-Init-Data` می‌فرستد.
2. gateway برای هر درخواستِ داده، **قبل از هر کاری**:
   - `data_check_string` = همهٔ فیلدهای initData جز `hash`، مرتبِ الفبایی، جدا با `\n`؛
   - `secret_key = HMAC_SHA256(msg=bot_token, key="WebAppData")` (توکن از env `TELEGRAM_BOT_TOKEN` — هرگز در کد/لاگ/نوت)؛
   - `HMAC_SHA256(data_check_string, key=secret_key)` باید با `hash` برابر باشد — مقایسه فقط با `hmac.compare_digest` (ضدِ timing)؛
   - `auth_date` حداکثر **۳۰۰ ثانیه** قدیمی (ضدِ replay)؛
   - `user.id` دقیقاً برابر `TELEGRAM_OWNER_CHAT_ID` (همان allowlist تک‌نفرهٔ `approval_channel.py`).
3. هر شکست → `403` با بدنهٔ خالی؛ هیچ پیام خطای اطلاعات‌دِه. شمارندهٔ شکست: بیش از ۱۰ خطا در ۶۰ ثانیه → تونل خودکشی می‌کند (بخش ۳).
4. شِلِ HTML اولیه (که تلگرام بدون initData در هدر می‌گیرد) **صفر داده و صفر state** است — فقط لودرِ استاتیک که SDK تلگرام را می‌خواند و بعد fetchهای احرازشده می‌زند. بنابراین «قبل از احراز، هیچ داده‌ای سرو نمی‌شود» برقرار است.
5. فقط‌خواندنی: هر متدِ غیر GET → `405`. هیچ cookie/session/state سمتِ سرور — هر درخواست مستقلاً احراز می‌شود.

## ۳. دفترِ ریسکِ در معرض‌گذاری + کلیدِ کشتار
| # | ریسک | مهار |
|---|---|---|
| R-1 | URL عمومی لو برود / حدس زده شود | دیوارِ HMAC (بدون initData معتبر هیچ داده‌ای نیست) + URL هر جلسه تازه + TTL ۳۰ دقیقه |
| R-2 | نشتِ bot token = امکان جعلِ initData | توکن فقط در env؛ چرخش طبق `SECRETS-ROTATION-CHECKLIST.md`؛ توکن هرگز به مرورگر/شِل نمی‌رود |
| R-3 | replay ِ initData شنودشده | TLS سرتاسری (تونل) + سقف ۳۰۰ ثانیهٔ `auth_date` |
| R-4 | باینریِ تونل (supply chain) | فقط باینریِ رسمی + پینِ checksum در اسکریپتِ راه‌انداز |
| R-5 | اکشن‌ها ناخواسته در معرض | تونل فقط به 8774؛ gateway اصلاً POST ندارد؛ 8773 فقط loopback (تغییری نمی‌کند) |
| R-6 | نشتِ secret در payload داده | redaction دولایه (8773 + gateway)؛ تستِ صریحِ ضدنشت در بخش ۵ |
| R-7 | DoS / اسکنِ خودکار روی URL عمومی | rate-limit سادهٔ درون‌پروسه‌ای + خودکشیِ تونل بعد از رگبارِ 403 + TTL |

**کلیدِ کشتار (سه لایه، هر کدام به‌تنهایی کافی):**
1. **تونل خاموش = مرگِ قطعی.** kill پروسهٔ cloudflared → URL بلافاصله می‌میرد؛ 8773/8774 هر دو loopbackاند و از بیرون هیچ‌اند.
2. فایلِ `STOP-MINIAPP` در `_ops` → gateway در health-loopاش می‌بیند، تونل را kill و خودش خارج می‌شود (همان الگوی STOP-ORGANISM/STOP-CORTEX).
3. فرمان `/panel_off` تلگرام + TTL خودکار — بدونِ دخالت هم همه‌چیز حداکثر ۳۰ دقیقه عمر دارد.

## ۴. قدم‌های ساخت (فقط بعد از GO)
1. `_ops/telegram_center/initdata_auth.py` — تابعِ خالصِ `validate(init_data, bot_token, owner_id, now)` → dict/None. صفر وابستگی، کاملاً آفلاین‌تست‌پذیر.
2. `_ops/telegram_center/miniapp_gateway.py` — سرورِ 8774: شِلِ بدون‌داده + proxy دو مسیرِ GET + دیوارِ بخش ۲ + rate-limit + حلقهٔ STOP-MINIAPP/TTL.
3. `_ops/telegram_center/tunnel.py` — start/stop ِ cloudflared quick tunnel، پارسِ URL از خروجی، TTL، گزارشِ وضعیت.
4. سیم‌کشیِ فرمان‌های `/panel` و `/panel_off` در `approval_channel.py` — پشتِ فلگِ `MINIAPP_ENABLED` (پیش‌فرض خاموش؛ الگوی flag-off موجود).
5. شِلِ HTML: همان کارتِ‌های /ops (کپیِ سبک‌شدهٔ `OPS_PAGE`) + `telegram-web-app.js` + هدرِ initData روی fetchها؛ بدونِ دکمهٔ act (اکشن‌ها در Bot API می‌مانند).
6. مستندِ اجرا + به‌روزرسانیِ HANDOFF و PROJECT ِ architect در پایانِ جلسهٔ ساخت.

## ۵. طرحِ تست (قبل از هر flip)
- **واحد — initdata_auth:** بردارِ معتبرِ ساخته‌شده با توکنِ تستی؛ hash دستکاری‌شده → رد؛ `user.id` غیرمالک → رد؛ `auth_date` کهنه (>۳۰۰s) → رد؛ فیلدِ اضافه/ترتیبِ متفاوت → پاس (مرتب‌سازی درست)؛ مقایسهٔ ضدِ timing (فراخوانیِ compare_digest در کد assert شود).
- **gateway:** بدون هدر → 403 برای همهٔ مسیرهای داده؛ initData معتبر → 200 و بدنه همانِ 8773 پس از redaction؛ هر POST/PUT → 405؛ رشتهٔ secretِ کاشته‌شده در state ِ تستی هرگز در پاسخ ظاهر نشود (تستِ ضدنشتِ صریح)؛ رگبارِ 403 → خودکشیِ تونلِ mock.
- **tunnel:** پارسِ URL از خروجیِ نمونهٔ cloudflared (fixture متنی، بدون شبکه)؛ TTL → kill؛ `STOP-MINIAPP` → kill.
- **e2e دستی (با مالک):** `/panel` از گوشیِ مالک → دکمه → کابین باز و داده زنده؛ همان URL از حسابِ غیرمالک/مرورگرِ خام → صفحهٔ خالی/403؛ `/panel_off` → URL مرده.
- **رگرسیون:** کلِ `run_all.py` سبز بماند؛ اعتبارسنج‌های vault مثل قبل.

## ۶. شرطِ صریحِ اجرا
این سند فقط طرح است. **ساختِ هر فایلِ کد، دانلودِ هر باینری، یا بازکردنِ هر تونل، نیازمندِ GO جداگانه و صریحِ مالک است** — جدا از GOهای قبلیِ T1–T3. تا آن لحظه: صفر تغییر در رفتارِ سیستم، صفر پورتِ باز، صفر وابستگیِ جدید.
