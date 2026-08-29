# مفهوم WBE و مقیاس‌گذاری: الهام، نه کلید ایمنی

## گزارهٔ اصلی

در مدل کلاسیک West–Brown–Enquist و تحت فرض‌های شبکهٔ توزیع عروقی ایده‌آل:

```text
B ∝ M^(3/4)
```

یعنی نرخ کل متابولیک `B` با جرم `M` زیرخطی رشد می‌کند. derivation محلی assumptionهای شبکهٔ سلسله‌مراتبی، space filling، terminal invariant و جمع خدمت capillary را فهرست کرده است. `[DOCUMENTED] /opt/octopus/ofn-l4/docs/SCALE-AND-ACTIVE-INFERENCE.md:22-35,61-80`.

برای **نرخ ویژه** یا per-unit-capacity:

```text
specific rate ∝ M^(α - 1)
```

پس:

- `α=0.75 → α-1=-0.25 → M^-0.25`
- `α=0.81 → α-1=-0.19 → M^-0.19`
- `α=0.85 → α-1=-0.15 → M^-0.15`

این تبدیل جبری است؛ هیچ‌کدام timer برد، threshold دما یا heartbeat interval نیست.

## asymptotic در برابر finite-size

- `3/4` نتیجهٔ leading-order/infinite-size mixed tree است. `[DOCUMENTED] SCALE-AND-ACTIVE-INFERENCE.md:61-80`.
- finite-size termهای حذف‌شده را نگه می‌دارد؛ slope مؤثر به mass window و geometry وابسته می‌شود.
- در mixed WBE و window خاص هشت دهه، مثال `≈0.81` به دست می‌آید. این «قانون بهتر جهانی» نیست و حتی با Kleiber empirical ~3/4 در تنش است. `[DOCUMENTED] :84-124`.
- `0.85` در این workspace به‌عنوان threshold homeostasis proto نیز دیده می‌شود، ولی آن کاربرد WBE نیست. `[CONFLICT-AVOIDED] /opt/octopus/research-intake/lab/proto-organism/octopus/homeostasis.py:27-33`.

### استعارهٔ «شبکهٔ رسانش»

A) **Vibe Coding:** یک شهر بزرگ‌تر برای رساندن غذا و انرژی شبکه‌ای شاخه‌ای لازم دارد.  
B) **ترجمهٔ مهندسی:** allometric hypothesis دربارهٔ scaling شبکهٔ توزیع در سامانه‌های زیستی.  
C) **محدودیت:** OCTOPUS رگ، capillary یا متابولیسم زیستی ندارد؛ eMMC، event bus و network interface معادل عروق WBE نیستند.

## چه کاری نباید کرد؟

- heartbeat را با `M^(1/4)` تنظیم نکن.
- `SAFE_HALT` را از `0.75` یا `0.81` نساز.
- تعداد event یا token را heartbeat زیستی ننام.
- `0.85` homeostasis threshold را evidence برای WBE فرض نکن.
- نتیجهٔ finite-size یک پنجره را constant عمومی نکن.

سند محلی صریحاً می‌گوید thermal/RAM/disk envelope باید engineering measurement باشد. `[DOCUMENTED] SCALE-AND-ACTIVE-INFERENCE.md:126-128`.

## کد و بلوغ فعلی

### ارگانیسم زنده

هیچ WBE scaling در heartbeat زنده وجود ندارد. interval 210 از rule رشد/مرحله می‌آید و در meta ذخیره می‌شود، نه از mass exponent. `[LOCAL-LIVE] /opt/octopus/lab/ofn/organism/growth/parent.py:194-204؛ tests/test_life.py:141-147؛ SQLite meta.heartbeat_interval_s=210`.

### OFN-L4

فقط سند WBE و commentهای صریح «not WBE» در config/theta/homeostat وجود دارد؛ policy loop ندارد. `[LOCAL-SCAFFOLD] /opt/octopus/ofn-l4/ofnl4/config.py:16-28؛ theta.py:7-10`.

### proto-organism پژوهشی

`AllometryModel` exponent را تا calibration محلی `UNKNOWN` نگه می‌دارد و rate را `b0 * mass ** exponent` می‌سازد. `WearAgingModel` beat count را برای mortality استفاده نمی‌کند. `[LOCAL-OFFLINE-LAB] /opt/octopus/research-intake/lab/proto-organism/octopus/scaling.py:1-37,40-63`.

README آن codebase وضعیت `LAB-VALIDATED (22/22)` را ثبت کرده و test برای exponent 0.75 و unknown-before-calibration وجود دارد. این codebase به runtime زنده authority ندارد. `[OFFLINE_TESTED] /opt/octopus/research-intake/lab/proto-organism/README.md:1-8,32؛ tests/test_fixes.py:26-50`.

## طبقه‌بندی

- دانش/derivation: `DOCUMENT_ONLY`
- AllometryModel proto: `OFFLINE_TESTED`
- activation در organism: `IMPLEMENTED_DISCONNECTED` نیست؛ عملاً **هیچ wiring زنده‌ای ندارد**
- استفاده برای safety/timer: ممنوع تا telemetry، model selection و owner-approved ADR

## درس مفهومی

WBE دربارهٔ رابطهٔ اندازه و هزینهٔ شبکه در کلاس خاصی از موجودات است. OCTOPUS می‌تواند از ایدهٔ «budget با scale تغییر می‌کند» الهام بگیرد، اما باید metricهای خودش—RAM، latency، wear، thermal، disk—را اندازه‌گیری کند و coefficient را از telemetry معتبر به دست آورد.

Active Inference جداگانه در [09_ACTIVE_INFERENCE_CONCEPT_FA.md](09_ACTIVE_INFERENCE_CONCEPT_FA.md) آمده است.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
