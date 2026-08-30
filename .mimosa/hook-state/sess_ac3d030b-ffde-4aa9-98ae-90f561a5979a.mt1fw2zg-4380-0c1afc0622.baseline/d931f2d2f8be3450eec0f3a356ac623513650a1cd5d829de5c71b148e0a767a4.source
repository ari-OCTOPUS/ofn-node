"""
agents/detector.py — W1: Shadow Detector.

Takes a raw time series, fits the shadow model to it, and determines:
Does this data show signs of a hidden dimension (E_shadow > 0)?

This is the core experiment agent: it connects RAW DATA to the model.
"""
from __future__ import annotations
import numpy as np
from .base import BaseAgent, AgentResult
from core.metrics import empirical_shadow, fit_shadow_parameters, build_report_card


class DetectorAgent(BaseAgent):
    name = "W1-Detector"
    role = "shadow detector (hidden-dimension search)"
    task_type = "analysis"

    def run(self, inputs: dict) -> AgentResult:
        """
        Inputs:
            series:  numpy array — the raw time series to analyze
            label:   str — source label for the report
        """
        series = inputs.get("series")
        label = inputs.get("label", "unknown source")

        if series is None:
            return self._make_result(
                findings={}, narrative="خطا: سری زمانی داده نشده.",
                status="fail",
            )

        series = np.asarray(series, dtype=float).flatten()

        # 1) Empirical shadow analysis
        shadow = empirical_shadow(series)
        fit = fit_shadow_parameters(series)

        # 2) Build the quantitative summary
        findings = {
            "label":         label,
            "n_points":      len(series),
            "temporal_mi":   shadow["temporal_mi"],
            "lag1_rho":      shadow["lag1_rho"],
            "memory_len":    shadow["memory_len"],
            "rho_hat":       fit["rho_hat"],
            "signal_frac":   fit["signal_frac"],
            "E_shadow_proxy": fit.get("E_shadow_proxy", 0.0),
            "detectable":    fit.get("detectable", False),
            "verdict":       fit.get("classification", "unknown"),
            "autocorr":      shadow["autocorr"],
        }

        # B12 (فلگ NONLINEAR_MI=1): MI غیرخطیِ باندی — آشوبِ قطعی (مثل logistic
        # map) را که تخمین‌گرِ خطی نمی‌بیند، آشکار می‌کند. کلیدِ additive؛ فلگ
        # خاموش = findings دقیقاً مثل قبل.
        import os
        if os.getenv("NONLINEAR_MI", "0") == "1":
            try:
                from core.nonlinear_mi import nonlinear_gain
                findings.update(nonlinear_gain(series))
            except Exception:
                pass

        # 3) Ask the LLM to interpret the findings
        prompt = self._build_prompt(findings)
        narrative = self.llm(prompt, temperature=0.4)

        status = "ok" if findings["detectable"] else "warning"

        return self._make_result(
            findings=findings,
            narrative=narrative,
            status=status,
        )

    def _build_prompt(self, f: dict) -> str:
        return f"""داده‌ی خام زیر را تحلیل کن — آیا نشانه‌ی بُعد پنهان در آن هست؟

منبع داده: {f['label']}
تعداد نقاط: {f['n_points']}
میانگین اطلاعات متقابل زمانی: {f['temporal_mi']:.6f} nat/گام
همبستگی خود لگ-۱: {f['lag1_rho']:.4f}
ρ تخمینی: {f['rho_hat']:.4f}
بُرداشت سایه (E_shadow proxy): {f['E_shadow_proxy']:.6f}
طول حافظه: {f['memory_len']:.4f}
قابل‌تشخیص: {'بله' if f['detectable'] else 'خیر'}

طبقه‌بندی سیستم: {f['verdict']}

لطفاً:
۱. بگو آیا λρ≠0 معادل برقرار است (آیا ساختار پنهان لو می‌خورد؟)
۲. مقدار E_shadow تخمینی را با لنگرِ مدل (۰.۰۱۲۵۵۳) مقایسه کن
۳. بگو چه نوع بُعد پنهانی محتمل است (فیزیکی/سیستم‌های پویا/اقتصادی)
۴. درجه‌ی اطمینان خودت را اعلام کن (بالا/متوسط/پایین)

پاسخ را مختصر و فنی بده."""
