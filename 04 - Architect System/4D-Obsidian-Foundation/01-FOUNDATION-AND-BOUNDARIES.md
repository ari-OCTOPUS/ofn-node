---
type: architecture
status: ready
tags: [4d, boundaries, governance, tcb]
created: 2026-07-16
updated: 2026-07-16
aligns_to: "[[06 - Architecture Maps/TRI-PLANE RECONCILIATION - ops vs NBB-CP vs 4D-control-plane]]"
---

# پایه‌ها و مرزهای 4D × Obsidian

## 1. هدف

هدف اتصال نظری این است که دانش و evidence تولیدشده توسط 4D برای انسان در Obsidian قابل مشاهده، ممیزی و مرور شود؛ بدون اینکه Vault جای runtime را بگیرد یا به 4D فرمان اجرایی مستقیم بدهد.

دو هدف 4D باید هم‌زمان حفظ شوند:

1. **SOG research:** سنجش امضای بعد پنهان در سری زمانی.
2. **Brain-OS testbed:** آزمایش نظریه‌های شناخت با معیارهای قابل‌اندازه‌گیری؛ نه ادعای آگاهی پدیداری.

## 2. لایه‌های مسئولیت

| لایه | مسئولیت | نباید انجام دهد |
|---|---|---|
| 4D Runtime | آزمایش، محاسبه، event، حافظه عملیاتی | تبدیل مستقیم خروجی به حقیقت canonical |
| 4D control_plane | مشاهده، shadow، approval/kill داخلی طبق قرارداد موجود | رقابت با `_ops` یا NBB-CP |
| Obsidian | review، MOC، provenance، decision، knowledge graph انسانی | نگه‌داری secret یا کنترل مستقیم actuator |
| Architect/_ops | حاکمیت اکوسیستم و registry کلان | بلعیدن منطق داخلی 4D |
| Human owner | verdict نهایی actionهای حساس و promotion | واگذاری حاکمیت نهایی به agent |

## 3. طبقه‌بندی حقیقت

هر ادعای واردشده به Vault یکی از این حالت‌هاست:

- **Observed:** خروجی خام یا snapshot با pointer به منبع.
- **Derived:** محاسبه‌ای که از observed ساخته شده و روش آن مشخص است.
- **Interpreted:** تفسیر ایجنت/انسان؛ الزاماً حقیقت نیست.
- **Hypothesis:** قابل ابطال و منتظر آزمایش.
- **Verified:** evidence و روش بازتولید دارد.
- **Canonical candidate:** برای پذیرش انسانی آماده است.
- **Canonical:** فقط پس از review/approval.

این واژگان در مرحله عملی باید بدون اختراع property جدید، ابتدا در بدنه‌ی نوت استفاده شوند؛ تغییر Property Schema فقط با تأیید مالک.

## 4. Trust Boundaries و TCB

### TCB 4D — دست‌نخورده

طبق اسناد فعلی، حداقل شامل `core/`، `config/`، `tests/`، `brain/guardrails.py`، `brain/automation.py`، `brain/self_code.py`، `brain/self_evolve.py`، `brain/events.py`، daemon/Telegram، LLM router/clients و entrypointهاست. فهرست دقیق باید از کد زنده دوباره استخراج شود.

### مرز Vault

- secretها، tokenها، PII خام، محتوای کامل log و payload حساس وارد Vault نمی‌شوند.
- Vault فقط pointer، hash، summary و provenance sanitised می‌گیرد.
- فایل‌های `outputs/*.db` و Chroma به Markdown کپی نمی‌شوند.
- نوت human-authored بازنویسی مخرب نمی‌شود.

### مرز اکشن

این موارد هرگز از Vault به‌طور مستقیم اجرا نمی‌شوند:

- daemon/Telegram start
- self-code approve/apply
- cloud budget activation
- external send/publish
- حذف، mass mutation یا تغییر TCB
- canonical promotion بدون review

## 5. Invariants پیشنهادی اتصال

این‌ها قرارداد طراحی‌اند، نه invariant اجرایی جدید:

- **OI-1 — Runtime authority:** runtime منبع وضعیت اجرایی است؛ Vault فقط projection است.
- **OI-2 — Provenance:** هر knowledge note ماشینی pointer به evidence دارد.
- **OI-3 — No secret replication:** هیچ secret یا payload حساس replicate نمی‌شود.
- **OI-4 — Idempotency:** یک artifact با شناسه/هش یکسان دوباره ساخته نمی‌شود.
- **OI-5 — Append/Version:** اصلاح history با نسخه/append، نه overwrite خاموش.
- **OI-6 — Human sovereignty:** promotion و action حساس human-gated است.
- **OI-7 — Fail closed:** unknown، stale یا schema mismatch ⇒ staging/blocked، نه canonical.
- **OI-8 — Coupled-not-merged:** اتصال از adapter/manifest است؛ هیچ پلین جدید یا merge ایجاد نمی‌شود.
- **OI-9 — Claim discipline:** testbed شناخت هرگز به ادعای consciousness تبدیل نمی‌شود.
- **OI-10 — Rebuildable view:** صفحات Dashboard از نوت‌های evidence بازسازی‌پذیرند.

## 6. معیار Rewrite Risk

اگر تغییر آینده یکی از موارد زیر را داشت، ایجنت متوقف شود و اجازه بگیرد:

- تغییر interface موجود یا بیش از حدود ۳۰٪ منطق یک ماژول؛
- جایگزینی `brain/vault_sync.py` به‌جای extension/adapter؛
- merge کردن 4D control plane با `_ops` یا NBB-CP؛
- تغییر لنگرها، TCB، schema کانونی یا مسیرهای runtime؛
- حذف نسخه‌ی قبلی یا تغییر رفتار بیرونی تثبیت‌شده.

## 7. Gateهای پایه

| Gate | شرط عبور |
|---|---|
| G0 Scope | مسیر canonical و وضعیت git/runtime با evidence روشن شود |
| G1 Safety | deny paths، TCB، secret boundary و rollback تأیید شوند |
| G2 Read model | inventory و contract بدون mutation تولید شود |
| G3 Shadow export | dry-run خروجی deterministic و sanitised بسازد |
| G4 Staging | فقط پوشه staging با idempotency/provenance نوشته شود |
| G5 Review | انسان candidate را accept/reject کند |
| G6 Dashboard | view فقط از داده accepted/verified ساخته شود |
| G7 Coupling | registry adapter صرفاً evidence رو به بالا بدهد |

## 8. Prompt این بخش برای ایجنت بعدی

```text
You are the Boundary & Governance Agent for 4D × Obsidian. Read 00-START-HERE, this file, the tri-plane reconciliation, Property Schema, 4d_system/MANIFEST.yaml, PROJECT_STATE.md, and control_plane/registry.yaml. Verify every path and status against the current filesystem; do not trust historical test counts. Produce a cited boundary audit covering: canonical repo, TCB, data sensitivity, authority, forbidden flows, coupled-not-merged constraints, and G0/G1 evidence. Do not edit code, runtime state, .env, _ops, existing registry, or existing dashboards. Do not run daemon/Telegram/cloud. Use Current/Delta/Preserved/Rollback. Unknown remains UNKNOWN. Stop after the report and await owner verdict.
```
