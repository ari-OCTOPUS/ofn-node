# AI Farm — نقشه‌ی پوشه‌ها

تفکیکِ تجویزشده‌ی `data-map-and-research`: **اثرِ خلاقانه** از **معماریِ ایمنی** جدا.

```
fusion-creative/        ← جریان A: codex، canonها، صحنه‌ها، promptها (intuition pump)
fusion-safety/          ← جریان B: معماریِ ایمنیِ واقعی
  ├── RECONCILIATION.md  ← منبعِ واحدِ زنده: این مجموعه چیست و قدمِ درست کدام
  ├── GAP-AUDIT.md       ← کدِ MVP در برابرِ ۴ معیار IGK (هست/نیست/اصلاح)
  ├── igk/               ← فاز ۰: کرنلِ مینیمالِ اعتماد + ۸ تستِ red-team
  └── docs/              ← checklist، v5-IGK، roadmap، data-map، bridge
fusion-mvp/             ← کدِ سیستمِ چندعاملی (۱۷ تستِ سبز) — متعلق به جریان B
```

## وضعیت
- baseline: **۱۷ سبز** · igk red-team: **۸ سبز** · igk integration: **۳ سبز** → **۲۸ سبز**.
- ✅ `orchestrator.py` به IGK وصل شد (فاز ۲): `ks.check()`ِ cooperative → `_kguard` بیرونی + `ActuationGate`ِ fail-closed روی finalize + گیتِ grounding. با `config.USE_IGK`/`GROUNDING_REQUIRED` کنترل می‌شود.
- کلیدِ قطعِ انسانی: فایلِ `fusion-mvp/logs/STOP` بساز → اجرا fail-closed متوقف می‌شود.

## پاکسازی
`CLEANUP.md` + `cleanup.ps1` را ببین: PDFهای تکراریِ root، `fusion-safety/igk` تکراری، و `.git`ِ ناقص قابلِ حذف‌اند (sandbox خودش نمی‌تواند پاک کند).
