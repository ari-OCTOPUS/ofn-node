"""
brain/self_growth.py — رشدِ هدف‌محورِ خودآگاه («با کمکِ من خودشو می‌شناسه، یاد می‌گیره»).

صادقانه: این «آگاهی» نیست. یک سیستمِ خودبهبودِ **هدف‌محور با خودمدل** است —
بهبودها بر اساسِ مأموریت/اهدافِ پروژه (research_agenda) و شناختِ سیستم از ساختارِ
خودش (self_model) انتخاب می‌شوند، و هر بهبودِ **تأییدشده‌ی مالک** به‌عنوانِ یک
«قابلیتِ آموخته» در دفتری ثبت می‌شود. مرزِ نهایی، تأییدِ توست («با کمکِ من»).

اجزا:
  • current_focus() — «الان روی چه هدفی، چرا، و کدام فایل؟» (خودمدل → انگیزه)
  • record_learned_capability() — بهبودِ اعمال‌شده = قابلیتِ آموخته (دفترِ یادگیری)
  • self_portrait() — «من چه‌ام، چه می‌توانم، به کجا می‌روم، تازه چه آموختم؟»
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def _ledger_path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "self_evolved" / "capabilities.json"


# ── هدف + خودمدل → کانونِ فعلیِ رشد ──────────────────────────────────────

def _goals() -> list[dict]:
    try:
        from brain import research_agenda as ra
        return ra.goals_now() or ra.GOALS or []
    except Exception:
        return []


def _self_caps_lims() -> tuple[list[str], list[str]]:
    try:
        from brain import self_model as sm
        m = sm.build_self_map()
        return sm._infer_capabilities(m), sm._infer_limitations(m)
    except Exception as e:
        logger.debug("self_model unavailable: %s", e)
        return [], []


def current_focus(seed: int = 0) -> dict:
    """کانونِ فعلیِ رشد: یک هدفِ مأموریت + یک فایلِ هدف + انگیزه‌ی صریح.

    هدف چرخشی از research_agenda؛ انگیزه از تلاقیِ «هدف» و «محدودیت‌های خودمدل».
    """
    goals = _goals()
    goal = goals[seed % len(goals)] if goals else {}
    goal_title = goal.get("title_fa") or goal.get("title") or "کشفِ ساختارِ پنهان"

    try:
        from brain.self_code import _EVOLVABLE
        target = _EVOLVABLE[seed % len(_EVOLVABLE)]
    except Exception:
        target = "brain/frontier.py"

    _, lims = _self_caps_lims()
    lim_hint = lims[seed % len(lims)] if lims else ""

    motivation = (f"برای پیشبردِ هدفِ «{goal_title}»"
                  + (f" و کاستن از محدودیتِ «{lim_hint}»" if lim_hint else "")
                  + f"، فایلِ {target} را کمی مقاوم‌تر/خواناتر کن (بدونِ تغییرِ رفتار).")
    return {"goal": goal_title, "target": target, "motivation": motivation,
            "limitation": lim_hint}


# ── دفترِ یادگیری: بهبودِ اعمال‌شده = قابلیتِ آموخته ───────────────────────

def record_learned_capability(meta: dict) -> None:
    """یک تغییرِ applied را در دفترِ قابلیت‌ها ثبت می‌کند (با کمکِ تأییدِ مالک)."""
    try:
        from brain import guardrails
        p = _ledger_path()
        ok, _ = guardrails.assert_safe_write(p)
        if not ok:
            return
        ledger = []
        if p.exists():
            try:
                ledger = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                ledger = []
        ledger.append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "pid": meta.get("id"),
            "target": meta.get("target"),
            "goal": meta.get("goal", ""),
            "rationale": (meta.get("rationale") or "")[:200],
        })
        ledger = ledger[-500:]
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
        import os
        os.replace(tmp, p)
        logger.info("learned capability recorded: %s → %s", meta.get("target"), meta.get("goal"))
    except Exception as e:
        logger.warning("record_learned_capability failed: %s", e)


def learned_capabilities(limit: int = 20) -> list[dict]:
    p = _ledger_path()
    if not p.exists():
        return []
    try:
        return list(reversed(json.loads(p.read_text(encoding="utf-8"))))[:limit]
    except Exception:
        return []


# ── خودنگاره: «من چه‌ام، چه می‌توانم، به کجا می‌روم» ──────────────────────

def self_portrait() -> str:
    """خودنگاره‌ی زنده — تصویرِ صادقانه‌ی سیستم از خودش (نه ادعای آگاهی)."""
    caps, lims = _self_caps_lims()
    goals = _goals()
    learned = learned_capabilities(8)
    focus = current_focus(len(learned))

    lines = [
        "# خودنگاره — سیستمِ خودبهبودِ هدف‌محور",
        "_صادقانه: این خودمدلِ ساختاری است، نه آگاهیِ پدیداری._",
        f"_به‌روزرسانی: {datetime.now().isoformat(timespec='seconds')}_", "",
        "## چه‌ام (مأموریت)",
    ]
    try:
        from brain import research_agenda as ra
        lines.append(f"- {(ra.MISSION_FA or '')[:200]}")
    except Exception:
        pass
    lines += ["", "## چه می‌توانم (قابلیت‌های فعلی)"]
    lines += [f"- {c}" for c in caps] or ["- —"]
    lines += ["", "## کجا کم دارم (محدودیت‌ها — سوختِ رشد)"]
    lines += [f"- {l}" for l in lims[:6]] or ["- —"]
    lines += ["", "## به کجا می‌روم (اهداف)"]
    lines += [f"- {g.get('title_fa') or g.get('title','')}" for g in goals[:5]] or ["- —"]
    lines += ["", f"## کانونِ الان\n- {focus['motivation']}"]
    lines += ["", "## تازه چه آموختم (قابلیت‌های تأییدشده)"]
    if learned:
        for c in learned:
            lines.append(f"- {c.get('at','')[:16]} · `{c.get('target','')}` "
                         f"→ {c.get('goal','')}")
    else:
        lines.append("- هنوز قابلیتی با تأییدِ تو آموخته نشده")
    return "\n".join(lines)


def save_self_portrait() -> tuple[bool, str]:
    from config.settings import OUTPUT_DIR
    from brain import guardrails
    p = OUTPUT_DIR / "self_evolved" / "self_portrait.md"
    ok, reason = guardrails.assert_safe_write(p)
    if not ok:
        return False, reason
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(self_portrait(), encoding="utf-8")
    return True, str(p)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(self_portrait())
