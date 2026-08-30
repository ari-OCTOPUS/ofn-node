# impl/base_brain.py — پایهٔ مغزهای Octopus (کابینِ مستقلِ Pydantic)
#
# قراردادِ ساده: هر مغز یک `name` دارد و `async execute(input_data) -> dict`.
# BrainError پرچمِ recoverable دارد: True → چرخه ادامه می‌یابد؛ False → توقفِ سخت.
# این پایه فقط برای hypothesis_engine است؛ مغزهایِ تابعیِ _ops/cortex از این ارث نمی‌برند.
from __future__ import annotations

from typing import Any, Dict


class BrainError(Exception):
    """خطای مغز.

    recoverable=True  → خطای نرم؛ فراخوان‌کننده می‌تواند چرخه را ادامه دهد.
    recoverable=False → خطای سخت؛ عملیات نامعتبر است و نباید دوباره تلاش شود.
    """

    def __init__(self, brain_name: str, message: str, *, recoverable: bool = True):
        self.brain_name = brain_name
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"[{brain_name}] {message}")


class BaseBrain:
    """پایهٔ قراردادِ مغز: نام + execute."""

    def __init__(self, name: str):
        self.name = name

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError(
            f"brain {self.name!r} باید async execute(input_data) را پیاده کند")
