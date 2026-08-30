#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spine_soak.py — C7 Slice 5: تلمتریِ soakِ مسیرِ واحدِ spine (C4 OCTOPUS_SPINE_VIA_ADAPTER).

جدا از spine_adapters نگه داشته شده چون spine_adapters ساختاراً حق ندارد env را مستقیم بخواند
(ناوردیِ ضدِ fork، test_spine_multidomain::t_i). این ماژول فقط گزارش می‌دهد؛ صفر emit/effect.

هدف: برای soakِ owner-observed، وضعیتِ صادقِ flag را بده — **پیش‌فرض OFF، dual_write بازنشسته
نشده، و مسیرِ واحد فقط READY است (نه LIVE)**.
"""
from __future__ import annotations

import os

VIA_ADAPTER_FLAG = "OCTOPUS_SPINE_VIA_ADAPTER"


def soak_status() -> dict:
    on = str(os.environ.get(VIA_ADAPTER_FLAG, "")).strip().lower() in ("1", "true", "yes", "on")
    return {"via_adapter_flag": "on" if on else "off",
            "default": "off",
            "direct_dual_write": "LIVE (not retired)",
            "single_surface": "READY (spine_adapters.emit_event) — parity byte-identical proven",
            "vocab": "spine = cross-domain event INDEX/projection (not a competing SoT); "
                     "outcomes.db/ledger = substrate; events.py/review_bus = independent projections"}
