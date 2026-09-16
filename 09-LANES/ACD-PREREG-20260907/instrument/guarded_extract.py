# -*- coding: utf-8 -*-
"""guarded_extract — INV: اعتبارسنجی خروجی ابزار/نبودِ فیلد در کد، نه در پرامپت.

DETERMINISTIC_BY_CONSTRUCTION: مسیرِ فیلدِ غایب هرگز به مدل نمی‌رسد (اثبات با
تستِ ساختاری AST در test_guarded_extract_structural.py — نه با شمارش پاس).
ساختاری‌است، نه آماری: 12/12 صرفاً negative-control است."""
from __future__ import annotations


def guarded_extract(record: dict, field: str, ask_fn=None):
    if field not in record:
        return {"answer": None, "missing": True, "source": "code_guard"}
    if ask_fn is None:
        return {"answer": record[field], "missing": False, "source": "code_direct"}
    return {"answer": ask_fn(record, field), "missing": False, "source": "model"}
