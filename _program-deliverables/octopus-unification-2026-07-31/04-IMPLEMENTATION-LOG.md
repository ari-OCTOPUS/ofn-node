# 04 — IMPLEMENTATION LOG · ۲۰۲۶-۰۷-۳۱

همهٔ کامیت‌ها روی شاخهٔ `claude/octopus-code-integration-175ecb` (شروع از
master=`9f14901` → ff به `ce35f61` = نوکِ tg-p2). صفر push/merge/restart/arm.

| کامیت | چه | شاهد سبزی |
|---|---|---|
| ff → `ce35f61` | شاخه روی نسخهٔ واقعیِ در حالِ اجرا (نه master ِ ۱۸۳ کامیت عقب) | جدولِ ff در 00-doc |
| `2ac7e9b`+`f2fceee` | نجاتِ ۶۳ فایلِ کد/تستِ زندهٔ بی‌گیت (owner_console، epoch_guard، ۴۴ تستِ TESTS) | secret-scan پاک؛ کپی بایت‌به‌بایت |
| `a9492c7` | پذیرشِ v2 ِ mission_contract + memory gate/store (وابستگیِ کدِ tracked) | bridge ۱۴/۱۴ · ccv2 ۱۰/۱۰ · memory_gate ۱۰/۱۰ |
| `0a303af` | **VQ-STATE-WRITE-001**: LockedJson.write با fsync + retry ِ محدود + رسیدِ شکست + blocker ِ snapshot | test_lockedjson_write ۶/۶ · جهش‌های M1..M4 قرمز · رگرسیون ۵ سوییت سبز |
| `830e38c` | **VQ-MISSION-CARD-001** (درزِ mission→کارتِ ap:، فلگ خاموش) + **§۱۰.۴** retrieval ِ مشورتیِ حافظه (فلگ خاموش) | card ۷/۷ · memory ۵/۵ · جهش‌های MC1..MC5/MR1..MR3 قرمز |
| `1247040` | MANIFEST_INVALID قابلِ‌دیدن + manifest ِ world_discovery + تصحیحِ probe ِ کهنهٔ unified_control + ثبتِ ۲۱ سوییتِ یتیمِ سبز در run_all | manifest_truth ۴/۴ · MF1/MF2 قرمز · validate_contract PASS (۶ manifest) |

## فایل‌های پرریسکی که عمداً لمس نشدند

```text
organism.py · wiring.py · telegram_center/center.py · budget/approval_channel.py
OCTOPUS-flags.cmd (هیچ فلگی ست نشد — هر سه فلگِ نو absent=off)
PRE-0/** · heart/** (shadow ماند) · هر فایلِ dirty ِ درخت زنده
```

## فلگ‌های نو (هر دو بیرونِ PAPER_FULL_FLAGS، غایب از flags.cmd = واقعاً خاموش)

| فلگ | چه چیزی را باز می‌کند | کارتِ رأی |
|---|---|---|
| `OCTOPUS_WIRE_MISSION_CARD` | mission ِ needs_approval → کارتِ pending در صفِ ap: | `LIVE-GATE-CARD-MISSION-CARD.md` |
| `OCTOPUS_WIRE_MEMORY_READ` | retrieval ِ مشورتیِ ساخت‌یافته پیش از planning (بی‌اثر بر plan) | همان کارت (بندِ جدا) |
