#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""leg_failure.py — ثبتِ علتِ افتادنِ لِگ (§۶ اکتاپوس‌OS).

شاهدِ ۲۵ جولای: `lead-naghshi` **۶۶ ری‌استارت** در ۱۵ روز، ۳۸ فاصله در باندِ ۶۱ ثانیه،
circuit-breaker ۹ بار — و **صفر تشخیص**. self-heal فقط بلندش می‌کند؛ هیچ‌جا علت ثبت نمی‌شود.

این ماژول **رفتارِ ری‌استارت را تغییر نمی‌دهد.** فقط علت را می‌گیرد. additive و
فقط‌نوشتنی، تا حلقهٔ کور به حلقهٔ باعلت تبدیل شود.

stdlib-only.
"""
from __future__ import annotations

import json
import traceback
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["FailureRecorder", "FailureRecord", "capture"]

MAX_RECORDS = 200


@dataclass(frozen=True)
class FailureRecord:
    leg_id: str
    ts: str
    exc_type: str
    message: str
    last_frame: str
    beat: int | None = None

    def as_dict(self) -> dict:
        return {"schema": "leg-failure.v1", "leg_id": self.leg_id, "ts": self.ts,
                "exc_type": self.exc_type, "message": self.message,
                "last_frame": self.last_frame, "beat": self.beat}


def capture(exc: BaseException, leg_id: str, ts: str,
            beat: int | None = None) -> FailureRecord:
    """استخراجِ علتِ فشرده از یک استثنا — بدونِ نشتِ مسیرِ کامل یا داده."""
    tb = traceback.extract_tb(exc.__traceback__)
    frame = ""
    if tb:
        f = tb[-1]
        frame = f"{Path(f.filename).name}:{f.lineno} in {f.name}"
    return FailureRecord(
        leg_id=leg_id, ts=ts, exc_type=type(exc).__name__,
        message=str(exc)[:300], last_frame=frame, beat=beat,
    )


@dataclass
class FailureRecorder:
    """می‌نویسد و خلاصه می‌کند. هیچ‌وقت raise نمی‌کند."""

    state_dir: Path
    _mem: list[FailureRecord] = field(default_factory=list)

    def record(self, rec: FailureRecord) -> None:
        self._mem.append(rec)
        del self._mem[:-MAX_RECORDS]
        try:
            d = self.state_dir / "legs"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{rec.leg_id}-last-failure.json").write_text(
                json.dumps(rec.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            with (d / "failures.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec.as_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass                                   # ثبتِ علت هرگز لِگ را نمی‌کشد

    def diagnose(self, leg_id: str | None = None) -> dict:
        """آیا این حلقه یک علتِ تکراری دارد؟ — چیزی که ۶۶ ری‌استارت هرگز نگفت."""
        rs = [r for r in self._mem if leg_id is None or r.leg_id == leg_id]
        if not rs:
            return {"n": 0, "verdict": "[UNKNOWN] هنوز شکستی ثبت نشده"}
        sig = Counter(f"{r.exc_type} @ {r.last_frame}" for r in rs)
        top, n = sig.most_common(1)[0]
        share = n / len(rs)
        return {
            "n": len(rs), "distinct": len(sig), "top_signature": top,
            "top_share": round(share, 3),
            "verdict": ("علتِ واحد و تکراری — قابلِ تعمیر" if share >= 0.7
                        else "علت‌های پراکنده — احتمالاً محیطی، نه یک باگ"),
            "all": [{"signature": s, "count": c} for s, c in sig.most_common(5)],
        }
