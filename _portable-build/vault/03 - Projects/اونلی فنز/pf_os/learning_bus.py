#!/usr/bin/env python3
"""learning_bus.py — سوختِ باهوش‌شدنِ Project-F OS.

این یک لایه‌ی نازکِ composition روی AcquisitionBrain + LearningBridge + ThompsonBandit
موجود است (نه rebuild). طبقِ توصیه‌ی architect-agent §5: «LearningBus که ThompsonBanditِ
موجود را reuse کند و از نتایجِ واقعی یاد بگیرد.»

حلقه‌ی اصلی (طبقِ توصیه §4):
  پیشنهاد (BrainCore) → سبا/مالک اجرا (propose-only) → ثبتِ نتیجه (record_result)
  → یادگیری (ThompsonBandit.observe) → پیشنهادِ بهتر (recommend)

این یعنی مغز از نتایجِ واقعی (upvotes, comments, unlocks, conversion) یاد می‌گیرد
و با Thompson sampling اکسپلور/اکسپلویت می‌کند. $0 آفلاین، stdlib-only.

رابط‌های کانونی:
  - record_result(tag, platform, upvotes, comments, unlocks, day, time_slot)
  - recommend(candidate_tags) → {best_tag, ranked, confidence}
  - status() → snapshot برای /api/learning

نامتغیر: هرگز PII/محتوا در یادگیری نمی‌رود — فقط tag/platform/metrics.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import config

# import brain موجود (اختیاری — fail-soft اگر نباشد)
_PROJ = config.PF_ROOT
_BRAIN = str(Path(_PROJ) / "brain")
if _BRAIN not in sys.path:
    sys.path.insert(0, _BRAIN)

_AcquisitionBrain = None
_AcquisitionMemory = None
_LearningBridge = None
_ThompsonBandit = None
try:
    from acquisition import AcquisitionBrain, AcquisitionMemory  # type: ignore
    from learning import LearningBridge, ThompsonBandit  # type: ignore
    _AcquisitionBrain = AcquisitionBrain
    _AcquisitionMemory = AcquisitionMemory
    _LearningBridge = LearningBridge
    _ThompsonBandit = ThompsonBandit
except Exception:  # noqa: BLE001 — brain موجود نبود → offline mode
    pass


@dataclass
class Recommendation:
    """خروجیِ recommend — برای BrainCore و /api/learning."""
    ok: bool
    best_tag: str = ""
    ranked: list = None  # list of (tag, score)
    confidence: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict:
        return {"ok": self.ok, "best_tag": self.best_tag,
                "ranked": self.ranked or [], "confidence": self.confidence,
                "reason": self.reason}


class LearningBus:
    """سوختِ باهوش‌شدن. compose می‌کند (نه rebuild):
      AcquisitionBrain.with_bandit() + LearningBridge

    دو سازنده:
      - LearningBus() — با state پیش‌فرض brain/ (acquisition_memory.json)
      - LearningBus(memory_path=..., halflife_days=21) — قابل تزریق برای تست
    """

    def __init__(self, memory_path: Optional[str] = None,
                 halflife_days: float = 21.0, seed: Optional[int] = None):
        if _AcquisitionBrain is None:
            self._available = False
            self._brain = None
            self._bridge = None
            self._memory = None
            return
        self._available = True
        # memory state path (طبقِ قرارداد brain موجود)
        mp = memory_path or str(Path(_BRAIN) / "acquisition_memory.json")
        try:
            self._memory = _AcquisitionMemory(data_path=mp)
        except Exception:  # noqa: BLE001
            self._memory = _AcquisitionMemory()
        # AcquisitionBrain با bandit (همان‌طور که acquisition.py طراحی شده)
        try:
            self._brain = _AcquisitionBrain.with_bandit(
                memory=self._memory, halflife_days=halflife_days, seed=seed)
        except Exception:  # noqa: BLE001
            self._brain = _AcquisitionBrain()
        try:
            self._bridge = _LearningBridge(self._memory,
                                           halflife_days=halflife_days, seed=seed)
        except Exception:  # noqa: BLE001
            self._bridge = None

    @property
    def available(self) -> bool:
        return self._available and self._brain is not None

    # ── رابطِ record_result (مهم‌ترین — حلقه‌ی یادگیری) ──
    def record_result(self, tag: str, platform: str,
                      upvotes: int = 0, comments: int = 0, unlocks: int = 0,
                      day: str = "", time_slot: str = "") -> bool:
        """ثبتِ نتیجه‌ی واقعیِ یک پست/درفت.

        این «سوختِ باهوش‌شدن» است: هر نتیجه → AcquisitionMemory.record_post_result
        + AcquisitionBrain.feedback_loop → ThompsonBandit.observe.

        args:
          tag: تگِ محتوا (مثلاً "cozy-socks"). PII هرگز.
          platform: "reddit" | "x" | "of"
          upvotes/comments/unlocks: metricsِ واقعی
          day: "mon"..."sun" (اختیاری)
          time_slot: "morning"|"afternoon"|"evening"|"night" (اختیاری)

        برمی‌گرداند True اگر ثبت شد.
        """
        if not self.available:
            return False
        if not tag or not platform:
            return False
        try:
            # feedback to bandit (عاملِ اصلیِ یادگیری) — خودش به memoryِ کانونی
            # هم ثبت می‌کند (feedback_loop → memory.record_post_result). پس ثبتِ
            # مستقیمِ memory اینجا حذف شد تا نتیجه double-record نشود (وگرنه
            # _post_results دوبرابر و learning_confidence مصنوعاً ۲برابر می‌شد).
            self._brain.feedback_loop(
                tag=tag, platform=platform, upvotes=upvotes,
                comments=comments, unlocks=unlocks, day=day, time_slot=time_slot)
            return True
        except Exception:  # noqa: BLE001
            return False

    # ── رابطِ recommend (پیشنهادِ مغز-محور) ──
    def recommend(self, candidate_tags: list[str]) -> Recommendation:
        """پیشنهادِ بهترین tag از میانِ candidateها، بر اساسِ یادگیری.

        اگر داده کافی نباشد، first candidate را با confidence پایین برمی‌گرداند.
        """
        if not self.available or not candidate_tags:
            return Recommendation(ok=False, reason="unavailable" if not self.available
                                  else "no-candidates")
        try:
            # LearningBridge.recommend — ساختارِ موجود
            out = self._bridge.recommend(candidate_tags)
            if isinstance(out, dict):
                # ساختارِ واقعی LearningBridge.recommend: top, ranked, explain
                # (نه best_tag/confidence که من قبلاً فرض می‌کردم)
                best = out.get("top") or out.get("best_tag") or candidate_tags[0]
                ranked = out.get("ranked") or []
                explain = out.get("explain", {}) if isinstance(out.get("explain"), dict) else {}
                arms = explain.get("arms", {}) if isinstance(explain.get("arms"), dict) else {}
                # confidence = 1 - uncertaintyِ best arm (heuristic)
                best_arm = arms.get(best, {})
                uncertainty = float(best_arm.get("uncertainty", 1.0))
                conf = max(0.0, 1.0 - uncertainty)
                # data-driven reason
                eff_pulls = sum(float(a.get("eff_pulls", 0)) for a in arms.values())
                reason = "low-data" if eff_pulls < 3 else "ok"
                return Recommendation(
                    ok=True, best_tag=best, ranked=ranked,
                    confidence=conf, reason=reason)
        except Exception:  # noqa: BLE001
            pass
        # fallback: first candidate
        return Recommendation(
            ok=True, best_tag=candidate_tags[0], ranked=[(candidate_tags[0], 0.0)],
            confidence=0.0, reason="fallback-first")

    # ── direct bandit access (advanced) ──
    def observe(self, arm: str, reward: float, approved: bool = True) -> bool:
        """دسترسیِ مستقیم به ThompsonBandit.observe برای rewardهای سفارشی.

        معمولاً record_result کافی است، ولی برای A/B testing یا reward تبدیل‌شده
        (مثلاً unlock_rate به‌جای raw upvotes) می‌توان مستقیم bandit را فید داد.
        """
        if not self.available or self._bridge is None:
            return False
        try:
            # LearningBridge wrapping می‌کند، ولی ThompsonBandit مستقیم هم هست
            bandit = getattr(self._bridge, "_bandit", None) or getattr(
                self._brain, "_bandit", None)
            if bandit is not None and hasattr(bandit, "observe"):
                bandit.observe(arm, reward, approved=approved)
                return True
        except Exception:  # noqa: BLE001
            pass
        return False

    # ── status snapshot ──
    def status(self) -> dict:
        """snapshot برای /api/learning و /api/health."""
        out = {"available": self.available}
        if not self.available:
            return out
        try:
            conf = self._memory.learning_confidence() if hasattr(
                self._memory, "learning_confidence") else 0.0
            out["learning_confidence"] = float(conf) if conf else 0.0
        except Exception:  # noqa: BLE001
            out["learning_confidence"] = 0.0
        try:
            # تعدادِ observations ثبت‌شده. AcquisitionMemory نتایج را در
            # _post_results نگه می‌دارد (نه _posts) — قبلاً همیشه 0 گزارش می‌شد.
            posts = getattr(self._memory, "_post_results", []) or []
            out["observations"] = len(posts) if isinstance(posts, list) else 0
        except Exception:  # noqa: BLE001
            out["observations"] = 0
        return out
