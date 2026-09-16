# INTEGRATION — طبق `SELF_IMPROVEMENT_DOCTRINE`

> «Improve, don't rewrite. Extend, don't replace. Inherit, don't reset.»

این سند همان چهارتایی است که `CLAUDE.md` قبل از هر بهبود می‌خواهد.

---

## Current — وضعیت فعلیِ سیستم

| بخش | وضعیت روی دیسک (`F:\backup\app`) |
|-----|-----------------------------------|
| `nbb_cp/kernel` | ساخته‌شده — ۱۲ invariant، gates، ledger، budget، sigma، fitness، lifecycle، pulse |
| `nbb_cp/adapters` | `llm/{cassette,mock}`، `runtime/system`، `storage/{memory,sqlite}`، `telemetry/noop` |
| `nbb_cp/app` | `service` (choke-point)، `governor`، `bootstrap`، `config` |
| `nbb_cp/api` | `http.py` (اسکلت) |
| `adapters/vault/` | **وجود ندارد** — هرچند `MANIFEST.yaml` آن را `BUILT + tested` اعلام کرده |
| `adapters/llm/fugu.py` | **وجود ندارد** — هرچند MANIFEST آن را `COMPLETE` اعلام کرده |
| `MANIFEST.yaml` → `primary_blocker` | «Phase 2 vault scanner needs vault path to run for real» |
| `VERDICT_QUEUE.md` → `NBB-V2` | «read-only dashboard ساخته شود؟» — **open** |
| اسکنِ متادیتای `_octopus` | خراب: سقف ۵۰k کاملاً داخل `.claude` مصرف شده، هیچ پوشهٔ نوتی دیده نشده |

> ⚠ **اختلافِ MANIFEST با کد** یک یافتهٔ مستقل است. یا این snapshot قدیمی است،
> یا MANIFEST جلوتر از واقعیت نوشته شده. تا وقتی روشن نشود، این ماژول **هیچ فایلی
> در `F:\backup\app` تغییر نمی‌دهد** — بیرون از آن می‌نشیند.

---

## Delta — دقیقاً چه چیزی اضافه می‌شود

یک پکیجِ **جدا و مستقل** به نام `nbb_cp_kre` در `F:\kre-out\nbb-cp-kre`:

```
+ src/nbb_cp_kre/kernel/guard.py            (جدید)  گاردِ read-only
+ src/nbb_cp_kre/kernel/types.py            (جدید)  types خالص
+ src/nbb_cp_kre/adapters/vault/scanner.py  (جدید)  ← جای خالیِ MANIFEST
+ src/nbb_cp_kre/adapters/vault/linkgraph.py(جدید)
+ src/nbb_cp_kre/adapters/kre/*.py          (جدید)  رقابت representationها
+ src/nbb_cp_kre/app/pipeline.py            (جدید)
+ src/nbb_cp_kre/ui/streamlit_app.py        (جدید)  ← پاسخِ NBB-V2
+ tests/test_kre.py                         (جدید)  ۱۶ تست
```

**هیچ خطی از `nbb_cp` تغییر نمی‌کند. هیچ فایلی حذف نمی‌شود. هیچ interfaceی عوض نمی‌شود.**
طبق قاعدهٔ ۳۰٪، این یک `rewrite` نیست — چون هیچ ماژولِ موجودی لمس نشده.

### وقتی تصمیم گرفتی داخلش کنی (اختیاری، بعداً)

فایل‌ها یک‌به‌یک به این مسیرها منتقل می‌شوند، **کنارِ** چیزهای موجود:

```
src/nbb_cp/adapters/vault/{scanner,linkgraph}.py
src/nbb_cp/adapters/kre/{representations,bakeoff,missing_links}.py
```

`kernel/` دست‌نخورده می‌ماند چون `guard.py` و `types.py` هم stdlib خالص‌اند و
`tests/test_import_lint.py` را نمی‌شکنند. `numpy/scipy/networkx/sklearn` فقط
داخل `adapters/` می‌روند و به `pyproject.toml` به‌صورت extra اضافه می‌شوند:

```toml
[project.optional-dependencies]
kre = ["numpy>=1.26", "scipy>=1.11", "networkx>=3.1", "scikit-learn>=1.3"]
```

اما این کار **الان انجام نشده**، چون:
1. `F:\backup` فقط‌خواندنی است (دستور مالک)
2. اختلافِ MANIFEST/کد هنوز حل نشده
3. طبق `RUNBOOK.md`، نقشِ NBB-CP هنوز `role-open` است

---

## Preserved — چه چیزی دست‌نخورده می‌ماند

* هر ۱۲ invariant — این ماژول هیچ‌کدام را نمی‌خواند، نمی‌نویسد، تضعیف نمی‌کند (INV-11)
* `ControlPlaneService.execute` همچنان تنها مسیرِ effect در nbb_cp است؛ این ماژول
  **هیچ effectی روی tenant/vault ندارد** پس مسیرِ دومِ اجرا نمی‌سازد (INV-4)
* خلوصِ `kernel/` (stdlib-only) و `test_import_lint.py`
* `policy.yaml` — این ماژول در ردهٔ `scan_metadata` + `create_report` می‌نشیند؛
  تنها فراتر رفتنش «خواندنِ محتوای `.md` برای استخراج لینک» است که **مالک برایش
  استثنای صریح داده**. هیچ‌یک از اقلامِ `requires_approval` انجام نمی‌شود.
* `money: locked` — این ماژول هیچ ربطی به budget/ledger ندارد

## Rollback — چطور همه‌چیز برمی‌گردد

```bat
python -m pip uninstall nbb-cp-kre
rmdir /s /q F:\kre-out
```

تمام. چون هیچ فایلی در `F:\backup` نوشته نشده، rollback یعنی حذفِ یک پوشه.
حالتِ سیستم دقیقاً همان چیزی است که قبل بود.

---

## پیشنهادِ verdictها

| ID | پیشنهاد | مبنا |
|----|----------|------|
| **NBB-V2** (read-only dashboard؟) | **YES** — ساخته و اجرا شد | خواستهٔ مالک + هیچ ریسکی ندارد چون read-only است |
| **NBB-V1** (نقش NBB نسبت به Architect/_ops) | همچنان `open` | این ماژول عمداً sibling است، نه governor — تصمیم را جلو نمی‌اندازد |
| **جدید: OCT-V1** | اسکنِ متادیتای `_octopus` باید تعمیر شود | ثابت شد که هیچ پوشهٔ نوتی را ندیده؛ `self_awareness: green` روی نقشهٔ خالی بنا شده |
| **جدید: NBB-V5** | اختلافِ `MANIFEST.yaml` با کدِ روی دیسک | MANIFEST دو فایل را `BUILT/COMPLETE` می‌خواند که وجود ندارند |
