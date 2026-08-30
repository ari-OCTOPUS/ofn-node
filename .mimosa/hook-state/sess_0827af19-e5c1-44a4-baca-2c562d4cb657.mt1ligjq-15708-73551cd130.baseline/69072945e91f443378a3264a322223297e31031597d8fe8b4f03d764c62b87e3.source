#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reconcile.py — سنجشِ mismatchِ dual-write بین Event Spine و یک domain source.

هنگامِ مهاجرتِ تدریجی، هر producer هم domain-ledgerِ خودش را می‌نویسد هم spine را؛ این ابزار
اختلاف را می‌سنجد (چه چیزی در یکی هست و دیگری نیست) تا drift قابل‌رصد شود. تابعِ خالص،
بدونِ side-effect؛ خروجیِ قطعی.
"""
from __future__ import annotations


def reconcile_keys(spine_keys, domain_keys) -> dict:
    """اختلافِ دو مجموعه idempotency/correlation key. خروجی: {matched, only_in_spine,
    only_in_domain, spine_total, domain_total, mismatch}."""
    s = set(str(k) for k in (spine_keys or []))
    d = set(str(k) for k in (domain_keys or []))
    only_s = sorted(s - d)
    only_d = sorted(d - s)
    return {"matched": len(s & d), "only_in_spine": only_s, "only_in_domain": only_d,
            "spine_total": len(s), "domain_total": len(d),
            "mismatch": len(only_s) + len(only_d)}


def reconcile_by_correlation(spine, domain_correlation_ids) -> dict:
    """spine.events را بر اساسِ correlation_id با idهای یک domain مقایسه کن."""
    spine_corr = {e["correlation_id"] for e in spine.events()}
    return reconcile_keys(spine_corr, domain_correlation_ids)
