# SECURITY-BOUNDARIES — BOARD 180

scope: this_host_only | method: read-only (no values read)

## Secrets (نام و مجوز؛ مقدار خوانده نشد)
| file | mode | owner | status |
|---|---|---|---|
| /etc/octopus/secrets.env | 600 | root | OK, value_not_read |
| /etc/octopus/lan-token | 600 | root | OK, value_not_read |
| /opt/octopus/ssh/id_ed25519 | 600 | root | OK, value_not_read |
| /root/.ssh/octopus_mesh_ed25519 | 600 | root | OK, value_not_read |
| /root/.ssh/octopus_180 | 600 | root | OK, value_not_read |

- اسکن نام‌محورِ docs/tasks مش: هیچ private key / bot token / password در خروجی‌ها نشت نکرده (NONE_FOUND).
- secretها هرگز در Git، prompt، mesh message یا این اسناد نوشته نمی‌شوند.

## سطح حملهٔ شبکه (listeners)
| bind | service | risk | note |
|---|---|---|---|
| 0.0.0.0:8780 | gateway (uvicorn) | LOW-MED | L0 read-only، بدون command surface؛ اما روی همهٔ interfaceها |
| 192.168.0.180:8090 | organism (LAN) | MED | dual-bind LAN؛ محافظت با OCTOPUS_REQUIRE_LAN_TOKEN |
| 127.0.0.1:8090 | organism (loopback) | LOW | loopback |
| 127.0.0.1:8081 | llama | LOW | loopback |
| 0.0.0.0:22 | dropbear | MED | key-only observed (password login رد شد) |
| 0.0.0.0:2222 | sshd (openssh) | MED | دو SSH server هم‌زمان فعال |

## یافته‌های مرزی (proposal فقط، بدون تغییر)
1. دو SSH server (dropbear:22 + sshd:2222) هم‌زمان → سطح حملهٔ دوگانه. پیشنهاد بررسی: آیا هر دو لازم است؟ (تصمیم/تغییر با مالک؛ 180 تغییر SSH نمی‌دهد.)
2. gateway روی 0.0.0.0 به‌جای bind LAN مشخص → می‌توان به 192.168.0.180 محدود کرد (proposal؛ بدون اجرا).
3. organism روی LAN با token → قابل قبول اگر token قوی و rotate شود؛ فقط ثبت.
4. mesh SSH keys per shared_system_model known_issue هنوز broad shell access می‌دهند → forced-command/restrict پیشنهادی برای فاز بعد.
5. port 9101 روی 182 (per shared_system_model) preexisting_risk — خارج از میزبان 180، فقط ارجاع.

## خطوط قرمز حفظ‌شده در این فاز
- بدون تغییر firewall، sshd_config، dropbear config، gate یا ofn/config.py.
- may_authorize=false ؛ external_actions=0 ؛ هیچ bind جدید روی 0.0.0.0.
