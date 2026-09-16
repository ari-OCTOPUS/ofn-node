# 02 — توپولوژی ناوگان (نقش‌ها فقط از شواهد واقعی)

| نود | IP | hostname | دسترسی SSH | شواهد نقش (سرویس/فایل واقعی) | زبان/پلتفرم |
|---|---|---|---|---|---|
| ۱۳۸ | 192.168.0.138 | DietPi | `ari@` ✓ | سرویس‌های `ofn.service` (PID 1351408 از ۰۸-۲۷)، `octopus-scheduler.timer` (هر ۱۵دقیقه)، `octopus-bridge/control-router/cycle-settler` — raw: raw/138/scheduler-138-journal (HW-DISCOVERY) | Linux/DietPi |
| ۱۸۰ | 192.168.0.180 | octopus-continuity-180 | `root@` ✓ | سرویس‌های `octopus-gateway (L0)`، `octopus-cognitive-worker`، `octopus-afferent-lab`، تایمرهای mesh/drain/mirror — raw: raw/180 (HW-DISCOVERY) | Linux |
| ۱۸۲ | 192.168.0.182 | sensorium-opi5pro | `root@` ✓ | سرویس `nats-server (JetStream, OCTOPUS Sensorium)`، تایمرهای witness/obs-autoheal/crossnode-probe، درایو `octopus_main` mount — raw: raw/182 | Linux/OrangePi5Pro |
| ۱۹۱ | 192.168.0.191 | (لپ‌تاپ خودمان) | ABSENT — sshd ندارد | میزبان vault و ایجنت‌ها؛ hostname/نسخه‌ها در raw/laptop/self-state.txt | Windows 11 |

قواعد: نقش‌ها فقط از سرویس‌های systemd واقعی و محتوای repo استنتاج شد — از IP یا چت حدس زده نشده (قاعدهٔ HARD RULES).
پورت ۲۲ هر سه برد باز است؛ ۱۹۱ بسته (طبیعی برای ویندوز بدون OpenSSH Server).
