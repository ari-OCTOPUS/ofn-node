---
type: runbook
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: active
tags: [ziman/runbook, setup, control-brain]
created: 2026-07-04
updated: 2026-07-04
---

# 🧠🌸 زنده‌سازیِ زیمان + اتصال به مغزِ کنترل — رانبوک

## خلاصهٔ سریع
پروژهٔ زیمان حالا یک **ورکرِ اجراشدنی** دارد (`ziman-agent/`) و به **مغزِ کنترل** (`control-brain/`)
وصل شده. مغز می‌تواند زیمان را **روشن/خاموش/تست** کند — از خط‌فرمان یا داشبوردِ وب (تلگرام بعداً).
ورکر، **پیش‌نویسِ محتوای مارکتینگ** می‌سازد، همیشه **زیرِ سقفِ ظرفیت (D4)** و **بدونِ هیچ انتشار/خرجِ خودکار**.

> این «برشِ نازکِ اول» است: کوچک، واقعی، و کاملاً تست‌شده. ۱۳ تستِ مغز + ۷ چکِ خودآزمونِ زیمان، همه سبز.

## چه چیزی ساخته شد
```
Ziman Galerry/
├─ control-brain/         ← مغزِ کنترل (روشن/خاموش/تست/وضعیت/توقفِ اضطراری)
│  └─ config/projects.yaml   ← زیمان اینجا ثبت شد (enabled: true)
└─ ziman-agent/          ← «جانِ» زیمان: ورکرِ مارکتینگ
   ├─ worker.py             ← نقطهٔ ورود + حالت‌ها + loopِ زنده
   ├─ ziman.yaml            ← پیکربندی (سقفِ ظرفیت=۳۰/هفته، مناسبت‌ها، مدل…)
   ├─ ziman/                ← منطق: capacity(D4)، content(offline+Claude)، brief، config
   └─ drafts/               ← خروجی‌ها (یک نمونهٔ EXAMPLE هست)
```

## مرحله‌به‌مرحله (ویندوز، محلی)

### گام ۰ — پیش‌نیاز (یک‌بار)
پایتون ۳.۱۰+ نصب باشد. بعد در پوشهٔ `control-brain`:
```
cd "C:\Users\Armin\Desktop\backup\03 - Projects\Ziman Galerry\control-brain"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### گام ۱ — تستِ خودِ مغز (بدونِ تلگرام/رمز)
```
python app.py status          # باید demo, زیمان, نقاشی(خاموش), حسابداری(خاموش) را نشان دهد
python run_tests.py           # ۱۳ سبز
```

### گام ۲ — زیمان را از طریقِ مغز تست کن
```
python app.py test ziman      # → ✅ سبز (خودآزمونِ زیمان)
```

### گام ۳ — زیمان را زنده کن
```
python app.py start ziman     # روشن → یک draft همان لحظه در ziman-agent\drafts ساخته می‌شود
python app.py status          # زیمان: running
python app.py stop ziman      # خاموشِ تمیز
```

### گام ۴ — داشبوردِ وب (فقط تماشا)
```
python app.py
```
مرورگر → `http://127.0.0.1:8770`  (هر ۵ ثانیه تازه می‌شود؛ روشن/خاموش از تلگرام در فازِ بعد.)

### گام ۵ — امتحانِ گاردِ ظرفیت (D4)
```
cd ..\ziman-agent
python worker.py --campaign 100   # ❌ رد، با دلیل (بالای سقفِ ۳۰)
python worker.py --campaign 20    # ✅ تأیید
```

## گیت‌های ایمنی (چه چیزهایی جلوگیری شده)
- **read-only:** زیمان فقط فایلِ draft محلی می‌نویسد. **هیچ پستی، هیچ خرجی، هیچ تماسِ بیرونی** جز (اختیاری) Claude برای نوشتنِ متن.
- **قیدِ D4:** هر هدفِ کمپینی بالاتر از سقفِ ظرفیت **رد** می‌شود و دلیل می‌دهد (`ziman/capacity.py`).
- **verdictِ انسانی:** انتشارِ هر draft با تصمیمِ توست؛ ایجنت فقط پیش‌نویس می‌دهد.
- **توقفِ اضطراری:** `python app.py halt` → تا `resume` هیچ پروژه‌ای روشن نمی‌شود (تست شد).

## فعال‌سازیِ تولیدِ زندهٔ Claude (وقتی آماده بودی)
الان بدونِ کلید، ورکر **offline** کار می‌کند (draftِ قالبی). برای متنِ واقعیِ Claude:
1. یک ورودی در **KeePassXC** با عنوانِ `anthropic-key` بساز و کلیدت را در فیلدِ Password بگذار.
2. در `control-brain\.env` مقدارِ `KEEPASS_DB` را به مسیرِ فایلِ `.kdbx` بده.
3. `python app.py secrets-check` → باید `✅ ziman: ANTHROPIC_API_KEY` بدهد.
4. از این‌به‌بعد `start ziman` کلید را فقط در لحظهٔ اجرا تزریق می‌کند (هیچ‌جای دیگر نمی‌ماند).
> مدل در `ziman.yaml` قابلِ تغییر است: `claude-sonnet-5` (کیفیت) یا `claude-haiku-4-5` (ارزان‌تر).
> نرخِ دقیق را از صفحهٔ pricing انتانروپیک ببین؛ ترتیبِ هزینه: haiku < sonnet < opus.

## فعال‌سازیِ تلگرام (فازِ بعد)
`@BotFather` → توکن؛ `@userinfobot` → آی‌دیِ عددی. در `.env`:
`TELEGRAM_TOKEN=...` و `OWNER_CHAT_ID=...`. بعد `python app.py` و در تلگرام `/status`.

## نکتهٔ ظرفیت (بلاکرِ باز در PROJECT.md)
سقفِ **۳۰ واحد/هفته** از `Business-Zeiman.md [Measured]` در `ziman.yaml` ثبت شد و گاردِ D4 روی همین کار می‌کند.
اگر عدد را در منشور هم می‌خواهی رسمی کنی، در `PROJECT.md`/`Capacity & Channels` واردش کن (اختیاری).

## قدم‌های بعدی
1. گام‌های ۱ تا ۵ را روی لپ‌تاپ اجرا کن؛ خروجیِ `drafts/` را نگاه کن.
2. کلیدِ Claude را در KeePassXC بگذار تا تولیدِ زنده روشن شود.
3. سندِ **معماریِ چند-کاربره (ادمین)** را با هم دقیق کنیم (طرحِ اولیه جدا آماده است).

---

## گام ۱ — محتوای واقعیِ فروش (تحویل‌شده)
- **`content/first-sale-pack.md`** — ۱۰ پیامِ DM بازارِ گرم + کپشنِ پست + پیامِ گروه‌ها + اسپرینتِ ۷ روزه. آمادهٔ ارسال (verdict با تو).
- **`content/Ziman-FirstSale-Tracker.xlsx`** — تراکرِ عملیاتی: داشبوردِ زنده (نرخِ پاسخ/تبدیل/درآمد)، لیستِ بازارِ گرم با dropdown، لاگِ کانال. ردیفِ «نمونه» را پاک کن و با نامِ واقعی پر کن.
- **ورکر حالا محتوا را زنده هم می‌سازد:**
```
cd ziman-agent
python worker.py --dm 6      # ۶ پیامِ DM در drafts/
python worker.py --posts 3   # ۳ کپشنِ پست در drafts/
```
بدونِ کلید offline (همین قالب‌ها)، با کلیدِ Claude نسخه‌های تازه و متنوع. از مغز هم: `python app.py test ziman` سبز است.

---

## گام ۲ — همیشه‌روشن روی لپ‌تاپ (تحویل‌شده)
پوشهٔ **`control-brain/autostart/`**:
- `run-brain.bat` — لانچرِ تولیدی: حالت در `%USERPROFILE%\.ziman-control` (بیرونِ vault)، `brain.log`، ری‌استارتِ خودکار.
- `install-startup-shortcut.bat` — خودکاراجرا از هر logon (بی‌پنجره). حذف: `uninstall-startup-shortcut.bat`.
- `install-daily-content.bat` — هر روز ۹ صبح یک بستهٔ DM+پست.
- راه‌اندازی: اول `run-brain.bat` را تست کن (`http://127.0.0.1:8770`)، بعد `install-startup-shortcut.bat`.

> تست‌شده: داشبورد HTTP جواب می‌دهد (۲۰۰)، زیمان دیده می‌شود، و `state.db` بیرونِ vault ساخته می‌شود.

---

## گام ۳ — کنترل از تلگرام (آماده — فقط توکن مانده)
فایلِ **`control-brain/.env`** ساخته شد؛ فقط دو خط را پر کن:
1. تلگرام → **@BotFather** → `/newbot` → یک **TELEGRAM_TOKEN** می‌گیری.
2. تلگرام → **@userinfobot** → **آی‌دیِ عددیِ** خودت = **OWNER_CHAT_ID**.
3. هر دو را در `.env` بگذار، بعد `start.bat` (یا `autostart\run-brain.bat`).
4. در تلگرام به رباتت `/status` بزن → دکمه‌های ▶️ روشن، ⏹ خاموش، 🧪 تست، و `/halt` `/resume`.

> ربات **فقط به آی‌دیِ خودت** جواب می‌دهد (owner-only، در کد enforce شده). کتابخانه با `pip install -r requirements.txt` نصب می‌شود.
