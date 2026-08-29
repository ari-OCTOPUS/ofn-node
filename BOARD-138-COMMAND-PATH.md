# مسیر فرمان ۱۸۰ → ۱۳۸

وضعیت: باز است. `http_api` لید روی LAN باز نشد (لوپ‌بک می‌ماند).

```bash
ssh board-138 'curl -s http://127.0.0.1:8792/healthz'
ssh board-138 'python3 /tmp/aine_commander_cycle_138.py'
```

- هویت این برد: مغز کیفیت، `may_authorize=false`، ارسال مشتری ممنوع
- فرمانده درآمد: `ari@192.168.0.138` + `ofn.service`
- کلید: `/opt/octopus/ssh/id_ed25519` (Host `board-138` در `/root/.ssh/config`)
- ledger ارگانیسم ۱۸۰ را با رویداد درآمد آلوده نکن
