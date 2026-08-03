# فرستادنِ LANGAR به GitHub و کلون روی VPS

> من نمی‌توانم مستقیم به گیت‌هابت وصل شوم (کانکتورِ امن نیست و نباید توکنت را لمس کنم).
> این مراحل را خودت اجرا کن — هر بلاک کپی‑پیست است.

## ⚠️ امنیت اول
داخلِ پروژه `.env`، `env`، `langar/.env`، `langar-pro/.env`، `*.db` با کلیدِ واقعی هست.
`.gitignore` آن‌ها را نادیده می‌گیرد، ولی **قبل از commit حتماً چک کن**:

```powershell
cd "C:\Users\Armin\Documents\Claude\Projects\AI Farm\AI-sume"
Remove-Item -Recurse -Force .git -ErrorAction SilentlyContinue   # پاک‌کردنِ .gitِ نیمه‌خراب
git init
git add .
git status        # ← مطمئن شو هیچ .env یا env یا .db در لیست نیست
```

اگر اشتباهی `.env` در لیست بود، `git rm --cached <file>` بزن و دوباره چک کن. وقتی لیست تمیز بود:

```powershell
git commit -m "LANGAR unified: core + langar-pro + upgrades (retrieval/BrainRouter/ACE)"
```

## راهِ A — با GitHub CLI (ساده‌ترین)
اگر `gh` نصب است (`winget install GitHub.cli`):

```powershell
gh auth login                       # یک‌بار، در مرورگر
gh repo create langar --private --source=. --remote=origin --push
```

تمام. ریپو ساخته و push شد.

## راهِ B — دستی (بدونِ gh)
۱) در github.com یک ریپوی **private** خالی بساز به نامِ `langar` (بدونِ README/gitignore).
۲) بعد:

```powershell
git branch -M main
git remote add origin https://github.com/<USERNAME>/langar.git
git push -u origin main
```

اگر رمز خواست، به‌جای رمز یک **Personal Access Token** بده
(GitHub → Settings → Developer settings → Tokens، با scope=`repo`).

## کلون روی VPS
بعدِ SSH به سرور:

```bash
git clone https://github.com/<USERNAME>/langar.git
cd langar
cp .env.example .env && nano .env     # پرکردنِ BOT_TOKEN/OWNER_ID/POSTGRES_PASSWORD
bash deploy.sh                        # build + smoke test
```

> چون `.env` در گیت نیست، روی VPS باید دوباره `.env` را پر کنی — این درست و امن است.
> هر بار تغییر دادی: روی لپ‌تاپ `git add . && git commit -m "..." && git push`،
> روی VPS `git pull && docker compose -f docker-compose.unified.yml up -d --build`.
