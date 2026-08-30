#!/usr/bin/env python3
"""cycle_evaluator — ارزیابِ مستقلِ چرخه: پیش‌ثبت را می‌خواند، دیسک را می‌سنجد، حکم می‌دهد.

استقلال یعنی چه (منشور §۴.۳ — «منتقدِ متخاصمِ مستقل»):
  • ورودی‌اش **فقط دیسک** است: ردیفِ پیش‌ثبت (target ِ منجمد) + مقدارِ فعلیِ
    سنجه از همان فایلی که پیش‌ثبت گفته. ادعای اجراکننده (journal ِ test_cycle)
    در حکم هیچ رأیی ندارد.
  • هیچ‌چیز جز دفترِ حکمِ خودش نمی‌نویسد؛ پیش‌ثبت را **هرگز** تغییر نمی‌دهد
    (تست ناوردی‌اش را بایت‌به‌بایت می‌سنجد).
  • target را بعد از دیدنِ نتیجه جابه‌جا نمی‌کند — اصلاً APIای برای آن ندارد.

حکم‌ها:
  PASS    سنجه به target رسید (op روی مقدارِ فعلی برقرار).
  PARTIAL حرکتِ مثبت به‌سوی target ولی نرسیده (فقط وقتی target از baseline دور است).
  FAIL    حرکتی نبود یا در جهتِ غلط.
  BLOCKED سنجه ناخوانا شد (ترازو از دست رفت — این خودش یافته است، نه سکوت).

absence of evidence ≠ success: سنجهٔ ناخوانا هرگز PASS نمی‌شود.

$0 · stdlib · فقط‌خواندنی جز دفترِ حکم · بدونِ فلگ (کتابخانه؛ صداکننده flag-gated).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "cycle_verdict.v1"
VERDICTS = opslib.STATE_DIR / "test_cycle" / "verdicts.jsonl"


def rows() -> list:
    out: list = []
    try:
        if not VERDICTS.exists():
            return out
        with open(VERDICTS, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("schema") == SCHEMA:
                    out.append(d)
    except OSError:
        pass
    return out


def last_verdict(goal_key: str) -> "dict | None":
    out = None
    for r in rows():
        if r.get("goal_key") == goal_key:
            out = r
    return out


def _cycles_elapsed(from_cycle: str, to_cycle: str, slots_per_day: int) -> "int | None":
    """چند اسلات بینِ دو cycle_id («YYYY-MM-DD#slot») گذشته؟ ناخوانا → None."""
    import datetime as _dt
    try:
        d1, s1 = str(from_cycle).split("#"), None
        d2, s2 = str(to_cycle).split("#"), None
        day1 = _dt.date.fromisoformat(d1[0])
        day2 = _dt.date.fromisoformat(d2[0])
        s1, s2 = int(d1[1]), int(d2[1])
    except (ValueError, IndexError):
        return None
    n = max(1, int(slots_per_day))
    return ((day2 - day1).days * n) + (s2 - s1)


def judge(prereg_row: dict, value_now: "float | None") -> dict:
    """تابعِ خالصِ حکم — بدونِ I/O، تا جهش‌پذیر و mutation-testable باشد."""
    t = prereg_row.get("target") or {}
    op, tval = t.get("op"), t.get("value")
    base = prereg_row.get("baseline")
    if value_now is None:
        return {"verdict": "BLOCKED", "reason": "metric-unreadable"}
    if not (op in (">", ">=") and isinstance(tval, (int, float))
            and isinstance(base, (int, float))):
        return {"verdict": "BLOCKED", "reason": "bad-prereg-target"}
    hit = (value_now > tval) if op == ">" else (value_now >= tval)
    if hit:
        return {"verdict": "PASS", "reason": "target-met"}
    if value_now > base:
        return {"verdict": "PARTIAL", "reason": "moved-not-met"}
    return {"verdict": "FAIL", "reason": ("no-movement" if value_now == base
                                          else "wrong-direction")}


def evaluate_pending(*, now: "float | None" = None) -> dict:
    """هر پیش‌ثبتِ بی‌حکم که deadline اش گذشته را ارزیابی کن و حکم را append کن.

    idempotent: پیش‌ثبتِ حکم‌خورده دوباره ارزیابی نمی‌شود (کلید = prereg_id)."""
    import prereg as _pr
    import test_cycle as _tc          # فقط برای ریاضیِ خالصِ کادنس (cycle_id/slots)
    current = _tc.cycle_id(now)
    slots = _tc._slots()
    judged = {str(r.get("prereg_id")) for r in rows()}
    out = []
    for r in _pr.rows():
        pid = str(r.get("prereg_id"))
        if pid in judged:
            continue
        elapsed = _cycles_elapsed(str(r.get("cycle_id")), current, slots)
        try:
            deadline = int(r.get("deadline_cycles", 2) or 2)
        except (TypeError, ValueError):
            deadline = 2
        if elapsed is None or elapsed < deadline:
            continue
        try:
            import goal_generator as _gg
            value_now = _gg.read_metric(str(r.get("metric_path")),
                                        str(r.get("metric_key")))
        except Exception:  # noqa: BLE001 — خواندنِ شکسته = BLOCKED، نه کرش
            value_now = None
        verdict = judge(r, value_now)
        rec = {
            "schema": SCHEMA, "ts": opslib.now_iso(),
            "prereg_id": pid, "cycle_id": r.get("cycle_id"),
            "evaluated_at_cycle": current,
            "goal_key": r.get("goal_key"),
            "method_index": r.get("method_index", 0),
            "baseline": r.get("baseline"), "value_now": value_now,
            "target": r.get("target"),
            "verdict": verdict["verdict"], "reason": verdict["reason"],
            "evidence": {"metric_path": r.get("metric_path"),
                         "metric_key": r.get("metric_key")},
        }
        try:
            opslib.append_jsonl(VERDICTS, rec)
        except (OSError, ValueError):
            # حکم ننوشته = حکم نداده — دفعهٔ بعد دوباره تلاش می‌شود (fail-closed)
            continue
        judged.add(pid)
        out.append(rec)
    return {"ok": True, "evaluated": len(out), "verdicts": out}


def scoreboard() -> dict:
    """شمارشِ خامِ حکم‌ها — عدد، نه صفت (آستانه در پیش‌ثبتِ SGC است، نه این‌جا)."""
    vs = rows()
    counts: dict = {}
    for r in vs:
        counts[r.get("verdict")] = counts.get(r.get("verdict"), 0) + 1
    return {"total": len(vs), **counts}


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"scoreboard": scoreboard(), "ledger": str(VERDICTS)},
                     ensure_ascii=False, indent=1))
