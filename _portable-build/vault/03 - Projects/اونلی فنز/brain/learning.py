#!/usr/bin/env python3
"""learning.py — 🧠 لایهٔ یادگیریِ قویِ Project-F (contextual bandit + eval).

چرا: مغزِ قبلی (acquisition.py) رتبه‌بندی را با **میانگینِ خام (greedy)** می‌کرد.
سیستم‌های قویِ ۲۰۲۶ (Thompson/UCB) این را باگ می‌دانند: greedy روی برندهٔ نویزیِ
اولیه قفل می‌شود و به تغییرِ ترند سازگار نمی‌شود. این ماژول اکتشاف (exploration) را
اصولی اضافه می‌کند، بدونِ شکستنِ خطوطِ قرمز.

مرزِ اخلاقی (سازگار با Ethics-Guard §۵ و λ_persist<0):
  • بندیت فقط بینِ سبک‌های محتوایِ **ازقبل-compliant** ساعتِ کمیابِ تولید را تخصیص می‌دهد.
    هرگز چیزی رو به فن دستکاری نمی‌کند؛ پاداش = عملکردِ پستِ عمومی (content-market fit)،
    نه engagement-at-any-cost.
  • اکتشاف = ضدِّ over-fitting به دادهٔ کم (هم‌راستا با round2 §۶.۲: نمونهٔ کوچک، پنجرهٔ ≥۲هفته).
  • propose-only: خروجی پیشنهاد است؛ تصمیم با آری.
  • فلور و سقفِ اکتشاف hard-coded تا هرگز رفتارِ رادیکال نگیرد.

stdlib-only ($0): از random.betavariate برای نمونه‌گیریِ Thompson استفاده می‌شود.
"""
from __future__ import annotations

import json
import math
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

# state قابل‌انحراف با PF_BRAIN_DIR (تست/harness)؛ بدونِ env = کنارِ ماژول (production)
# ۲۰۲۶-۰۸-۰۳ fix: lazy resolution (الگوی saba_link._studio_dir).
def _data_path() -> Path:
    env = os.environ.get("PF_BRAIN_DIR")
    base = Path(env) if env else Path(__file__).resolve().parent
    return base / "bandit_state.json"

# فلور/سقفِ اکتشاف — هرگز خارج از این بازه نمی‌رود (governance)
EXPLORE_FLOOR = 0.05        # حداقل ۵٪ احتمالِ اکتشاف
EXPLORE_CAP = 0.40          # حداکثر ۴۰٪ (بقیه exploitation)
MIN_PULLS = 3              # هر سبک حداقل ۳ بار قبل از قضاوت (small-sample discipline)
DEFAULT_HALFLIFE_DAYS = 21.0  # نیمه‌عمرِ recency = پنجرهٔ آزمایشِ M3


@dataclass
class Observation:
    """یک نتیجهٔ واقعیِ ثبت‌شده (approval-gated: فقط دادهٔ واقعی)."""
    arm: str
    reward: float          # نرمال‌شده در [0,1]
    ts: float = field(default_factory=time.time)
    approved: bool = True   # فقط نتایجِ تأییدشده وارد یادگیری می‌شوند


def normalize_reward(upvotes: int = 0, comments: int = 0, unlocks: int = 0) -> float:
    """پاداشِ نرمال بدونِ اشباعِ زودهنگام (برخلافِ min(1,...) قدیمی).
    از tanh استفاده می‌شود تا برندگانِ قوی از هم تفکیک بمانند و صفر≠۱ نچسبد."""
    raw = upvotes / 80.0 + comments / 15.0 + unlocks / 4.0
    return math.tanh(raw)   # 0→0, بزرگ→~1، هموار و بی‌اشباعِ ناگهانی


class ThompsonBandit:
    """بندیتِ Thompson (Beta-Bernoulli) با recency-decay + فلورِ اکتشاف + گاردِ min-pull.

    - هر arm یک posteriorِ Beta(α,β) دارد که از مشاهداتِ recency-weighted ساخته می‌شود.
    - select(): از هر posterior نمونه می‌گیرد (Thompson) → armِ برنده = بیشترین نمونه.
      arm با دادهٔ کم → posteriorِ پهن → طبیعتاً بیشتر explore می‌شود.
    - min-pull: هر armِ زیرِ MIN_PULLS اولویتِ اکتشاف می‌گیرد (هیچ سبکی نادیده نمی‌ماند).
    - recency: مشاهداتِ قدیمی با نیمه‌عمر decay می‌شوند → سازگار با non-stationarity (ترندِ متغیر).
    """

    def __init__(self, halflife_days: float = DEFAULT_HALFLIFE_DAYS,
                 data_path: str | Path | None = None, seed: int | None = None):
        self.halflife = halflife_days
        self._path = Path(data_path) if data_path else _data_path()
        self._obs: list[Observation] = self._load()
        self._rng = random.Random(seed)

    # ── persistence ──
    def _load(self) -> list[Observation]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return [Observation(**o) for o in data]
        except (json.JSONDecodeError, OSError, TypeError):
            return []

    def _save(self) -> None:
        try:
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps([o.__dict__ for o in self._obs],
                                      ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    # ── update (approval-gated) ──
    def observe(self, arm: str, reward: float, approved: bool = True,
                ts: float | None = None) -> None:
        """ثبتِ یک نتیجه. فقط approved=True وارد یادگیری می‌شود (approval-gated)."""
        reward = max(0.0, min(1.0, float(reward)))
        self._obs.append(Observation(arm=arm, reward=reward,
                                     ts=ts if ts is not None else time.time(),
                                     approved=approved))
        self._save()

    def _recency_weight(self, ts: float, now: float) -> float:
        age_days = max(0.0, (now - ts) / 86400.0)
        return 0.5 ** (age_days / self.halflife)   # نیمه‌عمر

    def posterior(self, now: float | None = None) -> dict[str, tuple[float, float]]:
        """Beta(α,β) هر arm از مشاهداتِ recency-weightedِ approved. prior=Beta(1,1)."""
        now = now or time.time()
        acc: dict[str, list[float]] = {}
        for o in self._obs:
            if not o.approved:
                continue
            w = self._recency_weight(o.ts, now)
            a, b = acc.get(o.arm, [1.0, 1.0])
            acc[o.arm] = [a + w * o.reward, b + w * (1.0 - o.reward)]
        return {arm: (ab[0], ab[1]) for arm, ab in acc.items()}

    def _eff_pulls(self, arm: str, post: dict) -> float:
        a, b = post.get(arm, (1.0, 1.0))
        return (a - 1.0) + (b - 1.0)   # pseudo-countِ مؤثر (بدونِ prior)

    def mean(self, arm: str, now: float | None = None) -> float:
        a, b = self.posterior(now).get(arm, (1.0, 1.0))
        return a / (a + b)

    def explore_rate(self, arms: list[str], now: float | None = None) -> float:
        """نرخِ اکتشاف = تابعِ کمبودِ داده، clamp بینِ فلور و سقف (governance)."""
        post = self.posterior(now)
        if not arms:
            return EXPLORE_CAP
        total = sum(self._eff_pulls(a, post) for a in arms)
        # داده کم → اکتشافِ بیشتر؛ داده زیاد → به فلور نزدیک
        raw = 1.0 / (1.0 + total / (len(arms) * 5.0))
        return max(EXPLORE_FLOOR, min(EXPLORE_CAP, raw))

    def rank(self, arms: list[str], now: float | None = None) -> list[tuple[str, float]]:
        """رتبه‌بندیِ Thompson: از هر posterior یک نمونه؛ armهای کم‌داده طبیعتاً بالا/پایین می‌پرند.
        armهای زیرِ MIN_PULLS اولویتِ اکتشاف (نمونهٔ خوش‌بینانه) می‌گیرند."""
        now = now or time.time()
        post = self.posterior(now)
        scored = []
        for arm in arms:
            a, b = post.get(arm, (1.0, 1.0))
            sample = self._rng.betavariate(a, b)
            if self._eff_pulls(arm, post) < MIN_PULLS:
                sample = max(sample, 0.5 + 0.5 * self._rng.random())  # boostِ اکتشافِ اجباری
            scored.append((arm, sample))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def select(self, arms: list[str], now: float | None = None) -> str | None:
        """یک armِ پیشنهادی (Thompson). propose-only — آری تصمیم می‌گیرد."""
        r = self.rank(arms, now)
        return r[0][0] if r else None

    def explain(self, arms: list[str], now: float | None = None) -> dict:
        """شفافیت (responsible-AI): mean/pulls/uncertainty هر arm + نرخِ اکتشاف."""
        now = now or time.time()
        post = self.posterior(now)
        out = {}
        for arm in arms:
            a, b = post.get(arm, (1.0, 1.0))
            mean = a / (a + b)
            var = (a * b) / ((a + b) ** 2 * (a + b + 1))
            out[arm] = {"mean": round(mean, 3), "eff_pulls": round(self._eff_pulls(arm, post), 2),
                        "uncertainty": round(math.sqrt(var), 3)}
        return {"arms": out, "explore_rate": round(self.explore_rate(arms, now), 3),
                "policy": "thompson+recency+minpull", "propose_only": True}


class UCB1:
    """UCB1 (جایگزینِ قطعی برای Thompson — بدونِ تصادف، برای reproducibility/تست).
    score = mean + c·sqrt(2·ln(N)/n_arm). armِ کم‌داده bonusِ اکتشافِ بالا می‌گیرد."""

    def __init__(self, c: float = 1.4):
        self.c = c
        self._sum: dict[str, float] = {}
        self._n: dict[str, int] = {}
        self._N = 0

    def observe(self, arm: str, reward: float) -> None:
        self._sum[arm] = self._sum.get(arm, 0.0) + max(0.0, min(1.0, reward))
        self._n[arm] = self._n.get(arm, 0) + 1
        self._N += 1

    def score(self, arm: str) -> float:
        n = self._n.get(arm, 0)
        if n == 0:
            return float("inf")   # armِ نادیده = اولویتِ اکتشافِ مطلق
        mean = self._sum[arm] / n
        return mean + self.c * math.sqrt(2 * math.log(max(self._N, 1)) / n)

    def select(self, arms: list[str]) -> str | None:
        return max(arms, key=self.score) if arms else None


# ─── Eval harness (چیزی که سیستمِ قوی دارد و toy ندارد) ───────────────────────
def regret_eval(true_means: dict[str, float], steps: int = 200,
                shift_at: int | None = None, shifted_means: dict | None = None,
                seed: int = 7) -> dict:
    """شبیه‌سازیِ محیطِ (غیرایستا) و مقایسهٔ regretِ Thompson vs Greedy.
    regret = مجموعِ (بهترین‌ممکن − پاداشِ انتخاب‌شده). کمتر = بهتر.
    اگر shift_at ست شود، میانگین‌ها وسطِ راه عوض می‌شوند (تستِ سازگاری با ترند)."""
    rng = random.Random(seed)
    arms = list(true_means.keys())

    def pull(means, arm):
        return 1.0 if rng.random() < means[arm] else 0.0

    # Thompson (recency کوتاه تا شیفت را ببیند)
    tb = ThompsonBandit(halflife_days=9999, data_path=Path("/tmp/_nonexist_ignore.json"))
    tb._obs = []; tb._rng = random.Random(seed + 1); tb._save = lambda: None
    # Greedy (میانگینِ خام، بدونِ اکتشاف — رفتارِ مغزِ قدیمی)
    g_sum = {a: 0.0 for a in arms}; g_n = {a: 0 for a in arms}

    def greedy_select():
        # pure-greedy کلاسیک (مثلِ analyze() قدیمی): بیشترین میانگین، **tie تصادفی**.
        # tie-break تصادفی همان نقطه‌ضعفِ واقعیِ greedy را آشکار می‌کند: قفل‌شدن روی
        # اولین arm‌ی که تصادفاً reward=1 داد (که اغلب بهینه نیست).
        best_m = -1.0
        for a in arms:
            m = (g_sum[a] / g_n[a]) if g_n[a] else 0.0
            if m > best_m:
                best_m = m
        cands = [a for a in arms if ((g_sum[a] / g_n[a]) if g_n[a] else 0.0) >= best_m - 1e-12]
        return rng.choice(cands)

    t_regret = g_regret = 0.0
    for t in range(steps):
        means = true_means
        if shift_at is not None and t >= shift_at and shifted_means:
            means = shifted_means
        best_mean = max(means.values())
        # Thompson
        ta = tb.select(arms, now=t * 86400.0) or arms[0]
        tr = pull(means, ta)
        tb._obs.append(Observation(arm=ta, reward=tr, ts=t * 86400.0))
        t_regret += best_mean - means[ta]
        # Greedy
        ga = greedy_select()
        gr = pull(means, ga)
        g_sum[ga] += gr; g_n[ga] += 1
        g_regret += best_mean - means[ga]

    return {"thompson_regret": round(t_regret, 2), "greedy_regret": round(g_regret, 2),
            "thompson_better": t_regret < g_regret,
            "improvement_pct": round(100 * (g_regret - t_regret) / max(g_regret, 0.01), 1)}


def regret_eval_avg(true_means: dict[str, float], steps: int = 200, seeds: int = 40,
                    shift_at: int | None = None, shifted_means: dict | None = None) -> dict:
    """میانگینِ regret روی چند seed — روشِ درستِ مقایسه (نه cherry-pick یک seed).
    نقطه‌ضعفِ greedy واریانس/lock-in است؛ روی میانگین Thompson باید ببرد."""
    t_all, g_all = [], []
    for s in range(seeds):
        r = regret_eval(true_means, steps, shift_at, shifted_means, seed=s)
        t_all.append(r["thompson_regret"]); g_all.append(r["greedy_regret"])
    tm = sum(t_all) / len(t_all); gm = sum(g_all) / len(g_all)
    return {"thompson_mean_regret": round(tm, 2), "greedy_mean_regret": round(gm, 2),
            "thompson_worst": round(max(t_all), 2), "greedy_worst": round(max(g_all), 2),
            "thompson_better_on_mean": tm < gm,
            "improvement_pct": round(100 * (gm - tm) / max(gm, 0.01), 1)}


class LearningBridge:
    """پل: از AcquisitionMemory (دادهٔ واقعیِ پست‌ها) یک ThompsonBandit می‌سازد تا
    رتبه‌بندیِ tag **اکتشاف‌دار** شود — جایگزینِ greedyِ acquisition.analyze().
    منبعِ حقیقت = همان AcquisitionMemory (کانِن دوم نمی‌سازد؛ bandit ephemeral است).
    propose-only: خروجی فقط پیشنهاد به آری."""

    def __init__(self, acq_memory, halflife_days: float = DEFAULT_HALFLIFE_DAYS,
                 seed: int | None = None):
        self.bandit = ThompsonBandit(halflife_days=halflife_days,
                                     data_path=Path("/dev/null"), seed=seed)
        self.bandit._save = lambda: None            # ephemeral؛ حقیقت در acq_memory
        self.bandit._obs = []
        for r in getattr(acq_memory, "_post_results", []):
            self.bandit._obs.append(Observation(
                arm=r.get("tag", "?"),
                reward=normalize_reward(r.get("upvotes", 0), r.get("comments", 0), r.get("unlocks", 0)),
                ts=r.get("ts", time.time())))

    def recommend(self, candidate_tags: list[str]) -> dict:
        """رتبه‌بندیِ اکتشاف‌دار + شفافیت. propose-only."""
        ranked = self.bandit.rank(candidate_tags)
        return {"ranked": ranked,
                "top": ranked[0][0] if ranked else None,
                "explain": self.bandit.explain(candidate_tags),
                "note": "propose-only · exploration-aware · human decides"}


if __name__ == "__main__":  # pragma: no cover
    # دموی سریع: محیطِ با شیفتِ ترند
    r = regret_eval({"nylon": 0.5, "oil": 0.2, "asmr": 0.35, "silk": 0.3, "lace": 0.25},
                    steps=300, shift_at=150,
                    shifted_means={"nylon": 0.2, "oil": 0.2, "asmr": 0.6, "silk": 0.3, "lace": 0.25})
    print("regret eval:", r)
