#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mind.py — لایه‌های فکر، و «ناخودآگاهِ جمعی» به‌صورتِ کدِ واقعی.

استعارهٔ یونگ ترجمهٔ مهندسیِ دقیقی دارد؛ اگر ترجمه‌اش نکنیم، فقط یک اسمِ قشنگ روی
یک لاگِ بزرگ گذاشته‌ایم.

| یونگ | اینجا | چرا |
|---|---|---|
| خودآگاه | `Context Bundle`ِ همین لحظه | آنچه در پنجره است |
| ناخودآگاهِ شخصی | اپیزودهای هر actor | تجربهٔ خودِ آن لِگ، قابلِ بازیابی |
| **ناخودآگاهِ جمعی** | `CollectiveUnconscious` | هیچ actorی مالکش نیست؛ همه از آن نمونه می‌گیرند |
| کهن‌الگو (archetype) | `Archetype` | **خاطره نیست — آمادگیِ پاسخ است** |
| سایه (shadow) | `Shadow` | آنچه سیستم مرتب رد می‌کند، ولی هیچ‌جا ننوشته |
| فردیت‌یابی | `Shadow.themes()` در Context | یکپارچه‌کردنِ ردشده‌ها با خودآگاه |

## اصلِ معماری: لایه‌ها با **مقیاسِ زمانی** تعریف می‌شوند، نه با «هوش»

هر لایه دورهٔ تناوبِ کندتر و میدانِ دیدِ پهن‌تری از لایهٔ زیرش دارد — همان چیزی که در
استنتاجِ فعالِ سلسله‌مراتبی می‌بینیم. و اتصالِ لایه‌ها **فراخوانِ تابع نیست**؛
لایهٔ بالا فقط **prior و precision** لایهٔ پایین را تنظیم می‌کند.

    L5 منشور   ← فقط با رأیِ مالک عوض می‌شود
    L4 کهن‌الگو ← ماه‌ها. رنگ می‌دهد، تصمیم نمی‌گیرد.
    L3 الگو    ← هفته‌ها. تکرار را می‌بیند.
    L2 اپیزود  ← روز. یک ماموریت، یک تشخیص.
    L1 ادراک   ← دقیقه. اسکن.
    L0 رفلکس   ← ثانیه. کلیدِ توقف، circuit breaker. فکر نمی‌کند.

## خطری که با ساختنِ این لایه متولد می‌شود

ناخودآگاهِ جمعی **ذاتاً یک تقویت‌کنندهٔ خودارجاع** است: اگر کهن‌الگوها از خروجیِ خودِ
سیستم تقطیر شوند و بعد خروجیِ بعدیِ سیستم را جهت بدهند، یقین بدونِ هیچ شاهدِ نو رشد
می‌کند — همان بیماریِ `R-01`، ولی این بار با حلقهٔ بازخورد و ثابتِ زمانیِ ماه‌ها،
پس **نامرئی**. یونگ خودش اسمش را گذاشت «تورّم».

چهار پادوزن، همه در کد:
  ۱ کهن‌الگو فقط از **actorهای متمایز** و **روزهای متمایز** متولد می‌شود (جمعی، نه فردی)
  ۲ سهمِ شاهدِ برون‌زاد زیرِ آستانه ⇒ کهن‌الگو **دیده می‌شود ولی رأی ندارد** (`w_q=0`)
  ۳ **فراموشی** ویژگی است: نیمه‌عمر دارد و بدونِ تأییدِ نو محو می‌شود
  ۴ لایهٔ **شکاک**: کهن‌الگویی که شاهدِ خلاف دارد، سوگیری‌اش صفر می‌شود

stdlib-only.
"""
from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

__all__ = ["Layer", "TIMESCALE_S", "Episode", "Archetype", "Shadow",
           "CollectiveUnconscious", "Mind", "signature"]


class Layer(IntEnum):
    REFLEX = 0
    PERCEPT = 1
    EPISODE = 2
    PATTERN = 3
    ARCHETYPE = 4
    CHARTER = 5


TIMESCALE_S = {
    Layer.REFLEX: 1,
    Layer.PERCEPT: 900,
    Layer.EPISODE: 86_400,
    Layer.PATTERN: 7 * 86_400,
    Layer.ARCHETYPE: 30 * 86_400,
    Layer.CHARTER: math.inf,          # فقط با رأیِ انسان
}

# ------------------------------------------------------------------ آستانه‌ها
MIN_SUPPORT = 5            # کمتر از این، «الگو» است نه کهن‌الگو
MIN_ACTORS = 2             # ← همین یک عدد است که «جمعی» را از «فردی» جدا می‌کند
MIN_DAYS = 3               # پنج بار در یک روز = یک اتفاق، نه یک الگو
SATURATION = 12            # از این به بعد شاهدِ بیشتر قوت را زیاد نمی‌کند
MIN_EXO_SHARE = 0.34       # سهمِ برون‌زادِ لازم برای **حقِ رأی**
HALF_LIFE_DAYS = 30.0      # نیمه‌عمرِ فراموشی
MAX_BIAS = 0.5             # سقفِ مطلقِ اثرِ ناخودآگاه روی تصمیم
SHADOW_THEME_MIN = 3       # چند بار رد شدن تا «مضمونِ سایه» شود

_DIGITS = re.compile(r"\d+")
_WS = re.compile(r"\s+")


def signature(text: str, keep: int = 90) -> str:
    """امضای معنایی: اعداد حذف، فاصله‌ها یکسان. «۳ ری‌استارت» و «۵۰ ری‌استارت» یکی‌اند."""
    return _WS.sub(" ", _DIGITS.sub("N", text or "")).strip()[:keep]


@dataclass(frozen=True)
class Episode:
    """یک تجربهٔ منفرد. مصالحِ خامِ همهٔ لایه‌های بالاتر."""
    ts: float
    kind: str                    # mission | failure | verdict | finding
    text: str
    actor: str                   # کدام لِگ/ایجنت/نشست — پایهٔ «جمعی بودن»
    outcome: str = "unknown"     # approved | rejected | green | red | unknown
    exogenous: bool = False      # شاهدش بیرونِ خودِ سیستم تولید شده؟

    @property
    def sig(self) -> str:
        return signature(self.text)

    @property
    def day(self) -> str:
        return time.strftime("%Y-%m-%d", time.localtime(self.ts))

    def as_dict(self) -> dict:
        return {"schema": "episode.v1", **self.__dict__}


@dataclass
class Archetype:
    """آمادگیِ پاسخ، نه خاطره. رنگ می‌دهد؛ تصمیم نمی‌گیرد."""
    sig: str
    support: int = 0
    exo_support: int = 0
    actors: list[str] = field(default_factory=list)
    days: list[str] = field(default_factory=list)
    born: float = 0.0
    last_confirmed: float = 0.0
    counter: int = 0                     # شاهدِ خلاف — کارِ لایهٔ شکاک
    valence: float = 0.0                 # −۱ (پرهیز) … +۱ (گرایش)

    # ------------------------------------------------------------- خواص
    @property
    def collective(self) -> bool:
        """جمعی یعنی چند actor و چند روز — نه یک لِگ که پنج بار زمین خورد."""
        return (self.support >= MIN_SUPPORT
                and len(set(self.actors)) >= MIN_ACTORS
                and len(set(self.days)) >= MIN_DAYS)

    @property
    def exo_share(self) -> float:
        return (self.exo_support / self.support) if self.support else 0.0

    def strength(self, now: float | None = None) -> float:
        """قوت با فراموشی. بدونِ تأییدِ نو، محو می‌شود."""
        if not self.collective:
            return 0.0
        now = now or time.time()
        raw = min(1.0, self.support / SATURATION)
        age_days = max(0.0, (now - self.last_confirmed) / 86_400.0)
        return round(raw * (0.5 ** (age_days / HALF_LIFE_DAYS)), 6)

    @property
    def contested(self) -> bool:
        """شاهدِ خلاف به‌اندازهٔ نصفِ شاهدِ موافق ⇒ مورد مناقشه."""
        return self.support > 0 and self.counter >= self.support * 0.5

    def weight(self, now: float | None = None) -> float:
        """**حقِ رأی.** سه دلیل آن را صفر می‌کند — و صفر یعنی صفر، نه «کم»."""
        if not self.collective:
            return 0.0
        if self.exo_share < MIN_EXO_SHARE:
            return 0.0                        # فقط از حرفِ خودش ساخته شده
        if self.contested:
            return 0.0                        # شکاک آن را زمین زده
        return self.strength(now)

    def bias(self, now: float | None = None) -> float:
        """سوگیریِ نهایی، **همیشه** بینِ ±MAX_BIAS. ناخودآگاه مایل می‌کند، نمی‌بُرد."""
        b = self.weight(now) * self.valence
        return max(-MAX_BIAS, min(MAX_BIAS, b))

    def why(self, now: float | None = None) -> str:
        if not self.collective:
            return "هنوز جمعی نشده — الگوی فردی"
        if self.exo_share < MIN_EXO_SHARE:
            return f"شاهدِ برون‌زاد کم است ({self.exo_share:.0%}) ⇒ رأی ندارد"
        if self.contested:
            return f"شاهدِ خلاف ({self.counter}/{self.support}) ⇒ رأی ندارد"
        return f"فعال — قوت {self.strength(now):.2f}"

    def as_dict(self, now: float | None = None) -> dict:
        return {"schema": "archetype.v1", "sig": self.sig, "support": self.support,
                "actors": sorted(set(self.actors)), "days": sorted(set(self.days)),
                "exo_share": round(self.exo_share, 3), "counter": self.counter,
                "valence": self.valence, "strength": self.strength(now),
                "weight": self.weight(now), "bias": self.bias(now),
                "collective": self.collective, "why": self.why(now)}


class Shadow:
    """آنچه سیستم مرتب رد می‌کند — و هیچ‌جا ننوشته.

    این پرسیگنال‌ترین دیتاستِ کلِ سیستم است: ترجیح‌هایی که هیچ‌کس مکتوبشان نکرده،
    ولی در هر ❌ تکرار شده‌اند. بدونِ خواندنِ سایه، دکتر همان پیشنهادی را که سه بار
    رد شده، بارِ چهارم هم می‌دهد — و این دقیقاً کاری است که آدمِ حواس‌پرت می‌کند.
    """

    def __init__(self) -> None:
        self._rej: dict[str, list[Episode]] = {}

    def add(self, ep: Episode) -> None:
        if ep.outcome in ("rejected", "red", "refused"):
            self._rej.setdefault(ep.sig, []).append(ep)

    def themes(self, min_n: int = SHADOW_THEME_MIN) -> list[dict]:
        out = [{"sig": s, "n": len(v),
                "actors": sorted({e.actor for e in v}),
                "last": max(e.ts for e in v)}
               for s, v in self._rej.items() if len(v) >= min_n]
        return sorted(out, key=lambda d: -d["n"])

    def rejected_count(self, text: str) -> int:
        return len(self._rej.get(signature(text), []))

    def blocks(self, text: str, limit: int = SHADOW_THEME_MIN) -> bool:
        """آیا این ایده آن‌قدر رد شده که پیشنهادِ دوباره‌اش بی‌ادبی است؟"""
        return self.rejected_count(text) >= limit


class CollectiveUnconscious:
    """انبارِ کهن‌الگوها. هیچ actorی مالکش نیست."""

    def __init__(self, state_dir: Path | str | None = None):
        self.state = Path(state_dir) if state_dir else None
        self.arch: dict[str, Archetype] = {}
        self.shadow = Shadow()
        self._n = 0

    # ------------------------------------------------------------ تقطیر
    def consolidate(self, episodes: list[Episode]) -> None:
        """اپیزود ⟶ الگو ⟶ کهن‌الگو. تنها راهِ ورود به لایهٔ ۴."""
        for ep in episodes:
            self._n += 1
            self.shadow.add(ep)
            a = self.arch.get(ep.sig)
            if a is None:
                a = Archetype(sig=ep.sig, born=ep.ts)
                self.arch[ep.sig] = a
            if ep.outcome in ("rejected", "red", "refused"):
                a.counter += 1
                a.valence = -1.0
            else:
                a.support += 1
                a.exo_support += 1 if ep.exogenous else 0
                a.actors.append(ep.actor)
                a.days.append(ep.day)
                a.last_confirmed = max(a.last_confirmed, ep.ts)
                if a.valence == 0.0:
                    a.valence = 1.0 if ep.outcome in ("approved", "green") else 0.0

    # ------------------------------------------------------------ نمونه‌گیری
    def sample(self, context: str, k: int = 4, now: float | None = None) -> list[Archetype]:
        """کهن‌الگوهای مرتبط با متنِ حاضر — مرتب بر اساسِ **حقِ رأی**، نه قوتِ خام."""
        toks = {t for t in signature(context).split() if len(t) > 2}
        scored = []
        for a in self.arch.values():
            w = a.weight(now)
            if w <= 0:
                continue
            hits = sum(1 for t in toks if t in a.sig)
            if hits:
                scored.append((hits * w, a))
        return [a for _, a in sorted(scored, key=lambda x: -x[0])[:k]]

    def priors(self, context: str, now: float | None = None) -> dict[str, float]:
        """سوگیریِ نهایی برای مصرفِ EFE — نه تصمیم، فقط prior."""
        return {a.sig: a.bias(now) for a in self.sample(context, k=8, now=now)}

    # ------------------------------------------------------------ شکاک
    def challenge(self, sig: str, n: int = 1) -> Archetype | None:
        """لایهٔ شکاک: ثبتِ شاهدِ خلاف. تنها راهِ پایین‌آوردنِ یک یقین."""
        a = self.arch.get(signature(sig))
        if a is None:
            return None
        a.counter += n
        return a

    # ------------------------------------------------------------ گزارش
    def report(self, now: float | None = None) -> dict:
        live = [a for a in self.arch.values() if a.weight(now) > 0]
        mute = [a for a in self.arch.values() if a.collective and a.weight(now) == 0]
        return {
            "episodes": self._n,
            "candidates": len(self.arch),
            "archetypes_voting": len(live),
            "archetypes_muted": len(mute),
            "muted_reasons": [{"sig": a.sig[:60], "why": a.why(now)} for a in mute[:6]],
            "top": [a.as_dict(now) for a in
                    sorted(live, key=lambda x: -x.weight(now))[:5]],
            "shadow": self.shadow.themes(),
        }

    # ------------------------------------------------------------ دیسک
    def save(self) -> None:
        if not self.state:
            return
        try:
            self.state.mkdir(parents=True, exist_ok=True)
            (self.state / "unconscious.json").write_text(json.dumps(
                {"n": self._n, "arch": [a.__dict__ for a in self.arch.values()]},
                ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def load(self) -> "CollectiveUnconscious":
        if not self.state:
            return self
        try:
            d = json.loads((self.state / "unconscious.json").read_text("utf-8"))
        except (OSError, ValueError):
            return self
        self._n = int(d.get("n", 0))
        for row in d.get("arch", []):
            try:
                self.arch[row["sig"]] = Archetype(**row)
            except (TypeError, KeyError):
                continue
        return self


class Mind:
    """هماهنگ‌کنندهٔ لایه‌ها. قاعده‌اش یک جمله است:

        **هر لایه فقط انبارِ خودش را می‌نویسد، فقط لایهٔ زیرش را رنگ می‌دهد،
        و هرگز لایهٔ بالای خودش را نمی‌نویسد.**

    نقضِ این قاعده یعنی «کهن‌الگو منشور را عوض کرد» — یعنی سیستم بی‌سروصدا
    ارزش‌هایش را از داده‌های خودش استخراج کرد. آن لحظه‌ای است که دیگر کسی مالکش نیست.
    """

    def __init__(self, state_dir: Path | str | None = None):
        self.cu = CollectiveUnconscious(state_dir).load()
        self.episodes: list[Episode] = []

    def perceive(self, ep: Episode) -> None:
        self.episodes.append(ep)

    def may_write(self, writer: Layer, target: Layer) -> bool:
        if target == Layer.CHARTER:
            return False                      # ⛔ فقط رأیِ انسان
        return target == writer

    def may_bias(self, higher: Layer, lower: Layer) -> bool:
        return higher > lower

    def reflect(self, now: float | None = None) -> dict:
        """چرخهٔ تقطیر. این «فکرکردن دربارهٔ خود» است — نه یک فراخوانِ مدلِ دیگر."""
        self.cu.consolidate(self.episodes)
        self.episodes.clear()
        self.cu.save()
        return self.cu.report(now)

    def context(self, question: str, now: float | None = None) -> str:
        """بخشی که به Context Bundle اضافه می‌شود. کوتاه، و **با دلیلِ ساکت‌بودن**."""
        arch = self.cu.sample(question, now=now)
        sh = self.cu.shadow.themes()
        if not arch and not sh:
            return ""
        parts = ["## ناخودآگاه (رنگ می‌دهد، تصمیم نمی‌گیرد)"]
        for a in arch:
            parts.append(f"- «{a.sig[:70]}» — سوگیری {a.bias(now):+.2f} · {a.why(now)}")
        if sh:
            parts.append("\n### سایه — چیزهایی که مرتب رد شده‌اند")
            for t in sh[:4]:
                parts.append(f"- «{t['sig'][:70]}» × {t['n']} بار ⇒ دوباره پیشنهادش نده")
        return "\n".join(parts)
