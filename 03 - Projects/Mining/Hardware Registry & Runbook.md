---
type: reference
status: active
project: "[[03 - Projects/Mining/PROJECT]]"
tags: [mining, hardware, runbook]
created: 2026-07-03
updated: 2026-07-03
---

# Hardware Registry & Remote-Ops Runbook

## رجیستری ناوگان (یک ردیف per دستگاه)

| ID | دستگاه | محل | روش دسترسی | نقش | وضعیت |
|---|---|---|---|---|---|
| OPI-1 | Orange Pi 5 Pro | `[To measure]` | SSH via Tailscale `[Assumption]` | `[To measure]` | `[To measure]` |
| OPI-2…6 | — | — | — | — | `[To measure — تعداد واقعی از config قدیمی Hcash: ۶ نود]` |
| ESP-1 | ESP32 | `[To measure]` | `[To measure]` | سنسور/watchdog `[Assumption]` | `[To measure]` |

> IPها و SSH_USER در `secrets-export/` (منتقل‌شده از Hcash config.env) — بعد از rotation، دسترسی جدید فقط در password manager.

## Runbook عملیات از راه دور (stub)

1. **اتصال:** Tailscale mesh → SSH با کلید (نه پسورد) `[Unverified — بعد از rotation ست شود]`.
2. **سلامت:** `uptime`, دمای SoC, هش‌ریت فعلی → گزارش روزانه به تلگرام (فاز ۴).
3. **توقف اضطراری:** فایل STOP / فلگ DB (kill-switch واحد D-06) → همه ماینرها down.
4. **قاعده AI (D-20):** ایجنت هرگز SSH مستقیم نمی‌زند — تغییرات فقط از مسیر repo + deploy gate با verdict.
5. **برق:** اگر هزینه > $0.05/kWh و خورشیدی نیست → HALT ساختاری (قید manifest).
