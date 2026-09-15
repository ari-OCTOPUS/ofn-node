# ACTIONS-LOG — تغییرات این جلسه + برگشت
**تاریخ:** 2026-09-15 · همهٔ تغییرها با تأیید صریح مالک انجام شد

---

## A1 — حذف کامل استک ماینینگ از `.100` و `.160`
**تأیید مالک:** «همه‌چیز را کامل پاک کن»

**چرا:** ماینینگ **صفر** بوده. شواهد:
- `grep -icE "block.*(success|found|mined|mint)"` روی کل `fullnode.log` ⇒ **۰ بلوک**
- نود از ۱۶ آپریل هیچ peer عمومی نگرفته: کنسول `P2P peers:` خالی، تیپ زنجیره `height 738143 time 2026-04-16`
- ۱۱۸۳۷ تلاش اتصال، همیشه `total 1 public 0 subnet`
- ماینر تخمین می‌زند **۰.۰۲ HAC در روز** با احتمال موفقیت ۰.۰۸۶٪
- **هیچ کیف پولی روی بردها نیست** (`/opt/hacash/data` خالی، `find / -iname "*wallet*"` چیزی نیافت) ⇒ فقط یک آدرس reward، بدون کلید خصوصی. پس حذف هیچ پولی را از بین نمی‌برد.
- `tdc_miner` (Tidecoin) هم از قبل شکسته بود: `status=203/EXEC` چون باینری `xmrig` قبلاً حذف شده بود.

**انجام‌شده:**
| برد | stop+disable | حذف‌شده | فضای آزادشده |
| :--- | :--- | :--- | :--- |
| `.100` | `hacash-fullnode`, `tdc_miner` | `/opt/hacash` (822M)، unitها، `hacash-health.sh`، کرون | ۸۲۲ مگ |
| `.160` | `hacash-miner` | `/opt/hacash` (126M)، unitها، `wait-for-master.sh` | ۱۲۶ مگ |

**تأیید شد:** `/opt/hacash` دیگر وجود ندارد؛ `systemctl list-unit-files | grep hacash` خالی؛ helperها رفته‌اند.
**ثبت:** کانفیگ‌ها، unitها و اسکریپت‌ها در `removed-hacash-record/` همین پوشه نگه داشته شدند.

**ROLLBACK:** غیرممکن برای باینری‌ها — ولی همه‌چیز از سورس قابل ساخت مجدد است و کانفیگ‌ها/unitها ضبط شده‌اند.
اگر لازم شد: کانفیگ‌ها را از `removed-hacash-record/` برگردان، سپس بر اساس
`03 - Projects/Mining/03 - Rigs/Mining-1/Hcash/` دوباره build کن.

---

## A2 — ساخت swap روی `182` برای قطع حلقهٔ OOM
**تأیید مالک:** «swap بساز تا حلقه قطع شود»

**چرا:** سرویس `octopus-sensorium` هر ~۱۵ ثانیه OOM می‌خورد و ری‌استارت می‌شد.
خط پایه قبل از تغییر: **`NRestarts=98`** و هیچ‌وقت به `READY` نمی‌رسید.
علت: برد ۳.۹ گیگ رم، **swap صفر**، سرویس سقف `MemoryMax=2G` و `MemorySwapMax=infinity`.

**انجام‌شده:**
- `fallocate -l 2G /swapfile` + `mkswap` + `swapon`
- یک خط `nofail` به `/etc/fstab`: `/swapfile none swap sw,nofail 0 0`
- از `/etc/fstab` نسخهٔ پشتیبان گرفته شد: `/etc/fstab.pre-swap-<timestamp>`
- `findmnt --verify` تمیز است (فقط هشدار `daemon-reload`)

**نتیجهٔ اندازه‌گیری‌شده (۱۵۰ ثانیه پایش):**
```
خط پایه:            NRestarts=98
t+ 30s  active     NRestarts=0   swap_used=826MB
t+ 60s  active     NRestarts=0   swap_used=340MB
t+ 90s  active     NRestarts=0   swap_used=751MB
t+120s  active     NRestarts=0   swap_used=930MB
t+150s  active     NRestarts=0   swap_used=701MB
Status: runtime=ACTIVE readiness=READY/WAVE0_OBSERVE_ONLY bus=CONNECTED
```
**هیچ OOM و هیچ ری‌استارتی رخ نداد و سرویس به `READY` و `bus=CONNECTED` رسید.**

**ROLLBACK:** `swapoff /swapfile && rm /swapfile` و حذف خط از `/etc/fstab`
(یا بازگرداندن `cp /etc/fstab.pre-swap-* /etc/fstab`).

---

## A3 — نوشتن ایمیج Pro روی کارت ۱۲۸ گیگِ داخل ۱۳۸
**چرا:** مالک کارت ۱۲۸ را در ۱۳۸ گذاشت تا برای برد Pro آماده شود.

**دو نکتهٔ مهمی که حین کار پیدا شد:**
1. **کارت ۱۲۸ خراب بود.** `e2fsck -fn` گفت `Directory inode 15745 ... directory corrupted`
   و abort کرد؛ `/etc/fstab` کاملاً صفر شده بود و `/opt` خالی. پس محتوایش آشغال بود
   و از بین بردنش ضرری نداشت.
2. **اولین تلاش نوشتن صفر بایت نوشت** چون `xz` روی ۱۳۸ **نصب نیست** —
   اسکریپت `write-pro-card.sh` از `xz -dc` استفاده می‌کرد. با `flash.py` مبتنی بر
   `lzma` پایتون جایگزین و دوباره اجرا شد. **`write-pro-card.sh` هم باید به همین شکل اصلاح شود.**

**تأیید بوت‌لودر روی کارت:**
```
sector 64    : 52 4b 4e 53 ...   <- RKNS idbloader  ✓
sector 16384 : d0 0d fe ed ...   <- FIT / u-boot    ✓
mmcblk1p1    : ext4, PARTLABEL="root"
```

**ROLLBACK:** کارت را دوباره فرمت/نوشتن کن؛ محتوای قبلی‌اش خراب بود و ارزشی نداشت.

---

## A4 — تشخیص: کارت ۱۲۸ سالم است، اسلات `182` خراب است
مالک کارت را از ۱۸۲ درآورد و در ۱۳۸ گذاشت ⇒ **۱۳۸ کارت را درست شناخت.**
پس خودِ کارت از نظر الکتریکی خوانده می‌شود و مشکل، **اسلات SD برد ۱۸۲** است
(کنترلر سه سرعت را امتحان می‌کند و بعد باس را خاموش می‌کند: `clock 0 Hz`, `power mode off`).
این بهترین توضیح موجود برای کرش‌های hot-plug روی ۱۸۲ هم هست.

**نتیجه:** برای بردهای بعدی، کارت را در ۱۸۲ نگذار. اسلات ۱۸۲ تا تعمیر/بررسی، قابل اعتماد نیست.

---

## A5 — 🔴 کارت ۱۲۸ حین کار **مرد**. باید فیزیکی از ۱۳۸ بیرون بیاید.

نوشتن **موفق بود** (`WROTE_BYTES 817701376` — دقیقاً اندازهٔ درست)، ولی بلافاصله بعدش کارت از کار افتاد:

```
mmc1: tried to HW reset card, got error -110
mmcblk1: recovery failed!
I/O error, dev mmcblk1, sector 0 op 0x0:(READ)
mmc_host mmc1: Timeout sending command (cmd 0x202000 ...)
mmc1: card never left busy state
```
- خواندن ۴ مگابایت **۲۸.۷ ثانیه** طول کشید (کارت سالم این را در چند صدم ثانیه می‌خواند)
- `blkid /dev/mmcblk1p1` دیگر هیچ خروجی نمی‌دهد ⇒ فایل‌سیستم ناخواناست
- چند پروسه از دستورهای من در حالت **D** گیر کردند: `sed`، `partprobe`، و `udev-worker`
  (kill -9 هم آنها را آزاد نکرد — تا کارت فیزیکی برداشته نشود آزاد نمی‌شوند)

**وضعیت ۱۳۸:** سالم است. `dd` روی eMMC با **۲۹۷ MB/s** خواند، هیچ ری‌استارتی نداده
(uptime پیوسته)، و **هر ۸ سرویس ارگانیسم بالاست** (bridge, control-router, cycle-settler,
router, supervisor, verify-dispatcher, …). کارت unmount شده و هیچ پروسه‌ای رویش نمی‌نویسد.

**پس این کارت دور انداختنی است.** کارت اول هم فایل‌سیستش خراب بود (`directory corrupted`)،
حالا هم فیزیکی مرد ⇒ **این کارت هرگز نباید روی برد جدید برود.**

---

## A6 — نقشهٔ اصلاح‌شده (چون کارت ۱۲۸ مرد)

| برد هدف | کارت لازم | وضعیت الان |
| :--- | :--- | :--- |
| **Plus** | کارت ۳۲ گیگ با ایمیج Armbian Plus + کلید | ✅ آماده است — **ولی الان داخل برد Pro است** |
| **Pro** | کارتی با ایمیج DietPi Pro | ❌ نداریم — کارت ۱۲۸ مرد |

**حرکت‌های فیزیکی لازم:**
1. 🔴 **کارت ۱۲۸ مرده را از ۱۳۸ بیرون بیاور** (پروسه‌های گیر فوراً آزاد می‌شوند).
2. **کارت ۳۲ گیگ را از برد Pro بردار و در برد Plus بگذار** — الان در برد اشتباه است
   و چون ایمیجش Plus است، برد Pro با آن بالا نمی‌آید.
3. **کارت microSD دیگرت را در ۱۳۸ بگذار** تا ایمیج Pro را رویش بنویسم
   (اسکریپت `write-pro-card.sh` اصلاح شد؛ اولین تلاش صفر بایت نوشت چون `xz` روی ۱۳۸ نصب نیست).

**نکته:** قبل از نوشتن روی کارت دیگر، اول با `sudo e2fsck -fn /dev/mmcblk1p1` سلامت آن را چک می‌کنم
تا دوباره روی کارت در حال مرگ وقت تلف نشود.

---

## A7 — 🎉 برد Plus بالا آمد و همه به مِش وصل شدند
**تأیید مالک:** «همرو بیا وصل کنیم به اختاپوس بفهمه دارتشون»

**برد جدید:** `192.168.0.194` — `Orange Pi 5 Plus`، Armbian 25.11.1، با کلید تزریق‌شده وارد شدم.
(on SD بوت شده: `findmnt /` ⇒ `/dev/mmcblk1p1`)

**کارت مرده از ۱۳۸ بیرون رفت** ⇒ پروسه‌های گیر آزاد شدند و load از **۶.۰ به ۱.۰۶** برگشت.

**ثبت در `~/octopus-mesh/config/nodes.json`** (کامیت `93fa88dc1` در ریپوی مِش):

| نود | نقش | رمز وضعیت |
| :--- | :--- | :--- |
| 100 | `compute-node` | از ماینینگ آزاد شد، load 0.00 |
| 160 | `compute-node` | از ماینینگ آزاد شد، load 0.00 |
| 194 | `model-server` | برد Plus جدید |
| 182 | `lab-witness` | **`retired` به false تغییر کرد** (تصمیم جدید مالک، Supersede تصمیم ۰۹-۰۴) |

نکات رعایت‌شده:
- `may_authorize` روی **همه** `false` ماند (طبق AGENTS.md بند ۵)
- entry نود ۱۸۲ **حذف نشد** چون کامیت قبلی هشدار داده بود
  `octomesh_agent_bridge transmit()` روی حذف KeyError می‌دهد
- از `nodes.json` نسخهٔ پشتیبان گرفته شد: `config/nodes.json.bak-<ts>`
- کلید مِش روی هر سه نود نصب شد؛ CR فایل `authorized_keys` پاک شد (traپ CRLF)
- `hostnamectl` روی `.100/.160` کار نکرد (dbus روی SSH خراب است) ⇒ مستقیم `/etc/hostname` نوشتم
- از ۱۳۸ با کلید identity، **هر ۵ نود جواب دادند** (`compute-100`, `compute-160`,
  `model-plus-194`, `sensorium-opi5pro`, `octopus-continuity-180`)

**ROLLBACK:** `git revert 93fa88dc1` در `~/octopus-mesh`، یا بازگرداندن `config/nodes.json.bak-*`
و `rm /root/.ssh/authorized_keys` خط مِش را از نودهای جدید بردار.

---

## A8 — ⚠️ برد Plus **eMMC ندارد** — درخواست «فلش روی eMMC» فعلاً ممکن نیست

مالک گفت سیستم Plus به eMMC منتقل شود تا کارت SD آزاد شود. اندازه‌گیری روی خود برد:

```
lsblk            -> mmcblk1 (29.7G) = کارت SD  ·  mtdblock0 (16M) = SPI NOR
                    هیچ mmcblk0 وجود ندارد
dmesg            -> mmc0: SDHCI controller on fe2e0000.mmc   (کنترلر ثبت شد)
                    ولی هیچ chipی وصل نیست ⇒ هیچ دستگاه بلوکی ساخته نشد
/dev/nvme*       -> وجود ندارد (اسلات M.2 خالی است)
/proc/mtd        -> mtd0: 01000000 "loader"   (SPI NOR هست)
```
**یعنی:** کنترلر eMMC هست ولی **ماژول eMMC نصب نیست**؛ M.2 هم خالی است.
تنها حافظهٔ پایدارِ در دسترس، همان کارت SD است (به‌علاوهٔ ۱۶ مگابایت SPI که فقط برای
u-boot کافی است، نه برای rootfs).

⇒ برای آزاد کردن کارت SD باید یا **ماژول eMMC** روی برد نصب شود یا **SSD NVMe M.2**.
تا آن موقع، Plus روی SD می‌ماند (که کار می‌کند).


