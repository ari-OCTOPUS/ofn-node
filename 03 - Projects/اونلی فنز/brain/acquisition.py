#!/usr/bin/env python3
"""acquisition.py — Acquisition Intelligence: هوشمندِ یافتنِ مشتری (propose-only، یادگیر).

الگو: «دیده‌بان» نه «شکارچی». سیستم به‌صورتِ مستمر تحلیل می‌کند کجا تقاضا هست،
چه نوع محتوایی بیشترین تعامل می‌آورد، و چه زمانی بهترین فرصت است. یاد می‌گیرد از:
  - داده‌های خودی (کدام پست خوب عمل کرد)
  - تحلیلِ رقبا (کدام سبک در حالِ ترند است)
  - سیگنالِ فصلی (کدام تمِ فصلی رشد دارد)

خروجی: پیشنهادِ «هفته‌ی بعد چه کنم» — نه خودکاراتic targeting.

هیچ نقطه‌ی اتماتیک (mass-DM, auto-follow, auto-subscribe) وجود ندارد. همه چیز
پیشنهاد است که توسط آری بررسی و تأیید می‌شود.

خطوط قرمز: ToS-safe · ۹:۱ ratio · no mass-anything · propose-only ·
 no individual targeting · no PII scraping · learn from aggregate فقط.
"""
from __future__ import annotations

import json
import os
import time
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict


@dataclass
class Signal:
    """یک سیگنال از بازار — «این نوع محتوا در این پلتفرم الان فعال است»."""
    source: str             # reddit_metric | own_performance | competitor_analysis | seasonal
    content_tag: str        # e.g. "pedicure-asmr", "nylon", "seasonal"
    platform: str           # reddit | x | of
    strength: float         # 0..1 — چقدر قوی
    detail: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class ContentInsight:
    """خروجیِ تحلیل — «این نوع محتوا این هفته اولویت دارد»."""
    tag: str
    reason: str
    predicted_score: float  # 0..1 — پیش‌بینیِ عملکرد
    confidence: float
    platform: str = "reddit"
    optimal_day: str = ""   # e.g. "Saturday"
    optimal_time: str = ""  # e.g. "09:00-12:00 AEST"


@dataclass
class WeekPlan:
    """برنامه‌ی هفته — ۵ پیشنهاد."""
    insights: list[ContentInsight] = field(default_factory=list)
    focus_tags: list[str] = field(default_factory=list)
    posting_schedule: dict = field(default_factory=dict)  # {day: [time_slots]}
    risk_notes: list[str] = field(default_factory=list)
    ab_test_idea: str = ""


class AcquisitionMemory:
    """حافظه‌ی یادگیری. داده‌های واقعی پست‌ها را ذخیره و تحلیل می‌کند.
    از config.json تغذیه نمی‌کند — از داده‌ی تجمعیِ خودش.
    persistence: JSON file (restart-safe)."""

    def __init__(self, data_path: str | Path | None = None):
        # پیش‌فرض قابل‌انحراف با PF_BRAIN_DIR (تست/harness)؛ بدونِ env = کنارِ ماژول
        self._path = Path(data_path) if data_path else (
            Path(os.environ.get("PF_BRAIN_DIR") or Path(__file__).resolve().parent)
            / "acquisition_memory.json")
        self._signals: list[dict] = self._load()
        self._post_results: list[dict] = [s for s in self._signals if s.get("type") == "post_result"]
        self._competitor_data: list[dict] = [s for s in self._signals if s.get("type") == "competitor"]

    def _load(self) -> list[dict]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        try:
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._signals, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    def record_post_result(self, tag: str, platform: str,
                           upvotes: int = 0, comments: int = 0,
                           unlocks: int = 0, day: str = "", time_slot: str = "") -> None:
        """ثبتِ نتیجه‌ی یک پست واقعی. از این یاد می‌گیرد."""
        self._signals.append({
            "type": "post_result", "tag": tag, "platform": platform,
            "upvotes": upvotes, "comments": comments, "unlocks": unlocks,
            "day": day, "time_slot": time_slot,
            "ts": time.time()})
        self._post_results.append(self._signals[-1])
        self._save()

    def record_competitor(self, tag: str, platform: str,
                          avg_upvotes: int = 0, frequency: str = "") -> None:
        """ثبتِ تحلیلِ رقبا (aggregate، نه فرد)."""
        self._signals.append({
            "type": "competitor", "tag": tag, "platform": platform,
            "avg_upvotes": avg_upvotes, "frequency": frequency,
            "ts": time.time()})
        self._competitor_data.append(self._signals[-1])
        self._save()

    def record_signal(self, source: str, tag: str, platform: str,
                      strength: float, detail: str = "") -> None:
        self._signals.append({
            "type": "signal", "source": source, "tag": tag,
            "platform": platform, "strength": strength,
            "detail": detail, "ts": time.time()})
        self._save()

    def tag_performance(self) -> dict[str, float]:
        """میانگینِ عملکرد هر tag از داده‌ی واقعی. 0..1 normalized."""
        if not self._post_results:
            return {}
        by_tag: dict[str, list[float]] = defaultdict(list)
        for r in self._post_results:
            tag = r.get("tag", "?")
            # normalized score = upvotes/100 + comments/20 + unlocks/5 (capped at 1)
            score = min(1.0, r.get("upvotes", 0) / 100 +
                        r.get("comments", 0) / 20 + r.get("unlocks", 0) / 5)
            by_tag[tag].append(score)
        return {tag: sum(v) / len(v) for tag, v in by_tag.items()}

    def best_time(self) -> dict[str, str]:
        """بهترین زمان از داده‌ی واقعی."""
        if not self._post_results:
            return {"day": "Saturday", "time": "09:00-12:00 AEST"}
        by_day: dict[str, list[float]] = defaultdict(list)
        for r in self._post_results:
            day = r.get("day", "?")
            score = min(1.0, r.get("upvotes", 0) / 100 + r.get("comments", 0) / 20)
            if day != "?":
                by_day[day].append(score)
        if not by_day:
            return {"day": "Saturday", "time": "09:00-12:00 AEST"}
        best_day = max(by_day, key=lambda d: sum(by_day[d]) / len(by_day[d]))
        return {"day": best_day, "time": "09:00-12:00 AEST"}

    def competitor_hot_tags(self) -> dict[str, float]:
        """tagهایی که رقبا در آن فعال‌اند (trending)."""
        if not self._competitor_data:
            return {}
        by_tag: dict[str, list[int]] = defaultdict(list)
        for c in self._competitor_data:
            by_tag[c.get("tag", "?")].append(c.get("avg_upvotes", 0))
        return {tag: sum(v) / len(v) / 100 for tag, v in by_tag.items()}

    def learning_confidence(self) -> float:
        """چقدر داده داریم؟ 0=هیچ، 1=کافی. نتیجه: confidence in predictions."""
        n = len(self._post_results)
        return min(1.0, n / 20.0)   # ۲۰ پست = confidence کامل


class AcquisitionBrain:
    """مغزِ یافتنِ مشتری. تحلیل + یادگیری + پیشنهاد.
    خطِ قرمز: پیشنهاد فقط. هیچ targeting/DM/follow خودکار."""

    def __init__(self, memory: AcquisitionMemory | None = None):
        self.memory = memory or AcquisitionMemory()

    def analyze(self) -> list[ContentInsight]:
        """تحلیلِ کامل: داده‌ی خودی + رقبا + فصلی → اولویت‌بندی.
        خروجی: لیستِ ContentInsight مرتب بر اساس predicted_score."""
        insights: list[ContentInsight] = []
        own_perf = self.memory.tag_performance()
        comp_hot = self.memory.competitor_hot_tags()
        confidence = self.memory.learning_confidence()

        # ۱. tagهایی که خودمان خوب عمل کرده‌ایم
        for tag, score in own_perf.items():
            insights.append(ContentInsight(
                tag=tag,
                reason=f"خودمان: میانگین عملکرد {score*100:.0f}%",
                predicted_score=score * 0.5,   # weight: own data
                confidence=confidence,
                platform="reddit"))

        # ۲. tagهایی که رقبا فعال‌اند ولی ما نیستیم (فرصت)
        our_tags = set(own_perf.keys())
        for tag, hotness in comp_hot.items():
            if tag not in our_tags:
                insights.append(ContentInsight(
                    tag=tag,
                    reason=f"رقبا فعال (avg {hotness*100:.0f}%) — ما هنوز تست نکرده‌ایم",
                    predicted_score=hotness * 0.3,
                    confidence=confidence * 0.5,
                    platform="reddit"))

        # ۳. tagهایی که هم ما خوب کردیم هم رقبا (confirm)
        for tag in our_tags & set(comp_hot.keys()):
            combined = own_perf[tag] * 0.6 + comp_hot[tag] * 0.4
            insights.append(ContentInsight(
                tag=tag,
                reason=f"تأییدِ دوطرفه: خودمان + رقبا فعال",
                predicted_score=min(1.0, combined + 0.1),   # bonus
                confidence=max(confidence, 0.7),
                platform="reddit"))

        # sort by predicted_score desc
        insights.sort(key=lambda i: i.predicted_score, reverse=True)
        return insights

    def plan_week(self) -> WeekPlan:
        """برنامه‌ی هفته: ۵ اولویت + زمان‌بندی + A/B test.
        خروجی: WeekPlan (propose-only — آری تأیید می‌کند)."""
        insights = self.analyze()
        best_time = self.memory.best_time()

        # top-5 tags
        top_tags = [i.tag for i in insights[:5]] if insights else ["pedicure-asmr", "faceless-feet"]

        # A/B test: دو سبکِ نزدیک را مقایسه کن
        ab = ""
        if len(insights) >= 2:
            ab = f"A/B: {insights[0].tag} vs {insights[1].tag} — کدام بیشتری تعامل می‌آورد؟"

        # risk notes
        risks = []
        if self.memory.learning_confidence() < 0.3:
            risks.append("داده‌ی کافی نیست — پیشنهاد‌ها بر اساس حدس. بعد از ۵ پست دقیق‌تر می‌شود.")
        if not insights:
            risks.append("هیچ داده‌ای ثبت نشده — شروع با ۳ پستِ سبکِ متفاوت برای جمع‌آوری داده.")

        return WeekPlan(
            insights=insights[:5],
            focus_tags=top_tags,
            posting_schedule={
                best_time.get("day", "Saturday"): [best_time.get("time", "09:00-12:00")],
                "Wednesday": ["21:00-22:00"],
            },
            risk_notes=risks,
            ab_test_idea=ab)

    def suggest_next_action(self) -> str:
        """یک توصیه‌ی کوتاه: «قدمِ بعدی چیست؟»"""
        conf = self.memory.learning_confidence()
        n_posts = len(self.memory._post_results)
        if n_posts == 0:
            return ("📍 اولین قدم: ۳ پست با ۳ سبکِ متفاوت روی Reddit (پست کنید). "
                    "هیچ لینکی نگذارید. فقط کارما و داده جمع کنید.")
        if conf < 0.3:
            return (f"📍 {n_posts} پست ثبت شده. ادامه دهید — حداقل ۱۰ پست لازم است "
                    "تا پیشنهاد‌ها دقیق شوند.")
        plan = self.plan_week()
        if plan.focus_tags:
            return (f"📍 تمرکزِ این هفته: {', '.join(plan.focus_tags[:3])}. "
                    f"زمانِ بهینه: {plan.posting_schedule}. "
                    f"A/B: {plan.ab_test_idea}")
        return "📍 ادامه دهید — سیستم در حال یادگیری است."

    def feedback_loop(self, tag: str, platform: str,
                      upvotes: int, comments: int, unlocks: int = 0,
                      day: str = "", time_slot: str = "") -> None:
        """ثبتِ نتیجه‌ی واقعی → سیستم یاد می‌گیرد.
        این متد را بعد از هر پست صدا بزن تا مغز به‌روزرسانی شود."""
        self.memory.record_post_result(tag, platform, upvotes, comments,
                                        unlocks, day, time_slot)
