# تور سامانهٔ زنده: از boot تا listener

## L0 continuity

L0 یک لایهٔ مشاهده/عرضه است، نه مغز تصمیم‌گیر:

- gateway با authority برابر `L0 Observe/Serve` فایل‌های state را می‌خواند. با وجود عنوان «read-only»، route سلامت خودش ping اجرا می‌کند؛ بنابراین GET الزاماً بدون side effect بیرونی نیست. `[LOCAL-CODE] /opt/octopus/gateway/app.py:24-27,41-77,96-157`.
- heartbeat فقط ICMP برای allowlist خانوادگی اجرا و `health.json` را به‌روزرسانی می‌کند؛ action هنگام هشدار `none` و تصمیم با مالک است. `[LOCAL-CODE] /opt/octopus/bin/heartbeat.sh:1-17,31-84`.
- mirror فقط one-way pull طراحی شده، ولی state فعلی `blocked` و `mirror_healthy=false` است؛ backup قابل اتکا اثبات نشده. `[LOCAL-CODE] /opt/octopus/bin/mirror-pull.sh:1-19,64-78,176-178؛ /opt/octopus/state/sync.json:1-15`.
- NATS broker روی این node شروع نمی‌شود، prefix فقط `continuity.*` است و `sensorium.*` ممنوع است؛ state فعلی `connected=false` و URL خالی است. `[LOCAL-CODE] /opt/octopus/bin/nats-observe.py:1-4,30-44,95-112؛ /opt/octopus/state/nats.json:4-14`.

### استعارهٔ «فانوس بندر»

A) **Vibe Coding:** L0 فانوس و دفتر بندر است؛ حضور را نشان می‌دهد ولی سکان کشتی را نمی‌چرخاند.  
B) **ترجمهٔ مهندسی:** health cache، ping، state JSON، pull-only mirror و client-only NATS با authority محدود.  
C) **محدودیت:** فانوس یک استعاره است؛ این اسکریپت‌ها قصد، خانواده یا مسئولیت اخلاقی ندارند.

## مرجع زنده و entrypoint واقعی

زنجیرهٔ startup امروز:

1. systemd unit با `WorkingDirectory=/opt/octopus/lab` و `PYTHONPATH` همان ریشه، `start-organism.sh` را اجرا می‌کند. `[LOCAL-LIVE] /etc/systemd/system/octopus-organism-lab.service:8-23`.
2. wrapper با `flock` مانع اجرای هم‌زمان می‌شود، environment یادگیری مفهومی را enable می‌کند و module `ofn.organism.runtime.app` را راه می‌اندازد. `[LOCAL-CODE] /opt/octopus/lab/bin/start-organism.sh:4-17,35-46`.
3. `main()` DB را باز، schema را ensure، identity genesis را verify/create، lesson/future را seed و outbox قبلی را replay می‌کند. `[LOCAL-CODE] /opt/octopus/lab/ofn/organism/runtime/app.py:644-672`.
4. socket loopback ابتدا bind ولی هنوز accept نمی‌کند؛ سپس `process_started` وارد identity ledger و listener فعال می‌شود. listener LAN جدا نیز تلاش می‌شود و موفقیتش ledger event دارد. `[LOCAL-CODE] runtime/app.py:674-729`.
5. heartbeat thread شروع می‌شود و shutdown فقط با signal، append هویت و close منظم انجام می‌شود. `[LOCAL-CODE] runtime/app.py:732-768`.

در snapshot فاز ۲، سرویس‌های gateway، llama، organism، afferent و soak active بودند و restart count همه صفر بود. listenerهای مرتبط: gateway روی port عمومی محلی `8780`، قشر فقط loopback `8081` و ارگانیسم روی loopback و هویت برد `8090`. `8091` و NATS broker listener وجود نداشتند. `[RUNTIME-VERIFIED] systemd show + ss listener snapshot`.

## source در برابر process

این سه گزاره هم‌زمان درست‌اند:

- source روی دیسک نسخهٔ package `0.6.0` است. `[LOCAL-CODE] /opt/octopus/lab/ofn/organism/__init__.py:1-2`.
- process فعلی ساعت `08:52:03 UTC` شروع شده است. `[RUNTIME-VERIFIED] service octopus-organism-lab.service ExecMainStartTimestamp`.
- `persistence/db.py` و `cognition/wan.py` حدود شش تا هفت دقیقه بعد تغییر کرده‌اند. DB فعلی نیز جدول source-declared `wan_fetches` را ندارد. `[CONFLICT] file metadata؛ persistence/db.py:143-165؛ SQLite sqlite_master`.

بنابراین presence فایل، activation آن نسخه را ثابت نمی‌کند. وضعیت درست `RUNTIME_SOURCE_MISMATCH` است تا وقتی مالک یک rollout کنترل‌شده و migration تصمیم‌گیری‌شده انجام دهد؛ این مأموریت هیچ rolloutی نکرد.

## وضعیت عملیاتی زنده

- public health: `STABLE`.
- autonomy: `PROPOSE_ONLY`.
- local cortex: `AVAILABLE`.
- school/development: passed / `MATURE`، بدون بازکردن actuator.
- identity: internal chain valid.
- heartbeat interval: `210`.
- soak: running و abort برابر null.

`[RUNTIME-VERIFIED] sanitized snapshot from /opt/octopus/lab/state/ORGANISM-PUBLIC.json؛ /opt/octopus/lab/evidence/SOAK-RESULTS.json:10-16`.

## چرا GET را فقط «خواندن» فرض نکنیم؟

چند route GET، `organism_snapshot()` را صدا می‌زنند. این تابع health transition احتمالی را به ledger می‌نویسد، futures را seed/apply می‌کند و public status را atomic replace می‌کند. route eval حتی evaluation را اجرا می‌کند و attestation route فایل می‌نویسد. `[LOCAL-CODE] runtime/app.py:251-455؛ runtime/app.py:170-225؛ runtime/life_cycle.py:72-126؛ identity/attestation.py:15-46`.

به همین دلیل این tour هیچ HTTP call انجام نداد و از file/process/SQLite metadata استفاده کرد.

سه codebase و مرز authority در [01_EXECUTIVE_MAP_FA.md](01_EXECUTIVE_MAP_FA.md)؛ ترتیب کامل heartbeat در [14_RUNTIME_VS_CONCEPT.md](14_RUNTIME_VS_CONCEPT.md).

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
