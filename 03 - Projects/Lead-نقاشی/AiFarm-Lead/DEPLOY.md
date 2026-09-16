# Brushline -- GitHub + Server Deploy Runbook

> هدف: کل پروژه روی یک repo **خصوصی** GitHub، و سرور (VPS) با **deploy key فقط-خواندنی**
> از GitHub `git pull` کند. هیچ secret و هیچ PII روی GitHub نمی‌رود (INV-2).

**فرض‌ها:** سرور Linux است (Ubuntu/Debian). روی ویندوز Git for Windows نصب است.
repo root = پوشه‌ی `AiFarm-Lead`. اپلیکیشن در
`Ai farm- sister Painting/brushline/60_code`.

> امنیت قبل از هر چیز: `.env` (سه کلید واقعی) و `data/` (DB با PII) با `.gitignore`
> از git حذف شده‌اند. هرگز آن‌ها را force-add نکن.

---

## A) یک‌بار: ساخت repo خصوصی روی GitHub

**روش UI:** github.com -> New repository -> نام مثلا `brushline` -> **Private** ->
بدون README/gitignore (چون از قبل داریم) -> Create.

**یا با gh CLI (اگر نصب است):**
```bash
gh repo create brushline --private --source . --remote origin --push
```
(اگر این را زدی، بخش B لازم نیست.)

---

## B) local (روی ویندوز، در Git Bash): init + commit + push

> این مراحل را روی کامپیوتر ویندوزِ خودت اجرا کن (Git for Windows لازم است).
> git داخل پوشه‌ی `AiFarm-Lead` اجرا می‌شود. فایل‌های `.gitignore` / `.gitattributes`
> / `deploy.sh` / `DEPLOY.md` از قبل آماده‌اند.

```bash
cd "/c/Users/Armin/Desktop/AI-sume/AGI-Personal/AiFarm-Lead"

git init -b main
git config user.email "australianpmnsw@gmail.com"
git config user.name  "Sume"
git add -A
```

**قبل از commit حتما این safety-check را بزن (نباید چیزی چاپ شود):**
```bash
git ls-files | grep -Ei '(^|/)\.env$|\.db$|/data/|KILL_SWITCH|__pycache__|\.pyc$'
```
- خروجی خالی = امن، ادامه بده.
- اگر چیزی چاپ شد = STOP. آن فایل اشتباها staged شده؛ `.gitignore` را چک کن و
  `git rm --cached <file>` بزن، بعد دوباره check کن.

```bash
git commit -m "Brushline: initial import (Phase 2 lead-path slice)"
```

**اتصال به GitHub و push:**
```bash
git remote add origin git@github.com:<YOUR_GH_USERNAME>/brushline.git
git push -u origin main
```

> اگر SSH روی ویندوز ست نیست، با HTTPS:
> `git remote add origin https://github.com/<YOUR_GH_USERNAME>/brushline.git`
> سپس `git push -u origin main` (GitHub یوزرنیم/PAT می‌خواهد).

> نکته: راه‌اندازی git داخل ابزار Cowork روی این پوشه ممکن نیست (نوع mount با
> عملیات اتمیکِ git سازگار نیست)، به همین خاطر init/commit را خودت روی ویندوز می‌زنی.

---

## C) سرور (VPS): deploy key فقط-خواندنی + clone

### 1. نصب پیش‌نیاز
```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip
```

### 2. ساخت deploy key روی سرور
```bash
ssh-keygen -t ed25519 -C "brushline-deploy@vps" -f ~/.ssh/brushline_deploy -N ""
cat ~/.ssh/brushline_deploy.pub      # این public key را کپی کن
```

### 3. افزودن public key به GitHub (read-only)
GitHub -> repo `brushline` -> Settings -> **Deploy keys** -> Add deploy key ->
عنوان: `vps-brushline` -> محتوای `.pub` را paste کن -> **Allow write access را تیک نزن**
(فقط خواندن) -> Add.

### 4. معرفی کلید به SSH برای GitHub
```bash
cat >> ~/.ssh/config <<'SSHCFG'
Host github-brushline
    HostName github.com
    User git
    IdentityFile ~/.ssh/brushline_deploy
    IdentitiesOnly yes
SSHCFG
chmod 600 ~/.ssh/config
```

### 5. clone با همان host alias
```bash
git clone github-brushline:<YOUR_GH_USERNAME>/brushline.git ~/brushline-repo
```

### 6. ساخت .env روی سرور (فقط همین‌جا، نه در git)
```bash
cd ~/brushline-repo/"Ai farm- sister Painting/brushline/60_code"
cp .env.example .env
nano .env     # کلیدهای واقعی ANTHROPIC/TELEGRAM/SERPER و ABN/business را پر کن
```

---

## D) deploy روتین

اسکریپت آماده است: `Ai farm- sister Painting/brushline/60_code/deploy.sh`
هر بار که خواستی آخرین کد را بگیری و ری‌استارت کنی:

```bash
cd ~/brushline-repo/"Ai farm- sister Painting/brushline/60_code"
./deploy.sh
```
اسکریپت: `git reset --hard origin/main` -> venv + `pip install` -> چک وجود `.env`
-> AST check -> restart (systemd `--user` unit به نام `brushline` اگر باشد).

**اختیاری -- pull خودکار هر ۵ دقیقه با cron:**
```bash
crontab -e
# خط زیر را اضافه کن:
*/5 * * * * cd "$HOME/brushline-repo/Ai farm- sister Painting/brushline/60_code" && ./deploy.sh >> "$HOME/brushline-deploy.log" 2>&1
```

> برای auto-deploy واقعی (push -> سرور خودش آپدیت شود) همین cron کافی است:
> سرور هر ۵ دقیقه origin/main را می‌گیرد. ساده و بدون webhook.

---

## E) چک‌لیست امنیتی (مهم)

- [ ] repo حتما **Private** است.
- [ ] deploy key روی سرور **بدون write access** اضافه شد.
- [ ] `.env` و `data/` هرگز در `git ls-files` نیستند.
- [ ] اگر یک کلید لو رفت: فورا rotate کن (Anthropic/Telegram/Serper) و در `.env` سرور آپدیت کن.
- [ ] backup جدا از سرور برای `data/*.db` (در git نیست -> جداگانه بکاپ بگیر).
- [ ] private key سرور (`~/.ssh/brushline_deploy`) را هرگز جابجا/کپی نکن.

