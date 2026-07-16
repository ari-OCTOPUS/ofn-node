# 🚀 LAUNCH RUNBOOK — Project-F (موج ۲)

> **هدف:** از کدِ آماده به لانچِ واقعی. این سند قدم‌به‌قدم راهنمای توست.
> **زمان تخمینی:** ۲-۳ ساعت کارِ متمرکز در یک روز.
> **پیش‌نیاز:** موج ۰ و ۱ انجام شده (commit `ff8d0bf`)؛ safety nets فعال؛ ۱۰۰ تست سبز.

---

## 📋 چک‌لیست پیش‌شروع (قبل از هر چیز)

- [ ] پیام به صبا ارسال شد (`drafts-awaiting-gate/msg-to-saba-question8.md`)
- [ ] یک ساعتِ بدون مزاحمت داری (این کار نیاز به تمرکز دارد)
- [ ] دسترسی به ایمیلِ اختصاصی برای اکانت‌ها
- [ ] VPN/پروکسیِ پایدار (تحقیق P3: Reddit به IP حساس است)
- [ ] شماره تلفن برای verify اکانت‌ها

---

## مرحله ۱ — تنظیم bot لنگر (۳۰ دقیقه)

### ۱.۱ ساخت Telegram Bot

1. در تلگرام به **@BotFather** برو
2. `/newbot` → نام: `LangarPF` (یا هر نامی) → username: `langar_pf_bot` (یکتا)
3. **API Token** رو کپی کن (مثل `123456:ABC-DEF...`)
4. **هشدار:** این token هرگز در git نباشه — فقط در `langar_config.json` (که در `.gitignore` است)

### ۱.۲ گرفتن chat_id آری

1. به bot جدیدت یک پیام بده (هر چیزی)
2. این URL رو در مرورگر باز کن:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. در JSON پاسخ، `"chat":{"id":NUMERIC_ID}` رو پیدا کن — این `chat_id` آریه

### ۱.۳ تنظیم langar_config.json

فایل `langar/langar_config.json` رو باز کن (الان PII صبا داره — خوبه) و این فیلدها رو اضافه/اصلاح کن:

```json
{
  "blocklist": [
    "Armin Mohebiazal",
    "0493577719",
    "9 cycas place stanhope gardens NSW sydney",
    "<نام واقعی صبا>",
    "<هر شناسهٔ حساس دیگر>"
  ],
  "city_terms": ["Sydney", "سیدنی", "sydney", "Stanhope", "Blacktown"],
  "name_map": {"صبا": "C", "آری": "A", "<نام واقعی>": "X"},
  "project_code": "Project-F",
  "owner_chat_id": <عدد chat_id آری>,
  "bot_token": "<TOKEN از BotFather>",
  "_note": "این فایل در .gitignore است — هرگز commit نشود. blocklist را کامل پر کن."
}
```

**تست:** در ترمینال:
```bash
cd "F:/backup/03 - Projects/اونلی فنز/langar"
python langar_bot.py
```
باید ببینی «shadow-mode» (بدون token) یا اگر token دادی، bot روشن می‌شه. در تلگرام `/status` بفرست — باید جواب بده.

برای توقف: `Ctrl+C`.

### ۱.۴ نصب Scheduled Task (auto-start)

در **PowerShell با دسترسی ادمین** (راست‌کلیک → Run as administrator):

```powershell
cd "F:/backup/03 - Projects/اونلی فنز/langar"
powershell -ExecutionPolicy Bypass -File install-scheduled-task.ps1
```

**تست فوری:**
```powershell
Start-ScheduledTask -TaskName 'ProjectF-Langar-Bot'
```

حالا bot در startup ویندوز خودکار بالا میاد و اگه crash کنه، ۱۰ ثانیه بعد restart می‌شه.

**حذف (اگه خواستی):**
```powershell
.\Uninstall-ScheduledTask.ps1
```

---

## مرحله ۲ — ساخت اکانت‌ها (۶۰-۹۰ دقیقه)

> ⚠️ **مرز:** این کار فقط دستِ توست. من نمی‌تونم اکانت بسازم، CAPTCHA حل کنم، یا رمز وارد کنم.

### ۲.۱ ایمیل اختصاصی

- یک ایمیل جدید بساز (ProtonMail توصیه می‌شه — رایگان، رمزنگاری‌شده، بدون شماره)
- نام: چیزی که به هویتِ واقعی وصل نیست (مثلاً `anar.soles@proton.me`)
- این ایمیل را برای همهٔ اکانت‌ها استفاده کن

### ۲.۲ Reddit account (مهم‌ترین — warm-up)

**استراتژی:** حسابِ aged بهتره ولی اگه نداری، fresh با warm-up صبورانه.

- [ ] اکانت Reddit بساز (با ایمیل اختصاصی)
- [ ] username: چیزی neutral، بدونِ geo-fact یا نام واقعی
- [ ] verify ایمیل
- [ ] **آستانهٔ warm-up:** تا ۲۰ کارما، هیچ لینک فروشی (safety net #2 خودکار جلوشو می‌گیره)
- [ ] در ۳-۵ sub مرتبط subscribe کن (r/feet, r/FootFetishNSFW و similar — چک کن quaraانتین نیستن)

**نکتهٔ حیاتی (P3 reddit-engine):**
- ۷۲ ساعت اول فقط بخوان و vote کن (صفر پست)
- بعدش: ۳ پست SFW (صفر فروش) در روزهای مختلف
- بعد از ۵-۷ روز و ≥۲۰ کارما → می‌تونی لینک بذاری

### ۲.۳ X (Twitter) account

- [ ] اکانت X بساز
- [ ] bio از `drafts-awaiting-gate/x-profile` (بدون geo-fact)
- [ ] profile pic: چیزی feet-themed ولی SFW (نه صورت)
- [ ] ۳ پست اول SFW (صفر لینک)

### ۲.۴ link-hub (AllMyLinks یا Linktree)

- [ ] اکانت AllMyLinks بساز (adult-tolerant‌تر از Linktree)
- [ ] کپی از `drafts-awaiting-gate/link-hub-copy`
- [ ] **tracking link per channel** از `drafts-awaiting-gate/tracking-link-design`

### ۲.۵ OnlyFans Free page (بدون محتوا هنوز)

- [ ] اکانت OF بساز (Free page)
- [ ] verify (ID/عکس — این نیاز به اطلاعات واقعی داره، فقط تو انجام بده)
- [ ] **هنوز هیچ محتوا نذار** — فقط verify شده باشه
- [ ] geo-block ایران را فعال کن (در تنظیمات)

### ۲.۶ (اختیاری) FeetFinder

- [ ] اگه وقت داری، FeetFinder هم بساز (موتور خریدارِ آماده، اولین فروش ۷-۱۴ روز)
- [ ] verify + watermark

---

## مرحله ۳ — تست نهایی bot (۱۵ دقیقه)

وقتی همه چیز تنظیم شد، در تلگرام به bot بفرست:

| دستور | چه باید ببینی |
|---|---|
| `/status` | وضعیت کامل پروژه |
| `/guards` | 🔒 warm-up: 0/20 + هیچ کانال قفل نیست |
| `/pf_status` | acquisition pipeline status + warm-up/locks info |
| `/dm_status` | DM HITL: pending 0، auto-send خاموش |
| `/help` | لیست کامل دستورها |

اگه همه جواب دادن، bot آماده‌ست. اگه نه، خطا رو ببین و اصلاح کن.

---

## مرحله ۴ — شروع warm-up (هفته ۱-۲)

### هر روز (۱۰-۱۵ دقیقه)

1. در تلگرام: `/pf_plan 2` → ۲ تا draft پیشنهاد می‌شه
2. مرور کن: `/pf_queue`
3. اگه OK بودن: `/pf_ok <id>`، اگه نه: `/pf_no <id>`
4. `/pf_ready <id>` → payload ظاهر می‌شه
5. **دستی copy-paste کن به Reddit** (SFW، صفر لینک فروش)

### هر ۲ روز

- به X هم همون پست رو repost کن

### هر جمعه (۱۵ دقیقه)

1. داشبورد Reddit رو باز کن، کارما رو بخون
2. در تلگرام: `/report_karma <عدد>` (مثلاً `/report_karma 25`)
3. وقتی به ۲۰ رسیدی → ✅ warm-up guard باز می‌شه، فروش مجاز می‌شه

---

## مرحله ۵ — وقتی کارما ≥۲۰ شد (Aggressive Launch)

این مرحله فقط وقتی `/guards` می‌گه «✅ آستانه محقق» شروع می‌شه.

### اقدامات

- [ ] لینک link-hub در bio Reddit و X
- [ ] اولین پست در OF Free page
- [ ] شروع PPV planning (`drafts-awaiting-gate/ppv-ladder`)
- [ ] DM HITL فعال: وقتی کسی پیام داد، `/dm_new <ch> <kind> <body>` → `/dm_ok` → دستی بفرست

### هفته ۴: اولین PPV

- قیمت اولیه: $5-8 (طبق ppv-ladder)
- بعد از ارسال، `/dm_sent <id>` بزن تا آمار کامل شه

### هفته ۶: G1 evaluation

- در تلگرام: `/pf_status` → KPIها رو ببین
- معیار G1: ≥۲۰۰ کلیک تجمعی، ≥۱۰٪ click→follow
- اگه پاس نشد: pivot (نه kill) — کانال‌mix رو عوض کن

---

## 🚨 واکنش در بحران

### اگه Reddit/X warning داد (shadowban، rate limit)

1. **فوراً** در تلگرام: `/report_warning reddit <reason>` (یا `x`)
2. کانال lock می‌شه → pipeline خودکار stop
3. ۲۴-۴۸ ساعت صبر کن، مشکل رو حل کن
4. `/clear_warning reddit` → قیف باز می‌شه

### اگه ۲ warning داد (full_stop)

1. **ایست کامل.** هیچ پستی نفرست.
2. در تلگرام: `/guards` → وضعیت رو ببین
3. تحقیق کن: چرا؟ IP؟ الگوی پست؟ محتوا؟
4. وقتی حل شد: `/clear_full_stop` (با verdict آوری)

### اگه سیگنال doxxing (کسی هویت رو پرسید)

1. **فوراً** `/kill` بزن در تلگرام
2. ۴۸ ساعت هیچ فعالیتی
3. پلن OpSec رو اجرا کن (`07 - Compliance & Privacy/`)
4. بعد از امن‌شدن: `/revive`

---

## 📊 متریک‌های هفتگی (جمعه)

هر جمعه این اعداد رو در `DecisionLog.md` ثبت کن:

```
هفتهٔ <N>:
- Reddit: <کارما> کارما، <n> پست، <median> upvote
- X: <n> فالوور، <n> engagement
- OF: <n> free-sub، <n> paid، <$x> درآمد
- DM: <n> دریافت، <n> پاسخ، <$x> conversion
- زمان آری: <h> ساعت
- زمان صبا: <h> ساعت
- warningها: <n>
- next: <تم هفتهٔ بعد>
```

این داده‌ها به مغز (ThompsonBandit) نمی‌رسه مگه از طریق `/record_kpi` صریح ثبت بشن.

---

## ❓ اگه گیر کردی

| مشکل | راه‌حل |
|---|---|
| bot جواب نمی‌ده | `Get-ScheduledTask -TaskName 'ProjectF-Langar-Bot' \| Get-ScheduledTaskInfo` — ببین آخرین اجرا کی بوده |
| `/status` خطا می‌ده | `langar_config.json` رو چک کن — owner_chat_id و bot_token درستن؟ |
| `/guards` ارور می‌ده | فایل `brain/guards.py` وجود داره؟ تست: `python -c "import sys; sys.path.insert(0,'brain'); from guards import WarmupGuard; print('ok')"` |
| warm-up guard ولم نمی‌کنه | `/report_karma <n>` با عددِ واقعیِ کارما بزن |
| خطای permission در commit | فایل lock شده — ویندوز آنتی‌ویروس رو چک کن |

---

## ✅ تعریفِ «روز صفر کامل»

وقتی همهٔ این‌ها صحیح:
- [ ] bot لنگر live و در startup
- [ ] `/status`، `/guards`، `/pf_status`، `/dm_status` همه جواب می‌دن
- [ ] Reddit account ساخته و verify شده
- [ ] X account ساخته با bio
- [ ] link-hub زنده
- [ ] OF Free page verify شده (بدون محتوا)
- [ ] langar_config.json کامل (blocklist + token + chat_id)
- [ ] پیام به صبا ارسال شده

بعد از این، وارد فاز warm-up (هفته ۱-۲) می‌شی.

---

> **یادآوری نهایی:** این مسیر با ریسکه. هر هفتهonest باش با خودت: اگه بعد از ۳ ماه هیچ سیگنال مثبتی نبود (G2 fail)، kill کن. ۶ ماه حداکثر، نه بیشتر.
