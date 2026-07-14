#!/usr/bin/env python3
"""crypto_leg.py — WP-F · LEG-01: پای Crypto (status صادق، نه اتوماسیونِ جعلی).

قرارداد مشترکِ ۴ پای جدید: این ماژول یک helperِ فقط‌خواندنی در سطحِ ماژول می‌دهد:
  crypto_status() -> {"leg","live","signal","note"}

صداقت: منبعِ دادهٔ واقعی (خروجیِ ingest_raw در پوشهٔ Crypto - etoro) را می‌خواند —
snapshotهای cryptoquant/lunarcrush و آخرین فایلِ analysis. اگر داده بود → live=True و
سیگنالِ واقعی (buy/sell/hold از summaryِ analysis، دادهٔ بازار، بی‌PII). اگر نبود → live=False.

خط قرمز: صفر منطقِ درآمد جعلی، صفر side-effectِ پول/ترید، صفر secret. فقط گزارشِ وضعیت.
propose-only · $0 آفلاین · stdlib-only · منبعِ خام هرگز دست نمی‌خورد.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
VAULT = _HERE.parents[1]                                  # _ops/legs → _ops → vault root
# منبعِ دادهٔ واقعی (همان مسیرِ ingest_raw.CRYPTO؛ دادهٔ بازار، بی‌PII)
CRYPTO_DIR = VAULT / "03 - Projects" / "Crypto - etoro"


def _latest_analysis(cdir: Path) -> Path | None:
    """آخرین فایلِ cryptoquant_analysis_*.json (بر اساسِ نام که تایم‌استمپ‌دار است). fail-soft."""
    try:
        files = sorted(cdir.glob("cryptoquant_analysis_*.json"))
    except OSError:
        return None
    return files[-1] if files else None


def _analysis_signal(o: dict) -> str:
    """سیگنالِ صادق از یک analysis JSON، robust به دو schema (دادهٔ بازار، بی‌PII):
      * schemaِ signal-based:  summary.buy_signals/sell_signals/hold_signals → 'buy=.. sell=.. hold=..'
      * schemaِ coverage-based: assets[] + completeness.pct + errors[] → 'assets=N pct=P errors=E'
    اگر هیچ‌کدام نبود → صرفاً 'analysis-present' (باز هم صادق)."""
    s = o.get("summary")
    if isinstance(s, dict) and any(k in s for k in ("buy_signals", "sell_signals", "hold_signals")):
        return (f"buy={s.get('buy_signals', '?')} "
                f"sell={s.get('sell_signals', '?')} "
                f"hold={s.get('hold_signals', '?')}")
    assets = o.get("assets")
    comp = o.get("completeness") or {}
    if isinstance(assets, list) or comp:
        n_assets = len(assets) if isinstance(assets, list) else "?"
        pct = comp.get("pct", "?") if isinstance(comp, dict) else "?"
        n_err = len(o.get("errors") or []) if isinstance(o.get("errors"), list) else 0
        return f"assets={n_assets} completeness={pct}% errors={n_err}"
    return "analysis-present"


def crypto_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Crypto. هرگز crash نمی‌کند (fail-soft کامل).
    live=True فقط اگر منبعِ دادهٔ واقعی موجود باشد. سیگنال = buy/sell/hold از آخرین analysis
    (دادهٔ بازار، بی‌PII) یا صرفاً تعدادِ snapshotها. صفر منطقِ ترید/پول."""
    leg = "crypto"
    cdir = CRYPTO_DIR
    try:
        exists = cdir.exists()
    except OSError:
        exists = False
    if not exists:
        return {"leg": leg, "live": False, "signal": "no-data",
                "note": "منبعِ دادهٔ Crypto پیدا نشد — skeleton، منتظرِ afferent/ingest."}

    try:
        snapshots = list(cdir.glob("cryptoquant_*.json")) + list(cdir.glob("lunarcrush_*.json"))
        n_snap = len([p for p in snapshots if "analysis" not in p.name])
    except OSError:
        n_snap = 0

    ap = _latest_analysis(cdir)
    if ap is not None:
        try:
            o = json.load(open(ap, encoding="utf-8"))
            signal = _analysis_signal(o)
            note = (f"دادهٔ بازار زنده — {n_snap} snapshot؛ آخرین analysis: {ap.name} "
                    f"(بی‌PII، فقط‌خواندنی، صفر ترید).")
            return {"leg": leg, "live": True, "signal": signal, "note": note}
        except Exception:                                 # noqa: BLE001 — analysis خراب/ناقص
            pass

    if n_snap > 0:
        return {"leg": leg, "live": True, "signal": f"snapshots={n_snap}",
                "note": "snapshotهای بازار موجود؛ فایلِ analysis خوانده نشد (فقط‌خواندنی)."}
    return {"leg": leg, "live": False, "signal": "empty",
            "note": "پوشهٔ Crypto هست ولی خالی از snapshot — skeleton."}


if __name__ == "__main__":
    print(json.dumps(crypto_status(), ensure_ascii=False, indent=2))
