"""registry.py — رجیستری پاها با گارد نام‌یکتا (درس C-014: بدون رجیستری، کارها دوبار).

هر پا دقیقاً یک‌بار ثبت می‌شود؛ ثبتِ نامِ تکراری = ValueError (نه بازنویسیِ خاموش).
"""
from __future__ import annotations

from typing import Optional

from nbb_cp.adapters.legs.base import LegAdapter


class LegRegistry:
    def __init__(self) -> None:
        self._legs: dict[str, LegAdapter] = {}

    def register(self, adapter: LegAdapter) -> LegAdapter:
        lid = adapter.leg_id
        if not lid or lid == "base":
            raise ValueError("leg_id باید در زیرکلاس مقدار یگانه بگیرد")
        if lid in self._legs:
            raise ValueError(f"پای تکراری: {lid!r} قبلاً ثبت شده — دو نمونه = دو کار (C-014)")
        self._legs[lid] = adapter
        return adapter

    def get(self, leg_id: str) -> Optional[LegAdapter]:
        return self._legs.get(leg_id)

    def all(self) -> list[LegAdapter]:
        return list(self._legs.values())

    def stale_legs(self, now: Optional[float] = None) -> list[str]:
        return [a.leg_id for a in self._legs.values() if a.status(now).stale]
