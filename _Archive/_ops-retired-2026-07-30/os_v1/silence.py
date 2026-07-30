#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""silence.py — انضباطِ سکوت (§۷ اکتاپوس‌OS، فازِ ۲).

دلیلِ صریحِ مالک: «رباتی که زیاد پیام بدهد را mute می‌کنم و کل سیستم می‌میرد.»
پس این یک **نیازمندیِ کارکردی** است، نه سلیقه.

سه قاعده:
  ۱ ضدتکرار — هشدارِ هم‌امضا در پنجرهٔ ۲۴ ساعته فقط یک‌بار
    (`governor-alerts.md` همان باگ را ۳۵۸ بار نوشت. آن الگو نباید به تلگرام برسد.)
  ۲ سقفِ ابتکاری — حداکثر N پیامِ خودجوش در روز؛ رسیدن به سقف = لاگ، نه پیامِ بیشتر
  ۳ ادغامِ دایجست — ۹ تاپیک در **یک** پیام، نه ۹ تا

پیام‌هایی که رأی می‌خواهند از سقف مستثنا هستند: آن‌ها کارِ مالک‌اند، نه نویز.

stdlib-only. حالت در حافظه + قابلِ persist با dict.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

__all__ = ["SilenceGate", "Msg", "Kind"]

_NUM = re.compile(r"\d+")


class Kind:
    VERDICT = "verdict"      # رأی می‌خواهد — هرگز throttle نمی‌شود
    ALERT = "alert"          # چیزی قرمز شد
    DIGEST = "digest"        # خلاصهٔ روزانه
    INFO = "info"            # بقیه — بیشترین احتمالِ throttle


@dataclass(frozen=True)
class Msg:
    kind: str
    text: str
    topic: str = "system"

    @property
    def signature(self) -> str:
        """امضای پیام: اعداد حذف می‌شوند تا «۳ ری‌استارت» و «۵ ری‌استارت» یکی شوند."""
        norm = _NUM.sub("N", self.text.strip())[:200]
        return hashlib.sha256(f"{self.kind}|{self.topic}|{norm}".encode()).hexdigest()[:16]


@dataclass
class SilenceGate:
    daily_cap: int = 6
    dedupe_window_s: float = 86400.0
    _seen: dict[str, float] = field(default_factory=dict)
    _sent_today: int = 0
    _day: str = ""

    def _roll(self, now: float) -> None:
        day = str(int(now // 86400))
        if day != self._day:
            self._day, self._sent_today = day, 0
            self._seen = {k: t for k, t in self._seen.items()
                          if now - t < self.dedupe_window_s}

    def allow(self, msg: Msg, now: float) -> tuple[bool, str]:
        """آیا این پیام برود؟ + دلیل."""
        self._roll(now)

        if msg.kind == Kind.VERDICT:
            self._sent_today += 1
            return True, "رأی می‌خواهد — از سقف مستثنا"

        sig = msg.signature
        last = self._seen.get(sig)
        if last is not None and (now - last) < self.dedupe_window_s:
            hrs = (now - last) / 3600.0
            return False, f"تکراری — همین امضا {hrs:.1f} ساعت پیش رفت"

        if self._sent_today >= self.daily_cap:
            return False, f"سقفِ روزانه ({self.daily_cap}) پر شد — لاگ شد، ارسال نشد"

        self._seen[sig] = now
        self._sent_today += 1
        return True, "ok"

    def merge_digest(self, per_topic: dict[str, str], header: str = "🐙 خلاصهٔ روز") -> Msg:
        """۹ دایجستِ جدا ⇒ **یک** پیام. تاپیک‌های خالی حذف می‌شوند."""
        lines = [header, "─" * 10]
        for topic, body in per_topic.items():
            b = (body or "").strip()
            if b:
                lines.append(f"• <b>{topic}</b>: {b}")
        if len(lines) == 2:
            lines.append("چیزی برای گزارش نیست.")
        return Msg(Kind.DIGEST, "\n".join(lines), topic="system")

    @property
    def stats(self) -> dict:
        return {"sent_today": self._sent_today, "daily_cap": self.daily_cap,
                "signatures_held": len(self._seen)}
