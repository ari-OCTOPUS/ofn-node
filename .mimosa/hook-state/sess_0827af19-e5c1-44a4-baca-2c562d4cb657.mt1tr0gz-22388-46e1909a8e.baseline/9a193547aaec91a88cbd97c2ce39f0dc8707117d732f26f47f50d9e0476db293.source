"""Legs — آداپتور ترکیبی پاها به NBB-CP (رأی NBB-V3: پایهٔ مشترک + کلاس‌های کوچک per-leg).

طراحی: `06-EVIDENCE/DESIGNS-NBB-CP-2026-08-16.md` §V3.
پاها در نسخهٔ فیزیکی روی برد OFN (Orange Pi) اجرا می‌شوند (رأی NBB-V5)؛
این آداپتورها نقشِ پروکسیِ لینک راه‌دور را دارند: heartbeat/propose/status —
بدون هیچ اجرایی. اجرا فقط با گیت‌های V2 (تپ مالک) / V4 (امضا) از مسیرهای امن.
"""
from nbb_cp.adapters.legs.base import LegAdapter, HeartbeatStatus
from nbb_cp.adapters.legs.registry import LegRegistry

__all__ = ["LegAdapter", "HeartbeatStatus", "LegRegistry"]
