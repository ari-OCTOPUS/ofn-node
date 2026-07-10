#!/usr/bin/env python3
"""goal_directed.py — ضدِ خودبهبودیِ دایره‌ای؛ هدف‌محور و عملی و سنجش‌پذیر (جلسه ۴۶).

رأی مالک: «خودبهبودی دایره‌ای الکی نباشه — عملی و هدف‌دار و قوی و اتوماتیک باشه.»
مسئله: `generate_proposals` انبوهی پیشنهادِ درون‌مانده می‌سازد («بلوغ را بالا ببر»،
«یک probe اضافه کن»، «یک ماژول را مستند کن») که به هدفِ واقعیِ مالک خدمت نمی‌کنند.

این لایه بین generate و top می‌نشیند و سه کار می‌کند:
  ۱) هر پیشنهاد را به هدفِ مالک (GOALS-OCTOPUS.md) لینک می‌کند؛ پیشنهادِ دایره‌ای
     (خودمتریک، بی‌لینکِ هدف) را دور می‌ریزد یا به سهمیهٔ کوچک می‌راند.
  ۲) اثرِ واقعی را تخمین می‌زند (کسب‌وکار/درآمد/لید > تعمیرِ سلامت > کارِ سندی).
  ۳) نیتِ سنجش را ثبت می‌کند (`state/cortex/outcomes.jsonl`) — تا لوپ بسته و
     غیرِدایره‌ای شود: بعداً معلوم می‌شود آیا تغییر واقعاً چیزی را جابه‌جا کرد.

$0 · stdlib · fail-soft · propose-only (فقط بازچینش/حاشیه‌نویسی، نه اعمال).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
GOALS_PATH = opslib.OPS / "GOALS-OCTOPUS.md"
OUTCOMES = STATE / "cortex" / "outcomes.jsonl"

# نشانه‌های «دایره‌ای» — بهبودِ خودِ ماشینِ سنجش، نه یک هدفِ واقعی.
_CIRCULAR = re.compile(
    r"(بلوغ|maturity|probe|ماتریس|audit|ممیزی|هم‌آهنگی|coherence|خودآگاهیِ سند|"
    r"docstring|مستند کن|self-model|توضیح)", re.I)
# نشانه‌های هدفِ واقعی/برون‌داد (هرگز دایره‌ای نیستند).
_OUTCOME = re.compile(
    r"(درآمد|revenue|لید|lead|فروش|sale|مشتری|customer|نقاشی|Ziman|زیمن|"
    r"reconcile|واریز|پول‌ساز|یادگیری|کشف|research)", re.I)


def load_goals() -> list[str]:
    try:
        text = GOALS_PATH.read_text("utf-8") if GOALS_PATH.exists() else ""
    except OSError:
        return []
    return [ln[2:].strip() for ln in text.splitlines() if ln.startswith("- ") and ln[2:].strip()]


def _kw(s: str) -> set:
    return {w for w in re.split(r"\W+", str(s).lower()) if len(w) > 3}


def goal_link(p: dict, goals: list[str]) -> str | None:
    """کدام هدفِ مالک را این پیشنهاد پیش می‌برد؟ (یا None)."""
    blob = f"{p.get('title', '')} {p.get('suggested_action', '')} {p.get('rationale', '')}"
    words = _kw(blob)
    if _OUTCOME.search(blob):                       # برون‌دادِ صریح = هدف‌محور
        best = None
        for g in goals:
            if words & _kw(g):
                return g
        return "برون‌دادِ واقعی (درآمد/لید/یادگیری)"
    for g in goals:
        if len(words & _kw(g)) >= 2:
            return g
    return None


def is_circular(p: dict) -> bool:
    """درخودمانده؟ فقط اگر متریکِ داخلی را دستکاری کند، هدفی پیش نبرد، و P0 نباشد
    (P0/امنیت واقعی است، نه دایره‌ای)."""
    if p.get("priority") == "P0":
        return False
    if p.get("source") in ("business-brain", "doctor", "synthesis"):
        return False           # کسب‌وکار/سلامت/ایدهٔ مغز = واقعی
    blob = f"{p.get('title', '')} {p.get('suggested_action', '')}"
    return bool(_CIRCULAR.search(blob)) and not _OUTCOME.search(blob)


def impact(p: dict, goals: list[str]) -> float:
    """اثرِ واقعیِ تخمینی (بالاتر = مهم‌تر). کسب‌وکار/هدف > سلامت > سندی."""
    if p.get("source") == "business-brain" or p.get("category") == "business":
        return 3.0
    if p.get("priority") == "P0":
        return 2.6            # امنیت/گافِ واقعی
    if goal_link(p, goals):
        return 2.2
    if p.get("source") in ("doctor", "synthesis"):
        return 1.6
    if is_circular(p):
        return 0.4
    return 1.0


def rerank(proposals: list[dict], *, max_circular: int = 2) -> dict:
    """پیشنهادها را هدف‌محور بازچینی کن: دایره‌ای‌ها به ته (سهمیهٔ کوچک)، هدف‌محورها بالا.
    هر پیشنهاد با `serves_goal` و `impact` حاشیه‌نویسی می‌شود. خروجی: {ranked, dropped_circular}."""
    goals = load_goals()
    scored, circular = [], []
    for p in proposals:
        p = dict(p)
        gl = goal_link(p, goals)
        p["serves_goal"] = gl or ("—" if not is_circular(p) else "دایره‌ای (بی‌هدف)")
        p["impact"] = impact(p, goals)
        (circular if is_circular(p) else scored).append(p)
    scored.sort(key=lambda x: -x["impact"])
    circular.sort(key=lambda x: -x["impact"])
    kept_circular = circular[:max_circular]     # فقط چند تعمیرِ داخلیِ ضروری
    ranked = scored + kept_circular
    return {"ranked": ranked, "n_goal_serving": sum(1 for p in scored if p["impact"] >= 2.0),
            "n_circular_dropped": max(0, len(circular) - len(kept_circular)),
            "goals_count": len(goals)}


def record_intent(top: list[dict]) -> None:
    """نیتِ سنجش را ثبت کن (لوپ را ببند، غیرِدایره‌ای کن): هر پیشنهادِ صدر چه هدفی و چه
    متریکی را قرار است جابه‌جا کند + baseline. بعداً measure می‌گوید آیا شد."""
    try:
        base = _baseline_metrics()
        OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTCOMES, "a", encoding="utf-8") as f:
            for p in top[:3]:
                f.write(json.dumps({
                    "ts": opslib.now_iso(), "id": p.get("id"),
                    "title": p.get("title"), "serves_goal": p.get("serves_goal"),
                    "impact": p.get("impact"), "baseline": base}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _baseline_metrics() -> dict:
    """متریک‌های برون‌دادیِ واقعی (نه خودمتریک): درآمد، کشف، σ."""
    def _r(p):
        try:
            return json.loads(p.read_text("utf-8")) if p.exists() else {}
        except (OSError, ValueError):
            return {}
    fit = _r(STATE / "fitness-latest.json").get("attribution", {})
    disc = _r(STATE / "discoveries.jsonl") if False else {}
    n_disc = 0
    try:
        dp = STATE / "discoveries.jsonl"
        n_disc = len(dp.read_text("utf-8").splitlines()) if dp.exists() else 0
    except OSError:
        n_disc = 0
    return {"confirmed_revenue": fit.get("confirmed", 0),
            "revenue_cells": len(fit.get("revenue_by_cell", {}) or {}),
            "total_discoveries": n_disc}


def measure() -> dict:
    """آیا پیشنهادهای اخیر واقعاً متریکی را جابه‌جا کردند؟ (بستنِ لوپ — ضدِ دایره).
    اگر برون‌دادها ثابت مانده‌اند → سیگنالِ «کارِ خودبهبودی به هدف نمی‌رسد»."""
    now = _baseline_metrics()
    try:
        if not OUTCOMES.exists():
            return {"tracked": 0, "moved": False, "now": now}
        rows = [json.loads(l) for l in OUTCOMES.read_text("utf-8").splitlines()[-20:] if l.strip()]
    except (OSError, ValueError):
        return {"tracked": 0, "moved": False, "now": now}
    if not rows:
        return {"tracked": 0, "moved": False, "now": now}
    oldest = rows[0].get("baseline", {})
    moved = any(now.get(k, 0) > oldest.get(k, 0) for k in
                ("confirmed_revenue", "revenue_cells", "total_discoveries"))
    return {"tracked": len(rows), "moved": moved, "now": now, "since": oldest}


if __name__ == "__main__":
    print(json.dumps({"goals": load_goals(), "measure": measure()},
                     ensure_ascii=False, indent=2))
