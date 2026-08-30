# -*- coding: utf-8 -*-
"""_ops/chord — فیلترِ وتر (Chord Filter) v0 — SHADOW MODE ONLY.

«وتر» = متریکِ مهندسیِ فاصلهٔ هندسی بین وضعِ واقعی و وضعِ هدف:
    d(x, x*) = sqrt( Σ w_i (x_i - x*_i)^2 / Σ w_i )   ∈ [0,1]

این ماژول برای دکترِ تکاملی و هر جزءِ خودترمیم یک «داورِ شواهدمحور» است:
مشاهده → بردارِ حالت → فاصله/گیتِ عدم‌قطعیت → verdict.

قوانینِ ساختاری (safety by construction — الگوی _ops/epistemics):
- LLMها (Fugu/Ollama-Qwen) فقط مشاور: خروجی JSON ساخت‌یافته، اعتبارسنجیِ deterministic.
- شواهدِ غایب = UNKNOWN؛ هرگز «سالم» فرض نمی‌شود (fail-closed).
- هیچ verdictی مجوزِ اجرا نیست: allowed_actions هرگز شاملِ code.apply/patch نمی‌شود.
- پول/secret/حذف/ارسالِ بیرونی/ژنوم → همیشه REQUEST_APPROVAL (ردهٔ مهمِ AUTONOMY-MATRIX).
- off-loop: این پکیج organism.py/center.py را import نمی‌کند؛ نوشتن فقط روی
  ledger مستقلِ خودش (_ops/chord/state/chord-ledger.jsonl، hash-chain).
- این متریک‌ها «کیفیتِ تصمیمِ عملیاتی» را می‌سنجند — نه هوش، نه آگاهی، نه روانِ انسان.
  لایهٔ تحقیقِ انسانی/زبانی جداست: 03 - Projects/Chord/ (برچسبِ سطحِ شواهد اجباری).

Docs: README.md (spec) · 04 - Architect System/CHORD — معماری فیلترِ وتر (v0).md
"""
from .schemas import (  # noqa: F401
    Verdict, Observation, StateVector, ChordAssessment,
    DIMENSIONS, DEFAULT_WEIGHTS, DEFAULT_TARGETS, clamp01,
)
from .metrics import weighted_distance, component_gaps  # noqa: F401
from .state_vector import build_state_vector  # noqa: F401
from .uncertainty_gate import gate  # noqa: F401
from .repair_policy import assess  # noqa: F401

__version__ = "0.1.0"
SHADOW_ONLY = True  # تا رأی صریح مالک، هیچ گیتِ زنده‌ای نیست — فقط ثبتِ سایه.
