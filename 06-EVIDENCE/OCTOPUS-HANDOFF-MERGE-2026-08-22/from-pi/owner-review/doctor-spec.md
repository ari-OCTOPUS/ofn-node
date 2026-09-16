# doctor-spec

Doctor باید **read-only** باشد. هیچ repair، restart، arming، امضا یا نوشتن NATS password مجاز نیست.

## پیاده‌سازی این جلسه

- اسکریپت: `/opt/octopus/scripts/octopus_doctor_readonly.py`
- خروجی: `doctor-report.json` در همین پوشه
- `repairs_attempted=0`، `executed_actions=0`
- واحد systemd اضافه **نشد** و enable **نشد**

## چک‌های الزامی (مگاپرامپت T3)

1. service state
2. metrics bind (`127.0.0.1:9101`)
3. unexpected listeners (`:8080`, `:9464`, 9101 غیر loopback)
4. ledger integrity
5. checkpoint signature (بدون bundle → FAIL؛ GAP-002 باز)
6. registry signature files present (verify محتوا جداگانه با root.pub)
7. policy mode WAVE0_OBSERVE_ONLY
8. planner import/invocation
9. executable action count
10. actuator authority
11. sensor coverage
12. missing data (UNKNOWN نه صفر)
13. clock monotonicity / NTP
14. disk health
15. stale observations
16. restart consistency (بدون reboot اجباری)
17. configuration drift

## خروجی استاندارد

```json
{
  "schema": "octopus.doctor-report.v1",
  "status": "PASS|DEGRADED|FAIL|UNKNOWN",
  "checks": [],
  "repairs_attempted": 0,
  "executed_actions": 0
}
```

Doctor سبز پیش‌شرط T7 است. تا `status=FAIL` است صدور OA-T7 بی‌معناست (کلید فنی دو‌کلیدی برقرار نیست).

هر FAIL باید `blocking_checks` مستقل داشته باشد، مثلاً:

```json
{
  "blocking_checks": [
    {"id": "gap_001_open", "severity": "blocking", "observed": "TESTED_FAIL", "required": "PASS_WITH_EVIDENCE"},
    {"id": "checkpoint_unsigned", "severity": "blocking", "observed": "unsigned", "required": "root-v2 verified"},
    {"id": "coverage_or_data_critical", "severity": "blocking", "observed": "would_block", "required": "healthy_or_explained"}
  ],
  "repairs_attempted": 0
}
```
