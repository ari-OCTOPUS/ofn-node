#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scanner.py — چشمِ دکتر: خواندنِ ارگانیسمِ زنده ⟶ تولیدِ اسکن.

این تنها قطعه‌ای بود که واقعاً کم داشتیم. بدونِ آن دکتر **کور** است: حافظه دارد،
مغز دارد، دست دارد — ولی نمی‌تواند ببیند امروز چه خبر است.

**فقط‌خواندنی.** هیچ فایلی در `F:\\backup` نوشته یا لمس نمی‌شود.
خروجی dictی است که `ingest.ingest_scan()` مستقیم می‌خورد.

هر سنجه با **منشأ** و **رسید** بیرون می‌آید — نه عددِ لخت. این همان چیزی است که
`R-01` را قابل‌اجرا می‌کند: سنجهٔ درون‌زاد وارد می‌شود ولی رأی نمی‌دهد.
"""
from __future__ import annotations

import json, re, sqlite3, subprocess
from datetime import datetime, timezone
from pathlib import Path

# منشأِ هر سنجه — یک‌بار اینجا تعریف می‌شود، نه پراکنده در کد
PROV = {
    "beat": ("درون‌زاد", "ORGANISM-STATE.json → beat"),
    "velocity_per_hr": ("درون‌زاد", "pulse/heart-signals-latest.json — ۹۶٪ متروَنوم"),
    "innervation_pct": ("درون‌زاد", "cortex/innervation-latest.json — file-freshness"),
    "self_awareness_pct": ("درون‌زاد", "cortex/self-model.json — پوششِ docstring"),
    "improvement_rate": ("درون‌زاد", "cortex/upgrades-digest.json"),
    "organism_stress": ("برون‌زاد", "cortex/stress-latest.json"),
    "confirmed_revenue": ("برون‌زاد", "fitness-latest.json → attribution.confirmed"),
    "memory_rows": ("برون‌زاد", "state/memory/memory.db → SELECT count(*)"),
    "suite": ("برون‌زاد", "_ops/tests/run_all.py → exit code + شمار"),
    "delta_self_raw": ("برون‌زاد", "pulse/heart-signals-latest.json → delta_self_raw"),
    "period_s": ("برون‌زاد", "ORGANISM-STATE.json → arbiter.effective_period_s"),
    "beat_budget_remaining": ("برون‌زاد", "state/cardiac-budget.json"),
    "fugu_used": ("برون‌زاد", "state/fugu-quota.json → used_total"),
    "alert_signatures": ("برون‌زاد", "governor/governor-alerts.md — امضای یکتا"),
}
_NUM = re.compile(r"\d+")


def _j(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _m(name: str, value, status: str = "", extra: str = "") -> dict:
    prov, receipt = PROV.get(name, ("نامعلوم", ""))
    return {"value": value, "provenance": prov,
            "receipt": (receipt + (" · " + extra if extra else "")) or None,
            "status": status}


def scan(ops: str | Path, run_suite: bool = False) -> dict:
    """اسکنِ فقط‌خواندنیِ `_ops/`. `run_suite=True` سوئیت را هم اجرا می‌کند (~۳ دقیقه)."""
    O = Path(ops)
    S = O / "state"
    out: dict = {"date": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d"),
                 "metrics": {}, "findings": [], "unknown": []}
    M = out["metrics"]

    org = _j(S / "ORGANISM-STATE.json")
    if not org:
        out["unknown"].append("ORGANISM-STATE.json خوانده نشد — ارگانیسم خاموش است؟")
        return out

    out["beat"] = org.get("beat")
    M["beat"] = _m("beat", org.get("beat"))

    arb = org.get("arbiter") or {}
    bio = ((org.get("cardiac") or {}).get("bio_rhythm") or {})
    per = arb.get("effective_period_s")
    M["period_s"] = _m("period_s", per,
                       "🔴" if arb.get("driver", "").startswith("brake") else "🟢",
                       f"driver={arb.get('driver')} · bio={bio.get('period_s')}")
    if str(arb.get("driver", "")).startswith("brake"):
        out["findings"].append({
            "id": "F-AUTO-BRAKE", "title": "قلب ترمز خورده", "status": "🔴",
            "body": f"`effective_period_s={per}` با راننده `{arb.get('driver')}` "
                    f"در حالی که ریتمِ زیستی `{bio.get('period_s')}` است."})

    bud = (org.get("cardiac") or {}).get("budget") or _j(S / "cardiac-budget.json")
    rem = bud.get("remaining")
    M["beat_budget_remaining"] = _m("beat_budget_remaining", rem,
                                    "🔴" if bud.get("depleted") else "🟢",
                                    f"spent={bud.get('spent')}/{bud.get('daily_cap')}")

    hs = _j(S / "pulse" / "heart-signals-latest.json")
    vel = (hs.get("velocity") or {})
    share = vel.get("metronome_share")
    M["velocity_per_hr"] = _m("velocity_per_hr", vel.get("velocity_per_hr"),
                              "🔴" if (share or 0) > 0.9 else "🟡",
                              f"metronome_share={share}")
    ds = (hs.get("delta_self") or {})
    raw = ds.get("delta_self_raw")
    M["delta_self_raw"] = _m("delta_self_raw", raw, "🔴" if (raw or 0) < 0 else "🟢",
                             f"S_blind={ds.get('S_blind')} S_informed={ds.get('S_informed')}")
    if raw is not None and raw < 0:
        out["findings"].append({
            "id": "F-AUTO-DELTASELF", "title": "خودشناسیِ منفی", "status": "🔴",
            "body": f"`delta_self_raw={raw}` ولی `delta_self_live="
                    f"{ds.get('delta_self_live')}` منتشر می‌شود — clamp، خلافِ [[R-02]]."})

    st = _j(S / "cortex" / "stress-latest.json")
    M["organism_stress"] = _m("organism_stress", st.get("organism_stress"),
                              "🔴" if (st.get("organism_stress") or 0) >= 0.9 else "🟢",
                              f"in_fear={st.get('in_fear')}")

    inn = _j(S / "cortex" / "innervation-latest.json")
    M["innervation_pct"] = _m("innervation_pct", inn.get("coverage_pct"), "🔴")

    sm = _j(S / "cortex" / "self-model.json")
    M["self_awareness_pct"] = _m("self_awareness_pct", sm.get("self_awareness_pct"), "🔴")

    fit = _j(S / "fitness-latest.json")
    M["confirmed_revenue"] = _m("confirmed_revenue",
                                (fit.get("attribution") or {}).get("confirmed"),
                                "🔴" if not (fit.get("attribution") or {}).get("confirmed") else "🟢")

    fq = _j(S / "fugu-quota.json")
    M["fugu_used"] = _m("fugu_used", fq.get("used_total"), "🟢")

    # حافظه — شمارِ واقعی، نه ادعا
    mdb = S / "memory" / "memory.db"
    if mdb.exists():
        try:
            c = sqlite3.connect(f"file:{mdb}?mode=ro", uri=True)
            n = c.execute("select count(*) from memory").fetchone()[0]
            c.close()
            M["memory_rows"] = _m("memory_rows", n, "🔴" if n < 10 else "🟢")
            if n < 10:
                out["findings"].append({
                    "id": "F-AUTO-MEMORY", "title": "حافظهٔ بلندمدت تقریباً خالی",
                    "status": "🔴", "body": f"جدولِ `memory` فقط **{n} سطر** دارد."})
        except sqlite3.Error as e:
            out["unknown"].append(f"memory.db خوانده نشد: {e}")
    else:
        out["unknown"].append("memory.db وجود ندارد")

    # هشدارهای تکراری — امضا، نه تعداد خام
    ga = O / "governor" / "governor-alerts.md"
    if ga.exists():
        try:
            lines = [l for l in ga.read_text("utf-8", errors="replace").splitlines()
                     if l.strip().startswith("- ")]
            sigs: dict[str, int] = {}
            for l in lines:
                k = _NUM.sub("N", l)[:90]
                sigs[k] = sigs.get(k, 0) + 1
            top = sorted(sigs.items(), key=lambda x: -x[1])[:5]
            M["alert_signatures"] = _m("alert_signatures", len(sigs), "🔴" if top and top[0][1] > 50 else "🟢",
                                       f"{len(lines)} خط، پرتکرارترین ×{top[0][1] if top else 0}")
            for sig, n in top:
                if n > 50:
                    out["findings"].append({
                        "id": f"F-AUTO-ALERT-{abs(hash(sig)) % 1000}",
                        "title": f"هشدارِ تکراری ×{n}", "status": "🔴",
                        "body": f"```\n{sig.strip()}\n```\nیک امضا، **{n}** بار."})
        except OSError as e:
            out["unknown"].append(f"governor-alerts خوانده نشد: {e}")

    if run_suite:
        try:
            r = subprocess.run(["python", "-X", "utf8", str(O / "tests" / "run_all.py")],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=900, cwd=str(O.parent))
            n = None
            for l in (r.stdout or "").splitlines()[-30:]:
                mm = re.search(r"(\d+)\s*فایل تست", l) or re.search(r"(\d+)\s*passed", l)
                if mm:
                    n = int(mm.group(1))
            out["suite"] = f"{n}/{n}" if (n and r.returncode == 0) else f"exit={r.returncode}"
            M["suite"] = _m("suite", out["suite"], "🟢" if r.returncode == 0 else "🔴")
        except Exception as e:                                   # noqa: BLE001
            out["unknown"].append(f"سوئیت اجرا نشد: {type(e).__name__}")
    else:
        out["unknown"].append("سوئیت اجرا نشد (run_suite=False) — عددِ تست [UNKNOWN]")

    try:
        g = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(O.parent),
                           capture_output=True, text=True, timeout=20)
        if g.returncode == 0:
            out["branch"] = g.stdout.strip()
    except Exception:                                            # noqa: BLE001
        pass
    return out


if __name__ == "__main__":
    import sys
    print(json.dumps(scan(sys.argv[1] if len(sys.argv) > 1 else r"F:\backup\_ops"),
                     ensure_ascii=False, indent=2))
