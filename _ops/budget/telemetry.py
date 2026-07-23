#!/usr/bin/env python3
"""
telemetry.py — T1 پک: خوانندهٔ واحد مصرف هر دو استک در فضای micro-USD.

منابع حقیقت (نقشهٔ 2026-07-06، هر دو verify‌شده path:line):
  1) genome-system → ledger/ledger.jsonl، رویدادهای METRIC با payload.llm_cost_usd
     (نوشته‌شده در common/llm.py:82-85). ارگان: GENOME_SYS.
  2) control-brain → core.db جدول usage(day,provider,business,tokens_in,tokens_out,cost_usd)
     (نوشته‌شده در core/gateway.py:86-96 → core/memory.py:188-195). خواندن فقط mode=ro.
بقیهٔ فایل‌های state (budget-state.json، doctor_lite_runs.jsonl، leads.db) فقط در کد
رفرنس‌اند — نبودشان fail-soft هندل می‌شود.

تله‌های هدف (تست‌کیس اول، پک T1):
  «متر or 0»: رویداد METRIC با هزینهٔ صفر و رکورد usage با هزینهٔ NULL/صفر در حالی که
  توکن مصرف شده → شمارش در suspects به‌جای بلعیدن بی‌صدا.
  «واحد ارز»: هزینه‌ها USD، سقف‌ها AUD — تبدیل فقط با نرخ پین‌شده (fx_aud_per_usd).

I3 (fail-closed): اگر جمع ماه از cap_monthly گذشت، یا billed (budget-state) با تلمتری
بیش از ۲۰٪ اختلاف داشت → FREEZE + [CONFLICT] به صف انسان + STOP-METABOLIC (شرط مرگ پک).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib  # noqa: E402

DIVERGENCE_DEATH = 0.20   # |billed−telemetry|/billed > 0.2 → STOP-METABOLIC (پک، شرط مرگ)

# نگاشت business/actor → ارگان budgets.yaml؛ ناشناخته‌ها UNMAPPED می‌شوند (نه حدس، نه حذف)
ORGAN_MAP = {
    "ziman": "ZIMAN",
    "projectf": "PROJECT_F",
    "debate": "DEBATE_LOOP",
    "metabolism": "ARCHITECT_SYS",
    "governor": "ARCHITECT_SYS",
    "evolution": "ARCHITECT_SYS",
    "painting": "PAINTING",        # verdict 2026-07-18 integration-debug (proposed-diff §۵) — رفع UNMAPPED:painting
    "accounting": "ACCOUNTING",    # verdict 2026-07-18 integration-debug (proposed-diff §۵) — رفع UNMAPPED:accounting
}


def _organ_of(business: str) -> str:
    b = (business or "").strip().lower()
    return ORGAN_MAP.get(b, f"UNMAPPED:{b or 'none'}")


def read_genome() -> dict:
    """METRICهای llm_cost_usd از ledger ژنوم. همهٔ مصرف این استک = ارگان GENOME_SYS."""
    out = {"events": 0, "cost_musd": 0, "by_day": {}, "suspect_zero": 0, "source": None}
    path = opslib.GENOME_DIR / "ledger" / "ledger.jsonl"
    if not path.exists():
        return out
    out["source"] = str(path)
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # سطر پاره‌شده وسط crash — خواننده تحمل می‌کند (قرارداد ledger)
            if rec.get("type") != "METRIC":
                continue
            p = rec.get("payload") or {}
            if "llm_cost_usd" not in p:
                continue
            day = (rec.get("ts") or "")[:10]
            cost = p.get("llm_cost_usd")
            m = opslib.micro(float(cost or 0.0))
            out["events"] += 1
            out["cost_musd"] += m
            out["by_day"][day] = out["by_day"].get(day, 0) + m
            if not cost:  # صفر/None با وجود call واقعی = مشکوک به تلهٔ «or 0» (llm.py:75-78)
                out["suspect_zero"] += 1
    return out


def _brain_db() -> Path | None:
    """core.db: کنار کد هاردکد است (app.py)؛ نسخهٔ تولیدی ممکن است زیر پروفایل کاربر باشد.
    جدیدترینِ موجودها انتخاب و منبع ثبت می‌شود."""
    import os
    candidates = [
        opslib.BRAIN_DIR / "core.db",
        Path(os.environ.get("USERPROFILE", "")) / ".ziman-control" / "core.db",
    ]
    existing = [p for p in candidates if p.exists()]
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)


def read_brain() -> dict:
    """جدول usage در core.db — فقط‌خواندنی (mode=ro) تا با سه نویسندهٔ موجود sqlite رقابت نکنیم."""
    out = {"rows": 0, "cost_musd": 0, "by_day": {}, "by_organ": {},
           "suspect_zero": 0, "unmapped": {}, "source": None}
    db = _brain_db()
    if db is None:
        return out
    out["source"] = str(db)
    uri = "file:///" + quote(str(db.resolve()).replace("\\", "/")) + "?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True, timeout=5)
    except sqlite3.Error as e:
        opslib.alert([f"telemetry: core.db unreadable ro: {e}"])
        return out
    try:
        rows = con.execute(
            "SELECT day, provider, business, tokens_in, tokens_out, cost_usd FROM usage").fetchall()
    except sqlite3.Error as e:
        opslib.alert([f"telemetry: usage table query failed: {e}"])
        return out
    finally:
        con.close()
    for day, provider, business, tin, tout, cost in rows:
        m = opslib.micro(float(cost or 0.0))
        organ = _organ_of(business)
        out["rows"] += 1
        out["cost_musd"] += m
        out["by_day"][day] = out["by_day"].get(day, 0) + m
        out["by_organ"][organ] = out["by_organ"].get(organ, 0) + m
        if organ.startswith("UNMAPPED:"):
            out["unmapped"][organ] = out["unmapped"].get(organ, 0) + m
        if not cost and ((tin or 0) + (tout or 0)) > 0:
            out["suspect_zero"] += 1   # تلهٔ «or 0» سمت gateway (gateway.py:87-93)
    return out


def read_organ_gate() -> dict:
    """مصرفِ زندهٔ گیتِ متابولیسم از organ-state.json — منبعِ حقیقتِ همان استکی که
    budget-state.json «billed» را می‌سازد (organ_gate → budget_gate، reserve/settle).
    این همان مسیری است که cortex/model_router با آن متر می‌کند و `core.db` هرگز آن را
    نمی‌بیند (نقشهٔ 2026-07-06: core.db فقط استکِ control-brain است). افزودنِ این منبع
    شکافِ رصدی را می‌بندد که تا 2026-07-23 «month=0» و واگراییِ کاذبِ ۱۰۰٪ می‌ساخت.
    fail-soft: نبودِ فایل / ماهِ کهنه / سطرِ خراب → 0 (نه حدس، نه مرگِ کاذب)."""
    out = {"month_musd": 0, "today_musd": 0, "by_organ": {}, "source": None, "live": False}
    path = opslib.ORGAN_STATE
    if not path.exists():
        return out
    out["source"] = str(path)
    try:
        state = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError) as e:
        opslib.alert([f"telemetry: organ-state unreadable: {e}"])
        return out
    out["live"] = True
    same_month = state.get("month") == opslib.month()
    today = opslib.today()
    for name, o in (state.get("organs") or {}).items():
        if not isinstance(o, dict):
            continue
        m = int(o.get("spent_month_musd", 0) or 0) if same_month else 0
        t = int(o.get("spent_today_musd", 0) or 0) if o.get("date") == today else 0
        out["month_musd"] += m
        out["today_musd"] += t
        if m:
            out["by_organ"][name] = out["by_organ"].get(name, 0) + m
    return out


def snapshot(write: bool = True) -> dict:
    """عکس واحد micro-USD از کل ارگانیسم + ثبت روی دیسک برای UI/گاورنر."""
    fx, fx_tag = opslib.fx_aud_per_usd()
    g, b, og = read_genome(), read_brain(), read_organ_gate()
    mon = opslib.month()
    # جمعِ ماه/امروز از منابعِ زنده: ژنوم‌لجر + organ_gate (متابولیسم/cortex — همان استکی که
    # billed را می‌سازد) + core.db (استکِ control-brain؛ فعلاً یخ‌زده → 0). organ_gate و core.db
    # مسیرهای مجزااند (call هر کدام فقط در یکی متر می‌شود) پس جمعشان دوباره‌شماری نیست.
    month_musd = (sum(v for d, v in g["by_day"].items() if d.startswith(mon))
                  + sum(v for d, v in b["by_day"].items() if d.startswith(mon))
                  + og["month_musd"])
    today_musd = (g["by_day"].get(opslib.today(), 0)
                  + b["by_day"].get(opslib.today(), 0)
                  + og["today_musd"])
    per_organ = dict(b["by_organ"])
    per_organ["GENOME_SYS"] = per_organ.get("GENOME_SYS", 0) + g["cost_musd"]
    for _name, _m in og["by_organ"].items():
        per_organ[_name] = per_organ.get(_name, 0) + _m
    snap = {
        "ts": opslib.now_iso(),
        "unit": "micro-USD (int)",
        "fx_aud_per_usd": {"rate": fx, "tag": fx_tag},
        "sources": {"genome_ledger": g["source"], "brain_core_db": b["source"],
                    "organ_gate": og["source"]},
        "genome": {k: g[k] for k in ("events", "cost_musd", "suspect_zero")},
        "brain": {k: b[k] for k in ("rows", "cost_musd", "suspect_zero")},
        "organ_gate": {"month_musd": og["month_musd"], "today_musd": og["today_musd"],
                       "live": og["live"]},
        "per_organ_alltime_musd": per_organ,
        "unmapped_musd": b["unmapped"],
        "month": {"key": mon, "musd": month_musd,
                  "usd": round(opslib.usd(month_musd), 6),
                  "aud": round(opslib.usd(month_musd) * fx, 6)},
        "today": {"musd": today_musd, "usd": round(opslib.usd(today_musd), 6)},
        "suspect_zero_total": g["suspect_zero"] + b["suspect_zero"],
    }
    if write:
        day_dir = opslib.STATE_DIR / "telemetry"
        with opslib.LockedJson(opslib.STATE_DIR / "telemetry-latest.json") as lj:
            lj.write(snap)
        with opslib.LockedJson(day_dir / f"{opslib.today()}.json") as lj:
            lj.write(snap)
    return snap


def reconcile(snap: dict) -> list[str]:
    """I3 + شرط مرگ پک. خروجی: لیست ناسازگاری‌ها (خالی = سالم)."""
    problems: list[str] = []
    caps = opslib.load_budgets()["global"]
    cap_aud = float(caps.get("cap_monthly", 30))
    if snap["month"]["aud"] > cap_aud:
        problems.append(
            f"telemetry month AU${snap['month']['aud']:.2f} > cap_monthly AU${cap_aud:.2f}")
    # billed = آنچه budget_gate رزرو/تسویه کرده (اگر state هنوز ساخته نشده → مقایسه‌ای نیست)
    if opslib.BUDGET_STATE.exists():
        try:
            billed = json.loads(opslib.BUDGET_STATE.read_text("utf-8"))
            billed_aud = float(billed.get("spent_month_aud", 0.0))
            tel_aud = float(snap["month"]["aud"])
            if billed_aud > 0.05:  # زیر ۵ سنت مقایسه بی‌معناست
                if tel_aud <= 0.0:
                    # شکافِ رصد، نه واگرایی: منبعِ زندهٔ تلمتری صفر/تهی است (مثلِ core.dbِ
                    # یخ‌زده) در حالی که billed>کف. صفرِ یک منبعِ تهی هرگز نباید «واگراییِ
                    # ۱۰۰٪» و مرگِ متابولیسم بسازد (درسِ 2026-07-23). فقط هشدارِ نرم.
                    problems.append(
                        f"observability-gap: billed AU${billed_aud:.2f} ولی تلمتری AU$0.00 "
                        f"— منبعِ زندهٔ مصرف به تلمتری wire نیست (soft، نه مرگ)")
                else:
                    div = abs(billed_aud - tel_aud) / billed_aud
                    if div > DIVERGENCE_DEATH:
                        problems.append(
                            f"billed↔telemetry divergence {div:.0%} > {DIVERGENCE_DEATH:.0%} "
                            f"(billed AU${billed_aud:.2f} vs telemetry AU${tel_aud:.2f})")
        except (OSError, ValueError) as e:
            problems.append(f"budget-state unreadable: {e}")
    if problems:
        # شکافِ رصد = نرم (فقط پرسش به انسان، بدونِ FREEZE/مرگ)؛ بقیه = سخت.
        soft = [p for p in problems if p.startswith("observability-gap")]
        hard = [p for p in problems if not p.startswith("observability-gap")]
        if hard:
            opslib.freeze("; ".join(hard))
            if any("divergence" in p for p in hard):
                # شرط مرگ متابولیسم (پک): توقف خودخواسته + سوال برای انسان
                opslib.STOP_METABOLIC.write_text(
                    opslib.now_iso() + "\n" + "\n".join(hard) + "\n", "utf-8")
            opslib.conflict_to_human(
                "METABOLIC",
                "تلمتری متابولیسم با حسابداری/سقف نمی‌خواند؛ grantها FREEZE شدند:\n"
                + "\n".join(f"- {p}" for p in hard)
                + "\nرفع: بررسی منابع تلمتری، سپس حذف دستی `_ops/budget/FREEZE.flag`"
                  " (و `_ops/STOP-METABOLIC` اگر ساخته شده).")
        if soft:
            opslib.conflict_to_human(
                "METABOLIC-OBS",
                "شکافِ رصدِ متابولیسم (بدونِ FREEZE): billed هست ولی منبعِ زندهٔ تلمتری صفر است:\n"
                + "\n".join(f"- {p}" for p in soft)
                + "\nرفع: منبعِ زندهٔ مصرف (organ-state.json / organ_gate) را به تلمتری wire کن.")
    return problems


if __name__ == "__main__":
    s = snapshot(write="--dry" not in sys.argv)
    probs = reconcile(s) if "--no-reconcile" not in sys.argv else []
    print(json.dumps({**s, "conflicts": probs}, ensure_ascii=False, indent=2))
