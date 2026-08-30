# -*- coding: utf-8 -*-
"""قرارداد رسمی دو رکن هر بیزنس — مغز دوم v2 (فاز ۱).

هر آداپتر بیزنس (زیمان/نقاشی/حسابداری/Project-F) موظف است دو کلاس بسازد:
  1) ResearchEngine       — رکن A: تحقیق درآمدزایی خودکار → Brief
  2) OwnerInteractionEngine — رکن B: تبدیل Brief به پیام برای صاحب بیزنس (approve-first)

اصول (ADR-005/006 در ARCHITECTURE.md):
- رکن B هرگز مستقیم send نمی‌کند؛ خروجی‌اش به ApprovalQueue می‌رود.
- کانال (تلگرام/واتساپ) پشت interface ی Channel انتزاعی است.
- بازخورد ادمین (مفید/بی‌فایده) با learn() به تحقیق بعدی برمی‌گردد.
هیچ secret ای در این ماژول نگه‌داری نمی‌شود.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, List, Optional


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- دیتاکلاس‌ها
@dataclass
class Brief:
    """خروجی استاندارد رکن A — کوتاه و عملی."""
    business: str                 # id بیزنس در projects.yaml (ziman/painting/accounting/projectf)
    title: str                    # یک خط: فرصت چیست
    opportunity: str              # شرح فرصت درآمدزایی
    why: str                      # چرا الان / برای این بیزنس
    action: str                   # اقدام پیشنهادی مشخص و قابل اجرا
    source: str                   # منبع (URL یا «تجربه داخلی»)
    id: Optional[int] = None      # پس از ذخیره در Memory پر می‌شود
    created: str = field(default_factory=_now)


@dataclass
class Feedback:
    """بازخورد ادمین روی یک Brief — سوخت حلقهٔ یادگیری."""
    brief_id: int
    useful: bool                  # 👍 True / 👎 False
    note: str = ""                # توضیح اختیاری ادمین
    ts: str = field(default_factory=_now)


@dataclass
class OutboxMessage:
    """پیام رکن B برای صاحب بیزنس — تا Approve نشود ارسال نمی‌شود."""
    business: str
    channel: str                  # "telegram" | "whatsapp"
    to_ref: str                   # ارجاع گیرنده (مثلاً user-id در users.yaml) — نه شماره/توکن خام
    text: str
    brief_id: Optional[int] = None
    status: str = "pending"       # pending → approved/edited/rejected → sent/failed
    id: Optional[int] = None
    ts: str = field(default_factory=_now)


# ---------------------------------------------------------------- کانال‌ها
class Channel(ABC):
    """کانال ارسال به صاحب بیزنس. تلگرام فاز ۳؛ واتساپ آداپتور بعدی روی همین interface."""

    name: str = "abstract"

    @abstractmethod
    def send(self, to_ref: str, text: str) -> bool:
        """ارسال واقعی. فقط ApprovalQueue بعد از تأیید صدا می‌زند. True=موفق."""

    def is_available(self) -> bool:
        """پیکربندی/توکن آماده است؟ (برای گزارش اتصال)"""
        return True


# ---------------------------------------------------------------- رکن A
class ResearchEngine(ABC):
    """رکن A — تحقیق درآمدزایی خودکار و زمان‌بندی‌شده (روزانه، ADR: DeepSeek از Gateway)."""

    business: str = ""

    @abstractmethod
    def gather_context(self) -> str:
        """دیتای پروژه + خلاصهٔ feedbackهای قبلی + یافته‌های قبلی knowledge → متن زمینه."""

    @abstractmethod
    def run(self, context: str) -> Brief:
        """یک دور تحقیق (وب از طریق gateway.search + gateway.llm) → دقیقاً یک Brief."""

    @abstractmethod
    def learn(self, feedbacks: Iterable[Feedback]) -> None:
        """بازخوردها را در استراتژی تحقیق بعدی لحاظ کن (مثلاً وزن موضوع‌ها)."""


# ---------------------------------------------------------------- رکن B
class OwnerInteractionEngine(ABC):
    """رکن B — تعامل انسانی با صاحب بیزنس. ساده برای گیرنده، approve-first برای ادمین."""

    business: str = ""
    channel: str = "telegram"

    @abstractmethod
    def compose(self, brief: Brief) -> OutboxMessage:
        """Brief فنی → پیام گرم و قابل‌فهم برای صاحب بیزنس (زبان/سبک خود بیزنس)."""

    @abstractmethod
    def discover(self) -> List[OutboxMessage]:
        """جدا از بریف‌ها: راه‌های متنوع پیشبرد اهداف را کشف و به‌صورت پیشنهاد پیام بده
        (مثلاً یادآوری مناسبت زیمان). خروجی هم به صف تأیید می‌رود."""


# ---------------------------------------------------------------- صف تأیید
class ApprovalQueue(ABC):
    """صف مرکزی لایه ۰ — پیاده‌سازی واقعی فاز ۲ روی جدول outbox + دکمه‌های inline ربات ادمین."""

    @abstractmethod
    def submit(self, msg: OutboxMessage) -> int:
        """ثبت پیام؛ کارت با [✅ Approve | ✏️ Edit | ❌ Reject] برای ادمین می‌رود. → id"""

    @abstractmethod
    def resolve(self, msg_id: int, decision: str, edited_text: Optional[str] = None) -> None:
        """decision ∈ approved/rejected؛ ‏edited_text جایگزین متن در حالت Edit.
        approved → ارسال با Channel مربوطه + status=sent + لاگ کامل."""

    @abstractmethod
    def pending(self) -> List[OutboxMessage]:
        """پیام‌های منتظر تأیید (برای /status ادمین)."""


__all__ = [
    "Brief", "Feedback", "OutboxMessage",
    "Channel", "ResearchEngine", "OwnerInteractionEngine", "ApprovalQueue",
]
