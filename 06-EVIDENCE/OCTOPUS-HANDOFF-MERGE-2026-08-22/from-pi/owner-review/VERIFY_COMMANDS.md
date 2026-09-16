# VERIFY_COMMANDS

همه read-only هستند. هیچ `systemctl restart`، reboot، ufw change، یا نوشتن secret.

Digest فایل `MANIFEST.json` امضا نیست و اثبات منشأ نیست. فقط‌خواندنی بودن بسته evidence تمامیت دائمی نیست؛ digestها مرجع تمامیت‌اند.

## بستهٔ owner-review روی لپ‌تاپ

از ریشهٔ بسته:

```bash
python3 verify_owner_review_pack.py .
```

بررسی‌های الزامی:

1. `MANIFEST.json.sha256` با فایل manifest تطبیق داده شود.
2. هر path داخل manifest نسبی، فاقد `..` و داخل ریشهٔ بسته باشد.
3. digest تک‌تک artifactها دوباره محاسبه شود.
4. فایل اضافی ثبت‌نشده یا artifact مفقود گزارش شود.
5. digest **کامل** checkpoint در seq 266 با audit ledger تطبیق داده شود: `sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2`
6. `chain_id=octopus-audit-ledger` صریحاً بررسی شود. عبارت `ledger head = 266` استفاده نشود. عبارت درست: `octopus-audit-ledger checkpoint anchored at seq=266`
7. فقط‌خواندنی بودن بسته را evidence امنیتی دائمی فرض نکنید.

## برد (بدون تغییر state)

```bash
python3 -c "import json; r=json.load(open('/var/lib/octopus/state/boot_report.json')); print(r['readiness_state'], r['gates_failed'], r.get('readiness_profile'))"
ss -lntup | grep -E ':9101|:9464|:8080|:4222|:8222' || true
python3 -m json.tool /var/lib/octopus/state/OWNER_REVIEW_DECISION.json
python3 -m json.tool /var/lib/octopus/state/gaps/GAP-001-cold_boot_unverified.json
python3 /var/lib/octopus/state/owner-review/verify_owner_review_pack.py /var/lib/octopus/state/owner-review
```

Doctor read-only (گزارش می‌نویسد؛ repair نمی‌کند؛ به inbound فقط‌خواندنی ننویس اگر بسته lock است):

```bash
/opt/octopus/venv/bin/python /opt/octopus/scripts/octopus_doctor_readonly.py
```
