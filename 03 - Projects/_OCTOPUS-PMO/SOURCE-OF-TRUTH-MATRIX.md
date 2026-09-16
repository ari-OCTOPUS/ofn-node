# Source of Truth Matrix

| موضوع | مرجع عملیاتی | مراجع مشتق/تاریخی | owner | freshness rule |
|---|---|---|---|---|
| تصمیم انسانی | root `VERDICT_QUEUE.md` + این Decision Register | صف‌های محلی فقط cross-link | Owner/PMO | status+effective date |
| policy ریسک | `RISK-LADDER.md` پس از VQ-ROOT-003 | README/manifest snapshots | Owner/Risk Governor | نسخهٔ مصوب |
| hierarchy | `PROGRAM-CHARTER.md` + VQ-ROOT-001 | README diagram | Owner | ADR/decision wins |
| قرارداد tenant | همان `MANIFEST.yaml`/JSON | READMEها | Tenant owner | locked rules حفظ |
| وضعیت tenant | `REGISTRY.md` + run ledger | MANIFEST status_snapshot | Steward | evidence timestamp |
| واقعیت workspace | filesystem فعلی | گزارش VaultScanner مربوط F: | Cartographer | root+generated_at اجباری |
| واقعیت F:\backup | مشاهدهٔ زندهٔ مجاز یا report تاریخ‌دار | بازسازی اسناد | Architect/Owner | هیچ ادعای live بدون mount |
| evidence عملیاتی | Event Ledger آینده | graph/vector/report | Evidence Steward | append + provenance |
| Graph | rebuilt derived index | markdown report | Cartographer | قابل بازسازی از ledger |
| Accounting/legal | advisor-confirmed records | research docs | Owner/Tax Agent | `[Unverified]` تا sign-off |
| NBB output | shadow recommendation record | model output | NBB Steward | non-binding همیشه |

## یافته‌های فعلی
- `README.md` هم Security Gate را بسته می‌داند و هم NBB را حاکم آینده معرفی می‌کند؛ هر دو operationally با context جدید محدود/جایگزین شده‌اند.
- VaultScanner inventory فعلی فقط snapshot از `F:\backup` است، نه workspace.
- ادعاهای test-count و readiness تا اجرای مستقل، `reported-not-verified` هستند.
