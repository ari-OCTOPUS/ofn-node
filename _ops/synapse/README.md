# 🧬 اندامِ SYNAPSE — نقطه‌ی اتصالِ ریاضیِ SOG به تله‌متریِ خودِ ارگانیسم

> ساخته‌شده: ۲۰۲۶-۰۷-۲۴ (جلسه‌ی kimi) · وضعیت: **shadow / پیش‌فرضِ خاموش** · هیچ wiringای به رانتایم انجام نشده.

## چیست
عضوی جدید و **additive** که سه قابلیت را بدونِ دست‌زدن به هیچ کدِ موجود فراهم می‌کند:

| ماژول | نقش | فلگ (پیش‌فرض خاموش) | خروجی |
|---|---|---|---|
| `sense.py` | SENSE: `E_shadow_proxy`/`delta_self_proxy`/`cpm` روی `events.jsonl» خودِ ارگانیسم — با importِ read-only از `4d_system/core/metrics.py` (بدونِ تکرارِ کد) | `SYNAPSE_ENABLED=1` (+ سقف `SYNAPSE_DAILY_MAX=3`) | `out/proposal-*.json` به‌قالبِ FROZENِ `b6.sog.proposal.v1` |
| `trajectory_monitor.py` | P3: تشخیصِ ناهنجاریِ **زنجیره‌ای** (burst / novel-3gram / egress-marker) — درسِ ExploitGym | `TRAJECTORY_MONITOR_ENABLED=1` | `out/trajectory-alerts.jsonl` (سازگار با الگوی event_bridge برای «منبع ۵») |
| `egress_policy.py` | P1: سیاستِ egress **deny-by-default** (policy-as-data) — localhost مجاز، ابر فقط با `DECLARED_ENDPOINTS`ِ تأییدشده‌ی مالک | `OCTOPUS_EGRESS_ENFORCE` / `OCTOPUS_EGRESS_AUDIT` | تصمیم + `out/egress-audit.jsonl` |

## ناوردها (hard)
- **propose-only**: هیچ‌کدام apply نمی‌کنند؛ خروجی فقط فایل در `out/`.
- **fail-closed**: هر خطا → no-op یا خروجیِ degraded؛ هرگز exception به بیرون.
- **صفر نوشتن** روی genome/، ledger.jsonl، state/، .env، budget، kill-switch.
- **مصرف LLM = صفر** (فقط ریاضی/قاعده) — سازگار با سقفِ بودجه.
- وقتی فلگ‌ها خاموش‌اند: **هیچ اثری** روی ارگانیسمِ زنده (byte-identical behavior).

## wiring (فقط با tapِ مالک، به‌ترتیب)
1. `SYNAPSE_ENABLED=1` + فراخوانی `sense_once()` از یک beat (پیشنهاد: wiring.py) — observation برای ۱ هفته.
2. «منبع ۵» در `event_bridge.py`: خواندنِ `trajectory-alerts.jsonl` (همان الگوی cursor) — patch آماده‌ی طراحی در roadmap §P3.
3. wrap کردنِ clientهای LLM با `egress_policy.decide()` — پس از پرکردنِ `DECLARED_ENDPOINTS` با تأییدِ مالک.

## تست
```
python _ops/synapse/sense.py               # self_test آفلاین (flag خاموش)
python _ops/synapse/trajectory_monitor.py  # self_test آفلاین
python _ops/synapse/egress_policy.py       # self_test آفلاین
python -m pytest _ops/tests/test_synapse_sense.py -v
```
⚠️ تست‌های pytest در جلسه‌ی نگارش اجرا **نشده‌اند** (ابزارِ اجرا نبود) — [UNKNOWN] تا اولین اجرا.
