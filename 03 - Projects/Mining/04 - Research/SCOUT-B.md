---
type: research
project: "[[03 - Projects/Mining/PROJECT]]"
tags: [scout, mining, arm, rk3588, randomx, track-b]
status: done
created: 2026-07-03
updated: 2026-07-04
---

# SCOUT-B — الگوهای CPU/ARM Edge-Mining

> خروجی ترک B. baseline: فلیت SBC ناهمگون — Orange Pi 5 (RK3588: ۴×A76 + ۴×A55) + ESP32 برای مانیتور/امضا؛ لبه ساختاری = برق خیلی ارزان (<$0.05/kWh یا سولار)؛ استراتژی = ماین کوین‌های تازه‌لانچِ CPU/ARM-viable و hold بلندمدت؛ solo operator.
> روش: ۴ ایجنت موازی، ~۴۰ جستجو، ~۴۰ منبع اولیه. تگ‌ها مثل SCOUT-A. **هیچ عدد hashrate بدون منبع نیامده؛ اعداد بی‌منبع در GAPS.**

## خلاصه اجرایی — پنج حقیقت که استراتژی ما را جهت می‌دهند

1. **RandomX روی RK3588 محدودِ پهنای‌باند حافظه است، نه compute.** بزرگ‌ترین اهرم‌های per-watt به‌ترتیب: (۱) انتخاب الگوریتم، (۲) سرعت RAM، (۳) huge pages. هسته A76 خیلی زود اشباع می‌شود.
2. **لبه واقعی ما H/s-per-watt است، نه H/s-per-core.** ARM per-core خیلی از x86 عقب‌تر است (~۲۶۰ H/s هر thread فست ARM در برابر ~۶۰۰–۷۰۰ x86). این استراتژی فقط وقتی برق تقریباً رایگان (سولار) است معنا دارد — که دقیقاً لبه ماست.
3. **MSR mod (بزرگ‌ترین برد RandomX روی x86) روی ARM وجود ندارد.** بن‌بست مستند؛ وقت نگذاریم.
4. **تنوع «هم‌ریگ» رایگان است:** Tari با merge-mining روی همان RandomX هم‌زمان با Monero ماین می‌شود → یک دارایی جدید با هزینه hashpower نهاییِ صفر. قوی‌ترین کاندید mine-and-hold.
5. **RandomX دیگر «ضدASIC مطلق» نیست** (Bitmain X5/X9 در ۲۰۲۴–۲۶). برای دوامِ CPU، yespower/yescrypt/GhostRider رتبه بالاتری از RandomX دارند. ادعای «RandomX = CPU-only» روی کوین جدید = پرچم زرد.

---

## کارت‌های الگو

### گروه ۱ — hashrate-per-watt روی RK3588

#### B1. Huge Pages (به‌ویژه 1GB pages)
- **Track:** B
- **Source:** xmrig RandomX optimization guide + hugepages doc — https://xmrig.com/docs/miner/randomx-optimization-guide · https://xmrig.com/docs/miner/hugepages [Verified]
- **مسئله:** dataset دو گیگی RandomX با page معمولی، TLB را می‌کوبد.
- **برتری:** hashrate-per-watt — huge pages معمولی تا **+۵۰٪** RandomX؛ `"1gb-pages": true` (فقط لینوکس، ۳GB آزاد لازم) **+۱–۳٪** بیشتر. صفر وات اضافه (نرم‌افزار خالص).
- **Portability:** S — `hugepages` در cmdline کرنل + فلگ config. روی بردهای ۸GB جا می‌شود؛ بردهای ۴GB نمی‌توانند ۳GB بدهند [GAP].
- **License/Lock-in:** GPLv3 (xmrig).
- **Verdict:** **BORROW NOW** — احتمالاً بزرگ‌ترین برد منفرد RandomX، مجانی.

#### B2. RAM OC (LPDDR5→6400) + CPU OC (2.4GHz) روی RK3588
- **Track:** B
- **Source:** sbcwiki — https://sbcwiki.com/news/articles/tune-your-rk3588 (Apr 2025) [Verified]
- **مسئله:** سقف پهنای‌باند حافظه، گلوگاه RandomX است.
- **برتری:** hashrate-per-watt — overlay‌های Armbian: `rockchip-rk3588-dmc-oc-3500mhz` + ابزار RKDDR (Hbiyik) برای بردن LPDDR5 از ۵۵۰۰ به ۶۴۰۰ MT/s؛ OC حافظه در وات تقریباً صفر، H/s را بالا می‌برد (+۴۰٪ در بنچ‌های حافظه؛ دلتای مخصوص RandomX اندازه‌گیری‌نشده [GAP]). OC پردازنده در ولتاژ ثابت ۱.۰۵V تقریباً per-watt خنثی ولی raw H/s بالا.
- **Portability:** M — برد LPDDR5 لازم است (نه Orange Pi 5 پایهٔ LPDDR4X) + ویرایش device-tree.
- **License/Lock-in:** overlayهای OSS.
- **Verdict:** **BORROW NOW** (RAM OC) / **PROTOTYPE** (CPU OC).

#### B3. فقط ۴ هسته A76 را ماین کن (A55 را رها کن)
- **Track:** B
- **Source:** xmrig benchmark ARM Cortex-A76 — https://xmrig.com/benchmark?cpu=ARM+Cortex-A76 [Verified] (A55 ~۴× کندتر از A76)
- **مسئله:** هسته‌های A55 H/s کم اضافه می‌کنند ولی برای L3/باس حافظه رقابت و وات مصرف می‌کنند.
- **برتری:** hashrate-per-watt — pin کردن threadها به A76 (affinity mask) وات و cache-thrash را کم می‌کند به قیمت افت کوچک raw H/s. دلتای دقیق A76-only اندازه‌گیری‌نشده [GAP/CONTRADICTION: گزارش «۱۰۰۰ H/s روی ۵ هسته» یعنی little-coreها هم کمک می‌کنند].
- **Portability:** S.
- **License/Lock-in:** GPLv3.
- **Verdict:** **PROTOTYPE** — A/B تست ۴×A76 در برابر همه‌۸ برای H/s-per-watt روی برد خودت.

#### B4. self-compile با GCC جدید + -mcpu=cortex-a76
- **Track:** B
- **Source:** github.com/auto-joe/oPi-xmrig-gcc7.3.0 (+~۱۴٪ از GCC6→7 روی Orange Pi Zero قدیمی) [Verified] · github.com/DocDrydenn/xmrig-build (اسکریپت build از سورس ARMv8) [Verified]
- **مسئله:** باینری‌های ARMv8 جنریک، از افزونه‌های crypto برد استفاده نمی‌کنند.
- **برتری:** hashrate-per-watt (همان وات، H/s بیشتر) — build روی خود دستگاه با `-mcpu=cortex-a76` + ARMv8.2 crypto. برد تاریخی GCC ۱۰–۱۵٪؛ مقدار روی RK3588 با GCC مدرن نامعلوم [GAP].
- **Portability:** S–M (یک‌بار compile per board).
- **License/Lock-in:** GPLv3 / اسکریپت MIT.
- **Verdict:** **BORROW NOW** — همیشه self-compile؛ upside ارزان.

#### B5. governor=performance (کشتن throttling DVFS)
- **Track:** B
- **Source:** github.com/bokiko/Verus-ARM64-Mining (فیکس «hashrate پایین» = `cpufreq-set -g performance`) [Verified]
- **مسئله:** ondemand/schedutil زیر بار ماین طولانی، کلاک را افت می‌دهد.
- **برتری:** maintainability + H/s پایدار — **نه per-watt** (performance با نگه‌داشتن ولتاژ بالا می‌تواند efficiency را بدتر کند → با undervolt جبران شود). با خنک‌کاری واقعی جفت شود (Rock 5B تا ۷۷°C passive → ریسک throttle).
- **Portability:** S.
- **License/Lock-in:** MIT.
- **Verdict:** **BORROW NOW** برای پایداری H/s؛ قبل از اعتماد برای efficiency، وات را اندازه بگیر.

#### B6. VerusHash روی ARM64 (سوییچ الگوریتم) — احتیاط منبع
- **Track:** B
- **Source:** ابزار: github.com/Oink70/Android-Mining (ccminer بهینه ARM64) [Verified] · github.com/bokiko/Verus-ARM64-Mining [Verified]. اعداد: growingdefi.com / medium (bloodys) — **[Unverified: بدنه صفحه رندر نشد؛ ~6.75 MH/s @ ~8W روی Orange Pi 5 فقط از extraction جستجو]**
- **مسئله:** RandomX روی این سیلیکون در لیگ efficiency پایین‌تری است.
- **برتری:** hashrate-per-watt — VerusHash محدودِ CPU است (با کلاک A76 مقیاس می‌گیرد نه RAM)، وات کمتر (~۸W در برابر ~۱۴W)، بدون dataset دو گیگی. **اما کوین متفاوت است (VRSC)، نه XMR.**
- **Portability:** S — Oink70 ccminer عملاً build مرجع ARM64.
- **License/Lock-in:** MIT.
- **Verdict:** **PROTOTYPE** — اگر کوینِ تازه‌لانچِ خانواده VerusHash با تز hold جور شد، بهترین مسیر per-watt. **اول عدد را روی برد خودت verify کن.**

#### B7. MSR mod روی ARM وجود ندارد (نتیجه منفی)
- **Track:** B
- **Source:** xmrig MSR doc — https://xmrig.com/docs/miner/randomx-optimization-guide/msr [Verified]
- **برتری:** —
- **Verdict:** **SKIP** — بن‌بست مستند؛ «FAILED TO APPLY MSR MOD» روی RK3588 نرمال است. معادل ARM = همان اهرم‌های huge-pages/RAM.

### گروه ۲ — چشم‌انداز الگوریتم/کوین ۲۰۲۶

#### B8. RandomX — الگوریتم لنگر فلیت
- **Track:** B
- **Source:** github.com/tevador/RandomX/blob/master/doc/design.md [Verified]
- **برتری:** correctness استراتژی — VM با زنجیره ۸ برنامه تصادفی (JIT به کد native)؛ dataset ۲۰۸۰MiB (fast/mining) vs cache ۲۵۶MiB (light/verify، عمداً ۸× کندتر). memory-hardness = مقاومت واقعی ASIC/FPGA/GPU. **جالب: طراحی صریحاً جدول latency هسته Cortex-A55 را ذکر می‌کند → ARM هدف طراحی بوده.**
- **Portability:** ≥۲.۵GiB RAM آزاد per node + AES سخت‌افزاری (افزونه crypto ARMv8) برای fast mode لازم. بردهای ۸/۱۶GB واجد شرایط؛ SBCهای زیر ۲GB و ESP32 رد.
- **Verdict:** **BORROW NOW** — RandomX لنگر فلیت.

#### B9. Tari (XTM) — RandomX merge-mined + SHA3x
- **Track:** B
- **Source:** theblock.co/post/353240 + chainwire (mainnet 2025-05-06) [Verified]؛ لیست XT.com [Unverified]
- **برتری:** mine-and-hold (قوی‌ترین کاندید) — mainnet می ۲۰۲۵ از مشارکت‌کنندگان سابق Monero؛ **merge-mined با Monero** یعنی XMR + XTM را هم‌زمان با هزینه hashpower نهاییِ صفر ماین می‌کنی. دقیقاً «ماین کوین جدید و hold».
- **Portability:** روی RK3588 (همان RandomX). هشدار: اپ دسکتاپ «Tari Universe» x86/Mac است؛ روی ARM از xmrig + pool merge-mining استفاده کن نه GUI.
- **Verdict:** **PROTOTYPE** — بالاترین سیگنال؛ اول verify کن poolـی merge-mining ARM/xmrig را ساپورت کند.

#### B10. Salvium (SAL) و Zephyr (ZEPH) — RandomX
- **Track:** B
- **Source:** livecoinwatch SAL + coingecko ZEPH [Verified]
- **برتری:** تنوع هم‌ریگ RandomX — هر دو زنجیره زنده روی codebase مونرو. Salvium hard fork فعال (Apr 2026، توکن/DeFi روی‌زنجیره)، ~$1.2M cap. Zephyr استیبل‌کوین خصوصی over-collateralized، محصول واقعی. **هر دو کم‌نقد = فقط hold، نه trade.**
- **Portability:** مثل Monero روی RK3588.
- **Verdict:** **WATCH → PROTOTYPE** — یک bag کوچک کنار XMR؛ نقدینگی برای بزرگ‌کردن کافی نیست.

#### B11. Wownero (WOW) — RandomWOW (scratchpad یک‌مگ)
- **Track:** B
- **Source:** wownero.org / cryptunit [Verified]
- **برتری:** hashrate-per-core روی ARM — **scratchpad یک‌مگی** (در برابر ۲ مگ Monero) در cache کوچک RK3588 (L2 ۲.۵MB / L3 ۳MB) بهتر جا می‌شود → H/s-per-core نسبتاً بالاتر و فشار RAM کمتر. راه acquire بدون exchange/KYC.
- **Portability:** عالی (RandomWOW در xmrig).
- **Verdict:** **PROTOTYPE** — بهترین واریانت RandomX برای cache محدود ARM.

#### B12. GhostRider (Raptoreum) و AstroBWTv3 (Dero)
- **Track:** B
- **Source:** xmrig ghostrider README + github.com/deroproject/astrobwt [Verified]؛ قیمت RTM [Unverified]
- **برتری:** دوام CPU — هر دو واقعاً non-ASIC/non-GPU-dominated. اما legهای CryptoNight در GhostRider cache-heavy (به‌نفع L3 بزرگ x86)؛ نقدینگی RTM اکنون **خیلی پایین** (~$0.0001، خروج سخت). ساپورت ARM64 برای AstroBWTv3 اثبات‌نشده [GAP].
- **Portability:** GhostRider روی ARM via xmrig ولی efficiency افت می‌کند (L3 کوچک).
- **Verdict:** **WATCH** — روی تز الگوریتمی درست، ولی احتیاط نقدینگی + efficiency ARM.

#### B13. خانواده yespower/yescrypt (لایه زیرِ RandomX، برای دستگاه‌های ریز)
- **Track:** B
- **Source:** github.com/yentencoin/yenten-arm-miner-yespowerr16 [Verified]؛ اعداد cpu-mining.info [Unverified]
- **برتری:** فوت‌پرینت — yespowerR16 فقط **~۴MB/thread** (در برابر ۲GB RandomX). این لایه‌ای است که **نیمه کم‌رمِ فلیت** می‌تواند لمس کند (RandomX آنجا اصلاً اجرا نمی‌شود). ماینر مخصوص ARM64 وجود دارد. اما بسیاری کوین‌های yespower نیمه‌مرده/کم‌نقدند.
- **Portability:** روی RK3588 و حتی SBCهای کم‌رم راحت. (خود ESP32 میکروکنترلر هنوز marginal است — verify شود.)
- **License/Lock-in:** cpuminer-opt/yespower = BSD/GPL، بدون dev fee.
- **Verdict:** **PROTOTYPE** روی لایه هسته‌کوچک — یک کوین yespower نقد انتخاب کن، زیاد سرمایه‌گذاری نکن.

### گروه ۳ — Orchestration فلیت (بهتر از SSH دستی)

#### B14. Tailscale (یا Headscale) به‌عنوان بستر mesh
- **Track:** B
- **Source:** tailscale.com/docs (free plan) [Verified] · github.com/juanfont/headscale (v0.28.0 Feb 2026، BSD-3، ۳۹.۶k★) [Verified]
- **مسئله:** SSH دستی به‌محض تغییر IP یا NAT اپراتور می‌شکند.
- **برتری:** robustness + maintainability — mesh وایرگارد با NAT traversal؛ هر node یک IP پایدار پشت CGNAT/لینک قطع‌ووصل. Tailscale SSH مدیریت کلید را حذف می‌کند (ACL-gated). free Personal ~۶ کاربر / دستگاه‌های شخصی عملاً نامحدود. **Headscale** = control-plane self-hosted بدون vendor (وقتی سقف ۶ کاربر یا وابستگی SaaS مشکل شد).
- **Portability:** S — daemon روی RK3588 راحت؛ **ESP32 کلاینت را نمی‌تواند اجرا کند** (via یک Pi/RK3588 به‌عنوان subnet router بریج شود).
- **License/Lock-in:** کلاینت OSS (BSD)؛ control-plane Tailscale proprietary/SaaS. جایگزین OSS: Headscale / NetBird.
- **Verdict:** **BORROW NOW** (Tailscale) — بزرگ‌ترین upgrade بر SSH دستی؛ / **PROTOTYPE** (Headscale).

#### B15. pyinfra روی mesh (config/exec بدون agent)
- **Track:** B
- **Source:** pyinfra.com (v3، MIT، ۵.۷k★) [Verified]
- **مسئله:** «SSH به هر باکس و paste» نه versioned است نه idempotent.
- **برتری:** maintainability — Python-native، agentless، تنها نیاز host یک shell است (حتی Python هم نه)، idempotent، `--dry` diff، concurrent؛ ادعای ۶× سریع‌تر از Ansible و سبک‌تر روی RK3588 (Ansible روی target به Python نیاز دارد).
- **Portability:** S — هیچ‌چیز روی nodeها؛ از لپ‌تاپ روی ۵–۲۰ باکس ARM via Tailscale.
- **License/Lock-in:** MIT. جایگزین: Ansible (اکوسیستم بزرگ‌تر، Python روی target)؛ Salt در این مقیاس overkill.
- **Verdict:** **BORROW NOW** — «pyinfra روی Tailscale» از «Ansible روی Tailscale» برای این فلیت بهتر.

#### B16. XMRigCC — C2 مخصوص ماین (برای مورد RandomX)
- **Track:** B
- **Source:** github.com/Bendr0id/xmrigCC (v3.4.9، Jan 2026، GPL-3.0، ARMv8-native) [Verified]
- **مسئله:** بابیسیتینگ per-node ابزار xmrig با SSH.
- **برتری:** autonomy + maintainability — fork xmrig + سرور Command&Control self-hosted: start/stop/restart/**shutdown/reboot** از راه دور، config template روی همه ماینرها با یک کلیک، log viewer، upgrade از راه دور، **آلارم hashrate/offline via Telegram/Pushover** + daemon که ماینر را زنده نگه می‌دارد. «performance بهتر روی ARMv8».
- **Portability:** S — Linux/ARMv8 native؛ سرور C2 یک process کوچک. **Hive OS/minerstat = GPU/x86-محور، ساپورت ARM-SBC ضعیف → SKIP.**
- **License/Lock-in:** GPL-3، self-hosted، صفر.
- **Verdict:** **BORROW NOW** — نزدیک‌ترین چیز به مدیر فلیت ماین ARM؛ زیر Tailscale تمیز می‌نشیند. **مستقیم روی Mining-1 قابل اعمال.**

#### B17. Beszel — مانیتور فوق‌سبک
- **Track:** B
- **Source:** github.com/henrygd/beszel (v0.18.7، Apr 2026، MIT، ۲۱.۹k★) [Verified]
- **مسئله:** node داغ/هنگ را موقع SSH بعدی کشف می‌کنی نه لحظه وقوع.
- **برتری:** robustness — Hub (PocketBase) + agent ریز (~۱۰–۱۵MB RAM idle): CPU/mem/disk/net/temp، آمار Docker، **S.M.A.R.T شامل فرسایش eMMC** (مهم روی SBC)، آلارم. ~۱۰× سبک‌تر از Prometheus+node_exporter+Grafana.
- **Portability:** S — طراحی‌شده برای homelab/SBC.
- **License/Lock-in:** MIT.
- **Verdict:** **BORROW NOW** — مانیتور پیش‌فرض ۱–۲۰ SBC؛ آلارم فرسایش eMMC یک برد واقعی.

#### B18. systemd watchdog + power-cycle (self-healing)
- **Track:** B
- **Source:** redhat.com/blog/systemd-automate-recovery [Unverified] · PoE watchdog [Unverified]
- **مسئله:** kernel lockup را نرم‌افزار نمی‌تواند فیکس کند.
- **برتری:** autonomy — دولایه: نرم `Restart=on-failure`/`on-watchdog` + `WatchdogSec` (heartbeat sd_notify)؛ سخت PoE-switch/smart-plug که ping می‌زند و برق را cut+restore می‌کند روی هنگ واقعی. بازیابی بدون SSH اپراتور.
- **Portability:** S — systemd روی هر SBC هست؛ PoE/smart-plug سخت‌افزار ارزان.
- **License/Lock-in:** OSS native + سخت‌افزار commodity.
- **Verdict:** **BORROW NOW** — ارزان‌ترین دلتای robustness؛ ماینر را همین امروز `Restart=` unit کن.

#### B19. ESPHome fleet + OTA برای لایه ESP32
- **Track:** B
- **Source:** esphome.io/guides/cli + changelog 2026.5.0 [Unverified]
- **مسئله:** برای میکروکنترلر «SSH» وجود ندارد.
- **برتری:** maintainability — YAML اعلانی per device؛ `esphome update-all` کل ESP32ها را compile+OTA-flash می‌کند و pass/fail per-device می‌دهد. تله‌متری via API/MQTT به Home Assistant. برای لایه MCU اکیداً بهتر از baseline.
- **Portability:** S — HA/ESPHome روی یک node RK3588 به‌عنوان مغز MCU فلیت.
- **License/Lock-in:** OSS (MIT/GPL).
- **Verdict:** **BORROW NOW** — پاسخ canonical «مدیریت چندین ESP32 از راه دور».

### گروه ۴ — چارچوب scouting کوین جدید

> **پایپ‌لاین: کشف → طبقه‌بندی الگوریتم → غربال بقا/rug → ارزیابی نقدینگی/خروج.** هیچ ابزار واحدی هر ۴ مرحله را نمی‌کند؛ هر مرحله feed مشخص و automatable دارد.

#### B20. bitcointalk Altcoin boards — شیلنگِ آتشِ لانچ (مرحله کشف)
- **Track:** B
- **Source:** bitcointalk.org board=160.0 (Mining Altcoins) + board=159.0 (Announcements) [Verified]
- **برتری:** freshness — نقطه مبدأ threadهای ANN کوین CPU، **قبل از اینکه هر aggregatorـی index کند**. snapshot ژوئن ۲۰۲۶: لانچ‌های تازه (Block Zero RandomX، QUB، Dilithion…) + دو thread ماینر مهم ARM: **cpuminer-opt v26.1 «x86_64 and AArch64» (JayDDee)** و SRBMiner.
- **Portability:** M — بدون API ولی HTML استاتیک، trivially scrapeable/RSS؛ board ID پایدار (159، 160).
- **License/Lock-in:** رایگان، بدون key.
- **Verdict:** **BORROW NOW** — هر دو board را poll کن؛ thread ماینر AArch64 هم‌زمان ground-truthِ «آیا ARM-runnable هست».

#### B21. MiningPoolStats /newcoins — تریاژ الگوریتم+pool
- **Track:** B
- **Source:** miningpoolstats.stream/newcoins + /calendar [Verified]
- **برتری:** کشف + بقای اولیه — لیست خودکار «New PoW Coins» با Algorithm، Age، Height، Poolهای شناخته، Network Hashrate. ستون pool اجازه می‌دهد زنجیره بدون pool (پرچم قرمز) را پیش‌فیلتر کنی.
- **Portability:** M — بدون API رسمی، صفحه JS-rendered (headless scrape)، ولی بهترین board رایگان by-algorithm.
- **License/Lock-in:** رایگان.
- **Verdict:** **BORROW NOW** — تریاژ «کوین هست + pool دارد + کدام الگو» در یک ویو.

#### B22. minerstat API — feed ساخت‌یافته (طبقه‌بندی + بقا)
- **Track:** B
- **Source:** api.minerstat.com/docs-coins [Verified]
- **برتری:** classify — سه API مستند JSON: Coins (الگوریتم، هش‌ریت شبکه، difficulty، قیمت، حجم)، Pools، **Hardware** (کدام ASIC/GPU per algorithm — فیچر قاتل: کوئری الگو → اگر ASIC/GPU لیست شد یعنی «مخفیانه CPU نیست»). ستون profit-switch/scoring خودکار.
- **Portability:** S/M — API درست ولی gated: اکانت dev + اشتراک پولی، ~۱۲ req/min، quota ماهانه.
- **License/Lock-in:** tierهای پولی، attribution لازم.
- **Verdict:** **PROTOTYPE** — بهترین feed ساخت‌یافته؛ تنها اصطکاک، cost-gate.

#### B23. جدول مرجع طبقه‌بندی الگوریتم (قاعده تصمیم)
- **Track:** B
- **Source:** openwall.com/yespower + coinguides.org/yescrypt-algorithm-coins + blockspot.io/algorithm/ghostrider [Verified]
- **برتری:** ارزان‌ترین اتوماسیون با بالاترین اهرم — نگاشت الگوی کوین جدید → {yespower/yescrypt/GhostRider = CPU-leaning؛ Ethash/KawPow/SHA256/Scrypt/Autolykos = نه}. لیست allow/deny استاتیک. **هشدار: RandomX دیگر امن‌ADSIC نیست (Bitmain X5 ۲۱۲kH/s / X9 ~۱MH/s شیپ‌شده ۲۰۲۴–۲۶) → RandomX ریسک algo-change + ASIC crowd-out دارد که yespower/GhostRider ندارند.**
- **Portability:** S — جدول lookup کوچک.
- **License/Lock-in:** رایگان.
- **Verdict:** **BORROW NOW**.

#### B24. CryptoMiso — رتبه‌بندی commit گیت‌هاب (غربال بقا/rug)
- **Track:** B
- **Source:** cryptomiso.com [Verified]
- **برتری:** survival screen — رتبه کوین‌ها بر اساس فعالیت commit (۳/۱۲ ماه)؛ مستقیماً پرچم «کد = fork آشکار با find-replace» و «تک‌dev، repo مرده» را می‌زند. commit کم/تک‌مؤلف/کهنه = سیگنال دوام‌نداشتن.
- **Portability:** M — ابزار وب، scrapeable؛ مکمل چک دستی گیت‌هاب (آیا کامپایل می‌شود، آیا clone بیت‌کوین/مونرو با string عوض‌شده).
- **License/Lock-in:** رایگان.
- **Verdict:** **BORROW NOW** — پروکسی عینی طول عمر زنجیره.

#### B25. GeckoTerminal Rug Checker + CoinGecko onchain (نقدینگی/خروج)
- **Track:** B
- **Source:** geckoterminal.com/rug-checker + coingecko onchain DEX API [Verified]
- **برتری:** exit-risk gate — Security Score روی ۲۵۰+ زنجیره (قفل نقدینگی، هولد سازنده، mint/freeze authority، honeypot). CoinGecko Onchain «Pools Megafilter» با honeypot detection + locked-liquidity روی **tier رایگان Demo** (۱۰۰ call/min). پاسخ «آیا کوین ماین‌شده اصلاً قابل فروش است یا honeypot/unlisted/wash-traded».
- **Portability:** S — API رایگان؛ DEXScreener بدون key.
- **License/Lock-in:** tier رایگان سخاوتمند.
- **Verdict:** **BORROW NOW** — گیت ریسک خروج که اکثر scoutها رد می‌کنند. (برای micro-listing صرفاً-CEX از مقایسه حجم cross-exchange کوین‌گکو/کوین‌پاپریکا استفاده کن.)

---

## کاندیدهای FOLLOW (خوراک سنتز)

- **SChernykh** (github.com/SChernykh) — dev هسته xmrig + هم‌طراح RandomX؛ محرک ARM64 JIT و هر برد efficiency.
- **tevador** (github.com/tevador) — نویسنده RandomX؛ منتظر RandomX v2/جانشین.
- **JayDDee (cpuminer-opt)** — نگه‌دار ماینر CPU AArch64؛ لیست الگوهای ساپورت‌شده‌اش ≈ جهان عملی کوین‌های ARM-mineable.
- **Oink70 / bokiko** — build مرجع ccminer ARM64 + wrapperهای RK3588.
- **BenDr0id (XMRigCC)** — تنها C2 ماین ARM-aware فعال.
- **henrygd (Beszel)** + **juanfont (Headscale)** — baseline سبک مانیتور/mesh.

## GAPS — فرضیه‌های قابل‌جستجو

1. دلتای H/s واقعی RandomX از LPDDR5-6400 OC روی RK3588 بدون منبع — فرضیه: memory-bound → شاید +۱۰–۲۵٪، بنچ لازم.
2. اعداد «~۱۰۰۰ H/s RandomX» و «۳× کارآمدتر از Ryzen 3900X روی Verus» فقط search-extracted — تا بنچ اولیه [Unverified].
3. عدد H/s برای yespower/GhostRider/Argon2 **مخصوص RK3588** پیدا نشد (جدول cpu-mining.info همه x86).
4. ساپورت AstroBWTv3 روی ARM64/RK3588 — بنچ نیست؛ جستجو: `astrobwt aarch64 benchmark RK3588`.
5. آیا poolـی merge-mining Tari↔Monero سازگار با ARM/xmrig هست (در برابر GUI فقط-x86)؟
6. viability هر PoW روی خود ESP32 (نه SBC) — مشکوک فقط الگوهای trivial؛ ESP32 احتمالاً node سنسور/کنترل است نه ماینر.
7. openBalena روی RK3588 — balena **ساپورت رسمی Orange Pi 5 ندارد**؛ آیا BSP جامعه کارآمد هست؟
8. RAUC vs Mender برای OTA اتمیک A/B روی RK3588 با U-Boot mainline ۲۰۲۵–۲۶.
9. premine/instamine % توسط هیچ API افشا نمی‌شود — دستی از ANN/explorer؛ automation از scraping explorer آزمایش‌نشده.
10. مدل کمّی «بقا در ۱–۳ سال» وجود ندارد — commit+pool-count+exchange-count پروکسی‌اند؛ **فرضیه: خودِ این چارچوب یک سنتز نوآورانهٔ قابل‌انتشار است.**

## CONTRADICTIONS — اختلاف منابع معتبر

- **هش‌ریت RandomX روی RK3588:** Rock 5B **۷۳۰ H/s @ ۱۴W** (forum Radxa، xmrigCC، Armbian/NVMe) [Verified] در برابر Orange Pi 5 **~۱۰۰۰ H/s روی ۵ هسته** (extraction فروم رزبری) [Unverified]. همان خانواده SoC، ~۳۷٪ فاصله — احتمالاً تفاوت thread-count/خنک‌کاری/tier حافظه. هر دو ارائه، حل‌نشده.
- **governor=performance:** bokiko برای max H/s توصیه می‌کند؛ ولی performance عموماً H/s-per-watt را در برابر setup undervolted DVFS **بدتر** می‌کند — تضاد «raw H/s» با «هدف per-watt».
- **«RandomX = CPU-only/ASIC-resistant»:** تاریخی درست و هنوز توسط لانچ‌های جدید تکرار می‌شود (Dilithion ANN مارس ۲۰۲۶ صریحاً «RandomX CPU only») ولی برای ۲۰۲۶ **منسوخ**: ASICهای Bitmain X5/X9 شیپ شدند. پیامد: ادعای RandomX روی کوین جدید = پرچم زرد؛ yespower/yescrypt/GhostRider را روی محور دوام CPU بالاتر رتبه بده.
- **k3s/k0s در لبه:** طرفداران RK3588 vs اردوگاه «برای فلیت solo خیلی سنگین» — اعداد ۲۰۲۶ طرف شکاک را تایید می‌کنند (k0s ~۶۵۸MB / k3s ~۷۵۰MB RAM control-plane). **Verdict: SKIP k8s اینجا** — container-OTA یا systemd ساده همان سود را بدون وزن می‌دهد.
- **تصحیح‌ها:** «Zano/yespowerZANO» **غلط** — Zano = ProgPoWZ (GPU). «Nexa» **غلط** — GPU. هر دو برای فلیت ARM رد. «Tari CPU-mined؟» **بله تایید شد**.
- **aggregator vs حقیقت:** CoinGecko/CoinPaprika تمیزتر ولی micro-cap CPU را lag می‌کنند؛ bitcointalk اول ولی noisy. هیچ منبع هم‌زمان fresh+ساختاریافته+تمیز نیست — پایپ‌لاین باید هر دو را fuse کند.

---
*مرحله بعد طبق پرامپت: Track C (Adjacent-Field Borrowing) پس از تایید مالک.*
