# 11 — ROLLBACK · ۲۰۲۶-۰۷-۳۱

همه‌چیز روی شاخهٔ ایزولهٔ `claude/octopus-code-integration-175ecb` است؛ درخت
زنده و master دست‌نخورده‌اند، پس «هیچ‌کاری نکردن» خودش rollback ِ کامل است.

```text
کلِ مأموریت           git branch -f claude/octopus-code-integration-175ecb 9f14901
                       (اشاره‌گرِ شاخهٔ خودم به نقطهٔ آغاز — master)
فقط تا پیش از patchها  git reset --keep f2fceee     (نجات‌ها می‌مانند)
فقط manifest/registry  git revert 1247040
فقط دو درزِ نو         git revert 830e38c
فقط LockedJson         git revert 0a303af
فقط پذیرشِ v2          git revert a9492c7           (⚠️ بعدش pipeline ِ tracked
                       دوباره با mission_contract ناسازگار می‌شود — ۳ قرمز برمی‌گردد)
رفتارِ زنده            هیچ تغییری نکرده: صفر restart، صفر فلگِ ست‌شده، صفر send.
                       دو فلگِ نو absent=off؛ تا merge + رأی + restart هیچ‌اند.
خاموشیِ آنی (همیشه)    _ops/STOP-ORGANISM روی درخت زنده
```

`reset --keep` نه `--hard` (کارِ کامیت‌نشده را رد می‌کند، پاک نمی‌کند).
