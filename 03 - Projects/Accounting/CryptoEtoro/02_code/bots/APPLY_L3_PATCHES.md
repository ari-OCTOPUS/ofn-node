---
type: patch-guide
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
tags: [crypto, L3, patch, deploy]
created: 2026-07-04
---

# APPLY — L3 patches (Coin Hunter scouting pipeline)

> این بسته سه اصلاحِ L3 را **پیاده و تست‌شده** می‌دهد. کدِ مقصد (`QuantumAlphaBot`) **بیرونِ** پوشهٔ کریپتوست → این‌ها را **آری/Architect از مسیرِ deploy gate (D-20)** اعمال می‌کند، نه مستقیم. همه **paper-mode** و مشروط به باز شدنِ §Security Gate.

## فایل‌های این بسته
| فایل | مقصد در repo | وضعیت |
|---|---|---|
| `fear_classifier.py` | `QuantumAlphaBot/modules/` | ✅ tested (11/11 + integration) |
| `mining_data.py` | `QuantumAlphaBot/modules/` | ✅ production-shaped (explorer registry) |
| `test_fear_classifier.py` | `QuantumAlphaBot/` | ✅ اجرا می‌شود با `python3` |

## Patch 1 — wire در `QuantumAlphaBot/main.py`

**imports (کنار بقیه، خطوط ۳۳–۴۲):**
```python
from modules.energy_funnel   import EnergyFunnel
from modules.edge_classifier import EdgeClassifier
from modules.fear_classifier import classify_fear
from modules.mining_data     import enrich_energy_inputs
```

**Step 1.5 — بعد از `coins = df.to_dict(...)` (خطِ ~۱۷۱):**
```python
    sec("Step 1.5: Energy Funnel")
    try:
        energy_cands = [enrich_energy_inputs(c) for c in EnergyFunnel().find_candidates()]
        seen = {c["symbol"] for c in coins}
        coins += [c for c in energy_cands if c["symbol"] not in seen]
        ok(f"EnergyFunnel: +{len(energy_cands)} candidate")
    except Exception as e:
        warn(f"EnergyFunnel error: {e}")
```

**Step 4.4 — بعد از HolderChecker (Step 4.3، خطِ ~۲۲۸) و قبل از VetoEngine (4.5):**
```python
    sec("Step 4.4: Edge Classification")
    try:
        for c in coins:
            c["fear_type"] = classify_fear(c)      # DISLOCATION را زنده می‌کند
        coins = EdgeClassifier().classify_all(coins)
        n_edge = sum(1 for c in coins if c.get("edge_present"))
        ok(f"EdgeClassifier: {n_edge}/{len(coins)} coin دارای edge")
    except Exception as e:
        warn(f"EdgeClassifier error: {e}")
```

> ترتیب حیاتی: EdgeClassifier **بعد از** HolderChecker (نیازِ `holder_count_delta`) و **بعد از** مشتقِ `fear_type`. حالا `paper_ledger.jsonl` مقدارِ `edge_present` معنادار دارد → گیتِ `②edge_present!=[]` در Coordinator عبور می‌کند.

## Patch 2 — تصحیحِ ۹→۱۶ worker (fleet count)

inventory واقعی **۱۶× OPi5 Pro** است، ولی کد ۹ فرض کرده → hashrate در همه‌جا کم‌شماری می‌شود.

**`fleet/models.py` خطِ ۳۴:**
```python
WORKER_COUNT = 16          # بود: 9  — inventory واقعی
```

**`QuantumAlphaBot/edges.yaml` (config_constants):**
```yaml
FLEET_HASHRATE_HS: 20400     # بود: 11475  (16 × 1500 × 0.85، yespower)
FLEET_TOTAL_RAM_GB: 272      # بود: 160    (16×16 + 16 main)
# کامنتِ «9× OPi5 Pro» → «16× OPi5 Pro»
```
> اثر: `fleet_share` بزرگ‌تر → آستانهٔ ENERGY برای شبکه‌های کوچک راحت‌تر عبور می‌کند (بدونِ آنکه kill مربوط به GPU/ASIC تضعیف شود).

## Patch 3 — ENERGY data (اختیاری، فازِ بعد)

`mining_data.enrich_energy_inputs()` در Step 1.5 وصل شد (بالا). تا وقتی `EXPLORERS` برای کوینِ هدف پر نشده، `network_hashrate=MISSING` و ENERGY صادقانه NO_EDGE می‌ماند (E-0). برای فعال‌سازی: یک ردیف به `EXPLORERS` اضافه کن (مثلاً Sugarchain) و explorerِ آن کوین را تست کن.

## Test evidence (اجراشده در sandbox، 2026-07-04)

```
$ python3 test_fear_classifier.py      → 11/11 passed (exit 0)

Integration (edge_classifier.py + edges.yaml واقعی):
  BEFORE (no fear_type): decision=NO_EDGE     edge_present=[]
  AFTER  (fear_type=PANIC_SELL): decision=DISLOCATION  edge_present=['DISLOCATION']
  INSIDER (fear_type=INSIDER_DUMP): decision=NO_EDGE   edge_present=[]
  → DISLOCATION فقط بعد از مشتقِ fear_type fire می‌کند؛ insider-dump همچنان killed.
```

## Governance

- **paper-mode فقط.** تا §Security Gate باز نشده (۴ CRITICAL) هیچ اجرای مالی/deploy.
- اعمالِ این patchها = تغییرِ کد → **verdictِ آری + مسیرِ deploy gate (D-20)**، نه مستقیم.
- بعد از اعمال: `test_fear_classifier.py` بخشی از anchor test بماند (BACKLOG-10).
