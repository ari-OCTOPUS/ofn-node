#!/usr/bin/env python3
"""crypto_leg.py — WP-F · LEG-01: پای Crypto (status صادق، نه اتوماسیونِ جعلی).

قرارداد مشترکِ ۴ پای جدید: این ماژول یک helperِ فقط‌خواندنی در سطحِ ماژول می‌دهد:
  crypto_status() -> {"leg","live","signal","note"}

صداقت: منبعِ دادهٔ واقعی (خروجیِ ingest_raw در پوشهٔ Crypto - etoro) را می‌خواند —
snapshotهای cryptoquant/lunarcrush و آخرین فایلِ analysis. برنامه ۷ (صداقتِ پاها):
live=True فقط وقتی داده *تازه* باشد (≤ CRYPTO_MAX_AGE_DAYS روز) — «داده جریان دارد»،
نه «فایلی وجود دارد». سیگنال همچنان صادقانه گزارش می‌شود (buy/sell/hold از summaryِ
analysis، دادهٔ بازار، بی‌PII) + کلیدِ افزودهٔ age_days (سنِ منبعِ سیگنال، یا null).

خط قرمز: صفر منطقِ درآمد جعلی، صفر side-effectِ پول/ترید، صفر secret. فقط گزارشِ وضعیت.
propose-only · $0 آفلاین · stdlib-only · منبعِ خام هرگز دست نمی‌خورد.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
try:
    from leg_freshness import age_days
except ImportError:                                       # fail-closed: سنِ نامعلوم → live=False
    def age_days(_p):  # type: ignore[misc]
        return None

VAULT = _HERE.parents[1]                                  # _ops/legs → _ops → vault root
# منبعِ دادهٔ واقعی (همان مسیرِ ingest_raw.CRYPTO؛ دادهٔ بازار، بی‌PII)
CRYPTO_DIR = VAULT / "03 - Projects" / "Crypto - etoro"
# آستانهٔ تازگی: بازارِ کریپتو روزانه است — دادهٔ >۷ روز یعنی pipeline خوابیده، نه زنده.
CRYPTO_MAX_AGE_DAYS = 7.0


_NAME_TS = re.compile(r"(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})")


def _data_age_days(p: Path | None) -> float | None:
    """سنِ *داده* به روز — اول تایم‌استمپِ داخلِ نامِ فایل (زمانِ واقعیِ ingest/analysis؛
    mtime بعد از copy/checkout/touch دروغ می‌گوید — دیده شد analysisِ 2026-06-15 با mtimeِ
    دیروز)، وگرنه fallback به mtime (leg_freshness.age_days). fail-soft None."""
    if p is None:
        return None
    m = _NAME_TS.search(p.name)
    if m:
        try:
            ts = datetime(*(int(g) for g in m.groups()))
            a = (datetime.now() - ts).total_seconds() / 86400.0
            return a if a >= 0.0 else 0.0
        except ValueError:
            pass
    return age_days(p)


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
    برنامه ۷: live=True فقط اگر منبعِ سیگنال تازه باشد (fresh ≤ CRYPTO_MAX_AGE_DAYS).
    سیگنال = buy/sell/hold از آخرین analysis (دادهٔ بازار، بی‌PII) یا تعدادِ snapshotها؛
    age_days = سنِ همان منبعی که سیگنال از آن آمد (گرد به ۰٫۱ روز، یا null). صفر ترید/پول."""
    leg = "crypto"
    cdir = CRYPTO_DIR
    try:
        exists = cdir.exists()
    except OSError:
        exists = False
    if not exists:
        return {"leg": leg, "live": False, "signal": "no-data", "age_days": None,
                "note": "منبعِ دادهٔ Crypto پیدا نشد — skeleton، منتظرِ afferent/ingest."}

    try:
        snapshots = [p for p in (list(cdir.glob("cryptoquant_*.json"))
                                 + list(cdir.glob("lunarcrush_*.json")))
                     if "analysis" not in p.name]
    except OSError:
        snapshots = []
    n_snap = len(snapshots)

    ap = _latest_analysis(cdir)
    if ap is not None:
        try:
            o = json.load(open(ap, encoding="utf-8"))
            signal = _analysis_signal(o)
            a = _data_age_days(ap)
            live = a is not None and a <= CRYPTO_MAX_AGE_DAYS
            note = (f"{n_snap} snapshot؛ آخرین analysis: {ap.name} "
                    f"(بی‌PII، فقط‌خواندنی، صفر ترید). "
                    + (f"دادهٔ تازه (≤{CRYPTO_MAX_AGE_DAYS:g} روز) — جریان دارد."
                       if live else
                       f"دادهٔ کهنه (>{CRYPTO_MAX_AGE_DAYS:g} روز) → live=False؛ "
                       f"pipeline (ingest_raw) باید دوباره داده بیاورد."))
            return {"leg": leg, "live": live, "signal": signal,
                    "age_days": round(a, 1) if a is not None else None, "note": note}
        except Exception:                                 # noqa: BLE001 — analysis خراب/ناقص
            pass

    if n_snap > 0:
        ages = [x for x in (_data_age_days(p) for p in snapshots) if x is not None]
        a = min(ages) if ages else None                   # تازه‌ترین داده، نه کهنه‌ترین
        live = a is not None and a <= CRYPTO_MAX_AGE_DAYS
        note = ("snapshotهای بازار موجود؛ فایلِ analysis خوانده نشد (فقط‌خواندنی). "
                + ("دادهٔ تازه — جریان دارد." if live else
                   f"snapshotها کهنه‌اند (>{CRYPTO_MAX_AGE_DAYS:g} روز) → live=False."))
        return {"leg": leg, "live": live, "signal": f"snapshots={n_snap}",
                "age_days": round(a, 1) if a is not None else None, "note": note}
    return {"leg": leg, "live": False, "signal": "empty", "age_days": None,
            "note": "پوشهٔ Crypto هست ولی خالی از snapshot — skeleton."}


if __name__ == "__main__":
    print(json.dumps(crypto_status(), ensure_ascii=False, indent=2))
