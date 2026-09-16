# 00-VANTAGE-PROOF — مأموریت کشف سه‌بردی 2026-09-03

```text
HOSTNAME   = DESKTOP-KA9RFN5                      ← خروجی خام hostname
IPv4       = 192.168.0.191 (Wi-Fi)                ← خروجی خام ipconfig
CROSS-CHECK= SourceAddress: 192.168.0.191 در Test-NetConnection (تأیید مستقل)
VANTAGE    = VALID — LAN محلی مالک، نه cloud/sandbox
PROBE ناوبری= همگی از همین vantage (پینگ/TCP/curl/arp محلی) + vantage دوم: ssh از board-138
INVALID_PROBE نشست قبلی (مرورگر cloud) = دور انداخته شد؛ در این دور استفاده نشد
```

## خروجی‌های خام
```
$ hostname
DESKTOP-KA9RFN5
$ ipconfig | grep -i "IPv4"
   IPv4 Address. . . . . . . . . . . : 192.168.0.191
$ netstat -ano | findstr ":8801"
(خالی — هیچ پروسه‌ای روی 8801 لپ‌تاپ گوش نمی‌دهد؛ findstr exit=1)
$ arp -a | findstr "192.168.0.138 192.168.0.180 192.168.0.182"
  192.168.0.138         c0-74-2b-f9-72-d5     dynamic
  192.168.0.180         c0-74-2b-f9-72-90     dynamic
  192.168.0.182         c0-74-2b-f9-86-64     dynamic
```
هر سه برد MAC با OUI واحد `c0:74:2b` و پسوندهای متوالی (.138→…72:d5، .180→…72:90) = یک بچ سخت‌افزاری.

اندازه‌گیری: 2026-09-03 ~11:05–11:15 AEST · FILES_I_MERGED=none · PRODUCTION_WRITES=none
