---
type: mining_roadmap
status: active
phase: execution-phase-1
mining_leg_status: active
created: 2026-07-12
updated: 2026-07-12
tags: [mining, roadmap, competitive-intel, execution, 10-steps]
---

# ۱۰ مرحله بعدی — نقشه راه اجرایی Mining

> **truth anchor.** این نوت ترتیب دقیق ۱۰ مرحله بعدی پروژه Mining را مشخص می‌کند.
> هر مرحله وابسته به تکمیل مرحله قبلی است. بدون پرش.
> الگوی اصلی = اختاپوس (MYCELIAL organism).

---

## وضعیت فعلی (جمع‌بندی)

```yaml
mining_leg: ACTIVE (OCTOPUS_WIRE_MINING=1, PID 21556)
organism_state:
  leg_id: mining-fleet
  money_link: incubating
  autonomy: read-only + propose-only
  electricity_mood: "🟡" (fail-closed — ریگ‌ها ناشناخته)
  nodes: 0/0
  hashrate_measured: false
  telegram_digest: active (⛏ topic)
verdict_queue: 6 open (MIN-V1 through MIN-V6)
security_gate: closed (wallet seed rotation)
files_verified: 20/20 saved
```

---

## مرحله ۱: تکمیل VERDICT_QUEUE — تأیید Safety State

**هدف:** بستن ۳ verdict که مستقیماً مربوط safety هستند (بدون نیاز به سخت‌افزار فیزیکی).

**اقدامات:**

| # | کار | خروجی | ریسک |
|---|---|---|---|
| ۱.۱ | **MIN-V3:** تأیید اینکه هیچ mining فعالی نیست | بررسی `ORGANISM-STATE.json` → nodes=0, hashrate=0 | 🟢 zero |
| ۱.۲ | **MIN-V5:** تأیید zero wallet access | بررسی `secrets=()` در mining_leg + REGISTRY.md → wallet_policy: zero | 🟢 zero |
| ۱.۳ | **MIN-V6:** تأیید coin scouting فقط report | بررسی RUNBOOK.md + adapter.yaml → autonomous_allowed: [] | 🟢 zero |

**مدت تخمینی:** ۱۵ دقیقه

**خروجی:** MIN-V3, V5, V6 → `closed` در VERDICT_QUEUE.md

---

## مرحله ۲: بررسی Rival Analysis — نقشه رقبا

**هدف:** درک کامل فضای رقابتی CPU/ARM mining 2025-2027.

### ماتریس رقبا (Tier-1: پلتفرم‌های مدیریت)

| رقیب | مدل | قیمت | CPU | ARM | OSINT | نقاط ضعف |
|---|---|---|---|---|---|---|
| **Hive OS** | Linux distro + dashboard | $0.50/mo per worker | ✅ | ❌ x86 only | ❌ | malware target، بدون ARM |
| **Awesome Miner** | Windows GUI | Free (2 rig) → paid | ✅ | ❌ x86 only | ❌ | بدون ARM، Windows-only |
| **MinerStat** | SaaS + Linux OS | ~$2/rig/mo | ✅ | ⚠️ Linux ممکن | ❌ | جامعه کوچک |

### ماتریس رقبا (Tier-2: ماینرها)

| رقیب | الگوریتم | ARM | مانیتورینگ |
|---|---|---|---|
| **XMRig** | RandomX, CryptoNight, KawPow, GhostRider | ✅ ARMv8 | ❌ CLI only |
| **XMRigCC** | (fork of XMRig) | ✅ ARMv8 | ✅ web dashboard + REST API |
| **Rigel** | Etchash, Ethash, FishHash, KarlsenHash... | ❌ NVIDIA GPU only | ❌ |

### ماتریس رقبا (Tier-3: پلتفرم‌ها)

| رقیب | نقش | CPU | تهدید |
|---|---|---|---|
| **NiceHash** | Hashpower marketplace | ⚠️ کاهش support CPU | algoritms تغییر کرد Aug 2025 |
| **Clore.ai** | GPU cloud + idle mining | ⚠️ محدود | Clore Fleet (scale) |
| **Antminer X5/X9** | RandomX ASIC | ❌ | **بزرگترین تهدید** — ASIC-resistant بودن RandomX شکسته |

### شکاف‌های بازار (فرصت ما)

| شکاف | توضیح | رقیب |
|---|---|---|
| **OSINT/Security** | هیچ پلتفرمی threat detection ندارد | هیچ‌کدام |
| **AI CPU optimization** | AI فقط روی GPU/ASIC تمرکز کرده | هیچ‌کدام |
| **ARM-native management** | هیچ پلتفرم اصلی ARM پشتیبانی نمی‌کند | هیچ‌کدام |
| **Unified CPU + monitor + security** | راه‌حل یکپارچه وجود ندارد | هیچ‌کدام |

**اقدام:** این تحلیل در Obsidian ذخیره شود به‌عنوان مرجع رقابتی.

---

## مرحله ۳: بررسی فیزیکی ریگ‌ها — MIN-V1

**هدف:** بستن MIN-V1 (چند ریگ قابل‌استفاده؟).

**اقدامات:**

| # | کار | روش | خروجی |
|---|---|---|---|
| ۳.۱ | لیست تمام دستگاه‌های Orange Pi | بررسی جعبه فیزیکی یا یادداشت قبلی | لیست سریال‌ها |
| ۳.۲ | تست روشن شدن هر دستگاه | پاور + SSH via Tailscale | status per device |
| ۳.۳ | بررسی نسخه SoC و RAM | `cat /proc/cpuinfo` via SSH | RK3588 confirm |
| ۳.۴ | تست دمای idle | `cat /sys/class/thermal/...` | baseline temp |
| ۳.۵ | تکمیل Hardware Registry | وارد کردن در `Hardware Registry & Runbook.md` | رجیستری پر شده |

**⚠️ اگر ریگی نبود یا خراب بود:** ثبت شود و ادامه با تعداد واقعی.

**خروجی:** MIN-V1 → `closed` (با عدد واقعی)

---

## مرحله ۴: بررسی هزینه برق — MIN-V2

**هدف:** بستن MIN-V2 (برق <$0.05/kWh یا solar؟).

**اقدامات:**

| # | کار | روش |
|---|---|---|
| ۴.۱ | بررسی قبض برق فعلی | خواندن قبض یا پرسش از مالک |
| ۴.۲ | محاسبه مصرف هر Orange Pi | ~10W idle، ~15W mining (از specs RK3588) |
| ۴.۳ | محاسبه هزینه روزانه | ` watts × hours / 1000 × cost_per_kWh` |
| ۴.۴ | بررسی گزینه solar | اگر rooftop/بالکن available |

**قانون ساختاری:** اگر هزینه > $0.05/kWh و solar نیست → **maining متوقف** (D2 constraint).

**خروجی:** MIN-V2 → `closed` (yes/no/unknown + عدد واقعی)

---

## مرحله ۵: انتخاب ماینر — بر اساس رقبا

**هدف:** انتخاب ماینر (نرم‌افزار) برای هر ریگ.

### تصمیم‌گیری بر اساس تحقیق رقبا:

| ماینر | مزایا | معایب | توصیه |
|---|---|---|---|
| **XMRig** | بهترین CPU، open-source، ARMv8، free | بدون dashboard | ✅ انتخاب اول — ماینر اصلی |
| **XMRigCC** | dashboard + REST API + notifications | fork، ممکن است کندتر آپدیت شود | ✅ اگر مانیتورینگ متمرکز می‌خوای |
| **nanominer** | چندالگوریتم | بدون ARM optimization | ⚠️ فقط اگر XMRig جواب نداد |

**توصیه:** XMRig (official) + XMRigCC (اگر dashboard خواستی). هر دو ARMv8 پشتیبانی می‌کنند.

**اقدام:**

| # | کار |
|---|---|
| ۵.۱ | دانلود آخرین نسخه ARMv8 XMRig از xmrig.com |
| ۵.۲ | تست روی یک ریگ (benchmark RandomX) |
| ۵.۳ | ثبت هش‌ریت واقعی در Hardware Registry |

---

## مرحله ۶: انتخاب کوین — اولین آزمایش

**هدف:** انتخاب اولین کوین برای آزمایش با چارچوب Coin Scouting Framework.

### کاندیدها بر اساس تحقیق بازار:

| کوین | الگوریتم | ARM-viable? | لانچ | نقدشوندگی | توصیه |
|---|---|---|---|---|---|
| **Monero (XMR)** | RandomX | ✅ | 2014 | بالا | ✅ **تست اول** — liquid،.community بزرگ |
| **Verus (VRSC)** | VerusHash | ✅ | 2021 | متوسط | ⚠️ بعد از XMR — قبلاً clusters داشتی |
| **Etica (ETI)** | RandomX | ✅ | 2024 | پایین | ⚠️ DeSci narrative — بعداً |
| **QRL** | RandomX | ✅ | 2018 | پایین | ⚠️ quantum-resistant — بعداً |
| **Qubic (QUBIC)** | Custom CPU | ❓ | 2024 | متوسط | ❓ نیاز به بررسی ARM support |

**توصیه:** **Monero (XMR)** به‌عنوان کوین اول — بالاترین نقدشوندگی، community فعال، XMRig پشتیبانی کامل، RandomX on ARMv8 کار می‌کنه.

**اقدام با چارچوب:**

| # | کار |
|---|---|
| ۶.۱ | پر کردن قالب لاگ آزمایش (از Coin Scouting Framework) |
| ۶.۲ | ثبت: الگوریتم=RandomX، نودها=[تعداد واقعی]، لانچ 2014 |
| ۶.۳ | تنظیم death-watch: dev dead threshold=8 هفته |

**خروجی:** کوین #۱ ثبت‌شده با قالب استاندارد + death-watch فعال.

---

## مرحله ۷: وصل کردن ریگ اول به اختاپوس

**هدف:** اولین ریگ methodically وصل شود — نه SSH مستقیم، بلکه از مسیر repo + deploy gate.

**اقدامات:**

| # | کار | فایل/مکانیزم |
|---|---|---|
| ۷.۱ | نصب XMRig ARMv8 روی ریگ | از مسیر `02 - Code/Ai bots/deploy/setup_worker.sh` (الگو) |
| ۷.۲ | تنظیم config (pool URL، wallet، threads) | config.json |
| ۷.۳ | راه‌اندازی systemd service | `deploy/systemd/worker-agent.service` (الگو) |
| ۷.۴ | تست ماین ۱ ساعته | بررسی hashrate + temperature + power |
| ۷.۵ | ثبت نتایج | Hardware Registry + noot آزمایش |

**⚠️ D-20:** هیچ SSH مستقیم. همه از مسیر repo + deploy gate.
**⚠️ D-11:** ولت فقط در password manager — هیچ trace در repo.

---

## مرحله ۸: فعال‌سازی Fleet Manager

**هدف:** وقتی حداقل یک ریگ در حال ماین است، Fleet Manager (کد موجود در `02 - Code/Ai bots/fleet/`) را بررسی و آماده کن.

| # | کار | توضیح |
|---|---|---|
| ۸.۱ | بررسی `fleet/manager.py` | REST :7700 — آیا با ریگ فعلی کار می‌کند؟ |
| ۸.۲ | بررسی ۳ شکاف شناسایی‌شده | worker count 9 vs 16، kill-switch unwired، SPOF |
| ۸.۳ | تصمیم: از Fleet Manager استفاده کنی یا اختاپوس Leg کافیه؟ | Mining Leg الان state گزارش می‌دهد — شاید کافی باشد |

**نکته:** Mining Leg الان تیک می‌زند و state می‌نویسد. Fleet Manager یک لایه مدیریت اضافی است. تا زمانی که >۱ ریگ نداری، Mining Leg کافیه.

---

## مرحله ۹: تنظیم Telegram Digest + Alertها

**هدف:** اطمینان از اینکه تلگرام digest ⛏ Mining درست کار می‌کند و alert‌ها فعال هستند.

| # | کار | انتظار |
|---|---|---|
| ۹.۱ | بررسی Telegram topic ⛏ Mining | باید digest ۳ خطی ببینی |
| ۹.۲ | تأیید electricity_mood تغییر می‌کند | وقتی ریگ اول روشن شود، mood باید 🟢 یا 🔴 شود (نه 🟡) |
| ۹.۳ | تأیید nodes_total/running | باید ≥۱ شود |
| ۹.۴ | بررسی thermal_warn | اگر دما >75°C، alert باید ظاهر شود |

---

## مرحله ۱۰: اولین گزارش هفتگی + بستن VERDICT_QUEUE

**هدف:** تولید اولین گزارش هفتگی واقعی با داده واقعی + بستن تمام verdict‌ها.

**اقدامات:**

| # | کار | خروجی |
|---|---|---|
| ۱۰.۱ | پر کردن لاگ هفتگی (قالب Coin Scouting Framework) | سکه mined، dev activity، network، note |
| ۱۰.۲ | بستن MIN-V4 (Hardware Registry پر شد) | ✅ closed |
| ۱۰.۳ | آپدیت MANIFEST.yaml | execution_state: minimal-active |
| ۱۰.۴ | آپدیت Phase Status | فاز ۱→۲ تکمیل |
| ۱۰.۵ | مرور پیشنهاد ارتقا به v3.0 | کدام ایجنت‌ها معنا پیدا می‌کنند؟ |

---

## خلاصه بصری

```
مرحله  NOW   ✅━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ۱     VERDICT بستن safety (V3,V5,V6)        ۱۵ min
  ۲     تحلیل رقبا + ذخیره در Obsidian         done ✅
  ۳     بررسی فیزیکی ریگ‌ها (V1)              ۱-۲ ساعت
  ۴     بررسی هزینه برق (V2)                  ۳۰ min
  ۵     انتخاب ماینر (XMRig ARM)               ۳۰ min
  ۶     انتخاب کوین #۱ (Monero)               ۳۰ min
  ۷     وصل ریگ اول (deploy gate)             ۱-۲ ساعت
  ۸     بررسی Fleet Manager                    ۳۰ min
  ۹     تأیید Telegram digest                  ۱۵ min
  ۱۰    اولین گزارش هفتگی + بستن V4           ۳۰ min

کل تخمین: ۴-۶ ساعت (بدون شامل time دیگه)
```

---

## تهدیدها — از تحقیق رقبا

| تهدید | شدت | پاسخ ما |
|---|---|---|
| **RandomX ASIC (Antminer X5/X9)** | 🔴 بالا | Monero community احتمالاً fork می‌کند. ما survival-based هستیم (D2). |
| **NiceHash حذف CPU algorithms** | 🟡 متوسط | ما مستقیم به pool وصل می‌شویم، نه marketplace. |
| **پایین بودن profitability** | 🟡 متوسط | D2 = survival، نه payback. معیار مرگ فقط death-watch است. |
| **Zero ARM management tools** | 🟢 فرصت | دقیقاً جایی که Mining Leg ما + اختاپوس مزیت دارد. |

---

## تغییرات

| تاریخ | تغییر |
|---|---|
| 2026-07-12 | نوت اولیه — ۱۰ مرحله + تحقیق رقبا ۱۲ منبع |
