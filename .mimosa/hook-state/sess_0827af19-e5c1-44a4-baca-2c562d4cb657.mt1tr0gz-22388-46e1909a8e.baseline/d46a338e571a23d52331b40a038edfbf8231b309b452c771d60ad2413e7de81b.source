#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chain_dashboard.py — پایش زنجیره‌های امضا/لجر/T48/پروب (درخواست مالک 2026-08-20).

نکتهٔ صادقانه دربارهٔ «chain 13»: چنین artifact ی در vault وجود ندارد و پیدا
نشد. زنجیره‌های واقعیِ قابل‌پایش همین‌ها هستند: (۱) زنجیرهٔ امضاهای Ed25519،
(۲) زنجیرهٔ هش لجر ژنوم (پیوند prev→hash)، (۳) جریان T48، (۴) پروب امضاشده،
(۵) گیت FX/انتشار RBA. اگر منظور چیز دیگری بود، نام دقیقش را بدهید.

اجرا:  python -X utf8 research/monitor/chain_dashboard.py [--fetch]
خروجی: JSON + خلاصهٔ یک‌خطی + 06-EVIDENCE/CHAIN-MONITOR-latest.json
هشدارها: هر FAIL/BLOCKED صریح چاپ می‌شود (برای چت/لاگ)."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "_ops"))
sys.path.insert(0, str(_ROOT / "_ops" / "cortex"))
sys.path.insert(0, str(_ROOT / "_ops" / "owner-signing"))

LEDGER = _ROOT / "07 - Knowledge/genome-system/ledger/ledger.jsonl"
PAYLOADS = ["EVENT-TIME-PROBE", "JUDGE-BIAS-PHASE2", "FULL-LOOP-FLASH"]
PROBE_RESULT = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json"
OUT = _ROOT / "06-EVIDENCE/CHAIN-MONITOR-latest.json"


def check_signatures() -> dict:
    from check_anchor import check
    ok_anchor, _, got = check()
    cards = {"anchor": {"ok": ok_anchor, "fingerprint": got}}
    for name in PAYLOADS:
        pay = _ROOT / f"02-DECISIONS/PAYLOAD-{name}-2026-08-20.json"
        sig = Path(str(pay) + ".sig")
        if not (pay.exists() and sig.exists()):
            cards[name] = {"ok": False, "why": "missing-files"}
            continue
        v = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-rawin",
                            "-inkey", str(_ROOT / "_ops/owner-signing/octopus-owner-ed25519-public.pem"),
                            "-in", str(pay), "-sigfile", str(sig)],
                           capture_output=True, text=True)
        cards[name] = {"ok": v.returncode == 0 and "Verified" in v.stdout,
                       "sha256": hashlib.sha256(pay.read_bytes()).hexdigest()[:16]}
    return cards


def check_ledger_chain(last_n: int = 200) -> dict:
    """پیوند ساختاری prev→hash روی آخرین N ردیف (بدون فرمول هش ردیف — صادقانه)."""
    if not LEDGER.exists():
        return {"ok": False, "why": "ledger-missing"}
    rows = []
    with LEDGER.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    tail = rows[-last_n:]
    breaks = 0
    for a, b in zip(tail, tail[1:]):
        if b.get("prev") and a.get("hash") and b["prev"] != a["hash"]:
            breaks += 1
    return {"ok": breaks == 0, "n_checked": len(tail), "linkage_breaks": breaks,
            "tip_n": len(rows), "tip_hash": (rows[-1].get("hash", "")[:16] if rows else "")}


def check_t48() -> dict:
    import sqlite3
    from datetime import datetime as dt
    db = _ROOT / "_ops/state/spine/spine.db"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    srcs = con.execute("SELECT domain, event_time_source, COUNT(*) FROM events "
                       "WHERE legacy_no_event_time=0 GROUP BY 1,2").fetchall()
    parse = lambda s: dt.fromisoformat(str(s).replace("Z", "+00:00"))
    stats = {}
    for dom, src, _n in srcs:
        vals = [(parse(r) - parse(o)).total_seconds() * 1000 for o, r in con.execute(
            "SELECT occurred_at, recorded_at FROM events WHERE legacy_no_event_time=0 "
            "AND domain=? AND event_time_source=?", (dom, src))]
        if len(vals) >= 2:
            m = sorted(vals)[len(vals)//2]
            mean = sum(vals)/len(vals)
            var = sum((v-mean)**2 for v in vals)/len(vals)
            stats[f"{dom}/{src}"] = {"n": len(vals), "median_ms": round(m, 1),
                                     "stdev_ms": round(var**0.5, 1)}
        else:
            stats[f"{dom}/{src}"] = {"n": len(vals)}
    con.close()
    return {"sources": stats}


def check_probe(fx_max_age_h: float = 24.0) -> dict:
    from cost_receipt import fx_pinned_fresh
    okfx, whyfx = fx_pinned_fresh(max_age_h=fx_max_age_h)
    out = {"fx_fresh": okfx, "fx_reason": whyfx}
    if PROBE_RESULT.exists():
        out["probe"] = json.loads(PROBE_RESULT.read_text(encoding="utf-8"))
    else:
        out["probe"] = {"status": "NOT_RUN", "why": "awaiting-fresh-FX (RBA publication)"}
    return out


def check_rba(fetch: bool) -> dict:
    csv_path = _ROOT / "_ops/state/f11-tmp.csv"
    if fetch:
        subprocess.run(["curl", "-s", "--max-time", "30",
                        "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv",
                        "-o", str(csv_path)], check=False)
    if not csv_path.exists():
        return {"latest_publication": "UNKNOWN (no cached CSV; run with --fetch)"}
    rows = list(csv.reader(csv_path.open(encoding="utf-8", errors="replace")))
    pub = rows[9][1] if len(rows) > 9 and len(rows[9]) > 1 else "?"
    last = [r for r in rows[11:] if len(r) > 1 and r[0].strip()[:1].isdigit()][-1:]
    return {"latest_publication": pub,
            "latest_row": {"date": last[0][0], "aud_usd": last[0][1]} if last else None}


def main(fetch: bool = False) -> dict:
    report = {
        "schema": "chain-monitor/1", "ts": datetime.now(timezone.utc).isoformat(),
        "note_chain13": "no artifact named 'chain 13' exists in vault; monitored real chains",
        "signatures": check_signatures(),
        "ledger_chain": check_ledger_chain(),
        "t48": check_t48(),
        "probe": check_probe(),
        "rba": check_rba(fetch),
    }
    alerts = []
    for k, v in report["signatures"].items():
        if not v.get("ok"):
            alerts.append(f"ALERT signature:{k} FAILED")
    if not report["ledger_chain"].get("ok"):
        alerts.append(f"ALERT ledger-chain {report['ledger_chain']}")
    p = report["probe"].get("probe", {})
    if p.get("status") == "CALL_FAILED":
        alerts.append("ALERT probe CALL_FAILED")
    if p.get("status") == "BLOCKED" and "fx" in str(p.get("why", "")):
        alerts.append("INFO probe blocked on FX (RBA pending) — watcher armed")
    report["alerts"] = alerts or ["ALL GREEN"]
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = main(fetch="--fetch" in sys.argv)
    print(json.dumps({"alerts": r["alerts"],
                      "signatures": {k: v.get("ok") for k, v in r["signatures"].items()},
                      "ledger": r["ledger_chain"],
                      "t48": r["t48"]["sources"],
                      "probe_status": r["probe"].get("probe", {}).get("status"),
                      "rba": r["rba"]}, ensure_ascii=False, indent=1))
