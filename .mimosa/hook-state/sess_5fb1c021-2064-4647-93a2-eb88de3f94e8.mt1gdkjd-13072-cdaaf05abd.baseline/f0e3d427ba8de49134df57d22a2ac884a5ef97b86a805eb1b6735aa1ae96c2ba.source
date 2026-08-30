#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""concept_code_mapping.py — C23 (مگا‌دستور #۱۷): نگاشت مفهوم زیستی → کد + falsifier.

هر مفهوم بدون falsifier فقط metaphor است و وارد معماری نمی‌شود."""
from __future__ import annotations

MAPPINGS = [
    {
        "concept": "afferent starvation",
        "biological_analogy": "سنسورهای حسی سیگنال نمی‌فرستند → مغز گرسنگی حسی را تشخیص می‌دهد",
        "code_construct": "source registry + freshness-weighted ratio (ratio_model.py)",
        "implementation": "_ops/organs/ratio_model.py::afferent_ratio()",
        "falsifier": "افزودن source معتبر (rate>0, reader=True, fresh) ratio را تغییر ندهد",
        "falsifier_test": "test_ratio_model.py::test_adding_valid_source_never_decreases_ratio",
        "status": "IMPLEMENTED_AND_TESTED",
    },
    {
        "concept": "organ sensation",
        "biological_analogy": "اندام حسی رویداد تولید می‌کند و مغز آن را می‌شنود",
        "code_construct": "provenance-bearing event stream + cognition inbox receipt",
        "implementation": "_ops/organs/knowledge_afferent.py (producer) + knowledge_hook.py (inbox) + cognition_inbox.py (receipt)",
        "falsifier": "event تولید شود ولی هیچ brain receipt ندهد → sensation نیست، noise است",
        "falsifier_test": "C17 canary: cognition_inbox → at least one brain heard receipt",
        "status": "HOOK_READY_AWAITING_CANARY",
    },
    {
        "concept": "feedback loop",
        "biological_analogy": "حسی که به اقدام می‌رسد و نتیجه به حافظه برمی‌گردد",
        "code_construct": "proposal destiny state machine (PROPOSED→SEEN→ACCEPTED|REJECTED|EXPIRED)",
        "implementation": "_ops/organs/feedback_destiny.py::FeedbackDestiny",
        "falsifier": "proposalها بدون outcome انباشته شوند → loop مرده است",
        "falsifier_test": "expire_stale() باید بی‌پاسخ‌ها را EXPIRED کند؛ count EXPIRED > 0 → dead",
        "status": "IMPLEMENTED_AND_TESTED",
    },
    {
        "concept": "homeostasis",
        "biological_analogy": "تعادل داخلی؛ انحراف → اصلاح؛ خیلی زیاد → halt",
        "code_construct": "ratio margin + protective state (BLOCK/SHADOW/ADVISORY)",
        "implementation": "ratio_model.py::RatioBreakdown.margin + metacontrol gate",
        "falsifier": "degraded source (freshness=0) هیچ تغییری در state ندهد → homeostasis نیست",
        "falsifier_test": "test_ratio_model.py::test_stale_source_scores_less_than_fresh + test_broken_reader_penalized",
        "status": "PARTIALLY_IMPLEMENTED (gate در turn_engine، نه در organism)",
    },
    {
        "concept": "bitemporal memory",
        "biological_analogy": "تفاوت زمان وقوع و زمان اطلاع — اختاپوس می‌داند چه زمانی چیزی را فهمید",
        "code_construct": "occurred_at (event time) + recorded_at (ingest time) + decision_time query",
        "implementation": "spine event_spine.py + test_bitemporal_spine_spec.py + EVENT-TIME-PRODUCERS.md",
        "falsifier": "رکورد future (recorded_at > decision_time) در query ظاهر شود → bitemporal نیست",
        "falsifier_test": "test_bitemporal_spine_spec.py::test_future_record_never_eligible + real_data_check.py R1",
        "status": "LAB_PASS_LIVE_PENDING_INDEPENDENT_CLOCKS",
    },
    {
        "concept": "loop breaker (fatigue)",
        "biological_analogy": "خستگی سیناپسی — تکرار بی‌اثر پیام کاهش می‌یابد",
        "code_construct": "tool request quarantine + alert deduplication + RFC merge",
        "implementation": "_ops/organs/loop_breakers_impl.py (ToolRequestGate + AlertAggregator + RFCDeduper)",
        "falsifier": "بدون loop breaker، درخواست تکراری باز هم به owner برسد → breaker کار نمی‌کند",
        "falsifier_test": "gate.check بعد از ۲ rejection باید allowed=False برگرداند؛ aggregator بعد از ۱۰۰ تکرار باید ۱ incident بدهد",
        "status": "IMPLEMENTED_AND_TESTED",
    },
]


def summary() -> dict:
    counts: dict[str, int] = {}
    for m in MAPPINGS:
        counts[m["status"]] = counts.get(m["status"], 0) + 1
    return {
        "total_concepts": len(MAPPINGS),
        "with_falsifier": sum(1 for m in MAPPINGS if m.get("falsifier")),
        "without_falsifier": sum(1 for m in MAPPINGS if not m.get("falsifier")),
        "status_distribution": counts,
        "rule": "هر مفهوم بدون falsifier فقط metaphor است و وارد معماری نمی‌شود",
        "all_have_falsifier": all(m.get("falsifier") for m in MAPPINGS),
    }
