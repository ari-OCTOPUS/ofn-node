# مأموریت Agent — اعتبارسنجی T2/T3/T4 روی برد RK35xx

این سند را عیناً به عامل اجرایی روی `192.168.0.180` بدهید. هدف، اجرای امن و بازتولیدپذیر آزمون‌ها بدون اختلال در soak جاری است.

---

## ۱. واقعیت محیط — غیرقابل تغییر

- معماری میزبان: `aarch64`، خانوادهٔ RK35xx.
- inference فعلی: `llama.cpp` و `libggml-cpu`؛ GPU/NVIDIA فعال نیست.
- `nvidia-smi` وجود ندارد و نباید نصب یا فراخوانی شود.
- ذخیره‌ساز: `/dev/mmcblk0` از نوع eMMC؛ NVMe نیست.
- `smartctl` نصب نیست و برای این مأموریت نباید نصب شود.
- power meter، INA219 و `powercap` موجود نیست.
- telemetry مجاز: دما، فرکانس CPU/GPU/NPU (در صورت export توسط sysfs)، load average و block I/O.
- وضعیت مشاهده‌شدهٔ eMMC: `life_time=0x01 0x00` و `pre_eol=0x01`؛ مقدار خام را دوباره بخوان و هرگز مقدار قبلی را hard-code نکن.
- soak فعال است و endpoint سلامت قبلاً HTTP 200 بوده است.
- T1 تا پایان soak و صدور مجوز صریح ممنوع است.

---

## ۲. هدف دقیق

به‌ترتیب:

1. دریافت و hash فایل‌ها.
2. ممیزی ایستای کد پیش از اجرا.
3. اجرای T2 مستقل و ثبت خروجی خام.
4. اجرای T3 مستقل و ثبت خروجی خام.
5. اجرای T4 فقط با برچسب `SCHEMA_SMOKE_TEST` و بدون ادعای عمر یا توان.
6. مهرکردن خروجی‌ها با SHA-256.
7. تهیهٔ گزارش PASS/FAIL و فهرست محدودیت‌ها.

کارهای خارج از دامنه:

- اجرای T1.
- نصب NumPy/Pandas یا هر بستهٔ Python دیگر.
- نصب `smartctl`.
- تغییر سرویس inference، restart، reboot یا تغییر ساعت سیستم.
- اتصال به Prometheus یا تغییر specification پیش از گزارش آزمون.
- هرگونه load generation.
- تخمین watt، joule یا عمر باقی‌ماندهٔ eMMC از دادهٔ ناکافی.

---

## ۳. فایل ورودی جدید

فقط این فایل برای اجرای آزمون‌ها لازم است:

```text
octopus_board_validation.py
```

این فایل فقط از Python standard library استفاده می‌کند. فایل‌های قبلی `octopus_fast_tests.py` و `octopus_temporal_architecture_spec.md` ممکن است برای آرشیو منتقل شوند، اما نسخهٔ قبلی تست اجرا نشود.

مسیر مقصد:

```text
/opt/octopus/lab/
```

فرمان انتقال از Windows PowerShell، از پوشه‌ای که فایل دانلود شده است:

```powershell
ssh root@192.168.0.180 "mkdir -p /opt/octopus/lab"
scp .\octopus_board_validation.py root@192.168.0.180:/opt/octopus/lab/
```

---

## ۴. پروتکل ممیزی قبل از اجرا

روی برد:

```bash
set -eu
cd /opt/octopus/lab
umask 077

mkdir -p audit
sha256sum octopus_board_validation.py | tee audit/source.sha256
python3 --version | tee audit/python_version.txt
uname -a | tee audit/uname.txt
uname -m | tee audit/machine.txt

python3 -m py_compile octopus_board_validation.py
python3 octopus_board_validation.py --help | tee audit/help.txt

grep -nE '^(import|from) ' octopus_board_validation.py \
  | tee audit/imports.txt

grep -nE 'nvidia-smi|smartctl|powercap|numpy|pandas|subprocess|os\.system|Popen|requests' \
  octopus_board_validation.py \
  | tee audit/forbidden_scan.txt || true
```

شرط قبولی ممیزی:

- `py_compile` exit code صفر.
- imports فقط standard library باشند.
- هیچ فراخوانی `nvidia-smi`، `smartctl`، package installer، shell execution یا HTTP client وجود نداشته باشد.
- فایل نباید سیستم‌زمان، سرویس‌ها یا sysfs را بنویسد؛ خواندن sysfs مجاز است.

اگر هر شرط رد شد، توقف کن و اجرا نکن.

---

## ۵. حفاظت از soak

قبل و بعد از هر تست، endpoint واقعی health را با URL موجود در پیکربندی همین میزبان بررسی کن. URL یا port را حدس نزن. آن را از unit/container/config فعال استخراج کن.

مقصد هر probe و هویت processهای محافظت‌شده را داخل campaign نگه دار. نمونهٔ قالب، نه فرمان قطعی:

```bash
mkdir -p "$CAMPAIGN/safety"

probe_health() {
  LABEL="$1"
  {
    date -u +'%Y-%m-%dT%H:%M:%SZ'
    printf 'url=%s\n' "$ACTUAL_HEALTH_URL"
    curl --silent --show-error \
      --connect-timeout 2 --max-time 5 \
      --output "$CAMPAIGN/safety/${LABEL}.body" \
      --write-out 'http_code=%{http_code}\n' \
      "$ACTUAL_HEALTH_URL"
    ps -p "$INFERENCE_PID","$SOAK_PID" \
      -o pid,lstart,etime,stat,cmd --no-headers
  } > "$CAMPAIGN/safety/${LABEL}.txt" 2>&1

  grep -qx 'http_code=200' "$CAMPAIGN/safety/${LABEL}.txt"
  kill -0 "$INFERENCE_PID"
  kill -0 "$SOAK_PID"
}
```

فایل evidence باید قبل و بعد T2/T3/T4 به‌ترتیب با نام‌های
`health_before_t2` تا `health_after_t4` ساخته شود. PID، زمان شروع process و
URL استخراج‌شده نیز باید حفظ شوند؛ صرف نوشتن عدد ۲۰۰ در گزارش کافی نیست.

همچنین پیش از هر تست ثبت کن:

```bash
uptime
cat /proc/loadavg
free -h
ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -20
```

اگر health دیگر 200 نیست، soak process غایب است، load غیرعادی است یا فضای دیسک کم است، تست را متوقف و فقط شواهد را ثبت کن.

```bash
df -h / /opt/octopus/lab
```

قفل صریح T1 ایجاد کن:

```bash
touch /opt/octopus/lab/T1_LOCKED_SOAK_ACTIVE
```

تا زمانی که این فایل وجود دارد هیچ فرمان T1 یا load-generation مجاز نیست.

---

## ۶. اجرای آزمون‌ها

### ۶.۱ ممیزی runtime و قابلیت‌ها

```bash
cd /opt/octopus/lab
python3 octopus_board_validation.py --audit \
  > audit_runtime_console.log 2>&1
```

آخرین run directory را پیدا کن:

```bash
AUDIT_RUN=$(find validation_runs -maxdepth 1 -type d -name 'run_*' | sort | tail -1)
echo "$AUDIT_RUN"
cat "$AUDIT_RUN/summary.json"
```

انتظار:

- `machine` برابر `aarch64` یا نام معادل ARM64 باشد.
- `mmcblk0_stat=true`.
- حداقل یک thermal zone موجود باشد.
- `t1_power_scaling_valid=false`.

### ۶.۲ اجرای T2

```bash
python3 octopus_board_validation.py --t2 \
  > t2_console.log 2>&1

T2_RUN=$(find validation_runs -maxdepth 1 -type d -name 'run_*' | sort | tail -1)
cat "$T2_RUN/t2_result.json"
```

معیارها:

```text
identical_below_5pct_regime = true
low_precision_noise_below_25pct_regime = true
persistent_regime_exceeds_high_precision_noise = true
verdict = PASS
```

تفسیر مجاز:

> الگوریتم سنجه در شبیه‌سازی deterministic و چهار سناریوی تعریف‌شده رفتار مورد انتظار دارد.

تفسیر ممنوع:

> زمان ذهنی یا آگاهی اثبات شد.

فایل‌های raw هر سناریو باید حفظ شوند.

### ۶.۳ اجرای T3

```bash
python3 octopus_board_validation.py --t3 \
  > t3_console.log 2>&1

T3_RUN=$(find validation_runs -maxdepth 1 -type d -name 'run_*' | sort | tail -1)
cat "$T3_RUN/t3_result.json"
```

هر چهار check باید `true` و verdict باید `PASS` باشد.

تفسیر مجاز:

> در unit test مصنوعی، ترتیب مبتنی بر monotonic با وجود offset منفی wall-clock حفظ شد.

تفسیر ممنوع:

> سیستم در برابر تمام خطاهای NTP، reboot و clock drift مقاوم است.

این تست عمداً ساعت سیستم را تغییر نمی‌دهد.

### ۶.۴ اجرای T4

برای جلوگیری از بار اضافی، ابتدا نمونهٔ ۶۰ ثانیه‌ای با فاصلهٔ ۲ ثانیه:

```bash
python3 octopus_board_validation.py \
  --t4 \
  --device mmcblk0 \
  --sample-seconds 60 \
  --interval 2 \
  > t4_console.log 2>&1

T4_RUN=$(find validation_runs -maxdepth 1 -type d -name 'run_*' | sort | tail -1)
cat "$T4_RUN/t4_result.json"
```

انتظار:

- `label=SCHEMA_SMOKE_TEST`.
- `power_measurement=UNAVAILABLE_NO_EXTERNAL_POWER_METER`.
- `wear_lifetime_prediction=NOT_CALCULATED_INSUFFICIENT_CALIBRATION`.
- delta نوشتن/خواندن از `/sys/block/mmcblk0/stat` ثبت شود.
- مقدار raw و تفسیر eMMC حفظ شود.
- thermal summary ثبت شود.

مقدار `sectors_written` در block stat با واحد sectorهای ۵۱۲ بایتی به byte تبدیل می‌شود. این مقدار حجم write در سطح block layer است و الزاماً مساوی NAND writes یا write amplification داخلی نیست.

T4 نباید عمر باقی‌مانده را به روز/سال تبدیل کند. کد eMMC bucket است، نه درصد دقیق.

اگر `/proc/PID/io` قابل خواندن بود، delta فرایندها فقط با برچسب
`PROC_IO_DELTA_PROXY_NOT_BLOCK_DEVICE_OR_NAND_ATTRIBUTION` ثبت شود. این داده
برای یافتن نامزدهای write burst مفید است، اما انتساب قطعی به `mmcblk0` یا NAND
نیست.

---

## ۷. مهرکردن کل artefactها

پس از اتمام:

```bash
cd /opt/octopus/lab
RUN_PACKAGE="validation_package_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN_PACKAGE"

cp -a audit "$RUN_PACKAGE/"
cp -a validation_runs "$RUN_PACKAGE/"
cp -a "$CAMPAIGN/safety" "$RUN_PACKAGE/"
cp -a ./*_console.log "$RUN_PACKAGE/" 2>/dev/null || true
cp -a T1_LOCKED_SOAK_ACTIVE "$RUN_PACKAGE/"
cp -a octopus_board_validation.py "$RUN_PACKAGE/"
cp -a AGENT_HANDOFF_RK35XX_VALIDATION.md "$RUN_PACKAGE/"

find "$RUN_PACKAGE" -type f ! -name 'SHA256SUMS.txt' -print0 \
  | sort -z \
  | xargs -0 sha256sum \
  > "$RUN_PACKAGE/SHA256SUMS.txt"

sha256sum -c "$RUN_PACKAGE/SHA256SUMS.txt"

tar --sort=name \
  --mtime='UTC 1970-01-01' \
  --owner=0 --group=0 --numeric-owner \
  -czf "${RUN_PACKAGE}.tar.gz" "$RUN_PACKAGE"

sha256sum "${RUN_PACKAGE}.tar.gz" \
  | tee "${RUN_PACKAGE}.tar.gz.sha256"

tar -xOf "${RUN_PACKAGE}.tar.gz" \
  "$RUN_PACKAGE/SHA256SUMS.txt" \
  > "${RUN_PACKAGE}.archive-manifest.txt"

cmp "$RUN_PACKAGE/SHA256SUMS.txt" \
  "${RUN_PACKAGE}.archive-manifest.txt"
```

خود `SHA256SUMS.txt` عمداً در manifest داخلی hash نمی‌شود؛ hash بیرونی archive
کل blob شامل manifest را مهر می‌کند. verification داخلی باید بدون failure
تمام شود و فایل source دقیقاً داخل archive باشد.

اگر نسخهٔ `tar` گزینه‌های deterministic را پشتیبانی نکرد، archive معمولی بساز اما این محدودیت را در گزارش بنویس.

---

## ۸. قالب گزارش اجباری

عامل باید گزارش را دقیقاً با این ساختار تحویل دهد:

```markdown
# OCTOPUS RK35xx Validation Report

## Identity
- Host:
- UTC start/end:
- Kernel:
- Architecture:
- Python:
- Script SHA-256:
- Archive SHA-256:

## Soak Safety
- Health before T2:
- Health after T2:
- Health before T3:
- Health after T3:
- Health before T4:
- Health after T4:
- Any restart or service change: NO/YES

## T2
- Verdict:
- Three checks:
- Raw artefacts:
- Interpretation limit:

## T3
- Verdict:
- Four checks:
- Minimum monotonic delta:
- Synthetic wall jump:
- Interpretation limit:

## T4
- Label: SCHEMA_SMOKE_TEST
- mmcblk0 bytes read/written delta:
- Min/mean/max temperature by zone:
- Thermal excursions >=15C:
- Process I/O attribution scope and top candidates:
- eMMC life_time raw and interpretation:
- eMMC pre_eol raw and interpretation:
- Power: UNAVAILABLE
- Remaining lifetime: NOT CALCULATED

## Failures
- Exact command:
- Exit code:
- stderr:
- Changed files/services:

## Decision
- ACCEPT / ACCEPT_WITH_LIMITATIONS / REJECT
- Required specification changes:
- T1 remains locked: YES
```

---

## ۹. اصلاحات specification پس از نتیجه

فقط پس از مشاهدهٔ خروجی‌ها، patch زیر پیشنهاد شود:

- T2: `precision × surprise` به‌تنهایی کافی نیست؛ شرط ماندگاری در مقیاس کند افزوده شود.
- T2: صریحاً بین `raw_information`, `persistent_information`, `N_cog` و `Theta_subj` تمایز گذاشته شود.
- T2: تا نبود mapping کالیبره، `Theta_subj` برابر
  `NOT_CALCULATED_NO_CALIBRATED_MAPPING` بماند.
- T3: wall-clock فقط metadata؛ محاسبهٔ interval و ordering با monotonic/HLC.
- T4: برای RK35xx، توان حذف و به `UNMEASURED` تبدیل شود؛ proxy دما/فرکانس هرگز watt نامیده نشود.
- T4: eMMC lifetime فقط bucket؛ write volume از block stat فقط host write proxy است.
- T4: ادعای «پیری فیزیولوژیک» تا زمان کالیبراسیون طولانی‌مدت ممنوع باشد.
- T1: به دو تست جدا شکسته شود:
  - `T1P`: performance–load–temperature روی llama.cpp.
  - `T1E`: power–load فقط پس از نصب power meter کالیبره.

---

## ۱۰. شرایط توقف فوری

در هر کدام از موارد زیر توقف کن:

- `/health` دیگر HTTP 200 نیست.
- soak process متوقف یا restart شده.
- دمای گزارش‌شده از آستانهٔ موجود در تنظیمات برد عبور کرده؛ آستانهٔ جدید اختراع نکن.
- filesystem نزدیک پرشدن است.
- Python درخواست dependency غیرstdlib می‌کند.
- T4 برای خواندن telemetry نیاز به تغییر permission یا نوشتن در sysfs دارد.
- هر فرمانی ممکن است بار inference را تغییر دهد.

اصل حاکم:

> ابتدا مشاهده، سپس آزمون کم‌خطر، سپس گزارش. هیچ بهینه‌سازی یا اصلاح خودکار در این مأموریت انجام نشود.
