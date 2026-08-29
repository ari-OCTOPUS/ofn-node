# هم‌ایستایی و آوران: حس‌کردن بدون افسانه‌سازی

## اندازه‌گیری بدن

نسخهٔ زنده این signalها را می‌خواند:

- `MemAvailable`، `MemTotal` و swap از `/proc/meminfo`
- PSI حافظه و CPU
- load1
- دمای SoC از thermal sysfs
- فضای آزاد root با `statvfs`

`[LOCAL-CODE] /opt/octopus/lab/ofn/organism/homeostasis/core.py:17-75`.

آستانه‌های source:

- MemAvailable خطر: کمتر از 350 MiB
- thermal danger: فاصله کمتر از 10°C تا critical برابر 115°C
- disk free خطر: کمتر از 1 GiB
- unknown danger: چهار signal یا بیشتر

`[LOCAL-CODE] homeostasis/core.py:5-9,76-93`.

در snapshot مأموریت، RAM available حدود 2.30 GB و root free حدود 7.03 GB بود؛ soak peak temp برابر 33.307°C و minimum memory available حدود 2.11 GiB ثبت کرده بود. public state `STABLE` بود. `[RUNTIME-VERIFIED] free/df snapshot؛ /opt/octopus/lab/evidence/SOAK-RESULTS.json:10-16`.

### استعارهٔ «تب و گرسنگی»

A) **Vibe Coding:** برد تب، گرسنگی و خستگی را از حسگرهایش می‌فهمد.  
B) **ترجمهٔ مهندسی:** thresholdهای RAM/thermal/disk و state machine deterministic.  
C) **محدودیت:** signal عددی درد یا نیاز ذهنی نیست؛ homeostasis اینجا کنترل مهندسی است، نه تجربهٔ زیسته.

## state machine

stateها: `BOOTSTRAP → OBSERVING → STABLE/DEGRADED/SAFE_HALT/RECOVERING`. transition pure است و health transition واقعی در identity ledger ثبت می‌شود. `[LOCAL-CODE] homeostasis/core.py:5,102-119؛ runtime/app.py:147-167`.

`STABLE` فقط بعد از پنج body sample بدون alert حاصل می‌شود. `[LOCAL-CODE] runtime/app.py:87-102`.

اگر cortex پایین باشد، health به `DEGRADED` می‌رود مگر این‌که از قبل `SAFE_HALT` باشد. `[LOCAL-CODE] runtime/app.py:175-189,558-573`.

## معنای دقیق `SAFE_HALT`

در implementation زنده، `SAFE_HALT` یک **state گزارش/هشدار** است. هیچ branch در `homeostasis/core.py` process را kill یا service را stop نمی‌کند. heartbeat loop نیز ادامه دارد و wait می‌کند. `[LOCAL-CODE] homeostasis/core.py:89-119؛ runtime/app.py:558-609`.

soak هم در abort، artifact را می‌نویسد و loop خودش را می‌شکند؛ ارگانیسم یا مدل را kill نمی‌کند. `[LOCAL-CODE] runtime/soak.py:90-123`.

بنابراین نام `SAFE_HALT` از رفتار اجرایی قوی‌تر است. این gap باید در آینده یا با rename (`SAFE_HALT_REPORTED`) یا با ADR/arbiter صریح رفع شود؛ هر عمل واقعی نیازمند owner approval است.

## afferent و LAN watcher

قابلیت‌ها:

- فقط CIDR محلی ثابت را قبول می‌کند.
- self، multicast، unspecified و broadcast را رد می‌کند.
- حداکثر چهار port برای هر target.
- ICMP و TCP probe می‌تواند اجرا کند.
- fail/recover streak را به up/down candidate تبدیل می‌کند.

`[LOCAL-CODE] /opt/octopus/lab/ofn/organism/runtime/lan_watch.py:12-33,60-81,84-122,125-151`.

side effectها:

- probe واقعی شبکهٔ LAN دارد.
- state JSON را atomic replace و mode موقت را `0644` می‌کند.
- در تغییرهای خطر/بازیابی letter محلی می‌نویسد و اگر Telegram آماده باشد، send می‌کند.

`[LOCAL-CODE] lan_watch.py:84-122,154-162؛ runtime/afferent.py:55-70,86-185`.

در snapshot، سرویس afferent active و سه target موجود در evidence فعلی up بودند؛ Telegram configured نبود و letter جدیدی در آن tick وجود نداشت. برای جلوگیری از تماس، این tour watcher را اجرا نکرد و فقط artifact موجود را به‌صورت aggregate خواند. `[LOCAL-LIVE] /opt/octopus/lab/evidence/AFFERENT-LIVE.json؛ service octopus-afferent-lab.service`.

### استعارهٔ «اعصاب محیطی»

A) **Vibe Coding:** afferent مثل عصب محیطی خبر تغییرات پیرامون را می‌آورد.  
B) **ترجمهٔ مهندسی:** allowlist، probe، hysteresis streak، state file و danger letter.  
C) **محدودیت:** ping ادراک یا رابطهٔ اجتماعی نیست؛ فقط reachability محدود و potentially side-effectful است.

## soak

soak هر دقیقه RAM، دما، RSS و health دو service را sample و هر ده چرخه یک tiny inference انجام می‌دهد؛ یعنی observer کاملاً passive نیست. `[LOCAL-CODE] runtime/soak.py:10-66,90-123`.

وضعیت فاز ۲: running، ۲۰۲ sample، abort=null. نام `cap: NONE_HOUR` و loop `while abort is None` نشان می‌دهد پایان زمانی داخلی ندارد؛ systemd restart-on-failure هم آن را طولانی‌مدت نگه می‌دارد. `[LOCAL-LIVE] SOAK-RESULTS.json:2-16؛ /etc/systemd/system/octopus-soak-lab.service:8-25`.

ریسک: soak نامحدود می‌تواند evidence و WAL/log را رشد دهد و خودش local HTTP/inference load ایجاد کند. mitigation آینده باید retention/cap صریح، budget دیسک و owner-approved stop policy باشد.

توالی heartbeat در [14_RUNTIME_VS_CONCEPT.md](14_RUNTIME_VS_CONCEPT.md) و ریسک‌ها در [15_RISKS_AND_GAPS_FA.md](15_RISKS_AND_GAPS_FA.md).

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
