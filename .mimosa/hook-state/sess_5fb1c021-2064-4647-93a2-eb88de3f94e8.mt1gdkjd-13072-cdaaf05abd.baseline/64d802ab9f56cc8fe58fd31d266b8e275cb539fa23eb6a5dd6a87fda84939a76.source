#!/usr/bin/env python3
"""eval_loop.py — 🔁 بستنِ حلقه‌ی eval→learn (بالاترین ROI طبق DEEP-ANALYSIS §۴.۳).

قبلاً: `learning.py` (Thompson) test-green ولی جزیره — هیچ فیدبکی به آن نمی‌رسید و
`kpi_dashboard.py` هم از آن بی‌خبر بود. این ماژول حلقه را می‌بندد:

  MockSource (دیتای staged/مصنوعی، deterministic) → LearningBus.record_result
  → ThompsonBandit یاد می‌گیرد → recommend() فردا → MetricPairGuard (ضدگودهارت)
  → KPIRenderer → PF_STATE/kpi_dashboard.html → رویدادها روی EventBus

طراحی real-data-ready (M2.f2): منبعِ داده یک interface تزریق‌پذیر است؛ سوییچِ
mock→real فقط تعویضِ source است (و همچنان پشتِ گیت‌ها). چون هنوز هیچ اجرایِ
واقعی/درآمدی وجود ندارد [FACT]، دیتای mock تنها راهِ درستِ تستِ end-to-end است.

نکته‌ی طراحیِ آموزشی: MockSource یک «تله‌ی گودهارت» دارد — تگی که کلیکِ بالا ولی
تبدیلِ صفر و report بالا می‌دهد؛ تا detector در عمل دیده شود، نه فقط در تست.

$0 · stdlib-only · صفر شبکه.
"""
from __future__ import annotations

import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from . import config
from .event_bus import EventBus
from .learning_bus import LearningBus
from .telemetry import JobTelemetry

# brain در sys.path (هم‌الگوی learning_bus)
_BRAIN = str(Path(config.PF_ROOT) / "brain")
if _BRAIN not in sys.path:
    sys.path.insert(0, _BRAIN)

try:
    from metric_pairs import MetricPairGuard  # type: ignore
except Exception:  # noqa: BLE001
    MetricPairGuard = None  # type: ignore[assignment]

try:
    from kpi_dashboard import KPIRenderer  # type: ignore
except Exception:  # noqa: BLE001
    KPIRenderer = None  # type: ignore[assignment]


# ─── منبعِ داده (interface تزریق‌پذیر — real-data-ready) ─────────────────────
@dataclass
class MockSource:
    """شبیه‌سازِ deterministic قیف: هر تگ یک کیفیتِ پنهان دارد + نویز.
    تگِ `viral-bait` = تله‌ی گودهارت (کلیکِ زیاد، تبدیلِ صفر، reportِ بالا)."""
    seed: int = 42

    TRUE_QUALITY = {
        "cozy-socks": 0.55, "nylon-sheer": 0.45, "oil-shine": 0.30,
        "pedi-red": 0.40, "viral-bait": 0.15,
    }

    def __post_init__(self):
        self._rng = random.Random(self.seed)

    @property
    def tags(self) -> list[str]:
        return list(self.TRUE_QUALITY)

    def day_metrics(self, day: int, chosen_tag: str) -> dict:
        """متریکِ یک روزِ شبیه‌سازی‌شده برای تگِ انتخابی. deterministic با seed."""
        q = self.TRUE_QUALITY.get(chosen_tag, 0.2)
        r = self._rng.random
        goodhart = chosen_tag == "viral-bait"
        clicks = int(60 + 220 * (q + (0.55 if goodhart else 0.0)) * (0.7 + 0.6 * r()))
        follows = int(clicks * (0.05 + 0.12 * q) * (0.7 + 0.6 * r()))
        upvotes = int(clicks * 0.4 * (0.6 + 0.8 * r()))
        comments = int(upvotes * 0.12 * r())
        paid_subs = 0 if goodhart else int(follows * (0.03 + 0.09 * q) + (r() < q) * 1)
        unlocks = 0 if goodhart else int(paid_subs * (0.5 + r()))
        report_rate = round((0.030 + 0.02 * r()) if goodhart else 0.004 * r(), 4)
        removal_rate = round((0.020 + 0.02 * r()) if goodhart else 0.003 * r(), 4)
        return {
            "day": day, "tag": chosen_tag,
            "clicks": clicks, "follows": follows, "upvotes": upvotes,
            "comments": comments, "unlocks": unlocks, "paid_subs": paid_subs,
            "free_to_paid_conv": round(paid_subs / max(follows, 1), 4),
            "subs_from_channel": paid_subs,
            "retention_rate": round(0.6 + 0.3 * q * r(), 3),
            "dm_replies": int(follows * 0.2 * r()),
            "report_rate": report_rate, "block_rate": round(report_rate * 0.8, 4),
            "removal_rate": removal_rate,
            "complaint_rate": round(report_rate * 0.5, 4),
            "visitors": clicks, "subscribers": max(1, follows // 3),
            "ppv_buyers": max(0, unlocks),
        }


class EvalLearnLoop:
    """حلقه‌ی بسته: پیشنهاد → نتیجه (staged) → یادگیری → ضدگودهارت → داشبورد → رویداد."""

    def __init__(self, bus: EventBus | None = None,
                 learning: LearningBus | None = None,
                 source: MockSource | None = None,
                 state_dir: str | Path | None = None,
                 telemetry: JobTelemetry | None = None):
        self.state = Path(state_dir) if state_dir else Path(config.ensure_pf_state())
        self.state.mkdir(parents=True, exist_ok=True)
        self.bus = bus or EventBus(state_dir=self.state)
        self.learning = learning or LearningBus(
            memory_path=str(self.state / "acq_memory_shadow.json"))
        self.source = source or MockSource()
        self.telemetry = telemetry or JobTelemetry(state_dir=self.state)
        self.guard = MetricPairGuard(
            state_path=self.state / "metric_pairs_state.json") if MetricPairGuard else None
        self.kpi = KPIRenderer() if KPIRenderer else None
        self.last: dict = {}

    def step(self, day: int) -> dict:
        """یک روزِ کامل shadow. خروجی: خلاصه‌ی صادقانه‌ی همان روز."""
        t0 = time.time()
        # ۱) پیشنهادِ مغز (propose-only)
        rec = self.learning.recommend(self.source.tags)
        chosen = rec.best_tag if rec.ok and rec.best_tag else self.source.tags[0]
        self.bus.safe_publish("learning.loop.started", "learning",
                              f"day {day}: chosen tag={chosen}",
                              status="started", payload={"confidence": rec.confidence})
        # ۲) «اجرا» فقط staged — نتیجه از MockSource (هیچ پلتفرم واقعی)
        m = self.source.day_metrics(day, chosen)
        # ۳) یادگیری از نتیجه (سوختِ باهوش‌شدن)
        recorded = self.learning.record_result(
            tag=chosen, platform="reddit", upvotes=m["upvotes"],
            comments=m["comments"], unlocks=m["unlocks"])
        # ۴) ضدگودهارت
        alarms = []
        if self.guard is not None:
            self.guard.add_period({k: m[k] for k in
                                   ("clicks", "paid_subs", "report_rate", "follows",
                                    "free_to_paid_conv", "block_rate", "upvotes",
                                    "subs_from_channel", "removal_rate", "dm_replies",
                                    "retention_rate", "complaint_rate")})
            alarms = [a.to_dict() for a in self.guard.check()]
            for a in alarms:
                self.bus.safe_publish("learning.goodhart.diverged", "learning",
                                      f"{a['proxy']}: {a['kind']} ({a['severity']})",
                                      status="blocked", level="WARN",
                                      approval_state="required",
                                      payload=a)
        # ۵) داشبورد
        dash_path = None
        if self.kpi is not None:
            html = self.kpi.render(
                config={"calendar": {"season": "summer"}},
                acquisition_data={"visitors": m["visitors"], "subscribers": m["subscribers"],
                                  "ppv_buyers": m["ppv_buyers"],
                                  "tag_performance": self._tag_perf()},
                brain_status={"agent_count": 7,
                              "last_insight": f"day {day}: {chosen} · alarms={len(alarms)}"},
                drafts_count=day)
            dash_path = self.state / "kpi_dashboard.html"
            dash_path.write_text(html, encoding="utf-8")
        # ۶) رویداد + telemetry
        dur = int((time.time() - t0) * 1000)
        self.bus.safe_publish("learning.loop.completed", "learning",
                              f"day {day} done: recorded={recorded} alarms={len(alarms)}",
                              status="success", duration_ms=dur)
        self.telemetry.record(job_id=f"eval-day-{day}", organ="learning",
                              duration_ms=dur, outcome="ok")
        self.last = {"day": day, "chosen": chosen, "recorded": recorded,
                     "metrics": m, "alarms": alarms,
                     "learning": self.learning.status(),
                     "dashboard": str(dash_path) if dash_path else None}
        return self.last

    def _tag_perf(self) -> dict:
        """میانگینِ posterior هر تگ برای نمایش (شفافیت، نه تصمیم)."""
        out = {}
        try:
            bridge = getattr(self.learning, "_bridge", None)
            bandit = getattr(bridge, "bandit", None)
            if bandit is not None:
                for t in self.source.tags:
                    out[t] = round(bandit.mean(t), 3)
        except Exception:  # noqa: BLE001
            pass
        return out
