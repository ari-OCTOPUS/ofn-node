#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""conftest.py — Project-F · هیچ تستی به فایلِ تولیدیِ حسابرسی نمی‌نویسد.

چرا این فایل هست (راستی‌آزماییِ متخاصمِ ۲۰۲۶-۰۷-۲۵):
سوئیتِ سبزِ خودِ ونچر ۵۰ ردیف در `langar/approvals.jsonl` — فایلِ **تولیدیِ**
ردِ حسابرسیِ تأییدِ انسانی — نوشته بود، که ۱۴ تای آن `actor: owner` داشت.
تنها یک تست (`tests/test_state_machines.py:212`) درزِ `DEFAULT_AUDIT_FILE` را
monkeypatch می‌کرد؛ بقیه مستقیم روی مسیرِ تولید می‌نوشتند و هر اجرای سوئیت ~۵۰
ردیفِ تازه اضافه می‌کرد.

ضررش امروز صفر است (فایل gitignore و بی‌خواننده)، ولی مؤخر و جدی: در سیستمی که
جدولِ رأیِ واقعی صفر ردیف دارد، این فایل تنها چیزی است که شبیهِ «مدرکِ تأییدِ
مالک» به‌نظر می‌رسد.

این fixture برای **هر** تستِ pytest مسیر را به tmp می‌برد و منشأ را `test` مهر
می‌کند. لایهٔ دومِ دفاع در `brain/audit.py::_origin` است — تا تستی که این conftest
را دور بزند (مثلاً اجرای مستقیمِ unittest از `run_all.py`) هم ردیفش قابلِ تفکیک بماند.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
for _p in (str(_ROOT), str(_ROOT / "brain"), str(_ROOT / "langar")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import pytest
except ImportError:  # pragma: no cover — سوئیتِ unittest بدونِ pytest
    pytest = None  # type: ignore[assignment]


if pytest is not None:

    @pytest.fixture(autouse=True)
    def _no_production_audit_writes(tmp_path, monkeypatch):
        """هر تست: سینکِ حسابرسی → tmp، و منشأ = test."""
        sink = tmp_path / "approvals.jsonl"
        monkeypatch.setenv("PF_AUDIT_FILE", str(sink))
        monkeypatch.setenv("PF_AUDIT_ORIGIN", "test")
        try:
            import audit as _audit  # brain/audit.py
        except ImportError:
            try:
                from brain import audit as _audit  # type: ignore[no-redef]
            except ImportError:
                yield
                return
        # `DEFAULT_AUDIT_FILE` در زمانِ import محاسبه می‌شود، پس setenv تنها کافی نیست.
        monkeypatch.setattr(_audit, "DEFAULT_AUDIT_FILE", sink, raising=False)
        yield
