# Server Architecture — Multi-Project AI Automation VPS (v1.0)

> نسخه: 2026-06-30 · نویسنده: design pass با Sume
> هدف: یک VPS که چند پروژه‌ی AI را میزبانی کند؛ GitHub منبع حقیقت؛ deploy کاملاً
> اتوماتیک ولی gated؛ کنترل از طریق Telegram (bot + userbot) + یک root CLI؛
> طراحی آزاد/منسجم و آماده‌ی تکامل تا 2028–2035 (مسیر مهاجرت به k8s باز است).

---

## 1) خلاصه‌ی سریع — این چیست و چه می‌گیری؟

یک «control plane» سبک روی VPS که:
- هر پروژه را به‌صورت **container** اجرا می‌کند (isolation کامل dependency/port).
- یک **root script (`stackctl`)** برای up/down/restart/status/logs/deploy همه‌ی پروژه‌ها.
- یک **Telegram bot** امن برای کنترل از موبایل + یک **userbot (Telethon)** برای کارهایی
  که واقعاً اکانت کاربر لازم دارند.
- **CI/CD کاملاً اتوماتیک**: push به GitHub → تست → build → deploy → health-check →
  rollback خودکار اگر خراب بود.
- secretها رمزنگاری‌شده در git (**SOPS + age**) — نه plaintext، نه بیرونِ نسخه‌بندی.
- monitoring سبک (Uptime Kuma + Dozzle) و audit log برای هر اکشن (هم‌راستا با INV-3).

نتیجه: هر AI روی repo خودش کار می‌کند، main محافظت‌شده است، و هیچ چیز بدون عبور از
gate تست/health روی سرور اجرا نمی‌شود.

---

## 2) تحلیل — مسئله، قید، ریسک، فرض

**Problem:** چند پروژه‌ی مستقل (stackهای متفاوت Python/Node)، چند AI سازنده،
یک سرور، نیاز به on/off و اتوماسیون منسجم و امن.

**Constraints:**
- سرور Linux (Ubuntu فرض شد). منابع محدود VPS.
- بودجه پایین (Brushline هدف AUD $15–40/ماه برای API؛ VPS جداست).
- چند AI = ریسک تغییر هم‌زمان و خرابی.
- secret/PII هرگز نباید لو برود (درس commit خانه: 327k فایل + private key).

**Assumptions (تصحیح کن اگر غلط):**
- فعلاً ~۲–۶ پروژه، هرکدام سبک (چند صد MB RAM).
- یک VPS واحد کافی است (نه چند سرور / نه k8s فعلاً).
- تو تنها operator انسانی هستی؛ AIها از طریق repo کار می‌کنند نه SSH مستقیم.

**Risks و mitigation:**
| ریسک | اثر | mitigation |
|---|---|---|
| commit خراب یک AI | کل پروژه down | CI test gate + health-check + auto-rollback |
| نشت secret | فاجعه | SOPS+age، .gitignore سخت، scan در CI |
| یک پروژه منابع را می‌بلعد | بقیه down | per-container `mem_limit`/`cpus` |
| userbot خلاف ToS / بن اکانت | از دست رفتن اکانت | userbot least-privilege، جدا از کنترل، فقط کار لازم |
| vendor lock-in | مهاجرت سخت | همه‌ی لایه‌ها OSS؛ deploy logic در `stackctl` نه در Actions |

---

## 3) راه‌حل — معماری پیشنهادی

### 3.1 ساختار repo (هیبرید — انتخاب تو)
```
GitHub (org یا account شخصی)
├── infra-control          ← مغز سیستم (root script, bot, userbot, compose, CI)
├── brushline              ← پروژه‌ی بزرگ، repo مستقل
├── project-x              ← پروژه‌ی بزرگ بعدی، repo مستقل
└── mono-misc              ← پروژه‌های کوچک، هرکدام یک پوشه‌ی containerized
```
- **پروژه‌ی بزرگ = repo مستقل** (AI اختصاصی، CI اختصاصی، تاریخچه‌ی تمیز).
- **پروژه‌های کوچک = monorepo `mono-misc`** با پوشه‌های جدا، هرکدام Dockerfile خودش.
- **`infra-control`** = جایی که root script + botها + compose سراسری + workflows زندگی می‌کنند.

### 3.2 runtime: Docker Compose (پیشنهاد من برای «آماده‌ی 2028–2035»)
چرا Docker و نه systemd/pm2: **isolation کامل** (هر پروژه با نسخه‌ی Python/Node و
dependency خودش)، **on/off یکدست** (`up -d` / `down`)، **portable** (هر VPS، و مسیر
مهاجرت به Kubernetes در آینده باز است)، و **آزاد/OSS** (بدون lock-in؛ قابل تعویض با Podman).

```
VPS
├── Traefik (reverse proxy)     ← TLS خودکار، روتینگ APIها بر اساس دامنه/مسیر
├── infra-control/
│   ├── stackctl                ← root CLI کنترل
│   ├── control-bot (container) ← Telegram bot
│   ├── userbot (container)     ← Telethon، least-privilege
│   └── monitoring/             ← uptime-kuma + dozzle (container)
├── brushline (container[s])
├── project-x (container[s])
└── mono-misc/* (container[s])
```
- **Traefik** جلوی همه؛ هر سرویس با label خودش route و TLS می‌گیرد (دینامیک، بدون
  ادیت دستی nginx). جایگزین ساده‌تر: **Caddy** (اگر تعداد سرویس کم است).
- هر پروژه `docker-compose.yml` خودش را دارد؛ `stackctl` آن‌ها را با یک registry
  مرکزی (`projects.yaml`) مدیریت می‌کند.

### 3.3 لایه‌ی کنترل: root script + bot + userbot
**`stackctl`** (تک‌منبعِ منطق کنترل، Python یا bash) روی سرور:
```
stackctl up <project>        # docker compose -p <project> up -d
stackctl down <project>      # ... down
stackctl restart <project>
stackctl status [project]    # وضعیت + health
stackctl logs <project> [-f]
stackctl deploy <project>    # pull + build + up + health + (rollback)
stackctl kill <project>      # kill switch فوری (INV-3)
stackctl kill --all          # global kill switch
```
**Telegram bot (BotFather)** = سطح کنترل امن: دکمه‌های inline برای up/down/status/logs
هر پروژه؛ فقط chat ID خودت مجاز؛ هر اکشن audit-log می‌شود. زیر کاپوت `stackctl` صدا می‌زند.

**Userbot (Telethon، اکانت جدا)** = فقط برای کارهایی که bot نمی‌تواند (خواندن کانال‌ها،
اتوماسیون‌های نیازمند اکانت کاربر). جدا از کنترل، least-privilege، در container ایزوله.
> ⚠️ ToS: userbot در بعضی کاربردها خلاف قوانین تلگرام است و ریسک بن اکانت دارد.
> فقط برای کار مشخص و کم‌خطر استفاده شود؛ هرگز برای کنترل زیرساخت.

### 3.4 deploy: کاملاً اتوماتیک + gated (CI/CD)
به‌ازای هر repo، `.github/workflows/ci.yml`:
```
push به main
   → 1. test  (AST + unit tests؛ Brushline: همان test_phase*.py)
   → 2. secret scan (gitleaks)
   → 3. build  (docker build)
   → 4. push   (image به GHCR — GitHub Container Registry)
   → 5. trigger deploy روی سرور (webhook امن یا SSH → stackctl deploy <project>)
   → 6. health-check (HTTP 200 / container healthy ظرف N ثانیه)
   → 7. اگر ناسالم → rollback به image قبلی + alert در Telegram
```
این «کاملاً اتوماتیک» است (تو هیچ کلیکی نمی‌کنی) ولی **gated**: کد خراب هرگز live
نمی‌ماند. این نسخه‌ی امنِ خواسته‌ی توست، نه auto-pull کور.

### 3.5 مدیریت secret (بحرانی)
- **هرگز در git به‌صورت plaintext.** `.gitignore` سخت (الان داریم).
- **SOPS + age**: فایل‌های secret **رمزنگاری‌شده** داخل `infra-control/secrets/` نسخه‌بندی
  می‌شوند؛ سرور با کلید خصوصی age رمزگشایی می‌کند. مزیت: نسخه‌بندی + امن + بدون vendor.
- جایگزین مدیریت‌شده (اختیاری): Infisical/Doppler (free tier) — ساده‌تر ولی vendor lock-in.
- در CI: **gitleaks** هر push را اسکن می‌کند تا secret تصادفی commit نشود.

### 3.6 observability + governance
- **Uptime Kuma** (۱ container): مانیتور up/down هر سرویس + alert تلگرام.
- **Dozzle** (۱ container): دیدن لاگ همه‌ی containerها از یک UI وب.
- **audit log**: هر اکشن کنترل/deploy لاگ می‌شود (الگوی hash-chain Brushline قابل‌استفاده‌ی مجدد).
- **kill switch** سراسری و per-project (INV-3). **resource limit** per-container.
- **branch protection** روی main همه‌ی repoها؛ AIها روی branch کار می‌کنند، merge → CI.

---

## 4) پیاده‌سازی — قدم‌به‌قدم (فازبندی، نه همه با هم)

**Phase 0 — پایه (هفته ۱):**
1. VPS: نصب Docker + Docker Compose plugin.
2. `infra-control` repo: ساختار + `stackctl` + `projects.yaml` + Traefik compose.
3. Brushline را به اولین پروژه‌ی containerized تبدیل کن (Dockerfile + compose + healthcheck).
4. `stackctl up brushline` → پشت Traefik بالا بیاید.

**Phase 1 — کنترل (هفته ۲):**
5. Telegram control bot (container) با /up /down /status /logs + auth chat ID + audit.
6. SOPS+age برای secretهای Brushline؛ حذف .env دستی.

**Phase 2 — اتوماسیون deploy (هفته ۳):**
7. `ci.yml` برای Brushline: test → gitleaks → build → GHCR → deploy → health → rollback.
8. webhook/SSH امن سرور برای trigger؛ تست یک deploy کامل end-to-end.

**Phase 3 — بلوغ (هفته ۴+):**
9. Uptime Kuma + Dozzle + alertها.
10. userbot (Telethon) ایزوله برای کار مشخص.
11. resource limits + global kill switch + پروژه‌ی دوم برای اثبات الگو.

---

## 5) trade-off — چرا این، چرا نه بقیه (نمره ۱–۱۰)

**runtime:**
| گزینه | Cost | Complexity | Scalability | Maintainability | Security(isolation) | آماده‌ی آینده |
|---|---|---|---|---|---|---|
| **Docker Compose (پیشنهاد)** | 8 | 6 | 8 | 8 | 9 | 9 |
| systemd | 9 | 7 | 5 | 6 | 5 | 5 |
| pm2/supervisor | 9 | 8 | 5 | 6 | 4 | 4 |
| اسکریپت+tmux | 10 | 9 | 2 | 3 | 2 | 2 |

→ Docker بالاترین ROI برای «چند پروژه + آماده‌ی 2028–2035» (مسیر k8s باز، isolation، portable).

**deploy:**
| گزینه | امنیت | اتوماسیون | Complexity |
|---|---|---|---|
| **CI/CD gated (پیشنهاد)** | 9 | 9 | 6 |
| auto-pull کور | 3 | 9 | 3 |
| manual approve | 10 | 4 | 4 |

→ CI/CD gated: هم اتوماتیک کامل، هم امن. بهترین تعادل برای محیط چند-AI.

---

## 6) هزینه و vendor lock-in

**هزینه (تقریبی، USD → AUD @1.45):**
- VPS 4GB/2vCPU: ~$24 USD/ماه (~AUD $35) برای چند container سبک؛ 8GB ~$48 (~AUD $70) برای headroom.
- GHCR (registry): private رایگان (با سقف storage).
- GitHub Actions: 2000 دقیقه/ماه private رایگان (برای این مقیاس کافی).
- Traefik / SOPS+age / Uptime Kuma / Dozzle / gitleaks: همه **رایگان و OSS**.
- جمع نرم‌افزار اضافه: ~$0. هزینه‌ی غالب = VPS (~AUD $35–70/ماه)، جدا از هزینه‌ی API هر پروژه.

**vendor lock-in:**
- Docker/Compose: استاندارد باز، portable (low lock-in؛ قابل‌تعویض با Podman، مسیر k8s).
- GHCR + Actions: تا حدی GitHub-محور → mitigation: منطق deploy در `stackctl` بماند تا CI
  فقط آن را صدا بزند؛ image‌ها به هر registry قابل‌انتقال‌اند.
- SOPS/age/Traefik/Kuma/Dozzle: کاملاً OSS، بدون lock-in.

---

## 7) قدم بعدی (بلافاصله بعد از این)

1. تأیید فرض‌ها: تعداد پروژه‌ها، مشخصات VPS فعلی (RAM/CPU/provider)، و اینکه فعلاً
   چند پروژه آماده‌ی container شدن داری.
2. ساخت repo `infra-control` و نوشتن `stackctl` + Traefik + Dockerfile/compose برای Brushline (Phase 0).
3. اگر تأیید کنی، اسکلت `infra-control` (stackctl + projects.yaml + compose + ci.yml نمونه)
   را همین‌جا می‌سازم تا فقط روی سرور clone و اجرا کنی.

> یادداشت سازگاری: این طرح INV-1 (gate قبل از اجرا = CI/health)، INV-2 (secret/PII خارج
> از git، SOPS)، و INV-3 (kill switch + audit + cap) را در سطح کل سرور تعمیم می‌دهد.
