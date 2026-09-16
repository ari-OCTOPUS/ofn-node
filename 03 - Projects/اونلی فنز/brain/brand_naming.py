#!/usr/bin/env python3
"""brand_naming.py — انتخابِ نامِ برند با A/B test از طریقِ ThompsonBandit (۲۰۲۶-۰۷-۲۵).

درخواستِ مالک ۲۰۲۶-۰۷-۲۵: «اسمِ برند را به‌مرور خودِ OS تصمیم بگیرد بر اساسِ
تستِ مخاطب» — یعنی نام از داده می‌آید، نه از عقیدهٔ ایجنت.

این ماژول ThompsonBandit موجود (brain/learning.py) را برایِ نام‌های برند به‌کار می‌برد:
  • هر نامِ کاندید = یک arm.
  • وقتی محتوایی زیرِ یک نام منتشر می‌شود و بازخورد می‌آید (click-through / unlock /
    engagement)، به‌عنوانِ reward ثبت می‌شود.
  • select_candidate(): نامِ بعدی را بر اساسِ نمونه‌برداریِ Thompson پیشنهاد می‌دهد
    (propose-only — مالک تصمیم می‌گیرد).
  • نام‌های کم‌داده طبیعتاً بیشتر explore می‌شوند؛ نام‌های خوب converژ می‌شوند.

طراحی:
  • BrandNaming یک فایلِ candidates (json) + یک ThompsonBandit (همانِ learning) دارد.
  • record_feedback(name, metric_value): reward را ثبت می‌کند (approval-gated).
  • propose_next(): نامِ بعدی + شفافیت (explain) را برمی‌گرداند.
  • محتوای نامِ برند هرگز به cortex نمی‌رود (مرزِ #۷) — فقط متریک.

نکتهٔ صداقت: این سیستم **پیش از GATE 0 کار می‌کند اما بدونِ دادهٔ واقعی** — یعنی
فقط ساختار را می‌سازد. نامِ واقعی از اولین sprintِ واقعی (پس از GO) شکل می‌گیرد.
تا آن‌موقع، نام‌های seed از تصمیمِ ۲۰۲۶-۰۷-۱۲ (Anar Soles/Yalda Arch) به‌عنوانِ
candidates ثبت می‌شوند ولی هیچ هنوز امتیازی نگرفته‌اند.

$0 · propose-only · flag-gated (پیش‌فرض خاموش).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
for _p in (str(_HERE), str(_PROJ)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_BRAND_NAMING"
"""فعال‌سازیِ انتخابِ پویای نام. خاموش = نامِ اولیه (seed) ثابت می‌ماند."""

# نام‌های کاندیدِ seed (از تصمیمِ برندِ ۲۰۲۶-۰۷-۱۲: Anar Soles #1، Yalda Arch reserve).
# این فقط نقطهٔ شروعه؛ سیستم با داده می‌تونه این‌ها را تقویت یا ابطال کنه. صفر امتیازِ اولیه.
DEFAULT_CANDIDATES = ["Anar Soles", "Yalda Arch"]

# متریک‌های مجاز برای reward (هرچه بیشتر = بهتر؛ نرمالایز به ۰..۱).
# این‌ها از feedbackِ واقعیِ محتوا میان (G2/G3 metrics در ACQUISITION-ENGINE).
_METRICS = ("ctr", "unlock_rate", "follow_rate", "manual_rating")


class BrandNaming:
    """انتخابِ پویای نامِ برند بر اساسِ feedback مخاطب."""

    def __init__(self, data_dir: str | Path | None = None,
                 candidates: Optional[list[str]] = None):
        self._dir = Path(data_dir) if data_dir else (_PROJ / "brain")
        self._candidates_path = self._dir / "brand_candidates.json"
        self._bandit_path = self._dir / "brand_bandit.json"
        self._candidates = self._load_candidates(candidates)
        # ThompsonBandit موجود را به‌کار ببر (دوباره‌کاری نکن).
        try:
            from learning import ThompsonBandit
            self._bandit = ThompsonBandit(
                halflife_days=30.0,   # نیمه‌عمرِ کوتاه‌تر از محتوا — نامِ برند پویاتر است
                data_path=str(self._bandit_path))
        except Exception:  # noqa: BLE001 — fail-soft
            self._bandit = None

    # ── candidates ──
    def _load_candidates(self, override: Optional[list[str]]) -> list[str]:
        if override:
            return list(override)
        try:
            data = json.loads(self._candidates_path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return [str(x) for x in data]
        except (OSError, ValueError):
            pass
        return list(DEFAULT_CANDIDATES)

    def add_candidate(self, name: str) -> bool:
        """افزودنِ یک نامِ کاندیدِ جدید. propose-only — مالک تصمیم می‌گیرد."""
        name = str(name).strip()
        if not name or name in self._candidates:
            return False
        self._candidates.append(name)
        try:
            self._candidates_path.write_text(
                json.dumps(self._candidates, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except OSError:
            return False
        return True

    def candidates(self) -> list[str]:
        return list(self._candidates)

    # ── feedback (approval-gated) ──
    def record_feedback(self, name: str, metric: str, value: float,
                        approved: bool = True) -> bool:
        """ثبتِ بازخوردِ یک نام. value باید در ۰..۱ نرمالایز بشه.

        metric: یکی از _METRICS (ctr/unlock_rate/follow_rate/manual_rating).
        approved=False یعنی فقط ثبت (log) ولی واردِ یادگیری نمی‌شه."""
        if self._bandit is None:
            return False
        if metric not in _METRICS:
            return False
        reward = max(0.0, min(1.0, float(value)))
        if name not in self._candidates:
            self.add_candidate(name)
        try:
            self._bandit.observe(arm=name, reward=reward, approved=approved)
            return True
        except Exception:  # noqa: BLE001
            return False

    # ── پیشنهاد ──
    def propose_next(self) -> Optional[dict]:
        """نامِ پیشنهادیِ بعدی + شفافیت. flag-off = نامِ اولیه (seed).

        خروجی: {name, rank, explain} یا None."""
        if not _flag_on():
            # flag-off: نامِ اولیه را پیشنهاد بده (رفتارِ ثابت تا روشن‌سازی).
            return {"name": self._candidates[0] if self._candidates else None,
                    "rank": [], "explain": {},
                    "reason": "flag-off (seed نام ثابت)"}
        if self._bandit is None or not self._candidates:
            return None
        try:
            ranked = self._bandit.rank(self._candidates)
            top = ranked[0][0] if ranked else None
            explain = self._bandit.explain(self._candidates)
            return {"name": top, "rank": ranked, "explain": explain,
                    "reason": "thompson-sample (propose-only)"}
        except Exception:  # noqa: BLE001
            return None

    def status(self) -> dict:
        """snapshot برای /status. هرگز PII/محتوا — فقط نام‌های برند و امتیاز."""
        out = {"candidates": self.candidates(), "flag_on": _flag_on()}
        if self._bandit is not None and self._candidates:
            try:
                out["explain"] = self._bandit.explain(self._candidates)
            except Exception:  # noqa: BLE001
                out["explain"] = {}
        return out


def _flag_on() -> bool:
    return os.environ.get(FLAG, "0") == "1"
