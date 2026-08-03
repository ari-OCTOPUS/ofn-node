# راهنمای استقرارِ LANGAR (۲۴ ساعته) — فارسی، قدم‌به‌قدم

این راهنما برای راه‌اندازیِ باتِ سبکِ LANGAR روی یک سرور است تا همیشه‌روشن بماند.

---

## ۱) چه چیزهایی لازم داری

**ضروری برای شروع:**
- یک **VPS** (سرورِ لینوکسی، Ubuntu 22.04).
- **توکنِ باتِ تلگرام** از `@BotFather`.
- **آیدیِ عددیِ تلگرامِ خودت** از `@userinfobot`.

**پیشنهادی (برای هوشمندتر شدن):**
- **کلیدِ LLM**: Claude (`CLAUDE_KEY`) یا یک سرویسِ OpenAI-compatible مثلِ DeepSeek (`OPENAI_KEY` + `OPENAI_BASE_URL` + `OPENAI_MODEL`). بدونِ این، بات آفلاین کار می‌کند.
- **کلیدِ جست‌وجو**: Brave Search (`BRAVE_API_KEY`) برای `/research` و `/ai_research`.

**اختیاری (حرفه‌ای‌تر):** دامنه، Cloudflare Tunnel (برای Webhook)، Postgres (نسخه‌ی `langar-pro`).

---

## ۲) اولویت و هزینه‌ی تقریبی

- **اقتصادی:** VPS کوچک + Claude Haiku/DeepSeek → حدود **۱۵ تا ۳۰ دلار/ماه**.
- **متعادل (پیشنهادی):** VPS دوهسته‌ای + مدلِ سبک برای کارِ روزمره و مدلِ قوی فقط برای AI-Lab + Brave → حدود **۳۰ تا ۸۰ دلار/ماه**.
- **قوی:** Postgres + بودجه‌ی API بالا → **۸۰ تا ۲۰۰ دلار/ماه** (فعلاً لازم نیست).

بودجه‌ی AI-Lab را خودت در `.env` سقف می‌گذاری (`AILAB_DAILY_BUDGET_USD`, `AILAB_MONTHLY_BUDGET_USD`) و با `/ai_budget` می‌بینی.

---

## ۳) راه‌اندازی روی VPS با Docker (ساده‌ترین مسیر)

```bash
# روی سرور (با کاربرِ غیرِ root بهتر است):
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
# پروژه را بیاور (git clone یا کپی با scp):
cd ~/langar
# .env را بساز (فقط key=value):
cp .env.example .env
nano .env          # BOT_TOKEN و OWNER_ID را پر کن (و کلیدها اگر داری)
chmod 600 .env     # فقط خودت بخوانی‌اش

# بالا بیاور (۲۴ ساعته، با ری‌استارتِ خودکار):
docker compose up -d --build

# لاگِ زنده:
docker compose logs -f
```

`restart: unless-stopped` در compose یعنی بعد از ری‌استارتِ سرور، بات خودکار بالا می‌آید. داده در پوشه‌ی `data/` پایدار می‌ماند.

---

## ۴) Polling یا Webhook؟

- **Polling (پیش‌فرض، پیشنهادی):** بات خودش از تلگرام می‌پرسد. نه دامنه می‌خواهد نه SSL. همین `docker compose up` کافی است.
- **Webhook (حرفه‌ای‌تر):** نیاز به دامنه + SSL + Cloudflare Tunnel. برای شروع لازم نیست؛ بعداً اگر خواستی اضافه می‌کنیم.

---

## ۵) بکاپ (مهم)

داده‌ات در `data/langar.db` است. یک بکاپِ روزانه بگیر:

```bash
# اسکریپتِ ساده:
mkdir -p ~/backups
cp ~/langar/data/langar.db ~/backups/langar-$(date +%F).db
# یا داخلِ بات: /export برای JSON · /export_csv برای CSV
```
> `.env` را در بکاپِ ناامن نگذار (کلید دارد). یا رمزگذاری کن.

---

## ۶) امنیت

- `.env` هرگز در git نرود (در `.gitignore` هست) و `chmod 600` باشد.
- بات فقط به `OWNER_ID`ِ تو جواب می‌دهد؛ غریبه = سکوت.
- کلیدها فقط در `.env` روی سرور — نه در چت/گیت/اسکرین‌شات.
- اگر کلیدی لو رفت، فوری revoke کن (BotFather `/revoke` برای توکن).
- AI-Lab فقط diff می‌سازد؛ هیچ اجرای خودکاری بدونِ تأییدِ تو نیست.

---

## ۷) چک‌لیستِ نهایی

- [ ] `docker compose up -d` بدونِ خطا بالا آمد؟
- [ ] در تلگرام `/start` و `/menu` جواب می‌دهند؟
- [ ] تستِ kill-switch: `/halt` → `/log` ساکت → `/resume`؟
- [ ] `/ailab` و `/ai_budget` کار می‌کنند؟
- [ ] `/privacy` درست توضیح می‌دهد؟
- [ ] سرور را `reboot` کردی و بات دوباره بالا آمد؟

---

## ۸) عیب‌یابی سریع

- «BOT_TOKEN تنظیم نشده» → `.env` خراب/خالی است؛ فقط `key=value`، بدونِ BOM (با `nano` یا `Set-Content -Encoding ascii`).
- بات جواب نمی‌دهد → `docker compose logs -f` را ببین؛ اگر `halted` بود `/resume` بزن.
- `/research` می‌گوید آفلاین → `BRAVE_API_KEY` نگذاشته‌ای (طبیعی است).
- بودجه تمام شد → `/ai_budget` را ببین یا سقف را در `.env` بالا ببر.
