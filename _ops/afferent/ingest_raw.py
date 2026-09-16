#!/usr/bin/env python3
"""ingest_raw.py — پاسِ ingestionِ دادهٔ خام (propose-only، محلی، $0، صفر نشتِ PII).

فایل‌های بزرگ را برنامه‌ای summarize می‌کند (نه full-dump به هیچ LLM):
  P1 Crypto JSON (بی‌PII، دادهٔ بازار) → schema + aggregate → <file>-summary.md کنارِ snapshot.
  P4 analysis JSON → سیگنال‌های buy/sell در همان summary.
  P2 Accounting xlsx (PII) → فقط ساختار (stdlib zip/XML، صفر مقدار) → نوتِ داخلِ پوشهٔ Accounting.
هر summary یک نوتِ draft/propose-only است. فید به sensory_bus (afferent) با لیبلِ بی‌PII.

خط قرمز: Accounting هرگز مقدار/ردیف/نام echo نمی‌شود (فقط تعداد شیت/ابعاد)؛ Crypto=بازار؛
propose-only؛ containment؛ بدونِ overwriteِ منبعِ خام؛ بدونِ git commit.
اجرا: python -X utf8 ingest_raw.py [--crypto] [--accounting]
"""
from __future__ import annotations

import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from sensory_bus import SensoryBus, Observation, _contains_pii  # noqa: E402

VAULT = _HERE.parents[1]                       # F:\backup
CRYPTO = VAULT / "03 - Projects" / "Crypto - etoro"
ACCT = VAULT / "03 - Projects" / "Accounting" / "data" / "حساب کتاب"

FM = ("---\ntype: report\nstatus: draft\ncreated_by: agent\n"
      "tags: [{tags}]\ncreated: {d}\nupdated: {d}\n---\n\n")
TODAY = "2026-07-09"


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _series_stats(rows: list) -> dict:
    """aggregate روی یک سری list-of-dict: بازهٔ تاریخ + min/max/mean ستون‌های عددی. بی‌PII (بازار)."""
    if not rows or not isinstance(rows[0], dict):
        return {"count": len(rows)}
    dates = [r.get("date") for r in rows if isinstance(r.get("date"), str)]
    numcols = [k for k in rows[0] if _num(rows[0].get(k))]
    stats = {}
    for c in numcols[:8]:
        vals = [r[c] for r in rows if _num(r.get(c))]
        if vals:
            stats[c] = {"min": round(min(vals), 4), "max": round(max(vals), 4),
                        "mean": round(sum(vals) / len(vals), 4)}
    out = {"count": len(rows), "numeric_cols": numcols[:12]}
    if dates:
        out["date_range"] = f"{min(dates)} … {max(dates)}"
    if stats:
        out["stats"] = stats
    return out


def summarize_crypto_file(fp: Path) -> tuple[str, dict]:
    """یک فایلِ crypto → متنِ summary + meta برای observation. صفر رکوردِ خام (فقط aggregate)."""
    o = json.load(open(fp, encoding="utf-8"))
    name = fp.name
    is_analysis = "analysis" in name
    lines = [f"# Crypto snapshot — {name}", ""]
    meta = o.get("meta") or {}
    fetched = meta.get("fetchedAt") or o.get("generated_at") or "?"
    lines.append(f"- منبع: `{name}` · fetched: {fetched} · plan: {o.get('plan') or meta.get('plan') or '?'}")
    obs_label = f"crypto {name.split('_')[0]} {str(fetched)[:10]}"

    if is_analysis:
        s = o.get("summary") or {}
        lines.append(f"- سیگنال‌ها: total={s.get('total_coins','?')} · "
                     f"buy={s.get('buy_signals','?')} · sell={s.get('sell_signals','?')} · "
                     f"hold={s.get('hold_signals','?')}")
        for side in ("top_buy_candidates", "top_sell_candidates"):
            cands = o.get(side) or []
            syms = [str(c.get("symbol")) for c in cands if isinstance(c, dict) and c.get("symbol")]
            if syms:
                lines.append(f"- {side.replace('top_','').replace('_candidates','')}: {', '.join(syms[:12])}")
        lines.append(f"- errors: {len(o.get('errors') or [])}")
        obs_type, intensity = "market", 0.7
    else:
        # snapshotِ خام: هر بخش → schema + aggregate
        coins = o.get("coins_detail")
        if isinstance(coins, dict) and coins:
            lines.append(f"- coins_detail: {len(coins)} سکه — {', '.join(list(coins)[:40])}")
        secs = [k for k in o if k != "meta"]
        lines.append(f"- بخش‌ها ({len(secs)}؛ نمایشِ ۴۰ اول — بقیه هم‌الگو):")
        stat_budget = 6                              # aggregateِ کلیدی فقط برای چند سریِ اول
        for k in secs[:40]:
            v = o[k]
            if isinstance(v, list):
                st = _series_stats(v)
                extra = f" · {st['date_range']}" if "date_range" in st else ""
                line = f"  - `{k}`: list[{st['count']}]{extra}"
                if stat_budget > 0 and st.get("stats"):
                    c0 = next(iter(st["stats"]))
                    s0 = st["stats"][c0]
                    line += f" · {c0}[min {s0['min']} · mean {s0['mean']} · max {s0['max']}]"
                    stat_budget -= 1
                lines.append(line)
            elif isinstance(v, dict):
                inner = v.get("data")
                n = len(inner) if isinstance(inner, (list, dict)) else len(v)
                lines.append(f"  - `{k}`: dict · ~{n} آیتم")
        if len(secs) > 40:
            lines.append(f"  - … و {len(secs) - 40} بخشِ دیگر (هم‌الگو).")
        if isinstance(meta.get("assets"), list):
            lines.append(f"- assets: {', '.join(str(a) for a in meta['assets'][:20])}")
        if meta.get("errors"):
            lines.append(f"- meta.errors: {meta.get('errors')}")
        obs_type, intensity = "market", 0.6
    lines.append("\n> propose-only · دادهٔ بازار (بی‌PII) · منبعِ خام دست‌نخورده.")
    text = FM.format(tags="crypto, market, ingestion, afferent", d=TODAY) + "\n".join(lines) + "\n"
    return text, {"label": obs_label, "obs_type": obs_type, "intensity": intensity}


def summarize_xlsx_structure(fp: Path) -> tuple[str, int]:
    """Accounting xlsx → فقط ساختار (تعداد شیت + ابعاد) با stdlib zip/XML. صفر مقدار خوانده می‌شود.
    نه sharedStrings، نه cellها — پس صفر ریسکِ PII. خروجی: (متن، تعداد شیت)."""
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    sheets, dims = [], {}
    with zipfile.ZipFile(fp) as z:
        names = z.namelist()
        try:
            wb = ET.fromstring(z.read("xl/workbook.xml"))
            for s in wb.iter(f"{ns}sheet"):
                sheets.append(s.get("name", "?"))
        except Exception:  # noqa: BLE001
            pass
        for wsname in [n for n in names if n.startswith("xl/worksheets/sheet")]:
            try:
                ws = ET.fromstring(z.read(wsname))
                dim = ws.find(f"{ns}dimension")
                dims[wsname.split("/")[-1]] = dim.get("ref") if dim is not None else "?"
            except Exception:  # noqa: BLE001
                dims[wsname.split("/")[-1]] = "?"
    # نامِ شیت ممکن است حساس باشد → PII-check؛ اگر مشکوک، redact
    safe_sheets = [s if not _contains_pii(s) else "‹redacted›" for s in sheets]
    lines = [f"# Accounting structure — {fp.name}", "",
             f"- شیت‌ها: {len(sheets)} → {', '.join(safe_sheets) if safe_sheets else '?'}",
             "- ابعاد (rows×cols ref، بدونِ هیچ مقدار):"]
    for sh, ref in dims.items():
        lines.append(f"  - {sh}: {ref}")
    lines.append("\n> ⚠️ فقط ساختار — صفر ردیف/نام/عدد خوانده شد (stdlib zip/XML، بدونِ sharedStrings/cell).")
    lines.append("> ⚑ برای معمار: استخراجِ ستون/جمع نیازمندِ openpyxl (نصب نیست؛ $0/offline اجازه نداد) — deferred.")
    lines.append("> propose-only · containment: داخلِ پوشهٔ Accounting · منبعِ خام دست‌نخورده.")
    text = FM.format(tags="accounting, structure, ingestion, containment", d=TODAY) + "\n".join(lines) + "\n"
    return text, len(sheets)


def run(do_crypto=True, do_acct=True) -> dict:
    bus = SensoryBus()
    report = {"crypto_notes": [], "acct_notes": [], "observations": 0,
              "pii_flags": [], "ratio_before": None, "ratio_after": None}

    # baseline: سیستم «رؤیا» می‌بیند (همه رویدادِ درونی، بدونِ ورودیِ حسی)
    for _ in range(20):
        bus.ingest_internal(source="organism", detail="epoch/tick")
    report["ratio_before"] = round(bus.afferent_ratio, 3)
    report["alarm_before"] = bus.check_alarm() is not None

    if do_crypto and CRYPTO.exists():
        for fp in sorted(CRYPTO.glob("*.json")):
            try:
                text, obsmeta = summarize_crypto_file(fp)
            except Exception as e:  # noqa: BLE001
                report["pii_flags"].append(f"crypto parse err {fp.name}: {type(e).__name__}")
                continue
            if _contains_pii(text):                      # نباید رخ دهد (بازار)
                report["pii_flags"].append(f"PII in {fp.name} — SKIPPED WRITE")
                continue
            note = fp.with_name(fp.stem + "-summary.md")
            note.write_text(text, encoding="utf-8")
            report["crypto_notes"].append(note.name)
            ev = bus.ingest(Observation(source="crypto", obs_type=obsmeta["obs_type"],
                                        label=obsmeta["label"], intensity=obsmeta["intensity"]))
            report["observations"] += 1
            if not ev.afferent:                          # PII در label → رد
                report["pii_flags"].append(f"obs rejected (PII label) {fp.name}")

    if do_acct and ACCT.exists():
        for fp in sorted(ACCT.glob("*.xlsx")):
            try:
                text, nsheets = summarize_xlsx_structure(fp)
            except Exception as e:  # noqa: BLE001
                report["pii_flags"].append(f"xlsx err {fp.name}: {type(e).__name__}")
                continue
            if _contains_pii(text):
                report["pii_flags"].append(f"PII in acct note {fp.name} — SKIPPED WRITE")
                continue
            note = fp.with_name(fp.stem + "-structure.md")
            note.write_text(text, encoding="utf-8")
            report["acct_notes"].append(note.name)
            # فیدِ sensory_bus: لیبلِ کاملاً انتزاعی (بدونِ نام/فایل) — بی‌PII، cross-domain امن
            bus.ingest(Observation(source="accounting", obs_type="status",
                                   label=f"accounting workbook · {nsheets} sheets (structure only)",
                                   intensity=0.4))
            report["observations"] += 1

    report["ratio_after"] = round(bus.afferent_ratio, 3)
    report["alarm_after"] = bus.check_alarm() is not None
    report["bus_status"] = bus.status()

    # پلِ School: آنچه حس شد را «کلاس درسِ» اختاپوس یاد بگیرد + persist (حافظه). propose-only.
    try:
        from school_bridge import SchoolBridge
        report["school"] = SchoolBridge().learn_from(list(bus._events))
    except Exception as e:  # noqa: BLE001 — پل اختیاری/additive، نباید ingestion را بکشد
        report["school"] = {"error": f"{type(e).__name__}: {e}"}
    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    r = run(do_crypto=("--accounting" not in args), do_acct=("--crypto" not in args)) if args else run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
