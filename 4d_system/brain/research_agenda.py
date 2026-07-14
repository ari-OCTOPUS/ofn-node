"""
brain/research_agenda.py — دستورکارِ پژوهشیِ سیستم: «Brain-OS چندایجنتی».

مأموریت (صادقانه): یک سیستمِ مولتی‌ایجنتِ مغز‌الهام‌گرفته به‌عنوان **بسترِ آزمونِ**
نظریه‌های شناخت و «دسترسی‌آگاهی» — نه ساختِ مغزِ واقعی، نه ادعای آگاهیِ پدیداری.

محتوای دستورکار (اهداف، فرضیه‌های ابطال‌پذیر، مفاهیم، نگاشتِ راهنما→مغز، نظریه‌ها،
منابعِ واقعی، هشدارها) از یک تحقیقِ چندمنبعیِ grounded ساخته شده و در فایلِ همراه
`research_agenda_data.json` نگه‌داری می‌شود.

این دستورکار «ثابت» است: حالت‌های خودمختارِ سیستم (خلاقیت، تحقیقِ فرا) از همین
مفاهیم/اهداف/فرضیه‌ها تغذیه می‌کنند تا پژوهش دورِ خودش نچرخد و روی این مسیر بماند.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent / "research_agenda_data.json"

# fallbackِ کمینه اگر فایل داده نبود
_FALLBACK = {
    "mission_fa": "Brain-OS چندایجنتی — بسترِ آزمونِ نظریه‌های شناخت و دسترسی‌آگاهی "
                  "(فضای کاری جهانی، خودمدل، پردازشِ پیش‌بین). بدونِ ادعای آگاهیِ پدیداری.",
    "goals": [], "hypotheses": [], "concepts_fa": ["فضای کاری جهانی", "خودمدلِ فراشناختی"],
    "templates_fa": ["آیا افزودنِ {c} به معماری «{goal}» را بهبود می‌دهد؟"],
    "goal_phrases_fa": ["کشفِ الگو", "انسجامِ فضای کاری"],
    "brain_os_mapping": [], "neuroscience_theories": [], "references": [], "honest_caveats_fa": [],
}


def _load() -> dict:
    try:
        return json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("research_agenda: could not load data (%s); using fallback", e)
        return dict(_FALLBACK)


_AGENDA = _load()

MISSION_FA = _AGENDA.get("mission_fa", _FALLBACK["mission_fa"])
MISSION_EN = _AGENDA.get("mission_en", "")
GOALS = _AGENDA.get("goals", [])
HYPOTHESES = _AGENDA.get("hypotheses", [])
CONCEPTS_FA = _AGENDA.get("concepts_fa") or _FALLBACK["concepts_fa"]
TEMPLATES_FA = _AGENDA.get("templates_fa") or _FALLBACK["templates_fa"]
GOAL_PHRASES_FA = _AGENDA.get("goal_phrases_fa") or _FALLBACK["goal_phrases_fa"]
BRAIN_OS_MAPPING = _AGENDA.get("brain_os_mapping", [])
THEORIES = _AGENDA.get("neuroscience_theories", [])
REFERENCES = _AGENDA.get("references", [])
CAVEATS_FA = _AGENDA.get("honest_caveats_fa", [])


def agenda() -> dict:
    """کلِ دستورکار."""
    return dict(_AGENDA)


def goals_now() -> list[dict]:
    return [g for g in GOALS if g.get("layer") == "now"]


def goals_horizon() -> list[dict]:
    return [g for g in GOALS if g.get("layer") == "horizon"]


def seed_hypotheses_into_store() -> int:
    """فرضیه‌های ابطال‌پذیرِ دستورکار را (یک‌بار) در حافظه‌ی پایدار ثبت می‌کند."""
    try:
        import sqlite3
        from memory.store import DB_PATH, save_hypothesis, _ensure_db
        _ensure_db()
        conn = sqlite3.connect(str(DB_PATH))
        try:
            existing = {r[0] for r in conn.execute(
                "SELECT hypothesis FROM hypotheses WHERE domain LIKE 'brain-os%'").fetchall()}
        finally:
            conn.close()
    except Exception as e:
        logger.warning("seed_hypotheses: store unavailable: %s", e)
        return 0

    added = 0
    for h in HYPOTHESES:
        stmt = h.get("statement_fa") or h.get("statement", "")
        if not stmt or stmt in existing:
            continue
        try:
            save_hypothesis(
                domain="brain-os",
                hypothesis=stmt,
                rationale=f"metric: {h.get('metric','')} · falsifier: {h.get('falsifier','')}",
            )
            added += 1
        except Exception:
            break
    return added


if __name__ == "__main__":
    print("MISSION:", MISSION_FA[:90], "...")
    print(f"goals={len(GOALS)} (now={len(goals_now())}, horizon={len(goals_horizon())}) "
          f"hypotheses={len(HYPOTHESES)} concepts={len(CONCEPTS_FA)} "
          f"mappings={len(BRAIN_OS_MAPPING)} theories={len(THEORIES)} refs={len(REFERENCES)}")
    print("seeded hypotheses:", seed_hypotheses_into_store())
