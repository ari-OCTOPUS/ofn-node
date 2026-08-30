"""CouncilRouter — نگاشت کار→شورا (سایه). مسیر اجرا ندارد؛ کارِ ناشناخته رد."""
from __future__ import annotations

from typing import Any

from councils.base import BaseCouncil

ROUTE_TABLE: dict[str, str] = {
    "architecture": "architecture",
    "schema": "architecture",
    "boundary": "architecture",
    "hypothesis": "epistemic",
    "evidence": "epistemic",
    "calibration": "epistemic",
    # safety/ops/product/identity: عمداً ثبت نشده‌اند — فازهای ۲ به بعد سند
}


class CouncilRouter:
    def __init__(self) -> None:
        self._councils: dict[str, BaseCouncil] = {}

    def register(self, council: BaseCouncil) -> None:
        if getattr(council, "zero_tool_access", False) is not True:
            raise ValueError("شورا بدون گارد zero_tool_access پذیرفته نمی‌شود")
        self._councils[council.name] = council

    def route(self, task: dict[str, Any]):
        """برمی‌گرداند: (council, None) یا (None, reason)."""
        kind = str(task.get("kind") or "").lower()
        target = ROUTE_TABLE.get(kind)
        if target is None:
            return None, f"کارِ ناشناخته/غیرمجاز در سایه: kind={kind!r}"
        council = self._councils.get(target)
        if council is None:
            return None, f"شورای {target!r} ثبت نشده — فازِ بعد سند"
        return council, None
