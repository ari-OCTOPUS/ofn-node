#!/usr/bin/env python3
"""approval_channel — منبعِ مستقلِ تأییدِ انسانی برای گیت‌های پول (A2/A3).

اصل (I7 + قاعدهٔ ضدِ گیم): تأیید هرگز از خودگزارشیِ ایجنت نمی‌آید — فقط از این کانال،
که در تولید به هستهٔ انسانی/core.db (نوشتهٔ کلیکِ انسان) وصل می‌شود.
adapterِ عملیاتی = Telegram (انتخابِ اپراتور 2026-07-07)؛ الان وصل نیست →
NotWiredStub که همیشه no-approval می‌دهد → گیت‌ها بسته (fail-closed مطلوبِ فازِ paper).

secret-guard: وصلِ Telegram یک قدمِ جدا و human-gated است؛ tokenِ botِ آن راز است
(انسان در زمانِ اجرا از env/secret-store می‌دهد، هرگز hardcode، هرگز در repo/.env کامیت‌شده).
"""
from __future__ import annotations

from dataclasses import dataclass

# فقط این وضعیت‌ها = «کلیکِ انسانیِ واقعی» در صف کنترل‌برین/core.db (هم‌راستا با I7 outbox status='sent')
VALID_STATUSES = frozenset({"approved", "sent"})


@dataclass(frozen=True)
class Approval:
    """یک تأییدِ per-action از منبعِ مستقل. amount_aud و action_id باید با همان اقدام match بخورند."""
    action_id: str
    amount_aud: float
    status: str
    source: str = "unknown"

    @property
    def valid(self) -> bool:
        return self.status in VALID_STATUSES


class ApprovalChannel:
    """interfaceِ pluggable. پیاده‌سازیِ واقعی (Telegram→core.db) بعداً و human-gated وصل می‌شود."""
    name = "abstract"

    def approval_for(self, action_id: str, amount_aud: float) -> Approval | None:
        raise NotImplementedError


class NotWiredStub(ApprovalChannel):
    """حالتِ فعلیِ فازِ paper: هیچ کانالی وصل نیست → هیچ تأییدی → گیت بسته."""
    name = "not-wired"

    def approval_for(self, action_id: str, amount_aud: float) -> Approval | None:
        return None


class MockApprovalChannel(ApprovalChannel):
    """فقط تست/shadow: مجموعه‌ای از approvalهای از پیش‌داده (شبیه‌سازیِ کلیکِ انسان).
    تطبیق فقط وقتی action_id و amount هر دو بخورند و وضعیت معتبر باشد (نه ادعای ایجنت)."""
    name = "mock"

    def __init__(self, approvals: list[Approval] | None = None):
        self._approvals = list(approvals or [])

    def approval_for(self, action_id: str, amount_aud: float) -> Approval | None:
        for a in self._approvals:
            if a.action_id == action_id and abs(a.amount_aud - amount_aud) < 1e-9 and a.valid:
                return a
        return None
