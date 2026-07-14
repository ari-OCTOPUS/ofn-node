# RUNBOOK — infra-control
> صفر تا اولین `stackctl up brushline` — راهنمای راه‌اندازی VPS

## پیش‌نیازها
- VPS Ubuntu 22.04 یا 24.04 (4GB RAM / 2 vCPU)
- دسترسی SSH root یا sudo
- دامنه با DNS به IP سرور (برای TLS)
- اکانت GitHub با دسترسی به repoهای پروژه
- توکن Telegram bot (از BotFather)

---

## مرحله ۱ — نصب Docker

```bash
# روی سرور (به‌عنوان root):
curl -fsSL https://raw.githubusercontent.com/GITHUB_USERNAME/infra-control/main/scripts/install-docker.sh \
    | sudo bash

# یا اگر repo را clone کرده‌ای:
sudo bash /opt/infra-control/scripts/install-docker.sh
```

بعد از نصب، log out و log in کن تا membership گروه docker اعمال شود.

```bash
docker run hello-world   # باید کار کند
```

---

## مرحله ۲ — clone کردن infra-control

```bash
mkdir -p /opt/projects
cd /opt
git clone git@github.com:GITHUB_USERNAME/infra-control.git
chmod +x /opt/infra-control/stackctl
```

### افزودن stackctl به PATH (اختیاری)
```bash
ln -sf /opt/infra-control/stackctl /usr/local/bin/stackctl
```

---

## مرحله ۳ — پیکربندی .env

```bash
cd /opt/infra-control
cp .env.example .env
nano .env   # پر کردن مقادیر:
            # DOMAIN، ACME_EMAIL، CF_API_TOKEN، CONTROL_BOT_TOKEN، ALLOWED_CHAT_IDS
```

**ALLOWED_CHAT_IDS:** Chat ID خودت را پیدا کن:
```
بفرست به @userinfobot در تلگرام، عدد id را کپی کن.
```

---

## مرحله ۴ — آماده‌سازی Traefik TLS

```bash
touch /opt/infra-control/traefik/acme.json
chmod 600 /opt/infra-control/traefik/acme.json
```

> ⚠️ بدون `chmod 600`، Traefik خطا می‌دهد و TLS کار نمی‌کند.

---

## مرحله ۵ — راه‌اندازی infra-control stack

```bash
cd /opt/infra-control
docker compose up -d

# بررسی:
docker compose ps
docker compose logs -f traefik   # باید TLS certificate بگیرد
```

بعد از ۱–۲ دقیقه، Uptime Kuma روی `https://status.yourdomain.com` در دسترس است.

---

## مرحله ۶ — clone و راه‌اندازی Brushline

```bash
mkdir -p /opt/projects/brushline
cd /opt/projects
git clone git@github.com:GITHUB_USERNAME/brushline.git brushline

# کپی .env از secrets یا ساختن دستی
cd brushline
cp .env.example .env
nano .env   # پر کردن ANTHROPIC_API_KEY، TELEGRAM_BOT_TOKEN، بقیه

# اولین بار: build local (قبل از اینکه CI image بسازد)
docker compose build

# بالا آوردن:
stackctl up brushline

# بررسی:
stackctl status brushline
stackctl logs brushline
```

---

## مرحله ۷ — تست control-bot

در تلگرام به bot خودت پیام بده:
```
/start
/status
/up brushline
```

اگر پاسخ گرفتی — سیستم کار می‌کند.

---

## مرحله ۸ — اتصال CI/CD (GitHub Actions)

### الف) یک deploy user بساز (روی سرور)
```bash
useradd -m -s /bin/bash deploy
usermod -aG docker deploy
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
```

### ب) کلید SSH برای GitHub Actions
```bash
# روی ماشین محلی:
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key -N ""

# کلید عمومی را روی سرور اضافه کن:
cat ~/.ssh/deploy_key.pub >> /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# کلید خصوصی را در GitHub Secrets اضافه کن:
# Repository → Settings → Secrets → Actions → New secret
# Name: DEPLOY_SSH_KEY   Value: محتوای deploy_key (خصوصی)
```

### ج) سرور را در GitHub Secrets ثبت کن
```
DEPLOY_HOST     = IP سرور
DEPLOY_USER     = deploy
GHCR_TOKEN      = GitHub Personal Access Token (packages:read/write)
```

بعد از این مرحله، هر push به main، CI را trigger می‌کند و deploy اتوماتیک می‌شود.

---

## عملیات روزانه

```bash
# وضعیت همه‌ی پروژه‌ها
stackctl status

# لاگ آنلاین
stackctl logs brushline -f

# deploy دستی (اگر CI نیاز بود)
stackctl deploy brushline

# kill switch فوری
stackctl kill brushline

# kill همه‌ی پروژه‌ها
stackctl kill --all

# audit log
tail -f /var/log/stackctl/audit.jsonl | python3 -m json.tool
```

---

## اضافه کردن پروژه‌ی جدید

1. `projects.yaml` را ویرایش کن و پروژه‌ی جدید را اضافه کن.
2. repo را در `/opt/projects/PROJECT_NAME` clone کن.
3. `Dockerfile` و `docker-compose.yml` برای پروژه بساز (الگوی brushline را ببین).
4. `stackctl up PROJECT_NAME`

---

## عیب‌یابی

| مشکل | راه‌حل |
|---|---|
| TLS certificate نمی‌گیرد | `chmod 600 traefik/acme.json`، DNS به IP سرور اشاره می‌کند؟ |
| control-bot جواب نمی‌دهد | `docker compose logs control-bot`، `ALLOWED_CHAT_IDS` درست است؟ |
| `stackctl up` خطا می‌دهد | `docker compose ps` در directory پروژه، `.env` کامل است؟ |
| deploy rollback می‌کند | `stackctl logs PROJECT -f` برای بررسی خطا |
| kill switch فعال است | `rm /opt/infra-control/.kill_all` سپس `stackctl up PROJECT` |

---

## امنیت

- `.env` هرگز commit نشود (`.gitignore` سخت).
- برای production: SOPS+age (کلید age در `/root/.age/key.txt`، فایل‌های encrypt‌شده در `secrets/`).
- audit log: `/var/log/stackctl/audit.jsonl` (hash-chained، دستکاری‌ناپذیر).
- SSH: فقط key-based، `PasswordAuthentication no` در `/etc/ssh/sshd_config`.
- Traefik dashboard فقط از IP داخلی یا VPN (middleware auth-basic کافی نیست برای public).
