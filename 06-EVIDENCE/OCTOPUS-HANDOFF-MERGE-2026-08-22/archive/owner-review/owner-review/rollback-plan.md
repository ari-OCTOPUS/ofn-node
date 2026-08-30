# rollback-plan

وضعیت فعلی باید **بدون rollback اجرایی** حفظ شود: WAVE0_OBSERVE_ONLY، actuator_authority=NONE.

این سند dry-run است. **DO NOT** `systemctl restart`، **DO NOT** reboot، **DO NOT** ufw disable.

## اصل

اگر هر transition آینده شکست بخورد:

1. Preflight fail → stop
2. Backup دارای SHA256
3. Apply one bounded change فقط پس از OA
4. Immediate verify
5. Commit or rollback
6. Append audit

الان هیچ change زنده‌ای برای rollback وجود ندارد (mutations=0).

## Dry-run (اجرا نکن؛ فقط بررسی وجود مسیر)

```text
test -f /etc/octopus/config/registry.yaml
test -f /var/lib/octopus/state/milestones/registry-v5/registry.yaml
test -f /var/lib/octopus/state/boot_report.json
python3 -c "import json; json.load(open('/var/lib/octopus/state/boot_report.json'))"
```

اگر Registry v6 روزی apply شود، backup در `/var/lib/octopus/state/config-history/pre-registry-v6-*` ساخته می‌شود (کد موجود در apply_signed_inbound.py). آن مسیر هنوز ایجاد نشده چون bundle ناقص است.

## فرمان‌های ممنوع در rollback این موج

- `systemctl restart octopus-sensorium` (مگر OA جدا)
- `shutdown` / `reboot`
- بازنویسی HEAD.json
- بستن GAP-002 بدون امضا
- کپی private key

## digestهای لنگر برای برگشت به همین freeze

- registry.yaml `sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5`
- board.yaml `sha256:b53ec5ba3764f035513535577df5e72f25767e54dda2cedfd5d9b1ca73cd0d5d`
- unsigned checkpoint `sha256:3b60751b3759698b4982ccda035a008539cc0014cb086d96f516fc274142c150` seq=`266`
- mutations=0

rollback dry-run در pytest INV-20 فقط وجود این فایل و ممنوعیت restart را چک می‌کند.
