---
type: design
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
tags: [crypto, L3, scouting, edge-classifier, skeleton-code]
version: 1.0
created: 2026-07-04
updated: 2026-07-04
parent: "[[03 - Projects/Crypto - etoro/CRYPTO_ARCHITECTURE_v1_2026-07-04]]"
---

# 🔬 L3 — SCOUTING PIPELINE: طراحی تفصیلی + اسکلت کد

> عمیق‌سازیِ L3 از `CRYPTO_ARCHITECTURE_v1`. مبنا: کدِ واقعیِ `QuantumAlphaBot` (main.py، edge_classifier.py، edges.yaml، energy_funnel.py). قانون: **کد واقعی > سند**.

---

## 1. Quick Summary

L3 = «کشف → فیلترِ بقا → edge → سایز». هستهٔ فکریِ کل پروژه اینجاست. کدِ اصلی ساخته شده، ولی **گلوگاهِ مسیرِ بحرانی همین‌جاست**: `EdgeClassifier` در `main.py` **صدا زده نمی‌شود**، و حتی با wire شدن، هر سه edge به‌خاطرِ **خلأِ داده** خاموش می‌مانند. این سند دقیقاً می‌گوید چرا و چطور درست می‌شود.

**حکم:** با ۳ اصلاحِ کوچک (wire + مشتق‌سازیِ `fear_type` + یک data-adapter) خط به کار می‌افتد؛ بدونِ آن‌ها `edge_present=[]` برای همیشه و کلِ سیستم NO_ACTION می‌دهد (که الان درست ولی بی‌ثمر است).

---

## 2. پایپ‌لاینِ واقعی امروز (از `main.py`)

| Step | ماژول | چه می‌کند | فیلدهایی که ست می‌کند |
|---|---|---|---|
| 1–3 | `GemHunter.find_gems()` | hard filters + scoring (survival/antifragile/social/derivs/on-chain) | `max_dd_pct`, `price_7d_pct`, `btc_trend`, `macro_cq_score` |
| 3.5 | `ScoutForensics.apply()` | کشتنِ ساختاری pre-LLM (LP lock، hooks، cluster) | `forensic_vetoed`, `forensic_reasons` |
| 4 | `LLMEvaluator` | Claude → ACCUMULATE/WATCH/SKIP | `llm_decision`, `llm_reasoning` |
| 4.3 | `HolderChecker.fetch()` | تمرکزِ هولدرها (GoPlus) | `holder_count_delta` |
| 4.5 | `VetoEngine.apply()` | veto پساسکورینگ | `vetoed` |
| 5 | `QuantumAllocator` | Barbell 80/20 + Kelly | `allocation_pct` |
| 5.5 | `PaperTrader.log_cycle()` | `paper_ledger.jsonl` (خوراکِ Coordinator) | — |

**❌ غایب:** بینِ هیچ‌کدام از این‌ها `EdgeClassifier` و `EnergyFunnel` صدا زده نمی‌شوند → `edge_present` هرگز روی coinها ست نمی‌شود → Coordinator گیتِ `②edge_present!=[]` را برای همه رد می‌کند → **NO_ACTION دائمی**.

---

## 3. ریشه‌یابی: چرا هر coin از edge gate رد می‌شود

`EdgeClassifier` اصل **E-0** دارد: edge فقط از inputهای **MEASURED** اثبات می‌شود. جدول زیر نشان می‌دهد هر edge کجا می‌میرد:

| Edge | required_inputs | وضعیتِ واقعی | چرا fire نمی‌کند |
|---|---|---|---|
| **ENERGY** (CORE) | mining_algo, **network_hashrate**, coin_price, **block_reward**, **blocks_per_day** | `energy_funnel._fetch_hashrate()` → **MISSING**؛ `_extract_block_reward()` → **None** | `inputs_missing=[network_hashrate]` + `sig_failed=[cost_below_price]` → همیشه False |
| **DISLOCATION** (SPEC) | forensic_*, max_dd_pct, price_7d_pct, **fear_type**, holder_count_delta | همه هست **جز `fear_type`** که **هیچ ماژولی derive نمی‌کند** → `None` | kill `fear_justified_or_unknown` (fear_type=None) → همیشه False |
| **YIELD** (CORE) | node_min_ram_gb, node_min_disk_gb, reward_rate, coin_price | **هیچ ماژولی این‌ها را source نمی‌کند** → همه None | `inputs_missing=[همه]` → همیشه False |

**نتیجهٔ کلیدی:** مشکل «باگ» نیست، **خلأِ منبعِ داده** است. سه اصلاحِ هدف‌دار لازم است (بخش ۵).

---

## 4. طراحیِ هدفِ L3 (Tier 1/2/3 + Edge framework)

سه‌tier، هم‌راستا با `tier1 scout prompt` و schemaِ Tier-3:

| Tier | نقش | موتور | هزینه |
|---|---|---|---|
| **Tier-1 Scout** | triageِ مکانیکی (launch≤90d، mcap $50k–$50M، CPU-algo، repo≥5، explorer زنده) | **LLM لوکال** (Qwen/Llama via Ollama) — rule-first | صفر (برق) |
| **Tier-2 Forensics + Edge** | `ScoutForensics` + `HolderChecker` + **`EdgeClassifier`** (E-0..E-3) | کد قاعده‌محور + GoPlus/on-chain | ~صفر |
| **Tier-3 Verdict** | مشورتِ عمیق + سایزِ Kelly | **Claude** (فقط برای بازماندگانِ Tier-2) | متری (budget sub-cap) |

**اصلِ edge (حفظ می‌شود):** E-0 NO_EDGE پیش‌فرض · E-1 هر edge = signature + kill محاسبه‌پذیر · E-2 PATIENCE فقط enabler · E-3 {latency_hft، generic_research، narrative_timing} هرگز.

**Data-source plan (برای fire شدنِ edgeها):**

| input | منبعِ پیشنهادی | جایگزین | یادداشت |
|---|---|---|---|
| network_hashrate | MiningPoolStats / minerstat API | explorerِ خودِ کوین | CoinGecko نمی‌دهد |
| block_reward + blocks_per_day | explorer API کوین (RPC `getblock`) | WhatToMine | per-coin |
| fear_type | **مشتق‌سازیِ محلی** (بخش ۵.۲) | — | صفر API |
| node specs (YIELD) | chain docs / staking API | — | YIELD فعلاً low-priority |

---

## 5. اصلاح‌های عملی (اسکلت کد)

### 5.1 — Wire کردنِ `EnergyFunnel` + `EdgeClassifier` در `main.py`

ترتیب حیاتی است: EdgeClassifier باید **بعد از HolderChecker** (نیازِ `holder_count_delta`) و **بعد از مشتقِ `fear_type`** اجرا شود.

```python
# main.py — imports (بالای فایل کنار بقیه)
from modules.energy_funnel   import EnergyFunnel
from modules.edge_classifier import EdgeClassifier
from modules.fear_classifier import classify_fear   # جدید — بخش 5.2

# ── Step 1.5: ENERGY funnel — coinهای PoW قابل‌ماین قبل از CEX listing ──
sec("Step 1.5: Energy Funnel")
try:
    ef = EnergyFunnel()
    energy_cands = ef.find_candidates()          # mining_algo/hashrate/... را annotate می‌کند
    # merge بدونِ تکرار (بر اساس symbol)
    seen = {c["symbol"] for c in coins}
    coins += [c for c in energy_cands if c["symbol"] not in seen]
    ok(f"EnergyFunnel: +{len(energy_cands)} candidate")
except Exception as e:
    warn(f"EnergyFunnel error: {e}")

# ── Step 4.4: Fear + Edge classification (بعد از HolderChecker 4.3) ──
sec("Step 4.4: Edge Classification")
try:
    for c in coins:
        c["fear_type"] = classify_fear(c)        # مشتقِ محلی، صفر API
    ec = EdgeClassifier()
    coins = ec.classify_all(coins)               # edge_present/edge_decision را ست می‌کند
    n_edge = sum(1 for c in coins if c.get("edge_present"))
    ok(f"EdgeClassifier: {n_edge}/{len(coins)} coin دارای edge")
except Exception as e:
    warn(f"EdgeClassifier error: {e}")
# سپس همان VetoEngine (4.5) → Allocation (5) → Paper (5.5)
```

> نتیجه: `paper_ledger.jsonl` حالا `edge_present` معنادار دارد → گیتِ Coordinator عبور می‌کند.

### 5.2 — ماژولِ جدید `modules/fear_classifier.py` (مشتقِ `fear_type`)

این تنها قطعهٔ گمشده‌ای است که DISLOCATION را از «همیشه‌خاموش» نجات می‌دهد. صفر API — از فیلدهای موجود مشتق می‌شود.

```python
"""fear_classifier.py — مشتقِ fear_type برای edge DISLOCATION (E-1)."""
import yaml
_CFG = yaml.safe_load(open("edges.yaml")).get("config_constants", {})
DD_FLOOR = float(_CFG.get("DD_FLOOR", 35.0))

def classify_fear(c: dict) -> str:
    """PANIC_SELL | SECTOR_CONTAGION | INSIDER_DUMP | UNKNOWN — از دادهٔ MEASURED."""
    dd       = c.get("max_dd_pct")
    hd       = c.get("holder_count_delta")       # HolderChecker؛ + = رشد هولدر حین ریزش
    forensic = bool(c.get("forensic_vetoed")) or bool(c.get("forensic_reasons"))
    regime   = (c.get("btc_trend") or "UNKNOWN").upper()  # GemHunter macro

    if dd is None or hd is None:
        return "UNKNOWN"                          # E-0: دادهٔ ناقص → قابل‌ابطال نیست
    if forensic or hd < 0:
        return "INSIDER_DUMP"                     # هولدرها فرار کردند / پرچمِ فارنزیک
    if regime == "DISTRIBUTING" and dd <= -DD_FLOOR:
        return "SECTOR_CONTAGION"                 # ریزشِ macro-driven، هولدر پایدار
    if hd >= 0 and dd <= -DD_FLOOR:
        return "PANIC_SELL"                       # پنیکِ ارگانیک، هولدر رو به رشد
    return "UNKNOWN"
```

منطق مستقیماً از `edges.yaml` (بخش fear_falsifiable) استخراج شده: فقط `PANIC_SELL`/`SECTOR_CONTAGION` می‌توانند edge بسازند؛ `INSIDER_DUMP`/`UNKNOWN` → kill.

### 5.3 — ENERGY data-adapter (اسکلتِ منبعِ hashrate/block-reward)

`energy_funnel._fetch_hashrate()` الان MISSING برمی‌گرداند. یک adapter واقعی جایش می‌گذاریم؛ تا آن زمان ENERGY صادقانه NO_EDGE می‌ماند (E-0 درست).

```python
# modules/mining_data.py (جدید) — منبعِ hashrate + block reward per-coin
import requests
from modules.field_value import FieldValue

def fetch_network_hashrate(coin_id: str, explorer_url: str | None) -> FieldValue:
    if not explorer_url:
        return FieldValue.missing("no-explorer")   # ENERGY خاموش می‌ماند — درست
    try:
        r = requests.get(f"{explorer_url}/api/getnetworkhashps", timeout=10)
        return FieldValue.measured(float(r.json()), "explorer")
    except Exception:
        return FieldValue.missing("explorer-error")
# blocks_per_day = 86400 / block_time_sec ؛ block_reward از getblockreward
```

### 5.4 — اصلاحِ `edges.yaml` برای ۱۶ worker (نه ۹)

inventory واقعی = **۱۶× OPi5 Pro** (نه ۹). مقادیرِ fleet را به‌روز کن:

| کلید | فعلی (۹) | درست (۱۶) |
|---|---|---|
| `FLEET_HASHRATE_HS` | 11475 | **20400** (16×1500×0.85) |
| `FLEET_TOTAL_RAM_GB` | 160 | **~272** (16×16 + 16) |
| کامنتِ «9× OPi5 Pro» | — | «16× OPi5 Pro» |

> اثر: `fleet_share` بزرگ‌تر → آستانهٔ ENERGY برای شبکه‌های کوچک راحت‌تر عبور می‌کند.

---

## 6. Failure modes & tests

- testهای موجود: `test_veto_*`, `test_social_*`, `test_social_holder_B5`. **افزودن:** `test_edge_classifier` (هر edge: کیسِ MEASURED-pass، کیسِ input-missing، کیسِ kill).
- **مانیتور:** اگر `n_edge==0` برای ≥N سیکلِ متوالی → همان الگوی `_check_macro_monotony` (هشدارِ تلگرام «edge sensor stuck» — احتمالِ خلأِ داده، نه بازارِ بی‌edge).
- **error compounding:** pipelineِ ۷مرحله‌ای → checkpoint بعد از EdgeClassifier (log تعدادِ survivor per stage).

---

## 7. Trade-offs (score 1–10؛ بالاتر=بهتر)

| تصمیم | Cost | Complexity | Maintainability | Security | Time | حکم |
|---|---|---|---|---|---|---|
| `fear_type` محلی (vs LLM) | 10 | 8 | 8 | 9 | 9 | ✅ صفر API، قطعی، falsifiable |
| ENERGY via explorer API (vs رهاکردن) | 6 | 5 | 6 | 7 | 4 | ⚠️ per-coin زحمت؛ فاز بعد |
| wire الان (vs صبر) | 9 | 9 | 8 | 8 | 9 | ✅ گلوگاه؛ کمترین کار، بیشترین اثر |
| YIELD فعلاً skip | 9 | 9 | 8 | 8 | 9 | ✅ ROI پایین تا staking source بیاید |

---

## 8. Next steps (فوری، بعد از باز شدنِ گیت)

1. **`fear_classifier.py` را بساز** + Step 4.4 را در `main.py` wire کن → DISLOCATION زنده می‌شود (بیشترین اثر، کمترین کد).
2. **`edges.yaml` را برای ۱۶ worker** به‌روز کن (بخش ۵.۴).
3. **یک explorer-adapter** برای ۱–۲ کوینِ yespowerِ هدف بساز تا ENERGY هم fire کند؛ تا آن زمان ENERGY صادقانه NO_EDGE.

> ⚠️ همهٔ این‌ها **paper-mode**‌اند و تا §Security Gate باز نشده صرفاً سیگنال/شبیه‌سازی‌اند — هیچ اجرای مالی.

---

## Sources (vault، read-only)

`QuantumAlphaBot/main.py` · `modules/edge_classifier.py` · `edges.yaml` · `modules/energy_funnel.py` · `Ai bots/ARCHITECTURE.md` · `tier1 scout prompt.pdf` · `CRYPTO_ARCHITECTURE_v1_2026-07-04.md`.
