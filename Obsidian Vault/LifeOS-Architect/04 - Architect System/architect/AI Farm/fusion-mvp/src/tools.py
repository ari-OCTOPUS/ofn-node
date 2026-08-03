"""
tools.py — چک‌لیست #۴: گذرگاه ابزار + least-privilege.

هر اقدام بیرونی فقط از این «گذرگاه» عبور می‌کند. قبل از اجرا بررسی می‌شود که
آیا آن ایجنت اصلاً مجاز به آن ابزار هست (config.AGENT_ALLOWED_TOOLS). اگر نه،
ToolPermissionError پرتاب می‌شود — یعنی «هیچ کنش بی‌مجوز».
"""
from __future__ import annotations

import config


class ToolPermissionError(Exception):
    pass


def _web_search_mock(query: str) -> str:
    # ابزار جستجوی نمونه (offline). در فاز بعدی با MCP/API واقعی جایگزین می‌شود.
    return (f"نتایج برای «{query}» (نمونه):\n"
            "- منبع ۱: داده‌ی معتبر.\n- منبع ۲: داده‌ی معتبر.\n"
            "- منبع ۳: ادعای اثبات‌نشده (پرچم احتیاط).")


TOOLS = {
    "web_search_mock": _web_search_mock,
}


class ToolGateway:
    """تنها نقطه‌ی اجرای ابزارها؛ مجوز scoped را اعمال می‌کند."""

    def __init__(self, audit=None):
        self.audit = audit

    def call(self, agent: str, tool: str, **kwargs):
        allowed = config.AGENT_ALLOWED_TOOLS.get(agent, set())
        if tool not in allowed:
            if self.audit:
                self.audit.log("tool_denied", agent, tool=tool, reason="least-privilege")
            raise ToolPermissionError(
                f"⛔ ایجنت «{agent}» مجاز به ابزار «{tool}» نیست (least-privilege)")
        if tool not in TOOLS:
            raise ToolPermissionError(f"ابزار ناشناخته: {tool}")
        if self.audit:
            self.audit.log("tool_call", agent, tool=tool, args=kwargs)
        return TOOLS[tool](**kwargs)
