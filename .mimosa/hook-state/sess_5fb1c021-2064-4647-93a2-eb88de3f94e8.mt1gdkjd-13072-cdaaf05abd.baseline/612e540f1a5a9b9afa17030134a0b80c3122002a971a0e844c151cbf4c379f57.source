#!/usr/bin/env python3
"""business_brain.py — «مغزِ دوم»: لوپِ عملیاتِ کسب‌وکار برای پروژه‌های درآمدزا (جلسه ۴۶).

رأی مالک: «دو پروژه اونلی‌فنز و نقاشیِ ساختمان وصل شد؛ مهندسی‌شونو درست کن به‌عنوان مغز دوم.»
مغزِ اول = خودنگه‌داری/خودارتقا (self_audit/improve/part_loops). مغزِ دوم = **عملیاتِ کسب‌وکار**:
هر پروژهٔ درآمدزا لوپِ observe→learn→propose خودش را دارد که به‌سمتِ لید و درآمدِ واقعی هل می‌دهد.

پروژه‌ها:
  • Lead-نقاشی — سیگنالِ واقعی از fitness/attribution (درآمدِ تأییدشده، لید، پوشش).
  • Project-F — **content-free** (طبقِ containment): فقط شمار/وضعیت، هرگز هویت/پلتفرم/محتوا.

propose-only مطلق: هیچ اقدامِ بیرونی/پولیِ خودکار؛ هر پیشنهاد به خانهٔ آره/نهِ مالک.
$0 · stdlib · read-only · fail-soft. خروجی: state/cortex/business-brain-latest.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
OUT = STATE / "cortex" / "business-brain-latest.json"


def _r(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def _prop(project, title, action, level="reconfig") -> dict:
    return {"part": project, "title": title, "action": action,
            "change_level": level, "auto_ok": False}   # کسب‌وکار هرگز auto نیست


# ── Lead-نقاشی: درآمد#۱، سیگنالِ واقعی ───────────────────────────────────────────
def _biz_lead():
    f = _r(STATE / "fitness-latest.json")
    att = f.get("attribution") or {}
    confirmed = att.get("confirmed") or 0
    revenue = att.get("revenue_by_cell") or {}
    n_cells = len([1 for v in revenue.values() if v])
    authoritative = f.get("authoritative")
    span = f.get("experience_span_days") or 0
    props = []
    status = "🟢" if confirmed else "🟡"
    if not confirmed and n_cells == 0:
        props.append(_prop("Lead-نقاشی", "هنوز درآمدِ تأییدشده‌ای ثبت نشده",
                           "یه لیدِ نقاشی ثبت کن (/lead) تا خطِ لوله راه بیفتد."))
    if authoritative is False and span < 28:
        props.append(_prop("Lead-نقاشی",
                           f"دادهٔ درآمد هنوز در حالِ ساخت است ({span}/۲۸ روز، سایه)",
                           "چند لیدِ واقعی بده تا اتریبیوشن معتبر شود.", "tune"))
    return {"id": "lead-naghshi", "name": "🎯 Lead-نقاشی", "status": status,
            "detail": f"تأیید {confirmed} · {n_cells} سلولِ درآمد",
            "authoritative": bool(authoritative)}, props


# ── Project-F: content-free (فقط وضعیت/شمار، نه محتوا/هویت) ───────────────────────
def _biz_projectf():
    paused = (STATE / "projectf-paused.flag").exists()
    # بودجهٔ ارگانِ PROJECT_F (عدد، content-free)
    t = _r(STATE / "telemetry-latest.json")
    organs = t.get("per_organ_alltime_musd") or {}
    spend = next((v for k, v in organs.items() if "project_f" in str(k).lower()), 0)
    status = "⏸" if paused else "🟢"
    props = []
    if paused:
        props.append(_prop("Project-F", "Project-F نگه‌داشته شده (درفت‌های نو روت نمی‌شوند)",
                           "اگر می‌خواهی ادامه بدهی، از کارتش «▶️ ادامه» بزن."))
    return {"id": "project-f", "name": "🎬 Project-F", "status": status,
            "detail": ("نگه‌داشته" if paused else "فعال · money-locked") +
                      f" · مهلت 2026-07-20", "content_free": True}, props


BUSINESSES = [_biz_lead, _biz_projectf]


def run_all(beat: int = 0) -> dict:
    """مغزِ دوم را بچرخان: وضعیت + پیشنهادهای کسب‌وکار. persist + رویداد. propose-only."""
    projects, proposals = [], []
    for fn in BUSINESSES:
        try:
            st, props = fn()
        except Exception as e:  # noqa: BLE001
            st, props = {"id": "?", "name": "?", "status": "⚪",
                         "detail": f"err:{type(e).__name__}"}, []
        projects.append(st)
        proposals.extend(props)
    digest = {"ts": opslib.now_iso(), "schema": "business-brain.v1", "beat": beat,
              "brain": "second (business ops)",
              "projects": projects, "n_proposals": len(proposals), "proposals": proposals}
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(OUT) as lj:
            lj.write(digest)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"business_brain persist failed: {e}"])
    try:
        sys.path.insert(0, str(_OPS))
        import events
        events.emit("task.completed", "business-brain",
                    summary=f"مغزِ دوم: {len(projects)} کسب‌وکار بررسی شد — {len(proposals)} پیشنهاد",
                    next_action="خانه: آره/نه" if proposals else "")
    except Exception:  # noqa: BLE001
        pass
    return digest


def summary() -> dict:
    d = _r(OUT)
    return {"brain": "second (business ops)",
            "projects": [{"name": p["name"], "status": p["status"], "detail": p.get("detail")}
                         for p in (d.get("projects") or [])],
            "n_proposals": d.get("n_proposals", 0)}


if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))
