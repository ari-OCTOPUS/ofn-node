# OWNER PACK — 2026-09-02 night (two items you ordered; run when ready)

قانون: هر خط یک فرمان PowerShell است — کپی، پیست، خروجی را همین‌جا برگردان («انگار خرم»).

---

## بستهٔ ۱ — استقرار خودمدل روی بورد۱۳۸
**پیش‌شرط: فقط بعد از ادغام PR #81.** قبل از آن اجرا نکن (کد روی main بورد نیست).

```
ssh board138 git -C ~/ofn fetch origin --prune
```
```
ssh board138 git -C ~/ofn checkout main
```
```
ssh board138 git -C ~/ofn pull --ff-only
```
```
ssh board138 python3 -X utf8 -m ofn.adapters.self_model_producer --repo ~/ofn --output ~/ofn/web/cockpit-v2/data/self-model.json
```
راستی‌آزمایی (باید خط اول `self-model status=` و شمارهٔ کامیت تازهٔ main را نشان دهد):
```
ssh board138 head -c 400 ~/ofn/web/cockpit-v2/data/self-model.json
```
```
ssh board138 head -n 1 ~/ofn/state/self-model/SYSTEM-SELF-MODEL.json
```

❌ DO NOT: دیتابیس را لمس نکن · سرویس restart نکن · فلگی را تغییر نده · چیزی حذف نکن. فقط همین شش خط.
اگر `ssh board138` وصل نشد (اسم alias فرق دارد)، فقط بگو چه نامی است تا بسته را با همان بازنویسی کنم.

---

## بستهٔ ۲ — تمرین بازیابی بکاپ (گام ۱: کشف)
اول ببینیم آرشیو بکاپ کجاست (این فقط `ls` است — هیچ چیز تغییر نمی‌کند):
```
ssh board138 ls -la ~/octopus-test-runs
```
```
ssh board138 ls -la ~/octopus-evidence-archive
```
```
ssh board138 ls -la ~ | head -40
```
خروجی هر سه را برگردان → من خطوط گام ۲ (استخراج آخرین بکاپ در `~/lab/restore-drill-20260902`، شمارش فایل، نمونهٔ sha256، رسید) را دقیق برای همان مسیرها می‌سازم.

❌ DO NOT: هیچ‌چیز extract/delete نکن در این گام · دیتای زنده (sqlite اصلی، outbox) را لمس نکن.

---

یادآوری‌های بدون‌فرمان (فقط برای تقویم شما): توکن HF امروز ~09:15Z منقضی شد — تازه‌سازی با خود شماست؛ ثبت‌نام buy.nsw را فعلاً انتخاب نکردید (بسته‌اش آماده می‌شود اگر خواستی).

---

## بستهٔ ۳ — Re-arm رسیددار WAL (رأی امشب: همین امشب؛ Q-05A ایمیل پیگیری در نشست بعد ساخته می‌شود)
مسیر تأییدشده روی بورد: `/home/ari/ofn/ofn/agi2027_runtime/managed_flags.json` — محتوای فعلی (خوانده‌شده): `{"OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": "0", "set_by": "owner-disarm-armin-2026-09-02"}`

۱) بکاپ وضعیت فعلی:
```
ssh ari@192.168.0.138 cp /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json.bak-rearm-20260902
```
۲) Re-arm با ارجاع رسید (printf با \042 برای گیومه — الگوی disarm):
```
ssh ari@192.168.0.138 "printf '{\042OCTOPUS_WIRE_LEAD_OUTBOUND_WAL\042: \0421\042, \042set_by\042: \042owner-rearm-armin-2026-09-02-Q05A\042}' > /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json"
```
۳) راستی‌آزمایی (باید JSON سالم با مقدار ۱ باشد):
```
ssh ari@192.168.0.138 cat /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json
```
❌ DO NOT: بعد از re-arm هیچ ارسال خودکار شروع نمی‌شود تا فرمان ایمیل جداگانه ساخته شود · منصرف شدید؟ بکاپِ خط ۱ را برگردانید · خروجی را برگردانید.

---

## وضعیت تمرین بازیابی — ✅ همان امشب توسط لین A اجرا و PASS شد
`~/backups/ofn-daily/20260902T030010Z/` (444K) → کپی در `~/lab/restore-drill-20260902/` → **۱۱/۱۱ فایل SHA256SUMS اوکی** + **۳/۳ دیتابیس sqlite `integrity_check=ok`** (outbound-effects، outbox، painting — اسکیمای painting خوانا، ۳۷ آبجکت). هشدار «بکاپ تأییدنشده» بسته شد. گام بعدی اختیاری: بازیابی کامل سرویس در محیط lab (نیاز به رأی جداگانه ندارد ولی انجامش با نشست بعدی است).
