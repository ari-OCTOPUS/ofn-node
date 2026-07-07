---
type: reference
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
tags: [crypto, orange-pi, automation]
updated: 2026-07-03
---

# Orange Pi Automation Hub - Claude Project Setup

> **هدف این فایل:**  
> یک فایل کامل و آماده برای import در Claude Projects / Claude Cowork.  
> شامل تمام پیش‌نیازها، استراتژی، مدیریت منابع، پروتکل ارتباطی و سؤالات اولیه.

---

## نحوه استفاده از این فایل

1. یک پروژه جدید در Claude بساز.
2. محتوای این فایل را در بخش **Instructions** پروژه قرار بده (یا به عنوان فایل اولیه آپلود کن).
3. بعد از ساخت پروژه، به Claude بگو:  
   > "فایل‌های پروژه را بخوان و بر اساس آن‌ها معماری کامل سیستم را طراحی کن و از من سؤال بپرس."

---

## Project Instructions (کپی کن در بخش Instructions کلود)

You are an expert systems architect specializing in low-cost, reliable, always-on automation systems using single-board computers (Orange Pi) and microcontrollers (ESP32).

**Project Goal:**
Design and implement a robust central automation system capable of reliably running approximately 20 medium to heavy automated projects/tasks (bots, scrapers, data processors, robots, etc.) on limited hardware.

**Current Hardware:**
- Main brain: Orange Pi 5 Plus with **4GB RAM** + 64GB eMMC
- Storage: 2TB portable USB SSD
- Edge devices: Multiple ESP32 boards
- Extra hardware available: One more Orange Pi 5 (64GB eMMC)
- Optional: Cheap VPS (~$10/month) as complement or backup

**Key Requirements:**
- Strong **retry + resume** capability (if interrupted, continue from the last state)
- Resource-efficient design (especially with only 4GB RAM)
- Use Docker with proper resource limits
- Communication between central system and ESP32s via MQTT
- Scheduling with systemd timers or cron
- Code should be portable to Linux VPS
- High reliability for long-running tasks

**Your Role:**
Act as a senior systems architect. First, ask me smart and targeted questions to clarify ambiguities (type of projects, execution patterns, browser usage, databases, real-time needs, etc.).

After gathering information, provide a complete, practical, and well-structured system architecture including:
- Overall architecture (Central + Edge + Communication)
- Recommended tech stack
- Folder structure and project organization
- Resource management strategy for 4GB RAM
- Retry/Resume and state management approach
- ESP32 integration plan
- Deployment steps on Orange Pi
- Backup and monitoring strategy
- Scaling plan
- Hybrid usage with cheap VPS

Always consider real constraints: limited RAM, power consumption, reliability, and cost.

---

## ۱. README.md

```markdown
# Orange Pi Automation Hub

سیستم مرکزی اتوماسیون برای اجرای حدود ۲۰ پروژه متوسط تا سنگین روی سخت‌افزار کم‌هزینه.

## هدف پروژه
- اجرای پایدار و قابل اعتماد ۲۰ پروژه اتوماتیک
- قابلیت Resume/Restart قوی
- مدیریت بهینه منابع (به خصوص ۴ گیگ رم)
- ارتباط هوشمند با دستگاه‌های لبه (ESP32)
- قابلیت گسترش به VPS

## سخت‌افزار اصلی
- Orange Pi 5 Plus (۴ گیگ رم + ۶۴ گیگ eMMC)
- SSD ۲ ترابایت USB
- چندین ESP32
- امکان اضافه کردن Orange Pi دوم

## وضعیت فعلی
پروژه در فاز طراحی معماری اولیه قرار دارد.
```

---

## ۲. PROJECT_STRATEGY.md

```markdown
# استراتژی کلی پروژه

## فلسفه طراحی
ما به دنبال ساخت سیستمی هستیم که:
- **پایدار** باشد (حتی اگر برق برود یا اینترنت قطع شود)
- **بهینه** باشد (با ۴ گیگ رم کار کند)
- **قابل گسترش** باشد
- **قابل حمل** باشد (بتوان روی VPS هم اجرا کرد)

## اصول کلیدی

### 1. Edge + Central Architecture
- کارهای سبک و real-time → روی ESP32
- کارهای سنگین، هماهنگی و ذخیره‌سازی → روی Orange Pi

### 2. State Management & Resume
هر پروژه باید قابلیت ذخیره وضعیت فعلی را داشته باشد تا در صورت قطع شدن، از همان نقطه ادامه دهد.

### 3. Resource Awareness
تمام کانتینرها و فرآیندها باید محدودیت رم و CPU داشته باشند.

### 4. Communication via MQTT
ارتباط بین Orange Pi و ESP32ها فقط از طریق MQTT انجام شود (سبک و قابل اعتماد)。

### 5. Queue-based Execution
برای جلوگیری از اجرای همزمان بیش از حد پروژه‌ها، از سیستم صف (Queue) استفاده می‌کنیم。

## فازهای پیاده‌سازی پیشنهادی
1. طراحی معماری کامل
2. راه‌اندازی پایه (Armbian + Docker + MQTT)
3. پیاده‌سازی سیستم Resume/Retry
4. اتصال ESP32ها
5. تست پایداری
6. گسترش به VPS (در صورت نیاز)
```

---

## ۳. RESOURCE_MANAGEMENT.md

```markdown
# مدیریت منابع (Resource Management)

## محدودیت‌های سخت‌افزاری
- رم کل: ۴ گیگابایت
- هدف: حداکثر استفاده ۷۰-۷۵٪ رم در حالت عادی

## استراتژی مدیریت رم

| نوع کار                        | حداکثر رم مجاز     | تعداد همزمان پیشنهادی | توضیح                     |
|--------------------------------|---------------------|-------------------------|---------------------------|
| اسکریپت سبک پایتون             | 150-250 MB         | زیاد                    | -                         |
| بات با دیتابیس                 | 300-500 MB         | متوسط                   | -                         |
| اتوماسیون مرورگر (Playwright)   | 600-900 MB         | کم                      | فقط با صف                 |
| پردازش سنگین                   | 800-1200 MB        | خیلی کم                 | آفلود به VPS              |

## پیشنهادهای فنی
- استفاده از Docker با `mem_limit` و `memswap_limit`
- استفاده از lightweight base image (Alpine یا Distroless)
- فعال کردن swap سبک روی SSD (حداکثر ۲ گیگ)
- مانیتورینگ رم با `htop` + `docker stats`
```

---

## ۴. COMMUNICATION_PROTOCOL.md

```markdown
# پروتکل ارتباطی سیستم

## روش ارتباط اصلی
**MQTT** (با Mosquitto Broker)

### دلایل انتخاب MQTT:
- سبک و کم‌مصرف
- Publish/Subscribe model مناسب برای IoT
- قابلیت QoS
- پشتیبانی خوب روی ESP32 و پایتون

## ساختار موضوعات (Topic Structure)

```
automation/
├── central/          # پیام‌های ارسالی از Orange Pi
├── edge/             # پیام‌های ارسالی از ESP32ها
│   ├── {device_id}/
│   │   ├── status
│   │   ├── sensor/
│   │   └── command/
└── projects/         # وضعیت پروژه‌های در حال اجرا
```

## فرمت پیام‌ها (JSON)

```json
{
  "timestamp": "2026-06-14T13:00:00Z",
  "device_id": "esp32-kitchen-01",
  "type": "sensor_data",
  "payload": {
    "temperature": 26.5,
    "humidity": 48
  }
}
```

## پروتکل‌های جایگزین (در صورت نیاز)
- HTTP/Webhook برای ارتباط با سرویس‌های خارجی
- WebSocket برای داشبورد real-time
```

---

## ۵. INITIAL_QUESTIONS.md

```markdown
# سؤالات اولیه برای تکمیل طراحی

لطفاً به سؤالات زیر پاسخ بده تا معماری دقیق‌تری طراحی کنم:

## ۱. نوع پروژه‌ها
- پروژه‌هایت بیشتر چه دسته‌ای هستند؟ (بات تلگرام، اسکریپینگ وب، دانلودر، کنترل ربات فیزیکی، پردازش داده، و ...)
- چند تا از آن‌ها نیاز به مرورگر (Playwright/Selenium) دارند؟

## ۲. الگوی اجرا
- پروژه‌ها باید به صورت مداوم اجرا شوند یا زمان‌بندی‌شده (هر ساعت/روز)؟
- آیا بعضی پروژه‌ها وابسته به هم هستند؟

## ۳. ESP32ها
- هر ESP32 چه کارهایی انجام می‌دهد؟ (سنسور، موتور، رله، دوربین و ...)
- آیا ESP32ها نیاز به منطق محلی مستقل دارند یا فقط گزارش‌دهی می‌کنند؟

## ۴. Resume / State
- در چه سطحی نیاز به قابلیت Resume داری؟ (سطح پروژه کامل یا سطح تسک داخل پروژه)

## ۵. دیتابیس و ذخیره‌سازی
- چه نوع دیتابیسی نیاز داری؟ (SQLite، PostgreSQL، InfluxDB و ...)
- داده‌های مهم کجا ذخیره شوند؟ (روی SSD یا هم روی VPS)

## ۶. مانیتورینگ
- چقدر نیاز به داشبورد و مانیتورینگ داری؟ (ساده یا پیشرفته)
```

---

## ساختار پوشه پیشنهادی

```
Orange-Pi-Automation-Hub/
├── README.md
├── PROJECT_STRATEGY.md
├── RESOURCE_MANAGEMENT.md
├── COMMUNICATION_PROTOCOL.md
├── INITIAL_QUESTIONS.md
├── REQUIREMENTS.md          ← بعداً اضافه کن
└── docs/
    └── architecture-overview.md
```

---

**این فایل کامل آماده دانلود است.**

حالا می‌تونی این فایل رو دانلود کنی و مستقیم توی پروژه Claude‌ات استفاده کنی.  
اگر خواستی نسخه کامل‌تری (با REQUIREMENTS.md و architecture diagram هم) برات بسازم، بگو.