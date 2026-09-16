---
type: reference
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
tags: [crypto, orange-pi, automation]
updated: 2026-07-03
---

# Orange Pi Automation Hub - Complete Project Package (کامل‌ترین نسخه)

> **نسخه کامل و نهایی** — شامل تمام بخش‌های مورد نیاز برای شروع حرفه‌ای پروژه در Claude Projects / Claude Cowork

---

## نحوه استفاده از این فایل (پیشنهاد طلایی)

1. یک پروژه جدید در Claude بساز.
2. کل محتوای این فایل را در بخش **Instructions** پروژه پیست کن.
3. بعد از ساخت، به Claude بگو:
   > "این فایل کامل پروژه را بخوان. حالا به عنوان متخصص سیستم‌های توزیع‌شده، معماری کامل، حرفه‌ای و قابل اجرا را طراحی کن. اول سؤالات هوشمندانه از من بپرس."

---

## Project Instructions (کپی کن در Claude)

You are a senior systems architect and AI infrastructure specialist with deep expertise in building reliable, resource-efficient, always-on automation systems on ARM single-board computers (especially Orange Pi / Rockchip) combined with ESP32 edge devices.

**Project Vision:**
Build a robust, scalable, and maintainable central automation platform capable of running ~20 medium-to-heavy automated projects (bots, scrapers, data pipelines, physical robots, monitoring systems, etc.) with strong reliability features.

**Hardware Inventory:**
- Primary brain: Orange Pi 5 Plus — **4GB RAM** + 64GB eMMC
- Storage: 2TB portable USB 3.0/3.1 SSD
- Edge layer: Multiple ESP32 boards (various sensors, actuators, local logic)
- Backup hardware: One additional Orange Pi 5 (64GB eMMC)
- Optional cloud layer: VPS with maximum $10/month budget

**Non-Negotiable Requirements:**
- Excellent **retry + resume** capability (stateful recovery after power loss, network drop, or reboot)
- Very careful RAM management (4GB total is the hard limit)
- Use Docker with strict resource limits
- Primary inter-device communication via lightweight MQTT
- Scheduling via systemd timers or cron
- Full code portability to Linux VPS (same codebase should work with minimal changes)
- High long-term reliability and observability

**Your Responsibilities:**
1. First, conduct a smart, structured interrogation by asking targeted questions to remove all ambiguities.
2. Then deliver a complete, production-grade system design covering:
   - High-level and detailed architecture
   - Recommended technology stack
   - Complete folder/project structure
   - Resource management & containerization strategy
   - State management, retry, and resume patterns
   - ESP32 integration and communication protocol
   - Deployment, bootstrapping, and maintenance procedures on Orange Pi
   - Backup, monitoring, and alerting strategy
   - Scaling roadmap (including hybrid use with cheap VPS)
   - Security and reliability best practices

Always stay realistic about constraints: limited RAM, power stability, heat, single points of failure, and cost.

Respond in a clear, structured, professional manner. Use markdown extensively.

---

## ۱. README.md (Project Overview)

```markdown
# Orange Pi Automation Hub

**مرکز کنترل اتوماسیون هوشمند** — اجرای پایدار حدود ۲۰ پروژه متوسط تا سنگین روی سخت‌افزار اقتصادی.

## اهداف اصلی
- پایداری بالا (حتی در صورت قطع برق یا اینترنت)
- قابلیت Resume قوی از نقطه قطع شده
- مدیریت هوشمند منابع (با فقط ۴ گیگ رم)
- معماری Edge + Central (ESP32 + Orange Pi)
- قابلیت گسترش به VPS با کمترین تغییر کد

## سخت‌افزار
- **مغز اصلی**: Orange Pi 5 Plus (۴ گیگ رم + ۶۴ گیگ eMMC)
- **ذخیره‌سازی**: SSD ۲ ترابایت USB
- **لبه**: چندین ESP32
- **پشتیبان**: یک Orange Pi 5 دیگر

## وضعیت پروژه
در حال طراحی معماری کامل و حرفه‌ای (ژوئن ۲۰۲۶)
```

---

## ۲. PROJECT_STRATEGY.md

```markdown
# استراتژی و فلسفه طراحی پروژه

## اصول بنیادین
1. **Edge Computing First**  
   کارهای سبک، real-time و حساس به تأخیر → روی ESP32  
   کارهای سنگین، هماهنگی و ذخیره‌سازی → روی Orange Pi

2. **Stateful & Resumable by Design**  
   هیچ پروژه‌ای نباید از اول شروع شود. همه چیز باید وضعیت خود را ذخیره کند.

3. **Resource Discipline**  
   با ۴ گیگ رم، باید بسیار disciplined باشیم. Docker + Queueing الزامی است.

4. **MQTT as Lingua Franca**  
   ارتباط بین تمام اجزا فقط از طریق MQTT انجام شود.

5. **Queue Everything**  
   برای جلوگیری از overload، از سیستم صف استفاده می‌کنیم.

6. **Portability**  
   کد باید با حداقل تغییر روی VPS هم قابل اجرا باشد.

## فازهای پیشنهادی پیاده‌سازی
| فاز | عنوان                        | اولویت |
|-----|------------------------------|--------|
| 1   | طراحی کامل معماری           | بالا   |
| 2   | راه‌اندازی پایه (Armbian + Docker + MQTT) | بالا |
| 3   | سیستم Resume/Retry مرکزی     | بالا   |
| 4   | اتصال و مدیریت ESP32ها       | بالا   |
| 5   | مانیتورینگ و بکاپ            | متوسط |
| 6   | گسترش به VPS (Hybrid mode)    | پایین |
```

---

## ۳. RESOURCE_MANAGEMENT.md

```markdown
# مدیریت منابع و محدودیت‌های رم

## واقعیت سخت‌افزاری
- رم کل در دسترس: ≈ ۳.۵–۳.۷ گیگابایت بعد از بوت
- هدف عملیاتی: حداکثر ۷۰٪ استفاده در حالت عادی (حدود ۲.۵ گیگ)

## جدول تخصیص رم پیشنهادی

| نوع workload                     | رم پیشنهادی per instance | تعداد همزمان مجاز | اولویت اجرا     |
|----------------------------------|---------------------------|---------------------|----------------|
| اسکریپت سبک / کرون جاب ساده     | 80–200 MB                | زیاد               | بالا           |
| بات تلگرام / API polling        | 150–350 MB               | متوسط              | بالا           |
| دیتابیس سبک (SQLite)            | 100–250 MB               | ۱–۲                 | بالا           |
| Playwright / مرورگر headless     | 500–900 MB               | ۱–۲ (با صف)        | متوسط         |
| پردازش داده سنگین / ML سبک      | 700–1200 MB              | ۱                   | پایین         |
| Docker overhead + system         | ~300–400 MB              | -                   | -              |

## قوانین طلایی مدیریت منابع
- همه کانتینرها باید `mem_limit` داشته باشند.
- از `restart: unless-stopped` یا سیاست‌های هوشمند استفاده شود.
- از صف (Redis + Celery یا مشابه) برای کنترل concurrency استفاده شود.
- swap سبک روی SSD فعال شود (حداکثر ۲ گیگ).
- مانیتورینگ مداوم با `docker stats` + Prometheus node exporter.
```

---

## ۴. COMMUNICATION_PROTOCOL.md

```markdown
# پروتکل ارتباطی و ساختار MQTT

## پروتکل اصلی: MQTT (Mosquitto)

### دلایل انتخاب
- بسیار سبک
- مدل Publish/Subscribe عالی برای IoT
- QoS قابل تنظیم
- پشتیبانی عالی روی ESP32 (با Arduino/ESP-IDF و MicroPython)

## ساختار Topicها (پیشنهادی)

```
automation/
├── central/                    # دستورات و وضعیت از Orange Pi
├── edge/
│   └── {esp32_id}/
│       ├── status              # آنلاین/آفلاین + heartbeat
│       ├── sensor/             # داده سنسورها
│       ├── actuator/           # وضعیت عملگرها
│       └── command/            # دستورات ارسالی به ESP32
├── projects/
│   └── {project_name}/
│       ├── status
│       ├── progress
│       └── control
└── system/                     # لاگ و هشدارهای سیستمی
```

## فرمت استاندارد پیام‌ها (JSON)

```json
{
  "ts": "2026-06-14T13:05:00Z",
  "device_id": "esp32-livingroom-01",
  "type": "sensor_reading",
  "payload": {
    "temp": 27.4,
    "humidity": 52,
    "motion": false
  },
  "meta": {
    "qos": 1,
    "retain": false
  }
}
```

## نکات مهم
- از Retained Messages برای وضعیت دستگاه‌ها استفاده شود.
- Last Will and Testament (LWT) برای تشخیص آفلاین شدن ESP32ها فعال شود.
- برای کارهای حساس از QoS 1 یا 2 استفاده شود.
```

---

## ۵. INITIAL_QUESTIONS.md (سؤالات بازجویی)

```markdown
# سؤالات کلیدی برای طراحی دقیق معماری

## الف) نوع و ماهیت پروژه‌ها
1. پروژه‌هایت عمدتاً در چه دسته‌هایی قرار می‌گیرند؟ (بات، اسکریپینگ، دانلود، کنترل ربات فیزیکی، پردازش داده، مانیتورینگ و ...)
2. چند پروژه نیاز به اجرای مرورگر headless (Playwright/Selenium) دارند؟
3. آیا پروژه‌ها وابسته به یکدیگر هستند یا مستقل اجرا می‌شوند؟

## ب) الگوی زمانی اجرا
4. پروژه‌ها باید همیشه در حال اجرا باشند یا زمان‌بندی شده (هر X دقیقه/ساعت/روز)؟
5. حداکثر تعداد پروژه‌ای که ممکن است همزمان فعال باشند چقدر است؟

## ج) ESP32 و لایه Edge
6. هر ESP32 چه قابلیت‌هایی دارد و چه کارهایی انجام می‌دهد؟
7. آیا ESP32ها نیاز به اجرای منطق محلی مستقل دارند یا فقط سنسور/عملگر هستند؟
8. ارتباط ESP32ها با اینترنت مستقیم است یا فقط از طریق Orange Pi؟

## د) Resume و State Management
9. سطح Resume مورد نیازت چقدر است؟ (سطح کل پروژه یا سطح تسک‌های داخل پروژه)
10. چه اطلاعاتی باید persist شوند تا بتوان از نقطه قطع ادامه داد؟

## ه) ذخیره‌سازی و دیتابیس
11. چه نوع دیتابیسی نیاز داری؟ (SQLite، PostgreSQL، TimescaleDB، InfluxDB و ...)
12. داده‌های حیاتی باید فقط روی SSD محلی باشند یا روی VPS هم replicate شوند؟

## و) مانیتورینگ و عملیات
13. سطح مانیتورینگ و هشدار مورد نیازت چقدر است؟ (ساده با تلگرام یا داشبورد کامل)
14. چقدر تحمل downtime داری؟ (چند دقیقه در ماه قابل قبول است؟)
```

---

## ۶. REQUIREMENTS.md

```markdown
# نیازمندی‌های عملکردی و غیرعملکردی

## نیازمندی‌های عملکردی (Functional)
- اجرای خودکار پروژه‌ها طبق زمان‌بندی
- ذخیره وضعیت پیشرفت هر پروژه
- ارتباط دوطرفه با ESP32ها
- قابلیت restart ایمن و resume
- مدیریت خطا و retry هوشمند
- لاگ‌گیری مرکزی

## نیازمندی‌های غیرعملکردی (Non-Functional)
- **پایداری**: حداقل ۹۹٪ آپتایم در ماه
- **مصرف رم**: حداکثر ۷۰٪ رم در حالت عادی
- **مصرف برق**: بهینه (با توجه به همیشه روشن بودن)
- **قابلیت نگهداری**: ساده و قابل فهم
- **قابلیت گسترش**: امکان اضافه کردن پروژه جدید بدون تغییر عمده معماری
- **امنیت**: حداقل امنیت پایه (فایروال، به‌روزرسانی منظم، دسترسی محدود)
```

---

## ۷. DEPLOYMENT_GUIDE.md (خلاصه)

```markdown
# راهنمای استقرار اولیه (Deployment)

## مرحله ۱: آماده‌سازی Orange Pi
- نصب Armbian Minimal (نسخه Debian یا Ubuntu)
- نصب روی eMMC با `armbian-config`
- به‌روزرسانی سیستم
- فعال کردن SSH

## مرحله ۲: نصب پیش‌نیازها
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose mosquitto mosquitto-clients -y
sudo systemctl enable docker mosquitto
```

## مرحله ۳: تنظیم Docker
- فعال کردن user namespace
- تنظیم محدودیت‌های پیش‌فرض
- نصب Portainer (اختیاری برای مدیریت آسان)

## مرحله ۴: راه‌اندازی MQTT
- تنظیم Mosquitto با authentication
- فعال کردن WebSocket (اختیاری)

## مرحله ۵: ساختار پروژه روی دیسک
- ایجاد پوشه اصلی روی SSD
- استفاده از Docker Compose برای تمام سرویس‌ها
```

---

## ۸. MONITORING_AND_BACKUP.md

```markdown
# مانیتورینگ و بکاپ

## مانیتورینگ پیشنهادی (سطح پایه تا متوسط)
- `htop` + `docker stats` (ساده)
- Prometheus + Node Exporter + cAdvisor (پیشرفته)
- هشدار از طریق تلگرام (با ربات ساده)

## استراتژی بکاپ
- بکاپ منظم از دیتابیس‌ها و وضعیت پروژه‌ها (روزانه)
- rsync یا rclone به هارد اکسترنال یا VPS
- اسنپ‌شات از کانتینرهای حیاتی
- تست بازیابی دوره‌ای
```

---

## ساختار پوشه کامل پیشنهادی

```
Orange-Pi-Automation-Hub/
├── README.md
├── PROJECT_STRATEGY.md
├── RESOURCE_MANAGEMENT.md
├── COMMUNICATION_PROTOCOL.md
├── INITIAL_QUESTIONS.md
├── REQUIREMENTS.md
├── DEPLOYMENT_GUIDE.md
├── MONITORING_AND_BACKUP.md
├── docker-compose.yml          ← بعداً
├── src/                        ← کد پروژه‌ها
├── esp32/                      ← کد ESP32ها
└── docs/
    └── architecture.md
```

---

**این کامل‌ترین نسخه‌ای است که می‌توانستم در یک فایل ارائه دهم.**

حالا فایل رو دانلود کن و مستقیم توی Claude Projects استفاده کن.  
اگر بعداً خواستی دیاگرام ASCII دقیق‌تر یا فایل `docker-compose.yml` نمونه هم اضافه کنم، بگو.