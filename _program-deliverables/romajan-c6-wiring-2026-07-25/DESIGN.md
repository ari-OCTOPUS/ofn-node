# romajan→C6 Wiring Design — فرضیه از ریاضی، نه از دستِ مالک

> تاریخ: 2026-07-25 · وضعیت: DESIGN (not wired) · رأیِ مالک: لازم
> ردیفِ دفترِ تز: `dream-4d-blackbox-extraction` (UNTESTED)
> بودجه: `_ops/budget/budgets.yaml → allocation.research` (share 0.25)

## ۱. مسئله

C6 producer الان ۴ پروب دارد (c6_probes.py) — همه **درونِ** vault هستند
(self_audit، RFC duplicates، Δ_self، phi). هیچ‌کدام از **بیرون** نمی‌آیند.
مسیرِ رویا (رأیِ مالک ۲۰۲۶-۰۷-۲۵) می‌گوید: «معادلاتِ ریاضیِ داخلِ دانشِ خام
استخراج شوند، در آزمایشگاه آزموده شوند.» آزمایشگاه = `F:\romajan`.

## ۲. آنچه romajan الان دارد (VERIFIED از 00-INDEX.md)

| موتور | چیست | خروجی |
|---|---|---|
| Engine A (PSLQ) | rediscovery قطعیِ روابطِ صحیح | claims_ledger.json (۱۷ verified) |
| Engine B (SINDy) | symbolic regression | claims_ledger.json (۲۷ executed) |
| evolution_lab | Price, Ne, F_ST | NO-GO (صادقانه) |
| evalharness | sealed eval + basis resolver | benchmark منجمد |

## ۳. طراحیِ سیم‌کشی (additive، flag-gated، default-off)

### ۳.۱ پروب‌های نو در c6_probes.py

```python
# فلگ: OCTOPUS_WIRE_ROMAJAN_PROBES (default OFF)
# مسیر: F:\romajan (hardcoded — همان lab در thesis-ledger._dream_track)

"romajan_new_claims": {
    "measure": _probe_romajan_new_claims,
    "floor": 0,
    "unit": "unprocessed-claims",
    "subject": "F:/romajan claims ledgers",
    "question": "آیا romajan ادعای verified/executed جدیدی دارد که C6 هنوز ندیده؟",
    "hypothesis": "claims_ledgerهای romajan شامل ادعاهایی هستند که هنوز به hypothesis-queue ترجمه نشده‌اند.",
    "falsification": ["تمام ادعاهای verified/executed قبلاً دیده شده‌اند (count=0)"],
    "fix_hint": "هر claim جدید → یک ردیف hypothesis با kind=romajan_claim",
}

"romajan_engine_a_idle": {
    "measure": _probe_romajan_engine_a_idle,
    "floor": 0,
    "unit": "days-since-last-run",
    "subject": "F:/romajan/propagation engine_a",
    "question": "آیا Engine A (PSLQ) بیش از ۷ روز است اجرا نشده؟",
    "hypothesis": "موتورِ rediscovery خاموش است و می‌تواند با یک اجرای read-only فرضیه بسازد.",
    "falsification": ["Engine A در ۷ روز اخیر اجرا شده (count=0)"],
}
```

### ۳.۲ مکانیزمِ پروب

```python
def _probe_romajan_new_claims() -> dict:
    """ادعاهای verified/executed در romajan را با seen-set مقایسه می‌کند.
    seen-set = state/c6/romajan-seen.json (append-only، هرگز حذف نمی‌شود).
    count = تعداد ادعاهای جدید. فقط‌خواندنی، $0، بدون شبکه."""
    ROMAJAN = Path(os.environ.get("ROMAJAN_LAB_PATH", "F:/romajan"))
    ledgers = [
        ROMAJAN / "propagation" / "claims_ledger.json",
        ROMAJAN / "propagation-lab" / "data" / "claims_ledger.json",
    ]
    seen_path = opslib.STATE_DIR / "c6" / "romajan-seen.json"
    seen = set()
    if seen_path.exists():
        try:
            seen = set(json.loads(seen_path.read_text("utf-8")))
        except (OSError, ValueError):
            pass
    new_ids = []
    for lp in ledgers:
        if not lp.exists():
            continue
        try:
            data = json.loads(lp.read_text("utf-8"))
            claims = data if isinstance(data, list) else data.get("claims", [])
            for c in claims:
                cid = str(c.get("id", ""))
                status = str(c.get("status", ""))
                if cid and cid not in seen and status in ("verified", "executed"):
                    new_ids.append(cid)
        except (OSError, ValueError):
            continue
    return {"count": len(new_ids), "detail": f"new={len(new_ids)} seen={len(seen)}"}
```

### ۳.۳ ترجمهٔ claim → hypothesis

وقتی پروب count>floor داد، producer یک ردیف می‌سازد:
- `kind`: `"romajan_claim"` (نوعِ نو در _derive_fns)
- `verifier`: claim را در evalharness romajan بازاجرا می‌کند (read-only)
- `falsification`: claim در بازاجرا fail شود
- RFC card به مالک: «romajan ادعای X را verified کرده — آیا به دفترِ تز اضافه شود؟»

### ۳.۴ آنچه این طراحی **نمی‌کند**

- کدِ romajan را تغییر نمی‌دهد (read-only)
- Engine A/B را اجرا نمی‌کند (فقط خروجی‌های موجود را می‌خواند)
- هیچ claim را خودکار به FACT ارتقا نمی‌دهد (قانونِ romajan: فقط اجرا → FACT)
- هیچ پولی خرج نمی‌کند ($0، بدون شبکه)

## ۴. قدم‌های اجرا (به ترتیب)

1. **مالک**: `OCTOPUS_WIRE_ROMAJAN_PROBES=1` را در OCTOPUS-flags.cmd بگذارد
2. **ایجنت**: دو پروب را به c6_probes.py اضافه کند (همین طراحی)
3. **ایجنت**: `romajan_claim` kind را به _derive_fns اضافه کند
4. **ایجنت**: تستِ hermetic بنویسد (بدونِ لمسِ F:\romajan در تست)
5. **مالک**: اولین RFC card را بخواند و رأی بدهد

## ۵. ریسک‌ها

- **مسیرِ hardcoded**: `F:\romajan` ممکن است جابجا شود. Mitigation: env var `ROMAJAN_LAB_PATH` با fallback.
- **claims_ledger schema**: اگر romajan فرمتِ ledger را عوض کند، پروب count=-1 می‌دهد (fail-soft، هرگز فرضیهٔ ساختگی).
- **تکرار با thesis_queue**: پروب‌های `thesis_delta_self_sign` و `thesis_phi_saturation` الان در c6_probes هستند و از state/thesis می‌خوانند. پروب‌های romajan مستقل‌اند و تداخل ندارند.

## ۶. معیارِ موفقیت

اولین ردیفِ `romajan_claim` در hypothesis-queue که:
1. از یک claimِ واقعیِ romajan آمده (نه seed)
2. در evalharness بازاجرا شده
3. RFC card به مالک رسیده
4. مالک رأی داده

→ ردیفِ `dream-4d-blackbox-extraction` در دفترِ تز از UNTESTED به اولین شاهد می‌رسد.
