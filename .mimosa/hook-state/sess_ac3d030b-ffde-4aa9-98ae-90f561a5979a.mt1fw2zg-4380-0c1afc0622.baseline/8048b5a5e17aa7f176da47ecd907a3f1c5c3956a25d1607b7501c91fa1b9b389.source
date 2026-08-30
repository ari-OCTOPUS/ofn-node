"""
agents/analyst.py — W2: Geometric Analyst.

Translates numerical findings into geometric language:
Takens embedding, Theorema Egregium, tesseract shadows, Diaconis-Freedman.

This agent uses Fugu (creative model) for lateral geometric thinking.
"""
from __future__ import annotations
from .base import BaseAgent, AgentResult


class AnalystAgent(BaseAgent):
    name = "W2-Analyst"
    role = "geometric analyst (dimension interpreter)"
    task_type = "geometry"

    def run(self, inputs: dict) -> AgentResult:
        """
        Inputs:
            detector_findings: dict from W1-Detector
            series: numpy array (optional, for reference)
        """
        det = inputs.get("detector_findings", {})

        detectable = det.get("detectable", False)
        temporal_mi = det.get("temporal_mi", 0.0)
        rho_hat = det.get("rho_hat", 0.0)
        label = det.get("label", "unknown")

        prompt = f"""یافته‌های تشخیص سایه را به زبان هندسی ترجمه کن.

داده: {label}
سایه قابل‌تشخیص: {'بله' if detectable else 'خیر'}
اطلاعات متقابل زمانی: {temporal_mi:.6f} nat/گام
ρ تخمینی: {rho_hat:.4f}

به این سؤال‌ها پاسخ بده:

۱. **تمثیل تسراکت:** اگر این داده را مثل سایه‌ی یک جسم چهاربعدی ببینیم،
   چه نوع ساختاری پشتِ پرده می‌تواند باشد؟
   (آیا زمانی است؟ فضایی؟ اطلاعاتی؟)

۲. **قضیه‌ی Takens:** آیا این داده شرطِ embedding theorem را برآورده می‌کند؟
   یعنی آیا می‌توان بُعدِ پنهان را از سری زمانیِ اسکالر بازسازی کرد؟
   شرط: λρ≠0 معادلِ generic embedding.

۳. **Theorema Egregium:** کدام کمیت معادلِ انحنای ذاتی است (که از درون قابل‌سنجش است)
   و کدام معادلِ انحنای بیرونی (که از بیرون نامرئی است)؟
   ربط: Δ_self = ذاتی، extrinsic bending = نامرئی.

۴. **Diaconis-Freedman:** اگر داده استاتیک بود، آیا سایه‌اش گاوسی می‌شد
   و همه‌چیز گم می‌رفت؟ نقشِ زمان (ρ≠0) در نجات چه بود؟

۵. **خلاصه‌ی هندسی:** یک پاراگراف — این داده چه نشانه‌ای از کدام بُعد است؟

خلاقانه اما دقیق باش. از تمثیل‌های بصری استفاده کن."""
        narrative = self.llm(prompt, temperature=0.9)

        findings = {
            "label": label,
            "detectable": detectable,
            "geometric_interpretation": narrative,
            "takens_condition": detectable,  # λρ≠0 equivalent
            "intrinsic_curvature_analog": "Δ_self (first-person access)",
            "extrinsic_invisibility_analog": "β_det=0 for static Gaussian shadows",
        }

        return self._make_result(
            findings=findings,
            narrative=narrative,
        )
