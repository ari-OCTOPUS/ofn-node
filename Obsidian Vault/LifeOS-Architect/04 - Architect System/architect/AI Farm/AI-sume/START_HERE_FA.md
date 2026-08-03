# LANGAR — گزارشِ راه‌اندازی (مرحله ۰: بررسی)

> پروژه در یک دایرکتوریِ تمیز چیده شد. این فایل = گزارشِ بررسی قبل از `build`.

## فرضِ صریح
آدرسی برای دسکتاپِ لپ‌تاپ در پیام نبود و من فقط به پوشه‌ی متصلِ **AI Farm** دسترسی دارم،
پس طبقِ fallbackِ خودت پروژه را اینجا چیدم:

```
AI Farm\AI-sume\
```

این پوشه روی کامپیوترِ خودت است و می‌مانَد. اگر می‌خواهی دقیقاً روی Desktop باشد:
فقط کلِ پوشه‌ی `AI-sume` را Cut/Paste کن به `C:\Users\<you>\Desktop\`. هیچ مسیرِ مطلقی در کد hard-code نشده، پس جابه‌جایی امن است.

## چه چیزی هست ✅
- `langar/` — باتِ تلگرام (چهره‌ی کاربر؛ python-telegram-bot + SQLite). شاملِ `bot.py`، `agents/`، `core/`، `brain/`، `researcher/`، `observability/`، `safety/`، `tests/`.
- `langar-pro/` — بک‌اندِ پژوهش (FastAPI + Postgres/pgvector): `app/`، `db/schema.sql`، `Dockerfile`.
- `docker-compose.unified.yml` — استکِ واحد: `bot + api + db(pgvector) + redis`، شبکه‌ی `langar-net`، `restart: unless-stopped`، healthcheckِ Postgres.
- `.env.example` (ریشه) — الگوی کاملِ متغیرها.
- مستندات: `CHECKLIST.md`، `ARCHITECTURE.md`، `PLAN.md`، `DEPLOYMENT_GUIDE_FA.md`.

## چه چیزی کم است ⚠️
1. **`.env` ریشه وجود ندارد** — compose با `env_file: .env` آن را می‌خواهد. باید `cp .env.example .env` بزنی و پر کنی.
2. **Docker روی این محیط نیست** — اجرای واقعیِ ۴ کانتینر فقط روی لپ‌تاپِ خودت ممکن است (نیازِ Docker Desktop روشن).
3. **Git repo ساخته نشده** — `git init` را خودت روی ویندوز بزن. `.gitignore` آماده و تست‌شده است (همه‌ی فایل‌های secret/db درست ignore می‌شوند).
4. **یک پوشه‌ی `.git`ِ نیمه‌خراب باقی ماند** — هنگام تستِ ignore ساخته شد ولی محیطِ من اجازه‌ی حذفش را روی این درایو نداد. **لطفاً پوشه‌ی `AI-sume\.git` را دستی پاک کن** (در Explorer)، بعد خودت `git init` تازه بزن.

## ریسک‌ها / کارهای امنیتی که انجام دادم 🔒
- پاک‌سازیِ `__pycache__` و `*.pyc` (cruft).
- یک **`.gitignore` ریشه‌ایِ سخت‌گیر** ساختم که این‌ها را هرگز commit نمی‌کند:
  `.env`، `env`، `**/.env`، `*.db`، `*.pickle`.
- ⚠️ **هشدارِ مهم:** سه فایلِ زیر شاملِ کلیدِ **واقعی** هستند (محتوایشان را چاپ نکردم):
  `langar/.env` · `langar/env` · `langar-pro/.env`.
  - این فایل‌ها الان توسطِ `.gitignore` محافظت‌شده‌اند، ولی **قبل از هر push** با `git status` مطمئن شو هیچ‌کدام staged نیستند.
  - توصیه: اگر این توکن‌ها جایی لو رفته‌اند (مثلاً همین zip را جای ناامن گذاشتی)، در @BotFather توکنِ بات را **revoke/regenerate** کن.

## قدمِ بعدی — دقیقاً این‌ها را خودت روی لپ‌تاپ بزن

```powershell
cd "<مسیرِ پوشه‌ی AI-sume>"

# ۱) ساختِ .env و پر کردنش (BOT_TOKEN, OWNER_ID, POSTGRES_PASSWORD یکسان در DATABASE_URL)
copy .env.example .env
notepad .env

# ۲) چک کن Docker روشن است
docker version          # باید Server هم بیاید؛ اگر نه → Docker Desktop را باز کن

# ۳) بالا آوردنِ کلِ استک با یک دستور
docker compose -f docker-compose.unified.yml up -d --build
docker ps               # langar-bot, langar-pro-api, langar-pro-db, langar-redis = Up

# ۴) تست‌های پذیرش
curl http://localhost:8000/health     # status: ok
# در تلگرام: /start ، /menu ، /halt→/resume (kill-switch) ، /research ، /ailab
```

دقیقاً کدام خطوطِ `.env` را پر کنی: `BOT_TOKEN`، `OWNER_ID`، `POSTGRES_PASSWORD`
(+همان رمز داخلِ `DATABASE_URL`). کلیدهای LLM/Brave اختیاری‌اند — بدون‌شان آفلاین کار می‌کند.
