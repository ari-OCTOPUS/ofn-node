---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
tags: [scout, architecture, adjacent-fields, track-c]
status: done
created: 2026-07-03
updated: 2026-07-04
---

# SCOUT-C — الگوهای Adjacent-Field Borrowing

> خروجی ترک C — بالاترین اهرم پرامپت. بهترین الگوها اغلب از بیرونِ دامنه می‌آیند؛ رشته‌هایی که دهه‌ها پیش مسائل ساختاری ما را حل کرده‌اند. هر الگو صریحاً به Track A یا B نگاشت می‌شود.
> روش: ۳ ایجنت موازی، ~۳۰ جستجو، ~۳۰ منبع. چون این حوزه، استانداردهای مهندسی دهه‌هاست، منابع کلاسیک معتبرند.

## خلاصه اجرایی — چهار قاعده طلایی که از بیرون قرض می‌گیریم

1. **E-stop = «قطع انرژی برای توقف»، نه «فرمان توقف».** اعتماد یک E-stop صنعتی از این است که برق را *برمی‌دارد* (سخت‌سیم، بیرون کامپیوتر)، نه اینکه به نرم‌افزار بگوید بایست. ترجمه به kill-switch ما: ایجنت‌ها فقط تا وقتی lease/heartbeat را نگه دارند اجرا می‌شوند؛ kill = باطل‌کردن credential → **نبود سیگنال = توقف پیش‌فرض**. (C→A)
2. **لایه ایمنی مستقل (SIS/IEC 61508).** در صنعت، تابع ایمنی از سیستم کنترل پایه *جدا* است تا خرابی/نفوذ کنترل نتواند شکستش دهد. این مبنای دکترین «kernel که ایجنت‌ها دورش نزنند» است — kernel باید process/credential/برقِ جدا داشته باشد، نه کتابخانه‌ای که ایجنت import می‌کند. (C→A)
3. **anchoring خارجی سرِ لاگ (Certificate Transparency).** یک witness بیرونی که head@N را دیده باشد، هر truncation زیر N را رسوا می‌کند. تبدیل «به دیسک اعتماد کن» به «به هیچ‌کس اعتماد نکن». ارزان‌ترین و پراهرم‌ترین فیکس Anchor Ledger. (C→A)
4. **device shadow + config-as-data (IoT/CDN)، self-hosted.** twin هر دستگاه با desired/reported/delta که آفلاین‌بودن node را تحمل می‌کند + push مرحله‌ای config با auto-rollback بر متریک سلامت. کل استک روی Mosquitto + git، بدون k8s و بدون cloud. (C→B)

---

## کارت‌های الگو — گروه C→A (حاکمیت و لاگ)

### C1. Two-Person Rule / No-Lone Zone
- **Track:** C→A
- **Source:** US AFI 91-104؛ ویکی‌پدیا Two-person rule — https://en.wikipedia.org/wiki/Two-person_rule [Verified]
- **رشته مبدأ:** مدیریت سلاح هسته‌ای / اقتدار پرتاب.
- **قاعده منتقل‌شونده:** هیچ actor منفردی نمی‌تواند اکشن بحرانی را کامل کند. اقتدار به *فاکتورهای هم‌زمانِ مستقلِ* فیزیکی-جدا شکسته می‌شود (دو کلید با فاصله فراتر از طول یک بازو).
- **نگاشت به A:** ضعف «solo operator = تک‌نقطه اعتماد» را روی محور autonomy-without-losing-control فیکس می‌کند. verdict پرریسک را حتی برای یک انسان به دو فاکتور مستقل بشکن: کلید سخت‌افزاری/YubiKey + کد seal-شدهٔ جدا؛ دو عمل عمدی روی دو کانال → یک کلیک خسته/تحت‌فشار نمی‌تواند approve کند.
- **هزینه:** S–M (یک توکن ~$25–50).
- **Verdict:** **BORROW NOW** — ارزان‌ترین ارتقای ساختاری root-of-trust.

### C2. M-of-N / Split-Knowledge Dual Control (نسخه نرم‌افزاریِ two-person)
- **Track:** C→A
- **Source:** AWS Organizations multi-party approval؛ CISSP «M of N»؛ key-ceremony دو-کنترلی [Verified: بخش AWS در همان ویکی] / [Unverified: doc دقیق AWS]
- **رشته مبدأ:** InfoSec / حاکمیت ابری / مراسم کلید CA.
- **قاعده:** هر approval به identity مجزا bind می‌شود؛ M تایید مستقل از N لازم است؛ هیچ principal کل secret را ندارد.
- **نگاشت به A:** آنالوگ دیجیتال مستقیم two-person — ثابت می‌کند الگوی هسته‌ای قبلاً وارد نرم‌افزار شده. برای solo: self-M-of-N زمان‌دار (دو دستگاه/identity) یا approver دومِ تعیین‌شده فقط برای بالاترین tier. هر share جدا لاگ می‌شود (tamper-evidence).
- **هزینه:** S (فقط نرم‌افزار).
- **Verdict:** **BORROW NOW** برای گیت‌های top-tier؛ **PROTOTYPE** جریان solo-دو-دستگاه.

### C3. Challenge–Response Callout + Sterile Cockpit
- **Track:** C→A
- **Source:** FAR 121.542؛ SKYbrary Sterile Flight Deck — https://skybrary.aero/articles/sterile-flight-deck [Verified]
- **رشته مبدأ:** CRM دو-خدمه هوانوردی.
- **قاعده:** یکی challenge را *می‌خواند*، دیگری state را *تایید می‌کند* (نه «OK» کور)؛ فعالیت غیرضروری در فازهای بحرانی ممنوع تا خطای حواس‌پرتی کم شود.
- **نگاشت به A:** بزرگ‌ترین شکست واقعیِ گیت solo یعنی approval-fatigue را فیکس می‌کند. UX را از «کلیک Yes» به challenge→typed-response تغییر بده (اپراتور باید اکشن/هدف مشخص را بازنویسی کند)، و «حالت sterile» که هنگام گیت برگشت‌ناپذیر بقیه prompt‌ها را خفه می‌کند.
- **هزینه:** S (طراحی UX).
- **Verdict:** **BORROW NOW** — نزدیک صفر هزینه، کاهش بالای خطا.

### C4. E-Stop = De-energize-to-Stop، سخت‌سیم (Cat 0 vs Cat 1)
- **Track:** C→A
- **Source:** ISO 13850:2015؛ IEC 60204-1 — https://blog.ansi.org/ansi/iso-13850-safety-of-machinery-emergency-stop/ [Verified]
- **رشته مبدأ:** ایمنی ماشین‌آلات.
- **قاعده:** E-stop *برق را برمی‌دارد* (Cat 0، قطع فوری) نه اینکه به نرم‌افزار فرمان توقف دهد؛ کنتاکت NC استفاده می‌کند تا سیم پاره/قطع‌برق خودش trip کند؛ reset فقط دستی؛ نباید به کنترلر عادی وابسته باشد. Cat 1 = کاهش کنترل‌شده سپس قطع.
- **نگاشت به A:** kill-switchـی که صرفاً *فرمان stop می‌فرستد* و ایجنت می‌تواند نادیده بگیرد/race کند را فیکس می‌کند. kill را **fail-safe** کن: ایجنت فقط تا وقتی lease/heartbeat را نگه دارد اجرا می‌شود (حالت «energized»)؛ kill = باطل‌کردن token → نبود سیگنال = توقف پیش‌فرض. نسخه Cat 0 (فریز فوری) و Cat 1 (تمام‌کن سپس halt).
- **هزینه:** S–M (طراحی مجدد مسیر kill به heartbeat/lease).
- **Verdict:** **BORROW NOW** — بازقاب‌بندی kill به‌عنوان de-energize، مهم‌ترین ترجمهٔ کل ترک C.

### C5. Safety Instrumented System — لایه ایمنی مستقل، de-energize to trip
- **Track:** C→A
- **Source:** IEC 61508 (SIL) / IEC 61511 (SIS) — https://en.wikipedia.org/wiki/IEC_61511 [Verified]؛ ISA 84
- **رشته مبدأ:** ایمنی تابعی صنایع فرآیندی.
- **قاعده:** SIF ترکیبِ *جدا و مستقلِ* سنسور/منطق/عنصر-نهایی از سیستم کنترل پایه است — تا خرابی یا نفوذ کنترل نتواند ایمنی را شکست دهد؛ پیش‌فرض de-energize-to-trip.
- **نگاشت به A:** مبنای دکترین «kernel که ایجنت‌ها دورش نزنند». kernel را لایه‌ای واقعاً جدا کن (process/credential/برقِ خودش روی رله kill)، نه کتابخانه‌ای که import می‌شود. سیستمِ کنترل‌شده نباید بتواند ابزار ایمنی خودش را غیرفعال کند.
- **هزینه:** M (جداسازی معماری، مرز IPC).
- **Verdict:** **BORROW NOW** (اصل) / **PROTOTYPE** (kernel کامل out-of-process). — **هم‌راستا با A12/A13 در SCOUT-A.**

### C6. Interlock → Boot into Safe State
- **Track:** C→A
- **Source:** طراحی interlock fail-safe (NC، de-energize-to-safe)؛ ISO 13849 [Verified: سنتز جستجو]
- **رشته مبدأ:** interlockهای SCADA/ماشین‌آلات.
- **قاعده:** روی هر fault/شرط نامعین، سیستم را به *حالت امن شناخته* ببر؛ قبل از ازسرگیری، reset دستیِ عمدی لازم (auto-restart نکن وقتی E-stop رها شد).
- **نگاشت به A:** ایدهٔ «boot در halted-safe» را تایید می‌کند. روی start، crash، حالت مبهم یا شکست integrity check، سیستم باید halted بنشیند و برای arm شدن verdict صریح اپراتور بخواهد — هرگز خودکار ازسر نگیرد. **هم‌راستا با A28.**
- **هزینه:** S.
- **Verdict:** **BORROW NOW**.

### C7. Defense-in-Depth + N-Version / IV&V (تایید مستقل)
- **Track:** C→A
- **Source:** NRC/IAEA INSAG-10 پنج‌سطحی DiD — https://en.wikipedia.org/wiki/Defense_in_depth_(nuclear_engineering) [Verified]؛ N-version & IV&V ذیل IEC 61508 [Unverified: بند دقیق]
- **رشته مبدأ:** هسته‌ای + نرم‌افزار ایمنی-بحرانی.
- **قاعده:** چند لایهٔ *مستقلِ متنوع*؛ به هیچ لایهٔ واحد تکیه نکن؛ استقلال سدها را حفظ و در برابر common-cause failure دفاع کن؛ خروجی ایمنی-بحرانی را با checker متنوع، مستقل بررسی کن.
- **نگاشت به A:** یک verifier دومِ *متنوع* (مدل/قاعدهٔ متفاوت) اکشن‌های پرریسک را قبل از گیت HITL cross-check می‌کند (N-version)، و integrity لاگ Anchor توسط process مستقل چک می‌شود (IV&V) — کاهش common-cause failure جایی که همان مدل هم act می‌کند هم self-approve.
- **هزینه:** M (checker متنوع) / L (IV&V رسمی).
- **Verdict:** **PROTOTYPE** verifier؛ **WATCH** N-version کامل.

## کارت‌های الگو — گروه C→A (لاگ tamper-evident، از حوزه ثبت‌سوابق)

### C8. anchoring خارجی سرِ لاگ (transparent log)
- **Track:** C→A
- **Source:** Russ Cox «Transparent Logs for Skeptical Clients» — https://research.swtch.com/tlog [Verified]؛ RFC 6962 — https://www.rfc-editor.org/rfc/rfc6962.html [Verified]
- **رشته مبدأ:** Certificate Transparency / لاگ‌های verifiable.
- **قاعده:** یک `Latest()` امضاشده = {size, root-hash} منتشر کن و بگذار هر observer یک consistency proof بخواهد که لاگ جدید هنوز شامل قدیم است. سروری که دروغ بگوید باید قربانی را «برای همیشه روی timeline بدیل» نگه دارد → کشف آسان.
- **نگاشت به A:** مستقیماً «زنجیره محلی توسط صاحب دیسک truncate/بازنویسی می‌شود» را می‌کشد. وقتی یک witness بیرونی head@N را گرفت، هیچ truncation زیر N جان به در نمی‌برد. **همان جهتِ A19/A21 در SCOUT-A — اینجا مبنای نظری‌اش.**
- **هزینه:** M (فایل hash append-only ساده است؛ یک witness بیرونی لازم — ارزان مثل post کردن head امضاشده به یک mailbox/gist/TSA).
- **Verdict:** **BORROW NOW** — تبدیل «به دیسک اعتماد کن» به «به هیچ‌کس اعتماد نکن».

### C9. RFC 3161 Trusted Timestamp روی head
- **Track:** C→A
- **Source:** RFC 3161 — https://www.rfc-editor.org/rfc/rfc3161.html [Verified] (به‌روزشده با RFC 5816)
- **رشته مبدأ:** PKI X.509 / notary.
- **قاعده:** یک TSA یک *hash* را امضا می‌کند (نه داده را)، اثبات «این قبل از زمان T وجود داشت» و جلوگیری از backdating — بدون افشای محتوا.
- **نگاشت به A:** اثبات مستقلِ اینکه head لاگ تا تاریخ T وجود داشت ⇒ مهاجم نمی‌تواند تاریخ را دوباره بزند. مکمل C8 (anchor = *چه*؛ timestamp = *کِی*، توسط شخص ثالث).
- **هزینه:** S (TSAهای عمومی رایگان/ارزان؛ فقط hashها box را ترک می‌کنند → privacy-safe).
- **Verdict:** **BORROW NOW** — ارزان‌ترین witness امضاشده و تاریخ‌دار برای solo.

### C10. Double-Entry Invariant (تمپرِ خود-آشکار)
- **Track:** C→A
- **Source:** Double-entry bookkeeping — https://en.wikipedia.org/wiki/Double-entry_bookkeeping [Verified] (Pacioli 1494)
- **رشته مبدأ:** حسابداری (~۵۰۰ سال).
- **قاعده:** هر رویداد دو طرف را می‌زند تا مجموع بدهکار = بستانکار؛ trial-balance یک reconciliation دوره‌ای ارزان است که هر ویرایش یک‌طرفهٔ خاموش را در جمع می‌شکند. journal فقط-افزودنی، بدون حذف.
- **نگاشت به A:** یک invariant افزونه فراتر از زنجیره hash اضافه کن — مثلاً یک شمارنده/aggregate در حال اجرا که یک entry جعلی نمی‌تواند ارضایش کند — تا تمپر روی reconciliation *خود-آشکار* شود، نه فقط روی re-hash کامل.
- **هزینه:** S (یک total در حال اجرا + یک reconcile check).
- **Verdict:** **BORROW NOW** — defense-in-depth بدون وابستگی؛ یک invariant دیگر برای شکستن.

### C11. Chain of Custody: لینک‌های handoff امضاشده
- **Track:** C→A
- **Source:** NIST SP 800-86 / NIST IR 8387 [Unverified — خلاصه جستجو؛ اصل در nvlpubs.nist.gov]؛ هش SHA-256 در هر انتقال
- **رشته مبدأ:** شواهد قضایی/forensics.
- **قاعده:** هر handoff یک لینکِ مستند، منتسب، زمان‌دار و *hash-شده* است که چه‌کسی–چه–کِی–چرا را ثبت می‌کند؛ زنجیره hash-verified نشکسته = قابلیت پذیرش. یک شکست، وزن شواهد را نابود می‌کند.
- **نگاشت به A:** هر *اکشن ایجنت → verdict انسانی* را یک لینک custody امضاشده مدل کن (actor، action-hash، prev-hash، verdict، sig). verdict HITL را از یک خط لاگ به root-of-trustِ غیرقابل‌انکار ارتقا می‌دهد.
- **هزینه:** S (already hash-chaining؛ actor + امضا per link اضافه کن).
- **Verdict:** **BORROW NOW** — بازقاب‌بندی زنجیره موجود به شکل custody قانونی، تقریباً رایگان.

### C12. Fixity + جداسازی دسترسی نوشتن (OAIS / حفظ دیجیتال)
- **Track:** C→A
- **Source:** DPC Handbook «Fixity and checksums» — https://www.dpconline.org/handbook/technical-solutions-and-tools/fixity-and-checksums [Verified]؛ NDSA Levels؛ OAIS ISO 14721
- **رشته مبدأ:** علم آرشیو.
- **قاعده:** checksum را در AIP ذخیره کن؛ طبق برنامه re-verify کن («data scrubbing») تا فساد *خاموش* را بگیری؛ ≥۲ نسخه نگه دار تا بد قابل‌ترمیم باشد؛ **NDSA L4: هیچ‌کس دسترسی نوشتن به همهٔ نسخه‌ها نداشته باشد.**
- **نگاشت به A:** re-verify دوره‌ای integrity (نه فقط append-time) + یک replica بیرون-box → truncation تک‌دیسکی هم قابل‌کشف هم قابل‌ترمیم. قاعدهٔ «هیچ‌کس به همهٔ نسخه‌ها write ندارد» پاسخ آرشیوی به «صاحب دیسک» است.
- **هزینه:** S–M (cron fixity + یک replica که اپراتور نتواند بی‌صدا بازنویسی کند).
- **Verdict:** **BORROW NOW** — replica + fixity زمان‌بندی‌شده، پادزهر عملیِ کنترل سطح-دیسک.

### C13. استقلال Black-Box + نوشتن پیوسته (flight recorder)
- **Track:** C→A
- **Source:** NTSB CVR/FDR + ویکی Flight recorder [Unverified — خلاصه؛ TSO-C123c/C124c، EUROCAE ED-112A]؛ RIPS برق مستقل ۱۰ دقیقه (TSO-C155b)
- **رشته مبدأ:** ایمنی هوانوردی.
- **قاعده:** ضبط‌کننده *مستقل از سیستمی است که ضبط می‌کند* (محفظه crash-hardened + برق پشتیبان مستقل)، پیوسته می‌نویسد، و بعد از رویداد شواهد read-only تحت custody می‌شود.
- **نگاشت به A:** ضبط‌کننده نباید کاملاً توسط سیستمِ ضبط‌شونده کنترل شود. روی یک SBC نمی‌توانی box هوانوردی دوم اضافه کنی، ولی می‌توانی استقلال را *تقریب* بزنی: storage حالت append-only/WORM + نوشتن safe در قطع‌برق + witness بیرون-box (C8–C9).
- **هزینه:** M–L استقلال سخت‌افزاری واقعی (دستگاه دوم/رسانه WORM)؛ S برای تقریب نرم‌افزاری.
- **Verdict:** **WATCH / BORROW جزئی** — اصل (استقلال + نوشتن durable پیوسته) را همین حالا نرم‌افزاری بگیر؛ استقلال سخت‌افزاری کامل برای اپراتور تک‌SBC تناقض دارد (پایین).

## کارت‌های الگو — گروه C→B (فلیت لبه)

### C14. Config-as-data + rollout مرحله‌ای با auto-rollback («Health Mediated Deployment»)
- **Track:** C→B
- **Source:** Cloudflare Quicksilver — https://blog.cloudflare.com/introducing-quicksilver-configuration-distribution-at-internet-scale [Verified] + Code Orange «Fail Small» — https://blog.cloudflare.com/fail-small-resilience-plan [Verified]
- **رشته مبدأ:** orchestration لبه CDN.
- **قاعده:** با config دقیقاً مثل کد رفتار کن — version، push از گیت‌ها (canary → درصد rollout)، و revert خودکار روی متریک سلامتِ شکست‌خورده. **قطعی‌های خودِ Cloudflare (دسامبر ۲۰۲۵) از push فوریِ جهانی بدون gating بود؛ فیکسشان HMD برای config است.**
- **نگاشت به B:** «SSH-edit-and-pray» را می‌کشد؛ drift + بدون rollback → اعلانی و برگشت‌پذیر.
- **هزینه:** S–M solo (یک git repo + agent pull-on-cron + یک health check).
- **Verdict:** **BORROW NOW** — یک node را canary کن، یک متریک را ببین، بعد fan out.

### C15. Device Shadow (desired/reported/delta)، self-hosted
- **Track:** C→B
- **Source:** AWS IoT Device Shadow — https://docs.aws.amazon.com/iot/latest/developerguide/iot-device-shadows.html [Verified]؛ Eclipse Ditto — https://eclipse.dev/ditto [Verified]
- **رشته مبدأ:** مدیریت دستگاه IoT.
- **قاعده:** یک twin JSON per device با `desired` (تو می‌نویسی) و `reported` (دستگاه می‌نویسد)؛ broker `delta` را حساب می‌کند؛ دستگاه هنگام reconnect reconcile می‌کند. شماره نسخه، deltaهای out-of-order/تکراری را امن دور می‌ریزد.
- **نگاشت به B:** یک منبع حقیقت واحد برای «هر Orange Pi/ESP32 *چه باید باشد*» که آفلاین‌بودن node را تحمل می‌کند. **تناقض «shadow به cloud نیاز دارد» را حل می‌کند** — Ditto یا پلاگین shadow روی Mosquitto خودت.
- **هزینه:** S–M.
- **Verdict:** **BORROW NOW** (twin self-hosted)، بدون lock-in AWS.

### C16. Store-and-Forward Telemetry روی لینک قطع‌ووصل (MQTT persistent، QoS 1)
- **Track:** C→B
- **Source:** HiveMQ MQTT Essentials Pt.7 — https://hivemq.com/blog/mqtt-essentials-part-7-persistent-session-queuing-messages [Verified]؛ SCADA RTU/DNP3 [Unverified]
- **رشته مبدأ:** SCADA شبکه‌برق + IoT.
- **قاعده:** روی قطع لینک محلی buffer کن، روی reconnect به‌ترتیب replay کن. MQTT `cleanSession=false` + QoS 1، broker را وامی‌دارد پیام‌های ازدست‌رفته را صف و redeliver کند تا ACK — دوقلوی نرم‌افزاریِ buffer store-and-forward یک RTU.
- **نگاشت به B:** مستقیماً اتصال سولار/قطع‌ووصل را فیکس می‌کند — تله‌متری و فرمان‌ها در blip لینک گم نمی‌شوند.
- **هزینه:** S (یک فلگ روی کلاینت MQTT) + disk-spool محلی برای قطعی طولانی.
- **Verdict:** **BORROW NOW**.

### C17. حالت Degraded/Safe با defaultهای معتبر («Fail Small»)
- **Track:** C→B
- **Source:** Cloudflare Code Orange [Verified: همان C14]؛ ROS 2 auto-route-out-of-pool [Unverified]
- **رشته مبدأ:** CDN + کنترل ازدحام robotics.
- **قاعده:** در هر interface، *فرض کن ورودی خراب است*؛ به‌جای panic به یک default معتبر برگرد. قطعی Cloudflare: یک config بد باعث panic-and-drop شد؛ فیکس «عبور ترافیک با classification پیش‌فرض». Robotics: ربات خراب خودکار از pool فعال drain می‌شود.
- **نگاشت به B:** ماینری که config/OTA بد می‌گیرد باید روی last-known-good به signing/monitoring ادامه دهد، نه brick شود.
- **هزینه:** S–M (انضباط طراحی، نه ابزار).
- **Verdict:** **BORROW NOW** — ارزان‌ترین برد resilience.

### C18. OTA با Confirm-or-Rollback و self-test (پارتیشن A/B)
- **Track:** C→B
- **Source:** ESP-IDF OTA API — https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/ota.html (`esp_ota_mark_app_valid_cancel_rollback()`، `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`) [Verified]
- **رشته مبدأ:** firmware MCU / OTA IoT.
- **قاعده:** image جدید **یک** بار فرصت boot دارد؛ باید self-test و *confirm* کند وگرنه bootloader خودکار به last-known-good برمی‌گردد. این همان HMD است ولی در سیلیکون.
- **نگاشت به B:** آپدیت firmware/OS امنِ بی‌مراقبت روی ESP32های دور (anti-rollback via eFuse). روی Pi با A/B root آینه کن (سبک balena/Mender [Unverified]).
- **هزینه:** S روی ESP32 (توی ESP-IDF هست)؛ M برای Pi A/B.
- **Verdict:** **BORROW NOW** (ESP32) / **PROTOTYPE** (Pi A/B). **مکمل مستقیم B19 در SCOUT-B.**

### C19. FCAPS به‌عنوان چک‌لیست سبک مدیریت
- **Track:** C→B
- **Source:** FCAPS (ISO/TMN) [Unverified]؛ TR-369/USP [Unverified]
- **رشته مبدأ:** NMS مخابرات.
- **قاعده:** مدیریت را در Fault، Config، (Accounting→) Performance، Security سازمان بده — یک نقشهٔ پوشش، نه یک محصول. تضمین می‌کند config+health بسازی ولی fault-alerting یا چرخش کلید را فراموش نکنی.
- **نگاشت به B:** SSH دستی را بدون ابزار سنگین به یک مدل ساخت‌یافته تبدیل می‌کند. **تناقض:** استک کامل TR-069/USP فلیت‌های ISP-scale فرض می‌کند — برای ۱۰ node اضافه‌وزن است.
- **هزینه:** S به‌عنوان چک‌لیست.
- **Verdict:** **BORROW** قاب FCAPS؛ **SKIP** سرورهای TR-069/USP.

### C20. Cattle-not-Pets + حلقه reconcile گیت‌آپس
- **Track:** C→B
- **Source:** Pets-vs-cattle (Bias، ~۲۰۱۲) [Unverified]؛ reconcilerهای GitOps فلیت [Unverified]
- **رشته مبدأ:** SRE / immutable infra.
- **قاعده:** nodeها یک‌بارمصرف‌اند، از image نسخه‌دار بازساخته می‌شوند — هرگز دستی patch نشوند. یک agent محلی سبک desired state را از git می‌کشد و reconcile می‌کند حتی وقتی control plane در دسترس نیست.
- **نگاشت به B:** یک Pi مرده را در چند دقیقه از golden image reflash کن به‌جای debug کردن snowflake.
- **هزینه:** M (پایپ‌لاین image + agent pull-reconcile per-node — **نه** k8s/Rancher Fleet که تلهٔ datacenter-weight است).
- **Verdict:** **PROTOTYPE** — ذهنیت را الان بگیر، ابزار را تدریجی.

---

## کاندیدهای FOLLOW (خوراک سنتز)

- **ISO 13850 + IEC 60204-1** — spec canonical kill-switch (stop categories، de-energize، manual reset).
- **IEC 61508 / 61511** — دکترین «لایه ایمنی جدا» برای طراحی kernel.
- **US AFI 91-104 + AWS Multi-party approval** — پل هسته‌ای→نرم‌افزار برای گیت HITL.
- **Russ Cox / Go `sumdb` & Trillian** — طراحی transparent-log تولیدی؛ پیاده‌سازی مرجع C8–C9.
- **Certificate Transparency / RFC 9162 (CT v2)** — جانشین 6962؛ الگوهای witness/gossip (توجه: Let's Encrypt لاگ‌های نسل 6962 را بازنشسته می‌کند → v2 را دنبال کن).
- **NDSA Levels + OAIS (ISO 14721/16363)** — نردبان بلوغ fixity/replication/جداسازی-کنترل.
- **Cloudflare eng blog (Code Orange)** — config-as-code درست در مقیاس.
- **Eclipse Ditto / HiveMQ + balena/Mender** — twin self-hosted + OTA A/B اندازهٔ SBC.

## GAPS — فرضیه‌های قابل‌جستجو

1. آیا solo operator می‌تواند استقلال two-person را معنادار برآورده کند، یا به two-factor تنزل می‌کند (ریسک security-theater)؟
2. آیا TSA عمومی رایگان + gist دوره‌ایِ head برای non-repudiation در سطح CT کافی است؟ (فرضیه: C8+C9 با هم کافی‌اند.)
3. مسیر audit-trail اصلاحیه SEC 17a-4 (۲۰۲۳): WORM *یا* audit trail زمان‌دارِ کامل که بتواند اصل را *بازسازی* کند — آیا مسیر audit-trail بهتر به لاگ hash-chained نگاشت می‌شود؟ [اصلاحیه verify شد: https://www.sec.gov/investment/amendments-electronic-recordkeeping-requirements-broker-dealers]
4. Crosby & Wallach 2009 «Efficient Data Structures for Tamper-Evident Logging» — primitive append-proof زیر CT؛ برای پیاده‌سازی اندازهٔ SBC بخوان.
5. آیا Eclipse Ditto روی یک RK3588 قابل‌قبول اجرا می‌شود یا JVM-heavy است → جایگزین سبک aMQTT/NanoMQ shadow plugin؟ [روی Orange Pi 5 تست شود.]
6. مرجع «GitOps برای فلیت homelab <۵۰ node» با systemd + git-pull ساده (بدون k8s)؟
7. نرخ خطای approval-fatigue در HITL-ML (ادبیات human-factors) برای توجیه UX حالت sterile.
8. semantics سلامت DNP3/Sparkplug-B که ارزش قرض‌گرفتن روی MQTT ساده برای سلامت ماینر دارد؟

## CONTRADICTIONS — تنش‌های منبع

- **E-stop سخت‌سیم آنالوگ نرم‌افزاری تمیز ندارد.** اعتماد هستهٔ E-stop صنعتی این است که برق را *فیزیکی بیرون کامپیوتر* برمی‌دارد؛ kill-switch نرم‌افزاری همیشه روی همان بستری اجرا می‌شود که می‌خواهد متوقفش کند. بهترین ترجمه = lease/heartbeat fail-safe (ایجنت روی loss-of-credential می‌میرد)، ولی ضعیف‌تر از de-energization واقعی. اگر سیستم به سخت‌افزار/خرج واقعی دست می‌زند، یک عنصر واقعاً سخت‌سیم (رله/PDU فیزیکی که kernel کنترل کند) در نظر بگیر.
- **two-person در برابر solo operator.** قدرت دکترین *همان انسان دوم مستقل* است؛ «دو فاکتور» یک اپراتور تنها، منفعت قضاوت مستقل را حذف می‌کند (نقد Rosenbaum: فرآیند فقط دستور را authenticate می‌کند نه سلامت عقلش را). solo M-of-N، coercion/خطا را کم می‌کند نه بدقضاوتی را — به‌عنوان ریسک باقی‌مانده علامت بزن، نه حل‌شده.
- **fail-safe (de-energize) در برابر fail-operational.** ایمنی می‌گوید پیش‌فرض *stopped*؛ ولی مزرعهٔ ایجنت always-on حالاتی دارد که halt ناگهانی Cat-0 خودش پرهزینه است (نوشتن corrupt). حل: Cat-1 (توقف کنترل‌شده → halt) برای حالات graceful، Cat-0 برای اورژانس واقعی.
- **هزینه/فایده N-version/diversity محل بحث است** — خود ادبیات می‌گوید توافقی نیست که تنوع چقدر reliability می‌خرد؛ verifier متنوع را defense-in-depth بدان نه تضمین.
- **استقلال سخت‌افزاری black-box در برابر یک SBC:** اعتماد هوانوردی از ضبط‌کنندهٔ *فیزیکی جدا* است؛ SBC تنها دستگاه دوم ندارد، پس استقلال باید via anchoring بیرون-box سنتز شود (C8–C9)، نه سخت‌افزار. فقط *اصل* منتقل می‌شود.
- **WORM قانونی در برابر self-hosted:** WORM سبک-SEC رسانهٔ vendor گواهی‌شده/lock-in را می‌رساند؛ اصلاحیهٔ audit-trail ۲۰۲۳ عمداً این را شل می‌کند و trail زمان‌دارِ بازساخت‌پذیر را ترجیح می‌دهد — که self-hosted شدنی است.
- **«device shadow به cloud نیاز دارد» در برابر Ditto/aMQTT self-hosted** — به‌نفع self-host حل شد.
- **push فوری جهانی (نقطهٔ فروش اولیه Quicksilver) در برابر قطعی‌های ۲۰۲۵ خودش** — خود این حوزه حالا می‌گوید *سرعت بدون gating یک باگ است* که staging را حتی در مقیاس ریز تایید می‌کند.
- **Cattle-not-pets در برابر واقعیت سولار/قطع‌ووصل:** cattle خالص، re-provision فوریِ ارزان فرض می‌کند؛ روی node فیزیکی دور هنوز به store-and-forward + degraded-mode نیاز داری — پس B یک هیبرید cattle-mindset / pet-hardware است.

---
*مرحله بعد: سنتز نهایی (TOP BORROW CANDIDATES + WHO TO FOLLOW + GAPS + CONTRADICTIONS ادغام‌شده) در `SCOUT-SUMMARY.md`.*
